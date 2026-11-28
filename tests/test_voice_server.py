"""The voice service's training steps, with RVC and the separator stood in: the order, and that each gets its input.

It runs in its own image, so here its heavy parts are replaced and only its own code is run.
"""
import importlib.util
import pathlib

import pytest

SERVER = pathlib.Path(__file__).resolve().parent.parent / "voice" / "server.py"


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICES_DIR", str(tmp_path / "voices"))
    spec = importlib.util.spec_from_file_location("voice_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "LOGS", tmp_path / "logs")
    monkeypatch.setattr(module, "ASSETS", tmp_path / "assets")
    return module


def test_the_minutes_are_shared_equally_and_a_short_song_gives_all_it_has(server):
    assert server.share_out([300, 300, 300], 600) == [200, 200, 200]
    shares = server.share_out([60, 400, 400], 600)        # the short song gives its 60 s, the others 270 s each
    assert shares[0] == 60 and abs(shares[1] - 270) < 1e-6 and abs(shares[2] - 270) < 1e-6
    assert server.share_out([30, 40], 600) == [30, 40]     # less than asked for: all of it
    assert server.share_out([0, 100], 50) == [0, 50]


def test_an_excerpt_holds_its_share_of_singing_around_the_middle(server):
    np = pytest.importorskip("numpy")
    mask = np.array([0, 1, 1, 0, 1, 1, 1, 0, 0, 1], dtype=bool)
    a, b = server.excerpt_with(mask, 3)
    assert int(mask[a:b].sum()) == 3 and a <= 5 <= b
    a, b = server.excerpt_with(mask, 99)
    assert (a, b) == (0, len(mask))


def test_training_separates_each_recording_then_runs_the_steps(server, tmp_path, monkeypatch):
    np = pytest.importorskip("numpy")
    soundfile = pytest.importorskip("soundfile")      # in the voice image; not every test image has it
    sources = []
    for name in ("one.flac", "two.flac"):
        path = tmp_path / name
        path.write_bytes(b"audio")
        sources.append(str(path))
    separated, steps = [], []
    monkeypatch.setattr(server, "separate", lambda source, out: separated.append(source.name) or (source, source))
    tone = (np.sin(np.linspace(0, 2000, 44100 * 4)) * 0.3).astype("float32")
    monkeypatch.setattr(server, "mono", lambda source, dest: soundfile.write(str(dest), tone, 44100))

    def run(args, job=None, log=None):
        steps.append(pathlib.Path(args[0]).name)
        raise RuntimeError("stop here")       # the first RVC step: enough to know everything before it worked

    monkeypatch.setattr(server, "run", run)
    job = {"state": "running"}
    with pytest.raises(RuntimeError, match="stop here"):
        server.train(job, "v1", sources, True, 2, minutes=0.05)     # 3 s of singing, shared across two songs
    assert separated == ["one.flac", "two.flac"]
    assert steps == ["preprocess.py"]
    staged = sorted((tmp_path / "voices" / "v1" / "work" / "trainset").iterdir())
    assert [p.name for p in staged] == ["000.wav", "001.wav"]
    assert all(abs(soundfile.info(str(p)).duration - 1.5) < 0.1 for p in staged)
    assert job["singing_seconds"] == 3


def test_a_stop_before_a_recording_is_separated_ends_the_run(server, tmp_path, monkeypatch):
    path = tmp_path / "one.flac"
    path.write_bytes(b"audio")
    monkeypatch.setattr(server, "separate", lambda source, out: pytest.fail("separated after a stop"))
    with pytest.raises(server.Stopped):
        server.train({"state": "running", "stop": True}, "v2", [str(path)], True, 2)


def test_the_reason_is_the_last_error_line(server, tmp_path):
    log = tmp_path / "train.log"
    log.write_text("starting\nTraceback (most recent call last):\n  File x\nRuntimeError: DataLoader worker exited\n"
                   "UserWarning: something\n")
    assert server._reason(log) == "RuntimeError: DataLoader worker exited"


def test_the_converted_vocal_is_lifted_to_the_rendered_ones_presence_and_level(server, tmp_path):
    np = pytest.importorskip("numpy")
    soundfile = pytest.importorskip("soundfile")
    pytest.importorskip("scipy")
    rate = 44100
    t = np.arange(rate * 4) / rate
    bright = (0.3 * np.sin(2 * np.pi * 400 * t) + 0.15 * np.sin(2 * np.pi * 4000 * t)).astype("float32")
    dull = (0.1 * np.sin(2 * np.pi * 400 * t) + 0.01 * np.sin(2 * np.pi * 4000 * t)).astype("float32")
    soundfile.write(str(tmp_path / "rendered.wav"), bright, rate)
    soundfile.write(str(tmp_path / "sung.wav"), dull, rate)
    server.settle(tmp_path / "rendered.wav", tmp_path / "sung.wav")
    settled, _ = soundfile.read(str(tmp_path / "sung.wav"), dtype="float32")
    assert server._presence(settled, rate) > server._presence(dull, rate) + 3
    assert abs(20 * np.log10(server._loudness(settled, rate) / server._loudness(bright, rate))) < 1.5


def test_on_a_mac_the_gpu_steps_run_on_apples_gpu_and_the_pitch_and_content_steps_on_the_cpu(tmp_path, monkeypatch):
    np = pytest.importorskip("numpy")
    soundfile = pytest.importorskip("soundfile")
    for key in ("RVC_TRAIN_DEVICE", "RVC_INFER_DEVICE", "PYTORCH_ENABLE_MPS_FALLBACK"):
        monkeypatch.setenv(key, "")      # so that what the service sets is taken away again afterwards
        monkeypatch.delenv(key)
    monkeypatch.setenv("VOICE_DEVICE", "mps")
    monkeypatch.setenv("VOICES_DIR", str(tmp_path / "voices"))
    spec = importlib.util.spec_from_file_location("voice_server_mac", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "LOGS", tmp_path / "logs")
    monkeypatch.setattr(module, "ASSETS", tmp_path / "assets")
    import os
    assert module.DEVICE == "mps"
    assert os.environ["RVC_TRAIN_DEVICE"] == os.environ["RVC_INFER_DEVICE"] == "mps"
    assert os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] == "1"
    source = tmp_path / "one.flac"
    source.write_bytes(b"audio")
    commands = []
    tone = (np.sin(np.linspace(0, 2000, 44100 * 4)) * 0.3).astype("float32")
    monkeypatch.setattr(module, "mono", lambda src, dest: soundfile.write(str(dest), tone, 44100))

    def run(args, job=None, log=None):
        commands.append(args)
        if pathlib.Path(args[0]).name == "extract_hubert_feature.py":
            raise RuntimeError("stop here")

    monkeypatch.setattr(module, "run", run)
    real_separate = module.separate
    monkeypatch.setattr(module, "separate", lambda src, out: (src, src))
    with pytest.raises(RuntimeError, match="stop here"):
        module.train({"state": "running"}, "v1", [str(source)], True, 2, minutes=0.05)
    f0, hubert = commands[1], commands[2]
    assert f0[:2] == ["train/dataset/extract_f0.py", "cpu"] and f0[-1] == "rmvpe"
    assert hubert[1] == "cpu"
    monkeypatch.setattr(module, "run", lambda args, job=None, log=None: commands.append(args))
    with pytest.raises(RuntimeError):
        real_separate(source, tmp_path / "sep")         # nothing written by the stand-in: the device is what matters
    assert commands[-1][commands[-1].index("--device") + 1] == "mps"


def test_elsewhere_the_steps_stay_on_the_nvidia_card(server, tmp_path, monkeypatch):
    assert server.DEVICE == "cuda"
    commands = []
    monkeypatch.setattr(server, "run", lambda args, job=None, log=None: commands.append(args))
    source = tmp_path / "one.flac"
    source.write_bytes(b"audio")
    with pytest.raises(RuntimeError):
        server.separate(source, tmp_path / "sep")
    assert commands[-1][commands[-1].index("--device") + 1] == "cuda"


def test_clean_f0_removes_groan_plunges_and_isolated_blips(server):
    np = pytest.importorskip("numpy")
    # 12 frames of steady 220 Hz singing, followed by a 3-frame drop to 90 Hz / 60 Hz at phrase end,
    # silence, then a 2-frame stray 130 Hz blip in silence.
    f0 = np.array(
        [0.0, 0.0] + [220.0] * 10 + [100.0, 82.0, 60.0] + [0.0] * 8 + [130.0, 128.0] + [0.0] * 4,
        dtype="float32",
    )
    cleaned = server.clean_f0(f0)
    # Main sung phrase stays intact
    assert np.allclose(cleaned[2:12], 220.0)
    # Phrase-end plunge (100/82/60 Hz) and short stray blip (130/128 Hz) are zeroed out
    assert np.all(cleaned[12:] == 0.0)
    # Raising the pitch floor to 115 Hz drops low-pitched 100 Hz runs as well
    low_run = np.array([100.0] * 10, dtype="float32")
    assert np.all(server.clean_f0(low_run, floor_hz=115.0) == 0.0)
    assert np.allclose(server.clean_f0(low_run, floor_hz=75.0), 100.0)


def test_prepare_for_rvc_and_gate_to_source_silence_phrase_tails_without_cutting_singing(server, tmp_path):
    np = pytest.importorskip("numpy")
    soundfile = pytest.importorskip("soundfile")
    pytest.importorskip("scipy")
    rate = 44100
    t_sing = np.arange(rate) / rate
    t_tail = np.arange(rate) / rate
    # 1 s of 330 Hz singing at 0.35 amplitude, then 1 s of -42 dB low-frequency tail + 50 Hz rumble
    singing = 0.35 * np.sin(2 * np.pi * 330 * t_sing)
    tail = 0.0025 * np.sin(2 * np.pi * 110 * t_tail) + 0.004 * np.sin(2 * np.pi * 45 * t_tail)
    vocals = np.concatenate([singing, tail]).astype("float32")
    src_path = tmp_path / "vocals.wav"
    clean_path = tmp_path / "vocals_clean.wav"
    soundfile.write(str(src_path), vocals, rate)

    server.prepare_for_rvc(src_path, clean_path)
    cleaned, _ = soundfile.read(str(clean_path), dtype="float32")
    # Singing half stays virtually untouched; tail half (after release settles) is strongly attenuated
    assert float(np.sqrt(np.mean(cleaned[:rate] ** 2))) > 0.22
    assert float(np.sqrt(np.mean(cleaned[rate + rate // 4:] ** 2))) < 0.0005

    # Now simulate RVC outputting a loud 0.12 groan during the silent second half
    sung_with_groan = np.concatenate([singing, 0.12 * np.sin(2 * np.pi * 70 * t_tail)]).astype("float32")
    sung_path = tmp_path / "sung.wav"
    soundfile.write(str(sung_path), sung_with_groan, rate)
    server.gate_to_source(src_path, sung_path)
    gated, _ = soundfile.read(str(sung_path), dtype="float32")
    assert float(np.sqrt(np.mean(gated[:rate] ** 2))) > 0.22
    assert float(np.sqrt(np.mean(gated[rate + rate // 3:] ** 2))) < 0.003


def _convert_fakes(server, monkeypatch, tmp_path, warm_fails=False):
    """A conversion with every heavy step stood in: what ran, warm (in the service) or as a script."""
    np = pytest.importorskip("numpy")
    sf = pytest.importorskip("soundfile")
    voice = server.VOICES / "v1"
    voice.mkdir(parents=True)
    (voice / "model.pth").write_bytes(b"x")
    ran = []

    def fake_separated(source, out_dir):
        out_dir.mkdir(parents=True, exist_ok=True)
        tone = (0.1 * np.sin(np.arange(44100) / 10)).astype("float32")
        for name in ("Vocals", "Instrumental"):
            sf.write(str(out_dir / f"{source.stem}_{name}.flac"), np.stack([tone, tone], 1), 44100)
        return server._separated(source, out_dir)

    def separate_here(source, out_dir):
        ran.append("separate here")
        if warm_fails:
            raise RuntimeError("no card")
        return fake_separated(source, out_dir)

    def separate(source, out_dir):
        ran.append("separate script")
        return fake_separated(source, out_dir)

    def sing_here(voice_id, vocals, sung, *args):
        ran.append("sing here")
        if warm_fails:
            raise RuntimeError("no card")
        sf.write(str(sung), sf.read(str(vocals))[0], 44100)

    def run(args, job=None, log=None):
        ran.append("sing script")
        out = pathlib.Path(args[args.index("--output") + 1])
        sf.write(str(out), sf.read(args[args.index("--input") + 1])[0], 44100)

    monkeypatch.setattr(server, "separate_here", separate_here)
    monkeypatch.setattr(server, "separate", separate)
    monkeypatch.setattr(server, "sing_here", sing_here)
    monkeypatch.setattr(server, "run", run)
    monkeypatch.setattr(server, "prepare_for_rvc", lambda vocals, dest, tail_gate="standard": __import__("shutil").copy(vocals, dest))
    for name in ("gate_to_source", "shift_formants", "settle", "blend"):
        monkeypatch.setattr(server, name, lambda *a, **k: None)
    monkeypatch.setattr(server, "audition_free", lambda: ran.append("let go"))
    source = tmp_path / "take.flac"
    sf.write(str(source), np.zeros((44100, 2), "float32"), 44100)
    server.convert("v1", source, tmp_path / "out.flac", 0)
    assert (tmp_path / "out.flac").exists()
    return ran


def test_a_conversion_runs_in_the_service_and_lets_go_of_the_voice(server, monkeypatch, tmp_path):
    monkeypatch.setattr(server, "WARM_CONVERT", True)
    assert _convert_fakes(server, monkeypatch, tmp_path) == ["separate here", "sing here", "let go"]


def test_a_conversion_that_fails_in_the_service_runs_as_scripts(server, monkeypatch, tmp_path):
    monkeypatch.setattr(server, "WARM_CONVERT", True)
    ran = _convert_fakes(server, monkeypatch, tmp_path, warm_fails=True)
    assert ran == ["separate here", "separate script", "sing here", "sing script", "let go"]


def test_voice_warm_off_runs_the_scripts_as_before(server, monkeypatch, tmp_path):
    monkeypatch.setattr(server, "WARM_CONVERT", False)
    assert _convert_fakes(server, monkeypatch, tmp_path) == ["separate script", "sing script", "let go"]


def test_the_separators_card_copies_are_emptied(server):
    class Module:
        def __init__(self):
            self._group_cache = {"cuda": 1}
            self._band_layers_cache = [1]
            self.keep = {"a": 1}

        def modules(self):
            return [self]
    model = Module()
    server._drop_device_caches(model)
    assert model._group_cache == {} and model._band_layers_cache is None and model.keep == {"a": 1}
