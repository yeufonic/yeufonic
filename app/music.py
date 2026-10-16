"""Canonical music theory, pitch calculations, and ABC notation primitives.

Consolidates pitch class maps, accidental arithmetic, octave calculation,
and ABC note-length multiplier parsing across score, transpose, voices,
aligner, soundfonts, and midi modules.
"""
from __future__ import annotations

import re

# Semitone offset of each natural pitch class relative to C (0..11)
PITCH_CLASS: dict[str, int] = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11,
}

# Semitone delta of standard ABC accidental notation
ACCIDENTAL_DELTA: dict[str, int] = {
    "^^": 2, "^": 1, "=": 0, "": 0, "_": -1, "__": -2,
}

# Canonical ABC accidental symbol for a semitone delta
ACCIDENTAL_SYMBOL: dict[int, str] = {
    2: "^^", 1: "^", 0: "=", -1: "_", -2: "__",
}

# Chromatic note names using sharps / flats (standard and ABC notation)
STANDARD_SHARP_NAMES: list[str] = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
]
STANDARD_FLAT_NAMES: list[str] = [
    "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B",
]
ABC_SHARP_NAMES: list[str] = [
    "C", "^C", "D", "^D", "E", "F", "^F", "G", "^G", "A", "^A", "B",
]
ABC_FLAT_NAMES: list[str] = [
    "C", "_D", "D", "_E", "E", "F", "_G", "G", "_A", "A", "_B", "B",
]

_LENGTH_RE = re.compile(r"(\d*)((?:/\d*)*)")


def parse_abc_length(mult_str: str) -> float:
    """Parse an ABC note-length multiplier suffix (e.g. '', '2', '/2', '3/2', '//').

    Returns the duration multiplier relative to the default note length L:."""
    found = _LENGTH_RE.match(mult_str or "")
    if not found:
        return 1.0
    value = float(found.group(1)) if found.group(1) else 1.0
    for part in re.findall(r"/(\d*)", found.group(2)):
        value /= float(part) if part else 2.0
    return value


def abc_note_octave(letter: str, marks: str = "") -> int:
    """Calculate the scientific octave number for an ABC note letter and octave marks.

    Uppercase letters (C..B) default to octave 4 (middle C = C4).
    Lowercase letters (c..b) default to octave 5.
    Apostrophes (') raise by octaves; commas (,) lower by octaves.
    """
    return (5 if letter.islower() else 4) + marks.count("'") - marks.count(",")


def abc_to_midi(letter: str, octave: int, accidental: int = 0) -> int:
    """Convert an ABC note letter, octave number, and accidental semitone delta to MIDI pitch (0..127).

    Middle C (C4) is MIDI note 60.
    """
    return 12 * (octave + 1) + PITCH_CLASS[letter.upper()] + accidental


def midi_to_abc_spelling(letter: str, octave: int) -> str:
    """Format a note letter and octave into ABC pitch notation (e.g. C, c, c', C,)."""
    return (letter.lower() + "'" * (octave - 5)
            if octave >= 5
            else letter.upper() + "," * (4 - octave))
