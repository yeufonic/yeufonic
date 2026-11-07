"""The editor covers the top bar, so it carries a copy of the job pill, shown while the pill is."""
import pytest

pytest.importorskip("playwright.sync_api")

from conftest import ARTIFACTS  # noqa: E402
from helpers import open_new  # noqa: E402


def test_the_editor_shows_what_the_engine_is_doing(page, app_server):
    open_new(page, "Song")
    page.evaluate("""() => {
      $('job-card').classList.remove('hidden');
      $('job-title').textContent = 'Training a voice: Mine';
      $('job-time').textContent = '1:05';
      $('job-bar').style.width = '40%';
      paintJobPill(0);
    }""")
    page.wait_for_selector("#ed-job:not(.hidden)")
    assert page.inner_text("#ed-job .job-pill-text") == "Training a voice: Mine"
    assert page.inner_text("#ed-job .job-pill-time") == "1:05"
    page.locator("#editor .ed-head").screenshot(path=str(ARTIFACTS / "editor-job-pill.png"))
    page.evaluate("() => $('job-card').classList.add('hidden')")
    page.wait_for_selector("#ed-job.hidden", state="attached")
