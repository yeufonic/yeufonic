"""A take's picture: an LLM describes it, the external image model draws it on white, and the app takes the
white out.  Nothing here reaches a provider: the describing and the drawing are stood in for."""
import asyncio

import numpy as np

from app import artwork, jobs
from app.db import execute, one, set_setting

from conftest import make_take

LYRICS = "[verse]\nLanterns on the water\nCarry what we said\n\n[chorus]\n\nAnd the river keeps it\n[male voice]\nAll night long"


def a_take(**fields):
    return make_take(**{"status": "done", "title": "River lights", "style": "folk, warm, female vocal", "lyrics": LYRICS, **fields})


def drawing(width=160, height=100):
    """White, with a dark ring whose middle is white too: a drawing with white inside it."""
    img = np.full((height, width, 3), 255, np.uint8)
    yy, xx = np.mgrid[0:height, 0:width]
    r = np.hypot(yy - height / 2, xx - width / 2)
    img[(r < 22) & (r > 12)] = (30, 30, 90)
    img[(r >= 22) & (r < 23)] = (140, 140, 170)     # the outline softened into the white
    return img


def as_file(rgb):
    return artwork.png_bytes(np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)]))


# ------------------------------------------------------------------ the words
def test_the_opening_words_are_the_sung_lines_only():
    assert artwork.opening_words(LYRICS) == ["Lanterns on the water", "Carry what we said", "And the river keeps it", "All night long"]
    assert artwork.opening_words(LYRICS, 2) == ["Lanterns on the water", "Carry what we said"]


def test_a_takes_title_loses_what_was_done_to_it():
    assert artwork.song_title("River lights · sung again") == "River lights"
    assert artwork.song_title("") == "Untitled"


def test_the_description_is_asked_without_real_names():
    asked = artwork.description_request({"title": "River lights · step 400", "style": "folk, warm", "lyrics": LYRICS})
    assert "Song title: River lights\n" in asked and "Style: folk, warm" in asked and "Carry what we said" in asked
    assert "Never name a real band, artist or person" in asked
    assert "no words in it at all" in asked and "lettering" in asked      # it lies behind the card's own words
    drawn = artwork.drawing_request("A lantern.")
    assert "pure white background" in drawn and "No text of any kind" in drawn
    assert artwork.tidy_description('Here is the prompt:\n"A lantern on a river."') == "A lantern on a river."


def test_a_refusal_says_what_usually_causes_it():
    try:
        artwork._gemini_image({"candidates": [{"finishReason": "IMAGE_OTHER"}]})
    except RuntimeError as exc:
        assert "real band's or person's name" in str(exc)
    else:
        raise AssertionError("no error")


# ------------------------------------------------------------------ the background
def test_the_white_round_the_drawing_comes_out_and_the_white_inside_it_stays():
    rgb = drawing()
    out = artwork.decode(artwork.cut_out(as_file(rgb)))
    alpha = out[..., 3]
    h, w = out.shape[:2]
    assert (h, w) == (45 + 2 * artwork.MARGIN, 45 + 2 * artwork.MARGIN)   # trimmed to the drawing and its margin
    assert alpha[0, 0] == 0 and alpha[h // 2, artwork.MARGIN + 6] == 255          # a corner clear, the ring solid
    assert alpha[h // 2, w // 2] == 255 and out[h // 2, w // 2, 0] == 255         # the white inside the ring kept
    edge = alpha[h // 2, artwork.MARGIN]                                          # the softened outline: part clear
    assert 0 < edge < 255
    assert out[h // 2, artwork.MARGIN, 0] < 140                                   # and the white taken out of its colour


def test_a_picture_drawn_transparent_is_kept_as_it_is():
    rgba = np.zeros((80, 120, 4), np.uint8)
    rgba[20:40, 20:60] = (200, 50, 50, 255)
    out = artwork.decode(artwork.cut_out(artwork.png_bytes(rgba)))
    assert out.shape[:2] == (20 + 2 * artwork.MARGIN, 40 + 2 * artwork.MARGIN) and out[..., 3].min() == 0


def test_the_png_written_reads_back_the_same():
    rgba = np.random.default_rng(1).integers(0, 256, (17, 23, 4), dtype=np.uint8)
    assert (artwork.decode(artwork.png_bytes(rgba)) == rgba).all()


# ------------------------------------------------------------------ the job and the routes
def test_described_by_gemma_it_waits_in_the_gpu_lane(client):
    take = a_take()
    set_setting("llm.provider", "local")
    reply = client.post(f"/api/takes/{take['id']}/art")
    assert reply.status_code == 200 and reply.json()["state"] == "queued"
    assert jobs.QUEUE._queue[-1] == {"kind": "art", "id": take["id"]}
    assert client.post(f"/api/takes/{take['id']}/art").status_code == 409
    assert client.get(f"/api/takes/{take['id']}/art").json()["state"] == "queued"


def test_it_cannot_start_without_the_provider_it_draws_with(client):
    take = a_take()
    set_setting("llm.api_url", "https://generativelanguage.googleapis.com")
    reply = client.post(f"/api/takes/{take['id']}/art")
    assert reply.status_code == 400 and "key" in reply.json()["detail"]
    assert client.get(f"/api/takes/{take['id']}/art").json()["state"] == "none"


def test_the_job_keeps_the_picture_and_its_description(client, monkeypatch):
    take = a_take()
    monkeypatch.setattr(artwork, "words_by_engine", lambda: False)

    async def describe(record):
        assert record["id"] == take["id"]
        return "A ring on white."

    async def draw(description):
        return as_file(drawing())

    monkeypatch.setattr(artwork, "describe_external", describe)
    monkeypatch.setattr(artwork, "draw", draw)
    asyncio.run(jobs.run_art(take["id"]))
    got = client.get(f"/api/takes/{take['id']}/art").json()
    assert got["state"] == "ready" and got["has"] and got["has_drawn"] and got["words"].startswith("A ring on white.")
    picture = client.get(f"/api/takes/{take['id']}/art.png")
    assert picture.status_code == 200 and picture.headers["content-type"] == "image/png"
    assert artwork.decode(picture.content)[0, 0, 3] == 0
    assert artwork.decode(client.get(f"/api/takes/{take['id']}/art.png?drawn=1").content)[0, 0, 3] == 255
    client.delete(f"/api/takes/{take['id']}")
    assert not artwork.png_path(take["id"]).exists() and not artwork.words_path(take["id"]).exists()


def test_a_failed_picture_says_why_and_leaves_the_take_alone(client, monkeypatch):
    take = a_take()
    monkeypatch.setattr(artwork, "words_by_engine", lambda: False)

    async def describe(record):
        raise RuntimeError("the LLM is away")

    monkeypatch.setattr(artwork, "describe_external", describe)
    asyncio.run(jobs.run_art(take["id"]))
    got = client.get(f"/api/takes/{take['id']}/art").json()
    assert got["state"] == "failed" and "away" in got["error"] and not got["has"]
    assert one("SELECT status FROM takes WHERE id = ?", (take["id"],))["status"] == "done"
    jobs.fail("art", take["id"], "boom")
    assert one("SELECT status, error FROM takes WHERE id = ?", (take["id"],))["status"] == "done"
    assert client.get(f"/api/takes/{take['id']}/art").json()["error"] == "boom"


# ------------------------------------------------------------------ made by itself
def external(key="a-key"):
    set_setting("llm.provider", "external")
    set_setting("llm.api_url", "https://generativelanguage.googleapis.com")
    if key:
        set_setting("llm.api_key", key)


def started(monkeypatch):
    calls = []
    monkeypatch.setattr(jobs, "start_art", lambda take_id: calls.append(take_id))
    return calls


def test_a_new_take_gets_its_picture_by_itself_where_the_provider_can_draw(client, monkeypatch):
    calls = started(monkeypatch)
    take, inner = a_take(), a_take()
    external()
    jobs.art_for_new_take(take["id"])
    execute("UPDATE takes SET parent_id = ? WHERE id = ?", (take["id"], inner["id"]))
    jobs.art_for_new_take(inner["id"])                 # inside another: shows that one's
    assert calls == [take["id"]]
    set_setting("art.auto", "off")
    jobs.art_for_new_take(a_take()["id"])
    assert calls == [take["id"]]


def test_no_picture_is_tried_without_a_provider_to_draw_it(client, monkeypatch):
    calls = started(monkeypatch)
    jobs.art_for_new_take(a_take()["id"])             # the defaults: local Gemma, no key
    external(key="")
    jobs.art_for_new_take(a_take()["id"])
    assert calls == []


def test_every_new_take_is_queued_through_the_picture_starter(client, monkeypatch):
    seen = []
    monkeypatch.setattr(jobs, "art_for_new_take", lambda take_id: seen.append(take_id))
    from test_score import GOOD
    take = make_take(status="done", title="River lights", abc=GOOD, seed=111)
    made = client.post(f"/api/takes/{take['id']}/tries", json={"count": 2}).json()["created"]
    assert seen == [m["id"] for m in made]
    import re
    from pathlib import Path
    main = (Path(__file__).resolve().parent.parent / "app" / "main.py").read_text(encoding="utf-8")
    after_startup = main[main.index("async def queue_take("):]
    assert not re.search(r'QUEUE\.put\(\{"kind": "(render|plan)"', after_startup)


def test_the_list_says_where_each_takes_picture_is(client):
    take, inner, bare = a_take(), a_take(), a_take(title="Lantern")
    execute("UPDATE takes SET parent_id = ? WHERE id = ?", (take["id"], inner["id"]))
    artwork.art_dir().mkdir(parents=True, exist_ok=True)
    artwork.png_path(take["id"]).write_bytes(as_file(drawing()))
    listed = {t["id"]: t for t in client.get("/api/takes", params={"space_id": "default"}).json()}
    assert listed[take["id"]]["art"].startswith(f"/api/takes/{take['id']}/art.png?v=")
    assert listed[bare["id"]]["art"] is None
    inside = client.get("/api/takes", params={"inside": take["id"]}).json()
    assert inside[0]["art"].startswith(f"/api/takes/{take['id']}/art.png")   # the take it is inside


def test_back_to_the_default_background_stays_there(client, monkeypatch):
    take, inner = a_take(), a_take()
    execute("UPDATE takes SET parent_id = ? WHERE id = ?", (take["id"], inner["id"]))
    artwork.art_dir().mkdir(parents=True, exist_ok=True)
    artwork.png_path(take["id"]).write_bytes(as_file(drawing()))
    got = client.delete(f"/api/takes/{inner['id']}/art").json()      # the take inside: no longer shows its mother's
    assert got["plain"] and not got["has"]
    assert artwork.url_for(inner["id"], take["id"]) is None and artwork.url_for(take["id"]) is not None
    assert client.delete(f"/api/takes/{take['id']}/art").json()["plain"]
    assert not artwork.png_path(take["id"]).exists() and artwork.url_for(take["id"]) is None
    calls = started(monkeypatch)
    external()
    jobs.art_for_new_take(take["id"])                                # never made again by itself
    assert calls == []
    monkeypatch.setattr(artwork, "words_by_engine", lambda: False)

    async def describe(record):
        return "A ring on white."

    async def draw(description):
        return as_file(drawing())

    monkeypatch.setattr(artwork, "describe_external", describe)
    monkeypatch.setattr(artwork, "draw", draw)
    asyncio.run(jobs.run_art(take["id"]))                            # asked for again: made, and the mark gone
    assert artwork.info(take["id"])["has"] and not artwork.info(take["id"])["plain"]


def test_the_page_is_told_whether_pictures_are_made(client):
    assert client.get("/api/state").json()["pictures"] is False
    external()
    assert client.get("/api/state").json()["pictures"] is True
