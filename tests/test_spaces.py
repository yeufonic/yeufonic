from app.db import TRASH_SPACE, execute, migrate, one, rows

from conftest import make_take


def test_every_take_starts_in_default(client):
    take = make_take()
    assert one("SELECT space_id FROM takes WHERE id = ?", (take["id"],))["space_id"] == "default"
    spaces = client.get("/api/spaces").json()
    assert [(s["id"], s["name"], s["takes"]) for s in spaces] == [("default", "Default", 1), ("trash", "Trash", 0)]


def test_create_rename_and_list_in_order(client):
    zed = client.post("/api/spaces", json={"name": "  Zed   demos "}).json()
    assert zed["name"] == "Zed demos"
    client.post("/api/spaces", json={"name": "alpha"})
    assert [s["name"] for s in client.get("/api/spaces").json()] == ["Default", "alpha", "Zed demos", "Trash"]
    assert client.post("/api/spaces", json={"name": "ALPHA"}).status_code == 409
    assert client.post("/api/spaces", json={"name": "Trash"}).status_code == 409
    assert client.post("/api/spaces", json={"name": "   "}).status_code == 400
    assert client.put(f"/api/spaces/{zed['id']}", json={"name": "zed DEMOS"}).json()["name"] == "zed DEMOS"
    assert client.put("/api/spaces/trash", json={"name": "Bin"}).status_code == 400
    assert client.put("/api/spaces/nope", json={"name": "x"}).status_code == 404


def test_move_and_filter(client):
    space = client.post("/api/spaces", json={"name": "Covers"}).json()
    first, second = make_take(), make_take()
    assert client.post(f"/api/takes/{first['id']}/move", json={"space_id": space["id"]}).status_code == 200
    assert [t["id"] for t in client.get(f"/api/takes?space_id={space['id']}").json()] == [first["id"]]
    assert [t["id"] for t in client.get("/api/takes?space_id=default").json()] == [second["id"]]
    assert len(client.get("/api/takes").json()) == 2
    assert client.post(f"/api/takes/{first['id']}/move", json={"space_id": "nope"}).status_code == 404
    assert client.post("/api/takes/nope/move", json={"space_id": "default"}).status_code == 404


def test_deleting_a_space_moves_its_takes_to_trash(client):
    space = client.post("/api/spaces", json={"name": "Scratch"}).json()
    take = make_take()
    client.post(f"/api/takes/{take['id']}/move", json={"space_id": space["id"]})
    assert client.delete(f"/api/spaces/{space['id']}").json() == {"deleted": True, "moved": 1}
    row = one("SELECT space_id, trashed_from FROM takes WHERE id = ?", (take["id"],))
    assert row["space_id"] == TRASH_SPACE and row["trashed_from"] is None
    assert client.delete("/api/spaces/default").status_code == 400
    assert client.delete("/api/spaces/trash").status_code == 400
    # Restoring a take whose original space was deleted puts it in Default.
    restored = client.post(f"/api/takes/{take['id']}/restore").json()
    assert restored == {"space_id": "default", "name": "Default"}
    assert one("SELECT space_id FROM takes WHERE id = ?", (take["id"],))["space_id"] == "default"


def test_new_songs_land_in_the_chosen_space_and_not_in_trash(client):
    space = client.post("/api/spaces", json={"name": "Ideas"}).json()
    body = {"lyrics": "[Verse]\nla la"}
    song = client.post("/api/songs", json={**body, "space_id": space["id"]}).json()
    assert one("SELECT space_id FROM takes WHERE id = ?", (song["id"],))["space_id"] == space["id"]
    assert client.post("/api/songs", json={**body, "space_id": "gone"}).status_code == 404
    assert client.post("/api/songs", json={**body, "space_id": "trash"}).status_code == 400


def test_trash_restore_empty_playlists_and_storage_reclaim(client, data_dir):
    space = client.post("/api/spaces", json={"name": "Demos"}).json()
    take_dir = data_dir / "takes" / "t-trash"
    take_dir.mkdir(parents=True)
    audio = take_dir / "song.flac"
    audio.write_bytes(b"fLaC" + b"\0" * 4096)
    take = make_take(id="ttrash01", title="Trashed song", audio_path=str(audio))
    client.post(f"/api/takes/{take['id']}/move", json={"space_id": space["id"]})
    # Star it so it enters Liked playlist too.
    client.post(f"/api/takes/{take['id']}/favourite?value=true")
    assert len(client.get("/api/playlists/liked").json()["items"]) == 1

    # First DELETE moves it to Trash; files stay on disk, hidden from regular listing and playlists.
    res = client.delete(f"/api/takes/{take['id']}").json()
    assert res == {"deleted": True, "trashed": True, "permanent": False, "inside": 0}
    assert audio.exists()
    assert client.get("/api/takes").json() == []
    assert [t["id"] for t in client.get("/api/takes?space_id=trash").json()] == [take["id"]]
    assert client.get("/api/playlists/liked").json()["items"] == []

    # Restore puts it back into Demos and makes it visible in Liked again.
    restored = client.post(f"/api/takes/{take['id']}/restore").json()
    assert restored == {"space_id": space["id"], "name": "Demos"}
    assert [t["id"] for t in client.get(f"/api/takes?space_id={space['id']}").json()] == [take["id"]]
    assert len(client.get("/api/playlists/liked").json()["items"]) == 1

    # Move back to Trash and verify Settings -> Storage reports it and can reclaim it.
    client.delete(f"/api/takes/{take['id']}")
    report = client.get("/api/storage").json()
    trash_item = next((i for i in report["items"] if i["id"] == "trash"), None)
    assert trash_item is not None and trash_item["bytes"] >= 4100
    reclaimed = client.post("/api/storage/reclaim", json={"ids": ["trash"]}).json()
    assert reclaimed["freed"] >= 4100
    assert one("SELECT id FROM takes WHERE id = ?", (take["id"],)) is None
    assert not take_dir.exists()

    # Empty Trash endpoint also permanently removes trashed takes and their files.
    take2_dir = data_dir / "takes" / "t-trash2"
    take2_dir.mkdir(parents=True)
    audio2 = take2_dir / "song2.flac"
    audio2.write_bytes(b"fLaC" + b"\0" * 1024)
    take2 = make_take(id="ttrash02", title="Empty me", audio_path=str(audio2))
    client.delete(f"/api/takes/{take2['id']}")
    assert client.post("/api/spaces/trash/empty").json() == {"deleted": 1}
    assert one("SELECT id FROM takes WHERE id = ?", (take2["id"],)) is None
    assert not take2_dir.exists()


def test_trash_migration_preserves_existing_user_space_named_trash(client):
    """If an existing user already created a custom space called 'Trash', the migration renames it rather than colliding."""
    execute("DELETE FROM spaces WHERE id = ?", (TRASH_SPACE,))
    execute("INSERT INTO spaces(id, name, created_at) VALUES('custom1', 'Trash', 100)")
    migrate()
    by_id = {r["id"]: r["name"] for r in rows("SELECT id, name FROM spaces")}
    assert by_id[TRASH_SPACE] == "Trash"
    assert by_id["custom1"] == "Trash (space)"
