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

from . import instrumental, score, transpose, voices

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


# A tune with no chords is given some from its own notes: the diatonic triads of its key, by the
# share of each bar's sounding time that is a chord tone.  Degrees from the tonic, and the quality.
_MAJOR_TRIADS = ((0, ""), (5, ""), (7, ""), (9, "m"), (2, "m"), (4, "m"))
_MINOR_TRIADS = ((0, "m"), (5, "m"), (7, ""), (3, ""), (8, ""), (10, ""), (7, "m"))
_NOTE = re.compile(r'"[^"]*"|!(?:[^!\n])*!|(?P<acc>\^\^|\^|__|_|=)?(?P<letter>[A-Ga-g])(?P<marks>[,\']*)(?P<len>\d*(?:/\d*)?)'
                   r"|(?P<rest>[zx])(?P<rlen>\d*(?:/\d*)?)")


def _length(text: str) -> float:
    if not text:
        return 1.0
    top, _, bottom = text.partition("/")
    return (float(top) if top else 1.0) / ((float(bottom) if bottom else 2.0) if _ else 1.0)


def _sounding(bar: str, signature: dict[str, int]) -> list[tuple[int, float, bool]]:
    """(pitch class, length, on the downbeat) of each note in a bar, accidentals as written or carried."""
    out, said, at = [], {}, 0.0
    for found in _NOTE.finditer(bar):
        if found.group("rest"):
            at += _length(found.group("rlen"))
            continue
        if not found.group("letter"):
            continue
        letter = found.group("letter")
        place = (letter.upper(), letter.islower(), found.group("marks"))
        acc = found.group("acc")
        if acc:
            said[place] = {"^^": 2, "^": 1, "=": 0, "__": -2, "_": -1}[acc]
        shift = said.get(place, signature.get(letter.upper(), 0))
        length = _length(found.group("len"))
        out.append(((transpose.BASE[letter.upper()] + shift) % 12, length, at == 0.0))
        at += length
    return out


def _chord_for(notes: list[tuple[int, float, bool]], tonic: int, minor: bool, before: str | None,
               flats: bool) -> str | None:
    total = sum(length for _, length, _ in notes)
    if not total:
        return None
    names = transpose.NAME_FLAT if flats else transpose.NAME_SHARP
    best, best_score = None, -9.0
    for rank, (degree, quality) in enumerate(_MINOR_TRIADS if minor else _MAJOR_TRIADS):
        root = (tonic + degree) % 12
        tones = {root, (root + (3 if quality == "m" else 4)) % 12, (root + 7) % 12}
        held = sum(length * (1.5 if first else 1.0) for pc, length, first in notes if pc in tones)
        score = held / total - 0.03 * rank       # the common chords first, when it is close
        name = names[root] + quality
        if name == before:
            score += 0.05                        # and the chord already sounding, rather than a change
        if score > best_score:
            best, best_score = name, score
    return best


def with_chords(abc: str) -> str:
    """The score with a chord symbol at the start of every Vocal bar, chosen from the tune's own
    notes, when the transcriber wrote none (a lone tune, played or hummed, often has none).  A plan
    held to a hook with no chords can be written with no chords at all, which no render can use.
    A score that has chords, or whose key cannot be read, comes back as it is."""
    if re.search(r'"[A-G][#b]?[^"\n]{0,10}"', abc or ""):
        return abc
    key = transpose.plan_key(abc or "")
    if not key:
        return abc
    tonic, minor, sharps = key
    signature, flats = transpose.signature(sharps), sharps < 0
    lines = abc.split("\n")
    start = next((i + 1 for i, line in enumerate(lines) if line.startswith("K:")), len(lines))
    voice, before = "", None
    for index in range(start, len(lines)):
        line = lines[index]
        if line.startswith("V:"):
            voice = line[2:].split()[0] if line[2:].split() else ""
            continue
        if voice != "Vocal" or line.startswith(("%", "w:")) or not line.strip():
            continue
        bars = line.split("|")
        for at, bar in enumerate(bars):
            if not bar.strip() or bar.lstrip().startswith("Z"):
                continue
            chord = _chord_for(_sounding(bar, signature), tonic, minor, before, flats) or before
            if chord:
                bars[at] = f'"{chord}"' + bar
                before = chord
        lines[index] = "|".join(bars)
    return "\n".join(lines)


def hook_of(abc: str) -> Hook:
    """The hook a recording's score makes: its header and its bars.  The tune is read from the
    Vocal voice, or from Ins where the transcriber heard the voice as an instrument; silence
    before the first note and after the last is left out.  NoMelody when it has no notes."""
    abc = with_chords(instrumental.tune_on_voice(abc or ""))
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



VOICES = (voices.MALE, voices.FEMALE)


def _shift_octaves(line: str, octaves: int) -> str:
    """A line of music with every note written `octaves` higher (or lower).  Every note moves by
    the same amount, so an accidental still holds for the notes it held for, and chord symbols,
    decorations and inline fields are left as they are."""
    def move(found: re.Match) -> str:
        if not found.group("note"):
            return found.group(0)
        letter, marks = found.group("letter"), found.group("marks")
        height = (4 if letter.isupper() else 5) + marks.count("'") - marks.count(",") + octaves
        text = letter.lower() + "'" * (height - 5) if height >= 5 else letter.upper() + "," * (4 - height)
        return (found.group("acc") or "") + text
    return transpose.TOKEN.sub(move, line)


def fit_to_voice(hook: Hook, voice: str) -> tuple[Hook, int]:
    """The hook with its tune moved by whole octaves to where the chosen voice is sung, and by how
    many.  The render takes the singer from the octave the vocal line is written in (voices.py),
    so a man's tune hummed, or a guitar line played, between the two registers or below them
    would otherwise be sung by whoever the model chose."""
    notes = voices.read(hook.head + hook.body)["notes"]
    total = sum(note["length"] for note in notes)
    if not total:
        return hook, 0
    mean = sum(note["pitch"] * note["length"] for note in notes) / total
    octaves = voices._octaves(mean, voice)
    if not octaves:
        return hook, 0
    lines, voice_now = hook.body.split("\n"), ""
    for index, line in enumerate(lines):
        if line.startswith("V:"):
            voice_now = line[2:].split()[0] if line[2:].split() else ""
        elif voice_now == "Vocal":
            lines[index] = _shift_octaves(line, octaves)
    return Hook(head=hook.head, body="\n".join(lines), key=hook.key, bpm=hook.bpm, bars=hook.bars), octaves


def style_for_voice(style: str, voice: str) -> str:
    """The style with the chosen voice named, unless it names a singer already: the style's own
    words are the user's and win."""
    if any(voices._word(pattern, style) for pattern in
           (voices._MALE_STRONG, voices._FEMALE_STRONG, voices._MALE_WEAK, voices._FEMALE_WEAK)):
        return style
    return f"{style}, {voice} vocals" if style else f"{voice} vocals"
