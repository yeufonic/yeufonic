import sqlite3

from app import config, db


def test_fresh_database_is_at_the_latest_version():
    assert db.conn().execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
    names = {r["name"] for r in db.rows("SELECT name FROM sqlite_master WHERE type = 'index'")}
    assert {"takes_created", "takes_source", "stem_sets_take", "stem_sets_source"} <= names


def test_legacy_takes_table_is_rebuilt(tmp_path, monkeypatch):
    path = tmp_path / "old.sqlite"
    legacy = sqlite3.connect(path)
    legacy.executescript(
        """CREATE TABLE takes (id TEXT PRIMARY KEY, source_id TEXT NOT NULL, title TEXT NOT NULL,
               style TEXT NOT NULL, lyrics TEXT NOT NULL, abc TEXT, mode TEXT NOT NULL, seed INTEGER NOT NULL,
               checkpoint TEXT NOT NULL, max_duration REAL NOT NULL DEFAULT 360, status TEXT NOT NULL DEFAULT 'queued',
               stage TEXT, prompt_id TEXT, audio_path TEXT, duration REAL, error TEXT,
               favourite INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL, finished_at REAL, elapsed REAL);
           INSERT INTO takes (id, source_id, title, style, lyrics, mode, seed, checkpoint, created_at)
               VALUES ('t1', 's1', 'Old', 'rock', 'la', 'full', 7, 'ck', 1.0);"""
    )
    legacy.commit()
    legacy.close()
    monkeypatch.setattr(config, "DB_PATH", path)
    db.migrate()
    take = db.one("SELECT * FROM takes WHERE id = 't1'")
    assert take["kind"] == "cover" and take["variety"] == "normal" and take["seed"] == 7
    db.migrate()   # a second run changes nothing
    assert db.conn().execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)


def test_a_database_from_the_engine_trial_branch_catches_up(tmp_path, monkeypatch):
    """That branch took version 24 for its engine column.  A database that ran it is
    at 24 already, and still gains what main added after."""
    path = tmp_path / "branch.sqlite"
    monkeypatch.setattr(config, "DB_PATH", path)
    db.migrate()
    c = db.conn()
    c.execute("ALTER TABLE takes DROP COLUMN normalised_to")
    c.execute("PRAGMA user_version = 24")
    c.commit()
    db.migrate()
    columns = {r["name"] for r in db.rows("PRAGMA table_info(takes)")}
    assert {"engine", "normalised_to"} <= columns
    assert c.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)


def test_settings_cache_follows_writes():
    assert db.get_setting("x", "fallback") == "fallback"
    db.set_setting("x", "1")
    assert db.get_setting("x") == "1"


def _at_version_53(tmp_path, monkeypatch, settings=()):
    """A library from before the new look: the latest schema, its version set back to 53."""
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "before.sqlite")
    db.migrate()
    c = db.conn()
    c.execute("DELETE FROM settings")
    for key, value in settings:
        c.execute("INSERT INTO settings(key, value) VALUES(?, ?)", (key, value))
    c.execute("PRAGMA user_version = 53")
    c.commit()
    db.migrate()
    return {r["key"]: r["value"] for r in db.rows("SELECT key, value FROM settings WHERE key LIKE 'appearance.%'")}


def test_a_new_library_starts_with_the_new_look():
    assert db.one("SELECT 1 FROM settings WHERE key IN ('appearance.theme', 'appearance.ui_style')") is None


def test_a_library_from_before_keeps_its_look(tmp_path, monkeypatch):
    assert _at_version_53(tmp_path, monkeypatch) == {"appearance.theme": "dark", "appearance.ui_style": "default"}


def test_a_chosen_theme_is_never_changed(tmp_path, monkeypatch):
    kept = _at_version_53(tmp_path, monkeypatch, [("appearance.theme", "light"), ("appearance.ui_style", "slate")])
    assert kept == {"appearance.theme": "light", "appearance.ui_style": "slate"}
