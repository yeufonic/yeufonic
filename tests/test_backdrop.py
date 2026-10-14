"""The backdrop's colour: a setting of the app's, kept as "on:<hue>:<strength>" (or "off:..." with the choice kept),
drawn by the page behind the takes and nowhere else."""
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def test_the_backdrop_is_a_setting_that_takes_a_hue_and_a_strength(client):
    spec = {item["key"]: item for item in client.get("/api/settings").json()["settings"]}
    assert spec["appearance.backdrop"]["type"] == "backdrop" and spec["appearance.backdrop"]["value"] == ""
    keys = list(spec)
    assert keys.index("appearance.backdrop") == keys.index("appearance.theme") + 1
    for good in ("on:205:0.6", "off:0:1", "on:359:0.1", ""):
        assert client.put("/api/settings", json={"key": "appearance.backdrop", "value": good}).status_code == 200, good
    saved = {item["key"]: item["value"] for item in client.put(
        "/api/settings", json={"key": "appearance.backdrop", "value": "on:150:0.55"}).json()["settings"]}
    assert saved["appearance.backdrop"] == "on:150:0.55"
    for bad in ("on", "maybe:20:0.5", "on:360:0.5", "on:-1:0.5", "on:20:0", "on:20:1.5", "on:red:0.5", "on:20:x"):
        assert client.put("/api/settings", json={"key": "appearance.backdrop", "value": bad}).status_code == 400, bad


def test_the_page_tints_only_the_ground_behind_the_takes():
    css = (STATIC / "styles.css").read_text(encoding="utf-8")
    assert ':root.backdrop-hue:not([data-theme="contrast"]) body {' in css
    assert ':root.backdrop-hue[data-theme="light"] body {' in css
    rules = [line for line in css.splitlines() if ":root.backdrop-hue" in line and "{" in line]
    assert all(line.rstrip().endswith("body {") for line in rules), rules      # the body's ground, nothing else
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "} else if (item.type === 'backdrop') {" in app_js and "adoptBackdrop();" in app_js
    row = app_js[app_js.index("function paintBackdropRow()"):app_js.index("function paintBackdropSliders(")]
    assert "event.stopPropagation();" in row and "saveBackdrop(backdropText(next))" in row
    # what the first trial kept in this browser becomes the setting, once, when the app has none
    adopt = app_js[app_js.index("function adoptBackdrop()"):app_js.index("function saveBackdrop(")]
    assert "localStorage.removeItem(BACKDROP_TRIAL)" in adopt and "if (!setting('appearance.backdrop', ''))" in adopt
