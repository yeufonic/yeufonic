"""Tests for the Microphone Vocal/Melody Recorder feature."""

import io
import math
import struct
import wave
from pathlib import Path

import torch
from app import autotune, config
from app.db import execute, one, rows


def _generate_wav_bytes(frequency: float = 445.0, duration_seconds: float = 0.5, sample_rate: int = 16000) -> bytes:
    """Generate a clean single-channel 16-bit PCM WAV in memory."""
    buf = io.BytesIO()
    num_samples = int(duration_seconds * sample_rate)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = []
        for i in range(num_samples):
            t = float(i) / sample_rate
            sample = 0.6 * math.sin(2.0 * math.pi * frequency * t)
            ival = int(sample * 32767.0)
            frames.append(struct.pack("<h", max(-32768, min(32767, ival))))
        wf.writeframes(b"".join(frames))
    return buf.getvalue()


def test_db_sources_has_origin_column():
    """Verify migration 40 added the origin column to the sources table with default 'upload'."""
    cols = [r["name"] for r in rows("PRAGMA table_info(sources)")]
    assert "origin" in cols, "sources table must contain origin column"

    source_id = "test-orig-check"
    execute(
        """INSERT INTO sources(id, title, filename, stored_path, sha256, created_at, duration)
           VALUES(?, 'Test Default', 'default.wav', '/tmp/fake.wav', 'fake-sha', 1000.0, 5.0)""",
        (source_id,)
    )
    res = one("SELECT origin FROM sources WHERE id = ?", (source_id,))
    assert res["origin"] == "upload", "default origin should be 'upload'"
    execute("DELETE FROM sources WHERE id = ?", (source_id,))


def test_static_recorder_js_and_markup_served(client):
    """Verify recorder.js is served with proper headers and referenced in index.html."""
    res = client.get("/static/recorder.js")
    assert res.status_code == 200
    assert "Yeufonic Melody Recorder" in res.text
    assert "getRootFrequency" in res.text
    assert "playCountInClick" in res.text
    assert "auditionRootNote" in res.text
    assert "setTimeSignature" in res.text
    assert res.headers["cache-control"] == "no-cache"

    page = client.get("/")
    assert page.status_code == 200
    assert "recorder.js" in page.text
    assert "recorder-modal" in page.text
    assert "source-record-btn" in page.text
    assert "record-melody-btn" in page.text
    assert "rec-close-btn" in page.text
    assert "rec-root-audition-btn" in page.text
    assert "rec-countin-root" in page.text
    assert "rec-timesig" in page.text
    assert "drop-record-btn" in page.text

    css = client.get("/static/styles.css")
    assert css.status_code == 200
    assert "#rec-close-btn" in css.text
    assert "position: absolute" in css.text
    assert ".rec-audition-btn" in css.text
    assert ".rec-countin-root" in css.text
    assert ".drop-action-btn" in css.text


def test_upload_melody_recording(client):
    """Verify recording upload stores into sources/recordings/ and records origin='recording'."""
    wav_data = _generate_wav_bytes(440.0, duration_seconds=0.3)
    resp = client.post(
        "/api/sources",
        files={"file": ("humming.wav", wav_data, "audio/wav")},
        data={"title": "Hummed Hook Take 1", "origin": "recording"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["origin"] == "recording"
    assert data["title"] == "Hummed Hook Take 1"
    assert "recordings" in data["stored_path"], "Stored path must be under recordings folder"

    stored_file = Path(data["stored_path"])
    assert stored_file.exists(), "Stored recording file must exist on disk"

    # Filtered GET tests
    all_sources = client.get("/api/sources").json()
    rec_sources = client.get("/api/sources?origin=recording").json()
    upl_sources = client.get("/api/sources?origin=upload").json()

    assert any(s["id"] == data["id"] for s in all_sources)
    assert any(s["id"] == data["id"] for s in rec_sources)
    assert not any(s["id"] == data["id"] for s in upl_sources)

    # Delete cleanup
    del_resp = client.delete(f"/api/sources/{data['id']}")
    assert del_resp.status_code == 200
    assert not stored_file.exists(), "Deleting the recorded source must remove file on disk"


def test_autotune_endpoint(client):
    """Verify /api/recorder/autotune endpoint processes audio and returns tuned WAV."""
    wav_data = _generate_wav_bytes(frequency=445.0, duration_seconds=0.4)
    resp = client.post(
        "/api/recorder/autotune",
        files={"audio_file": ("vocal.wav", wav_data, "audio/wav")},
        data={"scale": "major", "root": "C", "strength": 0.8},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("audio/wav")
    assert len(resp.content) > 100, "Should return non-empty WAV audio"

    # Validate output header is valid WAV
    with wave.open(io.BytesIO(resp.content), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getframerate() == 16000
        assert wf.getnframes() > 0


def test_autotune_quantize_scale():
    """Verify scale pitch snapping in autotune module."""
    # A4 is 440Hz -> MIDI note 69 (A)
    # 445Hz is slightly sharp of A4 (~69.19)
    f_sharp_a = 445.0
    # In C Major (notes: C, D, E, F, G, A, B), A (69) is in the scale.
    # Snapped pitch should be 440Hz (A4).
    snapped = autotune.quantize_pitch(f_sharp_a, scale="major", root="C")
    assert abs(snapped - 440.0) < 1.0, f"Expected 440.0Hz, got {snapped}"

    # F4 is ~349.23 Hz (MIDI 65, pitch class 5).
    # In C Major Pentatonic (C, D, E, G, A: 0, 2, 4, 7, 9), F is not in the scale.
    # The nearest note is E4 (MIDI 64, ~329.63 Hz).
    f_input = 345.0
    snapped_penta = autotune.quantize_pitch(f_input, scale="pentatonic", root="C")
    f_e4 = 440.0 * (2.0 ** ((64 - 69) / 12.0))
    assert abs(snapped_penta - f_e4) < 1.5, f"Expected E4 ({f_e4}), got {snapped_penta}"


def test_autotune_waveform_processing():
    """Verify tune_waveform on a synthetic PyTorch tensor."""
    sr = 16000
    dur = 0.3
    t = torch.linspace(0, dur, int(sr * dur))
    # 445Hz (around A4=440Hz)
    freq = 445.0
    waveform = (0.5 * torch.sin(2 * math.pi * freq * t)).unsqueeze(0)

    tuned, stats = autotune.tune_waveform(waveform, sr, scale="chromatic", root="C", strength=0.9)
    assert tuned.shape == waveform.shape, "Output waveform should preserve dimensions"
    assert not torch.isnan(tuned).any(), "Output should not contain NaNs"
    assert tuned.abs().max() > 0.01, "Output should contain audio signal"
