"""A corpus song keeps both versions of its words, and which is in use can be switched."""
import json

from app import jobs, llm
from app.db import execute, one

WHISPER = [{"start": 5.0, "end": 8.0, "text": "fire eating the larder"}, {"start": 9.0, "end": 12.0, "text": "la la la la"}]
MODEL = [{"start": 5.0, "end": 8.0, "text": "the fiery tangle in the order"}, {"start": 9.0, "end": 12.0, "text": "na na na na"}]


def a_song(tmp_path):
    folder = tmp_path / "song"
    folder.mkdir()
    (folder / "original.flac").write_bytes(b"x")
    execute("INSERT INTO identities(id, name, trigger_word, folder, consent, created_at) VALUES('c1', 'Band', 'b', '/x', 1, 0)")
    execute("""INSERT INTO identity_songs(id, identity_id, file, title, sha256, duration, include, position, stored_path,
                                          vocals_state, score_state, lyrics_state, style_state)
               VALUES('s1', 'c1', 'a.flac', 'A', 'h', 30, 1, 0, ?, 'done', 'done', 'done', 'done')""", (str(folder / "original.flac"),))
    return folder


def test_both_versions_are_kept_with_the_models_in_use(tmp_path):
    folder = a_song(tmp_path)
    found = {"lines": MODEL, "method": "gemini, timed by Whisper", "whisper": WHISPER, "llm": MODEL, "model": "gemini-3.8-flash"}
    jobs.keep_lyric_versions("s1", folder, found)
    assert json.loads((folder / "lyrics-whisper.json").read_text()) == WHISPER
    assert json.loads((folder / "lyrics-llm.json").read_text()) == MODEL
    versions = json.loads(one("SELECT lyrics_versions FROM identity_songs WHERE id = 's1'")["lyrics_versions"])
    assert versions == {"active": "llm", "whisper": {"words": 8}, "llm": {"model": "gemini-3.8-flash", "words": 10}}
    # Whisper alone keeps one file, removes any old LLM file, and says it is the one in use.
    jobs.keep_lyric_versions("s1", folder, {"lines": WHISPER, "whisper": WHISPER, "llm": None, "model": "x"})
    assert not (folder / "lyrics-llm.json").exists()
    assert json.loads(one("SELECT lyrics_versions FROM identity_songs WHERE id = 's1'")["lyrics_versions"]) == {
        "active": "whisper", "whisper": {"words": 8}}


def test_the_song_in_the_corpus_view_carries_its_versions(client, tmp_path):
    folder = a_song(tmp_path)
    jobs.keep_lyric_versions("s1", folder, {"lines": MODEL, "whisper": WHISPER, "llm": MODEL, "model": "gemini-3.8-flash"})
    song = client.get("/api/identities/c1").json()["songs"][0]
    assert song["lyrics_versions"]["active"] == "llm" and song["lyrics_versions"]["llm"]["words"] == 10


def test_switching_puts_the_other_version_in_use_and_drafts_its_words(client, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "is_external_enabled", lambda: False)
    folder = a_song(tmp_path)
    (folder / "whisper.json").write_text(json.dumps(MODEL))
    jobs.keep_lyric_versions("s1", folder, {"lines": MODEL, "whisper": WHISPER, "llm": MODEL, "model": "gemini-3.8-flash"})
    execute("UPDATE identity_songs SET lyrics = 'my own words', lyrics_checked = 1 WHERE id = 's1'")
    url = "/api/identities/c1/songs/s1/lyrics/source"
    reply = client.post(url, json={"source": "whisper"})
    assert reply.status_code == 200 and reply.json()["active"] == "whisper" and reply.json()["restored"] is False
    row = one("SELECT lyrics, lyrics_checked, lyrics_versions FROM identity_songs WHERE id = 's1'")
    assert "fire eating the larder" in row["lyrics"] and "fiery tangle" not in row["lyrics"] and row["lyrics_checked"] == 0
    assert json.loads(row["lyrics_versions"])["active"] == "whisper"
    assert json.loads((folder / "whisper.json").read_text()) == WHISPER          # the lines in use
    # Back to the other: the words that were in the box when it was left, with its tick, and no new draft.
    back = client.post(url, json={"source": "llm"})
    assert back.status_code == 200 and back.json()["restored"] is True and back.json()["lyrics"] == "my own words"
    row = one("SELECT lyrics, lyrics_checked FROM identity_songs WHERE id = 's1'")
    assert row["lyrics"] == "my own words" and row["lyrics_checked"] == 1


def test_switching_says_why_it_cannot(client, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "is_external_enabled", lambda: False)
    folder = a_song(tmp_path)
    jobs.keep_lyric_versions("s1", folder, {"lines": WHISPER, "whisper": WHISPER, "llm": None, "model": "x"})
    url = "/api/identities/c1/songs/s1/lyrics/source"
    assert client.post(url, json={"source": "llm"}).status_code == 400            # that version was not kept
    assert client.post(url, json={"source": "gemini"}).status_code == 422
    assert client.post("/api/identities/c1/songs/nope/lyrics/source", json={"source": "whisper"}).status_code == 404
    execute("UPDATE identity_songs SET lyrics_state = 'running' WHERE id = 's1'")
    assert client.post(url, json={"source": "whisper"}).status_code == 409
    execute("UPDATE identity_songs SET stored_path = NULL, lyrics_state = 'done' WHERE id = 's1'")
    assert client.post(url, json={"source": "whisper"}).status_code == 400


def test_recording_made_from_corpus_song_names_the_active_model(tmp_path):
    from app import main
    folder = a_song(tmp_path)
    (folder / "whisper.json").write_text(json.dumps(MODEL))
    jobs.keep_lyric_versions("s1", folder, {"lines": MODEL, "whisper": WHISPER, "llm": MODEL, "model": "gemini-3.8-flash"})
    song = one("SELECT * FROM identity_songs WHERE id = 's1'")
    text, method = main._corpus_song_lyrics(song, folder, "X:1\nK:C\n", 30.0)
    assert method == "gemini-3.8-flash, in the corpus analysis"



def test_a_version_is_drafted_once_and_then_swapped_back_without_drafting(client, tmp_path, monkeypatch):
    """Drafting marks the sections with the external model: once per version, not once per click."""
    monkeypatch.setattr(llm, "is_external_enabled", lambda: False)
    folder = a_song(tmp_path)
    (folder / "whisper.json").write_text(json.dumps(MODEL))
    jobs.keep_lyric_versions("s1", folder, {"lines": MODEL, "whisper": WHISPER, "llm": MODEL, "model": "gemini-3.8-flash"})
    jobs.maybe_draft("s1")                                   # the analysis drafts the version in use
    first = one("SELECT lyrics FROM identity_songs WHERE id = 's1'")["lyrics"]
    assert "fiery tangle" in first and jobs.remembered_words(one("SELECT * FROM identity_songs WHERE id = 's1'"), "llm") == first
    drafts = []
    real = jobs.maybe_draft
    monkeypatch.setattr(jobs, "maybe_draft", lambda song_id: (drafts.append(song_id), real(song_id))[1])
    url = "/api/identities/c1/songs/s1/lyrics/source"
    assert client.post(url, json={"source": "whisper"}).json()["restored"] is False        # never drafted: drafts
    second = one("SELECT lyrics FROM identity_songs WHERE id = 's1'")["lyrics"]
    assert "fire eating the larder" in second and len(drafts) == 1
    for source, words in (("llm", first), ("whisper", second), ("llm", first)):
        reply = client.post(url, json={"source": source})
        assert reply.json()["restored"] is True and reply.json()["lyrics"] == words
        assert one("SELECT lyrics FROM identity_songs WHERE id = 's1'")["lyrics"] == words
    assert len(drafts) == 1, "no further drafting, so no further calls to the model"
    assert json.loads((folder / "whisper.json").read_text()) == MODEL                      # the lines follow the version


def test_edits_and_the_checked_tick_stay_with_their_version(client, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "is_external_enabled", lambda: False)
    folder = a_song(tmp_path)
    (folder / "whisper.json").write_text(json.dumps(MODEL))
    jobs.keep_lyric_versions("s1", folder, {"lines": MODEL, "whisper": WHISPER, "llm": MODEL, "model": "gemini-3.8-flash"})
    jobs.maybe_draft("s1")
    url = "/api/identities/c1/songs/s1/lyrics/source"
    assert client.put("/api/identities/c1/songs/s1", json={"lyrics": "[Verse]\nmy edit", "lyrics_checked": True}).status_code == 200
    assert client.post(url, json={"source": "whisper"}).status_code == 200
    assert one("SELECT lyrics_checked FROM identity_songs WHERE id = 's1'")["lyrics_checked"] == 0
    back = client.post(url, json={"source": "llm"}).json()
    assert back["lyrics"] == "[Verse]\nmy edit" and back["checked"] is True


def test_a_song_analysed_before_words_were_kept_still_remembers_what_it_leaves(client, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "is_external_enabled", lambda: False)
    folder = a_song(tmp_path)
    jobs.keep_lyric_versions("s1", folder, {"lines": MODEL, "whisper": WHISPER, "llm": MODEL, "model": "gemini-3.8-flash"})
    execute("UPDATE identity_songs SET lyrics = 'drafted long ago' WHERE id = 's1'")          # no text file for it
    url = "/api/identities/c1/songs/s1/lyrics/source"
    assert client.post(url, json={"source": "whisper"}).json()["restored"] is False
    assert client.post(url, json={"source": "llm"}).json()["lyrics"] == "drafted long ago"
