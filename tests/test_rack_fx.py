"""Mastering rack / vintage FX chain persistence per take."""
import time
from app.db import execute, one


def a_take(**extra):
    row = {
        "id": "fx_take_1", "kind": "song", "title": "Mastering Test", "style": "rock", "lyrics": "hello",
        "abc": "X:1\nK:C\n", "mode": "full", "seed": 12345, "checkpoint": "x", "status": "done",
        "created_at": time.time(), "max_duration": 120,
    }
    row.update(extra)
    cols = list(row)
    execute(f"INSERT INTO takes({', '.join(cols)}) VALUES({', '.join('?' * len(cols))})", [row[c] for c in cols])
    return row


def test_get_fx_defaults_to_empty_dict(client):
    a_take(id="take_empty_fx")
    res = client.get("/api/takes/take_empty_fx/fx")
    assert res.status_code == 200
    assert res.json() == {}


def test_put_and_get_fx_persists_settings(client):
    a_take(id="take_with_fx")
    fx_settings = {
        "bypass": False,
        "eq": {"enabled": True, "low": 3.5, "mid1": -2.0, "high": 1.5},
        "compressor": {"enabled": True, "threshold": -16.0, "ratio": 4.0},
        "limiter": {"enabled": True, "threshold": -1.0, "ceiling": -0.1},
    }
    put_res = client.put("/api/takes/take_with_fx/fx", json=fx_settings)
    assert put_res.status_code == 200
    assert put_res.json()["status"] == "ok"
    assert put_res.json()["fx_chain"] == fx_settings

    # Verify retrieval via dedicated endpoint
    get_res = client.get("/api/takes/take_with_fx/fx")
    assert get_res.status_code == 200
    assert get_res.json() == fx_settings

    # Verify retrieval via general take endpoint
    take_res = client.get("/api/takes/take_with_fx")
    assert take_res.status_code == 200
    assert "fx_chain" in take_res.json()


def test_fx_endpoints_404_on_missing_take(client):
    assert client.get("/api/takes/nonexistent_take/fx").status_code == 404
    assert client.put("/api/takes/nonexistent_take/fx", json={}).status_code == 404


def test_rack_js_high_shelf_corner_tuning():
    from pathlib import Path
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    assert "this.eqHigh.frequency.value = 6800" in rack_js, "eqHigh init frequency must be 6800 Hz"
    assert "this.eqHigh.frequency.setTargetAtTime(6800, now, ramp)" in rack_js, "eqHigh applySettings frequency must be 6800 Hz"


def test_rack_floating_and_draggable_support():
    from pathlib import Path
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    styles_css = (Path(__file__).resolve().parent.parent / "app" / "static" / "styles.css").read_text(encoding="utf-8")

    # rack.js draggable & floating methods
    assert "initDraggable" in rack_js
    assert "dockToBottom" in rack_js
    assert "floatToCenter" in rack_js
    assert "restoreFloatingPosition" in rack_js
    assert "clampFloatingBounds" in rack_js
    assert "saveFloatingPosition" in rack_js
    assert "rack-drag-grip" in rack_js
    assert "rack-dock-btn" in rack_js

    # styles.css classes
    assert ".rack-panel.is-floating" in styles_css
    assert ".rack-panel.is-dragging" in styles_css
    assert ".rack-drag-grip" in styles_css

