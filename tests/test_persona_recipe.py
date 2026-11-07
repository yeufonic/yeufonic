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
