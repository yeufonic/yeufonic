"""Vocal autotune / pitch correction for hummed and sung melodies.

Snaps vocal pitches to the nearest semitone (Chromatic) or a selected
musical scale (Major, Minor, Pentatonic) using pitch detection and
time-domain pitch shifting.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

import torch
import torchaudio
import torchaudio.functional as F

log = logging.getLogger(__name__)

SCALES: dict[str, list[int]] = {
    "chromatic": list(range(12)),
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "pentatonic": [0, 2, 4, 7, 9],
}

ROOTS: dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


def allowed_pitch_classes(scale: str = "chromatic", root: str = "C") -> list[int]:
    """Returns the 0-11 pitch class numbers allowed for the given root and scale."""
    root_val = ROOTS.get(root.strip().capitalize(), 0)
    intervals = SCALES.get(scale.strip().lower(), SCALES["chromatic"])
    return sorted(list({(root_val + step) % 12 for step in intervals}))


def snap_midi_to_scale(midi: torch.Tensor, allowed_pcs: torch.Tensor) -> torch.Tensor:
    """Snaps each MIDI pitch value in `midi` to the nearest note in `allowed_pcs`."""
    octave = torch.floor(midi / 12.0) * 12.0
    pc = midi - octave
    dists = torch.abs(pc.unsqueeze(-1) - allowed_pcs)
    best_idx = torch.argmin(dists, dim=-1)
    return octave + allowed_pcs[best_idx]


def quantize_pitch(freq_hz: float, scale: str = "chromatic", root: str = "C") -> float:
    """Snaps a frequency in Hz to the nearest in-scale frequency in Hz."""
    if freq_hz <= 0:
        return freq_hz
    midi = 69.0 + 12.0 * math.log2(freq_hz / 440.0)
    allowed = torch.tensor(allowed_pitch_classes(scale=scale, root=root), dtype=torch.float32)
    snapped_midi = snap_midi_to_scale(torch.tensor([midi], dtype=torch.float32), allowed).item()
    return 440.0 * (2.0 ** ((snapped_midi - 69.0) / 12.0))


def tune_waveform(
    waveform: torch.Tensor,
    sample_rate: int,
    scale: str = "chromatic",
    root: str = "C",
    strength: float = 0.85,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Performs pitch correction on a 1D or 2D [channels, samples] audio tensor.
    Returns (tuned_waveform, stats_dict)."""
    if scale.lower() in ("off", "none") or strength <= 0:
        return waveform, {"tuned": False, "notes_detected": 0}

    # Ensure mono for pitch detection
    channels, n_samples = waveform.shape
    mono = waveform.mean(dim=0, keepdim=True) if channels > 1 else waveform

    # Detect pitch: frame_time of 0.02s (20 ms)
    frame_time = 0.02
    hop_length = int(frame_time * sample_rate)

    # Pad mono if shorter than minimum required by median smoothing filter
    min_samples = int(sample_rate * 0.8)
    if mono.shape[-1] < min_samples:
        padded_mono = torch.nn.functional.pad(mono, (0, min_samples - mono.shape[-1]))
    else:
        padded_mono = mono

    pitch = F.detect_pitch_frequency(padded_mono, sample_rate, frame_time=frame_time)
    expected_frames = max(1, mono.shape[-1] // hop_length)
    pitch = pitch[:, :expected_frames]
    n_frames = pitch.shape[1]

    # Voiced vocal frequencies: 55 Hz (A1) to 1100 Hz (C6)
    voiced = (pitch > 55.0) & (pitch < 1100.0)
    voiced_indices = voiced.squeeze(0).nonzero(as_tuple=True)[0]

    if len(voiced_indices) == 0:
        return waveform, {"tuned": False, "notes_detected": 0}

    allowed_pcs = torch.tensor(allowed_pitch_classes(scale, root), dtype=torch.float32, device=waveform.device)
    midi = 69.0 + 12.0 * torch.log2(pitch / 440.0)
    target_midi = snap_midi_to_scale(midi.squeeze(0), allowed_pcs).unsqueeze(0)

    # Shift needed per frame in semitones
    delta_semis = (target_midi - midi) * strength
    delta_semis[~voiced] = 0.0

    # Group contiguous voiced frames into discrete musical notes
    notes: list[tuple[int, int, float]] = []
    current_start = None
    last_frame = None

    for idx in voiced_indices.tolist():
        if current_start is None:
            current_start = idx
            last_frame = idx
        elif idx == last_frame + 1:
            last_frame = idx
        else:
            # Note break
            if last_frame - current_start >= 3:  # minimum 60 ms
                seg_shift = delta_semis[0, current_start:last_frame + 1].median().item()
                notes.append((current_start, last_frame, seg_shift))
            current_start = idx
            last_frame = idx

    if current_start is not None and last_frame is not None and last_frame - current_start >= 3:
        seg_shift = delta_semis[0, current_start:last_frame + 1].median().item()
        notes.append((current_start, last_frame, seg_shift))

    if not notes:
        return waveform, {"tuned": False, "notes_detected": 0}

    # Apply note-by-note pitch shift with smooth edge crossfades
    out = waveform.clone()
    fade_len = min(int(0.015 * sample_rate), hop_length // 2)  # 15 ms crossfade
    fade_in = torch.linspace(0, 1, fade_len, device=waveform.device)
    fade_out = torch.linspace(1, 0, fade_len, device=waveform.device)

    applied_count = 0
    for start_frame, end_frame, shift_amount in notes:
        if abs(shift_amount) < 0.04:  # within 4 cents is already in tune
            continue

        sample_start = max(0, start_frame * hop_length)
        sample_end = min(n_samples, (end_frame + 1) * hop_length)
        if sample_end - sample_start < fade_len * 2:
            continue

        chunk = waveform[:, sample_start:sample_end]
        try:
            shifted = F.pitch_shift(chunk, sample_rate, n_steps=shift_amount)
            # Crossfade boundaries
            shifted[:, :fade_len] = shifted[:, :fade_len] * fade_in + chunk[:, :fade_len] * fade_out
            shifted[:, -fade_len:] = shifted[:, -fade_len:] * fade_out + chunk[:, -fade_len:] * fade_in
            out[:, sample_start:sample_end] = shifted
            applied_count += 1
        except Exception as exc:
            log.warning("Could not pitch shift note segment (%d to %d): %s", sample_start, sample_end, exc)

    stats = {
        "tuned": applied_count > 0,
        "notes_detected": len(notes),
        "notes_adjusted": applied_count,
        "scale": scale,
        "root": root,
        "strength": strength,
    }
    return out, stats


def tune_file(
    src: Path,
    dest: Path,
    scale: str = "chromatic",
    root: str = "C",
    strength: float = 0.85,
) -> dict[str, Any]:
    """Reads audio from `src`, tunes it, and saves to `dest`."""
    waveform, sr = torchaudio.load(str(src))
    tuned_wav, stats = tune_waveform(waveform, sr, scale=scale, root=root, strength=strength)
    dest.parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(str(dest), tuned_wav, sr)
    stats["src"] = str(src)
    stats["dest"] = str(dest)
    return stats
