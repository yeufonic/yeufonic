"""Jam: opened from a take, a pass rolled from it and built on, and the keys."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import api, card, make_song, wait_take  # noqa: E402


def open_jam(page, take_id):
    # Chosen as the library does it: a click on the card could land on one of its buttons in a full library.
    card(page, take_id).wait_for()
    page.evaluate("(id) => selectTake(takeById(id))", take_id)
    page.wait_for_selector('#take-sheet [data-sheet="jam"]')
    page.click('#take-sheet [data-sheet="jam"]')
    page.wait_for_selector("#jam-modal:not(.hidden) .jam-hist-card.is-seed")


def test_a_pass_is_rolled_built_on_and_kept_out_of_the_library(page, app_server):
    made = make_song(page, app_server, style="dream pop, reverb guitars, female vocal")
    open_jam(page, made["id"])
    # The Seed is the base, and the Parts come from its style.
    assert page.locator(".jam-hist-card.is-seed.is-base").count() == 1
    assert page.locator(".jam-part-chip").count() >= 2
    assert "Seed" in page.locator(".jam-roll-from").inner_text()

    # A Part added counts as a change on Roll.
    page.click('.jam-tab[data-tab="genre"]')
    page.click('.jam-pick-chip[data-part-name="Shoegaze"]')
    assert page.locator(".jam-pending-badge").inner_text().startswith("1")
    # The Feel card starts collapsed; open it, pick a choice, and check it counts and is shown as set.
    page.click('[data-jam-act="feel-toggle"]')
    page.select_option("#jam-key", "D")
    assert page.locator(".jam-pending-badge").inner_text().startswith("2")
    assert "set" in page.locator("#jam-key").get_attribute("class")

    page.click('[data-jam-act="roll"]')
    page.wait_for_selector(".jam-hist-card:not(.is-seed)")
    pass_id = page.evaluate("() => JSON.parse(localStorage.getItem('yue2.jam.sessions'))['take:' + "
                            f"'{made['id']}'].passes.filter(p => !p.isSeed)[0].id")
    rolled = wait_take(app_server, pass_id)
    assert rolled["space_id"] == "__jam__" and rolled["abc"] and rolled["max_duration"] == 40
    assert pass_id not in [t["id"] for t in api(app_server, "/api/takes")]
    page.wait_for_selector(f'.jam-hist-card.selectable[data-pass-id="{pass_id}"]', timeout=30000)
    assert "from" in page.locator(f'.jam-hist-card[data-pass-id="{pass_id}"] .jam-from').inner_text().lower()

    # Clicking the card makes it the base: its settings come back, and the footer says so.
    page.click(f'.jam-hist-card[data-pass-id="{pass_id}"] .jam-hist-name')
    page.wait_for_selector(f'.jam-hist-card.is-base[data-pass-id="{pass_id}"]')
    assert "Pass #1" in page.locator(".jam-roll-from").inner_text()
    assert page.locator(".jam-pending-badge").count() == 0

    # The pass has no editor in Jam: its card offers Play, Full Song and Delete.
    assert page.locator(f'.jam-hist-card[data-pass-id="{pass_id}"] [data-jam-act="open-editor"]').count() == 0

    # Sync is on by itself once there are two tracks: number keys 0 jump to Seed, 1-9 to Pass #1-#9.
    page.wait_for_selector('.jam-sync-btn.on')
    page.locator(".jam-col-head h4").first.click()
    page.keyboard.press("0")
    page.wait_for_selector(".jam-hist-card.is-seed.is-base.playing")
    page.keyboard.press("1")
    page.wait_for_selector(f'.jam-hist-card.is-base.playing[data-pass-id="{pass_id}"]')
    page.keyboard.press("9")
    assert page.locator(f'.jam-hist-card.is-base.playing[data-pass-id="{pass_id}"]').count() == 1
    # Shift+0 to Shift+9 are Pass #10 to #19: the pass renumbered 12 in the saved Jam, Shift+2 reaches it.
    page.locator(".jam-col-head h4").first.click()
    page.keyboard.press("Escape")
    page.wait_for_selector("#jam-modal", state="hidden")
    page.evaluate("""([take, id]) => { const all = JSON.parse(localStorage.getItem('yue2.jam.sessions'));
        all['take:' + take].passes.forEach(p => { if (p.id === id) { p.num = 12; } });
        localStorage.setItem('yue2.jam.sessions', JSON.stringify(all)); }""", [made["id"], pass_id])
    page.reload()                                                # the Jam is read again from what was saved
    open_jam(page, made["id"])
    page.wait_for_selector('.jam-sync-btn.on')
    page.locator(".jam-col-head h4").first.click()
    page.keyboard.press("0")
    page.wait_for_selector(".jam-hist-card.is-seed.is-base.playing")
    page.keyboard.press("Shift+Digit2")
    page.wait_for_selector(f'.jam-hist-card.is-base.playing[data-pass-id="{pass_id}"]')
    page.keyboard.press("2")                                     # no Pass #2 now: nothing moves
    assert page.locator(f'.jam-hist-card.is-base[data-pass-id="{pass_id}"]').count() == 1
    # Turned off, it stays off, and the number keys do nothing.
    page.click('[data-jam-act="toggle-sync"]')
    page.wait_for_selector('.jam-sync-btn:not(.on)')
    page.locator(".jam-col-head h4").first.click()
    page.keyboard.press("0")
    assert page.locator(f'.jam-hist-card.is-base[data-pass-id="{pass_id}"]').count() == 1
    page.wait_for_timeout(500)
    assert page.locator('.jam-sync-btn.on').count() == 0
    page.click('[data-jam-act="toggle-sync"]')          # back on for the next Jam

    # The die rolls once with a new seed, every setting kept; the pass says so, and its card gives its seed.
    with page.expect_request(lambda r: r.url.endswith("/api/jam/roll") and r.method == "POST") as sent:
        page.click('[data-jam-act="roll-new-seed"]')
    assert "seed" not in sent.value.post_data_json
    page.wait_for_function("document.querySelectorAll('.jam-hist-card:not(.is-seed)').length >= 2", timeout=30000)
    assert "New seed" in page.locator(".jam-hist-card:not(.is-seed)").last.inner_text()

    # Editor on a pass: the editor opens on it, Esc comes back to the Jam as it was; making a take there makes a new
    # take in the Jam's space and comes back too, the pass left as it was.
    page.click(f'.jam-hist-card[data-pass-id="{pass_id}"] [data-jam-act="pass-editor"]')
    page.wait_for_selector('#editor-modal:not(.hidden)')
    assert page.locator('#jam-modal').is_hidden()
    assert page.input_value('#max-duration') == ''
    page.keyboard.press("Escape")
    page.wait_for_selector('#jam-modal:not(.hidden) .jam-hist-card.is-seed')
    assert page.locator(f'.jam-hist-card[data-pass-id="{pass_id}"]').count() == 1
    pass_before = api(app_server, f"/api/takes/{pass_id}")
    page.click(f'.jam-hist-card[data-pass-id="{pass_id}"] [data-jam-act="pass-editor"]')
    page.wait_for_selector('#editor-modal:not(.hidden)')
    with page.expect_response(lambda r: r.url.endswith(f"/api/takes/{pass_id}/render") and r.request.method == "POST") as sent:
        page.evaluate("renderInPlace()")
    new_id = sent.value.json()["id"]
    assert new_id != pass_id
    page.wait_for_selector('#jam-modal:not(.hidden) .jam-hist-card.is-seed')
    assert api(app_server, f"/api/takes/{new_id}")["space_id"] == made["space_id"]
    pass_after = api(app_server, f"/api/takes/{pass_id}")
    assert pass_after["space_id"] == "__jam__" and pass_after["abc"] == pass_before["abc"]
    # Back in Jam, the engine's work outside it shows in Jam's top bar, as the page's top bar shows it.
    page.evaluate("""() => { State.currentJob = { id: 'elsewhere', kind: 'render', title: 'Another take', stage: 'Rendering audio',
        elapsed: 3, progress: 0.4 }; paintJob(State.currentJob, [], State.options || {}); }""")
    page.wait_for_selector('#jam-topbar #jam-job:not(.hidden)')
    assert "Another take" in page.locator('#jam-job').inner_text()
    page.evaluate("() => { State.currentJob = null; paintJob(null, [], State.options || {}); }")
    page.wait_for_selector('#jam-job', state='hidden')

    # Write lyrics is offered in Jam's lyrics popup, and its window says new words need Plan & Roll.
    page.click('[data-jam-act="edit-lyrics"]')
    page.wait_for_selector('#lyrics-modal:not(.hidden) #lyrics-modal-write:not(.hidden)')
    page.click('#lyrics-modal-write')
    page.wait_for_selector('#write-modal:not(.hidden) #write-caution:not(.hidden)')
    assert "Plan & Roll" in page.locator('#write-caution').inner_text()
    page.click('#write-close')
    page.click('#lyrics-close')

    # Esc closes it.
    page.locator(".jam-col-head h4").first.click()
    page.keyboard.press("Escape")
    page.wait_for_selector("#jam-modal", state="hidden")


def test_a_full_song_asks_first(page, app_server):
    made = make_song(page, app_server, style="synthwave, analog synth, female vocal")
    open_jam(page, made["id"])
    page.click('[data-jam-act="scope-full"]')
    page.click('[data-jam-act="roll"]')
    page.wait_for_selector("#confirm-modal:not(.hidden)")
    page.click("#confirm-cancel")
    page.wait_for_selector("#confirm-modal", state="hidden")
    assert page.locator(".jam-hist-card:not(.is-seed)").count() == 0
    # Its name is ready to change, and the name typed is the take's.
    page.click('[data-jam-act="roll"]')
    page.wait_for_selector("#confirm-input:not(.hidden)")
    assert "(Jam #1)" in page.input_value("#confirm-input")
    page.fill("#confirm-input", "Night drive")
    with page.expect_request(lambda r: r.url.endswith("/api/jam/roll") and r.method == "POST") as sent:
        page.click("#confirm-ok")
    assert sent.value.post_data_json["title"] == "Night drive"


def test_a_jam_starts_at_the_seeds_tempo(page, app_server):
    # A score's tempo line, with no tempo locked, sets where the Tempo control starts: a fast one too (#80).
    made = make_song(page, app_server, style="punk, distorted guitars, male vocal")
    card(page, made["id"]).wait_for()
    page.evaluate("""(id) => { var take = Object.assign({}, takeById(id), { target_bpm: null });
                              take.abc = take.abc.replace(/^Q:.*$/m, 'Q:1/4=185'); Jam.openFromTake(take); }""", made["id"])
    page.wait_for_selector("#jam-modal:not(.hidden) .jam-hist-card.is-seed")
    assert page.input_value("#jam-bpm-slider") == "185"
    assert "185 BPM" in page.locator("#jam-bpm-val").inner_text()


def test_jam_lyrics_edit_per_pass_and_reset(page, app_server):
    made = make_song(page, app_server, style="indie folk, acoustic guitar, female vocal")
    seed_lyrics = api(app_server, f"/api/takes/{made['id']}")["lyrics"]
    open_jam(page, made["id"])

    # Open the Lyrics popup from the Vocals row and edit the words.
    page.click('[data-jam-act="edit-lyrics"]')
    page.wait_for_selector("#lyrics-modal:not(.hidden)")
    assert page.input_value("#lyrics-big") == seed_lyrics
    assert page.locator("#lyrics-reset").is_disabled()
    edited = "[Verse]\nNew words along the harbour wall\nShining through the evening mist"
    page.fill("#lyrics-big", edited)
    assert not page.locator("#lyrics-reset").is_disabled()
    page.click("#lyrics-close")
    page.wait_for_selector("#lyrics-modal", state="hidden")
    # Jam stays open, Lyrics button shows edited state, and Roll counts the change.
    assert page.locator("#jam-modal:not(.hidden)").count() == 1
    assert page.locator(".jam-lyrics-btn.edited").count() == 1
    assert page.locator(".jam-pending-badge").inner_text().startswith("1")

    # Roll Pass #1 and confirm the edited lyrics were sent while the Seed kept its own.
    with page.expect_request(lambda r: r.url.endswith("/api/jam/roll") and r.method == "POST") as sent:
        page.click('[data-jam-act="roll"]')
    assert sent.value.post_data_json["lyrics"] == edited
    page.wait_for_selector(".jam-hist-card:not(.is-seed)")
    pass_id = page.evaluate("() => JSON.parse(localStorage.getItem('yue2.jam.sessions'))['take:' + "
                            f"'{made['id']}'].passes.filter(p => !p.isSeed)[0].id")
    wait_take(app_server, pass_id)
    page.wait_for_selector(f'.jam-hist-card.selectable[data-pass-id="{pass_id}"]', timeout=30000)
    assert api(app_server, f"/api/takes/{made['id']}")["lyrics"] == seed_lyrics
    assert api(app_server, f"/api/takes/{pass_id}")["lyrics"] == edited
    assert "Lyrics edited" in page.locator(f'.jam-hist-card[data-pass-id="{pass_id}"] .jam-hist-diffs').inner_text()

    # Clicking back to Seed restores the Seed's lyrics; clicking Pass #1 restores Pass #1's lyrics.
    page.click(".jam-hist-card.is-seed .jam-hist-name")
    page.wait_for_selector(".jam-hist-card.is-seed.is-base")
    assert page.locator(".jam-lyrics-btn.edited").count() == 0
    page.click('[data-jam-act="edit-lyrics"]')
    page.wait_for_selector("#lyrics-modal:not(.hidden)")
    assert page.input_value("#lyrics-big") == seed_lyrics
    page.click("#lyrics-close")

    page.click(f'.jam-hist-card[data-pass-id="{pass_id}"] .jam-hist-name')
    page.wait_for_selector(f'.jam-hist-card.is-base[data-pass-id="{pass_id}"]')
    assert page.locator(".jam-lyrics-btn.edited").count() == 1
    page.click('[data-jam-act="edit-lyrics"]')
    page.wait_for_selector("#lyrics-modal:not(.hidden)")
    assert page.input_value("#lyrics-big") == edited
    # Reset to Seed inside the popup restores the Seed's original lyrics; Write lyrics is offered in Jam too.
    assert page.locator("#lyrics-modal-write").is_visible()
    assert page.locator("#lyrics-jam-hint").is_visible()
    page.click("#lyrics-reset")
    assert page.input_value("#lyrics-big") == seed_lyrics
    assert page.locator("#lyrics-reset").is_disabled()
    page.click("#lyrics-close")
    assert page.locator(".jam-lyrics-btn.edited").count() == 0

    # Reopening Lyrics immediately keeps the reset Seed lyrics; navigating back to Pass #1 restores Pass #1's snapshot.
    page.click('[data-jam-act="edit-lyrics"]')
    page.wait_for_selector("#lyrics-modal:not(.hidden)")
    assert page.input_value("#lyrics-big") == seed_lyrics
    page.click("#lyrics-close")
    page.click(".jam-hist-card.is-seed .jam-hist-name")
    page.click(f'.jam-hist-card[data-pass-id="{pass_id}"] .jam-hist-name')
    page.wait_for_selector(f'.jam-hist-card.is-base[data-pass-id="{pass_id}"]')
    assert page.locator(".jam-lyrics-btn.edited").count() == 1


def test_jam_tracks_renamed_and_moved_seed(page, app_server):
    # Reopening a saved Jam after renaming or moving its Seed picks up the current title and space.
    made = make_song(page, app_server, style="indie pop, jangly guitar, female vocal")
    open_jam(page, made["id"])
    page.locator(".jam-col-head h4").first.click()
    page.keyboard.press("Escape")
    page.wait_for_selector("#jam-modal", state="hidden")

    # Rename the Seed and move it to a new space via the API, then reload so Jam loads from localStorage.
    new_space = page.evaluate("""async (id) => {
        const sp = await api('/api/spaces', { method: 'POST', body: JSON.stringify({ name: 'Harbour Sessions' }) });
        await api('/api/takes/' + encodeURIComponent(id) + '/rename', {
            method: 'POST', body: JSON.stringify({ title: 'Harbour Lights' })
        });
        await api('/api/takes/' + encodeURIComponent(id) + '/move', {
            method: 'POST', body: JSON.stringify({ space_id: sp.id })
        });
        return sp;
    }""", made["id"])
    page.reload()
    page.wait_for_selector("#space-pick")
    page.click("#space-pick")
    page.locator("#space-list .space-row", has_text="Harbour Sessions").first.click()
    page.wait_for_function("() => document.getElementById('takes-heading').textContent === 'Harbour Sessions'")

    open_jam(page, made["id"])
    assert page.locator(".jam-seed-name").inner_text().strip() == "Harbour Lights"
    page.click('[data-jam-act="scope-full"]')
    page.click('[data-jam-act="roll"]')
    page.wait_for_selector("#confirm-input:not(.hidden)")
    assert page.input_value("#confirm-input") == "Harbour Lights (Jam #1)"
    with page.expect_request(lambda r: r.url.endswith("/api/jam/roll") and r.method == "POST") as sent:
        page.click("#confirm-ok")
    body = sent.value.post_data_json
    assert body["title"] == "Harbour Lights (Jam #1)"
    assert body["space_id"] == new_space["id"]
