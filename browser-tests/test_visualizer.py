"""The visualizer: what moves behind each scene over the take's picture, B to change it, and the choice kept."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import card, make_song  # noqa: E402

DEFAULTS = {"artwork": "Drifting colour", "yeufonic": "Breath", "kaleidoscope": "Spectrum halo", "grid": "Light rays",
            "liquid": "Ripples", "bars": "Breath"}


def test_each_picture_scene_starts_on_its_own_backdrop_and_b_changes_it_for_good(page, app_server):
    made = make_song(page, app_server, style="synthwave, night drive")
    page.wait_for_function("(id) => { const c = document.querySelector(`#takes article.take[data-id='${id}'] .cover`);"
                           " return c && c.classList.contains('has-art'); }", arg=made["id"], timeout=60000)
    card(page, made["id"]).locator('[data-act="play"]').click()
    page.wait_for_function("() => !document.getElementById('audio').paused")
    page.keyboard.press("v")
    page.wait_for_function("() => window.Visualizer && Visualizer.isOpen")
    for mode, name in DEFAULTS.items():
        page.evaluate(f"() => Visualizer.setMode('{mode}')")
        # Once a frame of it is drawn, which on a busy machine can take more than a few hundred milliseconds.
        try:
            page.wait_for_function("(name) => Visualizer.artMotionName() === name", arg=name, timeout=5000)
        except Exception:
            pass
        assert page.evaluate("() => Visualizer.artMotionName()") == name, mode
    page.evaluate("() => Visualizer.setMode('artwork')")
    page.locator('.vis-bottom-hint kbd[data-key="b"]').click()                # the hint's B acts as the key
    assert page.evaluate("() => Visualizer.artMotionName()") == "Depth"
    page.evaluate("() => Visualizer.setMode('wave')")
    page.keyboard.press("b")                                                  # a scene with its own background
    page.evaluate("() => document.getElementById('audio').pause()")
    page.reload()
    page.wait_for_function("() => window.Visualizer")
    page.evaluate("() => Visualizer.setMode('artwork')")
    assert page.evaluate("() => Visualizer.artMotionName()") == "Depth"        # kept in this browser
    page.evaluate("() => Visualizer.setMode('grid')")
    assert page.evaluate("() => Visualizer.artMotionName()") == "Light rays"   # another scene keeps its own
