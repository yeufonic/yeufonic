"""The recording picker searches what it lists, and the take panel's blocks fold to their heading and stay folded."""

import pytest

pytest.importorskip("playwright.sync_api")

from helpers import card, make_song  # noqa: E402


def test_the_recording_picker_searches_its_recordings(page):
    page.evaluate("""() => {
      State.sources = [
        { id: 'r1', title: 'Harbour lights demo', origin: 'upload', has_score: true },
        { id: 'r2', title: 'Night ferry', origin: 'upload', has_score: true },
        { id: 'r3', title: 'Lights on the quay', origin: 'recording' } ];
      State.corpusSongs = [];
      loadCorpusSongs = () => {};
      setMode('cover');
      openEditor('song');
    }""")
    page.click("#source-picker-btn")
    assert page.evaluate("() => document.activeElement.id") == "source-filter"
    page.keyboard.type("lights")
    titles = page.locator("#source-picker-menu .source-picker-item[data-id] .source-item-title").all_inner_texts()
    assert sorted(titles) == ["Harbour lights demo", "Lights on the quay"]
    page.keyboard.type(" quay")
    assert page.locator("#source-picker-menu .source-picker-item[data-id] .source-item-title").all_inner_texts() == ["Lights on the quay"]
    page.keyboard.press("Control+A")
    page.keyboard.type("zzz")
    assert "No recording matches." in page.locator("#source-picker-menu").inner_text()


def test_a_panel_block_folds_and_stays_folded(page, app_server):
    made = make_song(page, app_server)
    card(page, made["id"]).click(position={"x": 30, "y": 12})
    page.wait_for_selector('#take-sheet [data-fold="sound"]')
    page.click('#take-sheet [data-fold="sound"] .fold-head')
    assert "folded" in page.get_attribute('#take-sheet [data-fold="sound"]', "class")
    assert page.locator('#take-sheet [data-fold="sound"] .sheet-pairs').is_hidden()
    page.reload()
    page.wait_for_function("() => window.State && State.options && Object.keys(State.options).length > 0")
    card(page, made["id"]).click(position={"x": 30, "y": 12})
    page.wait_for_selector('#take-sheet [data-fold="sound"]')
    assert "folded" in page.get_attribute('#take-sheet [data-fold="sound"]', "class"), "kept in this browser"
    page.click('#take-sheet [data-fold="sound"] .fold-head')
    assert "folded" not in page.get_attribute('#take-sheet [data-fold="sound"]', "class")


def test_the_recording_and_style_lists_are_never_open_together(page):
    page.evaluate("() => { State.sources = [{ id: 'r1', title: 'Night ferry', origin: 'upload' }]; State.corpusSongs = [];"
                  " loadCorpusSongs = () => {}; setMode('cover'); openEditor('song'); }")
    page.click("#source-picker-btn")
    assert page.locator("#source-picker-menu").is_visible()
    page.click("#style-picker-btn")
    assert page.locator("#style-picker-menu").is_visible() and page.locator("#source-picker-menu").is_hidden()
    page.click("#source-picker-btn")
    assert page.locator("#source-picker-menu").is_visible() and page.locator("#style-picker-menu").is_hidden()
