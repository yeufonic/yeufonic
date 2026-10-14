"""A take's picture: an LLM describes it, the external image model draws it on white, and the app takes the
white out.  Nothing here reaches a provider: the describing and the drawing are stood in for."""
import asyncio

import numpy as np

from app import artwork, jobs
from app.db import one, set_setting

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
    assert "pure white background" in artwork.drawing_request("A lantern.")
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
