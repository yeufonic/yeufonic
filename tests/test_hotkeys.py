from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def test_hotkeys_modal_exists_in_index_html():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'id="hotkeys-modal"' in html
    assert 'id="hotkeys-title"' in html
    assert 'id="hotkeys-close"' in html
    assert 'class="modal hidden"' in html
    assert 'id="menu-hotkeys"' not in html
    assert 'id="menu-logs"' not in html


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
    hotkey_idx = app_js.index("event.key === '?' || (event.key === '/' && event.shiftKey)")
    assert guard_idx < hotkey_idx, "? must be checked after the input/textarea typing guard"
    assert "toggleHotkeys();" in app_js[hotkey_idx:hotkey_idx + 250]


def test_logs_hotkey_works_anywhere():
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    guard_idx = app_js.index("/^(INPUT|TEXTAREA|SELECT)$/.test(tag)")
    logs_key_idx = app_js.index("event.key === 'l' || event.key === 'L'")
    modal_guard_idx = app_js.index("var rackOverEditor = ")
    assert guard_idx < logs_key_idx < modal_guard_idx, (
        "L hotkey must be placed after the typing guard but before modal/editor guards"
    )
    snippet = app_js[logs_key_idx:logs_key_idx + 400]
    assert "if (LogsState.open) { closeLogsModal(); } else { showLogs(); }" in snippet


def test_popout_logs_closes_on_escape_and_l():
    logs_html = (STATIC / "logs.html").read_text(encoding="utf-8")
    assert "event.key === 'Escape'" in logs_html
    assert "event.key === 'l' || event.key === 'L'" in logs_html


def test_guide_documents_question_mark_hotkey():
    guide = (STATIC / "guide.md").read_text(encoding="utf-8")
    assert "| ? | show or hide the hot keys; again to close |" in guide

