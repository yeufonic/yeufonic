"""Moving, copying and removing the sections of a score (app/static/sectionedit.js)."""
import json
import subprocess
from pathlib import Path

MODULE = Path(__file__).resolve().parent.parent / "app" / "static" / "sectionedit.js"

SCORE = ("X:1\nM:4/4\nL:1/16\nQ:1/4=90\nV: Vocal\nV: Ins\nK:C\n"
         '% intro\nV: Vocal\n"C"z16|\nV: Ins\nc4e4g4e4|\n'
         '% verse\nV: Vocal\n"Am"z16|\nV: Ins\nA4c4e4c4|\n'
         '% chorus\nV: Vocal\n"F"z16|\nV: Ins\nF4A4c4A4|\n'
         '% verse\nV: Vocal\n"Am"z16|\nV: Ins\nA4c4e4a4|\n')


def run(abc, ops):
    script = ("const S = require(%s); let t=''; process.stdin.on('data', c => t += c);"
              "process.stdin.on('end', () => { const { abc, ops } = JSON.parse(t); let out = abc; const seen = [];"
              "for (const op of ops) { out = S.change(out, op); seen.push(out); if (out === null) break; }"
              "console.log(JSON.stringify(seen)); });" % json.dumps(str(MODULE)))
    res = subprocess.run(["node", "-e", script], input=json.dumps({"abc": abc, "ops": ops}),
                         capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def names(abc):
    return [line[1:].strip() for line in abc.splitlines() if line.startswith("% ")]


def test_a_section_moves_up_and_down():
    up, = run(SCORE, [{"act": "up", "index": 2}])
    assert names(up) == ["intro", "chorus", "verse", "verse"]
    down, = run(SCORE, [{"act": "down", "index": 0}])
    assert names(down) == ["verse", "intro", "chorus", "verse"]


def test_the_header_and_each_sections_notes_travel_unchanged():
    out, = run(SCORE, [{"act": "up", "index": 2}])
    assert out.startswith(SCORE[:SCORE.index("% intro")])
    assert "% chorus\nV: Vocal\n\"F\"z16|\nV: Ins\nF4A4c4A4|\n% verse\nV: Vocal\n\"Am\"z16|\nV: Ins\nA4c4e4c4|\n" in out


def test_copying_the_chorus_in_place_of_a_second_verse_gives_verse_chorus_verse_chorus():
    """The case that prompted this: verse, chorus, verse, verse becomes verse, chorus, verse, chorus."""
    score = SCORE.replace("% intro\nV: Vocal\n\"C\"z16|\nV: Ins\nc4e4g4e4|\n", "")      # verse, chorus, verse
    copied, = run(score, [{"act": "copy", "index": 1}])
    assert names(copied) == ["verse", "chorus", "chorus", "verse"]
    final = run(score, [{"act": "copy", "index": 1}, {"act": "down", "index": 2}])[-1]
    assert names(final) == ["verse", "chorus", "verse", "chorus"]
    assert final.count('"F"z16|') == 2


def test_a_section_can_be_taken_out_but_not_the_last_one():
    out, = run(SCORE, [{"act": "remove", "index": 1}])
    assert names(out) == ["intro", "chorus", "verse"]
    one = SCORE[:SCORE.index("% verse")]
    assert run(one, [{"act": "remove", "index": 0}]) == [None]


def test_changes_that_cannot_be_made_say_so():
    assert run(SCORE, [{"act": "up", "index": 0}]) == [None]
    assert run(SCORE, [{"act": "down", "index": 3}]) == [None]
    assert run(SCORE, [{"act": "copy", "index": 9}]) == [None]
    assert run(SCORE, [{"act": "dance", "index": 1}]) == [None]
    assert run("X:1\nK:C\nabc|\n", [{"act": "up", "index": 0}]) == [None]


def test_a_score_without_a_closing_newline_keeps_none_and_one_with_keeps_one():
    bare = SCORE.rstrip("\n")
    moved, = run(bare, [{"act": "up", "index": 1}])
    assert not moved.endswith("\n") and names(moved)[0] == "verse"
    kept, = run(SCORE, [{"act": "up", "index": 1}])
    assert kept.endswith("|\n") and not kept.endswith("\n\n")


def test_a_section_can_be_moved_to_a_place():
    out, = run(SCORE, [{"act": "move", "index": 3, "to": 1}])
    assert names(out) == ["intro", "verse", "verse", "chorus"]
    out, = run(SCORE, [{"act": "move", "index": 0, "to": 3}])
    assert names(out) == ["verse", "chorus", "verse", "intro"]
    assert run(SCORE, [{"act": "move", "index": 1, "to": 1}]) == [None]
    assert run(SCORE, [{"act": "move", "index": 1, "to": 9}]) == [None]
    back = run(SCORE, [{"act": "move", "index": 0, "to": 3}, {"act": "move", "index": 3, "to": 0}])
    assert back[-1] == SCORE


def test_moving_there_and_back_gives_the_original_score():
    seen = run(SCORE, [{"act": "down", "index": 1}, {"act": "up", "index": 2}])
    assert seen[-1] == SCORE


def test_the_page_loads_the_helper_before_the_script_that_uses_it():
    root = MODULE.parent
    html = (root / "index.html").read_text(encoding="utf-8")
    assert html.index("sectionedit.js") < html.index("/static/app.js")


def lib(expression):
    script = ("const S = require(%s); console.log(JSON.stringify(%s));" % (json.dumps(str(MODULE)), expression))
    return json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)


def test_a_score_that_fits_the_cap_is_left_alone_and_one_that_does_not_says_by_how_much_and_what_would_hold_it():
    assert lib("S.capCheck(180, 240)") == {"over": False}
    assert lib("S.capCheck(240, 240)") == {"over": False}                     # exactly the cap fits
    assert lib("S.capCheck(218, 180)") == {"over": True, "short": 38, "raiseTo": 230}
    assert lib("S.capCheck(181, 180)")["raiseTo"] == 200                      # ten seconds to spare, rounded up to ten
    assert lib("S.capCheck(895, 360)")["raiseTo"] == 900                      # never past what the engine allows
    assert lib("S.capCheck(0, 180)") == {"over": False} and lib("S.capCheck(100, 0)") == {"over": False}   # nothing to compare


def test_the_words_note_says_what_the_words_need_after_each_kind_of_change():
    assert "added 1 section" in lib("S.wordsNote(7, 8, false)") and "1 more block of words" in lib("S.wordsNote(7, 8, false)")
    assert "added 2 sections" in lib("S.wordsNote(7, 9, false)") and "2 more blocks of words" in lib("S.wordsNote(7, 9, false)")
    assert "took out 1 section" in lib("S.wordsNote(7, 6, false)") and "take their words out" in lib("S.wordsNote(7, 6, false)")
    assert "rearranged the sections" in lib("S.wordsNote(7, 7, true)")
    assert lib("S.wordsNote(7, 7, false)") is None                              # nothing changed, nothing to say
