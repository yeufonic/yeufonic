"""Sampling values set by hand (#72): over Plan variety and the Interpretation, kept with the take, carried by its
recipe, and kept by Variations only when asked."""
import json

import pytest

from app import jobs
from app.db import execute, one
from conftest import make_take

ABC = ('X:1\nM:4/4\nL:1/8\nQ:1/4=100\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\nK:C\n'
       '% verse\nV: Vocal\n' + '"C"c4|"Am"A4|"F"F4|"G"G4|' * 4 + '\n')
CUSTOM = {"plan": {"temperature": 0.9, "top_k": 40}, "render": {"top_k": 50, "repetition_penalty": 1.1}}


def test_only_the_values_given_are_kept_and_each_is_checked():
    assert jobs.clean_sampling(None) is None and jobs.clean_sampling({}) is None
    assert jobs.clean_sampling({"plan": {"temperature": "", "top_k": None}, "render": {}}) is None
    assert jobs.clean_sampling(json.dumps(CUSTOM)) == CUSTOM
    assert jobs.clean_sampling({"render": {"top_k": 50.0}}) == {"render": {"top_k": 50}}
    assert jobs.clean_sampling({"plan": {"temperature": 0.9}, "other": {"x": 1}}) == {"plan": {"temperature": 0.9}}
    for bad in ({"plan": {"temperature": 3}}, {"render": {"top_p": 0}}, {"render": {"top_k": 501}},
                {"plan": {"repetition_penalty": 0.9}}, {"plan": {"top_k": "many"}}, {"plan": {"top_k": True}}, "{"):
        with pytest.raises(ValueError):
            jobs.clean_sampling(bad)


def test_a_value_set_replaces_that_one_and_the_rest_follow_the_presets():
    take = make_take(variety="lively", interpretation="wide", sampling=json.dumps(CUSTOM), abc=ABC)
    plan = jobs.build_plan_graph(take)["2"]["inputs"]
    assert plan["temperature"] == 0.9 and plan["top_k"] == 40                     # set by hand
    assert plan["repetition_penalty"] == jobs.PLAN_VARIETY["lively"]["repetition_penalty"] and plan["top_p"] == 0.9
    render = jobs.build_render_graph(take)["11"]["inputs"]
    assert render["top_k"] == 50 and render["repetition_penalty"] == 1.1
    assert render["top_p"] == 0.99 and render["temperature"] == 1.0                # Wide's own, and Standard's
    plain = make_take(variety="lively", interpretation="wide", abc=ABC)
    assert jobs.build_render_graph(plain)["11"]["inputs"]["top_k"] == 250
    assert jobs.build_plan_graph(plain)["2"]["inputs"]["top_k"] == 30


def test_the_values_are_kept_with_a_take_and_cleared_by_sending_none(client):
    made = client.post("/api/songs", json={"title": "Glass Harbour", "style": "rock", "lyrics": "[Verse]\nla",
                                           "sampling": CUSTOM}).json()
    assert json.loads(one("SELECT sampling FROM takes WHERE id = ?", (made["id"],))["sampling"]) == CUSTOM
    execute("UPDATE takes SET status = 'planned', abc = ? WHERE id = ?", (ABC, made["id"]))
    # A render that says nothing about them keeps them; one that sends {} (the boxes cleared) takes them away.
    assert client.post(f"/api/takes/{made['id']}/render", json={}).status_code == 200
    assert one("SELECT sampling FROM takes WHERE id = ?", (made["id"],))["sampling"] is not None
    execute("UPDATE takes SET status = 'planned' WHERE id = ?", (made["id"],))
    assert client.post(f"/api/takes/{made['id']}/render", json={"sampling": {}}).status_code == 200
    assert one("SELECT sampling FROM takes WHERE id = ?", (made["id"],))["sampling"] is None


def test_a_value_out_of_range_is_refused(client):
    r = client.post("/api/songs", json={"title": "T", "style": "rock", "lyrics": "[Verse]\nla",
                                        "sampling": {"plan": {"temperature": 5}}})
    assert r.status_code == 400 and "temperature" in r.text


def test_variations_keep_the_music_values_only_when_asked(client):
    take = make_take(title="Copper Fields", abc=ABC, status="done", sampling=json.dumps(CUSTOM))
    plain = client.post(f"/api/takes/{take['id']}/variations", json={"interpretations": ["tight"]}).json()["created"][0]
    kept = client.post(f"/api/takes/{take['id']}/variations",
                       json={"interpretations": ["loose"], "keep_sampling": True}).json()["created"][0]
    assert json.loads(one("SELECT sampling FROM takes WHERE id = ?", (plain["id"],))["sampling"]) == {"plan": CUSTOM["plan"]}
    assert json.loads(one("SELECT sampling FROM takes WHERE id = ?", (kept["id"],))["sampling"]) == CUSTOM


def test_sing_again_keeps_the_values_but_not_the_note(client):
    take = make_take(title="Copper Fields", abc=ABC, status="done", sampling=json.dumps(CUSTOM), take_note="keep the bridge")
    again = client.post(f"/api/takes/{take['id']}/revoice").json()
    row = one("SELECT sampling, take_note FROM takes WHERE id = ?", (again["id"],))
    assert json.loads(row["sampling"]) == CUSTOM and row["take_note"] is None


def test_the_recipe_carries_the_values_and_an_import_keeps_them(client):
    take = make_take(title="Copper Fields", abc=ABC, status="done", sampling=json.dumps(CUSTOM))
    data = client.get(f"/api/takes/{take['id']}/recipe").json()
    assert data["take"]["sampling"] == CUSTOM
    got = client.post("/api/takes/import", json={"recipe": data, "space_id": "default"}).json()
    assert json.loads(one("SELECT sampling FROM takes WHERE id = ?", (got["id"],))["sampling"]) == CUSTOM
    data["take"]["sampling"] = {"render": {"top_k": 9999}}
    assert client.post("/api/takes/import", json={"recipe": data, "space_id": "default"}).status_code == 400


def test_the_page_is_told_each_presets_values():
    presets = jobs.sampling_presets()
    assert presets["plan"]["calm"] == {"top_p": 0.9, "top_k": 30, "temperature": 0.55, "repetition_penalty": 1.0}
    assert presets["render"]["wide"]["top_k"] == 250 and presets["render"]["tight"]["temperature"] == 0.8
    assert presets["limits"]["top_k"] == [1, 500]


def test_the_log_lines_name_the_settings_changed_from_their_defaults():
    assert jobs.custom_said(make_take()) == ""
    said = jobs.custom_said(make_take(target_key="D", target_meter="3/4", chord_hold_limit=4, voice_cues=0,
                                      fade_out_seconds=5.0, chord_sections=1, target_lufs=-14.0))
    assert said == (", custom: key lock=D; time signature=3/4; chord hold limit=4; sections open differently=always; "
                    "voice cues=off; outro fade=5.0")
    take = make_take(sampling=json.dumps(CUSTOM))
    assert jobs.sampling_said(take, "plan") == ", sampling temperature=0.9 top_k=40"
    assert jobs.sampling_said(take, "render") == ", sampling top_k=50 repetition_penalty=1.1"


def test_a_failed_plan_says_which_custom_values_it_ran_with(caplog):
    take = make_take(title="Copper Fields", sampling=json.dumps(CUSTOM), target_key="D")
    with caplog.at_level("WARNING"):
        jobs.fail("plan", take["id"], "the score could not be read")
    assert ("the score could not be read (made with sampling temperature=0.9 top_k=40; custom: key lock=D)"
            in caplog.text)


def test_a_covers_render_line_says_planner_values_were_not_used():
    cover = make_take(kind="cover", sampling=json.dumps({"plan": {"temperature": 0.9}}))
    assert jobs.sampling_said(cover, "render") == ", planner sampling set but not used (a cover plays its recording's score)"
    song = make_take(kind="song", sampling=json.dumps({"plan": {"temperature": 0.9}}))
    assert jobs.sampling_said(song, "render") == ""
