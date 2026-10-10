"""Tests for active take / recording synchronization in the transport bar.

When a take is highlighted (via card click, selection change, or mastering rack inspection),
its associated recording (rendered audio, or source recording if not yet rendered)
becomes active in the transport bar ready for playback via the Spacebar.
"""
from pathlib import Path


APP_JS = Path(__file__).resolve().parent.parent / "app" / "static" / "app.js"


def test_activate_take_recording_function_present():
    content = APP_JS.read_text(encoding="utf-8")
    assert "function activateTakeRecording(take)" in content, "activateTakeRecording definition is missing"
    assert "take.has_audio" in content, "Should check if take has rendered audio"
    assert "take.source_id" in content, "Should check if take has a source recording"


def test_set_selection_and_select_take_call_activate_take_recording():
    content = APP_JS.read_text(encoding="utf-8")
    assert "activateTakeRecording(take);" in content, "selectTake should invoke activateTakeRecording"
    assert "activateTakeRecording(t)" in content, "setSelection should invoke activateTakeRecording for active take"


def test_mastering_button_selects_take():
    content = APP_JS.read_text(encoding="utf-8")
    # Finding act === 'mastering' block
    idx = content.find("act === 'mastering'")
    assert idx != -1, "act === 'mastering' handler not found"
    snippet = content[idx:idx + 350]
    assert "selectTake(targetTake)" in snippet, "Clicking mastering icon must select the take"
    assert "openForTake(targetTake)" in snippet, "Clicking mastering icon must open rack for take"


def test_transport_play_handles_unrendered_take():
    content = APP_JS.read_text(encoding="utf-8")
    assert "This take has not been rendered yet." in content, (
        "btn-play should notify the user when the highlighted take has no audio or source"
    )
