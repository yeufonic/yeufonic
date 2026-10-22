"""A tune played on an instrument (a guitar into the recorder) as the sung tune of a song."""
from pathlib import Path

from app import composer, voices
from app.db import execute, one

from tests.test_recorder import _generate_wav_bytes

# A guitar line as the transcriber can write it: low on the neck, in Ins, the Vocal voice resting.
GUITAR = """X:1
T:
M:4/4
L:1/8
Q:1/4=96
K:G
V: Vocal
Z2|
V: Ins
G,,2B,,2D,2G,2|^F,2E,2D,4|
"""


def _mean(abc: str) -> float:
    notes = voices.read(abc)["notes"]
    return sum(n["pitch"] * n["length"] for n in notes) / sum(n["length"] for n in notes)


def _instrument_source(sid="gtr1", abc=GUITAR):
    execute("""INSERT INTO sources(id, title, filename, stored_path, sha256, created_at, abc, transcribe_state,
                                   origin, instrument)
               VALUES(?, 'Riff', 'melody.wav', '/tmp/melody.wav', ?, 1000.0, ?, 'done', 'recording', 1)""",
            (sid, sid, abc))
    return sid


def test_the_tune_is_moved_by_octaves_to_where_the_chosen_voice_is_sung():
    hook = composer.hook_of(GUITAR)
    assert _mean(hook.head + hook.body) < voices.MALE_FLOOR, "the line as played is below a man's register"

    man, up = composer.fit_to_voice(hook, voices.MALE)
    assert up == 1 and voices.MALE_FLOOR <= _mean(man.head + man.body) <= voices.MALE_TOP
    assert man.body.startswith("V: Vocal\nG,2B,2D2G2|^F2E2D4|"), "every note an octave up, the sharp kept with its note"

    woman, up = composer.fit_to_voice(hook, voices.FEMALE)
    assert up == 2 and _mean(woman.head + woman.body) >= voices.FEMALE_FLOOR
    assert "G2B2d2g2|^f2e2d4|" in woman.body
    # Only the tune moves: the header and what Ins holds are as they were.
    assert woman.head == hook.head and woman.body.split("V: Ins")[1] == hook.body.split("V: Ins")[1]


def test_a_tune_already_in_the_voices_register_is_left_alone():
    hook = composer.hook_of(GUITAR.replace("G,,2B,,2D,2G,2|^F,2E,2D,4|", '"G"G2B2d2B2|A2G2E4|'))
    fitted, moved = composer.fit_to_voice(hook, voices.MALE)
    assert moved == 0 and fitted == hook


def test_the_style_names_the_voice_unless_it_names_a_singer_already():
    assert composer.style_for_voice("indie rock", "female") == "indie rock, female vocals"
    assert composer.style_for_voice("", "male") == "male vocals"
    assert composer.style_for_voice("soul, female vocals", "male") == "soul, female vocals"
    assert composer.style_for_voice("folk, baritone", "female") == "folk, baritone"


def test_a_tune_played_on_an_instrument_needs_words_before_it_is_expanded(client):
    sid = _instrument_source()
    res = client.post("/api/composer/expand", json={"source_id": sid, "role": "chorus"})
    assert res.status_code == 400 and "Write lyrics" in res.json()["detail"]
    assert one("SELECT COUNT(*) AS n FROM takes")["n"] == 0


def test_the_guitar_line_is_sung_with_the_words_by_the_chosen_voice(client):
    sid = _instrument_source()
    words = "[Verse]\nDown the road\n\n[Chorus]\nSing it back to me"
    res = client.post("/api/composer/expand", json={"source_id": sid, "role": "chorus", "voice": "female",
                                                     "lyrics": words, "style": "indie rock"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["voice"] == "female" and data["octaves"] == 2
    take = one("SELECT * FROM takes WHERE id = ?", (data["take_id"],))
    assert take["kind"] == "cover" and take["lyrics"] == words and take["auto_render"] == 1
    assert take["style"] == "indie rock, female vocals"
    fitted, _ = composer.fit_to_voice(composer.hook_of(GUITAR), "female")
    assert take["hook_abc"] == fitted.head + fitted.body


def test_a_voice_that_is_neither_is_refused(client):
    sid = _instrument_source()
    res = client.post("/api/composer/expand", json={"source_id": sid, "voice": "choir", "lyrics": "[Chorus]\nLa"})
    assert res.status_code == 422


def test_the_recorder_says_a_take_was_played_and_no_words_are_heard_from_it(client):
    wav = _generate_wav_bytes(196.0, duration_seconds=0.3)
    res = client.post("/api/sources", files={"file": ("riff.wav", wav, "audio/wav")},
                      data={"title": "Riff", "origin": "recording", "instrument": "1"})
    assert res.status_code == 200, res.text
    sid = res.json()["id"]
    listed = next(s for s in client.get("/api/sources").json() if s["id"] == sid)
    assert listed["instrument"] == 1 and listed["origin"] == "recording"
    refused = client.post(f"/api/sources/{sid}/lyrics")
    assert refused.status_code == 400 and "Write lyrics" in refused.json()["detail"]
    client.delete(f"/api/sources/{sid}")


def test_an_upload_is_not_an_instrument_take(client):
    wav = _generate_wav_bytes(220.0, duration_seconds=0.3)
    res = client.post("/api/sources", files={"file": ("song.wav", wav, "audio/wav")},
                      data={"title": "Song", "instrument": "1"})
    assert res.status_code == 200 and res.json()["instrument"] == 0
    assert Path(res.json()["stored_path"]).exists()
    client.delete(f"/api/sources/{res.json()['id']}")
