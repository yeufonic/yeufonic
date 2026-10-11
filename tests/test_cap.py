"""The length cap: where a new take's comes from, and a planned take's rising to fit its plan.

A cap is a firm limit, not a target.  A plan longer than its take's cap would be cut short by
it, so a cap nobody set by hand is raised when the plan lands, by the sum a recording's score
sets its cap with: the length and ten seconds, rounded up to ten, and never over 900."""
import asyncio
from pathlib import Path

import pytest

from app import config, jobs, main, score
from app.db import execute, one
from conftest import make_take
from test_jobs import FakeEngine, PLAN_GRAPH, done, use

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def plan(bars: int, bpm: int = 120) -> str:
    """A readable plan of `bars` bars of 4/4: two seconds a bar at 120."""
    head = f'X:1\nM:4/4\nL:1/8\nQ:1/4={bpm}\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\nK:C\n% verse\nV: Vocal\n'
    return head + '"C"c2d2e2f2|"Am"A2B2c2d2|"F"F2G2A2B2|"G"G2A2B2c2|' * (bars // 4) + "\n"


@pytest.mark.parametrize("seconds, cap, typed, wanted", [
    (400, 360, 0, 410),          # longer than the cap: room for it and ten seconds
    (401, 360, None, 420),       # rounded up to ten; a take from before the setting counts as not typed
    (300, 360, 0, None),         # it fits: the cap stands, and is never brought down
    (360, 360, 0, 370),          # exactly the cap leaves no room to end in
    (400, 360, 1, None),         # set by hand: it stands, and the Score page says the plan will be cut
    (880, 600, 0, 890),
    (896, 600, 0, 900),          # never over what the engine allows
])
def test_the_cap_a_plan_needs(seconds, cap, typed, wanted, monkeypatch):
    monkeypatch.setattr(score, "estimate", lambda abc: {"seconds": float(seconds), "bars": 1, "bpm": 120})
    assert jobs.cap_for_plan("a plan", cap, typed) == wanted


def test_a_plan_that_cannot_be_measured_leaves_the_cap(monkeypatch):
    monkeypatch.setattr(score, "estimate", lambda abc: None)
    assert jobs.cap_for_plan("", 360, 0) is None


def landed(monkeypatch, abc: str, **fields) -> dict:
    later = ("cap_typed", "target_bpm")                   # columns make_take does not write
    take = make_take(status="queued", **{key: value for key, value in fields.items() if key not in later})
    for key in later:
        if key in fields:
            execute(f"UPDATE takes SET {key} = ? WHERE id = ?", (fields[key], take["id"]))
    use(monkeypatch, FakeEngine([None, done({"3": {"text": [abc]}}, PLAN_GRAPH)]))
    asyncio.run(jobs.run_job("plan", take["id"]))
    return one("SELECT * FROM takes WHERE id = ?", (take["id"],))


def test_a_plan_longer_than_its_cap_raises_it(monkeypatch):
    long = plan(200)                                      # 400 seconds
    assert score.estimate(long)["seconds"] == 400
    row = landed(monkeypatch, long, max_duration=360)
    assert row["status"] == "planned" and row["max_duration"] == 410

    row = landed(monkeypatch, long, max_duration=360, cap_typed=1)
    assert row["status"] == "planned" and row["max_duration"] == 360      # set by hand: it stands

    row = landed(monkeypatch, plan(100), max_duration=360)
    assert row["max_duration"] == 360                                     # the plan fits: nothing to do


def test_a_tempo_lock_counts_before_the_cap_is_fitted(monkeypatch):
    """The plan is made to say the locked tempo before it is measured, so the cap fits what is sung."""
    row = landed(monkeypatch, plan(200, bpm=120), max_duration=360, target_bpm=100)   # 200 bars at 100: 480 s
    assert row["max_duration"] == 490


def test_a_plan_far_past_its_cap_is_still_not_a_song(monkeypatch):
    """Raising the cap does not let a runaway plan through: one a third longer than a long cap,
    or over eight minutes with a short one, is written again as before."""
    take = make_take(status="queued", max_duration=360)
    jobs.RETRIED_PLANS.add(take["id"])                    # already tried once: this one fails
    use(monkeypatch, FakeEngine([None, done({"3": {"text": [plan(260)]}}, PLAN_GRAPH)]))   # 520 seconds
    asyncio.run(jobs.run_job("plan", take["id"]))
    row = one("SELECT * FROM takes WHERE id = ?", (take["id"],))
    assert row["status"] == "failed" and "minutes long" in row["error"] and row["max_duration"] == 360


def test_whose_cap_it_is(client):
    """A cap that was sent is someone's, unless the page says it only sent what the box held;
    a cap that was not sent is the one in Settings, and nobody's."""
    body = {"title": "S", "style": "rock", "lyrics": "[Verse]\nla la"}
    plain = client.post("/api/songs", json=body).json()
    assert (plain["max_duration"], plain["cap_typed"]) == (360, 0)
    asked = client.post("/api/songs", json={**body, "max_duration": 200}).json()
    assert (asked["max_duration"], asked["cap_typed"]) == (200, 1)
    untouched = client.post("/api/songs", json={**body, "max_duration": 360, "cap_typed": False}).json()
    assert (untouched["max_duration"], untouched["cap_typed"]) == (360, 0)
    typed = client.post("/api/songs", json={**body, "max_duration": 360, "cap_typed": True}).json()
    assert typed["cap_typed"] == 1
    inst = client.post("/api/instrumentals", json={"style": "ambient", "structure": "[intro]\n[verse]"}).json()
    assert (inst["max_duration"], inst["cap_typed"]) == (360, 0)


def test_the_cap_of_a_new_take_is_a_setting(client):
    spec = {item["key"]: item for item in client.get("/api/state").json()["settings"]}["takes.cap"]
    assert spec["value"] == "360" and [o["value"] for o in spec["options"]] == ["240", "360", "480", "600", "900"]
    assert client.put("/api/settings", json={"key": "takes.cap", "value": "600"}).status_code == 200
    body = {"title": "S", "style": "rock", "lyrics": "[Verse]\nla la"}
    assert client.post("/api/songs", json=body).json()["max_duration"] == 600
    assert client.post("/api/songs", json={**body, "max_duration": 120}).json()["max_duration"] == 120
    assert client.put("/api/settings", json={"key": "takes.cap", "value": "123"}).status_code == 400
    assert main.default_cap() == 600


def test_the_built_in_cap_can_come_from_the_environment(monkeypatch):
    for given, wanted in (("600", 600), ("450", 450), ("5", 10), ("5000", 900), ("ten", 360), ("", 360)):
        monkeypatch.setenv("DEFAULT_CAP", given)
        assert config._default_cap() == wanted
    monkeypatch.delenv("DEFAULT_CAP")
    assert config._default_cap() == 360


def test_the_page_says_whose_cap_it_is_and_takes_up_a_raised_one():
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert app_js.count("cap_typed: Boolean(State.capTyped)") == 2          # a song and an instrumental
    assert "State.capTyped = take.cap_typed === 1;" in app_js
    assert "if (!State.capTyped && take.max_duration) { $('max-duration').value = Math.round(take.max_duration); }" in app_js
    assert "box.value = defaultCap();" in app_js
