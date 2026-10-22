"""Hum to song: a recording's tune as the hook of a song the planner writes around it."""
from app import composer, jobs
from app.db import execute, one

# A hum as the transcriber can write it: the tune in Ins, the Vocal voice all rests, silence
# before it and after it, and a header that names the voices in its own way.
HUM = """X:1
T:
M:4/4
L:1/16
Q:1/4=104
V: Vocal clef=treble name="Vocal Melody" snm="Vocal"
V: Ins clef=treble name="Ins Melody" snm="Inst."
K:Cm
% verse
V: Vocal
Z4|
V: Ins
Z|z8z2F4F2|E8z4F4-|F2z2E4C2E2C4|
V: Vocal
Z3|
V: Ins
z4D4C4B,4|"Fm"C4z12|Z|
"""


def test_the_hook_is_the_tune_in_the_planners_layout():
    hook = composer.hook_of(HUM)
    assert hook.head == ('X:1\nT:\nM:4/4\nL:1/16\nQ:1/4=104\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\n'
                         'V: Ins clef=treble name="Ins Melody" snm="Inst."\nK:Cm\n')
    # The bar of silence before the tune and the one after it are left out; the tune is in Vocal,
    # four bars to a block, a chord kept where the transcriber heard one, and Ins rests bar for bar.
    assert hook.body == ("V: Vocal\nz8z2F4F2|E8z4F4-|F2z2E4C2E2C4|z4D4C4B,4|\nV: Ins\nz16|z16|z16|z16|\n"
                         'V: Vocal\n"Fm"C4z12|\nV: Ins\nz16|\n')
    assert (hook.key, hook.bpm, hook.bars) == ("Cm", 104, 5)
    assert "%" not in hook.body, "the planner names the sections; the hook is only bars"


def test_a_tune_in_the_vocal_voice_is_kept_with_what_ins_plays():
    abc = 'X:1\nM:3/4\nL:1/8\nQ:1/4=90\nK:G\nV: Vocal\n"G"B2d2g2|a6|\nV: Ins\nZ2|\n'
    hook = composer.hook_of(abc)
    assert "M:3/4\nL:1/8\nQ:1/4=90" in hook.head and hook.head.endswith("K:G\n")
    assert hook.body == 'V: Vocal\n"G"B2d2g2|a6|\nV: Ins\nZ2|\n'


def test_a_score_with_no_notes_has_no_hook():
    import pytest
    with pytest.raises(composer.NoMelody):
        composer.hook_of("X:1\nM:4/4\nL:1/4\nK:C\nV: Vocal\nZ4|\nV: Ins\nZ4|\n")


def _source(sid="hum1", abc=HUM, title="Hum"):
    execute("""INSERT INTO sources(id, title, filename, stored_path, sha256, created_at, abc, transcribe_state, origin)
               VALUES(?, ?, 'melody.wav', '/tmp/melody.wav', ?, 1000.0, ?, 'done', 'recording')""",
            (sid, title, sid, abc))
    return sid


def test_a_hum_becomes_a_cover_whose_plan_follows_its_structure_with_the_hook(client):
    sid = _source()
    res = client.post("/api/composer/expand", json={"source_id": sid, "preset": "short", "role": "chorus",
                                                     "style": "folk, acoustic guitar"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert (data["section"], data["bars"], data["key"], data["bpm"]) == ("chorus", 5, "Cm", 104)
    take = one("SELECT * FROM takes WHERE id = ?", (data["take_id"],))
    # A cover of the recording, whose score the planner writes: not a song from a prompt.
    assert take["kind"] == "cover" and take["source_id"] == sid and take["follow_structure"] == 1
    assert take["status"] == "queued" and take["abc"] == ""
    assert take["auto_render"] == 1, "rendered once the plan is written: the workflow ends in a cover"
    assert take["title"] == "Hum (Full Song)" and take["style"] == "folk, acoustic guitar, male vocals"
    assert take["lyrics"] == "[Verse 1]\n\n[Chorus]\n\n[Verse 2]\n\n[Chorus]\n\n[Outro]"
    hook = composer.hook_of(HUM)
    assert take["hook_abc"] == hook.head + hook.body and take["hook_section"] == "chorus"
    # The key and tempo come from the hook's header, which the plan opens with: no lock to move them.
    assert take["target_key"] is None and take["target_bpm"] is None

    node = jobs.build_plan_graph(take)["2"]
    assert node["class_type"] == jobs.HARMONY_NODE
    inputs = node["inputs"]
    assert inputs["hook_head"] == hook.head and inputs["hook_body"] == hook.body and inputs["hook_section"] == "chorus"
    assert inputs["follow_sections"] == "verse,chorus,verse,chorus,outro"


def test_the_words_in_the_lyrics_box_are_the_structure(client):
    sid = _source()
    words = "[Verse]\nA line\n\n[Chorus]\nThe hook line"
    res = client.post("/api/composer/expand", json={"source_id": sid, "role": "verse", "lyrics": words})
    assert res.status_code == 200, res.text
    take = one("SELECT lyrics, hook_section FROM takes WHERE id = ?", (res.json()["take_id"],))
    assert take["lyrics"] == words and take["hook_section"] == "verse"


def test_a_structure_with_no_place_for_the_tune_is_refused(client):
    sid = _source()
    res = client.post("/api/composer/expand", json={"source_id": sid, "preset": "aaba", "role": "chorus"})
    assert res.status_code == 400 and "[Chorus]" in res.json()["detail"]
    res = client.post("/api/composer/expand", json={"source_id": sid, "role": "chorus", "lyrics": "[Verse]\nOnly a verse"})
    assert res.status_code == 400 and "lyrics" in res.json()["detail"]


def test_a_recording_with_no_tune_is_refused(client):
    silent = _source("hum2", "X:1\nM:4/4\nL:1/4\nK:C\nV: Vocal\nZ4|\nV: Ins\nZ4|\n")
    assert client.post("/api/composer/expand", json={"source_id": silent}).status_code == 400
    untranscribed = _source("hum3", "")
    res = client.post("/api/composer/expand", json={"source_id": untranscribed})
    assert res.status_code == 400 and "Transcribe" in res.json()["detail"]
    assert client.post("/api/composer/expand", json={"source_id": "nonexistent"}).status_code == 404
    assert client.post("/api/composer/expand", json={}).status_code == 400
    assert client.post("/api/composer/expand", json={"abc": HUM}).status_code == 400, "a cover needs its recording"


def test_an_engine_that_cannot_hold_a_tune_is_told_to_be_rebuilt(client, monkeypatch):
    sid = _source()
    monkeypatch.setattr(jobs.ENGINE, "options_loaded", True)
    monkeypatch.setattr(jobs.ENGINE, "options", {**jobs.ENGINE.options, "hook": False})
    res = client.post("/api/composer/expand", json={"source_id": sid})
    assert res.status_code == 400 and "Rebuild" in res.json()["detail"]


def test_a_cover_made_from_a_hum_can_have_its_plan_written_again(client):
    sid = _source()
    take_id = client.post("/api/composer/expand", json={"source_id": sid}).json()["take_id"]
    execute("UPDATE takes SET status = 'planned', abc = 'X:1' WHERE id = ?", (take_id,))
    res = client.post(f"/api/takes/{take_id}/replan", json={})
    assert res.status_code == 200, res.text
    take = one("SELECT status, abc, hook_abc FROM takes WHERE id = ?", (take_id,))
    assert take["status"] == "queued" and take["abc"] == "" and take["hook_abc"], "the tune is held again"
    # A plain cover's score is its recording's transcription: nothing to write again.
    execute("UPDATE takes SET hook_abc = NULL, status = 'planned' WHERE id = ?", (take_id,))
    assert client.post(f"/api/takes/{take_id}/replan", json={}).status_code == 400


def test_a_plan_without_a_hook_is_unchanged(client):
    sid = _source()
    take_id = client.post("/api/composer/expand", json={"source_id": sid}).json()["take_id"]
    take = dict(one("SELECT * FROM takes WHERE id = ?", (take_id,)))
    take.update({"hook_abc": None, "hook_section": None, "follow_structure": 0})
    inputs = jobs.build_plan_graph(take)["2"]["inputs"]
    assert not any(name.startswith("hook_") for name in inputs)


def test_the_options_list_the_structures(client):
    data = client.get("/api/composer/options").json()
    assert {p["id"] for p in data["presets"]} == {"standard", "short", "aaba"}
