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
    persona.ready(made["id"], "/data/personas/x/tokens.semantic.npy")
    graph = jobs.build_render_graph(_take(voice_id=made["id"]))
    node = graph["11"]
    assert node["class_type"] == "Yue2PersonaGenerate"
    assert node["inputs"]["persona_tokens"] == "/data/personas/x/tokens.semantic.npy"
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
