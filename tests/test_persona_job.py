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


def test_stopping_a_training_run_stops_it_on_the_service(monkeypatch):
    made = _voice("trainstop")
    asked = []

    def handler(request):
        asked.append(request.url.path)
        if request.url.path == "/health":
            return httpx.Response(200, json={"ok": True, "models": {}})
        if request.url.path == "/train":
            jobs.CANCELLED.add(made["id"])        # the job card's Stop, pressed while it trains
            return httpx.Response(200, json={"job": "j3"})
        return httpx.Response(200, json={"state": "running", "progress": 0.3})

    _service(monkeypatch, handler)
    asyncio.run(jobs.run_voice_train(made["id"]))
    assert "/jobs/j3/stop" in asked
    assert persona.one(made["id"])["state"] == "failed"
    assert made["id"] not in jobs.CANCELLED and not jobs.CURRENT
    persona.delete(made["id"])


def test_a_half_cleared_job_does_not_break_the_page_poll(client, monkeypatch):
    monkeypatch.setattr(jobs, "CURRENT", jobs.CURRENT)
    jobs.CURRENT.clear()
    jobs.CURRENT.update({"progress": 0.5})       # what a stop left behind before
    try:
        assert client.get("/api/state").status_code == 200
    finally:
        jobs.CURRENT.clear()


def test_a_voice_training_shows_its_own_time_and_progress(client):
    import time as clock
    jobs.CURRENT.clear()
    jobs.CURRENT.update({"kind": "voice", "id": "vprog", "prompt_id": None, "started": clock.time() - 65,
                         "label": "Training a voice", "progress": 0.21})
    try:
        current = client.get("/api/state").json()["current"]
        assert current["progress"] == 0.21 and current["elapsed"] >= 64
    finally:
        jobs.CURRENT.clear()


def test_the_log_says_each_step_of_a_voice_training(caplog):
    said = {"stage": None, "quarter": 0}
    with caplog.at_level("INFO", logger="yue2.jobs"):
        for state in ({"stage": "separating", "progress": 0.02}, {"stage": "separating", "progress": 0.05},
                      {"stage": "training", "progress": 0.15, "clips": 139}, {"stage": "training", "progress": 0.4},
                      {"stage": "training", "progress": 0.56}, {"stage": "indexing", "progress": 0.97}):
            jobs._log_voice_step("Mine", state, said)
    lines = [r.getMessage() for r in caplog.records]
    assert lines == ["Recorded voice 'Mine': separating the vocals",
                     "Recorded voice 'Mine': training (139 clips of singing)",
                     "Recorded voice 'Mine': training 25% done",
                     "Recorded voice 'Mine': training 50% done",
                     "Recorded voice 'Mine': building its index"]
