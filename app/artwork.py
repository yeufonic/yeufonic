"""A picture for a take: an illustration of the song, with a transparent background.

Two steps.  A language model reads the take (its title, style and opening words) and writes a
description of a picture; that is the LLM the Settings name for it, the external one or Gemma on
the engine.  Then the external provider's image model draws it.  No image model asked here can
draw a transparent background (asked to, one draws a checkerboard), so it is asked for a plain
white one, and the white that reaches the picture's edges is taken out here: what is left is
the drawing, with its outline's softening kept as part-transparency.  White inside the drawing,
a clock face or a gap inside a letter, is not reached from the edges and stays."""
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

from . import config, llm
from .db import get_setting

log = logging.getLogger("yue2.artwork")

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-image"
DEFAULT_OPENAI_MODEL = "gpt-image-1"
ASPECT = "21:9"                 # a wide banner, as an album's artwork might be laid out across a page
OPENAI_SIZE = "1536x1024"       # the widest an OpenAI image model draws
WORD_LINES = 12                 # the opening of the song the description is written from
DRAW_TIMEOUT = 180.0

# Where a take's picture is being made: take id -> {state, error, started}.  States: queued,
# writing (the description), drawing, cutting (the background), failed.  A finished picture
# is on disk and needs no entry.
STATE: dict[str, dict[str, Any]] = {}


def art_dir() -> Path:
    return config.DATA_DIR / "art"


def png_path(take_id: str) -> Path:
    return art_dir() / f"{take_id}.png"


def drawn_path(take_id: str) -> Path:
    """The picture as the image model drew it, before the background came out (kept while it is tried)."""
    return art_dir() / f"{take_id}-drawn.png"


def words_path(take_id: str) -> Path:
    return art_dir() / f"{take_id}.txt"


def info(take_id: str) -> dict[str, Any]:
    png, words = png_path(take_id), words_path(take_id)
    held = STATE.get(take_id) or {}
    return {
        "state": held.get("state") or ("ready" if png.exists() else "none"),
        "error": held.get("error"),
        "has": png.exists(),
        "has_drawn": drawn_path(take_id).exists(),
        "v": int(png.stat().st_mtime) if png.exists() else None,
        "words": words.read_text(encoding="utf-8") if words.exists() else None,
    }


def busy(take_id: str) -> bool:
    return (STATE.get(take_id) or {}).get("state") in ("queued", "writing", "drawing", "cutting")


def forget(take_id: str) -> None:
    """A deleted take's picture goes with it."""
    STATE.pop(take_id, None)
    for path in (png_path(take_id), drawn_path(take_id), words_path(take_id)):
        path.unlink(missing_ok=True)


# ------------------------------------------------------------------ who does what
def words_by_engine() -> bool:
    """Whether the description is written by Gemma on the engine (else by the external LLM)."""
    chosen = (get_setting("art.words", "same") or "same").strip().lower()
    if chosen == "local":
        return True
    if chosen == "external":
        return False
    return not llm.is_external_enabled()


def image_model() -> str:
    chosen = (get_setting("art.model", "") or "").strip()
    if chosen:
        return chosen
    return DEFAULT_GEMINI_MODEL if _is_gemini(llm.get_config()["api_url"]) else DEFAULT_OPENAI_MODEL


def drawing_problem() -> str | None:
    """Why a picture cannot be drawn now, in words, or None."""
    cfg = llm.get_config()
    if not (cfg.get("api_url") or "").strip():
        return "set the external LLM's address in Settings: its image model draws the picture"
    if not (cfg.get("api_key") or "").strip() and _is_gemini(cfg["api_url"]):
        return "set the external LLM's key in Settings: its image model draws the picture"
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


def song_title(title: str) -> str:
    """The song's own title: a take made from another carries what was done after a dot ("· sung again")."""
    return (title or "").split(" \u00b7 ")[0].strip() or "Untitled"


def description_request(take: dict) -> str:
    title = song_title(take.get("title") or "")
    style = (take.get("style") or "").strip()
    words = opening_words(take.get("lyrics") or "")
    sung = "\n".join(words) if words else "(an instrumental: no words)"
    return (
        "You are an art director. Write one prompt for an image model: an illustration that captures this song, "
        "its imagery, its mood and its era.\n\n"
        f"Song title: {title}\n"
        f"Style: {style or 'not given'}\n"
        f"The opening of the song:\n{sung}\n\n"
        "The illustration is a wide banner, about twice as wide as it is tall. Hand-lettered words are part of it: "
        "the title, perhaps a short phrase from the song, and the style written small along a curve, exactly as "
        "given but with any name of a real band, artist or person left out. Say what is in the picture, how it is "
        "laid out, its colours and its kind of drawing. Never name a real band, artist or person anywhere in the "
        "prompt, not even in the lettering: an image model will not draw one, so describe the era and the look "
        "instead. Between 60 and 120 words. Reply with the prompt only."
    )


def tidy_description(reply: str) -> str:
    text = (reply or "").strip()
    text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text)
    text = re.sub(r"^(here is|here's)[^:\n]*:\s*", "", text, flags=re.I)
    text = re.sub(r"^(prompt|image prompt)\s*:\s*", "", text, flags=re.I)
    return text.strip().strip('"').strip()


async def describe_external(take: dict) -> str:
    reply = await llm.chat_complete([{"role": "user", "content": description_request(take)}],
                                    temperature=0.9, max_tokens=2048, timeout=120)
    return tidy_description(reply)


def describe_graph(take: dict, seed: int) -> dict:
    """Gemma on the engine writes the description, through the same nodes as the lyrics."""
    return {
        "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": config.LYRICS_MODEL, "type": "stable_diffusion"}},
        "2": {"class_type": "TextGenerate", "inputs": {
            "clip": ["1", 0], "prompt": description_request(take), "max_length": 400, "thinking": False,
            "sampling_mode": "on", "sampling_mode.temperature": 0.9, "sampling_mode.top_k": 64,
            "sampling_mode.top_p": 0.95, "sampling_mode.min_p": 0.05, "sampling_mode.repetition_penalty": 1.05,
            "sampling_mode.seed": int(seed)}},
        "3": {"class_type": "PreviewAny", "inputs": {"source": ["2", 0]}},
    }


def drawing_request(description: str) -> str:
    return (description.strip() + "\n\n"
            "Draw it as a cut-out: the artwork alone on a plain, flat, pure white background (#FFFFFF) that runs to "
            "every edge, with a clear white margin all round. No checkerboard pattern, no frame, no border, no drop "
            "shadow, no paper texture.")


# ------------------------------------------------------------------ the drawing
async def draw(description: str) -> bytes:
    """The image model's picture, as the bytes of an image file."""
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
            body = {"model": model, "prompt": prompt, "size": OPENAI_SIZE, "n": 1, "background": "transparent"}
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
    import av
    with av.open(io.BytesIO(data)) as container:
        frame = next(container.decode(video=0))
        return frame.to_ndarray(format="rgba")


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
    rgb = rgba[..., :3].astype(np.float32)
    bg, distance = background(rgba[..., :3])
    alpha = np.ones(distance.shape, np.float32)
    # the background: clear where it is white, fading in where it is merely near white
    alpha[bg] = np.clip((distance[bg] - WHITE_GONE) / (WHITE_NEAR - WHITE_GONE), 0.0, 1.0)
    # the drawing's outline, softened into the white: take the white back out of its colour
    band = bg.copy()
    for _ in range(EDGE):
        band = _grow(band)
    band &= ~bg
    # (an outline is dark, about this far from white: half of it blended with white is half clear)
    alpha[band] = np.minimum(1.0, distance[band] / OUTLINE)
    unmix = (alpha > 0) & (bg | band)
    a = alpha[unmix][:, None]
    rgb[unmix] = np.clip(255.0 - (255.0 - rgb[unmix]) / a, 0.0, 255.0)
    out = np.dstack([rgb, alpha * 255.0]).round().astype(np.uint8)
    return png_bytes(trim(out))


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
    drawn_path(take_id).write_bytes(png_bytes(decode(drawn)))
    png_path(take_id).write_bytes(picture)
    words_path(take_id).write_text(f"{description}\n\n(Described by {writer}; drawn by {model}.)\n", encoding="utf-8")
