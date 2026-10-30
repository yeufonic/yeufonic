"""A picture for a take: a well-worn vinyl album cover in the style of Hipgnosis.

Prompted from the song's title and style, and drawn by the external image model or local FLUX.2 klein on the engine."""
from __future__ import annotations

import base64
import io
import logging
import re
import struct
import time
import zlib
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from . import artscene, config, llm
from .db import get_setting

log = logging.getLogger("yue2.artwork")

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-image"
DEFAULT_OPENAI_MODEL = "gpt-image-1"
ASPECT = "1:1"                  # square album cover
OPENAI_SIZE = "1024x1024"       # square 1:1 album cover
WORD_LINES = 12                 # the opening of the song the description is written from
DRAW_TIMEOUT = 180.0

# FLUX.2 [klein] on this PC cannot spell, and letters what it is led to: the words "album cover", the
# design group's name, a "Song title:" label, a sign "reading" something.  So the picture drawn here is
# described as a photograph in the house style, without the name, and the scene loses any quoted words
# and signage, while an external image model, which renders lettering reliably, keeps the prompts as
# they were.  It is sampled as it was distilled to be, at cfg 1 with no negative: a weighted negative at
# cfg 3 kept the odd sign blank but burnt every picture (hard contrast, oversaturated, plastic), and
# spelling out "no text" in the prompt only put text in mind.
# What the scene is drawn as, after the scene: klein weighs the start of a prompt most, and a long fixed
# opening ("a vast and quiet real place", "generous empty space", "muted colour") drew the same bleak
# landscape under every scene.  So the scene leads, and this asks only for the craft: staged for real,
# sharp and detailed to the corners (an "old print" and "vintage film" brought a vignette and lost detail).
KLEIN_LOOK = (
    "Photographed for real, in camera, in the manner of classic British surrealist record-sleeve "
    "photography: a bold, precise composition, sharp focus and rich detail from edge to edge, clean and "
    "evenly exposed, true colour."
)
# Gemma, who writes the scene klein draws, is asked to leave people out: klein 4B draws them badly close up
# (a hand with four fingers, an arm too many), and asked only to keep them far off, Gemma put a distant
# figure in many of its scenes.  Leading with "leave people out" keeps them out; saying nothing about people
# let some back in.  klein itself is told nothing about people, since a sentence about them put a small
# figure in every picture.
PEOPLE_BRIEF = ("Leave people out: let the objects, the place and the light carry the picture. Only if the idea "
                "cannot work without a person, make them one small figure far off, seen from behind; never a "
                "close-up of hands or faces.")
KLEIN_WORN = "The print shows light ring-wear and creased corners; its colour is still strong."
KLEIN_WORDLESS = "A wordless image."
# Words that put lettering in a scene, and the words after them: "a sign reading ...", "a boat named ...".
SIGNAGE_RE = re.compile(
    r"\s*,?\s*\b(?:reading|that reads|which reads|saying|labell?ed|inscribed(?: with)?|bearing the words|"
    r"with the words|emblazoned with|spelling(?: out)?|named|called|titled|entitled)\s+"
    r"(?:[\"\u201c\u2018'][^\"\u201d\u2019']*[\"\u201d\u2019']|[A-Z][\w']*(?:\s+[A-Z][\w']*)*)",
)
QUOTED_RE = re.compile(r"[\"\u201c][^\"\u201d]*[\"\u201d]")
# Music tags that are no help to a picture, or draw the wrong one: a tempo, a key, who sings.
NOT_FOR_PICTURE_RE = re.compile(r"\d|\bbpm\b|\bkey\b|\btempo\b|vocal|voice|singer|\bmale\b|\bfemale\b|\bduet\b",
                                re.IGNORECASE)

# What the engine reports it has (set by the job lanes, which hold the engine).
engine_options = lambda: {}  # noqa: E731

# Whether the external provider has the image model asked for: (url, model, key's tail) -> (yes, when asked).
_EXTERNAL: dict[tuple, tuple[bool, float]] = {}
EXTERNAL_RECHECK = 6 * 3600

# Where a take's picture is being made: take id -> {state, error, started}.  States: queued,
# writing (the description), drawing, cutting (the background), failed.  A finished picture
# is on disk and needs no entry.
STATE: dict[str, dict[str, Any]] = {}

EXTERNAL_FAILURE_COOLDOWN = 120.0  # seconds to prefer fallback before trying external again
_EXTERNAL_DRAW_FAILED_AT: float = 0.0
_EXTERNAL_WORDS_FAILED_AT: float = 0.0


def record_external_draw_failure(reason: str = "") -> None:
    global _EXTERNAL_DRAW_FAILED_AT
    _EXTERNAL_DRAW_FAILED_AT = time.time()
    log.info("Recorded external draw failure (cooldown %.0fs): %s", EXTERNAL_FAILURE_COOLDOWN, reason)


def reset_external_draw_failure() -> None:
    global _EXTERNAL_DRAW_FAILED_AT
    _EXTERNAL_DRAW_FAILED_AT = 0.0


def external_draw_failed() -> bool:
    return bool(_EXTERNAL_DRAW_FAILED_AT and (time.time() - _EXTERNAL_DRAW_FAILED_AT < EXTERNAL_FAILURE_COOLDOWN))


def record_external_words_failure(reason: str = "") -> None:
    global _EXTERNAL_WORDS_FAILED_AT
    _EXTERNAL_WORDS_FAILED_AT = time.time()
    log.info("Recorded external words failure (cooldown %.0fs): %s", EXTERNAL_FAILURE_COOLDOWN, reason)


def reset_external_words_failure() -> None:
    global _EXTERNAL_WORDS_FAILED_AT
    _EXTERNAL_WORDS_FAILED_AT = 0.0


def clear_failures() -> None:
    reset_external_draw_failure()
    reset_external_words_failure()


def external_words_failed() -> bool:
    return bool(_EXTERNAL_WORDS_FAILED_AT and (time.time() - _EXTERNAL_WORDS_FAILED_AT < EXTERNAL_FAILURE_COOLDOWN))


def art_dir() -> Path:
    return config.DATA_DIR / "art"


def png_path(take_id: str) -> Path:
    return art_dir() / f"{take_id}.png"


def drawn_path(take_id: str) -> Path:
    """The picture as the image model drew it, before the background came out (kept while it is tried)."""
    return art_dir() / f"{take_id}-drawn.png"


def words_path(take_id: str) -> Path:
    return art_dir() / f"{take_id}.txt"


def plain_path(take_id: str) -> Path:
    """Its mark that the take was put back to the default background: no picture is shown or made for it."""
    return art_dir() / f"{take_id}.plain"


def info(take_id: str) -> dict[str, Any]:
    png, words = png_path(take_id), words_path(take_id)
    held = STATE.get(take_id) or {}
    return {
        "state": held.get("state") or ("ready" if png.exists() else "none"),
        "error": held.get("error"),
        "has": png.exists(),
        "plain": plain_path(take_id).exists(),
        "has_drawn": drawn_path(take_id).exists(),
        "v": int(png.stat().st_mtime) if png.exists() else None,
        "words": words.read_text(encoding="utf-8") if words.exists() else None,
    }


def url_for(take_id: str, parent_id: str | None = None) -> str | None:
    """Where the page finds the picture shown for a take: its own, or the one of the take it is inside."""
    if plain_path(take_id).exists():
        return None
    for owner in (take_id, parent_id):
        if owner:
            png = png_path(owner)
            if png.exists():
                return f"/api/takes/{owner}/art.png?v={int(png.stat().st_mtime)}"
    return None


def busy(take_id: str) -> bool:
    return (STATE.get(take_id) or {}).get("state") in ("queued", "writing", "drawing", "cutting")


def forget(take_id: str) -> None:
    """A deleted take's picture goes with it."""
    STATE.pop(take_id, None)
    for path in (png_path(take_id), drawn_path(take_id), words_path(take_id), plain_path(take_id)):
        path.unlink(missing_ok=True)


def to_default(take_id: str) -> None:
    """Back to the default background: the picture goes, and stays gone (the take inside another shows none either)."""
    forget(take_id)
    art_dir().mkdir(parents=True, exist_ok=True)
    plain_path(take_id).touch()


# ------------------------------------------------------------------ who does what
def gemma_ready() -> bool:
    """Gemma is on the engine (the Lyric drafts install option), with the node that runs it."""
    return bool((engine_options() or {}).get("lyrics"))


def describer() -> str:
    """Who writes the picture's description: "take" (made from the take itself, no LLM: quick, the default,
    whoever draws), "gemma" (Gemma on the engine) or "external" (the external LLM).  The external LLM chosen but
    not there (not set up, local for this session, or failed in the last two minutes) falls back to Gemma where
    it is installed: the take's own description is only its title and style tags, and FLUX.2 klein given that
    alone draws much the same landscape every time.  Gemma chosen but not there falls back to the take; so does
    anything else on file ("auto" and "same", earlier names for a choice that followed the drawer)."""
    chosen = (get_setting("art.words", "take") or "take").strip().lower()
    if chosen == "local":
        return "gemma" if gemma_ready() else "take"
    if chosen == "external":
        if llm.is_external_enabled() and not external_words_failed():
            return "external"
        return "gemma" if gemma_ready() else "take"
    return "take"


def words_by_engine() -> bool:
    """Whether the description needs the engine (Gemma)."""
    return describer() == "gemma"


COMMON_TERMS = {
    "a", "an", "and", "or", "in", "on", "at", "to", "for", "with", "by", "from", "of", "is", "it",
    "pop", "rock", "folk", "jazz", "soul", "blues", "punk", "disco", "metal", "country", "rap",
    "r&b", "ambient", "indie", "electronic", "dance", "classical", "acoustic", "electric", "vocal",
    "vocals", "male", "female", "slow", "fast", "song", "music", "style", "track", "sound", "band",
    "artist", "album", "cover", "voice", "lead", "guitar", "bass", "drums", "piano", "synth", "strings",
    "tempo", "key", "bpm", "major", "minor", "groove", "beat", "harmonies", "harmony", "rhythm",
}


def song_title(title: str) -> str:
    """The song's own title: a take made from another carries what was done after a dot ("· sung again")."""
    return (title or "").split(" \u00b7 ")[0].strip() or "Untitled"


def take_triggers(take: dict | None = None) -> set[str]:
    """All known corpus/identity trigger words and artist names that should be kept out of image prompts."""
    triggers: set[str] = set()

    # 1. Triggers and names from all registered identities/corpora in the database
    try:
        from . import db
        for r in db.rows("SELECT name, trigger_word FROM identities"):
            if r.get("trigger_word"):
                w = r["trigger_word"].strip()
                if w:
                    triggers.add(w)
            if r.get("name"):
                n = r["name"].strip()
                if n:
                    triggers.add(n)
    except Exception:
        pass

    # 2. Triggers and titles from installed LoRAs on disk
    try:
        from . import loras
        folder = loras.folder()
        if folder and folder.is_dir():
            for txt_file in folder.glob("*.txt"):
                try:
                    note = loras.note_for(txt_file.with_suffix(".safetensors"))
                    if note.get("trigger"):
                        w = note["trigger"].strip()
                        if w:
                            triggers.add(w)
                    if note.get("title"):
                        t = note["title"].strip()
                        if t:
                            triggers.add(t)
                except Exception:
                    pass
    except Exception:
        pass

    # 3. From the given take specifically
    if take:
        for key in ("style_lora", "voice_lora"):
            val = take.get(key)
            if val and isinstance(val, str):
                stem = val.removesuffix(".safetensors").strip()
                if stem:
                    triggers.add(stem)
        for key in ("identity_id", "persona_id"):
            val = take.get(key)
            if val and isinstance(val, str):
                try:
                    from . import db
                    row = db.one("SELECT name, trigger_word FROM identities WHERE id = ?", (val,))
                    if row:
                        if row.get("trigger_word"):
                            triggers.add(row["trigger_word"].strip())
                        if row.get("name"):
                            triggers.add(row["name"].strip())
                except Exception:
                    pass
        if take.get("lora_trigger"):
            triggers.add(str(take["lora_trigger"]).strip())

    return {t for t in triggers if len(t) >= 2 and t.lower() not in COMMON_TERMS}


def clean_cover_style(style: str, take: dict | None = None) -> str:
    """Strip known corpus trigger words and artist names from the style description."""
    if not style:
        return ""
    triggers = take_triggers(take)
    if not triggers:
        return style.strip()

    lower_triggers = {t.lower() for t in triggers}
    tags = [t.strip() for t in style.split(",") if t.strip()]
    filtered_tags = []

    for tag in tags:
        if tag.lower() in lower_triggers:
            continue
        cleaned_tag = tag
        for trig in sorted(triggers, key=len, reverse=True):
            cleaned_tag = re.sub(rf"\b{re.escape(trig)}\b", "", cleaned_tag, flags=re.IGNORECASE).strip()
        cleaned_tag = re.sub(r"\(\s*\)|\[\s*\]", "", cleaned_tag).strip()
        cleaned_tag = re.sub(r"\s+", " ", cleaned_tag).strip(" -:–—")
        if cleaned_tag and cleaned_tag.lower() not in lower_triggers:
            filtered_tags.append(cleaned_tag)

    result = ", ".join(filtered_tags)
    result = re.sub(r"\s*,\s*", ", ", result)
    result = re.sub(r",(\s*,)+", ", ", result)
    return result.strip(" ,")


def clean_cover_title(take: dict) -> str:
    """The song's title for the cover, with corpus trigger words and artist names stripped out."""
    title = song_title(take.get("title") or "")
    if not title or title.lower() == "untitled":
        return ""
    triggers = take_triggers(take)
    if not triggers:
        return title

    lower_triggers = {t.lower() for t in triggers}
    if title.lower() in lower_triggers:
        return ""

    cleaned = title
    for trig in sorted(triggers, key=len, reverse=True):
        cleaned = re.sub(rf"^{re.escape(trig)}\s*[-:–—]\s*", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(rf"\b{re.escape(trig)}\b", "", cleaned, flags=re.IGNORECASE).strip()

    cleaned = re.sub(r"\(\s*\)|\[\s*\]", "", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:–—")
    if not cleaned or cleaned.lower() == "untitled" or cleaned.lower() in lower_triggers:
        return ""
    return cleaned


def clean_prompt_text(text: str, take: dict | None = None) -> str:
    """Strip known corpus trigger words and artist names from prompt or description prose."""
    if not text:
        return ""
    triggers = take_triggers(take)
    if not triggers:
        return text
    cleaned = text
    for trig in sorted(triggers, key=len, reverse=True):
        cleaned = re.sub(rf"\b{re.escape(trig)}\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(\s*\)|\[\s*\]", "", cleaned)
    cleaned = re.sub(r"  +", " ", cleaned)
    cleaned = re.sub(r",\s*,+", ", ", cleaned)
    return cleaned.strip()


HIPGNOSIS_PREFIX_RE = re.compile(
    r"^Create an image in the shape of (?:a well[- ]worn |an )?album cover in the style of Hipgnosis "
    r"\(the UK art design group\) that uses the following as its inspiration.*?:",
    re.IGNORECASE | re.DOTALL
)


def is_well_worn(take: dict | None = None) -> bool:
    """Around 30% of covers are given vintage well-worn sleeve textures; the rest stay pristine."""
    if take and isinstance(take.get("seed"), (int, float)):
        try:
            return (int(take["seed"]) % 10) < 3
        except (ValueError, TypeError):
            pass
    import random
    return random.random() < 0.30


def album_cover_prefix(well_worn: bool = False) -> str:
    qualifier = "a well worn " if well_worn else "an "
    return (
        f"Create an image in the shape of {qualifier}album cover in the style of Hipgnosis "
        "(the UK art design group) that uses the following as its inspiration. "
        "Do not use the name Hipgnosis in the image; "
        "the image should only be influenced by that design group, not made to look like it was created by them:"
    )


def take_description(take: dict, scene: str | None = None, well_worn: bool | None = None) -> str:
    """An album cover prompt in the style of Hipgnosis, built from the song's title, style and a visual scene.
    With no scene given (nothing wrote one), the scene is made from the take itself (`artscene`): a title and
    style tags alone gave klein nothing to draw but a landscape."""
    title = clean_cover_title(take)
    style = clean_cover_style(take.get("style") or "", take) or config.DEFAULT_STYLE
    if scene is None:
        scene = artscene.take_scene(title, style, take.get("lyrics") or "")
    worn = is_well_worn(take) if well_worn is None else well_worn
    parts = [
        f"{album_cover_prefix(worn)}\n"
    ]
    if title:
        parts.append(f"Song title: {title}\n")
    parts.append(f'cover style:\n"{style}"')
    if scene:
        clean_scene = clean_prompt_text(scene.strip(), take)
        clean_scene = re.sub(r",?\s*(?:designed by|created by|in the style of|by)?\s*(?:hipgnosis|hignosis)\b", "", clean_scene, flags=re.IGNORECASE)
        clean_scene = re.sub(r"  +", " ", clean_scene).strip()
        if clean_scene:
            parts.append(f'\nvisual scene:\n"{clean_scene}"')
    return "\n".join(parts)


def image_model() -> str:
    chosen = (get_setting("art.model", "") or "").strip()
    if chosen:
        return chosen
    return DEFAULT_GEMINI_MODEL if _is_gemini(llm.get_config()["api_url"]) else DEFAULT_OPENAI_MODEL


def klein_size() -> str | None:
    """Which FLUX.2 klein draws here: "4b" (the default) or "9b", as Settings ask where that one is installed,
    else the other; "auto" takes the 9B where its files are there.  The 4B is the default, so the 9B draws
    only once it is chosen, even where its files are in place.  None when the engine has not said."""
    have = (engine_options() or {}).get("klein") or {}
    chosen = (get_setting("art.klein", "4b") or "4b").strip().lower()
    if chosen in have:
        return chosen
    return next((size for size in ("9b", "4b") if size in have), None)


def klein_files() -> tuple[str, str]:
    """The klein model and text encoder the picture is drawn with."""
    size = klein_size()
    if size:
        model, encoder = (engine_options() or {})["klein"][size]
        return model, encoder
    return config.PICTURE_MODEL, config.PICTURE_TEXT


def klein_name() -> str:
    size = klein_size()
    return f"FLUX.2 klein {size.upper()}" if size else "FLUX.2 klein"


def local_ready() -> bool:
    """FLUX.2 klein is on the engine (chosen at install), with the nodes to run it."""
    return bool((engine_options() or {}).get("pictures"))


def _external_key() -> tuple:
    cfg = llm.get_config()
    return (cfg.get("api_url") or "", image_model(), (cfg.get("api_key") or "")[-6:])


def external_ready() -> bool:
    """The external provider is set up, with a key, and lists the image model asked for (checked now and then,
    in the background: until it has been, it counts as not there)."""
    if llm.is_session_local_only():
        return False
    cfg = llm.get_config()
    if not (cfg.get("api_key") or "").strip() or not (cfg.get("api_url") or "").strip():
        return False
    held = _EXTERNAL.get(_external_key())
    return bool(held and held[0])


async def check_external(force: bool = False) -> bool:
    """Ask the provider's model list whether it has the image model; remembered for some hours."""
    cfg = llm.get_config()
    key = _external_key()
    held = _EXTERNAL.get(key)
    if held and not force and time.time() - held[1] < EXTERNAL_RECHECK:
        return held[0]
    if not (cfg.get("api_key") or "").strip() or not (cfg.get("api_url") or "").strip():
        _EXTERNAL[key] = (False, time.time())
        return False
    model = image_model()
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            if _is_gemini(cfg["api_url"]):
                resp = await client.get("https://generativelanguage.googleapis.com/v1beta/models",
                                        params={"pageSize": 1000}, headers={"x-goog-api-key": cfg["api_key"]})
                names = [m.get("name", "").split("/")[-1] for m in resp.json().get("models", [])] if resp.status_code == 200 else []
            else:
                url = cfg["api_url"].strip().rstrip("/")
                url = url[: -len("/chat/completions")] if url.endswith("/chat/completions") else url
                resp = await client.get(url + "/models", headers={"Authorization": f"Bearer {cfg['api_key']}"})
                names = [m.get("id", "") for m in (resp.json().get("data") or [])] if resp.status_code == 200 else []
        found = model in names
    except Exception as exc:  # noqa: BLE001
        log.info("could not ask the provider for its image models: %s", exc)
        held = _EXTERNAL.get(key)
        return bool(held and held[0])
    if (not held) or held[0] != found:
        log.info("The external provider %s the image model %s", "has" if found else "does not list", model)
    _EXTERNAL[key] = (found, time.time())
    return found


def drawer() -> str | None:
    """Who draws: "local" (FLUX.2 klein on the engine), "external" (the provider's image model), or None when
    neither is there.  Settings can ask for one; left to choose, this PC is preferred, as it costs nothing.
    If external drawing fails or is not ready, falls back to local FLUX.2 klein if available."""
    chosen = (get_setting("art.drawer", "auto") or "auto").strip().lower()
    if chosen in ("local", "auto") and local_ready():
        return "local"
    if chosen in ("external", "auto"):
        if external_draw_failed() and local_ready():
            return "local"
        if external_ready():
            return "external"
        if chosen == "external" and local_ready():
            return "local"
    return None


def words_passed_over() -> str | None:
    """Why the external LLM, chosen in Settings to describe pictures, is not asked this time; None when it is
    asked or was not chosen."""
    if (get_setting("art.words", "take") or "take").strip().lower() != "external":
        return None
    if llm.is_session_local_only():
        return "the external LLM is paused for this session (Resume in Settings)"
    if not llm.is_external_enabled():
        return "the external LLM is not set up"
    if external_words_failed():
        return (f"it failed {time.time() - _EXTERNAL_WORDS_FAILED_AT:.0f} s ago and is not asked again for "
                f"{EXTERNAL_FAILURE_COOLDOWN:.0f} s")
    return None


def drawing_passed_over() -> str | None:
    """Why the image model, chosen in Settings to draw, is not asked this time; None when it is asked or was not
    chosen."""
    if (get_setting("art.drawer", "auto") or "auto").strip().lower() != "external":
        return None
    if external_draw_failed():
        return (f"it failed {time.time() - _EXTERNAL_DRAW_FAILED_AT:.0f} s ago and is not asked again for "
                f"{EXTERNAL_FAILURE_COOLDOWN:.0f} s")
    if llm.is_session_local_only():
        return "the external LLM is paused for this session (Resume in Settings)"
    if not external_ready():
        return f"the provider is not set up, or does not list {image_model()}"
    return None


def possible() -> bool:
    """Pictures can be made here at all: what the Settings for them need."""
    return local_ready() or external_ready()


def automatic() -> bool:
    """Each new take gets a picture by itself: Settings say so (on unless turned off), and something can draw it."""
    if (get_setting("art.auto", "on") or "on").strip().lower() == "off":
        return False
    return drawer() is not None


def drawing_problem() -> str | None:
    """Why a picture cannot be drawn now, in words, or None."""
    if drawer() is None:
        return ("nothing here can draw a picture: FLUX.2 klein was not installed, and the external LLM has no image "
                "model (or it is not set up)")
    return None


def _is_gemini(url: str) -> bool:
    return "generativelanguage.googleapis.com" in (url or "")


# ------------------------------------------------------------------ the description
def opening_words(lyrics: str, limit: int = WORD_LINES) -> list[str]:
    """The song's first lines as sung: no section headings, no cue lines, no blank lines."""
    out = []
    for line in (lyrics or "").splitlines():
        line = line.strip()
        if not line or re.fullmatch(r"\[[^\]]*\]", line) or line.startswith("%"):
            continue
        out.append(line)
        if len(out) >= limit:
            break
    return out


def without_title(text: str, title: str) -> str:
    """The text without the song's title, wherever it appears in it, as whole words in any case."""
    if not text or not title:
        return text
    pattern = re.compile(r"(?<!\w)" + re.escape(title) + r"(?!\w)", re.IGNORECASE)
    return re.sub(r"  +", " ", pattern.sub("", text)).strip(" ,.;:-")


EXTERNAL_BRIEF = (
    "Describe a surreal, enigmatic photographic or painterly scene in the distinctive Hipgnosis style: "
    "striking visual metaphors, unexpected juxtaposition, dramatic landscapes, and vintage film textures"
)
KLEIN_BRIEF = (
    "Describe one surreal, enigmatic scene in the distinctive Hipgnosis style, staged and photographed for "
    "real: ordinary things in an impossible situation, a visual pun on the song. Choose the setting to suit "
    "the song, not a bare landscape by default: a room, a studio, a swimming pool, a beach, a city street, a "
    "factory, a motorway, a forest, the sky. Choose the light and colour to suit it too, bright and saturated "
    "as readily as dark or cold. Name concrete details: materials, colours, textures, what is near and what "
    "is far"
)


def description_request(take: dict, well_worn: bool | None = None, with_title: bool = True,
                        for_klein: bool = False) -> str:
    """The scene brief for the description model.

    With with_title false the title is left out of the brief, and out of the words and the style as
    well: a model given it works it into the scene ("a telephone box reading ..."), and klein then
    letters it on the sleeve — the one text it went on drawing.  With for_klein (Gemma's brief) the
    scene is asked for in what klein can draw from: a setting and light chosen for the song rather than
    a landscape every time, concrete details, and people left out (PEOPLE_BRIEF).
    """
    raw_title = clean_cover_title(take)
    title = raw_title if with_title else ""
    style = clean_cover_style(take.get("style") or "", take)
    words = opening_words(take.get("lyrics") or "")
    if not with_title:
        style = without_title(style, raw_title)
        words = [without_title(word, raw_title) for word in words]
        words = [word for word in words if word]
    sung = "\n".join(words) if words else "(an instrumental: no words)"
    title_line = f"Song title: {title}\n" if title else ""
    worn = is_well_worn(take) if well_worn is None else well_worn
    worn_intro = "a well-worn " if worn else "an "
    # klein is given the wear in its own words (KLEIN_WORN), so Gemma's scene need not carry it.
    worn_texture = " with well-worn album sleeve ring-wear and creased edges" if worn and not for_klein else ""
    return (
        "You are an art director in the style of Hipgnosis (the UK art design group). "
        f"Write one scene description for {worn_intro}album cover inspired by this song.\n\n"
        f"{title_line}"
        f"Style: {style or 'not given'}\n"
        f"The opening of the song:\n{sung}\n\n"
        f"{KLEIN_BRIEF if for_klein else EXTERNAL_BRIEF}"
        f"{worn_texture}. Do not use the name Hipgnosis in the image or description; "
        "the image should only be influenced by that design group, not made to look like it was created by them. "
        "Do not specify or add a year or decade unless one is explicitly stated in the style above. "
        f"{PEOPLE_BRIEF + ' ' if for_klein else ''}"
        "Between 40 and 90 words. Reply with the description only."
    )


def tidy_description(reply: str) -> str:
    text = (reply or "").strip()
    text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text)
    text = re.sub(r"^(here is|here's)[^:\n]*:\s*", "", text, flags=re.I)
    text = re.sub(r"^(prompt|image prompt)\s*:\s*", "", text, flags=re.I)
    text = re.sub(r"^(?:in the style of )?(?:hipgnosis|hignosis)\s*[:\-]\s*", "", text, flags=re.I)
    return text.strip().strip('"').strip()


async def describe_external(take: dict, well_worn: bool | None = None) -> str:
    reply = await llm.chat_complete([{"role": "user", "content": description_request(take, well_worn=well_worn)}],
                                    temperature=0.9, max_tokens=2048, timeout=120)
    return tidy_description(reply)


def describe_graph(take: dict, seed: int, with_title: bool = True) -> dict:
    """Gemma on the engine writes the description, through the same nodes as the lyrics.

    The title is in the brief, as it always was.  It is the *drawing* that leaves the title out when
    the picture is drawn here: klein letters a title it is given, and klein_request strips it.
    """
    return {
        "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": config.LYRICS_MODEL, "type": "stable_diffusion"}},
        "2": {"class_type": "TextGenerate", "inputs": {
            "clip": ["1", 0], "prompt": description_request(take, with_title=with_title, for_klein=True),
            "max_length": 400, "thinking": False,
            "sampling_mode": "on", "sampling_mode.temperature": 0.9, "sampling_mode.top_k": 64,
            "sampling_mode.top_p": 0.95, "sampling_mode.min_p": 0.05, "sampling_mode.repetition_penalty": 1.05,
            "sampling_mode.seed": int(seed)}},
        "3": {"class_type": "PreviewAny", "inputs": {"source": ["2", 0]}},
    }


def drawing_request(description: str, take: dict | None = None, well_worn: bool | None = None) -> str:
    """The prompt for an external image model, which renders lettering reliably: an album cover in
    the style of Hipgnosis, named, with the scene inside it."""
    text = clean_prompt_text(description.strip(), take)
    if HIPGNOSIS_PREFIX_RE.match(text):
        return text
    if take:
        return take_description(take, scene=text, well_worn=well_worn)
    worn = is_well_worn(take) if well_worn is None else well_worn
    prefix = album_cover_prefix(worn)
    clean_text = re.sub(r",?\s*(?:designed by|created by|in the style of|by)?\s*(?:hipgnosis|hignosis)\b", "", text, flags=re.IGNORECASE)
    clean_text = re.sub(r"  +", " ", clean_text).strip()
    return f"{prefix}\n\n{clean_text or text}"


def description_parts(text: str) -> tuple[bool, str, str]:
    """An album-cover prompt (take_description's) taken apart: whether the sleeve is well worn, its
    style, and its scene.  Anything else is all scene."""
    head = HIPGNOSIS_PREFIX_RE.match(text)
    if not head:
        return False, "", text.strip()
    worn = bool(re.search(r"well[- ]worn", head.group(0), re.IGNORECASE))
    style = re.search(r'cover style:\s*"(.*?)"\s*(?:visual scene:|\Z)', text, re.DOTALL)
    scene = re.search(r'visual scene:\s*"(.*)"\s*\Z', text, re.DOTALL)
    return worn, (style.group(1).strip() if style else ""), (scene.group(1).strip() if scene else "")


def picture_mood(style: str) -> str:
    """The take's style tags that say something a picture can show: no tempo, key or voice."""
    tags = [t.strip() for t in (style or "").split(",") if t.strip()]
    return ", ".join(t for t in tags if not NOT_FOR_PICTURE_RE.search(t))


def wordless_scene(scene: str, title: str) -> str:
    """The scene without the words klein would letter: signs reading something, quoted words, and the
    title where it is used as a name ("Night Fishing floats ...", in its own capitals).  The title's words used as things
    stay ("a paper moon on a string" for Paper Moon): they are the cover's visual pun, and taking them
    out left "holding a on a string"."""
    text = SIGNAGE_RE.sub("", scene)
    text = QUOTED_RE.sub("", text)
    if title and len(title.split()) > 1:
        text = re.sub(r"(?<!\w)" + re.escape(title) + r"(?!\w)", "", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return re.sub(r"  +", " ", text).strip(" ,;:-")


def klein_request(description: str, take: dict | None = None, title: str = "") -> str:
    """The prompt for FLUX.2 [klein] on this PC, which cannot spell.

    The scene first, then the house look described rather than named (naming the design group, or
    "album cover", is what made it letter the sleeve: "HIPGNOS?" as a signature), with the take's mood
    where there is no scene to carry it.  None of take_description's labels reach it: an empty "Song title:"
    asks for a title, and "72 bpm" for numbers.  Nor do the style's tags when there is a scene: guitars,
    drums and a male vocal made it draw the band, and its people are where its drawing goes wrong (a leg
    or an arm too few or too many); the scene was made with the style in mind already.
    """
    text = clean_prompt_text(description.strip(), take)
    worn, style, scene = description_parts(text)
    scene = re.sub(r",?\s*(?:designed by|created by|in the style of|by)?\s*(?:hipgnosis|hignosis)\b", "",
                   scene, flags=re.IGNORECASE)
    title = title or clean_cover_title(take or {})
    scene = wordless_scene(scene, title)
    parts = []
    if scene:
        parts += [scene, KLEIN_LOOK]
    else:
        parts.append(KLEIN_LOOK)
        mood = picture_mood(without_title(style, title))
        if mood:
            parts.append(f"Its mood: {mood}.")
    if worn:
        parts.append(KLEIN_WORN)
    parts.append(KLEIN_WORDLESS)
    return "\n\n".join(parts)


# ------------------------------------------------------------------ the drawing
WIDTH, HEIGHT = 1024, 1024     # square 1:1 album cover
LOCAL_STEPS = 4               # klein is distilled for four


def picture_graph(description: str, seed: int, prefix: str, title: str = "") -> dict:
    """FLUX.2 klein on the engine, as ComfyUI's own workflow for it runs it: no guidance, four steps.  The 4B
    and the 9B are both distilled for that, so they share it; only the files differ."""
    model, encoder = klein_files()
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": model, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": encoder, "type": "flux2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": config.PICTURE_VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0],
                                                           "text": klein_request(description, title=title)}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": WIDTH, "height": HEIGHT, "batch_size": 1}},
        "7": {"class_type": "Flux2Scheduler", "inputs": {"steps": LOCAL_STEPS, "width": WIDTH, "height": HEIGHT}},
        "8": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}},
        "10": {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0],
                                                     "cfg": 1.0}},
        "11": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["9", 0], "guider": ["10", 0], "sampler": ["8", 0],
                                                                 "sigmas": ["7", 0], "latent_image": ["6", 0]}},
        "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
        "13": {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": prefix}},
    }


async def draw(description: str) -> bytes:
    """The external image model's picture, as the bytes of an image file."""
    cfg = llm.get_config()
    model = image_model()
    prompt = drawing_request(description)
    started = time.time()
    async with httpx.AsyncClient(timeout=DRAW_TIMEOUT) as client:
        if _is_gemini(cfg["api_url"]):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            body = {"contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": ASPECT}}}
            resp = await client.post(url, json=body, headers={"x-goog-api-key": cfg["api_key"]})
            data = _reply_json(resp, model)
            image = _gemini_image(data)
        else:
            url = cfg["api_url"].strip().rstrip("/")
            url = url[: -len("/chat/completions")] if url.endswith("/chat/completions") else url
            headers = {"Authorization": f"Bearer {cfg['api_key']}"} if cfg.get("api_key") else {}
            body = {"model": model, "prompt": prompt, "size": OPENAI_SIZE, "n": 1}
            resp = await client.post(url + "/images/generations", json=body, headers=headers)
            data = _reply_json(resp, model)
            item = (data.get("data") or [{}])[0]
            if item.get("b64_json"):
                image = base64.b64decode(item["b64_json"])
            elif item.get("url"):
                image = (await client.get(item["url"])).content
            else:
                raise RuntimeError("the image model sent no picture")
    log.info("Image model %s drew a picture in %.1fs (%d bytes)", model, time.time() - started, len(image))
    return image


def _reply_json(resp: httpx.Response, model: str) -> dict:
    if resp.status_code != 200:
        try:
            err = resp.json().get("error") or {}
            message = err.get("message") if isinstance(err, dict) else str(err)
        except ValueError:
            message = resp.text[:200]
        raise RuntimeError(f"the image model ({model}) said {resp.status_code}: {message or 'no reason given'}")
    return resp.json()


def _gemini_image(data: dict) -> bytes:
    for candidate in data.get("candidates") or []:
        for part in ((candidate.get("content") or {}).get("parts") or []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    blocked = (data.get("promptFeedback") or {}).get("blockReason")
    finish = ((data.get("candidates") or [{}])[0]).get("finishReason")
    if finish in ("IMAGE_OTHER", "IMAGE_SAFETY", "IMAGE_PROHIBITED_CONTENT", "IMAGE_RECITATION") or blocked:
        # It says no more than this.  The commonest cause met: a real band's or person's name in the description.
        raise RuntimeError(f"the image model would not draw this description ({blocked or finish}). "
                           "A real band's or person's name in it is the usual cause: make the picture again")
    raise RuntimeError("the image model sent no picture" + (f" ({finish})" if finish else ""))


# ------------------------------------------------------------------ the background
WHITE_GONE = 0.05     # this close to white (largest channel shortfall, 0..1) is background, fully clear
WHITE_NEAR = 0.16     # up to this, still background where it joins it, but only partly clear
OUTLINE = 0.85        # how far from white a drawing's outline is taken to be, for unmixing its softened edge
EDGE = 2              # pixels of the drawing's outline unmixed from the white they were softened into
MARGIN = 12           # pixels of clear space kept round the drawing when the picture is trimmed


def decode(data: bytes) -> np.ndarray:
    """An image file's pixels, height x width x 4 (RGBA)."""
    try:
        import av
        with av.open(io.BytesIO(data)) as container:
            frame = next(container.decode(video=0))
            return frame.to_ndarray(format="rgba")
    except ImportError:
        from PIL import Image
        with Image.open(io.BytesIO(data)) as im:
            return np.array(im.convert("RGBA"))


def _grow(mask: np.ndarray) -> np.ndarray:
    """The mask and its eight neighbours."""
    padded = np.pad(mask, 1)
    out = mask.copy()
    h, w = mask.shape
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            if dy == 1 and dx == 1:
                continue
            out |= padded[dy:dy + h, dx:dx + w]
    return out


def background(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The near-white that reaches the edges (as a mask), and every pixel's distance from white."""
    distance = (255.0 - rgb.astype(np.float32)).max(axis=2) / 255.0
    near = distance < WHITE_NEAR
    reached = np.zeros_like(near)
    reached[0, :], reached[-1, :], reached[:, 0], reached[:, -1] = near[0, :], near[-1, :], near[:, 0], near[:, -1]
    while True:
        before = int(reached.sum())
        for _ in range(16):
            reached = _grow(reached) & near
        if int(reached.sum()) == before:
            return reached, distance


def cut_out(data: bytes) -> bytes:
    """The picture with its white background taken out, as a PNG trimmed to the drawing."""
    rgba = decode(data)
    if (rgba[..., 3] < 250).mean() > 0.05:      # drawn transparent already (an OpenAI model can)
        return png_bytes(trim(rgba))
    bg, distance = background(rgba[..., :3])
    # White background removal is only applied if there is a dominant white margin around the artwork (>15%),
    # preserving full-bleed album covers with their aged sleeve borders and paper textures intact.
    corners_pure_white = (distance[0, 0] < 0.03 and distance[0, -1] < 0.03 and
                          distance[-1, 0] < 0.03 and distance[-1, -1] < 0.03)
    if corners_pure_white and (bg.mean() > 0.15 or (rgba[..., :3] > 250).all(axis=2).mean() > 0.3):
        alpha = np.ones(distance.shape, np.float32)
        alpha[bg] = np.clip((distance[bg] - WHITE_GONE) / (WHITE_NEAR - WHITE_GONE), 0.0, 1.0)
        band = bg.copy()
        for _ in range(EDGE):
            band = _grow(band)
        band &= ~bg
        alpha[band] = np.minimum(1.0, distance[band] / OUTLINE)
        unmix = (alpha > 0) & (bg | band)
        a = alpha[unmix][:, None]
        rgb = rgba[..., :3].astype(np.float32)
        rgb[unmix] = np.clip(255.0 - (255.0 - rgb[unmix]) / a, 0.0, 255.0)
        out = np.dstack([rgb, alpha * 255.0]).round().astype(np.uint8)
        return png_bytes(trim(out))
    return png_bytes(rgba)


def trim(rgba: np.ndarray) -> np.ndarray:
    seen = rgba[..., 3] > 8
    if not seen.any():
        return rgba
    ys, xs = np.nonzero(seen)
    top, bottom = max(0, ys.min() - MARGIN), min(rgba.shape[0], ys.max() + 1 + MARGIN)
    left, right = max(0, xs.min() - MARGIN), min(rgba.shape[1], xs.max() + 1 + MARGIN)
    return rgba[top:bottom, left:right]


def png_bytes(rgba: np.ndarray) -> bytes:
    """An RGBA PNG, written directly: the app has no imaging library, and this is all it needs."""
    h, w = rgba.shape[:2]
    rows = np.concatenate([np.zeros((h, 1), np.uint8), np.ascontiguousarray(rgba, np.uint8).reshape(h, w * 4)], axis=1)

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows.tobytes(), 6)) + chunk(b"IEND", b""))


def keep(take_id: str, description: str, drawn: bytes, picture: bytes, model: str, writer: str) -> None:
    art_dir().mkdir(parents=True, exist_ok=True)
    plain_path(take_id).unlink(missing_ok=True)
    drawn_path(take_id).write_bytes(png_bytes(decode(drawn)))
    png_path(take_id).write_bytes(picture)
    words_path(take_id).write_text(f"{description}\n\n(Described by {writer}; drawn by {model}.)\n", encoding="utf-8")
