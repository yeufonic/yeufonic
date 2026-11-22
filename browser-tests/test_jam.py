"""Jam: opened from a take, a pass rolled from it and built on, the editor's round trip, and the keys."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import api, card, make_song, wait_take  # noqa: E402


def open_jam(page, take_id):
    card(page, take_id).click()
    page.wait_for_selector('#take-sheet [data-sheet="jam"]')
    page.click('#take-sheet [data-sheet="jam"]')
    page.wait_for_selector("#jam-modal:not(.hidden) .jam-hist-card.is-seed")


def test_a_pass_is_rolled_built_on_and_kept_out_of_the_library(page, app_server):
    made = make_song(page, app_server, style="dream pop, reverb guitars, female vocal")
    open_jam(page, made["id"])
    # The Seed is the base, and the Parts come from its style.
    assert page.locator(".jam-hist-card.is-seed.is-base").count() == 1
    assert page.locator(".jam-part-chip").count() >= 2
    assert "Seed" in page.locator(".jam-roll-from").inner_text()

    # A Part added counts as a change on Roll.
    page.click('.jam-tab[data-tab="genre"]')
    page.click('.jam-pick-chip[data-part-name="Shoegaze"]')
    assert page.locator(".jam-pending-badge").inner_text().startswith("1")

    page.click('[data-jam-act="roll"]')
    page.wait_for_selector(".jam-hist-card:not(.is-seed)")
    pass_id = page.evaluate("() => JSON.parse(localStorage.getItem('yue2.jam.sessions'))['take:' + "
                            f"'{made['id']}'].passes.filter(p => !p.isSeed)[0].id")
    rolled = wait_take(app_server, pass_id)
    assert rolled["space_id"] == "__jam__" and rolled["abc"] and rolled["max_duration"] == 40
    assert pass_id not in [t["id"] for t in api(app_server, "/api/takes")]
    page.wait_for_selector(f'.jam-hist-card.selectable[data-pass-id="{pass_id}"]', timeout=30000)
    assert "from" in page.locator(f'.jam-hist-card[data-pass-id="{pass_id}"] .jam-from').inner_text().lower()

    # Clicking the card makes it the base: its settings come back, and the footer says so.
    page.click(f'.jam-hist-card[data-pass-id="{pass_id}"] .jam-hist-name')
    page.wait_for_selector(f'.jam-hist-card.is-base[data-pass-id="{pass_id}"]')
    assert "Pass #1" in page.locator(".jam-roll-from").inner_text()
    assert page.locator(".jam-pending-badge").count() == 0

    # The editor opens the pass without keeping it, and closing it comes back to the Jam.
    page.click(f'.jam-hist-card[data-pass-id="{pass_id}"] [data-jam-act="open-editor"]')
    page.wait_for_selector("#editor-modal:not(.hidden)")
    assert api(app_server, f"/api/takes/{pass_id}")["space_id"] == "__jam__"
    page.click("#editor-close")
    page.wait_for_selector("#jam-modal:not(.hidden)")
    assert page.locator(f'.jam-hist-card.is-base[data-pass-id="{pass_id}"]').count() == 1

    # Esc closes it.
    page.locator(".jam-col-head h4").first.click()
    page.keyboard.press("Escape")
    page.wait_for_selector("#jam-modal", state="hidden")


def test_a_full_song_asks_first(page, app_server):
    made = make_song(page, app_server, style="synthwave, analog synth, female vocal")
    open_jam(page, made["id"])
    page.click('[data-jam-act="scope-full"]')
    page.click('[data-jam-act="roll"]')
    page.wait_for_selector("#confirm-modal:not(.hidden)")
    page.click("#confirm-cancel")
    page.wait_for_selector("#confirm-modal", state="hidden")
    assert page.locator(".jam-hist-card:not(.is-seed)").count() == 0
