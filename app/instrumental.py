"""Instrumentals: YuE2 with a LoRA that plans and plays a song with no vocal.

Where a song has lyrics, an instrumental has a structure, in one of three forms
the LoRA was trained on:

    [instrumental]                         YuE2 chooses the sections
    [intro] [verse] [chorus] ...           you choose the sections, YuE2 the lengths
    [intro 0:00-0:15] [verse 0:15-0:45]    you choose both

The LoRA adapts the language model only, so it is loaded on the CLIP side, for
the plan and for the render alike."""
from __future__ import annotations

import re
from fractions import Fraction
import subprocess
from pathlib import Path

SECTIONS = ("intro", "verse", "pre-chorus", "chorus", "bridge", "outro")
# The LoRA is always held at full strength.
#
# There was a Feel control that loosened it to 0.8, then 0.9, for more movement
# between sections. Measured at real song lengths, any loosening lets the vocal
# back in: at two minutes, 0.90 sang through 94%, 94% and 66% of three renders,
# and 0.95 through 15% of one, while full strength was clean on every seed and
# every length tried. An earlier sweep that looked clean had used one-minute
# renders, which are too short to fail this way.
#
# So the control is gone rather than retuned: its only safe setting was the
# default. Movement is still available through Plan variety, Harmony,
# Interpretation and choosing the sections, none of which risk a vocal.
FEELS = {"steady": 1.0}

BARE = "[instrumental]"
_TAG = re.compile(r"^\[\s*([a-z-]+)(?:\s+(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2}))?\s*\]$")


def normalise(text: str) -> str:
    """The structure as the LoRA expects it, one tag per line, lower case.  Raises
    ValueError with a reason a person can act on."""
    tags = [part for part in re.split(r"\s*\n\s*|(?<=\])\s+(?=\[)", (text or "").strip().lower()) if part]
    if not tags or tags == [BARE]:
        return BARE
    lines, timed, clock = [], None, 0
    for tag in tags:
        match = _TAG.match(tag)
        if not match or match.group(1) not in SECTIONS:
            raise ValueError(f"{tag!r} is not a section. Use {', '.join(SECTIONS)}.")
        has_time = match.group(2) is not None
        if timed is None:
            timed = has_time
        elif timed != has_time:
            raise ValueError("give every section a time, or none of them")
        if has_time:
            start = int(match.group(2)) * 60 + int(match.group(3))
            end = int(match.group(4)) * 60 + int(match.group(5))
            if end <= start or start != clock:
                raise ValueError(f"{tag} does not follow on from the section before it")
            clock = end
            lines.append(f"[{match.group(1)} {match.group(2)}:{match.group(3)}-{match.group(4)}:{match.group(5)}]")
        else:
            lines.append(f"[{match.group(1)}]")
    if len(lines) > 40:
        raise ValueError("a structure can have 40 sections at most")
    return "\n".join(lines)


def seconds(structure: str) -> int | None:
    """The total length of a timed structure, or None when it has no times."""
    ends = re.findall(r"-(\d{1,2}):(\d{2})\]", structure or "")
    return int(ends[-1][0]) * 60 + int(ends[-1][1]) if ends else None


def with_lora(graph: dict, loader: str, lora: str, text_nodes: tuple[str, ...], strength: float = 1.0) -> dict:
    """Put the LoRA between the checkpoint and the YuE2 text nodes.  The model side
    is left alone (strength 0), so the audio sampler is unchanged."""
    graph["20"] = {"class_type": "LoraLoader", "inputs": {
        "model": [loader, 0], "clip": [loader, 1], "lora_name": lora,
        "strength_model": 0.0, "strength_clip": strength}}
    for node in text_nodes:
        graph[node]["inputs"]["clip"] = ["20", 1]
    return graph


def sings(abc: str | None) -> int:
    """How many notes the plan puts in the Vocal voice.

    The instrumental LoRA writes that voice as rests carrying the chords and puts
    the melody in Ins. When it slips and writes an actual melody there, the
    render sings — every time, in everything measured: two plans with notes in
    that voice sang through two thirds of themselves, and fifteen with rests
    alone came out clean. The plan exists before the render, so this is known
    before any of it is generated.
    """
    voice, notes = None, 0
    for raw in (abc or "").split("\n"):
        line = raw.strip()
        if line.startswith("V:"):
            voice = line[2:].strip().split()[0] if line[2:].strip() else None
            continue
        if not line or line[0] == "%" or re.match(r"^[A-Za-z]:", line):
            continue
        if voice != "Vocal":
            continue
        notes += len(re.findall(r"[A-Ga-g]", re.sub(r'"[^"]*"', "", line)))
    return notes


# A transcribed score names its sections in "% name" lines.  The transcriber uses the
# LoRA's six and two more: an interlude, which plays the part a bridge does, and a
# silence, which opens or closes the piece, or else stands between two sections.
_SCORE_SECTION = re.compile(r"^%[ \t]*([A-Za-z][\w -]*?)[ \t]*$", re.M)
_AS_SECTION = {"interlude": "bridge", "prechorus": "pre-chorus", "pre chorus": "pre-chorus",
               "solo": "bridge", "break": "bridge", "breakdown": "bridge", "coda": "outro", "ending": "outro"}


def structure_of(abc: str | None) -> str:
    """The structure an instrumental of this score is rendered with: one tag per section
    of the score, in the names the LoRA knows.  A render pairs the tags with the score's
    sections, so a tag short and it stops a section early."""
    names = [name.strip().lower() for name in _SCORE_SECTION.findall(abc or "")]
    tags = []
    for index, name in enumerate(names):
        if name in SECTIONS:
            tags.append(name)
        elif name == "silence":
            tags.append("intro" if index == 0 else "outro" if index == len(names) - 1 else "bridge")
        else:
            tags.append(_AS_SECTION.get(name, "verse"))
    return "\n".join(f"[{tag}]" for tag in tags) or BARE


_TAG_NAME = re.compile(r"\[([a-z-]+)")


def structure_following(lyrics: str | None, abc: str | None) -> str | None:
    """The structure for a planned instrumental whose score has had its sections changed,
    or None when the tags already match the score's sections (a timed structure keeps its
    times) or are the bare '[instrumental]', which the planner's own sections suit."""
    tags = _TAG_NAME.findall(lyrics or "")
    if not tags or tags == ["instrumental"]:
        return None
    wanted = structure_of(abc)
    return None if _TAG_NAME.findall(wanted) == tags else wanted


# ------------------------------------------------ the tune played by an instrument
# A recording with a voice transcribes with the sung melody in the Vocal voice, and
# a render of that sings.  Emptying the voice is not enough: where the Ins voice rests
# too, the LoRA fills the gap with humming (measured: 14% of a take).  So the tune
# moves to Ins wherever Ins rests, and the Vocal voice keeps its chords over rests,
# one rest per chord as the LoRA writes its own plans (measured: no voice at all).
_NOTE = re.compile(r"(?:\^{1,2}|_{1,2}|=)?[A-Ga-g][,']*(\d*/?\d*)")
_RESTS = re.compile(r"(?:z\d*(?:/\d*)?)+")
_REST = re.compile(r"z(\d*)(/(\d*))?")
_QUOTED = re.compile(r'("[^"]*")')


def _has_notes(bar: str) -> bool:
    return bool(re.search(r"[A-Ga-g]", _QUOTED.sub("", bar)))


def _one_rest(run: re.Match) -> str:
    total = Fraction(0)
    for rest in _REST.finditer(run.group(0)):
        count = int(rest.group(1) or 1)
        total += Fraction(count, int(rest.group(3) or 2)) if rest.group(2) else Fraction(count)
    return "z" + (str(total.numerator) if total.denominator == 1 else f"{total.numerator}/{total.denominator}")


def _as_rests(bar: str) -> str:
    """The bar's notes as rests of the same length, its chords kept, a run of rests
    as one."""
    parts = _QUOTED.split(bar)
    return "".join(part if part.startswith('"') else
                   _RESTS.sub(_one_rest, _NOTE.sub(lambda m: "z" + m.group(1), part).replace("-", ""))
                   for part in parts)


def _tokens(lines: list[str]) -> list[tuple[str, str]]:
    """A voice's lines as bars and the field lines between them (M: and the like).
    Z4 is four bars of rest, so it counts as four."""
    out: list[tuple[str, str]] = []
    for line in lines:
        text = line.strip()
        if not text or re.match(r"^[A-Za-z]:", text):
            out.append(("field", line))
            continue
        for bar in text.split("|"):
            if not bar.strip():
                continue
            many = re.fullmatch(r"\s*Z(\d*)\s*", bar)
            out += [("bar", "Z")] * int(many.group(1) or 1) if many else [("bar", bar)]
    return out


def _lines(tokens: list[tuple[str, str]]) -> list[str]:
    out, bars = [], []
    for kind, text in tokens:
        if kind == "field":
            if bars:
                out.append("|".join(bars) + "|")
                bars = []
            out.append(text)
            continue
        bars.append(text)
        if len(bars) == 4:
            out.append("|".join(bars) + "|")
            bars = []
    if bars:
        out.append("|".join(bars) + "|")
    return out


def tune_on_instrument(abc: str) -> str:
    """The score with its sung melody played by an instrument.  The transcriber writes
    a stretch of music as a Vocal block and then an Ins block of the same bars; in each
    bar where Ins rests and Vocal has notes, the notes move to Ins, chords left behind.
    Where Ins already plays, the sung notes give way.  Every Vocal bar ends as rests
    under its chords, so the score keeps its length, its chords and its sections."""
    lines = (abc or "").split("\n")
    body = next((i + 1 for i, line in enumerate(lines) if line.startswith("K:")), None)
    if body is None:
        return abc
    out = lines[:body]
    blocks: list = []           # a field or section line, or [voice, its V: line, its lines]
    for line in lines[body:]:
        if line.startswith("V:"):
            name = line[2:].strip().split()
            blocks.append([name[0] if name else "", line, []])
        elif line.startswith("%") or not blocks or not isinstance(blocks[-1], list):
            blocks.append(line)
        else:
            blocks[-1][2].append(line)
    index = 0
    while index < len(blocks):
        block = blocks[index]
        if not isinstance(block, list):
            out.append(block)
            index += 1
            continue
        tokens = _tokens(block[2])
        after = blocks[index + 1] if index + 1 < len(blocks) else None
        if block[0] == "Vocal" and isinstance(after, list) and after[0] == "Ins":
            played = _tokens(after[2])
            sung = [i for i, token in enumerate(tokens) if token[0] == "bar"]
            ins = [i for i, token in enumerate(played) if token[0] == "bar"]
            if len(sung) == len(ins):
                for s, i in zip(sung, ins):
                    if _has_notes(tokens[s][1]) and not _has_notes(played[i][1]):
                        played[i] = ("bar", _QUOTED.sub("", tokens[s][1]))
            tokens = [(kind, _as_rests(text) if kind == "bar" else text) for kind, text in tokens]
            out += [block[1], *_lines(tokens), after[1], *_lines(played)]
            index += 2
            continue
        if block[0] == "Vocal":
            tokens = [(kind, _as_rests(text) if kind == "bar" else text) for kind, text in tokens]
        out += [block[1], *_lines(tokens)]
        index += 1
    return "\n".join(out)


def duration_of(src: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
        check=True, capture_output=True, timeout=60).stdout
    try:
        return float(out.decode().strip())
    except ValueError:
        return 0.0
