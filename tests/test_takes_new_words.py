"""Same tune, new words: a copy of a take with its score and seed, singing other words."""
import time

from app.db import execute, one

ABC = "X:1\nM:4/4\nL:1/16\nK:C\nV: Vocal\n" + "|".join(['"C"c4d4e4f4'] * 8) + "|\n"


def a_take(**extra):
    row = {"id": "orig1", "kind": "song", "title": "good1", "style": "pop", "lyrics": "[verse]\nla la",
           "abc": ABC, "mode": "full", "seed": 1747519420, "checkpoint": "x", "status": "done",
           "created_at": time.time(), "max_duration": 120, "interpretation": "tight", "variety": "calm",
           "style_lora": "tidewater_lora.safetensors", "style_lora_model": 0.7, "style_lora_clip": 0.7,
           "favourite": 1, "audio_path": "/data/takes/x.flac", "loudness": -15.0, "sound_seed": 999}
    row.update(extra)
    cols = list(row)
    execute(f"INSERT INTO takes({', '.join(cols)}) VALUES({', '.join('?' * len(cols))})", [row[c] for c in cols])
    return row


def test_new_words_sing_the_same_score_with_the_same_seed(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "_checkpoint", lambda: "x")
    a_take()
    made = client.post("/api/takes/orig1/words", json={"lyrics": "[verse]\r\nda da", "title": "good1"})
    assert made.status_code == 200, made.text
    copy = one("SELECT * FROM takes WHERE id = ?", (made.json()["id"],))
    assert copy["title"] == "good1 · new words", "an unchanged title is marked"
    assert copy["lyrics"] == "[verse]\nda da"
    assert copy["abc"] == ABC, "the same score"
    assert copy["seed"] == 1747519420 and copy["sound_seed"] == 999, "the same seeds"
    assert copy["interpretation"] == "tight" and copy["style_lora_clip"] == 0.7 and copy["max_duration"] == 120
    assert copy["status"] == "queued" and copy["audio_path"] is None and not copy["favourite"]
    original = one("SELECT * FROM takes WHERE id = 'orig1'")
    assert original["lyrics"] == "[verse]\nla la" and original["status"] == "done", "the original is untouched"


def test_new_words_take_a_new_title_and_the_edited_score(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "_checkpoint", lambda: "x")
    a_take()
    edited = ABC.replace('"C"', '"F"')
    made = client.post("/api/takes/orig1/words", json={"lyrics": "[verse]\nda", "title": " good2 ",
                                                        "abc": edited, "interpretation": "loose"})
    copy = one("SELECT * FROM takes WHERE id = ?", (made.json()["id"],))
    assert copy["title"] == "good2" and copy["abc"] == edited and copy["interpretation"] == "loose"
    assert one("SELECT abc FROM takes WHERE id = 'orig1'")["abc"] == ABC


def test_a_new_seed_lets_the_sound_follow_it(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "_checkpoint", lambda: "x")
    a_take()
    made = client.post("/api/takes/orig1/words", json={"lyrics": "[verse]\nda", "seed": 5})
    copy = one("SELECT * FROM takes WHERE id = ?", (made.json()["id"],))
    assert copy["seed"] == 5 and copy["sound_seed"] is None


def test_new_words_need_words_a_score_and_a_song(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "_checkpoint", lambda: "x")
    a_take()
    assert client.post("/api/takes/orig1/words", json={"lyrics": "  \n"}).status_code == 400
    execute("UPDATE takes SET abc = '' WHERE id = 'orig1'")
    assert client.post("/api/takes/orig1/words", json={"lyrics": "la"}).status_code == 400
    execute("UPDATE takes SET abc = ?, kind = 'instrumental' WHERE id = 'orig1'", (ABC,))
    assert client.post("/api/takes/orig1/words", json={"lyrics": "la"}).status_code == 400
    assert client.post("/api/takes/nope/words", json={"lyrics": "la"}).status_code == 404


def test_new_words_take_the_editors_style_cap_mode_and_lora(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "_checkpoint", lambda: "x")
    a_take()
    made = client.post("/api/takes/orig1/words", json={
        "lyrics": "[verse]\nda", "style": " rock ", "max_duration": 90, "mode": "melody",
        "style_lora": "other_lora.safetensors", "style_lora_model": 0.4, "style_lora_clip": 0.9})
    copy = one("SELECT * FROM takes WHERE id = ?", (made.json()["id"],))
    assert (copy["style"], copy["max_duration"], copy["mode"]) == ("rock", 90, "melody")
    assert (copy["style_lora"], copy["style_lora_model"], copy["style_lora_clip"]) == ("other_lora.safetensors", 0.4, 0.9)


def test_rendering_a_score_takes_the_editors_settings(client, monkeypatch):
    """Changing the style LoRA and rendering used to keep the take's old one."""
    from app import main
    monkeypatch.setattr(main, "_checkpoint", lambda: "x")
    a_take()
    got = client.post("/api/takes/orig1/render", json={"style": "folk", "max_duration": 60, "style_lora": ""})
    assert got.status_code == 200, got.text
    take = one("SELECT * FROM takes WHERE id = 'orig1'")
    assert (take["style"], take["max_duration"], take["style_lora"]) == ("folk", 60, None)


def test_a_render_that_leaves_settings_out_keeps_the_takes(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "_checkpoint", lambda: "x")
    a_take()
    client.post("/api/takes/orig1/render", json={"reseed": True})
    take = one("SELECT * FROM takes WHERE id = 'orig1'")
    assert (take["style"], take["max_duration"], take["style_lora"], take["style_lora_model"]) == \
        ("pop", 120, "tidewater_lora.safetensors", 0.7)


def test_a_songs_brief_is_kept_with_it_and_follows_its_new_words(client, monkeypatch):
    """What the lyrics were asked to be about comes back when the take is opened and Write lyrics is pressed."""
    from app import main
    monkeypatch.setattr(main, "_checkpoint", lambda: "x")
    made = client.post("/api/songs", json={"title": "S", "style": "rock", "lyrics": "[Verse]\nhi", "brief": "  a night bus home  "}).json()
    assert made["brief"] == "a night bus home"
    assert client.post("/api/songs", json={"title": "S", "style": "rock", "lyrics": "[Verse]\nhi"}).json()["brief"] is None
    execute("UPDATE takes SET status = 'done', abc = ? WHERE id = ?", (ABC, made["id"]))
    same = client.post(f"/api/takes/{made['id']}/words", json={"lyrics": "[Verse]\nho"}).json()
    assert one("SELECT brief FROM takes WHERE id = ?", (same["id"],))["brief"] == "a night bus home"      # copied
    edited = client.post(f"/api/takes/{made['id']}/words", json={"lyrics": "[Verse]\nhey", "brief": "a night bus to the sea"}).json()
    assert one("SELECT brief FROM takes WHERE id = ?", (edited["id"],))["brief"] == "a night bus to the sea"
    assert one("SELECT brief FROM takes WHERE id = ?", (made["id"],))["brief"] == "a night bus home"         # the original keeps its own
