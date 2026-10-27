"""The engine image's start script, which refuses to start ComfyUI on a driver too old for its PyTorch, and how the app
reports what it found: the engine pill while it waits, and the engine's build in About."""
import importlib.util
import json
import types
from pathlib import Path

import pytest

from app import config
from app.engine import engine_build, model_slow, start_problem

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("engine_start", ROOT / "engine" / "start.py")
start = importlib.util.module_from_spec(spec)
spec.loader.exec_module(start)


@pytest.mark.parametrize("built, driver, refused", [
    ("13.0", "12.8", True),     # the case it is for: a CUDA 13 PyTorch on a CUDA 12 driver
    ("13.0", "11.8", True),
    ("13.0", "13.0", False),
    ("13.0", "13.2", False),
    ("13.2", "13.0", False),    # within a major version a newer CUDA runs on an older driver
    ("12.8", "12.4", False),
    ("12.8", "13.0", False),
    (None, "12.8", False),      # anything it cannot read lets the engine start
    ("13.0", None, False),
])
def test_only_an_older_major_version_of_cuda_stops_the_engine(built, driver, refused):
    found = start.problem(built, driver)
    assert bool(found) is refused
    if refused:
        assert found["problem"] == "driver"
        assert "TORCH_CUDA=cu128" in found["message"] and driver in found["message"] and built in found["message"]


@pytest.mark.parametrize("line, cuda", [
    ("cuda: Optional[str] = '13.0'", "13.0"),
    ("cuda = '12.8'", "12.8"),
    ("cuda: Optional[str] = None", None),     # a CPU build
])
def test_the_cuda_build_is_read_from_torchs_version_file(tmp_path, monkeypatch, line, cuda):
    (tmp_path / "torch").mkdir()
    (tmp_path / "torch" / "__init__.py").write_text("")
    (tmp_path / "torch" / "version.py").write_text(f"__version__ = '2.9.1'\n{line}\ngit_version = 'x'\n")
    monkeypatch.setattr(start.importlib.util, "find_spec",
                        lambda name: types.SimpleNamespace(origin=str(tmp_path / "torch" / "__init__.py")))
    assert start.torch_cuda() == cuda


@pytest.fixture
def run(tmp_path, monkeypatch):
    """start.main with the driver and the build given, recording what it did instead of doing it."""
    note = tmp_path / "output" / "yeufonic" / "engine-start.json"
    monkeypatch.setattr(start, "NOTE", note)
    did = {}

    def go(argv, built="13.0", driver="13.0"):
        did.clear()
        monkeypatch.setattr(start, "torch_cuda", built if callable(built) else lambda: built)
        monkeypatch.setattr(start, "driver_cuda", lambda: driver)
        monkeypatch.setattr(start, "wait", lambda: did.setdefault("waited", True))
        monkeypatch.setattr(start.os, "execvp", lambda file, args: did.setdefault("ran", list(args)))
        start.main(argv)
        return did

    go.note = note
    return go


def test_a_driver_too_old_leaves_a_note_and_waits(run):
    did = run(["python", "main.py", "--port", "8188"], driver="12.8")
    assert did.get("waited")
    assert json.loads(run.note.read_text())["driver_cuda"] == "12.8"


def test_a_driver_that_will_do_starts_the_command_and_takes_the_note_away(run):
    run(["python", "main.py"], driver="12.8")
    assert run.note.exists()
    did = run(["python", "main.py", "--port", "8188"], driver="13.0")
    assert did == {"ran": ["python", "main.py", "--port", "8188"]}
    assert not run.note.exists(), "a note left behind would say the engine cannot start after it has"


def test_the_check_never_stands_in_the_way(run):
    def broken():
        raise OSError("unreadable")

    assert run(["python", "main.py"], built=broken).get("ran") == ["python", "main.py"]
    assert run(["python", "main.py", "--cpu"], driver="12.8").get("ran"), "a CPU engine needs no driver"
    assert run([], driver=None)["ran"][:2] == ["python", "main.py"]


def test_the_image_starts_through_the_script_and_builds_for_cuda_13_unless_told():
    dockerfile = (ROOT / "engine" / "Dockerfile").read_text()
    assert 'ENTRYPOINT ["python", "/opt/yeufonic/start.py"]' in dockerfile
    assert "COPY start.py /opt/yeufonic/start.py" in dockerfile
    assert "ARG TORCH_CUDA=cu130" in dockerfile
    compose = (ROOT / "compose.yml").read_text()
    assert 'TORCH_CUDA: "${TORCH_CUDA:-cu130}"' in compose


@pytest.mark.parametrize("version, built", [
    ("2.9.1+cu130", {"torch": "2.9.1", "cuda": "13.0"}),
    ("2.9.1+cu128", {"torch": "2.9.1", "cuda": "12.8"}),
    ("2.13.0+cu126", {"torch": "2.13.0", "cuda": "12.6"}),
    ("2.9.1", {"torch": "2.9.1", "cuda": None}),
    ("", None),
])
def test_the_engines_build_is_read_from_its_stats(version, built):
    assert engine_build({"system": {"pytorch_version": version}}) == built


def test_the_pill_says_why_an_engine_will_not_start(client, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ENGINE_OUTPUT_DIR", tmp_path)
    assert client.get("/api/state").json()["engine"]["problem"] is None
    (tmp_path / "yeufonic").mkdir()
    (tmp_path / "yeufonic" / "engine-start.json").write_text(json.dumps(start.problem("13.0", "12.8")))
    assert start_problem()["problem"] == "driver"
    assert "TORCH_CUDA=cu128" in client.get("/api/state").json()["engine"]["problem"]["message"]


@pytest.mark.parametrize("version, checkpoint, slow", [
    ("2.9.1+cu128", "int8", True),
    ("2.9.1+cu130", "int8", False),
    ("2.9.1+cu128", "bf16", False),
    ("2.9.1", "int8", False),
])
def test_about_says_when_the_low_memory_model_is_on_a_cuda_12_engine(monkeypatch, version, checkpoint, slow):
    monkeypatch.setattr(config, "CHECKPOINT", config.CHECKPOINT_INT8 if checkpoint == "int8" else config.CHECKPOINT_BF16)
    assert model_slow(engine_build({"system": {"pytorch_version": version}})) is slow
    assert model_slow(None) is False
