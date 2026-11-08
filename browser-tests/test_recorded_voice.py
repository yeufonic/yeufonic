"""The editor's Recorded voice field: it shows the voice of the take open in the editor, and waits for one being made."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import open_new  # noqa: E402


SERVICE = {"ok": True, "running": True, "models": {}}


def test_the_field_is_hidden_without_the_voice_service(page, app_server):
    page.route("**/api/voices/service", lambda route: route.fulfill(json={"ok": False, "running": False, "models": {}}))
    page.route("**/api/voices", lambda route: route.fulfill(json=[]))
    page.evaluate("() => loadPersonas()")
    open_new(page, "Song")
    page.wait_for_selector("#persona-field", state="attached")
    assert page.is_hidden("#persona-field")


def test_the_field_follows_the_take_shows_training_and_moves_an_octave(page, app_server):
    page.route("**/api/voices/service", lambda route: route.fulfill(json=SERVICE))
    calls = []
    def voices(route):
        calls.append(1)
        busy = len(calls) < 2
        route.fulfill(json=[
            {"id": "aaaaaaaaaaaa", "name": "Mine", "state": "ready", "octave": 0, "progress": 1},
            {"id": "bbbbbbbbbbbb", "name": "Busy", "state": "training" if busy else "ready", "octave": 0,
             "progress": 0.4 if busy else 1}])
    page.route("**/api/voices", voices)
    patched = []
    page.route("**/api/voices/aaaaaaaaaaaa", lambda route: (patched.append(route.request.post_data), route.fulfill(
        json={"id": "aaaaaaaaaaaa", "name": "Mine", "state": "ready", "octave": 1, "progress": 1})))
    page.evaluate("() => loadPersonas()")
    open_new(page, "Song")
    page.wait_for_selector("#persona-select option[value=bbbbbbbbbbbb]", state="attached")
    assert page.inner_text("label[for=persona-select]") == "Recorded voice"
    busy = page.locator("#persona-select option[value=bbbbbbbbbbbb]")
    assert busy.is_disabled() and "40%" in busy.inner_text()
    # A take with a voice selects it, and the octave shows; a take without one clears it.
    page.evaluate("() => setPersonaFromTake({ id: 't1', voice_id: 'aaaaaaaaaaaa' })")
    assert page.input_value("#persona-select") == "aaaaaaaaaaaa"
    assert not page.is_hidden("#persona-octave-wrap")
    page.select_option("#persona-octave", "1")
    page.wait_for_function("() => PERSONA.list[0].octave === 1")
    assert "octave=1" in patched[0]
    page.evaluate("() => setPersonaFromTake({ id: 't2', voice_id: null })")
    assert page.input_value("#persona-select") == ""
    # While a voice trains the list is asked again; once it is ready the option can be chosen.
    page.wait_for_function("() => !document.querySelector('#persona-select option[value=bbbbbbbbbbbb]').disabled",
                           timeout=15000)


def test_make_a_voice_asks_in_the_apps_own_dialog_then_goes_back_to_the_main_page(page, app_server):
    page.route("**/api/voices/from-identity", lambda route: route.fulfill(
        json={"id": "cccccccccccc", "name": "Band voice", "state": "training", "octave": 0, "progress": 0}))
    page.route("**/api/voices/service", lambda route: route.fulfill(json=SERVICE))
    page.route("**/api/voices", lambda route: route.fulfill(json=[]))
    page.evaluate("() => openIdentities()")
    page.wait_for_selector("#identities-modal:not(.hidden)")
    page.evaluate("() => { makeVoiceFromCorpus('abcdefabcdef', 'Band'); }")
    # The name is asked in the app's centred dialog, over Corpora, not in the browser's prompt.
    page.wait_for_selector("#confirm-modal:not(.hidden) #confirm-input:not(.hidden)")
    assert page.input_value("#confirm-input") == "Band voice"
    box = page.locator("#confirm-modal .modal-box, #confirm-modal > div").first.bounding_box()
    centre = box["x"] + box["width"] / 2
    assert abs(centre - 800) < 40
    page.click("#confirm-ok")
    page.wait_for_selector("#identities-modal.hidden", state="attached")
    assert page.is_hidden("#confirm-modal")


def test_a_failed_voice_can_be_chosen_to_train_it_again(page, app_server):
    page.route("**/api/voices/service", lambda route: route.fulfill(json=SERVICE))
    page.route("**/api/voices", lambda route: route.fulfill(json=[
        {"id": "dddddddddddd", "name": "Old", "state": "failed", "octave": 0, "progress": 0}]))
    page.evaluate("() => loadPersonas()")
    open_new(page, "Song")
    page.wait_for_selector("#persona-select option[value=dddddddddddd]", state="attached")
    assert not page.is_disabled("#persona-select option[value=dddddddddddd]")
    page.select_option("#persona-select", "dddddddddddd")
    assert not page.is_hidden("#persona-regen")
    assert page.is_hidden("#persona-octave-wrap")
    assert "Regenerate" in page.inner_text("#persona-hint")


def test_a_ready_voice_can_be_downloaded_and_a_voice_imported(page, app_server):
    page.route("**/api/voices/service", lambda route: route.fulfill(json=SERVICE))
    page.route("**/api/voices", lambda route: route.fulfill(json=[
        {"id": "eeeeeeeeeeee", "name": "Ready", "state": "ready", "octave": 0, "progress": 1}]))
    page.evaluate("() => loadPersonas()")
    open_new(page, "Song")
    page.wait_for_selector("#persona-import", state="attached")
    assert not page.is_hidden("#persona-import")
    assert page.is_hidden("#persona-export")
    page.select_option("#persona-select", "eeeeeeeeeeee")
    assert not page.is_hidden("#persona-export")
