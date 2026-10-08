"""Lyric drafts from a short brief, written by a language model on the engine.

The prompt asks for YuE2's own layout: a title line, then sections tagged
[Verse], [Chorus] and so on.  parse() tidies what comes back, since a model can
still add a stray note or bold a heading, and says what is missing."""
from __future__ import annotations

import re

STRUCTURES = {
    "verse-chorus-bridge": ["Verse", "Chorus", "Verse", "Chorus", "Bridge", "Chorus"],
    "verse-chorus": ["Verse", "Chorus", "Verse", "Chorus"],
    "intro-outro": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Outro"],
    "story": ["Verse", "Verse", "Chorus", "Verse", "Chorus", "Outro"],
    "pop-pre-chorus": ["Verse", "Pre-Chorus", "Chorus", "Verse", "Pre-Chorus", "Chorus", "Bridge", "Chorus"],
    "hook-first": ["Chorus", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Chorus"],
    "short": ["Verse", "Chorus", "Verse", "Chorus", "Chorus"],
    "hip-hop": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Verse", "Outro"],
    "double-bridge": ["Verse", "Chorus", "Verse", "Chorus", "Bridge", "Bridge", "Chorus", "Chorus"],
    "interlude": ["Verse", "Chorus", "Interlude", "Verse", "Chorus", "Bridge", "Chorus"],
    "full-pop": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Interlude", "Verse", "Pre-Chorus", "Chorus", "Outro"],
}
# What each shape suits, for the tooltip in the page.
HINTS = {
    "verse-chorus-bridge": "The classic song shape. Pop, rock, country and most radio songs.",
    "verse-chorus": "Short and direct. Folk, punk, country and early rock and roll.",
    "intro-outro": "Framed by an intro and an outro. Ballads, soft rock and singer-songwriter songs.",
    "story": "Two verses before the first hook. Story songs, folk, country and ballads.",
    "pop-pre-chorus": "Builds into each chorus. Modern pop, dance-pop, pop rock and K-pop.",
    "hook-first": "Opens on the hook. Streaming-era pop, indie pop and hip-hop hooks.",
    "short": "A tight, no-frills song. Punk, garage rock, rockabilly and folk.",
    "hip-hop": "Three verses with the hook between them. Rap, hip-hop, trap and R&B.",
    "double-bridge": "A long, building shape. Power ballads, progressive and symphonic rock, epic metal and musical theatre.",
    "interlude": "An instrumental break after the first chorus. Rock, pop rock and indie.",
    "full-pop": "Every part: intro, pre-choruses, an instrumental break and an outro. Pop and dance-pop.",
}
DEFAULT_STRUCTURE = "verse-chorus-bridge"
TAGS = {"verse", "chorus", "bridge", "intro", "outro", "pre-chorus", "interlude"}
# A section the planner plays as music alone: its tag stands by itself, with no lines under it.
INSTRUMENTAL = {"interlude"}
DEFAULT_LINES = 6

PROMPT = """You are a songwriter. Write original lyrics for a song.

What it is about: {brief}
The music: {style}
Structure, in this order: {structure}

Rules:
- The first line is: Title: <the song title>
- Then each section starts with its tag alone on a line, in square brackets, exactly as listed: {tags}
- Put one blank line between sections.
- Verses and choruses have {lines} lines each. A bridge, intro or outro has 2 to 4 lines.{interlude}
- Every chorus uses the same words.
- Keep lines singable: roughly 6 to 10 syllables, with rhymes at the ends of lines.
- The music description is for the sound only. Do not name instruments, genres or production in the lyrics.
- Use concrete images and plain words. Avoid cliches.
- Do not reuse lines from existing songs.
- Write in English unless the brief asks for another language.
- Output only the title and the lyrics. No notes, no explanations, no markdown."""


def plan_names(text: str) -> list[str]:
    """The section names a plan should follow, from a song's lyric tags in order: the planner writes an interlude
    where the lyrics say instrumental, and other tags (a verse number, a note) are not sections."""
    names = []
    for line in (text or "").splitlines():
        found = re.fullmatch(r"\[\s*([A-Za-z -]+?)\s*(?:\d+)?\s*\]", line.strip())
        if not found:
            continue
        name = found.group(1).strip().lower()
        name = "interlude" if name == "instrumental" else name
        if name in TAGS:
            names.append(name)
    return names


def clean_sections(sections: list[str]) -> list[str]:
    """The names a person put in the builder, as the tags the writer and the planner know; ValueError for any other."""
    out = []
    for name in sections:
        key = str(name).strip().lower()
        if key not in TAGS:
            raise ValueError(f"unknown section: {name}")
        out.append("Pre-Chorus" if key == "pre-chorus" else key.title())
    return out


def build_prompt(brief: str, style: str, structure: str, lines: int = DEFAULT_LINES,
                 sections: list[str] | None = None) -> str:
    """The writer's prompt for a structure by name, or for a list of sections the person built."""
    sections = clean_sections(sections) if sections else STRUCTURES.get(structure, STRUCTURES[DEFAULT_STRUCTURE])
    interlude = ""
    if any(name.lower() in INSTRUMENTAL for name in sections):
        interlude = ("\n- An Interlude is an instrumental passage: write its tag on a line of its own and no lines under it.")
    return PROMPT.format(brief=" ".join(brief.split()), style=" ".join(style.split()) or "any",
                         structure=", ".join(sections), lines=lines, interlude=interlude,
                         tags=" ".join(f"[{name}]" for name in dict.fromkeys(sections)))


def _tag(line: str) -> str | None:
    """'[Verse]', '**[verse 2]**' or 'Chorus:' as a section name; None for a lyric line."""
    bare = line.strip().strip("*_#").strip()
    match = re.fullmatch(r"\[([A-Za-z -]+?)(?:\s*\d+)?\]|([A-Za-z -]+?)(?:\s*\d+)?:", bare)
    if not match:
        return None
    name = (match.group(1) or match.group(2)).strip().lower()
    if name not in TAGS:
        return None
    return "Pre-Chorus" if name == "pre-chorus" else name.title()


def parse(text: str) -> dict:
    """{'title', 'lyrics', 'sections', 'problems'} from a model's reply."""
    title = None
    sections: list[tuple[str, list[str]]] = []
    for raw in (text or "").replace("\r", "").split("\n"):
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        if title is None and not sections and re.match(r"^\**\s*title\s*:", line, re.I):
            title = re.sub(r"^\**\s*title\s*:\s*", "", line, flags=re.I).strip("* \"'") or None
            continue
        tag = _tag(line)
        if tag:
            sections.append((tag, []))
        elif sections:
            sections[-1][1].append(line.strip("*_").strip())
        # Anything before the first section that is not the title is a preamble: dropped.
    # An interlude is music alone: its tag with no lines is a section, not an empty one.
    sections = [(name, lines) for name, lines in sections if lines or name.lower() in INSTRUMENTAL]
    problems = []
    if not sections:
        problems.append("no song sections")
    lyrics = "\n\n".join(f"[{name}]" + ("\n" + "\n".join(lines) if lines else "") for name, lines in sections)
    return {"title": title, "lyrics": lyrics, "sections": [name for name, _ in sections], "problems": problems}
