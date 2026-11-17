"""An emptied Length cap box is no cap of anyone's: the take gets the one in Settings, which rises to fit a longer plan,
not a cap of 360 seconds taken as typed by hand."""
import json
import urllib.request

import pytest

pytest.importorskip("playwright.sync_api")

from conftest import APP  # noqa: E402
from helpers import new_take_id, open_new, take, take_ids  # noqa: E402


def setting(key, value):
    req = urllib.request.Request(APP + "/api/settings", data=json.dumps({"key": key, "value": value}).encode(),
                                 method="PUT", headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10).read()


def made_with_cap(page, app_server, cap_text):
    before = take_ids(page)
    open_new(page, "Song")
    page.fill("#style", "indie rock, guitars")
    page.fill("#lyrics", "[Verse]\nfirst line here\n[Chorus]\nsecond line here")
    page.fill("#max-duration", cap_text)
    page.locator("#max-duration").blur()
    page.click("#create-song")
    return take(app_server, new_take_id(page, before))


def test_an_emptied_cap_is_the_settings_one_and_a_typed_one_stands(page, app_server):
    setting("takes.cap", "900")
    page.reload()
    page.wait_for_function("() => typeof setting === 'function' && String(setting('takes.cap', '')) === '900'")
    emptied = made_with_cap(page, app_server, "")
    assert (emptied["max_duration"], emptied["cap_typed"]) == (900, 0)
    typed = made_with_cap(page, app_server, "300")
    assert (typed["max_duration"], typed["cap_typed"]) == (300, 1)
    setting("takes.cap", "360")
