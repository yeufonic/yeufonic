"""A corpus whose Voice is "none": no vocal separation, no Whisper, section tags for lyrics."""
import asyncio
import json

from app import identities, jobs, llm
from app.db import execute, one

ABC = """X:1
T:x
M:4/4
L:1/8
Q:1/4=174
K:Am
%section: intro
V:Vocal
z8|z8|z8|z8|
"""


def corpus(tmp_path, voice="none", score=True):
    folder = tmp_path / "song"
    folder.mkdir()
    (folder / "original.flac").write_bytes(b"x")
    if score:
        (folder / "score.abc").write_text(ABC, encoding="utf-8")
    execute("INSERT INTO identities(id, name, trigger_word, folder, consent, created_at, voice, description) VALUES('c1', 'Band', 'b', '/x', 1, 0, ?, 'jungle')", (voice,))
    execute("""INSERT INTO identity_songs(id, identity_id, file, title, sha256, duration, include, position, stored_path,
                                          vocals_state, score_state, lyrics_state, style_state)
               VALUES('s1', 'c1', 'a.flac', 'A', 'h', 200, 1, 0, ?, 'none', ?, 'none', 'none')""",
            (str(folder / "original.flac"), "done" if score else "none"))
    return folder


def test_the_caption_leaves_out_the_vocal_clause():
    assert identities.caption("b", "jungle", "none", "A minor", 174) == "b, jungle, key of A minor, 174 BPM"
    assert "male vocal" in identities.caption("b", "jungle", "male", None, None)


def test_lyrics_are_the_scores_section_tags_without_hearing_anything(tmp_path, monkeypatch):
    monkeypatch.setattr(identities, "score_sections", lambda abc: [("intro", 8), ("verse", 16)])
    folder = corpus(tmp_path)
    jobs.maybe_draft("s1")                                  # no whisper.json, and none is wanted
    song = one("SELECT * FROM identity_songs WHERE id = 's1'")
    assert song["lyrics"] == "[Intro]\n\n[Verse]" and song["lyrics_state"] == "done" and song["lyrics_checked"] == 1
    assert not (folder / "whisper.json").exists()


def test_without_a_score_the_lyrics_are_instrumental(tmp_path, monkeypatch):
    monkeypatch.setattr(identities, "score_sections", lambda abc: [])
    corpus(tmp_path)
    jobs.maybe_draft("s1")
    assert one("SELECT lyrics FROM identity_songs WHERE id = 's1'")["lyrics"] == "[instrumental]"


def test_tags_edited_by_hand_survive_another_analysis(tmp_path, monkeypatch):
    monkeypatch.setattr(identities, "score_sections", lambda abc: [("intro", 8)])
    corpus(tmp_path)
    execute("UPDATE identity_songs SET lyrics = '[Drop]', lyrics_checked = 1 WHERE id = 's1'")
    jobs.maybe_draft("s1")
    assert one("SELECT lyrics FROM identity_songs WHERE id = 's1'")["lyrics"] == "[Drop]"


def test_preparing_a_song_skips_the_vocal_and_whisper(tmp_path, monkeypatch):
    src = tmp_path / "in"
    src.mkdir()
    (src / "a.flac").write_bytes(b"x")
    monkeypatch.setattr(identities, "allowed", lambda p: True)
    corpus(tmp_path)
    execute("UPDATE identities SET folder = ? WHERE id = 'c1'", (str(src),))
    execute("UPDATE identity_songs SET vocals_state = 'queued', lyrics_state = 'queued', score_state = 'done' WHERE id = 's1'")
    monkeypatch.setattr(identities, "song_dir", lambda identity_id, song: tmp_path / "song")
    monkeypatch.setattr(identities, "score_sections", lambda abc: [("intro", 8)])
    monkeypatch.setattr(jobs, "_store_original", lambda a, b: None)
    called = []

    async def forbidden(*a, **k):
        called.append(1)

    monkeypatch.setattr(jobs, "separate_stems", forbidden)
    monkeypatch.setattr(jobs, "hear_all", forbidden)
    asyncio.run(jobs.prepare_song("s1"))
    song = one("SELECT * FROM identity_songs WHERE id = 's1'")
    assert not called and song["vocals_state"] == "done" and song["lyrics_state"] == "done" and song["style_state"] == "queued"


def test_the_view_says_so_and_the_export_does_not_nag_about_unchecked_lyrics(client, tmp_path):
    corpus(tmp_path)
    view = client.get("/api/identities/c1").json()
    assert view["vocalless"] is True
    assert view["songs"][0]["caption"] == "b, jungle"


def test_changing_the_voice_to_none_turns_the_lyrics_into_tags_and_back_asks_for_hearing(client, tmp_path, monkeypatch):
    monkeypatch.setattr(identities, "score_sections", lambda abc: [("intro", 8)])
    monkeypatch.setattr(llm, "is_external_enabled", lambda: False)
    folder = corpus(tmp_path, voice="male")
    (folder / "whisper.json").write_text(json.dumps([{"start": 1, "end": 2, "text": "la la"}]), encoding="utf-8")
    execute("UPDATE identity_songs SET lyrics = '[Verse]\nla la', lyrics_checked = 1, lyrics_state = 'done', vocals_state = 'done' WHERE id = 's1'")
    assert client.put("/api/identities/c1", json={"voice": "none"}).json()["vocalless"] is True
    song = one("SELECT * FROM identity_songs WHERE id = 's1'")
    assert song["lyrics"] == "[Intro]" and song["lyrics_checked"] == 1
    (folder / "whisper.json").unlink()
    client.put("/api/identities/c1", json={"voice": "female"})
    song = one("SELECT * FROM identity_songs WHERE id = 's1'")
    assert song["lyrics"] == "" and song["lyrics_state"] == "none" and song["vocals_state"] == "none"
