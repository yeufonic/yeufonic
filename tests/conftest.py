"""Every test gets a fresh data folder.  The engine URL points at a closed port, so
the app starts with the engine offline, which is also a test of that path."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_BOOT = tempfile.mkdtemp(prefix="yue2-test-")
os.environ.update({
    "DATA_DIR": _BOOT,
    "VERSION_FILE": str(ROOT / "VERSION"),
    "ENGINE_URL": "http://127.0.0.1:9",
    "ALLOWED_HOSTS": "localhost,127.0.0.1,testserver",
    "MAX_UPLOAD_MB": "1",
})
sys.path.insert(0, str(ROOT))

from app import config  # noqa: E402


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "yue2.sqlite")
    monkeypatch.setattr(config, "STEMS_DIR", tmp_path / "stems")
    monkeypatch.setattr(config, "TAKES_DIR", tmp_path / "takes")
    monkeypatch.setattr(config, "SOURCES_DIR", tmp_path / "sources")
    monkeypatch.setattr(config, "WORK_DIR", tmp_path / "tmp")
    monkeypatch.setattr(config, "CORPUS_INBOX", tmp_path / "corpus")
    from app import db, llm
    db._settings_cache.clear()
    llm.reset_session_state()
    db.migrate()
    yield tmp_path


@pytest.fixture(autouse=True)
def no_update_traffic(monkeypatch):
    """The app starts a task that asks yeufonic.com for the current release.  Left alone it
    makes this suite talk to the internet and — worse — changes the answer underneath a test
    that is checking it, which is how four of them came to fail the day the manifest went
    live.  The task waits instead, and the one place that fetches is closed, so a test that
    forgets to stub it fails loudly rather than quietly asking the real site."""
    from app import update

    async def idle(enabled):
        return None

    def offline(url):
        raise OSError("the update check is closed in tests")

    monkeypatch.setattr(update, "watcher", idle)
    monkeypatch.setattr(update, "_fetch_json", offline)


@pytest.fixture
def client(data_dir, monkeypatch):
    """The app, with its GPU job worker held back.  A test reads the queue to see what
    a request asked for, and a live worker races it: it took the job first whenever
    it was free to, so such a test passed or failed by the order tests ran in."""
    import asyncio
    from fastapi.testclient import TestClient
    from app import jobs
    from app.main import app
    monkeypatch.setattr(jobs, "worker", lambda: asyncio.sleep(3600))

    def empty():   # with no worker, what one test queued would be the next one's
        while not jobs.QUEUE.empty():
            jobs.QUEUE.get_nowait()
        jobs.ART_WAITING.clear()
    empty()
    with TestClient(app, base_url="http://localhost") as test_client:
        yield test_client
    empty()


def make_take(**fields):
    import time
    import uuid
    from app.db import execute
    take = {
        "id": uuid.uuid4().hex[:12], "kind": "song", "source_id": None, "title": "Test song",
        "style": "rock", "lyrics": "[Verse]\nla la", "abc": "", "mode": "full", "seed": 1,
        "checkpoint": "yue2_3b_bf16.safetensors", "max_duration": 60, "status": "done",
        "created_at": time.time(), "audio_path": None,
    }
    take.update(fields)
    cols = ", ".join(take.keys())
    vals = ", ".join(f":{k}" for k in take.keys())
    execute(f"INSERT INTO takes({cols}) VALUES({vals})", take)
    return take


_TONE_CACHE: dict[tuple[str, float], Path] = {}


def tone(path: Path, seconds: float = 2.0) -> Path:
    import array
    import math
    import shutil
    import subprocess
    import wave

    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower()
    key = (ext, float(seconds))
    cached = _TONE_CACHE.get(key)
    if cached is not None and cached.exists():
        shutil.copyfile(cached, path)
        return path

    if ext == ".wav":
        rate = 44100
        total_frames = max(1, int(round(rate * seconds)))
        period = 100  # 441 Hz (exact 100-sample period at 44.1 kHz)
        one_cycle = array.array(
            "h",
            [int(16000.0 * math.sin(2.0 * math.pi * i / period)) for i in range(period)],
        )
        full_cycles, rem = divmod(total_frames, period)
        pcm = one_cycle.tobytes() * full_cycles + one_cycle[:rem].tobytes()
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(pcm)
    else:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
             "-ar", "44100", str(path)],
            check=True,
        )

    cache_file = Path(_BOOT) / f"tone_{abs(hash(key))}{ext}"
    try:
        shutil.copyfile(path, cache_file)
        _TONE_CACHE[key] = cache_file
    except OSError:
        pass
    return path


def extract_js_function(source: str, func_Declaration: str) -> str:
    """Return a brace-balanced slice starting at `func_Declaration` in `source`."""
    start = source.index(func_Declaration)
    brace_open = source.index("{", start)
    depth = 0
    in_str = None
    escaped = False
    for idx in range(brace_open, len(source)):
        ch = source[idx]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in ("'", '"', "`"):
            in_str = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[start : idx + 1]
    return source[start:]
