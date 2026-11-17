"""Whisper on a Mac's GPU, with the CPU to fall back on (identities.transcribe)."""
from pathlib import Path

import pytest

from app import identities


class FakeModel:
    def __init__(self, device, fails=False):
        self.yeufonic_device, self.fails = device, fails

    def transcribe(self, path, **kw):
        def gen():
            if self.fails:
                raise RuntimeError("MPS backend: an operation is not supported")
            yield identities.Segment(0.0, 2.0, "Morning light across the floor")
        return gen(), None


def test_a_mac_hears_on_metal_and_falls_back_to_the_cpu(monkeypatch, tmp_path):
    loads = []

    def load(device):
        loads.append(device)
        return FakeModel(device, fails=device == "mps")
    monkeypatch.setattr(identities, "WHISPER_DEVICES", ("mps", "cpu"))
    monkeypatch.setattr(identities, "_load_whisper", load)
    monkeypatch.setattr(identities, "_whisper", None)
    monkeypatch.setattr(identities, "lines_from_segments", lambda segs, *a, **k: [s.text for s in segs])
    assert identities.transcribe(tmp_path / "vocals.flac") == ["Morning light across the floor"]
    assert loads == ["mps", "cpu"]                    # Metal failed while hearing: the CPU heard it
    assert identities._whisper.yeufonic_device == "cpu"
    identities.transcribe(tmp_path / "vocals.flac")
    assert loads == ["mps", "cpu"]                    # and stays on the CPU


def test_a_stop_is_not_taken_for_a_metal_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(identities, "_whisper", FakeModel("mps"))

    def stop(*a, **k):
        raise identities.Stopped()
    monkeypatch.setattr(identities, "lines_from_segments", stop)
    monkeypatch.setattr(identities, "_load_whisper", lambda device: pytest.fail("reloaded on a stop"))
    with pytest.raises(identities.Stopped):
        identities.transcribe(tmp_path / "vocals.flac")


def test_only_apple_silicon_tries_metal():
    import platform, sys
    expected = ("mps", "cpu") if sys.platform == "darwin" and platform.machine() == "arm64" else ("cpu",)
    assert identities.WHISPER_DEVICES == expected
