"""The transport's A–B button: pressed at the start of a part and again at its end, the take plays that part round
and round until it is pressed a third time; another take starts with no part set."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import make_song  # noqa: E402


def test_a_part_plays_round_until_the_loop_is_let_go(page, app_server):
    made = make_song(page, app_server)
    page.evaluate("(id) => { $('audio').muted = true; playTake(id); }", made["id"])
    page.wait_for_function("() => !$('audio').paused && $('audio').currentTime > 0.2")
    button = page.locator("#btn-abloop")
    assert button.inner_text() == "A–B" and "on" not in button.get_attribute("class")

    page.evaluate("() => { $('audio').currentTime = 1.0; }")
    button.click()
    assert page.evaluate("() => ABLOOP.a") == pytest.approx(1.0, abs=0.3)
    assert "half" in button.get_attribute("class")
    page.evaluate("() => { $('audio').currentTime = 2.5; }")
    button.click()
    assert "on" in button.get_attribute("class") and button.get_attribute("aria-pressed") == "true"
    loop = page.evaluate("() => [ABLOOP.a, ABLOOP.b]")
    assert loop[0] == pytest.approx(1.0, abs=0.3) and loop[1] == pytest.approx(2.5, abs=0.3)

    # Played on into B, it goes back to A, more than once.
    for _ in range(2):
        page.wait_for_function("(b) => $('audio').currentTime > b - 0.4", arg=loop[1], timeout=6000)
        page.wait_for_function("(a) => $('audio').currentTime < a + 0.5", arg=loop[0], timeout=6000)

    button.click()                                            # let go: it plays on past B
    assert page.evaluate("() => ABLOOP.b") is None and "on" not in button.get_attribute("class")
    page.wait_for_function("(b) => $('audio').currentTime > b + 0.5", arg=loop[1], timeout=6000)

    page.evaluate("() => { $('audio').currentTime = 1.0; }")
    button.click()
    other = make_song(page, app_server, style="slow folk, male vocal")
    page.evaluate("(id) => playTake(id)", other["id"])          # another take: no part set
    page.wait_for_function("() => ABLOOP.a === null")
    page.evaluate("() => $('audio').pause()")
