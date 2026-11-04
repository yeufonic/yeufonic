"""The editor's words column, filling the window: the lyrics field never runs under the structure below it."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import open_new  # noqa: E402


def test_a_long_structure_does_not_cover_the_lyrics_checkboxes(page, app_server):
    open_new(page, "Cover")
    page.click("#editor-max")
    page.wait_for_function("() => document.getElementById('editor-max').getAttribute('aria-pressed') === 'true'")
    # A cover's sections from its recording's score: a long list, as a transcribed song gives, and the cue switch.
    page.evaluate("""() => {
      document.getElementById('lyrics').value = '[Verse]\\n' + 'a line of words\\n'.repeat(30);
      document.getElementById('structure-field').style.display = '';
      document.getElementById('structure-body').innerHTML =
        Array.from({ length: 14 }, (_, i) => `<div style="height:60px;border:1px solid #444">section ${i + 1}</div>`).join('');
      document.getElementById('voices-wrap').classList.remove('hidden');
    }""")
    page.wait_for_timeout(200)
    box = lambda sel: page.locator(sel).bounding_box()
    lyrics, voices, structure = box("#lyrics"), box("#voices-wrap"), box("#structure-field")
    assert lyrics["y"] + lyrics["height"] <= voices["y"] + 1
    assert voices["y"] + voices["height"] <= structure["y"] + 1
    # The switch can be clicked: nothing lies over it.
    before = page.is_checked("#voice-cues")
    page.click("#voices-wrap")
    assert page.is_checked("#voice-cues") != before
