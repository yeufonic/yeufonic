"""Install a staged Starter Pack into the user's Yeufonic library.

A Starter Pack is downloaded by ``scripts/fetch-models.sh --demos`` (or a native
installer) into ``<DATA_DIR>/starter-pack/`` alongside any missing LoRAs in
``models/loras/``.  On app startup (or via ``POST /api/starter-pack/install`` /
``python -m app.starter_pack``), ``install_pending()`` imports the staged space,
takes, artwork, cover recordings, and voices into SQLite and ``DATA_DIR`` using
paths resolved for the destination machine (Docker ``/data``, Linux, macOS, or
Windows).

Imports are strictly additive and idempotent:
- Reuses an existing space named "Starter Pack" (case-insensitive) or creates it.
- Skips voices that already exist by id or name, linking imported takes to the
  existing voice without overwriting the user's files or settings.
- Skips sources that already exist by id or sha256.
- Skips takes that already exist by id so re-running never overwrites edits.
"""
from __future__ import annotations

import json
import logging
import shutil
import time
from pathlib import Path
from typing import Any

from . import artwork, config, library
from .db import execute, get_setting, migrate, one, set_setting, transaction

log = logging.getLogger("yue2.starter_pack")

FORMAT = "yeufonic-starter-pack"
VERSION = 1
SPACE_NAME = "Starter Pack"
SPACE_ID = "starter-pack"
PACK_FILE = "pack.json"
INSTALLED_SETTING = "starter_pack.installed"

# Portable take columns copied from a pack entry into the destination database.
# Install-specific fields (prompt_id, identity_id, persona_id, trashed_from,
# audio_path, space_id, source_id, voice_id) are handled explicitly.
TAKE_COLUMNS = (
    "kind",
    "title",
    "style",
    "lyrics",
    "abc",
    "mode",
    "seed",
    "checkpoint",
    "max_duration",
    "duration",
    "favourite",
    "created_at",
    "finished_at",
    "elapsed",
    "auto_render",
    "variety",
    "harmony",
    "interpretation",
    "feel",
    "realaudio",
    "voice_lora",
    "voice_lora_strength",
    "voice_lora_clip",
    "vocal_check",
    "style_lora",
    "style_lora_model",
    "style_lora_clip",
    "loudness",
    "sound_seed",
    "normalise",
    "normalised",
    "weak_dismissed",
    "engine",
    "normalised_to",
    "sampler_steps",
    "avoid",
    "target_key",
    "target_bpm",
    "target_meter",
    "take_note",
    "sampling",
    "recording_ref",
    "max_abc_tokens",
    "chord_hold_limit",
    "chord_outside_bonus",
    "chord_sections",
    "follow_structure",
    "voice_cues",
    "cap_typed",
    "brief",
    "note_dismissed",
    "target_lufs",
    "fade_out_seconds",
    "fx_chain",
    "hook_abc",
    "hook_section",
    "cfg_scale",
    "voice_mix",
)

VOICE_COLUMNS = (
    "name",
    "prefix_seconds",
    "head",
    "created_at",
    "octave",
    "level_db",
    "likeness",
    "backing_db",
    "vocals_only",
    "room",
    "brightness",
    "protect",
    "dynamics",
    "formant",
    "wet",
    "tail_gate",
    "rmvpe_thred",
    "f0_floor",
)

SOURCE_COLUMNS = (
    "title",
    "filename",
    "sha256",
    "created_at",
    "abc",
    "abc_updated_at",
    "transcribe_state",
    "lyrics",
    "lyrics_state",
    "lyrics_progress",
    "duration",
    "lyrics_method",
    "origin",
    "instrument",
)


def stage_dir() -> Path:
    return config.DATA_DIR / "starter-pack"


def _safe_rel(root: Path, rel: str | None) -> Path | None:
    """Resolve a relative path inside ``root``, rejecting traversal."""
    if not rel:
        return None
    root_res = root.resolve()
    target = (root_res / rel).resolve()
    try:
        target.relative_to(root_res)
    except ValueError:
        log.warning("Starter Pack ignored unsafe relative path: %s", rel)
        return None
    return target


def _place_file(src: Path, dst: Path, *, move: bool = True) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if move:
        try:
            shutil.move(str(src), str(dst))
            return
        except OSError:
            pass
    shutil.copy2(src, dst)


def _find_or_create_space(space_name: str, preferred_id: str | None = None) -> str:
    found = one("SELECT id FROM spaces WHERE LOWER(name) = LOWER(?)", (space_name,))
    if found:
        return found["id"]
    sid = preferred_id or SPACE_ID
    if one("SELECT id FROM spaces WHERE id = ?", (sid,)):
        sid = SPACE_ID
        if one("SELECT id FROM spaces WHERE id = ?", (sid,)):
            sid = f"{SPACE_ID}-{int(time.time())}"
    execute(
        "INSERT INTO spaces (id, name, created_at) VALUES (?, ?, ?)",
        (sid, space_name, time.time()),
    )
    return sid


def _import_voice(entry: dict[str, Any], stage: Path, *, move: bool) -> tuple[str | None, bool]:
    """Import one voice if not already present. Returns (voice_id_in_db, added)."""
    vid = str(entry.get("id") or "").strip()
    name = str(entry.get("name") or "").strip()
    if not vid or not name:
        return None, False

    existing = one("SELECT id FROM voices WHERE id = ?", (vid,))
    if not existing:
        existing = one("SELECT id FROM voices WHERE LOWER(name) = LOWER(?)", (name,))
    if existing:
        return existing["id"], False

    files = entry.get("files") or {}
    src_model = _safe_rel(stage, files.get("model"))
    if not src_model or not src_model.is_file():
        log.info("Starter Pack voice '%s' (%s) skipped: model file not staged", name, vid)
        return None, False

    dest_dir = config.DATA_DIR / "voices" / vid
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_model = dest_dir / "model.pth"
    if not dest_model.is_file():
        _place_file(src_model, dest_model, move=move)

    src_index = _safe_rel(stage, files.get("index"))
    if src_index and src_index.is_file():
        dest_index = dest_dir / "model.index"
        if not dest_index.is_file():
            _place_file(src_index, dest_index, move=move)

    row: dict[str, Any] = {
        "id": vid,
        "state": "ready",
        "progress": 1.0,
        "model_path": str(dest_model),
        "created_at": entry.get("created_at") or time.time(),
    }
    for col in VOICE_COLUMNS:
        if col in entry and entry[col] is not None:
            row[col] = entry[col]
    cols = ", ".join(row)
    placeholders = ", ".join("?" * len(row))
    execute(f"INSERT INTO voices ({cols}) VALUES ({placeholders})", tuple(row.values()))
    return vid, True


def _import_source(entry: dict[str, Any], stage: Path, *, move: bool) -> tuple[str | None, bool]:
    """Import one cover recording source if not already present. Returns (source_id_in_db, added)."""
    sid = str(entry.get("id") or "").strip()
    sha256 = str(entry.get("sha256") or "").strip()
    filename = str(entry.get("filename") or "").strip()
    title = str(entry.get("title") or filename or "Recording").strip()
    if not sid or not sha256 or not filename:
        return None, False

    existing = one("SELECT id FROM sources WHERE id = ?", (sid,))
    if not existing:
        existing = one("SELECT id FROM sources WHERE sha256 = ?", (sha256,))
    if existing:
        return existing["id"], False

    src_audio = _safe_rel(stage, entry.get("file"))
    if not src_audio or not src_audio.is_file():
        log.warning("Starter Pack source '%s' (%s) missing audio file", title, sid)
        return None, False

    suffix = Path(filename).suffix or src_audio.suffix or ".flac"
    dest_audio = library.source_path(sha256, filename, title, suffix)
    if not dest_audio.is_file():
        _place_file(src_audio, dest_audio, move=move)

    row: dict[str, Any] = {
        "id": sid,
        "title": title,
        "filename": filename,
        "stored_path": str(dest_audio),
        "sha256": sha256,
        "created_at": entry.get("created_at") or time.time(),
    }
    for col in SOURCE_COLUMNS:
        if col in entry and entry[col] is not None:
            row[col] = entry[col]
    cols = ", ".join(row)
    placeholders = ", ".join("?" * len(row))
    execute(f"INSERT INTO sources ({cols}) VALUES ({placeholders})", tuple(row.values()))
    return sid, True


def _import_take(
    entry: dict[str, Any],
    stage: Path,
    space_id: str,
    voice_map: dict[str, str],
    source_map: dict[str, str],
    *,
    move: bool,
) -> bool:
    """Import one take if its id is not already in the database. Returns True if added."""
    tid = str(entry.get("id") or "").strip()
    title = str(entry.get("title") or "Untitled").strip()
    if not tid:
        return False

    if one("SELECT id FROM takes WHERE id = ?", (tid,)):
        return False

    files = entry.get("files") or {}
    src_audio = _safe_rel(stage, files.get("audio"))
    if not src_audio or not src_audio.is_file():
        log.warning("Starter Pack take '%s' (%s) skipped: audio file missing", title, tid)
        return False

    dest_audio = library.take_audio_path(tid, title)
    if src_audio.suffix and src_audio.suffix.lower() != dest_audio.suffix.lower():
        dest_audio = dest_audio.with_suffix(src_audio.suffix.lower())
    _place_file(src_audio, dest_audio, move=move)

    src_peaks = _safe_rel(stage, files.get("peaks"))
    if src_peaks and src_peaks.is_file():
        dest_peaks = dest_audio.with_suffix(".peaks.json")
        if not dest_peaks.is_file():
            _place_file(src_peaks, dest_peaks, move=move)

    for stem_key, stem_name in (("voice_backing", "backing.flac"), ("voice_vocal", "vocal.flac")):
        src_stem = _safe_rel(stage, files.get(stem_key))
        if src_stem and src_stem.is_file():
            dest_stem = dest_audio.parent / "voice" / stem_name
            if not dest_stem.is_file():
                _place_file(src_stem, dest_stem, move=move)

    src_art = _safe_rel(stage, files.get("art"))
    if src_art and src_art.is_file():
        dest_art = artwork.png_path(tid)
        if not dest_art.is_file():
            _place_file(src_art, dest_art, move=move)
    src_art_words = _safe_rel(stage, files.get("art_words"))
    if src_art_words and src_art_words.is_file():
        dest_words = artwork.words_path(tid)
        if not dest_words.is_file():
            _place_file(src_art_words, dest_words, move=move)

    row: dict[str, Any] = {
        "id": tid,
        "kind": entry.get("kind") or "song",
        "title": title,
        "style": entry.get("style") or "",
        "lyrics": entry.get("lyrics") or "",
        "mode": entry.get("mode") or "full",
        "seed": int(entry.get("seed") if entry.get("seed") is not None else 0),
        "checkpoint": entry.get("checkpoint") or "yue2_3b_bf16.safetensors",
        "status": "done",
        "audio_path": str(dest_audio),
        "created_at": entry.get("created_at") or time.time(),
        "space_id": space_id,
    }
    for col in TAKE_COLUMNS:
        if col in entry and entry[col] is not None:
            val = entry[col]
            if col in ("fx_chain", "voice_mix", "sampling", "recording_ref") and isinstance(val, (dict, list)):
                val = json.dumps(val)
            row[col] = val

    # Store normalised=0 when we ship a single audio file (not *.normalised.flac)
    # so library.rendered_path() resolves cleanly to dest_audio.
    if not library.is_normalised_file(dest_audio):
        row["normalised"] = 0

    src_id = entry.get("source_id")
    if src_id and src_id in source_map:
        row["source_id"] = source_map[src_id]
    voice_id = entry.get("voice_id")
    if voice_id and voice_id in voice_map:
        row["voice_id"] = voice_map[voice_id]

    cols = ", ".join(row)
    placeholders = ", ".join("?" * len(row))
    execute(f"INSERT INTO takes ({cols}) VALUES ({placeholders})", tuple(row.values()))

    try:
        library.write_take_note(row, dest_audio)
    except OSError as exc:
        log.warning("Starter Pack could not write take.json for %s: %s", tid, exc)
    return True


def install_pending(stage: Path | None = None, *, keep_stage: bool = False) -> dict[str, Any]:
    """Import a staged Starter Pack from ``stage`` (default ``DATA_DIR/starter-pack``).

    Returns a summary dict with ``installed`` (bool) and item counts.
    """
    stage_path = Path(stage) if stage is not None else stage_dir()
    pack_path = stage_path / PACK_FILE
    if not pack_path.is_file():
        return {"installed": False, "code": "none"}

    try:
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log.warning("Starter Pack manifest unreadable at %s: %s", pack_path, exc)
        return {"installed": False, "code": "invalid", "error": str(exc)}

    if not isinstance(pack, dict) or pack.get("format") != FORMAT:
        log.warning("Starter Pack at %s has unexpected format", pack_path)
        return {"installed": False, "code": "invalid"}

    version = pack.get("version")
    if not isinstance(version, int) or version < 1 or version > VERSION:
        log.warning("Starter Pack at %s has unsupported version %r", pack_path, version)
        return {"installed": False, "code": "unsupported_version"}

    space_name = str(pack.get("space_name") or SPACE_NAME).strip() or SPACE_NAME
    move = not keep_stage

    voices_added = voices_skipped = 0
    sources_added = sources_skipped = 0
    takes_added = takes_skipped = 0
    voice_map: dict[str, str] = {}
    source_map: dict[str, str] = {}

    with transaction():
        space_id = _find_or_create_space(space_name, preferred_id=SPACE_ID)

        for v in pack.get("voices") or []:
            mapped_id, added = _import_voice(v, stage_path, move=move)
            if mapped_id and v.get("id"):
                voice_map[str(v["id"])] = mapped_id
            if added:
                voices_added += 1
            elif mapped_id:
                voices_skipped += 1

        for s in pack.get("sources") or []:
            mapped_id, added = _import_source(s, stage_path, move=move)
            if mapped_id and s.get("id"):
                source_map[str(s["id"])] = mapped_id
            if added:
                sources_added += 1
            elif mapped_id:
                sources_skipped += 1

        for t in pack.get("takes") or []:
            if _import_take(t, stage_path, space_id, voice_map, source_map, move=move):
                takes_added += 1
            else:
                takes_skipped += 1

        record = {
            "version": version,
            "pack_id": pack.get("pack_id") or "",
            "space_id": space_id,
            "space_name": space_name,
            "installed_at": time.time(),
        }
        set_setting(INSTALLED_SETTING, json.dumps(record))

    if not keep_stage:
        shutil.rmtree(stage_path, ignore_errors=True)

    return {
        "installed": True,
        "space_id": space_id,
        "space_name": space_name,
        "takes_added": takes_added,
        "takes_skipped": takes_skipped,
        "voices_added": voices_added,
        "voices_skipped": voices_skipped,
        "sources_added": sources_added,
        "sources_skipped": sources_skipped,
    }


def status() -> dict[str, Any]:
    raw = get_setting(INSTALLED_SETTING)
    installed = None
    if raw:
        try:
            installed = json.loads(raw)
        except ValueError:
            installed = None
    return {
        "pending": (stage_dir() / PACK_FILE).is_file(),
        "installed": installed,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description=(
            "Import a staged Yeufonic Starter Pack into DATA_DIR. "
            "Options: --stage PATH (default: DATA_DIR/starter-pack), "
            "--keep-stage (copy files instead of moving and keep stage folder)."
        )
    )
    ap.add_argument("--stage", type=Path, default=None)
    ap.add_argument("--keep-stage", action="store_true")
    args = ap.parse_args(argv)

    migrate()
    result = install_pending(stage=args.stage, keep_stage=args.keep_stage)
    print(json.dumps(result, indent=2))
    return 0 if result.get("installed") or result.get("code") == "none" else 1


if __name__ == "__main__":
    raise SystemExit(main())
