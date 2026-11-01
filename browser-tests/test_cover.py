"""A cover, as a person makes one: a recording in, its words heard, its tune transcribed, the cover rendered."""
import pytest

pytest.importorskip("playwright.sync_api")

from fake_engine import tones  # noqa: E402
from helpers import api, new_take_id, open_new, take_ids, wait_take  # noqa: E402


SEEN = []


@pytest.fixture
def recording(tmp_path):
    """A recording of its own for each test: the app keeps one copy of a file it has been given before."""
    SEEN.append(1)
    path = tmp_path / f"Harbour demo {len(SEEN)}.wav"
    path.write_bytes(tones(12.0 + len(SEEN) / 10))
    return path


def load_recording(page, app_server, recording):
    """Choose the file as the Browse button would; the app takes it in and picks it."""
    before = {s["id"] for s in api(app_server, "/api/sources")}
    open_new(page, "Cover")
    page.set_input_files("#file", str(recording))
    page.wait_for_function("(before) => { const v = document.getElementById('source-select').value;"
                           " return v && !before.includes(v); }", arg=sorted(before), timeout=30000)
    return page.evaluate("() => document.getElementById('source-select').value")


def test_a_cover_from_a_recording(page, app_server, recording):
    source_id = load_recording(page, app_server, recording)
    assert "Harbour demo" in page.locator("#source-picker-label").inner_text()

    page.click("#source-lyrics")
    page.wait_for_function("() => document.getElementById('lyrics').value.includes('harbour wall')", timeout=60000)
    assert page.locator("#lyrics-hear-job.bad").count() == 0

    page.click("#transcribe")
    # As a person waits: until the page says the recording has its score.
    page.wait_for_function("() => /score/.test(document.getElementById('source-picker-label').textContent)", timeout=60000)
    assert next(s for s in api(app_server, "/api/sources") if s["id"] == source_id)["has_score"]

    before = take_ids(page)
    page.fill("#style", "acoustic folk, warm vocal")
    page.click("#create-cover")
    take_id = new_take_id(page, before)
    done = wait_take(app_server, take_id)
    assert done["kind"] == "cover" and done["source_id"] == source_id and done["has_audio"]


@pytest.mark.console_allows("Failed to load resource: net::ERR_FAILED")
def test_getting_the_words_carries_on_while_the_app_cannot_be_reached(page, app_server, recording):
    """The page asks how the job is going every second and a half.  While the app restarts those requests fail; the
    page used to give up at the first and say 'Lost touch with the job', though the job went on."""
    load_recording(page, app_server, recording)
    asked = []

    def unreachable(route):
        # The first ask is the button's own, before it starts the job: the app is there for that one.
        asked.append(route.request.method)
        if route.request.method == "GET" and asked.count("GET") > 1:
            route.abort()
        else:
            route.continue_()
    page.route("**/api/sources/*/lyrics", unreachable)
    page.click("#source-lyrics")
    page.wait_for_function("() => /Reaching the app/.test(document.getElementById('lyrics-hear-stage').textContent)")
    page.wait_for_timeout(4000)
    assert page.locator("#lyrics-hear-job.bad").count() == 0
    page.unroute("**/api/sources/*/lyrics")
    page.wait_for_function("() => document.getElementById('lyrics').value.includes('harbour wall')", timeout=60000)
    assert "Lost touch" not in page.locator("#lyrics-hear-stage").inner_text()


def test_a_failure_to_get_the_words_goes_when_another_recording_is_chosen(page, app_server, recording, tmp_path):
    first = load_recording(page, app_server, recording)
    page.route("**/api/sources/*/lyrics",
               lambda route: route.fulfill(json={"state": "failed", "error": "a test failure"})
               if route.request.method == "GET" else route.continue_())
    page.click("#source-lyrics")
    page.wait_for_selector("#lyrics-hear-job.bad")
    assert "a test failure" in page.locator("#lyrics-hear-stage").inner_text()
    page.unroute("**/api/sources/*/lyrics")

    other = tmp_path / "Second demo.wav"
    other.write_bytes(tones(6.3))
    page.set_input_files("#file", str(other))
    page.wait_for_function("(first) => { const v = document.getElementById('source-select').value; return v && v !== first; }",
                           arg=first, timeout=30000)
    page.wait_for_selector("#lyrics-hear-job", state="hidden")
