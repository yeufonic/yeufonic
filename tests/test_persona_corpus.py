"""A voice from a corpus: a collage of several songs, and regenerating it rebuilds that collage."""
import pathlib

from app import jobs, persona


class FakeEngine:
    """Stands in for the engine, writing the token file where the real one would."""

    def __init__(self):
        self.graphs = []

    async def upload(self, filename, data):
        return {"name": filename}

    async def submit(self, graph):
        self.graphs.append(graph)
        out = pathlib.Path(graph["1"]["inputs"]["out"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"tokens")
        return "p1"

    async def history(self, prompt_id):
        return {"status": {"status_str": "success"}}


def test_a_corpus_voice_records_where_it_came_from(client, monkeypatch):
    engine = FakeEngine()
    monkeypatch.setattr(jobs, "ENGINE", engine)
    monkeypatch.setattr(jobs, "PERSONA_POLL_SECONDS", 0.0)
    monkeypatch.setattr(jobs, "collage_from_corpus",
                        lambda identity_id, seconds=12.0, songs=4: _collage(identity_id))
    corpus = client.post("/api/identities", json={"name": "A corpus"}).json() if False else None
    # a corpus the fake collage can name, without building one
    from app.db import execute
    execute("INSERT OR IGNORE INTO identities (id, name, trigger_word, folder, created_at) VALUES (?,?,?,?,?)",
            ("corpus1", "A corpus", "trig", "/tmp", 0.0))
    made = client.post("/api/voices/from-identity",
                       data={"identity_id": "corpus1", "name": "From a corpus"}).json()
    assert made["name"] == "From a corpus"
    assert made["origin_identity"] == "corpus1"
    persona.delete(made["id"])


def test_regenerating_a_corpus_voice_rebuilds_the_collage(client, monkeypatch):
    monkeypatch.setattr(jobs, "PERSONA_POLL_SECONDS", 0.0)
    monkeypatch.setattr(jobs, "ENGINE", FakeEngine())
    rebuilt = []
    monkeypatch.setattr(jobs, "collage_from_corpus",
                        lambda identity_id, seconds=12.0, songs=4: rebuilt.append(identity_id) or _collage(identity_id))
    from app.db import execute
    execute("INSERT OR IGNORE INTO identities (id, name, trigger_word, folder, created_at) VALUES (?,?,?,?,?)",
            ("corpus2", "Another corpus", "trig", "/tmp", 0.0))
    made = client.post("/api/voices/from-identity", data={"identity_id": "corpus2"}).json()
    assert client.post(f"/api/voices/{made['id']}/regenerate").json()["queued"] is True
    assert rebuilt == ["corpus2", "corpus2"]      # once to make it, once to regenerate
    persona.delete(made["id"])


def test_a_corpus_voice_with_no_recording_says_so(client, monkeypatch):
    response = client.post("/api/voices/from-identity", data={"identity_id": "nope"})
    assert response.status_code == 404


def _collage(identity_id: str) -> pathlib.Path:
    from app import config
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    path = config.WORK_DIR / f"collage-{identity_id}.wav"
    path.write_bytes(b"RIFF....")
    return path


def test_an_excerpt_is_cut_from_a_real_vocal_file(tmp_path):
    """The collage's excerpts, on real FLAC and WAV files: the corpus tests above stand the collage in, so this is
    the one that runs ffmpeg and reads the length."""
    from conftest import tone

    for name in ("vocals.flac", "vocals.wav"):
        src = tone(tmp_path / name, seconds=6.0)
        out = tmp_path / f"part-{name}.wav"
        assert jobs._excerpt(src, out, 3.0)
        assert 2.5 < (jobs.audio_duration(out) or 0) < 3.5
