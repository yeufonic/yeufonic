"""Styles a user wrote and kept: saved under a name, listed by name, written over by saving the same name
again, and deleted.  The page shows them first in the style menu and its search covers them."""
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def test_a_style_is_kept_listed_by_name_and_deleted(client):
    assert client.get("/api/styles").json() == []
    second = client.post("/api/styles", json={"name": "Quiet harbour", "prompt": "ambient, soft pads, 70 BPM"}).json()
    first = client.post("/api/styles", json={"name": "  lantern   folk ", "prompt": " folk,  nylon guitar "}).json()
    assert first["name"] == "lantern folk" and first["prompt"] == "folk, nylon guitar" and first["replaced"] is False
    assert [s["name"] for s in client.get("/api/styles").json()] == ["lantern folk", "Quiet harbour"]
    assert client.delete(f"/api/styles/{second['id']}").json() == {"deleted": True}
    assert [s["name"] for s in client.get("/api/styles").json()] == ["lantern folk"]
    assert client.delete(f"/api/styles/{second['id']}").status_code == 404


def test_saving_under_a_name_already_there_writes_it_over_whatever_the_case(client):
    kept = client.post("/api/styles", json={"name": "Lantern folk", "prompt": "folk, nylon guitar"}).json()
    again = client.post("/api/styles", json={"name": "lantern FOLK", "prompt": "folk, nylon guitar, fiddle"}).json()
    assert again["id"] == kept["id"] and again["replaced"] is True
    styles = client.get("/api/styles").json()
    assert [(s["name"], s["prompt"]) for s in styles] == [("lantern FOLK", "folk, nylon guitar, fiddle")]


def test_a_style_needs_a_name_and_some_text(client):
    assert client.post("/api/styles", json={"name": "", "prompt": "folk"}).status_code == 422
    assert client.post("/api/styles", json={"name": "Folk", "prompt": ""}).status_code == 422
    assert client.post("/api/styles", json={"name": "   ", "prompt": "folk"}).status_code == 400
    assert client.post("/api/styles", json={"name": "x" * 61, "prompt": "folk"}).status_code == 422
    assert client.get("/api/styles").json() == []


def test_the_page_has_a_save_button_beside_the_style_menu():
    page = (STATIC / "index.html").read_text(encoding="utf-8")
    row = page[page.index('class="style-pick-row"'):page.index('id="lora-presets-wrap"')]
    assert row.index('id="style-picker"') < row.index('id="style-save"')
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "$('style-save').addEventListener('click', saveCurrentStyle)" in app_js
    # kept without the trigger word of the LoRA in use, which is put back when the style is chosen
    keep = app_js[app_js.index("function styleToSave()"):app_js.index("function currentSavedStyle()")]
    assert "removeStyleWord(val, trigger)" in keep
    use = app_js[app_js.index("function applyStyleText(prompt)"):app_js.index("/* ----------------------------------------------- a big LoRA's learned styles")]
    assert "trigger + ', ' + prompt" in use


def test_saved_styles_are_first_in_the_menu_under_a_heading_and_the_search_covers_them():
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    menu = app_js[app_js.index("function paintStylePickerMenu(filterText)"):app_js.index("function openStylePicker()")]
    assert "var saved = State.savedStyles.filter(has);" in menu and "var filtered = CANNED_STYLES.filter(has);" in menu
    assert "var listHtml = savedHtml + cannedHtml;" in menu
    assert 'data-style-group="saved"' in menu and "Saved styles" in menu
    # a search opens the heading by itself, and each saved style has its bin
    assert "var open = query ? saved.length > 0 : savedStylesOpen();" in menu
    assert 'data-style-del="' in menu and "icon('trash')" in menu
    # the heading is redrawn after its click has been heard, or the menu shuts as if clicked outside
    assert "setTimeout(paintStylePickerMenu, 0);" in app_js
