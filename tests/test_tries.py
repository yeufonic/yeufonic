"""Try more: the same score and words rendered again as a set of new takes."""
from app import jobs, loras
from app.db import execute, one, rows

from conftest import make_take
from test_score import GOOD


def queued():
    return [job["id"] for job in list(jobs.QUEUE._queue) if job["kind"] == "render"]


def a_take(**fields):
    take = make_take(abc=GOOD, status="done", title="Night drive", seed=111, **fields)
    return take


def test_new_seeds_come_out_as_takes_beside_the_original(client):
    take = a_take()
    reply = client.post(f"/api/takes/{take['id']}/tries", json={"mode": "seeds", "count": 3})
    assert reply.status_code == 200
    made = reply.json()["created"]
    assert [m["title"] for m in made] == ["Night drive · try 1", "Night drive · try 2", "Night drive · try 3"]
    seeds = {m["seed"] for m in made}
    assert len(seeds) == 3 and take["seed"] not in seeds
    assert queued() == [m["id"] for m in made]
    row = one("SELECT * FROM takes WHERE id = ?", (made[0]["id"],))
    assert row["status"] == "queued" and row["abc"] == GOOD and row["lyrics"] == take["lyrics"]
    assert row["style"] == take["style"] and row["max_duration"] == take["max_duration"]
    assert row["space_id"] == one("SELECT space_id FROM takes WHERE id = ?", (take["id"],))["space_id"]
    assert row["audio_path"] is None and row["favourite"] == 0


def test_the_numbering_carries_on_and_a_try_is_named_for_its_original(client):
    take = a_take()
    client.post(f"/api/takes/{take['id']}/tries", json={"count": 2})
    again = client.post(f"/api/takes/{take['id']}/tries", json={"count": 2}).json()["created"]
    assert [m["title"] for m in again] == ["Night drive · try 3", "Night drive · try 4"]
    # A try is kept inside its original and holds none of its own.  Taken out, it can be tried
    # again, and the suffix does not stack.
    second = one("SELECT * FROM takes WHERE title = 'Night drive · try 2'")
    assert client.post(f"/api/takes/{second['id']}/tries", json={"count": 1}).status_code == 400
    client.post(f"/api/takes/{second['id']}/promote")
    more = client.post(f"/api/takes/{second['id']}/tries", json={"count": 1}).json()["created"]
    assert more[0]["title"] == "Night drive · try 5"


def test_planner_strengths_keep_the_seed_and_skip_the_takes_own(client, monkeypatch):
    monkeypatch.setattr(loras, "describe", lambda name, root: {"name": name, "kind": "both"})
    take = a_take()
    execute("UPDATE takes SET style_lora = 'folk_band_lora.safetensors', style_lora_model = 0.6, style_lora_clip = 0.8 WHERE id = ?", (take["id"],))
    reply = client.post(f"/api/takes/{take['id']}/tries", json={"mode": "planner", "planner": [0.6, 0.8, 1.0, 1.0]})
    assert reply.status_code == 200
    made = reply.json()["created"]
    assert [m["title"] for m in made] == ["Night drive · planner 0.60", "Night drive · planner 1.00"]
    assert [m["style_lora_clip"] for m in made] == [0.6, 1.0]
    for m in made:
        row = one("SELECT * FROM takes WHERE id = ?", (m["id"],))
        assert row["seed"] == 111 and row["style_lora"] == "folk_band_lora.safetensors" and row["style_lora_model"] == 0.6
    # And a planner try, taken out and tried again, is still named for the original.
    client.post(f"/api/takes/{made[0]['id']}/promote")
    again = client.post(f"/api/takes/{made[0]['id']}/tries", json={"mode": "seeds", "count": 1}).json()["created"]
    assert again[0]["title"] == "Night drive · try 1"


def test_it_says_why_it_cannot(client, monkeypatch):
    plain = a_take()
    assert client.post(f"/api/takes/{plain['id']}/tries", json={"mode": "planner", "planner": [0.6]}).status_code == 400
    assert client.post("/api/takes/nope/tries", json={}).status_code == 404
    unplanned = make_take(abc="", status="done")
    assert client.post(f"/api/takes/{unplanned['id']}/tries", json={}).status_code == 400
    lora = a_take()
    execute("UPDATE takes SET style_lora = 'sound_only.safetensors', style_lora_clip = 0.0 WHERE id = ?", (lora["id"],))
    monkeypatch.setattr(loras, "describe", lambda name, root: {"name": name, "kind": "decoder"})
    refused = client.post(f"/api/takes/{lora['id']}/tries", json={"mode": "planner", "planner": [0.6]})
    assert refused.status_code == 400 and "planner half" in refused.json()["detail"]
    monkeypatch.setattr(loras, "describe", lambda name, root: {"name": name, "kind": "both"})
    execute("UPDATE takes SET style_lora_clip = 0.8 WHERE id = ?", (lora["id"],))
    assert client.post(f"/api/takes/{lora['id']}/tries", json={"mode": "planner", "planner": [0.8]}).status_code == 400
    assert client.post(f"/api/takes/{lora['id']}/tries", json={"mode": "planner", "planner": [3.5]}).status_code == 400
    assert client.post(f"/api/takes/{plain['id']}/tries", json={"count": 9}).status_code == 422


def test_the_cap_can_be_set_for_the_tries_only(client):
    take = a_take()
    made = client.post(f"/api/takes/{take['id']}/tries", json={"count": 1, "max_duration": 75}).json()["created"]
    assert one("SELECT max_duration FROM takes WHERE id = ?", (made[0]["id"],))["max_duration"] == 75
    assert one("SELECT max_duration FROM takes WHERE id = ?", (take["id"],))["max_duration"] == take["max_duration"]
