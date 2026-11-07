"""The persona store: a fresh database, a persona created, found, updated and deleted."""
import pathlib
import tempfile

from app import db, persona


def test_a_persona_lives_in_the_store():
    created = persona.create("My voice", prefix_seconds=48)
    assert created["state"] == "preparing"
    assert created["prefix_seconds"] == 48.0
    found = persona.one(created["id"])
    assert found and found["name"] == "My voice"
    assert any(p["id"] == created["id"] for p in persona.all())
    persona.ready(created["id"], "/tmp/tokens.semantic.npy", head="v9")
    ready = persona.one(created["id"])
    assert ready["state"] == "ready" and ready["head"] == "v9"
    changed = persona.update(created["id"], name="Renamed", prefix_seconds=999)
    assert changed["name"] == "Renamed" and changed["prefix_seconds"] == persona.MAX_PREFIX_SECONDS
    assert persona.folder(created["id"]).is_dir()
    removed = persona.folder(created["id"])          # the path, before delete removes it
    persona.delete(created["id"])
    assert persona.one(created["id"]) is None
    assert not removed.exists()


def test_the_migration_makes_the_table():
    names = {row["name"] for row in db.rows("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert "voices" in names
    import sqlite3
    from app import config
    con = sqlite3.connect(config.DB_PATH)
    version = con.execute("PRAGMA user_version").fetchone()[0]
    con.close()
    assert version >= 44
