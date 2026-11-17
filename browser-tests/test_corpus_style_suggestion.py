"""A corpus song's style suggestion: Use in a new song opens + Song with it in the Style box, and Save as a style keeps it
in the style list under the name given."""
import json
import math
import struct
import urllib.request
import wave
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from conftest import APP  # noqa: E402
from helpers import confirm  # noqa: E402

HINT = "dusty folk rock, warm baritone, fingerpicked acoustic guitar, brushed drums"


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(APP + path, data=data, method=method, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(request, timeout=30).read())


def a_corpus_song(data):
    folder = Path(data) / "corpus" / "Test folk"      # the folder the app takes corpora from
    folder.mkdir(parents=True, exist_ok=True)
    with wave.open(str(folder / "Harbour lights.wav"), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(22050)
        out.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(i / 20))) for i in range(22050 * 3)))
    corpus = call("POST", "/api/identities", {"name": "Test folk", "trigger_word": "testfolk", "folder": str(folder),
                                              "consent": True})
    song = call("GET", f"/api/identities/{corpus['id']}")["songs"][0]
    call("PUT", f"/api/identities/{corpus['id']}/songs/{song['id']}", {"style_hint": HINT})
    return corpus["id"], song["id"]


def test_a_style_suggestion_goes_into_a_new_song_or_the_style_list(page, app_server):
    corpus_id, song_id = a_corpus_song(app_server["data"])
    page.evaluate("id => { openIdentities(); return showIdentity(id); }", corpus_id)
    page.click(f'[data-open="{song_id}"]')
    page.wait_for_selector(f'[data-use-style="{song_id}"]')

    page.click(f'[data-use-style="{song_id}"]')
    page.wait_for_selector("#editor-modal:not(.hidden)")
    assert page.input_value("#style") == HINT
    assert page.locator("#identities-modal").is_hidden()      # the corpus window gave way to the editor
    page.click("#editor-close")

    page.evaluate("id => { openIdentities(); return showIdentity(id); }", corpus_id)
    page.click(f'[data-open="{song_id}"]')
    page.click(f'[data-keep-style="{song_id}"]')
    confirm(page, "Harbour folk")
    page.wait_for_function(f"() => document.querySelector('[data-keep-style=\"{song_id}\"]').disabled")
    kept = call("GET", "/api/styles")
    assert [(s["name"], s["prompt"]) for s in kept] == [("Harbour folk", HINT)]
