"""A job waiting in Up next can be taken back before it starts.  An analysis or a
transcription goes back to what it was, so cancelling a re-run keeps the old result."""
import pytest

from app.db import execute, one
from app.jobs import CURRENT, QUEUE

from conftest import make_take


@pytest.fixture(autouse=True)
def empty_queue():
    CURRENT.clear()
    while not QUEUE.empty():
        QUEUE.get_nowait()
    yield
    while not QUEUE.empty():
        QUEUE.get_nowait()


def corpus_song(**fields):
    song = {"id": "song-1", "title": "No More Lonely Nights", "style_hint": None, "key": None, "tempo": None,
            "score_state": "none", "style_state": "none", "vocals_state": "none", "lyrics_state": "none"}
    song.update(fields)
    execute("INSERT OR REPLACE INTO identities(id, name, trigger_word, folder, created_at) VALUES('id-1', 'Harbour Lights', 'harbourlights', '/tmp/m', 1.0)")
    execute("""INSERT OR REPLACE INTO identity_songs(id, identity_id, file, title, sha256, key, tempo, style_hint, score_state, style_state, vocals_state, lyrics_state)
               VALUES(:id, 'id-1', 'song.flac', :title, 'x', :key, :tempo, :style_hint, :score_state, :style_state, :vocals_state, :lyrics_state)""", song)
    return song


def test_cancelling_a_style_rerun_keeps_the_earlier_style(client):
    corpus_song(style_hint="melodic pop, piano ballad", style_state="done")
    client.post("/api/identities/id-1/songs/song-1/style")
    queue = client.get("/api/state").json()["queue"]
    assert [(q["kind"], q["title"]) for q in queue] == [("identity_style", "Style: No More Lonely Nights")]

    assert client.post("/api/queue/identity_style/song-1/cancel").json() == {"cancelled": True}
    song = one("SELECT style_state, style_hint FROM identity_songs WHERE id = 'song-1'")
    assert (song["style_state"], song["style_hint"]) == ("done", "melodic pop, piano ballad")
    assert client.get("/api/state").json()["queue"] == []


def test_cancelling_a_first_analysis_leaves_it_undone(client):
    corpus_song(score_state="queued")
    assert client.post("/api/queue/identity_score/song-1/cancel").json() == {"cancelled": True}
    assert one("SELECT score_state FROM identity_songs WHERE id = 'song-1'")["score_state"] == "none"


def test_a_running_analysis_is_not_cancelled_from_the_queue(client):
    corpus_song(style_state="running")
    assert client.post("/api/queue/identity_style/song-1/cancel").json() == {"cancelled": False}
    assert one("SELECT style_state FROM identity_songs WHERE id = 'song-1'")["style_state"] == "running"


def test_cancelling_a_transcription_keeps_the_score_it_had(client):
    execute("""INSERT INTO sources(id, title, filename, stored_path, sha256, created_at, abc, transcribe_state)
               VALUES('src1', 'Song', 'song.wav', '/tmp/song.wav', 'abc', 1.0, 'X:1', 'queued')""")
    assert client.post("/api/queue/transcribe/src1/cancel").json() == {"cancelled": True}
    assert one("SELECT transcribe_state FROM sources WHERE id = 'src1'")["transcribe_state"] == "done"


def test_cancelling_a_waiting_take(client):
    take = make_take(status="queued")
    QUEUE.put_nowait({"kind": "render", "id": take["id"]})
    assert client.post(f"/api/queue/render/{take['id']}/cancel").json() == {"cancelled": True}
    assert one("SELECT status, error FROM takes WHERE id = ?", (take["id"],)) == {"status": "failed", "error": "cancelled"}
    assert client.get("/api/state").json()["queue"] == []


def test_an_unknown_kind_is_not_cancelled(client):
    assert client.post("/api/queue/train/whatever/cancel").json() == {"cancelled": False}


def test_cancelling_current_job_stops_active_training_run(client):
    execute("""INSERT INTO lora_runs(id, identity_id, lora_name, steps, rank, state, started_at)
               VALUES('run-1', 'id-1', 'test_lora', 500, 64, 'running', 10.0)""")
    assert client.get("/api/state").json()["training"]["lora_name"] == "test_lora"
    res = client.post("/api/jobs/current/cancel").json()
    assert res == {"cancelled": True, "job": {"kind": "train", "id": "run-1"}}
    run = one("SELECT state, error FROM lora_runs WHERE id = 'run-1'")
    assert run["state"] == "cancelled"
    assert client.get("/api/state").json()["training"] is None


def test_active_corpus_style_analysis_appears_in_state_and_can_be_stopped(client):
    corpus_song(id="song-active", title="Breathe", style_state="running")
    CURRENT.clear()
    CURRENT.update({"kind": "identity_style", "id": "song-active", "prompt_id": None, "started": 10.0, "label": "External LLM"})
    try:
        st = client.get("/api/state").json()
        assert st["current"]["kind"] == "identity_style"
        assert st["current"]["id"] == "song-active"
        assert st["current"]["title"] == "Style: Breathe"
        assert st["current"]["label"] == "External LLM"

        res = client.post("/api/jobs/current/cancel").json()
        assert res == {"cancelled": True, "job": {"kind": "identity_style", "id": "song-active"}}
        assert client.get("/api/state").json()["current"] is None
    finally:
        CURRENT.clear()


def test_active_corpus_prep_appears_in_state_and_can_be_stopped(client):
    corpus_song(id="song-prep", title="Time", vocals_state="running")
    from app.jobs import CURRENT_IDENTITY
    CURRENT_IDENTITY.clear()
    CURRENT_IDENTITY.update({"id": "song-prep", "started": 10.0, "stage": "Separating the vocal (demucs)", "progress": 0.5})
    try:
        st = client.get("/api/state").json()
        assert st["current"]["kind"] == "identity_prep"
        assert st["current"]["id"] == "song-prep"
        assert st["current"]["title"] == "Vocal & lyrics: Time"
        assert st["current"]["label"] == "Separating the vocal (demucs)"
        assert st["current"]["progress"] == 0.5

        res = client.post("/api/jobs/current/cancel").json()
        assert res == {"cancelled": True, "job": {"kind": "identity_prep", "id": "song-prep"}}
        assert client.get("/api/state").json()["current"] is None
    finally:
        CURRENT_IDENTITY.clear()


def test_waiting_corpus_prep_appears_in_queue_and_can_be_cancelled(client):
    corpus_song(id="song-prep-wait", title="Money", vocals_state="queued")
    from app.jobs import IDENTITY_QUEUE
    while not IDENTITY_QUEUE.empty():
        IDENTITY_QUEUE.get_nowait()
    IDENTITY_QUEUE.put_nowait({"id": "song-prep-wait"})
    try:
        queue = client.get("/api/state").json()["queue"]
        assert any(q["kind"] == "identity_prep" and q["id"] == "song-prep-wait" and q["title"] == "Vocal & lyrics: Money" for q in queue)

        res = client.post("/api/queue/identity_prep/song-prep-wait/cancel").json()
        assert res == {"cancelled": True}
        assert one("SELECT vocals_state FROM identity_songs WHERE id = 'song-prep-wait'")["vocals_state"] == "none"
        queue = client.get("/api/state").json()["queue"]
        assert not any(q.get("id") == "song-prep-wait" for q in queue)
    finally:
        while not IDENTITY_QUEUE.empty():
            IDENTITY_QUEUE.get_nowait()


def test_reanalysing_corpus_styles_queues_all_songs(client):
    corpus_song(id="s-1", title="Song One", vocals_state="done", lyrics_state="done", score_state="done", style_state="done")
    corpus_song(id="s-2", title="Song Two", vocals_state="done", lyrics_state="done", score_state="done", style_state="done")

    # A plain analyse call on an already completed corpus automatically re-queues style analysis:
    res = client.post("/api/identities/id-1/analyse").json()
    assert res == {"queued": 2}
    s1 = one("SELECT style_state FROM identity_songs WHERE id = 's-1'")
    s2 = one("SELECT style_state FROM identity_songs WHERE id = 's-2'")
    assert (s1["style_state"], s2["style_state"]) == ("queued", "queued")
    q_titles = [q["title"] for q in client.get("/api/state").json()["queue"]]
    assert q_titles == ["Style: Song One", "Style: Song Two"]

    # Explicit step="style" also works identically:
    res = client.post("/api/identities/id-1/analyse?step=style").json()
    assert res == {"queued": 2}


def test_reanalysing_corpus_all_steps_queues_full_pipeline(client):
    corpus_song(id="s-all", title="Complete Song", vocals_state="done", lyrics_state="done", score_state="done", style_state="done")
    from app.jobs import IDENTITY_QUEUE
    while not IDENTITY_QUEUE.empty():
        IDENTITY_QUEUE.get_nowait()

    res = client.post("/api/identities/id-1/analyse?step=all").json()
    assert res == {"queued": 3}
    row = one("SELECT vocals_state, lyrics_state, score_state, style_state FROM identity_songs WHERE id = 's-all'")
    assert (row["vocals_state"], row["lyrics_state"], row["score_state"], row["style_state"]) == ("queued", "queued", "queued", "queued")


def test_prepare_song_reuses_stored_audio_when_inbox_removed(tmp_path, monkeypatch):
    import asyncio
    from app import identities, jobs
    song_dir = identities.song_dir("id-1", {"id": "s-stored", "title": "Track", "file": "track.flac"})
    song_dir.mkdir(parents=True, exist_ok=True)
    stored = song_dir / "original.flac"
    stored.write_bytes(b"dummy audio content")
    (song_dir / "vocals.flac").write_bytes(b"vocals")
    (song_dir / "whisper.json").write_text("[]")

    execute("""INSERT OR REPLACE INTO identities(id, name, trigger_word, folder, created_at)
               VALUES('id-1', 'Band', 'band', '/tmp/nonexistent_removed_folder', 1.0)""")
    execute("""INSERT OR REPLACE INTO identity_songs(id, identity_id, file, title, sha256, duration, include,
                                                     vocals_state, lyrics_state, score_state, position)
               VALUES('s-stored', 'id-1', 'track.flac', 'Track', 'x', 300, 1, 'queued', 'queued', 'done', 0)""")

    asyncio.run(jobs.prepare_song("s-stored"))
    row = one("SELECT vocals_state, lyrics_state, stored_path FROM identity_songs WHERE id = 's-stored'")
    assert row["stored_path"] == str(stored)
    assert row["vocals_state"] == "done"
    assert row["lyrics_state"] == "done"


def test_duration_threshold_is_25_minutes():
    from app import identities
    assert identities.MAX_SECONDS == 1500
    assert not identities.too_long(600)      # 10 min: previously blocked, now accepted
    assert not identities.too_long(1024)     # 17 min (Dogs): accepted
    assert not identities.too_long(1411)     # 23.5 min (Echoes): accepted
    assert not identities.too_long(1500)     # 25 min exact: accepted
    assert identities.too_long(1501)         # > 25 min: flagged as too long

