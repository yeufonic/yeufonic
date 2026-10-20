"""Playlists of takes: user-created playlists and the system Liked playlist populated from starred takes."""
from pathlib import Path
import time
from app.db import one
from conftest import make_take

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def test_liked_playlist_exists_by_default(client):
    playlists = client.get("/api/playlists").json()
    liked = next((p for p in playlists if p["id"] == "liked"), None)
    assert liked is not None
    assert liked["name"] == "Liked"
    assert liked["is_system"] is True


def test_starring_take_synchronises_with_liked_playlist(client):
    take = make_take(title="Strawberry Fields", favourite=0)

    # Initially not in liked
    liked_view = client.get("/api/playlists/liked").json()
    assert not any(item["id"] == take["id"] for item in liked_view["items"])

    # Star the take
    res = client.post(f"/api/takes/{take['id']}/favourite?value=true")
    assert res.status_code == 200

    # Now in liked playlist
    liked_view = client.get("/api/playlists/liked").json()
    assert any(item["id"] == take["id"] for item in liked_view["items"])
    assert liked_view["count"] >= 1

    # Unstar the take
    res = client.post(f"/api/takes/{take['id']}/favourite?value=false")
    assert res.status_code == 200

    # Removed from liked playlist
    liked_view = client.get("/api/playlists/liked").json()
    assert not any(item["id"] == take["id"] for item in liked_view["items"])


def test_adding_and_removing_from_liked_playlist_toggles_favourite(client):
    take = make_take(title="Penny Lane", favourite=0)

    # Add to liked playlist via playlist items API
    add_res = client.post("/api/playlists/liked/items", json={"take_id": take["id"]})
    assert add_res.status_code == 200

    row = one("SELECT favourite FROM takes WHERE id = ?", (take["id"],))
    assert row["favourite"] == 1

    # Remove from liked playlist via playlist items API
    del_res = client.delete(f"/api/playlists/liked/items/{take['id']}")
    assert del_res.status_code == 200

    row = one("SELECT favourite FROM takes WHERE id = ?", (take["id"],))
    assert row["favourite"] == 0


def test_custom_playlist_lifecycle(client):
    # Create playlist
    create_res = client.post("/api/playlists", json={"name": "Beatles Covers", "description": "Classic covers"})
    assert create_res.status_code == 200
    pl = create_res.json()
    assert pl["name"] == "Beatles Covers"
    assert pl["description"] == "Classic covers"
    assert pl["is_system"] is False
    pid = pl["id"]

    # Verify in list
    all_pls = client.get("/api/playlists").json()
    assert any(p["id"] == pid for p in all_pls)

    # Update name and description
    patch_res = client.patch(f"/api/playlists/{pid}", json={"name": "The Beatles Collection", "description": "Updated description"})
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["name"] == "The Beatles Collection"
    assert updated["description"] == "Updated description"

    # Cannot delete system playlist
    assert client.delete("/api/playlists/liked").status_code == 400

    # Cannot rename system playlist
    assert client.patch("/api/playlists/liked", json={"name": "New Name"}).status_code == 400

    # Delete custom playlist
    del_res = client.delete(f"/api/playlists/{pid}")
    assert del_res.status_code == 200
    assert del_res.json() == {"deleted": True, "id": pid}
    assert client.get(f"/api/playlists/{pid}").status_code == 404


def test_playlist_items_sorting_and_filtering(client):
    pl = client.post("/api/playlists", json={"name": "Driving Mix", "description": "Upbeat tracks"}).json()
    pid = pl["id"]

    t1 = make_take(title="Alpha Track", duration=120.0, style="Electronic Synthwave")
    time.sleep(0.01)
    t2 = make_take(title="Beta Melody", duration=240.0, style="Acoustic Folk")
    time.sleep(0.01)
    t3 = make_take(title="Gamma Rhythm", duration=180.0, style="Hard Rock")

    client.post(f"/api/playlists/{pid}/items", json={"take_id": t1["id"]})
    time.sleep(0.01)
    client.post(f"/api/playlists/{pid}/items", json={"take_id": t2["id"]})
    time.sleep(0.01)
    client.post(f"/api/playlists/{pid}/items", json={"take_id": t3["id"]})

    # Default sort: added_desc (t3, t2, t1)
    view = client.get(f"/api/playlists/{pid}?sort=added_desc").json()
    assert [item["id"] for item in view["items"]] == [t3["id"], t2["id"], t1["id"]]
    assert view["count"] == 3
    assert view["total_duration"] == 540.0

    # Sort: added_asc (t1, t2, t3)
    view_asc = client.get(f"/api/playlists/{pid}?sort=added_asc").json()
    assert [item["id"] for item in view_asc["items"]] == [t1["id"], t2["id"], t3["id"]]

    # Sort: title_asc (Alpha, Beta, Gamma)
    view_title = client.get(f"/api/playlists/{pid}?sort=title_asc").json()
    assert [item["title"] for item in view_title["items"]] == ["Alpha Track", "Beta Melody", "Gamma Rhythm"]

    # Sort: duration_desc (Beta: 240, Gamma: 180, Alpha: 120)
    view_dur = client.get(f"/api/playlists/{pid}?sort=duration_desc").json()
    assert [item["id"] for item in view_dur["items"]] == [t2["id"], t3["id"], t1["id"]]

    # Search filter q: 'synthwave'
    view_q = client.get(f"/api/playlists/{pid}?q=synthwave").json()
    assert len(view_q["items"]) == 1
    assert view_q["items"][0]["id"] == t1["id"]

    # Take playlists endpoint
    tp = client.get(f"/api/takes/{t1['id']}/playlists").json()
    assert pid in tp["playlists"]

    # Remove item
    client.delete(f"/api/playlists/{pid}/items/{t2['id']}")
    view_after = client.get(f"/api/playlists/{pid}").json()
    assert view_after["count"] == 2
    assert not any(item["id"] == t2["id"] for item in view_after["items"])


def test_deleting_take_removes_from_playlist_items(client):
    pl = client.post("/api/playlists", json={"name": "Temp List"}).json()
    take = make_take(title="To Be Deleted")
    client.post(f"/api/playlists/{pl['id']}/items", json={"take_id": take["id"]})

    # Verify present
    assert client.get(f"/api/playlists/{pl['id']}").json()["count"] == 1

    # Delete take from takes
    client.delete(f"/api/takes/{take['id']}")

    # Verify cleaned up
    assert client.get(f"/api/playlists/{pl['id']}").json()["count"] == 0


def test_the_page_has_playlist_elements():
    page = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'id="view-btn-playlists"' in page
    assert 'id="playlist-sidebar"' in page
    assert 'id="playlist-view"' in page
    assert 'id="playlist-picker-modal"' in page
    assert 'id="playlist-edit-modal"' in page
    assert 'class="th-title sortable"' in page
    assert 'class="th-duration sortable"' in page
    assert 'class="th-added sortable"' in page
    assert 'playlist-sort-select' not in page

    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "function wirePlaylists()" in app_js
    assert "function switchView(" in app_js
    assert "function openPlaylistPicker(" in app_js
    assert "actions += tile('playlist'" in app_js
    assert "function toggleColumnSort(" in app_js
    assert "function openTakeInLibrary(" in app_js

    styles = (STATIC / "styles.css").read_text(encoding="utf-8")
    assert "main.view-playlists" in styles
    assert "main:not(.view-playlists) > .playlist-sidebar" in styles
    assert "main.view-playlists > .sheet-panel" in styles
    assert "main.view-playlists > .library" in styles

