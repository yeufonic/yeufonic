"""Custom themes: CRUD validation, settings integration, and removal fallback (#82)."""
from pathlib import Path

from app import themes

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "app" / "static"


def test_custom_theme_crud_and_settings_integration(client):
    # Starts empty
    assert client.get("/api/themes").json()["themes"] == []

    # Create a custom theme with a gradient and apply it immediately
    created = client.post("/api/themes", json={
        "name": "Midnight Teal",
        "base": "dark",
        "colors": {"--bg": "#081014", "--accent-a": "#2dd4bf", "--wave-song": "#38bdf8"},
        "gradients": {"--panel": {"to": "#132a36", "dir": "135deg"}, "--bg": {"to": "#0f2027", "dir": "radial"}},
        "apply": True,
    })
    assert created.status_code == 200, created.text
    body = created.json()
    theme = body["theme"]
    assert theme["name"] == "Midnight Teal"
    assert theme["base"] == "dark"
    assert theme["colors"]["--bg"] == "#081014"
    assert theme["colors"]["--accent-a"] == "#2dd4bf"
    assert theme["gradients"]["--panel"] == {"to": "#132a36", "dir": "135deg"}
    assert theme["gradients"]["--bg"] == {"to": "#0f2027", "dir": "radial"}

    # Settings payload exposes the custom theme in options, custom_themes, and active value
    theme_spec = next(item for item in body["settings"] if item["key"] == "appearance.theme")
    assert theme_spec["value"] == f"custom:{theme['id']}"
    assert any(o["value"] == f"custom:{theme['id']}" and o["label"] == "Midnight Teal" for o in theme_spec["options"])
    assert len(theme_spec["custom_themes"]) == 1

    # Selecting it via PUT /api/settings succeeds; selecting an unknown custom id is rejected
    assert client.put("/api/settings", json={"key": "appearance.theme", "value": "studio"}).status_code == 200
    assert client.put("/api/settings", json={"key": "appearance.theme", "value": f"custom:{theme['id']}"}).status_code == 200
    assert client.put("/api/settings", json={"key": "appearance.theme", "value": "custom:missing"}).status_code == 400

    # Rename & update colours
    updated = client.put(f"/api/themes/{theme['id']}", json={
        "name": "Deep Ocean",
        "base": "light",
        "colors": {"--bg": "#eef5f9", "--accent-a": "#0284c7"},
    })
    assert updated.status_code == 200
    assert updated.json()["theme"]["name"] == "Deep Ocean"
    assert updated.json()["theme"]["base"] == "light"

    # Deleting the active custom theme removes it and falls back appearance.theme to studio
    deleted = client.delete(f"/api/themes/{theme['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["themes"] == []
    theme_spec_after = next(item for item in deleted.json()["settings"] if item["key"] == "appearance.theme")
    assert theme_spec_after["value"] == "studio"
    assert not any(o["value"].startswith("custom:") for o in theme_spec_after["options"])


def test_custom_theme_validation_rejects_bad_inputs(client):
    assert client.post("/api/themes", json={"name": "", "base": "dark"}).status_code == 400
    assert client.post("/api/themes", json={"name": "Studio", "base": "dark"}).status_code == 400
    assert client.post("/api/themes", json={"name": "Bad Base", "base": "neon"}).status_code == 400
    assert client.post("/api/themes", json={"name": "Bad Hex", "base": "dark", "colors": {"--bg": "red"}}).status_code == 400

    first = client.post("/api/themes", json={"name": "Warm Copper", "base": "studio", "colors": {"--bg": "#123"}})
    assert first.status_code == 200
    # 3-digit hex normalises to 6 digits
    assert first.json()["theme"]["colors"]["--bg"] == "#112233"
    # Duplicate name (case-insensitive) is rejected
    assert client.post("/api/themes", json={"name": "warm copper", "base": "studio"}).status_code == 400
    # Bad gradient direction or hex is rejected
    assert client.post("/api/themes", json={
        "name": "Bad Grad Dir",
        "base": "dark",
        "gradients": {"--panel": {"to": "#112233", "dir": "45deg"}},
    }).status_code == 400
    assert client.post("/api/themes", json={
        "name": "Bad Grad Hex",
        "base": "dark",
        "gradients": {"--panel": {"to": "blue", "dir": "135deg"}},
    }).status_code == 400


def test_theme_builder_covers_all_backend_tokens_and_mockups():
    themes_js = (STATIC / "themes.js").read_text(encoding="utf-8")
    styles_css = (STATIC / "styles.css").read_text(encoding="utf-8")
    for token in themes.COLOR_TOKENS:
        assert f"'{token}'" in themes_js, f"{token} missing from themes.js"
    assert "mockMainHtml" in themes_js
    assert "mockEditorHtml" in themes_js
    assert "mockJamHtml" in themes_js
    assert "tm-live-app" not in themes_js
    assert "tm-tint-btn" in themes_js
    assert ".tm-group {\n  flex: 0 0 auto;" in styles_css
    assert 'id="theme-modal"' in (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'data-tm-act="import-json"' in themes_js
    assert 'data-tm-act="export-json"' in themes_js
    assert 'data-theme-act="import"' in themes_js
    assert 'data-theme-act="export"' in themes_js


def test_custom_theme_json_export_and_import_roundtrip(client):
    created = client.post("/api/themes", json={
        "name": "Midnight Teal",
        "base": "dark",
        "colors": {"--bg": "#081014", "--accent-a": "#2dd4bf"},
        "gradients": {"--panel": {"to": "#132a36", "dir": "135deg"}},
        "apply": False,
    })
    assert created.status_code == 200
    theme_id = created.json()["theme"]["id"]

    # Export returns portable JSON without internal id/timestamps and an attachment filename
    exp = client.get(f"/api/themes/{theme_id}/export")
    assert exp.status_code == 200
    assert "midnight-teal.yeufonic-theme.json" in exp.headers.get("content-disposition", "")
    exported = exp.json()
    assert exported["format"] == "yeufonic-theme"
    assert exported["version"] == 1
    assert exported["name"] == "Midnight Teal"
    assert exported["base"] == "dark"
    assert exported["colors"] == {"--bg": "#081014", "--accent-a": "#2dd4bf"}
    assert exported["gradients"] == {"--panel": {"to": "#132a36", "dir": "135deg"}}
    assert "id" not in exported
    assert "updated_at" not in exported

    # Exporting a missing theme returns 404
    assert client.get("/api/themes/missing/export").status_code == 404

    # Importing the exported payload resolves the duplicate name cleanly and applies when asked
    imp = client.post("/api/themes/import", json={"theme": exported, "apply": True})
    assert imp.status_code == 200, imp.text
    imp_theme = imp.json()["theme"]
    assert imp_theme["id"] != theme_id
    assert imp_theme["name"] == "Midnight Teal (2)"
    assert imp_theme["base"] == "dark"
    assert imp_theme["colors"] == {"--bg": "#081014", "--accent-a": "#2dd4bf"}
    assert imp_theme["gradients"] == {"--panel": {"to": "#132a36", "dir": "135deg"}}
    theme_spec = next(item for item in imp.json()["settings"] if item["key"] == "appearance.theme")
    assert theme_spec["value"] == f"custom:{imp_theme['id']}"

    # Posting a raw exported theme JSON directly (without wrapper) also works, and reserved names are adjusted
    raw_imp = client.post("/api/themes/import", json={
        "format": "yeufonic-theme",
        "version": 1,
        "name": "Light",
        "base": "light",
        "colors": {"--bg": "#fafaff"},
    })
    assert raw_imp.status_code == 200, raw_imp.text
    assert raw_imp.json()["theme"]["name"] == "Light custom"
    assert raw_imp.json()["theme"]["base"] == "light"

    # Invalid payloads are rejected with 400
    assert client.post("/api/themes/import", json={"format": "wrong", "base": "dark"}).status_code == 400
    assert client.post("/api/themes/import", json={"name": "Empty"}).status_code == 400
    assert client.post("/api/themes/import", json={"base": "neon", "colors": {}}).status_code == 400
    assert client.post("/api/themes/import", json={"base": "dark", "colors": {"--bg": "not-a-hex"}}).status_code == 400
