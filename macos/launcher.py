"""Start Yeufonic on a Mac: the engine (ComfyUI, on the GPU through Metal) and the app
together, an icon in the menu bar to open the page, see the logs and quit, and the page in
the default browser as soon as the app answers.  The macOS counterpart of
windows/launcher.py.

Yeufonic.app's own program (written by macos/build.sh) sets the install up on first use,
and again after an update, then runs this with the app's Python.  `--console` runs it
without the menu bar, for a terminal or a test: Ctrl+C stops both.

The install lives in ~/Library/Application Support/Yeufonic (YEUFONIC_HOME moves it), its
logs in ~/Library/Logs/Yeufonic (YEUFONIC_LOGS), and settings.ini there overrides:

    [yue2]
    app_port = 8090
    engine_port = 8188
    engine_args =
    data_dir = ~/Library/Application Support/Yeufonic/data
    import_roots = ~
    open_browser = yes
    training = no
"""
from __future__ import annotations

import configparser
import json
import os
import shlex
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

APP = "Yeufonic"
HERE = Path(__file__).resolve().parent
# Inside the app, studio/ sits beside this file; run from a checkout, the checkout is it.
STUDIO = HERE / "studio" if (HERE / "studio").is_dir() else HERE.parent
SUPPORT = Path(os.environ.get("YEUFONIC_HOME") or Path.home() / "Library" / "Application Support" / APP)
LOGS = Path(os.environ.get("YEUFONIC_LOGS") or Path.home() / "Library" / "Logs" / APP)
COMFY = SUPPORT / "engine" / "ComfyUI"
ENGINE_PYTHON = SUPPORT / "engine" / "venv" / "bin" / "python"
APP_PYTHON = SUPPORT / "venv" / "bin" / "python"
TOOLS = SUPPORT / "tools" / "bin"
RUNNING = SUPPORT / "state" / "running.json"
# FluidSynth has no macOS build of its own; Homebrew's is used where it is installed.
HOMEBREW = Path("/opt/homebrew/bin")


def settings() -> dict:
    """Ports, the library's folder, and whether the page opens by itself.  settings.ini
    overrides the defaults.  Training is off unless asked for: the trainer is written for
    CUDA and has not been tried on a Mac."""
    values = {"app_port": "8090", "engine_port": "8188", "engine_args": "", "data_dir": str(SUPPORT / "data"),
              "import_roots": str(Path.home()), "open_browser": "yes", "training": "no", "update_manifest": ""}
    ini = SUPPORT / "settings.ini"
    if ini.exists():
        parser = configparser.ConfigParser()
        parser.read(ini, encoding="utf-8")
        if parser.has_section("yue2"):
            values.update({k: v for k, v in parser.items("yue2") if v.strip()})
    values["data_dir"] = str(Path(values["data_dir"]).expanduser())
    values["import_roots"] = ",".join(str(Path(p.strip()).expanduser()) for p in values["import_roots"].split(",") if p.strip())
    return values


def yes(value: str) -> bool:
    return str(value).strip().lower() in ("1", "yes", "true", "on")


def say(line: str) -> None:
    if sys.stdout:
        print(line, flush=True)


def record(line: str) -> None:
    """Said, and kept in the launcher's log."""
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
    except (OSError, ValueError):
        return False


def port_taken(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def engine_command(cfg: dict) -> list[str]:
    return [str(ENGINE_PYTHON), "-s", str(COMFY / "main.py"), "--disable-auto-launch",
            "--listen", "127.0.0.1", "--port", str(cfg["engine_port"]), *shlex.split(cfg.get("engine_args", ""))]


def engine_env(cfg: dict) -> dict:
    env = dict(os.environ)
    env.update({
        # Its start-up message then sends people to the app, not the engine.
        "YEUFONIC_APP_URL": f"http://127.0.0.1:{cfg['app_port']}",
        # An operation Metal does not have yet runs on the CPU rather than stopping the job.
        "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        "PYTHONUNBUFFERED": "1",
    })
    return env


def app_command(cfg: dict) -> list[str]:
    return [str(APP_PYTHON), "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", str(cfg["app_port"]), "--no-access-log"]


def app_env(cfg: dict) -> dict:
    """What the app is told, as the Windows launcher tells it."""
    data = Path(cfg["data_dir"])
    env = dict(os.environ)
    env.update({
        "PATH": os.pathsep.join([str(APP_PYTHON.parent), str(TOOLS), env.get("PATH", "/usr/bin:/bin"), str(HOMEBREW)]),
        "DATA_DIR": str(data),
        "MODELS_DIR": str(COMFY / "models"),
        "VERSION_FILE": str(STUDIO / "VERSION"),
        "BUILD_FILE": str(STUDIO / "BUILD"),
        "ENGINE_URL": f"http://127.0.0.1:{cfg['engine_port']}",
        "ENGINE_INPUT_DIR": str(COMFY / "input"),
        "ENGINE_OUTPUT_DIR": str(COMFY / "output"),
        "IMPORT_ROOTS": cfg["import_roots"],
        "TORCH_HOME": str(data / "models" / "torch"),
        "HF_HOME": str(data / "models" / "whisper"),
        "TRAINING_ENABLED": "1" if yes(cfg.get("training", "no")) else "0",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1",
        # The app runs from inside Yeufonic.app, which is not to be written in: a byte-compiled
        # file there would break the app's signature.
        "PYTHONPYCACHEPREFIX": str(SUPPORT / "cache" / "pycache"),
        # Set only for a test of the update notice: where to look for an update to try.
        "YEUFONIC_UPDATE_MANIFEST": cfg.get("update_manifest", ""),
    })
    return env


def _command_of(pid: int) -> str:
    try:
        return subprocess.run(["ps", "-ww", "-o", "command=", "-p", str(pid)], capture_output=True, text=True,
                              timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def end_leftovers() -> None:
    """A launcher that was killed outright leaves its engine and app running, holding their ports
    and several gigabytes of memory.  The ones it recorded, and only while they are still what it
    started, are stopped before starting again."""
    try:
        recorded = json.loads(RUNNING.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return

    def ours(pid: int) -> bool:
        # A process id can be given to something else once its process has gone.
        command = _command_of(pid)
        return str(COMFY / "main.py") in command or "app.main:app" in command

    stopping = []
    for name, pid in recorded.items():
        if ours(int(pid)):
            record(f"Stopping the {name} left running by an earlier start (pid {pid}).")
            try:
                os.kill(int(pid), signal.SIGTERM)
                stopping.append(int(pid))
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


class Launcher:
    """The two programs, started together and stopped together.  Nothing here knows about
    the menu bar, so the console mode and the tests use it as it is."""

    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.app_port = int(cfg["app_port"])
        self.engine_port = int(cfg["engine_port"])
        self.url = f"http://127.0.0.1:{self.app_port}"
        self.programs: dict[str, tuple[subprocess.Popen, Path]] = {}
        self.started = 0.0
        self.app_ready = False
        self.engine_ready = False
        self.engine_stopped = False
        self.quitting = False

    def problem(self) -> str:
        """Why it cannot start, in a sentence, or nothing."""
        if not ENGINE_PYTHON.exists() or not (COMFY / "main.py").exists():
            return "The engine is not set up. Open Yeufonic again to finish setting it up."
        if not APP_PYTHON.exists():
            return "The app is not set up. Open Yeufonic again to finish setting it up."
        for port, what in ((self.app_port, "the app"), (self.engine_port, "the engine")):
            if port_taken(port):
                return (f"Port {port}, which {what} uses, is taken by another program (another copy of "
                        f"Yeufonic or ComfyUI?). The ports can be changed in {SUPPORT / 'settings.ini'}.")
        return ""

    def start_engine(self) -> None:
        log = LOGS / "engine.log"
        engine = subprocess.Popen(engine_command(self.cfg), cwd=str(COMFY), env=engine_env(self.cfg),
                                  stdout=log.open("w", encoding="utf-8"), stderr=subprocess.STDOUT,
                                  stdin=subprocess.DEVNULL)
        self.programs["engine"] = (engine, log)
        self.engine_ready = False
        self.engine_stopped = False
        self._remember()

    def start(self) -> None:
        """The engine and the app at once: the app is up in seconds and copes with an engine
        still starting, so the page need not wait for ComfyUI."""
        LOGS.mkdir(parents=True, exist_ok=True)
        Path(self.cfg["data_dir"]).mkdir(parents=True, exist_ok=True)
        self.started = time.time()
        record("Starting the engine and the app...")
        self.start_engine()
        log = LOGS / "app.log"
        app = subprocess.Popen(app_command(self.cfg), cwd=str(STUDIO), env=app_env(self.cfg),
                               stdout=log.open("w", encoding="utf-8"), stderr=subprocess.STDOUT,
                               stdin=subprocess.DEVNULL)
        self.programs["app"] = (app, log)
        self._remember()

    def _remember(self) -> None:
        try:
            RUNNING.parent.mkdir(parents=True, exist_ok=True)
            RUNNING.write_text(json.dumps({name: p.pid for name, (p, _) in self.programs.items()}), encoding="utf-8")
        except OSError:
            pass

    def restart_engine(self) -> None:
        engine = self.programs.get("engine")
        if engine and engine[0].poll() is None:
            record("Restarting the engine.")
            self._end(engine[0])
        self.start_engine()

    def poll(self) -> str:
        """What has happened since the last look: "app ready", "app stopped", "engine stopped",
        or nothing."""
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
        if not self.engine_ready and answering(f"http://127.0.0.1:{self.engine_port}/system_stats"):
            self.engine_ready = True
            record(f"The engine answered after {now - self.started:.0f} s.")
        if not self.app_ready and answering(f"{self.url}/api/health"):
            self.app_ready = True
            record(f"The app answered after {now - self.started:.0f} s.")
            return "app ready"
        return ""

    def busy(self) -> str:
        """What quitting would stop, in a few words, or nothing."""
        try:
            with urllib.request.urlopen(f"{self.url}/api/state", timeout=2) as reply:
                state = json.load(reply)
        except (OSError, ValueError):
            return ""
        if state.get("training"):
            return "A LoRA is training. Quitting stops it."
        if state.get("current") or state.get("queue"):
            return "A job is running. Quitting stops it."
        return ""

    def open_page(self) -> None:
        webbrowser.open(self.url)

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
        # The app first, so it can tell the engine it is going, then the engine.
        for name in ("app", "engine"):
            if name in self.programs:
                self._end(self.programs[name][0])
        RUNNING.unlink(missing_ok=True)
        record("Stopped.")


def run_console(launcher: Launcher) -> int:
    def stop(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    launcher.start()
    say(f"{APP} opens at {launcher.url} once the app answers. Ctrl+C stops it.")
    try:
        while True:
            happened = launcher.poll()
            if happened == "app ready" and yes(launcher.cfg.get("open_browser", "yes")):
                launcher.open_page()
            elif happened == "app stopped":
                launcher.stop()
                return 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        launcher.stop()
        return 0


def run_menu_bar(launcher: Launcher) -> int:
    """The icon by the clock, as the Windows launcher has one in the tray: no Dock icon and no
    window of its own, since the page is the app."""
    import objc  # noqa: F401  (PyObjC; installed into the app's Python by setup.sh)
    from AppKit import (NSAlert, NSAlertFirstButtonReturn, NSApplication, NSApplicationActivationPolicyAccessory,
                        NSImage, NSMenu, NSMenuItem, NSStatusBar, NSVariableStatusItemLength, NSWorkspace)
    from Foundation import NSURL, NSObject, NSTimer

    def alert(text: str, detail: str = "", buttons: tuple[str, ...] = ("OK",)) -> int:
        box = NSAlert.alloc().init()
        box.setMessageText_(text)
        box.setInformativeText_(detail)
        for label in buttons:
            box.addButtonWithTitle_(label)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        return box.runModal() - NSAlertFirstButtonReturn

    class Delegate(NSObject):
        def applicationDidFinishLaunching_(self, _note):
            bar = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
            image = NSImage.imageWithSystemSymbolName_accessibilityDescription_("music.note", APP)
            if image:
                image.setTemplate_(True)
                bar.button().setImage_(image)
            else:
                bar.button().setTitle_("Y")
            bar.button().setToolTip_(APP)
            menu = NSMenu.alloc().init()
            for title, action in ((f"Open {APP}", "openPage:"), ("Show the logs", "showLogs:"),
                                  ("Restart the engine", "restartEngine:"), (None, None), (f"Quit {APP}", "quit:")):
                if title is None:
                    menu.addItem_(NSMenuItem.separatorItem())
                    continue
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, "")
                item.setTarget_(self)
                menu.addItem_(item)
            bar.setMenu_(menu)
            self.bar = bar
            launcher.start()
            self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.5, self, "tick:", None, True)

        def tick_(self, _timer):
            if launcher.quitting:
                return
            happened = launcher.poll()
            if happened == "app ready" and yes(launcher.cfg.get("open_browser", "yes")):
                launcher.open_page()
            elif happened == "engine stopped":
                alert("The engine stopped.", "Songs cannot be made until it is running again. "
                      f"Restart it from the {APP} menu in the menu bar; the engine log may say why.")
            elif happened == "app stopped":
                alert(f"{APP} stopped.", f"The app log in {LOGS} may say why.")
                NSApplication.sharedApplication().terminate_(None)

        def openPage_(self, _sender):
            launcher.open_page()

        def showLogs_(self, _sender):
            NSWorkspace.sharedWorkspace().openURL_(NSURL.fileURLWithPath_(str(LOGS)))

        def restartEngine_(self, _sender):
            warning = launcher.busy()
            if warning and alert("Restart the engine?", warning, ("Cancel", "Restart")) != 1:
                return
            launcher.restart_engine()

        def quit_(self, _sender):
            # Asked only when it would stop a job or a training run, as on Windows.
            warning = launcher.busy()
            if warning and alert(f"Quit {APP}?", warning, ("Cancel", "Quit")) != 1:
                return
            NSApplication.sharedApplication().terminate_(None)

        def applicationShouldHandleReopen_hasVisibleWindows_(self, _app, _flag):
            # Opening Yeufonic again while it runs: the page, as a second click does on Windows.
            launcher.open_page()
            return False

        def applicationWillTerminate_(self, _note):
            launcher.stop()

    def on_signal(_signum, _frame):
        launcher.stop()
        os._exit(0)
    signal.signal(signal.SIGTERM, on_signal)

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    delegate = Delegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()
    return 0


def fail(text: str, console: bool) -> int:
    record(text)
    if not console:
        subprocess.run(["osascript", "-e", f"display alert {json.dumps(APP, ensure_ascii=False)} message {json.dumps(text, ensure_ascii=False)}"],
                       check=False)
    return 1


def main() -> int:
    console = "--console" in sys.argv[1:]
    cfg = settings()
    launcher = Launcher(cfg)
    if answering(f"{launcher.url}/api/health"):
        # Started some other way, or still running from before: just open the page.
        launcher.open_page()
        return 0
    end_leftovers()
    problem = launcher.problem()
    if problem:
        return fail(problem, console)
    if console:
        return run_console(launcher)
    try:
        return run_menu_bar(launcher)
    except ImportError as exc:
        record(f"No menu-bar icon ({exc}); running as in a terminal.")
        return run_console(launcher)


if __name__ == "__main__":
    sys.exit(main())
