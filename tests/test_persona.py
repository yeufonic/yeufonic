"""The voice store: a voice created, trained, found, moved an octave and deleted; the migration's columns."""
import sqlite3

from app import config, db, persona


def test_a_voice_lives_in_the_store():
    created = persona.create("My voice", octave=1)
    assert created["state"] == "training" and created["octave"] == 1 and created["progress"] == 0.0
    assert any(v["id"] == created["id"] for v in persona.all())
    persona.training(created["id"], 0.4)
    assert persona.one(created["id"])["progress"] == 0.4
    assert not persona.usable(persona.one(created["id"]))
    model = persona.model_file(created["id"])
    model.write_bytes(b"weights")
    persona.ready(created["id"], str(model))
    assert persona.usable(persona.one(created["id"]))
    changed = persona.update(created["id"], name="Renamed", octave=5)
    assert changed["name"] == "Renamed" and changed["octave"] == persona.MAX_OCTAVE
    removed = persona.folder(created["id"])
    persona.delete(created["id"])
    assert persona.one(created["id"]) is None and not removed.exists()


def test_the_migration_gives_voices_a_model_and_an_octave():
    columns = {row["name"] for row in db.rows("PRAGMA table_info(voices)")}
    assert {"model_path", "octave", "progress"} <= columns
    con = sqlite3.connect(config.DB_PATH)
    version = con.execute("PRAGMA user_version").fetchone()[0]
    con.close()
    assert version >= 45


def test_a_voice_keeps_a_vocal_level_from_the_steps_offered():
    made = persona.create("Level")
    assert made["level_db"] == 0.0
    assert persona.update(made["id"], level_db=4)["level_db"] == 3.0      # the nearest step
    assert persona.update(made["id"], level_db=99)["level_db"] == 6.0
    persona.delete(made["id"])
