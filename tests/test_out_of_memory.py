"""Running out of GPU memory is said in plain words: when the engine reports it, when
it logged it and then lost the job, and a lost job says the engine stopped."""
import asyncio
import json
import time

import pytest

from app import jobs
from app.db import one
from app.engine import Engine

from conftest import make_take
from test_jobs import PLAN_GRAPH, REAL_SLEEP, FakeEngine, done, use


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(jobs.asyncio, "sleep", lambda _s: REAL_SLEEP(0))
    jobs.CANCELLED.clear()
    jobs.CURRENT.clear()


CUDA_OOM = "CUDA error: out of memory\nSearch for `cudaErrorMemoryAllocation'"
# A Mac's engine, on Metal.
MPS_OOM = ("MPS backend out of memory (MPS allocated: 27.10 GiB, other allocations: 5.77 MiB, max allowed: "
           "30.19 GiB). Tried to allocate 1.68 GiB on shared pool.")


def oom_report(graph, message=CUDA_OOM):
    job = done({}, graph, status="error")
    job["status"]["messages"] = [["execution_error", {
        "node_type": "YuE2GenerateABC", "exception_type": "torch.AcceleratorError",
        "exception_message": message}]]
    return job


@pytest.mark.parametrize("message", [CUDA_OOM, MPS_OOM])
def test_an_out_of_memory_report_is_said_plainly(monkeypatch, message):
    take = make_take(status="queued")
    use(monkeypatch, FakeEngine([oom_report(PLAN_GRAPH, message)]))
    asyncio.run(jobs.run_job("plan", take["id"]))
    error = one("SELECT error FROM takes WHERE id = ?", (take["id"],))["error"]
    assert error.startswith("the GPU ran out of memory.") and "length cap" in error


def test_other_engine_errors_keep_their_detail(monkeypatch):
    take = make_take(status="queued")
    use(monkeypatch, FakeEngine([done({}, PLAN_GRAPH, status="error")]))
    asyncio.run(jobs.run_job("plan", take["id"]))
    assert "engine reported error" in one("SELECT error FROM takes WHERE id = ?", (take["id"],))["error"]


def test_a_job_lost_after_the_engine_logged_running_out_says_so(monkeypatch):
    take = make_take(status="queued")
    engine = use(monkeypatch, FakeEngine([], started=True, state="gone"))
    engine.oom_at, engine.offline_at = time.time() + 1, time.time() + 1
    asyncio.run(jobs.run_job("plan", take["id"]))
    assert one("SELECT error FROM takes WHERE id = ?", (take["id"],))["error"].startswith("the GPU ran out of memory.")


def test_a_job_lost_when_the_engine_stopped_says_so(monkeypatch):
    take = make_take(status="queued")
    engine = use(monkeypatch, FakeEngine([], started=True, state="gone"))
    engine.oom_at, engine.offline_at = time.time() - 60, time.time() + 1
    asyncio.run(jobs.run_job("plan", take["id"]))
    assert "the engine stopped during this job" in one("SELECT error FROM takes WHERE id = ?", (take["id"],))["error"]


def test_training_lost_to_running_out_gets_the_training_hint(monkeypatch):
    engine = use(monkeypatch, FakeEngine([], started=True, state="gone"))
    engine.oom_at = time.time() + 1
    with pytest.raises(RuntimeError, match="ran out of memory.*TRAIN_MAX_MINUTES"):
        asyncio.run(jobs._run_graph("train", "run1", {}))


def test_the_engine_notes_running_out_but_not_a_retry_it_recovers_from():
    engine = Engine("http://127.0.0.1:1")
    engine._ingest_engine_entries([{"t": "1", "m": "Warning: Ran out of memory when regular VAE encoding, "
                                                  "retrying with tiled VAE encoding."}])
    assert engine.oom_at == 0
    engine._ingest_engine_entries([{"t": "2", "m": "!!! Exception during processing !!! CUDA error: out of memory"}])
    assert engine.oom_at > 0


# ---------------------------------------------------------------- the three sources

def test_the_error_the_engine_sent_names_a_lost_job(monkeypatch):
    take = make_take(status="queued")
    engine = use(monkeypatch, FakeEngine([], started=True, state="gone"))
    engine.failure = lambda pid: "YuE2GenerateMusic: AcceleratorError: CUDA error: out of memory"
    asyncio.run(jobs.run_job("render", take["id"]))
    assert one("SELECT error FROM takes WHERE id = ?", (take["id"],))["error"].startswith("the GPU ran out of memory.")


def test_another_error_the_engine_sent_is_given_as_it_came(monkeypatch):
    take = make_take(status="queued")
    engine = use(monkeypatch, FakeEngine([], started=True, state="gone"))
    engine.failure = lambda pid: "KSampler: ValueError: bad shape"
    asyncio.run(jobs.run_job("render", take["id"]))
    assert one("SELECT error FROM takes WHERE id = ?", (take["id"],))["error"] == "engine error: KSampler: ValueError: bad shape"


def write_fault(folder, **record):
    (folder / "yeufonic").mkdir(parents=True, exist_ok=True)
    (folder / "yeufonic" / "engine-fault.json").write_text(json.dumps(record))


def test_the_engines_note_as_its_job_thread_died_names_a_lost_job(monkeypatch, tmp_path):
    monkeypatch.setattr(jobs.config, "ENGINE_OUTPUT_DIR", tmp_path)
    write_fault(tmp_path, prompt_id="pid", at=time.time() + 1, out_of_memory=True, type="AcceleratorError", message="x")
    use(monkeypatch, FakeEngine([], started=True, state="gone"))
    with pytest.raises(RuntimeError, match="ran out of memory.*TRAIN_MAX_MINUTES"):
        asyncio.run(jobs._run_graph("train", "run1", {}))


def test_a_note_about_another_job_or_from_before_is_not_this_ones(monkeypatch, tmp_path):
    monkeypatch.setattr(jobs.config, "ENGINE_OUTPUT_DIR", tmp_path)
    use(monkeypatch, FakeEngine([], started=True, state="gone"))
    write_fault(tmp_path, prompt_id="other", at=time.time() + 1, out_of_memory=True, type="E", message="x")
    with pytest.raises(RuntimeError, match="^the engine lost the job$"):
        asyncio.run(jobs._run_graph("train", "run1", {}))
    write_fault(tmp_path, prompt_id="pid", at=time.time() - 60, out_of_memory=True, type="E", message="x")
    with pytest.raises(RuntimeError, match="^the engine lost the job$"):
        asyncio.run(jobs._run_graph("train", "run1", {}))


def test_a_note_of_another_fatal_error_is_given(monkeypatch, tmp_path):
    monkeypatch.setattr(jobs.config, "ENGINE_OUTPUT_DIR", tmp_path)
    write_fault(tmp_path, prompt_id="pid", at=time.time() + 1, out_of_memory=False, type="RuntimeError", message="boom")
    use(monkeypatch, FakeEngine([], started=True, state="gone"))
    with pytest.raises(RuntimeError, match="the engine stopped during this job: RuntimeError: boom"):
        asyncio.run(jobs._run_graph("render", "t1", {}))


def test_the_engine_keeps_the_error_it_was_sent_for_a_job():
    engine = Engine("http://127.0.0.1:1")
    engine.progress["p1"] = {}
    engine._handle_ws({"type": "execution_error", "data": {
        "prompt_id": "p1", "node_type": "YuE2GenerateMusic", "exception_type": "torch.AcceleratorError",
        "exception_message": "CUDA error: out of memory\nTIPS: ..."}})
    assert engine.failure("p1") == "YuE2GenerateMusic: AcceleratorError: CUDA error: out of memory TIPS: ..."
    assert engine.failure("p2") is None
    engine.forget("p1")
    assert engine.failure("p1") is None


# ---------------------------------------------------------------- the engine's side

def load_watch():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).parent.parent / "engine" / "custom_nodes" / "yue2_harmony" / "watch.py"
    spec = importlib.util.spec_from_file_location("yeufonic_watch", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_out_of_memory_is_found_behind_the_error_that_killed_the_thread():
    watch = load_watch()
    try:
        try:
            raise RuntimeError("CUDA error: out of memory")
        except RuntimeError:
            raise ValueError("while unloading")
    except ValueError as exc:
        assert watch.out_of_memory(exc)
    assert not watch.out_of_memory(ValueError("bad shape"))


def test_a_dying_job_thread_leaves_a_note(monkeypatch, tmp_path):
    import threading
    watch = load_watch()
    monkeypatch.setattr(watch, "output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(watch, "running_prompt", lambda: "p9")
    monkeypatch.setattr(watch, "_previous_hook", lambda args: None)
    monkeypatch.setattr(threading, "excepthook", watch.job_thread_died)

    def work():
        raise RuntimeError("CUDA error: out of memory")
    thread = threading.Thread(target=work, name="Thread-1 (prompt_worker)")
    thread.start()
    thread.join()
    fault = json.loads((tmp_path / "yeufonic" / "engine-fault.json").read_text())
    assert fault["prompt_id"] == "p9" and fault["out_of_memory"] and fault["type"] == "RuntimeError"
    assert (tmp_path / "yeufonic" / "engine-fault.json").stat().st_mode & 0o777 == 0o644


def test_another_thread_dying_leaves_no_note(monkeypatch, tmp_path):
    import threading
    watch = load_watch()
    monkeypatch.setattr(watch, "output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(watch, "_previous_hook", lambda args: None)
    monkeypatch.setattr(threading, "excepthook", watch.job_thread_died)
    thread = threading.Thread(target=lambda: 1 / 0, name="Thread-2 (other)")
    thread.start()
    thread.join()
    assert not (tmp_path / "yeufonic").exists()


def test_the_startup_message_points_at_the_app(monkeypatch):
    import logging
    watch = load_watch()
    record = logging.LogRecord("root", logging.INFO, __file__, 1, "To see the GUI go to: http://127.0.0.1:8188", None, None)
    monkeypatch.delenv("YEUFONIC_APP_URL", raising=False)
    watch.PointAtYeufonic().filter(record)
    assert record.getMessage() == "To see the GUI go to: http://127.0.0.1:8188", "left alone without the app's address"
    monkeypatch.setenv("YEUFONIC_APP_URL", "http://127.0.0.1:8090")
    watch.PointAtYeufonic().filter(record)
    assert record.getMessage() == "To see the GUI go to: http://127.0.0.1:8090"
    other = logging.LogRecord("root", logging.INFO, __file__, 1, "Starting server", None, None)
    watch.PointAtYeufonic().filter(other)
    assert other.getMessage() == "Starting server"


# ---------------------------------------------------------------- an engine left without a job thread

def test_a_job_whose_engine_thread_died_fails_at_once_and_marks_the_engine(monkeypatch, tmp_path):
    """The engine stayed up, still listing the job as running: without the note the
    wait would last until the time limit, hours for training."""
    monkeypatch.setattr(jobs.config, "ENGINE_OUTPUT_DIR", tmp_path)
    take = make_take(status="queued")
    engine = use(monkeypatch, FakeEngine([], started=True, state="running"))
    engine.stuck_on = None
    write_fault(tmp_path, prompt_id="pid", at=time.time() + 1, out_of_memory=True, type="AcceleratorError", message="x")
    started = time.time()
    asyncio.run(jobs.run_job("render", take["id"]))
    error = one("SELECT error FROM takes WHERE id = ?", (take["id"],))["error"]
    assert error.startswith("the GPU ran out of memory.") and error.endswith("until it is restarted.")
    assert engine.stuck_on == "pid" and time.time() - started < 2


def test_training_on_an_engine_without_a_job_thread_says_to_restart(monkeypatch, tmp_path):
    monkeypatch.setattr(jobs.config, "ENGINE_OUTPUT_DIR", tmp_path)
    engine = use(monkeypatch, FakeEngine([], started=True, state="running"))
    engine.stuck_on = None
    write_fault(tmp_path, prompt_id="pid", at=time.time() + 1, out_of_memory=True, type="AcceleratorError", message="x")
    with pytest.raises(RuntimeError, match="TRAIN_MAX_MINUTES.*restarted"):
        asyncio.run(jobs._run_graph("train", "run1", {}))


def test_jobs_wait_for_an_engine_that_needs_a_restart(monkeypatch):
    engine = use(monkeypatch, FakeEngine([]))
    engine.starting, engine.online, engine.options_loaded, engine.stuck_on = False, True, True, "pid"
    waits = []

    async def sleep(seconds):
        waits.append(seconds)
        if len(waits) == 3:
            engine.stuck_on = None
    monkeypatch.setattr(jobs.asyncio, "sleep", sleep)
    asyncio.run(jobs.wait_for_engine())
    assert len(waits) == 3


def test_the_mark_clears_once_the_restarted_engine_no_longer_lists_the_job():
    import httpx
    running = [[0, "pid", {}, {}, []]]

    def answer(request):
        if request.url.path == "/queue":
            return httpx.Response(200, json={"queue_running": running, "queue_pending": []})
        if request.url.path == "/system_stats":
            return httpx.Response(200, json={"devices": []})
        return httpx.Response(404)

    async def run():
        engine = Engine("http://engine")
        engine.client = httpx.AsyncClient(base_url="http://engine", transport=httpx.MockTransport(answer))
        engine.stuck_on = "pid"
        await engine.refresh_status()
        still = engine.stuck_on
        running.clear()
        await engine.refresh_status()
        await engine.client.aclose()
        return still, engine.stuck_on
    assert asyncio.run(run()) == ("pid", None)
