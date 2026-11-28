"""Jam's scratch passes live in a hidden space of their own.

A pass is a real take, so it renders like any other, but it is kept out of the spaces, the library
and Trash.  Takes made from one go to the space its Jam was opened from, as takes of their own."""
from app.db import JAM_SPACE, TRASH_SPACE, execute, one, rows

from conftest import make_take
from test_score import GOOD


def roll(client, **body):
    reply = client.post("/api/jam/roll", json={"title": "Night drive · Pass #1", "style": "synthwave", **body})
    assert reply.status_code == 200, reply.text
    return reply.json()


def a_pass(client, space_id="default"):
    made = roll(client, space_id=space_id, instrumental=False, lyrics="[verse]\nla la la")
    execute("UPDATE takes SET status = 'done', abc = ? WHERE id = ?", (GOOD, made["id"]))
    return made["id"]


def where(take_id):
    return one("SELECT space_id, parent_id, trashed_from FROM takes WHERE id = ?", (take_id,))


def test_a_pass_is_hidden_and_remembers_its_jams_space(client):
    space = client.post("/api/spaces", json={"name": "Ideas"}).json()
    made = roll(client, space_id=space["id"])
    assert where(made["id"]) == {"space_id": JAM_SPACE, "parent_id": None, "trashed_from": space["id"]}
    assert JAM_SPACE not in [s["id"] for s in client.get("/api/spaces").json()]
    assert client.get("/api/takes").json() == []
    assert client.get(f"/api/takes?space_id={space['id']}").json() == []


def test_a_full_song_is_a_take_in_the_jams_space(client):
    space = client.post("/api/spaces", json={"name": "Ideas"}).json()
    made = roll(client, space_id=space["id"], snippet=False, max_duration=360)
    assert where(made["id"]) == {"space_id": space["id"], "parent_id": None, "trashed_from": None}
    # its cap is Settings', which a longer score raises; a pass's length is Jam's
    assert made["cap_typed"] == 0 and made["lyrics"] == "[instrumental]"
    short = roll(client, max_duration=90)
    assert short["cap_typed"] == 1 and short["max_duration"] == 90 and short["lyrics"] == "[intro]\n[verse]"
    assert client.post("/api/jam/roll", json={"snippet": False, "space_id": TRASH_SPACE}).status_code == 400
    assert client.post("/api/jam/roll", json={"snippet": False, "space_id": JAM_SPACE}).status_code == 400


def test_a_pass_for_a_space_that_is_gone_belongs_to_default(client):
    made = roll(client, space_id="gone")
    assert where(made["id"])["trashed_from"] == "default"


def test_deleting_a_pass_is_for_good(client):
    take_id = a_pass(client)
    reply = client.delete(f"/api/takes/{take_id}").json()
    assert reply["permanent"] is True
    assert one("SELECT id FROM takes WHERE id = ?", (take_id,)) is None


def test_the_scratch_space_cannot_be_renamed_deleted_or_moved_into(client):
    take = make_take()
    assert client.put(f"/api/spaces/{JAM_SPACE}", json={"name": "Mine"}).status_code == 400
    assert client.delete(f"/api/spaces/{JAM_SPACE}").status_code == 400
    assert client.post(f"/api/takes/{take['id']}/move", json={"space_id": JAM_SPACE}).status_code == 400
    assert where(take["id"])["space_id"] == "default"
    reply = client.post("/api/songs", json={"lyrics": "[Verse]\nla la", "space_id": JAM_SPACE})
    assert reply.status_code == 400 and "Jam" in reply.json()["detail"]
    # a space of the user's own may share its name
    assert client.post("/api/spaces", json={"name": "Jam Scratch"}).status_code == 200


def test_keeping_a_pass_moves_it_to_a_space(client):
    space = client.post("/api/spaces", json={"name": "Ideas"}).json()
    take_id = a_pass(client, space["id"])
    assert client.post(f"/api/takes/{take_id}/move", json={"space_id": space["id"]}).status_code == 200
    assert where(take_id) == {"space_id": space["id"], "parent_id": None, "trashed_from": None}
    assert [t["id"] for t in client.get(f"/api/takes?space_id={space['id']}").json()] == [take_id]


def test_a_pass_sent_to_trash_restores_to_its_jams_space(client):
    space = client.post("/api/spaces", json={"name": "Ideas"}).json()
    take_id = a_pass(client, space["id"])
    client.post(f"/api/takes/{take_id}/move", json={"space_id": TRASH_SPACE})
    assert where(take_id) == {"space_id": TRASH_SPACE, "parent_id": None, "trashed_from": space["id"]}
    assert client.post(f"/api/takes/{take_id}/restore").json()["space_id"] == space["id"]


def test_takes_made_from_a_pass_go_to_its_jams_space_as_takes_of_their_own(client):
    space = client.post("/api/spaces", json={"name": "Ideas"}).json()
    take_id = a_pass(client, space["id"])
    made = [m["id"] for m in client.post(f"/api/takes/{take_id}/tries", json={"count": 2}).json()["created"]]
    made += [m["id"] for m in client.post(f"/api/takes/{take_id}/variations",
                                          json={"interpretations": ["tight"]}).json()["created"]]
    made.append(client.post(f"/api/takes/{take_id}/revoice").json()["id"])
    made.append(client.post(f"/api/takes/{take_id}/instrumental", json={}).json()["id"])
    for made_id in made:
        assert where(made_id) == {"space_id": space["id"], "parent_id": None, "trashed_from": None}, made_id
    assert rows("SELECT id FROM takes WHERE parent_id = ?", (take_id,)) == []


def test_storage_offers_the_passes_and_clears_them(client, data_dir):
    take_id = a_pass(client)
    folder = data_dir / "takes" / "t-jam"
    folder.mkdir(parents=True)
    audio = folder / "pass.flac"
    audio.write_bytes(b"fLaC" + b"\0" * 4096)
    execute("UPDATE takes SET audio_path = ? WHERE id = ?", (str(audio), take_id))
    kept = make_take()
    item = next(i for i in client.get("/api/storage").json()["items"] if i["id"] == "jam")
    assert item["bytes"] >= 4100 and item["blocked"] is None

    # not while a pass is being made
    cooking = roll(client)
    item = next(i for i in client.get("/api/storage").json()["items"] if i["id"] == "jam")
    assert item["blocked"]
    execute("UPDATE takes SET status = 'done' WHERE id = ?", (cooking["id"],))

    reply = client.post("/api/storage/reclaim", json={"ids": ["jam"]}).json()
    assert reply["freed"] >= 4100
    assert rows("SELECT id FROM takes WHERE space_id = ?", (JAM_SPACE,)) == []
    assert not folder.exists()
    assert one("SELECT id FROM takes WHERE id = ?", (kept["id"],))


def test_a_pass_gets_no_picture_until_it_is_kept(client, monkeypatch):
    from app import artwork, jobs
    started = []
    monkeypatch.setattr(artwork, "automatic", lambda: True)
    monkeypatch.setattr(jobs, "start_art", lambda take_id, style=None: started.append(take_id))
    take_id = a_pass(client)
    jobs.art_for_new_take(take_id)
    assert started == []
    client.post(f"/api/takes/{take_id}/move", json={"space_id": "default"})
    assert started == [take_id]


def test_rock_and_roll_plans_again_and_a_roll_keeps_the_seeds_score(client):
    from app import jobs
    seed = make_take(kind="instrumental", abc=GOOD, lyrics="[intro]\n[verse]\n[chorus]\n[outro]")
    kept = roll(client, base_take_id=seed["id"], lock_score=True)
    assert kept["abc"] and kept["auto_render"] == 0
    planned = roll(client, base_take_id=seed["id"], lock_score=False, structure=seed["lyrics"])
    assert planned["abc"] == "" and planned["auto_render"] == 1
    assert planned["lyrics"] == "[intro]\n[verse]\n[chorus]\n[outro]"
    queued = list(jobs.QUEUE._queue)
    assert [(job["kind"], job["id"]) for job in queued][-2:] == [("render", kept["id"]), ("plan", planned["id"])]
    # a structure the planner cannot follow is planned freely, not refused
    loose = roll(client, structure="[interlude]\n[verse]")
    assert loose["lyrics"] == "[intro]\n[verse]"


def test_the_pass_length_is_a_setting(client):
    spec = {item["key"]: item for item in client.get("/api/settings").json()["settings"]}["jam.pass_seconds"]
    assert spec["default"] == "40" and spec["group"] == "audio"


def test_planning_or_rendering_a_pass_in_the_editor_makes_a_new_take(client):
    space = client.post("/api/spaces", json={"name": "Ideas"}).json()
    take_id = a_pass(client, space["id"])
    before = one("SELECT status, abc, seed, max_duration FROM takes WHERE id = ?", (take_id,))
    rendered = client.post(f"/api/takes/{take_id}/render", json={}).json()
    planned = client.post(f"/api/takes/{take_id}/replan", json={}).json()
    for reply in (rendered, planned):
        made = one("SELECT space_id, parent_id, title, cap_typed, max_duration, status FROM takes WHERE id = ?", (reply["id"],))
        assert reply["id"] != take_id
        assert made["space_id"] == space["id"] and made["parent_id"] is None and made["status"] == "queued"
        assert made["title"] == "Night drive · Pass #1" and made["cap_typed"] == 0 and made["max_duration"] > 40
    # the pass itself is as it was, still a scratch pass
    assert one("SELECT status, abc, seed, max_duration FROM takes WHERE id = ?", (take_id,)) == before
    assert where(take_id)["space_id"] == JAM_SPACE
    # a take of the person's own is still planned and rendered in place
    own = make_take(abc=GOOD)
    assert client.post(f"/api/takes/{own['id']}/render", json={}).json()["id"] == own["id"]


def test_a_score_edited_in_the_editor_goes_onto_the_new_take_not_the_pass(client):
    space = client.post("/api/spaces", json={"name": "Ideas"}).json()
    take_id = a_pass(client, space["id"])
    before = one("SELECT abc FROM takes WHERE id = ?", (take_id,))["abc"]
    edited = before.replace("Q:1/4=", "Q:1/4=1", 1) if "Q:1/4=" in before else before + "\n"
    assert edited != before
    made = client.post(f"/api/takes/{take_id}/render", json={"abc": edited}).json()
    assert one("SELECT abc FROM takes WHERE id = ?", (made["id"],))["abc"] == edited
    assert one("SELECT abc FROM takes WHERE id = ?", (take_id,))["abc"] == before
    # a take of the person's own ignores it: its score is saved with the score route
    own = make_take(abc=GOOD)
    client.post(f"/api/takes/{own['id']}/render", json={"abc": "X:1"})
    assert one("SELECT abc FROM takes WHERE id = ?", (own["id"],))["abc"] == GOOD


def test_a_pass_can_start_at_a_section_of_the_kept_score(client):
    body = GOOD[GOOD.index("% intro"):]
    two = GOOD.rstrip("\n") + "\n" + body.replace("% intro", "% chorus")
    seed = make_take(abc=two, lyrics="[intro]\n\n[verse]\nla la la\n\n[chorus]\nhey hey\n")
    marks = [line for line in two.splitlines() if line.startswith("% ")]
    later = marks[1][2:].strip()
    made = roll(client, base_take_id=seed["id"], lock_score=True, instrumental=False,
                lyrics=seed["lyrics"], start_section=later)
    abc = made["abc"]
    assert abc.startswith("X:1") and "K:" in abc
    assert [line for line in abc.splitlines() if line.startswith("% ")][0] == marks[1]
    # a section the score does not have leaves it whole
    whole = roll(client, base_take_id=seed["id"], lock_score=True, instrumental=True, start_section="coda")
    assert [line for line in whole["abc"].splitlines() if line.startswith("% ")][0] == marks[0]


def test_jam_sync_wiring_and_transport_hooks():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent / "app" / "static"
    jam_js = (root / "jam.js").read_text(encoding="utf-8")
    app_js = (root / "app.js").read_text(encoding="utf-8")
    css = (root / "styles.css").read_text(encoding="utf-8")

    # Sync button in Roll History header, click handler, and 0/1-9 keyboard jump
    assert 'data-jam-act="toggle-sync"' in jam_js
    assert "act === 'toggle-sync'" in jam_js
    assert "linearRampToValueAtTime(target, now + 0.008)" in jam_js
    assert "if (JamSync.enabled) { JamSync.disable({ handoff: true }); }" in jam_js
    assert "function jumpToSyncPass(num)" in jam_js
    assert "/^[0-9]$/.test(event.key)" in jam_js
    assert ".jam-sync-btn.on" in css

    # Bottom transport bar delegates cleanly to Jam Sync when active
    for hook in ("isSyncActive", "isSyncPlaying", "syncClock", "syncSeek", "syncNudge", "onVolumeChange", "onRateChange", "stopSyncForMain"):
        assert hook in jam_js, f"Missing window.Jam.{hook} export in jam.js"
        assert hook in app_js, f"Missing window.Jam.{hook} hook in app.js"

    # Jam lyrics button in Vocals row and shared lyrics modal hook
    html = (root / "index.html").read_text(encoding="utf-8")
    assert 'data-jam-act="edit-lyrics"' in jam_js
    assert "window.openLyricsEditor" in jam_js and "window.openLyricsEditor = openLyricsEditor" in app_js
    assert 'id="lyrics-reset"' in html and 'id="lyrics-modal-write"' in html
    assert "#lyrics-modal { z-index: 70; }" in css and "#write-modal { z-index: 72; }" in css


def test_jam_edited_lyrics_align_to_vocal_seed_and_plan_from_instrumental_seed(client):
    from app import instrumental, jobs

    # 1. Vocal Seed with edited lyrics keeps the locked score and aligns the new words.
    vocal_seed = make_take(kind="song", abc=GOOD, lyrics="[verse]\nOld harbour lights\n")
    edited = "[verse]\nNew lantern glow\n"
    p1 = roll(client, base_take_id=vocal_seed["id"], lock_score=True, instrumental=False, lyrics=edited)
    assert p1["lyrics"] == edited.strip()
    assert p1["auto_render"] == 0 and p1["abc"].startswith("X:1")
    assert one("SELECT lyrics FROM takes WHERE id = ?", (vocal_seed["id"],))["lyrics"] == "[verse]\nOld harbour lights\n"
    assert list(jobs.QUEUE._queue)[-1]["kind"] == "render"

    # 2. Instrumental Seed turned into a vocal pass cannot lock onto an unsung score: it plans a vocal melody.
    inst_abc = instrumental.tune_on_instrument(GOOD)
    assert not instrumental.sings(inst_abc)
    inst_seed = make_take(kind="instrumental", abc=inst_abc, lyrics="[verse]")
    added = "[verse]\nSinging over the tide\n"
    p2 = roll(client, base_take_id=inst_seed["id"], lock_score=True, instrumental=False, lyrics=added)
    assert p2["kind"] == "song" and p2["lyrics"] == added.strip()
    assert p2["abc"] == "" and p2["auto_render"] == 1
    assert list(jobs.QUEUE._queue)[-1]["kind"] == "plan"
