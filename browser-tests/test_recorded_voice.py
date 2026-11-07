"""The editor's Recorded voice field: it shows the voice of the take open in the editor, and waits for one being made."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import open_new  # noqa: E402


def test_the_field_follows_the_take_and_polls_a_voice_being_made(page, app_server):
    open_new(page, "Song")
    page.wait_for_selector("#persona-select")
    assert page.inner_text("label[for=persona-select]") == "Recorded voice"
    # Two voices, as /api/voices lists them: one ready, one still being tokenised.
    page.evaluate("""() => {
      PERSONA.list = [
        { id: 'aaaaaaaaaaaa', name: 'Mine', state: 'ready', prefix_seconds: 48 },
        { id: 'bbbbbbbbbbbb', name: 'Busy', state: 'preparing', prefix_seconds: 48 }];
      paintPersonaField();
    }""")
    assert page.is_disabled("#persona-select option[value=bbbbbbbbbbbb]")
    # A take with a voice selects it; a take without one clears it, rather than inheriting the last take's.
    page.evaluate("() => setPersonaFromTake({ voice_id: 'aaaaaaaaaaaa' })")
    assert page.input_value("#persona-select") == "aaaaaaaaaaaa"
    assert not page.is_hidden("#persona-seconds-wrap")
    page.evaluate("() => setPersonaFromTake({ voice_id: null })")
    assert page.input_value("#persona-select") == ""
    # While the server lists a voice as preparing, the list is asked again; once it is ready it stops.
    calls = []
    page.route("**/api/voices", lambda route: (calls.append(1), route.fulfill(
        json=[{"id": "bbbbbbbbbbbb", "name": "Busy", "state": "preparing" if len(calls) < 2 else "ready",
               "prefix_seconds": 48}])))
    page.evaluate("() => loadPersonas()")
    page.wait_for_function("() => !document.querySelector('#persona-select option[value=bbbbbbbbbbbb]').disabled",
                           timeout=10000)
    page.wait_for_timeout(3500)
    assert len(calls) == 2


def test_make_a_voice_asks_in_the_apps_own_dialog_then_goes_back_to_the_main_page(page, app_server):
    page.route("**/api/voices/from-identity", lambda route: route.fulfill(
        json={"id": "cccccccccccc", "name": "Band voice", "state": "preparing", "prefix_seconds": 48}))
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
