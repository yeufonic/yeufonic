"""Make a new picture with a new prompt: an art style typed for one picture, in place of Settings' (which stays)."""
from app import artwork, jobs
from app.db import set_setting
from conftest import make_take


def test_a_style_typed_for_one_picture_replaces_settings_for_that_take_only(client, monkeypatch):
    monkeypatch.setattr(artwork, "words_by_engine", lambda: True)    # waits in the GPU lane: nothing starts here
    set_setting("art.style", "pastel watercolours")
    take, other = make_take(title="Copper Fields"), make_take(title="Glass Harbour")
    jobs.ART_WAITING.clear()
    jobs.start_art(take["id"], "  bold linocut, two colours  ")
    assert artwork.art_style(take["id"]) == "bold linocut, two colours"
    assert artwork.art_style(other["id"]) == "pastel watercolours"
    assert "Album art style: bold linocut, two colours" in artwork.description_request(take)
    assert "in this style: bold linocut, two colours" in artwork.take_description(take, scene="a lighthouse")
    assert "Hipgnosis" in artwork.take_description(other, scene="a lighthouse")
    assert artwork.info(take["id"])["style"] == "bold linocut, two colours"
    # The take's next picture without one goes back to Settings'.
    jobs.start_art(take["id"])
    assert artwork.art_style(take["id"]) == "pastel watercolours"
    assert artwork.info(take["id"])["style"] == "pastel watercolours"
    jobs.ART_WAITING.clear()
    artwork.STATE.clear()


def test_the_route_takes_a_style_for_one_picture(client, monkeypatch):
    asked = []
    monkeypatch.setattr(jobs, "start_art", lambda take_id, style=None: asked.append((take_id, style)))
    monkeypatch.setattr(artwork, "drawing_problem", lambda: None)
    take = make_take(title="Copper Fields")
    assert client.post(f"/api/takes/{take['id']}/art").status_code == 200
    assert client.post(f"/api/takes/{take['id']}/art", json={"style": "ink and wash"}).status_code == 200
    assert asked == [(take["id"], None), (take["id"], "ink and wash")]
    assert client.post(f"/api/takes/{take['id']}/art", json={"style": "x" * 4001}).status_code == 422
