"""Tokenising a persona: the engine is stubbed, and what matters is the graph it is asked to run and where the
stream ends up -- fetched back into the voice's own folder, so nothing but HTTP is shared with the engine."""
import asyncio
import pathlib

import pytest

from app import config, jobs, persona


class FakeEngine:
    """Records what it was asked, writes the stream beside the upload as the node does, and serves it back."""

    def __init__(self, inbox: pathlib.Path):
        self.inbox = inbox
        self.uploaded = None
        self.graph = None
        self.state = "success"
        self.queue = []            # what prompt_state answers on successive polls; then "running"
        self.history_calls = 0

    async def upload(self, filename, data):
        self.uploaded = (filename, len(data))
        (self.inbox / filename).write_bytes(data)
        return {"name": filename}

    async def submit(self, graph):
        self.graph = graph
        return "prompt-1"

    async def prompt_state(self, prompt_id):
        return self.queue.pop(0) if self.queue else "running"

    async def history(self, prompt_id):
        self.history_calls += 1
        if self.queue:
            return None
        if self.state == "success":
            audio = self.graph["1"]["inputs"]["audio"]
            (self.inbox / audio).with_suffix(".semantic.npy").write_bytes(b"tokens")
        return {"status": {"status_str": self.state}}

    async def download(self, item, dest):
        assert item["type"] == "input"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((self.inbox / item["filename"]).read_bytes())
        return dest

    async def cancel(self, prompt_id):
        pass


def _voice(name, tag):
    source = pathlib.Path(persona.folder(tag) / "source.wav")
    source.write_bytes(b"RIFF....")
    return persona.create(name, source=source)


def test_the_stream_comes_back_into_the_voices_own_folder(tmp_path, monkeypatch):
    inbox = tmp_path / "engine-input"
    inbox.mkdir()
    made = _voice("Tokenised", "ringtest")
    fake = FakeEngine(inbox)
    monkeypatch.setattr(jobs, "ENGINE", fake)
    monkeypatch.setattr(jobs, "PERSONA_POLL_SECONDS", 0.0)
    monkeypatch.setattr(config, "ENGINE_INPUT_DIR", inbox)
    result = asyncio.run(jobs.tokenise_persona(made["id"]))

    target = persona.tokens_file(made["id"])
    assert result["tokens_path"] == str(target)
    assert target.read_bytes() == b"tokens"
    assert target.parent == config.DATA_DIR / "voices" / made["id"]
    node = fake.graph["1"]
    assert node["class_type"] == "Yue2PersonaTokens"
    assert node["inputs"]["out"] == ""                 # beside the upload, in the engine's own input folder
    assert node["inputs"]["head"] == config.TOKENIZER_HEAD
    assert node["inputs"]["audio"].startswith("persona-")
    assert list(inbox.iterdir()) == []                 # the engine's copies are tidied when the app can reach them
    ready = persona.one(made["id"])
    assert ready["state"] == "ready" and ready["tokens_path"] == str(target)
    persona.delete(made["id"])


def test_waiting_in_the_engines_queue_does_not_count_against_the_timeout(tmp_path, monkeypatch):
    inbox = tmp_path / "engine-input"
    inbox.mkdir()
    made = _voice("Behind a training run", "queuetest")
    fake = FakeEngine(inbox)
    fake.queue = ["pending"] * 50
    clock = iter(range(0, 10_000, 100))                           # every poll seems to take 100 s
    monkeypatch.setattr(jobs, "PERSONA_CLOCK", lambda: next(clock))
    monkeypatch.setattr(jobs, "ENGINE", fake)
    monkeypatch.setattr(jobs, "PERSONA_POLL_SECONDS", 0.0)
    monkeypatch.setattr(jobs, "PERSONA_TIMEOUT_SECONDS", 0.0)   # any running time at all would time it out
    asyncio.run(jobs.tokenise_persona(made["id"]))
    assert fake.history_calls > 5
    assert persona.one(made["id"])["state"] == "ready"
    persona.delete(made["id"])


def test_a_failing_engine_leaves_the_persona_failed(tmp_path, monkeypatch):
    inbox = tmp_path / "engine-input"
    inbox.mkdir()
    made = _voice("Doomed", "failtest")
    fake = FakeEngine(inbox)
    fake.state = "error"
    monkeypatch.setattr(jobs, "ENGINE", fake)
    monkeypatch.setattr(jobs, "PERSONA_POLL_SECONDS", 0.0)
    with pytest.raises(RuntimeError):
        asyncio.run(jobs.tokenise_persona(made["id"]))
    assert persona.one(made["id"])["state"] == "failed"
    persona.delete(made["id"])


def test_the_cpp_engine_says_it_cannot_tokenise(tmp_path, monkeypatch):
    made = _voice("Wrong engine", "cpptest")
    monkeypatch.setattr(config, "ENGINE_KIND", "yue2cpp")
    with pytest.raises(RuntimeError):
        asyncio.run(jobs.tokenise_persona(made["id"]))
    failed = persona.one(made["id"])
    assert failed["state"] == "failed" and "ComfyUI" in (failed["error"] or "")
    persona.delete(made["id"])
