"""A recording from the microphone is a voice, whichever voice the transcriber files its notes in."""
import asyncio
import re
import time

from app import composer, instrumental, jobs, score
from app.db import execute, one

# A short wordless hum as the transcriber can write it: every note in Ins, the Vocal voice
# all rests, and a multi-bar rest standing for four bars.
HUM = """X:1
T:
M:4/4
L:1/16
Q:1/4=100
V: Vocal clef=treble name="Vocal Melody" snm="Vocal"
V: Ins clef=treble name="Ins Melody" snm="Inst."
K:Cm
% verse
V: Vocal
Z4|
V: Ins
z8z2F4F2|E8z4F4-|F2z2E4C2E2C4|z4D4C4B,4|
V: Vocal
Z2|
V: Ins
C4z12|Z|
"""

SUNG = """X:1
M:4/4
L:1/16
K:C
% verse
V: Vocal
"C"c4d4e4f4|"G"g8z8|
V: Ins
z16|E4G4c8|
"""


def test_a_tune_written_in_ins_moves_to_the_vocal_voice():
    voiced = instrumental.tune_on_voice(HUM)
    assert score.vocal_bars(voiced)[:4] == ["z8z2F4F2", "E8z4F4-", "F2z2E4C2E2C4", "z4D4C4B,4"]
    assert not any(instrumental._has_notes(bar) for bar in score.vocal_bars(voiced, "Ins")), "Ins is left as rests"
    assert score.problems(HUM, need_chords=False) == ["only 2 bars"], "the hum as transcribed cannot be covered"
    assert score.problems(voiced, need_chords=False) == []
    assert score.estimate(voiced)["bars"] == score.estimate(HUM)["bars"], "the score keeps its length"
    assert voiced.count("% verse") == 1


def test_a_vocal_bar_keeps_its_chords_when_it_takes_the_notes():
    abc = 'X:1\nM:4/4\nL:1/4\nK:G\nV: Vocal\n"G"z4|"D"z4|\nV: Ins\nG2B2|"Em"A4|\n'
    voiced = instrumental.tune_on_voice(abc)
    assert score.vocal_bars(voiced) == ['"G"G2B2', '"D"A4']
    assert score.vocal_bars(voiced, "Ins") == ["z4", "z4"]


def test_blocks_that_do_not_line_up_trade_places_whole():
    abc = "X:1\nM:4/4\nL:1/4\nK:C\nV: Vocal\nZ3|\nV: Ins\nc4|d4|\n"
    voiced = instrumental.tune_on_voice(abc)
    assert score.vocal_bars(voiced) == ["c4", "d4"]
    assert score.vocal_bars(voiced, "Ins") == ["Z3"]


def test_a_score_with_a_sung_line_is_left_as_it_is():
    assert instrumental.tune_on_voice(SUNG) == SUNG
    silent = "X:1\nM:4/4\nL:1/4\nK:C\nV: Vocal\nZ2|\nV: Ins\nZ2|\n"
    assert instrumental.tune_on_voice(silent) == silent


def _transcribed(source_id: str, origin: str, abc: str) -> str:
    execute("""INSERT INTO sources(id, title, filename, stored_path, sha256, created_at, transcribe_state, origin)
               VALUES(?, 'Hum', 'melody.wav', '/tmp/melody.wav', ?, 1000.0, 'running', ?)""",
            (source_id, source_id, origin))
    record = one("SELECT * FROM sources WHERE id = ?", (source_id,))
    job = {"prompt": [0, "p", {"3": {"class_type": "SheetSage2AudioToABC"}, "4": {"class_type": "PreviewAny"}}],
           "outputs": {"4": {"text": [abc]}}, "status": {"status_str": "success"}}
    asyncio.run(jobs._finish("transcribe", source_id, record, job, time.time()))
    return one("SELECT abc FROM sources WHERE id = ?", (source_id,))["abc"]


def test_a_microphone_recording_is_transcribed_with_its_tune_in_the_vocal_voice():
    stored = _transcribed("mic1", "recording", HUM)
    assert stored == instrumental.tune_on_voice(HUM) != HUM


def test_an_uploaded_file_keeps_the_voices_the_transcriber_gave_it():
    assert _transcribed("up1", "upload", HUM) == HUM


def test_a_hum_transcribed_before_the_change_still_makes_a_hook():
    # A score stored with the tune in Ins: the hook reads it from there.
    hook = composer.hook_of(HUM)
    assert _notes(hook.body).startswith("V: Vocal\nz8z2F4F2|E8z4F4-|F2z2E4C2E2C4|z4D4C4B,4|\n")


def _notes(body: str) -> str:
    """The hook's bars without the chords a tune with none is given (test_instrument_recording)."""
    return re.sub(r'"[^"]*"', "", body)


def test_a_hum_split_between_the_voices_is_all_given_to_the_vocal_voice():
    # The transcriber heard the first bars as an instrument and the rest as a voice.
    split = ("X:1\nM:4/4\nL:1/4\nK:Bm\nV: Vocal\nZ2|\nV: Ins\nB,DEG|EGDF|\n"
             "V: Vocal\nBAGF|EDE2|\nV: Ins\nE2z2|Z|\n")
    voiced = instrumental.tune_on_voice(split)
    assert score.vocal_bars(voiced) == ["B,DEG", "EGDF", "BAGF", "EDE2"]
    assert score.vocal_bars(voiced, "Ins") == ["z4", "z4", "E2z2", "Z"], "where the voice sings, Ins keeps its own"
    hook = composer.hook_of(split)
    assert _notes(hook.body).startswith("V: Vocal\nB,DEG|EGDF|BAGF|EDE2|\n")



# Hummed bars the transcriber called a chorus, opening with a bar of rest, under words of six sections
# that open with a verse.  The words outnumber the score's sections, so the aligner splits the section
# at the hum's pauses; the name the words give it still has to reach its "%" line.
GREEN = """X:1
M:4/4
L:1/16
Q:1/4=116
V: Vocal clef=treble name="Vocal Melody" snm="Vocal"
V: Ins clef=treble name="Ins Melody" snm="Inst."
K:C#m
% chorus
V: Vocal
Z|G3F^E2=D2C2D2E2C2|EF^E=D=E3DC2^B,2C2z2|G3F^E2=D2C2D2E2C2|
V: Ins
Z4|
V: Vocal
EF^E=D=E3DC2^B,2C2z2|D3FF2=D2E3FG2E2|F3GB2=d2c2B2A2z2|G3F^E2=D2C2D2E2C2|
V: Ins
Z4|
V: Vocal
EF^Ez4zC2^B,2C2z2|Z3|
V: Ins
Z4|
"""
WORDS = "\n\n".join(f"[{tag}]\n" + "\n".join(f"{tag} line {n} goes here" for n in range(1, 5))
                      for tag in ("Verse", "Chorus", "Verse", "Chorus", "Bridge", "Chorus"))


def test_a_score_opening_with_rests_takes_the_name_the_words_give_its_section(client):
    execute("""INSERT INTO sources(id, title, filename, stored_path, sha256, created_at, abc, transcribe_state, origin)
               VALUES('rec1', 'Hum', 'melody.wav', '/tmp/melody.wav', 'rec1', 1000.0, ?, 'done', 'recording')""", (GREEN,))
    made = client.post("/api/takes", json={"source_id": "rec1", "lyrics": WORDS}).json()
    abc = one("SELECT abc FROM takes WHERE id = ?", (made["id"],))["abc"]
    sections = [line for line in abc.split("\n") if line.startswith("%")]
    assert sections[0] == "% verse", "the hum's section is named as the words that are sung in it"
    assert "% chorus" not in sections[:1]
