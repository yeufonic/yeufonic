"""Is there a newer release than this build?

The app asks one small file on its own site — the manifest a release writes — and falls
back to GitHub's release for the same repository, in case the site is down.  A release
procedure that has to remember something is a release procedure that forgets, so this is
deliberately the only place that knows about either.

Nothing here may matter: one request every four hours, its own timeout, silence when it
fails, and never anything a page request waits on.  A tool that phones home loudly is worse
than one that does not check at all.  Four hours rather than a day is the compromise: a
release reaches an install the same working session, and six small requests a day to a
static file is not a cost to anyone.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

import httpx

from app import config, db

log = logging.getLogger("yue2.update")

# The manifest the site serves: a file in its public/ folder, written when a release is
# cut.  Whatever it says is what the app believes; the release API is only a fallback.
MANIFEST_URL = "https://yeufonic.com/updates.json"
RELEASE_API = "https://api.github.com/repos/yeufonic/yeufonic/releases/latest"
RELEASES_PAGE = "https://github.com/yeufonic/yeufonic/releases/latest"

TIMEOUT = 6.0
EVERY = 4 * 60 * 60           # how often the watcher wakes and asks again
USER_AGENT = "Yeufonic/" + config.VERSION + " (+https://yeufonic.com)"

# Where the last answer is kept between restarts.  Not settings: nobody chooses these.
# The whole answer is kept, not just the version, because the notice outlives the process:
# a restart in the evening must not lose the link it was offering in the afternoon.
KEY_CHECKED = "update.checked"
KEY_SEEN = "update.seen"
KEY_ANSWER = "update.answer"

def _initial() -> dict:
    """What we know before asking anything.  A function, so the state can be rebuilt:
    `config.VERSION` and the platform are read when this module is imported, and a test
    that wants a different answer builds its own."""
    return {
        "current": config.VERSION,
        "latest": None,
        "newer": False,
        "checked": 0.0,
        "notes": None,
        "installer": None,
        "sha256": None,
        "install": "windows" if sys.platform == "win32" else ("macos" if sys.platform == "darwin" else "docker"),
        "line": None,
        "seen": False,
        "error": None,
        "checking": False,
        "source": None,
        "source_url": None,
    }


# What we know now.  The page reads this; the watcher and the menu item fill it.
STATE: dict[str, Any] = _initial()


def parse_version(text: str | None) -> tuple[int, ...]:
    """`v0.0.11` and `0.0.11` are the same version; a suffix is not part of the order.
    Compared as numbers, never as text: '0.0.9' sorts after '0.0.10' as a string."""
    found = re.match(r"\s*v?(\d+(?:\.\d+)*)", str(text or ""))
    if not found:
        return ()
    return tuple(int(part) for part in found.group(1).split("."))


def is_newer(latest: str | None, mine: str | None = None) -> bool:
    """Whether the release is ahead of what is running.  A build of ours that is *ahead*
    of the last release is the normal case between a deploy and a release, and says
    nothing: only a genuinely newer release is worth telling anyone about."""
    theirs = parse_version(latest)
    ours = parse_version(mine or config.VERSION)
    if not theirs or not ours:
        return False
    return theirs > ours


def _installer_from(assets: list[dict] | None) -> tuple[str | None, str | None]:
    """The setup file and its hash, from a release's assets.  The installer is what a
    Windows or macOS user is sent to, so it is worth finding by name; anything else can fall back
    to the release page."""
    ext = ".dmg" if sys.platform == "darwin" else ".exe"
    for asset in assets or []:
        name = str(asset.get("name") or "")
        if name.lower().startswith("yeufonic-setup") and name.lower().endswith(ext):
            return asset.get("browser_download_url"), asset.get("digest") or None
    return None, None


def _from_manifest(data: dict) -> dict:
    installer = data.get("installer") or {}
    if isinstance(installer, str):                    # a plain URL is allowed too
        installer = {"url": installer}
    return {
        "latest": data.get("latest") or data.get("version"),
        "notes": data.get("notes") or data.get("notes_url") or RELEASES_PAGE,
        "installer": installer.get("url"),
        "sha256": installer.get("sha256"),
        "line": data.get("docker"),
    }


def _from_release(data: dict) -> dict:
    installer, digest = _installer_from(data.get("assets"))
    return {
        "latest": str(data.get("tag_name") or "").lstrip("v") or None,
        "notes": data.get("html_url") or RELEASES_PAGE,
        "installer": installer,
        "sha256": digest,
        "line": None,
    }


def _fetch_json(url: str) -> dict:
    """One GET, with the user agent GitHub insists on and the app's own name in it."""
    response = httpx.get(url, timeout=TIMEOUT, follow_redirects=True,
                         headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    response.raise_for_status()
    return response.json()


def _ask() -> dict:
    """The manifest first, GitHub second.  Raises if neither answers.  Which one answered
    is kept, because "is the site's manifest doing its job?" cannot be told from the answer
    alone: the fallback and the manifest can name the same version."""
    first_error: Exception | None = None
    if config.UPDATE_MANIFEST:
        sources = ((config.UPDATE_MANIFEST, _from_manifest, "test manifest"),)
    else:
        sources = ((MANIFEST_URL, _from_manifest, "yeufonic.com"),
                   (RELEASE_API, _from_release, "github"))
    for url, read, source in sources:
        try:
            answer = read(_fetch_json(url))
            answer["source"] = source
            answer["source_url"] = url
            return answer
        except Exception as exc:                       # noqa: BLE001 - any failure is the same here
            log.info("Update check: %s did not answer (%s)", url, exc)
            first_error = first_error or exc
    raise first_error or RuntimeError("no update source answered")


def advice() -> str:
    """What to do about it, in the words of the install this is running in."""
    if STATE["install"] == "windows":
        return "Run the installer over this one: your library and models are kept."
    if STATE["install"] == "macos":
        return "Open the DMG and drag Yeufonic over your existing app: your library and models are kept."
    return "Pull the new version and rebuild: " + (STATE["line"] or "git pull && docker compose up -d --build")


def state() -> dict:
    """What the page reads.  No network, nothing to wait for."""
    out = dict(STATE)
    out["line"] = out.get("line") or ("git pull && docker compose up -d --build"
                                      if out["install"] == "docker" else None)
    out["advice"] = advice()
    return out


async def check(force: bool = False, enabled: bool = True) -> dict:
    """Ask, unless it is off or recently asked.  The manual check passes force=True and
    is not subject to the setting, which governs the automatic one only."""
    if not force and not enabled:
        return state()
    if not force and STATE["checked"] and time.time() - STATE["checked"] < EVERY:
        return state()
    STATE["checking"] = True
    try:
        answer = await asyncio.to_thread(_ask)
        STATE.update(answer)
        STATE["latest"] = (answer.get("latest") or "").lstrip("v") or None
        STATE["newer"] = is_newer(STATE["latest"])
        STATE["error"] = None
        STATE["checked"] = time.time()
        db.set_setting(KEY_CHECKED, str(int(STATE["checked"])))
        db.set_setting(KEY_ANSWER, json.dumps({key: STATE[key] for key in
                                               ("latest", "notes", "installer", "sha256", "line",
                                                "source", "source_url")}))
        STATE["seen"] = (db.get_setting(KEY_SEEN) or "") == (STATE["latest"] or "")
        # One line per check, saying where it asked and what it heard: the Logs window is
        # where anyone asks "is it even looking?".
        log.info("Update check: %s says %s; this build is %s \u2014 %s",
                 STATE["source_url"] or STATE["source"] or "?", STATE["latest"], config.VERSION,
                 "a newer version is available" if STATE["newer"] else "up to date")
    except Exception as exc:                           # noqa: BLE001 - offline is normal
        STATE["error"] = str(exc) or exc.__class__.__name__
        STATE["checked"] = time.time()
        db.set_setting(KEY_CHECKED, str(int(STATE["checked"])))
        log.info("Update check: nothing answered (%s); it will try again later", STATE["error"])
    finally:
        STATE["checking"] = False
    return state()


def mark_seen(version: str | None = None) -> dict:
    """The notice has been shown and acted on, so it is not shown again for this release."""
    db.set_setting(KEY_SEEN, version or STATE["latest"] or "")
    STATE["seen"] = True
    return state()


def restore() -> None:
    """Pick up where the last run left off: what was seen and the last answer it gave,
    so a restart remembers the notice while checking for a newer release on startup."""
    STATE["checked"] = 0.0
    try:
        remembered = json.loads(db.get_setting(KEY_ANSWER) or "{}")
    except ValueError:
        remembered = {}
    for key in ("latest", "notes", "installer", "sha256", "line", "source", "source_url"):
        if key in remembered:
            STATE[key] = remembered[key]
    STATE["latest"] = (STATE["latest"] or "").lstrip("v") or None
    STATE["newer"] = is_newer(STATE["latest"])
    STATE["seen"] = bool(STATE["latest"]) and (db.get_setting(KEY_SEEN) or "") == STATE["latest"]


async def watcher(enabled) -> None:
    """Ask at startup and then daily.  `enabled` is called each time, so the setting can
    be changed without a restart."""
    restore()
    while True:
        try:
            await check(force=False, enabled=bool(enabled()))
        except asyncio.CancelledError:
            raise
        except Exception as exc:                       # noqa: BLE001 - a watcher never dies
            log.warning("Update watcher: %s", exc)
        await asyncio.sleep(EVERY)


def get_downloads_dir() -> Path:
    """The user's Downloads folder on Windows, or ~/Downloads across platforms."""
    if sys.platform == "win32":
        try:
            import winreg

            # Known folder GUID for User Shell Folders 'Downloads' is {374DE290-123F-4565-9164-39C4925E467B}
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            ) as key:
                val, _ = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")
                p = Path(os.path.expandvars(val))
                if p.exists():
                    return p
        except Exception:
            pass
    p = Path.home() / "Downloads"
    p.mkdir(parents=True, exist_ok=True)
    return p


DOWNLOAD_STATE: dict[str, Any] = {
    "status": "idle",  # "idle" | "downloading" | "done" | "error"
    "progress": 0.0,
    "downloaded_bytes": 0,
    "total_bytes": 0,
    "filename": "",
    "path": "",
    "error": None,
}
_download_task: asyncio.Task | None = None


def download_state() -> dict[str, Any]:
    return dict(DOWNLOAD_STATE)


async def start_download() -> dict[str, Any]:
    """Start streaming the installer to the Downloads folder with SHA-256 validation."""
    global _download_task
    if _download_task and not _download_task.done():
        return download_state()

    installer_url = STATE.get("installer")
    if not installer_url:
        raise ValueError("No installer URL available for this update")

    version = STATE.get("latest") or ""
    ext = ".dmg" if sys.platform == "darwin" else ".exe"
    filename = (
        f"Yeufonic-Setup-{version}{ext}"
        if version
        else Path(urllib.parse.urlsplit(installer_url).path).name or f"Yeufonic-Setup{ext}"
    )
    downloads = get_downloads_dir()
    target_path = downloads / filename
    part_path = downloads / f"{filename}.part"
    expected_hash = str(STATE.get("sha256") or "").replace("sha256:", "").strip().lower()

    # If the installer was already downloaded and matches the expected hash, reuse it
    if target_path.is_file() and expected_hash:
        try:
            hasher = hashlib.sha256()
            with target_path.open("rb") as f:
                while chunk := f.read(1024 * 1024):
                    hasher.update(chunk)
            if hasher.hexdigest().lower() == expected_hash:
                size = target_path.stat().st_size
                DOWNLOAD_STATE.update({
                    "status": "done",
                    "progress": 1.0,
                    "downloaded_bytes": size,
                    "total_bytes": size,
                    "filename": filename,
                    "path": str(target_path),
                    "error": None,
                })
                return download_state()
        except Exception:
            pass

    DOWNLOAD_STATE.update({
        "status": "downloading",
        "progress": 0.0,
        "downloaded_bytes": 0,
        "total_bytes": 0,
        "filename": filename,
        "path": "",
        "error": None,
    })

    async def _runner():
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=httpx.Timeout(15.0, read=60.0)) as client:
                async with client.stream("GET", installer_url, headers={"User-Agent": USER_AGENT}) as resp:
                    resp.raise_for_status()
                    total = int(resp.headers.get("content-length") or 0)
                    DOWNLOAD_STATE["total_bytes"] = total
                    DOWNLOAD_STATE["downloaded_bytes"] = 0
                    hasher = hashlib.sha256()
                    with part_path.open("wb") as f:
                        async for chunk in resp.aiter_bytes(chunk_size=128 * 1024):
                            f.write(chunk)
                            hasher.update(chunk)
                            DOWNLOAD_STATE["downloaded_bytes"] += len(chunk)
                            if total > 0:
                                DOWNLOAD_STATE["progress"] = min(1.0, DOWNLOAD_STATE["downloaded_bytes"] / total)

            actual_hash = hasher.hexdigest().lower()
            if expected_hash and actual_hash != expected_hash:
                part_path.unlink(missing_ok=True)
                raise ValueError(f"Checksum mismatch: expected {expected_hash}, got {actual_hash}")

            if target_path.exists():
                target_path.unlink(missing_ok=True)
            part_path.replace(target_path)
            DOWNLOAD_STATE.update({
                "status": "done",
                "progress": 1.0,
                "path": str(target_path),
                "error": None,
            })
            log.info("Downloaded and verified update installer to %s", target_path)
        except asyncio.CancelledError:
            part_path.unlink(missing_ok=True)
            DOWNLOAD_STATE.update({
                "status": "idle",
                "progress": 0.0,
                "error": None,
            })
            raise
        except Exception as exc:
            part_path.unlink(missing_ok=True)
            log.warning("Update installer download failed: %s", exc)
            DOWNLOAD_STATE.update({
                "status": "error",
                "error": str(exc) or exc.__class__.__name__,
            })

    _download_task = asyncio.create_task(_runner())
    return download_state()


def cancel_download() -> dict[str, Any]:
    global _download_task
    if _download_task and not _download_task.done():
        _download_task.cancel()
    filename = DOWNLOAD_STATE.get("filename")
    if filename:
        part_path = get_downloads_dir() / f"{filename}.part"
        part_path.unlink(missing_ok=True)
    DOWNLOAD_STATE.update({
        "status": "idle",
        "progress": 0.0,
        "error": None,
    })
    return download_state()


CREATE_BREAKAWAY_FROM_JOB = 0x01000000
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200


def launch_installer() -> bool:
    """Launch the installer executable on Windows."""
    path_str = DOWNLOAD_STATE.get("path")
    if not path_str or not Path(path_str).is_file():
        filename = DOWNLOAD_STATE.get("filename") or (
            f"Yeufonic-Setup-{STATE['latest']}.exe" if STATE.get("latest") else None
        )
        if filename:
            candidate = get_downloads_dir() / filename
            if candidate.is_file():
                path_str = str(candidate)
    if not path_str or not Path(path_str).is_file():
        return False
    if sys.platform == "win32":
        # The launcher keeps everything it starts in a job that ends with it, and the app is in
        # that job.  An installer started the ordinary way would be in it too, and would be
        # ended the moment Yeufonic is closed, which is what it asks the person to do.  The job
        # allows a program to break away, so the installer is started outside it.
        flags = CREATE_BREAKAWAY_FROM_JOB | DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        try:
            subprocess.Popen([path_str], creationflags=flags, close_fds=True,
                             cwd=str(Path(path_str).parent))
            return True
        except OSError as exc:
            log.warning("Could not start the installer outside the app's job (%s); starting it normally. "
                        "If it stops when Yeufonic closes, run it from the Downloads folder.", exc)
    if sys.platform == "win32" and hasattr(os, "startfile"):
        try:
            os.startfile(path_str)
            return True
        except Exception as exc:
            log.warning("Could not launch installer: %s", exc)
            raise
    if sys.platform == "darwin":
        try:
            subprocess.Popen(["open", path_str])
            return True
        except Exception as exc:
            log.warning("Could not open macOS installer DMG: %s", exc)
            raise
    return False


def reveal_installer() -> bool:
    """Reveal the downloaded installer in Windows Explorer or macOS Finder."""
    path_str = DOWNLOAD_STATE.get("path")
    if not path_str or not Path(path_str).is_file():
        ext = ".dmg" if sys.platform == "darwin" else ".exe"
        filename = DOWNLOAD_STATE.get("filename") or (
            f"Yeufonic-Setup-{STATE['latest']}{ext}" if STATE.get("latest") else None
        )
        if filename:
            candidate = get_downloads_dir() / filename
            if candidate.is_file():
                path_str = str(candidate)
    if not path_str or not Path(path_str).is_file():
        return False
    if sys.platform == "win32":
        try:
            subprocess.Popen(["explorer.exe", f"/select,{path_str}"])
            return True
        except Exception as exc:
            log.warning("Could not reveal installer: %s", exc)
            raise
    if sys.platform == "darwin":
        try:
            subprocess.Popen(["open", "-R", path_str])
            return True
        except Exception as exc:
            log.warning("Could not reveal installer in Finder: %s", exc)
            raise
    return False

