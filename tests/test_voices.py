"""Who sings: voice cues in the lyrics, kept on the plan's vocal line.

The render sings the vocal line an octave below where it is written and takes the voice from
the register, not from a cue line, so a cue is kept by moving the cued phrases by octaves: low
for a man, high for a woman, an octave pair for both.  These tests build small plans the way
the planner writes them, with its habit of changing octave every four lines."""
import asyncio
import json
import re
import subprocess
from pathlib import Path

import pytest

from app import jobs, score, transpose, voices
from app.db import execute, one
from conftest import make_take
from test_jobs import FakeEngine, PLAN_GRAPH, done, use

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"

LOW, HIGH = "CDEFGA", "cdefga"          # a phrase of six notes around E4, and the same an octave up
HEAD = ('X:1\nT:\nM:4/4\nL:1/8\nQ:1/4=100\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\n'
        'V: Ins clef=treble name="Ins Melody" snm="Inst."\nK:C\n')


def plan(*sections: tuple[str, list[str]]) -> str:
    """A plan of sections, each a list of phrases, one phrase to a bar: six notes and a rest."""
    out = [HEAD]
    for name, bars in sections:
        out.append(f"% {name}\nV: Vocal\n" + "".join(f'"C"{bar}z2|' for bar in bars) + f"\nV: Ins\nZ{len(bars)}|\n")
    return "".join(out)


def words(*blocks: tuple[str, int]) -> str:
    """Lyrics from (a tag or cue line, how many sung lines follow it)."""
    out = []
    for tag, count in blocks:
        out.append(tag)
        out.extend(["la la la la la la"] * count)
    return "\n".join(out)


def registers(abc: str, lyrics: str) -> str:
    """Each phrase of the vocal line as a letter: l low, h high, P an octave pair."""
    _, groups, _ = voices.voices_of(abc, lyrics)
    out = ""
    for group in groups:
        pair = all(len(note["parts"]) > 1 for note in group)
        out += "P" if pair else ("h" if voices._mean(group) >= 70.5 else "l")
    return out


DUET = words(("[Verse 1]", 0), ("[male voice, calm]", 8), ("[female voice, bright]", 8),
             ("[Chorus]", 0), ("[male and female voices, full harmony]", 4))
# The planner's habit: four lines low, four lines an octave up, and again, whoever is cued.
HABIT = plan(("verse", [LOW] * 4 + [HIGH] * 4 + [LOW] * 4 + [HIGH] * 4), ("chorus", [HIGH] * 4))


# ------------------------------------------------------------------ reading the cues
@pytest.mark.parametrize("line, voice", [
    ("[male voice, controlled, professional]", "male"),
    ("[female vocal]", "female"),
    ("[Female Voice]", "female"),
    ("[male and female voices, full harmony]", "both"),
    ("[both]", "both"), ("[Duet]", "both"), ("[Him]", "male"), ("[Her]", "female"), ("[tenor]", "male"),
    ("(female voice, soft, enigmatic)", "female"),
    ("(the woman sings)", "female"),
    ("(both voices)", "both"),
    ("[Verse 2 - female vocal]", "female"),
    ("[voix masculine]", "male"), ("[femme]", "female"),
    # not cues
    ("[Verse 1]", None), ("[Chorus]", None), ("[guitar solo]", None), ("[strings]", None),
    ("(oh man)", None), ("(together now)", None), ("(she said)", None),
    ("He told the woman to sing", None), ("a female voice in the hall", None), ("", None),
    ("[male voice] and then some words", None),
])
def test_what_is_a_cue(line, voice):
    assert voices.cue_of(line) == voice


def test_a_cue_holds_until_the_next_cue_or_the_next_section():
    lines = voices.sung_lines(
        "[Verse 1]\n[male voice]\none\ntwo\n[female voice]\nthree\n(oh yeah)\n\n"
        "[Chorus]\nfour\n[strings]\nfive\n[Verse 2: both]\nsix")
    assert [(l["text"], l["cue"], l["section"]) for l in lines] == [
        ("one", "male", "verse"), ("two", "male", "verse"),
        ("three", "female", "verse"), ("(oh yeah)", "female", "verse"),   # backing words are sung
        ("four", None, "chorus"), ("five", None, "chorus"),               # a section that says nothing
        ("six", "both", "verse"),
    ]
    assert voices.has_cues("[Verse]\n[female voice]\nla") and not voices.has_cues("[Verse]\nla\n(oh man)")


def test_syllables_in_several_scripts():
    assert voices.syllables("Votre mari est mort cette nuit") == 9
    assert voices.syllables("la la la") == 3
    assert voices.syllables("hmm") == 1
    assert voices.syllables("你好世界") == 4


# ------------------------------------------------------------------ fitting a plan
def test_the_planners_habit_is_put_right():
    assert registers(HABIT, DUET) == "llllhhhh" "llllhhhh" "hhhh"
    fitted, summary = voices.fit(HABIT, DUET)
    assert registers(fitted, DUET) == "llllllll" "hhhhhhhh" "PPPP"
    assert summary["changed"] and summary["moved"] == 8 and summary["paired"] == 4
    assert (summary["male"], summary["female"], summary["both"]) == (8, 8, 4)
    assert "8 phrases moved by an octave" in voices.describe(summary) and "4 doubled" in voices.describe(summary)


def test_only_the_octave_of_the_vocal_line_changes():
    fitted, _ = voices.fit(HABIT, DUET)
    before, after = HABIT.split("\n"), fitted.split("\n")
    assert len(before) == len(after)
    for old, new in zip(before, after):
        if old != new:
            # the same notes in the same order, with the same lengths, chords and barlines
            strip = lambda text: re.sub(r"[\[\],']", "", text).lower()   # noqa: E731
            assert strip(new).replace("cc", "c").replace("dd", "d").replace("ee", "e").replace("ff", "f") \
                .replace("gg", "g").replace("aa", "a") == strip(old)
    assert [l for l in after if l.startswith("Z")] == [l for l in before if l.startswith("Z")]
    assert fitted.count('"C"') == HABIT.count('"C"')
    # a pair is the note and the octave below it, the upper one where a woman sings
    assert '"C"[cC][dD][eE][fF][gG][aA]z2|' in fitted


def test_fitting_again_changes_nothing():
    fitted, _ = voices.fit(HABIT, DUET)
    again, summary = voices.fit(fitted, DUET)
    assert again == fitted and summary["changed"] is False
    assert voices.describe(summary) == "The voices are already as cued."


def test_a_plan_already_as_cued_is_left_exactly_as_it_is():
    cued = plan(("verse", [LOW] * 8 + [HIGH] * 8))
    lyrics = words(("[Verse]", 0), ("[male voice]", 8), ("[female voice]", 8))
    assert voices.fit(cued, lyrics)[0] is cued


def test_no_cues_no_change():
    assert voices.fit(HABIT, words(("[Verse]", 16), ("[Chorus]", 4))) == (HABIT, None)
    assert voices.fit("", DUET) == ("", None)
    assert voices.describe(None) == "The lyrics have no voice cues."


def test_new_cues_undo_the_old_ones():
    """Fitted for one set of cues and then for another, a plan follows the second: a pair goes
    back to one voice, and a line cued for nobody stays where it was put."""
    fitted, _ = voices.fit(HABIT, DUET)
    swapped = words(("[Verse 1]", 0), ("[female voice]", 8), ("[male voice]", 8), ("[Chorus]", 0), ("[female voice]", 4))
    again, summary = voices.fit(fitted, swapped)
    assert registers(again, swapped) == "hhhhhhhh" "llllllll" "hhhh"
    assert summary["singled"] == 4 and "[" not in again.split("% chorus")[1].split("V: Ins")[0].replace('"C"', "")


def test_a_run_of_tune_moves_as_one():
    """Phrases that sit together are one stretch of melody.  A man's verse that climbs a little
    is left alone, although its highest phrase alone would be too high for him."""
    climbing = plan(("verse", ["CDEFGA", "DEFGAB", "EFGABc", "DEFGAB"]))
    assert voices.fit(climbing, words(("[Verse]", 0), ("[male voice]", 4)))[0] is climbing
    # and the same tune for a woman goes up whole, its shape kept
    fitted, _ = voices.fit(climbing, words(("[Verse]", 0), ("[female voice]", 4)))
    assert '"C"cdefgaz2|"C"defgabz2|"C"efgabc\'z2|"C"defgabz2|' in fitted


def test_between_the_two_registers_nobody_is_left():
    """Around A4 to B4 the same notes have been sung by a man and by a woman.  A man's line found
    there goes down and a woman's goes up; for both, the upper voice is a woman's."""
    middle = plan(("verse", ["ABABAB"] * 4))
    his = voices.fit(middle, words(("[Verse]", 0), ("[male voice]", 4)))[0]
    hers = voices.fit(middle, words(("[Verse]", 0), ("[female voice]", 4)))[0]
    assert '"C"A,B,A,B,A,B,z2|' in his and '"C"ababab' in hers
    # a woman's line written far above the staff comes down to where the planner writes one
    high = plan(("verse", ["c'd'e'f'g'a'"] * 4))
    assert '"C"cdefga' in voices.fit(high, words(("[Verse]", 0), ("[female voice]", 4)))[0]


def test_a_pickup_belongs_to_the_phrase_it_leads_into():
    """A phrase often begins in the last bar of the section before.  The whole phrase moves,
    pickup and all, and the phrase that ends in that bar does not."""
    abc = (HEAD + "% verse\nV: Vocal\n" + '"C"CDEFGAz2|' * 3 + '"C"CDEFz2cd|' + "\nV: Ins\nZ4|\n"
           + "% chorus\nV: Vocal\n" + '"C"efgaz4|' + '"C"cdefgaz2|' * 3 + "\nV: Ins\nZ4|\n")
    lyrics = words(("[Verse]", 0), ("[female voice]", 4), ("[Chorus]", 0), ("[male voice]", 4))
    fitted, _ = voices.fit(abc, lyrics)
    assert '"C"cdefz2CD|' in fitted            # the verse's last phrase up, the chorus pickup down
    assert '"C"EFGAz4|' in fitted


def test_an_accidental_still_means_what_it_meant():
    """An accidental holds for its pitch, in its octave, to the end of the bar.  When part of a
    bar moves, a note that relied on one is given it again, and a note that would pick one up
    by moving next to it is marked natural."""
    abc = (HEAD + "% verse\nV: Vocal\n"
           '"C"^FGAGFEz2|"C"cdefz2^fg|"C"fgagfez2|"C"CDEFz2=cd|"C"^cdcdcdz2|' + "\nV: Ins\nZ5|\n")
    lyrics = words(("[Verse]", 0), ("[male voice]", 1), ("[female voice]", 1), ("[male voice]", 2), ("[female voice]", 1))
    fitted, _ = voices.fit(abc, lyrics)
    bars = fitted.split("V: Vocal\n")[-1].split("\n")[0].split("|")
    assert bars[0] == '"C"^FGAGFEz2'              # F sharp, and the later F still sharp: nothing moved here
    assert bars[1] == '"C"cdefz2^FG'              # the pickup to the man's phrase comes down with it
    assert bars[2] == '"C"FGAGFEz2'               # a new bar: the sharp is gone, as it was
    assert bars[3] == '"C"CDEFz2=cd'              # nothing moved, so not a character changed
    # read back, every note is the pitch it was, give or take whole octaves
    def pitches(text):
        plan_ = voices.read(text)
        key = transpose.signature(0)
        out, heard, line_bar = [], {}, None
        for note in plan_["notes"]:
            bar = (note["line"], text.split("\n")[note["line"]][:note["start"]].count("|"))
            if bar != line_bar:
                heard, line_bar = {}, bar
            part = note["top"]
            said = {"^": 1, "_": -1, "=": 0}.get(part["acc"])
            letter, octave = part["letter"].upper(), voices._height(part["letter"], part["marks"])
            if said is not None:
                heard[(letter, octave)] = said
            out.append((transpose.BASE[letter] + heard.get((letter, octave), key.get(letter, 0))) % 12)
        return out
    assert pitches(fitted) == pitches(abc)


def test_lines_the_plan_never_reached_are_not_pushed_onto_other_phrases():
    """A plan can stop before the lyrics do.  The lines it has no phrases for are left out;
    the outro's cue does not land on the last chorus."""
    short = plan(("verse", [LOW] * 4), ("chorus", [HIGH] * 4))
    lyrics = words(("[Verse]", 0), ("[male voice]", 4), ("[Chorus]", 0), ("[female voice]", 4),
                   ("[Outro]", 0), ("[male voice]", 6))
    _, groups, cues = voices.voices_of(short, lyrics)
    assert cues == ["male"] * 4 + ["female"] * 4
    assert voices.fit(short, lyrics)[0] is short


def test_a_section_the_plan_names_otherwise_still_carries_its_lines():
    """The planner may write a long verse as a verse and a pre-chorus.  The lines follow."""
    split = plan(("verse", [HIGH] * 4), ("pre-chorus", [HIGH] * 4), ("chorus", [LOW] * 4))
    lyrics = words(("[Verse 1]", 0), ("[male voice]", 8), ("[Chorus]", 0), ("[female voice]", 4))
    fitted, _ = voices.fit(split, lyrics)
    assert registers(fitted, lyrics) == "llllllll" "hhhh"


def test_a_line_sung_as_two_phrases_and_a_change_of_voice_one_phrase_out():
    """Syllables place a line to within a phrase.  Where the melody itself changes register a
    phrase away from where the count put the change of voice, the melody is believed."""
    halves = ["CDEz5", "FGAz5"] * 4 + [HIGH] * 4          # four lines, each sung in two halves, then four whole
    abc = HEAD + "% verse\nV: Vocal\n" + "".join(f'"C"{bar}|' if "z5" in bar else f'"C"{bar}z2|' for bar in halves) + "\nV: Ins\nZ12|\n"
    lyrics = words(("[Verse]", 0), ("[male voice]", 4), ("[female voice]", 4))
    fitted, _ = voices.fit(abc, lyrics)
    assert fitted == abc                                   # already as cued: the low eight halves are his


def test_a_fitted_score_is_still_a_score():
    """Octave pairs in the vocal line pass the checks a plan has to pass, and a key lock moves them whole."""
    fitted, _ = voices.fit(HABIT, DUET)
    assert score.problems(fitted, need_chords=False) == []
    moved = transpose.to_key(fitted, "D")
    assert moved and "K:D" in moved and '[dD][eE][fF][gG][aA][bB]' in moved      # F is sharp in the key now
    assert voices.fit(moved, DUET)[1]["changed"] is False     # and it is still as cued after the move


# ------------------------------------------------------------------ in the app
def test_the_tick_is_kept_with_the_take(client):
    body = {"title": "S", "style": "rock", "lyrics": DUET, "voice_cues": 1}
    take = client.post("/api/songs", json=body).json()
    assert take["voice_cues"] == 1
    assert client.post("/api/songs", json={k: v for k, v in body.items() if k != "voice_cues"}).json()["voice_cues"] is None
    assert client.post("/api/songs", json={**body, "voice_cues": 2}).status_code == 422


def test_a_plan_is_fitted_as_it_lands_when_the_take_asks(monkeypatch):
    ticked = make_take(status="queued", lyrics=DUET)
    execute("UPDATE takes SET voice_cues = 1 WHERE id = ?", (ticked["id"],))
    use(monkeypatch, FakeEngine([None, done({"3": {"text": [HABIT]}}, PLAN_GRAPH)]))
    asyncio.run(jobs.run_job("plan", ticked["id"]))
    row = one("SELECT * FROM takes WHERE id = ?", (ticked["id"],))
    assert row["status"] == "planned" and registers(row["abc"], DUET) == "llllllll" "hhhhhhhh" "PPPP"

    plain = make_take(status="queued", lyrics=DUET)
    use(monkeypatch, FakeEngine([None, done({"3": {"text": [HABIT]}}, PLAN_GRAPH)]))
    asyncio.run(jobs.run_job("plan", plain["id"]))
    assert one("SELECT abc FROM takes WHERE id = ?", (plain["id"],))["abc"] == HABIT


def test_a_render_sings_the_fitted_score_and_keeps_it(monkeypatch):
    """The words or the score may have changed since the plan, so the cues are kept again as a
    render starts, and the score kept with the take is the one that was sung."""
    take = make_take(status="queued", lyrics=DUET, abc=HABIT)
    execute("UPDATE takes SET voice_cues = 1 WHERE id = ?", (take["id"],))
    engine = use(monkeypatch, FakeEngine([done({}, {}, status="error")]))
    asyncio.run(jobs.run_job("render", take["id"]))
    sent = engine.submitted[0]["11"]["inputs"]["abc"]
    assert registers(sent, DUET) == "llllllll" "hhhhhhhh" "PPPP"
    kept = one("SELECT abc FROM takes WHERE id = ?", (take["id"],))["abc"]
    assert kept == voices.fit(HABIT, DUET)[0] and kept.strip() == sent.strip()


def test_who_is_never_fitted():
    fitted = voices.fit(HABIT, DUET)[0]
    assert jobs.voiced({"abc": HABIT, "lyrics": DUET, "kind": "song", "voice_cues": 1}) == fitted
    assert jobs.voiced({"abc": HABIT, "lyrics": DUET, "kind": "cover", "voice_cues": 1}) == fitted
    assert jobs.voiced({"abc": HABIT, "lyrics": DUET, "kind": "song", "voice_cues": None}) == HABIT
    assert jobs.voiced({"abc": HABIT, "lyrics": DUET, "kind": "instrumental", "voice_cues": 1}) == HABIT
    assert jobs.voiced({"abc": "not a score", "lyrics": DUET, "kind": "song", "voice_cues": 1}) == "not a score"


def test_the_score_window_can_ask_for_a_fit(client):
    answer = client.post("/api/voices/fit", json={"abc": HABIT, "lyrics": DUET}).json()
    assert answer["changed"] and answer["cues"] and registers(answer["abc"], DUET) == "llllllll" "hhhhhhhh" "PPPP"
    assert answer["message"].startswith("Voices fitted to the cues")
    again = client.post("/api/voices/fit", json={"abc": answer["abc"], "lyrics": DUET}).json()
    assert not again["changed"] and again["abc"] == answer["abc"] and again["message"] == "The voices are already as cued."
    none = client.post("/api/voices/fit", json={"abc": HABIT, "lyrics": "[Verse]\nla la"}).json()
    assert not none["changed"] and not none["cues"] and none["abc"] == HABIT


# ------------------------------------------------------------------ the page reads cues the same way
def test_the_page_offers_the_tick_for_the_lines_the_server_reads_as_cues():
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    start = app_js.index("var VOICE_WORDS = {")
    source = app_js[start:app_js.index("/* The tick is offered", start)]
    lines = ["[male voice, controlled]", "[female vocal]", "[male and female voices]", "[both]", "[Duet]", "[Him]",
             "(female voice, soft)", "(the woman sings)", "(both voices)", "[Verse 2 - female vocal]", "[voix masculine]",
             "[Verse 1]", "[Chorus]", "[guitar solo]", "(oh man)", "(together now)", "(she said)",
             "He told the woman to sing", "a female voice in the hall", "[male voice] and then some words"]
    script = source + f"\nconsole.log(JSON.stringify({json.dumps(lines)}.map(function (l) {{ return hasVoiceCues(l); }})));"
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert json.loads(res.stdout) == [voices.cue_of(line) is not None for line in lines]

    page = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'id="voice-cues"' in page and 'id="fit-voices"' in page
    assert "body.voice_cues = adv.voice_cues" in app_js
