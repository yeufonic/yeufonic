"""run_job and the stem lane against a fake engine: success, engine errors, the
timeout that starts only once the engine runs the job, cancelling, and a take
deleted while its audio downloads."""
import asyncio
import json
import shutil
import time

import pytest

from app import config, jobs
from app.db import execute, one
from app.library import peaks_path

from conftest import make_take, tone

REAL_SLEEP = asyncio.sleep


class FakeEngine:
    def __init__(self, histories, started=True, state="running", audio=None):
        self.histories = list(histories)
        self.started = started
        self.state = state
        self.audio = audio
        self.last_contact = time.time()
        self.cancelled, self.submitted, self.uploads = [], [], []
        self.on_download = None

    async def submit(self, graph):
        self.submitted.append(graph)
        return "pid"

    async def history(self, prompt_id):
        self.last_contact = time.time()
        return self.histories.pop(0) if self.histories else None

    def has_started(self, prompt_id):
        return self.started

    async def prompt_state(self, prompt_id):
        return self.state

    async def cancel(self, prompt_id):
        self.cancelled.append(prompt_id)

    def forget(self, prompt_id):
        pass

    async def upload(self, name, data):
        self.uploads.append(name)
        return {"name": name}

    async def download(self, item, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.audio, dest)
        if self.on_download:
            self.on_download()
        return dest


def done(outputs, graph, status="success"):
    return {"status": {"status_str": status, "completed": status == "success", "messages": [["x", {}]]},
            "prompt": [0, "pid", graph], "outputs": outputs}


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(jobs.asyncio, "sleep", lambda _s: REAL_SLEEP(0))
    jobs.CANCELLED.clear()
    jobs.CURRENT.clear()


def use(monkeypatch, engine):
    monkeypatch.setattr(jobs, "ENGINE", engine)
    return engine


PLAN_GRAPH = {"3": {"class_type": "PreviewAny"}}
# A plan that passes the score check: a key, a Vocal part with chords, enough bars.
ABC = ('X:1\nM:4/4\nL:1/8\nQ:1/4=100\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\nK:C\n'
       '% verse\nV: Vocal\n' + '"C"c4|"Am"A4|"F"F4|"G"G4|' * 4 + '\n')


def test_plan_lands(monkeypatch):
    take = make_take(status="queued")
    engine = use(monkeypatch, FakeEngine([None, done({"3": {"text": [ABC]}}, PLAN_GRAPH)]))
    asyncio.run(jobs.run_job("plan", take["id"]))
    row = one("SELECT * FROM takes WHERE id = ?", (take["id"],))
    assert row["status"] == "planned" and row["abc"] == ABC
    assert not engine.cancelled and not jobs.CURRENT


def test_an_engine_error_fails_at_once_not_after_the_timeout(monkeypatch):
    take = make_take(status="queued")
    use(monkeypatch, FakeEngine([done({}, PLAN_GRAPH, status="error")]))
    started = time.time()
    asyncio.run(jobs.run_job("plan", take["id"]))
    row = one("SELECT * FROM takes WHERE id = ?", (take["id"],))
    assert row["status"] == "failed" and "engine reported error" in row["error"]
    assert time.time() - started < 2


def test_a_job_the_engine_loses_mid_run_fails_at_once(monkeypatch):
    """An engine that restarts mid-job comes back without it.  The job had started,
    so its time limit (hours, for training) must not be what ends the wait."""
    take = make_take(status="queued")
    use(monkeypatch, FakeEngine([], started=True, state="gone"))
    started = time.time()
    asyncio.run(jobs.run_job("plan", take["id"]))
    row = one("SELECT * FROM takes WHERE id = ?", (take["id"],))
    assert row["status"] == "failed" and "lost" in row["error"]
    assert time.time() - started < 2


def test_timeout_cancels_the_prompt_on_the_engine(monkeypatch):
    monkeypatch.setitem(config.TIMEOUTS, "plan", 0.05)
    take = make_take(status="queued")
    engine = use(monkeypatch, FakeEngine([]))

    async def run():
        async def slow(_s):
            await REAL_SLEEP(0.02)
        monkeypatch.setattr(jobs.asyncio, "sleep", slow)
        await jobs.run_job("plan", take["id"])
    asyncio.run(run())
    row = one("SELECT * FROM takes WHERE id = ?", (take["id"],))
    assert row["status"] == "failed" and "timed out" in row["error"]
    assert engine.cancelled == ["pid"]


def test_waiting_in_the_engine_queue_does_not_count(monkeypatch):
    monkeypatch.setitem(config.TIMEOUTS, "plan", 0.01)
    take = make_take(status="queued")
    histories = [None] * 20 + [done({"3": {"text": [ABC]}}, PLAN_GRAPH)]
    use(monkeypatch, FakeEngine(histories, started=False, state="pending"))

    async def run():
        async def slow(_s):
            await REAL_SLEEP(0.005)
        monkeypatch.setattr(jobs.asyncio, "sleep", slow)
        await jobs.run_job("plan", take["id"])
    asyncio.run(run())
    assert one("SELECT status FROM takes WHERE id = ?", (take["id"],))["status"] == "planned"


def test_cancel_while_running(monkeypatch):
    take = make_take(status="queued")
    engine = use(monkeypatch, FakeEngine([]))
    jobs.CANCELLED.add(take["id"])
    asyncio.run(jobs.run_job("plan", take["id"]))
    row = one("SELECT * FROM takes WHERE id = ?", (take["id"],))
    assert row["status"] == "failed" and row["error"] == "cancelled"
    assert engine.cancelled == ["pid"] and take["id"] not in jobs.CANCELLED


def test_a_take_that_is_not_queued_is_skipped(monkeypatch):
    take = make_take(status="failed")
    engine = use(monkeypatch, FakeEngine([]))
    asyncio.run(jobs.run_job("render", take["id"]))
    assert not engine.submitted


RENDER_GRAPH = {"16": {"class_type": "SaveAudioAdvanced"}}


def render_history():
    return done({"16": {"audio": [{"filename": "take_00001_.flac", "subfolder": "yeufonic", "type": "output"}]}}, RENDER_GRAPH)


def test_render_saves_audio_note_peaks_and_drops_the_engine_copy(monkeypatch, data_dir):
    engine_out = data_dir / "engine-output"
    engine_copy = tone(engine_out / "yeufonic" / "take_00001_.flac", 1.0)
    monkeypatch.setattr(config, "ENGINE_OUTPUT_DIR", engine_out)
    # A one-second cap for the one-second tone: a render far shorter than its score
    # would be tried again, which is another test's business.
    take = make_take(status="queued", abc=ABC, title="Render Me", max_duration=1.0)
    use(monkeypatch, FakeEngine([render_history()], audio=engine_copy))
    asyncio.run(jobs.run_job("render", take["id"]))
    row = one("SELECT * FROM takes WHERE id = ?", (take["id"],))
    assert row["status"] == "done" and abs(row["duration"] - 1.0) < 0.05
    audio = config.TAKES_DIR / f"render-me-{take['id']}" / "render-me.flac"
    assert row["audio_path"] == str(audio) and audio.exists()
    note = json.loads((audio.parent / "take.json").read_text())
    assert note["seed"] == 1 and note["engine"] == row["engine"] == "comfyui"     # which engine rendered it
    assert peaks_path(audio).exists()
    assert not engine_copy.exists()


def test_a_take_deleted_during_download_leaves_no_folder(monkeypatch, data_dir):
    source_audio = tone(data_dir / "src.flac", 0.5)
    take = make_take(status="queued", abc=ABC, title="Gone")
    engine = use(monkeypatch, FakeEngine([render_history()], audio=source_audio))
    engine.on_download = lambda: execute("DELETE FROM takes WHERE id = ?", (take["id"],))
    asyncio.run(jobs.run_job("render", take["id"]))
    assert not (config.TAKES_DIR / f"gone-{take['id']}").exists()


def test_transcribe_uploads_the_recording_when_it_runs(monkeypatch, data_dir):
    path = tone(config.SOURCES_DIR / "abc-song.wav", 0.5)
    execute("""INSERT INTO sources(id, title, filename, stored_path, sha256, created_at, transcribe_state)
               VALUES('s1', 'Song', 'song.wav', ?, 'abc', 1, 'queued')""", (str(path),))
    graph = {"4": {"class_type": "PreviewAny"}}
    engine = use(monkeypatch, FakeEngine([done({"4": {"text": [ABC]}}, graph)]))
    asyncio.run(jobs.run_job("transcribe", "s1"))
    row = one("SELECT * FROM sources WHERE id = 's1'")
    # Sent as a FLAC with a clean ending, whatever it was uploaded as.
    assert engine.uploads == ["s1.flac"] and row["engine_file"] == "s1.flac"
    assert row["transcribe_state"] == "done" and row["abc"] == ABC
    assert engine.submitted[0]["1"]["inputs"]["audio"] == "s1.flac"


def test_cancelling_a_running_stem_job(monkeypatch, data_dir):
    audio = tone(data_dir / "a.flac", 0.5)
    take = make_take(audio_path=str(audio))
    execute("""INSERT INTO stem_sets(id, take_id, title, model, wanted, fmt, status, created_at, folder)
               VALUES('st1', ?, 't', 'htdemucs', 'vocals', 'wav', 'queued', 1, ?)""", (take["id"], str(data_dir / "stems" / "x")))
    killed = {}

    async def separate(*args, **kwargs):
        try:
            await REAL_SLEEP(30)
        except asyncio.CancelledError:
            killed["yes"] = True
            raise
    monkeypatch.setattr(jobs.stems, "separate", separate)

    async def run():
        worker = asyncio.create_task(jobs.stems_worker())
        await jobs.STEM_QUEUE.put({"id": "st1"})
        for _ in range(200):
            if jobs.CURRENT_STEMS.get("id") == "st1" and one("SELECT status FROM stem_sets WHERE id='st1'")["status"] == "running":
                break
            await REAL_SLEEP(0.01)
        jobs.cancel_stems(one("SELECT * FROM stem_sets WHERE id = 'st1'"))
        for _ in range(200):
            if not jobs.CURRENT_STEMS:
                break
            await REAL_SLEEP(0.01)
        worker.cancel()
        await asyncio.gather(worker, return_exceptions=True)
    asyncio.run(run())
    row = one("SELECT * FROM stem_sets WHERE id = 'st1'")
    assert killed and row["status"] == "failed" and row["error"] == "cancelled"


# ---------- an engine still starting ----------
def test_an_engine_that_has_not_answered_yet_is_starting_for_a_while():
    from app.engine import Engine
    engine = Engine("http://127.0.0.1:9")
    assert engine.starting
    engine.last_contact = time.time()          # it answered once, then went away
    assert not engine.starting
    engine = Engine("http://127.0.0.1:9")
    engine.created -= Engine.START_GRACE + 1   # never answered, and long past its start
    assert not engine.starting


def test_a_job_waits_for_a_starting_engine_then_goes_ahead(monkeypatch):
    import asyncio
    from types import SimpleNamespace

    engine = SimpleNamespace(starting=True, online=False, options_loaded=False)
    use(monkeypatch, engine)
    naps = []

    async def nap(seconds):
        naps.append(seconds)
        if len(naps) == 3:     # it answers, and its node list follows a moment later
            engine.starting, engine.online = False, True
        if len(naps) == 5:
            engine.options_loaded = True

    monkeypatch.setattr(jobs.asyncio, "sleep", nap)
    asyncio.run(jobs.wait_for_engine())
    assert len(naps) == 5 and engine.options_loaded


def test_an_engine_that_is_simply_offline_does_not_hold_a_job(monkeypatch):
    import asyncio
    from types import SimpleNamespace

    use(monkeypatch, SimpleNamespace(starting=False, online=False, options_loaded=False))
    naps = []

    async def nap(seconds):
        naps.append(seconds)

    monkeypatch.setattr(jobs.asyncio, "sleep", nap)
    asyncio.run(jobs.wait_for_engine())
    assert naps == []   # the job goes on, and fails as it always has


def test_training_has_no_time_limit(monkeypatch):
    """A clock blind to progress once stopped a run at step 1325 of 1400. Hours go
    by here between polls; training waits them out, where a render with a limit
    would not."""
    clock = {"now": 1_000_000.0}

    async def an_hour(_seconds):
        clock["now"] += 3600
    monkeypatch.setattr(jobs.asyncio, "sleep", an_hour)
    monkeypatch.setattr(jobs.time, "time", lambda: clock["now"])
    use(monkeypatch, FakeEngine([None, None, None, done({}, {})], started=True, state="running"))
    assert jobs.config.TIMEOUTS["train"] is None
    outcome, _job = asyncio.run(jobs._wait_for("train", "run1", "pid"))
    assert outcome == "done"
    use(monkeypatch, FakeEngine([None, None, None, done({}, {})], started=True, state="running"))
    outcome, _job = asyncio.run(jobs._wait_for("render", "t1", "pid"))
    assert outcome == "timeout"


# A score of 48 bars of 4/4 at 96 BPM: two minutes.
LONG_ABC = ('X:1\nM:4/4\nL:1/16\nQ:1/4=96\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\nK:C\n'
            '% verse\nV: Vocal\n' + '"C"c4d4e4f4|' * 48 + '\n')


def test_a_render_that_stops_long_before_its_score_is_tried_once_more(monkeypatch, data_dir, client):
    """The model sometimes writes a song's end long before its score runs out. The
    app renders it once more with a new seed before calling it done; a second early
    end is kept, and the take says it stopped early."""
    short = tone(data_dir / "short.flac", 5.0)
    take = make_take(status="queued", abc=LONG_ABC, title="Early", max_duration=360)
    jobs.RETRIED_EARLY.discard(take["id"])
    while not jobs.QUEUE.empty():
        jobs.QUEUE.get_nowait()
    use(monkeypatch, FakeEngine([render_history()], audio=short))
    asyncio.run(jobs.run_job("render", take["id"]))
    row = one("SELECT * FROM takes WHERE id = ?", (take["id"],))
    assert row["status"] == "queued" and row["seed"] != 1, "tried again, with a new seed"
    assert jobs.QUEUE.get_nowait() == {"kind": "render", "id": take["id"]}
    assert not (config.TAKES_DIR / f"early-{take['id']}" / "early.flac").exists(), "the short render is not kept"

    use(monkeypatch, FakeEngine([render_history()], audio=short))
    asyncio.run(jobs.run_job("render", take["id"]))
    row = one("SELECT * FROM takes WHERE id = ?", (take["id"],))
    assert row["status"] == "done", "a second early end is kept"
    assert client.get(f"/api/takes/{take['id']}").json()["stopped_early"] is True
    assert take["id"] not in jobs.RETRIED_EARLY, "a later render gets its own retry"


def test_a_render_that_ends_near_its_score_is_left_alone(monkeypatch, data_dir, client):
    full = tone(data_dir / "full.flac", 118.0)
    take = make_take(status="queued", abc=LONG_ABC, title="Whole", max_duration=360)
    use(monkeypatch, FakeEngine([render_history()], audio=full))
    asyncio.run(jobs.run_job("render", take["id"]))
    assert one("SELECT status FROM takes WHERE id = ?", (take["id"],))["status"] == "done"
    assert client.get(f"/api/takes/{take['id']}").json()["stopped_early"] is False
