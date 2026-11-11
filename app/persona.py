"""Recorded voices: a voice model trained from someone's singing, and a take's vocal sung again in it.

The route VOICE-PERSONA.md arrived at after the token prefix failed in use: a take is rendered as usual, its vocal is
separated (BS-Roformer), converted to the voice (RVC), and mixed back over the rest.  The voice service does the
training and the conversion (voice/server.py, the "voice" compose profile); this module is the app's record of them.

One folder per voice, ``data/voices/<id>/``:

    model.pth, model.index   the trained voice, written by the voice service
    recordings/              recordings made with the recorder or uploaded for it (table voice_recordings, which
                             also references library recordings by id; a corpus voice uses the corpus's songs)
    vocals/, excerpts/       what training learned from, kept to listen to (Settings → Storage can drop them)

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
# How far a voice's vocal can be set above or below the rendered vocal's level in the mix, in dB.
LEVELS_DB = (-3.0, 0.0, 3.0, 6.0)
BACKING_DB = (-9.0, -6.0, -3.0, 0.0)
# Training passes over the voice's recordings: enough for a few minutes of singing to settle (100 by ear).
TRAIN_EPOCHS = 100
LIKENESS = (0.25, 0.5, 0.75, 1.0)   # RVC's index rate: higher keeps closer to the singer's own sounds
# How much of a short room goes under the converted vocal (voice/server.py settle): dry, subtle (as it always was), more.
ROOMS = (0.0, 0.14, 0.28)
ROOM_NAMES = {0.0: "dry", 0.14: "subtle", 0.28: "more"}
# RVC's protect: how far breaths and consonants keep the rendered vocal's own sounds rather than the singer's, which
# can tear them (0.5 converts them like the rest).  And its RMS mix rate: whose loudness contour the vocal follows,
# the rendered vocal's (low) or the converted one's own (1).
PROTECT = (0.15, 0.33, 0.5)
DYNAMICS = (0.25, 0.5, 1.0)
# The converted vocal's formants, moved with its pitch kept (voice/server.py shift_formants): below 1 a larger, deeper
# voice, above 1 a smaller, brighter one.  And how much of the vocal the voice sings, the rest being the rendered
# vocal it was made from (wet against dry).
FORMANTS = (0.88, 0.94, 1.0, 1.06, 1.12)
WETS = (0.25, 0.5, 0.75, 1.0)
PASSES = (25, 50, 100, 200, 400, 800)
# A corpus voice samples at most this many of the corpus's songs: each is separated before the minutes of singing
# (Settings) are shared across them, and separating more adds time for little.
CORPUS_SONGS = 30


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
    out["recordings"] = db.rows("SELECT COUNT(*) AS n FROM voice_recordings WHERE voice_id = ?", (out["id"],))[0]["n"]
    # Without its index, Likeness has nothing to draw on (a voice imported from a .pth alone).
    out["has_index"] = (config.DATA_DIR / "voices" / out["id"] / "model.index").is_file()
    out["octave"] = clamp_octave(out.get("octave"))
    out["level_db"] = clamp_level(out.get("level_db"))
    out["likeness"] = clamp_likeness(out.get("likeness"))
    out["backing_db"] = clamp_backing(out.get("backing_db"))
    out["room"] = clamp_room(out.get("room"))
    out["brightness"] = clamp_brightness(out.get("brightness"))
    out["protect"] = clamp_protect(out.get("protect"))
    out["dynamics"] = clamp_dynamics(out.get("dynamics"))
    out["formant"] = clamp_formant(out.get("formant"))
    out["wet"] = clamp_wet(out.get("wet"))
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


def clamp_level(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(LEVELS_DB, key=lambda level: abs(level - number))


def clamp_backing(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(BACKING_DB, key=lambda level: abs(level - number))


def clamp_room(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ROOMS[1]
    return min(ROOMS, key=lambda step: abs(step - number))


def _step(steps, value, fallback):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return min(steps, key=lambda step: abs(step - number))


def clamp_protect(value) -> float:
    return _step(PROTECT, value, 0.33)


def clamp_dynamics(value) -> float:
    return _step(DYNAMICS, value, 0.25)


def clamp_formant(value) -> float:
    return _step(FORMANTS, value, 1.0)


def clamp_wet(value) -> float:
    return _step(WETS, value, 1.0)


def clamp_brightness(value) -> int:
    """1: the converted vocal's upper range is lifted to the rendered one's (as it always was); 0: left as converted."""
    if isinstance(value, str):
        return 0 if value.strip().lower() in ("0", "off", "false", "no") else 1
    return 0 if value is not None and not value else 1


def clamp_likeness(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.75
    return min(LIKENESS, key=lambda step: abs(step - number))


def create(name: str, source: Path | None = None, octave: int = 0, origin_identity: str | None = None,
           vocals_only: bool = False, state: str = "training") -> dict:
    """A voice with a name and what it is trained from: recordings (``source`` is a first one), or a corpus
    (``origin_identity``).  A voice of recordings can start empty (state "new"), and trains when asked."""
    name = (name or "").strip() or "Untitled voice"
    persona_id = uuid.uuid4().hex[:12]
    target = folder(persona_id)
    target.mkdir(parents=True, exist_ok=True)
    db.execute("INSERT INTO voices (id, name, origin_identity, octave, vocals_only, state, progress, "
               "created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
               (persona_id, name, origin_identity, clamp_octave(octave), 1 if vocals_only else 0, state, time.time()))
    if source is not None and Path(source).exists():
        add_file(persona_id, Path(source), "uploaded", Path(source).name, vocals_only)
    log.info("voice %s created from %s", name, f"corpus {origin_identity}" if origin_identity else "recordings")
    return one(persona_id)


# ---------------------------------------------------------------- a voice's recordings

def _seconds(path: Path) -> float | None:
    from .library import audio_duration  # noqa: PLC0415 - library imports a great deal; only this needs it

    try:
        return audio_duration(path)
    except Exception:  # noqa: BLE001 - a length it cannot read is shown as unknown
        return None


def add_file(persona_id: str, source: Path, kind: str, title: str, vocals_only: bool) -> dict:
    """A recording made with the recorder or uploaded, copied into the voice's own folder."""
    rid = uuid.uuid4().hex[:12]
    stored = folder(persona_id) / "recordings" / f"{rid}{source.suffix.lower() or '.wav'}"
    stored.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, stored)
    db.execute("INSERT INTO voice_recordings (id, voice_id, kind, path, title, vocals_only, seconds, created_at) "
               "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
               (rid, persona_id, kind, str(stored), (title or stored.name)[:200], 1 if vocals_only else 0,
                _seconds(stored), time.time()))
    return recording(persona_id, rid)


def add_library(persona_id: str, source: dict, vocals_only: bool) -> dict:
    """A library recording, referenced by id: nothing is copied, and deleting it from the library later leaves the
    trained voice as it is (the row then shows it missing)."""
    rid = uuid.uuid4().hex[:12]
    db.execute("INSERT INTO voice_recordings (id, voice_id, kind, source_id, title, vocals_only, seconds, created_at) "
               "VALUES (?, ?, 'library', ?, ?, ?, ?, ?)",
               (rid, persona_id, source["id"], (source.get("title") or source.get("filename") or "")[:200],
                1 if vocals_only else 0, source.get("duration"), time.time()))
    return recording(persona_id, rid)


def _resolve(row: dict) -> dict:
    out = dict(row)
    path = None
    if row["kind"] == "library":
        source = db.rows("SELECT stored_path FROM sources WHERE id = ?", (row["source_id"],))
        path = source[0]["stored_path"] if source else None
    else:
        path = row["path"]
    out["file"] = path if path and Path(path).is_file() else None
    out["missing"] = out["file"] is None
    if out["seconds"] is None and out["file"]:     # a recording kept from before lengths were measured
        out["seconds"] = _seconds(Path(out["file"]))
        if out["seconds"] is not None:
            db.execute("UPDATE voice_recordings SET seconds = ? WHERE id = ?", (out["seconds"], row["id"]))
    return out


def recordings(persona_id: str) -> list[dict]:
    return [_resolve(row) for row in db.rows("SELECT * FROM voice_recordings WHERE voice_id = ? ORDER BY created_at",
                                             (persona_id,))]


def recording(persona_id: str, rid: str) -> dict | None:
    found = db.rows("SELECT * FROM voice_recordings WHERE voice_id = ? AND id = ?", (persona_id, rid))
    return _resolve(found[0]) if found else None


def set_vocals_only(persona_id: str, rid: str, value: bool) -> dict | None:
    db.execute("UPDATE voice_recordings SET vocals_only = ? WHERE voice_id = ? AND id = ?",
               (1 if value else 0, persona_id, rid))
    return recording(persona_id, rid)


def remove_recording(persona_id: str, rid: str) -> None:
    """Out of the voice's list; its own copy is deleted, a library recording is left in the library."""
    found = recording(persona_id, rid)
    if not found:
        return
    if found["kind"] != "library" and found.get("path"):
        Path(found["path"]).unlink(missing_ok=True)
    db.execute("DELETE FROM voice_recordings WHERE voice_id = ? AND id = ?", (persona_id, rid))


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
    allowed = {"name", "octave", "level_db", "likeness", "backing_db", "room", "brightness", "protect", "dynamics",
               "formant", "wet"}
    wanted = {k: v for k, v in fields.items() if k in allowed}
    if "octave" in wanted:
        wanted["octave"] = clamp_octave(wanted["octave"])
    if "level_db" in wanted:
        wanted["level_db"] = clamp_level(wanted["level_db"])
    if "backing_db" in wanted:
        wanted["backing_db"] = clamp_backing(wanted["backing_db"])
    if "likeness" in wanted:
        wanted["likeness"] = clamp_likeness(wanted["likeness"])
    if "room" in wanted:
        wanted["room"] = clamp_room(wanted["room"])
    if "brightness" in wanted:
        wanted["brightness"] = clamp_brightness(wanted["brightness"])
    if "protect" in wanted:
        wanted["protect"] = clamp_protect(wanted["protect"])
    if "dynamics" in wanted:
        wanted["dynamics"] = clamp_dynamics(wanted["dynamics"])
    if "formant" in wanted:
        wanted["formant"] = clamp_formant(wanted["formant"])
    if "wet" in wanted:
        wanted["wet"] = clamp_wet(wanted["wet"])
    if wanted:
        sets = ", ".join(f"{key} = ?" for key in wanted)
        db.execute(f"UPDATE voices SET {sets} WHERE id = ?", (*wanted.values(), persona_id))
    return one(persona_id)


SETTINGS = ("octave", "level_db", "likeness", "backing_db", "room", "brightness", "protect", "dynamics", "formant", "wet")


def copy(persona_id: str, name: str, settings: dict | None = None) -> dict | None:
    """A new voice that sings with the same model as `persona_id`, under its own name and with `settings` as its
    defaults (the source's where not given): a voice auditioned into a sound of its own, kept.  The model files are
    linked where the filesystem allows, so a copy costs no space; deleting either voice leaves the other whole."""
    source = one(persona_id)
    if not usable(source):
        return None
    new_id = uuid.uuid4().hex[:12]
    target = folder(new_id)
    for file in ("model.pth", "model.index"):
        found = folder(persona_id) / file
        if found.is_file():
            try:
                (target / file).hardlink_to(found)
            except OSError:
                shutil.copy2(found, target / file)
    db.execute("INSERT INTO voices (id, name, state, progress, model_path, created_at) VALUES (?, ?, 'ready', 1, ?, ?)",
               (new_id, (name or "").strip()[:80] or f"{source['name']} (copy)", str(target / "model.pth"), time.time()))
    wanted = {key: (settings or {}).get(key, source.get(key)) for key in SETTINGS}
    made = update(new_id, **{k: v for k, v in wanted.items() if v is not None})
    log.info("voice %s made from %s with its own settings", made["name"], source["name"])
    return made


def delete(persona_id: str) -> None:
    db.execute("UPDATE takes SET voice_id = NULL WHERE voice_id = ?", (persona_id,))
    db.execute("DELETE FROM voices WHERE id = ?", (persona_id,))
    db.execute("DELETE FROM voice_recordings WHERE voice_id = ?", (persona_id,))
    shutil.rmtree(folder(persona_id), ignore_errors=True)


def describe(persona: dict | None) -> str:
    """A short line for logs."""
    if not persona:
        return ""
    octave = persona.get("octave") or 0
    return (persona["name"] + (f", {octave:+d} octave" if octave else "")
            + f", vocal {persona.get('level_db') or 0:+g} dB, instruments {persona.get('backing_db') or 0:+g} dB"
            + f", likeness {round(100 * float(persona.get('likeness', 0.75)))}%"
            + f", room {ROOM_NAMES.get(clamp_room(persona.get('room')), 'subtle')}"
            + (", brightness off" if not clamp_brightness(persona.get("brightness")) else "")
            + f", protect {clamp_protect(persona.get('protect')):g}, dynamics {clamp_dynamics(persona.get('dynamics')):g}"
            + (f", formant {clamp_formant(persona.get('formant')):g}" if clamp_formant(persona.get("formant")) != 1.0 else "")
            + (f", {round(100 * clamp_wet(persona.get('wet')))}% wet" if clamp_wet(persona.get("wet")) != 1.0 else ""))
