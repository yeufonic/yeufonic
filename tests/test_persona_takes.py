"""A recorded voice chosen in the editor reaches every way a take is rendered, and variations keep it."""
import pathlib

from app import persona
from app.db import one
from conftest import make_take
from tests.test_recipe import ABC


def _voice(tag):
    source = pathlib.Path(persona.folder(tag) / "source.wav")
    source.write_bytes(b"RIFF....")
    return persona.create("Editor voice", source=source)


def test_rendering_a_planned_take_takes_the_editors_voice_and_none_clears_it(client):
    voice = _voice("rendervoice")
    take = make_take(abc=ABC, status="planned")
    assert client.post(f"/api/takes/{take['id']}/render", json={"voice_id": voice["id"]}).status_code == 200
    assert one("SELECT voice_id FROM takes WHERE id = ?", (take["id"],))["voice_id"] == voice["id"]
    client.post(f"/api/takes/{take['id']}/cancel")
    from app.db import execute
    execute("UPDATE takes SET status = 'planned' WHERE id = ?", (take["id"],))
    assert client.post(f"/api/takes/{take['id']}/render", json={"voice_id": ""}).status_code == 200
    assert one("SELECT voice_id FROM takes WHERE id = ?", (take["id"],))["voice_id"] is None
    persona.delete(voice["id"])


def test_new_words_take_the_editors_voice(client):
    voice = _voice("wordsvoice")
    take = make_take(abc=ABC)
    made = client.post(f"/api/takes/{take['id']}/words",
                       json={"lyrics": "[Verse]\nother words here", "voice_id": voice["id"]}).json()
    assert one("SELECT voice_id FROM takes WHERE id = ?", (made["id"],))["voice_id"] == voice["id"]
    persona.delete(voice["id"])


def test_variations_keep_the_takes_voice(client):
    voice = _voice("variationvoice")
    take = make_take(abc=ABC, voice_id=voice["id"])
    made = client.post(f"/api/takes/{take['id']}/variations", json={"interpretations": ["loose"]}).json()["created"]
    assert one("SELECT voice_id FROM takes WHERE id = ?", (made[0]["id"],))["voice_id"] == voice["id"]
    persona.delete(voice["id"])


def test_an_instrumental_from_a_prompt_keeps_the_voice_it_was_given(client, monkeypatch):
    from app import jobs
    monkeypatch.setitem(jobs.ENGINE.options, "instrumental", True)
    voice = _voice("instvoice")
    made = client.post("/api/instrumentals", json={"style": "ambient", "structure": "[Intro] [Verse]",
                                                   "voice_id": voice["id"]})
    assert made.status_code == 200, made.text
    assert one("SELECT voice_id FROM takes WHERE id = ?", (made.json()["id"],))["voice_id"] == voice["id"]
    persona.delete(voice["id"])
