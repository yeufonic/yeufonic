"""Vocal personas: one person's recordings tokenised, applied at render as a prefix of its own tokens.

This is the other route to a singer's character than a corpus LoRA, and the one VOICE-PERSONA.md arrived
at by measurement: nothing is trained. The recordings are tokenised once into YuE2's semantic token stream,
and the render continues from a few seconds of that stream -- so the material that follows comes out in that
voice. Four seconds did not register by ear; forty-eight did.

One folder per persona under the data directory:

    tokens.semantic.npy   the token stream, one code per 25th of a second
    source.*              the recording the persona came from, kept for reference

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

# Prefices measured by ear: 4 s did not carry the voice, 48 s did (VOICE-PERSONA.md 7.8, 7.9).
DEFAULT_PREFIX_SECONDS = 48.0
MIN_PREFIX_SECONDS = 4.0
MAX_PREFIX_SECONDS = 120.0


def folder(persona_id: str) -> Path:
    """Where a persona's files live.  Created on demand."""
    path = config.DATA_DIR / "personas" / persona_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def tokens_file(persona_id: str) -> Path:
    return folder(persona_id) / "tokens.semantic.npy"


def _shape(row) -> dict:
    out = dict(row)
    out["prefix_seconds"] = float(out.get("prefix_seconds") or DEFAULT_PREFIX_SECONDS)
    return out


def all() -> list[dict]:
    return [_shape(row) for row in db.rows("SELECT * FROM voices ORDER BY created_at, name")]


def one(persona_id: str) -> dict | None:
    found = db.rows("SELECT * FROM voices WHERE id = ?", (persona_id,))
    return _shape(found[0]) if found else None


def clamp_seconds(seconds) -> float:
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        return DEFAULT_PREFIX_SECONDS
    return max(MIN_PREFIX_SECONDS, min(MAX_PREFIX_SECONDS, value))


def create(name: str, source: Path | None = None, prefix_seconds: float = DEFAULT_PREFIX_SECONDS,
           head: str = "", origin_identity: str | None = None) -> dict:
    """A persona with a name and a source recording; its token file arrives when tokenising finishes.

    ``origin_identity`` names the corpus a persona was collaged from, so regenerating it can rebuild that
    collage from the corpus as it is now rather than keep a stale copy.
    """
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
    db.execute("INSERT INTO voices (id, name, tokens_path, source_path, origin_identity, prefix_seconds, head, state, created_at) "
               "VALUES (?, ?, NULL, ?, ?, ?, ?, 'preparing', ?)",
               (persona_id, name, source_path, origin_identity, clamp_seconds(prefix_seconds), head or "", time.time()))
    log.info("persona %s created from %s", name, source_path or "(no recording)")
    return one(persona_id)


def ready(persona_id: str, tokens_path: str, head: str = "") -> None:
    db.execute("UPDATE voices SET tokens_path = ?, head = ?, state = 'ready', error = NULL WHERE id = ?",
               (tokens_path, head, persona_id))


def failed(persona_id: str, error: str) -> None:
    db.execute("UPDATE voices SET state = 'failed', error = ? WHERE id = ?", (error[:500], persona_id))


def update(persona_id: str, **fields) -> dict | None:
    allowed = {"name", "prefix_seconds"}
    wanted = {k: v for k, v in fields.items() if k in allowed}
    if "prefix_seconds" in wanted:
        wanted["prefix_seconds"] = clamp_seconds(wanted["prefix_seconds"])
    if wanted:
        sets = ", ".join(f"{key} = ?" for key in wanted)
        db.execute(f"UPDATE voices SET {sets} WHERE id = ?", (*wanted.values(), persona_id))
    return one(persona_id)


def delete(persona_id: str) -> None:
    db.execute("UPDATE takes SET voice_id = NULL WHERE voice_id = ?", (persona_id,))
    db.execute("DELETE FROM voices WHERE id = ?", (persona_id,))
    shutil.rmtree(folder(persona_id), ignore_errors=True)


def describe(persona: dict | None) -> str:
    """A short line for logs and the take list."""
    if not persona:
        return ""
    return f"{persona['name']} · {persona['prefix_seconds']:.0f} s"
