"""The version check: what it says, and what it must never do.

Every test here is offline.  Both places it would ask are replaced, so the suite is about
what the answers mean rather than whether yeufonic.com is up — and one of the cases below
is that neither answer arrives at all.
"""
import pytest

from app import config, update
from app.db import set_setting

MANIFEST = {
    "latest": "0.0.12",
    "released": "2026-10-02T09:00:00Z",
    "notes": "https://example.invalid/releases/v0.0.12",
    "installer": {"url": "https://example.invalid/Yeufonic-Setup-0.0.12.exe",
                  "sha256": "abc123", "bytes": 612345},
    "docker": "git pull && docker compose up -d --build",
}

RELEASE = {
    "tag_name": "v0.0.12",
    "html_url": "https://example.invalid/releases/tag/v0.0.12",
    "assets": [{"name": "Yeufonic-Setup-0.0.12.exe",
                "browser_download_url": "https://example.invalid/setup.exe",
                "digest": "sha256:deadbeef"}],
}


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    """A known build, and the state that goes with it.  Pinning the version keeps these
    tests from depending on what VERSION happens to say today: the fixtures name 0.0.12,
    and the day the app really became 0.0.12, four of them started failing for the right
    reason — 0.0.12 is not newer than 0.0.12."""
    monkeypatch.setattr(config, "VERSION", "0.0.10")
    # A Docker install wherever the tests run: on a Mac the state would otherwise say macos
    # and look for a disk image.  The Windows and Mac cases set theirs.
    monkeypatch.setattr(update, "_install_kind", lambda: "docker")
    monkeypatch.setattr(update, "STATE", update._initial())


def answering(monkeypatch, manifest=None, release=None):
    """A stand-in for the network: each source answers with what it was given, and one
    that was given nothing is unreachable, which is the offline case as well."""
    def fetch(url):
        source = manifest if url == update.MANIFEST_URL else release
        if source is None:
            raise OSError("no route to host")
        return source
    monkeypatch.setattr(update, "_fetch_json", fetch)


def test_versions_are_compared_as_numbers():
    # The one that bites: as text, '0.0.9' sorts after '0.0.10'.
    assert update.is_newer("0.0.10", "0.0.9") is True
    assert update.is_newer("v0.0.10", "0.0.9") is True
    assert update.is_newer("0.0.9", "0.0.10") is False
    assert update.is_newer("0.0.10", "0.0.10") is False
    assert update.is_newer("0.0.13-beta", "0.0.12") is True
    assert update.is_newer(None, "0.0.10") is False
    assert update.is_newer("nonsense", "0.0.10") is False


@pytest.mark.anyio
async def test_a_newer_manifest_is_news(monkeypatch):
    answering(monkeypatch, manifest=MANIFEST)
    state = await update.check(force=True)
    assert state["newer"] is True
    assert state["latest"] == "0.0.12"
    assert state["installer"] == MANIFEST["installer"]["url"]
    assert state["sha256"] == "abc123"
    assert state["error"] is None
    assert state["checked"] > 0
    assert state["source"] == "yeufonic.com"
    assert state["source_url"] == update.MANIFEST_URL


@pytest.mark.anyio
async def test_the_release_notes_are_the_fallback_when_the_site_is_silent(monkeypatch):
    answering(monkeypatch, release=RELEASE)          # the manifest raises
    state = await update.check(force=True)
    assert state["newer"] is True
    assert state["latest"] == "0.0.12"               # the 'v' comes off the tag
    assert state["installer"] == "https://example.invalid/setup.exe"
    assert state["sha256"] == "sha256:deadbeef"
    assert state["notes"] == RELEASE["html_url"]
    assert state["source"] == "github"
    assert state["source_url"] == update.RELEASE_API


@pytest.mark.anyio
async def test_a_build_ahead_of_the_last_release_says_nothing(monkeypatch):
    # Which is the normal case here: every deploy bumps VERSION, only releases get tagged.
    answering(monkeypatch, manifest={**MANIFEST, "latest": "0.0.1"})
    state = await update.check(force=True)
    assert state["latest"] == "0.0.1"
    assert state["newer"] is False


@pytest.mark.anyio
async def test_offline_is_quiet(monkeypatch):
    answering(monkeypatch)                           # neither source answers
    state = await update.check(force=True)
    assert state["newer"] is False
    assert state["latest"] is None
    assert state["error"]
    assert state["checked"] > 0                      # it will try again tomorrow
    assert update.state()["advice"]                  # and the page still gets an answer


def test_the_gap_between_checks_is_deliberate():
    # Four hours: a release reaches an install the same working session, and six small
    # requests a day to our own static file costs nobody anything.
    assert update.EVERY == 4 * 60 * 60


@pytest.mark.anyio
async def test_the_check_waits_between_times_and_the_manual_one_does_not(monkeypatch):
    asked = []

    def fetch(url):
        asked.append(url)
        return MANIFEST
    monkeypatch.setattr(update, "_fetch_json", fetch)

    await update.check(force=False)                  # the watcher's, first thing
    await update.check(force=False)                  # inside the gap: no request
    assert len(asked) == 1
    await update.check(force=True)                   # the menu's: asks again
    assert len(asked) == 2


@pytest.mark.anyio
async def test_startup_checks_fresh_after_restore(monkeypatch):
    asked = []

    def fetch(url):
        asked.append(url)
        return MANIFEST
    monkeypatch.setattr(update, "_fetch_json", fetch)

    await update.check(force=False)
    assert len(asked) == 1

    # App restarts: restore() is called
    monkeypatch.setattr(update, "STATE", update._initial())
    update.restore()

    # The watcher runs check(force=False) on startup
    await update.check(force=False)
    assert len(asked) == 2



@pytest.mark.anyio
async def test_the_setting_stops_the_automatic_check_only(monkeypatch):
    asked = []

    def fetch(url):
        asked.append(url)
        return MANIFEST
    monkeypatch.setattr(update, "_fetch_json", fetch)

    set_setting("app.update_check", "off")
    await update.check(force=False, enabled=False)
    assert asked == []
    await update.check(force=True)                   # Check for updates still asks
    assert len(asked) == 1


@pytest.mark.anyio
async def test_being_told_once_is_enough(monkeypatch, data_dir):
    answering(monkeypatch, manifest=MANIFEST)
    assert (await update.check(force=True))["seen"] is False
    update.mark_seen("0.0.12")
    assert update.state()["seen"] is True
    # A later check of the same release does not raise the notice again.
    assert (await update.check(force=True))["seen"] is True


@pytest.mark.anyio
async def test_the_advice_matches_the_install(monkeypatch):
    answering(monkeypatch, manifest=MANIFEST)
    await update.check(force=True)
    update.STATE["install"] = "windows"
    assert "installer" in update.state()["advice"]
    update.STATE["install"] = "docker"
    assert "git pull" in update.state()["advice"]


@pytest.mark.anyio
async def test_a_restart_remembers_what_it_was_offering(monkeypatch):
    answering(monkeypatch, manifest=MANIFEST)
    await update.check(force=True)
    # A new process: the same answer, without asking again and without losing the link.
    monkeypatch.setattr(update, "STATE", update._initial())
    update.restore()
    state = update.state()
    assert state["latest"] == "0.0.12"
    assert state["newer"] is True
    assert state["installer"] == MANIFEST["installer"]["url"]
    assert state["seen"] is False


def test_the_page_is_given_it_with_the_rest_of_the_state(client):
    body = client.get("/api/state").json()
    info = body["update"]
    assert info["current"] == config.VERSION
    assert info["newer"] is False
    assert info["install"] in ("windows", "docker")
    assert "advice" in info


def test_the_menu_can_ask_whatever_the_setting_says(client, monkeypatch):
    answering(monkeypatch, manifest=MANIFEST)
    set_setting("app.update_check", "off")
    body = client.post("/api/update/check").json()
    assert body["newer"] is True and body["latest"] == "0.0.12"
    # And the daily setting is still off: nothing was asked on its behalf.
    assert client.post("/api/update/seen", json={"version": "0.0.12"}).json()["seen"] is True


def test_the_setting_is_offered_with_a_sensible_default(client):
    spec = [item for item in client.get("/api/state").json()["settings"]
            if item["key"] == "app.update_check"]
    assert spec and spec[0]["default"] == "on"
    assert [option["value"] for option in spec[0]["options"]] == ["on", "off"]


import hashlib
from pathlib import Path


def test_get_downloads_dir_exists():
    p = update.get_downloads_dir()
    assert isinstance(p, Path)
    assert p.is_dir()


@pytest.mark.anyio
async def test_start_download_and_verify_success(monkeypatch, tmp_path):
    monkeypatch.setattr(update, "get_downloads_dir", lambda: tmp_path)
    fake_content = b"fake-exe-installer-binary-data"
    content_hash = hashlib.sha256(fake_content).hexdigest()

    update.STATE["latest"] = "0.0.12"
    update.STATE["installer"] = "https://example.invalid/Yeufonic-Setup-0.0.12.exe"
    update.STATE["sha256"] = content_hash

    class MockResponse:
        def __init__(self):
            self.headers = {"content-length": str(len(fake_content))}

        def raise_for_status(self):
            pass

        async def aiter_bytes(self, chunk_size=1024):
            yield fake_content

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        def stream(self, method, url, headers=None):
            return MockResponse()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockClient)

    state = await update.start_download()
    # Wait for background task if running
    if update._download_task:
        await update._download_task

    final_state = update.download_state()
    assert final_state["status"] == "done"
    assert final_state["progress"] == 1.0
    target_file = tmp_path / "Yeufonic-Setup-0.0.12.exe"
    assert target_file.is_file()
    assert target_file.read_bytes() == fake_content
    assert not (tmp_path / "Yeufonic-Setup-0.0.12.exe.part").exists()


@pytest.mark.anyio
async def test_start_download_hash_mismatch(monkeypatch, tmp_path):
    monkeypatch.setattr(update, "get_downloads_dir", lambda: tmp_path)
    fake_content = b"fake-exe-installer-binary-data"

    update.STATE["latest"] = "0.0.12"
    update.STATE["installer"] = "https://example.invalid/Yeufonic-Setup-0.0.12.exe"
    update.STATE["sha256"] = "wrong_hash"

    class MockResponse:
        def __init__(self):
            self.headers = {"content-length": str(len(fake_content))}

        def raise_for_status(self):
            pass

        async def aiter_bytes(self, chunk_size=1024):
            yield fake_content

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        def stream(self, method, url, headers=None):
            return MockResponse()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockClient)

    await update.start_download()
    if update._download_task:
        try:
            await update._download_task
        except Exception:
            pass

    final_state = update.download_state()
    assert final_state["status"] == "error"
    assert "Checksum mismatch" in str(final_state["error"])
    assert not (tmp_path / "Yeufonic-Setup-0.0.12.exe").exists()
    assert not (tmp_path / "Yeufonic-Setup-0.0.12.exe.part").exists()


@pytest.mark.anyio
async def test_start_download_reuses_existing_valid_file(monkeypatch, tmp_path):
    monkeypatch.setattr(update, "get_downloads_dir", lambda: tmp_path)
    fake_content = b"already-downloaded-installer-data"
    content_hash = hashlib.sha256(fake_content).hexdigest()

    target_file = tmp_path / "Yeufonic-Setup-0.0.12.exe"
    target_file.write_bytes(fake_content)

    update.STATE["latest"] = "0.0.12"
    update.STATE["installer"] = "https://example.invalid/Yeufonic-Setup-0.0.12.exe"
    update.STATE["sha256"] = content_hash

    state = await update.start_download()
    assert state["status"] == "done"
    assert state["progress"] == 1.0
    assert state["path"] == str(target_file)


def test_cancel_download_cleans_up(monkeypatch, tmp_path):
    monkeypatch.setattr(update, "get_downloads_dir", lambda: tmp_path)
    part_file = tmp_path / "Yeufonic-Setup-0.0.12.exe.part"
    part_file.write_bytes(b"partial-data")
    update.DOWNLOAD_STATE["filename"] = "Yeufonic-Setup-0.0.12.exe"
    update.DOWNLOAD_STATE["status"] = "downloading"

    res = update.cancel_download()
    assert res["status"] == "idle"
    assert not part_file.exists()


def test_download_api_endpoints(client, monkeypatch, tmp_path):
    monkeypatch.setattr(update, "get_downloads_dir", lambda: tmp_path)
    res = client.get("/api/update/download").json()
    assert "status" in res

    cancel_res = client.post("/api/update/download/cancel").json()
    assert cancel_res["status"] == "idle"

    launch_res = client.post("/api/update/launch").json()
    assert "launched" in launch_res

    reveal_res = client.post("/api/update/reveal").json()
    assert "revealed" in reveal_res



def test_the_installer_is_started_outside_the_apps_job(tmp_path, monkeypatch):
    """The launcher ends everything in its job when it closes, the app is in that job, and the
    installer asks the person to close Yeufonic: so it is started with the break-away flag."""
    installer = tmp_path / "Yeufonic-Setup-9.9.9.exe"
    installer.write_bytes(b"MZ")
    monkeypatch.setitem(update.DOWNLOAD_STATE, "path", str(installer))
    monkeypatch.setattr(update.sys, "platform", "win32")
    started = []
    monkeypatch.setattr(update.subprocess, "Popen", lambda args, **kw: started.append((args, kw)))

    assert update.launch_installer() is True
    args, kw = started[0]
    assert args == [str(installer)]
    assert kw["creationflags"] & update.CREATE_BREAKAWAY_FROM_JOB
    assert kw["creationflags"] & update.DETACHED_PROCESS


def test_an_installer_that_cannot_break_away_is_still_started(tmp_path, monkeypatch):
    installer = tmp_path / "Yeufonic-Setup-9.9.9.exe"
    installer.write_bytes(b"MZ")
    monkeypatch.setitem(update.DOWNLOAD_STATE, "path", str(installer))
    monkeypatch.setattr(update.sys, "platform", "win32")

    def refused(*args, **kw):
        raise OSError(5, "Access is denied")
    opened = []
    monkeypatch.setattr(update.subprocess, "Popen", refused)
    monkeypatch.setattr(update.os, "startfile", lambda path: opened.append(path), raising=False)

    assert update.launch_installer() is True
    assert opened == [str(installer)]


def test_a_test_manifest_is_the_only_place_asked(monkeypatch):
    """A test build is pointed at an address only the tester knows, and asks nowhere else: not the
    site's manifest, and not GitHub, which would answer with the public release."""
    asked = []

    def fetch(url):
        asked.append(url)
        if url == "https://example.invalid/t/updates.json":
            return {"latest": "9.9.9", "installer": {"url": "https://example.invalid/t/setup.exe", "sha256": "abc"}}
        raise AssertionError(f"asked {url}")
    monkeypatch.setattr(update, "_fetch_json", fetch)
    monkeypatch.setattr(config, "UPDATE_MANIFEST", "https://example.invalid/t/updates.json")

    answer = update._ask()
    assert asked == ["https://example.invalid/t/updates.json"]
    assert answer["latest"] == "9.9.9" and answer["source"] == "test manifest"


def test_a_test_manifest_that_does_not_answer_does_not_fall_back_to_github(monkeypatch):
    asked = []

    def fetch(url):
        asked.append(url)
        raise OSError("down")
    monkeypatch.setattr(update, "_fetch_json", fetch)
    monkeypatch.setattr(config, "UPDATE_MANIFEST", "https://example.invalid/t/updates.json")

    with pytest.raises(OSError):
        update._ask()
    assert asked == ["https://example.invalid/t/updates.json"]
