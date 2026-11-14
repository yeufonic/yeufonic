"""Whisper listens to the whole vocal.  Its voice detector, built for speech, threw
most singing away before listening, which caused most of its mistakes; it is kept off."""
from types import SimpleNamespace

import pytest

from app import identities


class FakeWhisper:
    """Stands in for faster-whisper: records what it was asked, returns set segments."""
    def __init__(self, texts):
        self.texts, self.asked = texts, None

    def transcribe(self, path, **kwargs):
        self.asked = kwargs
        segs = [SimpleNamespace(start=10.0 * i, end=10.0 * i + 4.0, text=t) for i, t in enumerate(self.texts)]
        return iter(segs), None


@pytest.fixture
def whisper(monkeypatch):
    def use(texts):
        fake = FakeWhisper(texts)
        monkeypatch.setattr(identities, "_whisper", fake)
        return fake
    return use


def test_the_voice_detector_is_off(whisper, tmp_path):
    fake = whisper(["I left the porch light on for you"])
    identities.transcribe(tmp_path / "vocals.flac")
    assert fake.asked["vad_filter"] is False, "it threw away most of a sung vocal"


def test_what_is_invented_over_silence_is_guarded_against(whisper, tmp_path):
    """The detector used to hide the silences; without it the guard has to."""
    fake = whisper(["Paper boat"])
    identities.transcribe(tmp_path / "vocals.flac")
    assert fake.asked["hallucination_silence_threshold"] == 2.0
    assert fake.asked["word_timestamps"] is True, "the silence guard needs word times"


def test_whispers_stock_lines_are_dropped(whisper, tmp_path):
    whisper(["I left the porch light on for you", "Thank you.", "Thanks for watching!", "Paper boat"])
    lines = identities.transcribe(tmp_path / "vocals.flac")
    assert [l["text"] for l in lines] == ["I left the porch light on for you", "Paper boat"]


def test_a_real_line_that_starts_the_same_way_is_kept(whisper, tmp_path):
    whisper(["Thank you for loving me", "Thank you, baby"])
    lines = identities.transcribe(tmp_path / "vocals.flac")
    assert [l["text"] for l in lines] == ["Thank you for loving me", "Thank you, baby"]


def test_a_dropped_line_keeps_the_others_timing(whisper, tmp_path):
    """Two sentences in one segment share its time; dropping one must not shift the other."""
    whisper(["Thank you. Paper boat."])
    lines = identities.transcribe(tmp_path / "vocals.flac")
    assert len(lines) == 1 and lines[0]["text"] == "Paper boat"
    assert lines[0]["start"] > 0.0, "it keeps its place after the dropped line"


def test_whisper_finds_the_language_sung(whisper, tmp_path):
    """A song in another language is written in it, not turned into English, and the language is judged past
    the first stretch, which in a vocal is often a silent intro."""
    fake = whisper(["Una canción"])
    identities.transcribe(tmp_path / "vocals.flac")
    assert fake.asked["language"] is None
    assert fake.asked["language_detection_segments"] == 4
