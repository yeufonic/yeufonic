"""The engine's stem separation node: what it hands back, with a stand-in for the model."""
import importlib.util
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("demucs")

NODE = Path(__file__).resolve().parent.parent / "engine" / "custom_nodes" / "yue2_harmony" / "separate.py"
spec = importlib.util.spec_from_file_location("yue2_separate", NODE)
separate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(separate)


class FakeModel:
    sources = ["drums", "bass", "other", "vocals"]
    samplerate = 44100
    audio_channels = 2

    def eval(self):
        return self

    def to(self, device):
        return self


@pytest.fixture
def fake(monkeypatch):
    separate._CACHE.clear()
    separate._CACHE["htdemucs"] = FakeModel()
    seen = {}

    def apply_model(model, wav, **kwargs):
        seen.update(kwargs, shape=tuple(wav.shape))
        # four stems, each a constant, so what is summed is easy to check
        out = torch.stack([torch.full_like(wav[0], v) for v in (0.1, 0.2, 0.3, 0.4)])
        return out[None]

    monkeypatch.setattr("demucs.apply.apply_model", apply_model)
    yield seen
    separate._CACHE.clear()


def test_the_instruments_are_everything_but_the_vocal(fake):
    wave = torch.randn(2, 4410) * 0.1
    stems, rate = separate.separate(wave, 44100, "htdemucs", 1, 0.25, "cpu")
    assert rate == 44100
    assert set(stems) == {"drums", "bass", "other", "vocals", "instruments"}
    assert stems["instruments"].shape == stems["vocals"].shape == (2, 4410)
    # the model's stems are scaled back by the track's own spread and mean, so compare the sum, not the constants
    total = stems["drums"] + stems["bass"] + stems["other"]
    assert torch.allclose(stems["instruments"], total, atol=1e-5)


def test_a_track_at_another_rate_and_channel_count_is_brought_to_the_models(fake):
    mono = torch.randn(1, 22050) * 0.1
    stems, rate = separate.separate(mono, 22050, "htdemucs", 0, 0.25, "cpu")
    assert rate == 44100 and stems["vocals"].shape[0] == 2
    assert fake["shape"][1:] == (2, 44100), "run at the model's rate and channels"
    assert fake["shifts"] == 0 and fake["split"] is True and fake["overlap"] == 0.25


def test_progress_is_reported_as_a_share_of_the_work(fake, monkeypatch):
    got = []

    def apply_model(model, wav, callback=None, **kwargs):
        length = wav.shape[-1]
        for offset in (0, length // 2):
            callback({"state": "start", "model_idx_in_bag": 0, "shift_idx": 0, "segment_offset": offset})
            callback({"state": "end", "model_idx_in_bag": 0, "shift_idx": 0, "segment_offset": offset})
        return torch.zeros(1, 4, 2, length)

    monkeypatch.setattr("demucs.apply.apply_model", apply_model)

    class Interrupt:
        @staticmethod
        def throw_exception_if_processing_interrupted():
            pass

    import sys
    import types
    comfy = types.ModuleType("comfy")
    comfy.model_management = Interrupt
    monkeypatch.setitem(sys.modules, "comfy", comfy)
    monkeypatch.setitem(sys.modules, "comfy.model_management", Interrupt)
    separate.separate(torch.zeros(2, 1000), 44100, "htdemucs", 1, 0.25, "cpu", on_progress=got.append)
    assert got == [0.0, 0.5] and all(0 <= x <= 1 for x in got)


def test_the_node_lists_a_stem_for_every_output():
    assert separate.OUTPUTS[-1] == "instruments" and len(separate.Yue2Separate.RETURN_TYPES) == len(separate.OUTPUTS)
    assert separate.silence(44100)["waveform"].shape[-1] == 1


# ------------------------------------------------------------------ the Whisper node
HEAR = Path(__file__).resolve().parent.parent / "engine" / "custom_nodes" / "yue2_harmony" / "hear.py"
hear_spec = importlib.util.spec_from_file_location("yue2_hear", HEAR)
hearing = importlib.util.module_from_spec(hear_spec)
hear_spec.loader.exec_module(hearing)


class Heard:
    def __init__(self, *rows):
        self.rows = rows
        self.options = None

    def transcribe(self, audio, **options):
        self.audio, self.options = audio, options
        return iter([type("Seg", (), {"start": a, "end": b, "text": t}) for a, b, t in self.rows]), None


def test_the_node_hears_with_the_options_the_cpu_uses():
    model = Heard((0.0, 2.0, " one"), (2.0, 4.0, " two"))
    seen = []
    out = hearing.hear(torch.zeros(2, 44100 * 4), 44100, "large-v3-turbo", "en", on_progress=seen.append, model=model)
    assert out == [{"start": 0.0, "end": 2.0, "text": " one"}, {"start": 2.0, "end": 4.0, "text": " two"}]
    assert seen == [0.5, 1.0]
    assert model.audio.shape == (64000,) and model.audio.dtype.name == "float32", "mono, 16 kHz"
    assert model.options == {"language": "en", "vad_filter": False, "beam_size": 5, "condition_on_previous_text": False,
                             "word_timestamps": True, "hallucination_silence_threshold": 2.0}


def test_the_node_can_be_stopped_between_segments():
    class Stop(Exception):
        pass

    def check():
        raise Stop()

    with pytest.raises(Stop):
        hearing.hear(torch.zeros(1, 16000), 16000, "large-v3-turbo", "", check=check, model=Heard((0.0, 1.0, "x")))


def test_the_node_uses_a_plain_folder_of_the_model_when_there_is_one(monkeypatch, tmp_path):
    """What scripts/fetch-models.sh writes, used as it stands; otherwise the model's name, for the Hugging Face cache."""
    import sys
    import types
    import faster_whisper

    folder_paths = types.ModuleType("folder_paths")
    folder_paths.models_dir = str(tmp_path)
    monkeypatch.setitem(sys.modules, "folder_paths", folder_paths)
    asked = []
    monkeypatch.setattr(faster_whisper, "WhisperModel", lambda target, **kw: asked.append((target, kw["local_files_only"])) or object())
    hearing.load("large-v3-turbo")
    assert asked[-1][0] == "large-v3-turbo"
    plain = tmp_path / "whisper" / "large-v3-turbo"
    plain.mkdir(parents=True)
    (plain / "model.bin").write_bytes(b"x")
    hearing.load("large-v3-turbo")
    assert asked[-1] == (str(plain), True)


def test_what_the_engine_fetches_is_left_deletable_by_whoever_owns_the_folder(tmp_path):
    """The engine runs as root: a folder it makes is root's, and a user without root could not tidy it."""
    import os

    perms_spec = importlib.util.spec_from_file_location("yue2_perms", NODE.with_name("perms.py"))
    perms = importlib.util.module_from_spec(perms_spec)
    perms_spec.loader.exec_module(perms)
    root = tmp_path / "whisper"
    (root / "models--x" / "blobs").mkdir(parents=True)
    blob = root / "models--x" / "blobs" / "abc"
    blob.write_bytes(b"x")
    os.chmod(blob, 0o600)
    os.chmod(root, 0o700)
    link = root / "models--x" / "link"
    link.symlink_to("blobs/abc")
    perms.open_up(str(root))
    assert (root.stat().st_mode & 0o777) == 0o777 and ((root / "models--x" / "blobs").stat().st_mode & 0o777) == 0o777
    assert (blob.stat().st_mode & 0o666) == 0o666
    perms.open_up(str(tmp_path / "missing"))     # nothing there: nothing to do


def test_on_windows_whisper_runs_in_a_process_of_its_own(monkeypatch, tmp_path):
    """Its CUDA 12 cuDNN and PyTorch's CUDA 13 one share a name, so the engine's own first use of cuDNN broke when
    Whisper's libraries were put where it could see them.  The worker has its own process and its own PATH."""
    import sys
    import types

    folder_paths = types.ModuleType("folder_paths")
    folder_paths.models_dir = str(tmp_path)
    monkeypatch.setitem(sys.modules, "folder_paths", folder_paths)
    stub = tmp_path / "worker.py"
    stub.write_text("import sys, json\nprint('P 0.5', flush=True)\nprint('noise', flush=True)\n"
                    "print('R', json.dumps([{'start': 0.0, 'end': 1.0, 'text': ' hi'}]), flush=True)\n")
    monkeypatch.setattr(hearing, "ISOLATE", True)
    monkeypatch.setattr(hearing, "WORKER", stub)
    seen = []
    out = hearing.hear(torch.zeros(1, 16000), 16000, "large-v3-turbo", "en", on_progress=seen.append)
    assert out == [{"start": 0.0, "end": 1.0, "text": " hi"}] and seen == [0.5]
    # the engine's own PATH is not touched, only the worker's
    import os
    before = os.environ["PATH"]
    hearing.worker_env()
    assert os.environ["PATH"] == before


def test_the_worker_is_ended_when_the_job_is_stopped_and_a_failure_says_why(monkeypatch, tmp_path):
    import sys
    import types

    folder_paths = types.ModuleType("folder_paths")
    folder_paths.models_dir = str(tmp_path)
    monkeypatch.setitem(sys.modules, "folder_paths", folder_paths)
    slow = tmp_path / "slow.py"
    slow.write_text("import time\nprint('loading', flush=True)\ntime.sleep(60)\n")
    broken = tmp_path / "broken.py"
    broken.write_text("print('cublas64_12.dll is not found', flush=True)\nraise SystemExit(1)\n")
    monkeypatch.setattr(hearing, "ISOLATE", True)

    class Stop(Exception):
        pass

    calls = []

    def check():
        calls.append(1)
        if len(calls) > 2:
            raise Stop()

    monkeypatch.setattr(hearing, "WORKER", slow)
    with pytest.raises(Stop):
        hearing.hear(torch.zeros(1, 16000), 16000, "large-v3-turbo", "", check=check)
    monkeypatch.setattr(hearing, "WORKER", broken)
    with pytest.raises(RuntimeError, match="cublas64_12.dll is not found"):
        hearing.hear(torch.zeros(1, 16000), 16000, "large-v3-turbo", "")


def test_choosing_yue2cpp_keeps_a_compose_override(tmp_path):
    """Naming the files in COMPOSE_FILE stops compose reading compose.override.yml by itself, so the line names it."""
    import re, subprocess
    script = (Path(__file__).resolve().parent.parent / "scripts" / "fetch-models.sh").read_text(encoding="utf-8")
    snippet = re.search(r"^  if ! grep -qs '\^COMPOSE_FILE=' .*?^  fi$", script, re.S | re.M).group(0)
    for override, files in ((False, "compose.yml:compose.cpp.yml"),
                            (True, "compose.yml:compose.cpp.yml:compose.override.yml")):
        (tmp_path / ".env").write_text("APP_UID=1000", encoding="utf-8")
        (tmp_path / "compose.override.yml").unlink(missing_ok=True)
        if override:
            (tmp_path / "compose.override.yml").write_text("services: {}\n", encoding="utf-8")
        subprocess.run(["sh", "-c", snippet], env={"ROOT": str(tmp_path), "PATH": "/usr/bin:/bin"}, check=True,
                       capture_output=True)
        assert (tmp_path / ".env").read_text(encoding="utf-8").splitlines() == ["APP_UID=1000", f"COMPOSE_FILE={files}"]


def _run_fetch(tmp_path, *args, env_text="", override=False, containers=(), gpu="", build=False):
    """fetch-models.sh in a folder of its own, with curl and docker stood in for: nothing is downloaded or stopped."""
    import shutil, stat, subprocess
    root = tmp_path / "yeufonic"
    if not root.exists():
        (root / "scripts").mkdir(parents=True)
        shutil.copy(Path(__file__).resolve().parent.parent / "scripts" / "fetch-models.sh", root / "scripts")
        shutil.copy(Path(__file__).resolve().parent.parent / "compose.cpp.yml", root)
        (root / ".env").write_text(env_text, encoding="utf-8")
    if override:
        (root / "compose.override.yml").write_text("services: {}\n", encoding="utf-8")
    bin_ = tmp_path / "bin"
    bin_.mkdir(exist_ok=True)
    if gpu:
        (bin_ / "nvidia-smi").write_text(f'#!/bin/sh\necho "{gpu}"\n')
    (bin_ / "curl").write_text('#!/bin/sh\nwhile [ $# -gt 0 ]; do [ "$1" = -o ] && echo x > "$2"; shift; done\n')
    # docker: inspect answers this checkout's folder for the containers named; rm and the rest are recorded.
    (bin_ / "docker").write_text(
        '#!/bin/sh\necho "$@" >> "%s/docker.log"\n'
        'if [ "$1" = inspect ]; then for c in %s; do [ "$c" = "$4" ] && { echo "%s"; exit 0; }; done; exit 1; fi\n'
        % (tmp_path, " ".join(containers) or "none", root))
    for f in ("curl", "docker", "nvidia-smi"):
        if not (bin_ / f).exists():
            continue
        (bin_ / f).chmod((bin_ / f).stat().st_mode | stat.S_IEXEC)
    out = subprocess.run(["sh", str(root / "scripts" / "fetch-models.sh"), *args], capture_output=True, text=True,
                         env={"PATH": f"{bin_}:/usr/bin:/bin", "HOME": str(tmp_path),
                              **({"YUE2CPP_BUILD": "1"} if build else {})})
    assert out.returncode == 0, out.stderr
    log = tmp_path / "docker.log"
    return root, out.stdout, (log.read_text() if log.exists() else "")


def test_gemma_is_fetched_for_yue2cpp_when_asked(tmp_path):
    """--gemma was read as the Gemma download address, so it never fetched Gemma or chose its service."""
    root, said, docker = _run_fetch(tmp_path, "--cpp", "--gemma", "--pictures", env_text="APP_UID=1000\n")
    assert "ollama pull gemma4:e4b-it-qat" in docker
    assert "COMPOSE_PROFILES=gemma,pictures" in (root / ".env").read_text()


def test_switching_engines_takes_one_command_each_way(tmp_path):
    """--cpp chooses yue2.cpp and removes the ComfyUI engine left running; --comfyui takes yue2.cpp out of .env
    again, keeping the rest of it, and removes yue2.cpp's three; a run with neither keeps the engine as it is."""
    root, said, docker = _run_fetch(tmp_path, "--cpp", "--gemma", "--pictures", override=True,
                                    env_text="APP_UID=1000\nAPP_GID=1024\nCOMPOSE_PROFILES=mine\n",
                                    containers=("yeufonic-engine",))
    env = (root / ".env").read_text().splitlines()
    assert "COMPOSE_FILE=compose.yml:compose.cpp.yml:compose.override.yml" in env
    assert "COMPOSE_PROFILES=mine,gemma,pictures" in env
    assert "rm -f yeufonic-engine" in docker and "switching the engine from comfyui to cpp" in said

    (tmp_path / "docker.log").unlink()
    root, said, docker = _run_fetch(tmp_path)
    assert "switching the engine" not in said and "rm -f" not in docker
    assert "COMPOSE_FILE=compose.yml:compose.cpp.yml:compose.override.yml" in (root / ".env").read_text()

    root, said, docker = _run_fetch(tmp_path, "--comfyui", containers=("yeufonic-engine-cpp", "yeufonic-gemma"))
    assert (root / ".env").read_text().splitlines() == ["APP_UID=1000", "APP_GID=1024", "COMPOSE_PROFILES=mine"]
    assert "rm -f yeufonic-engine-cpp" in docker and "rm -f yeufonic-gemma" in docker
    assert "rm -f yeufonic-pictures" not in docker            # not this checkout's: left alone


def test_a_compose_file_line_of_your_own_keeps_its_other_files(tmp_path):
    root, _, _ = _run_fetch(tmp_path, "--comfyui",
                            env_text="COMPOSE_FILE=compose.yml:compose.cpp.yml:compose.gpu2.yml\nCOMPOSE_PROFILES=gemma\n")
    assert (root / ".env").read_text().splitlines() == ["COMPOSE_FILE=compose.yml:compose.gpu2.yml"]


def test_yue2cpp_built_here_is_built_for_this_pcs_card(tmp_path):
    """The ready-made images need no build; one built here (YUE2CPP_BUILD=1) is compiled for this PC's card alone,
    which takes a fraction of the time every card does."""
    root, said, _ = _run_fetch(tmp_path, "--cpp", env_text="APP_UID=1000\n", gpu="8.9")
    env = (root / ".env").read_text().splitlines()
    assert "COMPOSE_FILE=compose.yml:compose.cpp.yml" in env and not any("CUDA_ARCH" in line for line in env)
    built = tmp_path / "built"
    built.mkdir()
    root, _, _ = _run_fetch(built, "--cpp", env_text="APP_UID=1000\n", gpu="8.9", build=True)
    env = (root / ".env").read_text().splitlines()
    assert "COMPOSE_FILE=compose.yml:compose.cpp.yml:compose.cpp-build.yml" in env and "YUE2CPP_CUDA_ARCH=89" in env
    root, _, _ = _run_fetch(built, "--comfyui")
    assert not any(line.startswith("COMPOSE_FILE=") for line in (root / ".env").read_text().splitlines())
    other = tmp_path / "other"
    other.mkdir()
    root, _, _ = _run_fetch(other, "--cpp", env_text="YUE2CPP_CUDA_ARCH=86\n", gpu="8.9", build=True)
    assert (root / ".env").read_text().count("YUE2CPP_CUDA_ARCH") == 1          # a choice already made stays


def test_the_ready_made_images_are_the_ones_their_folders_build():
    """compose.cpp.yml names each image by a hash of the folder it is built from, so a change to that folder needs
    the new tag here, and the workflow builds and publishes the image under it."""
    import re, subprocess
    root = Path(__file__).resolve().parent.parent
    compose = (root / "compose.cpp.yml").read_text(encoding="utf-8")
    for folder, name in (("engine-cpp", "yeufonic-engine-cpp"), ("engine-pictures", "yeufonic-pictures")):
        tag = subprocess.run(["sh", str(root / "scripts" / "engine-image-tag.sh"), folder], capture_output=True,
                             text=True, check=True).stdout.strip()
        assert re.fullmatch(r"[0-9a-f]{12}", tag)
        assert f"image: ghcr.io/yeufonic/{name}:{tag}\n" in compose, f"{folder}/ changed: name {name}:{tag}"
    workflow = (root / ".github" / "workflows" / "engine-images.yml").read_text(encoding="utf-8")
    assert "scripts/engine-image-tag.sh" in workflow and "push-to-registry: true" in workflow
    assert "build:" not in compose                    # a build here belongs in compose.cpp-build.yml



def _compose(path):
    """A compose file as data, with compose's own tags (!override, !reset) read as plain values."""
    import yaml

    class Loader(yaml.SafeLoader):
        pass
    for tag in ("!override", "!reset"):
        Loader.add_constructor(tag, lambda loader, node: (loader.construct_sequence(node)
                                                          if isinstance(node, yaml.SequenceNode) else
                                                          loader.construct_mapping(node)
                                                          if isinstance(node, yaml.MappingNode) else
                                                          loader.construct_scalar(node)))
    return yaml.load(path.read_text(encoding="utf-8"), Loader=Loader) or {}


@pytest.mark.parametrize("engine", ["--comfyui", "--cpp"])
def test_every_folder_the_app_writes_in_is_made_by_the_setup_script(tmp_path, engine):
    """The app runs as you, not root.  A folder it mounts that is not there when Docker starts it is made by Docker,
    as root, and the app cannot write in it: on a new install, Whisper could not be fetched (data/models/whisper was
    mounted on its own) and a training set could not be staged (engine-state/input was never made).  An existing
    install had the folders from long ago, so nothing showed there.  So: after fetch-models.sh on a new checkout,
    every folder mounted read-write into a service that runs as a user must exist, or be part of the checkout."""
    repo = Path(__file__).resolve().parent.parent
    root, _, _ = _run_fetch(tmp_path, engine, env_text="APP_UID=1000\n")
    files = ["compose.yml"] + (["compose.cpp.yml"] if engine == "--cpp" else [])
    users, mounts = set(), {}
    for name in files:
        for service, spec in (_compose(repo / name).get("services") or {}).items():
            if spec.get("user"):
                users.add(service)
            for volume in spec.get("volumes") or []:
                source, _, rest = (volume if isinstance(volume, str) else
                                   f"{volume.get('source')}:{volume.get('target')}"
                                   f"{':ro' if volume.get('read_only') else ''}").partition(":")
                if source.startswith("./") and not rest.endswith(":ro"):
                    mounts.setdefault(service, set()).add(source[2:])
    assert "app" in users
    missing = []
    for service in users:
        for source in sorted(mounts.get(service, ())):
            tracked = (repo / source).exists() and source.split("/")[0] in {"app", ".git", "VERSION"}
            if not tracked and not (root / source).exists():
                missing.append(f"{service}: ./{source}")
    assert not missing, f"fetch-models.sh does not make these, so Docker would, as root: {missing}"
