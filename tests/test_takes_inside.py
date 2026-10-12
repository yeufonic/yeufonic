"""Takes made from a take are kept inside it.

Variations, Try more and Checkpoints fill a space with takes that all belong to one song.  They
go inside the take they were made from: the list shows that take, which says how many it holds,
and the takes inside are asked for by name."""
import json
import subprocess
from pathlib import Path

from app.db import execute, one, rows

from conftest import make_take
from test_score import GOOD


def a_take(**fields):
    return make_take(abc=GOOD, **{"status": "done", "title": "Night drive", "seed": 111, **fields})


def listed(client, **params):
    return client.get("/api/takes", params={"space_id": "default", **params}).json()


def finish(*ids):
    for take_id in ids:
        execute("UPDATE takes SET status = 'done' WHERE id = ?", (take_id,))


def tries(client, take, count=3):
    reply = client.post(f"/api/takes/{take['id']}/tries", json={"count": count})
    assert reply.status_code == 200
    return [made["id"] for made in reply.json()["created"]]


# ------------------------------------------------------------------ where the new takes go
def test_tries_and_variations_go_inside_the_take_they_were_made_from(client):
    take = a_take()
    tried = tries(client, take, 2)
    varied = [m["id"] for m in client.post(f"/api/takes/{take['id']}/variations",
                                           json={"interpretations": ["tight", "loose"]}).json()["created"]]
    for made in tried + varied:
        assert one("SELECT parent_id FROM takes WHERE id = ?", (made,))["parent_id"] == take["id"]
    assert one("SELECT parent_id FROM takes WHERE id = ?", (take["id"],))["parent_id"] is None


def test_the_list_shows_the_take_and_says_how_many_it_holds(client):
    take, other = a_take(), a_take(title="Harbour")
    made = tries(client, take, 3)
    finish(made[0])
    got = listed(client)
    assert sorted(t["id"] for t in got) == sorted([take["id"], other["id"]])
    mine = next(t for t in got if t["id"] == take["id"])
    assert (mine["children"], mine["children_pending"]) == (1, 2)
    theirs = next(t for t in got if t["id"] == other["id"])
    assert (theirs["children"], theirs["children_pending"]) == (0, 0)
    assert client.get("/api/takes", params={"space_id": "default"}).headers["X-Total-Count"] == "2"


def test_the_takes_inside_show_once_they_are_finished(client):
    take = a_take()
    made = tries(client, take, 3)
    assert listed(client, inside=take["id"]) == []
    finish(made[0])
    execute("UPDATE takes SET status = 'failed', error = 'out of memory' WHERE id = ?", (made[1],))
    inside = listed(client, inside=take["id"])
    assert sorted(t["id"] for t in inside) == sorted(made[:2])            # the one still being made is not there
    assert all(t["parent_id"] == take["id"] and t["parent_title"] == "Night drive" for t in inside)


def test_a_poll_that_finds_nothing_new_costs_nothing_and_a_finished_take_is_news(client):
    take = a_take()
    made = tries(client, take, 1)
    first = client.get("/api/takes", params={"space_id": "default"})
    assert client.get("/api/takes", params={"space_id": "default"}, headers={"If-None-Match": first.headers["ETag"]}).status_code == 304
    finish(*made)
    assert client.get("/api/takes", params={"space_id": "default"}, headers={"If-None-Match": first.headers["ETag"]}).status_code == 200


def test_a_search_finds_a_take_wherever_it_is(client):
    take = a_take()
    made = tries(client, take, 2)
    finish(*made)
    found = listed(client, q="try 2")
    assert [t["title"] for t in found] == ["Night drive · try 2"] and found[0]["parent_title"] == "Night drive"
    assert len(listed(client, q="night drive")) == 3


def test_the_filters_work_on_the_takes_inside_and_the_take_on_show_stays_in_the_list(client):
    take, other = a_take(), a_take(title="Harbour")
    made = tries(client, take, 2)
    finish(*made)
    execute("UPDATE takes SET favourite = 1 WHERE id IN (?, ?)", (made[0], other["id"]))
    assert [t["id"] for t in listed(client, inside=take["id"], favourite="true")] == [made[0]]
    # Starred, with nothing kept: the take whose insides are open is not starred and would leave the page
    assert [t["id"] for t in listed(client, favourite="true")] == [other["id"]]
    assert sorted(t["id"] for t in listed(client, favourite="true", keep=take["id"])) == sorted([take["id"], other["id"]])
    # and a take inside another is never kept in the list that way
    assert [t["id"] for t in listed(client, favourite="true", keep=made[1])] == [other["id"]]


def test_a_space_counts_the_takes_its_list_shows(client):
    take = a_take()
    tries(client, take, 3)
    spaces = {space["id"]: space["takes"] for space in client.get("/api/spaces").json()}
    assert spaces["default"] == 1


# ------------------------------------------------------------------ one level
def test_a_take_inside_another_holds_none_of_its_own(client):
    take = a_take()
    child = tries(client, take, 1)[0]
    finish(child)
    for path, body in (("tries", {"count": 1}), ("variations", {"interpretations": ["tight"]})):
        reply = client.post(f"/api/takes/{child}/{path}", json=body)
        assert reply.status_code == 400 and "inside another" in reply.json()["detail"]
    assert rows("SELECT id FROM takes WHERE parent_id = ?", (child,)) == []


def test_what_else_is_made_from_a_take_inside_another_is_a_take_of_its_own(client):
    take = a_take()
    child = tries(client, take, 1)[0]
    finish(child)
    again = client.post(f"/api/takes/{child}/revoice").json()
    assert one("SELECT parent_id FROM takes WHERE id = ?", (again["id"],))["parent_id"] is None
    # and Sing again on the take itself is beside it, as it was
    beside = client.post(f"/api/takes/{take['id']}/revoice").json()
    assert one("SELECT parent_id FROM takes WHERE id = ?", (beside["id"],))["parent_id"] is None


# ------------------------------------------------------------------ taking one out
def test_a_take_is_taken_out_and_is_then_a_take_like_any_other(client):
    take = a_take()
    child = tries(client, take, 2)[0]
    finish(child)
    reply = client.post(f"/api/takes/{child}/promote")
    assert reply.status_code == 200 and reply.json() == {"id": child, "parent_id": None, "was_inside": take["id"]}
    assert child in [t["id"] for t in listed(client)] and child not in [t["id"] for t in listed(client, inside=take["id"])]
    assert client.post(f"/api/takes/{child}/tries", json={"count": 1}).status_code == 200      # it can hold takes now
    assert client.post(f"/api/takes/{child}/promote").status_code == 400
    assert client.post("/api/takes/nothere/promote").status_code == 404


# ------------------------------------------------------------------ deleting and moving
def test_deleting_a_take_deletes_the_takes_inside_it(client):
    take, other = a_take(), a_take(title="Harbour")
    made = tries(client, take, 3)
    finish(made[0])
    reply = client.delete(f"/api/takes/{take['id']}")
    assert reply.json() == {"deleted": True, "inside": 3}
    assert [row["id"] for row in rows("SELECT id FROM takes")] == [other["id"]]
    assert rows("SELECT id FROM stem_sets") == []


def test_deleting_a_take_inside_another_leaves_the_rest(client):
    take = a_take()
    made = tries(client, take, 2)
    assert client.delete(f"/api/takes/{made[0]}").json() == {"deleted": True, "inside": 0}
    assert sorted(row["id"] for row in rows("SELECT id FROM takes")) == sorted([take["id"], made[1]])


def test_moving_a_take_takes_the_takes_inside_it_along(client):
    take = a_take()
    made = tries(client, take, 2)
    space = client.post("/api/spaces", json={"name": "Keepers"}).json()
    assert client.post(f"/api/takes/{take['id']}/move", json={"space_id": space["id"]}).status_code == 200
    assert {row["space_id"] for row in rows("SELECT space_id FROM takes")} == {space["id"]}
    reply = client.post(f"/api/takes/{made[0]}/move", json={"space_id": "default"})
    assert reply.status_code == 400 and "Take it out first" in reply.json()["detail"]


# ------------------------------------------------------------------ takes made inside another from the start
def test_a_new_take_can_be_made_inside_another_which_is_how_checkpoints_keeps_its_set(client):
    first = client.post("/api/songs", json={"title": "Night drive · full", "lyrics": "[Verse]\nla la la"}).json()
    inside = client.post("/api/songs", json={"title": "Night drive · step 50", "lyrics": "[Verse]\nla la la",
                                             "parent_id": first["id"]}).json()
    assert one("SELECT parent_id FROM takes WHERE id = ?", (inside["id"],))["parent_id"] == first["id"]
    assert [t["id"] for t in listed(client)] == [first["id"]]
    # not inside a take that is itself inside one, not in another space, not in a take that is not there
    deeper = client.post("/api/songs", json={"title": "x", "lyrics": "[Verse]\nla", "parent_id": inside["id"]})
    assert deeper.status_code == 400
    space = client.post("/api/spaces", json={"name": "Elsewhere"}).json()
    away = client.post("/api/songs", json={"title": "x", "lyrics": "[Verse]\nla", "parent_id": first["id"], "space_id": space["id"]})
    assert away.status_code == 400
    assert client.post("/api/songs", json={"title": "x", "lyrics": "[Verse]\nla", "parent_id": "nothere"}).status_code == 404


def test_takes_from_before_are_takes_of_their_own(client):
    old, new = a_take(title="Night drive · try 1"), a_take()
    assert sorted(t["id"] for t in listed(client)) == sorted([old["id"], new["id"]])
    assert all(t["parent_id"] is None for t in listed(client))


# ------------------------------------------------------------------ the page
STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def page(state: dict, ask: str):
    """The page's own reading of which takes are which, run on a made-up state."""
    script = (STATIC / "app.js").read_text(encoding="utf-8")
    block = script[script.index("function insideOpen()"):script.index("function toggleInside(")]
    words = script[script.index("function heldBy(take)"):script.index("// The panel under a take's card")]
    res = subprocess.run(["node", "-e", "var State = " + json.dumps(state) + ";" + block + words +
                          "console.log(JSON.stringify(" + ask + "));"], capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def take(take_id, **fields):
    return {"id": take_id, "kind": "song", "favourite": 0, "has_audio": True, **fields}


LISTED = [take("a", children=2, children_pending=1), take("b", favourite=1), take("c", kind="cover")]
INSIDE = [take("a1", parent_id="a", favourite=1), take("a2", parent_id="a")]


def state(**fields):
    return {"listed": LISTED, "inside": None, "search": "", "filter": "all", "kinds": [], **fields}


def test_the_tools_act_on_the_space_until_a_take_is_opened_and_then_on_what_is_inside_it():
    ids = "visibleTakes().map(function (t) { return t.id; })"
    assert page(state(), ids) == ["a", "b", "c"]
    assert page(state(inside={"id": "a", "takes": INSIDE}), ids) == ["a1", "a2"]
    assert page(state(inside={"id": "a", "takes": INSIDE}, filter="favourite"), ids) == ["a1"]
    assert page(state(kinds=["cover"]), ids) == ["c"]


def test_the_take_that_is_open_stays_on_the_page_whatever_the_filters_say():
    cards = "listedTakes().map(function (t) { return t.id; })"
    assert page(state(filter="favourite"), cards) == ["b"]
    assert page(state(filter="favourite", inside={"id": "a", "takes": INSIDE}), cards) == ["a", "b"]
    assert page(state(kinds=["cover"], inside={"id": "a", "takes": INSIDE}), cards) == ["a", "c"]


def test_a_search_shows_what_it_finds_flat_and_the_panel_comes_back_after_it():
    open_take = {"id": "a", "takes": INSIDE}
    assert page(state(inside=open_take, search="night"), "[insideOpen(), insideTakes().length]") == [None, 0]
    assert page(state(inside=open_take), "[insideOpen(), insideTakes().length]") == ["a", 2]


def test_a_card_says_what_its_take_holds():
    say = "[insideWords(State.listed[0]), heldBy(State.listed[0]), insideWords(State.listed[1]), heldBy(State.listed[1])]"
    assert page(state(), say) == ["2 takes, and 1 more being made", 3, "Nothing inside this take yet", 0]
    only = state(listed=[take("a", children=0, children_pending=2), take("b", children=1, children_pending=0)])
    assert page(only, "State.listed.map(insideWords)") == ["2 takes being made", "1 take"]


def test_the_cards_offer_what_the_rules_allow():
    script = (STATIC / "app.js").read_text(encoding="utf-8")
    card = script[script.index("var cardOf = function (take) {"):script.index("$('takes').innerHTML = list.map")]
    # Variations and Try more are for takes of their own, Take out for takes inside another, Move not for those
    assert "(take.parent_id ? '' :\n              '<button class=\"take-move\" data-act=\"variations\"" in card
    assert "(take.parent_id\n            ? '<button class=\"take-move\" data-act=\"promote\"" in card
    assert "(take.parent_id ? '' :\n          '<button class=\"take-move\" data-act=\"move\"" in card
    assert "var holds = !take.parent_id && !State.search;" in card
    # and the three that make takes put them inside
    assert "if (holder) { body.parent_id = holder.id; }" in script


def test_a_take_that_holds_nothing_has_nothing_to_open():
    script = (STATIC / "app.js").read_text(encoding="utf-8")
    act = script[script.index("if (act === 'inside') {"):script.index("if (act === 'promote') {")]
    assert "!(holder && heldBy(holder))) { return; }" in act and act.index("return; }") < act.index("toggleInside(id)")
    # and a panel whose last take has gone is closed, not left open on nothing
    assert "take.id === open && heldBy(take) > 0; })) { State.inside = null; }" in script


def test_a_cards_mastering_button_follows_the_rack_at_once():
    rack = (STATIC / "rack.js").read_text(encoding="utf-8")
    cards = rack[rack.index("updateTakeCardsUI: function () {"):rack.index("openForTake: function (take) {")]
    assert "b.classList.toggle('mastered', self.hasActiveMastering(cardId));" in cards
    save = rack[rack.index("debouncedSave: function () {"):rack.index("this.saveTimer = setTimeout(", rack.index("debouncedSave: function () {"))]
    assert save.rstrip().endswith("if (this.saveTimer) { clearTimeout(this.saveTimer); }") and "this.updateTakeCardsUI();" in save.split("State.loadedTake.fx_chain = payload;")[-1]
    # drawn and updated by the same question, the one Save asks
    assert "window.Rack.hasActiveMastering(take.id)" in (STATIC / "app.js").read_text(encoding="utf-8")
