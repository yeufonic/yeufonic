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
