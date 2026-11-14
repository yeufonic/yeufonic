"""The take panel's score line names the time signature, and every one a plan changes to on the way."""
import pytest

pytest.importorskip("playwright.sync_api")

HELD = 'X:1\nT:\nM:3/4\nL:1/16\nQ:1/4=90\nV: Vocal\nK:D\n% verse\nV: Vocal\n"D"d12|"G"g12|\n'
LEFT = 'X:1\nT:\nM:3/4\nL:1/32\nQ:1/4=120\nV: Vocal\nK:D\n% intro\nV: Vocal\nM:4/4\n"G"z32|"D"z32|\n'


def test_the_score_line_names_the_time_signature(page):
    held = page.evaluate("(abc) => sheetScore(abc)", HELD)
    assert held["meters"] == ["3/4"] and held["bars"] == 2
    assert page.evaluate("(abc) => sheetScore(abc).meters", LEFT) == ["3/4", "4/4"]
    html = page.evaluate("""(abc) => sheetHTML({ id: 'x', title: 'Night drive', kind: 'song', status: 'done', abc: abc + ' '.repeat(60),
                                                  lyrics: '', has_audio: true })""", HELD)
    assert "Key D · 90 BPM · 2 bars · 3/4" in html
