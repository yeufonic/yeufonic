"""The render graph: a take with a persona renders through the persona node, and one without does not."""
import pathlib

from app import jobs, persona


def _take(**extra):
    base = {"id": "t1", "style": "rock", "lyrics": "la la", "abc": "X:1\nK:C\nCDEF|", "seed": 7,
            "mode": "full", "kind": "song", "sound_seed": None, "sampler_steps": 32,
            "interpretation": "standard", "target_key": None, "target_bpm": None, "avoid": None}
    base.update(extra)
    return base


def test_a_take_without_a_persona_uses_the_music_node():
    graph = jobs.build_render_graph(_take())
    assert graph["11"]["class_type"] == "YuE2GenerateMusic"
    assert "persona_tokens" not in graph["11"]["inputs"]


def test_a_ready_persona_replaces_the_music_node(tmp_path):
    source = pathlib.Path(persona.folder("rendertest") / "source.wav")
    source.write_bytes(b"RIFF....")
    made = persona.create("In the render", source=source, prefix_seconds=36)
    persona.tokens_file(made["id"]).write_bytes(b"tokens")
    persona.ready(made["id"], str(persona.tokens_file(made["id"])))
    graph = jobs.build_render_graph(_take(voice_id=made["id"]))
    node = graph["11"]
    assert node["class_type"] == "Yue2PersonaGenerate"
    # By its name in the engine's input folder, where the render job uploads it: no path the engine must share.
    assert node["inputs"]["persona_tokens"] == persona.engine_name(made["id"])
    assert node["inputs"]["persona_seconds"] == 36.0
    assert node["inputs"]["style"] == "rock" and node["inputs"]["seed"] == 7
    persona.delete(made["id"])


def test_a_persona_still_preparing_is_not_used(tmp_path):
    source = pathlib.Path(persona.folder("preptest") / "source.wav")
    source.write_bytes(b"RIFF....")
    made = persona.create("Not ready", source=source)
    graph = jobs.build_render_graph(_take(voice_id=made["id"]))
    assert graph["11"]["class_type"] == "YuE2GenerateMusic"
    persona.delete(made["id"])


class Uploads:
    def __init__(self):
        self.sent = {}

    async def upload(self, filename, data):
        self.sent[filename] = data
        return {"name": filename}


def test_the_render_job_uploads_the_tokens_the_graph_names(monkeypatch):
    import asyncio
    source = pathlib.Path(persona.folder("uploadtest") / "source.wav")
    source.write_bytes(b"RIFF....")
    made = persona.create("Sent along", source=source)
    persona.tokens_file(made["id"]).write_bytes(b"the stream")
    persona.ready(made["id"], str(persona.tokens_file(made["id"])))
    engine = Uploads()
    monkeypatch.setattr(jobs, "ENGINE", engine)
    asyncio.run(jobs.voice_for_render(_take(voice_id=made["id"])))
    assert engine.sent == {persona.engine_name(made["id"]): b"the stream"}
    persona.delete(made["id"])


def test_the_cpp_engine_renders_without_the_voice(monkeypatch):
    from app import config
    source = pathlib.Path(persona.folder("cpptest") / "source.wav")
    source.write_bytes(b"RIFF....")
    made = persona.create("Not here", source=source)
    persona.tokens_file(made["id"]).write_bytes(b"tokens")
    persona.ready(made["id"], str(persona.tokens_file(made["id"])))
    monkeypatch.setattr(config, "ENGINE_KIND", "yue2cpp")
    graph = jobs.build_render_graph(_take(voice_id=made["id"]))
    assert graph["11"]["class_type"] == "YuE2GenerateMusic"
    persona.delete(made["id"])
