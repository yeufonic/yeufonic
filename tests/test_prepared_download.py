"""A download made in the background (Save): started, asked after with its progress, then fetched once."""
import io
import time
import zipfile

from conftest import make_take, tone


def wait_done(client, token):
    for _ in range(100):
        state = client.get(f"/api/downloads/{token}").json()
        if state["state"] != "working":
            return state
        time.sleep(0.05)
    raise AssertionError("the download never finished")


def test_a_prepared_mp3_reports_progress_and_is_fetched_once(client, data_dir):
    audio = tone(data_dir / "takes" / "a" / "a.flac", 2.0)
    take = make_take(title="Copper Fields", audio_path=str(audio), duration=2.0)
    token = client.post(f"/api/takes/{take['id']}/prepare-download", json={"format": "mp3"}).json()["token"]
    state = wait_done(client, token)
    assert state["state"] == "done" and state["progress"] == 1.0
    r = client.get(f"/api/downloads/{token}/file")
    assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg" and len(r.content) > 1000
    assert "Copper%20Fields.mp3" in r.headers["content-disposition"]
    assert client.get(f"/api/downloads/{token}/file").status_code == 404        # once only


def test_with_the_recipe_it_comes_as_one_zip(client, data_dir):
    audio = tone(data_dir / "takes" / "b" / "b.flac", 1.0)
    take = make_take(title="Copper Fields", audio_path=str(audio), abc="X:1\nK:C\nC|")
    token = client.post(f"/api/takes/{take['id']}/prepare-download", json={"format": "wav", "recipe": True}).json()["token"]
    wait_done(client, token)
    names = zipfile.ZipFile(io.BytesIO(client.get(f"/api/downloads/{token}/file").content)).namelist()
    assert sorted(names) == ["Copper Fields.wav", "Copper Fields.yeufonic.json"]


def test_what_cannot_be_made_is_refused_at_once(client, data_dir):
    take = make_take(title="No audio")
    assert client.post(f"/api/takes/{take['id']}/prepare-download", json={"format": "mp3"}).status_code == 404
    audio = tone(data_dir / "takes" / "c" / "c.flac", 1.0)
    pictureless = make_take(audio_path=str(audio))
    assert client.post(f"/api/takes/{pictureless['id']}/prepare-download", json={"format": "mp4"}).status_code == 409
    assert client.post(f"/api/takes/{pictureless['id']}/prepare-download", json={"format": "ogg"}).status_code == 400
    assert client.get("/api/downloads/nosuchtoken").status_code == 404


def test_ffmpeg_progress_is_read_from_its_own_lines(data_dir):
    from app import library
    src = tone(data_dir / "p.flac", 2.0)
    seen = []
    library.tagged_copy(src, data_dir / "p.mp3", "mp3", ["-c:a", "libmp3lame", "-b:a", "128k"], "T", None,
                        progress=seen.append)
    assert seen and seen[-1] > 0.9 and all(0 <= f <= 1 for f in seen)
