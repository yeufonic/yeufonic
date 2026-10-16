"""Moving a written plan to another key.

The planner does not follow a key in the style (measured: asked for F# minor, A major or Eb
major it wrote the keys it writes with no hint), so a key lock is done afterwards, on the plan:
every note and every chord symbol moves by the same number of semitones and the key signature
is rewritten to match.  Notes are read as absolute pitches (the key signature and the bar's
accidentals applied) and spelled again in the new key, so a plan in D minor moved up three
semitones is the same music in F minor, not the same letters under a new signature.

The mode is the plan's own: a major plan stays major, a minor one minor.  Only the tonic moves.
A score this cannot read with certainty (a mode, a key change part way, a key it cannot parse)
is left as it is; `to_key` returns None and the caller says so."""
from __future__ import annotations

import re

from . import music

BASE = music.PITCH_CLASS
SHARP_ORDER = "FCGDAEB"
FLAT_ORDER = "BEADGCF"
# The signature (sharps positive, flats negative) of the key on each tonic pitch class.
MAJOR = {0: 0, 1: -5, 2: 2, 3: -3, 4: 4, 5: -1, 6: 6, 7: 1, 8: -4, 9: 3, 10: -2, 11: 5}
MINOR = {0: -3, 1: 4, 2: -1, 3: -6, 4: 1, 5: -4, 6: 3, 7: -2, 8: 5, 9: 0, 10: -5, 11: 2}
NAME_SHARP = {0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F", 6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"}
NAME_FLAT = {0: "C", 1: "Db", 2: "D", 3: "Eb", 4: "E", 5: "F", 6: "Gb", 7: "G", 8: "Ab", 9: "A", 10: "Bb", 11: "B"}
SHARP_SPELLING = {1: ("C", 1), 3: ("D", 1), 6: ("F", 1), 8: ("G", 1), 10: ("A", 1)}
FLAT_SPELLING = {1: ("D", -1), 3: ("E", -1), 6: ("G", -1), 8: ("A", -1), 10: ("B", -1)}
NATURAL = {0: "C", 2: "D", 4: "E", 5: "F", 7: "G", 9: "A", 11: "B"}
SYMBOL = music.ACCIDENTAL_SYMBOL

KEY_TEXT = re.compile(r"^\s*([A-Ga-g])([#b]?)\s*(m(?![a-z])|min(?:or)?|maj(?:or)?|M|ion|aeo)?\s*$")
KEY_LINE = re.compile(r"^K:\s*(\S+)(.*)$")
FIELD_LINE = re.compile(r"^[A-Za-z]:")
CHORD = re.compile(r"^([A-G])([#b]?)((?:m(?!aj)|min|maj|M|dim|aug|sus|add|\+|-|°|ø|[0-9]|#|b|\(|\)|,)*)(?:/([A-G])([#b]?))?$")
TOKEN = re.compile(
    r'(?P<quote>"(?:[^"\\]|\\.)*")|(?P<deco>![^!\n]*!|\+[^+\n]*\+)|(?P<inline>\[[A-Za-z]:[^\]]*\])'
    r"|(?P<comment>%.*$)|(?P<note>(?P<acc>\^\^|\^|__|_|=)?(?P<letter>[A-Ga-g])(?P<marks>[,']*))|(?P<bar>\|)")


def read_key(text: str) -> tuple[int, bool] | None:
    """(tonic pitch class, minor?) for 'Dm', 'F#', 'Bbmaj', 'C#min'; None for a mode or anything else."""
    found = KEY_TEXT.match(text or "")
    if not found:
        return None
    letter, accidental, mode = found.group(1).upper(), found.group(2), (found.group(3) or "")
    minor = mode in ("m", "min", "minor", "aeo")
    return (BASE[letter] + (1 if accidental == "#" else -1 if accidental == "b" else 0)) % 12, minor


def signature(sharps: int) -> dict[str, int]:
    """The accidental each letter carries in a key with this many sharps (or, negative, flats)."""
    if sharps >= 0:
        return {letter: 1 for letter in SHARP_ORDER[:sharps]}
    return {letter: -1 for letter in FLAT_ORDER[:-sharps]}


def _sharps_of(name: str, minor: bool) -> int:
    """The signature of a spelled key ('Db', 'C#', 'F#'): sharps positive, flats negative, and 99
    when the spelling would need more than seven accidentals (B# major, Fb minor)."""
    read = read_key(name)
    if not read:
        return 99
    count = (MINOR if minor else MAJOR)[read[0]]
    accidental = name.strip()[1:2]
    if accidental == "b" and count > 0:
        count -= 12
    if accidental == "#" and count < 0:
        count += 12
    return count if abs(count) <= 7 else 99


def key_name(tonic: int, minor: bool, prefer_flats: bool) -> str:
    """The key to write on a tonic: the spelling with the fewest accidentals, and on a tie
    (F# or Gb) the one the person named."""
    sharp, flat = NAME_SHARP[tonic], NAME_FLAT[tonic]
    if sharp != flat:
        light = abs(_sharps_of(sharp, minor)) - abs(_sharps_of(flat, minor))
        name = flat if light > 0 or (light == 0 and prefer_flats) else sharp
    else:
        name = sharp
    return name + ("m" if minor else "")


MODE_WORD = re.compile(r"^\s*(min(?:or)?|aeo(?:lian)?|maj(?:or)?|ion(?:ian)?|m|dor\w*|mix\w*|lyd\w*|phr\w*|loc\w*)\b", re.I)


def _key_and_rest(line: str) -> tuple[tuple[int, bool, int] | None, str]:
    """Read a K: line: ((tonic, minor, sharps), what follows the key and its mode), or (None, "")
    for a mode other than major and minor, or anything unreadable."""
    found = KEY_LINE.match(line.strip())
    if not found:
        return None, ""
    word, rest = found.group(1), found.group(2)
    read = read_key(word)
    if not read:
        return None, ""
    tonic, minor = read
    spoken = MODE_WORD.match(rest)
    if spoken:
        mode = spoken.group(1).lower()
        if mode[:3] in ("dor", "mix", "lyd", "phr", "loc"):
            return None, ""
        minor = mode[0] in ("m",) and not mode.startswith("maj") or mode.startswith("aeo")
        rest = rest[spoken.end():]
    sharps = _sharps_of(word[0].upper() + (word[1:2] if word[1:2] in ("#", "b") else ""), minor)
    return (None, "") if sharps == 99 else ((tonic, minor, sharps), rest)


def plan_key(abc: str) -> tuple[int, bool, int] | None:
    """(tonic, minor, sharps) of a score with exactly one key and no change of it, else None."""
    keys = [line for line in abc.splitlines() if KEY_LINE.match(line.strip())]
    if len(keys) != 1 or re.search(r"\[K:", abc):
        return None
    return _key_and_rest(keys[0])[0]


def _spell(pc: int, key: dict[str, int], flats: bool) -> tuple[str, int]:
    for letter, base in BASE.items():
        if (base + key.get(letter, 0)) % 12 == pc:
            return letter, key.get(letter, 0)
    if pc in NATURAL:
        return NATURAL[pc], 0
    return (FLAT_SPELLING if flats else SHARP_SPELLING)[pc]


def _chord(text: str, steps: int, key: dict[str, int], flats: bool) -> str:
    found = CHORD.match(text)
    if not found:
        return text
    root = (BASE[found.group(1)] + (1 if found.group(2) == "#" else -1 if found.group(2) == "b" else 0) + steps) % 12
    letter, acc = _spell(root, key, flats)
    out = letter + ("#" if acc > 0 else "b" if acc < 0 else "") + found.group(3)
    if found.group(4):
        bass = (BASE[found.group(4)] + (1 if found.group(5) == "#" else -1 if found.group(5) == "b" else 0) + steps) % 12
        letter, acc = _spell(bass, key, flats)
        out += "/" + letter + ("#" if acc > 0 else "b" if acc < 0 else "")
    return out


TIE_AFTER = re.compile(r"^[\d/<>]*-")


def _music_line(line: str, steps: int, key_in: dict[str, int], key_out: dict[str, int], flats: bool,
                carry: int | None = None) -> tuple[str, int | None]:
    """One line of music moved, and the pitch a tie leaves open at its end (for the next line).

    abcjs does not carry the accidental of a note that continues a tie across a barline to the
    notes after it in that bar, unlike the notes of any other bar; the score is read here as abcjs
    reads it, so the preview plays the same music before and after the move."""
    bar_in: dict[tuple[str, int], int] = {}
    bar_out: dict[tuple[str, int], int] = {}
    state = {"tie": None, "carry": carry}

    def move(found: re.Match) -> str:
        if found.group("quote"):
            body = found.group("quote")[1:-1]
            return '"' + _chord(body, steps, key_out, flats) + '"'
        if found.group("bar"):
            bar_in.clear()
            bar_out.clear()
            state["carry"], state["tie"] = state["tie"], None
            return "|"
        if found.group("note"):
            letter, marks = found.group("letter"), found.group("marks")
            upper = letter.isupper()
            octave = (4 if upper else 5) + (marks.count("'") - marks.count(","))
            letter = letter.upper()
            spoken = {"^^": 2, "^": 1, "=": 0, "__": -2, "_": -1}.get(found.group("acc") or "")
            explicit = spoken is not None
            if spoken is None:
                spoken = bar_in.get((letter, octave), key_in.get(letter, 0))
            heard = 12 * (octave + 1) + BASE[letter] + spoken
            continuing = state["carry"] is not None and state["carry"] == heard
            state["carry"] = None
            if explicit and not continuing:
                bar_in[(letter, octave)] = spoken
            state["tie"] = heard if TIE_AFTER.match(found.string[found.end():]) else None
            midi = heard + steps
            new_letter, new_acc = _spell(midi % 12, key_out, flats)
            new_octave = (midi - BASE[new_letter] - new_acc) // 12 - 1
            shown = SYMBOL[new_acc] if new_acc != bar_out.get((new_letter, new_octave), key_out.get(new_letter, 0)) else ""
            if not continuing:
                bar_out[(new_letter, new_octave)] = new_acc
            text = new_letter.lower() if new_octave >= 5 else new_letter
            return shown + text + ("'" * (new_octave - 5) if new_octave >= 5 else "," * (4 - new_octave))
        return found.group(0)

    moved = TOKEN.sub(move, line)
    # A tie left open when a line ends on a barline goes on into the first note of the next.
    return moved, state["carry"] if re.search(r"\|[\]:]?\s*$", line) else None


def to_key(abc: str, target: str) -> str | None:
    """The score moved so its tonic is `target` ('F#m', 'Eb', 'C'), the plan's mode kept.  The
    shortest way: at most a fourth down or a tritone up.  Returns the score unchanged if it is
    in that key already, and None when it cannot be read with certainty."""
    wanted, current = read_key(target), plan_key(abc or "")
    if not wanted or not current:
        return None
    tonic, minor, sharps = current
    steps = (wanted[0] - tonic) % 12
    if steps > 6:
        steps -= 12
    if steps == 0:
        return abc
    flats_named = bool(re.match(r"^\s*[A-Ga-g]b", target))
    new_tonic = (tonic + steps) % 12
    new_key = key_name(new_tonic, minor, flats_named)
    new_sharps = _sharps_of(new_key, minor)
    key_in, key_out = signature(sharps), signature(new_sharps)
    flats = new_sharps < 0
    out, voice, carries = [], "", {}
    for raw in abc.split("\n"):
        line = raw.rstrip("\r")
        stripped = line.strip()
        found = KEY_LINE.match(stripped)
        if found:
            out.append("K:" + new_key + _key_and_rest(stripped)[1])
        elif not stripped or stripped.startswith("%") or FIELD_LINE.match(stripped):
            if stripped.startswith("V:") and stripped[2:].split():
                voice = stripped[2:].split()[0]          # a tie belongs to its voice
            out.append(line)
        else:
            text, carries[voice] = _music_line(line, steps, key_in, key_out, flats, carries.get(voice))
            out.append(text)
    return "\n".join(out)
