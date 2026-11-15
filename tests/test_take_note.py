"""A take's note (#71): the person's own words on a take, searched, and carried by its recipe file."""
from app.db import one
from conftest import make_take

ABC = ('X:1\nM:4/4\nL:1/8\nQ:1/4=100\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\nK:C\n'
       '% verse\nV: Vocal\n' + '"C"c4|"Am"A4|"F"F4|"G"G4|' * 4 + '\n')


def test_a_note_is_kept_changed_and_removed(client):
    take = make_take(title="Paper Lanterns")
    r = client.post(f"/api/takes/{take['id']}/note", json={"note": "  only the first chorus; cut the bass  "})
    assert r.status_code == 200 and r.json()["take_note"] == "only the first chorus; cut the bass"
    assert one("SELECT take_note FROM takes WHERE id = ?", (take["id"],))["take_note"] == "only the first chorus; cut the bass"
    listed = next(t for t in client.get("/api/takes").json() if t["id"] == take["id"])
    assert listed["take_note"] == "only the first chorus; cut the bass"
    assert client.post(f"/api/takes/{take['id']}/note", json={"note": "   "}).json()["take_note"] is None
    assert one("SELECT take_note FROM takes WHERE id = ?", (take["id"],))["take_note"] is None


def test_a_note_for_no_take_or_too_long_is_refused(client):
    assert client.post("/api/takes/nosuchtake/note", json={"note": "hello"}).status_code == 404
    take = make_take()
    assert client.post(f"/api/takes/{take['id']}/note", json={"note": "x" * 20_001}).status_code == 422


def test_a_search_finds_a_take_by_its_note(client):
    noted = make_take(title="Copper Fields")
    make_take(title="Glass Harbour")
    client.post(f"/api/takes/{noted['id']}/note", json={"note": "keep for the demo reel"})
    found = client.get("/api/takes", params={"q": "demo reel"}).json()
    assert [t["id"] for t in found] == [noted["id"]]


def test_the_recipe_carries_the_note_and_an_import_keeps_it(client):
    take = make_take(title="Copper Fields", abc=ABC, status="done")
    client.post(f"/api/takes/{take['id']}/note", json={"note": "the bridge is the best part"})
    data = client.get(f"/api/takes/{take['id']}/recipe").json()
    assert data["version"] == 1 and data["take"]["note"] == "the bridge is the best part"
    got = client.post("/api/takes/import", json={"recipe": data, "space_id": "default"}).json()
    assert one("SELECT take_note FROM takes WHERE id = ?", (got["id"],))["take_note"] == "the bridge is the best part"


def test_a_recipe_from_before_notes_imports_with_none(client):
    take = make_take(title="Copper Fields", abc=ABC, status="done")
    data = client.get(f"/api/takes/{take['id']}/recipe").json()
    data["take"].pop("note", None)
    got = client.post("/api/takes/import", json={"recipe": data, "space_id": "default"})
    assert got.status_code == 200, got.text
    assert one("SELECT take_note FROM takes WHERE id = ?", (got.json()["id"],))["take_note"] is None
