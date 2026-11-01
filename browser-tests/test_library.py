"""Making takes from the page and doing what people do with them in the library."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import card, confirm, make_song, new_take_id, open_new, take, take_ids, wait_take  # noqa: E402


def test_the_page_comes_up_with_the_engine_ready(page):
    pill = page.locator("#engine-pill")
    assert "ready" in pill.inner_text().lower()
    for kind in ("Song", "Cover", "Instrumental"):
        assert page.get_by_role("button", name=f"+ {kind}").first.is_visible()


def test_a_song_is_planned_rendered_and_plays(page, app_server):
    made = make_song(page, app_server, style="warm indie rock, male vocal")
    assert made["kind"] == "song" and made["has_audio"]
    tile = card(page, made["id"])
    tile.wait_for()
    assert "Lights along the harbour wall" in tile.locator(".take-title").inner_text()
    # Once the page has the finished take: which engine rendered it.
    page.wait_for_function("(id) => /Engine: ComfyUI/.test(document.querySelector(`#takes article.take[data-id='${id}']"
                           " .take-meta`).textContent)", arg=made["id"])
    tile.locator('[data-act="play"]').click()
    page.wait_for_function("() => { const a = document.getElementById('audio'); return a && !a.paused && a.currentTime > 0.3; }")
    assert "Lights along the harbour wall" in page.locator("#np-title").inner_text()
    page.click("#btn-play")          # pause again: nothing goes on playing after the test
    page.wait_for_function("() => document.getElementById('audio').paused")


def test_an_instrumental_is_made_from_a_style(page, app_server):
    before = take_ids(page)
    open_new(page, "Instrumental")
    page.fill("#style", "calm piano, strings")
    page.click("#create-inst")
    take_id = new_take_id(page, before)
    done = wait_take(app_server, take_id)
    assert done["status"] == "done"


def test_a_take_is_starred_renamed_and_deleted(page, app_server):
    made = make_song(page, app_server)
    tile = card(page, made["id"])
    tile.locator('[data-act="star"]').click()
    page.wait_for_function("(id) => State.takes.some(t => t.id === id && t.favourite)", arg=made["id"])
    assert take(app_server, made["id"])["favourite"]

    tile.locator(".take-title").dblclick()
    page.fill(".take-title-input", "Harbour lights, second go")
    page.press(".take-title-input", "Enter")
    page.wait_for_function("(id) => document.querySelector(`#takes article.take[data-id='${id}'] .take-title`)"
                           ".textContent.includes('second go')", arg=made["id"])
    assert take(app_server, made["id"])["title"] == "Harbour lights, second go"

    tile.locator('[data-act="del"]').click()
    confirm(page)
    card(page, made["id"]).wait_for(state="detached")
    assert made["id"] not in take_ids(page)
