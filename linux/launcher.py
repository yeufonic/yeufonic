"""Start Yeufonic on Linux: the engine (ComfyUI or yue2.cpp, on an NVIDIA GPU) and the app
together, and open the page in the browser as soon as the app answers. The native Linux
counterpart of windows/launcher.py and macos/launcher.py.

Zero GUI toolkit dependencies (pure Python standard library), so it runs identically across
Ubuntu/Debian, Red Hat/Fedora/Rocky/AlmaLinux, Arch, openSUSE, headless servers, and WSL2.

The install lives in ~/.local/share/yeufonic (YEUFONIC_HOME moves it), its logs in
$YEUFONIC_HOME/logs (YEUFONIC_LOGS moves them), and settings.ini there overrides:

    [yue2]
    app_port = 8090
    engine_port = 8188
    engine_args =
    data_dir = ~/.local/share/yeufonic/data
    import_roots = ~
    open_browser = yes
    window = browser
    unload_when_idle = auto
    training = yes
    model = bf16
    voice_port = 8190
    engine = comfyui
    gemma_port = 11435
    pictures_port = 8187
    gemma_model = gemma4:e4b-it-qat
    yue2cpp_model = YuE2-3B-Q8_0.gguf
    cpp_engine_args =
"""
from __future__ import annotations

import configparser
import ctypes
import json
import os
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# Every probe this launcher makes is to localhost. Bypass any HTTP_PROXY / VPN proxy so
# 127.0.0.1 health checks never stall behind a system proxy (lesson from Windows #76).
LOCAL = urllib.request.build_opener(urllib.request.ProxyHandler({}))

APP = "Yeufonic"
HERE = Path(__file__).resolve().parent
STUDIO = HERE / "studio" if (HERE / "studio").is_dir() else HERE.parent
HOME_DIR = Path(os.environ.get("YEUFONIC_HOME") or (Path.home() / ".local" / "share" / "yeufonic")).expanduser()
LOGS = Path(os.environ.get("YEUFONIC_LOGS") or (HOME_DIR / "logs")).expanduser()
ENGINE_DIR = HOME_DIR / "engine"
COMFY = ENGINE_DIR / "ComfyUI"
MODELS = COMFY / "models"
CUDA12_LIBS = ENGINE_DIR / "cuda12"
ENGINE_START = ENGINE_DIR / "start.py"
CPP = HOME_DIR / "engine-cpp"
ENGINE_PYTHON = ENGINE_DIR / "venv" / "bin" / "python"
APP_PYTHON = HOME_DIR / "venv" / "bin" / "python"
TOOLS = HOME_DIR / "tools" / "bin"
RUNNING = HOME_DIR / "state" / "running.json"
PROFILES = HOME_DIR / "browsers"
VOICE = HOME_DIR / "voice"
VOICE_PYTHON = VOICE / "venv" / "bin" / "python"
VOICE_SERVER = STUDIO / "voice" / "server.py"

APP_BROWSERS = ("google-chrome", "chromium", "chromium-browser", "brave-browser", "vivaldi", "microsoft-edge")
PR_SET_PDEATHSIG = 1


def _set_pdeathsig() -> None:
    """Ask the Linux kernel to send SIGTERM to the child if this launcher dies abruptly."""
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.prctl(PR_SET_PDEATHSIG, signal.SIGTERM)
    except OSError:
        pass


def settings() -> dict:
    """Ports, folders, engine choice and window behaviour from settings.ini."""
    values = {
        "app_port": "8090",
        "engine_port": "8188",
        "engine_args": "",
        "data_dir": str(HOME_DIR / "data"),
        "import_roots": str(Path.home()),
        "open_browser": "yes",
        "window": "browser",
        "training": "yes",
        "model": "",
        "update_manifest": "",
        "unload_when_idle": "auto",
        "voice_port": "8190",
        "engine": "comfyui",
        "gemma_port": "11435",
        "pictures_port": "8187",
        "gemma_model": "gemma4:e4b-it-qat",
        "yue2cpp_model": "YuE2-3B-Q8_0.gguf",
        "cpp_engine_args": "",
    }
    ini = HOME_DIR / "settings.ini"
    if ini.exists():
        parser = configparser.ConfigParser()
        parser.read(ini, encoding="utf-8")
        if parser.has_section("yue2"):
            values.update({k: v for k, v in parser.items("yue2") if v.strip()})
    values["data_dir"] = str(Path(values["data_dir"]).expanduser())
    values["import_roots"] = ",".join(
        str(Path(p.strip()).expanduser()) for p in values["import_roots"].split(",") if p.strip()
    )
    return values


def yes(value: str) -> bool:
    return str(value).strip().lower() in ("1", "yes", "true", "on")


def say(line: str) -> None:
    if sys.stdout:
        print(line, flush=True)


def record(line: str) -> None:
    """Print and append to launcher.log."""
    say(line)
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        with (LOGS / "launcher.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {line}\n")
    except OSError:
        pass


def answering(url: str) -> bool:
    try:
        with LOCAL.open(url, timeout=1) as reply:
            return reply.status == 200
    except (OSError, ValueError):
        return False


def port_taken(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def is_cpp(cfg: dict) -> bool:
    return cfg.get("engine", "comfyui").strip().lower() == "yue2cpp"


def engine_command(cfg: dict) -> list[str]:
    """ComfyUI, launched through engine/start.py when present so a driver/PyTorch mismatch is reported cleanly."""
    comfy_cmd = [
        str(ENGINE_PYTHON),
        "-s",
        str(COMFY / "main.py"),
        "--disable-auto-launch",
        "--listen",
        "127.0.0.1",
        "--port",
        str(cfg["engine_port"]),
        "--max-upload-size=2048",
        "--disable-pinned-memory",
        *shlex.split(cfg.get("engine_args", "")),
    ]
    if ENGINE_START.is_file():
        return [str(ENGINE_PYTHON), "-s", str(ENGINE_START), *comfy_cmd]
    return comfy_cmd


def cpp_command(cfg: dict) -> list[str]:
    gguf = MODELS / "yue2cpp"
    args = [
        str(CPP / "yue2cpp" / "yue-server"),
        "--host",
        "127.0.0.1",
        "--port",
        str(cfg["engine_port"]),
        "--model",
        str(gguf / cfg["yue2cpp_model"]),
        "--vae",
        str(gguf / "YuE2-Vae-F32.gguf"),
        "--adapters",
        str(MODELS / "loras"),
    ]
    if (gguf / "SheetSage2-Q8_0.gguf").exists():
        args += ["--transcriber", str(gguf / "SheetSage2-Q8_0.gguf")]
    return args + shlex.split(cfg.get("cpp_engine_args", ""))


def companions(cfg: dict) -> list[tuple[str, list[str], dict, Path, dict]]:
    """Optional companions beside yue2.cpp: Ollama for Gemma, and stable-diffusion.cpp for pictures."""
    out = []
    ollama = CPP / "ollama" / "bin" / "ollama"
    if not ollama.exists():
        ollama = CPP / "ollama" / "ollama"
    if ollama.exists() and (MODELS / "ollama" / "manifests").is_dir():
        port = cfg["gemma_port"]
        ollama_env = _with_local_no_proxy(dict(os.environ))
        ollama_env.update({
            "OLLAMA_HOST": f"127.0.0.1:{port}",
            "OLLAMA_MODELS": str(MODELS / "ollama"),
            "OLLAMA_KEEP_ALIVE": "0",
        })
        out.append((
            "gemma",
            [str(ollama), "serve"],
            ollama_env,
            ollama.parent,
            {"GEMMA_URL": f"http://127.0.0.1:{port}", "GEMMA_MODEL": cfg["gemma_model"]},
        ))
    sdserver = CPP / "yue2cpp" / "sd-server"
    if sdserver.exists():
        port = cfg["pictures_port"]
        out.append((
            "pictures",
            [str(sdserver), "--model-dir", str(MODELS), "--listen-ip", "127.0.0.1", "--listen-port", str(port)],
            _with_local_no_proxy(dict(os.environ)),
            CPP / "yue2cpp",
            {"PICTURES_URL": f"http://127.0.0.1:{port}"},
        ))
    return out


def _with_local_no_proxy(env: dict) -> dict:
    """Ensure localhost calls between app, engine, voice and companions never go through a system/VPN proxy."""
    for var in ("NO_PROXY", "no_proxy"):
        existing = [x.strip() for x in env.get(var, "").split(",") if x.strip()]
        for host in ("127.0.0.1", "localhost", "::1"):
            if host not in existing:
                existing.append(host)
        env[var] = ",".join(existing)
    return env


def engine_env(cfg: dict) -> dict:
    env = _with_local_no_proxy(dict(os.environ))
    env.update({
        "PATH": os.pathsep.join([str(ENGINE_PYTHON.parent), str(TOOLS), env.get("PATH", "/usr/bin:/bin")]),
        "YEUFONIC_APP_URL": f"http://127.0.0.1:{cfg['app_port']}",
        "ENGINE_START_NOTE": str(COMFY / "output" / "yeufonic" / "engine-start.json"),
        "CUDA12_LIBS": str(CUDA12_LIBS),
        "PYTHONUNBUFFERED": "1",
    })
    return env


def app_command(cfg: dict) -> list[str]:
    return [
        str(APP_PYTHON),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(cfg["app_port"]),
        "--no-access-log",
    ]


def app_env(cfg: dict) -> dict:
    data = Path(cfg["data_dir"])
    env = _with_local_no_proxy(dict(os.environ))
    env.update({
        "PATH": os.pathsep.join([str(APP_PYTHON.parent), str(TOOLS), env.get("PATH", "/usr/bin:/bin")]),
        "DATA_DIR": str(data),
        "MODELS_DIR": str(MODELS),
        "VERSION_FILE": str(STUDIO / "VERSION"),
        "BUILD_FILE": str(STUDIO / "BUILD"),
        "ENGINE_URL": f"http://127.0.0.1:{cfg['engine_port']}",
        "ENGINE_INPUT_DIR": str(COMFY / "input"),
        "ENGINE_OUTPUT_DIR": str(COMFY / "output"),
        "IMPORT_ROOTS": cfg["import_roots"],
        "TORCH_HOME": str(data / "models" / "torch"),
        "HF_HOME": str(data / "models" / "whisper"),
        "TRAINING_ENABLED": "1" if yes(cfg.get("training", "yes")) else "0",
        "UNLOAD_WHEN_IDLE": cfg.get("unload_when_idle", "auto"),
        "YEUFONIC_INSTALL": "linux",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1",
        "PYTHONPYCACHEPREFIX": str(HOME_DIR / "cache" / "pycache"),
        "YEUFONIC_UPDATE_MANIFEST": cfg.get("update_manifest", ""),
    })
    if cfg.get("model"):
        env["YUE2_CHECKPOINT"] = cfg["model"]
    return env


def voices_installed() -> bool:
    return VOICE_PYTHON.exists() and (VOICE / "rvc" / "infer").is_dir() and VOICE_SERVER.exists()


def voice_command(cfg: dict) -> list[str]:
    return [str(VOICE_PYTHON), str(VOICE_SERVER)]


def voice_env(cfg: dict) -> dict:
    env = _with_local_no_proxy(dict(os.environ))
    env.update({
        "RVC_DIR": str(VOICE / "rvc"),
        "VOICES_DIR": str(Path(cfg["data_dir"]) / "voices"),
        "VOICE_HOST": "127.0.0.1",
        "VOICE_PORT": str(cfg["voice_port"]),
        "VOICE_DEVICE": "cuda",
        "PATH": os.pathsep.join([str(VOICE_PYTHON.parent), str(TOOLS), env.get("PATH", "/usr/bin:/bin")]),
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1",
    })
    return env


def _command_of(pid: int) -> str:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        if raw:
            return raw.replace(b"\x00", b" ").decode("utf-8", errors="replace").strip()
    except OSError:
        pass
    try:
        return subprocess.run(
            ["ps", "-ww", "-o", "args=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _read_running() -> dict:
    try:
        return json.loads(RUNNING.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def launcher_pid() -> int:
    try:
        pid = int(_read_running().get("launcher") or 0)
    except (ValueError, TypeError):
        return 0
    if pid > 0 and pid != os.getpid() and "launcher.py" in _command_of(pid):
        return pid
    return 0


def launcher_running() -> bool:
    return launcher_pid() > 0


def end_leftovers() -> None:
    """Stop any recorded engine/app/voice processes left behind by a killed launcher."""
    recorded = _read_running()
    if not recorded:
        return

    def ours(pid: int) -> bool:
        command = _command_of(pid)
        return (
            str(COMFY / "main.py") in command
            or str(ENGINE_START) in command
            or "app.main:app" in command
            or str(VOICE_SERVER) in command
            or str(CPP) in command
        )

    stopping = []
    for name, pid in recorded.items():
        if name == "launcher":
            continue
        try:
            pid_int = int(pid)
        except (ValueError, TypeError):
            continue
        if ours(pid_int):
            record(f"Stopping the {name} left running by an earlier start (pid {pid_int}).")
            try:
                os.kill(pid_int, signal.SIGTERM)
                stopping.append(pid_int)
            except OSError:
                pass
    deadline = time.time() + 10
    while stopping and time.time() < deadline:
        stopping = [pid for pid in stopping if ours(pid)]
        time.sleep(0.2)
    for pid in stopping:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    RUNNING.unlink(missing_ok=True)


def stop_running() -> int:
    """Stop an active Yeufonic launcher (and wait for it to shut down its children)."""
    pid = launcher_pid()
    if pid:
        say(f"Stopping Yeufonic (launcher pid {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        deadline = time.time() + 15
        while time.time() < deadline and "launcher.py" in _command_of(pid):
            time.sleep(0.2)
        if "launcher.py" in _command_of(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
    end_leftovers()
    say("Yeufonic is stopped.")
    return 0


def print_status(cfg: dict) -> int:
    url = f"http://127.0.0.1:{cfg['app_port']}"
    engine_probe = f"http://127.0.0.1:{cfg['engine_port']}/" + ("health" if is_cpp(cfg) else "system_stats")
    pid = launcher_pid()
    app_up = answering(f"{url}/api/health")
    eng_up = answering(engine_probe)
    if pid or app_up:
        say(f"Yeufonic: running (launcher pid {pid or 'none'})")
        say(f"  app:    {url} ({'ready' if app_up else 'starting'})")
        say(f"  engine: {'ready' if eng_up else 'starting'} ({cfg['engine']})")
        return 0
    say("Yeufonic: stopped")
    return 3


def _has_gui() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def open_browser(url: str, window: str = "browser") -> None:
    """Open the page without blocking; no-op on headless sessions."""
    if not _has_gui():
        return
    if window.strip().lower() == "app":
        for name in APP_BROWSERS:
            exe = shutil.which(name)
            if exe:
                profile = PROFILES / name
                profile.mkdir(parents=True, exist_ok=True)
                subprocess.Popen(
                    [exe, f"--app={url}", f"--user-data-dir={profile}", "--no-first-run"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return
    xdg = shutil.which("xdg-open")
    if xdg:
        subprocess.Popen(
            [xdg, url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )


class Launcher:
    """Supervises the engine (+ companions / voice) and the app together."""

    def __init__(self, cfg: dict, allow_browser: bool = True) -> None:
        self.cfg = cfg
        self.allow_browser = allow_browser
        self.app_port = int(cfg["app_port"])
        self.engine_port = int(cfg["engine_port"])
        self.url = f"http://127.0.0.1:{self.app_port}"
        self.cpp = is_cpp(cfg)
        self.engine_probe = f"http://127.0.0.1:{self.engine_port}/" + ("health" if self.cpp else "system_stats")
        self.programs: dict[str, tuple[subprocess.Popen, Path]] = {}
        self.started = 0.0
        self.app_ready = False
        self.engine_ready = False
        self.engine_stopped = False
        self.voice_stopped = False
        self.quitting = False

    def problem(self) -> str:
        if self.cpp:
            if not (CPP / "yue2cpp" / "yue-server").exists():
                return "The yue2.cpp engine is not set up. Run 'yeufonic setup --engine yue2cpp' first."
        elif not ENGINE_PYTHON.exists() or not (COMFY / "main.py").exists():
            return "The engine is not set up. Run 'yeufonic setup' first."
        if not APP_PYTHON.exists():
            return "The app is not set up. Run 'yeufonic setup' first."
        ports = [(self.app_port, "the app"), (self.engine_port, "the engine")]
        if voices_installed():
            ports.append((int(self.cfg["voice_port"]), "the voice service"))
        if self.cpp:
            active = {c[0] for c in companions(self.cfg)}
            for name, what in (("gemma", "Gemma"), ("pictures", "the picture server")):
                if name in active:
                    ports.append((int(self.cfg[f"{name}_port"]), what))
        for port, what in ports:
            if port_taken(port):
                return (
                    f"Port {port}, which {what} uses, is taken by another program (Docker, or another "
                    f"copy of Yeufonic or ComfyUI?). Ports can be changed in {HOME_DIR / 'settings.ini'}."
                )
        return ""

    def _spawn(self, command: list[str], cwd: Path, env: dict, log_path: Path) -> subprocess.Popen:
        return subprocess.Popen(
            command,
            cwd=str(cwd),
            env=env,
            stdout=log_path.open("w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            preexec_fn=_set_pdeathsig,
        )

    def start_engine(self) -> None:
        log_path = LOGS / "engine.log"
        if self.cpp:
            command, cwd, env = cpp_command(self.cfg), CPP / "yue2cpp", _with_local_no_proxy(dict(os.environ))
        else:
            command, cwd, env = engine_command(self.cfg), COMFY, engine_env(self.cfg)
        proc = self._spawn(command, cwd, env, log_path)
        self.programs["engine"] = (proc, log_path)
        self.engine_ready = False
        self.engine_stopped = False
        self._remember()

    def start(self) -> None:
        LOGS.mkdir(parents=True, exist_ok=True)
        Path(self.cfg["data_dir"]).mkdir(parents=True, exist_ok=True)
        (COMFY / "input").mkdir(parents=True, exist_ok=True)
        (COMFY / "output").mkdir(parents=True, exist_ok=True)
        self.started = time.time()
        record("Starting the engine and the app...")
        self.start_engine()
        env = app_env(self.cfg)
        if self.cpp:
            env["ENGINE_KIND"] = "yue2cpp"
            for name, command, program_env, cwd, told in companions(self.cfg):
                log_path = LOGS / f"{name}.log"
                self.programs[name] = (self._spawn(command, cwd, program_env, log_path), log_path)
                env.update(told)
        if voices_installed():
            log_path = LOGS / "voice.log"
            proc = self._spawn(voice_command(self.cfg), VOICE / "rvc", voice_env(self.cfg), log_path)
            self.programs["voice"] = (proc, log_path)
            env["VOICE_URL"] = f"http://127.0.0.1:{self.cfg['voice_port']}"
        log_path = LOGS / "app.log"
        proc = self._spawn(app_command(self.cfg), STUDIO, env, log_path)
        self.programs["app"] = (proc, log_path)
        self._remember()

    def _remember(self) -> None:
        try:
            RUNNING.parent.mkdir(parents=True, exist_ok=True)
            started = {name: p.pid for name, (p, _) in self.programs.items()}
            RUNNING.write_text(json.dumps({"launcher": os.getpid(), **started}), encoding="utf-8")
        except OSError:
            pass

    def poll(self) -> str:
        now = time.time()
        app, app_log = self.programs["app"]
        if app.poll() is not None:
            record(f"The app stopped (exit code {app.returncode}). See {app_log}.")
            return "app stopped"
        engine, engine_log = self.programs["engine"]
        if engine.poll() is not None and not self.engine_stopped:
            self.engine_stopped = True
            record(f"The engine stopped (exit code {engine.returncode}). See {engine_log}.")
            return "engine stopped"
        voice = self.programs.get("voice")
        if voice and voice[0].poll() is not None and not self.voice_stopped:
            self.voice_stopped = True
            record(f"The voice service stopped (exit code {voice[0].returncode}). See {voice[1]}.")
        if not self.engine_ready and answering(self.engine_probe):
            self.engine_ready = True
            record(f"The engine answered after {now - self.started:.0f} s.")
        if not self.app_ready and answering(f"{self.url}/api/health"):
            self.app_ready = True
            record(f"The app answered after {now - self.started:.0f} s.")
            return "app ready"
        return ""

    def open_page(self) -> None:
        if self.allow_browser and yes(self.cfg.get("open_browser", "yes")):
            open_browser(self.url, self.cfg.get("window", "browser"))

    @staticmethod
    def _end(program: subprocess.Popen, wait: float = 10.0) -> None:
        if program.poll() is None:
            program.terminate()
            try:
                program.wait(wait)
            except subprocess.TimeoutExpired:
                program.kill()
                program.wait(5)

    def stop(self) -> None:
        if self.quitting:
            return
        self.quitting = True
        record("Stopping the app and the engine.")
        for name in ("app", "voice", "gemma", "pictures", "engine"):
            if name in self.programs:
                self._end(self.programs[name][0])
        RUNNING.unlink(missing_ok=True)
        record("Stopped.")


def run_foreground(launcher: Launcher) -> int:
    def stop(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    launcher.start()
    say(f"{APP} is available at {launcher.url} once the app answers. Ctrl+C stops it.")
    try:
        while True:
            happened = launcher.poll()
            if happened == "app ready":
                launcher.open_page()
            elif happened == "app stopped":
                launcher.stop()
                return 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        launcher.stop()
        return 0


def spawn_background(args: list[str]) -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    child_args = [sys.executable, str(Path(__file__).resolve()), *[a for a in args if a != "--background"]]
    with (LOGS / "launcher.log").open("a", encoding="utf-8") as log_fh:
        subprocess.Popen(
            child_args,
            cwd=str(HOME_DIR),
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    say(f"{APP} is starting in the background. Run 'yeufonic status' or 'yeufonic stop' to manage it.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cfg = settings()
    if "--stop" in args:
        return stop_running()
    if "--status" in args:
        return print_status(cfg)
    if "--background" in args:
        return spawn_background(args)

    allow_browser = "--no-browser" not in args
    launcher = Launcher(cfg, allow_browser=allow_browser)
    if answering(f"{launcher.url}/api/health") and (launcher_running() or not RUNNING.exists()):
        say(f"{APP} is already running at {launcher.url}.")
        launcher.open_page()
        return 0
    end_leftovers()
    problem = launcher.problem()
    if problem:
        record(problem)
        return 1
    return run_foreground(launcher)


if __name__ == "__main__":
    sys.exit(main())
