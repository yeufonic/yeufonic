"""A take for a DAW: one zip holding its audio, its stems, a MIDI file and the score, a chord chart, and its recipe.

The audio and the stems are the files the app keeps.  The MIDI file is written by the page, from the same sequence the
score preview plays (midiwrite.js), and arrives here ready; so does the audio when the mastering rack changes the take,
rendered by the rack in the page.  The chord chart is read from the score here."""
from __future__ import annotations

import re

from . import library, transpose

# A bar's chord: the first "…" symbol in it.  abcjs and the planner write chords that way, as in "Dmaj7" or "G/A".
CHORD = re.compile(r'"([^"]+)"')
# A bar of rests standing for several, Z4, counts as that many bars.
MULTI_REST = re.compile(r"^\s*Z(\d*)\s*$")
SECTION = re.compile(r"^%\s*([A-Za-z][\w -]*)\s*$")
VOICE = re.compile(r"^V:\s*(\S+)")
BARS_PER_LINE = 4


def _bars(line: str) -> list[str]:
    """A music line's bars, without the bar lines, repeat marks or a trailing comment."""
    line = line.split("%", 1)[0]
    parts = re.split(r":?\|+:?|\[\d", line)
    return [part for part in parts if part.strip()]


def chord_sections(abc: str) -> list[tuple[str, list[str]]]:
    """[(section, chords per bar)], from the first voice that carries chord symbols.  A bar with no chord of its own
    keeps the one before it, written "%", as a chart does."""
    lines = abc.splitlines()
    voices: list[str] = []
    current = None
    for line in lines:
        found = VOICE.match(line.strip())
        if found:
            current = found.group(1)
            continue
        if current and CHORD.search(line) and current not in voices:
            voices.append(current)
    voice = voices[0] if voices else None
    sections: list[tuple[str, list[str]]] = []
    current = None
    for raw in lines:
        line = raw.strip()
        named = SECTION.match(line)
        if named:
            sections.append((named.group(1).strip().title(), []))
            continue
        found = VOICE.match(line)
        if found:
            # A V: line in the header names the voices; one in the music switches to it.
            rest = line[found.end():].strip()
            current = found.group(1) if not rest or "=" not in rest else current
            continue
        if not line or re.match(r"^[A-Za-z]:", line) or line.startswith("%"):
            continue
        if voice is not None and current != voice:
            continue
        if not sections:
            sections.append(("", []))
        bars = sections[-1][1]
        for bar in _bars(line):
            rest = MULTI_REST.match(bar)
            if rest and not CHORD.search(bar):
                bars.extend(["%"] * int(rest.group(1) or 1))
                continue
            chord = CHORD.search(bar)
            bars.append(chord.group(1) if chord else "%")
    return [(name, bars) for name, bars in sections if bars]


def _header(abc: str, key: str) -> str | None:
    found = re.search(rf"^{key}:\s*(.+)$", abc, re.M)
    return found.group(1).strip() if found else None


def chart(take: dict) -> str:
    """The take as a chord chart in plain text: its tempo, key, time and length, each section's chords four bars to a
    line, then the words."""
    abc = take.get("abc") or ""
    music = library.music_tags(abc)
    facts = []
    if music.get("bpm"):
        facts.append(f"Tempo: {music['bpm']} BPM")
    key = music.get("key")
    if not key and abc:
        found = transpose.plan_key(abc)
        key = transpose.key_name(found[0], found[1], found[2] < 0) if found else _header(abc, "K")
    if key:
        facts.append(f"Key: {key}")
    meter = _header(abc, "M") if abc else None
    if meter:
        facts.append(f"Time: {meter}")
    if take.get("duration"):
        seconds = int(round(float(take["duration"])))
        facts.append(f"Length: {seconds // 60}:{seconds % 60:02d}")
    out = [take.get("title") or "Untitled", "   ".join(facts), ""]
    for name, bars in chord_sections(abc):
        if name:
            out.append(name)
        for start in range(0, len(bars), BARS_PER_LINE):
            out.append("| " + " | ".join(bars[start:start + BARS_PER_LINE]) + " |")
        out.append("")
    words = library.sung_words(take.get("kind") or "", take.get("lyrics"))
    if words:
        out += ["Lyrics", "", words.strip(), ""]
    return "\n".join(out).rstrip() + "\n"
