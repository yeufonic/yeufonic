"""A take's recipe (#58): saved from the Save window, alone or beside the audio, and imported as a new take."""
import json
import zipfile

import pytest

pytest.importorskip("playwright.sync_api")

from helpers import api, card, make_song, take_ids, wait_take  # noqa: E402


def open_save(page, take_id):
    card(page, take_id).locator('[data-act="save"]').click()
    page.wait_for_selector("#save-modal:not(.hidden)")


def test_the_recipe_is_saved_beside_the_audio_and_alone_and_comes_back_as_a_take(page, app_server, tmp_path):
    made = make_song(page, app_server, style="sea shanty, choir")

    # The first time, nothing is chosen: nothing to save.
    open_save(page, made["id"])
    assert page.locator("#save-format button.active").count() == 0 and page.locator("#save-recipe.active").count() == 0
    assert page.locator("#save-run").is_disabled() and "Choose what to save" in page.locator("#save-note").inner_text()

    # Take with FLAC: one zip holding both.
    page.click("#save-recipe")
    page.click('#save-format button[data-format="flac"]')
    assert "one zip" in page.locator("#save-note").inner_text()
    with page.expect_download() as got:
        page.click("#save-run")
    zipped = tmp_path / got.value.suggested_filename
    got.value.save_as(zipped)
    assert zipped.suffix == ".zip"
    names = zipfile.ZipFile(zipped).namelist()
    assert any(n.endswith(".flac") for n in names) and any(n.endswith(".yeufonic.json") for n in names)

    # Both are remembered; pressing FLAC again leaves the audio out: the recipe alone.
    open_save(page, made["id"])
    assert page.locator("#save-recipe.active").count() == 1
    assert page.locator('#save-format button.active').get_attribute("data-format") == "flac"
    page.click('#save-format button.active')
    with page.expect_download() as got:
        page.click("#save-run")
    alone = tmp_path / got.value.suggested_filename
    got.value.save_as(alone)
    assert alone.name.endswith(".yeufonic.json")
    recipe = json.loads(alone.read_text())
    assert recipe["format"] == "yeufonic-take" and recipe["take"]["style"] == "sea shanty, choir"

    # And next time it starts with the recipe alone, as last saved.
    open_save(page, made["id"])
    assert page.locator("#save-recipe.active").count() == 1 and page.locator("#save-format button.active").count() == 0
    page.click("#save-close")

    # Imported: a new take holding the same plan, ready to render.
    before = take_ids(page)
    page.set_input_files("#take-import-file", str(alone))
    page.wait_for_function("(before) => [...document.querySelectorAll('#takes article.take')]"
                           ".some(a => !before.includes(a.dataset.id))", arg=before)
    new_id = page.evaluate("(before) => [...document.querySelectorAll('#takes article.take')]"
                           ".map(a => a.dataset.id).find(id => !before.includes(id))", before)
    imported = api(app_server, f"/api/takes/{new_id}")
    original = api(app_server, f"/api/takes/{made['id']}")
    assert imported["status"] == "planned" and imported["abc"] == original["abc"]
    assert imported["seed"] == original["seed"] and imported["style"] == original["style"]
    assert "plan ready" in card(page, new_id).inner_text()

    # And it renders.
    card(page, new_id).locator(".take-status, [data-act='render']").first.wait_for()
    page.evaluate("(id) => fetch('/api/takes/' + id + '/render', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'})", new_id)
    assert wait_take(app_server, new_id)["has_audio"]


@pytest.mark.console_allows("status of 400")
def test_a_file_that_is_not_a_take_is_refused_and_says_so(page, app_server, tmp_path):
    bad = tmp_path / "notes.json"
    bad.write_text('{"hello": "world"}')
    page.set_input_files("#take-import-file", str(bad))
    page.wait_for_selector("#confirm-modal:not(.hidden)")
    assert "not a Yeufonic take file" in page.locator("#confirm-message").inner_text()
    page.click("#confirm-ok")
