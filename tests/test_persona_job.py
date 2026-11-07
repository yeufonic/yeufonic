"""Training a voice and singing a take in it, against a stand-in voice service: what is asked, and what is kept."""
import asyncio
import json
import pathlib

import httpx

from app import config, jobs, persona


class FakeEngine:
    freed = 0

    async def free(self):
        FakeEngine.freed += 1


def _service(monkeypatch, handler):
    """Every httpx client jobs.py makes talks to `handler` instead of a network."""
    real = httpx.AsyncClient
    monkeypatch.setattr(jobs.httpx, "AsyncClient",
                        lambda **kw: real(transport=httpx.MockTransport(handler), base_url="http://voice"))
    monkeypatch.setattr(config, "VOICE_URL", "http://voice")
    monkeypatch.setattr(jobs, "ENGINE", FakeEngine())
    monkeypatch.setattr(jobs, "VOICE_POLL_SECONDS", 0.0)


def _voice(tag, **extra):
    source = pathlib.Path(persona.folder(tag) / "source.wav")
    source.write_bytes(b"RIFF....")
    return persona.create("A voice", source=source, **extra)


def test_training_frees_the_engine_and_marks_the_voice_ready(monkeypatch):
    made = _voice("trainok")
    asked = {}

    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"ok": True, "models": {}})
        if request.url.path == "/train":
            asked.update(json.loads(request.content))
            persona.model_file(made["id"]).write_bytes(b"weights")   # where the service writes it
            return httpx.Response(200, json={"job": "j1"})
        return httpx.Response(200, json={"state": "done", "progress": 1.0})

    _service(monkeypatch, handler)
    asyncio.run(jobs.run_voice_train(made["id"]))
    ready = persona.one(made["id"])
    assert ready["state"] == "ready" and persona.usable(ready)
    assert asked["id"] == made["id"] and asked["sources"] == [made["source_path"]] and asked["separate"] is True
    assert FakeEngine.freed >= 1
    persona.delete(made["id"])


def test_a_failed_training_says_why(monkeypatch):
    made = _voice("trainbad")

    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"ok": True, "models": {}})
        if request.url.path == "/train":
            return httpx.Response(200, json={"job": "j2"})
        return httpx.Response(200, json={"state": "failed", "error": "no singing was found"})

    _service(monkeypatch, handler)
    asyncio.run(jobs.run_voice_train(made["id"]))
    failed = persona.one(made["id"])
    assert failed["state"] == "failed" and "no singing" in failed["error"]
    persona.delete(made["id"])


def test_without_the_service_training_fails_at_once(monkeypatch):
    made = _voice("noservice")
    monkeypatch.setattr(config, "VOICE_URL", "")
    asyncio.run(jobs.run_voice_train(made["id"]))
    assert persona.one(made["id"])["state"] == "failed"
    persona.delete(made["id"])


def test_a_take_is_sung_in_its_voice_in_place(monkeypatch, tmp_path):
    made = _voice("singok", octave=1)
    persona.model_file(made["id"]).write_bytes(b"weights")
    persona.ready(made["id"], str(persona.model_file(made["id"])))
    take = tmp_path / "take.flac"
    take.write_bytes(b"as rendered")
    asked = {}

    def handler(request):
        asked.update(json.loads(request.content))
        pathlib.Path(asked["output"]).write_bytes(b"sung in the voice")
        return httpx.Response(200, json={"ok": True})

    _service(monkeypatch, handler)
    from app.db import execute
    execute("INSERT INTO takes (id, kind, title, style, lyrics, abc, mode, seed, checkpoint, max_duration, status, created_at) "
            "VALUES ('tv1', 'song', 't', 's', 'l', '', 'full', 1, 'c', 60, 'running', 0)")
    asyncio.run(jobs._sing_in_voice("tv1", {"voice_id": made["id"], "title": "t"}, take))
    assert take.read_bytes() == b"sung in the voice"
    assert asked["id"] == made["id"] and asked["input"] == str(take) and asked["octave"] == 1
    persona.delete(made["id"])


def test_a_failed_conversion_keeps_the_take_as_rendered(monkeypatch, tmp_path):
    made = _voice("singbad")
    persona.model_file(made["id"]).write_bytes(b"weights")
    persona.ready(made["id"], str(persona.model_file(made["id"])))
    take = tmp_path / "take.flac"
    take.write_bytes(b"as rendered")
    _service(monkeypatch, lambda request: httpx.Response(500, json={"error": "out of memory"}))
    from app.db import execute
    execute("INSERT INTO takes (id, kind, title, style, lyrics, abc, mode, seed, checkpoint, max_duration, status, created_at) "
            "VALUES ('tv2', 'song', 't', 's', 'l', '', 'full', 1, 'c', 60, 'running', 0)")
    asyncio.run(jobs._sing_in_voice("tv2", {"voice_id": made["id"], "title": "t"}, take))
    assert take.read_bytes() == b"as rendered"
    assert not list(tmp_path.glob("*.voice.*"))
    persona.delete(made["id"])
