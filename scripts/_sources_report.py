"""Says whether every address the installers download from still answers, and still holds what is pinned.

Called by scripts/check-upstream.sh. An install that cannot fetch one file stops, so a
repository that moves or is taken down breaks every fresh install (it happened to the
trainer's). This reads the addresses from where they are written, so nothing is listed
twice:

  - windows/setup.ps1: every file with a Url (and our Copy of it), the commits it fetches,
    the engine's Whisper files;
  - scripts/fetch-models.sh: every fetch, the style LoRAs' list;
  - macos/setup.sh, where the branch has it;
  - engine/Dockerfile: the repositories it clones, at their pinned refs;
  - app/soundfonts.py: where the score preview's samples come from.

A file on Hugging Face is asked about in one batch per repository, and its size and
SHA-256 (where Hugging Face keeps one: large files) compared with what is pinned, so a
file replaced under the same name shows as well as one that is gone. Anything else gets
a HEAD request; a pinned commit is looked up on GitHub. Exit status 1 when anything is
missing or different.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HF_FILE = re.compile(r"^https://huggingface\.co/([\w.-]+/[\w.-]+)/resolve/([^/]+)/(.+)$")


@dataclass
class Source:
    where: str
    url: str
    sha: str | None = None
    size: int | None = None


def _expand(text: str, names: dict[str, str]) -> str | None:
    """$NAME, ${NAME} and $NAME/... from the names found; None if anything is left unexpanded."""
    def one(m: re.Match) -> str:
        return names.get(m.group(1) or m.group(2), m.group(0))
    out = re.sub(r"\$\{(\w+)\}|\$(\w+)", one, text)
    return None if "$" in out else out


def from_setup_ps1(path: Path) -> list[Source]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    names: dict[str, str] = {}
    for m in re.finditer(r"^\s*\$(\w+)\s*=\s*(['\"])((?:https://|\$\w+/)[^'\"]*)\2\s*$", text, re.M):
        value = _expand(m.group(3), names)
        if value:
            names[m.group(1)] = value
    found = []
    for block in re.findall(r"@\{([^{}]*)\}", text, re.S):
        sha = re.search(r"\bSha\s*=\s*'([0-9a-f]{64})'", block)
        size = re.search(r"\bSize\s*=\s*(\d+)", block)
        for key in ("Copy", "Url"):
            m = re.search(rf"\b{key}\s*=\s*(['\"])([^'\"]+)\1", block)
            url = m and _expand(m.group(2), names)
            if url:
                found.append(Source(f"{path.relative_to(ROOT)} ({key.lower()})" if key == "Copy" else str(path.relative_to(ROOT)),
                                    url, sha and sha.group(1), size and int(size.group(1))))
    # The engine's Whisper files: a list of names under one address.
    whisper = re.search(r"\$whisperUrl\s*=\s*'([^']+)'", text)
    files = re.search(r"\$whisperFiles\s*=\s*@\((.*?)\n\s*\)", text, re.S)
    if whisper and files:
        for entry in re.findall(r"@\{([^{}]*)\}", files.group(1)):
            name = re.search(r"File\s*=\s*'([^']+)'", entry)
            sha = re.search(r"Sha\s*=\s*'([0-9a-f]{64})'", entry)
            size = re.search(r"Size\s*=\s*(\d+)", entry)
            if name:
                found.append(Source(str(path.relative_to(ROOT)), f"{whisper.group(1)}/{name.group(1)}",
                                    sha and sha.group(1), size and int(size.group(1))))
    pins = dict(re.findall(r"^\s*(\w+)\s*=\s*'([0-9a-f]{40})'", text, re.M))
    for repo, pin in re.findall(r"Get-Commit '([\w.-]+/[\w.-]+)' \$Pins\.(\w+)", text):
        if pin in pins:
            found.append(Source(f"{path.relative_to(ROOT)} (commit)", f"https://github.com/{repo}/commit/{pins[pin]}"))
    return found


def from_fetch_models(path: Path) -> list[Source]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    names = {m.group(1): m.group(2) for m in re.finditer(r"^\s*([A-Z_]+)=(https://\S+)\s*$", text, re.M)}
    found = []
    for m in re.finditer(r'fetch "([^"]+)"[^\n]*(?:\\\n[^\n]*)*', text):
        for raw in [m.group(1)] + re.findall(r'"(\$\w+/[^"]+|https://[^"]+)"', m.group(0))[1:]:
            url = _expand(raw, names)
            if url and url.startswith("https://"):
                found.append(Source(str(path.relative_to(ROOT)), url))
    lists = re.search(r"STYLE_LORAS=(https://\S+).*?<<'LIST'\n(.*?)\nLIST", text, re.S)
    if lists:
        for line in lists.group(2).splitlines():
            parts = line.split()
            if len(parts) == 2:
                found.append(Source(str(path.relative_to(ROOT)), f"{lists.group(1)}/{parts[0]}", parts[1]))
    return found


def from_macos_setup(path: Path) -> list[Source]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    names: dict[str, str] = {}
    for m in re.finditer(r"^\s*([A-Z_]+)=((?:https://|\$\w+/)\S+?)\s*$", text, re.M):
        value = _expand(m.group(2), names)
        if value:
            names[m.group(1)] = value
    found = []
    # dir|file|bytes|sha256|url|lyrics[|copy]
    for size, sha, raw, copy in re.findall(r"^\w+\|[^|]+\|(\d+)\|([0-9a-f]{64})\|([^|]+)\|[^|\n]*(?:\|([^|\n]+))?$", text, re.M):
        for where, address in ((str(path.relative_to(ROOT)), raw), (f"{path.relative_to(ROOT)} (copy)", copy)):
            url = address and _expand(address, names)
            if url:
                found.append(Source(where, url, sha, int(size)))
    commit = re.search(r"^TRAINER_COMMIT=([0-9a-f]{40})", text, re.M)
    repo = re.search(r"get_commit ([\w.-]+/[\w.-]+) \"\$TRAINER_COMMIT\"", text)
    if commit and repo:
        found.append(Source(f"{path.relative_to(ROOT)} (commit)", f"https://github.com/{repo.group(1)}/commit/{commit.group(1)}"))
    return found


def from_dockerfile(path: Path) -> list[Source]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    refs = dict(re.findall(r"^ARG (\w+_REF)=(\S+)", text, re.M))
    found = []
    for m in re.finditer(r"git clone --quiet https://github\.com/([\w.-]+/[\w.-]+?)(?:\.git)?\s", text):
        ref = re.search(r"checkout --quiet \$\{(\w+)\}", text[m.end():])
        if ref and ref.group(1) in refs:
            found.append(Source(f"{path.relative_to(ROOT)} (commit)", f"https://github.com/{m.group(1)}/commit/{refs[ref.group(1)]}"))
    return found


def from_soundfonts(path: Path) -> list[Source]:
    if not path.exists():
        return []
    m = re.search(r'^UPSTREAM = "([^"]+)"', path.read_text(encoding="utf-8"), re.M)
    return [Source(f"{path.relative_to(ROOT)} (one sample)", f"{m.group(1)}acoustic_grand_piano-mp3/A4.mp3")] if m else []


def sources() -> list[Source]:
    found = (from_setup_ps1(ROOT / "windows" / "setup.ps1") + from_fetch_models(ROOT / "scripts" / "fetch-models.sh")
             + from_macos_setup(ROOT / "macos" / "setup.sh") + from_dockerfile(ROOT / "engine" / "Dockerfile")
             + from_soundfonts(ROOT / "app" / "soundfonts.py"))
    merged: dict[str, Source] = {}
    for s in found:   # one address may be written in several places: check it once, keep the pins it has
        if s.url in merged:
            have = merged[s.url]
            have.sha, have.size = have.sha or s.sha, have.size or s.size
            if s.where not in have.where:
                have.where += ", " + s.where
        else:
            merged[s.url] = s
    return list(merged.values())


def _hf_batch(repo: str, revision: str, paths: list[str]) -> tuple[dict[str, dict] | str, str | None]:
    """The files' entries (or why not), and the repository's new name if it has moved.

    A renamed repository answers with a redirect, which a download follows; but the old name
    can be taken by someone else at any time, so a move is worth knowing about. urllib does
    not follow a redirect for a POST, so it is followed here, once.
    """
    moved = None
    for _ in range(2):
        url = f"https://huggingface.co/api/models/{moved or repo}/paths-info/{urllib.parse.quote(revision, safe='')}"
        data = urllib.parse.urlencode([("paths", p) for p in paths]).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
                return {entry["path"]: entry for entry in json.load(r)}, moved
        except urllib.error.HTTPError as exc:
            where = re.search(r"/api/models/([\w.-]+/[\w.-]+)", exc.headers.get("Location") or "")
            if exc.code in (301, 302, 307, 308) and where and not moved:
                moved = where.group(1)
                continue
            return f"HTTP {exc.code}", moved
        except Exception as exc:  # noqa: BLE001
            return str(exc), moved
    return "no answer", moved


def _head(url: str) -> str:
    """'ok', or why not."""
    for method, headers in (("HEAD", {}), ("GET", {"Range": "bytes=0-0"})):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": "yeufonic-check", **headers})
            with urllib.request.urlopen(req, timeout=30):
                return "ok"
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 405) and method == "HEAD":
                continue   # some hosts refuse HEAD; ask for one byte instead
            return f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001
            return str(exc)
    return "no answer"


def _compare(s: Source, entry: dict) -> str:
    published = (entry.get("lfs") or {}).get("oid")
    if s.size and entry.get("size") != s.size:
        return f"DIFFERENT: {entry.get('size')} bytes, pinned {s.size}"
    if s.sha and published and published != s.sha:
        return f"DIFFERENT: sha256 {published[:12]}, pinned {s.sha[:12]}"
    return "ok" + ("" if not s.sha or published else " (size only: a small file)")


def check(found: list[Source]) -> list[tuple[Source, str]]:
    results: dict[str, str] = {}
    by_repo: dict[tuple[str, str], list[tuple[Source, str]]] = {}
    others = []
    for s in found:
        m = HF_FILE.match(s.url)
        if m:
            by_repo.setdefault((m.group(1), m.group(2)), []).append((s, urllib.parse.unquote(m.group(3))))
        else:
            others.append(s)
    for (repo, revision), items in by_repo.items():
        answer, moved = _hf_batch(repo, revision, [p for _, p in items])
        for s, p in items:
            if moved and not isinstance(answer, str) and p in answer:
                results[s.url] = f"MOVED to {moved}: " + _compare(s, answer[p]) + "; change the address"
                continue
            if isinstance(answer, str):
                results[s.url] = f"MISSING: the repository answered {answer}"
                continue
            entry = answer.get(p)
            if not entry:
                results[s.url] = "MISSING: no such file in the repository"
                continue
            results[s.url] = _compare(s, entry)
    with ThreadPoolExecutor(max_workers=8) as pool:
        for s, state in zip(others, pool.map(lambda s: _head(s.url), others)):
            results[s.url] = state if state == "ok" else f"MISSING: {state}"
    return [(s, results[s.url]) for s in found]


def main() -> int:
    found = sources()
    print()
    print(f"Download sources ({len(found)}): does each still answer, with what is pinned?")
    problems = moves = 0
    quiet = "--show-details" not in sys.argv[1:]
    for s, state in check(found):
        moved = state.startswith("MOVED") and ": ok" in state
        bad = not state.startswith("ok") and not moved
        problems += bad
        moves += moved
        if bad or moved or not quiet:
            print(f"  {'!!' if bad else '~~' if moved else 'ok'} {s.url}\n       {state}  [{s.where}]")
    if moves:
        print(f"\n{moves} sources still answer through a redirect from a renamed repository: move them to the new name.")
    if problems:
        print(f"\n{problems} of {len(found)} sources are missing or different. A fresh install that needs one of them stops.")
        return 1
    print(f"  all {len(found)} answer as pinned" + ("  (--show-details lists them)" if quiet else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
