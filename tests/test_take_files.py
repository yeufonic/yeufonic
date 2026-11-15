"""Covers in take files (#60): a take saved with its recording and its rendition, and imported as the kind it was
saved as, linked to its recording, with every setting kept."""
import hashlib
import io
import json
import zipfile

from app import jobs
from app.db import execute, one
from conftest import make_take, tone

ABC = ('X:1\nM:4/4\nL:1/8\nQ:1/4=100\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\nK:C\n'
       '% verse\nV: Vocal\n' + '"C"c4|"Am"A4|"F"F4|"G"G4|' * 4 + '\n')


def a_recording(data_dir, name="demo.wav", seconds=1.0):
    path = tone(data_dir / "sources" / name, seconds)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    execute("INSERT INTO sources(id, title, filename, stored_path, sha256, created_at, duration) "
            "VALUES('src1', 'Paper Boats demo', ?, ?, ?, 0, ?)", (name, str(path), digest, seconds))
    return path, digest


def a_cover(data_dir, **fields):
    audio = tone(data_dir / "takes" / "cover" / "cover.flac", 1.0)
    return make_take(kind="cover", source_id="src1", title="Paper Boats", style="indie folk", lyrics="[verse]\nla",
                     abc=ABC, seed=777, sound_seed=33, target_bpm=96, harmony=2, voice_cues=0, cap_typed=1,
                     max_duration=240, interpretation="loose", audio_path=str(audio), **fields)


def test_the_recipe_names_its_recording_and_nothing_of_this_install(client, data_dir):
    _, digest = a_recording(data_dir)
    data = client.get(f"/api/takes/{a_cover(data_dir)['id']}/recipe").json()
    assert data["take"]["kind"] == "cover"
    assert data["take"]["recording"] == {"title": "Paper Boats demo", "file": "demo.wav", "duration": 1.0, "sha256": digest}
    assert "src1" not in json.dumps(data) and "/sources/" not in json.dumps(data)


def test_saved_with_its_recording_the_zip_holds_it_under_recording(client, data_dir):
    a_recording(data_dir)
    cover = a_cover(data_dir)
    r = client.get(f"/api/takes/{cover['id']}/audio?download=1&format=flac&recipe=1&recording=1")
    assert sorted(zipfile.ZipFile(io.BytesIO(r.content)).namelist()) == [
        "Paper Boats.flac", "Paper Boats.yeufonic.json", "recording/demo.wav"]
    r = client.get(f"/api/takes/{cover['id']}/recipe?recording=1")
    assert sorted(zipfile.ZipFile(io.BytesIO(r.content)).namelist()) == ["Paper Boats.yeufonic.json", "recording/demo.wav"]
    # Without the tick, as before.
    assert client.get(f"/api/takes/{cover['id']}/recipe").headers["content-type"] == "application/json"


def test_a_cover_imported_alone_stays_a_cover_and_keeps_every_setting(client, data_dir):
    a_recording(data_dir)
    cover = a_cover(data_dir)
    data = client.get(f"/api/takes/{cover['id']}/recipe").json()
    execute("DELETE FROM sources")                                   # another PC: the recording is not here
    got = client.post("/api/takes/import", json={"recipe": data}).json()
    row = one("SELECT * FROM takes WHERE id = ?", (got["id"],))
    assert got["kind"] == "cover" and got["recording"] == "missing"
    assert row["kind"] == "cover" and row["source_id"] is None and json.loads(row["recording_ref"])["file"] == "demo.wav"
    for column in ("abc", "seed", "sound_seed", "target_bpm", "harmony", "voice_cues", "cap_typed", "max_duration",
                   "interpretation", "style", "lyrics"):
        assert row[column] == cover[column], column
    # It renders just as the original did.
    assert jobs.build_render_graph(dict(row))["11"]["inputs"] == jobs.build_render_graph(cover)["11"]["inputs"]


def test_a_recording_already_here_is_linked_and_one_imported_later_links_too(client, data_dir):
    path, digest = a_recording(data_dir)
    data = client.get(f"/api/takes/{a_cover(data_dir)['id']}/recipe").json()
    got = client.post("/api/takes/import", json={"recipe": data}).json()
    assert got["recording"] == "linked" and one("SELECT source_id FROM takes WHERE id = ?", (got["id"],))["source_id"] == "src1"
    execute("DELETE FROM sources")
    later = client.post("/api/takes/import", json={"recipe": data}).json()
    assert later["recording"] == "missing"
    up = client.post("/api/sources", files={"file": ("demo.wav", path.read_bytes(), "audio/wav")}).json()
    row = one("SELECT source_id, recording_ref FROM takes WHERE id = ?", (later["id"],))
    assert row["source_id"] == up["id"] and row["recording_ref"] is None


def test_all_three_in_a_zip_arrive_as_the_whole_cover_done(client, data_dir):
    a_recording(data_dir)
    cover = a_cover(data_dir)
    saved = client.get(f"/api/takes/{cover['id']}/audio?download=1&format=flac&recipe=1&recording=1").content
    execute("DELETE FROM sources")
    r = client.post("/api/takes/import-file", files=[("files", ("Paper Boats.zip", saved, "application/zip"))])
    assert r.status_code == 200, r.text
    got = r.json()
    row = one("SELECT * FROM takes WHERE id = ?", (got["id"],))
    source = one("SELECT * FROM sources WHERE id = ?", (row["source_id"],))
    assert got["recording"] == "linked" and got["rendition"] and source and source["filename"] == "demo.wav"
    assert row["kind"] == "cover" and row["status"] == "done" and row["duration"] and row["audio_path"].endswith(".flac")
    assert jobs.build_render_graph(dict(row))["11"]["inputs"] == jobs.build_render_graph(cover)["11"]["inputs"]


def test_a_recipe_chosen_with_its_recording_links_it(client, data_dir):
    path, _ = a_recording(data_dir)
    data = client.get(f"/api/takes/{a_cover(data_dir)['id']}/recipe").json()
    execute("DELETE FROM sources")
    r = client.post("/api/takes/import-file", files=[
        ("files", ("Paper Boats.yeufonic.json", json.dumps(data).encode(), "application/json")),
        ("files", ("demo.wav", path.read_bytes(), "audio/wav"))])
    got = r.json()
    row = one("SELECT * FROM takes WHERE id = ?", (got["id"],))
    assert got["recording"] == "linked" and not got["rendition"] and row["status"] == "planned" and row["source_id"]


def test_a_song_chosen_with_its_audio_arrives_done(client, data_dir):
    song = make_take(title="Copper Fields", abc=ABC, audio_path=str(tone(data_dir / "takes" / "s" / "s.flac", 1.0)))
    data = client.get(f"/api/takes/{song['id']}/recipe").json()
    audio = tone(data_dir / "out.wav", 1.0).read_bytes()
    got = client.post("/api/takes/import-file", files=[
        ("files", ("Copper Fields.yeufonic.json", json.dumps(data).encode(), "application/json")),
        ("files", ("Copper Fields.wav", audio, "audio/wav"))]).json()
    row = one("SELECT * FROM takes WHERE id = ?", (got["id"],))
    assert got["kind"] == "song" and got["rendition"] and row["status"] == "done" and got["recording"] is None


def test_a_take_can_be_given_a_recording_from_the_library(client, data_dir):
    a_recording(data_dir)
    take = make_take(kind="cover", abc=ABC, recording_ref=json.dumps({"file": "demo.wav"}))
    assert client.post(f"/api/takes/{take['id']}/recording", json={"source_id": "src1"}).status_code == 200
    row = one("SELECT source_id, recording_ref FROM takes WHERE id = ?", (take["id"],))
    assert row["source_id"] == "src1" and row["recording_ref"] is None


def test_an_import_with_no_take_file_is_refused(client):
    r = client.post("/api/takes/import-file", files=[("files", ("x.wav", b"RIFF", "audio/wav"))])
    assert r.status_code == 400
