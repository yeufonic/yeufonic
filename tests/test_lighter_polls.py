"""What the library page polls stays small: the state's options and settings once each, every corpus's progress in
one list, a card's picture as a few kilobytes, and score estimates kept rather than worked out on every poll."""
import numpy as np

from app import artwork, db, score
from app.db import execute
from conftest import make_take
from test_identities import make_folder


def test_the_state_leaves_out_what_the_page_already_holds(client):
    first = client.get("/api/state").json()
    assert first["options"] and first["settings"] and first["options_tag"] and first["settings_tag"]
    again = client.get("/api/state", params={"options_tag": first["options_tag"], "settings_tag": first["settings_tag"]}).json()
    assert again["options"] is None and again["settings"] is None
    assert again["options_tag"] == first["options_tag"] and again["engine"] == first["engine"]
    # a setting changed (here, or in another tab) comes back with a new tag
    assert client.put("/api/settings", json={"key": "takes.cap", "value": "480"}).status_code == 200
    changed = client.get("/api/state", params={"options_tag": first["options_tag"], "settings_tag": first["settings_tag"]}).json()
    assert changed["settings"] and changed["settings_tag"] != first["settings_tag"] and changed["options"] is None
    # a page from before, which sends no tags, gets everything
    assert client.get("/api/state").json()["options"]


def test_the_corpus_list_carries_each_corpuss_progress(client, tmp_path, monkeypatch):
    _, folder = make_folder(tmp_path, monkeypatch)
    made = client.post("/api/identities", json={"name": "Me", "trigger_word": "me", "voice": "male", "folder": str(folder),
                                                "consent": True}).json()
    songs = [s for s in made["songs"] if s["include"]]
    first, second = songs[0]["id"], songs[1]["id"]
    for field in ("vocals_state", "score_state", "lyrics_state", "style_state"):
        execute(f"UPDATE identity_songs SET {field} = 'done' WHERE id = ?", (first,))
    execute("UPDATE identity_songs SET vocals_state = 'running' WHERE id = ?", (second,))
    listed = next(c for c in client.get("/api/identities").json() if c["id"] == made["id"])
    progress = listed["progress"]
    assert progress == {"done": 1, "total": len(songs), "failed": 0, "started": True, "busy": True}


def test_a_cards_picture_comes_small_and_is_kept_by_the_browser(client):
    take = make_take(title="Lantern")
    artwork.art_dir().mkdir(parents=True, exist_ok=True)
    rgba = np.zeros((1024, 1024, 4), np.uint8)
    rgba[..., 0] = np.linspace(0, 255, 1024, dtype=np.uint8)
    rgba[..., 3] = 255
    rgba[:200, :200, 3] = 0                                        # some of it clear, as a cut-out drawing is
    artwork.png_path(take["id"]).write_bytes(artwork.png_bytes(rgba))
    url = artwork.url_for(take["id"])
    whole = client.get(url)
    small = client.get(url + "&thumb=1")
    assert whole.status_code == small.status_code == 200
    assert small.headers["content-type"] in ("image/webp", "image/png") and len(small.content) < len(whole.content) / 10
    assert "immutable" in small.headers["cache-control"] and "immutable" in whole.headers["cache-control"]
    pixels = artwork.decode(small.content)
    assert max(pixels.shape[:2]) <= artwork.THUMB_SIZE and pixels[0, 0, 3] < 16 and pixels[-1, -1, 3] > 240
    # made once, then served as it is, until the picture changes
    assert artwork.thumbnail(take["id"])[0].read_bytes() == small.content
    assert "no-cache" in client.get(f"/api/takes/{take['id']}/art.png").headers["cache-control"]   # no time: not kept
    artwork.forget(take["id"])
    assert not artwork.thumb_path(take["id"]).exists()


def test_a_score_is_measured_once():
    abc = "X:1\nM:4/4\nL:1/4\nQ:1/4=120\nV: Vocal\nK:C\n% verse\n" + "c4|" * 16 + "\n% chorus\n" + "c4|" * 8 + "\n"
    first = score.estimate(abc)
    first["seconds"] = -1                                          # a caller's copy: the kept one is not touched
    hits = score._estimate.cache_info().hits
    assert score.estimate(abc)["seconds"] == 48.0
    assert score._estimate.cache_info().hits == hits + 1
    assert score.last_section_start(abc) == 32.0 and score.last_section_start(abc) == 32.0


def test_a_write_moves_the_databases_generation():
    before = db.generation()
    execute("UPDATE takes SET title = title WHERE id = 'nothing'")      # changed nothing
    assert db.generation() == before
    take = make_take(title="One")
    execute("UPDATE takes SET title = 'Two' WHERE id = ?", (take["id"],))
    assert db.generation() > before
