"""Recorded voices: a voice model trained from someone's singing, and a take's vocal sung again in it.

The route VOICE-PERSONA.md arrived at after the token prefix failed in use: a take is rendered as usual, its vocal is
separated (BS-Roformer), converted to the voice (RVC), and mixed back over the rest.  The voice service does the
training and the conversion (voice/server.py, the "voice" compose profile); this module is the app's record of them.

One folder per voice, ``data/voices/<id>/``:

    model.pth, model.index   the trained voice, written by the voice service
    source.*                 the recording a voice was made from (none for a corpus voice: its songs are used)

(``voices.py`` is the score's two voices; this module is the sung one.)
"""
from __future__ import annotations

import logging
import shutil
import time
import uuid
from pathlib import Path

from . import config, db

log = logging.getLogger("yue2.persona")

# A voice in another range sounds wrong at the take's pitch, and only whole octaves keep the vocal in the backing's
# key: so the one pitch setting is an octave, up or down.
MIN_OCTAVE, MAX_OCTAVE = -1, 1
# Training passes over the voice's recordings: enough for a few minutes of singing to settle (100 by ear).
TRAIN_EPOCHS = 100
# A corpus voice trains on at most this many of the corpus's songs: more adds time, not much voice.
CORPUS_SONGS = 15


def folder(persona_id: str) -> Path:
    """Where a voice's files live.  Created on demand."""
    # Not data/personas: on an install that began as YuE2 Studio that name is a link to the corpora.
    path = config.DATA_DIR / "voices" / persona_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def model_file(persona_id: str) -> Path:
    return folder(persona_id) / "model.pth"


def _shape(row) -> dict:
    out = dict(row)
    out["octave"] = clamp_octave(out.get("octave"))
    out["progress"] = float(out.get("progress") or 0.0)
    return out


def all() -> list[dict]:
    return [_shape(row) for row in db.rows("SELECT * FROM voices ORDER BY created_at, name")]


def one(persona_id: str) -> dict | None:
    found = db.rows("SELECT * FROM voices WHERE id = ?", (persona_id,))
    return _shape(found[0]) if found else None


def clamp_octave(value) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(MIN_OCTAVE, min(MAX_OCTAVE, number))


def create(name: str, source: Path | None = None, octave: int = 0, origin_identity: str | None = None) -> dict:
    """A voice with a name and what it is trained from: a recording, or a corpus (``origin_identity``)."""
    name = (name or "").strip() or "Untitled voice"
    persona_id = uuid.uuid4().hex[:12]
    target = folder(persona_id)
    source_path = None
    if source is not None and Path(source).exists():
        suffix = Path(source).suffix or ".wav"
        stored = target / f"source{suffix}"
        if Path(source).resolve() != stored.resolve():
            shutil.copy2(source, stored)
        source_path = str(stored)
    db.execute("INSERT INTO voices (id, name, source_path, origin_identity, octave, state, progress, created_at) "
               "VALUES (?, ?, ?, ?, ?, 'training', 0, ?)",
               (persona_id, name, source_path, origin_identity, clamp_octave(octave), time.time()))
    log.info("voice %s created from %s", name, source_path or f"corpus {origin_identity}")
    return one(persona_id)


def training(persona_id: str, progress: float = 0.0) -> None:
    db.execute("UPDATE voices SET state = 'training', progress = ?, error = NULL WHERE id = ?",
               (float(progress), persona_id))


def ready(persona_id: str, model_path: str) -> None:
    db.execute("UPDATE voices SET model_path = ?, state = 'ready', progress = 1, error = NULL WHERE id = ?",
               (model_path, persona_id))


def failed(persona_id: str, error: str) -> None:
    db.execute("UPDATE voices SET state = 'failed', error = ? WHERE id = ?", (error[:500], persona_id))


def usable(persona: dict | None) -> bool:
    return bool(persona) and persona.get("state") == "ready" and Path(persona.get("model_path") or "").is_file()


def update(persona_id: str, **fields) -> dict | None:
    allowed = {"name", "octave"}
    wanted = {k: v for k, v in fields.items() if k in allowed}
    if "octave" in wanted:
        wanted["octave"] = clamp_octave(wanted["octave"])
    if wanted:
        sets = ", ".join(f"{key} = ?" for key in wanted)
        db.execute(f"UPDATE voices SET {sets} WHERE id = ?", (*wanted.values(), persona_id))
    return one(persona_id)


def delete(persona_id: str) -> None:
    db.execute("UPDATE takes SET voice_id = NULL WHERE voice_id = ?", (persona_id,))
    db.execute("DELETE FROM voices WHERE id = ?", (persona_id,))
    shutil.rmtree(folder(persona_id), ignore_errors=True)


def describe(persona: dict | None) -> str:
    """A short line for logs."""
    if not persona:
        return ""
    octave = persona.get("octave") or 0
    return persona["name"] + (f", {octave:+d} octave" if octave else "")
