"""The voice routes: a recording or a corpus queues training; rename, octave, regenerate, delete."""
import io

from app import jobs, persona
from app.db import execute


def _queued():
    found = []
    while not jobs.QUEUE.empty():
        found.append(jobs.QUEUE.get_nowait())
    return found


def test_a_recording_becomes_a_voice_in_training(client):
    made = client.post("/api/voices", files={"file": ("my-voice.wav", io.BytesIO(b"RIFF...."), "audio/wav")},
                       data={"name": "My voice", "octave": "-1"}).json()
    assert made["name"] == "My voice" and made["octave"] == -1 and made["state"] == "training"
    assert {"kind": "voice", "id": made["id"]} in _queued()
    assert [v["id"] for v in client.get("/api/voices").json()] == [made["id"]]
    changed = client.patch(f"/api/voices/{made['id']}", data={"name": "Mine", "octave": "1"}).json()
    assert changed["name"] == "Mine" and changed["octave"] == 1
    assert client.post(f"/api/voices/{made['id']}/regenerate").json()["queued"] is True
    assert {"kind": "voice", "id": made["id"]} in _queued()
    assert client.delete(f"/api/voices/{made['id']}").json()["deleted"] == made["id"]
    assert client.get("/api/voices").json() == []


def test_a_corpus_voice_trains_on_the_corpus_songs(client, tmp_path):
    from app import config, identities
    execute("INSERT INTO identities (id, name, trigger_word, folder, created_at) VALUES (?,?,?,?,?)",
            ("corpusv", "A corpus", "trig", str(tmp_path), 0.0))
    execute("INSERT INTO identity_songs (id, identity_id, title, file, sha256, include, position) VALUES (?,?,?,?,?,1,0)",
            ("songv1", "corpusv", "A song", "a-song.flac", "0" * 64))
    song = {"id": "songv1", "title": "A song", "file": "a-song.flac"}
    folder = identities.song_dir("corpusv", song)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "original.flac").write_bytes(b"fLaC")
    made = client.post("/api/voices/from-identity", data={"identity_id": "corpusv"}).json()
    assert made["origin_identity"] == "corpusv" and made["state"] == "training"
    assert jobs.voice_sources(persona.one(made["id"])) == [str(folder / "original.flac")]
    _queued()
    persona.delete(made["id"])


def test_a_corpus_with_no_songs_is_refused(client, tmp_path):
    execute("INSERT INTO identities (id, name, trigger_word, folder, created_at) VALUES (?,?,?,?,?)",
            ("corpusempty", "Empty", "trig", str(tmp_path), 0.0))
    assert client.post("/api/voices/from-identity", data={"identity_id": "corpusempty"}).status_code == 400


def test_a_non_audio_upload_and_a_missing_voice_are_refused(client):
    assert client.post("/api/voices", files={"file": ("notes.txt", io.BytesIO(b"hi"), "text/plain")}).status_code == 400
    assert client.patch("/api/voices/nope", data={"name": "x"}).status_code == 404
    assert client.delete("/api/voices/nope").status_code == 404


def test_without_a_voice_service_voices_are_not_offered(client, monkeypatch):
    from app import config
    monkeypatch.setattr(config, "VOICE_URL", "")
    assert client.get("/api/voices/service").json()["ok"] is False
