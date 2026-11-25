"""A recorded voice travels in a take recipe by name, and is left out when there is none."""
from app import recipe


def _take(**extra):
    base = {"title": "A song", "kind": "song", "style": "rock", "lyrics": "la", "abc": "", "seed": 1,
            "mode": "full", "voice_lora": None, "style_lora": None}
    base.update(extra)
    return base


def test_a_voice_is_in_the_recipe_by_name():
    data = recipe.export(_take(), "0.0.54", voice="My voice")
    assert data["take"]["voice"] == "My voice"
    assert "voice_id" not in data["take"]


def test_no_voice_leaves_the_field_out():
    data = recipe.export(_take(), "0.0.54")
    assert "voice" not in data["take"]


def test_a_recipe_with_a_voice_reads_back_without_an_id():
    data = recipe.export(_take(), "0.0.54", voice="My voice")
    columns = recipe.read(data)
    assert "voice_id" not in columns          # resolved against this install, not carried as an id
    assert data["take"]["voice"] == "My voice"


def test_an_import_picks_up_the_voice_of_that_name_or_says_there_is_none(client):
    import pathlib

    from app import persona
    from app.db import one
    from tests.test_recipe import full_take

    source = pathlib.Path(persona.folder("importtest") / "source.wav")
    source.write_bytes(b"RIFF....")
    voice = persona.create("My voice", source=source)
    take = full_take()
    data = client.get(f"/api/takes/{take['id']}/recipe").json()
    data["take"]["voice"] = "My voice"
    got = client.post("/api/takes/import", json={"recipe": data}).json()
    assert got["missing_voice"] is None
    assert one("SELECT voice_id FROM takes WHERE id = ?", (got["id"],))["voice_id"] == voice["id"]

    data["take"]["voice"] = "Somebody else"
    got = client.post("/api/takes/import", json={"recipe": data}).json()
    assert got["missing_voice"] == "Somebody else"
    assert one("SELECT voice_id FROM takes WHERE id = ?", (got["id"],))["voice_id"] is None
    persona.delete(voice["id"])


def test_voice_cleanup_thresholds_roundtrip_in_take_recipe_json(client):
    import json
    import pathlib

    from app import persona
    from app.db import execute, one
    from tests.test_recipe import full_take

    source = pathlib.Path(persona.folder("cleanuptest") / "source.wav")
    source.write_bytes(b"RIFF....")
    voice = persona.create("Cleanup voice", source=source)
    take = full_take()
    saved_mix = {
        "octave": 0, "level_db": 3.0, "backing_db": 0.0, "likeness": 0.75, "room": 0.14,
        "brightness": 1, "protect": 0.33, "dynamics": 0.25, "formant": 1.0, "wet": 1.0,
        "tail_gate": "firm", "rmvpe_thred": 0.14, "f0_floor": 115,
    }
    execute("UPDATE takes SET voice_id = ?, voice_mix = ? WHERE id = ?",
            (voice["id"], json.dumps(saved_mix), take["id"]))

    # Exported recipe JSON holds tail_gate, rmvpe_thred, and f0_floor under take.voice_settings
    exported = client.get(f"/api/takes/{take['id']}/recipe").json()
    assert exported["take"]["voice"] == "Cleanup voice"
    vs = exported["take"]["voice_settings"]
    assert vs["tail_gate"] == "firm"
    assert vs["rmvpe_thred"] == 0.14
    assert vs["f0_floor"] == 115

    # Importing that recipe restores those exact settings onto the imported take
    imported = client.post("/api/takes/import", json={"recipe": exported}).json()
    restored = json.loads(one("SELECT voice_mix FROM takes WHERE id = ?", (imported["id"],))["voice_mix"])
    assert restored["tail_gate"] == "firm"
    assert restored["rmvpe_thred"] == 0.14
    assert restored["f0_floor"] == 115
    persona.delete(voice["id"])
