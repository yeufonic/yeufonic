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
