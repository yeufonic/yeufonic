"""A tune played on an instrument (a guitar into the recorder) as the sung tune of a song."""
import re
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
    assert re.sub(r'"[^"]*"', "", man.body).startswith("V: Vocal\nG,2B,2D2G2|^F2E2D4|"), "every note an octave up, the sharp kept with its note"

    woman, up = composer.fit_to_voice(hook, voices.FEMALE)
    assert up == 2 and _mean(woman.head + woman.body) >= voices.FEMALE_FLOOR
    assert "G2B2d2g2|^f2e2d4|" in re.sub(r'"[^"]*"', "", woman.body)
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


def test_a_recorded_tune_is_transcribed_as_melody_only_and_an_upload_with_chords():
    from app import jobs
    assert jobs.transcribe_mode({"origin": "recording", "instrument": 1}) == "melody"
    assert jobs.transcribe_mode({"origin": "recording"}) == "melody"
    assert jobs.transcribe_mode({"origin": "upload"}) == "full"
    graph = jobs.build_transcribe_graph("tune.flac", jobs.transcribe_mode({"origin": "recording"}))
    assert graph["3"]["inputs"]["mode"] == "melody" and graph["1"]["inputs"]["audio"] == "tune.flac"
    assert jobs.build_transcribe_graph("song.flac")["3"]["inputs"]["mode"] == "full"


# A lone tune as the transcriber writes it when it hears no chords: a guitar line in A minor.
NO_CHORDS = """X:1
T:
M:4/4
L:1/16
Q:1/4=90
V: Vocal clef=treble name="Vocal Melody" snm="Vocal"
V: Ins clef=treble name="Ins Melody" snm="Inst."
K:Am
V: Vocal
z12c4|A8z2A2c2d2|G12G2A2|_B4f6f2e2c2|
V: Ins
z16|z16|z16|z16|
V: Vocal
d2c_BA12|Z|
V: Ins
z16|Z|
"""


def test_a_tune_with_no_chords_is_given_them_from_its_own_notes():
    # A plan held to a hook with no chords was written with none, twice, and failed its checks.
    hook = composer.hook_of(NO_CHORDS)
    first = hook.body.split("\n")[1]
    assert first == '"Am"z12c4|"Am"A8z2A2c2d2|"C"G12G2A2|"F"_B4f6f2e2c2|'
    # The flat a bar's B carries holds for the rest of that bar: a D minor bar, not a B flat one.
    assert hook.body.split("\n")[5] == '"Dm"d2c_BA12|'
    # Ins keeps its rests, and no chord is put on a bar of whole rests.
    assert hook.body.split("\n")[3] == "z16|z16|z16|z16|"
    assert hook.bars == 5


def test_a_tune_whose_transcription_has_chords_keeps_them():
    with_some = NO_CHORDS.replace("|G12G2A2|", '|"Em"G12G2A2|')
    assert composer.with_chords(with_some) == with_some
    assert '"Em"G12G2A2' in composer.hook_of(with_some).body
    assert '"Am"' not in composer.hook_of(with_some).body


def test_chords_follow_the_key_signature_and_a_flat_key_is_spelled_in_flats():
    abc = "X:1\nM:4/4\nL:1/8\nK:Bb\nV: Vocal\nB2d2f4|E2G2B4|F2A2c4|\nV: Ins\nZ3|\n"
    assert composer.with_chords(abc).split("\n")[5] == '"Bb"B2d2f4|"Eb"E2G2B4|"F"F2A2c4|'


def test_the_expand_window_takes_the_tune_from_the_recording_not_a_takes_plan():
    page = (Path(__file__).resolve().parents[1] / "app/static/app.js").read_text(encoding="utf-8")
    start = page.index("async function doExpandToSong")
    sent = page[start:page.index("JSON.stringify", start) + 400]
    assert "abc: expandBoxIsTune(source) ?" in sent
    assert "Selection.boxKind === 'source' && Selection.boxId === source.id" in page
