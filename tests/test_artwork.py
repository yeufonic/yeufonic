"""A take's picture: an LLM describes it, the external image model draws it on white, and the app takes the
white out.  Nothing here reaches a provider: the describing and the drawing are stood in for."""
import asyncio
import time

import numpy as np

from app import artwork, config, jobs
from app.db import execute, one, set_setting

from conftest import make_take

LYRICS = "[verse]\nLanterns on the water\nCarry what we said\n\n[chorus]\n\nAnd the river keeps it\n[male voice]\nAll night long"


import pytest


@pytest.fixture(autouse=True)
def fresh_memory():
    """What the module remembers (the provider check, pictures being made) starts empty in every test."""
    artwork._EXTERNAL.clear()
    artwork.STATE.clear()
    artwork.clear_failures()
    yield
    artwork._EXTERNAL.clear()
    artwork.STATE.clear()
    artwork.clear_failures()


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
def test_a_takes_title_loses_what_was_done_to_it():
    assert artwork.song_title("River lights · sung again") == "River lights"
    assert artwork.song_title("") == "Untitled"


def test_the_description_is_asked_without_real_names():
    asked = artwork.description_request({"title": "River lights · step 400", "style": "folk, warm", "lyrics": LYRICS})
    assert "Song title: River lights\n" in asked and "Song style: folk, warm" in asked and "Carry what we said" in asked
    drawn = artwork.drawing_request("A lantern.")
    assert "Hipgnosis" in drawn and "album cover" in drawn
    assert artwork.tidy_description('Here is the prompt:\n"A lantern on a river."') == "A lantern on a river."
    assert artwork.tidy_description("**Image Prompt:**\n\nA lantern on a river.") == "A lantern on a river."


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
def test_described_by_gemma_it_waits_in_the_gpu_lane(client, monkeypatch):
    monkeypatch.setattr(artwork, "engine_options", lambda: {"lyrics": True})
    take = a_take()
    external()
    set_setting("art.words", "local")
    reply = client.post(f"/api/takes/{take['id']}/art")
    assert reply.status_code == 200 and reply.json()["state"] == "queued"
    assert jobs.ART_WAITING[-1] == take["id"]
    assert client.post(f"/api/takes/{take['id']}/art").status_code == 409
    assert client.get(f"/api/takes/{take['id']}/art").json()["state"] == "queued"


def test_it_cannot_start_without_something_to_draw_it(client):
    take = a_take()
    set_setting("llm.api_url", "https://generativelanguage.googleapis.com")
    reply = client.post(f"/api/takes/{take['id']}/art")
    assert reply.status_code == 400 and "FLUX.2 klein was not installed" in reply.json()["detail"]
    assert client.get(f"/api/takes/{take['id']}/art").json()["state"] == "none"


def test_the_job_keeps_the_picture_and_its_description(client, monkeypatch):
    take = a_take()
    monkeypatch.setattr(artwork, "describer", lambda: "external")
    monkeypatch.setattr(artwork, "drawer", lambda: "external")

    async def describe(record, *args, **kwargs):
        assert record["id"] == take["id"]
        return "A ring on white."

    async def draw(description, as_given=False):
        return as_file(drawing())

    monkeypatch.setattr(artwork, "describe_external", describe)
    monkeypatch.setattr(artwork, "draw", draw)
    asyncio.run(jobs.run_art(take["id"]))
    got = client.get(f"/api/takes/{take['id']}/art").json()
    assert got["state"] == "ready" and got["has"] and got["has_drawn"] and "A ring on white." in got["words"]
    picture = client.get(f"/api/takes/{take['id']}/art.png")
    assert picture.status_code == 200 and picture.headers["content-type"] == "image/png"
    assert artwork.decode(picture.content)[0, 0, 3] == 0
    assert artwork.decode(client.get(f"/api/takes/{take['id']}/art.png?drawn=1").content)[0, 0, 3] == 255
    client.delete(f"/api/takes/{take['id']}")
    assert not artwork.png_path(take["id"]).exists() and not artwork.words_path(take["id"]).exists()


def test_the_log_says_how_the_picture_was_made_and_how_long_it_took(client, monkeypatch, caplog):
    take = a_take()
    monkeypatch.setattr(artwork, "describer", lambda: "take")
    monkeypatch.setattr(artwork, "drawer", lambda: "external")
    monkeypatch.setattr(artwork, "image_model", lambda: "an-image-model")

    async def draw(description, as_given=False):
        return as_file(drawing())

    monkeypatch.setattr(artwork, "draw", draw)
    with caplog.at_level("INFO", logger="yue2.jobs"):
        asyncio.run(jobs.run_art(take["id"]))
    ready = [r.getMessage() for r in caplog.records if "is ready" in r.getMessage()]
    assert len(ready) == 1
    assert "Method: described from its own title, style and words, drawn by an-image-model." in ready[0]
    assert "Duration: 0 seconds (describing 0 seconds, drawing 0 seconds)." in ready[0]


def test_times_in_the_log_read_as_words():
    assert jobs.took(0.4) == "0 seconds" and jobs.took(1) == "1 second" and jobs.took(10.4) == "10 seconds"
    assert jobs.took(60) == "1 minute" and jobs.took(96) == "1 minute 36 seconds" and jobs.took(121) == "2 minutes 1 second"


def test_a_failed_picture_says_why_and_leaves_the_take_alone(client, monkeypatch):
    take = a_take()
    monkeypatch.setattr(artwork, "describer", lambda: "take")
    monkeypatch.setattr(artwork, "drawer", lambda: "external")

    async def draw(description, as_given=False):
        raise RuntimeError("the image model is away")

    monkeypatch.setattr(artwork, "draw", draw)
    asyncio.run(jobs.run_art(take["id"]))
    got = client.get(f"/api/takes/{take['id']}/art").json()
    assert got["state"] == "failed" and "away" in got["error"] and not got["has"]
    assert one("SELECT status FROM takes WHERE id = ?", (take["id"],))["status"] == "done"
    jobs.fail("art", take["id"], "boom")
    assert one("SELECT status, error FROM takes WHERE id = ?", (take["id"],))["status"] == "done"
    assert client.get(f"/api/takes/{take['id']}/art").json()["error"] == "boom"


# ------------------------------------------------------------------ made by itself
def external(key="a-key", draws=True):
    """An external provider set up; `draws`: its model list has the image model (as the background check found)."""
    set_setting("llm.provider", "external")
    set_setting("llm.api_url", "https://generativelanguage.googleapis.com")
    if key:
        set_setting("llm.api_key", key)
        artwork._EXTERNAL[artwork._external_key()] = (draws, time.time())


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


def test_every_new_take_waits_for_render_before_picture_starts(client, monkeypatch):
    seen = []
    monkeypatch.setattr(jobs, "art_for_new_take", lambda take_id: seen.append(take_id))
    from test_score import GOOD
    take = make_take(status="done", title="River lights", abc=GOOD, seed=111)
    made = client.post(f"/api/takes/{take['id']}/tries", json={"count": 2}).json()["created"]
    assert seen == []   # queuing a take no longer triggers artwork; it waits until render is done


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
    monkeypatch.setattr(artwork, "describer", lambda: "external")
    monkeypatch.setattr(artwork, "drawer", lambda: "external")

    async def describe(record, *args, **kwargs):
        return "A ring on white."

    async def draw(description, as_given=False):
        return as_file(drawing())

    monkeypatch.setattr(artwork, "describe_external", describe)
    monkeypatch.setattr(artwork, "draw", draw)
    asyncio.run(jobs.run_art(take["id"]))                            # asked for again: made, and the mark gone
    assert artwork.info(take["id"])["has"] and not artwork.info(take["id"])["plain"]


def test_the_page_is_told_whether_pictures_are_made(client):
    assert client.get("/api/state").json()["pictures"] is False
    external()
    assert client.get("/api/state").json()["pictures"] is True


# ------------------------------------------------------------------ who draws
def test_who_draws_this_pc_first_then_the_provider_then_nobody(client, monkeypatch):
    engine = {}
    monkeypatch.setattr(artwork, "engine_options", lambda: engine)
    assert artwork.drawer() is None and not artwork.possible() and not artwork.automatic()
    external(draws=False)                                    # a provider with no image model draws nothing
    assert artwork.drawer() is None
    external()
    assert artwork.drawer() == "external" and artwork.automatic()
    engine["pictures"] = True                                # FLUX.2 klein installed: it is preferred, it costs nothing
    assert artwork.drawer() == "local"
    set_setting("art.drawer", "external")
    assert artwork.drawer() == "external"
    set_setting("art.drawer", "local")
    engine["pictures"] = False
    assert artwork.drawer() is None                          # asked for this PC, which has not got it
    assert client.get("/api/state").json()["pictures_possible"] is True


def test_drawn_here_the_picture_waits_its_turn_in_the_gpu_lane(client, monkeypatch):
    monkeypatch.setattr(artwork, "engine_options", lambda: {"pictures": True})
    external()                                               # described by the external LLM, drawn here
    take = a_take()
    jobs.start_art(take["id"])
    assert jobs.ART_WAITING[-1] == take["id"]


def test_the_job_draws_on_the_engine_when_this_pc_draws(client, monkeypatch):
    monkeypatch.setattr(artwork, "engine_options", lambda: {"pictures": True})
    monkeypatch.setattr(artwork, "describer", lambda: "external")
    monkeypatch.setattr(artwork, "is_well_worn", lambda take=None: False)
    take, drawn_with = a_take(), []

    async def describe(record, *args, **kwargs):
        return "A ring on white."

    async def on_engine(take_id, description, title='', as_given=False):
        drawn_with.append((take_id, description, as_given))
        return as_file(drawing())

    async def never(description, as_given=False):
        raise AssertionError("the external model was asked")

    monkeypatch.setattr(artwork, "describe_external", describe)
    monkeypatch.setattr(artwork, "draw", never)
    monkeypatch.setattr(jobs, "_draw_on_engine", on_engine)
    asyncio.run(jobs.run_art(take["id"]))
    # the LLM's image prompt is drawn as it is
    assert drawn_with == [(take["id"], "A ring on white.", True)]
    got = artwork.info(take["id"])
    assert got["has"] and "drawn by FLUX.2 klein on this PC" in got["words"]


def test_only_the_local_drawing_leaves_the_title_out():
    """The brief keeps the title; the take's own description, drawn on this PC, leaves it out, since klein letters
    one."""
    take = {"title": "Night Fishing", "style": "folk, warm", "lyrics": "Night Fishing\nA boat at dusk", "seed": 1}
    assert "Song title: Night Fishing" in artwork.description_request(take)      # local and external
    # the drawing on this PC strips it from a description it makes into klein's prompt
    graph = artwork.picture_graph("Night Fishing floats on calm water.", 3, "yeufonic/p", title="Night Fishing")
    local = graph["4"]["inputs"]["text"]
    assert "Night Fishing" not in local and "floats on calm water" in local
    # an external image model is asked with it, unchanged
    assert "Night Fishing" in artwork.drawing_request("A boat at dusk.", take)


def test_the_flux_graph_is_comfyuis_own_klein_workflow():
    graph = artwork.picture_graph("A lantern.", 7, "yeufonic/picture-x")
    kinds = {node["class_type"]: node["inputs"] for node in graph.values()}
    assert kinds["UNETLoader"]["unet_name"] == "flux-2-klein-4b-fp8.safetensors"
    assert kinds["CLIPLoader"] == {"clip_name": "qwen_3_4b_fp4_flux2.safetensors", "type": "flux2"}
    assert kinds["VAELoader"]["vae_name"] == "flux2-vae.safetensors"
    assert kinds["Flux2Scheduler"]["steps"] == 4 and kinds["RandomNoise"]["noise_seed"] == 7
    assert kinds["EmptyFlux2LatentImage"]["width"] % 16 == 0 and kinds["EmptyFlux2LatentImage"]["height"] % 16 == 0
    # klein cannot spell: what it is sent names the design group only as a style, with no branding, and
    # never an album cover, and it is sampled as it was distilled, at cfg 1 with the negative zeroed (a
    # real negative at cfg 3 burnt the pictures).  The external model, which letters reliably, keeps the
    # named Hipgnosis album-cover prompt.
    local = graph["4"]["inputs"]["text"]
    assert local.startswith("A lantern.") and artwork.KLEIN_LOOK in local     # the scene leads
    assert "Hipgnosis style, no Hipgnosis branding" in local and "album cover" not in local.lower()
    assert "in the style of Hipgnosis" not in local
    assert kinds["ConditioningZeroOut"]["conditioning"] == ["4", 0] and kinds["CFGGuider"]["cfg"] == 1.0
    external = artwork.drawing_request("A lantern.")
    assert "Hipgnosis" in external and artwork.KLEIN_LOOK not in external
    for node in graph.values():                              # every link points at a node in the graph
        for value in node["inputs"].values():
            if isinstance(value, list):
                assert value[0] in graph


def test_the_provider_is_asked_whether_it_has_the_image_model(monkeypatch):
    set_setting("llm.provider", "external")
    set_setting("llm.api_url", "https://generativelanguage.googleapis.com")
    set_setting("llm.api_key", "a-key")
    listed = {"models": [{"name": "models/gemini-flash-latest"}, {"name": "models/gemini-3.1-flash-image"}]}
    asked = []

    class Reply:
        status_code = 200

        def json(self):
            return listed

    class Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, **kwargs):
            asked.append(url)
            return Reply()

    monkeypatch.setattr(artwork.httpx, "AsyncClient", Client)
    assert not artwork.external_ready()                      # not asked yet: not counted on
    assert asyncio.run(artwork.check_external()) and artwork.external_ready()
    asyncio.run(artwork.check_external())                    # remembered: not asked again
    assert len(asked) == 1
    set_setting("art.model", "gemini-9-image")               # a model it has not got
    assert not asyncio.run(artwork.check_external()) and not artwork.external_ready()


def test_every_engine_job_kind_has_a_time_limit():
    """_wait_for looks the kind up in TIMEOUTS: a kind missing there fails the job before it starts."""
    import re
    from pathlib import Path
    from app import config
    source = Path(jobs.__file__).read_text()
    kinds = set(re.findall(r'_run_graph\(\s*"(\w+)"', source))
    assert "art" in kinds
    assert kinds <= set(config.TIMEOUTS)


def test_left_to_choose_a_picture_is_described_by_gemma_where_it_is_installed(monkeypatch):
    """Gemma is the default describer whoever draws, where it is installed, and the take's own description where it
    is not.  The take itself, Gemma or the external LLM are kept when chosen; the last two fall back when not there."""
    external()
    gemma = {"lyrics": True}
    monkeypatch.setattr(artwork, "engine_options", lambda: gemma)
    for chosen in (None, "auto", "same"):              # "same": an earlier choice, read as the default
        if chosen:
            set_setting("art.words", chosen)
        for draws in ("local", "external"):
            monkeypatch.setattr(artwork, "drawer", lambda: draws)
            gemma["lyrics"] = True
            assert artwork.describer() == "gemma" and artwork.words_by_engine()
            gemma["lyrics"] = False                    # Gemma not installed (no Lyric drafts)
            assert artwork.describer() == "take" and not artwork.words_by_engine()
    gemma["lyrics"] = True
    set_setting("art.words", "take")
    assert artwork.describer() == "take" and not artwork.words_by_engine()
    set_setting("art.words", "external")
    assert artwork.describer() == "external"
    set_setting("art.words", "local")
    assert artwork.describer() == "gemma" and artwork.words_by_engine()
    monkeypatch.setattr(artwork, "engine_options", lambda: {})       # Gemma not installed (no Lyric drafts)
    assert artwork.describer() == "take"


def test_the_external_llm_not_there_falls_back_to_gemma_before_the_take(monkeypatch):
    """The take's own description is its title and style tags alone, from which klein draws much the same landscape
    every time: so an external LLM that is local for the session, or has just failed, gives way to Gemma."""
    from app import llm
    external()
    set_setting("art.words", "external")
    monkeypatch.setattr(artwork, "engine_options", lambda: {"lyrics": True})
    try:
        llm.set_session_local_only(True)
        assert artwork.describer() == "gemma" and artwork.words_by_engine()
        llm.set_session_local_only(False)
        assert artwork.describer() == "external"
        artwork.record_external_words_failure("HTTP 429")
        assert artwork.describer() == "gemma"
        monkeypatch.setattr(artwork, "engine_options", lambda: {})   # no Gemma: the take, as before
        assert artwork.describer() == "take"
    finally:
        llm.reset_session_state()


def test_an_external_description_that_fails_is_written_by_gemma_in_the_gpu_lane(client, monkeypatch):
    """Beside a render the external LLM fails: the picture goes to wait for the GPU lane, and there Gemma writes it."""
    external()
    set_setting("art.words", "external")
    monkeypatch.setattr(artwork, "engine_options", lambda: {"lyrics": True, "pictures": True})
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    take = a_take()
    asked, drawn = [], []

    async def fail_describe(record, *args, **kwargs):
        asked.append("external")
        raise RuntimeError("External LLM HTTP 429: quota exhausted")

    async def gemma(kind, ref_id, graph):
        asked.append("gemma")
        assert graph["2"]["class_type"] == "TextGenerate"
        return {"gemma": True}

    async def on_engine(take_id, description, title='', as_given=False):
        drawn.append(description)
        return as_file(drawing())

    monkeypatch.setattr(artwork, "describe_external", fail_describe)
    monkeypatch.setattr(jobs, "_run_graph", gemma)
    monkeypatch.setattr(jobs, "extract_text_output", lambda job, *a: "A piano floating over a salt flat.")
    monkeypatch.setattr(jobs, "_draw_on_engine", on_engine)
    monkeypatch.setattr(jobs, "songs_in_flight", lambda: False)
    jobs.ART_WAITING.clear()

    asyncio.run(jobs.run_art(take["id"]))                  # beside the render: no Gemma here
    assert asked == ["external"] and list(jobs.ART_WAITING) == [take["id"]]
    assert artwork.STATE[take["id"]]["state"] == "queued" and not drawn

    artwork.clear_failures()                               # the lane gets to it after the two minutes are up
    jobs.ART_WAITING.clear()
    asyncio.run(jobs.run_art(take["id"], on_gpu=True))
    assert asked == ["external", "gemma"]                  # not the external LLM again
    assert "A piano floating over a salt flat." in drawn[0]
    got = artwork.info(take["id"])
    assert got["has"] and "Described by Gemma on this PC (" in got["words"] and "failed)" in got["words"]
    assert take["id"] not in jobs._ART_WORDS_FALLBACK


def test_in_the_gpu_lane_a_failed_external_description_goes_straight_to_gemma(client, monkeypatch):
    external()
    set_setting("art.words", "external")
    monkeypatch.setattr(artwork, "engine_options", lambda: {"lyrics": True, "pictures": True})
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    take = a_take()
    asked = []

    async def fail_describe(record, *args, **kwargs):
        asked.append("external")
        raise RuntimeError("External LLM request timed out")

    async def gemma(kind, ref_id, graph):
        asked.append("gemma")
        return {}

    async def on_engine(take_id, description, title='', as_given=False):
        return as_file(drawing())

    monkeypatch.setattr(artwork, "describe_external", fail_describe)
    monkeypatch.setattr(jobs, "_run_graph", gemma)
    monkeypatch.setattr(jobs, "extract_text_output", lambda job, *a: "A chair on a frozen lake.")
    monkeypatch.setattr(jobs, "_draw_on_engine", on_engine)
    monkeypatch.setattr(jobs, "songs_in_flight", lambda: False)
    jobs.ART_WAITING.clear()
    asyncio.run(jobs.run_art(take["id"], on_gpu=True))
    assert asked == ["external", "gemma"] and not jobs.ART_WAITING
    assert "Gemma on this PC" in artwork.info(take["id"])["words"]


def test_the_image_model_setting_only_applies_when_the_provider_draws(client):
    shown = next(s for s in client.get("/api/settings").json()["settings"] if s["key"] == "art.model")
    assert shown["requires"] == {"art.drawer": "external"} and shown["requires_note"]
    words = next(s for s in client.get("/api/settings").json()["settings"] if s["key"] == "art.words")
    assert words["default"] == "auto" and [o["value"] for o in words["options"]] == ["auto", "local", "take", "external"]


def test_a_description_from_the_take_paints_its_look_and_letters_only_its_title():
    take = {"title": "Harbour Lights \u00b7 sung again",
            "style": "synthwave, female vocal, analog synth lead, gated drums, 112 BPM, neon, wistful",
            "lyrics": "[Verse]\nThe harbour lights are counting down\nA ferry hums across the bay\n\n[Chorus]\nStay"}
    text = artwork.take_description(take)
    assert "album cover in the style of Hipgnosis" in text
    assert "Song title: Harbour Lights" in text
    assert "sung again" not in text
    assert 'cover style:\n"synthwave, female vocal, analog synth lead, gated drums, 112 BPM, neon, wistful"' in text
    bare = artwork.take_description({"title": "Untitled", "style": "", "lyrics": ""})
    assert "Song title:" not in bare
    assert "cover style:" in bare


def test_with_nothing_to_draw_take_pictures_says_no_pictures(client, monkeypatch):
    """Nothing here can draw: Take pictures reads No pictures, and pictures for each take cannot be chosen.  Once
    something can draw, they are on unless chosen off."""
    def picture_setting():
        return next(s for s in client.get("/api/settings").json()["settings"] if s["key"] == "art.auto")
    monkeypatch.setattr(artwork, "local_ready", lambda: False)
    shown = picture_setting()
    assert shown["value"] == "off"
    assert [o["value"] for o in shown["options"] if o.get("disabled")] == ["on"]
    assert "requires" not in shown                        # a choice, not a greyed-out row
    assert "FLUX.2 [klein]" in shown["help"]
    assert not artwork.automatic()
    external()                                            # a provider that can draw
    shown = picture_setting()
    assert shown["value"] == "on" and not any(o.get("disabled") for o in shown["options"])
    assert artwork.automatic()
    set_setting("art.auto", "off")                        # chosen off: kept off
    assert picture_setting()["value"] == "off" and not artwork.automatic()


def test_with_pictures_off_for_new_takes_one_can_still_be_made_when_asked(client, monkeypatch):
    """Off means none by itself: the page still offers Make a picture, and Settings still show how it is made."""
    external()
    set_setting("art.auto", "off")
    state = client.get("/api/state").json()
    assert state["pictures"] is False and state["pictures_drawable"] is True
    settings = {s["key"]: s for s in client.get("/api/settings").json()["settings"]}
    assert all("art.auto" not in (settings[key].get("requires") or {})
               for key in ("art.drawer", "art.klein", "art.words", "art.style", "art.title", "art.prompt", "art.model"))
    take = a_take()
    monkeypatch.setattr(jobs, "start_art", lambda take_id: None)
    assert client.post(f"/api/takes/{take['id']}/art").status_code == 200


def test_a_picture_waits_until_no_song_is_being_made(client, monkeypatch):
    """A picture that needs the GPU is not taken while a take is queued or running, nor before song work already
    in the queue: it comes after the song, never between its plan and its render."""
    picture, song = a_take(), a_take()
    jobs.ART_WAITING.append(picture["id"])
    execute("UPDATE takes SET status = 'queued' WHERE id = ?", (song["id"],))
    jobs.QUEUE.put_nowait({"kind": "render", "id": song["id"]})

    async def next_now():
        return await asyncio.wait_for(jobs.next_gpu_job(), timeout=0.5)

    assert asyncio.run(next_now()) == ({"kind": "render", "id": song["id"]}, True)
    execute("UPDATE takes SET status = 'running' WHERE id = ?", (song["id"],))
    with pytest.raises(asyncio.TimeoutError):           # the song is being made: the picture keeps waiting
        asyncio.run(next_now())
    assert list(jobs.ART_WAITING) == [picture["id"]]
    execute("UPDATE takes SET status = 'done' WHERE id = ?", (song["id"],))
    assert asyncio.run(next_now()) == ({"kind": "art", "id": picture["id"]}, False)
    assert not jobs.ART_WAITING


def test_a_waiting_picture_is_listed_last_and_can_be_cancelled(client):
    picture, song = a_take(), a_take()
    jobs.ART_WAITING.append(picture["id"])
    artwork.STATE[picture["id"]] = {"state": "queued", "error": None}
    jobs.QUEUE.put_nowait({"kind": "render", "id": song["id"]})
    assert [job["kind"] for job in jobs.waiting_jobs()] == ["render", "art"]
    assert asyncio.run(jobs.cancel_waiting("art", picture["id"]))
    assert not jobs.ART_WAITING and picture["id"] not in artwork.STATE
    assert not asyncio.run(jobs.cancel_waiting("art", picture["id"]))


def test_a_running_picture_steps_aside_when_song_work_comes_in(client, monkeypatch):
    """While a picture runs on the engine, song work arriving stops it there, and the picture goes back to the
    front of its line, to start again when the GPU is free."""
    async def nothing_yet(prompt_id):
        return None
    real_sleep = asyncio.sleep

    async def no_wait(seconds):
        await real_sleep(0.001)
    monkeypatch.setattr(jobs.ENGINE, "history", nothing_yet)
    monkeypatch.setattr(jobs.asyncio, "sleep", no_wait)
    monkeypatch.setattr(jobs.ENGINE, "last_contact", time.time() + 3600, raising=False)
    song = a_take()
    jobs.QUEUE.put_nowait({"kind": "render", "id": song["id"]})
    assert asyncio.run(jobs._wait_for("art", "p1", "prompt-1")) == ("yield", None)

    picture, other = a_take(), a_take()
    jobs.ART_WAITING.append(other["id"])
    async def stopped(kind, ref_id, graph):
        raise jobs.ArtYielded()
    monkeypatch.setattr(jobs, "_run_graph", stopped)
    monkeypatch.setattr(artwork, "describer", lambda: "gemma")
    asyncio.run(jobs.run_art(picture["id"], on_gpu=True))
    assert list(jobs.ART_WAITING) == [picture["id"], other["id"]]
    assert artwork.STATE[picture["id"]]["state"] == "queued"


def test_an_idle_worker_notices_a_picture_added_while_it_waits(client, monkeypatch):
    """The worker waiting on an empty queue must still see a picture that joins its line afterwards."""
    picture = a_take()

    async def scenario():
        monkeypatch.setattr(jobs, "QUEUE", asyncio.Queue())     # a queue of this loop's own, and empty
        waiting = asyncio.ensure_future(jobs.next_gpu_job())
        await asyncio.sleep(0.2)                  # the worker is now waiting, with nothing anywhere
        jobs.ART_WAITING.append(picture["id"])
        return await asyncio.wait_for(waiting, timeout=5)

    assert asyncio.run(scenario()) == ({"kind": "art", "id": picture["id"]}, False)


def test_external_draw_failure_falls_back_to_local_flux(client, monkeypatch):
    monkeypatch.setattr(artwork, "engine_options", lambda: {"pictures": True})
    monkeypatch.setattr(artwork, "describer", lambda: "take")
    monkeypatch.setattr(artwork, "drawer", lambda: "external")
    take = a_take()
    drawn_on_engine = []

    async def fail_draw(description, as_given=False):
        raise RuntimeError("the image model (gpt-image-1) said 429: rate limit exceeded")

    async def on_engine(take_id, description, title='', as_given=False):
        drawn_on_engine.append((take_id, description))
        return as_file(drawing())

    monkeypatch.setattr(artwork, "draw", fail_draw)
    monkeypatch.setattr(jobs, "_draw_on_engine", on_engine)
    asyncio.run(jobs.run_art(take["id"]))

    assert len(drawn_on_engine) == 1
    got = artwork.info(take["id"])
    assert got["has"]
    assert "drawn by FLUX.2 klein on this PC" in got["words"]


def test_external_words_failure_falls_back_to_take_description(client, monkeypatch):
    monkeypatch.setattr(artwork, "engine_options", lambda: {"pictures": True})
    monkeypatch.setattr(artwork, "describer", lambda: "external")
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    take = a_take()

    async def fail_describe(record, *args, **kwargs):
        raise RuntimeError("External LLM HTTP 429: quota exhausted")

    async def on_engine(take_id, description, title='', as_given=False):
        return as_file(drawing())

    monkeypatch.setattr(artwork, "describe_external", fail_describe)
    monkeypatch.setattr(jobs, "_draw_on_engine", on_engine)
    asyncio.run(jobs.run_art(take["id"]))

    got = artwork.info(take["id"])
    assert got["has"]
    assert "its own title, style and words" in got["words"]
    assert "failed" in got["words"]


def test_external_draw_failure_without_flux_fails_job(client, monkeypatch):
    monkeypatch.setattr(artwork, "engine_options", lambda: {})
    monkeypatch.setattr(artwork, "describer", lambda: "take")
    monkeypatch.setattr(artwork, "drawer", lambda: "external")
    take = a_take()

    async def fail_draw(description, as_given=False):
        raise RuntimeError("the image model said 429: rate limit exceeded")

    monkeypatch.setattr(artwork, "draw", fail_draw)
    asyncio.run(jobs.run_art(take["id"]))

    assert artwork.STATE[take["id"]]["state"] == "failed"
    assert "429" in artwork.STATE[take["id"]]["error"]


def test_trigger_words_and_artist_names_are_stripped_from_cover_prompts():
    execute("INSERT OR REPLACE INTO identities (id, name, trigger_word, folder, created_at) VALUES (?, ?, ?, ?, ?)",
            ("id-test-dylan", "Bobby Dylan", "bobbydyln", "bob", 12345.0))
    triggers = artwork.take_triggers()
    assert "bobbydyln" in triggers
    assert "Bobby Dylan" in triggers

    # Style cleaning removes both the trigger word and the artist name
    style = "bobbydyln, mid-1970s soft rock, Bobby Dylan, acoustic rhythm guitar, male vocal"
    cleaned_style = artwork.clean_cover_style(style)
    assert "bobbydyln" not in cleaned_style
    assert "Bobby Dylan" not in cleaned_style
    assert "mid-1970s soft rock" in cleaned_style
    assert "acoustic rhythm guitar" in cleaned_style

    # Title cleaning drops titles that are solely the trigger word or artist name
    assert artwork.clean_cover_title({"title": "bobbydyln"}) == ""
    assert artwork.clean_cover_title({"title": "Bobby Dylan"}) == ""
    # But preserves actual song titles with artist prefix stripped
    assert artwork.clean_cover_title({"title": "Bobby Dylan - Like a Rolling Stone"}) == "Like a Rolling Stone"

    # The title lettered on the cover is the user's own, an artist's name in it included; the description
    # sent to the LLM still leaves it out.
    assert artwork.lettered_title({"title": "Bobby Dylan · sung again"}) == "Bobby Dylan"
    assert artwork.lettered_title({"title": "Untitled"}) == ""
    set_setting("art.title", "on")
    assert artwork.title_at({"title": "bobbydyln"}) is not None
    assert "bobbydyln" not in artwork.description_request({"title": "bobbydyln", "style": "folk"}, "top band")
    set_setting("art.title", "off")

    # take_description omits title if it was the trigger word, and strips triggers from cover style
    take = {"title": "bobbydyln", "style": "bobbydyln, 1970s rock, acoustic guitar", "lyrics": LYRICS}
    desc = artwork.take_description(take)
    assert "bobbydyln" not in desc
    assert "Bobby Dylan" not in desc
    assert "Song title:" not in desc
    assert 'cover style:\n"1970s rock, acoustic guitar"' in desc

    # description_request omits trigger words and artist name from Style and Song title
    req = artwork.description_request({"title": "Bobby Dylan - Tangled", "style": "bobbydyln, folk rock", "lyrics": LYRICS})
    assert "bobbydyln" not in req
    assert "Song title: Tangled\n" in req
    assert "Song style: folk rock\n" in req

    # drawing_request strips any stray artist names or trigger words from description prose
    drawn = artwork.drawing_request("A surreal photo of Bobby Dylan in a desert with bobbydyln guitar.")
    assert "Bobby Dylan" not in drawn
    assert "bobbydyln" not in drawn
    assert "Hipgnosis" in drawn


def test_well_worn_randomization_and_scene_inclusion():
    # is_well_worn logic based on take seed (seeds 0, 1, 2 are well worn; seeds 3-9 are not)
    assert artwork.is_well_worn({"seed": 0}) is True
    assert artwork.is_well_worn({"seed": 2}) is True
    assert artwork.is_well_worn({"seed": 3}) is False
    assert artwork.is_well_worn({"seed": 7}) is False

    # take_description with well_worn=False produces "an album cover" without "well worn"
    clean_desc = artwork.take_description({"title": "Old Man", "style": "soft rock, 118 BPM"}, well_worn=False)
    assert "Create an image in the shape of an album cover" in clean_desc
    assert "well worn" not in clean_desc
    assert "Song title: Old Man\n" in clean_desc
    assert 'cover style:\n"soft rock, 118 BPM"' in clean_desc

    # take_description with well_worn=True produces "a well worn album cover"
    worn_desc = artwork.take_description({"title": "Old Man", "style": "soft rock, 118 BPM"}, well_worn=True)
    assert "Create an image in the shape of a well worn album cover" in worn_desc

    # take_description includes visual scene when passed
    scene_desc = artwork.take_description({"title": "Old Man", "style": "soft rock"}, scene="A pear on a crate.", well_worn=False)
    assert "Song title: Old Man\n" in scene_desc
    assert 'cover style:\n"soft rock"' in scene_desc
    assert 'visual scene:\n"A pear on a crate."' in scene_desc

    # drawing_request with take combines scene with song title and style prompt
    combined = artwork.drawing_request("A lonely telephone box.", take={"title": "Dial In", "style": "yacht rock", "seed": 5})
    assert "Song title: Dial In\n" in combined
    assert 'cover style:\n"yacht rock"' in combined
    assert 'visual scene:\n"A lonely telephone box."' in combined


def test_hipgnosis_attribution_and_year_rules():
    # 1. album_cover_prefix explicitly specifies not to use the name Hipgnosis on the image
    # and that the artwork is only influenced by them, not created by them
    prefix = artwork.album_cover_prefix()
    assert "Do not use the name Hipgnosis in the image" in prefix
    assert "only be influenced by that design group, not made to look like it was created by them" in prefix

    # 2. take_description and drawing_request inherit this instruction
    take = {"title": "Silent Night", "style": "acoustic, ambient"}
    prompt = artwork.take_description(take)
    assert "Do not use the name Hipgnosis in the image" in prompt
    assert "only be influenced by that design group, not made to look like it was created by them" in prompt

    drawn = artwork.drawing_request("A solitary lighthouse.")
    assert "Do not use the name Hipgnosis in the image" in drawn

    # 3. If a year is in the style prompt, it is included in Song style / cover style
    req_with_year = artwork.description_request({"title": "Neon Grid", "style": "1984 synthwave"})
    assert "Song style: 1984 synthwave" in req_with_year
    desc_with_year = artwork.take_description({"title": "Neon Grid", "style": "1984 synthwave"})
    assert 'cover style:\n"1984 synthwave"' in desc_with_year

    # 5. Stray "by Hipgnosis" or "Hipgnosis" in scene descriptions are stripped out
    scene_with_leak = artwork.take_description(take, scene="A glowing monolith in the desert, designed by Hipgnosis.")
    assert 'visual scene:\n"A glowing monolith in the desert."' in scene_with_leak
    assert "designed by Hipgnosis" not in scene_with_leak


def test_external_artwork_starts_before_audio_finishes(monkeypatch, data_dir):
    from test_jobs import FakeEngine, render_history, tone, use
    called_order = []

    def fake_art(take_id):
        called_order.append(("art", take_id))

    monkeypatch.setattr(jobs, "art_for_new_take", fake_art)
    monkeypatch.setattr(artwork, "automatic", lambda: True)
    monkeypatch.setattr(artwork, "drawer", lambda: "external")
    monkeypatch.setattr(artwork, "words_by_engine", lambda: False)

    engine_out = data_dir / "engine-output"
    engine_copy = tone(engine_out / "yeufonic" / "take_00001_.flac", 1.0)
    monkeypatch.setattr(config, "ENGINE_OUTPUT_DIR", engine_out)
    take = make_take(status="queued", abc="X:1\nT:Test\nK:C\nC4|", title="Parallel Art Order", max_duration=1.0)
    engine = use(monkeypatch, FakeEngine([render_history()], audio=engine_copy))
    orig_download = engine.download

    async def mock_download(item, dest):
        called_order.append(("download", take["id"]))
        return await orig_download(item, dest)

    engine.download = mock_download

    asyncio.run(jobs.run_job("render", take["id"]))
    assert ("art", take["id"]) in called_order
    assert ("download", take["id"]) in called_order
    art_idx = called_order.index(("art", take["id"]))
    dl_idx = called_order.index(("download", take["id"]))
    assert art_idx < dl_idx


def test_local_artwork_does_not_start_before_render_finishes(monkeypatch, data_dir):
    from test_jobs import FakeEngine, render_history, tone, use
    called_order = []

    def fake_art(take_id):
        called_order.append(("art", take_id))

    monkeypatch.setattr(jobs, "art_for_new_take", fake_art)
    monkeypatch.setattr(artwork, "automatic", lambda: True)
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    monkeypatch.setattr(artwork, "words_by_engine", lambda: False)

    engine_out = data_dir / "engine-output"
    engine_copy = tone(engine_out / "yeufonic" / "take_00001_.flac", 1.0)
    monkeypatch.setattr(config, "ENGINE_OUTPUT_DIR", engine_out)
    take = make_take(status="queued", abc="X:1\nT:Test\nK:C\nC4|", title="Local Art Order", max_duration=1.0)
    engine = use(monkeypatch, FakeEngine([render_history()], audio=engine_copy))
    orig_download = engine.download

    async def mock_download(item, dest):
        called_order.append(("download", take["id"]))
        return await orig_download(item, dest)

    engine.download = mock_download

    asyncio.run(jobs.run_job("render", take["id"]))
    assert ("art", take["id"]) in called_order
    assert ("download", take["id"]) in called_order
    art_idx = called_order.index(("art", take["id"]))
    dl_idx = called_order.index(("download", take["id"]))
    assert art_idx > dl_idx






def test_klein_is_drawn_with_whichever_pair_of_files_is_installed():
    # FP8 + FP4 on Windows and Docker; the full-precision pair on a Mac, whose GPU cannot run FP8 or FP4.
    nvidia, mac = config.PICTURE_PAIRS
    assert nvidia == ("flux-2-klein-4b-fp8.safetensors", "qwen_3_4b_fp4_flux2.safetensors")
    assert config.choose_picture_files([nvidia[0], mac[0]], [nvidia[1], mac[1]]) == nvidia
    assert config.choose_picture_files([mac[0]], [mac[1], "gemma.safetensors"]) == mac
    assert config.choose_picture_files([nvidia[0]], [mac[1]]) == nvidia          # no whole pair: the usual names
    assert config.choose_picture_files(None, None) == nvidia


def test_an_engine_with_the_full_precision_klein_files_can_draw(monkeypatch):
    import httpx
    from app.engine import Engine
    model, encoder = config.PICTURE_PAIRS[1]
    combo = lambda field, names: {"input": {"required": {field: [names]}}}
    info = {"UNETLoader": combo("unet_name", [model]), "CLIPLoader": combo("clip_name", [encoder]),
            "VAELoader": combo("vae_name", [config.PICTURE_VAE]), "CheckpointLoaderSimple": combo("ckpt_name", []),
            **{node: {"input": {"required": {}}} for node in ("EmptyFlux2LatentImage", "Flux2Scheduler",
                                                             "SamplerCustomAdvanced", "CFGGuider")}}

    async def run():
        engine = Engine("http://engine")
        engine.client = httpx.AsyncClient(base_url="http://engine",
                                          transport=httpx.MockTransport(lambda r: httpx.Response(200, json=info)))
        await engine.refresh_options()
        await engine.client.aclose()
        return engine.options["pictures"]
    monkeypatch.setattr(config, "PICTURE_MODEL", config.PICTURE_MODEL)
    monkeypatch.setattr(config, "PICTURE_TEXT", config.PICTURE_TEXT)
    assert asyncio.run(run()) is True
    assert (config.PICTURE_MODEL, config.PICTURE_TEXT) == (model, encoder)
    assert artwork.picture_graph("a field", 1, "p")["1"]["inputs"]["unet_name"] == model


def test_klein_is_sent_the_scene_and_the_look_without_the_prompts_labels():
    """take_description's labels never reach klein: an empty "Song title:" asks for a title, "72 bpm" for
    numbers.  A well-worn sleeve keeps its wear, and the take's mood stands in only where there is no scene."""
    take = {"title": "Paper Moon", "style": "melancholic indie folk, female vocals, piano, 72 bpm", "seed": 1}
    scene = 'A man holds a paper moon on a string beside a phone box reading "Paper Moon".'
    local = artwork.klein_request(artwork.take_description(take, scene=scene, well_worn=True), take)
    assert "Song title" not in local and "cover style" not in local and "visual scene" not in local
    assert "holds a paper moon on a string beside a phone box." in local        # the pun stays, the sign goes
    assert '"' not in local and "bpm" not in local and "melancholic" not in local
    assert artwork.KLEIN_WORN in local
    bare = artwork.klein_request(artwork.take_description(take, scene="", well_worn=False), take)
    assert "Its mood: melancholic indie folk, piano." in bare
    assert artwork.KLEIN_WORN not in bare and "72" not in bare and "vocals" not in bare


def test_klein_loses_the_words_it_would_letter():
    assert artwork.wordless_scene("A boat named Night Fishing drifts on fog.", "Night Fishing") == "A boat drifts on fog."
    assert artwork.wordless_scene("A sign that reads \u201cRain\u201d in a field.", "Rain") == "A sign in a field."
    assert artwork.wordless_scene("Rain falls on open umbrellas.", "Rain") == "Rain falls on open umbrellas."
    assert artwork.wordless_scene("Two figures, called by the sea, wait.", "") == "Two figures, called by the sea, wait."


def test_a_picture_that_skips_the_external_models_says_why(client, monkeypatch, caplog):
    """After a failure the external models are not asked for a while: the log says so for each picture, rather
    than only showing a local writer and drawer."""
    external()
    set_setting("art.words", "external")
    set_setting("art.drawer", "external")
    monkeypatch.setattr(artwork, "engine_options", lambda: {"pictures": True})
    artwork.record_external_words_failure("HTTP 503")
    artwork.record_external_draw_failure("HTTP 429")
    take = a_take()

    async def on_engine(take_id, description, title='', as_given=False):
        return as_file(drawing())

    monkeypatch.setattr(jobs, "_draw_on_engine", on_engine)
    with caplog.at_level("WARNING", logger="yue2.jobs"):
        asyncio.run(jobs.run_art(take["id"]))
    said = caplog.text
    assert "not described by the external LLM, as it failed" in said and "the take's own scene instead" in said
    assert "not drawn by" in said and "FLUX.2 klein on this PC instead" in said
    assert artwork.info(take["id"])["has"]


def test_klein_is_given_the_scene_first():
    """klein weighs the start of its prompt most, so the scene leads; klein itself is told nothing about people,
    which put a small figure in every picture."""
    klein = artwork.klein_request("A man rows a boat at dusk.")
    assert klein.startswith("A man rows a boat at dusk.")
    assert "person" not in klein.lower() and "figure" not in klein.lower() and "hand" not in klein.lower()
    assert "vast" not in klein and "empty space" not in klein and "muted" not in klein


def test_klein_9b_is_found_when_its_files_are_put_in_and_drawn_with_as_settings_ask(monkeypatch):
    """The 9B is never installed by Yeufonic, but its files put in by hand are found, beside the 4B or alone.
    Settings choose: the 4B by default, so a clean install draws with it; "auto" takes the 9B; one asked for
    and not there leaves the other to draw."""
    import httpx

    from app.engine import Engine
    four, nine = config.PICTURE_PAIRS[0], ("flux-2-klein-9b.safetensors", "qwen_3_8b_fp8mixed.safetensors")
    combo = lambda field, names: {"input": {"required": {field: [names]}}}

    def options(unets, encoders):
        info = {"UNETLoader": combo("unet_name", unets), "CLIPLoader": combo("clip_name", encoders),
                "VAELoader": combo("vae_name", [config.PICTURE_VAE]), "CheckpointLoaderSimple": combo("ckpt_name", []),
                **{node: {"input": {"required": {}}} for node in ("EmptyFlux2LatentImage", "Flux2Scheduler",
                                                                 "SamplerCustomAdvanced", "CFGGuider")}}

        async def run():
            engine = Engine("http://engine")
            engine.client = httpx.AsyncClient(base_url="http://engine",
                                              transport=httpx.MockTransport(lambda r: httpx.Response(200, json=info)))
            await engine.refresh_options()
            await engine.client.aclose()
            return engine.options
        return asyncio.run(run())

    monkeypatch.setattr(config, "PICTURE_MODEL", config.PICTURE_MODEL)
    monkeypatch.setattr(config, "PICTURE_TEXT", config.PICTURE_TEXT)
    both = options([four[0], nine[0]], [four[1], nine[1]])
    assert both["pictures"] and both["klein"] == {"4b": list(four), "9b": list(nine)}
    alone = options([nine[0]], [nine[1]])
    assert alone["pictures"] and alone["klein"] == {"9b": list(nine)}
    assert options([nine[0]], [four[1]])["pictures"] is False          # the 9B model without its text encoder

    chosen = {}
    monkeypatch.setattr(artwork, "get_setting", lambda key, default=None: chosen.get(key, default))
    monkeypatch.setattr(artwork, "engine_options", lambda: both)
    unet = lambda: artwork.picture_graph("a field", 1, "p")["1"]["inputs"]["unet_name"]
    assert unet() == four[0] and artwork.klein_name() == "FLUX.2 klein 4B"          # the default, 9B there or not
    assert artwork.picture_graph("a", 1, "p")["2"]["inputs"]["clip_name"] == four[1]
    chosen["art.klein"] = "9b"
    assert unet() == nine[0] and artwork.klein_name() == "FLUX.2 klein 9B"
    chosen["art.klein"] = "auto"
    assert unet() == nine[0]
    chosen["art.klein"] = "4b"
    monkeypatch.setattr(artwork, "engine_options", lambda: alone)
    assert unet() == nine[0] and artwork.klein_name() == "FLUX.2 klein 9B"          # the 4B asked for, not there


def test_flux3_klein_is_found_when_its_files_are_put_in_and_drawn_its_own_way(monkeypatch):
    """FLUX 3 klein is never installed by Yeufonic either: its model and Qwen3-VL encoder put in by hand are found,
    on a ComfyUI that knows its encoder type, and chosen in Settings it draws with the plain sampler, sixteen steps,
    no guidance.  Asked for and not there, a FLUX.2 klein draws."""
    import httpx

    from app.engine import Engine
    four = config.PICTURE_PAIRS[0]
    three = ("flux3-image-klein-int8-convrot.safetensors", "qwen3vl_4b_int8_convrot.safetensors")
    combo = lambda field, names: {"input": {"required": {field: [names]}}}

    def options(unets, encoders, types=("flux2", "flux3")):
        info = {"UNETLoader": combo("unet_name", unets),
                "CLIPLoader": {"input": {"required": {"clip_name": [encoders], "type": [list(types)]}}},
                "VAELoader": combo("vae_name", [config.PICTURE_VAE]), "CheckpointLoaderSimple": combo("ckpt_name", []),
                **{node: {"input": {"required": {}}} for node in ("EmptyFlux2LatentImage", "Flux2Scheduler",
                                                                 "SamplerCustomAdvanced", "CFGGuider", "KSampler")}}

        async def run():
            engine = Engine("http://engine")
            engine.client = httpx.AsyncClient(base_url="http://engine",
                                              transport=httpx.MockTransport(lambda r: httpx.Response(200, json=info)))
            await engine.refresh_options()
            await engine.client.aclose()
            return engine.options
        return asyncio.run(run())

    both = options([four[0], three[0]], [four[1], three[1]])
    assert both["klein"] == {"4b": list(four), "flux3": list(three)}
    assert options([four[0], three[0]], [four[1], three[1]], types=("flux2",))["klein"] == {"4b": list(four)}
    assert options([three[0]], [four[1]])["pictures"] is False          # the model without its encoder

    chosen = {}
    monkeypatch.setattr(artwork, "get_setting", lambda key, default=None: chosen.get(key, default))
    monkeypatch.setattr(artwork, "engine_options", lambda: both)
    assert artwork.picture_graph("a field", 1, "p")["1"]["inputs"]["unet_name"] == four[0]   # the 4B by default
    chosen["art.klein"] = "flux3"
    graph = artwork.picture_graph("a field", 7, "p", as_given=True)
    assert graph["1"]["inputs"]["unet_name"] == three[0] and artwork.klein_name() == "FLUX 3 klein"
    assert graph["2"]["inputs"] == {"clip_name": three[1], "type": "flux3"}
    sampler = graph["7"]
    assert sampler["class_type"] == "KSampler" and sampler["inputs"]["steps"] == 16 and sampler["inputs"]["cfg"] == 1.0
    assert sampler["inputs"]["seed"] == 7 and graph["4"]["inputs"]["text"] == "a field"
    assert graph["3"]["inputs"]["vae_name"] == config.PICTURE_VAE and graph["9"]["inputs"]["filename_prefix"] == "p"
    monkeypatch.setattr(artwork, "engine_options", lambda: {"klein": {"4b": list(four)}})
    assert artwork.picture_graph("a", 1, "p")["1"]["inputs"]["unet_name"] == four[0]          # not there: the 4B
    from app.main import SETTINGS_BY_KEY
    assert "flux3" in [o["value"] for o in SETTINGS_BY_KEY["art.klein"]["options"]]


def test_fibo2_is_found_when_its_files_are_put_in_and_drawn_its_own_way(monkeypatch):
    """FIBO 2.0 is never installed by Yeufonic: its model, put in by hand beside FLUX 3's encoder, is found on a ComfyUI
    with its prompt node, and chosen in Settings it draws through that node: with its turbo add-on in eight steps and
    no guidance, without it at Dev's own fifty steps and a guidance of five."""
    import httpx

    from app.engine import Engine
    four = config.PICTURE_PAIRS[0]
    fibo = ("fibo2_dev_int8_convrot.safetensors", "qwen3vl_4b_int8_convrot.safetensors")
    combo = lambda field, names: {"input": {"required": {field: [names]}}}

    def options(unets, encoders, loras=(), nodes=("TextEncodeFibo2", "LoraLoaderModelOnly"), types=("flux2", "fibo2")):
        info = {"UNETLoader": combo("unet_name", unets),
                "CLIPLoader": {"input": {"required": {"clip_name": [encoders], "type": [list(types)]}}},
                "VAELoader": combo("vae_name", [config.PICTURE_VAE]), "CheckpointLoaderSimple": combo("ckpt_name", []),
                **{node: {"input": {"required": {}}} for node in ("EmptyFlux2LatentImage", "Flux2Scheduler",
                                                                 "SamplerCustomAdvanced", "CFGGuider", "KSampler", *nodes)}}
        if "LoraLoaderModelOnly" in nodes:
            info["LoraLoaderModelOnly"] = combo("lora_name", list(loras))

        async def run():
            engine = Engine("http://engine")
            engine.client = httpx.AsyncClient(base_url="http://engine",
                                              transport=httpx.MockTransport(lambda r: httpx.Response(200, json=info)))
            await engine.refresh_options()
            await engine.client.aclose()
            return engine.options
        return asyncio.run(run())

    turbo = options([four[0], fibo[0]], [four[1], fibo[1]], loras=[config.PICTURE_FIBO2_TURBO])
    assert turbo["klein"] == {"4b": list(four), "fibo2": list(fibo)} and turbo["fibo2_turbo"] is True
    plain = options([four[0], fibo[0]], [four[1], fibo[1]])
    assert plain["klein"]["fibo2"] == list(fibo) and plain["fibo2_turbo"] is False
    assert "fibo2" not in options([four[0], fibo[0]], [four[1], fibo[1]], nodes=("LoraLoaderModelOnly",))["klein"]
    assert "fibo2" not in options([four[0], fibo[0]], [four[1], fibo[1]], types=("flux2",))["klein"]

    chosen = {"art.klein": "fibo2"}
    monkeypatch.setattr(artwork, "get_setting", lambda key, default=None: chosen.get(key, default))
    monkeypatch.setattr(artwork, "engine_options", lambda: turbo)
    graph = artwork.picture_graph("a field", 7, "p", as_given=True)
    assert graph["1"]["inputs"]["unet_name"] == fibo[0] and artwork.klein_name() == "FIBO 2.0"
    assert graph["2"]["inputs"] == {"clip_name": fibo[1], "type": "fibo2"}
    assert graph["4"]["class_type"] == "TextEncodeFibo2" and graph["4"]["inputs"]["prompt"] == "a field"
    assert graph["5"]["inputs"]["lora_name"] == config.PICTURE_FIBO2_TURBO and graph["7"]["inputs"]["model"] == ["5", 0]
    sampler = graph["7"]["inputs"]
    assert (sampler["steps"], sampler["cfg"], sampler["seed"]) == (8, 1.0, 7)
    assert sampler["latent_image"] == ["4", 2] and sampler["negative"] == ["4", 1]
    monkeypatch.setattr(artwork, "engine_options", lambda: plain)
    graph = artwork.picture_graph("a field", 7, "p", as_given=True)
    assert "5" not in graph and graph["7"]["inputs"]["model"] == ["1", 0]
    assert (graph["7"]["inputs"]["steps"], graph["7"]["inputs"]["cfg"]) == (50, 5.0)
    from app.main import SETTINGS_BY_KEY
    assert "fibo2" in [o["value"] for o in SETTINGS_BY_KEY["art.klein"]["options"]]


def test_fibo2_gets_a_sleeve_with_no_frame_line(monkeypatch):
    """FIBO 2.0 boxed the title and barred the frame line on the sleeve klein draws well; drawn by FIBO on this PC, the
    band is worded without the line and the title printed on the paper.  Anything else keeps the sleeve as it was."""
    monkeypatch.setattr(artwork.random, "random", lambda: 0.9)          # lower case
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    monkeypatch.setattr(artwork, "klein_size", lambda: "fibo2")
    fibo = artwork.with_title("A scene.", "Big Sky", "bottom band")
    assert 'the title "big sky" is printed directly on the paper' in fibo and "line" not in fibo and "box" not in fibo
    assert "deeper margin along the bottom" in fibo
    monkeypatch.setattr(artwork, "klein_size", lambda: "flux3")
    assert "thin dark line" in artwork.with_title("A scene.", "Big Sky", "bottom band")
    monkeypatch.setattr(artwork, "klein_size", lambda: "fibo2")
    monkeypatch.setattr(artwork, "drawer", lambda: "external")
    assert "thin dark line" in artwork.with_title("A scene.", "Big Sky", "bottom band")


def test_a_clean_install_draws_with_the_4b():
    from app.main import SETTINGS_BY_KEY
    spec = SETTINGS_BY_KEY["art.klein"]
    assert spec["default"] == "4b" and spec["options"][0]["value"] == "4b"


# ------------------------------------------------------------------ the image prompt
def test_the_llm_is_asked_for_an_image_prompt_from_the_title_the_art_style_the_style_and_the_words():
    take = {"title": "Corner Shop · sung again", "style": "barbershop, close harmony", "lyrics": LYRICS, "seed": 1}
    asked = artwork.description_request(take)
    assert asked.startswith("create an image prompt for an album cover based on the following criteria:\n\n")
    assert "Song title: Corner Shop\n" in asked and "sung again" not in asked
    assert f"Album art style: {artwork.DEFAULT_ART_STYLE}" in asked
    assert "Song style: barbershop, close harmony" in asked
    # the words as written, headings and the gaps between sections kept, cue lines out
    assert "Lyrics:\n\n[verse]\nLanterns on the water\nCarry what we said\n\n[chorus]\n\nAnd the river keeps it" in asked
    assert asked.endswith(f"{artwork.PROMPT_BRIEF}\n\nReply with the image prompt only.")
    assert artwork.describe_graph(take, 1)["2"]["inputs"]["prompt"] == asked          # Gemma is asked the same
    set_setting("art.style", "Bold geometric shapes in primary colours.")
    assert "Album art style: Bold geometric shapes in primary colours." in artwork.description_request(take)
    set_setting("art.style", "  ")
    assert artwork.DEFAULT_ART_STYLE in artwork.description_request(take)          # emptied: the default again


def test_at_most_fifty_lines_of_words_are_given_and_none_for_an_instrumental():
    long = "\n".join(f"line {n}" for n in range(1, 80))
    words = artwork.song_words("[verse]\n" + long)
    assert words.count("\n") + 1 == artwork.PROMPT_LINES and words.endswith("line 49")
    asked = artwork.description_request({"title": "Tide", "style": "ambient", "lyrics": "", "seed": 1})
    assert "Lyrics" not in asked and "Song style: ambient" in asked


def test_the_art_style_is_a_setting_for_when_an_llm_writes_the_prompt(client):
    shown = {s["key"]: s for s in client.get("/api/settings").json()["settings"]}
    assert shown["art.style"]["value"] == artwork.DEFAULT_ART_STYLE
    assert shown["art.style"]["requires"]["art.words"] == ["auto", "local", "external"]


def test_gemmas_image_prompt_is_drawn_as_it_is(client, monkeypatch):
    """klein draws what Gemma wrote, with nothing added: no house look, no wordless rewriting."""
    take = a_take(title="Night Fishing", lyrics="[verse]\nNight Fishing\nA boat at dusk")
    monkeypatch.setattr(artwork, "describer", lambda: "gemma")
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    monkeypatch.setattr(artwork, "is_well_worn", lambda take=None: False)
    asked, drawn_with = [], []

    async def gemma(kind, take_id, graph):
        asked.append(graph["2"]["inputs"]["prompt"])
        return {"written": "**Image Prompt:**\n\nA rowing boat full of lanterns on a black lake."}

    async def on_engine(take_id, description, title='', as_given=False):
        drawn_with.append((description, as_given))
        return as_file(drawing())

    monkeypatch.setattr(jobs, "_run_graph", gemma)
    monkeypatch.setattr(jobs, "extract_text_output", lambda job, *kinds: job["written"])
    monkeypatch.setattr(jobs, "_draw_on_engine", on_engine)
    asyncio.run(jobs.run_art(take["id"], on_gpu=True))
    assert asked == [artwork.description_request(take)]
    assert drawn_with == [("A rowing boat full of lanterns on a black lake.", True)]
    got = artwork.info(take["id"])
    assert got["has"] and "Described by Gemma on this PC" in got["words"]
    graph = artwork.picture_graph(drawn_with[0][0], 3, "yeufonic/p", title="Night Fishing", as_given=True)
    assert graph["4"]["inputs"]["text"] == "A rowing boat full of lanterns on a black lake."


def test_about_three_in_ten_image_prompts_ask_for_a_little_wear(client, monkeypatch):
    take = a_take()
    monkeypatch.setattr(artwork, "describer", lambda: "external")
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    monkeypatch.setattr(artwork, "is_well_worn", lambda take=None: True)
    drawn_with = []

    async def describe(record, *args):
        return "A rowing boat full of lanterns on a black lake."

    async def on_engine(take_id, description, title='', as_given=False):
        drawn_with.append(description)
        return as_file(drawing())

    monkeypatch.setattr(artwork, "describe_external", describe)
    monkeypatch.setattr(jobs, "_draw_on_engine", on_engine)
    asyncio.run(jobs.run_art(take["id"]))
    assert drawn_with == [f"A rowing boat full of lanterns on a black lake.\n\n{artwork.KLEIN_WORN}"]


def test_your_own_prompt_leads_the_llms_image_prompt(client, monkeypatch):
    assert artwork.with_own_words("A barber chair in a desert.") == "A barber chair in a desert."     # none set
    set_setting("art.prompt", "  big sky,  doom-laden,. ")
    assert artwork.with_own_words("A barber chair in a desert.") == "big sky, doom-laden, a barber chair in a desert."
    assert artwork.with_own_words("NASA photograph of a chair.") == "big sky, doom-laden, NASA photograph of a chair."
    assert artwork.with_own_words("Paris at dusk, a chair.") == "big sky, doom-laden, paris at dusk, a chair."
    shown = {s["key"]: s for s in client.get("/api/settings").json()["settings"]}
    assert shown["art.prompt"]["value"] == "  big sky,  doom-laden,. " and shown["art.prompt"]["requires"]["art.words"]
    assert shown["art.prompt"]["max_length"] == 512
    assert client.put("/api/settings", json={"key": "art.prompt", "value": "x" * 513}).status_code == 400
    assert client.put("/api/settings", json={"key": "art.prompt", "value": "x" * 512}).status_code == 200
    set_setting("art.prompt", "  big sky,  doom-laden,. ")

    take = a_take()
    monkeypatch.setattr(artwork, "describer", lambda: "external")
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    monkeypatch.setattr(artwork, "is_well_worn", lambda take=None: True)
    drawn_with = []

    async def describe(record, *args):
        return "A rowing boat on a black lake."

    async def on_engine(take_id, description, title='', as_given=False):
        drawn_with.append(description)
        return as_file(drawing())

    monkeypatch.setattr(artwork, "describe_external", describe)
    monkeypatch.setattr(jobs, "_draw_on_engine", on_engine)
    asyncio.run(jobs.run_art(take["id"]))
    assert drawn_with == [f"big sky, doom-laden, a rowing boat on a black lake.\n\n{artwork.KLEIN_WORN}"]


def test_the_song_title_is_lettered_in_a_border_or_now_and_then_over_the_picture(client, monkeypatch):
    take = a_take(title="Corner Shop · sung again")
    assert artwork.title_at(take) is None                                    # off unless Settings ask
    set_setting("art.title", "on")
    assert artwork.title_at({"title": ""}) is None                           # nothing to letter
    places = [artwork.title_at(take) for _ in range(400)]
    assert set(places) == set(artwork.TITLE_BANDS) | set(artwork.TITLE_CORNERS)
    assert 40 < sum(not p.endswith(" band") for p in places) < 130            # about one in five over the picture
    shown = {s["key"]: s for s in client.get("/api/settings").json()["settings"]}
    assert shown["art.title"]["value"] == "on" and shown["art.title"]["default"] == "off"

    # The LLM keeps clear the part of the picture a title goes over; a title in the border needs nothing of it.
    assert "Keep the" not in artwork.description_request(take, "bottom band")
    assert "Keep the" not in artwork.description_request(take)
    asked = artwork.description_request(take, "top left")
    assert "Keep the top left corner of the picture clear and uncluttered for the song's title" in asked
    assert asked.endswith("Reply with the image prompt only.")
    assert "Keep the bottom of the picture clear" in artwork.description_request(take, "bottom centre")

    monkeypatch.setattr(artwork.random, "random", lambda: 0.8)              # small letters
    over = artwork.with_title("A boat.", "Corner Shop", "bottom centre")
    assert over == ('A boat.\n\nAt the bottom of the picture, centred, the title "corner shop" in bold sans-serif '
                    "letters, in a muted colour taken from the picture, with the slightly worn look of print on an old "
                    "sleeve.")
    assert artwork.with_title("A boat.", "Corner Shop", "top right").startswith(
        'A boat.\n\nAt the top right of the picture, the title "corner shop"')

    monkeypatch.setattr(artwork, "describer", lambda: "external")
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    monkeypatch.setattr(artwork, "is_well_worn", lambda take=None: True)
    monkeypatch.setattr(artwork.random, "choice", lambda options: options[0])
    monkeypatch.setattr(artwork.random, "random", lambda: 0.3)              # in the border; capitals
    asked_with, drawn_with = [], []

    async def describe(record, at=None):
        asked_with.append(at)
        return "A rowing boat on a black lake."

    async def on_engine(take_id, description, title='', as_given=False):
        drawn_with.append(description)
        return as_file(drawing())

    monkeypatch.setattr(artwork, "describe_external", describe)
    monkeypatch.setattr(jobs, "_draw_on_engine", on_engine)
    asyncio.run(jobs.run_art(take["id"]))
    assert asked_with == ["top band"]
    assert drawn_with == ["A rowing boat on a black lake.\n\nThe photograph is printed inside a wide off-white border, "
                          "as on a 1970s album sleeve, with a thin dark line framing the photograph: an even margin on "
                          "three sides and a deeper band along the top. In that band, centred, the title "
                          '"CORNER SHOP" in bold sans-serif letters, in a dark colour taken from the photograph. The '
                          f"band is plain, with no box or line around the title.\n\n{artwork.KLEIN_WORN}"]
