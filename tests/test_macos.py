"""The Mac install: what can be tried without a Mac.

setup.sh's system check runs here with stand-ins for the commands it asks (uname, sw_vers,
sysctl, curl), the app's own program (written by build.sh) runs with stand-ins for `open` and
`osascript`, and the launcher starts and stops real programs in place of the engine and the
app.  What only a Mac can show (Metal, the menu bar, the disk image, Gatekeeper) is in
macos/README.md's test plan.
"""
import importlib.util
import json
import os
import plistlib
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

from app import config, update

ROOT = Path(__file__).resolve().parent.parent
MACOS = ROOT / "macos"
SETUP = MACOS / "setup.sh"
SETUP_PS1 = ROOT / "windows" / "setup.ps1"

needs_bash = pytest.mark.skipif(sys.platform == "win32", reason="bash scripts")


def load_launcher(monkeypatch, home: Path):
    monkeypatch.setenv("YEUFONIC_HOME", str(home / "support"))
    monkeypatch.setenv("YEUFONIC_LOGS", str(home / "logs"))
    spec = importlib.util.spec_from_file_location("mac_launcher", MACOS / "launcher.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------- one list of models

def mac_models() -> dict:
    text = SETUP.read_text(encoding="utf-8")
    block = re.search(r"model_list\(\) \{\n  cat <<LIST\n(.*?)\nLIST", text, re.S).group(1)
    out = {}
    for line in block.splitlines():
        folder, name, size, sha, url, _lyrics = line.split("|")
        out[name] = {"dir": folder, "size": int(size), "sha": sha, "url": url.replace("$HF", "https://huggingface.co")}
    return out


def windows_models() -> dict:
    text = SETUP_PS1.read_text(encoding="utf-8")
    core = text.split("$ModelFiles = @(", 1)[1].split("\n)\n", 1)[0]
    soundfonts = text.split("$SoundFontFiles = @(", 1)[1].split("\n)\n", 1)[0]
    out = {}
    for block in (core, soundfonts):
        for entry in re.findall(r"@\{(.*?Size = \d+) \}", block, re.S):
            name = re.search(r"File = '([^']+)'", entry).group(1)
            url = re.search(r"Url = [\"']([^\"']+)[\"']", entry).group(1).replace("$HF", "https://huggingface.co")
            out[name] = {"size": int(re.search(r"Size = (\d+)", entry).group(1)),
                         "sha": re.search(r"Sha = '([0-9a-f]{64})'", entry).group(1), "url": url}
    return out


def test_the_mac_fetches_the_windows_models_with_the_same_checksums():
    mac, windows = mac_models(), windows_models()
    assert mac, "no models found in setup.sh"
    for name, entry in mac.items():
        assert name in windows, f"{name} is fetched on a Mac but not on Windows"
        for key in ("size", "sha", "url"):
            assert entry[key] == windows[name][key], f"{name}: {key} differs from windows/setup.ps1"
    # Every Windows model is on a Mac too, but for the soundfonts (a list of their own).
    left_out = set(windows) - set(mac) - {"github_Jnsgm2.sf2", "Arachno_SoundFont_Version_1.0.sf2"}
    assert not left_out, f"windows/setup.ps1 fetches {left_out}, setup.sh does not"


def test_the_mac_fetches_the_windows_soundfonts():
    text = SETUP.read_text(encoding="utf-8")
    block = re.search(r"soundfont_list\(\) \{\n  cat <<LIST\n(.*?)\nLIST", text, re.S).group(1)
    windows = windows_models()
    for line in block.splitlines():
        name, size, sha, url = line.split("|")
        assert windows[name] == {"size": int(size), "sha": sha, "url": url}


def test_the_engine_is_pinned_where_docker_and_windows_pin_it():
    mac = SETUP.read_text(encoding="utf-8")
    ps1 = SETUP_PS1.read_text(encoding="utf-8")
    dockerfile = (ROOT / "engine" / "Dockerfile").read_text(encoding="utf-8")
    comfy = re.search(r"^COMFY_COMMIT=([0-9a-f]{40})$", mac, re.M).group(1)
    trainer = re.search(r"^TRAINER_COMMIT=([0-9a-f]{40})$", mac, re.M).group(1)
    assert f"ComfyCommit       = '{comfy}'" in ps1
    assert f"Yue2TrainerCommit = '{trainer}'" in ps1
    assert re.search(r"^ARG COMFYUI_REF=(\w+)$", dockerfile, re.M).group(1) == comfy[:8]
    assert f"ARG YUE2_TRAINER_REF={trainer}" in dockerfile


# ------------------------------------------------------------- setup.sh's checks

def fake_mac(tmp_path: Path, arch="arm64", version="15.1", memory_gb=32) -> dict:
    """A PATH on which uname, sw_vers and sysctl describe a Mac, and the network answers."""
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir(exist_ok=True)
    tools = {
        "uname": f'[ "$1" = -m ] && echo {arch} || echo Darwin',
        "sw_vers": f"echo {version}",
        "sysctl": f"echo {memory_gb * 1073741824}",
        "curl": "exit 0",
        "nc": "exit 1",
    }
    for name, body in tools.items():
        path = bin_dir / name
        path.write_text(f"#!/bin/sh\n{body}\n")
        path.chmod(0o755)
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", HOME=str(tmp_path),
               YEUFONIC_LOGS=str(tmp_path / "logs"))
    return env


def check(tmp_path, *extra, **mac):
    return subprocess.run(["bash", str(SETUP), "--check-only", "--install-dir", str(tmp_path / "install"), *extra],
                          env=fake_mac(tmp_path, **mac), capture_output=True, text=True, timeout=60)


@needs_bash
def test_setup_scripts_parse():
    for script in ("setup.sh", "build.sh"):
        res = subprocess.run(["bash", "-n", str(MACOS / script)], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr


@needs_bash
def test_setup_passes_a_suitable_mac(tmp_path):
    res = check(tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "This Mac is suitable." in res.stdout
    assert "Setup stopped" not in res.stdout


@needs_bash
@pytest.mark.parametrize("mac, says", [
    ({"arch": "x86_64"}, "needs a Mac with Apple silicon"),
    ({"version": "13.6"}, "macOS 14 (Sonoma) or later"),
    ({"memory_gb": 8}, "16 GB is the least"),
])
def test_setup_refuses_a_mac_that_cannot_run_it(tmp_path, mac, says):
    res = subprocess.run(["bash", str(SETUP), "--install-dir", str(tmp_path / "install")],
                         env=fake_mac(tmp_path, **mac), capture_output=True, text=True, timeout=60)
    assert res.returncode == 1
    assert says in res.stdout
    assert "Setup stopped: this Mac does not meet the requirements" in res.stdout
    # It stopped at the check: nothing was fetched or set up.
    assert not (tmp_path / "install" / "tools" / "bin" / "uv").exists()


@needs_bash
def test_a_build_machine_with_little_memory_may_still_test_the_setup(tmp_path):
    res = check(tmp_path, memory_gb=7)
    assert res.returncode == 0, res.stdout
    assert "too little to make songs" in res.stdout


@needs_bash
def test_setup_keeps_a_log(tmp_path):
    check(tmp_path)
    assert "This Mac is suitable." in (tmp_path / "logs" / "setup.log").read_text()


# ----------------------------------------------------------------- the built app

@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist")
    res = subprocess.run(["bash", str(MACOS / "build.sh")], env=dict(os.environ, OUT=str(out), VERSION="0.0.98"),
                         capture_output=True, text=True, timeout=300)
    assert res.returncode == 0, res.stdout + res.stderr
    return out / "Yeufonic.app"


@needs_bash
def test_the_app_carries_what_setup_and_the_launcher_need(built):
    contents = built / "Contents"
    info = plistlib.loads((contents / "Info.plist").read_bytes())
    assert info["CFBundleShortVersionString"] == "0.0.98"
    assert info["CFBundleExecutable"] == "Yeufonic"
    assert info["LSUIElement"] is True
    assert info["LSMinimumSystemVersion"] == "14.0"
    res = contents / "Resources"
    for need in ("setup.sh", "launcher.py", "yeufonic.icns", "studio/VERSION", "studio/BUILD",
                 "studio/requirements.txt", "studio/app/main.py", "studio/engine-nodes/yue2_harmony/__init__.py"):
        assert (res / need).exists(), need
    assert (res / "studio" / "VERSION").read_text().strip() == "0.0.98"
    assert not list(res.rglob("__pycache__"))
    assert (contents / "MacOS" / "Yeufonic").stat().st_mode & stat.S_IXUSR


def run_stub(built, tmp_path, app_path=None):
    """The app's own program, as macOS would start it, with `open` and `osascript` recorded."""
    calls = tmp_path / "calls"
    bin_dir = tmp_path / "stubbin"
    bin_dir.mkdir(exist_ok=True)
    for name in ("open", "osascript"):
        (bin_dir / name).write_text(f'#!/bin/sh\necho "{name} $*" >> "{calls}"\n')
        (bin_dir / name).chmod(0o755)
    app = built
    if app_path:
        app_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cp", "-R", str(built), str(app_path)], check=True)
        app = app_path
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", HOME=str(tmp_path),
               YEUFONIC_HOME=str(tmp_path / "support"))
    res = subprocess.run([str(app / "Contents" / "MacOS" / "Yeufonic")], env=env, capture_output=True,
                         text=True, timeout=30)
    return res, (calls.read_text() if calls.exists() else "")


@needs_bash
def test_first_open_sets_up_in_terminal_and_comes_back(built, tmp_path):
    res, calls = run_stub(built, tmp_path)
    assert res.returncode == 0, res.stderr
    command = tmp_path / "support" / "Set up Yeufonic.command"
    assert f"open -a Terminal {command}" in calls
    text = command.read_text()
    assert str(built / "Contents" / "Resources" / "setup.sh").replace(" ", "\\ ") in text
    assert f"--then-open {built}" in text
    assert os.access(command, os.X_OK)


@needs_bash
def test_opened_from_the_disk_image_it_asks_to_be_moved_first(built, tmp_path):
    # /Volumes cannot be made here; App Translocation's path is the same case.
    res, calls = run_stub(built, tmp_path, tmp_path / "AppTranslocation" / "x" / "d" / "Yeufonic.app")
    assert "osascript" in calls and "Applications folder first" in calls
    assert "Terminal" not in calls


@needs_bash
def test_once_set_up_it_runs_the_launcher_and_sets_up_again_after_an_update(built, tmp_path):
    support = tmp_path / "support"
    python = support / "venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f'#!/bin/sh\necho "launcher $*" >> "{tmp_path / "calls"}"\n')
    python.chmod(0o755)
    studio = built / "Contents" / "Resources" / "studio"
    (support / "state").mkdir()
    (support / "state" / "set-up-for").write_text((studio / "VERSION").read_text() + (studio / "BUILD").read_text())
    _, calls = run_stub(built, tmp_path)
    assert f"launcher {built / 'Contents' / 'Resources' / 'launcher.py'}" in calls
    assert "Terminal" not in calls
    # A newer app dragged over this one is not the one set up: setup runs again.
    (support / "state" / "set-up-for").write_text("0.0.97\n")
    (tmp_path / "calls").unlink()
    _, calls = run_stub(built, tmp_path)
    assert "open -a Terminal" in calls and "launcher" not in calls


# ------------------------------------------------------------------- the launcher

def test_the_app_is_told_what_the_windows_launcher_tells_it(monkeypatch, tmp_path):
    launcher = load_launcher(monkeypatch, tmp_path)
    env = launcher.app_env(launcher.settings())
    windows = (ROOT / "windows" / "launcher.py").read_text(encoding="utf-8")
    told = set(re.findall(r'^\s+"([A-Z_]+)": ', windows.split("env.update({", 1)[1].split("})", 1)[0], re.M))
    assert told - {"HF_HUB_DISABLE_SYMLINKS_WARNING"} <= set(env), told - set(env)
    support = tmp_path / "support"
    assert env["MODELS_DIR"] == str(support / "engine" / "ComfyUI" / "models")
    assert env["DATA_DIR"] == str(support / "data")
    assert env["PATH"].split(os.pathsep)[:2] == [str(support / "venv" / "bin"), str(support / "tools" / "bin")]
    assert env["TRAINING_ENABLED"] == "0"
    assert env["PYTHONPYCACHEPREFIX"].startswith(str(support))


def test_settings_ini_moves_ports_and_data_and_turns_training_on(monkeypatch, tmp_path):
    launcher = load_launcher(monkeypatch, tmp_path)
    (tmp_path / "support").mkdir()
    (tmp_path / "support" / "settings.ini").write_text(
        "[yue2]\napp_port = 8099\nengine_port = 8199\ndata_dir = ~/Music/Yeufonic\ntraining = yes\nengine_args = --cpu --lowvram\n")
    cfg = launcher.settings()
    assert cfg["data_dir"] == str(Path.home() / "Music" / "Yeufonic")
    assert launcher.app_env(cfg)["TRAINING_ENABLED"] == "1"
    assert launcher.app_env(cfg)["ENGINE_URL"] == "http://127.0.0.1:8199"
    assert launcher.engine_command(cfg)[-2:] == ["--cpu", "--lowvram"]
    assert "8099" in launcher.app_command(cfg)


SERVER = """
import http.server, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        ok = self.path == sys.argv[2]
        self.send_response(200 if ok else 404); self.end_headers(); self.wfile.write(b"{}")
    def log_message(self, *a): pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
"""


def free_port() -> int:
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def why_not_answering(port: int, path: str) -> dict:
    """What a failure to answer looked like from here, for a run on a machine we cannot reach."""
    import socket
    import urllib.request
    out = {"proxies": urllib.request.getproxies()}
    with socket.socket() as s:
        s.settimeout(2)
        out["connect"] = s.connect_ex(("127.0.0.1", port))
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=3) as reply:
            out["urlopen"] = reply.status
    except Exception as exc:  # noqa: BLE001 - reported, not handled
        out["urlopen"] = repr(exc)
    return out


def test_the_launcher_starts_both_and_stops_both(monkeypatch, tmp_path):
    launcher = load_launcher(monkeypatch, tmp_path)
    server = tmp_path / "server.py"
    server.write_text(SERVER)
    app_port, engine_port = free_port(), free_port()
    monkeypatch.setattr(launcher, "COMFY", tmp_path)
    monkeypatch.setattr(launcher, "STUDIO", tmp_path)
    monkeypatch.setattr(launcher, "engine_command", lambda cfg: [sys.executable, str(server), str(engine_port), "/system_stats"])
    monkeypatch.setattr(launcher, "app_command", lambda cfg: [sys.executable, str(server), str(app_port), "/api/health"])
    cfg = dict(launcher.settings(), app_port=str(app_port), engine_port=str(engine_port))
    run = launcher.Launcher(cfg)
    run.start()
    try:
        recorded = json.loads(launcher.RUNNING.read_text())
        assert set(recorded) == {"engine", "app"}
        deadline = time.time() + 20
        seen = []
        while time.time() < deadline and "app ready" not in seen:
            seen.append(run.poll())
            time.sleep(0.2)
        logs = {name: log.read_text() if log.exists() else "(no log)" for name, (_, log) in run.programs.items()}
        assert "app ready" in seen, (sorted(set(seen)), logs, why_not_answering(app_port, "/api/health"))
        assert run.engine_ready, logs
        assert run.busy() == ""          # /api/state does not answer here: nothing to lose
    finally:
        run.stop()
    assert all(p.poll() is not None for p, _ in run.programs.values())
    assert not launcher.RUNNING.exists()
    assert "Stopped." in (tmp_path / "logs" / "launcher.log").read_text()


def test_a_stopped_engine_is_said_once_and_can_be_restarted(monkeypatch, tmp_path):
    launcher = load_launcher(monkeypatch, tmp_path)
    server = tmp_path / "server.py"
    server.write_text(SERVER)
    app_port = free_port()
    monkeypatch.setattr(launcher, "COMFY", tmp_path)
    monkeypatch.setattr(launcher, "STUDIO", tmp_path)
    monkeypatch.setattr(launcher, "engine_command", lambda cfg: [sys.executable, "-c", "raise SystemExit(3)"])
    monkeypatch.setattr(launcher, "app_command", lambda cfg: [sys.executable, str(server), str(app_port), "/api/health"])
    run = launcher.Launcher(dict(launcher.settings(), app_port=str(app_port), engine_port=str(free_port())))
    run.start()
    try:
        deadline = time.time() + 20
        seen = []
        while time.time() < deadline and "engine stopped" not in seen:
            seen.append(run.poll())
            time.sleep(0.2)
        assert seen.count("engine stopped") == 1
        assert run.poll() in ("", "app ready")   # said once, not every half second
        run.restart_engine()
        assert run.programs["engine"][0].pid != 0 and not run.engine_stopped
    finally:
        run.stop()


@pytest.mark.skipif(not shutil.which("ps"), reason="needs ps, as a Mac has")
def test_programs_left_by_a_killed_launcher_are_stopped_first(monkeypatch, tmp_path):
    launcher = load_launcher(monkeypatch, tmp_path)
    marker = tmp_path / "ComfyUI"
    monkeypatch.setattr(launcher, "COMFY", marker)
    (marker).mkdir()
    (marker / "main.py").write_text("import time\ntime.sleep(60)\n")
    leftover = subprocess.Popen([sys.executable, str(marker / "main.py")])
    stranger = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        launcher.RUNNING.parent.mkdir(parents=True)
        launcher.RUNNING.write_text(json.dumps({"engine": leftover.pid, "app": stranger.pid}))
        launcher.end_leftovers()
        assert leftover.wait(5) == -signal.SIGTERM
        assert stranger.poll() is None, "a process the launcher did not start was stopped"
        assert not launcher.RUNNING.exists()
    finally:
        for p in (leftover, stranger):
            p.kill()
            p.wait()


def test_the_launcher_says_what_is_missing(monkeypatch, tmp_path):
    launcher = load_launcher(monkeypatch, tmp_path)
    run = launcher.Launcher(dict(launcher.settings(), app_port=str(free_port()), engine_port=str(free_port())))
    assert "engine is not set up" in run.problem()


# ---------------------------------------------------------------- the update notice

MANIFEST = {
    "latest": "0.0.12",
    "notes": "https://example.invalid/releases/v0.0.12",
    "installer": {"url": "https://example.invalid/Yeufonic-Setup-0.0.12.exe", "sha256": "abc"},
    "docker": "git pull && docker compose up -d --build",
}


@pytest.fixture
def on_a_mac(monkeypatch):
    monkeypatch.setattr(config, "VERSION", "0.0.10")
    monkeypatch.setattr(update, "STATE", dict(update._initial(), install="macos"))


def test_a_mac_is_never_sent_the_windows_installer(on_a_mac):
    answer = update._from_manifest(MANIFEST)
    assert answer["installer"] is None
    assert answer["notes"] == MANIFEST["notes"]


def test_a_mac_is_sent_the_disk_image_the_manifest_names(on_a_mac):
    answer = update._from_manifest(dict(MANIFEST, macos={"url": "https://example.invalid/Yeufonic-0.0.12.dmg",
                                                         "sha256": "def"}))
    assert answer["installer"].endswith(".dmg") and answer["sha256"] == "def"
    assert "Applications" in update.advice()
    assert update.state()["line"] is None


def test_a_mac_finds_the_disk_image_among_the_release_assets(on_a_mac):
    assets = [{"name": "Yeufonic-Setup-0.0.12.exe", "browser_download_url": "https://example.invalid/a.exe"},
              {"name": "Yeufonic-0.0.12.dmg", "browser_download_url": "https://example.invalid/a.dmg", "digest": "sha256:1"}]
    assert update._installer_from(assets) == ("https://example.invalid/a.dmg", "sha256:1")
    update.STATE["install"] = "windows"
    assert update._installer_from(assets)[0] == "https://example.invalid/a.exe"
