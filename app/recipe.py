"""A take's recipe as a file: what made it, without its audio, to keep, share or import (#58).

The file says what a person chose and what the engine was given: the words, the style and the score, the seeds,
the settings and the LoRAs by name.  Nothing in it belongs to one install (no ids, no paths, no keys), and nothing
is specific to one engine: either can render it.  Where it came from (the app's version, the engine that rendered
it, the model size) is there for information, and an import ignores it.

A take made from a recording (a cover, or an instrumental from a recording) names its recording: title, file name,
length and fingerprint (sha256).  The recording itself can travel beside the file (#60: in the zip under
`recording/`, or chosen with it); without it, the take arrives as the kind it was saved as, linked to that recording
when it is in the library, or later when it is imported.
"""
from __future__ import annotations

import json
import time
from typing import Any

FORMAT = "yeufonic-take"
VERSION = 1
SUFFIX = ".yeufonic.json"
MAX_BYTES = 1_000_000

# The take's own settings, by the name the file uses for each and the take's column.
FIELDS = {
    "title": "title",
    "kind": "kind",
    "style": "style",
    "lyrics": "lyrics",
    "brief": "brief",
    "score": "abc",
    "mode": "mode",
    "seed": "seed",
    "sound_seed": "sound_seed",
    "length_cap": "max_duration",
    "length_cap_set": "cap_typed",
    "plan_variety": "variety",
    "harmony": "harmony",
    "interpretation": "interpretation",
    "feel": "feel",
    "production_polish": "realaudio",
    "normalise": "normalise",
    "style_lora": "style_lora",
    "style_lora_planner": "style_lora_clip",
    "style_lora_sound": "style_lora_model",
    "voice_lora": "voice_lora",
    "voice_lora_strength": "voice_lora_strength",
    "voice_lora_planner": "voice_lora_clip",
    "sampler_steps": "sampler_steps",
    "avoid": "avoid",
    "target_key": "target_key",
    "target_bpm": "target_bpm",
    "target_meter": "target_meter",
    "max_score_tokens": "max_abc_tokens",
    "chord_hold_limit": "chord_hold_limit",
    "chord_outside_bonus": "chord_outside_bonus",
    "chord_sections": "chord_sections",
    "follow_structure": "follow_structure",
    "voice_cues": "voice_cues",
    "target_lufs": "target_lufs",
    "fade_out_seconds": "fade_out_seconds",
    "cfg_scale": "cfg_scale",
    "hook_score": "hook_abc",
    "hook_section": "hook_section",
    "note": "take_note",
}
FLAGS = {"length_cap_set", "production_polish", "normalise"}


def recording_of(source: dict | None) -> dict | None:
    """What a recipe says of a recording: enough to find it again, nothing of this install."""
    if not source:
        return None
    return {"title": source.get("title"), "file": source.get("filename"), "duration": source.get("duration"),
            "sha256": source.get("sha256")}


def export(take: dict, version: str, voice: str | None = None, recording: dict | None = None) -> dict:
    """The recipe of a take, as the file holds it.

    ``voice`` is a recorded voice's *name*, not its id: a recipe holds nothing that belongs to one install, and
    an import matches the name against the voices that install has.  ``recording``: the take's recording as
    recording_of() gives it; without one, the recording a take imported without it still names.
    """
    out: dict[str, Any] = {}
    for name, column in FIELDS.items():
        value = take.get(column)
        out[name] = bool(value) if name in FLAGS else value
    if voice:
        out["voice"] = voice
        # The take's own octave, levels and likeness for that voice.
        try:
            settings = json.loads(take.get("voice_mix") or "null")
        except (TypeError, ValueError):
            settings = None
        if isinstance(settings, dict) and settings:
            out["voice_settings"] = settings
    if recording is None and take.get("recording_ref"):
        try:
            recording = json.loads(take["recording_ref"])
        except (TypeError, ValueError):
            recording = None
    if isinstance(recording, dict) and recording:
        out["recording"] = recording
    mastering = None
    if take.get("fx_chain"):
        try:
            mastering = json.loads(take["fx_chain"])
        except (TypeError, ValueError):
            mastering = None
    out["mastering"] = mastering if isinstance(mastering, dict) and mastering else None
    # Sampling values set by hand (#72), as an object: {"plan": {...}, "render": {...}}.
    try:
        sampling = json.loads(take.get("sampling") or "null")
    except (TypeError, ValueError):
        sampling = None
    if isinstance(sampling, dict) and sampling:
        out["sampling"] = sampling
    return {
        "format": FORMAT,
        "version": VERSION,
        "exported": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "from": {"app": "Yeufonic", "version": version, "engine": take.get("engine"),
                 "model": take.get("checkpoint")},
        "take": out,
    }


class RecipeError(ValueError):
    """Why a file cannot be imported, in words for the person importing it."""


def read(data: Any) -> dict:
    """The take a recipe describes, as take columns, from a parsed file.  Raises RecipeError for a file that is
    not a recipe, or is one from a later Yeufonic than this.  What the columns may hold is checked where the take
    is made, as for one made in the page."""
    if not isinstance(data, dict) or data.get("format") != FORMAT or not isinstance(data.get("take"), dict):
        raise RecipeError("this is not a Yeufonic take file")
    version = data.get("version")
    if not isinstance(version, int) or version < 1:
        raise RecipeError("this take file has no version Yeufonic knows")
    if version > VERSION:
        raise RecipeError("this take file is from a later Yeufonic: update to import it")
    take = data["take"]
    columns = {column: take.get(name) for name, column in FIELDS.items() if name in take}
    for name in FLAGS:
        if name in take:
            columns[FIELDS[name]] = 1 if take[name] else 0
    # A take arrives as the kind it was saved as: nothing is converted on import (#60).
    if columns.get("kind") not in ("song", "instrumental", "cover"):
        columns["kind"] = "song"
    recording = take.get("recording")
    if isinstance(recording, dict) and recording:
        columns["recording_ref"] = {key: recording.get(key) for key in ("title", "file", "duration", "sha256")}
    mastering = take.get("mastering")
    columns["fx_chain"] = json.dumps(mastering) if isinstance(mastering, dict) and mastering else None
    sampling = take.get("sampling")
    if isinstance(sampling, dict) and sampling:
        columns["sampling"] = sampling      # checked where the take is made
    return columns


def loras_named(columns: dict) -> list[str]:
    """The LoRAs a recipe uses, by file name."""
    return [name for name in (columns.get("style_lora"), columns.get("voice_lora")) if name]


def filename(title: str | None) -> str:
    safe = "".join(ch for ch in (title or "take") if ch.isalnum() or ch in " -_")[:60].strip() or "take"
    return safe + SUFFIX
