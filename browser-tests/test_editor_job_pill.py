"""The editor covers the top bar, so it carries a copy of the job pill, shown while the pill is, and never at the
cost of a second line in the editor's header."""
import pytest

pytest.importorskip("playwright.sync_api")

from conftest import ARTIFACTS  # noqa: E402
from helpers import make_song, open_new  # noqa: E402


def _busy(page):
    page.evaluate("""() => {
      $('job-card').classList.remove('hidden');
      $('job-title').textContent = 'Training a voice: A rather long voice name for the pill';
      $('job-time').textContent = '108:37';
      $('job-bar').style.width = '40%';
      paintJobPill(0);
    }""")
    page.wait_for_selector("#ed-job:not(.hidden)")


def test_the_editor_shows_what_the_engine_is_doing(page, app_server):
    open_new(page, "Song")
    _busy(page)
    assert page.inner_text("#ed-job .job-pill-time") == "108:37"
    page.evaluate("() => $('job-card').classList.add('hidden')")
    page.wait_for_selector("#ed-job.hidden", state="attached")


@pytest.mark.parametrize("width", [1600, 1280])
def test_with_a_take_open_the_header_stays_on_one_line(page, app_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    take_id = make_song(page, app_server)["id"]
    page.evaluate("id => selectTake(takeById(id))", take_id)
    page.evaluate("() => openEditor('song')")
    page.wait_for_selector("#ed-take-tools:not(.hidden)")
    page.evaluate("() => editorMax() && setEditorMax(false)")
    _busy(page)
    head = page.locator("#editor .ed-head")
    page.locator("#editor .ed-head").screenshot(path=str(ARTIFACTS / f"editor-head-{width}.png"))
    tops = page.evaluate("""() => Array.from(document.querySelectorAll('#editor .ed-head > *'))
      .filter(el => el.offsetParent !== null).map(el => Math.round(el.getBoundingClientRect().top))""")
    assert max(tops) - min(tops) < 20, f"the header wrapped: {tops}"
    assert head.bounding_box()["height"] < 90
