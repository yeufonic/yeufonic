"""The rest of a working session: lyric drafts, stems, a picture, playlists, spaces, the score, settings."""
import time

import pytest

pytest.importorskip("playwright.sync_api")

from helpers import api, card, confirm, make_song, open_new  # noqa: E402


def test_lyrics_are_drafted_on_this_pc(page, app_server):
    open_new(page, "Song")
    page.fill("#style", "bright indie pop")
    page.click("#lyrics-write")
    page.wait_for_selector("#write-modal:not(.hidden)")
    page.fill("#write-brief", "a ship leaving harbour at night")
    page.click("#write-go")
    page.wait_for_function("() => document.getElementById('lyrics').value.includes('Hold on')", timeout=60000)


def test_stems_are_separated_from_a_take(page, app_server):
    made = make_song(page, app_server)
    before = len(api(app_server, "/api/stem-sets"))
    card(page, made["id"]).locator('[data-act="stems"]').click()
    page.wait_for_selector("#stems-modal:not(.hidden)")
    page.click("#stems-run")
    deadline = time.time() + 60
    while len(api(app_server, "/api/stem-sets")) <= before:
        assert time.time() < deadline, "no stems were made"
        time.sleep(0.5)


def test_a_finished_take_gets_its_picture(page, app_server):
    made = make_song(page, app_server, style="synthwave, night drive")
    page.wait_for_function("(id) => { const c = document.querySelector(`#takes article.take[data-id='${id}'] .cover`);"
                           " return c && c.classList.contains('has-art'); }", arg=made["id"], timeout=60000)
    src = card(page, made["id"]).locator(".cover").get_attribute("data-art")
    loaded = page.evaluate("(src) => new Promise(ok => { const i = new Image(); i.onload = () => ok(i.naturalWidth);"
                           " i.onerror = () => ok(0); i.src = src; })", src)
    assert loaded > 0


def test_a_take_goes_in_a_new_playlist_and_plays_from_it(page, app_server):
    made = make_song(page, app_server)
    card(page, made["id"]).locator('[data-act="playlist"]').click()
    page.wait_for_selector("#playlist-picker-modal:not(.hidden)")
    page.fill("#playlist-picker-new-name", "Harbour mix")
    page.click("#playlist-picker-create")
    deadline = time.time() + 15
    while not any(p.get("name") == "Harbour mix" and p.get("count", p.get("track_count", 1))
                  for p in api(app_server, "/api/playlists")):
        assert time.time() < deadline, "the playlist was not made"
        time.sleep(0.3)
    page.keyboard.press("Escape")
    page.click("#view-btn-playlists")
    page.get_by_text("Harbour mix").first.click()
    page.wait_for_selector("#playlist-tracks-body tr")
    page.click("#playlist-play-hero-btn")
    page.wait_for_function("() => { const a = document.getElementById('audio'); return !a.paused && a.currentTime > 0.3; }")
    page.click("#btn-play")
    page.wait_for_function("() => document.getElementById('audio').paused")


def test_a_new_space_holds_a_take_moved_into_it(page, app_server):
    made = make_song(page, app_server)
    page.click("#space-new")
    confirm(page, "Sea songs")
    page.wait_for_function("() => [...document.getElementById('space').options].some(o => o.text.startsWith('Sea songs'))")
    page.select_option("#space", label=next(o for o in page.eval_on_selector_all("#space option", "os => os.map(o => o.text)")
                                             if o.startswith("Default")))
    card(page, made["id"]).locator('[data-act="move"]').click()
    page.wait_for_selector("#move-modal:not(.hidden)")
    page.locator("#move-list").get_by_text("Sea songs").first.click()
    page.wait_for_function("(id) => !document.querySelector(`#takes article.take[data-id='${id}']`)", arg=made["id"])
    space = next(s for s in api(app_server, "/api/spaces") if s["name"] == "Sea songs")
    assert api(app_server, f"/api/takes/{made['id']}")["space_id"] == space["id"]


def test_the_score_of_a_take_opens_in_the_editor(page, app_server):
    made = make_song(page, app_server)
    card(page, made["id"]).locator('[data-act="open"]').click()
    page.wait_for_selector("#editor-modal:not(.hidden)")
    page.wait_for_function("() => document.getElementById('abc').value.includes('X:1')")
    assert page.locator("#abc").is_visible()


def open_settings(page):
    page.click("#brand")
    page.click("#menu-settings")
    page.wait_for_selector("#settings-modal:not(.hidden)")
    choice = page.locator('#settings-list [data-key="art.words"]')
    group = page.locator("#settings-list details.settings-group", has=page.locator('[data-key="art.words"]'))
    if group.get_attribute("open") is None:
        group.locator("summary").click()            # its group, opened as a person would
    return choice


def test_a_setting_is_kept(page, app_server):
    """Who describes a take's picture, changed in Settings: saved at once, and there after a reload."""
    choice = open_settings(page)
    assert choice.input_value() == "auto"
    choice.select_option("take")
    deadline = time.time() + 10
    while next(x for x in api(app_server, "/api/settings")["settings"] if x["key"] == "art.words")["value"] != "take":
        assert time.time() < deadline, "the setting was not saved"
        time.sleep(0.3)
    page.reload()
    page.wait_for_function("() => window.State && State.options && Object.keys(State.options).length > 0")
    choice = open_settings(page)
    assert choice.input_value() == "take"
    choice.select_option("auto")
    # Your own prompt for pictures: a text box that takes no more than 512 characters.
    own = page.locator('#settings-list input[data-key="art.prompt"]')
    assert own.get_attribute("maxlength") == "512"
    page.click("#settings-close")
    page.wait_for_selector("#settings-modal", state="hidden")
