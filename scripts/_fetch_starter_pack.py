#!/usr/bin/env python3
"""Download and stage the Yeufonic Starter Pack for Docker installs.

Called by ``scripts/fetch-models.sh --demos`` (using only Python 3's standard
library and ``curl``).

1. Fetches ``<STARTER_PACK_URL>/manifest.json`` (default
   ``https://yeufonic.com/starter-pack``).
2. Downloads any referenced style LoRAs not already in ``<root>/models/loras/``
   with resumable ``curl -C -`` and SHA-256 verification.
3. Downloads any referenced voices not already present in ``<root>/data/voices/``
   or ``<root>/data/yue2.sqlite`` (matched by id or name) into
   ``<root>/data/starter-pack/voices/<id>/``.
4. Downloads ``starter-pack.zip`` (unless this pack_id is already installed in
   a non-empty Starter Pack space), verifies its SHA-256, and extracts it into
   ``<root>/data/starter-pack/``.
5. If Yeufonic is already running on localhost, triggers
   ``POST /api/starter-pack/install`` so the space appears immediately;
   otherwise leaves ``data/starter-pack/`` staged for automatic import on next
   startup.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

DEFAULT_URL = "https://media.yeufonic.com/starter-pack"
FALLBACK_URL = "https://huggingface.co/pshields/yeufonic-starter-pack/resolve/main"
MANIFEST_FORMAT = "yeufonic-starter-pack-manifest"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_url_bytes(url: str, timeout: int = 30) -> bytes:
    if shutil.which("curl"):
        res = subprocess.run(
            ["curl", "-fsSL", "--retry", "3", "--connect-timeout", "15", url],
            capture_output=True,
        )
        if res.returncode == 0:
            return res.stdout
        err = res.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"failed to fetch {url}: {err or f'curl exit {res.returncode}'}")
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


def fetch_file(
    url: str,
    dest: Path,
    expected_sha: str | None = None,
    label: str | None = None,
    fallback_url: str | None = None,
) -> bool:
    """Download ``url`` to ``dest`` (trying ``fallback_url`` if the primary fails).

    Returns True if the fallback URL was used, False otherwise.
    """
    name = label or dest.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 0:
        if not expected_sha or sha256_file(dest) == expected_sha:
            print(f"have  {name}")
            return False
        print(f"note  {name} checksum mismatch; re-downloading", file=sys.stderr)
        dest.unlink(missing_ok=True)

    sources = [url] + ([fallback_url] if fallback_url and fallback_url != url else [])
    last_err: Exception | None = None
    for idx, src_url in enumerate(sources):
        print(f"fetch {name}" + (" (fallback mirror)" if idx > 0 else ""))
        part = dest.with_name(dest.name + ".part")
        try:
            if shutil.which("curl"):
                retries = "3" if len(sources) > 1 and idx == 0 else "5"
                cmd = ["curl", "-L", "--fail", "--retry", retries, "--retry-all-errors", "-C", "-", "-o", str(part), src_url]
                res = subprocess.run(cmd)
                if res.returncode != 0:
                    raise RuntimeError(f"download failed for {src_url} (curl exit {res.returncode})")
            else:
                with urllib.request.urlopen(src_url, timeout=120) as resp, part.open("wb") as out:
                    shutil.copyfileobj(resp, out)

            if expected_sha:
                got = sha256_file(part)
                if got != expected_sha:
                    part.unlink(missing_ok=True)
                    raise RuntimeError(
                        f"{name} did not match its published checksum; removed so the next run fetches it again"
                    )
            part.replace(dest)
            return idx > 0
        except Exception as exc:
            part.unlink(missing_ok=True)
            last_err = exc
            if idx + 1 < len(sources):
                print(f"note  could not download {name} from {src_url}; trying fallback mirror", file=sys.stderr)
    assert last_err is not None
    raise last_err


def _existing_voices(data_dir: Path) -> tuple[set[str], set[str]]:
    """Return (ids, lower_names) of voices already present on disk or in SQLite."""
    ids: set[str] = set()
    names: set[str] = set()
    voices_dir = data_dir / "voices"
    if voices_dir.is_dir():
        for d in voices_dir.iterdir():
            if d.is_dir() and (d / "model.pth").is_file():
                ids.add(d.name)
    db_path = data_dir / "yue2.sqlite"
    if db_path.is_file():
        try:
            con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            try:
                for vid, name in con.execute("SELECT id, name FROM voices"):
                    if vid:
                        ids.add(str(vid))
                    if name:
                        names.add(str(name).strip().lower())
            finally:
                con.close()
        except sqlite3.Error:
            pass
    return ids, names


def _already_installed(data_dir: Path, pack_id: str, space_name: str) -> bool:
    """True if this exact pack_id is recorded in settings and its space still has takes."""
    if not pack_id:
        return False
    db_path = data_dir / "yue2.sqlite"
    if not db_path.is_file():
        return False
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            row = con.execute(
                "SELECT value FROM settings WHERE key = 'starter_pack.installed'"
            ).fetchone()
            if not row or not row[0]:
                return False
            info = json.loads(row[0])
            if info.get("pack_id") != pack_id:
                return False
            sp = con.execute(
                "SELECT id FROM spaces WHERE LOWER(name) = LOWER(?)", (space_name,)
            ).fetchone()
            if not sp:
                return False
            cnt = con.execute("SELECT COUNT(*) FROM takes WHERE space_id = ?", (sp[0],)).fetchone()[0]
            return cnt > 0
        finally:
            con.close()
    except (sqlite3.Error, ValueError, TypeError):
        return False


def _read_app_port(root: Path) -> int:
    env_file = root / ".env"
    if env_file.is_file():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\s*PORT\s*=\s*(\d+)\s*$", line)
                if m:
                    return int(m.group(1))
        except OSError:
            pass
    try:
        return int(os.environ.get("PORT", "8090"))
    except ValueError:
        return 8090


def _trigger_live_install(port: int) -> dict[str, Any] | None:
    url = f"http://127.0.0.1:{port}/api/starter-pack/install"
    req = urllib.request.Request(url, method="POST", data=b"")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None
    return None


def _safe_extract_zip(zip_path: Path, dest_dir: Path) -> None:
    dest_res = dest_dir.resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            target = (dest_res / member.filename).resolve()
            try:
                target.relative_to(dest_res)
            except ValueError as exc:
                raise RuntimeError(f"Unsafe path in Starter Pack archive: {member.filename}") from exc
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member, "r") as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)


def fetch_starter_pack(
    root: Path,
    base_url: str = DEFAULT_URL,
    *,
    fallback_url: str | None = None,
    trigger_live: bool = True,
) -> dict[str, Any]:
    active_base = base_url.rstrip("/")
    if fallback_url is None:
        fallback = FALLBACK_URL.rstrip("/") if active_base == DEFAULT_URL.rstrip("/") else ""
    else:
        fallback = fallback_url.rstrip("/")
    if fallback == active_base:
        fallback = ""

    def _download(rel_path: str, dest: Path, expected_sha: str | None, label: str) -> None:
        nonlocal active_base, fallback
        quoted = urllib.parse.quote(rel_path.lstrip("/"), safe="/")
        fb_url = f"{fallback}/{quoted}" if fallback else None
        used_fb = fetch_file(f"{active_base}/{quoted}", dest, expected_sha=expected_sha, label=label, fallback_url=fb_url)
        if used_fb and fallback:
            active_base = fallback
            fallback = ""

    manifest_url = f"{active_base}/manifest.json"
    print(f"fetch Starter Pack manifest ({manifest_url})")
    try:
        raw = fetch_url_bytes(manifest_url)
    except Exception:
        if not fallback:
            raise
        active_base = fallback
        fallback = ""
        manifest_url = f"{active_base}/manifest.json"
        print(f"note  primary manifest unreachable; trying fallback ({manifest_url})", file=sys.stderr)
        raw = fetch_url_bytes(manifest_url)
    manifest = json.loads(raw.decode("utf-8"))
    if not isinstance(manifest, dict) or manifest.get("format") != MANIFEST_FORMAT:
        raise RuntimeError(f"Unexpected Starter Pack manifest at {manifest_url}")

    models_loras = root / "models" / "loras"
    data_dir = root / "data"
    stage_dir = data_dir / "starter-pack"
    models_loras.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. LoRAs: place directly into models/loras/ if not already present (never overwrite user files)
    loras_fetched = 0
    for item in manifest.get("loras") or []:
        fname = Path(item["file"]).name
        dest = models_loras / fname
        if dest.is_file() and dest.stat().st_size > 0:
            print(f"have  {fname}")
            continue
        _download(item["path"], dest, item.get("sha256"), fname)
        loras_fetched += 1

    pack_id = str(manifest.get("pack_id") or "")
    space_name = str(manifest.get("space_name") or "Starter Pack")
    if _already_installed(data_dir, pack_id, space_name):
        print(f"have  {space_name} ({pack_id})")
        return {"skipped_bundle": True, "pack_id": pack_id, "loras_fetched": loras_fetched}

    # 2. Voices: download only if not already present by id or name
    have_ids, have_names = _existing_voices(data_dir)
    voices_fetched = 0
    for voice in manifest.get("voices") or []:
        vid = str(voice.get("id") or "").strip()
        vname = str(voice.get("name") or "").strip()
        if not vid:
            continue
        if vid in have_ids or (vname and vname.lower() in have_names):
            print(f"have  voice {vname or vid}")
            continue
        for fitem in voice.get("files") or []:
            rel_dest = Path(fitem["dest"]).name
            dest = stage_dir / "voices" / vid / rel_dest
            _download(fitem["path"], dest, fitem.get("sha256"), f"{vname or vid}/{rel_dest}")
            voices_fetched += 1

    # 3. Core Starter Pack zip bundle(s) (takes audio/peaks, artwork, cover sources, pack.json)
    bundles = manifest.get("bundles") or ([manifest["bundle"]] if manifest.get("bundle") else [])
    for bundle in bundles:
        bundle_path = str(bundle.get("path") or "starter-pack.zip")
        zip_name = Path(bundle_path).name
        zip_dest = stage_dir / zip_name
        _download(bundle_path, zip_dest, bundle.get("sha256"), zip_name)
        _safe_extract_zip(zip_dest, stage_dir)
        zip_dest.unlink(missing_ok=True)

    # 4. If Yeufonic is already running, trigger immediate import; else wait for next start.
    live_result = None
    if trigger_live:
        port = _read_app_port(root)
        live_result = _trigger_live_install(port)
        if live_result and live_result.get("installed"):
            print(
                f"installed {live_result['space_name']}: "
                f"{live_result['takes_added']} takes, "
                f"{live_result['voices_added']} voices, "
                f"{live_result['sources_added']} sources"
            )
        else:
            print(
                f"staged {space_name} in data/starter-pack/ — "
                "it will be imported automatically when Yeufonic starts."
            )

    return {
        "skipped_bundle": False,
        "pack_id": pack_id,
        "loras_fetched": loras_fetched,
        "voices_fetched": voices_fetched,
        "live_result": live_result,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch and stage the Yeufonic Starter Pack.")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent, help="Yeufonic repo root")
    ap.add_argument("--url", default=os.environ.get("STARTER_PACK_URL", DEFAULT_URL), help="Base URL of Starter Pack R2 folder")
    ap.add_argument(
        "--fallback-url",
        default=os.environ.get("STARTER_PACK_FALLBACK_URL"),
        help="Fallback mirror base URL (defaults to Hugging Face when --url is the default R2 URL)",
    )
    ap.add_argument("--no-live", action="store_true", help="Do not attempt to ping a running Yeufonic server")
    args = ap.parse_args(argv)
    try:
        fetch_starter_pack(
            args.root.resolve(),
            base_url=args.url,
            fallback_url=args.fallback_url,
            trigger_live=not args.no_live,
        )
    except Exception as exc:
        print(f"error: Starter Pack: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
