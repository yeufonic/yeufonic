"""A take's recipe as a file (#58): saved on its own or beside the audio, and imported as a new take."""
import io
import json
import zipfile

from app import config
from app.db import one, execute
from conftest import make_take, tone

ABC = ('X:1\nM:4/4\nL:1/8\nQ:1/4=100\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\nK:C\n'
       '% verse\nV: Vocal\n' + '"C"c4|"Am"A4|"F"F4|"G"G4|' * 4 + '\n')


def full_take(**fields):
    return make_take(**{
        "title": "Harbour Lights", "style": "indie folk, warm vocal", "lyrics": "[verse]\nLights along the wall",
        "abc": ABC, "seed": 4242, "sound_seed": 77, "max_duration": 240, "cap_typed": 1, "variety": "calm",
        "harmony": 2, "interpretation": "tight", "realaudio": 1, "style_lora": "bright-pop.safetensors",
        "style_lora_model": 0.6, "style_lora_clip": 0.4, "voice_lora": "my-voice.safetensors",
        "voice_lora_strength": 0.9, "voice_lora_clip": 0.3, "sampler_steps": 40, "avoid": "drums",
        "target_key": "D", "target_bpm": 96, "fade_out_seconds": 5.0, "follow_structure": 1, "voice_cues": 0,
        "fx_chain": json.dumps({"eq": {"on": True}}), "engine": "yue2cpp", "identity_id": "corpus123",
        "space_id": "default", "audio_path": "/data/takes/harbour/harbour.flac", **fields})


def test_the_recipe_holds_the_take_and_nothing_of_this_install(client):
    take = full_take()
    r = client.get(f"/api/takes/{take['id']}/recipe")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    assert 'filename="Harbour Lights.yeufonic.json"' in r.headers["content-disposition"]
    data = r.json()
    assert data["format"] == "yeufonic-take" and data["version"] == 1
    assert data["from"]["engine"] == "yue2cpp"
    t = data["take"]
    assert t["score"] == ABC and t["seed"] == 4242 and t["sound_seed"] == 77 and t["length_cap"] == 240
    assert t["style_lora"] == "bright-pop.safetensors" and t["style_lora_sound"] == 0.6 and t["style_lora_planner"] == 0.4
    assert t["voice_lora"] == "my-voice.safetensors" and t["sampler_steps"] == 40 and t["target_bpm"] == 96
    assert t["production_polish"] is True and t["mastering"] == {"eq": {"on": True}}
    text = r.text
    for private in (take["id"], "corpus123", "/data/takes", "default"):
        assert private not in text                     # no ids, paths or spaces of this install


def test_an_imported_recipe_is_a_take_ready_to_render_with_the_same_settings(client):
    take = full_take()
    data = client.get(f"/api/takes/{take['id']}/recipe").json()
    space = client.post("/api/spaces", json={"name": "Shared"}).json()["id"]
    r = client.post("/api/takes/import", json={"recipe": data, "space_id": space})
    assert r.status_code == 200, r.text
    got = r.json()
    assert got["title"] == "Harbour Lights" and sorted(got["missing_loras"]) == ["bright-pop.safetensors", "my-voice.safetensors"]
    row = one("SELECT * FROM takes WHERE id = ?", (got["id"],))
    assert row["status"] == "planned" and row["space_id"] == space and row["audio_path"] is None
    for column in ("abc", "style", "lyrics", "seed", "sound_seed", "max_duration", "variety", "harmony", "interpretation",
                   "style_lora", "style_lora_model", "style_lora_clip", "voice_lora", "voice_lora_strength",
                   "sampler_steps", "avoid", "target_key", "target_bpm", "fade_out_seconds", "follow_structure",
                   "voice_cues", "fx_chain"):
        assert row[column] == take[column], column
    assert row["engine"] is None and row["identity_id"] is None and row["checkpoint"] == config.CHECKPOINT


def test_a_cover_arrives_as_a_song_with_its_score(client):
    execute("INSERT INTO sources(id, title, filename, stored_path, sha256, created_at) VALUES('src1', 'My demo', "
            "'demo.wav', '/data/sources/demo.wav', 'x', 0)")
    cover = full_take(kind="cover", source_id="src1", style_lora=None, voice_lora=None)
    data = client.get(f"/api/takes/{cover['id']}/recipe").json()
    assert data["take"]["kind"] == "cover" and data["take"]["recording"] == "not included"
    assert "src1" not in json.dumps(data) and "demo.wav" not in json.dumps(data)
    got = client.post("/api/takes/import", json={"recipe": data}).json()
    row = one("SELECT * FROM takes WHERE id = ?", (got["id"],))
    assert got["was_cover"] and row["kind"] == "song" and row["source_id"] is None and row["abc"] == ABC
    # What belonged to the recording is left behind, so a new plan from it starts as a song from a prompt does.
    assert row["target_bpm"] is None and row["harmony"] == 1 and row["voice_cues"] == 1 and row["cap_typed"] == 0
    assert row["target_key"] == cover["target_key"] and row["style"] == cover["style"]      # the rest is kept


def test_a_file_that_is_not_a_recipe_or_is_from_a_later_yeufonic_is_refused(client):
    assert client.post("/api/takes/import", json={"recipe": {"hello": 1}}).status_code == 400
    data = client.get(f"/api/takes/{full_take()['id']}/recipe").json()
    later = {**data, "version": 99}
    r = client.post("/api/takes/import", json={"recipe": later})
    assert r.status_code == 400 and "later Yeufonic" in r.json()["detail"]
    no_score = {**data, "take": {**data["take"], "score": ""}}
    assert client.post("/api/takes/import", json={"recipe": no_score}).status_code == 400
    bad = {**data, "take": {**data["take"], "seed": -5}}
    assert client.post("/api/takes/import", json={"recipe": bad}).status_code == 400


def test_the_audio_and_the_recipe_come_as_one_zip(client, data_dir):
    audio = tone(data_dir / "takes" / "harbour" / "harbour.flac", 1.0)
    take = full_take(audio_path=str(audio))
    r = client.get(f"/api/takes/{take['id']}/audio?download=1&format=mp3&recipe=1")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
    assert sorted(names) == ["Harbour Lights.mp3", "Harbour Lights.yeufonic.json"]
    plain = client.get(f"/api/takes/{take['id']}/audio?download=1&format=mp3")
    assert plain.headers["content-type"] == "audio/mpeg"
