"""Yeufonic: a browser front end for YuE2 running in ComfyUI.

The heavy lifting happens in the engine.  This service keeps the library, drives
the engine, separates stems, and serves one page.

  config.py   environment settings
  db.py       SQLite: connections, schema, migrations, settings
  library.py  files in the data folder: names, sidecars, durations, peaks
  engine.py   the ComfyUI client
  jobs.py     the GPU and stem job lanes
  main.py     this file: the HTTP API
"""
from __future__ import annotations

import asyncio
import collections
import contextlib
import hashlib
import httpx
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.background import BackgroundTask
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import aligner, config, identities, instrumental, jobs, library, llm, logging_setup, loras, lyrics, mcp, midi, score, soundfonts, stems, storage, system_stats, trainsize, transpose, update
from .db import DEFAULT_SPACE, delete_setting, execute, get_setting, migrate, one, rows, set_setting

personas = identities
from .engine import stage_label
from .jobs import (CURRENT, CURRENT_STEMS, ENGINE, HARMONY_STEPS, INTERPRETATION_NAMES, INTERPRETATIONS, LYRICS,
                   PLAN_VARIETY, QUEUE, STEM_QUEUE)
from .library import (audio_duration, ensure_peaks, fill_loudness, inside, kept_beside, relayout, remove_tree,
                      slugify, source_path, take_folder, vocal_path)

logging_setup.setup_logging(config.DATA_DIR / "logs")
log = logging.getLogger("yue2")

STATIC_DIR = Path(__file__).parent / "static"
ACTIVE = ("queued", "running")
MAX_SEED = 2**64 - 1


# --------------------------------------------------------------------- settings
# Everything the Settings panel can change.  The panel renders this spec, so a
# new setting is a server-side change only.
SETTINGS_SPEC: list[dict] = [
    {
        "key": "stems.format",
        "label": "Output audio format",
        "type": "select",
        # FLAC by default: lossless like WAV at about half the size, and what takes are
        # saved as.  WAV stays for software that cannot open FLAC.
        "default": "flac",
        "options": [
            {"value": "flac", "label": "FLAC, lossless"},
            {"value": "wav", "label": "WAV, uncompressed"},
            {"value": "mp3", "label": "MP3, 320 kbps"},
        ],
        "help": "The format for saving stems or takes.",
    },
    {
        "key": "normalise.level",
        "label": "Normalise to",
        "type": "select",
        # What streaming services play at, and where a render that went well lands.
        "default": "-14",
        "options": [
            {"value": "-16", "label": "\u221216 LUFS, quieter"},
            {"value": "-14", "label": "\u221214 LUFS, the usual"},
            {"value": "-11", "label": "\u221211 LUFS, loud"},
        ],
        "help": "How loud a normalised take is made. Louder squeezes its peaks harder.",
    },
    {
        "key": "appearance.theme",
        "label": "Theme",
        "type": "select",
        "default": "dark",
        "options": [
            {"value": "dark", "label": "Dark"},
            {"value": "light", "label": "Light"},
            {"value": "system", "label": "Match the computer (dark or light)"},
            {"value": "studio", "label": "Studio (warm, dark)"},
            {"value": "contrast", "label": "High contrast"},
        ],
        "help": "How the app looks.",
    },
    {
        "key": "editor.layout",
        "label": "Editor layout",
        "type": "select",
        # Everything in view at once; steps suit someone finding their way.
        "default": "columns",
        "options": [
            {"value": "columns", "label": "Three columns, everything in view"},
            {"value": "steps", "label": "Steps, one part at a time"},
        ],
        "help": "How the window for making and changing takes is laid out.",
    },
    {
        "key": "app.update_check",
        "label": "Check for a new version",
        "type": "select",
        "default": "on",
        "options": [
            {"value": "on", "label": "Every 4 hours"},
            {"value": "off", "label": "Do not check"},
        ],
        # One small request to our own site, and nothing else: worth saying plainly in a
        # tool whose selling point is that it runs on your own machine.
        "help": "One request every four hours to yeufonic.com, to see whether a newer release is out. "
                "Nothing else leaves the computer, and Check for updates in the menu works either way.",
    },
    {
        "key": "stems.model",
        "label": "Stem separation model",
        "type": "select",
        "default": "htdemucs",
        "options": [{"value": key, "label": spec["label"]} for key, spec in stems.MODELS.items()],
        "help": "The model new runs start with.",
    },
    {
        "key": "mcp.enabled",
        "label": "MCP server",
        "type": "select",
        "default": "off",
        "options": [
            {"value": "off", "label": "Off"},
            {"value": "on", "label": "On"},
        ],
        "help": "Lets an AI agent on this computer (Claude Code, Cursor and others) make songs and read the library, at "
                "/mcp. A request can start work on the GPU, so it is off until you turn it on.",
    },
    {
        "key": "stems.folder",
        "label": "Stem save folder",
        "type": "text",
        "default": str(config.STEMS_DIR),
        "help": f"Where stems are written. It must sit inside {config.DATA_DIR}.",
    },
    {
        "key": "processing.gpu",
        "label": "Use the GPU for stems and lyrics",
        "type": "select",
        "default": "on",
        "options": [
            {"value": "on", "label": "On"},
            {"value": "off", "label": "Off"},
        ],
        "help": "Separating a vocal and hearing its words run on the engine's GPU when it has what they need, as jobs in its "
                "queue beside plans and renders. Off, or while a LoRA is training, the CPU does them: slower, and never in a "
                "render's way.",
    },
    {
        "key": "training.checkpoints",
        "section": "storage",
        "label": "Training checkpoints",
        "type": "select",
        # Kept by default: each sounds about as good as the finished LoRA but reads the
        # style its own way, so they are worth trying by ear.
        "default": "keep",
        "options": [
            {"value": "keep", "label": "Keep them"},
            {"value": "delete", "label": "Delete when training ends"},
        ],
        "help": "A training run saves a checkpoint every 50 steps, folded under its LoRA in the Style LoRA list. "
                "Each gives its own take on the style. Each is as big as the LoRA itself.",
    },
    {
        "key": "storage.working_copies",
        "section": "storage",
        "label": "Working copies of corpus songs",
        "type": "select",
        # Removed by default: nothing reads them once a song has been analysed, and a corpus makes about
        # 40 MB of them per song.
        "default": "remove",
        "options": [
            {"value": "remove", "label": "Remove when a song's analysis ends"},
            {"value": "keep", "label": "Keep them"},
        ],
        "help": "Analysing a corpus song makes copies for the engine to read: the song with its tags stripped, "
                "a padded copy for the transcriber and a short clip for its style. Nothing reads them again. "
                "If a song is analysed again they are made again.",
    },
    {
        "key": "storage.training_set",
        "section": "storage",
        "label": "Training sets",
        "type": "select",
        # Kept by default: removing one means pressing Export again before the corpus can train again.
        "default": "keep",
        "options": [
            {"value": "keep", "label": "Keep them"},
            {"value": "delete", "label": "Remove when training ends"},
        ],
        "help": "A corpus's training set is its songs written again as lossless FLAC, larger than the originals. "
                "Once a LoRA is trained it is not used again. Removed, it is written again with Export before "
                "the corpus can train again, which takes a few minutes. LoRAs already trained are not affected.",
    },
    {
        "key": "llm.provider",
        "label": "LLM for writing lyrics & style tags",
        "type": "select",
        "default": "local",
        "options": [
            {"value": "local", "label": "Local Gemma (engine ComfyUI node)"},
            {"value": "external", "label": "External LLM (OpenAI-compatible API)"},
        ],
        "help": "Choose whether to run local Gemma on GPU or connect to an external LLM (OpenAI, Anthropic, Gemini, Groq, OpenRouter, Ollama, LM Studio). Using external LLM avoids loading Gemma into GPU memory and produces significantly richer lyrics and style descriptions.",
    },
    {
        "key": "llm.api_url",
        "label": "External LLM API URL",
        "type": "text",
        "default": "https://api.openai.com/v1",
        "help": "Base URL for OpenAI-compatible completions (e.g. https://api.openai.com/v1, http://localhost:11434/v1 for Ollama, https://openrouter.ai/api/v1, or https://generativelanguage.googleapis.com/v1beta/openai/ for Gemini).",
    },
    {
        "key": "llm.api_key",
        "label": "External LLM API Key",
        "type": "password",
        "default": "",
        "help": "API authentication key (leave empty or use 'ollama' for local servers without authentication).",
    },
    {
        "key": "llm.model",
        "label": "External LLM Model",
        "type": "text",
        "default": "gpt-4o-mini",
        "help": "Model identifier to query (e.g. gpt-4o-mini, claude-3-5-sonnet-20241022, gemini-1.5-flash, llama3.2, mistral-large).",
    },
    {
        "key": "lyrics.transcriber",
        "label": "Lyrics from a recording",
        "type": "select",
        "default": "whisper",
        "options": [
            {"value": "whisper", "label": "Whisper, on this machine"},
            {"value": "llm", "label": "External LLM"},
        ],
        # Only meaningful with an external provider.  The sheet greys it out
        # otherwise, and the job ignores it, so a stale "llm" can do no harm.
        "requires": {"llm.provider": "external"},
        "requires_note": "Choose External LLM as the provider to use this.",
        "help": "The LLM must accept audio, as Gemini does. Whisper still times the lines, and is used instead if the LLM can't hear it.",
    },
    {
        "key": "midi.soundfont",
        "label": "MIDI SoundFont (.sf2)",
        "type": "select",
        "default": "Arachno_SoundFont_Version_1.0.sf2",
        "options": [
            {"value": "Arachno_SoundFont_Version_1.0.sf2", "label": "Arachno SoundFont 1.0 (148.2 MB)"},
            {"value": "Musyng_Kite.sf2", "label": "Musyng Kite (1020.6 MB)"},
            {"value": "DSoundFontV4.sf2", "label": "DSoundFont V4 (553.3 MB)"},
            {"value": "github_Jnsgm2.sf2", "label": "Jnsgm2 GM (31.7 MB)"},
        ],
        "help": "SoundFont used for high-fidelity MIDI audio rendering and audition in data/models/soundfonts/sf2.",
    },
]

SETTINGS_BY_KEY = {item["key"]: item for item in SETTINGS_SPEC}


def setting_value(key: str) -> str:
    # The stems folder follows the data folder, read now rather than when this module
    # was first imported.
    return get_setting(key, None) or setting_default(key)


def settings_payload() -> list[dict]:
    """Every setting with its value.  A key is reported only as saved or not: the
    page never needs it back, since the server uses the one on file."""
    out = []
    for spec in SETTINGS_SPEC:
        if spec["key"] == "midi.soundfont":
            sf_list = soundfonts.available_sf2()
            if sf_list:
                spec = {
                    **spec,
                    "options": [
                        {"value": sf["id"], "label": f"{sf['name']} ({sf['size_mb']} MB)"}
                        for sf in sf_list
                    ],
                }
        value = setting_value(spec["key"])
        if spec["type"] == "password":
            out.append({**spec, "value": "", "saved": bool(value)})
        else:
            out.append({**spec, "value": value})
    return out


def save_setting(key: str, value: str) -> None:
    spec = SETTINGS_BY_KEY.get(key)
    if not spec:
        raise HTTPException(400, f"unknown setting {key}")
    value = (value or "").strip()
    if spec["type"] == "select":
        allowed = [option["value"] for option in spec["options"]]
        if key == "midi.soundfont":
            sf_list = soundfonts.available_sf2()
            if sf_list:
                allowed = [sf["id"] for sf in sf_list]
        if value not in allowed:
            raise HTTPException(400, f"{key} must be one of {', '.join(allowed)}")
    if key == "stems.folder":
        if not value:
            raise HTTPException(400, "the stem folder cannot be empty")
        if not inside(Path(value), config.DATA_DIR):
            raise HTTPException(400, f"the stem folder must be inside {config.DATA_DIR}")
    # The panel saves every field, not only the one changed.  A value that is just the
    # default is not stored, so a better default reaches everyone who never chose.
    secret = spec["type"] == "password"
    if not secret and value == setting_default(key):
        delete_setting(key)
    else:
        set_setting(key, value)
    masked = "***" if any(w in key.lower() for w in ("key", "secret", "password", "token")) else value
    log.info("Setting updated: %s = %s", key, masked)


def setting_default(key: str) -> str:
    return str(config.STEMS_DIR) if key == "stems.folder" else SETTINGS_BY_KEY[key]["default"]


def forget_frozen_defaults() -> int:
    """Settings saved before only real choices were stored hold every default as it was
    then.  Those go, so today's defaults apply.  A WAV stem format is one: WAV was the
    default until FLAC, and a saved WAV cannot be told from one saved by accident."""
    gone = 0
    for spec in SETTINGS_SPEC:
        key = spec["key"]
        if spec["type"] == "password":
            continue
        stored = get_setting(key, None)
        if stored is not None and (stored == setting_default(key) or (key == "stems.format" and stored == "wav")):
            delete_setting(key)
            gone += 1
    if gone:
        log.info("Forgot %d saved settings that only repeated a default", gone)
    return gone


def guess_title(lyrics: str) -> str:
    """First real lyric line. Section and genre tags do not make a title."""
    for line in (lyrics or "").splitlines():
        text = line.strip()
        if not text or text[0] in "[#({":
            continue
        return text[:60]
    return ""


def remove_folders(folders: list[tuple[Path | None, Path]]) -> None:
    """Delete each folder that sits strictly inside its root.  The check stops a bad
    path in the database from ever taking the library with it."""
    for folder, root in folders:
        if folder and inside(folder, root) and folder.resolve() != root.resolve():
            remove_tree(folder)


# --------------------------------------------------------------------- lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    migrate()
    remove_tree(config.WORK_DIR)
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    # Songs to build a corpus from go here, so nobody has to mount a folder or know
    # a path: copy the files in, and the corpus screen offers them.
    await asyncio.to_thread(config.CORPUS_INBOX.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(sweep_engine_input)
    # A job that was running when the app stopped cannot be picked up again.  One
    # that was only waiting can, so it goes back in the queue.
    execute("UPDATE takes SET status = 'failed', error = 'interrupted by a restart' WHERE status = 'running'")
    execute("UPDATE sources SET transcribe_state = 'failed', transcribe_error = 'interrupted by a restart' WHERE transcribe_state = 'running'")
    execute("UPDATE stem_sets SET status = 'failed', error = 'interrupted by a restart' WHERE status = 'running'")
    execute("UPDATE lora_runs SET state = 'failed', error = 'interrupted by a restart', finished_at = ? WHERE state IN ('queued', 'running')", (time.time(),))
    await requeue_waiting()
    # Before relayout, which names each take's file, and before the levels are read.
    await asyncio.to_thread(library.convert_old_normalised)
    await asyncio.to_thread(relayout)
    forget_frozen_defaults()
    await asyncio.to_thread(fill_source_durations)
    if config.ENGINE_OUTPUT_DIR:
        # Renders are saved here.  Created by the app, so the app may delete the
        # engine's copy once it has its own, though the engine writes as root.
        try:
            (config.ENGINE_OUTPUT_DIR / "yeufonic").mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            log.warning("engine output folder not usable, renders stay in the engine: %s", exc)
    await ENGINE.start()
    # Identity analysis is not queued again after a restart: its states go back to
    # none, and Analyse picks up whatever is left.
    execute("""UPDATE identity_songs SET vocals_state = 'none' WHERE vocals_state IN ('queued', 'running')""")
    for field in ("score_state", "lyrics_state", "style_state"):
        execute(f"UPDATE identity_songs SET {field} = 'none' WHERE {field} IN ('queued', 'running')")
    tasks = [asyncio.create_task(jobs.worker()), asyncio.create_task(jobs.stems_worker()), asyncio.create_task(jobs.keeper()),
             asyncio.create_task(jobs.identity_worker()),
             # One request a day to our own site, on this loop rather than in a job lane:
             # it must never stand in front of a render, a training run or a corpus.
             asyncio.create_task(update.watcher(lambda: setting_value("app.update_check") == "on")),
             # A fifth of a second a take, so off the start path.
             asyncio.create_task(asyncio.to_thread(fill_loudness))]
    log.info("Yeufonic %s up. engine=%s (%s) data=%s", config.VERSION, config.ENGINE_URL,
             "online" if ENGINE.online else "offline", config.DATA_DIR)
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await ENGINE.close()


async def requeue_waiting() -> None:
    """Put jobs that were waiting at shutdown back in their queues, oldest first."""
    waiting = [(row["created_at"], "take", row) for row in rows("SELECT id, abc, created_at FROM takes WHERE status = 'queued'")]
    waiting += [(row["created_at"], "source", row) for row in rows("SELECT id, created_at FROM sources WHERE transcribe_state = 'queued'")]
    for _, kind, row in sorted(waiting, key=lambda item: item[0]):
        if kind == "source":
            await QUEUE.put({"kind": "transcribe", "id": row["id"]})
        else:
            await QUEUE.put({"kind": "render" if (row["abc"] or "").strip() else "plan", "id": row["id"]})
    for row in rows("SELECT id FROM stem_sets WHERE status = 'queued' ORDER BY created_at"):
        await STEM_QUEUE.put({"id": row["id"]})
    for row in rows("SELECT id FROM sources WHERE lyrics_state IN ('queued', 'running') ORDER BY created_at"):
        execute("UPDATE sources SET lyrics_state = 'queued' WHERE id = ?", (row["id"],))
        await STEM_QUEUE.put({"kind": "lyrics", "id": row["id"]})
    if waiting:
        log.info("%d waiting jobs queued again after the restart", len(waiting))


app = FastAPI(title="Yeufonic", lifespan=lifespan)


# A refusal shows once in the page's status line and was gone after that.  Each one that
# answers an action is logged, so a report of "it would not render" has a line to read.
# The page's polls (GET) are left out: a missing waveform while a take renders is normal.
@app.exception_handler(StarletteHTTPException)
async def logged_refusal(request: Request, exc: StarletteHTTPException):
    if request.method != "GET" and 400 <= exc.status_code < 500:
        log.info("Refused %s %s (%d): %s", request.method, request.url.path, exc.status_code, str(exc.detail)[:300])
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def logged_invalid(request: Request, exc: RequestValidationError):
    # Where and why, never the values sent: a settings request carries a key.
    problems = "; ".join(f"{'.'.join(str(p) for p in e.get('loc', ()))}: {e.get('msg')}" for e in exc.errors()[:5])
    log.warning("Rejected %s %s: %s", request.method, request.url.path, problems[:300])
    return await request_validation_exception_handler(request, exc)


def host_allowed(host_header: str) -> bool:
    if "*" in config.ALLOWED_HOSTS:
        return True
    hostname = (urlsplit("//" + host_header).hostname or "").lower()
    return hostname in config.ALLOWED_HOSTS


# Every path the corpus and training workflow answers on.  One tuple in one place,
# because the workflow has twenty-odd route decorators and a guard repeated that many
# times is a guard that will be forgotten on the next one added.
TRAINING_PATHS = ("/api/identities", "/api/personas", "/api/lora-runs", "/api/import/")


@app.middleware("http")
async def training_off(request: Request, call_next):
    """Corpora and training, when TRAINING_ENABLED=0 has switched them off.

    The whole workflow is behind this, not only the training step: preparing a corpus
    costs real CPU — a vocal separation and a transcription for every song — and with
    no way to train at the end of it, that work buys nothing.  Any corpus already on
    disk is untouched; only the way in is closed."""
    if not config.TRAINING_ENABLED and request.url.path.startswith(TRAINING_PATHS):
        # JSON with a detail key, like every other refusal here, so the page shows the
        # reason rather than a wall of plain text.
        return JSONResponse(
            {"detail": "Corpora and LoRA training are switched off. Set TRAINING_ENABLED=1 "
                       "for the app, with the engine built with WITH_TRAINER=1."},
            status_code=501,
        )
    return await call_next(request)


@app.middleware("http")
async def guard(request: Request, call_next):
    """Refuse unknown Host names (DNS rebinding) and cross-site writes (a page on
    another site posting to this one).  Then set cache headers on the page."""
    if not host_allowed(request.headers.get("host", "")):
        return PlainTextResponse("This host name is not allowed. Add it to ALLOWED_HOSTS.", status_code=421)
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin is not None and urlsplit(origin).netloc.lower() != request.headers.get("host", "").lower():
            return PlainTextResponse("Cross-site request refused.", status_code=403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return PlainTextResponse("Cross-site request refused.", status_code=403)
    if request.method == "POST" and request.url.path == "/api/sources":
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > config.MAX_UPLOAD_MB * 1024 * 1024 + 65536:
            return PlainTextResponse(f"That file is larger than {config.MAX_UPLOAD_MB} MB.", status_code=413)
    response = await call_next(request)
    # Revalidate the page and its assets on every load, so a new app.js is never
    # hidden behind a stale copy, but an unchanged file costs a 304, not a download.
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.middleware("http")
async def revalidate_static(request, call_next):
    """Let the browser cache the page's scripts and stylesheets, but check them
    every time.  They are asked for as app.js?v=<VERSION>, and the version moves
    only for a feature release, so without this a deploy could leave a browser on
    the old files.  StaticFiles sends an ETag and a Last-Modified, so an unchanged
    file costs a 304 rather than a download."""
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ------------------------------------------------------------------- api models
class ScoreIn(BaseModel):
    abc: str = Field(max_length=200_000)


class RetrackIn(BaseModel):
    vocal_track: int
    ins_track: int | None = None
    octave_shift: int | None = None
    bar_offset: int | None = None


ADVANCED_KEYS = (
    "sampler_steps", "avoid", "target_key", "target_bpm", "max_abc_tokens",
    "chord_hold_limit", "chord_outside_bonus", "chord_sections", "follow_structure", "target_lufs", "fade_out_seconds",
)
ADVANCED_DEFAULTS = {
    "sampler_steps": 32,
    "avoid": None,
    "target_key": None,
    "target_bpm": None,
    "max_abc_tokens": 8192,
    "chord_hold_limit": 8,
    "chord_outside_bonus": 0.0,
    # None follows the Harmony step (sections open differently from Colourful up); 1 forces it on, 0 off.
    "chord_sections": None,
    # 1 makes the plan write exactly the sections the lyrics name, in order; None and 0 leave the planner its own shape.
    "follow_structure": None,
    "target_lufs": None,
    "fade_out_seconds": 3.0,
}


def _advanced_of(body, fallback: dict | None = None) -> dict:
    """Extract advanced take settings from an input model, falling back to an
    existing take dict or defaults."""
    res = {}
    fb = fallback or {}
    sent = getattr(body, "model_fields_set", set()) if body is not None else set()
    for key in ADVANCED_KEYS:
        val = getattr(body, key, None) if body is not None else None
        if key in sent:
            # Asked for, so a null or an empty text is the page saying "back to the default" (Reset),
            # not "I said nothing": the take's old value must not come back.
            res[key] = ADVANCED_DEFAULTS[key] if val is None or (isinstance(val, str) and not val.strip()) else val
        elif key in fb and fb[key] is not None:
            res[key] = fb[key]
        else:
            res[key] = ADVANCED_DEFAULTS[key]
    return res


class SongIn(BaseModel):
    title: str | None = Field(None, max_length=200)
    # What the lyrics were asked to be about, kept with the take so Write lyrics can show it again.
    brief: str | None = Field(None, max_length=1000)
    style: str = Field(config.DEFAULT_STYLE, max_length=2000)
    lyrics: str = Field("", max_length=20_000)
    seed: int | None = Field(None, ge=0, le=MAX_SEED)
    max_duration: float = Field(360.0, ge=10, le=900)
    auto_render: bool = False
    interpretation: str = "standard"
    variety: str = "normal"
    harmony: int = Field(0, ge=0, le=len(HARMONY_STEPS) - 1)
    space_id: str = Field(DEFAULT_SPACE, max_length=64)
    realaudio: bool = True
    normalise: bool = False
    identity_id: str | None = Field(None, max_length=64)
    persona_id: str | None = Field(None, max_length=64)
    voice_lora: str | None = Field(None, max_length=200)
    voice_lora_strength: float = 1.0
    voice_lora_clip: float = Field(0.0, ge=0.0, le=3.0)
    style_lora: str | None = Field(None, max_length=200)
    style_lora_model: float = Field(1.0, ge=0.0, le=3.0)
    style_lora_clip: float = Field(1.0, ge=0.0, le=3.0)
    sampler_steps: int | None = Field(32, ge=16, le=64)
    avoid: str | None = Field(None, max_length=1000)
    target_key: str | None = Field(None, max_length=50)
    target_bpm: int | None = Field(None, ge=20, le=400)
    max_abc_tokens: int | None = Field(8192, ge=512, le=8192)
    chord_hold_limit: int | None = Field(8, ge=1, le=32)
    chord_outside_bonus: float | None = Field(0.0, ge=0.0, le=10.0)
    chord_sections: int | None = Field(None, ge=0, le=1)
    follow_structure: int | None = Field(None, ge=0, le=1)
    target_lufs: float | None = Field(None, ge=-30.0, le=-4.0)
    fade_out_seconds: float | None = Field(3.0, ge=0.5, le=15.0)


def _style_lora_of(body) -> dict:
    """The style LoRA a create request asked for.  Both strengths are kept even
    when the name is empty, so an interrupted choice does not leave a take
    claiming a strength it never used."""
    name = (getattr(body, "style_lora", None) or "").strip() or None
    return {
        "style_lora": name,
        "style_lora_model": float(getattr(body, "style_lora_model", 1.0) or 0.0) if name else 1.0,
        "style_lora_clip": float(getattr(body, "style_lora_clip", 1.0) or 0.0) if name else 1.0,
    }


class ReplanIn(BaseModel):
    # Both optional: an omitted field keeps what the take already has.
    variety: str | None = None
    harmony: int | None = Field(None, ge=0, le=len(HARMONY_STEPS) - 1)
    sampler_steps: int | None = Field(None, ge=16, le=64)
    avoid: str | None = Field(None, max_length=1000)
    target_key: str | None = Field(None, max_length=50)
    target_bpm: int | None = Field(None, ge=20, le=400)
    max_abc_tokens: int | None = Field(None, ge=512, le=8192)
    chord_hold_limit: int | None = Field(None, ge=1, le=32)
    chord_outside_bonus: float | None = Field(None, ge=0.0, le=10.0)
    chord_sections: int | None = Field(None, ge=0, le=1)
    follow_structure: int | None = Field(None, ge=0, le=1)
    target_lufs: float | None = Field(None, ge=-30.0, le=-4.0)
    fade_out_seconds: float | None = Field(None, ge=0.5, le=15.0)


class TakeIn(BaseModel):
    source_id: str = Field(max_length=64)
    title: str | None = Field(None, max_length=200)
    style: str = Field(config.DEFAULT_STYLE, max_length=2000)
    lyrics: str = Field("", max_length=20_000)
    abc: str | None = Field(None, max_length=200_000)
    mode: str = "full"
    seed: int | None = Field(None, ge=0, le=MAX_SEED)
    max_duration: float = Field(360.0, ge=10, le=900)
    space_id: str = Field(DEFAULT_SPACE, max_length=64)
    interpretation: str = "standard"
    realaudio: bool = True
    normalise: bool = False
    identity_id: str | None = Field(None, max_length=64)
    persona_id: str | None = Field(None, max_length=64)
    voice_lora: str | None = Field(None, max_length=200)
    voice_lora_strength: float = 1.0
    voice_lora_clip: float = Field(0.0, ge=0.0, le=3.0)
    style_lora: str | None = Field(None, max_length=200)
    style_lora_model: float = Field(1.0, ge=0.0, le=3.0)
    style_lora_clip: float = Field(1.0, ge=0.0, le=3.0)
    sampler_steps: int | None = Field(32, ge=16, le=64)
    avoid: str | None = Field(None, max_length=1000)
    target_key: str | None = Field(None, max_length=50)
    target_bpm: int | None = Field(None, ge=20, le=400)
    max_abc_tokens: int | None = Field(8192, ge=512, le=8192)
    chord_hold_limit: int | None = Field(8, ge=1, le=32)
    chord_outside_bonus: float | None = Field(0.0, ge=0.0, le=10.0)
    chord_sections: int | None = Field(None, ge=0, le=1)
    follow_structure: int | None = Field(None, ge=0, le=1)
    target_lufs: float | None = Field(None, ge=-30.0, le=-4.0)
    fade_out_seconds: float | None = Field(3.0, ge=0.5, le=15.0)


class InstrumentalIn(BaseModel):
    title: str | None = Field(None, max_length=200)
    style: str = Field(config.DEFAULT_STYLE, max_length=2000)
    structure: str = Field(instrumental.BARE, max_length=4000)
    # From a recording: its transcription is the score, as a cover's is, and its
    # sections the structure.  The score as the editor holds it, when sent.
    source_id: str | None = Field(None, max_length=64)
    abc: str | None = Field(None, max_length=200_000)
    seed: int | None = Field(None, ge=0, le=MAX_SEED)
    max_duration: float = Field(360.0, ge=10, le=900)
    auto_render: bool = False
    variety: str = "normal"
    harmony: int = Field(0, ge=0, le=len(HARMONY_STEPS) - 1)
    space_id: str = Field(DEFAULT_SPACE, max_length=64)
    interpretation: str = "standard"
    feel: str = "steady"
    realaudio: bool = True
    normalise: bool = False
    identity_id: str | None = Field(None, max_length=64)
    persona_id: str | None = Field(None, max_length=64)
    voice_lora: str | None = Field(None, max_length=200)
    voice_lora_strength: float = 1.0
    voice_lora_clip: float = Field(0.0, ge=0.0, le=3.0)
    style_lora: str | None = Field(None, max_length=200)
    style_lora_model: float = Field(1.0, ge=0.0, le=3.0)
    style_lora_clip: float = Field(1.0, ge=0.0, le=3.0)
    sampler_steps: int | None = Field(32, ge=16, le=64)
    avoid: str | None = Field(None, max_length=1000)
    target_key: str | None = Field(None, max_length=50)
    target_bpm: int | None = Field(None, ge=20, le=400)
    max_abc_tokens: int | None = Field(8192, ge=512, le=8192)
    chord_hold_limit: int | None = Field(8, ge=1, le=32)
    chord_outside_bonus: float | None = Field(0.0, ge=0.0, le=10.0)
    chord_sections: int | None = Field(None, ge=0, le=1)
    follow_structure: int | None = Field(None, ge=0, le=1)
    target_lufs: float | None = Field(None, ge=-30.0, le=-4.0)
    fade_out_seconds: float | None = Field(3.0, ge=0.5, le=15.0)


class IdentityIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    trigger_word: str = Field(min_length=2, max_length=40)
    description: str = Field("", max_length=400)
    voice: str = Field("", max_length=20)
    folder: str = Field(min_length=1, max_length=1000)
    consent: bool = False
    lora: str | None = Field(None, max_length=200)


PersonaIn = IdentityIn


class IdentityEdit(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=80)
    trigger_word: str | None = Field(None, min_length=2, max_length=40)
    description: str | None = Field(None, max_length=400)
    voice: str | None = Field(None, max_length=20)
    lora: str | None = Field(None, max_length=200)


PersonaEdit = IdentityEdit


class IdentitySongEdit(BaseModel):
    include: bool | None = None
    # This song's sound, when it differs from the identity's. Empty means the identity's.
    description: str | None = Field(None, max_length=400)
    lyrics: str | None = Field(None, max_length=20_000)
    lyrics_checked: bool | None = None
    style_hint: str | None = Field(None, max_length=500)


PersonaSongEdit = IdentitySongEdit


class LLMTestIn(BaseModel):
    api_url: str | None = None
    api_key: str | None = None
    model: str | None = None


class RenderIn(BaseModel):
    # Optional: an omitted interpretation keeps the take's own.
    interpretation: str | None = None
    # A fresh seed for the same score: what to reach for when a take came out
    # wrong in a way the settings do not explain, such as an instrumental that
    # sang. The plan is kept; only the rendering of it changes.
    reseed: bool = False
    realaudio: bool | None = None
    normalise: bool | None = None
    identity_id: str | None = Field(None, max_length=64)
    persona_id: str | None = Field(None, max_length=64)
    voice_lora: str | None = Field(None, max_length=200)
    voice_lora_strength: float | None = None
    seed: int | None = Field(None, ge=0, le=MAX_SEED)
    # What the editor shows, so a render is made from that rather than from what
    # the take last had. Each omitted field keeps the take's own.
    style: str | None = Field(None, max_length=2000)
    max_duration: float | None = Field(None, ge=10, le=900)
    mode: str | None = None
    style_lora: str | None = Field(None, max_length=200)
    style_lora_model: float | None = Field(None, ge=0.0, le=3.0)
    style_lora_clip: float | None = Field(None, ge=0.0, le=3.0)
    sampler_steps: int | None = Field(None, ge=16, le=64)
    avoid: str | None = Field(None, max_length=1000)
    target_key: str | None = Field(None, max_length=50)
    target_bpm: int | None = Field(None, ge=20, le=400)
    max_abc_tokens: int | None = Field(None, ge=512, le=8192)
    chord_hold_limit: int | None = Field(None, ge=1, le=32)
    chord_outside_bonus: float | None = Field(None, ge=0.0, le=10.0)
    chord_sections: int | None = Field(None, ge=0, le=1)
    follow_structure: int | None = Field(None, ge=0, le=1)
    target_lufs: float | None = Field(None, ge=-30.0, le=-4.0)
    fade_out_seconds: float | None = Field(None, ge=0.5, le=15.0)


class WordsIn(RenderIn):
    lyrics: str = Field(max_length=20_000)
    brief: str | None = Field(None, max_length=1000)
    # The score as the editor holds it, so an edit to it goes with the words and the
    # original keeps its own. Omitted, the take's score is used.
    abc: str | None = Field(None, max_length=200_000)
    title: str | None = Field(None, max_length=200)


class RearrangeIn(RenderIn):
    # The score as the editor holds it, with its sections changed.
    abc: str = Field(max_length=200_000)
    title: str | None = Field(None, max_length=200)


class VariationsIn(BaseModel):
    interpretations: list[str] = Field(min_length=1, max_length=len(INTERPRETATIONS))
    # For these takes only; omitted, each keeps the original's.
    max_duration: float | None = Field(None, ge=10, le=900)
    realaudio: bool | None = None
    normalise: bool | None = None
    identity_id: str | None = Field(None, max_length=64)
    persona_id: str | None = Field(None, max_length=64)
    voice_lora: str | None = Field(None, max_length=200)
    voice_lora_strength: float | None = None


class LyricsIn(BaseModel):
    brief: str = Field(min_length=1, max_length=1000)
    style: str = Field("", max_length=2000)
    structure: str = lyrics.DEFAULT_STRUCTURE
    # The sections as built in the editor; when given, they are the structure.
    sections: list[str] | None = Field(None, min_length=1, max_length=40)
    lines: int = Field(lyrics.DEFAULT_LINES, ge=2, le=12)
    feel: str = lyrics.DEFAULT_FEEL
    seed: int | None = Field(None, ge=0, le=2**32 - 1)


class SpaceIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)


class MoveIn(BaseModel):
    space_id: str = Field(max_length=64)


class StemsIn(BaseModel):
    # All optional: an omitted field means "use what Settings says", not a hard
    # coded default, which is why these are None rather than "wav" and friends.
    model: str | None = None
    stems: list[str] = []
    format: str | None = None
    save_dir: str | None = Field(None, max_length=1000)


class SettingIn(BaseModel):
    key: str
    value: str = Field(max_length=1000)


# ------------------------------------------------------------------ page, state
def _asset_version() -> str:
    """Asset version query string for static cache busting. Includes mtime of core assets
    so browsers automatically fetch updated scripts without needing manual hard-reloads."""
    try:
        stamp = max(int(p.stat().st_mtime) for p in (STATIC_DIR / "app.js", STATIC_DIR / "pianoroll.js", STATIC_DIR / "rack.js") if p.exists())
        return f"{config.VERSION}.{stamp}"
    except (OSError, ValueError):
        return config.VERSION


_INDEX = (STATIC_DIR / "index.html").read_text(encoding="utf-8").replace("{{VERSION}}", config.VERSION)


_GUIDE = (STATIC_DIR / "guide.html").read_text(encoding="utf-8").replace("{{VERSION}}", config.VERSION)


@app.get("/")
def index() -> HTMLResponse:
    content = (STATIC_DIR / "index.html").read_text(encoding="utf-8").replace("{{VERSION}}", _asset_version())
    return HTMLResponse(content)


@app.get("/guide")
def guide() -> HTMLResponse:
    """The user guide, which is markdown on disk and rendered in the browser.

    It is served from a tidy path rather than /static/guide.html because it is a
    page people are sent to, and because the markdown itself stays readable in
    the repository and on GitHub."""
    content = (STATIC_DIR / "guide.html").read_text(encoding="utf-8").replace("{{VERSION}}", _asset_version())
    return HTMLResponse(content)


@app.get("/logs")
def logs_page() -> HTMLResponse:
    """Standalone live logs viewer in its own window or tab."""
    content = (STATIC_DIR / "logs.html").read_text(encoding="utf-8").replace("{{VERSION}}", config.VERSION)
    return HTMLResponse(content)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "engine": ENGINE.online, "version": config.VERSION}


@app.get("/api/logs")
def get_logs(
    level: str | None = None,
    search: str | None = None,
    source: str | None = None,
    limit: int = 200,
    since_id: int | None = None,
) -> dict:
    return logging_setup.get_recent_logs(level=level, search=search, source=source, limit=limit, since_id=since_id)


class ClientErrorIn(BaseModel):
    message: str = Field("", max_length=2000)
    source: str = Field("", max_length=300)
    line: int = 0
    column: int = 0
    stack: str = Field("", max_length=4000)
    page: str = Field("", max_length=300)


_CLIENT_ERRORS: collections.deque[float] = collections.deque(maxlen=30)


@app.post("/api/logs/client")
def client_error(body: ClientErrorIn) -> dict:
    """A script error in the browser, which otherwise lives only in its console.  The page
    sends at most twenty a load; this takes at most thirty a minute from all of them."""
    now = time.time()
    if len(_CLIENT_ERRORS) == _CLIENT_ERRORS.maxlen and now - _CLIENT_ERRORS[0] < 60:
        return {"logged": False}
    _CLIENT_ERRORS.append(now)
    where = f" ({body.source}:{body.line}:{body.column})" if body.source else ""
    first = " | ".join(line.strip() for line in body.stack.splitlines()[1:3] if line.strip())
    log.warning("Browser error on %s: %s%s%s", body.page or "/", body.message[:300], where,
                f" | {first[:300]}" if first else "")
    return {"logged": True}


@app.get("/api/logs/download")
def download_logs():
    if not logging_setup.LOG_FILE_PATH or not logging_setup.LOG_FILE_PATH.exists():
        raise HTTPException(404, "No log file found")
    return FileResponse(
        logging_setup.LOG_FILE_PATH,
        media_type="text/plain",
        filename="yeufonic.log",
    )


def _shorten(text: str, limit: int) -> str:
    """Cut at the last whole word that fits, and say it was cut.  A line that
    stops mid-word reads like something went wrong with the prompt."""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0] or text[:limit]
    return cut + "\u2026"


def _job_title(kind: str, ref_id: str) -> str | None:
    if kind in jobs.IDENTITY_FIELDS:
        row = one("SELECT title FROM identity_songs WHERE id = ?", (ref_id,))
        label = {"identity_score": "key and tempo", "identity_style": "style",
                 "persona_score": "key and tempo", "persona_style": "style"}.get(kind, "analysis")
        return f"{label.capitalize()}: {row['title']}" if row else None
    if kind == "lyrics":
        record = LYRICS.get(ref_id)
        return ("Lyrics: " + _shorten(record["brief"], 60)) if record else None
    if kind == "transcribe":
        row = one("SELECT title FROM sources WHERE id = ?", (ref_id,))
    else:
        row = one("SELECT title FROM takes WHERE id = ?", (ref_id,))
    return row["title"] if row else None


def queue_view() -> list[dict]:
    """Everything ahead of and behind the GPU: the engine's own queue, running first,
    then the app's jobs that have not been sent yet.  Jobs sent to the engine by
    something else are listed too, without a title, since only their kind is known."""
    now = time.time()
    items = []
    for entry in ENGINE.queue:
        item = {"state": entry["state"], "kind": entry["kind"], "outside": not entry["mine"],
                "client": None if entry["mine"] else (entry["client"] or "unknown"),
                "since": entry["running_since"] if entry["state"] == "running" else entry["queued_at"]}
        if entry["mine"] and CURRENT.get("prompt_id") == entry["prompt_id"]:
            item.update({"id": CURRENT["id"], "kind": CURRENT["kind"], "title": _job_title(CURRENT["kind"], CURRENT["id"])})
            if entry["state"] == "running":
                snap = ENGINE.snapshot(entry["prompt_id"])
                item.update({"progress": snap.get("progress"),
                             "label": stage_label(snap["stage"]) if snap.get("stage") else None})
        elif entry["mine"] and not entry["client"].startswith(ENGINE.client_id):
            item["note"] = "sent before the app restarted"
        items.append(item)
    if CURRENT.get("id") and not CURRENT.get("prompt_id"):
        items.append({
            "state": "running",
            "kind": CURRENT["kind"],
            "outside": False,
            "client": None,
            "since": CURRENT.get("started", now),
            "id": CURRENT["id"],
            "title": _job_title(CURRENT["kind"], CURRENT["id"]),
            "label": "External LLM",
        })
    for job in jobs.waiting_jobs():
        if job["kind"] in jobs.IDENTITY_FIELDS:
            song = one(f"SELECT {jobs.IDENTITY_FIELDS[job['kind']]} AS status FROM identity_songs WHERE id = ?", (job["id"],))
            row = {"title": _job_title(job["kind"], job["id"]), "status": song["status"]} if song else None
        elif job["kind"] == "lyrics":
            draft = LYRICS.get(job["id"])
            row = {"title": _job_title("lyrics", job["id"]), "status": draft["status"]} if draft else None
        elif job["kind"] == "transcribe":
            row = one("SELECT title, transcribe_state AS status FROM sources WHERE id = ?", (job["id"],))
        else:
            row = one("SELECT title, status FROM takes WHERE id = ?", (job["id"],))
        if not row or row["status"] != "queued":
            continue   # deleted or cancelled while it waited; the worker will skip it
        title = row["title"]
        items.append({"state": "waiting", "kind": job["kind"], "id": job["id"], "title": title,
                      "outside": False, "client": None, "since": None})
    for item in items:
        item["seconds"] = round(now - item["since"], 1) if item.get("since") else None
        item.pop("since", None)
    return items


def _learned_style(song: dict, corpus: dict) -> str:
    """A corpus song's training caption, less the trigger word and the tempo the page
    adds: the same parts, and the same override, as the export in _identity_view."""
    return identities.caption("", song["description"] or corpus["description"] or "", corpus["voice"] or "",
                              song["key"], None, song["style_hint"] or "")


def _lora_corpus_styles() -> dict[str, list[dict]]:
    """Map each identity's LoRA filename to its included songs' learned styles.

    Each one is the song's training caption, less the trigger word the page puts in
    front and the tempo it puts after.  A LoRA learns the sound together with the
    words it was captioned with, so a style that drops the corpus's description or
    the voice asks it for something it never saw, and it falls back to stock."""
    try:
        identity_rows = rows("SELECT id, lora, description, voice FROM identities WHERE lora IS NOT NULL AND lora != ''")
        out: dict[str, list[dict]] = {}
        for iden in identity_rows:
            songs = rows(
                "SELECT title, style_hint, tempo, key, description FROM identity_songs "
                "WHERE identity_id = ? AND include = 1 ORDER BY position, id",
                (iden["id"],),
            )
            seen = set()
            song_list = []
            for s in songs:
                prompt = _learned_style(s, iden)
                if not prompt or (prompt, s["tempo"]) in seen:
                    continue
                seen.add((prompt, s["tempo"]))
                song_list.append({"title": s["title"], "prompt": prompt, "hint": s["style_hint"] or "",
                                  "tempo": s["tempo"], "key": s["key"]})
            if song_list:
                out[iden["lora"]] = song_list
        return out
    except Exception as err:
        log.warning("could not query corpus styles for loras: %s", err)
        return {}


def _catalogue_with_styles() -> list[dict]:
    items = loras.catalogue(ENGINE.options.get("loras", []))
    corpus_styles = _lora_corpus_styles()
    for item in items:
        # A checkpoint was trained on the same captions as its LoRA, so it takes the same chips.
        styles = corpus_styles.get(item["name"]) or corpus_styles.get(loras.run_lora(item["name"]))
        if styles:
            item["styles"] = styles
    return items


class UpdateSeenIn(BaseModel):
    version: str | None = None


class UpdateOpenIn(BaseModel):
    url: str


@app.post("/api/update/check")
async def update_check() -> dict:
    """Ask now, whatever the daily setting says: this is the menu's Check for updates.
    The answer is in the reply, so the page can say it where the click happened."""
    return await update.check(force=True)


@app.post("/api/update/seen")
def update_seen(body: UpdateSeenIn) -> dict:
    """The notice has been read, so it is not shown again for this release."""
    return update.mark_seen(body.version)


@app.post("/api/update/open")
def update_open(body: UpdateOpenIn) -> dict:
    """Open an update link in the default desktop browser rather than inside the
    application's tile-less window, so downloads and SmartScreen prompts are handled
    by the user's primary browser and detached from the launcher."""
    url = body.url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")
    if hasattr(os, "startfile"):
        try:
            os.startfile(url)
            return {"opened": True}
        except Exception as exc:
            log.warning("Could not open update URL via system shell: %s", exc)
    return {"opened": False}


@app.post("/api/update/download")
async def update_download() -> dict:
    """Start downloading the update installer directly in the background."""
    try:
        return await update.start_download()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        log.warning("Could not start update download: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/update/download")
def update_download_status() -> dict:
    """Current state of the in-app update installer download."""
    return update.download_state()


@app.post("/api/update/download/cancel")
def update_download_cancel() -> dict:
    """Cancel an ongoing update download."""
    return update.cancel_download()


@app.post("/api/update/launch")
def update_launch() -> dict:
    """Launch the downloaded installer."""
    try:
        launched = update.launch_installer()
        return {"launched": launched}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/update/reveal")
def update_reveal() -> dict:
    """Reveal the downloaded installer in Windows Explorer."""
    try:
        revealed = update.reveal_installer()
        return {"revealed": revealed}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))



@app.get("/api/state")
def state() -> dict:
    """Served from what the keeper last saw, so a page poll never waits on the engine."""
    training = _training_run()
    current = None
    if CURRENT:
        current = {
            "kind": CURRENT["kind"],
            "id": CURRENT["id"],
            "elapsed": round(time.time() - CURRENT["started"], 1),
            **ENGINE.snapshot(CURRENT.get("prompt_id")),
        }
        if current.get("stage"):
            current["label"] = stage_label(current["stage"])

    engine_gpu = ENGINE.gpu() if ENGINE.online else None
    return {
        "version": config.VERSION,
        "build": config.BUILD,
        "model": config.CHECKPOINT_LABELS.get(config.CHECKPOINT, config.CHECKPOINT),
        # Whether a newer release is out, and what to do about it: a background task keeps
        # this current, and this route only ever reads it.
        "update": update.state(),
        "settings": settings_payload(),
        "system": {
            "cpu": system_stats.get_cpu_percent(),
            "gpu": system_stats.get_gpu_percent(engine_gpu=engine_gpu),
        },
        "engine": {
            "url": config.ENGINE_URL,
            "online": ENGINE.online,
            "starting": ENGINE.starting,
            "stuck": bool(ENGINE.stuck_on),
            "error": ENGINE.last_error,
            "compat": ENGINE.compat,
            "queue": ENGINE.queue_counts,
            "gpu": engine_gpu,
        },
        "current": current,
        # A LoRA being trained holds the card, so the page disables the rest while it
        # reports: a training run, how far along, and what it has cost so far.
        "training": None if not training else {
            "id": training["id"],
            "identity_id": training["identity_id"],
            "lora_name": training["lora_name"],
            "state": training["state"],
            "steps": training["steps"],
            "rank": training["rank"],
            "stage": training["stage"],
            "progress": training["progress"],
            "elapsed": round(time.time() - training["started_at"], 1) if training["started_at"] else 0,
        },
        "queue": queue_view(),
        "stems": {
            "available": stems.installed(),
            "models": [{"id": k, "label": v["label"], "stems": v["stems"]} for k, v in stems.MODELS.items()],
            "formats": stems.FORMATS,
            "avg_seconds": float(get_setting("avg_stems_seconds", "0") or 0),
            "current": ({"id": CURRENT_STEMS.get("id"), "title": CURRENT_STEMS.get("title"),
                         "elapsed": round(time.time() - CURRENT_STEMS.get("started", time.time()), 1)}
                        if CURRENT_STEMS else None),
        },
        "options": {
            "default_style": config.DEFAULT_STYLE,
            "avg_render_seconds": float(get_setting("avg_render_seconds", "0") or 0),
            "interpretations": [{"id": key, "name": INTERPRETATION_NAMES[key]} for key in INTERPRETATIONS],
            "lyric_structures": [{"id": key, "sections": value, "hint": lyrics.HINTS.get(key, "")} for key, value in lyrics.STRUCTURES.items()],
            "lyric_sections": sorted(lyrics.TAGS, key=["intro", "verse", "pre-chorus", "chorus", "bridge", "interlude", "outro"].index),
            "lyric_lines": lyrics.DEFAULT_LINES,
            "lyric_feels": [{"id": key, "label": f"{value[0]} ({lyrics.FEEL_SYLLABLES[key]} syllables)", "hint": value[2]}
                            for key, value in lyrics.FEELS.items()],
            "lyrics_available": bool(llm.is_external_enabled() or ENGINE.options.get("lyrics", False)),
            "llm_provider": llm.get_config()["provider"],
            "instrumental_available": ENGINE.options.get("instrumental", False),
            "realaudio": ENGINE.options.get("realaudio", False),
            "loras": _catalogue_with_styles(),
            "harmony_steps": HARMONY_STEPS,
            # Unknown until the engine has been read, so only a confirmed absence disables it.
            "harmony_available": ENGINE.options.get("harmony", False) or not ENGINE.options_loaded,
            # Both switches and the engine's node, so the page never offers a button
            # that would answer 501.  See config.TRAINING_ENABLED.
            "training_available": config.TRAINING_ENABLED and ENGINE.options.get("trainer", False),
            "weak_render_db": config.WEAK_RENDER_DB,
        },
    }


# ----------------------------------------------------------------------- sources
@app.get("/api/sources")
def list_sources() -> list[dict]:
    got = rows(
        """SELECT id, title, filename, created_at, transcribe_state, transcribe_error, duration,
                  abc, lyrics_state, (lyrics IS NOT NULL AND lyrics != '') AS has_lyrics,
                  (abc IS NOT NULL AND abc != '') AS has_score,
                  (SELECT COUNT(*) FROM takes t WHERE t.source_id = sources.id) AS take_count
           FROM sources ORDER BY created_at DESC"""
    )
    for item in got:
        # What the score says the music lasts, so the page can weigh it against the
        # recording without asking for the whole score.
        found = score.estimate(item.pop("abc") or "")
        item["score_seconds"] = found["seconds"] if found else None
        item["score_bpm"] = found["bpm"] if found else None
    return got


@app.get("/api/sources/{source_id}")
def get_source(source_id: str) -> dict:
    source = one("SELECT * FROM sources WHERE id = ?", (source_id,))
    if not source:
        raise HTTPException(404, "no such source")
    return source


class TooLarge(Exception):
    pass


def _store_upload(fileobj) -> tuple[str, Path, int]:
    """Copy an upload into the work folder while hashing it, a megabyte at a time."""
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    limit = config.MAX_UPLOAD_MB * 1024 * 1024
    digest = hashlib.sha256()
    size = 0
    fd, name = tempfile.mkstemp(dir=config.WORK_DIR, prefix="upload-")
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as out:
            fileobj.seek(0)
            while chunk := fileobj.read(1 << 20):
                size += len(chunk)
                if size > limit:
                    raise TooLarge()
                digest.update(chunk)
                out.write(chunk)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return digest.hexdigest(), tmp, size


@app.post("/api/sources")
async def upload_source(file: UploadFile = File(...), title: str = Form("", max_length=200)) -> dict:
    try:
        digest, tmp, size = await asyncio.to_thread(_store_upload, file.file)
    except TooLarge:
        raise HTTPException(413, f"That file is larger than {config.MAX_UPLOAD_MB} MB.")
    if not size:
        tmp.unlink(missing_ok=True)
        raise HTTPException(400, "empty upload")
    existing = one("SELECT * FROM sources WHERE sha256 = ?", (digest,))
    if existing:
        tmp.unlink(missing_ok=True)
        return {**existing, "duplicate": True}

    ext = Path(file.filename or "source.mp3").suffix.lower() or ".mp3"
    if len(ext) > 6 or not ext[1:].isalnum():
        ext = ".audio"
    source_id = uuid.uuid4().hex[:12]
    dest = source_path(digest, file.filename or "", title or "source", ext)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp.replace(dest)

    # Detect MIDI uploads by extension or binary header
    is_midi = ext in (".mid", ".midi")
    if not is_midi:
        try:
            with dest.open("rb") as f_check:
                is_midi = f_check.read(4) == b"MThd"
        except OSError:
            is_midi = False

    if is_midi:
        midi_data = None
        try:
            raw_midi = dest.read_bytes()
            midi_data = await asyncio.to_thread(midi.parse_midi, raw_midi, title or Path(file.filename or "Untitled").stem)
        except Exception as exc:
            log.warning("Could not parse MIDI file %s: %s", file.filename, exc)

        if midi_data:
            duration = midi_data["duration"]
            abc = midi_data["abc"]
            lyrics_text = midi_data.get("lyrics")
            record = {
                "id": source_id,
                "title": title or midi_data["title"] or Path(file.filename or "Untitled").stem,
                "filename": file.filename or dest.name,
                "stored_path": str(dest),
                "engine_file": None,
                "sha256": digest,
                "created_at": time.time(),
                "duration": duration,
                "abc": abc,
                "abc_updated_at": time.time(),
                "transcribe_state": "done",
                "lyrics": lyrics_text or None,
                "lyrics_state": "done" if lyrics_text else "none",
                "lyrics_method": "midi" if lyrics_text else None,
            }
            execute(
                """INSERT INTO sources(id, title, filename, stored_path, engine_file, sha256, created_at, duration,
                                       abc, abc_updated_at, transcribe_state, lyrics, lyrics_state, lyrics_method)
                   VALUES(:id, :title, :filename, :stored_path, :engine_file, :sha256, :created_at, :duration,
                          :abc, :abc_updated_at, :transcribe_state, :lyrics, :lyrics_state, :lyrics_method)""",
                record,
            )
            # Render audio preview with active SoundFont
            try:
                flac_p = dest.with_suffix(".flac")
                await asyncio.to_thread(soundfonts.render_midi_to_audio, dest, flac_p)
            except Exception as exc:
                log.warning("Could not pre-render MIDI audio %s: %s", dest.name, exc)
            dur_str = f", {record['duration']:.1f}s" if record.get("duration") else ""
            log.info("Uploaded MIDI source '%s' (%s%s, converted to ABC)", record["title"], record["id"], dur_str)
            return {**record, "duplicate": False}

    record = {
        "id": source_id,
        "title": title or Path(file.filename or "Untitled").stem,
        "filename": file.filename or dest.name,
        "stored_path": str(dest),
        "engine_file": None,   # sent to the engine when it is transcribed
        "sha256": digest,
        "created_at": time.time(),
        # Read once here, so a score transcribed from it can be checked against it.
        "duration": await asyncio.to_thread(audio_duration, dest),
    }
    execute(
        """INSERT INTO sources(id, title, filename, stored_path, engine_file, sha256, created_at, duration)
           VALUES(:id, :title, :filename, :stored_path, :engine_file, :sha256, :created_at, :duration)""",
        record,
    )
    dur_str = f", {record['duration']:.1f}s" if record.get("duration") else ""
    log.info("Uploaded source recording '%s' (%s%s)", record["title"], record["id"], dur_str)
    return {**record, "transcribe_state": "none", "abc": None, "duplicate": False}


# ------------------------------------------------------ a corpus song as a recording
# A corpus's analysis already did what a cover needs from a recording: SheetSage's
# score, and the words heard by Whisper, with the vocal separated.  So an analysed
# corpus song can become a recording in one step, with nothing run again.
def _corpus_song_files(song: dict) -> tuple[Path, Path] | None:
    """The song's stored copy and its score, if both are there."""
    stored = Path(song["stored_path"]) if song.get("stored_path") else None
    if not stored or not stored.is_file():
        return None
    abc = stored.parent / "score.abc"
    return (stored, abc) if abc.is_file() else None


def _score_caveat(abc: str, duration: float | None) -> str | None:
    """A corpus score that was a fallback: made without chords, or from the first
    minutes only, when the whole song would not transcribe.  Fine for training, less
    so for a cover, so the picker says so."""
    if not re.search(r'"[A-G][#b]?[^"\n]{0,10}"', abc):
        return "melody only"
    found = score.estimate(abc)
    if found and duration and found["seconds"] < 0.8 * duration:
        return f"first {round(found['seconds'] / 60)} min"
    return None


@app.get("/api/corpus-songs")
def corpus_songs() -> list[dict]:
    """Every analysed corpus song that could become a recording, corpus by corpus."""
    # A recording made from a corpus song says which, and is a hard link to its file:
    # found either way without hashing hundreds of songs on every look at the list.
    made = {}
    known = {}
    for row in rows("SELECT id, stored_path, corpus_song_id FROM sources"):
        if row["corpus_song_id"]:
            made[row["corpus_song_id"]] = row["id"]
        with contextlib.suppress(OSError):
            found = os.stat(row["stored_path"])
            known[(found.st_dev, found.st_ino)] = row["id"]
    groups: dict[str, dict] = {}
    for song in rows("""SELECT s.*, i.name AS corpus, i.description AS corpus_description, i.voice AS corpus_voice
                        FROM identity_songs s JOIN identities i ON i.id = s.identity_id
                        WHERE s.score_state = 'done' ORDER BY lower(i.name), s.position"""):
        files = _corpus_song_files(song)
        if not files:
            continue
        abc = files[1].read_text(encoding="utf-8", errors="replace")
        on_disk = files[0].stat()
        group = groups.setdefault(song["identity_id"], {"id": song["identity_id"], "name": song["corpus"], "songs": []})
        group["songs"].append({
            "id": song["id"], "title": song["title"] or Path(song["file"]).stem, "duration": song["duration"],
            "key": song["key"], "tempo": song["tempo"], "caveat": _score_caveat(abc, song["duration"]),
            "source_id": made.get(song["id"]) or known.get((on_disk.st_dev, on_disk.st_ino)),
            # What a cover of it starts from, as its learned-style chip has it.
            "style": _learned_style(song, {"description": song["corpus_description"], "voice": song["corpus_voice"]}),
        })
    return list(groups.values())


@app.post("/api/sources/from-corpus/{song_id}")
async def source_from_corpus(song_id: str) -> dict:
    """Make an analysed corpus song a recording: its file linked in, not copied, so it
    takes no more space and outlives the corpus; its score as the transcription; its
    heard words laid under the score's sections, as Extract lyrics does, or its words
    as they stand when someone has checked them; and its separated vocal, so Extract
    lyrics has no separating to do."""
    song = one("SELECT * FROM identity_songs WHERE id = ?", (song_id,))
    if not song:
        raise HTTPException(404, "no such corpus song")
    files = _corpus_song_files(song)
    if not files or song["score_state"] != "done":
        raise HTTPException(400, "this song has not been analysed yet")
    stored, abc_file = files
    existing = one("SELECT * FROM sources WHERE corpus_song_id = ?", (song_id,))
    if existing:
        return {**existing, "duplicate": True}
    digest = await asyncio.to_thread(_sha256_of, stored)
    existing = one("SELECT * FROM sources WHERE sha256 = ?", (digest,))
    if existing:
        return {**existing, "duplicate": True}
    title = song["title"] or Path(song["file"]).stem
    dest = source_path(digest, title, "source", stored.suffix.lower() or ".flac")
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(stored, dest)
    except OSError:
        await asyncio.to_thread(shutil.copyfile, stored, dest)
    abc = abc_file.read_text(encoding="utf-8", errors="replace")
    duration = song["duration"] or await asyncio.to_thread(audio_duration, dest)
    lyrics_text, method = await asyncio.to_thread(_corpus_song_lyrics, song, stored.parent, abc, duration)
    vocals = identities.vocals_file(stored.parent)
    if vocals:
        await asyncio.to_thread(_flac_copy, vocals, vocal_path(dest))
    record = {
        "id": uuid.uuid4().hex[:12], "title": title, "filename": Path(song["file"]).name,
        "stored_path": str(dest), "engine_file": None, "sha256": digest, "created_at": time.time(),
        "duration": duration, "abc": abc, "abc_updated_at": time.time(), "transcribe_state": "done",
        "lyrics": lyrics_text or None, "lyrics_state": "done" if lyrics_text else "none", "lyrics_method": method,
        "corpus_song_id": song_id,
    }
    execute(
        """INSERT INTO sources(id, title, filename, stored_path, engine_file, sha256, created_at, duration,
                               abc, abc_updated_at, transcribe_state, lyrics, lyrics_state, lyrics_method, corpus_song_id)
           VALUES(:id, :title, :filename, :stored_path, :engine_file, :sha256, :created_at, :duration,
                  :abc, :abc_updated_at, :transcribe_state, :lyrics, :lyrics_state, :lyrics_method, :corpus_song_id)""",
        record,
    )
    log.info("Made corpus song '%s' a recording (%s), with its score%s", title, record["id"],
             " and words" if lyrics_text else "")
    return {**record, "duplicate": False}


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _corpus_song_lyrics(song: dict, folder: Path, abc: str, duration: float | None) -> tuple[str, str | None]:
    """Words someone has checked are kept as they are.  Otherwise the lines Whisper
    heard are laid under the score's sections, as Extract lyrics lays them, so the
    sections match the score the cover follows."""
    if song["lyrics_checked"] and (song["lyrics"] or "").strip():
        return song["lyrics"], "the corpus, as checked there"
    heard = folder / "whisper.json"
    try:
        lines = json.loads(heard.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        lines = None
    if lines:
        method = "Whisper, in the corpus analysis"
        versions = song.get("lyrics_versions")
        if isinstance(versions, str):
            try:
                versions = json.loads(versions)
            except ValueError:
                versions = None
        if isinstance(versions, dict) and versions.get("active") == "llm":
            model = (versions.get("llm") or {}).get("model") or "the external LLM"
            method = f"{model}, in the corpus analysis"
        return identities.tag_lyrics(lines, identities.score_sections(abc), duration or 0.0), method
    return (song["lyrics"] or ""), ("the corpus" if song["lyrics"] else None)


def _flac_copy(src: Path, dest: Path) -> None:
    """A recording keeps its vocal as FLAC beside itself (the corpus keeps it as FLAC too, WAV for older songs)."""
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-c:a", "flac", str(dest)],
                       check=True, capture_output=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as exc:
        log.warning("could not keep the corpus vocal beside the recording: %s", exc)
        dest.unlink(missing_ok=True)


@app.post("/api/sources/{source_id}/transcribe")
async def transcribe(source_id: str) -> dict:
    _gpu_free_for_rendering()
    source = one("SELECT * FROM sources WHERE id = ?", (source_id,))
    if not source:
        raise HTTPException(404, "no such source")
    if (source.get("filename") or "").lower().endswith((".mid", ".midi")):
        if source.get("abc"):
            return {"queued": False, "transcribe_state": "done"}
        p = Path(source["stored_path"])
        if p.exists():
            midi_info = await asyncio.to_thread(midi.parse_midi, p.read_bytes(), source.get("title") or "")
            execute("UPDATE sources SET abc = ?, abc_updated_at = ?, transcribe_state = 'done', duration = ? WHERE id = ?",
                    (midi_info["abc"], time.time(), midi_info["duration"], source_id))
            return {"queued": False, "transcribe_state": "done"}
    if source["transcribe_state"] in ACTIVE:
        raise HTTPException(409, "this recording is already being transcribed")
    if not Path(source["stored_path"]).exists():
        raise HTTPException(400, "the file for this recording is missing")
    execute("UPDATE sources SET transcribe_state = 'queued', transcribe_error = NULL WHERE id = ?", (source_id,))
    await QUEUE.put({"kind": "transcribe", "id": source_id})
    log.info("Queued transcription for source '%s' (%s)", source.get("title") or source_id, source_id)
    return {"queued": True}


@app.put("/api/sources/{source_id}/score")
def save_score(source_id: str, body: ScoreIn) -> dict:
    before = one("SELECT title, abc FROM sources WHERE id = ?", (source_id,))
    if not execute("UPDATE sources SET abc = ?, abc_updated_at = ? WHERE id = ?", (body.abc, time.time(), source_id)):
        raise HTTPException(404, "no such source")
    if before and (before["abc"] or "") != (body.abc or ""):
        log.info("Score of recording '%s' (%s) edited by hand (%d characters)", before["title"], source_id, len(body.abc or ""))
    return {"saved": True, "chars": len(body.abc)}


@app.get("/api/sources/{source_id}/tracks")
def get_source_tracks(source_id: str) -> dict:
    """Inspect and return detected tracks and roles for a MIDI source."""
    source = one("SELECT * FROM sources WHERE id = ?", (source_id,))
    if not source:
        raise HTTPException(404, "no such source")
    stored_path = Path(source["stored_path"])
    if not stored_path.exists():
        raise HTTPException(400, "the file for this recording is missing")
    if not (source.get("filename") or "").lower().endswith((".mid", ".midi")):
        return {"tracks": []}
    try:
        data = stored_path.read_bytes()
        tracks = midi.extract_midi_tracks(data)
        return {"tracks": tracks}
    except Exception as exc:
        log.warning("Could not extract tracks from MIDI source %s: %s", source_id, exc)
        return {"tracks": []}


@app.post("/api/sources/{source_id}/retrack")
def retrack_source(source_id: str, body: RetrackIn) -> dict:
    """Reparse a MIDI source with specified Vocal and Accompaniment tracks."""
    source = one("SELECT * FROM sources WHERE id = ?", (source_id,))
    if not source:
        raise HTTPException(404, "no such source")
    stored_path = Path(source["stored_path"])
    if not stored_path.exists():
        raise HTTPException(400, "the file for this recording is missing")
    if not (source.get("filename") or "").lower().endswith((".mid", ".midi")):
        raise HTTPException(400, "Retracking requires a MIDI recording")
    try:
        data = stored_path.read_bytes()
        title = source.get("title") or stored_path.stem
        parsed = midi.parse_midi(
            data,
            title=title,
            vocal_track=body.vocal_track,
            ins_track=body.ins_track,
            octave_shift=body.octave_shift,
            bar_offset=body.bar_offset,
        )
        new_abc = parsed["abc"]
        if source.get("lyrics"):
            try:
                new_abc = aligner.align_lyrics_to_abc(new_abc, source["lyrics"])
            except Exception as exc:
                log.warning("Could not auto-align lyrics during retracking of %s: %s", source_id, exc)
        execute(
            "UPDATE sources SET abc = ?, abc_updated_at = ? WHERE id = ?",
            (new_abc, time.time(), source_id),
        )
        log.info("Retracked source '%s' (%s) with vocal track %d", source.get("title") or source_id, source_id, body.vocal_track)
        return {"id": source_id, "abc": new_abc, "tracks": parsed.get("tracks", [])}
    except Exception as exc:
        log.error("Retracking failed for source %s: %s", source_id, exc)
        raise HTTPException(500, f"Could not retrack MIDI: {exc}")


@app.delete("/api/sources/{source_id}")
async def delete_source(source_id: str) -> dict:
    """Delete an uploaded recording and its stems.  Covers made from it keep their
    audio and score, but cannot be rendered again from the recording."""
    source = one("SELECT * FROM sources WHERE id = ?", (source_id,))
    if not source:
        raise HTTPException(404, "no such source")
    if source["transcribe_state"] in ACTIVE:
        raise HTTPException(409, "this recording is being transcribed. Wait for it to finish.")
    sets = rows("SELECT * FROM stem_sets WHERE source_id = ?", (source_id,))
    for item in sets:
        jobs.cancel_stems(item)
    execute("DELETE FROM stem_sets WHERE source_id = ?", (source_id,))
    execute("DELETE FROM sources WHERE id = ?", (source_id,))
    log.info("Deleted source recording '%s' (%s)", source.get("title") or source_id, source_id)
    folders = [(Path(source["stored_path"]), config.SOURCES_DIR)]
    # Its waveform cache and separated vocal sit beside it and would outlive it.
    folders += [(kept, config.SOURCES_DIR) for kept in kept_beside(Path(source["stored_path"]))]
    folders += [(Path(item["folder"]), config.DATA_DIR) for item in sets if item["folder"]]
    await asyncio.to_thread(remove_folders, folders)
    if source.get("engine_file") and config.ENGINE_INPUT_DIR:
        ef = config.ENGINE_INPUT_DIR / source["engine_file"]
        if inside(ef, config.ENGINE_INPUT_DIR):
            ef.unlink(missing_ok=True)
    return {"deleted": True}


# ------------------------------------------------------------------------- takes
def _attach_stem_sets(takes: list[dict]) -> None:
    by_take: dict[str, list[dict]] = {take["id"]: [] for take in takes}
    if by_take:
        marks = ",".join("?" * len(by_take))
        for item in rows(
            f"""SELECT id, take_id, status, stage, progress, wanted, model, fmt, elapsed, error, folder
                FROM stem_sets WHERE take_id IN ({marks}) ORDER BY created_at DESC""",
            tuple(by_take),
        ):
            item["files"] = stem_files(item) if item["status"] == "done" else []
            by_take[item.pop("take_id")].append(item)
    for take in takes:
        take["stem_sets"] = by_take[take["id"]]


def ran_to_cap(take: dict) -> bool:
    """A render that was still going at its Length cap and was cut there, though its
    score ended well before: the model never wrote its end, and the take stops
    mid-stream.  A take capped short on purpose, shorter than its score, is not this."""
    duration, cap = take.get("duration"), take.get("max_duration")
    if not duration or not cap or duration < cap - 0.5:
        return False
    planned = score.estimate(take.get("abc") or "")
    return bool(planned and planned["seconds"] < cap - 10)


# What a search of the library looks through.
SEARCHED = ("title", "style", "lyrics", "style_lora", "voice_lora")


@app.get("/api/takes")
def list_takes(
    request: Request,
    source_id: str | None = None,
    space_id: str | None = None,
    favourite: bool = False,
    kinds: str = Query("", max_length=60),
    q: str = Query("", max_length=200),
    limit: int = Query(300, ge=1, le=5000),
) -> Response:
    """The library, newest first.  Carries an ETag, so a poll that finds nothing
    new costs a 304 instead of the whole list.  `q` keeps the takes where every
    word of it appears in the title, style, lyrics or a LoRA's name."""
    where, args = [], []
    for word in q.split():
        like = "%" + word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        where.append("(" + " OR ".join(f"{col} LIKE ? ESCAPE '\\'" for col in SEARCHED) + ")")
        args.extend([like] * len(SEARCHED))
    if source_id:
        where.append("source_id = ?")
        args.append(source_id)
    if space_id:
        where.append("space_id = ?")
        args.append(space_id)
    if favourite:
        where.append("favourite = 1")
    wanted = [k for k in kinds.split(",") if k in ("song", "cover", "instrumental")]
    if wanted:
        where.append("kind IN (" + ",".join("?" * len(wanted)) + ")")
        args.extend(wanted)
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    total = one(f"SELECT COUNT(*) AS n FROM takes {clause}", tuple(args))["n"]
    got = rows(f"SELECT * FROM takes {clause} ORDER BY created_at DESC LIMIT ?", (*args, limit))
    for take in got:
        take["has_audio"] = bool(take["audio_path"] and Path(take["audio_path"]).exists())
        take["ran_to_cap"] = ran_to_cap(take)
        take["stopped_early"] = score.stopped_early(take.get("duration"), take.get("abc"), take.get("max_duration"))
        if take.get("prompt_id") and take["status"] == "running":
            take["live"] = ENGINE.snapshot(take["prompt_id"])
    _attach_stem_sets(got)
    body = json.dumps(got, separators=(",", ":"))
    etag = '"' + hashlib.sha1(body.encode()).hexdigest()[:24] + f'-{total}"'
    headers = {"ETag": etag, "Cache-Control": "no-cache", "X-Total-Count": str(total)}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return Response(body, media_type="application/json", headers=headers)


@app.get("/api/takes/{take_id}")
def get_take(take_id: str) -> dict:
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    take["has_audio"] = bool(take["audio_path"] and Path(take["audio_path"]).exists())
    take["ran_to_cap"] = ran_to_cap(take)
    take["stopped_early"] = score.stopped_early(take.get("duration"), take.get("abc"), take.get("max_duration"))
    if take.get("prompt_id") and take["status"] == "running":
        take["live"] = ENGINE.snapshot(take["prompt_id"])
    return take


@app.get("/api/takes/{take_id}/fx")
def get_take_fx(take_id: str) -> dict:
    take = one("SELECT fx_chain FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    raw = take.get("fx_chain")
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return {}


@app.put("/api/takes/{take_id}/fx")
async def update_take_fx(take_id: str, request: Request) -> dict:
    if not one("SELECT id FROM takes WHERE id = ?", (take_id,)):
        raise HTTPException(404, "no such take")
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(400, "invalid json")
    execute("UPDATE takes SET fx_chain = ? WHERE id = ?", (json.dumps(data), take_id))
    return {"status": "ok", "fx_chain": data}


@app.post("/api/takes/{take_id}/favourite")
def favourite(take_id: str, value: bool = True) -> dict:
    if not execute("UPDATE takes SET favourite = ? WHERE id = ?", (1 if value else 0, take_id)):
        raise HTTPException(404, "no such take")
    return {"favourite": value}


class RenameTakeIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


@app.post("/api/takes/{take_id}/rename")
@app.patch("/api/takes/{take_id}")
async def rename_take(take_id: str, body: RenameTakeIn) -> dict:
    take = one("SELECT id, title FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    title = body.title.strip()
    if not title:
        raise HTTPException(400, "title cannot be empty")
    execute("UPDATE takes SET title = ? WHERE id = ?", (title, take_id))
    return {"id": take_id, "title": title}


@app.delete("/api/takes/{take_id}")
async def delete_take(take_id: str) -> dict:
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    if take["status"] in ACTIVE:
        await jobs.cancel_take(take)
    sets = rows("SELECT * FROM stem_sets WHERE take_id = ?", (take_id,))
    for item in sets:
        jobs.cancel_stems(item)
    # Rows first: a file that fails to delete leaves clutter, never a row that
    # points at nothing.
    execute("DELETE FROM stem_sets WHERE take_id = ?", (take_id,))
    execute("DELETE FROM takes WHERE id = ?", (take_id,))
    log.info("Deleted take '%s' (%s)", take.get("title") or take_id, take_id)
    folder = Path(take["audio_path"]).parent if take.get("audio_path") else take_folder(take_id, take["title"])
    folders = [(folder, config.TAKES_DIR)] + [(Path(item["folder"]), config.DATA_DIR) for item in sets if item["folder"]]
    await asyncio.to_thread(remove_folders, folders)
    return {"deleted": True}


def _locked_score(abc: str, adv: dict) -> str:
    """The score with the take's tempo and key locks applied, so the Score the person reads is
    the one that is sung.  A key it cannot move leaves the score in the key it has."""
    locked = jobs.lock_tempo(abc or "", adv.get("target_bpm"))
    if adv.get("target_key"):
        locked = transpose.to_key(locked, adv["target_key"]) or locked
    return locked


def _check_score(abc: str | None, kind: str | None = None) -> None:
    """Refuse to render a score that cannot be the song.  An empty score is allowed:
    the engine then writes its own."""
    if abc and abc.strip():
        issues = score.problems(abc, need_chords=False, instrumental=kind == "instrumental")
        if issues:
            raise HTTPException(400, f"This score cannot be rendered ({', '.join(issues)}). "
                                     "Write a new plan, or fix the score.")


def _checkpoint() -> str:
    """The one checkpoint the app uses.  Refused only once the engine has been read
    and does not have it; before that the job waits for the engine like any other."""
    if ENGINE.options_loaded and config.CHECKPOINT not in (ENGINE.options.get("checkpoints") or []):
        raise HTTPException(400, f"The engine does not have {config.CHECKPOINT}. Run scripts/fetch-models.sh.")
    return config.CHECKPOINT


def _interpretation(name: str | None) -> str:
    if name not in INTERPRETATIONS:
        raise HTTPException(400, f"unknown interpretation: {name}")
    return name


@app.post("/api/takes")
async def create_take(body: TakeIn) -> dict:
    source = one("SELECT * FROM sources WHERE id = ?", (body.source_id,))
    if not source:
        raise HTTPException(404, "no such source")
    abc_to_use = body.abc if body.abc is not None else (source["abc"] or "")
    if body.lyrics and abc_to_use and ("V: Vocal" in abc_to_use or "V:Vocal" in abc_to_use):
        try:
            abc_to_use = aligner.align_lyrics_to_abc(abc_to_use, body.lyrics)
        except Exception as exc:
            log.warning("Could not auto-align lyrics to ABC for take: %s", exc)
    _check_score(abc_to_use)
    _space(body.space_id)
    take_id = uuid.uuid4().hex[:12]
    seed = body.seed if body.seed is not None else int.from_bytes(os.urandom(4), "big")
    adv = _advanced_of(body)
    record = {
        "id": take_id,
        "source_id": body.source_id,
        "title": body.title or source["title"],
        "style": body.style.strip() or config.DEFAULT_STYLE,
        "lyrics": body.lyrics,
        "abc": _locked_score(abc_to_use, adv),
        "mode": body.mode if body.mode in ("full", "melody") else "full",
        "seed": seed,
        "checkpoint": _checkpoint(),
        "max_duration": body.max_duration,
        "created_at": time.time(),
        "space_id": body.space_id,
        "interpretation": _interpretation(body.interpretation),
        "realaudio": 1 if body.realaudio else 0,
        "normalise": 1 if body.normalise else 0,
        "identity_id": body.identity_id or body.persona_id,
        "persona_id": body.identity_id or body.persona_id,
        "voice_lora": body.voice_lora,
        "voice_lora_strength": body.voice_lora_strength,
        "voice_lora_clip": body.voice_lora_clip,
        **_style_lora_of(body),
        **adv,
    }
    execute(
        """INSERT INTO takes(id, source_id, title, style, lyrics, abc, mode, seed, checkpoint, max_duration, status, created_at,
                             space_id, interpretation, realaudio, normalise, identity_id, persona_id, voice_lora, voice_lora_strength, voice_lora_clip,
                             style_lora, style_lora_model, style_lora_clip,
                             sampler_steps, avoid, target_key, target_bpm, max_abc_tokens,
                             chord_hold_limit, chord_outside_bonus, chord_sections, follow_structure, target_lufs, fade_out_seconds)
           VALUES(:id, :source_id, :title, :style, :lyrics, :abc, :mode, :seed, :checkpoint, :max_duration, 'queued', :created_at,
                  :space_id, :interpretation, :realaudio, :normalise, :identity_id, :persona_id, :voice_lora, :voice_lora_strength, :voice_lora_clip,
                  :style_lora, :style_lora_model, :style_lora_clip,
                  :sampler_steps, :avoid, :target_key, :target_bpm, :max_abc_tokens,
                  :chord_hold_limit, :chord_outside_bonus, :chord_sections, :follow_structure, :target_lufs, :fade_out_seconds)""",
        record,
    )
    if record["mode"] == "full" and not record["abc"]:
        log.info("render queued with an empty score; the engine will write its own chords")
    await QUEUE.put({"kind": "render", "id": take_id})
    log.info("Queued cover render for '%s' (%s, mode=%s, seed=%d)", record["title"], take_id, record["mode"], record["seed"])
    return {**record, "status": "queued"}


@app.post("/api/songs")
async def create_song(body: SongIn) -> dict:
    _gpu_free_for_rendering()
    """Plan a song from style and lyrics alone. The take lands in the planned state."""
    if not body.lyrics.strip():
        raise HTTPException(400, "write some lyrics first. The planner needs words to shape the melody.")
    title = (body.title or "").strip() or guess_title(body.lyrics) or "Untitled song"
    return await _plan_new_take("song", title, body.lyrics, body)


@app.post("/api/instrumentals")
async def create_instrumental(body: InstrumentalIn) -> dict:
    """Plan an instrumental from style and structure.  Its structure is kept where a
    song keeps its lyrics, so replan, render and Variations work unchanged."""
    if ENGINE.options_loaded and not ENGINE.options.get("instrumental"):
        raise HTTPException(400, f"The engine cannot make instrumentals: it needs {config.INSTRUMENTAL_LORA} "
                                 "in models/loras. Run scripts/fetch-models.sh.")
    try:
        structure = instrumental.normalise(body.structure)
    except ValueError as exc:
        raise HTTPException(400, f"That structure will not work: {exc}") from exc
    # "varied" was a setting once, and an old page may still send it. It is
    # taken as steady rather than refused, because that is what it renders as.
    if body.feel not in instrumental.FEELS and body.feel != "varied":
        raise HTTPException(400, f"unknown feel: {body.feel}")
    if body.source_id:
        return await _instrumental_from_recording(body)
    title = (body.title or "").strip() or "Untitled instrumental"
    return await _plan_new_take("instrumental", title, structure, body)


def _unsung(abc: str) -> str:
    """A score with a sung melody, as an instrumental plays it: the tune on an instrument."""
    if not instrumental.sings(abc):
        return abc
    played = instrumental.tune_on_instrument(abc)
    sung = instrumental.sings(played)
    if sung:
        raise HTTPException(400, f"this score's sung melody could not be given to an instrument ({sung} notes are "
                                 "left in its Vocal voice), so the instrumental would sing.")
    return played


async def _instrumental_from_recording(body: InstrumentalIn) -> dict:
    """An instrumental played from a recording's score, rendered at once: the score is
    already there, so there is no plan to write.  Its structure is the score's own
    sections, so the render covers the whole score."""
    _gpu_free_for_rendering()
    source = one("SELECT * FROM sources WHERE id = ?", (body.source_id,))
    if not source:
        raise HTTPException(404, "no such recording")
    abc = body.abc if (body.abc or "").strip() else (source["abc"] or "")
    if not abc.strip():
        raise HTTPException(400, "transcribe this recording first. Its score is what the instrumental plays.")
    abc = _unsung(abc)
    _check_score(abc, "instrumental")
    title = (body.title or "").strip() or source["title"] or "Untitled instrumental"
    record = _new_take_record("instrumental", title, instrumental.structure_of(abc), body)
    record.update(source_id=source["id"], abc=abc, auto_render=0)
    _insert_new_take(record)
    await QUEUE.put({"kind": "render", "id": record["id"]})
    log.info("Queued instrumental of recording '%s' for '%s' (%s)", source["title"], title, record["id"])
    return {**record, "status": "queued"}


async def _plan_new_take(kind: str, title: str, words: str, body: SongIn | InstrumentalIn) -> dict:
    record = _new_take_record(kind, title, words, body)
    _insert_new_take(record)
    await QUEUE.put({"kind": "plan", "id": record["id"]})
    log.info("Queued %s plan for '%s' (%s, variety=%s, auto_render=%s)",
             kind, title, record["id"], record["variety"], bool(record["auto_render"]))
    return {**record, "status": "queued"}


def _new_take_record(kind: str, title: str, words: str, body: SongIn | InstrumentalIn) -> dict:
    """A song or an instrumental as it starts out: no score yet, and no recording."""
    _check_harmony(body.harmony)
    _space(body.space_id)
    seed = body.seed if body.seed is not None else int.from_bytes(os.urandom(4), "big")
    return {
        "id": uuid.uuid4().hex[:12],
        "kind": kind,
        "source_id": None,
        "abc": "",
        "title": title,
        "style": body.style.strip() or config.DEFAULT_STYLE,
        "lyrics": words,
        "brief": (getattr(body, "brief", None) or "").strip() or None,
        "mode": "full",
        "seed": seed,
        "checkpoint": _checkpoint(),
        "max_duration": body.max_duration,
        "created_at": time.time(),
        "auto_render": 1 if body.auto_render else 0,
        "variety": body.variety if body.variety in PLAN_VARIETY else "normal",
        "harmony": body.harmony,
        "space_id": body.space_id,
        "interpretation": _interpretation(body.interpretation),
        "feel": getattr(body, "feel", "steady"),
        "realaudio": 1 if getattr(body, "realaudio", True) else 0,
        "normalise": 1 if getattr(body, "normalise", False) else 0,
        "identity_id": getattr(body, "identity_id", None) or getattr(body, "persona_id", None),
        "persona_id": getattr(body, "identity_id", None) or getattr(body, "persona_id", None),
        "voice_lora": getattr(body, "voice_lora", None),
        "voice_lora_strength": getattr(body, "voice_lora_strength", 1.0),
        "voice_lora_clip": getattr(body, "voice_lora_clip", 0.0),
        **_style_lora_of(body),
        **_advanced_of(body),
    }


def _insert_new_take(record: dict) -> None:
    execute(
        """INSERT INTO takes(id, kind, source_id, title, style, lyrics, brief, abc, mode, seed, checkpoint,
                             max_duration, status, created_at, auto_render, variety, harmony, space_id, interpretation, feel, realaudio,
                             normalise, identity_id, persona_id, voice_lora, voice_lora_strength, voice_lora_clip,
                             style_lora, style_lora_model, style_lora_clip,
                             sampler_steps, avoid, target_key, target_bpm, max_abc_tokens,
                             chord_hold_limit, chord_outside_bonus, chord_sections, follow_structure, target_lufs, fade_out_seconds)
           VALUES(:id, :kind, :source_id, :title, :style, :lyrics, :brief, :abc, :mode, :seed, :checkpoint,
                  :max_duration, 'queued', :created_at, :auto_render, :variety, :harmony, :space_id, :interpretation, :feel, :realaudio,
                  :normalise, :identity_id, :persona_id, :voice_lora, :voice_lora_strength, :voice_lora_clip,
                  :style_lora, :style_lora_model, :style_lora_clip,
                  :sampler_steps, :avoid, :target_key, :target_bpm, :max_abc_tokens,
                  :chord_hold_limit, :chord_outside_bonus, :chord_sections, :follow_structure, :target_lufs, :fade_out_seconds)""",
        record,
    )


# ------------------------------------------------------------------------ spaces
def _space(space_id: str) -> dict:
    space = one("SELECT * FROM spaces WHERE id = ?", (space_id,))
    if not space:
        raise HTTPException(404, "that space no longer exists. Choose another.")
    return space


def _space_name(name: str, keep: str | None = None) -> str:
    """A trimmed name no other space already has, ignoring case."""
    name = " ".join(name.split())
    if not name:
        raise HTTPException(400, "give the space a name")
    clash = one("SELECT id FROM spaces WHERE lower(name) = lower(?) AND id IS NOT ?", (name, keep))
    if clash:
        raise HTTPException(409, f"there is already a space called {name}")
    return name


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> Response:
    """Yeufonic as an MCP server (app/mcp.py), over the app's own routes."""
    if get_setting("mcp.enabled", "off") != "on":
        return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {
            "code": -32000, "message": "The MCP server is off. Turn it on in Settings, under MCP server."}}, status_code=503)
    try:
        message = await request.json()
    except ValueError:
        return JSONResponse(mcp.error_reply(None, -32700, "not JSON"), status_code=400)

    async def api(method: str, path: str, json: dict | None = None, params: dict | None = None):
        # In-process, with this app's own host name, so every route's checks apply as they do for the page.
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost") as client:
            reply = await client.request(method, path, json=json, params=params)
        if reply.status_code >= 400:
            try:
                detail = reply.json().get("detail", reply.text)
            except ValueError:
                detail = reply.text
            raise mcp.ApiRefused(detail if isinstance(detail, str) else str(detail))
        return reply.json() if reply.content else {}

    base = str(request.base_url).rstrip("/")          # how this client reached the app, for links it can open
    batch = message if isinstance(message, list) else [message]
    replies = [r for r in [await mcp.handle(item, api, config.VERSION, base) for item in batch] if r is not None]
    if not replies:
        return Response(status_code=202)
    return JSONResponse(replies if isinstance(message, list) else replies[0])


@app.get("/mcp")
def mcp_stream() -> Response:
    """No server-initiated stream: a client that asks for one is told so, as the protocol allows."""
    return Response(status_code=405, headers={"Allow": "POST"})


@app.get("/api/spaces")
def list_spaces() -> list[dict]:
    """Default first, then by name, each with how many takes it holds."""
    return rows(
        """SELECT s.id, s.name, s.created_at, COUNT(t.id) AS takes, MAX(t.created_at) AS last_take_at
           FROM spaces s LEFT JOIN takes t ON t.space_id = s.id
           GROUP BY s.id ORDER BY s.id != ?, lower(s.name)""",
        (DEFAULT_SPACE,),
    )


@app.post("/api/spaces")
def create_space(body: SpaceIn) -> dict:
    space = {"id": uuid.uuid4().hex[:12], "name": _space_name(body.name), "created_at": time.time()}
    execute("INSERT INTO spaces(id, name, created_at) VALUES(:id, :name, :created_at)", space)
    return {**space, "takes": 0, "last_take_at": None}


@app.put("/api/spaces/{space_id}")
def rename_space(space_id: str, body: SpaceIn) -> dict:
    _space(space_id)
    name = _space_name(body.name, keep=space_id)
    execute("UPDATE spaces SET name = ? WHERE id = ?", (name, space_id))
    return {"id": space_id, "name": name}


@app.delete("/api/spaces/{space_id}")
def delete_space(space_id: str) -> dict:
    """Deleting a space never deletes takes: they move to Default."""
    if space_id == DEFAULT_SPACE:
        raise HTTPException(400, "the Default space cannot be deleted")
    _space(space_id)
    moved = execute("UPDATE takes SET space_id = ? WHERE space_id = ?", (DEFAULT_SPACE, space_id))
    execute("DELETE FROM spaces WHERE id = ?", (space_id,))
    return {"deleted": True, "moved": moved}


@app.post("/api/takes/{take_id}/move")
def move_take(take_id: str, body: MoveIn) -> dict:
    space = _space(body.space_id)
    if not execute("UPDATE takes SET space_id = ? WHERE id = ?", (space["id"], take_id)):
        raise HTTPException(404, "no such take")
    return {"space_id": space["id"], "name": space["name"]}


def _check_harmony(step: int | None) -> None:
    if step and ENGINE.options_loaded and not ENGINE.options.get("harmony"):
        raise HTTPException(400, "The engine has no harmony node, so Harmony must stay at Familiar. "
                                 "Rebuild the engine: docker compose up -d --build engine")


def _idle_take(take_id: str) -> dict:
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    if take["status"] in ACTIVE:
        raise HTTPException(409, "this take is already queued or running. Cancel it first.")
    return take


def _render_settings(take: dict, body: RenderIn | None) -> dict:
    """The style, length cap, mode and style LoRA a render asks for, each falling
    back to the take's own when the request leaves it out."""
    got = {
        "style": take["style"],
        "max_duration": take["max_duration"],
        "mode": take["mode"],
        "style_lora": take.get("style_lora"),
        "style_lora_model": take.get("style_lora_model", 1.0),
        "style_lora_clip": take.get("style_lora_clip", 1.0),
    }
    if body is None:
        return got
    if body.style is not None:
        got["style"] = body.style.strip() or config.DEFAULT_STYLE
    if body.max_duration is not None:
        got["max_duration"] = body.max_duration
    if body.mode is not None:
        got["mode"] = body.mode if body.mode in ("full", "melody") else "full"
    if body.style_lora is not None:
        got.update(_style_lora_of(body))
    return got


@app.post("/api/takes/{take_id}/render")
async def render_take(take_id: str, body: RenderIn | None = None) -> dict:
    _gpu_free_for_rendering()
    """Render a take that already has a score, optionally in another interpretation."""
    take = _idle_take(take_id)
    if not (take["abc"] or "").strip():
        raise HTTPException(400, "this take has no score yet. Write a plan first.")
    _check_score(take["abc"], take["kind"])
    if take["kind"] == "instrumental" and take.get("source_id"):
        # An edit to the score may have given it a sung melody, or changed its sections.
        abc = _unsung(take["abc"])
        execute("UPDATE takes SET abc = ?, lyrics = ? WHERE id = ?", (abc, instrumental.structure_of(abc), take_id))
    elif take["kind"] == "instrumental":
        # A planned instrumental whose sections were rearranged in the editor: the tags follow the score.
        following = instrumental.structure_following(take["lyrics"], take["abc"])
        if following:
            execute("UPDATE takes SET lyrics = ? WHERE id = ?", (following, take_id))
    _checkpoint()
    interpretation = take["interpretation"] if body is None or body.interpretation is None else _interpretation(body.interpretation)
    realaudio = take["realaudio"] if body is None or body.realaudio is None else (1 if body.realaudio else 0)
    normalise = take.get("normalise", 0) if body is None or body.normalise is None else (1 if body.normalise else 0)
    identity_val = None
    if body is not None:
        identity_val = body.identity_id or body.persona_id
    if identity_val is None:
        identity_val = take.get("identity_id") or take.get("persona_id")
    voice_lora = take.get("voice_lora") if body is None or body.voice_lora is None else (body.voice_lora or None)
    voice_lora_strength = take.get("voice_lora_strength", 1.0) if body is None or body.voice_lora_strength is None else body.voice_lora_strength
    sl = _render_settings(take, body)
    adv = _advanced_of(body, fallback=take)
    # The locks are on the score itself, so the Score the person reads is the one that is sung.
    stored = one("SELECT abc FROM takes WHERE id = ?", (take_id,))["abc"] or ""
    locked = _locked_score(stored, adv)
    if locked != stored:
        execute("UPDATE takes SET abc = ? WHERE id = ?", (locked, take_id))
    if body is not None and body.seed is not None:
        seed = body.seed
    elif body is not None and body.reseed:
        seed = int.from_bytes(os.urandom(4), "big")
    else:
        seed = take["seed"]
    execute("UPDATE takes SET status = 'queued', error = NULL, stage = NULL, checkpoint = ?, interpretation = ?, realaudio = ?, normalise = ?, identity_id = ?, persona_id = ?, voice_lora = ?, voice_lora_strength = ?, style_lora = ?, style_lora_model = ?, style_lora_clip = ?, style = ?, max_duration = ?, mode = ?, seed = ?, sound_seed = ?, vocal_check = NULL, loudness = NULL, sampler_steps = ?, avoid = ?, target_key = ?, target_bpm = ?, max_abc_tokens = ?, chord_hold_limit = ?, chord_outside_bonus = ?, chord_sections = ?, follow_structure = ?, target_lufs = ?, fade_out_seconds = ? WHERE id = ?",
            (config.CHECKPOINT, interpretation, realaudio, normalise, identity_val, identity_val, voice_lora, voice_lora_strength, sl["style_lora"], sl["style_lora_model"], sl["style_lora_clip"],
             sl["style"], sl["max_duration"], sl["mode"], seed,
             take.get("sound_seed") if seed == take["seed"] else None,
             adv["sampler_steps"], adv["avoid"], adv["target_key"], adv["target_bpm"], adv["max_abc_tokens"],
             adv["chord_hold_limit"], adv["chord_outside_bonus"], adv["chord_sections"], adv["follow_structure"], adv["target_lufs"], adv["fade_out_seconds"], take_id))
    await QUEUE.put({"kind": "render", "id": take_id})
    log.info("Queued audio render for take '%s' (%s, seed=%d)", take.get("title") or take_id, take_id, seed)
    return {"queued": True, "seed": seed}


@app.post("/api/takes/{take_id}/clear")
def clear_take(take_id: str) -> dict:
    """Drop a stale failure.  A take interrupted by a restart keeps its audio and its
    score, so it can go back to the state it already reached without another job."""
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    if take["status"] != "failed":
        raise HTTPException(409, "this take has not failed")
    audio = take["audio_path"]
    if audio and Path(audio).exists():
        status = "done"
    elif (take["abc"] or "").strip():
        status = "planned"
    else:
        raise HTTPException(400, "this take has nothing to keep. Delete it, or write a plan.")
    execute("UPDATE takes SET status = ?, error = NULL, stage = NULL WHERE id = ?", (status, take_id))
    return {"status": status}


@app.post("/api/takes/{take_id}/replan")
async def replan_take(take_id: str, body: ReplanIn | None = None) -> dict:
    """Write a fresh score plan for the same lyrics and style, optionally with a
    different plan variety or harmony."""
    take = _idle_take(take_id)
    if take.get("source_id"):
        raise HTTPException(400, "this take's score is its recording's transcription, so there is no plan to write again.")
    body = body or ReplanIn()
    _check_harmony(body.harmony)
    variety = body.variety if body.variety in PLAN_VARIETY else take["variety"]
    harmony = take["harmony"] if body.harmony is None else body.harmony
    adv = _advanced_of(body, fallback=take)
    seed = int.from_bytes(os.urandom(4), "big")
    execute(
        """UPDATE takes SET seed = ?, sound_seed = NULL, abc = '', status = 'queued', error = NULL, stage = NULL,
                            variety = ?, harmony = ?, checkpoint = ?,
                            sampler_steps = ?, avoid = ?, target_key = ?, target_bpm = ?, max_abc_tokens = ?,
                            chord_hold_limit = ?, chord_outside_bonus = ?, chord_sections = ?, follow_structure = ?, target_lufs = ?, fade_out_seconds = ?
           WHERE id = ?""",
        (seed, variety, harmony, config.CHECKPOINT,
         adv["sampler_steps"], adv["avoid"], adv["target_key"], adv["target_bpm"], adv["max_abc_tokens"],
         adv["chord_hold_limit"], adv["chord_outside_bonus"], adv["chord_sections"], adv["follow_structure"], adv["target_lufs"], adv["fade_out_seconds"], take_id),
    )
    await QUEUE.put({"kind": "plan", "id": take_id})
    log.info("Queued replan for take '%s' (%s, variety=%s, harmony=%s, seed=%d)",
             take.get("title") or take_id, take_id, variety, harmony, seed)
    return {"queued": True, "seed": seed}


TRY_TAIL = re.compile(r"try \d+|planner \d+\.\d\d")


def _base_title(title: str) -> str:
    """'Night drive · Tight' -> 'Night drive', so a variation of a variation is not 'X · Tight · Loose'."""
    head, sep, tail = title.rpartition(" \u00b7 ")
    known = tail in INTERPRETATION_NAMES.values() or tail in ("new voice", "sung again", "new words", "instrumental")
    return head if sep and (known or TRY_TAIL.fullmatch(tail)) else title


# What Sing again leaves behind: the copy is a new take with its own audio and state.
_REVOICE_FRESH = {"id", "title", "status", "stage", "error", "audio_path", "duration", "prompt_id", "created_at",
                  "finished_at", "elapsed", "favourite", "vocal_check", "loudness", "sound_seed", "normalised",
                  "normalised_to", "weak_dismissed", "note_dismissed"}


@app.post("/api/takes/{take_id}/revoice")
async def revoice(take_id: str) -> dict:
    """The same score sung again: a new take beside the original with a new seed.

    The voice lives in what the note stage writes, not in the decoder's noise: a copy
    that kept the seed and drew only new noise came back sounding the same.  A new seed
    sings the same score with a different voice and slightly different phrasing."""
    _gpu_free_for_rendering()
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    if not (take["abc"] or "").strip():
        raise HTTPException(400, "this take has no score to render again. Write a plan first.")
    _check_score(take["abc"], take["kind"])
    _checkpoint()
    record = {key: value for key, value in take.items() if key not in _REVOICE_FRESH}
    seed = int.from_bytes(os.urandom(4), "big")
    record.update(id=uuid.uuid4().hex[:12], title=f"{_base_title(take['title'])} \u00b7 sung again",
                  status="queued", created_at=time.time(), checkpoint=config.CHECKPOINT, seed=seed, sound_seed=None)
    columns = list(record)
    execute(f"INSERT INTO takes({', '.join(columns)}) VALUES({', '.join(':' + c for c in columns)})", record)
    await QUEUE.put({"kind": "render", "id": record["id"]})
    log.info("Queued Sing again for take '%s' (%s -> %s, seed %d)", take.get("title") or take_id,
             take_id, record["id"], seed)
    return {"id": record["id"], "title": record["title"], "seed": seed}


class InstrumentalOfIn(BaseModel):
    title: str | None = Field(None, max_length=200)
    # The score as the editor holds it, so an edit goes into the instrumental and the original keeps its own.
    abc: str | None = Field(None, max_length=200_000)


@app.post("/api/takes/{take_id}/instrumental")
async def instrumental_of_take(take_id: str, body: InstrumentalOfIn | None = None) -> dict:
    """The same score as an instrumental: a new take beside the original, which is left as it was.

    Emptying a song's Vocal voice by hand is not enough, because the render still sings the words it is given.  What
    works is the instrumental path: the sung melody moved to an instrument (as for a recording), the score's section
    tags in place of words, the instrumental LoRA, and a style without its vocal descriptions."""
    _gpu_free_for_rendering()
    if ENGINE.options_loaded and not ENGINE.options.get("instrumental"):
        raise HTTPException(400, f"The engine cannot make instrumentals: it needs {config.INSTRUMENTAL_LORA} "
                                 "in models/loras. Run scripts/fetch-models.sh.")
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    if take["kind"] == "instrumental":
        raise HTTPException(400, "this take is an instrumental already")
    given = body.abc if body is not None and (body.abc or "").strip() else None
    abc = given or take["abc"] or ""
    if not abc.strip():
        raise HTTPException(400, "this take has no score yet. Write a plan first.")
    abc = _unsung(abc)
    _check_score(abc, "instrumental")
    _checkpoint()
    record = {key: value for key, value in take.items() if key not in _REVOICE_FRESH}
    title = " ".join(((body.title if body else "") or "").split()) or f"{_base_title(take['title'])} \u00b7 instrumental"
    record.update(id=uuid.uuid4().hex[:12], kind="instrumental", title=title, abc=abc, lyrics=instrumental.structure_of(abc),
                  style=instrumental.without_vocal_tags(take["style"]) or take["style"], status="queued", created_at=time.time(),
                  checkpoint=config.CHECKPOINT, sound_seed=None, auto_render=0, mode="full",
                  identity_id=None, persona_id=None, voice_lora=None, voice_lora_strength=1.0, voice_lora_clip=0.0)
    columns = list(record)
    execute(f"INSERT INTO takes({', '.join(columns)}) VALUES({', '.join(':' + c for c in columns)})", record)
    await QUEUE.put({"kind": "render", "id": record["id"]})
    log.info("Queued an instrumental of take '%s' (%s -> %s)", take.get("title") or take_id, take_id, record["id"])
    return {"id": record["id"], "title": title, "seed": record["seed"]}


@app.post("/api/takes/{take_id}/words")
async def new_words(take_id: str, body: WordsIn) -> dict:
    """The same score sung with other words: a new take beside the original, with its seed.

    The planner reads every word before it writes a note, so a plan for changed words
    is a new tune, even with the same seed.  The render takes the score and the words
    separately, so a score already liked keeps its melody, key and tempo this way."""
    _gpu_free_for_rendering()
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    if take["kind"] == "instrumental":
        raise HTTPException(400, "an instrumental has no words to change")
    words = body.lyrics.replace("\r\n", "\n")
    if not words.strip():
        raise HTTPException(400, "write some lyrics first")
    abc = take["abc"] if body.abc is None else body.abc
    if not (abc or "").strip():
        raise HTTPException(400, "this take has no score to sing. Write a plan first.")
    if body.abc is None and words and abc and ("\nw: " in abc or "\nw:" in abc or "\nW: " in abc) and ("V: Vocal" in abc or "V:Vocal" in abc):
        try:
            abc = aligner.align_lyrics_to_abc(abc, words)
        except Exception as exc:
            log.warning("Could not auto-align lyrics to ABC for new words: %s", exc)
    _check_score(abc, take["kind"])
    _checkpoint()
    record = {key: value for key, value in take.items() if key not in _REVOICE_FRESH}
    if body.brief is not None:
        record["brief"] = body.brief.strip() or None
    title = " ".join((body.title or "").split())
    if not title or title == take["title"]:
        title = f"{_base_title(take['title'])} \u00b7 new words"
    if body.seed is not None:
        seed = body.seed
    elif body.reseed:
        seed = int.from_bytes(os.urandom(4), "big")
    else:
        seed = take["seed"]
    record.update(id=uuid.uuid4().hex[:12], title=title, lyrics=words, abc=abc, status="queued",
                  created_at=time.time(), checkpoint=config.CHECKPOINT, seed=seed,
                  sound_seed=take.get("sound_seed") if seed == take["seed"] else None)
    record.update(_render_settings(take, body))
    record.update(_advanced_of(body, fallback=take))
    if body.interpretation is not None:
        record["interpretation"] = _interpretation(body.interpretation)
    if body.realaudio is not None:
        record["realaudio"] = 1 if body.realaudio else 0
    if body.normalise is not None:
        record["normalise"] = 1 if body.normalise else 0
    columns = list(record)
    execute(f"INSERT INTO takes({', '.join(columns)}) VALUES({', '.join(':' + c for c in columns)})", record)
    await QUEUE.put({"kind": "render", "id": record["id"]})
    log.info("Queued new words for take '%s' (%s -> %s, seed %d)", take.get("title") or take_id,
             take_id, record["id"], seed)
    return {"id": record["id"], "title": record["title"], "seed": seed}


@app.post("/api/takes/{take_id}/rearrange")
async def rearrange(take_id: str, body: RearrangeIn) -> dict:
    """Render a take's score as a new take beside it, which leaves the original with its own score
    and audio.  An instrumental's section tags follow the score."""
    _gpu_free_for_rendering()
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    if take["kind"] == "cover":
        raise HTTPException(400, "a cover is made again from its recording, not from a score")
    if not (body.abc or "").strip():
        raise HTTPException(400, "this take has no score to render. Write a plan first.")
    _check_score(body.abc, take["kind"])
    _checkpoint()
    record = {key: value for key, value in take.items() if key not in _REVOICE_FRESH}
    # The title is the person's: a new render of a take keeps it.
    title = " ".join((body.title or "").split()) or take["title"]
    if body.seed is not None:
        seed = body.seed
    elif body.reseed:
        seed = int.from_bytes(os.urandom(4), "big")
    else:
        seed = take["seed"]
    abc, lyrics = body.abc, take["lyrics"]
    if take["kind"] == "instrumental" and take.get("source_id"):
        # An edit to a recording's score may have given it a sung melody, or changed its sections.
        abc = _unsung(abc)
        lyrics = instrumental.structure_of(abc)
    elif take["kind"] == "instrumental":
        lyrics = instrumental.structure_following(take["lyrics"], abc) or take["lyrics"]
    record.update(id=uuid.uuid4().hex[:12], title=title, abc=abc, status="queued", created_at=time.time(),
                  lyrics=lyrics, checkpoint=config.CHECKPOINT, seed=seed,
                  sound_seed=take.get("sound_seed") if seed == take["seed"] else None)
    record.update(_render_settings(take, body))
    record.update(_advanced_of(body, fallback=take))
    # The locks are on the score itself, as for a take rendered in place.
    record["abc"] = _locked_score(record["abc"], record)
    if body.interpretation is not None:
        record["interpretation"] = _interpretation(body.interpretation)
    if body.realaudio is not None:
        record["realaudio"] = 1 if body.realaudio else 0
    if body.normalise is not None:
        record["normalise"] = 1 if body.normalise else 0
    columns = list(record)
    execute(f"INSERT INTO takes({', '.join(columns)}) VALUES({', '.join(':' + c for c in columns)})", record)
    await QUEUE.put({"kind": "render", "id": record["id"]})
    log.info("Queued a rearranged score for take '%s' (%s -> %s, seed %d)", take.get("title") or take_id,
             take_id, record["id"], seed)
    return {"id": record["id"], "title": record["title"], "seed": seed}


@app.post("/api/takes/{take_id}/variations")
async def variations(take_id: str, body: VariationsIn) -> dict:
    _gpu_free_for_rendering()
    """Render the same score and seed once in each chosen interpretation.  Each is a
    new take beside the original, titled with its interpretation."""
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    if not (take["abc"] or "").strip():
        raise HTTPException(400, "this take has no score to render again. Write a plan first.")
    _check_score(take["abc"], take["kind"])
    _checkpoint()
    wanted = list(dict.fromkeys(_interpretation(name) for name in body.interpretations))
    base = _base_title(take["title"])
    now = time.time()
    created = []
    realaudio = take.get("realaudio", 0) if body.realaudio is None else (1 if body.realaudio else 0)
    normalise = take.get("normalise", 0) if body.normalise is None else (1 if body.normalise else 0)
    identity_val = (body.identity_id or body.persona_id) if (body.identity_id is not None or body.persona_id is not None) else (take.get("identity_id") or take.get("persona_id"))
    voice_lora = take.get("voice_lora") if body.voice_lora is None else (body.voice_lora or None)
    voice_lora_strength = take.get("voice_lora_strength", 1.0) if body.voice_lora_strength is None else body.voice_lora_strength
    for offset, name in enumerate(wanted):
        record = {
            "id": uuid.uuid4().hex[:12], "kind": take["kind"], "source_id": take["source_id"],
            "title": f"{base} \u00b7 {INTERPRETATION_NAMES[name]}", "style": take["style"], "lyrics": take["lyrics"],
            "abc": take["abc"], "mode": take["mode"], "seed": take["seed"], "checkpoint": config.CHECKPOINT,
            "max_duration": body.max_duration or take["max_duration"], "created_at": now + offset * 0.001,
            "variety": take["variety"],
            "harmony": take["harmony"], "space_id": take["space_id"], "interpretation": name, "feel": take["feel"],
            "realaudio": realaudio, "normalise": normalise, "identity_id": identity_val, "persona_id": identity_val,
            "voice_lora": voice_lora, "voice_lora_strength": voice_lora_strength,
            "voice_lora_clip": take.get("voice_lora_clip", 0.0),
            "style_lora": take.get("style_lora"),
            "style_lora_model": take.get("style_lora_model", 1.0),
            "style_lora_clip": take.get("style_lora_clip", 1.0),
            "sound_seed": take.get("sound_seed"),
            "sampler_steps": take.get("sampler_steps", 32),
            "avoid": take.get("avoid"),
            "target_key": take.get("target_key"),
            "target_bpm": take.get("target_bpm"),
            "max_abc_tokens": take.get("max_abc_tokens", 8192),
            "chord_hold_limit": take.get("chord_hold_limit", 8),
            "chord_outside_bonus": take.get("chord_outside_bonus", 0.0),
            "chord_sections": take.get("chord_sections"),
            "follow_structure": take.get("follow_structure"),
            "target_lufs": take.get("target_lufs", -14.0),
            "fade_out_seconds": take.get("fade_out_seconds", 3.0),
        }
        execute(
            """INSERT INTO takes(id, kind, source_id, title, style, lyrics, abc, mode, seed, checkpoint, max_duration,
                                 status, created_at, variety, harmony, space_id, interpretation, feel, realaudio, normalise,
                                 identity_id, persona_id, voice_lora, voice_lora_strength, voice_lora_clip,
                                 style_lora, style_lora_model, style_lora_clip, sound_seed,
                                 sampler_steps, avoid, target_key, target_bpm, max_abc_tokens,
                                 chord_hold_limit, chord_outside_bonus, chord_sections, follow_structure, target_lufs, fade_out_seconds)
               VALUES(:id, :kind, :source_id, :title, :style, :lyrics, :abc, :mode, :seed, :checkpoint, :max_duration,
                      'queued', :created_at, :variety, :harmony, :space_id, :interpretation, :feel, :realaudio, :normalise,
                      :identity_id, :persona_id, :voice_lora, :voice_lora_strength, :voice_lora_clip,
                      :style_lora, :style_lora_model, :style_lora_clip, :sound_seed,
                      :sampler_steps, :avoid, :target_key, :target_bpm, :max_abc_tokens,
                      :chord_hold_limit, :chord_outside_bonus, :chord_sections, :follow_structure, :target_lufs, :fade_out_seconds)""",
            record,
        )
        await QUEUE.put({"kind": "render", "id": record["id"]})
        created.append({"id": record["id"], "title": record["title"], "interpretation": name})
    log.info("Queued %d variations for take '%s' (%s)", len(created), take.get("title") or take_id, take_id)
    return {"created": created}


# ---------------------------------------------------------------- sounds for the score preview
@app.get("/soundfonts/{instrument}-mp3/{note}.mp3")
def soundfont_note(instrument: str, note: str) -> Response:
    """One note sample, for abcjs.  404 when the sounds have not been fetched."""
    path = soundfonts.sample(instrument, note)
    if not path:
        raise HTTPException(404, "no such sample")
    return FileResponse(path, media_type="audio/mpeg", headers={"Cache-Control": "public, max-age=31536000, immutable"})


@app.get("/api/soundfonts")
def soundfonts_status() -> dict:
    have = soundfonts.installed()
    return {"installed": have, "available": [{"id": key, "name": name} for key, name in soundfonts.SETS.items()],
            # How far each set that is here can play, so the preview can shift a score
            # into it: the sets are not all the same size.
            "ranges": {name: soundfonts.range_of(name) for name in have},
            "megabytes": 7, "ready": bool(have)}


@app.post("/api/soundfonts/{instrument}/download")
async def soundfonts_download(instrument: str) -> dict:
    """Fetch an instrument's samples from their upstream home.  Only when asked."""
    if instrument not in soundfonts.SETS:
        raise HTTPException(404, "no such instrument")
    try:
        fetched = await asyncio.to_thread(soundfonts.download, instrument)
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not fetch the %s samples: %s", instrument, exc)
        raise HTTPException(502, f"could not fetch the sounds ({exc.__class__.__name__}). Check the connection and try again.") from exc
    return {"fetched": fetched, "installed": soundfonts.installed()}


class SoundFontSelectIn(BaseModel):
    filename: str


@app.get("/api/soundfonts/sf2")
def list_soundfonts_sf2() -> dict:
    available = soundfonts.available_sf2()
    selected = soundfonts.get_active_sf2()
    return {
        "soundfonts": available,
        "selected": selected,
        "available": len(available) > 0,
    }


@app.post("/api/soundfonts/sf2/select")
def select_soundfont_sf2(body: SoundFontSelectIn) -> dict:
    soundfonts.set_active_sf2(body.filename)
    return {
        "status": "ok",
        "selected": soundfonts.get_active_sf2(),
    }


class ScoreRenderIn(BaseModel):
    midi_base64: str | None = None
    sf2: str | None = None
    title: str = "score"


@app.post("/api/score/render-sf2")
async def render_score_sf2(body: ScoreRenderIn) -> dict:
    available = soundfonts.available_sf2()
    if not available:
        return {
            "status": "unavailable",
            "detail": "No SoundFont (.sf2) files found in data/models/soundfonts/sf2.",
            "available": [],
        }

    active_sf2 = body.sf2 or soundfonts.get_active_sf2()
    if not active_sf2 or not (soundfonts.sf2_folder() / active_sf2).is_file():
        return {
            "status": "unavailable",
            "detail": f"SoundFont '{active_sf2}' is not available.",
            "available": [s["filename"] for s in available],
        }

    if not body.midi_base64:
        raise HTTPException(400, "No MIDI data provided")

    import base64, hashlib
    try:
        midi_bytes = base64.b64decode(body.midi_base64)
    except Exception as exc:
        raise HTTPException(400, f"Invalid base64 MIDI: {exc}")

    if not midi_bytes:
        raise HTTPException(400, "Empty MIDI data provided")

    content_hash = hashlib.sha256(midi_bytes + active_sf2.encode("utf-8")).hexdigest()[:16]
    out_dir = config.WORK_DIR / "score_renders"
    out_dir.mkdir(parents=True, exist_ok=True)
    flac_path = out_dir / f"{content_hash}.flac"
    midi_path = out_dir / f"{content_hash}.mid"

    if not flac_path.exists() or flac_path.stat().st_size == 0:
        midi_path.write_bytes(midi_bytes)
        try:
            await asyncio.to_thread(soundfonts.render_midi_to_audio, midi_path, flac_path, active_sf2)
        except Exception as exc:
            log.exception("Failed to render score audio with SF2 %s", active_sf2)
            raise HTTPException(500, f"SoundFont synthesis failed: {exc}")

    peaks = library.ensure_peaks(flac_path)
    return {
        "status": "ok",
        "audio_url": f"/api/score/rendered-audio/{content_hash}",
        "peaks_url": f"/api/score/rendered-audio/{content_hash}/peaks",
        "soundfont": active_sf2,
        "key": content_hash,
        "has_peaks": peaks is not None,
    }


@app.get("/api/score/rendered-audio/{key}")
def score_rendered_audio_file(key: str) -> FileResponse:
    if not re.fullmatch(r"[a-f0-9]{16}", key):
        raise HTTPException(400, "invalid key")
    flac_path = config.WORK_DIR / "score_renders" / f"{key}.flac"
    if not flac_path.exists():
        raise HTTPException(404, "rendered audio not found")
    return FileResponse(flac_path, filename=f"score-{key}.flac", media_type="audio/flac")


@app.get("/api/score/rendered-audio/{key}/peaks")
def score_rendered_audio_peaks(key: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{16}", key):
        raise HTTPException(400, "invalid key")
    flac_path = config.WORK_DIR / "score_renders" / f"{key}.flac"
    if not flac_path.exists():
        raise HTTPException(404, "rendered audio not found")
    peaks = library.ensure_peaks(flac_path)
    if not peaks:
        return {"columns": 128, "peaks": [0.0] * 128, "rms": [0.0] * 128}
    return peaks



class TriesIn(BaseModel):
    mode: Literal["seeds", "planner"] = "seeds"
    count: int = Field(4, ge=1, le=8)                                   # new seeds
    planner: list[float] = Field(default_factory=list, max_length=8)   # planner strengths to try
    max_duration: float | None = Field(None, ge=10, le=900)


def _next_try(base: str, space_id: str) -> int:
    """The number after the highest 'try N' this take's title has in its space."""
    pattern = re.compile(re.escape(base) + r" \u00b7 try (\d+)")
    seen = [int(m.group(1)) for r in rows("SELECT title FROM takes WHERE space_id = ? AND title LIKE ?",
                                          (space_id, base.replace("%", "").replace("_", "") + "%"))
            if (m := pattern.fullmatch(r["title"]))]
    return max(seen, default=0) + 1


@app.post("/api/takes/{take_id}/tries")
async def tries(take_id: str, body: TriesIn) -> dict:
    """The same score and words rendered again as several new takes: with new seeds, or,
    for a take with a style LoRA that has a planner half, at other planner strengths with
    its own seed.  Which roll suits a song is heard, not predicted (a seed does not carry
    from one set of words to another, and the best planner strength differs per seed), so
    the takes are made together to be listened to together."""
    _gpu_free_for_rendering()
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    if not (take["abc"] or "").strip():
        raise HTTPException(400, "this take has no score to render again. Write a plan first.")
    _check_score(take["abc"], take["kind"])
    _checkpoint()
    base = _base_title(take["title"])
    specs: list[dict] = []
    if body.mode == "planner":
        if not take.get("style_lora"):
            raise HTTPException(400, "this take has no style LoRA, so it has no planner strength to try.")
        if loras.describe(take["style_lora"], loras.folder())["kind"] in ("decoder", "other"):
            raise HTTPException(400, "this LoRA has no planner half, so there is no planner strength to try.")
        own = float(take.get("style_lora_clip") if take.get("style_lora_clip") is not None else 1.0)
        for value in dict.fromkeys(round(float(v), 2) for v in body.planner):
            if not 0.0 <= value <= 3.0:
                raise HTTPException(400, "a planner strength is between 0 and 3.")
            if abs(value - own) >= 0.005:      # the take's own would repeat it exactly
                specs.append({"title": f"{base} \u00b7 planner {value:.2f}", "seed": take["seed"],
                              "sound_seed": take.get("sound_seed"), "style_lora_clip": value})
        if not specs:
            raise HTTPException(400, "pick at least one planner strength other than this take's own.")
    else:
        first = _next_try(base, take["space_id"])
        for n in range(body.count):
            specs.append({"title": f"{base} \u00b7 try {first + n}", "seed": int.from_bytes(os.urandom(4), "big"),
                          "sound_seed": None})
    now = time.time()
    created = []
    for offset, spec in enumerate(specs):
        record = {key: value for key, value in take.items() if key not in _REVOICE_FRESH}
        record.update(id=uuid.uuid4().hex[:12], status="queued", created_at=now + offset * 0.001,
                      checkpoint=config.CHECKPOINT, max_duration=body.max_duration or take["max_duration"], **spec)
        columns = list(record)
        execute(f"INSERT INTO takes({', '.join(columns)}) VALUES({', '.join(':' + c for c in columns)})", record)
        await QUEUE.put({"kind": "render", "id": record["id"]})
        created.append({"id": record["id"], "title": record["title"], "seed": record["seed"],
                        "style_lora_clip": record.get("style_lora_clip")})
    log.info("Queued %d tries (%s) for take '%s' (%s)", len(created), body.mode, take.get("title") or take_id, take_id)
    return {"created": created}


# ---------------------------------------------------------------------- identities
IDENTITY_STEPS = ("vocals_state", "score_state", "lyrics_state", "style_state")
PERSONA_STEPS = IDENTITY_STEPS


def _identity(identity_id: str) -> dict:
    identity = one("SELECT * FROM identities WHERE id = ?", (identity_id,))
    if not identity:
        raise HTTPException(404, "no such identity")
    return identity


_persona = _identity


def _train_sizing(identity_id: str) -> dict:
    """How much of each song a corpus trains on, from the card as it is now."""
    durations = [r["duration"] for r in rows(
        "SELECT duration FROM identity_songs WHERE identity_id = ? AND include = 1", (identity_id,))]
    return trainsize.for_corpus(durations, ENGINE.gpu())


def _training_cut(song: dict, limit: float) -> dict | None:
    """Where the trainer's length limit (seconds) cuts this song, and the words that stay (#7)."""
    if not song.get("stored_path") or not song.get("duration") or song["duration"] <= limit + 1:
        return None
    folder = Path(song["stored_path"]).parent
    try:
        lines = json.loads((folder / "whisper.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        lines = []
    try:
        abc = (folder / "score.abc").read_text(encoding="utf-8")
    except OSError:
        abc = ""
    return identities.training_cut(lines, identities.score_sections(abc), song["duration"], limit, song["lyrics"] or "")


def _identity_view(identity: dict) -> dict:
    songs = rows("SELECT * FROM identity_songs WHERE identity_id = ? ORDER BY position", (identity["id"],))
    limit = _train_sizing(identity["id"])["minutes"] * 60
    for song in songs:
        try:
            song["lyrics_versions"] = json.loads(song.get("lyrics_versions") or "null")
        except ValueError:
            song["lyrics_versions"] = None
        cut = _training_cut(song, limit) if song["include"] else None
        song["trained_to"] = cut["seconds"] if cut else None
        song["caption"] = identities.caption(identity["trigger_word"], song["description"] or identity["description"],
                                             identity["voice"], song["key"], song["tempo"],
                                             style_hint=song.get("style_hint") or "")
        # Too long to analyse: most likely a whole album, which a cue sheet can split.
        song["too_long"] = identities.too_long(song["duration"])
        if song["too_long"]:
            song["flag"] = song["flag"] or identities.TOO_LONG
            found = identities.cue_for(_song_source(identity, song))
            song["cue"] = {"file": found["cue"], "tracks": len(found["tracks"])} if found else None
    chosen = [s for s in songs if s["include"]]
    busy = any(s[f] in ("queued", "running") for s in songs for f in IDENTITY_STEPS)
    return {**identity, "vocalless": identities.vocalless(identity["voice"]), "songs": songs, "busy": busy,
            "working": jobs.identity_working({s["id"] for s in songs}) if busy else None,
            "exporting": EXPORTING.get(identity["id"]),
            "run_all": _run_all_view(identity["id"]),
            "last_run": _last_run(identity),
            # A LoRA already trained under this corpus's name, for the Train window to ask about.
            "previous_lora": _previous_lora(identity),
            # Redraft marks the sections from the words, which needs the external LLM.
            "external_llm": llm.is_external_enabled(),
            "summary": {"songs": len(songs), "included": len(chosen),
                        "minutes": round(sum(s["duration"] or 0 for s in chosen) / 60, 1),
                        "analysed": sum(1 for s in chosen if all(s[f] == "done" for f in IDENTITY_STEPS)),
                        "checked": sum(1 for s in chosen if s["lyrics_checked"])}}


_persona_view = _identity_view


class CheckpointsDeleteIn(BaseModel):
    names: list[str] = Field(min_length=1, max_length=1000)


def _run_label(run: str, base: str, root: Path | None) -> str:
    """This run, with the day it was trained, or a previous one by its date."""
    if not run:
        path = root / f"{base}.safetensors" if root else None
        if path and path.is_file():
            when = time.localtime(path.stat().st_mtime)
            return f"This run · trained {when.tm_mday} {time.strftime('%b', when)}"
        return "This run"
    when = time.strptime(run[:8], "%Y%m%d")
    return f"Previous run · {when.tm_mday} {time.strftime('%b', when)} {when.tm_year}"


@app.get("/api/identities/{identity_id}/checkpoints")
def identity_checkpoints(identity_id: str) -> dict:
    """The checkpoints this corpus's training runs kept, run by run, with their sizes."""
    identity = one("SELECT * FROM identities WHERE id = ?", (identity_id,))
    if not identity:
        raise HTTPException(404, "no such corpus")
    base, root = _lora_base(identity), loras.folder()
    runs: dict[str, dict] = {}
    for item in loras.checkpoints(base, root):
        run = runs.setdefault(item["run"], {"run": item["run"], "label": _run_label(item["run"], base, root),
                                            "checkpoints": []})
        run["checkpoints"].append(item)
    return {"base": base, "visible": root is not None, "runs": list(runs.values())}


@app.post("/api/identities/{identity_id}/checkpoints/delete")
async def delete_identity_checkpoints(identity_id: str, body: CheckpointsDeleteIn) -> dict:
    """Delete some of this corpus's checkpoints.  Only its own step files: never a
    finished LoRA, and never another corpus's, whatever names are sent."""
    identity = one("SELECT * FROM identities WHERE id = ?", (identity_id,))
    if not identity:
        raise HTTPException(404, "no such corpus")
    active = _training_run()
    if active and active["identity_id"] == identity_id:
        raise HTTPException(409, "this corpus is training. Delete its checkpoints when it has finished.")
    root = loras.folder()
    own = {item["name"]: item for item in loras.checkpoints(_lora_base(identity), root)}
    unknown = [name for name in body.names if name not in own]
    if unknown:
        raise HTTPException(400, f"not a checkpoint of this corpus: {unknown[0]}")
    freed = 0
    try:
        for name in dict.fromkeys(body.names):
            await asyncio.to_thread(loras.remove, name, root)
            freed += own[name]["bytes"]
    except (OSError, ValueError) as exc:
        raise HTTPException(500, f"could not delete a checkpoint: {exc}")
    finally:
        try:
            await ENGINE.refresh_options()
        except Exception as exc:  # noqa: BLE001
            log.warning("the engine's list was not re-read: %s", exc)
    log.info("deleted %d checkpoints of corpus '%s' (%.1f GB)", len(set(body.names)), identity["name"], freed / 1e9)
    return {"deleted": len(set(body.names)), "bytes": freed}


def _previous_lora(identity: dict) -> dict | None:
    base = _lora_base(identity)
    found = loras.previous_run(base, loras.folder())
    return {**found, "name": base, "keep_as": f"{identity['name']} · {found['day']} (previous)"} if found else None


def _song_source(identity: dict, song: dict) -> Path:
    """Where a corpus song is read from: its folder, or the corpus's own tracks folder
    for a track cut from an album (stored by its full path)."""
    return Path(identity["folder"]) / song["file"]


def _clean_trigger(word: str) -> str:
    word = re.sub(r"[^a-z0-9]", "", word.lower())
    if len(word) < 2:
        raise HTTPException(400, "the trigger word needs at least two letters or digits")
    return word


@app.get("/api/import/browse")
def import_browse(path: str | None = None) -> dict:
    try:
        return identities.browse(path)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


class ReclaimIn(BaseModel):
    ids: list[str] = Field(max_length=200)


def _storage_busy() -> storage.Busy:
    return storage.Busy(exporting=set(EXPORTING))


@app.get("/api/storage")
async def storage_report() -> dict:
    """Where the space is and what can be given back, measured now.  A big library takes a few seconds."""
    return await asyncio.to_thread(storage.scan, _storage_busy(), _lora_base)


@app.post("/api/storage/reclaim")
async def storage_reclaim(body: ReclaimIn) -> dict:
    """Remove the named items from the Storage window, and say how much came back."""
    result = await asyncio.to_thread(storage.reclaim, body.ids, _storage_busy(), _lora_base)
    if any(r["id"].startswith("checkpoints:") for r in result["removed"]):
        try:
            await ENGINE.refresh_options()     # the Style LoRA list follows the files
        except Exception as exc:  # noqa: BLE001
            log.warning("the engine's list was not re-read: %s", exc)
    return result


@app.get("/api/storage/compress-vocals")
def storage_compress_state() -> dict:
    return storage.compress_state()


@app.post("/api/storage/compress-vocals")
async def storage_compress_start() -> dict:
    """Convert the corpus vocals that are still WAV to FLAC, in the background."""
    why = _storage_busy().anywhere()
    if why:
        raise HTTPException(409, f"Not now: {why}.")
    if storage.begin_compress():
        asyncio.create_task(asyncio.to_thread(storage.compress_vocals))
    return storage.compress_state()


@app.post("/api/storage/compress-vocals/stop")
def storage_compress_stop() -> dict:
    storage.stop_compress()
    return storage.compress_state()


@app.post("/api/engine/reload-options")
async def reload_engine_options() -> dict:
    """Read the engine's lists again, for a model file that changed by hand."""
    try:
        await ENGINE.refresh_options()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, f"the engine did not answer: {exc}")
    options = ENGINE.options or {}
    return {"checkpoints": len(options.get("checkpoints") or []),
            "loras": len(options.get("loras") or [])}


@app.get("/api/identities")
@app.get("/api/personas", include_in_schema=False)
def list_identities() -> list[dict]:
    return rows("""SELECT i.id, i.name, i.trigger_word, i.voice, i.lora, i.created_at, i.exported_at,
                          COUNT(s.id) AS songs, SUM(s.include) AS included
                   FROM identities i LEFT JOIN identity_songs s ON s.identity_id = i.id
                   GROUP BY i.id ORDER BY i.created_at DESC""")


list_personas = list_identities


@app.post("/api/identities")
@app.post("/api/personas", include_in_schema=False)
async def create_identity(body: IdentityIn) -> dict:
    """Scan a folder of one singer's songs.  The folder is only read."""
    if not body.consent:
        raise HTTPException(400, "confirm that the voice is yours, or that the singer has given permission")
    folder = Path(body.folder)
    try:
        found = await asyncio.to_thread(identities.scan, folder)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not found:
        raise HTTPException(400, "there are no songs in that folder")
    identity_id = uuid.uuid4().hex[:12]
    execute("""INSERT INTO identities(id, name, trigger_word, description, voice, folder, consent, created_at, lora)
               VALUES(?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (identity_id, body.name.strip(), _clean_trigger(body.trigger_word), body.description.strip(),
             body.voice.strip().lower(), str(folder), time.time(), (body.lora or "").strip() or None))
    for position, song in enumerate(found):
        execute("""INSERT INTO identity_songs(id, identity_id, file, title, sha256, duration, bit_rate, include, flag, position)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uuid.uuid4().hex[:12], identity_id, song["file"], song["title"], song["sha256"], song["duration"],
                 song["bit_rate"], 1 if song["include"] else 0, song["flag"], position))
    return _identity_view(_identity(identity_id))


create_persona = create_identity


@app.get("/api/identities/{identity_id}")
@app.get("/api/personas/{identity_id}", include_in_schema=False)
def get_identity(identity_id: str) -> dict:
    return _identity_view(_identity(identity_id))


get_persona = get_identity


@app.put("/api/identities/{identity_id}")
@app.put("/api/personas/{identity_id}", include_in_schema=False)
def edit_identity(identity_id: str, body: IdentityEdit) -> dict:
    _identity(identity_id)
    changes = {k: v.strip() for k, v in body.model_dump().items() if v is not None}
    if "trigger_word" in changes:
        changes["trigger_word"] = _clean_trigger(changes["trigger_word"])
    if "voice" in changes:
        changes["voice"] = changes["voice"].lower()
    was = identities.vocalless(_identity(identity_id)["voice"])
    if changes:
        execute(f"UPDATE identities SET {', '.join(f'{k} = ?' for k in changes)} WHERE id = ?", (*changes.values(), identity_id))
    if "voice" in changes and identities.vocalless(changes["voice"]) != was:
        _voice_kind_changed(identity_id, now_vocalless=not was)
    return _identity_view(_identity(identity_id))


def _voice_kind_changed(identity_id: str, now_vocalless: bool) -> None:
    """Songs analysed under the other kind of corpus: to no vocals, their lyrics become the score's
    section tags; from it, they have no words yet and the next analysis hears them."""
    for song in rows("SELECT * FROM identity_songs WHERE identity_id = ?", (identity_id,)):
        if song["lyrics_state"] in ("queued", "running"):
            continue
        if now_vocalless:
            if song["stored_path"] and song["score_state"] in ("done", "failed"):
                jobs.set_song(song["id"], lyrics_checked=0)
                jobs.maybe_draft(song["id"])
        else:
            folder = Path(song["stored_path"]).parent if song["stored_path"] else None
            if not folder or not (folder / "whisper.json").exists():
                jobs.set_song(song["id"], lyrics="", lyrics_checked=0, lyrics_state="none",
                              **({"vocals_state": "none"} if not (folder and identities.vocals_file(folder)) else {}))


edit_persona = edit_identity


@app.delete("/api/identities/{identity_id}")
@app.delete("/api/personas/{identity_id}", include_in_schema=False)
async def delete_identity(identity_id: str) -> dict:
    """Removes the identity and its copies in the library.  The original folder is untouched."""
    _identity(identity_id)
    await jobs.stop_identity_analysis(identity_id)
    execute("DELETE FROM identity_songs WHERE identity_id = ?", (identity_id,))
    execute("DELETE FROM identities WHERE id = ?", (identity_id,))
    await asyncio.to_thread(remove_tree, config.DATA_DIR / "identities" / identity_id)
    return {"deleted": True}


delete_persona = delete_identity


@app.put("/api/identities/{identity_id}/songs/{song_id}")
@app.put("/api/personas/{identity_id}/songs/{song_id}", include_in_schema=False)
def edit_identity_song(identity_id: str, song_id: str, body: IdentitySongEdit) -> dict:
    song = one("SELECT * FROM identity_songs WHERE id = ? AND identity_id = ?", (song_id, identity_id))
    if not song:
        raise HTTPException(404, "no such song")
    changes = {}
    if body.include and identities.too_long(song["duration"]):
        raise HTTPException(400, f"this recording is {identities.TOO_LONG}: split it into tracks first")
    if body.include is not None:
        changes["include"] = 1 if body.include else 0
    if body.lyrics is not None:
        changes["lyrics"] = body.lyrics.replace("\r\n", "\n")
    if body.lyrics_checked is not None:
        changes["lyrics_checked"] = 1 if body.lyrics_checked else 0
    if body.description is not None:
        changes["description"] = " ".join(body.description.split())
    if body.style_hint is not None:
        changes["style_hint"] = " ".join(body.style_hint.split())[:300]
    if changes:
        jobs.set_song(song_id, **changes)
        if "lyrics" in changes:
            jobs.remember_in_use(song_id, changes["lyrics"])
    return one("SELECT * FROM identity_songs WHERE id = ?", (song_id,))


edit_persona_song = edit_identity_song


@app.post("/api/identities/{identity_id}/songs/{song_id}/style")
@app.post("/api/personas/{identity_id}/songs/{song_id}/style", include_in_schema=False)
async def regenerate_song_style(identity_id: str, song_id: str) -> dict:
    """Queue or run style analysis for a single song."""
    song = one("SELECT * FROM identity_songs WHERE id = ? AND identity_id = ?", (song_id, identity_id))
    if not song:
        raise HTTPException(404, "no such song")
    jobs.set_song(song_id, style_state="queued", error=None)
    await QUEUE.put({"kind": "identity_style", "id": song_id})
    log.info("Queued style analysis for corpus song '%s' (%s)", song.get("title") or song_id, song_id)
    return {"queued": True, "song_id": song_id}


@app.post("/api/identities/{identity_id}/analyse")
@app.post("/api/personas/{identity_id}/analyse", include_in_schema=False)
async def analyse_identity(identity_id: str) -> dict:
    """Queue every step not yet done for each included song.  Safe to press again:
    finished steps are kept, failed ones are tried again."""
    identity = _identity(identity_id)
    queued = 0
    for song in rows("SELECT * FROM identity_songs WHERE identity_id = ? AND include = 1 ORDER BY position", (identity_id,)):
        if identities.too_long(song["duration"]):
            continue
        cpu = {f: "queued" for f in ("vocals_state", "lyrics_state") if song[f] in ("none", "failed")}
        if cpu:
            jobs.set_song(song["id"], **cpu, error=None)
            await jobs.IDENTITY_QUEUE.put({"id": song["id"]})
            queued += 1
        if song["vocals_state"] == "done":
            for kind, field in jobs.IDENTITY_FIELDS.items():
                if song[field] in ("none", "failed") and kind.startswith("identity_"):
                    jobs.set_song(song["id"], **{field: "queued"}, error=None)
                    await QUEUE.put({"kind": kind, "id": song["id"]})
                    queued += 1
    log.info("Queued analysis for corpus '%s' (%d jobs queued)", identity.get("name") or identity_id, queued)
    return {"queued": queued}


analyse_persona = analyse_identity


@app.post("/api/identities/{identity_id}/songs/{song_id}/lyrics/redraft")
async def redraft_identity_lyrics(identity_id: str, song_id: str) -> dict:
    """Draft a song's lyrics again from the lines already heard, with the sections
    marked by the external LLM: the same words, without running Whisper again.
    Replaces what is there, checked or not: it is asked for by hand."""
    song = one("SELECT * FROM identity_songs WHERE id = ? AND identity_id = ?", (song_id, identity_id))
    if not song:
        raise HTTPException(404, "no such song")
    heard = Path(song["stored_path"]).parent / "whisper.json" if song["stored_path"] else None
    if not heard or not heard.exists():
        raise HTTPException(400, "the lyrics have not been heard yet. Press Analyse.")
    if not llm.is_external_enabled():
        raise HTTPException(400, "redrafting marks the sections with the external LLM, which is not set in Settings")
    if song["lyrics_state"] in ("queued", "running"):
        raise HTTPException(409, "the lyrics are being drafted already")
    jobs.set_song(song_id, lyrics_checked=0, error=None)
    jobs.maybe_draft(song_id)
    log.info("Redrafting the lyrics of corpus song '%s'", song.get("title") or song_id)
    return {"lyrics_state": one("SELECT lyrics_state FROM identity_songs WHERE id = ?", (song_id,))["lyrics_state"]}


class LyricsSourceIn(BaseModel):
    source: Literal["llm", "whisper"]


@app.post("/api/identities/{identity_id}/songs/{song_id}/lyrics/source")
async def choose_lyrics_source(identity_id: str, song_id: str, body: LyricsSourceIn) -> dict:
    """Make one version of a song's words the one in use: the external model's, or Whisper's.
    Both were kept when the song was analysed.  The words in the box are drafted again from the
    chosen lines, replacing what is there, checked or not: it is asked for by hand."""
    song = one("SELECT * FROM identity_songs WHERE id = ? AND identity_id = ?", (song_id, identity_id))
    if not song:
        raise HTTPException(404, "no such song")
    if not song["stored_path"]:
        raise HTTPException(400, "the lyrics have not been heard yet. Press Analyse.")
    folder = Path(song["stored_path"]).parent
    chosen = folder / ("lyrics-llm.json" if body.source == "llm" else "lyrics-whisper.json")
    if not chosen.exists():
        raise HTTPException(400, "that version of the words was not kept for this song")
    if song["lyrics_state"] in ("queued", "running"):
        raise HTTPException(409, "the lyrics are being drafted already")
    try:
        versions = json.loads(song.get("lyrics_versions") or "null") or {}
    except ValueError:
        versions = {}
    # What is in the box belongs to the version being left, with its checked tick: coming back to it restores both.
    leaving = versions.get("active")
    if leaving in ("llm", "whisper") and isinstance(versions.get(leaving), dict) and (song["lyrics"] or "").strip():
        jobs.remember_words(song, leaving, song["lyrics"])
        versions[leaving]["checked"] = 1 if song["lyrics_checked"] else 0
    kept = jobs.remembered_words(song, body.source)
    versions["active"] = body.source
    await asyncio.to_thread(shutil.copyfile, chosen, folder / "whisper.json")
    name = "external model's" if body.source == "llm" else "Whisper"
    if kept is not None:
        # Drafted before: its words come straight back, with no new draft and no call to the model.
        checked = 1 if (versions.get(body.source) or {}).get("checked") else 0
        jobs.set_song(song_id, lyrics_versions=json.dumps(versions), lyrics=kept, lyrics_state="done",
                      lyrics_checked=checked, error=None)
        log.info("Corpus song '%s': the %s version of the words is back in use, as it was left", song.get("title") or song_id, name)
        return {"active": body.source, "lyrics_state": "done", "restored": True, "lyrics": kept, "checked": bool(checked)}
    jobs.set_song(song_id, lyrics_versions=json.dumps(versions), lyrics_checked=0, error=None)
    jobs.maybe_draft(song_id)
    log.info("Corpus song '%s': the %s version of the words is in use", song.get("title") or song_id, name)
    return {"active": body.source, "restored": False,
            "lyrics_state": one("SELECT lyrics_state FROM identity_songs WHERE id = ?", (song_id,))["lyrics_state"]}


@app.post("/api/identities/{identity_id}/stop")
async def stop_identity(identity_id: str) -> dict:
    """Stop the corpus's analysis, waiting and running, on both lanes.  Finished
    steps are kept, so Analyse carries on from where it stopped."""
    identity = _identity(identity_id)
    # Run all would otherwise take the stop for the end of the analysis, and export.
    await _end_run_all(identity_id, "stopped")
    stopped = await jobs.stop_identity_analysis(identity_id)
    log.info("Stopped the analysis of corpus '%s' (%d songs)", identity.get("name") or identity_id, stopped)
    return {"stopped": stopped}


@app.post("/api/identities/{identity_id}/songs/{song_id}/split")
async def split_identity_song(identity_id: str, song_id: str) -> dict:
    """Cut an album in one file into its tracks, by the cue sheet beside it, and put
    the tracks in the corpus in its place.  The corpus folder is only read: the tracks
    go in the corpus's own folder, and the album's copy in the library is removed."""
    identity = _identity(identity_id)
    song = one("SELECT * FROM identity_songs WHERE id = ? AND identity_id = ?", (song_id, identity_id))
    if not song:
        raise HTTPException(404, "no such song")
    source = _song_source(identity, song)
    if not identities.allowed(source) or not source.is_file():
        raise HTTPException(400, "the recording is no longer in its folder")
    found = identities.cue_for(source)
    if not found:
        raise HTTPException(400, "there is no cue sheet beside this recording that lists its tracks")
    await jobs.stop_song_analysis(song_id)
    dest = identities.tracks_dir(identity_id) / f"{slugify(song['title'])}-{song_id}"
    log.info("Splitting '%s' into %d tracks by %s", song["file"], len(found["tracks"]), found["cue"])
    try:
        tracks = await asyncio.to_thread(identities.split_album, source, found["tracks"], dest)
        described = await asyncio.to_thread(lambda: [
            {**t, **identities.probe(t["path"]), "sha256": identities.sha256(t["path"])} for t in tracks])
    except (subprocess.SubprocessError, OSError) as exc:
        await asyncio.to_thread(remove_tree, dest)
        raise HTTPException(500, f"could not split the recording: {exc}") from exc
    new_rows = []
    for track in described:
        flag = None
        if identities.OTHER_SINGER.search(track["title"]):
            flag = "the title names another singer"
        elif track["duration"] and track["duration"] < identities.MIN_SECONDS:
            flag = f"shorter than {identities.MIN_SECONDS} seconds"
        elif identities.too_long(track["duration"]):
            flag = identities.TOO_LONG
        new_rows.append({"id": uuid.uuid4().hex[:12], "file": str(track["path"]), "title": track["title"],
                         "sha256": track["sha256"], "duration": round(track["duration"], 1),
                         "bit_rate": track["bit_rate"], "include": 0 if flag else 1, "flag": flag})
    # The tracks take the album's place in the list.
    order = []
    for other in rows("SELECT id FROM identity_songs WHERE identity_id = ? ORDER BY position", (identity_id,)):
        order.extend([r["id"] for r in new_rows] if other["id"] == song_id else [other["id"]])
    for row in new_rows:
        execute("""INSERT INTO identity_songs(id, identity_id, file, title, sha256, duration, bit_rate, include, flag, position)
                   VALUES(:id, :identity_id, :file, :title, :sha256, :duration, :bit_rate, :include, :flag, 0)""",
                {**row, "identity_id": identity_id})
    execute("DELETE FROM identity_songs WHERE id = ?", (song_id,))
    for position, sid in enumerate(order):
        execute("UPDATE identity_songs SET position = ? WHERE id = ?", (position, sid))
    await asyncio.to_thread(remove_tree, identities.song_dir(identity_id, song))
    log.info("Split '%s' into %d tracks for corpus '%s'", song["file"], len(new_rows), identity.get("name") or identity_id)
    return _identity_view(_identity(identity_id))


@app.get("/api/identities/{identity_id}/songs/{song_id}/audio")
@app.get("/api/personas/{identity_id}/songs/{song_id}/audio", include_in_schema=False)
def identity_song_audio(identity_id: str, song_id: str, which: str = "original") -> FileResponse:
    song = one("SELECT * FROM identity_songs WHERE id = ? AND identity_id = ?", (song_id, identity_id))
    if not song or not song["stored_path"]:
        raise HTTPException(404, "this song has not been copied in yet. Press Analyse.")
    path = Path(song["stored_path"]) if which == "original" else identities.vocals_file(Path(song["stored_path"]).parent)
    if not path or not path.is_file() or not inside(path, config.DATA_DIR):
        raise HTTPException(404, "not there yet")
    return FileResponse(path)


persona_song_audio = identity_song_audio


@app.post("/api/identities/{identity_id}/lora")
async def install_identity_lora(
    identity_id: str,
    file: UploadFile = File(...),
    name: str = Form("", max_length=80),
    trigger: str = Form("", max_length=40),
) -> dict:
    """Take a LoRA trained from this corpus and put it where the engine will find it.

    The app prepares the training set and cannot train, so the file arrives from a
    trainer: here, in ComfyUI, or anywhere else.  It is placed in models/loras with a
    note beside it, the corpus records it, and the engine is asked to look again so
    the picker offers it at once."""
    identity = _identity(identity_id)
    try:
        _digest, tmp, size = await asyncio.to_thread(_store_upload, file.file)
    except TooLarge:
        raise HTTPException(413, f"That file is larger than {config.MAX_UPLOAD_MB} MB.")
    if not size:
        tmp.unlink(missing_ok=True)
        raise HTTPException(400, "empty upload")
    wanted = name.strip() or Path(file.filename or "lora").stem
    try:
        result = await asyncio.to_thread(
            loras.install, tmp, wanted, (trigger.strip() or identity["trigger_word"]), identity["name"]
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except OSError as exc:
        raise HTTPException(500, f"could not write the LoRA: {exc}")
    finally:
        tmp.unlink(missing_ok=True)
    execute("UPDATE identities SET lora = ? WHERE id = ?", (result["name"], identity_id))
    try:
        await ENGINE.refresh_options()
    except Exception as exc:  # noqa: BLE001
        log.warning("the engine's list was not re-read: %s", exc)
    return result


def _lora_file(name: str) -> Path:
    """A LoRA in the engine's folder, by its file name and nothing else."""
    root = loras.folder()
    if not root or Path(name).name != name or not name.endswith(".safetensors"):
        raise HTTPException(404, "no such LoRA")
    path = root / name
    if not path.is_file():
        raise HTTPException(404, "no such LoRA")
    return path


@app.get("/api/loras/{name}/download")
async def download_lora(name: str) -> FileResponse:
    """The LoRA and its note in one zip, for someone else's app.  A LoRA trained from a
    corpus has its learned styles written into the note, so its chips travel with it."""
    path = _lora_file(name)
    corpus_styles = _lora_corpus_styles()
    styles = corpus_styles.get(name) or corpus_styles.get(loras.run_lora(name)) or loras.note_for(path).get("styles") or []
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    archive = config.WORK_DIR / f"lora-{uuid.uuid4().hex[:8]}.zip"
    await asyncio.to_thread(loras.bundle, path, styles, archive)
    return FileResponse(archive, media_type="application/zip", filename=f"{path.stem}.zip",
                        background=BackgroundTask(archive.unlink, missing_ok=True))


@app.delete("/api/loras/{name}")
async def delete_lora(name: str) -> dict:
    """Remove a LoRA from the engine's folder, with its note and its group line."""
    path = _lora_file(name)
    try:
        gone = await asyncio.to_thread(loras.remove, path.name)
    except (OSError, ValueError) as exc:
        raise HTTPException(500, f"could not delete the LoRA: {exc}")
    # A corpus that made it no longer has a file to point at.
    execute("UPDATE identities SET lora = NULL WHERE lora = ?", (name,))
    try:
        await ENGINE.refresh_options()
    except Exception as exc:  # noqa: BLE001
        log.warning("the engine's list was not re-read: %s", exc)
    return {"deleted": gone}


class StrengthsIn(BaseModel):
    planner: float | None = Field(None, ge=0.0, le=3.0)
    sound: float | None = Field(None, ge=0.0, le=3.0)


@app.put("/api/loras/{name}/strengths")
def lora_strengths(name: str, body: StrengthsIn) -> dict:
    """The strengths this LoRA starts at when chosen.  Both empty clears them."""
    path = _lora_file(name)
    if (body.planner is None) != (body.sound is None):
        raise HTTPException(400, "give both strengths, or neither to clear them")
    try:
        loras.set_strengths(path, body.planner, body.sound)
    except OSError as exc:
        raise HTTPException(500, f"could not write the LoRA's note: {exc}")
    return {"name": name, "strengths": loras.note_for(path).get("strengths")}


@app.post("/api/loras/install")
async def install_shared_lora(file: UploadFile = File(...)) -> dict:
    """A LoRA from someone else: the zip Download makes, or a bare .safetensors file."""
    try:
        _digest, tmp, size = await asyncio.to_thread(_store_upload, file.file)
    except TooLarge:
        raise HTTPException(413, f"That file is larger than {config.MAX_UPLOAD_MB} MB.")
    if not size:
        tmp.unlink(missing_ok=True)
        raise HTTPException(400, "empty upload")
    try:
        result = await asyncio.to_thread(loras.install_shared, tmp, file.filename or "lora.safetensors")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except OSError as exc:
        raise HTTPException(500, f"could not write the LoRA: {exc}")
    finally:
        tmp.unlink(missing_ok=True)
    try:
        await ENGINE.refresh_options()
    except Exception as exc:  # noqa: BLE001
        log.warning("the engine's list was not re-read: %s", exc)
    return result


def _training_run() -> dict | None:
    """The LoRA being trained, if there is one: it holds the whole GPU."""
    return one("SELECT * FROM lora_runs WHERE state IN ('queued', 'running') ORDER BY started_at IS NULL, started_at DESC LIMIT 1")


def _engine_free_for_training() -> None:
    """Refuse to start training when the card is already in use."""
    busy = CURRENT.get("kind")
    if busy:
        raise HTTPException(409, f"The engine is busy with a {busy}. Wait for it to finish.")
    waiting = one("SELECT COUNT(*) AS n FROM takes WHERE status IN ('queued', 'running')")["n"]
    if waiting:
        raise HTTPException(409, "Something is already queued for the engine. Wait for it, or stop it.")


def _gpu_free_for_rendering() -> None:
    """Refuse to start a render while a LoRA is training.  The two cannot share the
    card: training was measured at 12.5 GB of 16, and a render on top would fail."""
    run = _training_run()
    if run:
        raise HTTPException(409, "A LoRA is training, and it has the GPU until it finishes. "
                                 "Stop it first if you need the engine.")


class TrainIn(BaseModel):
    steps: int | None = Field(None, ge=50, le=50000)
    rank: int | None = Field(None, ge=4, le=128)
    # What to do with the LoRA a previous run left under the same name.
    previous: Literal["keep", "delete"] | None = None


def _lora_base(identity: dict) -> str:
    """The name a corpus's LoRA is trained under: the corpus name, made safe."""
    name = re.sub(r"[^a-z0-9]+", "_", (identity["name"] or "corpus").lower()).strip("_")[:40] or "corpus"
    return f"{name}_lora"


def _training_built_in() -> None:
    """Training, when TRAINING_ENABLED=0 has switched it off.  A caller gets the
    reason rather than a 404 that looks like a bug."""
    if not config.TRAINING_ENABLED:
        raise HTTPException(
            501,
            "Training a LoRA is switched off. Set TRAINING_ENABLED=1 for the app, with "
            "the engine built with WITH_TRAINER=1, or export the training set and train "
            "it elsewhere.",
        )


@app.post("/api/identities/{identity_id}/train")
async def train_identity(identity_id: str, body: TrainIn | None = None) -> dict:
    """Train a LoRA from this corpus's set.

    It takes the better part of an hour and the whole GPU, so the app refuses to start
    it while the engine is busy, refuses to start anything else on the engine while it
    runs, and shows it on the main screen with a stop button."""
    _training_built_in()
    identity = _identity(identity_id)
    if ENGINE.options_loaded and config.TRAIN_CHECKPOINT not in (ENGINE.options.get("checkpoints") or []):
        raise HTTPException(400, "Training learns from the full-quality model, and this install has the "
                                 "low-memory one. Run the installer again and choose full quality, or "
                                 "scripts/fetch-models.sh for Docker.")
    if _training_run():
        raise HTTPException(409, "A LoRA is already training.")
    _engine_free_for_training()
    dataset = config.DATA_DIR / "identities" / identity_id / "dataset"
    songs = sorted(dataset.glob("*.flac")) if dataset.is_dir() else []
    if not songs:
        raise HTTPException(400, "Export the training set first: there is nothing to train on.")
    if not config.ENGINE_INPUT_DIR:
        raise HTTPException(503, "The app cannot see the engine's input folder, so it cannot hand it the set.")

    base = _lora_base(identity)
    root = loras.folder()
    if loras.previous_run(base, root):
        choice = body.previous if body else None
        if choice not in ("keep", "delete"):
            raise HTTPException(409, f"{base} already exists: say whether to keep it or delete it")
        if choice == "keep":
            kept = await asyncio.to_thread(loras.set_aside, base, root, identity["name"])
            log.info("Kept the previous LoRA of corpus '%s' as %s", identity["name"], kept)
        else:
            await asyncio.to_thread(loras.delete_run, base, root)
            log.info("Deleted the previous LoRA of corpus '%s' before training again", identity["name"])
        with contextlib.suppress(Exception):
            await ENGINE.refresh_options()

    run_id = uuid.uuid4().hex[:12]
    run = {
        "id": run_id,
        "identity_id": identity_id,
        "lora_name": base,
        "steps": (body.steps if body and body.steps else config.train_steps(len(songs))),
        "rank": (body.rank if body and body.rank else config.TRAIN_RANK),
    }
    execute(
        """INSERT INTO lora_runs(id, identity_id, lora_name, steps, rank, state)
           VALUES(:id, :identity_id, :lora_name, :steps, :rank, 'queued')""",
        run,
    )
    await jobs.QUEUE.put({"kind": "train", "id": run_id})
    log.info("Queued LoRA training run %s for corpus '%s' (%d steps, rank=%d)", run_id, identity["name"], run["steps"], run["rank"])
    return {**run, "state": "queued", "songs": len(songs)}


@app.post("/api/lora-runs/{run_id}/finish")
async def finish_lora_run(run_id: str) -> dict:
    """Finish a run that stopped short, from what it saved, as a finished run would:
    its best copy, or its last checkpoint, becomes the LoRA, with its checkpoints under
    it.  No GPU time: for a run stopped by Stop, a crash or a limit, whose files are
    still there."""
    run = one("SELECT * FROM lora_runs WHERE id = ?", (run_id,))
    if not run:
        raise HTTPException(404, "no such training run")
    if run["state"] not in ("failed", "cancelled"):
        raise HTTPException(409, "this run did not stop short")
    if _training_run():
        raise HTTPException(409, "A LoRA is training. Finish this one when it has finished.")
    identity = one("SELECT * FROM identities WHERE id = ?", (run["identity_id"],))
    if not identity:
        raise HTTPException(404, "the corpus is gone")
    root = loras.folder()
    saved = _run_saved(run, root)
    if not saved or not saved["finishable"]:
        raise HTTPException(400, "this run saved nothing to finish from")
    try:
        name = await jobs.finish_training(run, identity, stopped=True)
    except RuntimeError as exc:
        raise HTTPException(400, str(exc)) from exc
    after = f", after step {saved['last_step']} of {run['steps']}" if saved["last_step"] else ""
    jobs._run_state(run_id, state="done", stage=f"finished from what it saved{after}", progress=1.0, error=None,
                    finished_at=time.time())
    log.info("Finished the stopped training run %s of corpus '%s' from what it saved%s -> %s",
             run_id, identity["name"], after, name)
    return {"lora": name, "last_step": saved["last_step"]}


def _run_saved(run: dict, root: Path | None) -> dict | None:
    """What a run that stopped short left behind: the trainer's best copy, its last
    checkpoint, and whether that is enough to finish it (it is not, once a LoRA of that
    name exists again)."""
    if not root:
        return None
    name = run["lora_name"]
    steps = jobs.run_checkpoints(name, root)
    last = int(re.sub(r"\D", "", steps[-1].stem.rsplit("_step", 1)[1]) or 0) if steps else None
    best = (root / f"{name}_best.safetensors").is_file()
    finished = (root / f"{name}.safetensors").is_file()
    return {"best": best, "last_step": last, "finishable": (best or bool(steps)) and not finished}


def _last_run(identity: dict) -> dict | None:
    """The corpus's latest training run, and for one that stopped short, what it saved."""
    run = one("SELECT * FROM lora_runs WHERE identity_id = ? ORDER BY started_at IS NULL, started_at DESC LIMIT 1",
              (identity["id"],))
    if not run:
        return None
    view = {key: run[key] for key in ("id", "state", "stage", "error", "steps", "started_at", "finished_at")}
    if run["state"] in ("failed", "cancelled"):
        view["saved"] = _run_saved(run, loras.folder())
    return view


@app.post("/api/lora-runs/{run_id}/cancel")
async def cancel_lora_run(run_id: str) -> dict:
    """Stop a training run."""
    run = one("SELECT * FROM lora_runs WHERE id = ?", (run_id,))
    if not run:
        raise HTTPException(404, "no such training run")
    await jobs.cancel_train(run_id)
    return {"cancelled": True}


@app.post("/api/identities/{identity_id}/export")
@app.post("/api/personas/{identity_id}/export", include_in_schema=False)
async def export_identity(identity_id: str) -> dict:
    """Write the training set: per included song, the audio as FLAC, its lyrics and
    its style caption.  Songs without a copy yet are skipped and listed.  How far it
    has got shows in the corpus window while it runs."""
    identity = _identity(identity_id)
    if identity_id in EXPORTING:
        raise HTTPException(409, "the training set is being written already")
    view = _identity_view(identity)
    chosen = [s for s in view["songs"] if s["include"]]
    EXPORTING[identity_id] = {"done": 0, "total": len(chosen), "song": None, "since": time.time()}
    try:
        return await _export(identity, view, chosen)
    finally:
        EXPORTING.pop(identity_id, None)


# The corpora whose training set is being written, and how far each has got.
EXPORTING: dict[str, dict] = {}


async def _export(identity: dict, view: dict, chosen: list[dict]) -> dict:
    identity_id = identity["id"]
    dest = config.DATA_DIR / "identities" / identity_id / "dataset"
    await asyncio.to_thread(remove_tree, dest)
    dest.mkdir(parents=True, exist_ok=True)
    written, skipped, unchecked, cut_short = [], [], [], []
    sizing = _train_sizing(identity_id)
    log.info("Exporting corpus '%s' for training on %s", identity["name"], sizing["reason"])
    for number, song in enumerate(chosen):
        EXPORTING[identity_id].update(done=number, song=song["title"])
        if not song["stored_path"] or not Path(song["stored_path"]).is_file():
            skipped.append(song["title"])
            continue
        lyrics_content = (song["lyrics"] or "").strip() or "[instrumental]"
        name = identities.export_name(song)
        # A song longer than the trainer's limit is cut at the end of a section, faded out,
        # and keeps only the words still sung (#7).
        cut = await asyncio.to_thread(_training_cut, song, sizing["minutes"] * 60)
        command = ["ffmpeg", "-v", "error", "-y", "-i", song["stored_path"]]
        if cut:
            fade_from = max(0.0, cut["seconds"] - identities.TRAIN_FADE)
            command += ["-t", f"{cut['seconds']:.2f}", "-af", f"afade=t=out:st={fade_from:.2f}:d={identities.TRAIN_FADE}"]
            lyrics_content = cut["lyrics"].strip() or lyrics_content
            cut_short.append({"title": song["title"], "seconds": cut["seconds"], "at_section": cut["at_section"]})
            log.info("Corpus song '%s' is cut for training at %.0fs%s", song["title"], cut["seconds"],
                     " (the end of a section)" if cut["at_section"] else "")
        await asyncio.to_thread(subprocess.run, [*command, str(dest / f"{name}.flac")], check=True, timeout=600)
        (dest / f"{name}.lyrics.txt").write_text(lyrics_content + "\n", encoding="utf-8")
        (dest / f"{name}.txt").write_text(song["caption"] + "\n", encoding="utf-8")
        written.append(song["title"])
        if not song["lyrics_checked"] and not identities.vocalless(identity["voice"]):
            unchecked.append(song["title"])
    manifest = {"identity": identity["name"], "trigger_word": identity["trigger_word"], "consent": True,
                "songs": written, "unchecked_lyrics": unchecked, "cut_for_training": cut_short, "train_minutes": sizing["minutes"],
                "exported_at": time.time(), "app": config.VERSION}
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    execute("UPDATE identities SET exported_at = ?, export_dir = ? WHERE id = ?", (time.time(), str(dest), identity_id))
    log.info("Exported training dataset for corpus '%s' (%d songs) -> %s", identity["name"], len(written), dest)
    return {"folder": _host_path(dest), "written": written, "skipped": skipped, "unchecked": unchecked,
            "cut": cut_short}


export_persona = export_identity


# ------------------------------------------------------------------------ run all
# Analyse, export and train, one after the other, for someone who would rather not
# wait for each: a corpus of many songs takes hours to analyse.  It runs here, so the
# page can be closed.  Kept in memory: a restart ends it, and the steps it finished
# are kept, as a restart keeps them anyway.
RUN_ALL: dict[str, dict] = {}


class RunAllIn(BaseModel):
    # What to do with the LoRA a previous run left under the same name.
    previous: Literal["keep", "delete"] | None = None


def _analysed(song: dict) -> bool:
    return all(song[field] == "done" for field in IDENTITY_STEPS)


@app.post("/api/identities/{identity_id}/run-all")
async def run_all_identity(identity_id: str, body: RunAllIn | None = None) -> dict:
    """Start the chain.  Everything it will need to ask is asked now, so it never
    stops halfway to wait for an answer."""
    _training_built_in()
    identity = _identity(identity_id)
    if (RUN_ALL.get(identity_id) or {}).get("stage") in ("analysing", "exporting", "waiting"):
        raise HTTPException(409, "Run all is already going for this corpus.")
    if _training_run():
        raise HTTPException(409, "A LoRA is already training. Run all when it has finished.")
    if identity_id in EXPORTING:
        raise HTTPException(409, "The training set is being written. Run all when it has finished.")
    if not rows("SELECT id FROM identity_songs WHERE identity_id = ? AND include = 1", (identity_id,)):
        raise HTTPException(400, "Include some songs first.")
    if not config.ENGINE_INPUT_DIR:
        raise HTTPException(503, "The app cannot see the engine's input folder, so it cannot hand it the set.")
    previous = body.previous if body else None
    if loras.previous_run(_lora_base(identity), loras.folder()) and previous not in ("keep", "delete"):
        raise HTTPException(409, f"{_lora_base(identity)} already exists: say whether to keep it or delete it")
    RUN_ALL[identity_id] = {"stage": "analysing", "since": time.time(), "left_out": [], "error": None}
    RUN_ALL[identity_id]["task"] = asyncio.create_task(_run_all(identity, previous))
    log.info("Run all started for corpus '%s'", identity["name"])
    return _run_all_view(identity_id)


@app.post("/api/identities/{identity_id}/run-all/stop")
async def stop_run_all(identity_id: str) -> dict:
    """Stop the chain, and the analysis if that is where it is.  Finished steps are
    kept; a training run it has already started has its own Stop."""
    _identity(identity_id)
    await _end_run_all(identity_id, "stopped")
    return {"stopped": True}


async def _end_run_all(identity_id: str, stage: str) -> None:
    run = RUN_ALL.get(identity_id)
    if not run or run.get("stage") not in ("analysing", "exporting", "waiting"):
        return
    if run["stage"] == "analysing":
        await jobs.stop_identity_analysis(identity_id)
    if run["stage"] == "exporting":
        # Cut short, the training set would be half written: it finishes, then stops.
        run["stopping"] = True
        return
    run.update(stage=stage)
    task = run.get("task")
    if task and not task.done() and task is not asyncio.current_task():
        task.cancel()
    log.info("Run all %s for corpus %s", stage, identity_id)


def _run_all_view(identity_id: str) -> dict | None:
    run = RUN_ALL.get(identity_id)
    if not run:
        return None
    view = {key: value for key, value in run.items() if key not in ("task", "stopping")}
    # Handed over, it ends with the training, which the corpus window reports itself.
    if view["stage"] == "training":
        latest = one("SELECT state FROM lora_runs WHERE identity_id = ? AND started_at >= ? "
                     "ORDER BY started_at DESC LIMIT 1", (identity_id, run["since"]))
        if latest and latest["state"] in ("done", "failed", "cancelled"):
            view["stage"] = "ended"
    return view


async def _run_all(identity: dict, previous: str | None) -> None:
    identity_id = identity["id"]
    run = RUN_ALL[identity_id]
    try:
        await analyse_identity(identity_id)
        # The queue fills and empties song by song; a moment first, so a song queued
        # a breath ago is seen as waiting rather than the whole thing as done.
        await asyncio.sleep(3)
        while _identity_view(_identity(identity_id))["busy"]:
            await asyncio.sleep(3)
        view = _identity_view(_identity(identity_id))
        chosen = [song for song in view["songs"] if song["include"]]
        ready = [song for song in chosen if _analysed(song)]
        run["left_out"] = [song["title"] or song["file"] for song in chosen if not _analysed(song)]
        if not ready:
            raise RuntimeError("no song could be analysed, so there is nothing to train on")

        run["stage"] = "exporting"
        EXPORTING[identity_id] = {"done": 0, "total": len(ready), "song": None, "since": time.time()}
        try:
            await _export(identity, view, ready)
        finally:
            EXPORTING.pop(identity_id, None)
        if run.get("stopping"):
            run["stage"] = "stopped"
            log.info("Run all stopped for corpus '%s' after the export", identity["name"])
            return

        # Whatever else is using the engine finishes first, as it would if Train
        # had been pressed by hand and pressed again.
        run["stage"] = "waiting"
        while True:
            try:
                await train_identity(identity_id, TrainIn(previous=previous))
                break
            except HTTPException as exc:
                if exc.status_code != 409 or "busy" not in exc.detail and "queued" not in exc.detail:
                    raise RuntimeError(exc.detail) from exc
                await asyncio.sleep(10)
        run["stage"] = "training"
        log.info("Run all for corpus '%s' handed over to training%s", identity["name"],
                 f", {len(run['left_out'])} songs left out" if run["left_out"] else "")
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001
        run.update(stage="failed", error=str(exc))
        log.warning("Run all for corpus '%s' failed: %s", identity["name"], exc)


def _host_path(path: Path) -> str:
    """A path under the data folder as the user sees it on the host, when known."""
    if config.DATA_DIR_HOST:
        try:
            return config.DATA_DIR_HOST + "/" + str(path.relative_to(config.DATA_DIR))
        except ValueError:
            pass
    return str(path)


# ------------------------------------------------------------------------ lyrics
@app.post("/api/lyrics")
async def write_lyrics(body: LyricsIn) -> dict:
    """Queue a lyric draft.  The page polls GET /api/lyrics/{id} for the words."""
    if not llm.is_external_enabled():
        if ENGINE.options_loaded and not ENGINE.options.get("lyrics"):
            raise HTTPException(400, f"The engine cannot write lyrics: it needs {config.LYRICS_MODEL} "
                                     "in models/text_encoders. Run scripts/fetch-models.sh.")
    sections = None
    if body.sections:
        try:
            sections = lyrics.clean_sections(body.sections)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
    elif body.structure not in lyrics.STRUCTURES:
        raise HTTPException(400, f"unknown structure: {body.structure}")
    if body.feel not in lyrics.FEELS:
        raise HTTPException(400, f"unknown lyric feel: {body.feel}")
    jobs.forget_old_lyrics()
    record = {
        "id": uuid.uuid4().hex[:12], "status": "queued", "brief": body.brief.strip(),
        "style": body.style.strip(), "structure": body.structure,
        "sections": sections, "lines": body.lines, "feel": body.feel,
        "seed": body.seed if body.seed is not None else int.from_bytes(os.urandom(4), "big"),
        "created_at": time.time(), "title": None, "lyrics": None, "error": None,
    }
    LYRICS[record["id"]] = record
    await QUEUE.put({"kind": "lyrics", "id": record["id"]})
    log.info("Queued lyrics draft (%s, structure=%s, brief='%s')", record["id"], record["structure"], record["brief"][:40])
    return record


@app.get("/api/lyrics/{draft_id}")
def get_lyrics(draft_id: str) -> dict:
    record = LYRICS.get(draft_id)
    if not record:
        raise HTTPException(404, "no such draft. It may have expired, or the app restarted.")
    return record


@app.post("/api/lyrics/{draft_id}/cancel")
async def cancel_lyrics(draft_id: str) -> dict:
    record = LYRICS.get(draft_id)
    if not record:
        raise HTTPException(404, "no such draft")
    if record["status"] not in ACTIVE:
        return {"cancelled": False, "status": record["status"]}
    await jobs.cancel_lyrics(record)
    return {"cancelled": True}


@app.post("/api/takes/{take_id}/cancel")
async def cancel_take(take_id: str) -> dict:
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take:
        raise HTTPException(404, "no such take")
    if take["status"] not in ACTIVE:
        return {"cancelled": False, "status": take["status"]}
    await jobs.cancel_take(take)
    return {"cancelled": True}


@app.put("/api/takes/{take_id}/score")
def save_take_score(take_id: str, body: ScoreIn) -> dict:
    before = one("SELECT title, abc FROM takes WHERE id = ?", (take_id,))
    if not execute("UPDATE takes SET abc = ? WHERE id = ?", (body.abc, take_id)):
        raise HTTPException(404, "no such take")
    # The page saves the score before every render; only a real change is worth a line.
    if before and (before["abc"] or "") != (body.abc or ""):
        log.info("Score of take '%s' (%s) edited by hand (%d characters)", before["title"], take_id, len(body.abc or ""))
    return {"saved": True, "chars": len(body.abc)}


# What Save hands over, in the output format chosen in Settings.  Takes are kept as FLAC.
SAVE_FORMATS = {
    "flac": ("audio/flac", None),
    "wav": ("audio/wav", ["-c:a", "pcm_s16le"]),
    "mp3": ("audio/mpeg", ["-c:a", "libmp3lame", "-b:a", "320k"]),
}


@app.get("/api/takes/{take_id}/audio")
def take_audio(
    take_id: str,
    download: bool = False,
    format: str | None = None,
    raw: bool = False,
) -> FileResponse:
    """The take's audio: inline to play, or as a file to save.  It is always the take as it is kept.  Mastering is
    never applied here: the rack renders a mastered file in the browser, with the chain that plays it, and sends it
    to `export-mastered`.  `raw` is accepted for pages that still send it."""
    if format and format not in SAVE_FORMATS:
        raise HTTPException(400, "the format must be flac, wav or mp3")
    take = one("SELECT audio_path, title, kind, lyrics FROM takes WHERE id = ?", (take_id,))
    if not take or not take["audio_path"] or not Path(take["audio_path"]).exists():
        raise HTTPException(404, "no audio for this take")
    safe = "".join(ch for ch in (take["title"] or "take") if ch.isalnum() or ch in " -_")[:60].strip() or "take"
    if not download:   # playing: the FLAC as kept, inline, so a link to it plays in a browser and does not save
        return FileResponse(take["audio_path"], media_type="audio/flac", filename=f"{safe}.flac",
                            content_disposition_type="inline")
    # A download is in the format asked for, else the one set in Settings.
    fmt = format or setting_value("stems.format")
    fmt = fmt if fmt in SAVE_FORMATS else "flac"
    media, codec = SAVE_FORMATS[fmt]
    # Made for this download only, with its tags, and removed once it has been sent.
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    out = config.WORK_DIR / f"save-{take_id}-{uuid.uuid4().hex[:8]}.{fmt}"
    try:
        library.tagged_copy(Path(take["audio_path"]), out, fmt, codec, take["title"] or "",
                            library.sung_words(take["kind"], take["lyrics"]))
    except (subprocess.SubprocessError, OSError) as exc:
        out.unlink(missing_ok=True)
        log.warning("Could not convert take '%s' to %s: %s", take["title"] or take_id, fmt, exc)
        raise HTTPException(500, f"could not convert this take to {fmt.upper()}") from exc
    return FileResponse(out, media_type=media, filename=f"{safe}.{fmt}",
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
                        background=BackgroundTask(out.unlink, missing_ok=True))


_PENDING_EXPORTS: dict[str, dict] = {}


@app.post("/api/takes/{take_id}/export-mastered")
async def export_mastered_take(
    take_id: str,
    format: str = Query("flac"),
    prepare: bool = Query(False),
    audio_file: UploadFile = File(...)
):
    """Export take with exact mastering DSP rendered in browser via OfflineAudioContext,
    tagging and encoding to the requested format (FLAC, MP3, or WAV).
    If prepare=True, returns JSON {"download_url": ...} so browser triggers a native HTTP download prompt."""
    fmt = format.lower()
    if fmt not in SAVE_FORMATS:
        raise HTTPException(400, "the format must be flac, wav or mp3")
    take = one("SELECT audio_path, title, kind, lyrics FROM takes WHERE id = ?", (take_id,))
    if not take or not take["audio_path"] or not Path(take["audio_path"]).exists():
        raise HTTPException(404, "no audio for this take")

    media, codec = SAVE_FORMATS[fmt]
    safe = "".join(ch for ch in (take["title"] or "take") if ch.isalnum() or ch in " -_")[:60].strip() or "take"

    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    temp_wav = config.WORK_DIR / f"upload-master-{take_id}-{uuid.uuid4().hex[:8]}.wav"
    out = config.WORK_DIR / f"save-master-{take_id}-{uuid.uuid4().hex[:8]}.{fmt}"

    try:
        content = await audio_file.read()
        temp_wav.write_bytes(content)
        # The upload was rendered by the rack's own chain: it is only tagged and encoded here.
        library.tagged_copy(temp_wav, out, fmt, codec, take["title"] or "",
                            library.sung_words(take["kind"], take["lyrics"]))
    except (subprocess.SubprocessError, OSError) as exc:
        out.unlink(missing_ok=True)
        log.warning("Could not convert uploaded mastered audio for take '%s' to %s: %s", take["title"] or take_id, fmt, exc)
        raise HTTPException(500, f"could not convert mastered take to {fmt.upper()}") from exc
    finally:
        temp_wav.unlink(missing_ok=True)

    if prepare:
        now = time.time()
        for old_tok, old_entry in list(_PENDING_EXPORTS.items()):
            if now - old_entry.get("time", 0) > 300:
                _PENDING_EXPORTS.pop(old_tok, None)
                try:
                    Path(old_entry["path"]).unlink(missing_ok=True)
                except OSError:
                    pass
        token = uuid.uuid4().hex
        _PENDING_EXPORTS[token] = {
            "path": out,
            "media": media,
            "safe": safe,
            "fmt": fmt,
            "time": now,
        }
        return {"download_url": f"/api/takes/{take_id}/download-mastered?token={token}"}

    return FileResponse(out, media_type=media, filename=f"{safe}.{fmt}",
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
                        background=BackgroundTask(out.unlink, missing_ok=True))


@app.get("/api/takes/{take_id}/download-mastered")
def download_mastered_take(take_id: str, token: str = Query(...)) -> FileResponse:
    """Serve prepared mastered export via direct HTTP GET, preserving native browser Save As prompts."""
    entry = _PENDING_EXPORTS.pop(token, None)
    if not entry or not Path(entry["path"]).exists():
        raise HTTPException(404, "Export expired or not found")
    out_path = Path(entry["path"])
    return FileResponse(
        out_path,
        media_type=entry["media"],
        filename=f"{entry['safe']}.{entry['fmt']}",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        background=BackgroundTask(out_path.unlink, missing_ok=True)
    )


@app.post("/api/takes/{take_id}/bake-master")
async def bake_master_take(
    take_id: str,
    undo: bool = Query(False),
    audio_file: UploadFile | None = File(None)
) -> dict:
    """Keep a take's mastering for good, or restore the unmastered original.  The mastered audio is the
    WAV the rack rendered in the browser, with the chain that plays it: the server does no processing of
    its own, so without that file there is nothing to bake."""
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take or not take["audio_path"] or not Path(take["audio_path"]).exists():
        raise HTTPException(404, "no audio for this take")
    if take["status"] != "done":
        raise HTTPException(409, "this take is busy")
    if not undo and audio_file is None:
        raise HTTPException(400, "send the mastered audio: the rack renders it, the server does not")

    current_audio = Path(take["audio_path"])
    premaster = library.premaster_path(current_audio)

    if undo:
        if not premaster.exists():
            raise HTTPException(409, "this take has no unmastered original to restore")
        try:
            shutil.copy2(str(premaster), str(current_audio))
            premaster.unlink(missing_ok=True)
        except OSError as exc:
            log.warning("Could not restore unmastered take '%s': %s", take["title"] or take_id, exc)
            raise HTTPException(500, "could not restore unmastered audio") from exc

        # Invalidate and recompute waveform peaks
        library.peaks_path(current_audio).unlink(missing_ok=True)
        fresh_peaks = await asyncio.to_thread(ensure_peaks, current_audio)
        new_loudness = await asyncio.to_thread(library.loudness, current_audio)
        new_duration = await asyncio.to_thread(library.audio_duration, current_audio)

        execute("UPDATE takes SET audio_path = ?, loudness = ?, duration = ? WHERE id = ?",
                (str(current_audio), new_loudness, new_duration, take_id))
        log.info("Restored unmastered audio for take '%s' (%s)", take["title"] or take_id, take_id)
        return {"status": "ok", "take_id": take_id, "reverted": True, "peaks": fresh_peaks}

    # Baking master
    if not premaster.exists():
        try:
            shutil.copy2(str(current_audio), str(premaster))
        except OSError as exc:
            log.warning("Could not backup premaster for '%s': %s", take["title"] or take_id, exc)
            raise HTTPException(500, "could not backup unmastered audio") from exc

    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    temp_target = config.WORK_DIR / f"bake-{take_id}-{uuid.uuid4().hex[:8]}.flac"

    try:
        temp_wav = config.WORK_DIR / f"bake-in-{take_id}-{uuid.uuid4().hex[:8]}.wav"
        try:
            content = await audio_file.read()
            temp_wav.write_bytes(content)
            library.tagged_copy(temp_wav, temp_target, "flac", None, take["title"] or "",
                                library.sung_words(take["kind"], take["lyrics"]))
        finally:
            temp_wav.unlink(missing_ok=True)

        shutil.move(str(temp_target), str(current_audio))
    except (subprocess.SubprocessError, OSError) as exc:
        temp_target.unlink(missing_ok=True)
        log.warning("Could not bake master for take '%s': %s", take["title"] or take_id, exc)
        raise HTTPException(500, "could not bake mastering processing into take") from exc

    library.peaks_path(current_audio).unlink(missing_ok=True)
    fresh_peaks = await asyncio.to_thread(ensure_peaks, current_audio)
    new_loudness = await asyncio.to_thread(library.loudness, current_audio)
    new_duration = await asyncio.to_thread(library.audio_duration, current_audio)

    execute("UPDATE takes SET audio_path = ?, fx_chain = NULL, loudness = ?, duration = ? WHERE id = ?",
            (str(current_audio), new_loudness, new_duration, take_id))

    log.info("Baked mastering processing into take '%s' (%s)", take["title"] or take_id, take_id)
    return {
        "status": "ok",
        "take_id": take_id,
        "baked": True,
        "has_premaster": True,
        "peaks": fresh_peaks,
        "loudness": new_loudness,
        "duration": new_duration
    }


@app.post("/api/takes/{take_id}/normalise")
async def normalise_take(take_id: str, undo: bool = False) -> dict:
    """Bring a quiet take up to the usual loudness, or put back the level it was
    rendered at.  Only when asked: a take's audio is otherwise left as it came."""
    take = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    if not take or not take["audio_path"] or not Path(take["audio_path"]).exists():
        raise HTTPException(404, "no audio for this take")
    if take["status"] != "done":
        raise HTTPException(409, "this take is busy")
    rendered = library.rendered_path(Path(take["audio_path"]))
    if not rendered.exists():
        raise HTTPException(404, "the file as rendered is missing")
    try:
        if undo:
            if not take["normalised"]:
                raise HTTPException(409, "this take has not been normalised")
            playing, target = rendered, None
        else:
            target = float(take["target_lufs"]) if take.get("target_lufs") is not None else library.normal_target()
            playing = await asyncio.to_thread(library.normalise, rendered, target)
    except PermissionError as exc:
        log.warning("Could not normalise take '%s': its file is open in another program (%s)", take["title"] or take_id, exc)
        raise HTTPException(409, "its audio file is open in another program; close it and try again") from exc
    except (subprocess.SubprocessError, OSError, RuntimeError) as exc:
        log.warning("Could not normalise take '%s': %s", take["title"] or take_id, exc)
        raise HTTPException(500, "could not normalise this take") from exc
    # The recorded level stays the one it was rendered at: that is what says whether
    # the render went wrong, and normalising does not change that.
    execute("UPDATE takes SET normalised = ?, normalised_to = ?, audio_path = ? WHERE id = ?",
            (0 if undo else 1, target, str(playing), take_id))
    if undo:
        # Gone if nothing has it open; a later render clears it otherwise.
        with contextlib.suppress(OSError):
            library.normalised_path(rendered).unlink(missing_ok=True)
    await asyncio.to_thread(ensure_peaks, playing)
    log.info("%s take '%s'", "Restored the rendered level of" if undo else "Normalised", take["title"] or take_id)
    return {"normalised": not undo}


@app.post("/api/takes/{take_id}/weak/dismiss")
def dismiss_weak(take_id: str) -> dict:
    """Listened to, and fine: the weak-render note on a normalised take goes."""
    if not execute("UPDATE takes SET weak_dismissed = 1 WHERE id = ?", (take_id,)):
        raise HTTPException(404, "no such take")
    return {"dismissed": True}


@app.post("/api/takes/{take_id}/note/dismiss")
def dismiss_note(take_id: str) -> dict:
    """Listened to, and the end is fine: the note that a take ran to the length cap, or stopped before its
    last section, goes."""
    if not execute("UPDATE takes SET note_dismissed = 1 WHERE id = ?", (take_id,)):
        raise HTTPException(404, "no such take")
    return {"dismissed": True}


@app.get("/api/takes/{take_id}/peaks")
def take_peaks(take_id: str) -> dict:
    take = one("SELECT audio_path FROM takes WHERE id = ?", (take_id,))
    if not take or not take["audio_path"] or not Path(take["audio_path"]).exists():
        raise HTTPException(404, "no audio for this take")
    result = ensure_peaks(Path(take["audio_path"]))
    if not result:
        raise HTTPException(500, "could not read the waveform")
    return result


def sweep_engine_input(max_age_hours: float = 24) -> None:
    """Let go of the copies the app has sent the engine and finished with.

    Everything the app uploads is written into the engine's input folder and, until
    now, nothing ever removed it: 634 MB had collected.  It is only ever a copy of
    something the app still holds, so anything a day old goes.  Directories are left
    alone — a training run caches its encoded latents in one, and rebuilding that
    costs twenty five seconds per corpus."""
    root = config.ENGINE_INPUT_DIR
    if not root or not root.is_dir():
        return
    cutoff = time.time() - max_age_hours * 3600
    removed = 0
    for entry in root.iterdir():
        try:
            if not entry.is_file() or entry.stat().st_mtime > cutoff:
                continue
            entry.unlink()
            removed += 1
        except OSError as exc:  # noqa: BLE001
            log.debug("could not remove %s: %s", entry, exc)
    if removed:
        log.info("removed %d finished uploads from the engine's input folder", removed)


def fill_source_durations() -> None:
    """Recordings added before the column existed: read each one's length once."""
    for source in rows("SELECT id, stored_path FROM sources WHERE duration IS NULL"):
        path = Path(source["stored_path"])
        if not path.exists():
            continue
        seconds = audio_duration(path)
        if seconds:
            execute("UPDATE sources SET duration = ? WHERE id = ?", (seconds, source["id"]))


_active_sf2_renders: dict[str, asyncio.Task] = {}
_sf2_render_lock = asyncio.Lock()


async def _ensure_source_midi_rendered(stored_p: Path, flac_p: Path, active_sf2: str) -> None:
    if flac_p.exists() and flac_p.stat().st_size > 0:
        return
    key = str(flac_p)
    async with _sf2_render_lock:
        if flac_p.exists() and flac_p.stat().st_size > 0:
            return
        task = _active_sf2_renders.get(key)
        if not task:
            task = asyncio.create_task(
                asyncio.to_thread(soundfonts.render_midi_to_audio, stored_p, flac_p, active_sf2)
            )
            _active_sf2_renders[key] = task
    try:
        await task
    finally:
        async with _sf2_render_lock:
            if _active_sf2_renders.get(key) is task:
                _active_sf2_renders.pop(key, None)


@app.get("/api/sources/{source_id}/peaks")
async def source_peaks(source_id: str, sf2: str | None = None) -> dict:
    """The waveform for a recording, cached beside it the way a take's is."""
    source = one("SELECT stored_path, filename FROM sources WHERE id = ?", (source_id,))
    if not source or not Path(source["stored_path"]).exists():
        raise HTTPException(404, "no audio for this recording")
    stored_p = Path(source["stored_path"])
    if (source.get("filename") or "").lower().endswith((".mid", ".midi")):
        active_sf2 = sf2 or soundfonts.get_active_sf2()
        if not active_sf2 or not (soundfonts.sf2_folder() / active_sf2).is_file():
            return {"columns": 128, "peaks": [0.0] * 128, "rms": [0.0] * 128}
        flac_p = stored_p.parent / f"{stored_p.stem}-{active_sf2}.flac"
        if not flac_p.exists() or flac_p.stat().st_size == 0:
            legacy_p = stored_p.with_suffix(".flac")
            if legacy_p.exists() and legacy_p.stat().st_size > 0 and sf2 is None:
                flac_p = legacy_p
        if flac_p.exists():
            peaks = ensure_peaks(flac_p)
            if peaks:
                return peaks
        try:
            await _ensure_source_midi_rendered(stored_p, flac_p, active_sf2)
            peaks = ensure_peaks(flac_p)
            if peaks:
                return peaks
        except Exception as exc:
            log.warning("Could not render peaks for MIDI %s: %s", source_id, exc)
        return {"columns": 128, "peaks": [0.0] * 128, "rms": [0.0] * 128}
    result = ensure_peaks(stored_p)
    if not result:
        raise HTTPException(500, "could not read the waveform")
    return result


@app.get("/api/sources/{source_id}/audio")
def source_audio(source_id: str, format: str | None = None) -> FileResponse:
    source = one("SELECT stored_path, filename FROM sources WHERE id = ?", (source_id,))
    if not source or not Path(source["stored_path"]).exists():
        raise HTTPException(404, "no audio for this source")
    stored_p = Path(source["stored_path"])
    is_midi = (source.get("filename") or "").lower().endswith((".mid", ".midi"))
    if is_midi and format == "audio":
        active_sf2 = soundfonts.get_active_sf2()
        if not active_sf2 or not (soundfonts.sf2_folder() / active_sf2).is_file():
            raise HTTPException(503, "No .sf2 SoundFont available to render MIDI. Place .sf2 files in data/models/soundfonts/sf2.")
        flac_p = stored_p.parent / f"{stored_p.stem}-{active_sf2}.flac"
        if not flac_p.exists() or flac_p.stat().st_size == 0:
            soundfonts.render_midi_to_audio(stored_p, flac_p, sf2_filename=active_sf2)
        return FileResponse(flac_p, filename=Path(source["filename"]).stem + ".flac", media_type="audio/flac")
    media_type = "audio/midi" if is_midi else None
    return FileResponse(stored_p, filename=source["filename"], media_type=media_type)


@app.get("/api/sources/{source_id}/rendered-audio")
async def source_rendered_audio(source_id: str, sf2: str | None = None) -> FileResponse:
    """The high-fidelity SoundFont-rendered audio for a MIDI source, or native audio for non-MIDI."""
    source = one("SELECT stored_path, filename FROM sources WHERE id = ?", (source_id,))
    if not source or not Path(source["stored_path"]).exists():
        raise HTTPException(404, "no audio for this source")
    stored_p = Path(source["stored_path"])
    if not (source.get("filename") or "").lower().endswith((".mid", ".midi")):
        return FileResponse(stored_p, filename=source["filename"])

    active_sf2 = sf2 or soundfonts.get_active_sf2()
    if not active_sf2 or not (soundfonts.sf2_folder() / active_sf2).is_file():
        raise HTTPException(503, "No .sf2 SoundFont available to render MIDI. Place .sf2 files in data/models/soundfonts/sf2.")

    flac_p = stored_p.parent / f"{stored_p.stem}-{active_sf2}.flac"
    if not flac_p.exists() or flac_p.stat().st_size == 0:
        try:
            await _ensure_source_midi_rendered(stored_p, flac_p, active_sf2)
        except Exception as exc:
            log.exception("Failed to render MIDI audio for %s with %s", source_id, active_sf2)
            raise HTTPException(500, f"Failed to render MIDI audio: {exc}")
    rendered_filename = f"{Path(source['filename']).stem}-{active_sf2}.flac"
    return FileResponse(flac_p, filename=rendered_filename, media_type="audio/flac")


@app.post("/api/sources/{source_id}/render-audio")
async def render_source_audio(source_id: str, sf2: str | None = None) -> dict:
    source = one("SELECT stored_path, filename FROM sources WHERE id = ?", (source_id,))
    if not source or not Path(source["stored_path"]).exists():
        raise HTTPException(404, "no audio for this source")
    stored_p = Path(source["stored_path"])
    if not (source.get("filename") or "").lower().endswith((".mid", ".midi")):
        raise HTTPException(400, "source is not a MIDI file")
    active_sf2 = sf2 or soundfonts.get_active_sf2()
    if not active_sf2 or not (soundfonts.sf2_folder() / active_sf2).is_file():
        raise HTTPException(503, "No .sf2 SoundFont available to render MIDI. Place .sf2 files in data/models/soundfonts/sf2.")
    flac_p = stored_p.parent / f"{stored_p.stem}-{active_sf2}.flac"
    await asyncio.to_thread(soundfonts.render_midi_to_audio, stored_p, flac_p, active_sf2)
    peaks = library.ensure_peaks(flac_p)
    return {"status": "ok", "audio_path": str(flac_p), "soundfont": active_sf2, "has_peaks": peaks is not None}



# ---------------------------------------------------------------------- jobs
@app.post("/api/queue/{kind}/{job_id}/cancel")
async def cancel_waiting_job(kind: str, job_id: str) -> dict:
    """Take a job out of Up next before it starts.  One already running is stopped
    from the job card instead."""
    return {"cancelled": await jobs.cancel_waiting(kind, job_id)}


@app.post("/api/jobs/current/cancel")
async def cancel_current_job() -> dict:
    stopped = await jobs.cancel_current()
    return {"cancelled": bool(stopped), "job": stopped}


@app.post("/api/engine/interrupt")
async def interrupt() -> dict:
    """Stops whatever the engine is running, including work this app did not send."""
    await ENGINE.interrupt()
    return {"interrupted": True}


# ------------------------------------------------------------------- settings
@app.get("/api/settings")
def get_settings() -> dict:
    return {"settings": settings_payload()}


@app.put("/api/settings")
def put_setting(body: SettingIn) -> dict:
    save_setting(body.key, body.value)
    return {"settings": settings_payload()}


@app.post("/api/settings/test-llm")
async def test_llm_settings(body: LLMTestIn | None = None) -> dict:
    """Test connection to the external LLM provider using current or provided settings."""
    override = None
    if body:
        override = {}
        if body.api_url is not None:
            override["api_url"] = body.api_url
        if body.api_key:   # empty means the saved key, which the page never sees
            override["api_key"] = body.api_key
        if body.model is not None:
            override["model"] = body.model
        if override:
            current = llm.get_config()
            current.update(override)
            override = current
    log.info("Testing external LLM connection via settings")
    try:
        res = await llm.test_connection(config_override=override)
        return res
    except Exception as exc:
        log.warning("External LLM connection test failed: %s", exc)
        raise HTTPException(400, f"Connection test failed: {exc}")


class LLMModelsIn(BaseModel):
    api_url: str | None = None
    api_key: str | None = None


@app.post("/api/settings/llm-models")
@app.get("/api/settings/llm-models")
async def list_llm_models(body: LLMModelsIn | None = None) -> dict:
    """Fetch available models from the external LLM provider."""
    override = None
    if body:
        override = {}
        if body.api_url is not None:
            override["api_url"] = body.api_url
        if body.api_key:   # empty means the saved key, which the page never sees
            override["api_key"] = body.api_key
        if override:
            current = llm.get_config()
            current.update(override)
            override = current
    try:
        models = await llm.fetch_models(config_override=override)
        return {"models": models}
    except Exception as exc:
        log.warning("Could not list LLM models: %s", exc)
        raise HTTPException(400, f"Could not list models: {exc}")


# ----------------------------------------------------------------------- stems
@app.get("/api/stems/options")
def stems_options() -> dict:
    return {
        "available": stems.installed(),
        "models": [{"id": key, "label": spec["label"], "stems": spec["stems"]} for key, spec in stems.MODELS.items()],
        "formats": stems.FORMATS,
        "default_dir": setting_value("stems.folder"),
        "default_format": setting_value("stems.format"),
        "default_model": setting_value("stems.model"),
        "threads": stems.DEFAULT_THREADS,
        "avg_seconds": float(get_setting("avg_stems_seconds", "0") or 0),
    }


def queue_stems(kind: str, ref_id: str, body: StemsIn) -> dict:
    if kind == "take":
        item = one("SELECT id, title, audio_path FROM takes WHERE id = ?", (ref_id,))
        if not item:
            raise HTTPException(404, "no such take")
        if not item["audio_path"] or not Path(item["audio_path"]).exists():
            raise HTTPException(400, "this take has no audio yet")
        take_id, source_id = item["id"], None
    else:
        item = one("SELECT id, title, filename, stored_path FROM sources WHERE id = ?", (ref_id,))
        if not item:
            raise HTTPException(404, "no such source")
        if (item.get("filename") or "").lower().endswith((".mid", ".midi")):
            raise HTTPException(400, "Stem separation requires an audio recording, not a MIDI file.")
        if not Path(item["stored_path"]).exists():
            raise HTTPException(400, "the file for this recording is missing")
        take_id, source_id = None, item["id"]
    if not stems.installed():
        raise HTTPException(503, "demucs is not installed in this container")
    # An explicit choice wins; otherwise the Settings panel decides.
    model = body.model if body.model in stems.MODELS else setting_value("stems.model")
    if model not in stems.MODELS:
        model = "htdemucs"
    allowed = stems.MODELS[model]["stems"]
    wanted = [s for s in body.stems if s in allowed] or list(allowed)
    fmt = body.format if body.format in stems.FORMATS else setting_value("stems.format")
    if fmt not in stems.FORMATS:
        fmt = "wav"
    set_id = uuid.uuid4().hex[:12]
    # Default destination, or an override that must stay inside the data folder so
    # it survives a container rebuild and lands in the backup.
    wanted_dir = (body.save_dir or "").strip() or setting_value("stems.folder")
    dest = Path(wanted_dir) / f"{slugify(item['title'])}-{set_id}"
    if not inside(dest, config.DATA_DIR):
        raise HTTPException(400, f"the save folder must be inside {config.DATA_DIR}")
    execute(
        """INSERT INTO stem_sets(id, take_id, source_id, title, model, wanted, fmt, status, created_at, folder)
           VALUES(?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?)""",
        (set_id, take_id, source_id, item["title"], model, ",".join(wanted), fmt, time.time(), str(dest)),
    )
    return {"id": set_id, "model": model, "stems": wanted, "format": fmt, "status": "queued"}


@app.post("/api/takes/{take_id}/stems")
async def take_stems(take_id: str, body: StemsIn) -> dict:
    result = queue_stems("take", take_id, body)
    await STEM_QUEUE.put({"id": result["id"]})
    log.info("Queued stem separation for take %s (%s, model=%s, wanted=%s)", take_id, result["id"], body.model, body.stems or "all")
    return result


@app.post("/api/sources/{source_id}/stems")
async def source_stems(source_id: str, body: StemsIn) -> dict:
    result = queue_stems("source", source_id, body)
    await STEM_QUEUE.put({"id": result["id"]})
    log.info("Queued stem separation for source %s (%s, model=%s, wanted=%s)", source_id, result["id"], body.model, body.stems or "all")
    return result


@app.post("/api/sources/{source_id}/lyrics")
async def source_lyrics(source_id: str) -> dict:
    """Hear the words in a recording.  Separating the vocal and listening to it
    takes minutes, so it is asked for rather than done with every transcription,
    and it runs in the CPU lane beside stems, leaving the GPU free."""
    source = one("SELECT * FROM sources WHERE id = ?", (source_id,))
    if not source:
        raise HTTPException(404, "no such recording")
    if (source.get("filename") or "").lower().endswith((".mid", ".midi")):
        raise HTTPException(400, "Lyrics extraction with Whisper requires an audio recording, not a MIDI file.")
    if not Path(source["stored_path"]).exists():
        raise HTTPException(400, "the file for this recording is missing")
    if source["lyrics_state"] in ("queued", "running"):
        return {"state": source["lyrics_state"], "progress": source["lyrics_progress"]}
    execute("UPDATE sources SET lyrics_state = 'queued', lyrics_error = NULL, lyrics_progress = 0,"
            " lyrics_stage = 'Waiting' WHERE id = ?", (source_id,))
    await STEM_QUEUE.put({"kind": "lyrics", "id": source_id})
    log.info("Queued lyrics extraction for source '%s' (%s)", source.get("title") or source_id, source_id)
    return {"state": "queued", "progress": 0.0}


@app.get("/api/sources/{source_id}/lyrics")
def source_lyrics_state(source_id: str) -> dict:
    """What the job is doing, and the words once it has them."""
    source = one("SELECT * FROM sources WHERE id = ?", (source_id,))
    if not source:
        raise HTTPException(404, "no such recording")
    # The words last used for a cover of this recording, for one whose words were typed or pasted and
    # never heard: the recording has none of its own, and the next cover is likely to want the same.
    last_used = one(
        "SELECT lyrics FROM takes WHERE source_id = ? AND kind = 'cover' AND TRIM(COALESCE(lyrics, '')) != ''"
        " ORDER BY created_at DESC LIMIT 1", (source_id,))
    return {
        "state": source["lyrics_state"],
        "progress": source["lyrics_progress"],
        "stage": source["lyrics_stage"],
        "error": source["lyrics_error"],
        "lyrics": source["lyrics"],
        "last_used": last_used["lyrics"] if last_used else None,
        # Whisper, or the external LLM timed by Whisper, or Whisper with the reason
        # the LLM was not used.  None for lyrics heard before this was recorded.
        "method": source["lyrics_method"],
    }


@app.delete("/api/sources/{source_id}/lyrics")
def stop_source_lyrics(source_id: str) -> dict:
    """Stop a running job.  A queued one never starts; a running one is the task
    the CPU lane is holding."""
    source = one("SELECT * FROM sources WHERE id = ?", (source_id,))
    if not source:
        raise HTTPException(404, "no such recording")
    if source["lyrics_state"] == "running" and CURRENT_STEMS.get("id") == source_id:
        CURRENT_STEMS["task"].cancel()
    elif source["lyrics_state"] == "queued":
        execute("UPDATE sources SET lyrics_state = 'failed', lyrics_error = 'cancelled',"
                " lyrics_stage = NULL WHERE id = ?", (source_id,))
    return {"state": "cancelled"}


def stem_files(item: dict) -> list[dict]:
    if not item.get("folder"):
        return []
    folder = Path(item["folder"])
    if not folder.is_dir():
        return []
    return [
        {"name": path.stem, "file": path.name, "bytes": path.stat().st_size}
        for path in sorted(folder.glob(f"*.{item['fmt']}"))
    ]


@app.get("/api/stem-sets")
def list_stem_sets(take_id: str | None = None, source_id: str | None = None) -> list[dict]:
    if take_id:
        sets = rows("SELECT * FROM stem_sets WHERE take_id = ? ORDER BY created_at DESC", (take_id,))
    elif source_id:
        sets = rows("SELECT * FROM stem_sets WHERE source_id = ? ORDER BY created_at DESC", (source_id,))
    else:
        sets = rows("SELECT * FROM stem_sets ORDER BY created_at DESC LIMIT 100")
    for item in sets:
        item["files"] = stem_files(item) if item["status"] == "done" else []
    return sets


def _build_zip(files: list[Path]) -> Path:
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=config.WORK_DIR, prefix="zip-", suffix=".zip")
    os.close(fd)
    with zipfile.ZipFile(name, "w", zipfile.ZIP_STORED) as archive:
        for path in files:
            archive.write(path, arcname=path.name)
    return Path(name)


@app.get("/api/stem-sets/{set_id}/zip")
def stem_zip(set_id: str) -> FileResponse:
    item = one("SELECT * FROM stem_sets WHERE id = ?", (set_id,))
    if not item or not item["folder"]:
        raise HTTPException(404, "no such stem set")
    files = [Path(item["folder"]) / f["file"] for f in stem_files(item)]
    if not files:
        raise HTTPException(404, "this stem set has no files")
    archive = _build_zip(files)
    safe = "".join(ch for ch in (item["title"] or "stems") if ch.isalnum() or ch in " -_")[:60].strip() or "stems"
    return FileResponse(archive, media_type="application/zip", filename=f"{safe} stems.zip",
                        background=BackgroundTask(archive.unlink, missing_ok=True))


def _stem_path(set_id: str, name: str) -> Path:
    """Only names the set actually holds.  Nothing built from the request is trusted."""
    item = one("SELECT * FROM stem_sets WHERE id = ?", (set_id,))
    if not item or not item["folder"]:
        raise HTTPException(404, "no such stem set")
    if name not in {f["file"] for f in stem_files(item)}:
        raise HTTPException(404, "no such stem")
    return Path(item["folder"]) / name


@app.get("/api/stem-sets/{set_id}/{name}/peaks")
def stem_peaks(set_id: str, name: str) -> dict:
    result = ensure_peaks(_stem_path(set_id, name))
    if not result:
        raise HTTPException(500, "could not read the waveform")
    return result


@app.get("/api/stem-sets/{set_id}/{name}")
def stem_file(set_id: str, name: str) -> FileResponse:
    return FileResponse(_stem_path(set_id, name), filename=name)


@app.post("/api/stem-sets/{set_id}/cancel")
async def cancel_stem_set(set_id: str) -> dict:
    item = one("SELECT * FROM stem_sets WHERE id = ?", (set_id,))
    if not item:
        raise HTTPException(404, "no such stem set")
    jobs.cancel_stems(item)
    return {"cancelled": item["status"] in ACTIVE}


@app.delete("/api/stem-sets/{set_id}")
async def delete_stem_set(set_id: str) -> dict:
    item = one("SELECT * FROM stem_sets WHERE id = ?", (set_id,))
    if not item:
        raise HTTPException(404, "no such stem set")
    jobs.cancel_stems(item)
    execute("DELETE FROM stem_sets WHERE id = ?", (set_id,))
    if item["folder"]:
        await asyncio.to_thread(remove_folders, [(Path(item["folder"]), config.DATA_DIR)])
    return {"deleted": True}
