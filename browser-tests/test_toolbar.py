"""The row above the takes: the space as its heading and the list that chooses one, what picked takes offer, and the
job's pill in the top bar."""
import json
import urllib.request

import pytest

pytest.importorskip("playwright.sync_api")

from helpers import WORDS, card, make_song  # noqa: E402


def post(app_server, path, body):
    req = urllib.request.Request(app_server["url"] + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Origin": app_server["url"]})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def test_a_space_is_found_by_typing_and_chosen_with_enter(page, app_server):
    for name in ("Lighthouse demos", "Lantern songs", "Quay sketches"):
        post(app_server, "/api/spaces", {"name": name})
    page.reload()
    page.wait_for_function("() => window.State && State.spaces && State.spaces.length >= 4")
    page.click("#space-pick")
    assert page.locator("#space-find").evaluate("el => el === document.activeElement")
    page.keyboard.type("lant")
    assert page.locator("#space-list .space-row").all_inner_texts() == ["Lantern songs\n0"]
    page.keyboard.press("Enter")
    page.wait_for_function("() => document.getElementById('takes-heading').textContent === 'Lantern songs'")
    assert page.locator("#space-menu").is_hidden()
    assert page.locator("#space-count").inner_text() == "0 takes"
    # Escape shuts the list and leaves the space as it was.
    page.click("#space-pick")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Escape")
    assert page.locator("#space-menu").is_hidden()
    assert page.locator("#takes-heading").inner_text() == "Lantern songs"
    # The list's own actions are in it; Default cannot be deleted.
    page.click("#space-pick")
    page.locator("#space-list .space-row", has_text="Default").first.click()
    page.wait_for_function("() => document.getElementById('takes-heading').textContent.startsWith('Default')")
    page.click("#space-pick")
    assert page.locator("#space-delete").is_disabled()
    assert page.locator("#space-rename").is_visible() and page.locator("#take-import").is_visible()


def test_picked_takes_swap_the_filters_for_what_can_be_done_with_them(page, app_server):
    first = make_song(page, app_server)
    second = make_song(page, app_server, style="slow folk, male vocal")
    assert page.locator(".show-tools").is_visible() and page.locator("#pick-tools").is_hidden()
    for made in (first, second):
        card(page, made["id"]).locator('input[data-act="pick"]').check()
    assert page.locator(".show-tools").is_hidden()
    assert page.locator("#picked-count").inner_text() == "2 picked"
    assert page.locator("#compare-picked").is_visible() and page.locator("#bulk-delete").inner_text() == "Delete 2"
    page.click("#pick-done")
    assert page.locator(".show-tools").is_visible() and page.locator("#pick-tools").is_hidden()
    assert not card(page, first["id"]).locator('input[data-act="pick"]').is_checked()


def test_the_view_icons_show_which_layout_is_on(page, app_server):
    page.click("#layout-comfy")
    assert "active" in page.locator("#layout-comfy").get_attribute("class")
    assert "active" not in (page.locator("#layout-compact").get_attribute("class") or "")
    assert "comfy" in page.locator("#takes").get_attribute("class")
    page.click("#layout-compact")
    assert "comfy" not in page.locator("#takes").get_attribute("class")
    page.click("#fold-toggle")
    assert page.locator("#fold-toggle").get_attribute("aria-pressed") == "true"
    page.click("#fold-toggle")
    # A kind shown is lit, and the others fade; clicking it again shows every kind.
    page.locator(".filters .kinds").screenshot(path="browser-tests/artifacts/kinds-none.png")
    page.click('[data-takekind="cover"]')
    assert page.locator('[data-takekind="cover"]').get_attribute("aria-pressed") == "true"
    assert "some" in page.locator(".filters .kinds").get_attribute("class")
    page.locator(".filters .kinds").screenshot(path="browser-tests/artifacts/kinds-one.png")
    page.click('[data-takekind="song"]')
    page.mouse.move(5, 600)
    page.locator(".filters .kinds").screenshot(path="browser-tests/artifacts/kinds-two.png")
    page.click('[data-takekind="song"]')
    page.click('[data-takekind="cover"]')
    assert "some" not in page.locator(".filters .kinds").get_attribute("class")
    # Starred is one switch.
    page.click('[data-filter="favourite"]')
    page.wait_for_function("() => State.filter === 'favourite'")
    page.click('[data-filter="favourite"]')
    page.wait_for_function("() => State.filter === 'all'")


def test_a_job_shows_in_the_top_bar_and_the_takes_stay_where_they_are(page, app_server):
    make_song(page, app_server)
    top = page.evaluate("() => document.getElementById('takes').getBoundingClientRect().top")
    for n in range(3):
        post(app_server, "/api/songs", {"title": f"Queue test {n}", "style": "bright pop", "lyrics": WORDS,
                                        "auto_render": True})
    page.wait_for_selector("#job-card:not(.hidden)")
    assert page.locator("#job-card").evaluate("el => !!el.closest('.topbar')")
    assert page.evaluate("() => document.getElementById('takes').getBoundingClientRect().top") == top
    assert page.locator("#job-panel").is_hidden()
    page.click("#job-pill")
    page.wait_for_selector("#job-panel:not(.hidden)")
    assert page.locator("#job-stop").is_visible()
    assert page.locator("#job-pill-text").inner_text() == page.locator("#job-title").inner_text()
    page.mouse.click(5, 600)
    assert page.locator("#job-panel").is_hidden()
    page.wait_for_selector("#job-card.hidden", state="attached", timeout=60000)
