from app.jobs import (PLAN_VARIETY, build_plan_graph, build_render_graph, build_transcribe_graph,
                      extract_audio_item, extract_text_output)


TAKE = {"id": "t1", "checkpoint": "ck", "style": "rock", "lyrics": "la", "abc": "X:1", "seed": 42,
        "mode": "melody", "max_duration": 120, "variety": "wild"}


def test_templates_are_fresh_copies():
    first = build_transcribe_graph("a.wav")
    second = build_transcribe_graph("b.wav")
    assert first["1"]["inputs"]["audio"] == "a.wav" and second["1"]["inputs"]["audio"] == "b.wav"


def test_plan_graph_uses_the_variety():
    node = build_plan_graph(TAKE)["2"]["inputs"]
    assert node["temperature"] == PLAN_VARIETY["wild"]["temperature"]
    assert node["mode"] == "full" and node["seed"] == 42


def test_render_graph():
    graph = build_render_graph(TAKE)
    assert graph["11"]["inputs"]["abc"] == "X:1"
    assert graph["11"]["inputs"]["max_duration"] == 120.0
    assert graph["14"]["inputs"]["seed"] == 42
    assert graph["15"]["class_type"] == "VAEDecodeAudioTiled"
    assert graph["15"]["inputs"]["tile_size"] == 512
    assert graph["15"]["inputs"]["overlap"] == 64
    # A new prefix every run, so the engine never answers from its output cache.
    assert graph["16"]["inputs"]["filename_prefix"].startswith("yeufonic/t1-")


def test_extractors():
    job = {
        "prompt": [0, "pid", {"3": {"class_type": "PreviewAny"}, "16": {"class_type": "SaveAudioAdvanced"}}],
        "outputs": {"3": {"text": ["X:1\nabc"]}, "16": {"audio": [{"filename": "take.flac", "subfolder": "yeufonic"}]}},
    }
    assert extract_text_output(job, "PreviewAny") == "X:1\nabc"
    assert extract_audio_item(job, "SaveAudioAdvanced")["filename"] == "take.flac"
    assert extract_text_output({}, "PreviewAny") is None


def test_train_graph():
    from app.jobs import train_graph
    g = train_graph("lora-run1", "dataset1", "test_lora", 50, 64, 32, 3.5)
    assert g["1"]["class_type"] == "CheckpointLoaderSimple"
    assert g["2"]["class_type"] == "AudioEncoderLoader"
    assert g["3"]["class_type"] == "YuE2TrainerDatasetFolder"
    assert g["3"]["inputs"]["folder"] == "lora-run1"
    assert g["4"]["class_type"] == "YuE2TrainerEncodeDataset"
    assert g["4"]["inputs"]["max_seconds"] == 3.5 * 60
    assert g["5"]["class_type"] == "YuE2TrainerRegularizationScores"
    assert g["6"]["class_type"] == "YuE2TrainerPlannerLoRA"
    assert g["6"]["inputs"]["steps"] == 50
    assert g["6"]["inputs"]["rank"] == 64
    assert g["7"]["class_type"] == "YuE2TrainerAcousticLoRA"
    assert g["7"]["inputs"]["rank"] == 32
    assert g["7"]["inputs"]["conditioning"] == "compact"
    assert g["8"]["class_type"] == "YuE2TrainerSaveLoRA"
    assert g["9"]["class_type"] == "YuE2TrainerSaveLoRA"


def test_train_graph_optional_settings():
    from app.jobs import train_graph
    # Acoustic-only branch omits regularization (5), planner (6) and planner save (8)
    g_ac = train_graph("lora-run1", "dataset1", "test_lora", 100, branches="acoustic",
                       semantic_tokens="on", keep_strategy="final", targets="attention", max_minutes=0.0)
    assert "5" not in g_ac and "6" not in g_ac and "8" not in g_ac
    assert "7" in g_ac and "9" in g_ac
    assert g_ac["4"]["inputs"]["max_seconds"] == 0.0
    assert g_ac["7"]["inputs"]["use_semantic_tokens"] is True
    assert g_ac["7"]["inputs"]["train_acoustic_head"] is True
    assert g_ac["7"]["inputs"]["keep"] == "final"
    assert g_ac["7"]["inputs"]["ema_decay"] == 0.0
    assert g_ac["7"]["inputs"]["eval_holdout"] == 0
    assert g_ac["7"]["inputs"]["targets"] == "attention"
    assert g_ac["7"]["inputs"]["conditioning"] == "compact"

    g_inf = train_graph("lora-run1", "dataset1", "test_lora", 100, branches="acoustic", conditioning="inference_like")
    assert g_inf["7"]["inputs"]["conditioning"] == "inference_like"

    # Planner-only branch without regularization omits (5), acoustic (7) and acoustic save (9)
    g_pl = train_graph("lora-run1", "dataset1", "test_lora", 100, branches="planner",
                       regularization="off", semantic_tokens="on", targets="attention")
    assert "5" not in g_pl and "7" not in g_pl and "9" not in g_pl
    assert "6" in g_pl and "8" in g_pl
    assert "regularization" not in g_pl["6"]["inputs"]
    assert g_pl["6"]["inputs"]["regularization_fraction"] == 0.0
    assert g_pl["6"]["inputs"]["train_semantic"] is True
    assert g_pl["6"]["inputs"]["targets"] == "attention"



def test_a_sound_seed_draws_the_sound_and_leaves_the_notes():
    """Node 11 chooses the notes and node 14 draws the sound from noise. A take with a
    sound seed of its own keeps its notes and gets a new voice; one without renders as
    it always did."""
    from app.jobs import build_render_graph
    take = {"id": "t1", "style": "pop", "lyrics": "[verse]\na", "abc": "X:1", "seed": 111, "mode": "full",
            "interpretation": "standard", "max_duration": 120}
    plain = build_render_graph(take)
    assert plain["11"]["inputs"]["seed"] == 111 and plain["14"]["inputs"]["seed"] == 111
    voiced = build_render_graph({**take, "sound_seed": 222})
    assert voiced["11"]["inputs"]["seed"] == 111 and voiced["14"]["inputs"]["seed"] == 222


def test_plan_graph_advanced_settings():
    take = {
        "id": "t_adv", "style": "disco", "lyrics": "dance", "seed": 42,
        "mode": "full", "max_duration": 180, "variety": "normal",
        "max_abc_tokens": 2048,
        "chord_hold_limit": 4,
        "chord_outside_bonus": 1.5,
        "target_key": "Dm",
        "target_bpm": 128,
        "avoid": "screaming vocals, harsh noise",
    }
    graph = build_plan_graph(take)
    # Token cap
    assert graph["2"]["inputs"]["max_abc_tokens"] == 2048
    # Harmony settings wired
    assert graph["2"]["inputs"]["hold_limit"] == 4
    assert graph["2"]["inputs"]["outside_bonus"] == 1.5
    # Style combines style, key, tempo, and avoid
    style = graph["2"]["inputs"]["style"]
    assert "disco" in style
    assert "key of D minor" in style
    assert "128 BPM" in style
    assert "avoid: screaming vocals, harsh noise" in style


def test_render_graph_advanced_settings():
    take = {
        "id": "t_adv_render", "style": "synthpop", "lyrics": "hello", "seed": 99,
        "mode": "full", "max_duration": 180, "abc": "X:1\nM:4/4\nL:1/8\nQ:1/4=100\nK:C\nCDEF|",
        "sampler_steps": 48,
        "target_bpm": 135,
        "target_key": "Am",
        "avoid": "guitar solos",
    }
    graph = build_render_graph(take)
    # Sampler steps
    assert graph["14"]["inputs"]["steps"] == 48
    # ABC tempo replaced by target_bpm
    assert "Q:1/4=135" in graph["11"]["inputs"]["abc"]
    # Style combines style, key, tempo, avoid
    style = graph["11"]["inputs"]["style"]
    assert "synthpop" in style
    assert "key of A minor" in style
    assert "135 BPM" in style
    assert "avoid: guitar solos" in style
