"""The native Linux installer: checksum parity, .run self-extractor CLI, pre-flight checks, and launcher lifecycle."""
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LINUX = ROOT / "linux"
SETUP = LINUX / "setup.sh"
SETUP_PS1 = ROOT / "windows" / "setup.ps1"

needs_linux = pytest.mark.skipif(sys.platform == "win32", reason="bash scripts")


def load_launcher(monkeypatch, home: Path):
    monkeypatch.setenv("YEUFONIC_HOME", str(home / "install"))
    monkeypatch.setenv("YEUFONIC_LOGS", str(home / "logs"))
    spec = importlib.util.spec_from_file_location("linux_launcher", LINUX / "launcher.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------- checksum parity

def _linux_models() -> dict:
    text = SETUP.read_text(encoding="utf-8")
    block = re.search(r"model_list\(\) \{\n  cat <<LIST\n(.*?)\nLIST", text, re.S).group(1)
    out = {}
    copies = "https://huggingface.co/pshields/yue2-mothersuperior-copies/resolve/main"
    for line in block.splitlines():
        folder, name, size, sha, url, _lyrics, *copy = line.split("|")
        out[name] = {
            "dir": folder,
            "size": int(size),
            "sha": sha,
            "url": url.replace("$HF", "https://huggingface.co"),
            "copy": copy[0].replace("$COPIES", copies) if copy else None,
        }
    return out


def _windows_models() -> dict:
    text = SETUP_PS1.read_text(encoding="utf-8")
    core = text.split("$ModelFiles = @(", 1)[1].split("\n)\n", 1)[0]
    pics = text.split("$PictureFiles = @(", 1)[1].split("\n)\n", 1)[0]
    soundfonts = text.split("$SoundFontFiles = @(", 1)[1].split("\n)\n", 1)[0]
    out = {}
    for block in (core, pics, soundfonts):
        for entry in re.findall(r"@\{(.*?Size = \d+) \}", block, re.S):
            name = re.search(r"File = '([^']+)'", entry).group(1)
            url = re.search(r"Url = [\"']([^\"']+)[\"']", entry).group(1).replace("$HF", "https://huggingface.co")
            copy = re.search(r"Copy = \"([^\"]+)\"", entry)
            out[name] = {
                "size": int(re.search(r"Size = (\d+)", entry).group(1)),
                "sha": re.search(r"Sha = '([0-9a-f]{64})'", entry).group(1),
                "url": url,
                "copy": copy.group(1).replace("$Copies", "https://huggingface.co/pshields/yue2-mothersuperior-copies/resolve/main") if copy else None,
            }
    return out


def test_linux_fetches_the_same_core_models_and_checksums_as_windows():
    linux, windows = _linux_models(), _windows_models()
    assert linux, "no models found in linux/setup.sh"
    for name, entry in linux.items():
        assert name in windows, f"{name} is in linux/setup.sh but not windows/setup.ps1"
        for key in ("size", "sha", "url", "copy"):
            assert entry[key] == windows[name][key], f"{name}: {key} differs from windows/setup.ps1"


def test_linux_fetches_the_same_nvidia_picture_models_and_soundfonts_as_windows():
    text = SETUP.read_text(encoding="utf-8")
    windows = _windows_models()
    pic_block = re.search(r"picture_list\(\) \{\n  cat <<LIST\n(.*?)\nLIST", text, re.S).group(1)
    for line in pic_block.splitlines():
        _dir, name, size, sha, url = line.split("|")
        assert windows[name] == {
            "size": int(size),
            "sha": sha,
            "url": url.replace("$HF", "https://huggingface.co"),
            "copy": None,
        }
    sf_block = re.search(r"soundfont_list\(\) \{\n  cat <<LIST\n(.*?)\nLIST", text, re.S).group(1)
    for line in sf_block.splitlines():
        name, size, sha, url = line.split("|")
        assert windows[name] == {"size": int(size), "sha": sha, "url": url, "copy": None}


def test_linux_pins_the_same_engine_trainer_and_rvc_commits():
    linux = SETUP.read_text(encoding="utf-8")
    ps1 = SETUP_PS1.read_text(encoding="utf-8")
    engine_df = (ROOT / "engine" / "Dockerfile").read_text(encoding="utf-8")
    voice_df = (ROOT / "voice" / "Dockerfile").read_text(encoding="utf-8")
    comfy = re.search(r"^COMFY_COMMIT=([0-9a-f]{40})$", linux, re.M).group(1)
    trainer = re.search(r"^TRAINER_COMMIT=([0-9a-f]{40})$", linux, re.M).group(1)
    rvc = re.search(r"^RVC_COMMIT=([0-9a-f]{40})$", linux, re.M).group(1)
    assert f"ComfyCommit       = '{comfy}'" in ps1
    assert f"Yue2TrainerCommit = '{trainer}'" in ps1
    assert f"RvcCommit         = '{rvc}'" in ps1
    assert f"ARG COMFYUI_REF={comfy}" in engine_df
    assert f"ARG YUE2_TRAINER_REF={trainer}" in engine_df
    assert f"ARG RVC_COMMIT={rvc}" in voice_df


# --------------------------------------------------------------- .run packaging

@needs_linux
def test_build_run_supports_help_version_extract_only_and_checksum(tmp_path):
    out = tmp_path / "dist"
    res = subprocess.run(
        ["bash", str(LINUX / "build.sh")],
        env={**os.environ, "OUT": str(out), "VERSION": "0.0.99"},
        capture_output=True,
        text=True,
        check=True,
    )
    run_file = out / "yeufonic-0.0.99-linux-x86_64.run"
    assert run_file.is_file() and os.access(run_file, os.X_OK)
    assert (out / "yeufonic-0.0.99-linux-x86_64.run.sha256").is_file()

    ver = subprocess.run([str(run_file), "--version"], capture_output=True, text=True, check=True)
    assert "0.0.99" in ver.stdout

    hlp = subprocess.run([str(run_file), "--help"], capture_output=True, text=True, check=True)
    for flag in ("--install-dir", "--extract-only", "--no-desktop", "--force-downloads", "--check-only", "--skip-models"):
        assert flag in hlp.stdout

    extracted = tmp_path / "unpacked"
    ext = subprocess.run([str(run_file), "--extract-only", str(extracted)], capture_output=True, text=True, check=True)
    assert (extracted / "install.sh").is_file()
    assert (extracted / "setup.sh").is_file()
    assert (extracted / "launcher.py").is_file()
    assert (extracted / "studio" / "VERSION").read_text(encoding="utf-8").strip() == "0.0.99"

    # A corrupted payload must be rejected before extraction.
    bad = tmp_path / "corrupt.run"
    data = bytearray(run_file.read_bytes())
    data[-1] ^= 0xFF
    bad.write_bytes(bytes(data))
    bad.chmod(0o755)
    fail = subprocess.run([str(bad), "--extract-only", str(tmp_path / "nope")], capture_output=True, text=True)
    assert fail.returncode != 0
    assert "checksum mismatch" in fail.stderr.lower()


# --------------------------------------------------------------- setup.sh checks

def _fake_linux(tmp_path: Path, arch="x86_64", glibc="2.39", gpu="RTX 4070, 16384, 580.10, 8.9",
                has_libcuda=True, has_smi=True) -> dict:
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    tools = {
        "uname": f'[ "$1" = -m ] && echo {arch} || echo Linux',
        "ldd": f'echo "ldd (GNU libc) {glibc}"',
        "curl": "exit 0",
        "ldconfig": (
            'echo "libcuda.so.1 => /usr/lib/libcuda.so.1"\n'
            'echo "libgomp.so.1 => /usr/lib/libgomp.so.1"\n'
            'echo "libGL.so.1 => /usr/lib/libGL.so.1"\n'
            'echo "libglib-2.0.so.0 => /usr/lib/libglib-2.0.so.0"'
        ) if has_libcuda else 'echo "libgomp.so.1 => /usr/lib/libgomp.so.1"',
        "df": 'echo "Filesystem 1024-blocks Used Available Capacity Mounted"\necho "/dev/sda1 200000000 50000000 150000000 25% /"',
    }
    if has_smi:
        tools["nvidia-smi"] = f'echo "{gpu}"'
    for name, body in tools.items():
        p = bin_dir / name
        p.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        p.chmod(0o755)
    return {**os.environ, "PATH": f"{bin_dir}:/usr/bin:/bin"}


@needs_linux
def test_check_only_passes_on_suitable_linux_and_warns_on_cu128_driver(tmp_path):
    env = _fake_linux(tmp_path, gpu="RTX 4070, 16384, 550.54, 8.9")
    res = subprocess.run(
        ["bash", str(SETUP), "--install-dir", str(tmp_path / "inst"), "--check-only"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "cu128" in res.stdout
    assert "This machine is suitable." in res.stdout


@needs_linux
def test_check_only_rejects_old_glibc_or_old_gpu(tmp_path):
    env_glibc = _fake_linux(tmp_path / "a", glibc="2.17")
    r1 = subprocess.run(
        ["bash", str(SETUP), "--install-dir", str(tmp_path / "inst1"), "--check-only"],
        env=env_glibc,
        capture_output=True,
        text=True,
    )
    assert r1.returncode != 0
    assert "glibc 2.17" in r1.stdout

    env_gpu = _fake_linux(tmp_path / "b", gpu="GTX 1080, 8192, 580.10, 6.1")
    r2 = subprocess.run(
        ["bash", str(SETUP), "--install-dir", str(tmp_path / "inst2"), "--check-only"],
        env=env_gpu,
        capture_output=True,
        text=True,
    )
    assert r2.returncode != 0
    assert "compute 6.1" in r2.stdout


# --------------------------------------------------------------- launcher

def test_launcher_sets_cuda12_libs_no_proxy_and_linux_install_kind(tmp_path, monkeypatch):
    mod = load_launcher(monkeypatch, tmp_path)
    cfg = mod.settings()
    e_env = mod.engine_env(cfg)
    a_env = mod.app_env(cfg)
    assert e_env["CUDA12_LIBS"] == str(mod.CUDA12_LIBS)
    assert a_env["YEUFONIC_INSTALL"] == "linux"
    assert "127.0.0.1" in a_env["NO_PROXY"] and "localhost" in a_env["no_proxy"]
    assert str(mod.TOOLS) in a_env["PATH"].split(os.pathsep)


def test_launcher_reads_settings_ini_ports_and_model(tmp_path, monkeypatch):
    mod = load_launcher(monkeypatch, tmp_path)
    mod.HOME_DIR.mkdir(parents=True, exist_ok=True)
    (mod.HOME_DIR / "settings.ini").write_text(
        "[yue2]\napp_port = 8095\nengine_port = 8195\nmodel = int8\nopen_browser = no\n",
        encoding="utf-8",
    )
    cfg = mod.settings()
    assert cfg["app_port"] == "8095"
    assert cfg["engine_port"] == "8195"
    assert cfg["model"] == "int8"
    assert mod.app_env(cfg)["YUE2_CHECKPOINT"] == "int8"


@needs_linux
def test_get_verified_skips_present_files_and_honors_force_downloads(tmp_path):
    """Existing models/LoRAs are skipped by default (with one-time checksum if .sha256ok is absent),
    and re-downloaded when FORCE_DOWNLOADS=1."""
    import hashlib

    src = tmp_path / "server_file.bin"
    payload = b"hello yeufonic model bytes" * 100
    src.write_bytes(payload)
    sha = hashlib.sha256(payload).hexdigest()
    size = len(payload)

    # Extract only the helper definitions from setup.sh (up to the system check section).
    setup_text = SETUP.read_text(encoding="utf-8")
    helpers = setup_text.split("# ------------------------------------------------------------------- helpers", 1)[1]
    helpers = helpers.split("# -------------------------------------------------------------- system check", 1)[0]

    harness = tmp_path / "harness.sh"
    harness.write_text(
        f"#!/bin/bash\nset -euo pipefail\n"
        f"IS_TTY=0\nCHECK_ONLY=1\nLOGS={tmp_path}\nSTATE={tmp_path}\nDOWNLOADS={tmp_path}\n"
        f"FORCE_DOWNLOADS=${{FORCE_DOWNLOADS:-0}}\nexec 3>&1 4>&2\n"
        f"{helpers}\n"
        f'get_verified "$@"\n',
        encoding="utf-8",
    )
    harness.chmod(0o755)
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
    fake_curl = fakebin / "curl"
    fake_curl.write_text(
        "#!/bin/sh\n"
        "out=''\n"
        "url=''\n"
        "while [ $# -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    -o) out=\"$2\"; shift 2 ;;\n"
        "    -C|--retry) shift 2 ;;\n"
        "    -*) shift ;;\n"
        "    *) url=\"$1\"; shift ;;\n"
        "  esac\n"
        "done\n"
        "cp \"${url#file://}\" \"$out\"\n",
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)
    base_env = {**os.environ, "PATH": f"{fakebin}:{os.environ.get('PATH', '/usr/bin:/bin')}"}

    dest = tmp_path / "dest.bin"
    url = f"file://{src}"

    # 1. Fresh download works and writes .sha256ok
    r1 = subprocess.run([str(harness), url, str(dest), str(size), sha, "", "[1/1]"], env=base_env, capture_output=True, text=True, check=True)
    assert "Downloading dest.bin" in r1.stdout
    assert dest.read_bytes() == payload
    assert (tmp_path / "dest.bin.sha256ok").is_file()

    # 2. Second run skips immediately without downloading
    r2 = subprocess.run([str(harness), url, str(dest), str(size), sha, "", "[1/1]"], env=base_env, capture_output=True, text=True, check=True)
    assert "already present, skipping" in r2.stdout
    assert "Downloading" not in r2.stdout

    # 3. Existing file without .sha256ok (e.g. copied from Docker) verifies once and skips downloading
    (tmp_path / "dest.bin.sha256ok").unlink()
    r3 = subprocess.run([str(harness), url, str(dest), str(size), sha, "", "[1/1]"], env=base_env, capture_output=True, text=True, check=True)
    assert "already present, verifying checksum" in r3.stdout
    assert "Downloading" not in r3.stdout
    assert (tmp_path / "dest.bin.sha256ok").is_file()

    # 4. KeepIfPresent=1 (style LoRAs) skips even a modified user file when FORCE_DOWNLOADS=0
    dest.write_bytes(b"custom user lora")
    (tmp_path / "dest.bin.sha256ok").unlink()
    r4 = subprocess.run([str(harness), url, str(dest), str(size), sha, "", "[1/1]", "1"], env=base_env, capture_output=True, text=True, check=True)
    assert "already present, skipping" in r4.stdout
    assert dest.read_bytes() == b"custom user lora"

    # 5. FORCE_DOWNLOADS=1 re-downloads even when present
    r5 = subprocess.run(
        [str(harness), url, str(dest), str(size), sha, "", "[1/1]", "1"],
        env={**base_env, "FORCE_DOWNLOADS": "1"},
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Downloading dest.bin" in r5.stdout
    assert dest.read_bytes() == payload


@needs_linux
def test_interactive_prompts_display_prompt_on_tty_and_record_answers(tmp_path):
    """ask_yes_no must write its prompt visibly to the TTY and set the variable to yes/no (not swallow it in $())."""
    import pty
    import select

    setup_text = SETUP.read_text(encoding="utf-8")
    m = re.search(r"ask_yes_no\(\) \{.*?\n\}", setup_text, re.S)
    assert m, "ask_yes_no not found in linux/setup.sh"

    script = tmp_path / "ask.sh"
    script.write_text(
        f"#!/bin/bash\nset -euo pipefail\nCHECK_ONLY=1\nLOGS={tmp_path}\n"
        f"log_line() {{ :; }}\n"
        f"say() {{ printf '%s\\n' \"$*\"; }}\n"
        f"{m.group(0)}\n"
        f"PICTURES=''; LORAS=''\n"
        f"say 'Take pictures drawn on this PC (optional)'\n"
        f"ask_yes_no PICTURES 'Set up local take pictures?'\n"
        f"say 'Style LoRAs (optional)'\n"
        f"ask_yes_no LORAS 'Fetch the style LoRAs?'\n"
        f"echo \"GOT_PICTURES=$PICTURES GOT_LORAS=$LORAS\"\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    master, slave = pty.openpty()
    proc = subprocess.Popen([str(script)], stdin=slave, stdout=slave, stderr=slave, close_fds=True)
    os.close(slave)
    out = bytearray()
    answers = [b"y\n", b"n\n"]
    sent = 0
    deadline = time.time() + 5
    while time.time() < deadline:
        r, _, _ = select.select([master], [], [], 0.1)
        if r:
            try:
                chunk = os.read(master, 4096)
                if not chunk:
                    break
                out.extend(chunk)
                text = out.decode("utf-8", errors="replace")
                if sent == 0 and "Set up local take pictures? [y/N] " in text:
                    os.write(master, answers[0])
                    sent = 1
                elif sent == 1 and "Fetch the style LoRAs? [y/N] " in text:
                    os.write(master, answers[1])
                    sent = 2
            except OSError:
                break
        elif proc.poll() is not None:
            break
    os.close(master)
    rc = proc.wait(timeout=5)
    text = out.decode("utf-8", errors="replace")
    assert rc == 0, text
    assert "Set up local take pictures? [y/N] " in text
    assert "Fetch the style LoRAs? [y/N] " in text
    assert "GOT_PICTURES=yes GOT_LORAS=no" in text


@needs_linux
def test_port_taken_detects_listening_and_free_ports_instantly(tmp_path):
    """port_taken reads /proc/net/tcp{,6} directly — instant, no hang, and does not touch FD 3."""
    import socket

    setup_text = SETUP.read_text(encoding="utf-8")
    m = re.search(r"port_taken\(\) \{.*?\n\}", setup_text, re.S)
    assert m, "port_taken not found in linux/setup.sh"

    script = tmp_path / "pt.sh"
    script.write_text(f"#!/bin/bash\nset -euo pipefail\n{m.group(0)}\nport_taken \"$1\"\n", encoding="utf-8")
    script.chmod(0o755)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        busy_port = srv.getsockname()[1]
        r_busy = subprocess.run([str(script), str(busy_port)], timeout=2)
        assert r_busy.returncode == 0
    r_free = subprocess.run([str(script), str(busy_port)], timeout=2)
    assert r_free.returncode != 0


def test_phase1_build_scripts_match_pinned_versions_and_workflows():
    fs_linux = (LINUX / "build-fluidsynth.sh").read_text(encoding="utf-8")
    fs_macos = (ROOT / "macos" / "build-fluidsynth.sh").read_text(encoding="utf-8")
    for var in ("FLUIDSYNTH_VERSION", "FLUIDSYNTH_SHA", "SNDFILE_VERSION", "SNDFILE_SHA"):
        m_l = re.search(rf"^{var}=(\S+)$", fs_linux, re.M)
        m_m = re.search(rf"^{var}=(\S+)$", fs_macos, re.M)
        assert m_l and m_m and m_l.group(1) == m_m.group(1), f"{var} differs between Linux and macOS FluidSynth builds"

    cpp_linux = (LINUX / "build-cpp.sh").read_text(encoding="utf-8")
    assert "engine-cpp/Dockerfile" in cpp_linux
    assert "engine-pictures/Dockerfile" in cpp_linux
    assert "CMAKE_INSTALL_RPATH=$ORIGIN" in cpp_linux
    assert "check_glibc_floor" in cpp_linux
    assert (ROOT / ".github" / "workflows" / "fluidsynth-linux.yml").is_file()
    assert (ROOT / ".github" / "workflows" / "engine-cpp-linux.yml").is_file()

    # Both Phase 1 pre-releases must be pinned in linux/setup.sh with URL, 64-hex SHA-256, and byte size.
    setup = SETUP.read_text(encoding="utf-8")
    for prefix in ("FLUIDSYNTH", "CPP"):
        url_m = re.search(rf'^{prefix}_URL="\$\{{YEUFONIC_{prefix}_URL:-(https://github\.com/yeufonic/yeufonic/releases/download/[^"]+\.tar\.gz)\}}"$', setup, re.M)
        sha_m = re.search(rf'^{prefix}_SHA="\$\{{YEUFONIC_{prefix}_SHA:-([0-9a-f]{{64}})\}}"$', setup, re.M)
        size_m = re.search(rf'^{prefix}_SIZE="\$\{{YEUFONIC_{prefix}_SIZE:-([0-9]+)\}}"$', setup, re.M)
        assert url_m, f"{prefix}_URL is not pinned in linux/setup.sh"
        assert sha_m, f"{prefix}_SHA is not pinned in linux/setup.sh"
        assert size_m and int(size_m.group(1)) > 0, f"{prefix}_SIZE is not pinned in linux/setup.sh"


def test_launcher_cpp_env_prepends_bundled_cuda_dir_and_preserves_existing_ld_library_path(tmp_path, monkeypatch):
    monkeypatch.setenv("LD_LIBRARY_PATH", "/usr/lib/wsl/lib")
    mod = load_launcher(monkeypatch, tmp_path)
    env = mod._cpp_env()
    parts = env["LD_LIBRARY_PATH"].split(os.pathsep)
    assert parts[0] == str(mod.CPP / "yue2cpp")
    assert "/usr/lib/wsl/lib" in parts
    assert "127.0.0.1" in env["NO_PROXY"] and "localhost" in env["no_proxy"]


@needs_linux
def test_reconfigure_allows_switching_engine_interactively_with_saved_defaults(tmp_path):
    """Running setup.sh --reconfigure on a TTY re-asks engine & model with current settings pre-selected."""
    import pty
    import select

    inst = tmp_path / "inst"
    state = inst / "state"
    state.mkdir(parents=True)
    (state / "engine").write_text("comfyui\n", encoding="utf-8")
    (state / "model").write_text("bf16\n", encoding="utf-8")
    (state / "lyrics").write_text("yes\n", encoding="utf-8")
    (state / "pictures").write_text("no\n", encoding="utf-8")
    (state / "loras").write_text("yes\n", encoding="utf-8")
    (state / "voices").write_text("no\n", encoding="utf-8")

    env = _fake_linux(tmp_path)
    # Provide a fake CPP_URL so yue2cpp is selectable during pre-flight; stop right after prompts via bad network?
    # Better: pass --skip-models and fake curl failing on network so it stops cleanly right after saving state/ choices.
    (tmp_path / "fakebin" / "curl").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    env["YEUFONIC_CPP_URL"] = "https://example.invalid/yue2cpp-linux-test.tar.gz"

    master, slave = pty.openpty()
    proc = subprocess.Popen(
        ["bash", str(SETUP), "--install-dir", str(inst), "--reconfigure", "--skip-models"],
        env=env,
        stdin=slave,
        stdout=slave,
        stderr=slave,
        close_fds=True,
    )
    os.close(slave)
    out = bytearray()
    prompts = [
        ("Choose engine (1 or 2) [1]: ", b"2\n"),          # switch comfyui -> yue2cpp
        ("Choose yue2.cpp model (1 or 2) [1]: ", b"2\n"),  # pick bf16
        ("Include local Gemma 4? [Y/n] ", b"\n"),          # keep yes
        ("Set up local take pictures? [y/N] ", b"\n"),     # keep saved 'no' (shown as [y/N]!)
        ("Fetch the style LoRAs? [Y/n] ", b"\n"),          # keep saved 'yes' (shown as [Y/n]!)
        ("Set up recorded voices? [y/N] ", b"\n"),         # keep saved 'no'
    ]
    step = 0
    deadline = time.time() + 10
    while time.time() < deadline:
        r, _, _ = select.select([master], [], [], 0.1)
        if r:
            try:
                chunk = os.read(master, 4096)
                if not chunk:
                    break
                out.extend(chunk)
                text = out.decode("utf-8", errors="replace")
                while step < len(prompts) and prompts[step][0] in text:
                    os.write(master, prompts[step][1])
                    step += 1
            except OSError:
                break
        elif proc.poll() is not None:
            break
    os.close(master)
    proc.wait(timeout=5)
    text = out.decode("utf-8", errors="replace")
    assert step == len(prompts), f"stopped at prompt {step}:\n{text}"
    assert (state / "engine").read_text(encoding="utf-8").strip() == "yue2cpp"
    assert (state / "cpp-model").read_text(encoding="utf-8").strip() == "bf16"
    assert (state / "lyrics").read_text(encoding="utf-8").strip() == "yes"
    assert (state / "pictures").read_text(encoding="utf-8").strip() == "no"
    assert (state / "loras").read_text(encoding="utf-8").strip() == "yes"
    assert (state / "voices").read_text(encoding="utf-8").strip() == "no"




