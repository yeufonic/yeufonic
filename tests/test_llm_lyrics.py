"""Hearing a recording's lyrics with an external LLM, and Whisper keeping the time.

Whisper's mistakes on a sung vocal are mostly lines it misses, which a model that
hears the audio can fill.  These pin how the two are combined and every way back to
Whisper.
"""
import asyncio
import time
from pathlib import Path

import pytest

from app import identities, jobs, llm
from app.db import execute, one, set_setting

WHISPER = [
    {"start": 10.0, "end": 14.0, "text": "I left the porch light on for you"},
    # "Counting cars along the bridge" is sung here, and Whisper misses it.
    {"start": 30.0, "end": 33.0, "text": "Paper boat"},
]
HEARD = ["I left the porch light on for you", "Counting cars along the bridge", "Paper boat"]


def test_matched_lines_take_whispers_times():
    timed = identities.time_lines(WHISPER, HEARD)
    assert timed[0]["text"] == "I left the porch light on for you"
    assert 10.0 <= timed[0]["start"] <= timed[0]["end"] <= 14.0
    assert 30.0 <= timed[2]["start"] <= 33.0


def test_a_line_whisper_missed_is_placed_between_its_neighbours():
    """The whole point: the lines an LLM recovers are the ones with no time."""
    timed = identities.time_lines(WHISPER, HEARD)
    missed = timed[1]
    assert missed["text"] == "Counting cars along the bridge"
    assert timed[0]["end"] < missed["start"] < timed[2]["start"]


def test_words_that_are_not_this_recording_are_refused():
    """A famous song written out from memory barely matches what was sung."""
    other = ["The morning light came over the hill", "And all the day was warm and still"]
    assert identities.time_lines(WHISPER, other) is None


def test_the_reply_loses_labels_fences_and_markup():
    reply = "```\n[Verse]\n**I left the porch light on**\nPaper boat\n(instrumental)\n\n```"
    assert llm._hear_lines(reply) == ["I left the porch light on", "Paper boat"]


# ------------------------------------------------------------ choosing a method

@pytest.fixture
def whisper(monkeypatch):
    monkeypatch.setattr(identities, "transcribe", lambda vocal, on_progress=None, duration=0.0, should_stop=None: list(WHISPER))


def hear():
    return asyncio.run(jobs.hear(Path("/nowhere/vocals.wav"), 40.0, title="Harbour Wind"))


def refuse(*args, **kwargs):
    raise AssertionError("the LLM should not have been asked")


def external(model="gemini-3.8-flash", url="https://generativelanguage.googleapis.com"):
    set_setting("llm.provider", "external")
    set_setting("llm.model", model)
    set_setting("llm.api_url", url)


def test_whisper_is_the_default(whisper, monkeypatch):
    monkeypatch.setattr(llm, "hear_lyrics", refuse)
    external()
    lines, method = hear()
    assert method == "Whisper" and lines == WHISPER


def test_the_setting_does_nothing_without_an_external_provider(whisper, monkeypatch):
    monkeypatch.setattr(llm, "hear_lyrics", refuse)
    set_setting("llm.provider", "local")
    set_setting("lyrics.transcriber", "llm")
    assert hear()[1] == "Whisper"


def test_the_llm_hears_and_whisper_times(whisper, monkeypatch):
    async def heard(vocal):
        return list(HEARD)
    monkeypatch.setattr(llm, "hear_lyrics", heard)
    external()
    set_setting("lyrics.transcriber", "llm")
    lines, method = hear()
    assert [l["text"] for l in lines] == HEARD
    assert method == "gemini-3.8-flash, timed by Whisper"


def test_a_model_that_cannot_take_audio_falls_back_and_says_why(whisper, monkeypatch):
    async def fails(vocal):
        raise RuntimeError("External LLM HTTP 400: audio input is not supported")
    monkeypatch.setattr(llm, "hear_lyrics", fails)
    external("gpt-4o-mini", "https://api.openai.com/v1")
    set_setting("lyrics.transcriber", "llm")
    lines, method = hear()
    assert lines == WHISPER
    assert method.startswith("Whisper (gpt-4o-mini could not take the audio")
    assert "not supported" in method


def test_words_that_do_not_match_whisper_still_win_and_are_spread_over_the_song(whisper, monkeypatch):
    """Whisper can miss a vocal buried in a mix.  A reply that looks like lyrics is kept even when
    nothing in it matches what Whisper heard: it has no times to borrow, so it is laid out between
    the first and last line Whisper found."""
    other = ["The morning light came over the hill", "And all the day was warm and still",
             "Oh I remember the morning"]

    async def heard(vocal):
        return list(other)
    monkeypatch.setattr(llm, "hear_lyrics", heard)
    external()
    set_setting("lyrics.transcriber", "llm")
    lines, method = hear()
    assert [l["text"] for l in lines] == other
    assert method == "gemini-3.8-flash, spread over the song (its words differ from Whisper's)"
    assert lines[0]["start"] == WHISPER[0]["start"] and lines[-1]["end"] <= WHISPER[-1]["end"] + 0.01
    assert all(a["end"] <= b["start"] + 0.01 for a, b in zip(lines, lines[1:]))        # in order


# ---------------------------------------------------------- the setting and the API

def test_the_setting_needs_an_external_provider(client):
    spec = {item["key"]: item for item in client.get("/api/settings").json()["settings"]}
    item = spec["lyrics.transcriber"]
    assert item["value"] == "whisper"
    assert item["requires"] == {"llm.provider": "external"}
    assert item["requires_note"]


def test_the_setting_takes_only_its_own_values(client):
    assert client.put("/api/settings", json={"key": "lyrics.transcriber", "value": "llm"}).status_code == 200
    assert client.put("/api/settings", json={"key": "lyrics.transcriber", "value": "gemini"}).status_code == 400


def test_the_lyrics_endpoint_says_who_heard_them(client):
    execute("""INSERT INTO sources (id, title, filename, stored_path, sha256, created_at, lyrics,
               lyrics_state, lyrics_method) VALUES ('s1', 'Paper Boat', 'mg.flac', '/data/mg.flac',
               '0', ?, '[Verse]\nPaper boat', 'done', 'gemini-3.8-flash, timed by Whisper')""", (time.time(),))
    got = client.get("/api/sources/s1/lyrics").json()
    assert got["method"] == "gemini-3.8-flash, timed by Whisper"


# ------------------------------------------------------------ what the log says

def first_line(caplog):
    return next(r.getMessage() for r in caplog.records if r.getMessage().startswith("Lyrics for"))


def test_the_log_says_up_front_when_the_llm_will_listen(whisper, monkeypatch, caplog):
    """Whisper's own lines appear either way, so the method is stated before them."""
    async def heard(vocal):
        return list(HEARD)
    monkeypatch.setattr(llm, "hear_lyrics", heard)
    external()
    set_setting("lyrics.transcriber", "llm")
    caplog.set_level("INFO")
    hear()
    assert first_line(caplog) == ("Lyrics for 'Harbour Wind': the external LLM (gemini-3.8-flash) "
                                  "will hear the words; Whisper runs first to time the lines")
    said = " ".join(r.getMessage() for r in caplog.records)
    assert "sending the vocal to gemini-3.8-flash" in said
    assert "gemini-3.8-flash heard 3 lines, where Whisper heard 2" in said


def test_the_log_says_when_whisper_is_the_setting(whisper, monkeypatch, caplog):
    monkeypatch.setattr(llm, "hear_lyrics", refuse)
    external()
    caplog.set_level("INFO")
    hear()
    assert first_line(caplog) == "Lyrics for 'Harbour Wind': Whisper, as set in Settings"


def test_the_log_says_why_the_llm_setting_was_not_used(whisper, monkeypatch, caplog):
    monkeypatch.setattr(llm, "hear_lyrics", refuse)
    set_setting("llm.provider", "local")
    set_setting("lyrics.transcriber", "llm")
    caplog.set_level("INFO")
    hear()
    assert "provider is not External LLM" in first_line(caplog)


# ------------------------------------------------- a reply that is not the whole song

def test_a_trailing_line_is_not_a_held_back_reply():
    assert llm.held_back(["Hold on…", "Paper boat"]) is None


def test_lines_cut_short_are_held_back():
    """What the Gemini app did with a well-known song: every section cut to "..."."""
    assert llm.held_back(["You'd think that people would've had enough...", "I love you..."]) == "cut lines short"


def test_a_notice_about_lyrics_is_held_back():
    note = ("You can view the complete, licensed lyrics by searching for the song on Google "
            "or visiting major lyric databases like Genius or LyricFind.")
    assert llm.held_back(["I love you", note]) == "wrote a notice instead of the full lyrics"
    assert llm.held_back(["I cannot provide the lyrics to this song"]) is not None


def test_sung_words_that_look_like_a_notice_are_not():
    assert llm.held_back(["Love is a genius thing", "Complete me, baby",
                          "I wrote you the lyrics of my heart", "Search your soul"]) is None


def test_a_held_back_reply_falls_back_and_says_why(whisper, monkeypatch):
    """The agreement check would pass it: every word it does give is in the song."""
    async def cut(vocal):
        return ["I left the porch light on...", "Paper boat..."]
    monkeypatch.setattr(llm, "hear_lyrics", cut)
    external()
    set_setting("lyrics.transcriber", "llm")
    lines, method = hear()
    assert lines == WHISPER
    assert method == "Whisper (gemini-3.8-flash cut lines short)"


def test_a_reply_that_is_almost_nothing_falls_back_but_fewer_words_than_whisper_do_not(whisper, monkeypatch):
    """Looking like lyrics is what counts, not matching Whisper's count: Whisper can inflate its own
    (a held "la" written a hundred times), and an LLM's shorter, right words must not lose to it."""
    async def short(vocal):
        return ["Paper boat"]
    monkeypatch.setattr(llm, "hear_lyrics", short)
    external()
    set_setting("lyrics.transcriber", "llm")
    lines, method = hear()
    assert lines == WHISPER and method == "Whisper (gemini-3.8-flash returned only 2 words)"

    async def fewer(vocal):                     # 12 words against Whisper's 10 + a long vocalise
        return ["I left the porch light on for you", "Counting cars along the bridge now"]
    monkeypatch.setattr(identities, "transcribe", lambda vocal, on_progress=None, duration=0.0, should_stop=None:
                        WHISPER + [{"start": 40.0, "end": 70.0, "text": "la " * 40}])
    monkeypatch.setattr(llm, "hear_lyrics", fewer)
    lines, method = hear()
    assert [l["text"] for l in lines] == ["I left the porch light on for you", "Counting cars along the bridge now"]
    assert method.startswith("gemini-3.8-flash")


def test_both_versions_come_back_and_the_models_is_the_one_in_use(whisper, monkeypatch):
    async def heard(vocal):
        return list(HEARD)
    monkeypatch.setattr(llm, "hear_lyrics", heard)
    external()
    set_setting("lyrics.transcriber", "llm")
    found = asyncio.run(jobs.hear_all(Path("/nowhere/vocals.wav"), 40.0, title="x"))
    assert found["whisper"] == WHISPER and [l["text"] for l in found["llm"]] == HEARD
    assert found["lines"] == found["llm"] and found["model"] == "gemini-3.8-flash"
    # Whisper alone: the other version is None.
    set_setting("lyrics.transcriber", "whisper")
    alone = asyncio.run(jobs.hear_all(Path("/nowhere/vocals.wav"), 40.0, title="x"))
    assert alone["llm"] is None and alone["lines"] == WHISPER


def test_a_long_run_of_one_syllable_from_whisper_is_cut_and_the_llms_is_not():
    assert identities.collapse_runs("La " * 237) == " ".join(["La"] * identities.MAX_REPEAT)
    assert identities.collapse_runs("la, La. la! LA la la la la la la la") == "la, La. la! LA la la la la"      # eight kept
    assert identities.collapse_runs("go go go and go go") == "go go go and go go"                        # short runs stay
    assert identities.collapse_runs("") == ""


def test_lines_with_no_times_are_spread_by_their_words():
    out = identities.spread_lines(["one two", "three four five six"], 10.0, 22.0)
    assert [(l["start"], l["end"]) for l in out] == [(10.0, 14.0), (14.0, 22.0)]          # a third and two thirds of 12 s
    assert [l["text"] for l in out] == ["one two", "three four five six"]
