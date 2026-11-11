"""Hearing a voice on a loop before a take is made with it, and keeping what was heard as a voice of its own, against
a stand-in voice service: what is asked of it, what the page gets back, and when it is refused."""
import asyncio
import json

import httpx
import pytest

from app import config, jobs, main, persona


@pytest.fixture(autouse=True)
def idle_gpu(monkeypatch):
    """No GPU work under way, whatever an earlier test left in jobs.CURRENT: an audition is refused while there is."""
    monkeypatch.setattr(jobs, "CURRENT", {})


def _ready(name="A voice", **settings):
    made = persona.create(name, state="new")
    persona.model_file(made["id"]).write_bytes(b"PK weights")
    (persona.folder(made["id"]) / "model.index").write_bytes(b"IwFl index")
    persona.ready(made["id"], str(persona.model_file(made["id"])))
    return persona.update(made["id"], **settings) if settings else persona.one(made["id"])


def _service(monkeypatch, handler):
    real = httpx.AsyncClient
    for module in (main, jobs):
        monkeypatch.setattr(module.httpx, "AsyncClient",
                            lambda **kw: real(transport=httpx.MockTransport(handler), base_url="http://voice"))
    monkeypatch.setattr(config, "VOICE_URL", "http://voice")


def test_the_loops_are_listed_and_served(client):
    loops = client.get("/api/voices/loops").json()
    assert [loop["id"] for loop in loops] == ["male", "female"]
    got = client.get(loops[0]["url"])
    assert got.status_code == 200 and got.content[:4] == b"fLaC"
    assert client.get("/api/voices/loops/nobody.flac").status_code == 404


def test_an_audition_asks_the_service_and_returns_what_it_sang(client, monkeypatch):
    voice = _ready()
    asked = {}

    def handler(request):
        asked.update(json.loads(request.content))
        with open(asked["output"], "wb") as out:      # where the service writes it
            out.write(b"RIFF sung")
        return httpx.Response(200, json={"ok": True, "seconds": 0.4})

    _service(monkeypatch, handler)
    got = client.post(f"/api/voices/{voice['id']}/audition",
                      json={"loop": "female", "octave": 3, "likeness": 0.6, "formant": 0.9, "brightness": 0})
    assert got.status_code == 200 and got.content == b"RIFF sung" and got.headers["content-type"] == "audio/wav"
    # Each setting in the voice's own steps; the loop where the service can read it.
    assert (asked["octave"], asked["likeness"], asked["formant"], asked["brightness"]) == (1, 0.5, 0.88, 0)
    assert asked["loop"] == str(config.DATA_DIR / "voice-loops" / ".app" / "female.flac")
    assert (config.DATA_DIR / "voice-loops" / ".app" / "female.flac").read_bytes()[:4] == b"fLaC"
    assert not list(config.WORK_DIR.glob("audition-*")), "the sung loop is not kept once sent"
    assert jobs.AUDITION_HELD["at"] > 0
    persona.delete(voice["id"])


def test_an_audition_is_refused_while_the_gpu_works_or_without_a_service(client, monkeypatch):
    voice = _ready()
    monkeypatch.setattr(config, "VOICE_URL", "")
    assert client.post(f"/api/voices/{voice['id']}/audition", json={}).status_code == 503
    _service(monkeypatch, lambda request: httpx.Response(404, json={"error": "not found"}))
    old = client.post(f"/api/voices/{voice['id']}/audition", json={})
    assert old.status_code == 503 and "older" in old.json()["detail"]
    assert client.post(f"/api/voices/{voice['id']}/audition", json={"loop": "choir"}).status_code == 400
    monkeypatch.setitem(jobs.CURRENT, "kind", "render")
    assert client.post(f"/api/voices/{voice['id']}/audition", json={}).status_code == 409
    untrained = persona.create("Untrained", state="new")
    assert client.post(f"/api/voices/{untrained['id']}/audition", json={}).status_code == 400
    persona.delete(voice["id"])
    persona.delete(untrained["id"])


def test_gpu_work_lets_go_of_an_audition_first(monkeypatch):
    freed = []
    _service(monkeypatch, lambda request: (freed.append(request.url.path), httpx.Response(200, json={"ok": True}))[1])
    monkeypatch.setitem(jobs.AUDITION_HELD, "at", 0.0)
    asyncio.run(jobs.release_audition())
    assert freed == [], "nothing is asked of the service when no audition ran"
    monkeypatch.setitem(jobs.AUDITION_HELD, "at", 123.0)
    asyncio.run(jobs.release_audition())
    assert freed == ["/audition/free"] and jobs.AUDITION_HELD["at"] == 0.0


def test_what_was_heard_is_kept_as_a_voice_of_its_own(client):
    source = _ready("Original", likeness=0.5)
    made = client.post(f"/api/voices/{source['id']}/copy",
                       json={"name": "Original, deeper", "settings": {"formant": 0.88, "wet": 0.75, "octave": -1}}).json()
    assert made["name"] == "Original, deeper" and made["state"] == "ready" and persona.usable(made)
    assert (made["formant"], made["wet"], made["octave"], made["likeness"]) == (0.88, 0.75, -1, 0.5)
    assert persona.model_file(made["id"]).read_bytes() == b"PK weights" and made["has_index"]
    persona.delete(source["id"])
    assert persona.usable(persona.one(made["id"])), "the copy outlives the voice it came from"
    unnamed = client.post(f"/api/voices/{made['id']}/copy", json={}).json()
    assert unnamed["name"] == "Original, deeper (copy)"
    persona.delete(made["id"])
    persona.delete(unnamed["id"])
    assert client.post("/api/voices/nobody/copy", json={}).status_code == 400


def test_formant_and_blend_are_a_voices_settings_and_a_takes():
    voice = _ready(formant=1.1, wet=0.3)
    assert (voice["formant"], voice["wet"]) == (1.12, 0.25)
    assert json.loads(main._voice_mix({"formant": 0.95, "wet": 0.6})) == {"formant": 0.94, "wet": 0.5}
    assert "formant 1.12" in persona.describe(voice) and "25% wet" in persona.describe(voice)
    assert "formant" not in persona.describe(persona.update(voice["id"], formant=1, wet=1))
    persona.delete(voice["id"])


def test_your_own_loops_come_from_the_librarys_folder(client, monkeypatch):
    folder = config.DATA_DIR / "voice-loops"
    (folder / ".app").mkdir(parents=True)
    (folder / "My Phrase.wav").write_bytes(b"RIFF mine")
    (folder / "notes.txt").write_text("not a loop")
    (folder / ".app" / "male.flac").write_bytes(b"fLaC the app's copy")
    loops = client.get("/api/voices/loops").json()
    assert [loop["id"] for loop in loops] == ["male", "female", "own:My Phrase.wav"]
    mine = loops[-1]
    assert mine["name"] == "My Phrase" and mine["own"] and client.get(mine["url"]).content == b"RIFF mine"
    assert client.get("/api/voices/loops/own/notes.txt").status_code == 404
    assert client.get("/api/voices/loops/own/..%2Fyue2.sqlite").status_code == 404

    voice = _ready()
    asked = {}

    def handler(request):
        asked.update(json.loads(request.content))
        with open(asked["output"], "wb") as out:
            out.write(b"RIFF sung")
        return httpx.Response(200, json={"ok": True})

    _service(monkeypatch, handler)
    assert client.post(f"/api/voices/{voice['id']}/audition", json={"loop": "own:My Phrase.wav"}).status_code == 200
    assert asked["loop"] == str(folder / "My Phrase.wav")
    assert client.post(f"/api/voices/{voice['id']}/audition", json={"loop": "own:notes.txt"}).status_code == 400
    assert client.post(f"/api/voices/{voice['id']}/audition", json={"loop": "own:../yue2.sqlite"}).status_code == 400
    client.post(f"/api/voices/{voice['id']}/audition", json={"loop": "female"})
    assert asked["loop"] == str(folder / ".app" / "female.flac"), "the shipped loops are copied out of the list's way"
    persona.delete(voice["id"])
