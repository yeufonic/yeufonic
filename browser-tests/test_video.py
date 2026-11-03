"""Video both ways: Save offers a video of the song with its picture once the take has one, and a video dropped in as
a cover's recording comes in as its sound."""
import subprocess

import pytest

pytest.importorskip("playwright.sync_api")

from helpers import api, card, make_song, open_new  # noqa: E402


def open_save(page, take_id):
    card(page, take_id).locator('[data-act="save"]').click()
    page.wait_for_selector("#save-modal:not(.hidden)")


def test_save_offers_a_video_only_for_a_take_with_a_picture(page, app_server, tmp_path):
    made = make_song(page, app_server, style="dream pop, hazy synths")

    open_save(page, made["id"])
    assert page.locator("#save-video").is_hidden()
    page.click("#save-close")

    # A picture, as the app keeps one, and the library read again.
    art = app_server["data"] / "art"
    art.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=teal:s=256x256", "-frames:v", "1",
                    str(art / f"{made['id']}.png")], check=True)
    page.evaluate("() => loadTakes()")
    card(page, made["id"]).locator(".take-cover-pic, [data-act='cover-pic']").first.wait_for()

    open_save(page, made["id"])
    assert page.locator("#save-video").is_visible()
    page.click("#save-video")
    assert "video" in page.locator("#save-note").inner_text()
    with page.expect_download(timeout=60000) as got:
        page.click("#save-run")
    saved = tmp_path / got.value.suggested_filename
    got.value.save_as(saved)
    assert saved.suffix == ".mp4"
    codecs = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(saved)],
                            capture_output=True, text=True).stdout.split()
    assert sorted(codecs) == ["aac", "h264"]

    # Remembered for next time, while the take still has its picture.
    open_save(page, made["id"])
    assert page.locator("#save-format button.active").get_attribute("data-format") == "mp4"
    page.click("#save-close")


def test_a_video_dropped_in_for_a_cover_comes_in_as_its_sound(page, app_server, tmp_path):
    clip = tmp_path / "Rooftop rehearsal.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=160x120:d=6", "-f", "lavfi",
                    "-i", "sine=frequency=330:duration=6", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-shortest", str(clip)], check=True)
    before = {s["id"] for s in api(app_server, "/api/sources")}
    open_new(page, "Cover")
    page.set_input_files("#file", str(clip))
    page.wait_for_function("(before) => { const v = document.getElementById('source-select').value;"
                           " return v && !before.includes(v); }", arg=sorted(before), timeout=30000)
    assert "Rooftop rehearsal" in page.locator("#source-picker-label").inner_text()
    source_id = page.evaluate("() => document.getElementById('source-select').value")
    source = next(s for s in api(app_server, "/api/sources") if s["id"] == source_id)
    assert abs(source["duration"] - 6.0) < 0.3
