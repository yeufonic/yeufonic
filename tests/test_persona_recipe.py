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
