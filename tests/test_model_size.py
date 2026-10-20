"""The two sizes of the YuE2 model: which one an install uses, and what needs the full one."""
from app import config, jobs
from app.main import ENGINE


def test_the_full_model_is_used_when_it_is_installed():
    both = [config.CHECKPOINT_INT8, config.CHECKPOINT_BF16]
    assert config.choose_checkpoint(both) == config.CHECKPOINT_BF16
    assert config.choose_checkpoint([config.CHECKPOINT_BF16]) == config.CHECKPOINT_BF16


def test_the_small_model_is_used_when_it_is_all_there_is():
    assert config.choose_checkpoint([config.CHECKPOINT_INT8]) == config.CHECKPOINT_INT8


def test_with_neither_the_usual_name_is_kept_so_the_message_names_it():
    assert config.choose_checkpoint([]) == config.CHECKPOINT_BF16
    assert config.choose_checkpoint(None) == config.CHECKPOINT_BF16


def test_the_environment_can_force_one(monkeypatch):
    both = [config.CHECKPOINT_BF16, config.CHECKPOINT_INT8]
    monkeypatch.setenv("YUE2_CHECKPOINT", "int8")
    assert config.choose_checkpoint(both) == config.CHECKPOINT_INT8
    monkeypatch.setenv("YUE2_CHECKPOINT", "BF16")
    assert config.choose_checkpoint(both) == config.CHECKPOINT_BF16
    monkeypatch.setenv("YUE2_CHECKPOINT", "my_own.safetensors")
    assert config.choose_checkpoint(both) == "my_own.safetensors"


def test_plans_and_renders_ask_for_the_model_in_use(monkeypatch):
    monkeypatch.setattr(config, "CHECKPOINT", config.CHECKPOINT_INT8)
    take = {"id": "t1", "title": "T", "style": "folk", "lyrics": "[Verse]\nla", "seed": 1, "abc": "", "mode": "full", "max_duration": 60,
            "interpretation": "standard", "variety": "normal", "harmony": 0, "sound_seed": None}
    assert jobs.build_plan_graph(take)["1"]["inputs"]["ckpt_name"] == config.CHECKPOINT_INT8
    assert jobs.build_render_graph(take)["10"]["inputs"]["ckpt_name"] == config.CHECKPOINT_INT8


def test_the_state_says_which_model_is_in_use(client, monkeypatch):
    monkeypatch.setattr(config, "CHECKPOINT", config.CHECKPOINT_INT8)
    assert client.get("/api/state").json()["model"] == "Low memory (INT8)"
    monkeypatch.setattr(config, "CHECKPOINT", config.CHECKPOINT_BF16)
    assert client.get("/api/state").json()["model"] == "Full quality (BF16)"


def test_training_needs_the_full_model(client, monkeypatch, tmp_path):
    from test_lora_training import a_corpus
    a_corpus()
    monkeypatch.setattr(config, "ENGINE_INPUT_DIR", tmp_path / "engine-input")
    monkeypatch.setattr(ENGINE, "options_loaded", True)
    monkeypatch.setattr(ENGINE, "options", {"checkpoints": [config.CHECKPOINT_INT8], "trainer": True})
    # By default, an int8 install allows training on int8 out of the box
    assert client.post("/api/identities/corpus1/train", json={}).status_code == 200
    # When allow_int8 is explicitly turned off, training refuses and requires the full-quality model
    assert client.put("/api/settings", json={"key": "training.allow_int8", "value": "off"}).status_code == 200
    reply = client.post("/api/identities/corpus1/train", json={})
    assert reply.status_code == 400 and "full-quality" in reply.json()["detail"]
