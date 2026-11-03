"""Video both ways: a take saved as an MP4 showing its picture, for messaging apps that send a video as one, and a
video brought in as a recording, of which only the sound is kept."""
import json
import subprocess

from app import artwork

from conftest import make_take, tone


def picture(take_id, size="320x200", alpha=False):
    """A picture for the take, as the app keeps one."""
    path = artwork.png_path(take_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    source = f"color=c=orange:s={size}" + (",format=rgba,colorchannelmixer=aa=0.5" if alpha else "")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", source, "-frames:v", "1", str(path)], check=True)
    return path


def streams(content: bytes, tmp_path) -> dict:
    path = tmp_path / "got.mp4"
    path.write_bytes(content)
    out = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", str(path)],
                         capture_output=True, text=True).stdout
    return json.loads(out)


def test_a_take_with_a_picture_saves_as_a_video_of_the_song(client, tmp_path):
    take = make_take(title="Paper Lanterns", lyrics="[Verse]\nPaper lanterns on the tide",
                     audio_path=str(tone(tmp_path / "take.flac", 3.0)))
    picture(take["id"], size="321x201", alpha=True)   # odd sizes and see-through parts, as an older picture has

    got = client.get(f"/api/takes/{take['id']}/audio?download=1&format=mp4")
    assert got.status_code == 200
    assert got.headers["content-type"] == "video/mp4" and "Paper%20Lanterns.mp4" in got.headers["content-disposition"]
    info = streams(got.content, tmp_path)
    kinds = {s["codec_type"]: s for s in info["streams"]}
    assert kinds["video"]["codec_name"] == "h264" and kinds["video"]["pix_fmt"] == "yuv420p"
    assert (kinds["video"]["width"], kinds["video"]["height"]) == (320, 200)
    assert kinds["audio"]["codec_name"] == "aac"
    assert abs(float(info["format"]["duration"]) - 3.0) < 0.2   # as long as the song, not the picture's loop
    assert info["format"]["tags"]["title"] == "Paper Lanterns"


def test_a_take_inside_another_uses_the_picture_its_card_shows(client, tmp_path):
    outer = make_take(title="Outer", audio_path=str(tone(tmp_path / "outer.flac", 1.0)))
    inner = make_take(title="Inner", parent_id=outer["id"], audio_path=str(tone(tmp_path / "inner.flac", 1.0)))
    picture(outer["id"])
    got = client.get(f"/api/takes/{inner['id']}/audio?download=1&format=mp4")
    assert got.status_code == 200 and got.headers["content-type"] == "video/mp4"


def test_no_picture_means_no_video(client, tmp_path):
    take = make_take(title="Plain", audio_path=str(tone(tmp_path / "plain.flac", 1.0)))
    got = client.get(f"/api/takes/{take['id']}/audio?download=1&format=mp4")
    assert got.status_code == 409 and "no picture" in got.json()["detail"]
    picture(take["id"])
    artwork.plain_path(take["id"]).touch()   # put back to the default background: no picture is shown
    assert client.get(f"/api/takes/{take['id']}/audio?download=1&format=mp4").status_code == 409
    assert client.get(f"/api/takes/{take['id']}/audio?download=1&format=avi").status_code == 400


def test_a_mastered_save_can_be_a_video_too(client, tmp_path):
    take = make_take(title="Mastered", audio_path=str(tone(tmp_path / "m.flac", 1.0)))
    picture(take["id"])
    wav = tone(tmp_path / "rendered.wav", 1.0)
    got = client.post(f"/api/takes/{take['id']}/export-mastered?format=mp4",
                      files={"audio_file": ("master.wav", wav.read_bytes(), "audio/wav")})
    assert got.status_code == 200 and got.headers["content-type"] == "video/mp4"
    assert {s["codec_name"] for s in streams(got.content, tmp_path)["streams"]} == {"h264", "aac"}


def video(path, sound=True, seconds=2.0):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc=s=160x120:d={seconds}"]
    if sound:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-c:a", "aac"]
    subprocess.run(cmd + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-shortest", str(path)], check=True)
    return path


def test_a_video_brought_in_as_a_recording_keeps_only_its_sound(client, tmp_path):
    clip = video(tmp_path / "Garden Party.mp4")
    got = client.post("/api/sources", files={"file": ("Garden Party.mp4", clip.read_bytes(), "video/mp4")})
    assert got.status_code == 200, got.text
    source = got.json()
    assert source["title"] == "Garden Party" and source["stored_path"].endswith(".flac")
    assert abs(source["duration"] - 2.0) < 0.2
    kept = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "stream=codec_name", "-of", "csv=p=0",
                           source["stored_path"]], capture_output=True, text=True).stdout.split()
    assert kept == ["flac"]

    # The same video again is the same recording.
    again = client.post("/api/sources", files={"file": ("Garden Party.mp4", clip.read_bytes(), "video/mp4")}).json()
    assert again["duplicate"] and again["id"] == source["id"]


def test_a_video_with_no_sound_is_refused(client, tmp_path):
    clip = video(tmp_path / "silent.mp4", sound=False)
    got = client.post("/api/sources", files={"file": ("silent.mp4", clip.read_bytes(), "video/mp4")})
    assert got.status_code == 400 and "no sound" in got.json()["detail"]
    assert client.get("/api/sources").json() == [] or all(s["title"] != "silent" for s in client.get("/api/sources").json())
