"""Compare plays every take at once, from the same instant, and a switch only moves which one is heard: nothing
restarts, so the change is gapless and lands on the same moment of the song."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import card, make_song  # noqa: E402

GAINS = "() => COMPARE.items.map(item => Math.round(item.gain.gain.value * 100) / 100)"


def test_a_switch_moves_the_gains_and_restarts_nothing(page, app_server):
    first = make_song(page, app_server)
    second = make_song(page, app_server, style="slow folk, male vocal")
    for made in (first, second):
        card(page, made["id"]).locator('input[data-act="pick"]').check()
    page.click("#compare-picked")
    page.wait_for_function("() => COMPARE.loaded === 2 && !$('compare-play').disabled")
    assert page.evaluate("() => COMPARE.items.every(item => item.buffer)")

    page.click("#compare-play")
    page.wait_for_function("() => comparePosition() > 0.6")
    page.evaluate("() => { window.__sources = COMPARE.sources.slice(); }")
    page.wait_for_function(f"() => {{ const g = ({GAINS})(); return g[0] > 0.04 && g[1] === 0; }}")
    before = page.evaluate("() => comparePosition()")

    page.keyboard.press("2")
    page.wait_for_function(f"() => {{ const g = ({GAINS})(); return g[0] === 0 && g[1] > 0.04; }}")
    after = page.evaluate("() => comparePosition()")
    assert after >= before, "the place in the song carries on"
    assert page.evaluate("() => COMPARE.sources.every((source, i) => source === window.__sources[i])"), \
        "the same sources play on: nothing was restarted"
    assert page.evaluate("() => COMPARE.active") == 1

    page.keyboard.press("Space")
    assert page.evaluate("() => COMPARE.playing") is False
    held = page.evaluate("() => comparePosition()")
    page.wait_for_timeout(300)
    assert page.evaluate("() => comparePosition()") == held

    page.click("#compare-close")
    assert page.evaluate("() => COMPARE.ctx") is None
