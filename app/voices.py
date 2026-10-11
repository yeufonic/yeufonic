"""Who sings: a man, a woman or both, as cue lines in the lyrics ask.

The render does not take the singer from a cue line.  It sings the plan's vocal line an
octave below where it is written, and the register decides the voice: a phrase written low
comes out as a man, one written an octave higher as a woman.  The planner, left alone, writes
a verse in two octaves and changes about every four lines, whatever the cues say.

So the cues are kept on the plan itself.  Each phrase of the vocal line (a run of notes
between rests) is matched to the lyric lines it carries, and moved by whole octaves into the
register of the voice cued for them; where both are cued every note becomes an octave pair,
which is sung as two voices.  Nothing else in the plan changes: the notes, their lengths, the
chords and the other voice are as the planner wrote them."""
from __future__ import annotations

import re
from typing import Any

from . import transpose

MALE, FEMALE, BOTH = "male", "female", "both"

# A stretch of melody is judged by the mean pitch it is written at, weighted by length (MIDI numbers,
# C4 = 60).  The planner writes in two clusters, around C4 to G4 and an octave above; the lower is sung
# by a man and the upper by a woman.  Between them, around A4 to B4, either voice has sung what was
# written, following the lines around it, so a stretch found there is left where it is: moved up an
# octave it would sit above where a woman's line is sung at all (tried: it came out low instead).
MALE_TOP = 71.0
MALE_FLOOR = 53.0
FEMALE_FLOOR = 69.0
FEMALE_TOP = 81.0
# No single phrase is carried past where its voice is sung by the stretch it belongs to.
PHRASE_TOP = 80.0
PHRASE_FLOOR = 53.0
# Phrases whose means are within this many semitones of each other are one stretch of tune and move
# together, so a melody is never broken in the middle to make a point about a single phrase.
LEAP = 7.0

# ------------------------------------------------------------------ the cues in the lyrics
_MALE_STRONG = r"male|masculine?|masculin[eo]?|m[aä]nnlich"
_FEMALE_STRONG = r"female|feminine?|f[eé]minine?|femenin[ao]|weiblich"
_MALE_WEAK = r"man|men|boy|boys|him|he|baritone|tenor|homme|hombre|mann"
_FEMALE_WEAK = r"woman|women|girl|girls|her|she|soprano|alto|femme|mujer|frau"
_BOTH = r"both|duet|duo|together|unison|ensemble|tous les deux"
_SINGING = r"voice|voices|vocal|vocals|sing|sings|singer|singers|singing|voix|voz|stimme"
_SECTION = re.compile(r"(?i)\b(pre[- ]?chorus|chorus|refrain|hook|verse|bridge|intro|outro|coda|interlude|solo|break|instrumental)\b")
_WHOLE = re.compile(r"^\s*(?:\[(?P<square>[^\]]*)\]|\((?P<round>[^)]*)\))\s*$")


def _word(pattern: str, text: str) -> bool:
    return re.search(rf"(?i)(?<![\w]){'(?:' + pattern + ')'}(?![\w])", text) is not None


def cue_of(line: str) -> str | None:
    """The voice a line of the lyrics asks for, when the line is a cue: a whole line in square
    brackets or in parentheses that names a voice.  A sung line never is one, and a line in
    parentheses has to say so plainly ("male voice", "the woman sings"), since backing words are
    written that way too."""
    found = _WHOLE.match(line or "")
    if not found:
        return None
    square = found.group("square") is not None
    text = found.group("square") if square else found.group("round")
    # In square brackets, or beside a word for singing, the everyday words count too: "[Him]", "(the woman sings)".
    plain = square or _word(_SINGING, text)
    male = _word(_MALE_STRONG, text) or (plain and _word(_MALE_WEAK, text))
    female = _word(_FEMALE_STRONG, text) or (plain and _word(_FEMALE_WEAK, text))
    if (male and female) or (plain and _word(_BOTH, text)):
        return BOTH
    return MALE if male else FEMALE if female else None


def section_of(line: str) -> str | None:
    """The kind of section a bracketed line opens ("[Verse 2]" is a verse), or None."""
    found = _WHOLE.match(line or "")
    if not found or found.group("square") is None:
        return None
    named = _SECTION.search(found.group("square"))
    if not named:
        return None
    name = re.sub(r"[- ]", "", named.group(1).lower())
    return {"prechorus": "pre-chorus", "refrain": "chorus", "hook": "chorus", "coda": "outro"}.get(name, name)


_VOWELS = re.compile(r"[aeiouyàâäáãåæéèêëíìîïóòôöõœúùûüÿ]+", re.I)
_CJK = re.compile("[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")   # kana, Han, Hangul


def syllables(line: str) -> int:
    """About how many notes a line wants: one for each run of vowels, or each character of a
    script that writes a syllable to a character."""
    count = 0
    for word in re.findall(r"[^\s\-—–]+", line or ""):
        cjk = len(_CJK.findall(word))
        count += cjk if cjk else max(1, len(_VOWELS.findall(word)))
    return count


def sung_lines(lyrics: str) -> list[dict[str, Any]]:
    """The lines that are sung, in order, each with the voice cued for it and the section it is in.
    A cue holds until the next cue or the next section: a section that says nothing is left to the plan."""
    out: list[dict[str, Any]] = []
    cue, section = None, None
    for raw in (lyrics or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        opened, asked = section_of(line), cue_of(line)
        if opened:
            section, cue = opened, asked
            continue
        if asked:
            cue = asked
            continue
        if _WHOLE.match(line) and _WHOLE.match(line).group("square") is not None:
            continue   # another direction in brackets: "[strings]"
        out.append({"text": line, "cue": cue, "section": section, "syllables": syllables(line)})
    return out


def has_cues(lyrics: str) -> bool:
    return any(cue_of(line) for line in (lyrics or "").splitlines())


# ------------------------------------------------------------------ the plan's vocal line
_TOKEN = re.compile(
    r'(?P<quote>"(?:[^"\\]|\\.)*")|(?P<deco>![^!\n]*!)|(?P<inline>\[[A-Za-z]:[^\]]*\])'
    r"|(?P<comment>%.*$)"
    r"|(?P<chord>\[(?P<inside>[^\]\n|:]*)\])"
    r"|(?P<note>(?P<acc>\^\^|\^|__|_|=)?(?P<letter>[A-Ga-g])(?P<marks>[,']*))"
    r"|(?P<rest>[zx])|(?P<bars>Z)|(?P<bar>\|)"
)
_MEMBER = re.compile(r"(?P<acc>\^\^|\^|__|_|=)?(?P<letter>[A-Ga-g])(?P<marks>[,']*)(?P<len>[\d/]*)")
_LENGTH = re.compile(r"(\d*)((?:/\d*)*)")
_FIELD = re.compile(r"^[A-Za-z]:")
_ACC = {"^^": 2, "^": 1, "=": 0, "__": -2, "_": -1}


def _units(text: str) -> float:
    found = _LENGTH.match(text)
    value = float(found.group(1)) if found.group(1) else 1.0
    for part in re.findall(r"/(\d*)", found.group(2)):
        value /= float(part) if part else 2.0
    return value


def _height(letter: str, marks: str) -> int:
    """The octave a note is written in: 4 for C to B, 5 for c to b."""
    return (5 if letter.islower() else 4) + marks.count("'") - marks.count(",")


def _spelled(letter: str, octave: int) -> str:
    return letter.lower() + "'" * (octave - 5) if octave >= 5 else letter.upper() + "," * (4 - octave)


def _fraction(text: str, default: float) -> float:
    found = re.match(r"\s*(\d+)\s*/\s*(\d+)", text or "")
    return int(found.group(1)) / int(found.group(2)) if found and int(found.group(2)) else default


def read(abc: str) -> dict[str, Any]:
    """The vocal line as its notes in order.  Each note knows where it is written in the text,
    how long it is, how long the rest before it was, and which section it is in."""
    lines = (abc or "").split("\n")
    unit, meter, voice, section = 1 / 8, 1.0, "", None
    notes: list[dict[str, Any]] = []
    rest = 0.0
    for index, raw in enumerate(lines):
        line = raw.rstrip("\r")
        stripped = line.strip()
        if stripped.startswith("%"):
            section = stripped.lstrip("%").strip().lower() or section
            continue
        if stripped.startswith("V:"):
            voice = stripped[2:].split()[0] if stripped[2:].split() else ""
            continue
        if _FIELD.match(stripped):
            if stripped.startswith("L:"):
                unit = _fraction(stripped[2:], unit)
            elif stripped.startswith("M:"):
                meter = _fraction(stripped[2:], meter)
            continue
        if voice != "Vocal":
            continue
        for found in _TOKEN.finditer(line):
            if found.group("inline"):
                field = found.group("inline")[1:-1]
                if field.startswith("M:"):
                    meter = _fraction(field[2:], meter)
                elif field.startswith("L:"):
                    unit = _fraction(field[2:], unit)
                continue
            if found.group("rest"):
                rest += _units(line[found.end():]) * unit
            elif found.group("bars"):
                rest += _units(line[found.end():]) * meter
            elif found.group("chord") or found.group("note"):
                if found.group("chord"):
                    members = [m for m in _MEMBER.finditer(found.group("inside")) if m.group("letter")]
                    if not members:
                        continue
                    parts = [{"acc": m.group("acc") or "", "letter": m.group("letter"), "marks": m.group("marks"),
                              "len": m.group("len")} for m in members]
                    inner = _units(parts[0]["len"]) if parts[0]["len"] else 1.0
                    length = inner * _units(line[found.end():]) * unit
                else:
                    parts = [{"acc": found.group("acc") or "", "letter": found.group("letter"),
                              "marks": found.group("marks"), "len": ""}]
                    length = _units(line[found.end():]) * unit
                top = max(parts, key=lambda p: (_height(p["letter"], p["marks"]), transpose.BASE[p["letter"].upper()]))
                tail = line[found.end():]
                notes.append({
                    "line": index, "start": found.start(), "end": found.end(), "parts": parts, "top": top,
                    "chord": bool(found.group("chord")),
                    "pitch": 12 * (_height(top["letter"], top["marks"]) + 1) + transpose.BASE[top["letter"].upper()],
                    "length": length, "rest_before": rest, "section": section,
                    "tied": bool(transpose.TIE_AFTER.match(tail)),
                })
                rest = 0.0
    return {"lines": lines, "notes": notes, "quarter": 0.25}


def phrases(notes: list[dict[str, Any]], gap: float) -> list[list[dict[str, Any]]]:
    """The notes as phrases: a new one wherever the rests before a note come to `gap` or more."""
    out: list[list[dict[str, Any]]] = []
    for note in notes:
        if not out or note["rest_before"] >= gap:
            out.append([])
        out[-1].append(note)
    return out


def _mean(phrase: list[dict[str, Any]]) -> float:
    total = sum(n["length"] for n in phrase) or 1.0
    return sum(n["pitch"] * n["length"] for n in phrase) / total


def _onsets(phrase: list[dict[str, Any]]) -> int:
    """The notes a phrase gives words to: one tied on from the note before carries none."""
    count, tied = 0, False
    for note in phrase:
        count += 0 if tied else 1
        tied = note["tied"]
    return max(count, 1)


def _section(phrase: list[dict[str, Any]]) -> str | None:
    """The section most of a phrase is in: one often starts with a pickup in the bar before."""
    seen: dict[str | None, int] = {}
    for note in phrase:
        seen[note["section"]] = seen.get(note["section"], 0) + 1
    name = max(seen, key=lambda key: seen[key])
    if not name:
        return None
    found = _SECTION.search(name)
    if not found:
        return name
    low = re.sub(r"[- ]", "", found.group(1).lower())
    return {"prechorus": "pre-chorus", "refrain": "chorus", "hook": "chorus", "coda": "outro"}.get(low, low)


# ------------------------------------------------------------------ which phrase carries which line
SPLIT = 2.0          # a line sung as two phrases, or two lines in one
SKIP = 8.0           # a line never sung, or a phrase with no line of its own
ELSEWHERE = 8.0      # a line in a section of another name than the lyrics give it


def match(lines: list[dict[str, Any]], groups: list[list[dict[str, Any]]]) -> tuple[list[list[int]], list[bool], float]:
    """For each phrase, the lyric lines it carries (usually one), found for the whole song at once:
    the lines in order, the phrases in order, each line where its syllables fit the notes best.
    Also, for each phrase, whether it is one line sung as one phrase, which is as sure as this gets."""
    n, m = len(lines), len(groups)
    size = [_onsets(g) for g in groups]
    place = [_section(g) for g in groups]
    want = [line["syllables"] for line in lines]

    def away(i: int, j: int) -> float:
        """A plan may name a section otherwise than the lyrics do, but lines the plan never reached
        are left unsung rather than pushed onto the phrases of another section."""
        a, b = lines[i]["section"], place[j]
        return ELSEWHERE if a and b and a != b else 0.0

    best = [[float("inf")] * (m + 1) for _ in range(n + 1)]
    back: list[list[tuple[int, int] | None]] = [[None] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            here = best[i][j]
            if here == float("inf"):
                continue
            steps = []
            if i < n and j < m:
                steps.append((1, 1, abs(want[i] - size[j]) + away(i, j)))
            if i < n and j + 1 < m:
                steps.append((1, 2, abs(want[i] - size[j] - size[j + 1]) + SPLIT + away(i, j)))
            if i + 1 < n and j < m:
                steps.append((2, 1, abs(want[i] + want[i + 1] - size[j]) + SPLIT + away(i, j)))
            if i < n:
                steps.append((1, 0, SKIP))
            if j < m:
                steps.append((0, 1, SKIP))
            for di, dj, cost in steps:
                if here + cost < best[i + di][j + dj]:
                    best[i + di][j + dj] = here + cost
                    back[i + di][j + dj] = (di, dj)
    carried: list[list[int]] = [[] for _ in range(m)]
    plain = [False] * m
    i, j = n, m
    while (i, j) != (0, 0):
        di, dj = back[i][j]
        if di and dj:
            for phrase in range(j - dj, j):
                carried[phrase] = list(range(i - di, i))
                plain[phrase] = (di, dj) == (1, 1)
        i, j = i - di, j - dj
    return carried, plain, best[n][m]


def voices_of(abc: str, lyrics: str) -> tuple[dict[str, Any], list[list[dict[str, Any]]], list[str | None]]:
    """The plan read, its vocal line in phrases, and the voice cued for each phrase (None where
    no cue reaches it).  The length of rest that parts two phrases is whichever fits the lines best."""
    plan = read(abc)
    lines = sung_lines(lyrics)
    notes = plan["notes"]
    if not notes or not lines:
        return plan, [], []
    chosen: tuple[float, list[list[dict[str, Any]]], list[list[int]], list[bool]] | None = None
    for quarters in (0.5, 0.75, 1.0, 1.5, 2.0):
        groups = phrases(notes, quarters * plan["quarter"])
        carried, plain, cost = match(lines, groups)
        if chosen is None or cost < chosen[0]:
            chosen = (cost, groups, carried, plain)
    _, groups, carried, plain = chosen
    cues: list[str | None] = []
    for held in carried:
        asked = [lines[i]["cue"] for i in held if lines[i]["cue"]]
        cues.append(asked[0] if asked else None)
    return plan, groups, _settled(groups, cues, plain)


def _settled(groups: list[list[dict[str, Any]]], cues: list[str | None], plain: list[bool]) -> list[str | None]:
    """The cues with a change of voice set on the plan's own change of register when that is one
    phrase away and the count is not to be trusted there.  Where lines are sung in halves, or two
    to a phrase, syllables place a line only to within a phrase; the melody says exactly where one
    voice stops and the next begins, and a phrase left on the wrong side would be torn from its
    tune.  Where each line is plainly one phrase, the count stands."""
    out = list(cues)
    height = [_mean(g) for g in groups]

    def leap(k: int) -> bool:      # between phrase k - 1 and phrase k
        return 0 < k < len(groups) and abs(height[k] - height[k - 1]) >= LEAP

    for k in range(1, len(out)):
        if not out[k] or not out[k - 1] or out[k] == out[k - 1] or leap(k) or (plain[k] and plain[k - 1]):
            continue
        later = leap(k + 1) and k + 1 < len(out) and cues[k + 1] == cues[k]
        earlier = leap(k - 1) and k >= 2 and cues[k - 2] == cues[k - 1]
        if later and not earlier:
            out[k] = out[k - 1]
        elif earlier and not later:
            out[k - 1] = out[k]
    return out


# ------------------------------------------------------------------ moving the phrases
def _octaves(mean: float, cue: str) -> int:
    """How many octaves to move a stretch of tune written at `mean` so it sits where its voice is sung."""
    moved = 0
    if cue == MALE:
        while mean + 12 * moved > MALE_TOP:
            moved -= 1
        while mean + 12 * moved < MALE_FLOOR and mean + 12 * (moved + 1) <= MALE_TOP:
            moved += 1
    else:   # a woman, or the upper voice of a pair
        while mean + 12 * moved < FEMALE_FLOOR:
            moved += 1
        while mean + 12 * moved > FEMALE_TOP and mean + 12 * (moved - 1) >= FEMALE_FLOOR:
            moved -= 1
    return moved


def moves(groups: list[list[dict[str, Any]]], cues: list[str | None]) -> list[int]:
    """The octaves each phrase moves by.  Neighbouring phrases of one voice that sit together are a
    stretch of tune and are judged, and moved, as one: the planner's habit is a whole run of lines
    an octave up, and that run comes down as it went up."""
    out = [0] * len(groups)
    start = 0
    while start < len(groups):
        end = start + 1
        if cues[start]:
            while (end < len(groups) and cues[end] == cues[start]
                   and abs(_mean(groups[end]) - _mean(groups[end - 1])) < LEAP):
                end += 1
            notes = [note for group in groups[start:end] for note in group]
            together = _octaves(_mean(notes), cues[start])
            for k in range(start, end):
                moved, mean = together, _mean(groups[k])
                # ... unless staying behind would leave it in the other voice's register
                if cues[start] == MALE:
                    while moved < 0 and mean + 12 * moved < PHRASE_FLOOR and mean + 12 * (moved + 1) <= MALE_TOP:
                        moved += 1
                else:
                    while moved > 0 and mean + 12 * moved > PHRASE_TOP and mean + 12 * (moved - 1) >= FEMALE_FLOOR:
                        moved -= 1
                out[k] = moved
        start = end
    return out


def _key_at(lines: list[str]) -> dict[int, dict[str, int]]:
    """The key signature in force on each line of the text."""
    out, key = {}, transpose.signature(0)
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped.startswith("K:"):
            found, _ = transpose._key_and_rest(stripped)
            if found:
                key = transpose.signature(found[2])
        out[index] = key
    return out


def fit(abc: str, lyrics: str) -> tuple[str, dict[str, Any] | None]:
    """The plan with every cued phrase of its vocal line in the register of its voice, and what
    was done.  A plan already as cued comes back unchanged, so this can be run again at any time;
    lyrics with no cues leave the plan alone and return no summary."""
    if not has_cues(lyrics) or not (abc or "").strip():
        return abc, None
    plan, groups, cues = voices_of(abc, lyrics)
    summary = {"phrases": 0, "moved": 0, "paired": 0, "singled": 0, MALE: 0, FEMALE: 0, BOTH: 0}
    wanted: dict[int, tuple[int, bool]] = {}     # id(note) -> (octaves, as a pair)
    for group, cue, moved in zip(groups, cues, moves(groups, cues)):
        if not cue:
            continue
        summary["phrases"] += 1
        summary[cue] += 1
        pair = cue == BOTH
        was_pair = all(len(n["parts"]) > 1 for n in group)
        if moved:
            summary["moved"] += 1
        if pair and not was_pair:
            summary["paired"] += 1
        if not pair and any(len(n["parts"]) > 1 for n in group):
            summary["singled"] += 1
        for note in group:
            wanted[id(note)] = (moved, pair)
    if not wanted:
        return abc, summary
    lines = list(plan["lines"])
    keys = _key_at(lines)
    by_line: dict[int, list[dict[str, Any]]] = {}
    for note in plan["notes"]:
        by_line.setdefault(note["line"], []).append(note)
    changed = False
    for index, notes in by_line.items():
        new = _rewrite(lines[index], notes, wanted, keys[index])
        if new != lines[index]:
            lines[index], changed = new, True
    summary["changed"] = changed
    return ("\n".join(lines) if changed else abc), summary


def _members(note: dict[str, Any], want: tuple[int, bool] | None) -> list[tuple[dict[str, Any], int]]:
    """The pitches a note is written as, each as (the part it comes from, its octave): as it
    stands, or as asked: its top note moved, alone or with the octave below."""
    if want is None:
        return [(part, _height(part["letter"], part["marks"])) for part in note["parts"]]
    octaves, pair = want
    top = _height(note["top"]["letter"], note["top"]["marks"]) + octaves
    return [(note["top"], top), (note["top"], top - 1)] if pair else [(note["top"], top)]


def _rewrite(line: str, notes: list[dict[str, Any]], wanted: dict[int, tuple[int, bool]], key: dict[str, int]) -> str:
    """One line of the vocal part with its notes moved.  An accidental holds for a pitch in its
    own octave to the end of the bar, so in a bar where anything moves every note is written to
    mean what it meant before; a bar where nothing moves is left exactly as it was."""
    at = {note["start"]: note for note in notes}
    pieces: list[tuple[int, int, str]] = []
    bar: list[dict[str, Any]] = []
    heard: dict[tuple[str, int], int] = {}

    def spelling(members: list[tuple[dict[str, Any], int]]) -> list[tuple[str, int]]:
        return sorted((part["letter"].upper(), octave) for part, octave in members)

    def close() -> None:
        if any(spelling(_members(n, None)) != spelling(_members(n, wanted.get(id(n)))) for n in bar):
            shown: dict[tuple[str, int], int] = {}
            for note in bar:
                out = []
                for part, octave in _members(note, wanted.get(id(note))):
                    letter, means = part["letter"].upper(), part["meant"]
                    sign = transpose.SYMBOL[means] if means != shown.get((letter, octave), key.get(letter, 0)) else ""
                    shown[(letter, octave)] = means
                    out.append(sign + _spelled(letter, octave) + part["len"])
                pieces.append((note["start"], note["end"], "[" + "".join(out) + "]" if len(out) > 1 else out[0]))
        bar.clear()
        heard.clear()

    for found in _TOKEN.finditer(line):
        if found.group("bar"):
            close()
        elif found.start() in at and (found.group("note") or found.group("chord")):
            note = at[found.start()]
            for part in note["parts"]:
                letter, octave = part["letter"].upper(), _height(part["letter"], part["marks"])
                said = _ACC.get(part["acc"])
                part["meant"] = said if said is not None else heard.get((letter, octave), key.get(letter, 0))
                if said is not None:
                    heard[(letter, octave)] = said
            bar.append(note)
    close()
    for start, end, text in sorted(pieces, reverse=True):
        line = line[:start] + text + line[end:]
    return line


def describe(summary: dict[str, Any] | None) -> str:
    """What fitting did, in a line for the page."""
    if summary is None:
        return "The lyrics have no voice cues."
    if not summary["phrases"]:
        return "No sung phrase could be matched to a cued line."
    if not summary.get("changed"):
        return "The voices are already as cued."
    done = []
    if summary["moved"]:
        done.append(f"{summary['moved']} phrase{'s' if summary['moved'] != 1 else ''} moved by an octave")
    if summary["paired"]:
        done.append(f"{summary['paired']} doubled for both voices")
    if summary["singled"] and not done:
        done.append(f"{summary['singled']} back to one voice")
    return "Voices fitted to the cues: " + ", ".join(done) + "."
