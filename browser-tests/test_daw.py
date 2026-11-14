"""Save → For a DAW: one zip with the take's audio, the score as MIDI (written by the page) and ABC, a chord chart
and the recipe."""
import zipfile

import pytest

pytest.importorskip("playwright.sync_api")

from helpers import make_song  # noqa: E402
from test_recipe import open_save  # noqa: E402


def test_for_a_daw_saves_one_zip_with_the_midi_in_it(page, app_server, tmp_path):
    made = make_song(page, app_server, style="indie rock, electric guitar, drums")
    open_save(page, made["id"])
    page.click('#save-format button[data-format="daw"]')
    assert "for a DAW" in page.locator("#save-note").inner_text()
    with page.expect_download() as got:
        page.click("#save-run")
    zipped = tmp_path / got.value.suggested_filename
    got.value.save_as(zipped)
    assert zipped.name.endswith(" - DAW.zip")
    archive = zipfile.ZipFile(zipped)
    names = archive.namelist()
    assert any(n.endswith(".wav") for n in names) and any(n.endswith(".mid") for n in names)
    assert any(n.endswith(".abc") for n in names) and any(n.endswith("chart.txt") for n in names)
    midi = archive.read(next(n for n in names if n.endswith(".mid")))
    assert midi[:4] == b"MThd"
