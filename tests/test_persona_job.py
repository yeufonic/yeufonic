"""Tokenising a persona: the engine is stubbed, and what matters is the graph it is asked to run."""
import asyncio
import pathlib

import pytest

from app import config, db, jobs, persona


class FakeEngine:
    """Records what it was asked, and leaves the token file where the engine would."""

    def __init__(self, target: pathlib.Path):
        self.target = target
        self.uploaded = None
        self.graph = None
        self.state = "success"

    async def upload(self, filename, data):
        self.uploaded = (filename, len(data))
        return {"name": filename}

    async def submit(self, graph):
        self.graph = graph
        return "prompt-1"

    async def history(self, prompt_id):
        if self.state == "success":
            self.target.parent.mkdir(parents=True, exist_ok=True)
            self.target.write_bytes(b"tokens")
        return {"status": {"status_str": self.state}}


def test_tokenising_writes_the_stream_where_the_app_reads_it(tmp_path, monkeypatch):
    source = pathlib.Path(persona.folder("ringtest") / "source.wav")
    source.write_bytes(b"RIFF....")
    made = persona.create("Tokenised", source=source)
    target = pathlib.Path("/data/personas") / made["id"] / "tokens.semantic.npy"
    fake = FakeEngine(target)
    monkeypatch.setattr(jobs, "ENGINE", fake)
    monkeypatch.setattr(jobs, "PERSONA_POLL_SECONDS", 0.0)
    result = asyncio.run(jobs.tokenise_persona(made["id"]))

    assert result["tokens_path"] == str(target)
    node = fake.graph["1"]
    assert node["class_type"] == "Yue2PersonaTokens"
    assert node["inputs"]["out"] == str(target)
    assert node["inputs"]["head"] == config.TOKENIZER_HEAD
    assert node["inputs"]["audio"].startswith("persona-")
    ready = persona.one(made["id"])
    assert ready["state"] == "ready" and ready["tokens_path"] == str(target)
    persona.delete(made["id"])


def test_a_failing_engine_leaves_the_persona_failed(tmp_path, monkeypatch):
    source = pathlib.Path(persona.folder("failtest") / "source.wav")
    source.write_bytes(b"RIFF....")
    made = persona.create("Doomed", source=source)
    fake = FakeEngine(pathlib.Path("/data/personas") / made["id"] / "tokens.semantic.npy")
    fake.state = "error"
    monkeypatch.setattr(jobs, "ENGINE", fake)
    monkeypatch.setattr(jobs, "PERSONA_POLL_SECONDS", 0.0)
    with pytest.raises(RuntimeError):
        asyncio.run(jobs.tokenise_persona(made["id"]))
    assert persona.one(made["id"])["state"] == "failed"
    persona.delete(made["id"])
