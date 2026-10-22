"""Hum to song: a short recorded tune made into a whole song by the planner.

The tune is the hook.  The plan is written with it held in place: the plan opens with the
hook's own header, so it is in the hook's key, metre, note length and tempo, and every
section of the hook's name (the chorus, usually) holds the hook's bars.  The planner writes
everything else around it, with the hook in what it has already written (the engine's
yue2_harmony node does the holding, as it holds a plan to a structure).

The hook is given to the planner in the planner's own layout, which is also the
transcriber's: blocks of up to four bars, V: Vocal then V: Ins, the two voices bar for bar.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import instrumental, score

# Song structures, as the lyric tags of a plan with no words of its own
PRESETS: dict[str, list[str]] = {
    "standard": ["Intro", "Verse 1", "Pre-Chorus", "Chorus", "Verse 2", "Pre-Chorus", "Chorus", "Bridge", "Chorus", "Outro"],
    "short": ["Verse 1", "Chorus", "Verse 2", "Chorus", "Outro"],
    "aaba": ["Verse 1", "Verse 2", "Bridge", "Verse 3", "Outro"],
}

VOCAL_LINE = 'V: Vocal clef=treble name="Vocal Melody" snm="Vocal"'
INS_LINE = 'V: Ins clef=treble name="Ins Melody" snm="Inst."'


class NoMelody(ValueError):
    """The score has no notes to make a song from."""


@dataclass
class Hook:
    head: str       # the plan's header, through its K: line and the newline after it
    body: str       # the hook's bars as V: Vocal and V: Ins blocks, ending with a newline
    key: str        # as the K: line writes it ("Cm")
    bpm: int
    bars: int


def _field(abc: str, name: str, default: str) -> str:
    found = re.search(rf"^{name}:\s*(\S+)", abc, re.M)
    return found.group(1) if found else default


def _voice_bars(abc: str, voice: str) -> list[str]:
    """A voice's bars in order across all its blocks, Z4 written out as four."""
    body = abc.split("\n")
    start = next((i + 1 for i, line in enumerate(body) if line.startswith("K:")), len(body))
    lines = [line for block in instrumental._voice_blocks(body[start:])
             if isinstance(block, list) and block[0] == voice for line in block[2]]
    return [text for kind, text in instrumental._tokens(lines) if kind == "bar"]


def _rests_only(bar: str) -> bool:
    return not instrumental._has_notes(bar)


def _block(bars: list[str]) -> str:
    """Up to four bars on a line, as the planner writes them: a block of whole-bar rests as Zn."""
    if all(bar.strip() == "Z" for bar in bars):
        return f"Z{len(bars)}|" if len(bars) > 1 else "Z|"
    return "|".join(bars) + "|"


def hook_of(abc: str) -> Hook:
    """The hook a recording's score makes: its header and its bars.  The tune is read from the
    Vocal voice, or from Ins where the transcriber heard the voice as an instrument; silence
    before the first note and after the last is left out.  NoMelody when it has no notes."""
    abc = instrumental.tune_on_voice(abc or "")
    vocal, ins = _voice_bars(abc, "Vocal"), _voice_bars(abc, "Ins")
    if not any(instrumental._has_notes(bar) for bar in vocal):
        raise NoMelody("This score has no melody notes to make a song from.")
    length = max(len(vocal), len(ins))
    vocal += ["Z"] * (length - len(vocal))
    ins += ["Z"] * (length - len(ins))
    sounding = [i for i in range(length) if not (_rests_only(vocal[i]) and _rests_only(ins[i]))]
    first, last = sounding[0], sounding[-1] + 1
    vocal, ins = vocal[first:last], ins[first:last]

    key = _field(abc, "K", "C")
    tempo = re.search(r"^Q:\s*1/4\s*=\s*(\d+)", abc, re.M)
    bpm = int(tempo.group(1)) if tempo else 120
    head = "\n".join(["X:1", "T:", f"M:{_field(abc, 'M', '4/4')}", f"L:{_field(abc, 'L', '1/8')}",
                      f"Q:1/4={bpm}", VOCAL_LINE, INS_LINE, f"K:{key}"]) + "\n"
    lines = []
    for i in range(0, len(vocal), 4):
        lines += ["V: Vocal", _block(vocal[i:i + 4]), "V: Ins", _block(ins[i:i + 4])]
    return Hook(head=head, body="\n".join(lines) + "\n", key=key, bpm=bpm, bars=len(vocal))


def section_name(role: str) -> str:
    """The section the hook fills, as the planner names it."""
    return "verse" if role == "verse" else "chorus"

