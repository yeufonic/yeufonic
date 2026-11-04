"""A song sung with no score (YuE2 composing as it sings), and Follow the style (the music stage's guidance, CFG):
what the app asks each engine for, and what a take with no score can and cannot do."""
from app import engine_cpp, jobs
from app.db import execute, one
from app.engine_cpp import translate
from app.jobs import build_render_graph

from conftest import make_take

WORDS = "[Verse]\nLanterns on the water\n\n[Chorus]\nCarry me home"
TAKE = {"id": "t1", "kind": "song", "style": "indie pop", "lyrics": WORDS, "abc": "X:1\nK:C\nV: Vocal\nc4|\n", "seed": 42,
        "mode": "full", "max_duration": 120}


def queued():
    out = []
    while not jobs.QUEUE.empty():
        out.append(jobs.QUEUE.get_nowait())
    return out


def options(monkeypatch, **values):
    monkeypatch.setattr(jobs.ENGINE, "options", {**(jobs.ENGINE.options or {}), **values})


# ---------- what the engines are asked for
def test_no_score_sends_an_empty_score_to_both_engines():
    graph = build_render_graph({**TAKE, "mode": "off"})
    node = graph["11"]["inputs"]
    # ComfyUI's node lists only full and melody; an empty score is its "off".
    assert node["abc"] == "" and node["mode"] == "full"
    body = translate(graph)["body"]
    # yue2.cpp would write a plan first for an empty score in full: it is asked for off.
    assert body["abc"] == "" and body["cot"] == "off"
    assert "cfg_scale" not in body                    # its own guidance for off, 1.01


def test_a_scored_take_is_unchanged():
    body = translate(build_render_graph(TAKE))["body"]
    assert body["cot"] == "full" and body["abc"].startswith("X:1") and "cfg_scale" not in body


def test_follow_the_style_reaches_an_engine_that_has_it(monkeypatch):
    options(monkeypatch, cfg=True)
    graph = build_render_graph({**TAKE, "cfg_scale": 1.3})
    assert graph["11"]["inputs"]["cfg_scale"] == 1.3
    assert translate(graph)["body"]["cfg_scale"] == 1.3


def test_follow_the_style_is_left_out_for_an_engine_without_it(monkeypatch):
    """A ComfyUI from before the input was added would refuse a graph naming it."""
    options(monkeypatch, cfg=False)
    assert "cfg_scale" not in build_render_graph({**TAKE, "cfg_scale": 1.3})["11"]["inputs"]


def test_comfyui_reports_the_guidance_input():
    """Read from its music node's optional inputs: a ComfyUI from before 2026-10 has none."""
    import asyncio
    import httpx
    from app.engine import Engine
    combo = lambda field, names: {"input": {"required": {field: [names]}}}

    def detected(optional):
        info = {"CheckpointLoaderSimple": combo("ckpt_name", []),
                "YuE2GenerateMusic": {"input": {"required": {}, "optional": optional}}}

        async def run():
            engine = Engine("http://engine")
            engine.client = httpx.AsyncClient(base_url="http://engine",
                                              transport=httpx.MockTransport(lambda r: httpx.Response(200, json=info)))
            await engine.refresh_options()
            await engine.client.aclose()
            return engine.options["cfg"]
        return asyncio.run(run())
    assert detected({"abc": {}, "cfg_scale": {}}) is True
    assert detected({"abc": {}}) is False


# ---------- making and remaking a song with no score
def test_a_song_with_no_score_is_rendered_at_once(client):
    queued()
    got = client.post("/api/songs", json={"style": "dream pop", "lyrics": WORDS, "mode": "off", "cfg_scale": 1.2})
    assert got.status_code == 200, got.text
    take = one("SELECT * FROM takes WHERE id = ?", (got.json()["id"],))
    assert take["mode"] == "off" and take["abc"] == "" and take["cfg_scale"] == 1.2
    assert queued() == [{"kind": "render", "id": take["id"]}]


def test_a_song_otherwise_is_planned_first(client):
    queued()
    got = client.post("/api/songs", json={"style": "dream pop", "lyrics": WORDS, "mode": "melody"}).json()
    assert one("SELECT mode FROM takes WHERE id = ?", (got["id"],))["mode"] == "full"
    assert queued() == [{"kind": "plan", "id": got["id"]}]


def test_a_take_with_no_score_renders_sings_again_and_tries_more(client):
    take = make_take(mode="off", abc="", lyrics=WORDS)
    queued()
    assert client.post(f"/api/takes/{take['id']}/render", json={}).status_code == 200
    again = client.post(f"/api/takes/{take['id']}/revoice")
    assert again.status_code == 200, again.text
    assert one("SELECT mode, abc FROM takes WHERE id = ?", (again.json()["id"],))["mode"] == "off"
    execute("UPDATE takes SET status = 'done' WHERE id = ?", (take["id"],))
    assert client.post(f"/api/takes/{take['id']}/variations", json={"interpretations": ["tight"]}).status_code == 200
    assert client.post(f"/api/takes/{take['id']}/tries", json={"count": 2}).status_code == 200
    assert {job["kind"] for job in queued()} == {"render"}


def test_a_scored_take_can_be_rendered_with_no_score_and_keeps_its_score(client):
    take = make_take(abc=TAKE["abc"] * 4, lyrics=WORDS)
    assert client.post(f"/api/takes/{take['id']}/render", json={"mode": "off"}).status_code == 200
    row = one("SELECT mode, abc FROM takes WHERE id = ?", (take["id"],))
    assert row["mode"] == "off" and row["abc"].startswith("X:1")
    assert build_render_graph({**row, **{k: take[k] for k in ("id", "style", "lyrics", "seed", "max_duration")},
                               "kind": "song"})["11"]["inputs"]["abc"] == ""


def test_a_render_beside_it_has_no_score(client):
    take = make_take(abc=TAKE["abc"] * 4, lyrics=WORDS, status="done")
    got = client.post(f"/api/takes/{take['id']}/rearrange", json={"abc": "", "mode": "off"})
    assert got.status_code == 200, got.text
    row = one("SELECT mode, abc FROM takes WHERE id = ?", (got.json()["id"],))
    assert row["mode"] == "off" and row["abc"] == ""


def test_new_words_with_no_score(client):
    take = make_take(mode="off", abc="", lyrics=WORDS, status="done")
    got = client.post(f"/api/takes/{take['id']}/words", json={"lyrics": "[Verse]\nOther words entirely"})
    assert got.status_code == 200, got.text
    row = one("SELECT mode, abc, lyrics FROM takes WHERE id = ?", (got.json()["id"],))
    assert row["mode"] == "off" and row["abc"] == "" and "Other words" in row["lyrics"]


def test_only_a_song_from_a_prompt_has_no_score(client):
    cover = make_take(kind="cover", source_id="s1", abc=TAKE["abc"] * 4)
    assert client.post(f"/api/takes/{cover['id']}/render", json={"mode": "off"}).status_code == 400
    inst = make_take(kind="instrumental", abc=TAKE["abc"] * 4)
    assert client.post(f"/api/takes/{inst['id']}/render", json={"mode": "off"}).status_code == 400


def test_a_new_plan_gives_it_a_score_again(client):
    take = make_take(mode="off", abc="", lyrics=WORDS, status="done")
    queued()
    assert client.post(f"/api/takes/{take['id']}/replan", json={}).status_code == 200
    assert one("SELECT mode FROM takes WHERE id = ?", (take["id"],))["mode"] == "full"
    assert queued() == [{"kind": "plan", "id": take["id"]}]


def test_a_take_with_no_score_waiting_at_shutdown_is_rendered(data_dir):
    import asyncio
    from fastapi.testclient import TestClient
    from app.main import app
    take = make_take(status="queued", mode="off", abc="")
    queued()
    original = jobs.worker
    jobs.worker = lambda: asyncio.sleep(3600)
    try:
        with TestClient(app, base_url="http://localhost"):
            got = queued()
    finally:
        jobs.worker = original
    assert {"kind": "render", "id": take["id"]} in got


def test_its_recipe_goes_and_comes_back_with_no_score(client):
    take = make_take(mode="off", abc="", lyrics=WORDS, status="done", cfg_scale=1.4, seed=5)
    recipe = client.get(f"/api/takes/{take['id']}/recipe").json()
    assert recipe["take"]["mode"] == "off" and recipe["take"]["cfg_scale"] == 1.4
    got = client.post("/api/takes/import", json={"recipe": recipe})
    assert got.status_code == 200, got.text
    row = one("SELECT mode, abc, cfg_scale FROM takes WHERE id = ?", (got.json()["id"],))
    assert row["mode"] == "off" and row["abc"] == "" and row["cfg_scale"] == 1.4


def test_a_recipe_with_no_score_and_no_mode_saying_so_is_still_refused(client):
    take = make_take(abc=TAKE["abc"] * 4, lyrics=WORDS, status="done")
    recipe = client.get(f"/api/takes/{take['id']}/recipe").json()
    recipe["take"]["score"] = ""
    for key in ("abc", "score"):
        recipe["take"].pop(key, None)
    assert client.post("/api/takes/import", json={"recipe": recipe}).status_code == 400


def test_follow_the_style_is_kept_and_reset(client):
    take = make_take(abc=TAKE["abc"] * 4, lyrics=WORDS)
    client.post(f"/api/takes/{take['id']}/render", json={"cfg_scale": 1.6})
    assert one("SELECT cfg_scale FROM takes WHERE id = ?", (take["id"],))["cfg_scale"] == 1.6
    execute("UPDATE takes SET status = 'done' WHERE id = ?", (take["id"],))
    client.post(f"/api/takes/{take['id']}/render", json={"cfg_scale": None})
    assert one("SELECT cfg_scale FROM takes WHERE id = ?", (take["id"],))["cfg_scale"] is None
    assert client.post("/api/songs", json={"lyrics": WORDS, "cfg_scale": 101}).status_code == 422
    assert client.post("/api/songs", json={"lyrics": WORDS, "cfg_scale": 7.5}).status_code == 200


def test_the_page_is_told_whether_the_engine_has_it(client, monkeypatch):
    options(monkeypatch, cfg=True)
    assert client.get("/api/state").json()["options"]["cfg_available"] is True
    options(monkeypatch, cfg=False)
    assert client.get("/api/state").json()["options"]["cfg_available"] is False


def test_a_database_a_branch_moved_on_still_gets_the_column(data_dir):
    from app import db
    db.execute("ALTER TABLE takes DROP COLUMN cfg_scale")
    db.conn().execute("PRAGMA user_version = 43")
    db.migrate()
    assert "cfg_scale" in db._columns("takes")


def test_the_render_log_says_which_cfg_is_used(monkeypatch):
    """ComfyUI does not log it, so the app does."""
    options(monkeypatch, cfg=True)
    assert jobs.cfg_said({"cfg_scale": 1.5}) == "cfg=1.5"
    assert jobs.cfg_said({}) == "cfg=1.0 (the engine's own)"
    assert jobs.cfg_said({"mode": "off"}) == "cfg=1.01 (the engine's own)"
    options(monkeypatch, cfg=False)
    assert "1.5 was asked for" in jobs.cfg_said({"cfg_scale": 1.5})
