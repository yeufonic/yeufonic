"""A take whose model never wrote the song's end runs on to the Length cap.  It is
told apart from a take capped short on purpose by what its score says."""
from app.main import ran_to_cap

from conftest import make_take

# 50 bars of 4/4 at 120: the score says 100 seconds.
ABC = "X:1\nM:4/4\nQ:1/4=120\nK:C\nV:Vocal\n" + "C4 |" * 50 + "\n"


def test_a_render_that_ran_past_its_score_to_the_cap():
    assert ran_to_cap({"duration": 360.0, "max_duration": 360.0, "abc": ABC})


def test_a_take_capped_short_on_purpose_is_not_flagged():
    assert not ran_to_cap({"duration": 60.0, "max_duration": 60.0, "abc": ABC})


def test_a_take_that_ended_on_its_own_is_not_flagged():
    assert not ran_to_cap({"duration": 101.2, "max_duration": 360.0, "abc": ABC})


def test_without_a_score_nothing_is_claimed():
    assert not ran_to_cap({"duration": 360.0, "max_duration": 360.0, "abc": ""})
    assert not ran_to_cap({"duration": None, "max_duration": 360.0, "abc": ABC})


def test_the_library_carries_it(client):
    make_take(abc=ABC, max_duration=360)
    from app.db import execute
    execute("UPDATE takes SET duration = 360.0")
    assert [t["ran_to_cap"] for t in client.get("/api/takes").json()] == [True]


def test_the_ran_to_cap_note_can_be_dismissed_and_a_copy_starts_without_it_dismissed(client):
    from app.db import execute, one
    from conftest import make_take
    take = make_take()
    assert client.get("/api/takes").json()[0]["cap_dismissed"] == 0
    assert client.post(f"/api/takes/{take['id']}/cap/dismiss").json() == {"dismissed": True}
    assert one("SELECT cap_dismissed FROM takes WHERE id = ?", (take["id"],))["cap_dismissed"] == 1
    assert client.post("/api/takes/nosuch/cap/dismiss").status_code == 404
    from app import main
    assert "cap_dismissed" in main._REVOICE_FRESH
