"""A song sung with no score, chosen in Mode, and Follow the style in the Advanced window, as a person uses them."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import WORDS, api, card, new_take_id, open_new, take_ids, wait_take  # noqa: E402


def test_a_song_with_no_score_greys_out_what_steers_a_plan_and_is_sung_at_once(page, app_server):
    open_new(page, "Song")
    assert page.locator("#mode-hint").is_hidden()
    page.select_option("#mode", "off")
    assert page.locator("#mode-hint").is_visible() and "No plan" in page.locator("#mode-hint").inner_text()
    assert page.locator("#harmony").is_disabled() and page.locator("#variety").is_disabled()
    assert page.locator("#create-song").inner_text() == "Sing with no score"
    page.screenshot(path="browser-tests/artifacts/no-score-chosen.png")

    page.fill("#style", "dream pop, hazy synths")
    page.fill("#lyrics", WORDS)
    before = take_ids(page)
    page.click("#create-song")
    take_id = new_take_id(page, before)
    done = wait_take(app_server, take_id)
    assert done["mode"] == "off" and not done["abc"] and done["has_audio"]
    page.wait_for_function("(id) => /no score/.test(document.querySelector(`#takes article.take[data-id='${id}']`)"
                           ".textContent)", arg=take_id)

    # Back to a score: the controls come back.
    open_new(page, "Song")
    page.select_option("#mode", "full")
    assert not page.locator("#harmony").is_disabled() and page.locator("#create-song").inner_text() == "Write score plan"


def test_no_score_is_for_songs_only(page, app_server):
    open_new(page, "Song")
    page.select_option("#mode", "off")
    page.click("#editor-close")
    open_new(page, "Cover")
    assert page.evaluate("() => document.getElementById('mode').value") == "full"
    assert page.evaluate("() => document.getElementById('mode-off').hidden") is True


def test_follow_the_style_is_set_in_advanced_and_kept_by_the_take(page, app_server):
    open_new(page, "Song")
    page.click("#btn-advanced-toggle")
    page.wait_for_selector("#adv-cfg-field", state="visible")
    page.fill("#adv-cfg-scale", "1.5")
    page.locator("#adv-cfg-scale").dispatch_event("input")
    assert page.locator("#adv-reset-btn").is_enabled()
    page.locator("#advanced-take-modal .modal-box, #advanced-take-modal").first.screenshot(
        path="browser-tests/artifacts/follow-the-style.png")
    page.click("#adv-done-btn")
    page.select_option("#mode", "off")
    page.fill("#style", "garage rock")
    page.fill("#lyrics", WORDS)
    before = take_ids(page)
    page.click("#create-song")
    take_id = new_take_id(page, before)
    assert wait_take(app_server, take_id)["cfg_scale"] == 1.5
    assert card(page, take_id).count() == 1
    assert api(app_server, f"/api/takes/{take_id}")["mode"] == "off"
