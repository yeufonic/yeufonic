"""A new page starts on Song, and each of the main page's letter keys means one thing: V the visualizer and Shift+V
Variations, L the logs and Shift+L the visualizer's lyrics, whatever is playing or showing."""
import pytest

pytest.importorskip("playwright.sync_api")

TAKE = """() => {
  const take = { id: 'k1', title: 'Night drive', abc: 'X:1\\n' + 'K:C\\n' + 'C D E F '.repeat(20), status: 'done',
                 parent_id: null, has_audio: true };
  window.__acts = [];
  selectedTakeId = () => 'k1';
  takeById = (id) => id === 'k1' ? take : null;
  runTakeAction = (act, id) => { window.__acts.push(act + ':' + id); };
}"""


def test_a_new_page_starts_on_song(page):
    assert page.evaluate("() => State.mode") == "song"
    assert page.locator("#headline").inner_text() == "Write a song"


def test_v_is_the_visualizer_and_shift_v_variations(page):
    page.evaluate(TAKE)
    page.locator("body").click(position={"x": 5, "y": 5})
    page.keyboard.press("v")                                   # nothing playing: still the visualizer
    page.wait_for_function("() => Visualizer.isOpen === true")
    page.keyboard.press("v")
    page.wait_for_function("() => Visualizer.isOpen === false")
    assert page.evaluate("() => window.__acts") == []
    page.keyboard.press("Shift+V")
    assert page.evaluate("() => window.__acts") == ["variations:k1"]
    assert page.evaluate("() => Visualizer.isOpen") is False


def test_l_is_the_logs_and_shift_l_the_lyrics(page):
    page.evaluate("() => { window.__lyrics = 0; Visualizer.toggleLyrics = () => { window.__lyrics++; }; }")
    page.locator("body").click(position={"x": 5, "y": 5})
    page.keyboard.press("l")
    page.wait_for_function("() => LogsState.open === true")
    page.keyboard.press("l")
    page.wait_for_function("() => LogsState.open === false")
    page.keyboard.press("v")
    page.wait_for_function("() => Visualizer.isOpen === true")
    page.keyboard.press("l")                                   # the logs, even with the visualizer showing
    page.wait_for_function("() => LogsState.open === true")
    page.keyboard.press("l")
    page.keyboard.press("Shift+L")
    assert page.evaluate("() => window.__lyrics") == 1
