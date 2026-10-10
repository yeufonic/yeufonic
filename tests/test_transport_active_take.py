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
    snippet = content[idx:idx + 500]
    assert "selectTake(targetTake)" in snippet, "Clicking mastering icon must select the take"
    assert "openForTake(targetTake)" in snippet, "Clicking mastering icon must open rack for take"


def test_transport_play_handles_unrendered_take():
    content = APP_JS.read_text(encoding="utf-8")
    assert "This take has not been rendered yet." in content, (
        "btn-play should notify the user when the highlighted take has no audio or source"
    )


def test_playback_continues_when_another_take_selected():
    content = APP_JS.read_text(encoding="utf-8")
    idx = content.find("function activateTakeRecording(take)")
    assert idx != -1
    snippet = content[idx:idx + 400]
    assert "!audio.paused && !audio.ended" in snippet, (
        "activateTakeRecording should check if audio is currently playing"
    )
    assert "return;" in snippet, (
        "activateTakeRecording must return early and not pause audio when playback is active"
    )


def test_spacebar_plays_highlighted_take_when_another_is_playing():
    content = APP_JS.read_text(encoding="utf-8")
    btn_play_idx = content.find("$('btn-play').addEventListener('click'")
    assert btn_play_idx != -1
    snippet = content[btn_play_idx:btn_play_idx + 1500]
    assert "activeTake && activeTake.id !== State.playing" in snippet, (
        "btn-play should check if the highlighted take is different from the currently playing take"
    )
    assert "playTake(activeTake.id);" in snippet, (
        "btn-play must switch to and play the highlighted take"
    )


def test_ended_event_primes_highlighted_take():
    content = APP_JS.read_text(encoding="utf-8")
    ended_idx = content.find("stopWaveLoop(); wave.ratio = 1; drawWave();")
    assert ended_idx != -1
    snippet = content[ended_idx:ended_idx + 500]
    assert "activateTakeRecording(activeTake)" in snippet, (
        "When audio ends naturally, activateTakeRecording should prime the highlighted take"
    )


def test_active_playback_mastering_rack_not_altered_when_selecting_another_take():
    app_js = APP_JS.read_text(encoding="utf-8")
    idx = app_js.find("function activateTakeRecording(take)")
    assert idx != -1
    snippet = app_js[idx:idx + 400]
    # In activateTakeRecording's active audio guard, Rack.onTake must NOT be called
    guard_end = snippet.find("return;")
    assert guard_end != -1
    assert "Rack.onTake" not in snippet[:guard_end], (
        "activateTakeRecording must not call Rack.onTake while another take is playing"
    )

    # In rack.js, onTake must also guard against altering active playback
    rack_js = (APP_JS.parent / "rack.js").read_text(encoding="utf-8")
    on_take_idx = rack_js.find("onTake: function (take)")
    assert on_take_idx != -1
    on_take_snippet = rack_js[on_take_idx:on_take_idx + 400]
    assert "State.playing && String(State.playing) !== String(take.id)" in on_take_snippet, (
        "Rack.onTake must guard against modifying DSP when a different take is playing"
    )


def test_activate_take_recording_preserves_card_dom():
    app_js = APP_JS.read_text(encoding="utf-8")
    start = app_js.find("function activateTakeRecording(take)")
    assert start != -1
    end = app_js.find("function stepTake(delta)", start)
    assert end != -1
    snippet = app_js[start:end]
    assert "paintTakes()" not in snippet, (
        "activateTakeRecording must not call paintTakes() as rebuilding card DOM destroys dblclick and selection"
    )


def test_card_double_click_opens_editor():
    app_js = APP_JS.read_text(encoding="utf-8")
    click_idx = app_js.find("$('takes').addEventListener('click'")
    assert click_idx != -1
    click_snippet = app_js[click_idx:click_idx + 2000]
    assert "openEditor(take.status === 'planned' ? 'score' : 'song')" in click_snippet
    dblclick_idx = app_js.find("$('takes').addEventListener('dblclick'")
    assert dblclick_idx != -1
    dblclick_snippet = app_js[dblclick_idx:dblclick_idx + 1000]
    assert "openEditor(take.status === 'planned' ? 'score' : 'song')" in dblclick_snippet



