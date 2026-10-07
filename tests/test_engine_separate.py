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
