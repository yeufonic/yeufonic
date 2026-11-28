"""Tests for per-take advanced settings: storage, API validation, replan/render persistence, and propagation."""
import pytest
from app.db import one, execute
from test_jobs import fast  # noqa: F401,E402 - the job loop's waits take no time


def test_song_creation_with_advanced_settings(client):
    payload = {
        "title": "Advanced Song",
        "style": "indie rock",
        "lyrics": "[Verse]\nHello world",
        "sampler_steps": 40,
        "avoid": "electronic beats, synth lead",
        "target_key": "F#m",
        "target_bpm": 115,
        "max_abc_tokens": 4096,
        "chord_hold_limit": 6,
        "chord_outside_bonus": 2.0,
        "target_lufs": -12.5,
        "fade_out_seconds": 5.0,
    }
    res = client.post("/api/songs", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["sampler_steps"] == 40
    assert data["avoid"] == "electronic beats, synth lead"
    assert data["target_key"] == "F#m"
    assert data["target_bpm"] == 115
    assert data["max_abc_tokens"] == 4096
    assert data["chord_hold_limit"] == 6
    assert data["chord_outside_bonus"] == 2.0
    assert data["target_lufs"] == -12.5
    assert data["fade_out_seconds"] == 5.0

    # Verify DB row
    row = one("SELECT * FROM takes WHERE id = ?", (data["id"],))
    assert row["sampler_steps"] == 40
    assert row["avoid"] == "electronic beats, synth lead"
    assert row["target_key"] == "F#m"
    assert row["target_bpm"] == 115
    assert row["max_abc_tokens"] == 4096
    assert row["chord_hold_limit"] == 6
    assert row["chord_outside_bonus"] == 2.0
    assert row["target_lufs"] == -12.5
    assert row["fade_out_seconds"] == 5.0


def test_song_creation_defaults_when_omitted(client):
    payload = {
        "title": "Plain Song",
        "style": "ambient",
        "lyrics": "[Verse]\nCalm waters",
    }
    res = client.post("/api/songs", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["sampler_steps"] == 32
    assert data["avoid"] in ("", None)
    assert data["target_key"] in ("", None)
    assert data["target_bpm"] is None
    assert data["max_abc_tokens"] == 8192
    assert data["chord_hold_limit"] == 8
    assert data["chord_outside_bonus"] == 0.0
    assert data["target_lufs"] is None
    assert data["fade_out_seconds"] == 3.0


def test_replan_updates_advanced_settings(client):
    res = client.post("/api/songs", json={"title": "Replan Test", "lyrics": "[Verse]\nLa"})
    take_id = res.json()["id"]
    execute("UPDATE takes SET status = 'planned' WHERE id = ?", (take_id,))

    replan_payload = {
        "sampler_steps": 48,
        "avoid": "brass",
        "target_key": "Gm",
        "target_bpm": 90,
        "max_abc_tokens": 1024,
        "chord_hold_limit": 3,
        "chord_outside_bonus": 1.0,
        "target_lufs": -16.0,
        "fade_out_seconds": 2.0,
    }
    res_replan = client.post(f"/api/takes/{take_id}/replan", json=replan_payload)
    assert res_replan.status_code == 200, res_replan.text

    row = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    assert row["sampler_steps"] == 48
    assert row["avoid"] == "brass"
    assert row["target_key"] == "Gm"
    assert row["target_bpm"] == 90
    assert row["max_abc_tokens"] == 1024
    assert row["chord_hold_limit"] == 3
    assert row["chord_outside_bonus"] == 1.0
    assert row["target_lufs"] == -16.0
    assert row["fade_out_seconds"] == 2.0


def test_render_updates_advanced_settings(client):
    res = client.post("/api/songs", json={"title": "Render Test", "lyrics": "[Verse]\nLa"})
    take_id = res.json()["id"]

    abc = ('X:1\nM:4/4\nL:1/8\nQ:1/4=100\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\nK:C\n'
           '% verse\nV: Vocal\n' + '"C"c4|"Am"A4|"F"F4|"G"G4|' * 4 + '\n')
    execute("UPDATE takes SET status = 'planned', abc = ? WHERE id = ?", (abc, take_id))

    render_payload = {
        "sampler_steps": 50,
        "avoid": "snare drum",
        "target_key": "C#",
        "target_bpm": 140,
        "target_lufs": -11.0,
        "fade_out_seconds": 4.5,
    }
    res_render = client.post(f"/api/takes/{take_id}/render", json=render_payload)
    assert res_render.status_code == 200, res_render.text

    row = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    assert row["sampler_steps"] == 50
    assert row["avoid"] == "snare drum"
    assert row["target_key"] == "C#"
    assert row["target_bpm"] == 140
    assert row["target_lufs"] == -11.0
    assert row["fade_out_seconds"] == 4.5


def test_a_tempo_lock_is_written_into_the_plan(monkeypatch):
    """The planner treats the BPM in the style as a hint and wrote its own 102; a locked
    take's saved score says the locked tempo."""
    import asyncio
    from app import jobs
    from conftest import make_take
    from test_jobs import ABC, PLAN_GRAPH, FakeEngine, done, use

    take = make_take(status="queued")
    execute("UPDATE takes SET target_bpm = 80 WHERE id = ?", (take["id"],))
    use(monkeypatch, FakeEngine([None, done({"3": {"text": [ABC.replace("Q:1/4=100", "Q:1/4=102")]}}, PLAN_GRAPH)]))
    asyncio.run(jobs.run_job("plan", take["id"]))
    row = one("SELECT status, abc FROM takes WHERE id = ?", (take["id"],))
    assert row["status"] == "planned"
    assert "Q:1/4=80" in row["abc"] and "102" not in row["abc"]


def test_lock_tempo():
    from app.jobs import lock_tempo
    assert lock_tempo("X:1\nL:1/8\nQ:120\nK:C\nc[Q:1/4=90]d|", 80) == "X:1\nL:1/8\nQ:1/4=80\nK:C\nc[Q:1/4=80]d|"
    assert lock_tempo("X:1\nL:1/8\nK:C\ncd|", 70) == "X:1\nL:1/8\nQ:1/4=70\nK:C\ncd|"
    assert lock_tempo("X:1\nQ:1/4=100\n", None) == "X:1\nQ:1/4=100\n"


# ------------------------------------------------------- Reset to defaults really resets

NULLS = {"sampler_steps": 32, "avoid": None, "target_key": None, "target_bpm": None, "max_abc_tokens": 8192,
         "chord_hold_limit": 8, "chord_outside_bonus": 0.0, "target_lufs": None, "fade_out_seconds": 3.0}
CUSTOM = {"sampler_steps": 40, "avoid": "brass", "target_key": "Am", "target_bpm": 115, "max_abc_tokens": 2048,
          "chord_hold_limit": 4, "chord_outside_bonus": 6.0, "target_lufs": -12.0, "fade_out_seconds": 7.0}
DEFAULTS = {"sampler_steps": 32, "avoid": None, "target_key": None, "target_bpm": None, "max_abc_tokens": 8192,
            "chord_hold_limit": 8, "chord_outside_bonus": 0.0, "target_lufs": None, "fade_out_seconds": 3.0}


def advanced_of(take_id):
    row = one("SELECT * FROM takes WHERE id = ?", (take_id,))
    return {key: row[key] for key in CUSTOM}


def a_planned_take(client):
    from test_score import GOOD
    made = client.post("/api/songs", json={"title": "R", "style": "rock", "lyrics": "[Verse]\nla", **CUSTOM}).json()
    execute("UPDATE takes SET status = 'planned', abc = ? WHERE id = ?", (GOOD, made["id"]))
    assert advanced_of(made["id"]) == CUSTOM
    return made["id"]


def test_what_the_page_sends_after_reset_puts_every_setting_back_to_its_default(client):
    take_id = a_planned_take(client)
    assert client.post(f"/api/takes/{take_id}/render", json=NULLS).status_code == 200
    assert advanced_of(take_id) == DEFAULTS                     # the nulls are the default, not "keep the old value"


def test_a_render_that_says_nothing_about_them_keeps_what_the_take_has(client):
    take_id = a_planned_take(client)
    assert client.post(f"/api/takes/{take_id}/render", json={"seed": 7}).status_code == 200
    assert advanced_of(take_id) == CUSTOM                       # an older page, or one that left them out
    execute("UPDATE takes SET status = 'planned' WHERE id = ?", (take_id,))
    assert client.post(f"/api/takes/{take_id}/render", json={"target_bpm": None}).status_code == 200
    now = advanced_of(take_id)
    assert now["target_bpm"] is None and now["target_key"] == "Am" and now["sampler_steps"] == 40     # only what was sent


def test_replan_resets_them_too(client):
    take_id = a_planned_take(client)
    assert client.post(f"/api/takes/{take_id}/replan", json=NULLS).status_code == 200
    assert advanced_of(take_id) == DEFAULTS


def test_new_words_take_the_panels_settings_and_otherwise_the_takes(client):
    take_id = a_planned_take(client)
    execute("UPDATE takes SET status = 'done' WHERE id = ?", (take_id,))
    same = client.post(f"/api/takes/{take_id}/words", json={"lyrics": "[Verse]\nlo"}).json()
    assert advanced_of(same["id"]) == CUSTOM
    changed = client.post(f"/api/takes/{take_id}/words", json={"lyrics": "[Verse]\nli", **NULLS}).json()
    assert advanced_of(changed["id"]) == DEFAULTS


# ------------------------------------------------------- the locks are said once, in the planner's words

def test_a_tempo_in_the_style_is_replaced_by_the_lock_not_added_to():
    from app import jobs
    style = "Afrobeats, buoyant groove, 104 BPM, auto-tuned vocals"
    locked = jobs.effective_style(style, target_bpm=80)
    assert locked == "Afrobeats, buoyant groove, 80 BPM, auto-tuned vocals"
    assert jobs.effective_style("rock, drums", target_bpm=80) == "rock, drums, 80 BPM"           # none to replace: added
    assert jobs.effective_style(style) == style                                                   # no lock, no change


def test_a_key_is_written_the_way_the_training_captions_write_it():
    from app import jobs
    assert jobs.effective_style("rock", target_key="Cm") == "rock, key of C minor"
    assert jobs.effective_style("rock", target_key="F#") == "rock, key of F#"
    assert jobs.effective_style("rock", target_key="Eb") == "rock, key of Eb"
    assert jobs.effective_style("rock, key of D minor, 90 BPM", target_key="A", target_bpm=120) == "rock, key of A, 120 BPM"
    assert jobs.effective_style("", target_key="Am", target_bpm=90) == "key of A minor, 90 BPM"


def test_avoid_is_added_once():
    from app import jobs
    assert jobs.effective_style("rock", avoid="brass, synths") == "rock, avoid: brass, synths"
    assert jobs.effective_style("rock, avoid: brass", avoid="brass") == "rock, avoid: brass"


def test_a_plan_is_stored_at_the_locked_tempo(monkeypatch):
    """The planner may still write its own tempo; the plan the person sees and the render reads says the lock."""
    import asyncio
    from app import jobs
    from conftest import make_take
    from test_score import GOOD, PlanEngine
    real_sleep = asyncio.sleep
    monkeypatch.setattr(jobs.asyncio, "sleep", lambda _s: real_sleep(0))
    monkeypatch.setattr(jobs, "ENGINE", PlanEngine(GOOD))                  # GOOD says Q:1/4=97
    take = make_take(status="queued")
    execute("UPDATE takes SET target_bpm = 80 WHERE id = ?", (take["id"],))
    asyncio.run(jobs.run_job("plan", take["id"]))
    stored = one("SELECT status, abc FROM takes WHERE id = ?", (take["id"],))
    assert stored["status"] == "planned" and "Q:1/4=80" in stored["abc"] and "Q:1/4=97" not in stored["abc"]
    unlocked = make_take(status="queued")
    asyncio.run(jobs.run_job("plan", unlocked["id"]))
    assert "Q:1/4=97" in one("SELECT abc FROM takes WHERE id = ?", (unlocked["id"],))["abc"]


# ------------------------------------------------ sections open differently

def test_sections_open_differently_follows_the_harmony_step_unless_forced(monkeypatch):
    from app import jobs
    from conftest import make_take
    plan = lambda harmony, sections: jobs.build_plan_graph(make_take(harmony=harmony, chord_sections=sections))["2"]
    assert plan(0, None)["class_type"] != jobs.HARMONY_NODE                                # Familiar: the stock planner
    assert plan(1, None)["inputs"]["section_strength"] == 0.0                                 # Varied: off
    assert plan(2, None)["inputs"]["section_strength"] == jobs.SECTION_STRENGTH               # Colourful and up: on
    assert plan(0, 1)["class_type"] == jobs.HARMONY_NODE                                      # forced on at Familiar
    assert plan(0, 1)["inputs"]["section_strength"] == jobs.SECTION_STRENGTH
    assert plan(1, 1)["inputs"]["section_strength"] == jobs.SECTION_STRENGTH
    assert plan(3, 0)["inputs"]["section_strength"] == 0.0                                    # forced off at Adventurous
    assert plan(0, 0)["class_type"] != jobs.HARMONY_NODE


def test_sections_open_differently_is_kept_with_the_take_and_null_means_follow(client):
    res = client.post("/api/songs", json={"title": "S", "style": "rock", "lyrics": "[Verse]\nhi", "chord_sections": 1})
    assert res.status_code == 200, res.text
    take = res.json()
    assert take["chord_sections"] == 1
    assert client.post("/api/songs", json={"title": "S", "style": "rock", "lyrics": "[Verse]\nhi"}).json()["chord_sections"] is None
    assert client.post("/api/songs", json={"title": "S", "style": "rock", "lyrics": "[Verse]\nhi", "chord_sections": 2}).status_code == 422
    execute("UPDATE takes SET status = 'planned', abc = ? WHERE id = ?", ("X:1\nK:C\nV: Vocal\n" + "z8|" * 40, take["id"]))
    assert client.post(f"/api/takes/{take['id']}/replan", json={"chord_sections": 0}).status_code == 200
    assert one("SELECT chord_sections FROM takes WHERE id = ?", (take["id"],))["chord_sections"] == 0
    execute("UPDATE takes SET status = 'planned' WHERE id = ?", (take["id"],))
    assert client.post(f"/api/takes/{take['id']}/replan", json={"chord_sections": None}).status_code == 200
    assert one("SELECT chord_sections FROM takes WHERE id = ?", (take["id"],))["chord_sections"] is None


# ------------------------------------------------------ follow my structure exactly

def test_the_sections_a_plan_must_follow_come_from_the_lyric_tags():
    from app import lyrics
    text = "Title: x\n[Intro]\nhum\n\n[Verse 2]\nwords\n\n[Pre-Chorus]\nlift\n\n[Chorus]\nhook\n\n[Instrumental]\n\n[Verse 2: stripped back]\nnot a section\n[Outro]"
    assert lyrics.plan_names(text) == ["intro", "verse", "pre-chorus", "chorus", "interlude", "outro"]
    assert lyrics.plan_names("") == []


def test_following_the_structure_is_written_into_the_plan_request_for_songs_only():
    from app import jobs
    from conftest import make_take
    words = "[Verse]\na\n\n[Chorus]\nb\n\n[Instrumental]\n\n[Chorus]\nb"
    node = lambda **f: jobs.build_plan_graph(make_take(lyrics=words, **f))["2"]
    assert node(follow_structure=1)["class_type"] == jobs.HARMONY_NODE                       # even at Familiar
    assert node(follow_structure=1)["inputs"]["follow_sections"] == "verse,chorus,interlude,chorus"
    assert "follow_sections" not in node(follow_structure=None)["inputs"]
    # An instrumental's tags are its structure, chosen as such: followed whether or not the song tick is on.
    assert node(follow_structure=None, kind="instrumental")["inputs"]["follow_sections"] == "verse,chorus,interlude,chorus"
    assert node(follow_structure=1, harmony=2)["inputs"]["section_strength"] == jobs.SECTION_STRENGTH   # alongside the chord nudge


def test_following_the_structure_is_kept_with_the_take(client):
    body = {"title": "S", "style": "rock", "lyrics": "[Verse]\nhi\n[Chorus]\nyo", "follow_structure": 1}
    take = client.post("/api/songs", json=body).json()
    assert take["follow_structure"] == 1
    assert client.post("/api/songs", json={k: v for k, v in body.items() if k != "follow_structure"}).json()["follow_structure"] is None
    assert client.post("/api/songs", json={**body, "follow_structure": 2}).status_code == 422


# ------------------------------------------------------------------- time signature

def test_a_time_signature_opens_the_plan_with_its_meter():
    from app import jobs
    from conftest import make_take
    plan = lambda **f: jobs.build_plan_graph(make_take(**f))["2"]
    assert plan()["class_type"] != jobs.HARMONY_NODE                       # Auto: the stock planner
    waltz = plan(target_meter="3/4")
    assert waltz["class_type"] == jobs.HARMONY_NODE
    assert waltz["inputs"]["hook_head"] == "X:1\nT:\nM:3/4\n"
    assert plan(target_meter="11/8")["class_type"] != jobs.HARMONY_NODE    # not one it can be held to: Auto
    tune = "X:1\nT:\nM:4/4\nL:1/8\nK:C\n"
    held = plan(target_meter="6/8", hook_abc=tune + "cdef|\n", hook_section="chorus")["inputs"]
    assert held["hook_head"] == tune, "a recorded tune's own header wins"


def test_a_time_signature_is_kept_with_the_take(client):
    res = client.post("/api/songs", json={"style": "folk pop", "lyrics": "[verse]\nla la la", "target_meter": "6/8"})
    assert res.status_code == 200
    assert one("SELECT target_meter FROM takes WHERE id = ?", (res.json()["id"],))["target_meter"] == "6/8"
    assert client.post("/api/songs", json={"style": "folk pop", "lyrics": "[verse]\nla", "target_meter": "11/8"}).status_code == 422


def test_an_engine_that_can_keep_the_time_signature_is_told_to(monkeypatch):
    from app import jobs
    from conftest import make_take
    monkeypatch.setattr(jobs.ENGINE, "options", {"hold_meter": True}, raising=False)
    assert jobs.build_plan_graph(make_take(target_meter="3/4"))["2"]["inputs"]["hold_meter"] is True
    monkeypatch.setattr(jobs.ENGINE, "options", {}, raising=False)
    assert "hold_meter" not in jobs.build_plan_graph(make_take(target_meter="3/4"))["2"]["inputs"]


def test_meter_left():
    from app.jobs import meter_left
    assert meter_left("X:1\nM:3/4\nK:D\nV: Vocal\nM:4/4\nz16|", "3/4")
    assert meter_left("X:1\nM:3/4\nK:D\nz12|[M:4/4]z16|", "3/4")
    assert not meter_left("X:1\nM:3/4\nK:D\nz12|", "3/4")
    assert not meter_left("X:1\nM:4/4\nK:D\nz16|", None)


def test_a_plan_that_leaves_its_time_signature_is_written_once_more_then_kept(monkeypatch):
    import asyncio
    from app import jobs
    from conftest import make_take
    from test_jobs import ABC, PLAN_GRAPH, FakeEngine, done, use
    take = make_take(status="queued")
    execute("UPDATE takes SET target_meter = '3/4' WHERE id = ?", (take["id"],))
    wandered = ABC.replace("K:", "M:4/4\nK:", 1) if "M:" not in ABC else ABC
    use(monkeypatch, FakeEngine([None, done({"3": {"text": [wandered]}}, PLAN_GRAPH)]))
    asyncio.run(jobs.run_job("plan", take["id"]))
    assert one("SELECT status FROM takes WHERE id = ?", (take["id"],))["status"] == "queued", "written once more"
    assert jobs.QUEUE.get_nowait() == {"kind": "plan", "id": take["id"]}
    execute("UPDATE takes SET status = 'queued' WHERE id = ?", (take["id"],))
    use(monkeypatch, FakeEngine([None, done({"3": {"text": [wandered]}}, PLAN_GRAPH)]))
    asyncio.run(jobs.run_job("plan", take["id"]))
    assert one("SELECT status FROM takes WHERE id = ?", (take["id"],))["status"] == "planned", "the second is kept"


def test_a_plan_whose_bars_are_not_the_meters_length_left_it():
    from app.jobs import bars_fit, meter_left
    five = "X:1\nM:5/4\nL:1/16\nK:D\nV: Vocal\n" + '"D"d16|' * 6 + "\n"         # bars of four under a 5/4 head
    assert bars_fit(five, "5/4") == 0.0 and meter_left(five, "5/4")
    kept = "X:1\nM:5/4\nL:1/16\nK:D\nV: Vocal\nZ2|\n" + '"D"d16e4|' * 6 + "\n"
    assert bars_fit(kept, "5/4") == 1.0 and not meter_left(kept, "5/4")
    eighths = "X:1\nM:12/8\nL:1/8\nK:D\nV: Vocal\n" + "d3e3f3g3|" * 4 + "\n"
    assert not meter_left(eighths, "12/8")


def test_the_meter_the_bars_make():
    from app.jobs import meter_written
    assert meter_written("X:1\nM:5/4\nL:1/16\nK:D\nV: Vocal\n" + '"D"d16|' * 6) == "4/4"
    assert meter_written("X:1\nL:1/8\nK:D\nV: Vocal\n" + "d3e4|" * 5) == "7/8"
    assert meter_written("X:1\nL:1/8\nK:D\n") is None


def test_a_number_outside_its_usual_range_is_kept_and_only_the_impossible_refused(client):
    """The page flags a value outside a setting's usual range and sends it as typed; the server keeps it and refuses
    only what cannot work (never changing a value)."""
    unusual = {"sampler_steps": 80, "target_bpm": 30, "max_abc_tokens": 256, "chord_hold_limit": 40,
               "chord_outside_bonus": 15.0, "target_lufs": -30.0, "fade_out_seconds": 25.0}
    r = client.post("/api/songs", json={"title": "Glass Harbour", "style": "rock", "lyrics": "[Verse]\nla", **unusual})
    assert r.status_code == 200, r.text
    row = one("SELECT * FROM takes WHERE id = ?", (r.json()["id"],))
    for key, value in unusual.items():
        assert row[key] == value, key
    for impossible in ({"sampler_steps": 0}, {"target_bpm": 1000}, {"max_abc_tokens": 9000}, {"chord_hold_limit": 65},
                       {"chord_outside_bonus": 21}, {"target_lufs": 1}, {"fade_out_seconds": 0}, {"sampler_steps": 32.5}):
        assert client.post("/api/songs", json={"title": "T", "style": "rock", "lyrics": "[Verse]\nla", **impossible}).status_code == 422, impossible


def test_an_instrumentals_timed_structure_is_followed_and_one_from_a_recording_or_of_one_tag_is_not():
    """Timed sections, as the page sends them, on one line: each name is a section the plan must write, in order. A
    long one was planned as a fraction of itself before (6 sections of 23)."""
    from app import jobs, lyrics
    from conftest import make_take
    timed = " ".join(f"[{name} {i}:00-{i}:30]" for i, name in enumerate(["intro", "verse", "chorus", "bridge", "outro"]))
    assert lyrics.structure_names(timed) == ["intro", "verse", "chorus", "bridge", "outro"]
    node = lambda **f: jobs.build_plan_graph(make_take(kind="instrumental", **f))["2"]["inputs"]
    assert node(lyrics=timed)["follow_sections"] == "intro,verse,chorus,bridge,outro"
    assert "follow_sections" not in node(lyrics="[instrumental]")          # Let YuE2 decide: nothing to follow
