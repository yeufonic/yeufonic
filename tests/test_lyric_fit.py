"""Words set on the notes of a score whose sections are not the lyrics' sections.

A plan names its own sections and lyrics have their own headings, with cue lines such as
"[male voice]" among them, so the two seldom count the same.  The server (aligner.py) and the
piano roll (pianoroll.js) both then fit every line to the whole melody at once, and must agree:
these tests run both on one score."""
import json
import subprocess
from pathlib import Path

from app import aligner

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"

HEAD = ('X:1\nT:\nM:4/4\nL:1/{unit}\nQ:1/4=96\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\n'
        'V: Ins clef=treble name="Ins Melody" snm="Inst."\nK:C\n')
# One syllable to a word, and none the syllable splitter would divide, so a line is six notes' worth.
LINES = ["walk down the long white road", "count all the lamps we pass", "hold on to what you know",
         "keep time with slow grey ships", "sing it out loud and clear", "ring all the bells we own"]
# Cues among the headings, as a duet is written: two real sections, and four headings that are not.
WORDS = "\n".join(["[Verse 1]", "[male voice]", LINES[0], LINES[1], "", "[female voice]", LINES[2], LINES[3], "",
                   "[Chorus]", "[both voices]", LINES[4], LINES[5]])


def plan(unit: int) -> str:
    """Six phrases, one to a bar (six notes and a rest), in three sections of the plan's own naming."""
    step = unit // 8                                        # an eighth note, in this score's units
    bar = "".join(f"{note}{step}" for note in "CDEFGA") + f"z{2 * step}"
    out = [HEAD.format(unit=unit)]
    for name, chord in (("verse", "C"), ("verse", "F"), ("chorus", "G")):
        out.append(f'% {name}\nV: Vocal\n"{chord}"{bar}|"{chord}"{bar}|\nV: Ins\nZ2|\n')
    return "".join(out)


def bars_of_words(abc: str) -> list[list[str]]:
    """The words under each bar, from a score's w: lines."""
    out = []
    for line in abc.splitlines():
        if line.startswith("w:"):
            out.extend(bar.split() for bar in line[2:].strip().rstrip("|").split("|"))
    return out


def in_the_roll(abc: str, lyrics: str) -> dict:
    """The piano roll matching these lyrics to this score, and the server's answer read by the same roll."""
    page = (STATIC / "app.js").read_text(encoding="utf-8")
    cues = page[page.index("var VOICE_WORDS"):page.index("/* The tick is offered once")]
    script = (
        "const fs = require('fs'); const d = JSON.parse(fs.readFileSync(0, 'utf8'));"
        + cues + ";"
        # the roll looks for the page's cue reader on the window, which under node is what it exports
        "const P = require(%s); P.hasVoiceCues = hasVoiceCues;"
        "function sung(model) { return model.notes.filter(n => n.voice === 'Vocal' && n.lyric).sort((a, b) => a.startTick - b.startTick)"
        "  .map(n => [n.startTick * 16 / model.unitLength, n.lyric]); }"
        "P.PianoRoll.model = P.parseAbc(d.abc); P.PianoRoll.listeners = []; P.PianoRoll.renderAll = function () {};"
        "P.PianoRoll.matchSongLyrics(d.lyrics, true);"
        "console.log(JSON.stringify({ roll: sung(P.PianoRoll.model), server: sung(P.parseAbc(d.server)),"
        "  sections: P.PianoRoll.model.sections.map(s => s.text), abc: P.serializeToAbc(P.PianoRoll.model) }));"
        % json.dumps(str(STATIC / "pianoroll.js")))
    data = {"abc": abc, "lyrics": lyrics, "server": aligner.align_lyrics_to_abc(abc, lyrics)}
    res = subprocess.run(["node", "-e", script], input=json.dumps(data), capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


# ------------------------------------------------------------------ the server
def test_a_cue_line_is_not_a_section_of_the_lyrics():
    sections = aligner.sung_sections(WORDS)
    assert [(s["name"], s["lines"]) for s in sections] == [("Verse 1", LINES[:4]), ("Chorus", LINES[4:])]
    # a direction that names no voice is still a block of its own, as it was
    assert [s["name"] for s in aligner.sung_sections("[strings]\none two\n[full orchestra]\nthree four")] == ["strings", "full orchestra"]
    # and cues with no section above them are one run of lines
    assert [(s["name"], len(s["lines"])) for s in aligner.sung_sections("[male voice]\na b\n[female voice]\nc d")] == [("", 2)]


def test_every_line_starts_its_own_phrase_whatever_unit_the_score_counts_in():
    for unit in (32, 16, 8):
        aligned = aligner.align_lyrics_to_abc(plan(unit), WORDS)
        assert bars_of_words(aligned) == [line.split() for line in LINES], unit


def test_the_first_sung_phrase_gets_the_first_line_when_a_heading_is_followed_by_a_cue():
    aligned = aligner.align_lyrics_to_abc(plan(32), WORDS)
    assert bars_of_words(aligned)[0] == LINES[0].split()
    assert aligned.count("\nw:") == 3                       # every sung line of the score has its words


def test_lengths_written_as_fractions_and_bars_of_rest_keep_their_place():
    score = (HEAD.format(unit=8) + "% verse\nV: Vocal\n"
             '"C"C/2D/2E/2F/2 G/2A/2B/2c/2 z4|Z2|"F"c/D/E/F/ G/A/B/c/ z4|\nV: Ins\nZ4|\n')
    aligned = aligner.align_lyrics_to_abc(score, "one two three four five six strong eight\nnine ten some more words in a line")
    assert bars_of_words(aligned) == [["one", "two", "three", "four", "five", "six", "strong", "eight"], [],
                                      ["nine", "ten", "some", "more", "words", "in", "a", "line"]]


def test_a_field_written_in_a_line_is_not_a_note():
    score = plan(16).replace('% chorus\nV: Vocal\n"G"', '% chorus\nV: Vocal\n[M:4/4]"G"')
    assert bars_of_words(aligner.align_lyrics_to_abc(score, WORDS)) == [line.split() for line in LINES]


# ------------------------------------------------------------------ the piano roll
def test_the_roll_sets_the_words_where_the_server_does():
    for unit in (32, 16):
        out = in_the_roll(plan(unit), WORDS)
        assert out["roll"] == out["server"] and len(out["roll"]) == 36, unit
        assert [word for _, word in out["roll"]] == " ".join(LINES).split()
        # each line on its own bar: a bar is sixteen sixteenths, and a line is six eighths from its start
        assert [at for at, _ in out["roll"]] == [bar * 16 + note * 2 for bar in range(6) for note in range(6)]


def test_the_roll_leaves_the_plans_sections_as_the_plan_named_them():
    out = in_the_roll(plan(32), WORDS)
    assert out["sections"] == ["% verse", "% verse", "% chorus"]
    assert bars_of_words(out["abc"])[0] == LINES[0].split()


def test_the_roll_and_the_server_agree_when_the_words_outrun_the_tune():
    long_words = "\n".join(["[Verse 1]", "[male voice]"] + LINES + ["[female voice]"] + LINES + ["[Chorus]"] + LINES)
    out = in_the_roll(plan(32), long_words)
    assert out["roll"] == out["server"]
    assert [word for _, word in out["roll"]][:6] == LINES[0].split()        # the start is where it should be


def test_a_heading_with_a_cue_under_it_does_not_take_a_section_of_the_score_for_itself():
    """Three headings and three sections of the score, but one heading is a cue: counted as a section, the
    first heading had no lines of its own and the first sung phrase was left without words."""
    words = "\n".join(["[Verse 1]", "[male voice]"] + LINES[:4] + ["[Chorus]"] + LINES[4:])
    assert bars_of_words(aligner.align_lyrics_to_abc(plan(32), words)) == [line.split() for line in LINES]
    out = in_the_roll(plan(32), words)
    assert out["roll"] == out["server"]
    assert [word for _, word in out["roll"]][:6] == LINES[0].split() and out["roll"][0][0] == 0


def test_the_roll_and_the_server_hold_the_same_notes_when_a_line_is_shorter_than_its_phrase():
    """Short and long notes, and fewer syllables than notes: which notes are held is the fitting's choice."""
    bar = "C2D2E4F2G2A4B8z8"                                 # seven notes of three lengths, then a rest
    score = HEAD.format(unit=32) + "".join(
        f'% {name}\nV: Vocal\n"C"{bar}|"F"{bar}|\nV: Ins\nZ2|\n' for name in ("verse", "verse", "chorus"))
    words = "\n".join(["[Verse 1]"] + [" ".join(line.split()[:4]) for line in LINES[:4]] + ["[Chorus]", "sing loud", "ring all the bells we own"])
    out = in_the_roll(score, words)
    assert out["roll"] == out["server"] and len(out["roll"]) == 4 * 4 + 2 + 6
    assert [at for at, _ in out["roll"]][:5] == [0, 1, 2, 8, 16]        # a line's last word is on the note the phrase rests after


def test_sections_that_count_the_same_are_still_matched_one_to_one():
    words = "\n".join(["[Verse 1]", LINES[0], LINES[1], "[Verse 2]", LINES[2], LINES[3], "[Chorus]", LINES[4], LINES[5]])
    out = in_the_roll(plan(32), words)
    assert [word for _, word in out["roll"]] == " ".join(LINES).split()
    assert [at for at, _ in out["roll"]][::6] == [0, 16, 32, 48, 64, 80]
