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


def test_training_separates_each_recording_then_runs_the_steps(server, tmp_path, monkeypatch):
    sources = []
    for name in ("one.flac", "two.flac"):
        path = tmp_path / name
        path.write_bytes(b"audio")
        sources.append(str(path))
    separated, steps = [], []
    monkeypatch.setattr(server, "separate", lambda source, out: separated.append(source.name) or (source, source))
    monkeypatch.setattr(server, "mono", lambda source, dest: dest.write_bytes(b"wav"))

    def run(args, job=None, log=None):
        steps.append(pathlib.Path(args[0]).name)
        raise RuntimeError("stop here")       # the first RVC step: enough to know everything before it worked

    monkeypatch.setattr(server, "run", run)
    job = {"state": "running"}
    with pytest.raises(RuntimeError, match="stop here"):
        server.train(job, "v1", sources, True, 2)
    assert separated == ["one.flac", "two.flac"]
    assert steps == ["preprocess.py"]
    assert sorted(p.name for p in (tmp_path / "voices" / "v1" / "work" / "trainset").iterdir()) == ["000.wav", "001.wav"]


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
