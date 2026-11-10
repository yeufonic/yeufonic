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
    assert jobs.voice_sources(persona.one(made["id"])) == [{"path": str(folder / "original.flac"), "separate": True}]
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


def _model_bytes():
    return b"PK\x03\x04" + b"weights" * 10        # torch.save writes a zip; the app checks no further


def test_a_voice_exports_and_imports_back(client):
    import zipfile
    made = persona.create("Shared voice", octave=1)
    persona.model_file(made["id"]).write_bytes(_model_bytes())
    (persona.folder(made["id"]) / "model.index").write_bytes(b"index")
    persona.ready(made["id"], str(persona.model_file(made["id"])))
    got = client.get(f"/api/voices/{made['id']}/export")
    assert got.status_code == 200 and "Shared voice.voice.zip" in got.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(got.content)) as archive:
        assert sorted(archive.namelist()) == ["model.index", "model.pth", "voice.json"]
    back = client.post("/api/voices/import", files={"file": ("Shared voice.voice.zip", got.content, "application/zip")}).json()
    assert back["name"] == "Shared voice" and back["octave"] == 1 and back["state"] == "ready"
    assert persona.model_file(back["id"]).read_bytes() == _model_bytes()
    assert (persona.folder(back["id"]) / "model.index").read_bytes() == b"index"
    persona.delete(made["id"])
    persona.delete(back["id"])


def test_an_rvc_model_from_elsewhere_imports(client):
    import zipfile
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("Somebody/Somebody.pth", _model_bytes())
        archive.writestr("Somebody/trained_IVF1_Flat.index", b"t")
        archive.writestr("Somebody/added_IVF1_Flat.index", b"a")
    got = client.post("/api/voices/import", files={"file": ("Somebody.zip", buffer.getvalue(), "application/zip")}).json()
    assert got["name"] == "Somebody" and got["state"] == "ready"
    assert (persona.folder(got["id"]) / "model.index").read_bytes() == b"a"   # the added index is the one conversion uses
    bare = client.post("/api/voices/import", files={"file": ("Bare.pth", _model_bytes(), "application/octet-stream")}).json()
    assert bare["name"] == "Bare" and persona.usable(persona.one(bare["id"]))
    persona.delete(got["id"])
    persona.delete(bare["id"])


INDEX = b"IwFl" + b"\x00" * 40        # a faiss IVF-Flat index's tag, which is what RVC writes


def test_an_rvc_models_loose_files_import_together(client):
    got = client.post("/api/voices/import", files=[("file", ("Loose.pth", _model_bytes(), "application/octet-stream")),
                                                  ("file", ("Loose.index", INDEX, "application/octet-stream"))]).json()
    assert got["name"] == "Loose" and got["state"] == "ready" and got["has_index"] is True
    assert (persona.folder(got["id"]) / "model.index").read_bytes() == INDEX
    persona.delete(got["id"])


def test_a_voice_without_an_index_takes_one_later(client):
    bare = client.post("/api/voices/import", files={"file": ("Bare.pth", _model_bytes(), "application/octet-stream")}).json()
    assert bare["has_index"] is False
    assert client.post(f"/api/voices/{bare['id']}/index", files={"file": ("x.index", b"not an index at all", "x")}).status_code == 400
    assert client.post(f"/api/voices/{bare['id']}/index", files={"file": ("x.txt", INDEX, "x")}).status_code == 400
    got = client.post(f"/api/voices/{bare['id']}/index", files={"file": ("Bare.index", INDEX, "x")}).json()
    assert got["has_index"] is True and (persona.folder(bare["id"]) / "model.index").read_bytes() == INDEX
    untrained = persona.create("Untrained")
    assert client.post(f"/api/voices/{untrained['id']}/index", files={"file": ("u.index", INDEX, "x")}).status_code == 400
    persona.delete(bare["id"])
    persona.delete(untrained["id"])


def test_loose_files_that_do_not_make_one_voice_are_refused(client):
    pth, index = ("file", ("A.pth", _model_bytes(), "x")), ("file", ("A.index", INDEX, "x"))
    before = len(persona.all())
    for files in ([index], [pth, ("file", ("B.pth", _model_bytes(), "x"))], [pth, index, ("file", ("B.index", INDEX, "x"))],
                  [("file", ("A.zip", b"PK", "x")), index], [pth, ("file", ("A.index", b"garbage here", "x"))],
                  [pth, ("file", ("notes.txt", b"hi", "x"))]):
        assert client.post("/api/voices/import", files=files).status_code == 400
    assert len(persona.all()) == before


def test_what_is_not_a_voice_is_refused(client):
    assert client.post("/api/voices/import", files={"file": ("notes.txt", b"hi", "text/plain")}).status_code == 400
    assert client.post("/api/voices/import", files={"file": ("fake.pth", b"not a model", "x")}).status_code == 400
    assert client.post("/api/voices/import", files={"file": ("bad.zip", b"not a zip", "x")}).status_code == 400
    made = persona.create("Untrained")
    assert client.get(f"/api/voices/{made['id']}/export").status_code == 400
    persona.delete(made["id"])


def test_a_voices_sound_settings_are_kept_in_their_steps_and_a_take_can_change_them(client):
    made = client.post("/api/voices", files={"file": ("a.wav", io.BytesIO(b"RIFF...."), "audio/wav")},
                       data={"name": "Settings"}).json()
    assert (made["room"], made["brightness"], made["protect"], made["dynamics"]) == (0.14, 1, 0.33, 0.25)
    changed = client.patch(f"/api/voices/{made['id']}", data={"room": "0.3", "brightness": "0", "protect": "0.1",
                                                               "dynamics": "0.9", "likeness": "0.5"}).json()
    assert (changed["room"], changed["brightness"], changed["protect"], changed["dynamics"]) == (0.28, 0, 0.15, 1.0)
    assert changed["likeness"] == 0.5
    from app.main import _voice_mix
    import json
    assert json.loads(_voice_mix({"room": 0, "brightness": 1, "protect": 0.5, "dynamics": 0.5, "nonsense": 3})) == \
        {"room": 0.0, "brightness": 1, "protect": 0.5, "dynamics": 0.5}
    client.delete(f"/api/voices/{made['id']}")
