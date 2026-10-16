from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def test_hotkeys_modal_exists_in_index_html():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'id="hotkeys-modal"' in html
    assert 'id="hotkeys-title"' in html
    assert 'id="hotkeys-close"' in html
    assert 'class="modal hidden"' in html
    assert 'id="menu-hotkeys"' in html


def test_hotkeys_css_rules():
    css = (STATIC / "styles.css").read_text(encoding="utf-8")
    assert "#hotkeys-modal { z-index: 70; }" in css
    assert ".modal-box.hotkeys-box" in css
    assert "kbd {" in css


def test_hotkeys_script_wiring_and_handler():
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "function openHotkeys()" in app_js
    assert "function closeHotkeys()" in app_js
    assert "function toggleHotkeys()" in app_js
    assert "function wireHotkeys()" in app_js
    assert "wireHotkeys();" in app_js

    # Escape handler
    assert "event.key === 'Escape' && $('hotkeys-modal')" in app_js

    # Keydown ? handler after typing guard
    guard_idx = app_js.index("/^(INPUT|TEXTAREA|SELECT)$/.test(tag)")
    hotkey_idx = app_js.index("event.key === '?' && !event.ctrlKey && !event.metaKey && !event.altKey")
    assert guard_idx < hotkey_idx, "? must be checked after the input/textarea typing guard"
    assert "toggleHotkeys();" in app_js[hotkey_idx:hotkey_idx + 200]


def test_guide_documents_question_mark_hotkey():
    guide = (STATIC / "guide.md").read_text(encoding="utf-8")
    assert "| ? | show or hide the hot keys; again to close |" in guide
