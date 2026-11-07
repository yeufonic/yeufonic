"""The persona routes: create from a recording, list, rename, retune the prefix, delete."""
import io

from app import jobs, persona


async def _stub_tokenise(persona_id):
    persona.STUBBED.append(persona_id)
    return {"tokens_path": ""}


def test_the_persona_routes(client, monkeypatch):
    monkeypatch.setattr(persona, "STUBBED", [], raising=False)
    monkeypatch.setattr(jobs, "tokenise_persona", _stub_tokenise)
    made = client.post("/api/voices",
                       files={"file": ("my-voice.wav", io.BytesIO(b"RIFF...."), "audio/wav")},
                       data={"name": "My voice", "prefix_seconds": "36"}).json()
    assert made["name"] == "My voice" and made["prefix_seconds"] == 36.0
    assert made["state"] == "preparing"

    listed = client.get("/api/voices").json()
    assert [p["id"] for p in listed] == [made["id"]]

    renamed = client.patch(f"/api/voices/{made['id']}",
                           data={"name": "Mine", "prefix_seconds": "60"}).json()
    assert renamed["name"] == "Mine" and renamed["prefix_seconds"] == 60.0

    assert client.post(f"/api/voices/{made['id']}/tokenise").json()["queued"] is True

    assert client.delete(f"/api/voices/{made['id']}").json()["deleted"] == made["id"]
    assert client.get("/api/voices").json() == []


def test_a_non_audio_upload_is_refused(client):
    response = client.post("/api/voices",
                           files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")})
    assert response.status_code == 400


def test_a_missing_persona_is_404(client):
    assert client.patch("/api/voices/nope", data={"name": "x"}).status_code == 404
    assert client.delete("/api/voices/nope").status_code == 404
