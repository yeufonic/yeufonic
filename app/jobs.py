"""The two job lanes: the GPU lane (transcribe, plan, render) driven through the
engine, and the CPU lane for stems.  Both run in this process."""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from . import config, identities, instrumental, llm, loras, lyrics, score, stems, storage, trainsize, transpose
from .db import bump_average, execute, get_setting, one, rows
from .engine import OUT_OF_MEMORY, Engine, load_template
from .library import (audio_duration, ensure_peaks, fade_out_end, loudness, inside, normal_target, normalise, normalised_path, original_path, remove_tree,
                      take_audio_path, vocal_path, write_take_note)

personas = identities

log = logging.getLogger("yue2.jobs")

ENGINE = Engine(config.ENGINE_URL)
QUEUE: "asyncio.Queue[dict]" = asyncio.Queue()
# Stems get their own lane.  Renders run on the GPU and stems on the CPU, so a
# three minute separation must never sit in front of a render.
STEM_QUEUE: "asyncio.Queue[dict]" = asyncio.Queue()
CURRENT: dict = {}
CURRENT_STEMS: dict = {}
# Ids whose running job was cancelled.  The job notices and stops.
CANCELLED: set[str] = set()
# Renders tried once more because they ended well before their score (in memory:
# a restart forgets, and at worst a take gets a second retry).
RETRIED_EARLY: set[str] = set()
# Plans written once more because the first came out unreadable or runaway (in memory,
# as above).
RETRIED_PLANS: set[str] = set()
# Identity songs being copied in and having their vocal separated, on the CPU.
IDENTITY_QUEUE: "asyncio.Queue[dict]" = asyncio.Queue()
# Corpus songs whose running GPU step was stopped: it goes back to not started, not failed.
STOPPED_SONGS: set[str] = set()
CURRENT_IDENTITY: dict = {}
# GPU steps for an identity song.  Copying in, the vocal and the lyrics run on the CPU.
IDENTITY_FIELDS = {
    "identity_score": "score_state", "identity_style": "style_state",
    "persona_score": "score_state", "persona_style": "style_state",
}
PERSONA_QUEUE = IDENTITY_QUEUE
CURRENT_PERSONA = CURRENT_IDENTITY
PERSONA_FIELDS = IDENTITY_FIELDS
# Lyric drafts, by id.  Kept in memory only: a draft is copied into the form as soon
# as it lands, so nothing is lost when the app restarts.
LYRICS: dict[str, dict] = {}
LYRICS_KEEP = 3600   # seconds a finished draft stays readable


# ------------------------------------------------------------------- templates
def build_transcribe_graph(engine_file: str) -> dict:
    graph = load_template("transcribe.json")
    graph["1"]["inputs"]["audio"] = engine_file
    return graph


# The ABC sampler settings behind the "plan variety" control.
# The vendor default is temperature 0.7 with a repetition penalty of 1.005, which
# lets a four-bar loop repeat for a whole song. A higher penalty pushes back on that.
# The penalty hits every token, bar lines and voice headers included, so too much of
# it breaks the score: wild used to be 1.25 / 1.18 and broke 6 of 6 test plans.
# 1.15 / 1.08 kept every test plan readable and still varies more than bold.
# How freely the planner writes.  The repetition penalty is the lever: it pushes against
# every recently used token, chords and melody notes alike, so a strong one keeps the plan
# moving to new chords and new registers.  Temperature matters little between 0.55 and 1.0.
# Measured on plans alone, 8 per step: from calm to bold the chord vocabulary grows about
# threefold while the melody stays within two octaves; at 1.08 it spans five and jumps
# register between sections, and wild changes key.
PLAN_VARIETY = {
    "calm": {"temperature": 0.55, "repetition_penalty": 1.0},
    "normal": {"temperature": 0.7, "repetition_penalty": 1.005},
    "lively": {"temperature": 0.85, "repetition_penalty": 1.02},
    "bold": {"temperature": 1.0, "repetition_penalty": 1.03},
    "quirky": {"temperature": 1.0, "repetition_penalty": 1.08},
    "wild": {"temperature": 1.15, "repetition_penalty": 1.08},
}


# The Harmony control.  Each step is a setting of the yue2_harmony node, measured
# against the stock planner on the same lyrics and seeds, on indie pop and on
# minor-key rock (see the README).  Every step caps a held root at 8 bars: without
# the cap, Colourful sat on one chord for 30 bars on rock.
#   Familiar     the stock planner: often one four-chord loop for the whole song
#   Varied       recently used chords are discouraged by their exact spelling
#   Colourful    the same, harder: verse and chorus part ways, richer chords
#   Adventurous  recently used roots are discouraged, so the harmony has to move;
#                borrowed chords appear
#   Outside      adventurous, plus a pull towards roots outside the key
HARMONY_NODE = "YuE2GenerateABCHarmony"
HARMONY_STEPS = ["Familiar", "Varied", "Colourful", "Adventurous", "Outside"]
HARMONY_OFF = {"chord_identity": "root", "chord_strength": 0.0, "chord_window": 16, "hold_limit": 8,
               "outside_bonus": 0.0, "outside_limit": 0.25, "section_strength": 0.0, "section_open": 4}
# From Colourful up, a section may not open the way the one before it did (see the node).
SECTION_STRENGTH = 8.0
HARMONY = {
    1: {"chord_identity": "spelling", "chord_strength": 8.0},
    2: {"chord_identity": "spelling", "chord_strength": 16.0, "section_strength": SECTION_STRENGTH},
    3: {"chord_identity": "root", "chord_strength": 32.0, "section_strength": SECTION_STRENGTH},
    4: {"chord_identity": "root", "chord_strength": 32.0, "outside_bonus": 3.0, "section_strength": SECTION_STRENGTH},
}


# How the render reads the score: the music sampler's settings, one named set each.
# Standard is YuE2's own default.  The names describe the result, not the numbers.
INTERPRETATIONS = {
    "standard": {"temperature": 1.0, "top_p": 0.95, "top_k": 100, "repetition_penalty": 1.2},
    "tight": {"temperature": 0.8},
    "loose": {"temperature": 1.2},
    "settled": {"repetition_penalty": 1.0},
    "restless": {"repetition_penalty": 1.35},
    "wide": {"top_k": 250, "top_p": 0.99},
}
INTERPRETATION_NAMES = {
    "standard": "Standard", "tight": "Tight", "loose": "Loose",
    "settled": "Settled", "restless": "Restless", "wide": "Wide",
}


def interpretation_sampling(name: str | None) -> dict:
    return {**INTERPRETATIONS["standard"], **INTERPRETATIONS.get(name or "standard", {})}


def feel_strength(take: dict) -> float:
    return instrumental.FEELS.get(take.get("feel") or "steady", instrumental.FEELS["steady"])


KEY_IN_STYLE = re.compile(r"(?i)\bkey of\s+[A-G][#b]?(?:\s*(?:major|minor|maj|min)|m)?(?![a-z#])")
BPM_IN_STYLE = re.compile(r"(?i)\b\d{2,3}\s*bpm\b")


def key_phrase(key: str) -> str:
    """A key as the planner's training captions say it: 'key of C# minor', not 'Cm'."""
    found = re.fullmatch(r"\s*([A-Ga-g][#b]?)\s*(m|min|minor|maj|major)?\s*", str(key))
    if not found:
        return f"key of {str(key).strip()}"
    root = found.group(1)[0].upper() + found.group(1)[1:]
    minor = (found.group(2) or "").lower() in ("m", "min", "minor")
    return f"key of {root} {'minor' if minor else 'major'}"


def effective_style(style: str, target_key: str | None = None, target_bpm: int | None = None, avoid: str | None = None) -> str:
    """The style the planner and the render read, with the locks said once.  A key or a tempo the
    style already names is replaced, not added to: 'a 104 BPM groove' and '80 BPM' together are
    two instructions, and the planner followed neither."""
    text = (style or "").strip()
    if target_key and str(target_key).strip():
        phrase = key_phrase(target_key)
        text = KEY_IN_STYLE.sub(phrase, text) if KEY_IN_STYLE.search(text) else ", ".join(p for p in (text, phrase) if p)
    if target_bpm:
        phrase = f"{int(target_bpm)} BPM"
        text = BPM_IN_STYLE.sub(phrase, text) if BPM_IN_STYLE.search(text) else ", ".join(p for p in (text, phrase) if p)
    if avoid and str(avoid).strip():
        wanted = str(avoid).strip()
        if wanted.lower() not in text.lower():
            text = ", ".join(p for p in (text, wanted if wanted.lower().startswith("avoid") else f"avoid: {wanted}") if p)
    return text


def build_plan_graph(take: dict) -> dict:
    """Write a score plan from the style and lyrics alone. No recording involved."""
    graph = load_template("song_plan.json")
    graph["1"]["inputs"]["ckpt_name"] = config.CHECKPOINT
    node = graph["2"]["inputs"]
    node["style"] = effective_style(take["style"], target_key=take.get("target_key"),
                                    target_bpm=take.get("target_bpm"), avoid=take.get("avoid"))
    node["lyrics"] = take["lyrics"]
    node["seed"] = int(take["seed"])
    node["mode"] = "full"
    node["max_abc_tokens"] = int(take.get("max_abc_tokens") or 8192)
    variety = PLAN_VARIETY.get(take.get("variety") or "normal", PLAN_VARIETY["normal"])
    node["temperature"] = variety["temperature"]
    node["repetition_penalty"] = variety["repetition_penalty"]
    step = int(take.get("harmony") or 0)
    hold_limit = int(take["chord_hold_limit"]) if take.get("chord_hold_limit") is not None else 8
    outside_bonus = float(take["chord_outside_bonus"]) if take.get("chord_outside_bonus") is not None else 0.0
    if step in HARMONY or hold_limit != 8 or outside_bonus != 0.0:
        graph["2"]["class_type"] = HARMONY_NODE
        node.update({**HARMONY_OFF, **HARMONY.get(step, {})})
        if take.get("chord_hold_limit") is not None:
            node["hold_limit"] = hold_limit
        if take.get("chord_outside_bonus") is not None and (step != 4 or outside_bonus != 0.0):
            node["outside_bonus"] = outside_bonus
    if take.get("kind") == "instrumental":
        instrumental.with_lora(graph, "1", config.INSTRUMENTAL_LORA, ("2",), feel_strength(take))
    style_lora = take.get("style_lora")
    if style_lora:
        with_plan_lora(graph, "1", style_lora, ("2",), float(take.get("style_lora_clip") or 0.0))
    voice_lora = take.get("voice_lora")
    voice_clip = float(take.get("voice_lora_clip") or 0.0)
    if voice_lora and voice_clip and voice_lora != style_lora:
        with_plan_lora(graph, "1", voice_lora, ("2",), voice_clip, node_id="22")
    return graph


def with_plan_lora(graph: dict, loader: str, lora: str, text_nodes: tuple[str, ...],
                   strength_clip: float = 1.0, node_id: str = "21") -> dict:
    """Put a style LoRA in front of the planner, where its planner half does its
    work: the plan is written in its own run, before any audio exists.

    It chains onto whatever already feeds those text nodes rather than replacing
    it, so an instrumental keeps its own LoRA and gains this one."""
    upstream = graph[text_nodes[0]]["inputs"].get("clip") or [loader, 1]
    graph[node_id] = {"class_type": "LoraLoader", "inputs": {
        "model": [loader, 0], "clip": upstream, "lora_name": lora,
        "strength_model": 0.0, "strength_clip": strength_clip}}
    for node in text_nodes:
        graph[node]["inputs"]["clip"] = [node_id, 1]
    return graph


def with_render_lora(graph: dict, node_id: str, lora: str, loader: str = "10", strength_model: float = 1.0, strength_clip: float = 0.0) -> dict:
    """Put a LoRA into the render: its sound half before KSampler, and, when
    strength_clip is above 0, its planner half before YuE2GenerateMusic.

    A render has two language-model steps, not one.  The plan writes the score;
    then YuE2GenerateMusic reads that score and writes the music tokens the
    decoder turns into audio.  A LoRA's planner half belongs in both.  It used to
    reach only the first, because strength_clip was set here and its output was
    never connected, so the render wrote its music tokens without it.  Measured on
    one take, same score and seed: adding it changed the render almost entirely
    (correlation 0.145, against 1.000 for the same render run twice).

    Both halves chain onto what is already there, as the model side always has,
    so an instrumental keeps its own LoRA and gains this one.  At strength_clip 0
    the text side is left exactly as it was."""
    current_model = graph["14"]["inputs"]["model"]
    wire_clip = strength_clip > 0
    graph[node_id] = {
        "class_type": "LoraLoader",
        "inputs": {
            "model": current_model,
            "clip": (graph["11"]["inputs"].get("clip") or [loader, 1]) if wire_clip else [loader, 1],
            "lora_name": lora,
            "strength_model": strength_model,
            "strength_clip": strength_clip,
        },
    }
    graph["14"]["inputs"]["model"] = [node_id, 0]
    if wire_clip:
        graph["11"]["inputs"]["clip"] = [node_id, 1]
    return graph


def with_realaudio_lora(graph: dict, loader: str = "10", lora: str | None = None, strength: float = 1.0) -> dict:
    """Put the Realaudio decoder LoRA between the checkpoint and KSampler. The text/CLIP
    side is left alone (strength 0.0), so the ABC planner and language model are untouched."""
    lora_name = lora or config.REAL_AUDIO_LORA
    return with_render_lora(graph, "25", lora_name, loader=loader, strength_model=strength, strength_clip=0.0)


def with_style_lora(graph: dict, lora: str, loader: str = "10",
                    strength_model: float = 1.0, strength_clip: float = 1.0) -> dict:
    """Put a style LoRA from elsewhere between the checkpoint and KSampler.

    Unlike the app's own two, both strengths are the caller's to set.  A style
    LoRA usually holds both halves, and the planner half is the one that changes
    what is written, so switching it off quietly is the wrong default."""
    return with_render_lora(graph, "27", lora, loader=loader,
                            strength_model=strength_model, strength_clip=strength_clip)


def with_identity_lora(graph: dict, lora: str, loader: str = "10", strength: float = 1.0,
                       strength_clip: float = 0.0) -> dict:
    """Put the Identity voice LoRA between the checkpoint (or upstream LoRA) and KSampler.

    The voice lives in the decoder half, which is what `strength` sets and what
    this has always applied.  An Identity trained by the FS_Audio pipeline also
    holds a planner half — how that singer writes, not how they sound — and
    `strength_clip` is that, off unless asked for."""
    return with_render_lora(graph, "26", lora, loader=loader, strength_model=strength,
                            strength_clip=strength_clip)


with_persona_lora = with_identity_lora


def with_peak_guard(graph: dict, ceiling_db: float | None = None) -> dict:
    """The engine's peak guard between the decode and the save.  It works on the floating
    point audio, turns it down around any peak that would clip and leaves the rest alone,
    where the 16-bit save would flatten those peaks."""
    graph["30"] = {"class_type": "Yue2PeakGuard", "inputs": {
        "audio": ["15", 0], "ceiling_db": config.PEAK_CEILING_DB if ceiling_db is None else ceiling_db,
        "window_ms": 8.0}}
    graph["16"]["inputs"]["audio"] = ["30", 0]
    return graph


def lock_tempo(abc: str, bpm) -> str:
    """The score at a locked tempo: every Q: header and inline [Q:...] change says
    `bpm`, and a score with none gets one after its L: line.  No lock, no change."""
    if not bpm or not abc or not abc.strip():
        return abc
    bpm = int(bpm)
    out = re.sub(r"^Q:.*$", f"Q:1/4={bpm}", abc, flags=re.M)
    out = re.sub(r"\[Q:[^\]]*\]", f"[Q:1/4={bpm}]", out)
    if not re.search(r"^Q:", out, re.M):
        lines = out.split("\n")
        at = next((i for i, l in enumerate(lines) if l.strip().startswith("L:")), -1)
        lines.insert(at + 1 if at >= 0 else 1, f"Q:1/4={bpm}")
        out = "\n".join(lines)
    return out


def build_render_graph(take: dict) -> dict:
    graph = load_template("render.json")
    graph["10"]["inputs"]["ckpt_name"] = config.CHECKPOINT
    node = graph["11"]["inputs"]
    node.update(interpretation_sampling(take.get("interpretation")))
    node["style"] = effective_style(take["style"], target_key=take.get("target_key"),
                                    target_bpm=take.get("target_bpm"), avoid=take.get("avoid"))
    node["lyrics"] = take["lyrics"]
    # Strip embedded w: lyric lines from ABC before sending to YuE2.
    # The UI uses w: lines for piano roll display, but YuE2's language model
    # expects standard score notation and gets token pollution from w: lines.
    abc_raw = take["abc"] or ""
    abc_clean = "\n".join(
        line for line in abc_raw.splitlines()
        if not line.strip().startswith(("w:", "W:"))
    )
    node["abc"] = lock_tempo(abc_clean, take.get("target_bpm"))
    node["seed"] = int(take["seed"])
    node["mode"] = take["mode"]
    node["max_duration"] = float(take.get("max_duration") or 360)
    # The notes come from the seed on node 11; the noise the decoder shapes into sound
    # comes from this one.  A sound seed of its own draws a new voice over the same notes.
    graph["14"]["inputs"]["seed"] = int(take.get("sound_seed") or take["seed"])
    graph["14"]["inputs"]["steps"] = int(take.get("sampler_steps") or 32)
    # A prefix unique to this run.  ComfyUI caches an output node whose inputs have
    # not changed and answers with the file it saved last time, which the app has
    # already taken and deleted.  With a new prefix only the save runs again.
    graph["16"]["inputs"]["filename_prefix"] = f"yeufonic/{take['id']}-{int(time.time() * 1000)}"
    # First, because it takes the text side straight from the checkpoint rather than
    # chaining.  Anything added after it chains onto it, the same order the plan
    # graph uses; added last, it silently dropped a style LoRA's planner half.
    if take.get("kind") == "instrumental":
        node["mode"] = "full"
        instrumental.with_lora(graph, "10", config.INSTRUMENTAL_LORA, ("11",), feel_strength(take))
    if take.get("realaudio"):
        with_realaudio_lora(graph, "10", config.REAL_AUDIO_LORA)
    voice_lora = take.get("voice_lora")
    style_lora = take.get("style_lora")
    # The same file can be reached two ways: as an Identity's voice, which is
    # applied model-side only, and as a style LoRA, which is applied on both.
    # Chaining it twice would double it, so the style picker wins: it is the
    # more explicit of the two, and it carries both strengths.
    if voice_lora and voice_lora != style_lora:
        strength = float(take.get("voice_lora_strength") or 1.0)
        with_identity_lora(graph, voice_lora, loader="10", strength=strength,
                           strength_clip=float(take.get("voice_lora_clip") or 0.0))
    if style_lora:
        with_style_lora(graph, style_lora, loader="10",
                        strength_model=float(take.get("style_lora_model") or 0.0),
                        strength_clip=float(take.get("style_lora_clip") or 0.0))
    if config.PEAK_GUARD and (getattr(ENGINE, "options", None) or {}).get("peak_guard"):
        with_peak_guard(graph)
    return graph


def build_lyrics_graph(record: dict) -> dict:
    """Gemma through ComfyUI's own text nodes.  Built here rather than from a
    template, so an engine without them still passes the compatibility check."""
    prompt = lyrics.build_prompt(record["brief"], record["style"], record["structure"],
                                 lines=record.get("lines") or lyrics.DEFAULT_LINES, sections=record.get("sections"))
    return {
        "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": config.LYRICS_MODEL, "type": "stable_diffusion"}},
        "2": {"class_type": "TextGenerate", "inputs": {
            "clip": ["1", 0], "prompt": prompt, "max_length": 900, "thinking": False,
            "sampling_mode": "on", "sampling_mode.temperature": 0.8, "sampling_mode.top_k": 64,
            "sampling_mode.top_p": 0.95, "sampling_mode.min_p": 0.05, "sampling_mode.repetition_penalty": 1.05,
            "sampling_mode.seed": int(record["seed"])}},
        "3": {"class_type": "PreviewAny", "inputs": {"source": ["2", 0]}},
    }


def forget_old_lyrics(now: float | None = None) -> None:
    now = now or time.time()
    for key in [k for k, r in LYRICS.items() if r["status"] in ("done", "failed") and now - r["created_at"] > LYRICS_KEEP]:
        del LYRICS[key]


def _outputs_of(job: dict, class_types: tuple[str, ...]) -> list[dict]:
    prompt = (job or {}).get("prompt") or []
    graph = prompt[2] if len(prompt) > 2 else {}
    wanted = {nid for nid, node in graph.items() if node.get("class_type") in class_types}
    return [out for nid, out in ((job or {}).get("outputs") or {}).items() if nid in wanted]


def extract_text_output(job: dict, *class_types: str) -> str | None:
    """Pull a node's text output out of a finished history record."""
    for out in _outputs_of(job, class_types):
        text = out.get("text")
        if isinstance(text, list) and text and isinstance(text[0], str):
            return text[0]
    return None


def extract_audio_item(job: dict, class_type: str) -> dict | None:
    for out in _outputs_of(job, (class_type,)):
        audio = out.get("audio")
        if isinstance(audio, list) and audio:
            return audio[0]
    return None


# ----------------------------------------------------------------------- GPU lane
def fail(kind: str, ref_id: str, message: str) -> None:
    title = None
    if kind in ("plan", "render"):
        row = one("SELECT title FROM takes WHERE id = ?", (ref_id,))
        title = row["title"] if row else None
    elif kind in ("transcribe", "lyrics"):
        row = one("SELECT title FROM sources WHERE id = ?", (ref_id,))
        title = row["title"] if row else None
    title_str = f" for '{title}'" if title else ""
    log.warning("%s %s%s failed: %s", kind, ref_id, title_str, message)
    if kind == "lyrics":
        if ref_id in LYRICS:
            LYRICS[ref_id].update({"status": "failed", "error": message})
    elif kind == "transcribe":
        execute("UPDATE sources SET transcribe_state = 'failed', transcribe_error = ? WHERE id = ?", (message, ref_id))
    else:
        execute("UPDATE takes SET status = 'failed', error = ?, stage = NULL WHERE id = ?", (message, ref_id))


async def _ensure_engine_file(source: dict) -> str:
    """Upload the recording now.  Doing it at transcribe time, not at upload time,
    means a failed or lost upload is simply retried, and an engine that was
    replaced or wiped still gets the file."""
    path = Path(source["stored_path"])
    # Ended cleanly (see _ended_copy): a song whose last chord is still ringing as the
    # file ends is otherwise refused whole.  This copy is only ever transcribed.
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    ended = config.WORK_DIR / f"transcribe-{source['id']}.flac"
    try:
        await asyncio.to_thread(_ended_copy, path, ended)
        data = await asyncio.to_thread(ended.read_bytes)
    finally:
        ended.unlink(missing_ok=True)
    result = await ENGINE.upload(f"{source['id']}.flac", data)
    name = result.get("name")
    if not name:
        raise RuntimeError("the engine did not accept the recording")
    execute("UPDATE sources SET engine_file = ? WHERE id = ?", (name, source["id"]))
    return name


async def _wait_for(kind: str, ref_id: str, prompt_id: str) -> tuple[str, dict | None]:
    """Poll until the prompt finishes.  Returns ('done', job), ('cancelled', None),
    ('timeout', None) or ('lost', None).  The time limit starts when the engine
    starts executing, so a wait in the engine's own queue does not count."""
    limit = config.TIMEOUTS[kind]
    deadline = None
    last_queue_check = 0.0
    while True:
        await asyncio.sleep(1.5)
        if ref_id in CANCELLED:
            return "cancelled", None
        job = None
        try:
            job = await ENGINE.history(prompt_id)
        except Exception as exc:  # noqa: BLE001
            log.debug("history poll failed: %s", exc)
        if job and job.get("status", {}).get("completed") is not None and job.get("status", {}).get("status_str"):
            return "done", job
        now = time.time()
        if now - ENGINE.last_contact > config.ENGINE_LOST_AFTER:
            return "lost", None
        if deadline is None and limit and ENGINE.has_started(prompt_id):
            deadline = now + limit
        if deadline is not None and now > deadline:
            return "timeout", None
        # The queue is asked even once the job runs: an engine that restarts mid-job
        # comes back without it, and waiting out the time limit (hours, for training)
        # would leave the job looking frozen.
        if now - last_queue_check > 6:
            last_queue_check = now
            state = await ENGINE.prompt_state(prompt_id)
            if state == "running" and deadline is None and limit:
                deadline = now + limit
            elif state == "running" and _engine_fault(prompt_id):
                # Its thread died and the engine stayed up, still listing the job as
                # running: nothing more will happen to it, or to anything after it.
                ENGINE.stuck_on = prompt_id
                log.warning("the engine's job thread died on %s; the engine needs a restart", prompt_id)
                return "dead", None
            elif state == "gone":
                # Finished between the two calls, or the engine restarted.
                try:
                    job = await ENGINE.history(prompt_id)
                except Exception:  # noqa: BLE001
                    job = None
                if job:
                    continue
                return "lost", None


async def run_job(kind: str, ref_id: str) -> None:
    started = time.time()
    record = None
    if kind in IDENTITY_FIELDS:
        await run_identity_job(kind, ref_id)
        return
    if kind == "train":
        # A run queued before training was switched off must not start when the app
        # comes back up without it.
        if not config.TRAINING_ENABLED:
            _run_state(ref_id, state="failed", error="training is switched off",
                       finished_at=time.time())
            return
        await run_lora_train(ref_id)
        return
    if kind == "lyrics":
        record = LYRICS.get(ref_id)
        if not record or record["status"] != "queued":
            return   # cancelled while it waited
        record["status"] = "running"
        if llm.is_external_enabled():
            log.info("Starting external LLM lyrics generation for draft %s (structure=%s, brief='%s')",
                     ref_id, ", ".join(record.get("sections") or []) or record.get("structure"), (record.get("brief") or "")[:40])
            CURRENT.clear()
            CURRENT.update({"kind": kind, "id": ref_id, "prompt_id": None, "started": started})
            try:
                result = await llm.generate_lyrics(
                    brief=record["brief"],
                    style=record["style"],
                    structure=record["structure"],
                    lines=record.get("lines") or lyrics.DEFAULT_LINES,
                    sections=record.get("sections"),
                )
                if ref_id in CANCELLED:
                    fail(kind, ref_id, "cancelled")
                    return
                record["title"] = result["title"]
                record["lyrics"] = result["lyrics"]
                record["status"] = "done"
                record["error"] = None
                log.info("Finished external LLM lyrics generation for draft %s ('%s', %d chars)",
                         ref_id, record["title"], len(record["lyrics"]))
                return
            except Exception as exc:
                log.exception("External LLM lyrics generation failed for draft %s: %s", ref_id, exc)
                fail(kind, ref_id, f"external LLM failed: {exc}")
                return
            finally:
                CURRENT.clear()
                CANCELLED.discard(ref_id)
        log.info("Starting lyrics generation for draft %s (structure=%s)", ref_id, record.get("structure"))
        graph = build_lyrics_graph(record)
    elif kind == "transcribe":
        record = one("SELECT * FROM sources WHERE id = ?", (ref_id,))
        if not record or record["transcribe_state"] != "queued":
            return   # deleted or cancelled while it waited
        execute("UPDATE sources SET transcribe_state = 'running', transcribe_error = NULL WHERE id = ?", (ref_id,))
        log.info("Starting audio transcription for source '%s' (%s)", record.get("title") or ref_id, ref_id)
        try:
            graph = build_transcribe_graph(await _ensure_engine_file(record))
        except Exception as exc:  # noqa: BLE001
            fail(kind, ref_id, f"could not send the recording to the engine: {exc}")
            return
    else:
        record = one("SELECT * FROM takes WHERE id = ?", (ref_id,))
        if not record or record["status"] != "queued":
            return   # deleted or cancelled while it waited
        graph = build_plan_graph(record) if kind == "plan" else build_render_graph(record)
        execute("UPDATE takes SET status = 'running', error = NULL, stage = NULL WHERE id = ?", (ref_id,))
        title = record.get("title") or ref_id
        if kind == "plan":
            log.info("Starting score plan for '%s' (%s, %s, variety=%s, harmony=%s)",
                     title, ref_id, record.get("kind", "song"),
                     record.get("variety", "normal"), record.get("harmony", "familiar"))
        else:
            style_info = f", style_lora={record.get('style_lora')}" if record.get("style_lora") else ""
            voice_info = f", voice_lora={record.get('voice_lora')}" if record.get("voice_lora") else ""
            log.info("Starting audio render for '%s' (%s, mode=%s%s%s)",
                     title, ref_id, record.get("mode", "full"),
                     style_info, voice_info)

    try:
        prompt_id = await ENGINE.submit(graph)
    except Exception as exc:  # noqa: BLE001
        fail(kind, ref_id, str(exc))
        return

    CURRENT.clear()
    CURRENT.update({"kind": kind, "id": ref_id, "prompt_id": prompt_id, "started": started})
    if kind in ("plan", "render"):
        execute("UPDATE takes SET prompt_id = ? WHERE id = ?", (prompt_id, ref_id))
    try:
        outcome, job = await _wait_for(kind, ref_id, prompt_id)
        if outcome != "done":
            if outcome in ("cancelled", "timeout"):
                await ENGINE.cancel(prompt_id)
            messages = {"cancelled": "cancelled", "timeout": "timed out while the engine was working",
                        "lost": _lost(kind, started, prompt_id) or "the engine lost this job, or stopped answering",
                        "dead": (_lost(kind, started, prompt_id) or "the engine stopped running jobs.") + RESTART}
            fail(kind, ref_id, messages[outcome])
            return
        await _finish(kind, ref_id, record, job, started)
    finally:
        ENGINE.forget(prompt_id)
        CURRENT.clear()
        CANCELLED.discard(ref_id)


async def _finish(kind: str, ref_id: str, record: dict, job: dict, started: float) -> None:
    status_str = job.get("status", {}).get("status_str")
    if ref_id in CANCELLED:
        fail(kind, ref_id, "cancelled")
        return
    if status_str != "success":
        detail = json.dumps(job.get("status", {}).get("messages") or [])[-500:]
        fail(kind, ref_id, _engine_failure(kind, job) or f"engine reported {status_str}: {detail}")
        return

    if kind == "lyrics":
        text = extract_text_output(job, "TextGenerate", "PreviewAny")
        draft = lyrics.parse(text or "")
        if draft["problems"]:
            fail(kind, ref_id, "the draft came out without song sections. Write again.")
            return
        record.update({"status": "done", "title": draft["title"], "lyrics": draft["lyrics"],
                       "finished_at": time.time(), "error": None})
        log.info("Lyrics generation finished for '%s' in %.1fs", draft["title"] or ref_id, time.time() - started)
        return

    if kind == "transcribe":
        abc = extract_text_output(job, "SheetSage2AudioToABC", "PreviewAny")
        if not abc:
            fail(kind, ref_id, "the engine returned no score")
            return
        execute(
            "UPDATE sources SET abc = ?, abc_updated_at = ?, transcribe_state = 'done', transcribe_error = NULL WHERE id = ?",
            (abc, time.time(), ref_id),
        )
        log.info("Audio transcription finished for source '%s' in %.1fs", record.get("title") or ref_id, time.time() - started)
        return

    if kind == "plan":
        abc = extract_text_output(job, "YuE2GenerateABC", "PreviewAny")
        if not abc:
            fail(kind, ref_id, "the engine returned no score plan")
            return
        # The planner reads "80 BPM" in the style as a hint and may write its own Q:.
        # A tempo lock is a lock: the score is made to say it, before the checks
        # below measure its length at that tempo.
        abc = lock_tempo(abc, record.get("target_bpm"))
        # The planner ignores a key in the style (measured), so the key is a lock on the finished plan.
        if record.get("target_key"):
            moved = transpose.to_key(abc, record["target_key"])
            if moved is None:
                log.warning("Plan for '%s': could not move it to %s (not one key it can read), keeping the planner's key",
                            record.get("title") or ref_id, record["target_key"])
            else:
                abc = moved
        is_inst = record.get("kind") == "instrumental"
        # Words to sing: lines that are not section tags.  A song of tags alone has no vocal to miss.
        has_words = any(line.strip() and not line.strip().startswith("[") for line in (record.get("lyrics") or "").splitlines())
        issues = score.problems(abc, instrumental=is_inst) or score.runaway(
            abc, instrumental=is_inst, cap=float(record.get("max_duration") or 0), vocal=has_words)
        # A plan that lost its thread is written once more with a new seed before anyone
        # is told; a second in a row fails, with advice on the settings (#5).
        if issues and ref_id not in RETRIED_PLANS:
            RETRIED_PLANS.add(ref_id)
            seed = int.from_bytes(os.urandom(4), "big")
            execute("UPDATE takes SET status = 'queued', stage = NULL, seed = ?, sound_seed = NULL WHERE id = ?", (seed, ref_id))
            log.info("Plan for '%s' came out unreadable (%s); writing it once more with seed %d",
                     record.get("title") or ref_id, ", ".join(issues), seed)
            await QUEUE.put({"kind": "plan", "id": ref_id})
            return
        RETRIED_PLANS.discard(ref_id)
        if issues:
            advice_parts = []
            clip_val = float(record.get("style_lora_clip") or 0.0)
            harmony_val = int(record.get("harmony") or 0)
            variety_val = record.get("variety")
            if is_inst and record.get("style_lora") and clip_val > 0.6:      # a take with no LoRA still stores a strength
                advice_parts.append(f"lower style LoRA Planner strength ({clip_val:.2f}) to ~0.50–0.60")
            if harmony_val > 0:
                advice_parts.append("set Harmony to Familiar")
            if variety_val in ("bold", "quirky", "wild"):
                advice_parts.append("choose a calmer Plan variety")
            if len([tag for tag in (record.get("style") or "").split(",") if tag.strip()]) <= 3:
                advice_parts.append("describe the style in more detail: genre, instruments and feel")
            if variety_val == "calm" and record.get("style_lora"):
                advice_parts.append("choose Normal Plan variety, which loops less with a style LoRA")
            advice = f". Try to {', or '.join(advice_parts)}" if advice_parts else ""
            # A style LoRA's later checkpoints can collapse where an earlier one writes a readable plan.
            again = "Write a new plan or try a different checkpoint" if record.get("style_lora") else "Write a new plan"
            fail(kind, ref_id, f"the plan came out unreadable twice ({', '.join(issues)}). {again}{advice}.")
            return
        elapsed = time.time() - started
        changed = execute(
            "UPDATE takes SET abc = ?, status = 'planned', stage = NULL, error = NULL, elapsed = ? WHERE id = ? AND status = 'running'",
            (abc, elapsed, ref_id),
        )
        bump_average("plan", elapsed)
        log.info("Score plan finished for '%s' in %.1fs", record.get("title") or ref_id, elapsed)
        # An instrumental whose plan has a melody in the Vocal voice will sing.
        # That is knowable now, before the render is paid for, so the take waits
        # to be looked at rather than being rendered automatically.
        if changed and record.get("kind") == "instrumental" and instrumental.sings(abc):
            execute("UPDATE takes SET error = ? WHERE id = ?",
                    ("the plan has a melody in the vocal part: this may sing", ref_id))
            log.info("instrumental %s planned a vocal line; not auto-rendering", ref_id)
            return
        if changed and record.get("auto_render"):
            execute("UPDATE takes SET status = 'queued' WHERE id = ?", (ref_id,))
            await QUEUE.put({"kind": "render", "id": ref_id})
            log.info("auto-render queued for '%s' (%s)", record.get("title") or ref_id, ref_id)
        return

    item = extract_audio_item(job, "SaveAudioAdvanced")
    if not item:
        fail(kind, ref_id, "the engine returned no audio file")
        return
    dest = take_audio_path(ref_id, record.get("title") or ref_id)
    try:
        await ENGINE.download(item, dest)
    except Exception as exc:  # noqa: BLE001
        fail(kind, ref_id, f"could not fetch the audio: {exc}")
        return
    _drop_engine_output(item)
    # The take may have been deleted or cancelled while the file came down.
    if ref_id in CANCELLED or not one("SELECT id FROM takes WHERE id = ?", (ref_id,)):
        remove_tree(dest.parent)
        return
    # A new render replaces any level set before, and the louder copy made from the
    # last one.  One still open somewhere is overwritten when this take is next normalised.
    for stale in (normalised_path(dest), original_path(dest)):
        with contextlib.suppress(OSError):
            stale.unlink(missing_ok=True)
    # Ended long before its score: the model wrote its end early (about one render in
    # eighty, most of them instrumentals). Tried once more with a new seed before
    # anyone is told it's ready; a second early end is kept, and its card says so.
    if kind == "render" and ref_id not in RETRIED_EARLY:
        rendered_for = await asyncio.to_thread(audio_duration, dest)
        if score.stopped_early(rendered_for, record.get("abc"), float(record.get("max_duration") or 0)):
            RETRIED_EARLY.add(ref_id)
            with contextlib.suppress(OSError):
                dest.unlink(missing_ok=True)
            seed = int.from_bytes(os.urandom(4), "big")
            execute("UPDATE takes SET status = 'queued', stage = NULL, seed = ?, sound_seed = NULL WHERE id = ?", (seed, ref_id))
            log.info("Render of '%s' stopped at %.0fs, well before its score; trying once more with seed %d",
                     record.get("title") or ref_id, rendered_for or 0, seed)
            await QUEUE.put({"kind": "render", "id": ref_id})
            return
    RETRIED_EARLY.discard(ref_id)
    # Stopped by the length cap, not by its own ending: fade it out rather than leave
    # it cut off mid-bar, before its level is read or a louder copy is made (#24).
    cap = float(record.get("max_duration") or 0)
    if cap:
        rendered_for = await asyncio.to_thread(audio_duration, dest)
        if rendered_for and rendered_for >= cap - 0.5:
            fade_seconds = float(record.get("fade_out_seconds") or 3.0)
            try:
                await asyncio.to_thread(fade_out_end, dest, fade_seconds)
            except Exception as exc:  # noqa: BLE001
                log.warning("Could not fade out '%s' at its length cap: %s", record.get("title") or ref_id, exc)
    # The level as rendered, before any normalising: a render far quieter than usual
    # has often gone wrong, and a louder copy of it has not been put right.
    level = await asyncio.to_thread(loudness, dest)
    normalised, normalised_to = 0, None
    playing = dest
    if record.get("normalise"):
        try:
            target = float(record["target_lufs"]) if record.get("target_lufs") is not None else normal_target()
            playing = await asyncio.to_thread(normalise, dest, target)
            normalised, normalised_to = 1, target
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not normalise '%s'; it keeps the level it was rendered at: %s",
                        record.get("title") or ref_id, exc)
    duration = await asyncio.to_thread(audio_duration, dest)
    elapsed = time.time() - started
    execute(
        "UPDATE takes SET status = 'done', stage = NULL, audio_path = ?, duration = ?, finished_at = ?, elapsed = ?, error = NULL, loudness = ?, normalised = ?, normalised_to = ?, weak_dismissed = 0 WHERE id = ?",
        (str(playing), duration, time.time(), elapsed, level, normalised, normalised_to, ref_id),
    )
    fresh = one("SELECT * FROM takes WHERE id = ?", (ref_id,))
    if fresh:
        await asyncio.to_thread(write_take_note, fresh, dest)
    await asyncio.to_thread(ensure_peaks, playing)
    bump_average("render", elapsed)
    log.info("Audio render finished for '%s' (duration=%.1fs, elapsed=%.1fs)",
             record.get("title") or ref_id, duration or 0.0, elapsed)


def _drop_engine_output(item: dict) -> None:
    """The engine keeps every render it saves.  Once the app has its copy, the
    engine's is a duplicate.  Only possible when the folder is mounted here."""
    root = config.ENGINE_OUTPUT_DIR
    if not root or item.get("type", "output") != "output":
        return
    path = root / (item.get("subfolder") or "") / item["filename"]
    if inside(path, root) and path.is_file():
        try:
            path.unlink()
        except OSError as exc:
            log.warning("could not remove the engine's copy %s: %s", path, exc)


async def cancel_take(take: dict) -> None:
    """Stop a take's job, queued or running.  A queued job is skipped when the
    worker reaches it, because its status is no longer 'queued'."""
    log.info("Cancelling take '%s' (%s, status=%s)", take.get("title") or take["id"], take["id"], take["status"])
    if take["status"] == "queued":
        execute("UPDATE takes SET status = 'failed', error = 'cancelled' WHERE id = ? AND status = 'queued'", (take["id"],))
    elif take["status"] == "running":
        CANCELLED.add(take["id"])
        if CURRENT.get("id") == take["id"] and CURRENT.get("prompt_id"):
            await ENGINE.cancel(CURRENT["prompt_id"])


async def cancel_current() -> dict | None:
    # Training is cancelled by its own id: it is not a take, and its state lives in
    # its own table.
    if CURRENT.get("kind") == "train":
        run_id = CURRENT.get("id")
        log.info("Cancelling LoRA training run %s", run_id)
        await cancel_train(run_id)
        return {"kind": "train", "id": run_id}

    if not CURRENT:
        active_train = one("SELECT id FROM lora_runs WHERE state IN ('queued', 'running') ORDER BY started_at IS NULL, started_at DESC LIMIT 1")
        if active_train:
            run_id = active_train["id"]
            log.info("Cancelling LoRA training run %s", run_id)
            await cancel_train(run_id)
            return {"kind": "train", "id": run_id}
        return None
    log.info("Cancelling current %s job %s", CURRENT.get("kind"), CURRENT.get("id"))
    CANCELLED.add(CURRENT["id"])
    if CURRENT.get("prompt_id"):
        await ENGINE.cancel(CURRENT["prompt_id"])
    # A corpus song's analysis is one thing to the user: stopping its GPU step stops
    # its vocal separation and lyrics too, instead of leaving them running unseen.
    if CURRENT.get("kind") in IDENTITY_FIELDS:
        await stop_song_analysis(CURRENT["id"])
    return {"kind": CURRENT["kind"], "id": CURRENT["id"]}


# ---------------------------------------------------------------------- identities
def identity_song(song_id: str) -> dict | None:
    return one("SELECT * FROM identity_songs WHERE id = ?", (song_id,))


persona_song = identity_song


def set_song(song_id: str, **fields) -> None:
    if fields:
        execute(f"UPDATE identity_songs SET {', '.join(f'{k} = ?' for k in fields)} WHERE id = ?", (*fields.values(), song_id))


set_identity_song = set_song


async def identity_worker() -> None:
    """Copies each song into the library and separates its vocal, one at a time,
    then hands the song to the GPU lane for key, tempo, lyrics and style."""
    while True:
        job = await IDENTITY_QUEUE.get()
        CURRENT_IDENTITY.clear()
        # The task, so Stop can cancel it (which kills demucs), and a flag Whisper
        # checks between lines, since a thread cannot be cancelled.
        stop = threading.Event()
        task = asyncio.create_task(prepare_song(job["id"]))
        CURRENT_IDENTITY.update({"id": job["id"], "started": time.time(), "task": task, "stop": stop,
                                 "stage": None, "progress": None})
        try:
            await asyncio.wait({task})
            if task.cancelled():
                _stopped(job["id"])
            elif task.exception():
                exc = task.exception()
                log.error("identity song %s failed", job["id"], exc_info=exc)
                set_song(job["id"], vocals_state="failed", error=f"could not prepare the song: {exc}"[:400])
        except asyncio.CancelledError:
            task.cancel()
            raise
        finally:
            CURRENT_IDENTITY.clear()
            IDENTITY_QUEUE.task_done()


def _stopped(song_id: str) -> None:
    """Whatever the CPU lane had not finished goes back to not started."""
    song = identity_song(song_id)
    if not song:
        return
    reset = {f: "none" for f in ("vocals_state", "lyrics_state") if song[f] in ("queued", "running")}
    set_song(song_id, **reset, error="stopped")


async def stop_song_analysis(song_id: str) -> bool:
    """Stop every step of one song's analysis, waiting or running, on both lanes."""
    song = identity_song(song_id)
    if not song:
        return False
    stopped = False
    if CURRENT_IDENTITY.get("id") == song_id and CURRENT_IDENTITY.get("task"):
        CURRENT_IDENTITY["stop"].set()
        CURRENT_IDENTITY["task"].cancel()
        stopped = True
    # Waiting on the CPU lane: the worker skips a song whose steps are no longer queued.
    waiting = {f: "none" for f in ("vocals_state", "lyrics_state") if song[f] == "queued"}
    # A lyrics step marked running while nothing works on it is only waiting.
    if song["lyrics_state"] == "running" and CURRENT_IDENTITY.get("id") != song_id:
        waiting["lyrics_state"] = "none"
    if waiting:
        set_song(song_id, **waiting, error="stopped")
        stopped = True
    for kind, field in IDENTITY_FIELDS.items():
        if not kind.startswith("identity_"):
            continue
        if song[field] == "queued":
            stopped = await cancel_waiting(kind, song_id, whole_song=False) or stopped
        elif song[field] == "running" and CURRENT.get("id") == song_id and CURRENT.get("kind") in (kind, kind.replace("identity", "persona")):
            STOPPED_SONGS.add(song_id)
            CANCELLED.add(song_id)
            if CURRENT.get("prompt_id"):
                await ENGINE.cancel(CURRENT["prompt_id"])
            stopped = True
    if stopped:
        log.info("Stopped the analysis of corpus song '%s'", song.get("title") or song_id)
    return stopped


async def stop_identity_analysis(identity_id: str) -> int:
    songs = rows("SELECT id FROM identity_songs WHERE identity_id = ?", (identity_id,))
    return sum([await stop_song_analysis(song["id"]) for song in songs])


def identity_working(song_ids: set[str]) -> dict | None:
    """What the analysis of these songs is doing right now, for the corpus window."""
    if CURRENT_IDENTITY.get("id") in song_ids:
        song = identity_song(CURRENT_IDENTITY["id"]) or {}
        return {"song": song.get("title") or song.get("file"), "stage": CURRENT_IDENTITY.get("stage"),
                "progress": CURRENT_IDENTITY.get("progress"), "since": CURRENT_IDENTITY.get("started")}
    if CURRENT.get("kind") in IDENTITY_FIELDS and CURRENT.get("id") in song_ids:
        song = identity_song(CURRENT["id"]) or {}
        stage = "Finding key and tempo" if CURRENT["kind"].endswith("_score") else "Describing its style"
        return {"song": song.get("title") or song.get("file"), "stage": stage + " on the GPU",
                "progress": CURRENT.get("progress"), "since": CURRENT.get("started")}
    return None


persona_worker = identity_worker


def _store_original(source: Path, stored: Path) -> None:
    """The song's own copy, so the corpus survives its folder changing.  A track the
    app cut from an album already lives in the corpus's own folder, so it is linked
    instead: the same file under a second name, taking no more space."""
    if identities.is_track(source):
        try:
            os.link(source, stored)
            return
        except OSError:
            pass    # a filesystem without links: copy after all
    shutil.copy2(source, stored)


async def prepare_song(song_id: str) -> None:
    """Copy in, separate the vocal, and transcribe it with Whisper, skipping whatever
    is already done.  Key and tempo, and the style hint, go to the GPU lane."""
    song = identity_song(song_id)
    if not song or "queued" not in (song["vocals_state"], song["lyrics_state"]):
        return
    if not song["include"]:
        # Unticked while it waited: leave it for later rather than spend the time.
        set_song(song_id, **{f: "none" for f in ("vocals_state", "lyrics_state") if song[f] == "queued"})
        return
    if identities.too_long(song["duration"]):
        set_song(song_id, **{f: "none" for f in ("vocals_state", "lyrics_state") if song[f] == "queued"},
                 error=f"{identities.TOO_LONG}: split it into tracks first")
        return
    id_val = song.get("identity_id") or song.get("persona_id")
    identity = one("SELECT * FROM identities WHERE id = ?", (id_val,))
    # A track cut from an album is stored by its full path, in the corpus's own folder.
    source = Path(identity["folder"]) / song["file"]
    if not (identities.allowed(source) or identities.is_track(source)) or not source.is_file():
        raise RuntimeError("the song is no longer in its folder")
    set_song(song_id, vocals_state="running", error=None)
    folder = identities.song_dir(identity["id"], song)
    folder.mkdir(parents=True, exist_ok=True)
    stored = folder / f"original{source.suffix.lower()}"
    if not stored.exists():
        await asyncio.to_thread(_store_original, source, stored)
    set_song(song_id, stored_path=str(stored))
    song_title = song.get("title") or song.get("file")
    log.info("Preparing corpus song '%s' for '%s' (separating vocals, transcribing)", song_title, identity["name"])
    # Key and tempo only need the recording, so the GPU can start while demucs runs.
    if song["score_state"] in ("none", "failed"):
        set_song(song_id, score_state="queued")
        await QUEUE.put({"kind": "identity_score", "id": song_id})
    def stage(name: str, progress: float | None = None) -> None:
        if CURRENT_IDENTITY.get("id") == song_id:
            CURRENT_IDENTITY.update(stage=name, progress=progress)

    if identities.vocalless(identity["voice"]):
        # No vocals to separate and no words to hear: the lyrics are the score's section tags.
        set_song(song_id, vocals_state="done")
        if identity_song(song_id)["style_state"] in ("none", "failed"):
            set_song(song_id, style_state="queued")
            await QUEUE.put({"kind": "identity_style", "id": song_id})
        log.info("Finished preparing corpus song '%s' (no vocals)", song_title)
        maybe_draft(song_id)
        return
    if not identities.vocals_file(folder):
        stage("Separating the vocal (demucs)", 0.0)
        # FLAC: the same audio exactly, in about half the room of the WAV it used to be written as.
        await separate_stems(stored, folder, "htdemucs", ["vocals"], "flac", work_root=config.WORK_DIR,
                             on_progress=lambda frac, _: stage("Separating the vocal (demucs)", frac))
    set_song(song_id, vocals_state="done")
    if identity_song(song_id)["style_state"] in ("none", "failed"):
        set_song(song_id, style_state="queued")
        await QUEUE.put({"kind": "identity_style", "id": song_id})
    if not (folder / "whisper.json").exists():
        set_song(song_id, lyrics_state="running")
        stage("Hearing the lyrics (Whisper)", 0.0)
        stop = CURRENT_IDENTITY.get("stop")
        try:
            found = await hear_all(identities.vocals_file(folder) or folder / "vocals.flac", seconds=song["duration"] or 0.0, title=song_title,
                                   on_progress=lambda frac: stage("Hearing the lyrics (Whisper)", frac),
                                   on_download=lambda text: stage(text, 0.0),
                                   should_stop=stop.is_set if stop else None)
            lines, method = found["lines"], found["method"]
            log.info("Corpus song '%s': lyrics heard by %s", song_title, method)
        except Exception as exc:  # noqa: BLE001
            set_song(song_id, lyrics_state="failed", error=f"lyrics: {exc}"[:400])
            return
        (folder / "whisper.json").write_text(json.dumps(lines, indent=1), encoding="utf-8")
        keep_lyric_versions(song_id, folder, found)
    log.info("Finished preparing corpus song '%s'", song_title)
    maybe_draft(song_id)


def keep_lyric_versions(song_id: str, folder: Path, found: dict) -> None:
    """Both versions of the words, each in a file of its own, and which one `whisper.json`
    (the lines in use) holds.  The file keeps its old name: everything that reads the lines
    reads it."""
    words = lambda lines: sum(len(line["text"].split()) for line in lines)
    versions = {"active": "llm" if found.get("llm") else "whisper", "whisper": {"words": words(found["whisper"])}}
    (folder / "lyrics-whisper.json").write_text(json.dumps(found["whisper"], indent=1), encoding="utf-8")
    if found.get("llm"):
        (folder / "lyrics-llm.json").write_text(json.dumps(found["llm"], indent=1), encoding="utf-8")
        versions["llm"] = {"model": found["model"], "words": words(found["llm"])}
    else:
        (folder / "lyrics-llm.json").unlink(missing_ok=True)
    set_song(song_id, lyrics_versions=json.dumps(versions))


def _text_file(song: dict, source: str) -> Path | None:
    """Where a version's finished words are kept, beside the lines they were drafted from."""
    if not song.get("stored_path") or source not in ("llm", "whisper"):
        return None
    return Path(song["stored_path"]).parent / f"lyrics-text-{source}.txt"


def remember_words(song: dict, source: str, text: str) -> None:
    """Keep a version's finished words (its sections marked, and any edits), so choosing it again is a swap, not a new
    draft and another call to the model."""
    path = _text_file(song, source)
    if path is None:
        return
    try:
        path.write_text(text or "", encoding="utf-8")
    except OSError as exc:
        # An optimisation, not the job: a folder that cannot be written costs the next switch a draft, nothing more.
        log.warning("Could not keep the words of '%s' (%s): %s", song.get("title") or song.get("id"), source, exc)


def remembered_words(song: dict, source: str) -> str | None:
    path = _text_file(song, source)
    if path is None or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    return text if text.strip() else None


def remember_in_use(song_id: str, text: str) -> None:
    """The words just drafted or saved belong to the version in use."""
    song = identity_song(song_id)
    if not song:
        return
    try:
        active = (json.loads(song.get("lyrics_versions") or "null") or {}).get("active")
    except ValueError:
        return
    if active:
        remember_words(song, active, text)


def maybe_draft(song_id: str) -> None:
    """Tag Whisper's lines with the score's sections once both are in.  A score that
    failed still gets a draft, under one verse."""
    song = identity_song(song_id)
    if not song or not song["stored_path"]:
        return
    folder = Path(song["stored_path"]).parent
    vocalless = identities.vocalless((one("SELECT voice FROM identities WHERE id = ?", (song.get("identity_id") or song.get("persona_id"),)) or {}).get("voice"))
    # Whisper not finished: the CPU lane owns the lyrics step until it is, and a
    # stopped song must not be left looking busy.  A corpus without vocals has no words to wait for.
    if not vocalless and not (folder / "whisper.json").exists():
        return
    if song["score_state"] not in ("done", "failed"):
        set_song(song_id, lyrics_state="running")   # heard; waiting for the sections
        return
    lines = [] if vocalless else json.loads((folder / "whisper.json").read_text(encoding="utf-8"))
    abc = (folder / "score.abc").read_text(encoding="utf-8") if (folder / "score.abc").exists() else ""
    sections = identities.score_sections(abc)
    draft = identities.tag_lyrics(lines, sections, song["duration"] or 0)
    if not draft.strip():
        if sections:
            draft = "\n\n".join(f"[{identities.SECTION_TAGS[name]}]" for name, _ in sections)
        else:
            draft = "[instrumental]"
    if vocalless:
        # Section tags are all there is: nothing to review, so the song counts as checked and a
        # later analysis does not replace tags edited by hand.
        if not (song["lyrics_checked"] and (song["lyrics"] or "").strip()):
            set_song(song_id, lyrics=draft, lyrics_state="done", lyrics_checked=1)
        else:
            set_song(song_id, lyrics_state="done")
        return
    # Words the user has already checked are theirs: a new draft never replaces them.
    if song["lyrics_checked"]:
        set_song(song_id, lyrics_state="done")
        return
    # With an external LLM, the sections are marked from the words as well (see
    # llm.tag_sections), off the lane that got here, since it waits on the network.
    if lines and llm.is_external_enabled():
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop:
            set_song(song_id, lyrics_state="running")
            task = loop.create_task(_llm_sections(song_id, lines, draft))
            _DRAFTING.add(task)
            task.add_done_callback(_DRAFTING.discard)
            return
    set_song(song_id, lyrics=draft, lyrics_state="done")
    remember_in_use(song_id, draft)


_DRAFTING: set = set()     # held, so a running task is not collected


async def _llm_sections(song_id: str, lines: list[dict], fallback: str) -> None:
    """The draft with its sections marked by the external LLM; the music analysis's
    draft when the model cannot, or its reply does not hold every line in order."""
    song = identity_song(song_id) or {}
    title = song.get("title") or song.get("file") or ""
    model = llm.get_config().get("model") or "the external LLM"
    draft = fallback
    try:
        blocks = await llm.tag_sections(lines)
        draft = identities.lyrics_text(blocks)
        log.info("Lyrics for '%s': sections marked by %s", title, model)
    except Exception as exc:  # noqa: BLE001
        log.warning("Lyrics for '%s': %s could not mark the sections, keeping the music analysis's: %s",
                    title, model, str(exc)[:200])
    # Only if nothing changed meanwhile: stopped, re-analysed, or checked by hand.
    now = identity_song(song_id)
    if now and now["lyrics_state"] == "running" and not now["lyrics_checked"]:
        set_song(song_id, lyrics=draft, lyrics_state="done")
        remember_in_use(song_id, draft)


def _gemma_graph(prompt: str, audio_files: list[str], max_length: int) -> dict:
    """Gemma on the engine: one CLIPLoader, then one TextGenerate per audio file (or
    one with no audio).  Greedy, so a transcription does not invent words."""
    graph = {"1": {"class_type": "CLIPLoader", "inputs": {"clip_name": config.LYRICS_MODEL, "type": "stable_diffusion"}}}
    for index, name in enumerate(audio_files or [None]):
        base = 10 + index * 3
        inputs = {"clip": ["1", 0], "prompt": prompt, "max_length": max_length, "thinking": False, "sampling_mode": "off"}
        if name:
            graph[str(base)] = {"class_type": "LoadAudio", "inputs": {"audio": name}}
            inputs["audio"] = [str(base), 0]
        graph[str(base + 1)] = {"class_type": "TextGenerate", "inputs": inputs}
        graph[str(base + 2)] = {"class_type": "PreviewAny", "inputs": {"source": [str(base + 1), 0]}}
    return graph


# What to try when the GPU runs out, by job.
OOM_HINTS = {
    "train": "Close anything else using the GPU, or set TRAIN_MAX_MINUTES to a lower number (see the README), and train again.",
    "render": "Close anything else using the GPU, or lower the length cap, and render again.",
    "plan": "Close anything else using the GPU, or lower the length cap, and plan again.",
}


def out_of_memory(kind: str) -> str:
    return "the GPU ran out of memory. " + OOM_HINTS.get(kind, "Close anything else using the GPU and try again.")


def _engine_failure(kind: str, job: dict) -> str | None:
    """A failure the engine reported, in plain words when there are some for it."""
    return out_of_memory(kind) if OUT_OF_MEMORY.search(_engine_error(job)) else None


# Written by the engine as its job thread dies (engine/custom_nodes/yue2_harmony/watch.py).
ENGINE_FAULT = "yeufonic/engine-fault.json"


def _engine_fault(prompt_id: str, since: float = 0.0) -> dict | None:
    """The engine's note of the error that killed its job thread, if it is about
    this job: the job it was running, written after this one was sent. A note with
    no job id is taken on its time alone."""
    if not config.ENGINE_OUTPUT_DIR:
        return None
    try:
        fault = json.loads((config.ENGINE_OUTPUT_DIR / ENGINE_FAULT).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(fault, dict) or float(fault.get("at") or 0) < since:
        return None
    if fault.get("prompt_id") and fault["prompt_id"] != prompt_id:
        return None
    if not fault.get("prompt_id") and not since:
        return None
    return fault


RESTART = " The engine can't run anything else until it is restarted."


def _lost(kind: str, since: float, prompt_id: str) -> str | None:
    """Why the engine came back without a job, from the surest word first: the error
    it sent for the job, then its note as the job thread died, then, from an engine
    built before that note, its log, and last that it stopped answering."""
    sent = ENGINE.failure(prompt_id) if hasattr(ENGINE, "failure") else None
    if sent:
        return out_of_memory(kind) if OUT_OF_MEMORY.search(sent) else "engine error: " + sent
    fault = _engine_fault(prompt_id, since)
    if fault:
        if fault.get("out_of_memory"):
            return out_of_memory(kind)
        return f"the engine stopped during this job: {fault.get('type')}: {fault.get('message')}"
    if getattr(ENGINE, "oom_at", 0) >= since:
        return out_of_memory(kind)
    if getattr(ENGINE, "offline_at", 0) >= since:
        return "the engine stopped during this job and came back without it. The log may say why."
    return None


def _engine_error(job: dict) -> str:
    """What went wrong, from the engine's own report: the node and its exception.
    The report also carries the node's inputs, which for audio is the waveform as
    numbers, so its tail says nothing useful."""
    messages = (job or {}).get("status", {}).get("messages") or []
    for item in messages:
        if isinstance(item, (list, tuple)) and len(item) == 2 and item[0] == "execution_error" and isinstance(item[1], dict):
            data = item[1]
            kind = str(data.get("exception_type") or "error").rsplit(".", 1)[-1]
            text = " ".join(str(data.get("exception_message") or "").split())
            node = data.get("node_type") or ""
            return (f"{node}: " if node else "") + f"{kind}: {text}"[:300]
    return json.dumps(messages)[-300:]


# The transcriber refuses a whole song when a note is still sounding at the very end
# of the audio: its beat grid stops short of the end, and a note there fits no cell.
# A song ending on a long held chord failed at 315.51 s of 315.53, and cut at four
# minutes, again at 239.94 s of 240.  So what it is given always ends cleanly -- a short fade
# and a few seconds of silence -- which costs nothing the score needs.  A corpus song
# that still fails is tried melody-only, then on its first four minutes, as the
# trainer does.  (A cover gets the clean ending but no shortening: its score is the
# whole song.)
FADE_SECONDS = 2
PAD_SECONDS = 5
TRANSCRIBE_TRIES = (("full", None), ("melody", None), ("full", 240), ("melody", 240))


def _ended_copy(src: Path, dest: Path, seconds: float | None = None) -> Path:
    """The recording as the transcriber should hear it: faded over its last seconds
    and followed by silence, shortened first when asked.  FLAC, with no tags."""
    length = identities.probe(src).get("duration") or 0.0
    end = min(length, seconds) if seconds else length
    chain = (f"atrim=0:{end:.3f},afade=t=out:st={max(0.0, end - FADE_SECONDS):.3f}:d={FADE_SECONDS},"
             f"apad=pad_dur={PAD_SECONDS}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-map_metadata", "-1", "-af", chain,
                    "-c:a", "flac", str(dest)], check=True, capture_output=True, timeout=300)
    return dest


async def _transcribe_corpus_song(kind: str, song_id: str, staged: Path, folder: Path) -> tuple[str, str]:
    """The score, and how it was got: "" the first way, else what it took."""
    failed: Exception | None = None
    for mode, seconds in TRANSCRIBE_TRIES:
        path = await asyncio.to_thread(_ended_copy, staged, folder / f"engine-copy-ended{f'-{seconds}s' if seconds else ''}.flac",
                                       seconds)
        name = await _upload(path, f"identity-{song_id}-{path.stem}{path.suffix}")
        graph = build_transcribe_graph(name)
        graph["3"]["inputs"]["mode"] = mode
        try:
            job = await _run_graph(kind, song_id, graph)
        except RuntimeError as exc:
            # A stop, a timeout or a lost engine is not the song's fault: no retry.
            # Running out of memory is worth them too: melody only, or the first
            # four minutes, asks less of the card.
            if not str(exc).startswith(("engine error", "the GPU ran out of memory")) or song_id in STOPPED_SONGS:
                raise
            failed = exc
            log.info("Transcription of corpus song %s failed (%s%s), trying another way: %s", song_id, mode,
                     f", first {seconds}s" if seconds else "", str(exc)[:160])
            continue
        abc = extract_text_output(job, "SheetSage2AudioToABC", "PreviewAny") or ""
        if abc.count("|") >= 4:
            if (mode, seconds) == TRANSCRIBE_TRIES[0]:
                return abc, ""
            return abc, ("melody only" if mode == "melody" else "melody and chords") + \
                (f", first {seconds // 60} minutes" if seconds else "")
    raise failed or RuntimeError("the transcription came back empty")


def _texts_in_order(job: dict) -> list[str]:
    outputs = (job or {}).get("outputs") or {}
    return [outputs[nid]["text"][0] for nid in sorted(outputs, key=int) if outputs[nid].get("text")]


async def _run_graph(kind: str, ref_id: str, graph: dict) -> dict:
    since = time.time()
    prompt_id = await ENGINE.submit(graph)
    CURRENT.clear()
    CURRENT.update({"kind": kind, "id": ref_id, "prompt_id": prompt_id, "started": time.time()})
    try:
        outcome, job = await _wait_for(kind, ref_id, prompt_id)
        if outcome != "done":
            if outcome in ("cancelled", "timeout"):
                await ENGINE.cancel(prompt_id)
            if outcome == "dead":
                raise RuntimeError((_lost(kind, since, prompt_id) or "the engine stopped running jobs.") + RESTART)
            raise RuntimeError({"cancelled": "cancelled", "timeout": "timed out"}.get(outcome)
                               or _lost(kind, since, prompt_id) or "the engine lost the job")
        if job.get("status", {}).get("status_str") != "success":
            raise RuntimeError(_engine_failure(kind, job) or "engine error: " + _engine_error(job))
        return job
    finally:
        ENGINE.forget(prompt_id)
        CURRENT.clear()
        CANCELLED.discard(ref_id)


def _without_tags(src: Path, folder: Path) -> Path:
    """A copy of the audio with its tags dropped, or the original if that fails.

    The engine reads audio with PyAV, and a tag it cannot decode raises inside it:
    an mp3 carrying a mangled lyrics frame failed the whole score step with
    "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xfe".  ffmpeg reads the
    same file happily, and nothing here wants the tags, so they go before the
    upload."""
    dest = folder / ("engine-copy" + src.suffix)
    try:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-map_metadata", "-1",
             "-c", "copy", str(dest)],
            check=True, capture_output=True, timeout=120,
        )
        if dest.exists() and dest.stat().st_size > 0:
            return dest
    except (subprocess.SubprocessError, OSError) as exc:
        log.warning("could not strip the tags from %s: %s", src.name, exc)
    return src


async def _upload(path: Path, name: str) -> str:
    data = await asyncio.to_thread(path.read_bytes)
    result = await ENGINE.upload(name, data)
    if not result.get("name"):
        raise RuntimeError("the engine did not accept the audio")
    return result["name"]


# ------------------------------------------------------------ stems on the GPU
# The engine's node orders its outputs like this; the app's names for them are the same.
SEPARATE_OUTPUTS = ("vocals", "drums", "bass", "other", "guitar", "piano", "instruments")


def gpu_wanted() -> bool:
    """Stems and lyric hearing on the GPU: Settings says so (on unless turned off), and STEMS_ON_GPU=0 overrides it."""
    return bool(config.STEMS_ON_GPU and get_setting("processing.gpu", "on") != "off")


def _engine_can(node: str) -> bool:
    """Asked for, the engine is up and has the node, and it is not held by training: a job would wait in its
    queue for the whole run."""
    return bool(gpu_wanted() and ENGINE.online and ENGINE.options.get(node) and CURRENT.get("kind") != "train")


def _can_separate_on_engine() -> bool:
    return _engine_can("separate")


def _engine_has_whisper() -> bool:
    """The engine's copy of the Whisper model is on disk, so a hearing starts at once.  Where this machine cannot see the
    engine's models it is assumed to be (nothing to say)."""
    root = Path(config.MODELS_DIR) / "whisper"
    if not (Path(config.MODELS_DIR)).is_dir():
        return True
    return (root / identities.WHISPER_MODEL / "model.bin").is_file() or any(root.glob("models--*/snapshots/*/model.bin"))


async def hear_lines(vocal: Path, on_progress=None, duration: float = 0.0, should_stop=None, on_stage=None) -> list[dict]:
    """The sung lines of a separated vocal, with their times: Whisper on the engine's GPU when it can, as a job in the
    engine's queue, and Whisper on the CPU here otherwise or when the engine fails it.  Either way the segments
    become lines the same way (identities.lines_from_segments)."""
    if _engine_can("hear"):
        try:
            if on_stage and not _engine_has_whisper():
                on_stage("Downloading the Whisper model, first time only")
            segments = await _hear_on_engine(vocal, on_progress, should_stop)
            return identities.lines_from_segments(segments, on_progress, duration, should_stop)
        except (asyncio.CancelledError, identities.Stopped):
            raise
        except Exception as exc:  # noqa: BLE001
            log.warning("Hearing '%s' on the GPU failed, using the CPU: %s", vocal.name, exc)
    return await asyncio.to_thread(identities.transcribe, vocal, on_progress, duration, should_stop)


def _gpu_hearing_progress(rec: dict) -> float | None:
    """How far Whisper is, from the engine's last word.  None until it starts on the audio: the model loads first, and
    saying 0% over and over would overwrite whatever the page was told about that wait."""
    if rec.get("stage") == "Yue2Hear" and rec.get("value") is not None:
        return rec.get("frac") or 0.0
    return None


async def _hear_on_engine(vocal: Path, on_progress, should_stop) -> list[identities.Segment]:
    token = os.urandom(4).hex()
    started = time.time()
    name = await _upload(vocal, f"hear-{token}{vocal.suffix}")
    graph = {"1": {"class_type": "LoadAudio", "inputs": {"audio": name}},
             "2": {"class_type": "Yue2Hear", "inputs": {"audio": ["1", 0], "model": identities.WHISPER_MODEL, "language": "en"}},
             "3": {"class_type": "PreviewAny", "inputs": {"source": ["2", 0]}}}
    prompt_id = await ENGINE.submit(graph)
    stopped = False

    async def watch() -> None:
        nonlocal stopped
        while True:
            await asyncio.sleep(0.7)
            if should_stop and should_stop() and not stopped:
                stopped = True
                CANCELLED.add(token)           # _wait_for returns "cancelled"
            frac = _gpu_hearing_progress(ENGINE.progress.get(prompt_id) or {})
            if frac is not None and on_progress:
                on_progress(max(0.0, min(1.0, frac)))

    watcher = asyncio.create_task(watch())
    try:
        outcome, job = await _wait_for("hear", token, prompt_id)
    except asyncio.CancelledError:
        with contextlib.suppress(Exception):
            await ENGINE.cancel(prompt_id)
        raise
    finally:
        watcher.cancel()
        CANCELLED.discard(token)
        ENGINE.forget(prompt_id)
    if stopped:
        with contextlib.suppress(Exception):
            await ENGINE.cancel(prompt_id)
        raise identities.Stopped()
    if outcome != "done":
        raise RuntimeError(outcome)
    if job.get("status", {}).get("status_str") != "success":
        raise RuntimeError(_engine_error(job))
    texts = _texts_in_order(job)
    if not texts:
        raise RuntimeError("the engine returned no words")
    log.info("Heard '%s' on the GPU in %.1fs", vocal.name, time.time() - started)
    return [identities.Segment(float(s["start"]), float(s["end"]), s["text"]) for s in json.loads(texts[0])]


def _gpu_separation_progress(rec: dict) -> tuple[float, str] | None:
    """Where an engine separation is, from what the engine last said: reading the recording, loading the model (the
    node says nothing until it starts on the audio), separating, then saving.  The separating itself is the quick part."""
    stage = rec.get("stage")
    if stage == "LoadAudio":
        return 0.05, "Reading the recording (GPU)"
    if stage == "Yue2Separate":
        if rec.get("value") is None:
            return 0.10, "Loading the model (GPU)"
        return 0.15 + 0.55 * (rec.get("frac") or 0.0), "Separating (GPU)"
    if stage == "SaveAudio":
        return 0.75, "Saving the stems (GPU)"
    return None


async def separate_stems(src: Path, dest_dir: Path, model: str, wanted: list[str], fmt: str,
                         on_progress=None, work_root: Path | None = None) -> dict:
    """stems.separate, on the engine's GPU when it can, as a job in the engine's own queue beside the plans and
    renders; on the CPU when it cannot, or when the engine fails it."""
    if _can_separate_on_engine():
        try:
            done = await _separate_on_engine(src, dest_dir, model, wanted, fmt, on_progress, work_root)
            log.info("Separated '%s' on the GPU in %.1fs (%s)", src.name, done["seconds"], model)
            return done
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            log.warning("Separating on the GPU failed, using the CPU: %s", exc)
            if on_progress:
                on_progress(0.02, "Using the CPU")
    return await stems.separate(src, dest_dir, model, wanted, fmt, on_progress, work_root=work_root)


async def _separate_on_engine(src: Path, dest_dir: Path, model: str, wanted: list[str], fmt: str,
                              on_progress, work_root: Path | None) -> dict:
    spec = stems.MODELS[model]
    keep = [s for s in wanted if s in spec["stems"]] or list(spec["stems"])
    fmt = fmt if fmt in stems.FORMATS else "wav"
    started = time.time()
    token = os.urandom(4).hex()

    def report(frac: float, stage: str) -> None:
        if on_progress:
            on_progress(max(0.0, min(1.0, frac)), stage)

    if work_root:
        work_root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="stems-gpu-", dir=work_root))
    prompt_id = None
    try:
        report(0.02, "Sending it to the engine")
        # The engine reads audio with PyAV, which can stumble on tags: a lossless copy without them.
        staged = work / "engine-copy.flac"
        await asyncio.to_thread(subprocess.run, ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-map_metadata", "-1",
                                                 "-c:a", "flac", str(staged)], check=True, capture_output=True, timeout=600)
        name = await _upload(staged, f"stems-{token}.flac")
        graph = {"1": {"class_type": "LoadAudio", "inputs": {"audio": name}},
                 "2": {"class_type": "Yue2Separate",
                       "inputs": {"audio": ["1", 0], "model": spec.get("demucs", model), "shifts": 1, "overlap": 0.25}}}
        saves = {}
        for index, stem in enumerate(keep):
            node = str(3 + index)
            saves[node] = stem
            graph[node] = {"class_type": "SaveAudio",
                           "inputs": {"audio": ["2", SEPARATE_OUTPUTS.index(stem)], "filename_prefix": f"yeufonic/stems-{token}/{stem}"}}
        prompt_id = await ENGINE.submit(graph)

        async def watch() -> None:
            while True:
                await asyncio.sleep(0.7)
                step = _gpu_separation_progress(ENGINE.progress.get(prompt_id) or {})
                if step:
                    report(*step)

        watcher = asyncio.create_task(watch())
        try:
            outcome, job = await _wait_for("separate", token, prompt_id)
        finally:
            watcher.cancel()
        if outcome != "done":
            raise RuntimeError(outcome)
        if job.get("status", {}).get("status_str") != "success":
            raise RuntimeError(_engine_error(job))

        report(0.92, "Collecting the stems")
        dest_dir.mkdir(parents=True, exist_ok=True)
        out: dict[str, str] = {}
        for node, stem in saves.items():
            item = ((job.get("outputs") or {}).get(node) or {}).get("audio", [None])[0]
            if not item:
                raise RuntimeError(f"the engine returned no {stem}")
            got = await ENGINE.download(item, work / f"{stem}.flac")
            target = dest_dir / f"{stem}.{fmt}"
            if fmt == "flac":
                shutil.move(str(got), str(target))
            else:
                codec = ["-c:a", "pcm_s16le"] if fmt == "wav" else ["-c:a", "libmp3lame", "-b:a", "320k"]
                await asyncio.to_thread(subprocess.run, ["ffmpeg", "-v", "error", "-y", "-i", str(got), *codec, str(target)],
                                        check=True, capture_output=True, timeout=600)
            out[stem] = str(target)
        report(1.0, "Done")
        return {"stems": out, "model": model, "format": fmt, "seconds": round(time.time() - started, 1), "device": "gpu"}
    except asyncio.CancelledError:
        if prompt_id:
            with contextlib.suppress(Exception):
                await ENGINE.cancel(prompt_id)
        raise
    finally:
        if prompt_id:
            ENGINE.forget(prompt_id)
        shutil.rmtree(work, ignore_errors=True)


async def run_identity_job(kind: str, song_id: str) -> None:
    field = IDENTITY_FIELDS[kind]
    song = identity_song(song_id)
    if not song or song[field] != "queued":
        return
    if not song["include"]:
        set_song(song_id, **{field: "none"})
        return
    set_song(song_id, **{field: "running"})
    folder = Path(song["stored_path"]).parent if song.get("stored_path") else None
    song_title = song.get("title") or song.get("file")
    log.info("Starting %s for corpus song '%s'", kind, song_title)
    try:
        if kind in ("identity_score", "persona_score"):
            source = Path(song["stored_path"])
            staged = await asyncio.to_thread(_without_tags, source, folder)
            abc, how = await _transcribe_corpus_song(kind, song_id, staged, folder)
            (folder / "score.abc").write_text(abc, encoding="utf-8")
            key, tempo = identities.key_and_tempo(abc)
            set_song(song_id, key=key, tempo=tempo, score_state="done")
            log.info("Finished score analysis for corpus song '%s' (key=%s, tempo=%s%s)", song_title, key or "unknown",
                     tempo or "unknown", f"; transcribed {how}, after the full transcription failed" if how else "")
            maybe_draft(song_id)
        elif kind in ("identity_style", "persona_style"):
            # With no words, the external model has only a title; the local one listens to the music.
            owner = one("SELECT voice FROM identities WHERE id = ?", (song.get("identity_id") or song.get("persona_id"),)) or {}
            listens = identities.vocalless(owner.get("voice")) and bool(ENGINE.options.get("lyrics"))
            if llm.is_external_enabled() and not listens:
                # The title and the words only.  No artist: the corpus's name is whatever
                # the user called the folder, and a model can read it as an unrelated band
                # and describe the songs in that band's genre.  A file's artist tag can be
                # as wrong, or missing.
                title = song.get("title") or song_title
                lyrics_text = song.get("lyrics") or ""
                log.info("Starting external LLM style analysis for corpus song '%s' (%s)", title, song_id)
                hint = await llm.describe_song_style(title=title, lyrics_text=lyrics_text)
                set_song(song_id, style_hint=hint, style_state="done")
                log.info("Finished external LLM style analysis for corpus song '%s': %s", song_title, hint[:60] + "..." if len(hint) > 60 else hint)
            else:
                # Gemma is optional (the Windows installer can leave it out).  Without it
                # the engine cannot run this, and says so only in its own terms.
                if ENGINE.options_loaded and not ENGINE.options.get("lyrics"):
                    raise RuntimeError("needs Gemma 4 on this PC, or an external LLM set in Settings")
                samples = await asyncio.to_thread(identities.read_mono, Path(song["stored_path"]))
                middle = len(samples) / identities.CHUNK_RATE * 0.4
                clip = identities.write_chunk(samples, (middle, middle + 30), folder / "style-clip.wav")
                name = await _upload(clip, f"identity-{song_id}-style.wav")
                job = await _run_graph(kind, song_id, _gemma_graph(identities.DESCRIBE, [name], 120))
                hint = " ".join((_texts_in_order(job) or [""])[0].split())[:300]
                set_song(song_id, style_hint=hint, style_state="done")
                log.info("Finished style analysis for corpus song '%s': %s", song_title, hint[:60] + "..." if len(hint) > 60 else hint)
    except Exception as exc:  # noqa: BLE001
        if song_id in STOPPED_SONGS:
            STOPPED_SONGS.discard(song_id)
            log.info("%s for '%s' (%s) stopped", kind, song_title, song_id)
            set_song(song_id, **{field: "none"}, error="stopped")
            return
        log.warning("%s for '%s' (%s) failed: %s", kind, song_title, song_id, exc)
        set_song(song_id, **{field: "failed"}, error=f"{kind.split('_')[1]}: {exc}"[:400])
        if kind in ("identity_score", "persona_score"):
            maybe_draft(song_id)
    finally:
        # The copies made for the engine are not read again; Settings > Storage can keep them.
        if get_setting("storage.working_copies", "remove") != "keep":
            freed = await asyncio.to_thread(storage.drop_working_copies, folder, song_id)
            if freed:
                log.debug("Removed %d bytes of working copies for corpus song %s", freed, song_id)


run_persona_job = run_identity_job


# --------------------------------------------------------------- training a LoRA
#
# Everything from here to cancel_train is reached only when config.TRAINING_ENABLED is
# set and the engine image carries the trainer (WITH_TRAINER=1), both the defaults.
#
# The trainer is a ComfyUI node pack inside the engine image.  It reads a folder of
# audio with a caption beside each file and writes a LoRA into the engine's
# models/loras.  It holds the GPU for the better part of an hour — measured: 5000
# steps, 44 minutes, 12.5 GB — so nothing else that needs the card may start while it
# runs, and the routes refuse to start it while something else is using the card.

def train_graph(audio_folder: str, dataset_name: str, lora_name: str, steps: int,
                rank_planner: int = 64, rank_decoder: int = 32,
                max_minutes: float = 3.5, max_tokens: int | None = None) -> dict:
    """The dual-branch FS_Audio training graph in ComfyUI prompt API format.

    Trains both planner LoRA (composition/harmony/phrasing) and decoder LoRA
    (timbre/production) in one joint loop with regularizer contrast.
    """
    return {
        "1": {
            "class_type": "FSAudioLoraLoader",
            "inputs": {
                "lora_name": config.REAL_AUDIO_LORA,
                "strength_model": 1.0,
                "strength_clip": 0.0,
            },
        },
        "2": {
            "class_type": "FSAudioModelLoader",
            "inputs": {
                "yue2_checkpoint": config.TRAIN_CHECKPOINT,
                "melody_transcriber": "sheetsage2_bf16.safetensors",
                "loras": ["1", 0],
            },
        },
        "3": {
            "class_type": "FSAudioDatasetBuilder",
            "inputs": {
                "pipe": ["2", 0],
                "audio_folder": audio_folder,
                "dataset_name": dataset_name,
                "tokenizer_head": config.TOKENIZER_HEAD,
                "default_style": "",
                "default_lyrics": "[instrumental]",
                "transcribe_scores": True,
                "hold_out_percent": 0,
                "max_minutes": max_minutes,
                "store_latents": True,
                "auto_tempo_key": True,
            },
        },
        "4": {
            "class_type": "FSAudioRegularizer",
            "inputs": {"pack": config.REGULARIZER_PACK},
        },
        "5": {
            "class_type": "FSAudioArtistTrainer",
            "inputs": {
                "pipe": ["2", 0],
                "dataset": ["3", 0],
                "regularizer": ["4", 0],
                "lora_name": lora_name,
                "steps": max(50, steps),
                "decoder_steps": config.TRAIN_DECODER_STEPS,
                "rank_planner": rank_planner,
                "rank_decoder": rank_decoder,
                "planner_lr": 3e-5,
                "decoder_lr": 4e-5,
                "io_lr": 2e-5,
                "artist_fraction": config.TRAIN_ARTIST_FRACTION,
                "batch_songs": config.TRAIN_BATCH_SONGS,
                "kl_weight": 0.1,
                "score_first_fraction": config.TRAIN_SCORE_FIRST,
                "end_token_weight": config.TRAIN_END_TOKEN_WEIGHT,
                "max_tokens": max_tokens or config.TRAIN_MAX_TOKENS,
                "window_seconds": 30.0,
                "ema_decay": 0.99,
                "eval_every": 25,
                "checkpoint_from": config.TRAIN_CHECKPOINT_EVERY,
                "checkpoint_every": config.TRAIN_CHECKPOINT_EVERY,
                "seed": 0,
                "strength_model": 1.0,
                "strength_clip": 1.0,
            },
        },
        # FSAudioArtistTrainer is not an output node, so PreviewAny provides the output sink.
        "7": {"class_type": "PreviewAny", "inputs": {"source": ["5", 1]}},
    }


def _run_state(run_id: str, **changes) -> None:
    sets = ", ".join(f"{key} = ?" for key in changes)
    execute(f"UPDATE lora_runs SET {sets} WHERE id = ?", (*changes.values(), run_id))


async def run_lora_train(run_id: str) -> None:
    run = one("SELECT * FROM lora_runs WHERE id = ?", (run_id,))
    if not run or run["state"] != "queued":
        return   # cancelled or deleted while it waited
    identity = one("SELECT * FROM identities WHERE id = ?", (run["identity_id"],))
    if not identity:
        _run_state(run_id, state="failed", error="the corpus is gone", finished_at=time.time())
        return
    dataset = config.DATA_DIR / "identities" / run["identity_id"] / "dataset"
    if not dataset.is_dir() or not any(dataset.glob("*.flac")):
        _run_state(run_id, state="failed", error="export the training set first", finished_at=time.time())
        return
    if not config.ENGINE_INPUT_DIR:
        _run_state(run_id, state="failed", error="the app cannot see the engine's input folder",
                   finished_at=time.time())
        return

    # The node reads a folder, and the engine can only read its own, so the set is
    # copied in.
    staged = config.ENGINE_INPUT_DIR / f"lora-{run_id}"
    try:
        await asyncio.to_thread(remove_tree, staged)
        await asyncio.to_thread(shutil.copytree, dataset, staged)
    except OSError as exc:
        _run_state(run_id, state="failed", error=f"could not stage the training set: {exc}",
                   finished_at=time.time())
        return

    started = time.time()
    _run_state(run_id, state="running", stage="Building dataset & tokens", progress=0.0,
               started_at=started, error=None)
    try:
        steps = max(50, int(run["steps"]))
        rank_planner = int(run.get("rank") or config.TRAIN_RANK_PLANNER)
        rank_decoder = config.TRAIN_RANK_DECODER
        log.info("Starting LoRA training run %s for corpus '%s' (%d steps, rank=%d, name=%s)",
                 run_id, identity["name"], steps, rank_planner, run["lora_name"])
        # Whatever analysis or renders left loaded would share the card with the trainer,
        # and preparing long songs already takes most of a 16 GB card.
        await ENGINE.free()
        # How much of each song, and how large a context, from the card as it is now (the
        # engine has just let go of what it held, and that is counted as free).
        sizing = trainsize.for_corpus(
            [r["duration"] for r in rows("SELECT duration FROM identity_songs WHERE identity_id = ? AND include = 1",
                                         (identity["id"],))], ENGINE.gpu())
        log.info("Training on %s. %s", sizing["reason"],
                 "" if not config.TRAIN_MINUTES_AUTO else "Set TRAIN_MAX_MINUTES to change it.")
        if sizing["tight"]:
            log.warning("This card is short of memory for training: preparing the songs may run out at %s",
                        trainsize.clock(sizing["minutes"]))
        graph = train_graph(f"lora-{run_id}", f"dataset_{run_id}",
                            run["lora_name"], steps, rank_planner, rank_decoder,
                            sizing["minutes"], sizing["tokens"])
        await _run_graph("train", run_id, graph)
        produced = await finish_training(run, identity)
        _run_state(run_id, state="done", stage=None, progress=1.0, finished_at=time.time(),
                   elapsed=round(time.time() - started, 1))
        log.info("LoRA training run %s for corpus '%s' finished in %.1fs -> %s",
                 run_id, identity["name"], time.time() - started, produced)
    except Exception as exc:  # noqa: BLE001
        log.warning("training %s failed: %s", run_id, exc)
        _run_state(run_id, state="failed", error=str(exc)[:300], finished_at=time.time(),
                   elapsed=round(time.time() - started, 1))
    finally:
        await asyncio.to_thread(remove_tree, staged)


def run_checkpoints(name: str, root: Path) -> list[Path]:
    """A run's checkpoints (name_stepN), in step order."""
    return sorted(root.glob(f"{name}_step*.safetensors"),
                  key=lambda path: int(re.sub(r"\D", "", path.stem.rsplit("_step", 1)[1]) or 0))


async def finish_training(run: dict, identity: dict, stopped: bool = False) -> str:
    """What a run does once the engine has written its files: the trainer's best copy
    becomes the LoRA, named after the corpus, noted and grouped; the checkpoints are
    kept or deleted as Settings says, and noted under it; the corpus remembers it.

    Also for a run that stopped short (stopped=True): the same from what it saved, its
    best copy, or failing that its last checkpoint, which then stays a checkpoint too.
    Returns the LoRA's file name."""
    root = loras.folder()
    if not root:
        raise RuntimeError("the app cannot see the LoRA folder")
    name = run["lora_name"]
    produced = None
    for cand_name in (f"{name}_best.safetensors", f"{name}.safetensors"):
        cand = root / cand_name
        if cand.exists():
            produced = cand
            break
    snapshots = run_checkpoints(name, root)
    if produced is None and stopped and snapshots:
        produced = snapshots[-1]
    if not produced or not produced.exists():
        raise RuntimeError("the engine wrote no LoRA file" if not stopped else "the run saved nothing to finish from")
    # The engine writes as root.  Its trainer is patched to leave the files readable;
    # an engine image built before that patch leaves them to root alone, and nothing
    # after this point can work.  Say so rather than finish half the job.
    if not os.access(produced, os.R_OK):
        raise RuntimeError(f"the engine wrote {produced.name} but this app cannot read it (it is readable "
                           "by root only). Rebuild the engine image (docker compose build engine), and make "
                           "the files readable: docker compose exec engine chmod 644 /app/models/loras/*.safetensors")

    # Ensure all produced checkpoints and logs are readable by non-root processes
    for p in root.glob(f"{name}*"):
        with contextlib.suppress(OSError):
            os.chmod(p, 0o644)

    canonical = root / f"{name}.safetensors"
    was_best = produced.name == f"{name}_best.safetensors"
    if produced != canonical:
        with contextlib.suppress(OSError):
            shutil.copyfile(produced, canonical)
            with contextlib.suppress(OSError):
                os.chmod(canonical, 0o644)
            produced = canonical
    # The best is now the file above, so its copy goes.  The snapshots go too unless
    # Settings keeps them, in a group of their own: the published LoRAs were each a
    # checkpoint picked by ear, often well before the last, and the trainer's own
    # "best" only follows the planner's loss.
    if produced == canonical and was_best:
        with contextlib.suppress(OSError):
            (root / f"{name}_best.safetensors").unlink(missing_ok=True)

    # Parse training log if present to check loss progression against reference targets
    # (blgr_rhodope: artist ~4.635, regularizer ~3.576, decoder ~1.069).
    log_file = root / f"{name}_log.json"
    if log_file.exists():
        try:
            log_data = json.loads(log_file.read_text(encoding="utf-8"))
            if log_data and isinstance(log_data, list):
                last = log_data[-1]
                log.info("LoRA %s training finished. Final losses: artist=%s (target ~4.635), "
                         "regularizer=%s (target ~3.576), decoder=%s (target ~1.069)",
                         name, last.get("artist"), last.get("regularizer"), last.get("decoder"))
        except Exception as e:
            log.debug("Could not parse training log %s: %s", log_file, e)

    # Name it, group it, and remember it on the corpus.
    await asyncio.to_thread(loras.write_note, produced, identity["trigger_word"], identity["name"],
                            title=identity["name"])
    # Kept unless Settings says otherwise: each is as big as the LoRA itself.
    if get_setting("training.checkpoints", "keep") == "delete":
        for snapshot in snapshots:
            with contextlib.suppress(OSError, ValueError):
                loras.remove(snapshot.name, root)
        snapshots = []
    for snapshot in snapshots:
        step = snapshot.stem.rsplit("_step", 1)[1].lstrip("0") or "0"
        await asyncio.to_thread(loras.write_note, snapshot, identity["trigger_word"], identity["name"],
                                title=f"{identity['name']} · step {step}", family=loras.CHECKPOINT_FAMILY)
    execute("UPDATE identities SET lora = ? WHERE id = ?", (produced.name, identity["id"]))
    # A finished run no longer needs its training set, if Settings says to let it go.  A run that
    # stopped short keeps it: the person may want to try again.
    if not stopped and get_setting("storage.training_set", "keep") == "delete":
        freed = await asyncio.to_thread(storage.drop_training_set, identity["id"], run["id"])
        log.info("Removed the training set of corpus '%s' (%.1f GB); Export writes it again", identity["name"], freed / 1e9)
    with contextlib.suppress(Exception):
        await ENGINE.refresh_options()
    return produced.name


async def cancel_train(run_id: str) -> None:
    run = one("SELECT * FROM lora_runs WHERE id = ?", (run_id,))
    if not run:
        return
    if run["state"] == "queued":
        _run_state(run_id, state="cancelled", finished_at=time.time(), error="cancelled")
        return
    if run["state"] == "running":
        CANCELLED.add(run_id)
        if CURRENT.get("id") == run_id and CURRENT.get("prompt_id"):
            await ENGINE.cancel(CURRENT["prompt_id"])
        _run_state(run_id, state="cancelled", finished_at=time.time(), error="cancelled")


async def cancel_lyrics(record: dict) -> None:
    if record["status"] == "queued":
        record.update({"status": "failed", "error": "cancelled"})
    elif record["status"] == "running":
        CANCELLED.add(record["id"])
        if CURRENT.get("id") == record["id"] and CURRENT.get("prompt_id"):
            await ENGINE.cancel(CURRENT["prompt_id"])


async def cancel_waiting(kind: str, ref_id: str, whole_song: bool = True) -> bool:
    """Take back a job still waiting for the GPU.  The worker skips anything no longer
    'queued', so this only changes the state.  An analysis or a transcription goes back
    to what it was before, so cancelling a re-run keeps the earlier result; a take is
    cancelled as it is from its own card."""
    if kind in IDENTITY_FIELDS:
        field = IDENTITY_FIELDS[kind]
        song = identity_song(ref_id)
        if not song or song[field] != "queued":
            return False
        had = (song.get("key") or song.get("tempo")) if field == "score_state" else song.get("style_hint")
        set_song(ref_id, **{field: "done" if had else "none"})
        log.info("Cancelled waiting %s for corpus song '%s'", kind, song.get("title") or ref_id)
        if whole_song:
            await stop_song_analysis(ref_id)
        return True
    if kind == "lyrics":
        record = LYRICS.get(ref_id)
        if not record or record["status"] != "queued":
            return False
        await cancel_lyrics(record)
        return True
    if kind == "transcribe":
        source = one("SELECT title, abc FROM sources WHERE id = ? AND transcribe_state = 'queued'", (ref_id,))
        if not source:
            return False
        state = "done" if (source["abc"] or "").strip() else "none"
        execute("UPDATE sources SET transcribe_state = ?, transcribe_error = NULL WHERE id = ? AND transcribe_state = 'queued'",
                (state, ref_id))
        log.info("Cancelled waiting transcription for source '%s'", source["title"] or ref_id)
        return True
    if kind in ("render", "plan"):
        take = one("SELECT * FROM takes WHERE id = ?", (ref_id,))
        if not take or take["status"] != "queued":
            return False
        await cancel_take(take)
        return True
    return False


def waiting_jobs() -> list[dict]:
    """App jobs not yet sent to the engine, in the order the worker will take them."""
    return list(QUEUE._queue)   # asyncio.Queue keeps its items in a deque


async def wait_for_engine() -> None:
    """A job asked for while the engine is still starting waits for it rather than
    failing.  Once it answers, a moment more for its node list, which the keeper reads
    next; an engine that stays offline is left to fail the job as before."""
    while ENGINE.starting:
        await asyncio.sleep(1)
    # An engine whose job thread died would take the job and never run it: wait for
    # the restart instead, which the keeper notices.
    while getattr(ENGINE, "stuck_on", None):
        await asyncio.sleep(2)
    for _ in range(15):
        if not ENGINE.online or ENGINE.options_loaded:
            return
        await asyncio.sleep(1)


async def worker() -> None:
    while True:
        job = await QUEUE.get()
        try:
            await wait_for_engine()
            await run_job(job["kind"], job["id"])
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            log.exception("job crashed")
            fail(job["kind"], job["id"], f"internal error: {exc}")
        finally:
            QUEUE.task_done()


async def keeper() -> None:
    """Keep the engine status fresh for the page, and read the node schemas again
    when the engine comes back or every few minutes."""
    last_options = time.time() if ENGINE.options_loaded else 0.0
    was_online = ENGINE.online
    while True:
        await ENGINE.refresh_status()
        now = time.time()
        if ENGINE.online and (not was_online or not ENGINE.options_loaded or now - last_options > 300):
            try:
                await ENGINE.refresh_options()
                last_options = now
            except Exception as exc:  # noqa: BLE001
                log.warning("option refresh failed: %s", exc)
        if ENGINE.online != was_online:
            log.info("engine %s", "online" if ENGINE.online else f"offline: {ENGINE.last_error}")
        was_online = ENGINE.online
        await asyncio.sleep(2)


# ---------------------------------------------------------------------- stem lane
def fail_stem(set_id: str, message: str) -> None:
    log.warning("stems %s failed: %s", set_id, message)
    execute("UPDATE stem_sets SET status = 'failed', error = ?, stage = NULL WHERE id = ?", (message, set_id))


async def run_stems_job(set_id: str) -> None:
    job = one("SELECT * FROM stem_sets WHERE id = ?", (set_id,))
    if not job or job["status"] != "queued":
        return
    started = time.time()
    execute("UPDATE stem_sets SET status = 'running', stage = 'Starting', progress = 0 WHERE id = ?", (set_id,))

    input_path = None
    if job["take_id"]:
        row = one("SELECT audio_path FROM takes WHERE id = ?", (job["take_id"],))
        input_path = row["audio_path"] if row else None
    elif job["source_id"]:
        row = one("SELECT stored_path FROM sources WHERE id = ?", (job["source_id"],))
        input_path = row["stored_path"] if row else None
    if not input_path or not Path(input_path).exists():
        fail_stem(set_id, "the audio for this item is missing")
        return

    last_write = {"at": 0.0}

    def progress(frac: float, stage: str) -> None:
        now = time.time()
        if now - last_write["at"] < 1.0 and frac < 1.0:
            return
        last_write["at"] = now
        execute("UPDATE stem_sets SET progress = ?, stage = ? WHERE id = ?", (round(frac, 3), stage, set_id))

    wanted = [s for s in (job["wanted"] or "").split(",") if s]
    dest = Path(job["folder"]) if job.get("folder") else (config.STEMS_DIR / set_id)
    target_type = "take" if job.get("take_id") else "source"
    target_id = job.get("take_id") or job.get("source_id") or set_id
    log.info("Starting stem separation for %s %s (model=%s, wanted=%s)", target_type, target_id, job["model"], job["wanted"])
    await separate_stems(Path(input_path), dest, job["model"], wanted, job["fmt"], progress, work_root=config.WORK_DIR)

    elapsed = time.time() - started
    changed = execute(
        """UPDATE stem_sets SET status = 'done', stage = NULL, progress = 1,
                  finished_at = ?, elapsed = ?, error = NULL WHERE id = ?""",
        (time.time(), elapsed, set_id),
    )
    if not changed:
        remove_tree(dest)   # deleted while it ran
        return
    bump_average("stems", elapsed)
    log.info("Stem separation %s for %s %s finished in %.1fs -> %s", set_id, target_type, target_id, elapsed, dest)


def fail_cover_lyrics(source_id: str, message: str) -> None:
    row = one("SELECT title FROM sources WHERE id = ?", (source_id,))
    title_str = f" for '{row['title']}'" if row and row.get("title") else ""
    log.warning("cover lyrics extraction %s%s failed: %s", source_id, title_str, message)
    execute("UPDATE sources SET lyrics_state = 'failed', lyrics_error = ?, lyrics_stage = NULL WHERE id = ?",
            (message, source_id))


# An LLM that heard the whole song writes about as many words as Whisper, or more:
# 204 against 205 on Modern Girl, 281 against about 250 on Silly Love Songs.  Well
# under that, it left something out.
# A reply with fewer words than this is not a song's lyrics, whatever it says.
MIN_HEARD_WORDS = 8


async def hear_all(vocal: Path, seconds: float = 0.0, on_progress=None, on_stage=None,
                   title: str = "", should_stop=None, on_download=None) -> dict:
    """What was heard in a separated vocal, by each method that ran, and which one is in use.

    Whisper always runs: it times the lines.  When Settings asks for the external LLM to
    listen, and an external LLM is the provider, the vocal is sent to it too.  A reply that
    looks like lyrics always wins over Whisper's: Whisper can miss a vocal buried in a mix, where
    the model that was asked for the words has no such trouble.  A reply that does not look like
    lyrics (a refusal, a notice, cut-off lines, almost nothing) or no reply at all comes back to
    Whisper's lines, with the reason in the method, so the lyrics always arrive and it is always
    clear who heard them.  Both versions come back, for whoever wants the other.

    The result: `lines` and `method` (what was chosen), `whisper` (Whisper's own lines),
    `llm` (the model's lines, timed, or None) and `model`.

    The method is decided, and logged, before anything runs.  Whisper's own log
    lines appear in both methods, so without this a reader of the log cannot tell
    whether the external LLM is in use until the job has finished.
    """
    name = title or vocal.name
    wanted = get_setting("lyrics.transcriber", "whisper") == "llm"
    external = llm.is_external_enabled()
    model = llm.get_config().get("model") or "the external LLM"
    if wanted and external:
        log.info("Lyrics for '%s': the external LLM (%s) will hear the words; Whisper runs first "
                 "to time the lines", name, model)
    elif wanted:
        log.info("Lyrics for '%s': Whisper. The setting asks for the external LLM, but the "
                 "provider is not External LLM", name)
    else:
        log.info("Lyrics for '%s': Whisper, as set in Settings", name)

    lines = await hear_lines(vocal, on_progress, seconds, should_stop, on_download)
    only_whisper = {"lines": lines, "method": "Whisper", "whisper": lines, "llm": None, "model": model}
    if not (wanted and external):
        return only_whisper
    if on_stage:
        on_stage(f"Listening with {model}")
    log.info("Lyrics for '%s': Whisper timed %d lines; sending the vocal to %s", name, len(lines), model)
    try:
        heard = await llm.hear_lyrics(vocal)
    except Exception as exc:  # noqa: BLE001
        log.warning("Lyrics for '%s': %s could not hear the vocal, keeping Whisper's lines: %s",
                    name, model, exc)
        return {**only_whisper, "method": f"Whisper ({model} could not take the audio: {str(exc)[:160]})"}
    heard_words = sum(len(line.split()) for line in heard)
    reason = llm.held_back(heard)
    if reason is None and (heard_words < MIN_HEARD_WORDS or len(heard) < 2):
        reason = f"returned only {heard_words} word{'s' if heard_words != 1 else ''}"
    if reason:
        log.warning("Lyrics for '%s': %s %s, keeping Whisper's lines", name, model, reason)
        return {**only_whisper, "method": f"Whisper ({model} {reason})"}
    whisper_words = sum(len(line["text"].split()) for line in lines)
    timed = identities.time_lines(lines, heard)
    method = f"{model}, timed by Whisper"
    if timed is None:
        # Its words are not Whisper's, so there is nothing to match the times to: spread them
        # over the stretch Whisper heard singing (or the whole song, if it heard none).
        start, end = (lines[0]["start"], lines[-1]["end"]) if lines else (0.0, seconds)
        timed = identities.spread_lines(heard, start, end if end > start else seconds)
        method = f"{model}, spread over the song (its words differ from Whisper's)"
        log.info("Lyrics for '%s': %s's %d words agree little with Whisper's %d, so its lines are spread "
                 "over the song and kept", name, model, heard_words, whisper_words)
    log.info("Lyrics for '%s': %s heard %d lines, where Whisper heard %d", name, model, len(timed), len(lines))
    return {"lines": timed, "method": method, "whisper": lines, "llm": timed, "model": model}


async def hear(vocal: Path, seconds: float = 0.0, on_progress=None, on_stage=None,
               title: str = "", should_stop=None) -> tuple[list[dict], str]:
    """The lines chosen by `hear_all`, and which method heard them."""
    found = await hear_all(vocal, seconds, on_progress, on_stage, title, should_stop)
    return found["lines"], found["method"]


async def run_cover_lyrics(source_id: str) -> None:
    """Hear the words in a recording: separate its vocal, transcribe it, and lay
    the lines under the sections of the score already transcribed from it."""
    source = one("SELECT * FROM sources WHERE id = ?", (source_id,))
    if not source or source["lyrics_state"] != "queued":
        return
    path = Path(source["stored_path"])
    if not path.exists():
        fail_cover_lyrics(source_id, "the recording is missing")
        return

    started = time.time()
    source_title = source.get("title") or source_id
    log.info("Starting lyrics extraction for source '%s' (%s)", source_title, source_id)
    last = {"at": 0.0}

    def progress(frac: float, stage: str) -> None:
        now = time.time()
        if now - last["at"] < 1.0 and frac < 1.0:
            return
        last["at"] = now
        execute("UPDATE sources SET lyrics_progress = ?, lyrics_stage = ? WHERE id = ?",
                (round(frac, 3), stage, source_id))

    execute("UPDATE sources SET lyrics_state = 'running', lyrics_error = NULL,"
            " lyrics_stage = 'Starting', lyrics_progress = 0 WHERE id = ?", (source_id,))

    work = config.WORK_DIR / f"lyrics-{source_id}"
    vocal = vocal_path(path)
    if vocal.exists():
        # Separated on an earlier run: the same recording and model give the same
        # vocal, and separating is most of the job's time.
        log.info("Lyrics for '%s': reusing the vocal separated earlier", source_title)
        progress(0.60, "Using the vocal separated earlier")
    else:
        # Separation is most of the wait, so it owns most of the bar.
        await separate_stems(path, work, "htdemucs", ["vocals"], "flac",
                             lambda frac, stage: progress(0.02 + 0.58 * frac, "Separating the vocal"),
                             work_root=config.WORK_DIR)
        separated = next(iter(work.glob("vocals.*")), None)
        if not separated:
            fail_cover_lyrics(source_id, "the vocal could not be separated")
            return
        # Moved in only once it is whole, so a run stopped halfway never leaves a
        # partial file to be reused as if it were the vocal.
        os.replace(separated, vocal)

    try:
        seconds = await asyncio.to_thread(instrumental.duration_of, vocal)
        progress(0.62, "Listening for words")
        lines, method = await hear(
            vocal, seconds,
            lambda frac: progress(0.62 + 0.30 * frac, "Listening for words"),
            lambda stage: progress(0.93, stage), title=source_title)
        if not lines:
            fail_cover_lyrics(source_id, "no words were heard in this recording")
            return
        progress(0.97, "Laying the words out")
        sections = identities.score_sections(source["abc"] or "")
        text = await asyncio.to_thread(identities.tag_lyrics, lines, sections, seconds)
        execute("UPDATE sources SET lyrics = ?, lyrics_state = 'done', lyrics_stage = NULL,"
                " lyrics_progress = 1, lyrics_method = ? WHERE id = ?", (text, method, source_id))
        log.info("Lyrics extraction finished for source '%s' in %.1fs (%d lines, heard by %s)",
                 source_title, time.time() - started, len(lines), method)
    finally:
        shutil.rmtree(work, ignore_errors=True)


async def stems_worker() -> None:
    while True:
        job = await STEM_QUEUE.get()
        lyrics_job = job.get("kind") == "lyrics"
        table, fail = ("sources", fail_cover_lyrics) if lyrics_job else ("stem_sets", fail_stem)
        row = one(f"SELECT title FROM {table} WHERE id = ?", (job["id"],))
        task = asyncio.create_task(
            run_cover_lyrics(job["id"]) if lyrics_job else run_stems_job(job["id"]))
        CURRENT_STEMS.clear()
        CURRENT_STEMS.update({"id": job["id"], "started": time.time(), "task": task,
                              "title": row["title"] if row else ""})
        try:
            try:
                await asyncio.wait({task})
            except asyncio.CancelledError:
                # The app is shutting down: stop demucs with it.
                task.cancel()
                with contextlib.suppress(BaseException):
                    await task
                raise
            if task.cancelled():
                fail(job["id"], "cancelled")
            elif task.exception():
                log.error("a CPU job crashed", exc_info=task.exception())
                fail(job["id"], str(task.exception())[:400])
        finally:
            CURRENT_STEMS.clear()
            STEM_QUEUE.task_done()


def cancel_stems(item: dict) -> None:
    if item["status"] == "queued":
        execute("UPDATE stem_sets SET status = 'failed', error = 'cancelled' WHERE id = ? AND status = 'queued'", (item["id"],))
    elif item["status"] == "running" and CURRENT_STEMS.get("id") == item["id"]:
        CURRENT_STEMS["task"].cancel()
