"""The engine image's entry point: checks the NVIDIA driver can run this image's PyTorch, then starts ComfyUI.

A PyTorch built for CUDA 13 (the image built with TORCH_CUDA=cu130) needs a driver that supports CUDA 13.  On an older
one, ComfyUI fails as it starts, and Docker starts it again every few seconds, so the app only ever sees the engine
offline.  Here the driver's CUDA version is read first, straight from libcuda, and when it is too old the reason is
written where the app reads it (engine-start.json in the engine's output folder) and the container waits rather than
going round again.  A driver that will do, or anything this check cannot read, starts the command as it was given: the
check never stands in the way of an engine that could run.
"""
from __future__ import annotations

import ctypes
import importlib.util
import json
import os
import re
import signal
import sys
import time
from pathlib import Path

NOTE = Path(os.environ.get("ENGINE_START_NOTE", "/app/output/yeufonic/engine-start.json"))


def torch_cuda() -> str | None:
    """The CUDA version this image's PyTorch was built for, e.g. "13.0", read from its version.py without importing it
    (importing torch takes seconds, and this runs before every start)."""
    spec = importlib.util.find_spec("torch")
    if not spec or not spec.origin:
        return None
    found = re.search(r"^cuda\s*(?::\s*\S+)?\s*=\s*['\"]([\d.]+)['\"]", (Path(spec.origin).parent / "version.py").read_text(),
                      re.M)
    return found.group(1) if found else None


def driver_cuda() -> str | None:
    """The newest CUDA version the installed driver supports, e.g. "12.8"; None when there is no driver to ask."""
    try:
        cuda = ctypes.CDLL("libcuda.so.1")
    except OSError:
        return None
    version = ctypes.c_int(0)
    if cuda.cuDriverGetVersion(ctypes.byref(version)) != 0 or version.value <= 0:
        return None
    return f"{version.value // 1000}.{version.value % 1000 // 10}"


def problem(built: str | None, driver: str | None) -> dict | None:
    """What stops this PyTorch running, or None.  Within one major version a newer CUDA runs on an older driver
    (CUDA's minor version compatibility), so only the major version is compared."""
    if not built or not driver:
        return None
    if int(driver.split(".")[0]) >= int(built.split(".")[0]):
        return None
    return {"problem": "driver", "driver_cuda": driver, "torch_cuda": built, "at": time.time(),
            "message": f"The NVIDIA driver supports CUDA {driver}, and this engine needs CUDA {built}. Update the driver, "
                       "or put TORCH_CUDA=cu128 in .env and rebuild the engine (docker compose up -d --build)."}


def wait() -> None:
    """Stay up without starting anything, until Docker stops the container (as PID 1, a signal with no handler is
    ignored, so a stop would otherwise wait out its timeout)."""
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: sys.exit(0))
    while True:
        signal.pause()


def main(argv: list[str]) -> None:
    command = argv or ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
    found = None
    if "--cpu" not in command:
        try:
            found = problem(torch_cuda(), driver_cuda())
        except Exception as exc:  # noqa: BLE001
            print(f"[yeufonic] driver check skipped: {exc}", flush=True)
    try:
        if found:
            NOTE.parent.mkdir(parents=True, exist_ok=True)
            NOTE.write_text(json.dumps(found), encoding="utf-8")
            NOTE.chmod(0o644)
        elif NOTE.exists():
            NOTE.unlink()
    except OSError as exc:
        print(f"[yeufonic] {NOTE}: {exc}", flush=True)
    if found:
        print("[yeufonic] The engine cannot start. " + found["message"], flush=True)
        wait()
    os.execvp(command[0], command)


if __name__ == "__main__":
    main(sys.argv[1:])
