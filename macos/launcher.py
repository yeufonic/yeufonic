"""Start Yeufonic on macOS: the engine (ComfyUI) and the app together, then the page
in your browser as soon as the app answers.

Designed for Apple Silicon (M1/M2/M3/M4) running Metal Performance Shaders (MPS).
Closing the browser leaves Yeufonic running in the terminal or background.
Pressing Ctrl+C ends both processes cleanly.

Logs are written to ~/Library/Logs/Yeufonic/ (or logs/ beside the app).
Settings are read from ~/Library/Application Support/Yeufonic/settings.ini.
"""
from __future__ import annotations

import configparser
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE / "studio" if (HERE / "studio").exists() else HERE.parent

# Standard macOS user directories
APP_SUPPORT = Path.home() / "Library" / "Application Support" / "Yeufonic"
DEFAULT_DATA = APP_SUPPORT / "data"
LOGS = Path.home() / "Library" / "Logs" / "Yeufonic"
ENGINE = HERE / "engine" if (HERE / "engine").exists() else HERE / "ComfyUI"
COMFY = ENGINE / "ComfyUI" if (ENGINE / "ComfyUI").exists() else ENGINE

APP = "Yeufonic"
CONSOLE = "--console" in sys.argv[1:]


def settings() -> dict:
    """Read configuration from settings.ini or defaults."""
    values = {
        "app_port": "8090",
        "engine_port": "8188",
        "engine_args": "--force-fp16 --disable-pinned-memory",
        "data_dir": str(DEFAULT_DATA),
        "import_roots": str(Path.home() / "Music"),
        "open_browser": "yes"
    }
    ini_paths = [
        APP_SUPPORT / "settings.ini",
        HERE / "settings.ini",
        STUDIO / "settings.ini"
    ]
    for ini in ini_paths:
        if ini.exists():
            parser = configparser.ConfigParser()
            parser.read(ini, encoding="utf-8")
            if parser.has_section("yue2"):
                values.update({k: v for k, v in parser.items("yue2") if v.strip()})
            break
    return values


def say(line: str) -> None:
    if sys.stdout:
        print(line, flush=True)


def record(line: str) -> None:
    say(line)
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        with (LOGS / "launcher.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {line}\n")
    except OSError:
        pass


def answering(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1) as reply:
            return reply.status == 200
    except OSError:
        return False


def find_python() -> tuple[Path | None, Path | None]:
    """Find the app virtualenv python and engine python."""
    app_py = None
    engine_py = None

    candidates_app = [
        HERE / "venv" / "bin" / "python",
        HERE / "python" / "bin" / "python3",
        STUDIO / "venv" / "bin" / "python",
        Path.home() / ".local" / "share" / "yeufonic" / "venv" / "bin" / "python"
    ]
    for c in candidates_app:
        if c.exists() and os.access(c, os.X_OK):
            app_py = c
            break

    candidates_engine = [
        ENGINE / "python_embeded" / "bin" / "python",
        HERE / "python_embeded" / "bin" / "python",
        app_py  # Fallback to app's python if unified
    ]
    for c in candidates_engine:
        if c and c.exists() and os.access(c, os.X_OK):
            engine_py = c
            break

    if not app_py:
        app_py = Path(sys.executable)
    if not engine_py:
        engine_py = app_py

    return app_py, engine_py


class MacOSLauncher:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.app_port = int(cfg["app_port"])
        self.engine_port = int(cfg["engine_port"])
        self.url = f"http://127.0.0.1:{self.app_port}"
        self.app_url = f"{self.url}/api/health"
        self.engine_url = f"http://127.0.0.1:{self.engine_port}/system_stats"
        self.programs: list[tuple[str, subprocess.Popen, Path]] = []
        self.app_ready = False
        self.engine_ready = False
        self.quitting = False
        self.started = 0.0

    def start(self) -> None:
        LOGS.mkdir(parents=True, exist_ok=True)
        data_dir = Path(self.cfg["data_dir"])
        data_dir.mkdir(parents=True, exist_ok=True)

        app_py, engine_py = find_python()
        record(f"Starting {APP} on macOS (Apple Silicon MPS)...")
        record(f"App Python: {app_py}")
        record(f"Engine Python: {engine_py}")

        self.started = time.time()

        # 1. Start Engine (ComfyUI with MPS)
        comfy_main = COMFY / "main.py"
        if comfy_main.exists() and engine_py:
            engine_log = LOGS / "engine.log"
            engine_args = self.cfg.get("engine_args", "").split()
            cmd = [
                str(engine_py), str(comfy_main),
                "--listen", "127.0.0.1",
                "--port", str(self.engine_port),
            ] + engine_args
            log_fh = engine_log.open("a", encoding="utf-8")
            env = dict(os.environ)
            env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
            env["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
            p = subprocess.Popen(cmd, stdout=log_fh, stderr=log_fh, env=env, cwd=str(COMFY.parent))
            self.programs.append(("Engine", p, engine_log))
            record(f"Spawned engine process (PID {p.pid}).")
        else:
            record("Engine not found locally; expecting external or Docker engine.")

        # 2. Start App (FastAPI)
        app_log = LOGS / "app.log"
        app_log_fh = app_log.open("a", encoding="utf-8")
        app_env = dict(os.environ)
        app_env["PORT"] = str(self.app_port)
        app_env["DATA_DIR"] = str(data_dir)
        app_env["ENGINE_URL"] = f"http://127.0.0.1:{self.engine_port}"
        app_env["PYTHONUNBUFFERED"] = "1"

        app_cmd = [
            str(app_py), "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1",
            "--port", str(self.app_port)
        ]
        p_app = subprocess.Popen(app_cmd, stdout=app_log_fh, stderr=app_log_fh, env=app_env, cwd=str(STUDIO))
        self.programs.append(("App", p_app, app_log))
        record(f"Spawned app process (PID {p_app.pid}).")

        # Setup signal handling
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        self.loop()

    def handle_signal(self, signum, _frame) -> None:
        record(f"Received signal {signum}. Stopping...")
        self.stop()
        sys.exit(0)

    def busy(self) -> str:
        """Check if generation or training is underway."""
        try:
            with urllib.request.urlopen(f"{self.url}/api/state", timeout=1) as reply:
                state = json.load(reply)
                if state.get("training"):
                    return "A LoRA model is currently training."
                if state.get("current") or state.get("queue"):
                    return "An audio generation job is currently running."
        except Exception:
            pass
        return ""

    def stop(self) -> None:
        if self.quitting:
            return
        self.quitting = True

        warning = self.busy()
        if warning:
            record(f"Warning: {warning}")

        record("Shutting down processes...")
        for name, p, _ in self.programs:
            if p.poll() is None:
                record(f"Stopping {name} (PID {p.pid})...")
                p.terminate()

        deadline = time.time() + 3.0
        for name, p, _ in self.programs:
            while p.poll() is None and time.time() < deadline:
                time.sleep(0.1)
            if p.poll() is None:
                record(f"Force-killing {name}...")
                p.kill()

        record("All processes stopped.")

    def loop(self) -> None:
        while not self.quitting:
            time.sleep(0.5)
            now = time.time()

            # Check health of child processes
            for name, p, log_path in self.programs:
                if p.poll() is not None:
                    record(f"Error: {name} exited unexpectedly with code {p.returncode}. See {log_path}")
                    self.stop()
                    sys.exit(1)

            # Check app readiness
            if not self.app_ready:
                if answering(self.app_url):
                    self.app_ready = True
                    record(f"App ready in {now - self.started:.1f} s.")
                    if self.cfg.get("open_browser", "yes").lower() != "no":
                        record(f"Opening browser at {self.url}...")
                        webbrowser.open(self.url)
                elif now - self.started > 180:
                    record("Error: App failed to respond within 3 minutes.")
                    self.stop()
                    sys.exit(1)

            # Check engine readiness
            if not self.engine_ready:
                if answering(self.engine_url):
                    self.engine_ready = True
                    record(f"Engine ready in {now - self.started:.1f} s.")
                elif now - self.started > 300:
                    record("Warning: Engine took longer than 5 minutes to respond.")


def main() -> None:
    cfg = settings()
    launcher = MacOSLauncher(cfg)
    try:
        launcher.start()
    except KeyboardInterrupt:
        launcher.stop()


if __name__ == "__main__":
    main()
