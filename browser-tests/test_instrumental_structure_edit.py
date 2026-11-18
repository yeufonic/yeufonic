"""An instrumental's structure once it has a plan: written afresh into a new take, and a new instrumental starting from a
clean structure whatever was open before."""
import pytest

pytest.importorskip("playwright.sync_api")

from fake_engine import tones  # noqa: E402
from helpers import card, new_take_id, open_new, take, take_ids, wait_take  # noqa: E402


def make_instrumental(page, app_server):
    before = take_ids(page)
    open_new(page, "Instrumental")
    page.fill("#style", "calm piano, strings")
    page.click("#create-inst")
    return wait_take(app_server, new_take_id(page, before))


def test_an_instrumental_with_a_plan_gets_a_new_structure_in_a_new_take(page, app_server):
    made = make_instrumental(page, app_server)
    card(page, made["id"]).locator('[data-act="open"]').click()
    page.wait_for_function("(id) => takeIdInEditor() === id", arg=made["id"])
    page.evaluate("() => openEditor('song')")             # the card's open button shows the score page
    page.wait_for_selector('[data-sec-act="restructure"]')
    sections = page.evaluate("() => scoreSectionSpans(document.getElementById('abc').value).map(s => s.name)")
    assert "this take's score" in page.locator("#structure-body").inner_text()

    page.click('[data-sec-act="restructure"]')
    # The editable list a new instrumental has, holding this take's sections; the button writes a new plan.
    assert page.evaluate("() => STRUCTURE.sections.map(s => s.name)") == sections
    assert page.locator("#structure-body select").count() == len(sections)
    assert page.locator("#create-inst").inner_text() == "Write score plan"
    page.click("#structure-body [data-add='bridge']")

    page.click('[data-sec-act="back"]')                    # and back again
    page.wait_for_selector('[data-sec-act="restructure"]')
    assert page.locator("#create-inst").inner_text() == "Render this score"

    page.click('[data-sec-act="restructure"]')
    page.click("#structure-body [data-add='bridge']")
    before = take_ids(page)
    page.click("#create-inst")
    fresh = take(app_server, new_take_id(page, before))
    assert fresh["kind"] == "instrumental" and fresh["id"] != made["id"]
    assert fresh["lyrics"].split() == [f"[{name}]" for name in sections + ["bridge"]]
    assert take(app_server, made["id"])["abc"] == made["abc"]          # the take that was open is left as it was


def test_a_new_instrumental_after_one_from_a_recording_starts_clean(page, app_server, tmp_path):
    path = tmp_path / "Shoreline sketch.wav"
    path.write_bytes(tones(9.7))
    open_new(page, "Instrumental")
    page.set_input_files("#file", str(path))
    page.wait_for_function("() => document.getElementById('source-select').value", timeout=30000)
    page.click("#editor-close")
    open_new(page, "Instrumental")
    assert page.evaluate("() => document.getElementById('source-select').value") == ""
    assert page.locator("#structure-kind").is_visible()
    assert page.evaluate("() => STRUCTURE.sections.length") == 8
