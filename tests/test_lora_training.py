"""Training a LoRA: it holds the GPU, so the app keeps everything else off it.

Training is on by default and can be switched off.  The tests pin it on, so they do
not depend on the environment; the ones for it switched off are at the bottom.
"""
import time
from pathlib import Path

import pytest

from app import config
from app.db import execute, one, set_setting


@pytest.fixture(autouse=True)
def training_built_in(monkeypatch):
    """Everything above the "switched off" tests assumes the feature is on."""
    monkeypatch.setattr(config, "TRAINING_ENABLED", True)


def a_corpus(with_export: bool = True, tmp_path=None) -> dict:
    identity_id = "corpus1"
    execute("""INSERT INTO identities(id, name, trigger_word, description, voice, folder, consent, created_at)
               VALUES(?, 'Alicia', 'alicia', 'Soulful R&B', 'female', '/music', 1, ?)""",
            (identity_id, time.time()))
    if with_export:
        dataset = config.DATA_DIR / "identities" / identity_id / "dataset"
        dataset.mkdir(parents=True)
        (dataset / "one.flac").write_bytes(b"not really audio")
    return {"id": identity_id}


def test_training_needs_an_export_first(client):
    corpus = a_corpus(with_export=False)
    answer = client.post(f"/api/identities/{corpus['id']}/train")
    assert answer.status_code == 400
    assert "Export" in answer.json()["detail"]


def test_training_queues_a_run_and_reports_it(client, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ENGINE_INPUT_DIR", tmp_path / "engine-input")
    corpus = a_corpus()
    answer = client.post(f"/api/identities/{corpus['id']}/train", json={"steps": 50, "rank": 8})
    assert answer.status_code == 200
    run = answer.json()
    assert run["lora_name"] == "alicia_lora" and run["steps"] == 50

    state = client.get("/api/state").json()
    assert state["training"]["id"] == run["id"]
    assert state["training"]["state"] == "queued"


def test_a_running_loRA_keeps_the_engine_to_itself(client, monkeypatch, tmp_path):
    """Measured at 12.5 GB of 16: a render on top of training would fail, so it is
    refused rather than started."""
    monkeypatch.setattr(config, "ENGINE_INPUT_DIR", tmp_path / "engine-input")
    a_corpus()
    execute("""INSERT INTO lora_runs(id, identity_id, lora_name, steps, rank, state, started_at)
               VALUES('run1', 'corpus1', 'alicia_lora', 5000, 16, 'running', ?)""", (time.time(),))

    refused = client.post("/api/songs", json={"title": "x", "style": "pop", "lyrics": "[Verse]\none"})
    assert refused.status_code == 409
    assert "GPU" in refused.json()["detail"]

    # and a second training run is refused too
    again = client.post("/api/identities/corpus1/train")
    assert again.status_code == 409


def test_a_finished_run_is_named_after_the_corpus_and_keeps_its_snapshots(client, monkeypatch, tmp_path):
    """The best goes under the plain name and its copy is dropped.  The snapshots stay,
    each named for its step, because a published LoRA is a checkpoint picked by ear,
    but in a group of their own so they do not read as more finished LoRAs."""
    import asyncio
    from app import jobs, loras

    root = tmp_path / "loras"
    root.mkdir()
    monkeypatch.setattr(config, "ENGINE_INPUT_DIR", tmp_path / "engine-input")
    monkeypatch.setattr(loras, "folder", lambda: root)

    async def trained(kind, run_id, graph):
        for name in ("alicia_lora_best", "alicia_lora_step50", "alicia_lora_step100"):
            (root / f"{name}.safetensors").write_bytes(name.encode())
        (root / "alicia_lora_log.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(jobs, "_run_graph", trained)

    a_corpus()
    execute("""INSERT INTO lora_runs(id, identity_id, lora_name, steps, rank, state)
               VALUES('run1', 'corpus1', 'alicia_lora', 100, 16, 'queued')""")
    asyncio.run(jobs.run_lora_train("run1"))

    assert one("SELECT state FROM lora_runs WHERE id = 'run1'")["state"] == "done"
    assert sorted(path.name for path in root.glob("*.safetensors")) == [
        "alicia_lora.safetensors", "alicia_lora_step100.safetensors", "alicia_lora_step50.safetensors"]
    assert (root / "alicia_lora.safetensors").read_bytes() == b"alicia_lora_best"
    assert (root / "alicia_lora.txt").read_text(encoding="utf-8").split("\n")[0] == "Alicia"
    assert (root / "alicia_lora_step50.txt").read_text(encoding="utf-8").split("\n")[0] == "Alicia · step 50"
    assert loras.families(root) == {"alicia_lora": "Your corpora", "alicia_lora_step50": "Training checkpoints",
                                    "alicia_lora_step100": "Training checkpoints"}
    assert "\n\n" not in (root / "families.txt").read_text(encoding="utf-8")
    assert one("SELECT lora FROM identities WHERE id = 'corpus1'")["lora"] == "alicia_lora.safetensors"


def test_a_run_trains_on_as_much_of_each_song_as_the_card_allows(client, monkeypatch, tmp_path):
    """Worked out when Train is pressed, from the card as it is then: the minutes reach the
    dataset builder and the context reaches the trainer. Numbers in the settings win."""
    import asyncio
    from app import jobs, loras

    root = tmp_path / "loras"
    root.mkdir()
    monkeypatch.setattr(config, "ENGINE_INPUT_DIR", tmp_path / "engine-input")
    monkeypatch.setattr(loras, "folder", lambda: root)
    monkeypatch.setattr(config, "TRAIN_MINUTES_AUTO", True)
    monkeypatch.setattr(config, "TRAIN_TOKENS_AUTO", True)
    monkeypatch.setattr(jobs.ENGINE, "gpu", lambda: {"vram_free": 14.7 * 1024 ** 3, "engine_vram": 0})
    seen = {}

    async def trained(kind, run_id, graph):
        seen["graph"] = graph
        (root / "alicia_lora_best.safetensors").write_bytes(b"x")
    monkeypatch.setattr(jobs, "_run_graph", trained)

    a_corpus()
    execute("""INSERT INTO identity_songs(id, identity_id, file, title, sha256, duration, include, position)
               VALUES('s1', 'corpus1', 'a.flac', 'A', 'h1', 400, 1, 0)""")
    execute("""INSERT INTO lora_runs(id, identity_id, lora_name, steps, rank, state)
               VALUES('run1', 'corpus1', 'alicia_lora', 100, 16, 'queued')""")
    asyncio.run(jobs.run_lora_train("run1"))
    assert seen["graph"]["4"]["inputs"]["max_seconds"] == 5.5 * 60
    assert seen["graph"]["6"]["inputs"]["max_tokens"] == 10240

    monkeypatch.setattr(config, "TRAIN_MINUTES_AUTO", False)
    monkeypatch.setattr(config, "TRAIN_MAX_MINUTES", 4.0)
    execute("UPDATE lora_runs SET state = 'queued' WHERE id = 'run1'")
    asyncio.run(jobs.run_lora_train("run1"))
    assert seen["graph"]["4"]["inputs"]["max_seconds"] == 4.0 * 60


def test_steps_follow_the_size_of_the_corpus_above_a_floor(monkeypatch):
    """About ten passes over each song, the trainer's rule of thumb, rounded up to a
    checkpoint, and never fewer than 500.  Ten passes alone give a small corpus too few
    steps to learn from; the checkpoints are
    kept, so a run that goes on too long can be heard back to an earlier step."""
    monkeypatch.setattr(config, "TRAIN_STEPS", None)
    assert config.train_steps(14) == 500
    assert config.train_steps(1) == 500
    assert config.train_steps(43) == 500
    assert config.train_steps(60) == 600, "a large corpus still gets its ten passes"
    assert config.train_steps(63) == 650
    monkeypatch.setattr(config, "TRAIN_STEPS", 600)
    assert config.train_steps(17) == 600, "an explicit setting wins"


def test_the_trainer_gets_the_published_recipe():
    from app import jobs

    g = jobs.train_graph("in", "set", "alicia_lora", 200)
    planner_inputs = g["6"]["inputs"]
    acoustic_inputs = g["7"]["inputs"]
    assert planner_inputs["steps"] == 200
    assert acoustic_inputs["steps"] == 1000
    assert planner_inputs["save_every"] == 50
    assert acoustic_inputs["save_every"] == 50


def test_a_queued_run_can_be_cancelled(client):
    execute("""INSERT INTO lora_runs(id, identity_id, lora_name, steps, rank, state)
               VALUES('run2', 'corpus1', 'alicia_lora', 5000, 16, 'queued')""")
    answer = client.post("/api/lora-runs/run2/cancel")
    assert answer.status_code == 200
    assert one("SELECT state FROM lora_runs WHERE id = 'run2'")["state"] == "cancelled"
    assert client.get("/api/state").json()["training"] is None


# ------------------------------------------------------------------ switched off

def test_training_is_on_by_default():
    """Both switches default to on: the app's setting, and the engine image's."""
    root = Path(__file__).resolve().parent.parent
    assert 'os.environ.get("TRAINING_ENABLED", "1")' in (root / "app" / "config.py").read_text()
    assert "ARG WITH_TRAINER=1" in (root / "engine" / "Dockerfile").read_text()
    compose = (root / "compose.yml").read_text()
    assert 'WITH_TRAINER: "1"' in compose and 'TRAINING_ENABLED: "1"' in compose


def test_switched_off_it_says_so(client, monkeypatch):
    """It answers 501 with the reason, not 404, so a caller can tell the difference
    between a feature switched off and a URL that is wrong."""
    monkeypatch.setattr(config, "TRAINING_ENABLED", False)
    corpus = a_corpus()
    answer = client.post(f"/api/identities/{corpus['id']}/train")
    assert answer.status_code == 501
    detail = answer.json()["detail"]
    assert "switched off" in detail and "TRAINING_ENABLED=1" in detail


def test_the_gate_comes_before_anything_else(client, monkeypatch):
    """A corpus with no export still reports the feature, not the missing export: the
    user cannot act on advice about exporting if the button will never appear."""
    monkeypatch.setattr(config, "TRAINING_ENABLED", False)
    corpus = a_corpus(with_export=False)
    assert client.post(f"/api/identities/{corpus['id']}/train").status_code == 501


def test_the_page_is_told_so_it_can_hide_the_button(client, monkeypatch):
    monkeypatch.setattr(config, "TRAINING_ENABLED", False)
    assert client.get("/api/state").json()["options"]["training_available"] is False


def test_it_still_needs_the_engine_node_when_the_flag_is_on(client, monkeypatch):
    """Both halves are required: the flag alone, on an image built without the pack,
    must not offer the button."""
    monkeypatch.setattr(config, "TRAINING_ENABLED", True)
    from app.main import ENGINE
    monkeypatch.setitem(ENGINE.options, "trainer", False)
    assert client.get("/api/state").json()["options"]["training_available"] is False
    monkeypatch.setitem(ENGINE.options, "trainer", True)
    assert client.get("/api/state").json()["options"]["training_available"] is True


def test_exporting_is_gated_with_everything_else(client, monkeypatch):
    """Exporting a set was once left open, on the argument that it feeds a trainer
    elsewhere. It closes with the rest: a set nobody can train here is an hour of CPU
    spent on a folder, and the wall should come before the work, not after it."""
    monkeypatch.setattr(config, "TRAINING_ENABLED", True)
    corpus = a_corpus()
    monkeypatch.setattr(config, "TRAINING_ENABLED", False)
    assert client.post(f"/api/identities/{corpus['id']}/export").status_code == 501


# ------------------------------------- the whole workflow, not just the button

def test_the_corpus_routes_are_closed_too(client, monkeypatch):
    """Preparing a corpus costs a vocal separation and a transcription for every song.
    With no way to train at the end of it that work buys nothing, so the way in closes
    with the training step rather than after it."""
    monkeypatch.setattr(config, "TRAINING_ENABLED", False)
    for method, path in (
        ("get", "/api/identities"),
        ("post", "/api/identities"),
        ("get", "/api/personas"),
        ("get", "/api/import/browse"),
        ("post", "/api/lora-runs/whatever/cancel"),
    ):
        answer = getattr(client, method)(path)
        assert answer.status_code == 501, f"{method} {path} answered {answer.status_code}"


def test_a_corpus_that_exists_is_left_alone(client, monkeypatch):
    """Closing the way in must not touch what is already on disk or in the database."""
    monkeypatch.setattr(config, "TRAINING_ENABLED", True)
    corpus = a_corpus()
    monkeypatch.setattr(config, "TRAINING_ENABLED", False)
    assert client.get(f"/api/identities/{corpus['id']}").status_code == 501
    assert one("SELECT * FROM identities WHERE id = ?", (corpus["id"],)) is not None


def test_the_rest_of_the_app_is_untouched(client, monkeypatch):
    """The gate is a prefix match, so this is the test that catches it growing teeth."""
    monkeypatch.setattr(config, "TRAINING_ENABLED", False)
    for path in ("/api/state", "/api/takes", "/api/sources", "/api/spaces", "/api/settings"):
        assert client.get(path).status_code == 200, path


def test_a_learned_style_is_the_caption_the_lora_was_trained_on(client):
    """A LoRA learns a sound with the words it was captioned with, so a chip that left
    out the corpus description would ask it for something it never saw."""
    from app import main

    execute("""INSERT INTO identities(id, name, trigger_word, description, voice, folder, consent, created_at, lora)
               VALUES('c1', 'Marlow Sands', 'marlowsands', 'British accent, raspy baritone', 'male', '/m', 1, ?,
                      'marlow_sands_lora.safetensors')""", (time.time(),))
    for position, (title, hint, own) in enumerate((("Tin Roof Rain", "blues rock", ""),
                                                    ("Small Hours", "", ""),
                                                    ("Copperline", "folk rock", "bright piano"))):
        execute("""INSERT INTO identity_songs(id, identity_id, file, title, sha256, include, key, tempo, style_hint,
                                              description, position)
                   VALUES(?, 'c1', ?, ?, ?, 1, 'A major', 86, ?, ?, ?)""",
                (f"s{position}", f"{title}.flac", title, f"sha{position}", hint, own, position))

    chips = main._lora_corpus_styles()["marlow_sands_lora.safetensors"]
    captions = {song["title"]: song["caption"] for song in main._identity_view(one("SELECT * FROM identities WHERE id = 'c1'"))["songs"]}

    assert len(chips) == 3, "a song with no style suggestion still has a caption, so it gets a chip"
    for chip in chips:
        # The page puts the trigger in front and the tempo after, as the caption has them.
        assert f"marlowsands, {chip['prompt']}, {chip['tempo']} BPM" == captions[chip["title"]]
    assert "British accent" in chips[0]["prompt"] and "male vocal" in chips[0]["prompt"]
    assert "bright piano" in chips[2]["prompt"] and "British accent" not in chips[2]["prompt"], \
        "a song's own description replaces the corpus one, as it does in the export"


def test_a_checkpoint_offers_its_loras_learned_styles(client, monkeypatch):
    """A checkpoint was trained on the same captions as the LoRA it folds under, so
    it gets the same chips, and so does a previous run set aside under a dated name."""
    from app import loras, main

    assert loras.run_lora("marlow_sands_lora_step950.safetensors") == "marlow_sands_lora.safetensors"
    assert loras.run_lora("marlow_sands_lora_20260920_step50.safetensors") == "marlow_sands_lora.safetensors"
    assert loras.run_lora("marlow_sands_lora_20260920_1432.safetensors") == "marlow_sands_lora.safetensors"
    assert loras.run_lora("marlow_sands_lora.safetensors") == "marlow_sands_lora.safetensors"
    assert loras.run_lora("slider-metal.safetensors") == "slider-metal.safetensors"

    chips = [{"title": "Tin Roof Rain", "prompt": "blues rock", "hint": "blues rock", "tempo": 86, "key": "A major"}]
    monkeypatch.setattr(main, "_lora_corpus_styles", lambda: {"marlow_sands_lora.safetensors": chips})
    monkeypatch.setattr(main.ENGINE, "options", {"loras": ["marlow_sands_lora.safetensors",
                                                           "marlow_sands_lora_step950.safetensors",
                                                           "marlow_sands_lora_20260920_step50.safetensors",
                                                           "slider-metal.safetensors"]})
    styles = {item["name"]: item.get("styles") for item in main._catalogue_with_styles()}

    assert styles["marlow_sands_lora_step950.safetensors"] == chips
    assert styles["marlow_sands_lora_20260920_step50.safetensors"] == chips
    assert not styles["slider-metal.safetensors"], "a LoRA from elsewhere has no corpus behind it"


def test_a_lora_this_app_cannot_read_fails_the_run_with_the_fix(client, monkeypatch, tmp_path):
    """An engine image older than the trainer patch leaves its files readable by root
    only.  The run says so and how to fix it, rather than leaving a LoRA half finished."""
    import asyncio
    from app import jobs, loras

    root = tmp_path / "loras"
    root.mkdir()
    monkeypatch.setattr(config, "ENGINE_INPUT_DIR", tmp_path / "engine-input")
    monkeypatch.setattr(loras, "folder", lambda: root)

    async def trained(kind, run_id, graph):
        (root / "alicia_lora_best.safetensors").write_bytes(b"x")
    monkeypatch.setattr(jobs, "_run_graph", trained)
    real_access = jobs.os.access
    monkeypatch.setattr(jobs.os, "access", lambda path, mode: False if str(path).endswith("_best.safetensors") else real_access(path, mode))

    a_corpus()
    execute("""INSERT INTO lora_runs(id, identity_id, lora_name, steps, rank, state)
               VALUES('run1', 'corpus1', 'alicia_lora', 100, 16, 'queued')""")
    asyncio.run(jobs.run_lora_train("run1"))
    run = one("SELECT state, error FROM lora_runs WHERE id = 'run1'")
    assert run["state"] == "failed" and "readable by root only" in run["error"] and "chmod" in run["error"]


def test_checkpoints_are_deleted_when_training_ends_if_settings_says_so(client, monkeypatch, tmp_path):
    """Each checkpoint is as big as the LoRA, so Settings can delete them."""
    import asyncio
    from app import jobs, loras

    root = tmp_path / "loras"
    root.mkdir()
    monkeypatch.setattr(config, "ENGINE_INPUT_DIR", tmp_path / "engine-input")
    monkeypatch.setattr(loras, "folder", lambda: root)

    async def trained(kind, run_id, graph):
        for name in ("alicia_lora_best", "alicia_lora_step50", "alicia_lora_step100"):
            (root / f"{name}.safetensors").write_bytes(name.encode())
    monkeypatch.setattr(jobs, "_run_graph", trained)

    a_corpus()
    set_setting("training.checkpoints", "delete")
    execute("""INSERT INTO lora_runs(id, identity_id, lora_name, steps, rank, state)
               VALUES('run1', 'corpus1', 'alicia_lora', 100, 16, 'queued')""")
    asyncio.run(jobs.run_lora_train("run1"))
    assert one("SELECT state FROM lora_runs WHERE id = 'run1'")["state"] == "done"
    assert sorted(p.name for p in root.glob("*.safetensors")) == ["alicia_lora.safetensors"]
    assert "alicia_lora_step50" not in loras.families(root)
    listed = {item["key"]: item for item in client.get("/api/settings").json()["settings"]}
    assert listed["training.checkpoints"]["value"] == "delete"
    client.put("/api/settings", json={"key": "training.checkpoints", "value": "keep"})
    listed = {item["key"]: item for item in client.get("/api/settings").json()["settings"]}
    assert listed["training.checkpoints"]["value"] == "keep"


def test_a_previous_run_is_kept_under_a_dated_name_or_deleted(tmp_path):
    """Training again under a name that has a LoRA would replace it, and leave any
    checkpoints past the new run's end looking like its own."""
    import os
    from app import loras
    root = tmp_path / "loras"
    root.mkdir()
    for stem in ("mycorpus_lora", "mycorpus_lora_step50", "mycorpus_lora_step600", "other_lora"):
        (root / f"{stem}.safetensors").write_bytes(b"x")
        loras.write_note(root / f"{stem}.safetensors", "mycorpus", "mycorpus", title=stem)
    (root / "mycorpus_lora.txt").write_text("mycorpus\nTrigger: mycorpus\nStyle: 60s rock\n", encoding="utf-8")
    (root / "mycorpus_lora_log.json").write_text("[]", encoding="utf-8")
    when = 1790337600          # 25 Sep 2026
    for path in root.glob("mycorpus_lora*.safetensors"):
        os.utime(path, (when, when))

    found = loras.previous_run("mycorpus_lora", root)
    assert found["files"] == 3 and found["day"].endswith("Sep")
    new = loras.set_aside("mycorpus_lora", root, "mycorpus")
    assert new.startswith("mycorpus_lora_2026")
    assert sorted(p.name for p in root.glob("mycorpus_lora*.safetensors")) == [
        f"{new}.safetensors", f"{new}_step50.safetensors", f"{new}_step600.safetensors"]
    note = (root / f"{new}.txt").read_text(encoding="utf-8").split("\n")
    assert note[0].startswith("mycorpus · ") and note[0].endswith("(previous)") and "Style: 60s rock" in note
    assert (root / f"{new}_step50.txt").read_text(encoding="utf-8").startswith("mycorpus · ")
    assert loras.families(root)[new.lower()] == loras.PREVIOUS_FAMILY
    assert (root / f"{new}_log.json").is_file() and loras.previous_run("mycorpus_lora", root) is None
    assert (root / "other_lora.safetensors").is_file()                         # nothing else touched

    for stem in ("mycorpus_lora", "mycorpus_lora_step50"):
        (root / f"{stem}.safetensors").write_bytes(b"x")
    assert loras.delete_run("mycorpus_lora", root) == 2
    assert loras.previous_run("mycorpus_lora", root) is None and (root / f"{new}.safetensors").is_file()


def test_training_again_asks_what_to_do_with_the_last_run(client, tmp_path, monkeypatch):
    from app import loras, main
    root = tmp_path / "loras"
    root.mkdir()
    monkeypatch.setattr(loras, "folder", lambda: root)
    a_corpus()
    ident = one("SELECT * FROM identities WHERE id = 'corpus1'")
    base = main._lora_base(ident)
    (root / f"{base}.safetensors").write_bytes(b"x")
    view = client.get("/api/identities/corpus1").json()
    assert view["previous_lora"]["name"] == base and view["previous_lora"]["keep_as"].endswith("(previous)")
    monkeypatch.setattr(main, "_engine_free_for_training", lambda: None)
    monkeypatch.setattr(config, "ENGINE_INPUT_DIR", tmp_path / "engine-input")
    assert client.post("/api/identities/corpus1/train", json={}).status_code == 409      # must choose
    made = client.post("/api/identities/corpus1/train", json={"previous": "keep"})
    assert made.status_code == 200
    assert not (root / f"{base}.safetensors").exists() and list(root.glob(f"{base}_2*.safetensors"))
    from app import jobs
    while not jobs.QUEUE.empty():
        jobs.QUEUE.get_nowait()


def test_training_asks_the_engine_to_unload_its_models_first(client, monkeypatch, tmp_path):
    """Models left loaded by analysis or renders would share the card with the trainer."""
    import asyncio
    from app import jobs, loras

    root = tmp_path / "loras"
    root.mkdir()
    monkeypatch.setattr(config, "ENGINE_INPUT_DIR", tmp_path / "engine-input")
    monkeypatch.setattr(loras, "folder", lambda: root)
    order = []

    async def freed():
        order.append("free")
    monkeypatch.setattr(jobs.ENGINE, "free", freed)

    async def trained(kind, run_id, graph):
        order.append("train")
        (root / "alicia_lora_best.safetensors").write_bytes(b"x")
    monkeypatch.setattr(jobs, "_run_graph", trained)

    a_corpus()
    execute("""INSERT INTO lora_runs(id, identity_id, lora_name, steps, rank, state)
               VALUES('run1', 'corpus1', 'alicia_lora', 100, 16, 'queued')""")
    asyncio.run(jobs.run_lora_train("run1"))
    assert order == ["free", "train"]


def test_settings_groups_and_lora_training_options(client, monkeypatch, tmp_path):
    """Settings are organised into collapsible groups, and the training.* settings
    materially configure the training workflow, song length cap, and int8 model gate."""
    import asyncio
    from app import jobs, loras, main

    items = client.get("/api/settings").json()["settings"]
    by_key = {item["key"]: item for item in items}

    # Every non-storage setting belongs to one of the five Settings sub-folders
    non_storage = [item for item in items if item.get("section") != "storage"]
    assert all(item.get("group") in ("audio", "training", "llm", "art", "system") for item in non_storage)

    training_keys = {item["key"] for item in non_storage if item.get("group") == "training"}
    assert training_keys == {
        "training.branches",
        "training.regularization",
        "training.semantic_tokens",
        "training.keep_strategy",
        "training.targets",
        "training.conditioning",
        "training.max_minutes",
        "training.allow_int8",
    }
    assert by_key["training.regularization"]["requires"] == {"training.branches": ["both", "planner"]}
    assert by_key["training.conditioning"]["requires"] == {"training.branches": ["both", "acoustic"]}

    # Low-memory (int8) gate: blocked by default when only the int8 model is present, allowed when turned on
    corpus = a_corpus()
    monkeypatch.setattr(config, "ENGINE_INPUT_DIR", tmp_path / "engine-input")
    monkeypatch.setattr(main.ENGINE, "options_loaded", True)
    monkeypatch.setitem(main.ENGINE.options, "checkpoints", ["yue2_3b_int8_convrot.safetensors"])

    refused = client.post(f"/api/identities/{corpus['id']}/train")
    assert refused.status_code == 400 and "low-memory" in refused.json()["detail"]

    assert client.put("/api/settings", json={"key": "training.allow_int8", "value": "on"}).status_code == 200
    allowed = client.post(f"/api/identities/{corpus['id']}/train", json={"steps": 50, "rank": 16})
    assert allowed.status_code == 200
    while not jobs.QUEUE.empty():
        jobs.QUEUE.get_nowait()

    # Configure custom training options and verify run_lora_train wires them into the graph
    assert client.put("/api/settings", json={"key": "training.branches", "value": "acoustic"}).status_code == 200
    assert client.put("/api/settings", json={"key": "training.semantic_tokens", "value": "on"}).status_code == 200
    assert client.put("/api/settings", json={"key": "training.keep_strategy", "value": "final"}).status_code == 200
    assert client.put("/api/settings", json={"key": "training.targets", "value": "attention"}).status_code == 200
    assert client.put("/api/settings", json={"key": "training.max_minutes", "value": "0"}).status_code == 200

    # Full song (0) means _train_sizing gives 60 minutes for export/view and 0.0 max_seconds in EncodeDataset
    assert main._train_sizing(corpus["id"])["minutes"] == 60.0

    root = tmp_path / "loras"
    root.mkdir()
    monkeypatch.setattr(loras, "folder", lambda: root)
    seen = {}

    async def trained(kind, run_id, graph):
        seen["graph"] = graph
        (root / "alicia_lora_acoustic.safetensors").write_bytes(b"acoustic")
    monkeypatch.setattr(jobs, "_run_graph", trained)

    asyncio.run(jobs.run_lora_train(allowed.json()["id"]))
    g = seen["graph"]
    assert "6" not in g and "5" not in g and "7" in g
    assert g["4"]["inputs"]["max_seconds"] == 0.0
    assert g["7"]["inputs"]["use_semantic_tokens"] is True
    assert g["7"]["inputs"]["keep"] == "final"
    assert g["7"]["inputs"]["targets"] == "attention"


def test_regularization_can_use_all_songs_or_sample_by_percentage(client, tmp_path):
    """training.regularization supports 'on' (100% of songs), percentage samples ('75%', '50%', '25%', '10%'), and 'off'."""
    from app import jobs

    ds = tmp_path / "dataset"
    ds.mkdir()
    for idx in range(20):
        (ds / f"song_{idx:02d}.style.txt").write_text(f"trig, indie rock song {idx}, 120 BPM\n", encoding="utf-8")
        (ds / f"song_{idx:02d}.lyrics.txt").write_text(f"[Verse]\nLine {idx} one\nLine {idx} two\n\n[Chorus]\nHook {idx}\n",
                                                       encoding="utf-8")

    # 'on' leaves styles/lyrics blank so YuE2TrainerRegularizationScores uses all songs from the dataset
    assert jobs._sample_regularization_prompts(ds, "on") == ("", "")
    assert jobs._sample_regularization_prompts(ds, "off") == ("", "")

    # '25%' of 20 songs samples 5 evenly spaced style prompts and a representative lyric block
    styles_25, lyrics_25 = jobs._sample_regularization_prompts(ds, "25%")
    lines = styles_25.splitlines()
    assert len(lines) == 5
    assert lines[0] == "trig, indie rock song 0, 120 BPM"
    assert lines[-1] == "trig, indie rock song 19, 120 BPM"
    assert "[Verse]" in lyrics_25 and "[Chorus]" in lyrics_25

    # '50%' of 20 songs samples 10 prompts
    styles_50, _ = jobs._sample_regularization_prompts(ds, "50%")
    assert len(styles_50.splitlines()) == 10

    # Setting '25%' via PUT /api/settings is accepted and wired into Node 5 of train_graph
    assert client.put("/api/settings", json={"key": "training.regularization", "value": "25%"}).status_code == 200
    g = jobs.train_graph("in", "set", "alicia_lora", 200, regularization="25%", reg_styles=styles_25, reg_lyrics=lyrics_25)
    assert g["5"]["inputs"]["styles"] == styles_25
    assert g["5"]["inputs"]["lyrics"] == lyrics_25
    assert g["6"]["inputs"]["regularization"] == ["5", 0]


def test_finish_training_cleans_up_dual_branch_and_resume_files(monkeypatch, tmp_path):
    """When dual-branch training finishes, planner and acoustic weights and step checkpoints
    are merged into unified files, and all raw branch parts, raw weights, and .resume optimizer
    states are deleted."""
    import asyncio
    import pytest
    pytest.importorskip("safetensors.torch")
    import safetensors.torch
    import torch
    from app import jobs, loras

    root = tmp_path / "loras"
    root.mkdir()
    monkeypatch.setattr(loras, "folder", lambda: root)

    name = "alicia_lora"
    # Create final branch files
    safetensors.torch.save_file({"diffusion_model.weight": torch.zeros(2)}, str(root / f"{name}_acoustic.safetensors"))
    safetensors.torch.save_file({"text_encoders.weight": torch.zeros(2)}, str(root / f"{name}_planner.safetensors"))
    (root / f"{name}_acoustic_raw.safetensors").write_bytes(b"raw_acoustic")
    (root / f"{name}_planner_raw.safetensors").write_bytes(b"raw_planner")
    (root / f"{name}_acoustic.resume").write_bytes(b"resume_acoustic")
    (root / f"{name}_planner.resume").write_bytes(b"resume_planner")

    # Create step 50 branch files
    safetensors.torch.save_file({"diffusion_model.step50": torch.zeros(2)}, str(root / f"{name}_acoustic_000050.safetensors"))
    safetensors.torch.save_file({"text_encoders.step50": torch.zeros(2)}, str(root / f"{name}_planner_000050.safetensors"))
    (root / f"{name}_acoustic_000050.resume").write_bytes(b"resume_acoustic_50")
    (root / f"{name}_planner_000050.resume").write_bytes(b"resume_planner_50")

    run = {"id": "run1", "lora_name": name}
    identity = {"id": "c1", "name": "Alicia", "trigger_word": "alicia"}

    produced = asyncio.run(jobs.finish_training(run, identity))
    assert produced == f"{name}.safetensors"
    assert (root / f"{name}.safetensors").is_file()
    assert (root / f"{name}_step50.safetensors").is_file()

    # Verify merged contents contain both planner and acoustic weights
    final_sd = safetensors.torch.load_file(str(root / f"{name}.safetensors"))
    assert "diffusion_model.weight" in final_sd and "text_encoders.weight" in final_sd

    step50_sd = safetensors.torch.load_file(str(root / f"{name}_step50.safetensors"))
    assert "diffusion_model.step50" in step50_sd and "text_encoders.step50" in step50_sd

    # Verify no .resume or branch files remain
    assert not list(root.glob("*.resume"))
    assert not list(root.glob("*_acoustic*"))
    assert not list(root.glob("*_planner*"))




