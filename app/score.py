"""Reading a score's ABC well enough to tell a usable score from a broken one.

A score plan is text the model writes token by token, and at high temperature it can
lose the thread: garbled voice headers, no vocal part, a single bar.  Such a score
renders into something that is not the song, so it is caught here instead.
"""
from __future__ import annotations

import re

KEY = re.compile(r"^K:\s*\S", re.M)
VOICE = re.compile(r"^V:\s*(\S+)")
HEADER = re.compile(r"^[A-Za-z]:")
CHORD = re.compile(r'"[A-G][#b]?[^"\s]*"')
COLLAPSE = re.compile(r"([^\w\s])\1{7,}")
MIN_BARS = 4


METER = re.compile(r"(?:^|\[)M:\s*(\d+)/(\d+)")
MULTI_REST = re.compile(r"\s*Z(\d*)\s*")
BARLINE_ONLY = re.compile(r"[\s:\[\]]*")


def estimate(abc: str) -> dict | None:
    """How long the score says the music is: bars, tempo, and the seconds they imply.

    Used to check a transcription against the recording it came from. A score whose
    tempo is wrong describes more or less music than the recording holds, and a
    cover follows the score, so it plays at that tempo.

    The tempo counts quarter notes, so a bar lasts its meter in quarters: a 6/8 bar is
    three, not six.  Z4 is four bars of rest, and a voice can change meter part way.
    """
    if not abc:
        return None
    tempo = re.search(r"^Q:1/4=(\d+)", abc, re.M)
    bpm = int(tempo.group(1)) if tempo else 120
    header_meter = (4, 4)
    meters: dict[str, tuple[int, int]] = {}
    quarters: dict[str, float] = {}
    bars: dict[str, int] = {}
    voice = None
    for raw in abc.split("\n"):
        line = raw.strip()
        if line.startswith("V:"):
            voice = line[2:].strip().split()[0] if line[2:].strip() else None
            continue
        meter = METER.match(line)
        if meter and not line.startswith("["):
            found = (int(meter.group(1)), int(meter.group(2)) or 4)
            if voice:
                meters[voice] = found
            else:
                header_meter = found
            continue
        if not line or line[0] == "%" or HEADER.match(line) or not voice:
            continue
        for bar in line.split("|"):
            if BARLINE_ONLY.fullmatch(bar):
                continue
            inline = METER.search(bar)
            if inline:
                meters[voice] = (int(inline.group(1)), int(inline.group(2)) or 4)
            beats, unit = meters.get(voice, header_meter)
            rest = MULTI_REST.fullmatch(bar)
            count = int(rest.group(1) or 1) if rest else 1
            bars[voice] = bars.get(voice, 0) + count
            quarters[voice] = quarters.get(voice, 0.0) + count * beats * 4 / unit
    if not quarters or not bpm:
        return None
    longest = max(quarters, key=quarters.get)
    return {"bars": bars[longest], "bpm": bpm, "seconds": round(quarters[longest] * 60 / bpm, 1)}


EARLY_SHARE = 0.6    # a score of one section: a render shorter than this share of it stopped early
EARLY_MIN = 30.0     # seconds: a score shorter than this is not judged
SECTION_MARK = re.compile(r"^% *\S", re.M)


def last_section_start(abc: str) -> float | None:
    """Seconds into the score where its last section begins, or None for a score of
    fewer than two sections."""
    marks = [m.start() for m in SECTION_MARK.finditer(abc or "")]
    if len(marks) < 2:
        return None
    before = estimate((abc or "")[:marks[-1]])
    return before["seconds"] if before else None


def stopped_early(duration: float | None, abc: str | None, cap: float | None) -> bool:
    """A render that ended before its score's last section began: the model wrote its
    end long before the music it was given ran out.  A score of one section is judged
    by the share of it that was played.  The cap counts as the end when it is the
    shorter, so a take capped on purpose is not this."""
    planned = estimate(abc or "")
    if not duration or not planned:
        return False
    expected = min(planned["seconds"], cap or planned["seconds"])
    if expected < EARLY_MIN:
        return False
    start = last_section_start(abc or "")
    if start is None:
        return duration < EARLY_SHARE * expected
    return duration < min(start, (cap - 2) if cap else start)


# A plan the model wrote with its thread lost can still be readable ABC: a vocal line
# leaping across octaves, bars of 1/8 then 9/8, chords spelled with double sharps.
# Written plans measured well inside these (the widest line 34 semitones, at most three
# metre changes, nine such chords); the runaways went far past them (#5).
RUNAWAY_SPAN = 36       # semitones: three octaves
RUNAWAY_METERS = 4      # changes of metre in the melody
RUNAWAY_DOUBLES = 12    # chord symbols with a double sharp or flat
RUNAWAY_SECONDS = 480   # a written plan longer than this is not a song (the usual cap is 360)...
RUNAWAY_CAP_SHARE = 1.3  # ...nor is one this much past a longer cap
NOTE = re.compile(r"([_^=]*)([A-Ga-g])([,']*)")
NOT_NOTES = re.compile(r'"[^"]*"|![^!]*!|\+[^+]*\+|\[[A-Za-z]:[^\]]*\]|%.*$')
DOUBLE_CHORD = re.compile(r'"[A-G](?:##|bb)')
STEPS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def voice_lines(abc: str, voice_name: str) -> list[str]:
    """The music lines of one voice, headers and comments left out."""
    lines, voice = [], None
    for raw in (abc or "").splitlines():
        line = raw.strip()
        match = VOICE.match(line)
        if match:
            voice = match.group(1)
            continue
        if voice == voice_name and line and not line.startswith("%") and not HEADER.match(line):
            lines.append(line)
    return lines


def pitch_span(abc: str, voice_name: str = "Vocal") -> int:
    """Semitones from the lowest note of a voice to its highest.  The key's own sharps
    and flats are left out: a semitone either way does not matter here."""
    pitches = []
    for line in voice_lines(abc, voice_name):
        for accidental, letter, octaves in NOTE.findall(NOT_NOTES.sub(" ", line)):
            pitches.append(STEPS[letter.upper()] + (12 if letter.islower() else 0)
                           + 12 * (octaves.count("'") - octaves.count(","))
                           + accidental.count("^") - accidental.count("_"))
    return max(pitches) - min(pitches) if pitches else 0


def meter_changes(abc: str, voice_name: str = "Vocal") -> int:
    """How many times the metre changes, in the header and then in one voice."""
    changes, current, voice = 0, None, None
    for raw in (abc or "").splitlines():
        line = raw.strip()
        match = VOICE.match(line)
        if match:
            voice = match.group(1)
            continue
        if voice not in (None, voice_name):
            continue
        for meter in re.finditer(r"(?:^|\[)M:\s*([^\]\s]+)", line):
            if current is not None and meter.group(1) != current:
                changes += 1
            current = meter.group(1)
    return changes


def sung_bars(abc: str) -> list[str]:
    """The Vocal voice's bars that hold at least one note, not only rests and chords."""
    return [bar for bar in vocal_bars(abc) if NOTE.search(NOT_NOTES.sub(" ", bar))]


def runaway(abc: str, instrumental: bool = False, cap: float | None = None, vocal: bool = True) -> list[str]:
    """What makes a written plan unsingable, or not a song, though it reads as a score.  Only
    for plans the model has just written: a transcription can change metre as often as its
    song, and can be as long as its recording.  `cap` is the length cap the render will run
    to, and `vocal` says the words have a vocal to sing them."""
    melody = "Ins" if instrumental else "Vocal"
    found = []
    planned = estimate(abc)
    if planned and planned["seconds"] > max(RUNAWAY_SECONDS, RUNAWAY_CAP_SHARE * (cap or 0)):
        found.append(f"a plan {planned['seconds'] / 60:.0f} minutes long")
    if vocal and not instrumental and vocal_bars(abc) and not sung_bars(abc):
        found.append("no sung notes in the vocal line")
    span = pitch_span(abc, melody)
    if span > RUNAWAY_SPAN:
        found.append(f"a {'melody' if instrumental else 'vocal line'} {span / 12:.0f} octaves wide")
    changes = meter_changes(abc, melody)
    if changes > RUNAWAY_METERS:
        found.append(f"the metre changing {changes} times")
    doubles = len(DOUBLE_CHORD.findall(abc or ""))
    if doubles > RUNAWAY_DOUBLES:
        found.append(f"{doubles} chords with double sharps or flats")
    return found


def vocal_bars(abc: str, voice_name: str = "Vocal") -> list[str]:
    """The bars of one voice, the Vocal voice unless told otherwise, in order."""
    bars, voice = [], None
    for raw in (abc or "").splitlines():
        line = raw.strip()
        match = VOICE.match(line)
        if match:
            voice = match.group(1)
            continue
        if voice != voice_name or not line or line.startswith("%") or HEADER.match(line):
            continue
        bars.extend(bar for bar in line.split("|") if bar.strip())
    return bars


def problems(abc: str, need_chords: bool = True, instrumental: bool = False) -> list[str]:
    """What makes this score unusable, in words a person can act on.  Empty when fine.
    An instrumental plan keeps a Vocal voice of rests that carries the chords, and
    puts its melody in an Ins voice; either one will do."""
    found = []
    if COLLAPSE.search(abc or ""):
        found.append("repetitive token collapse")
    if not KEY.search(abc or ""):
        found.append("no key")
    bars = vocal_bars(abc)
    if instrumental and not bars:
        bars = vocal_bars(abc, "Ins")
    if not bars:
        found.append("no instrument part" if instrumental else "no vocal part")
    elif len(bars) < MIN_BARS:
        found.append(f"only {len(bars)} bar{'s' if len(bars) != 1 else ''}")
    if need_chords and bars and not any(CHORD.search(bar) for bar in bars):
        found.append("no chord symbols")
    return found
