"""Keep this tune and words that do not fit (app.js: vocalNotes, lyricSyllables, tuneGap).

A tune sings one syllable a note.  Words with far more syllables than its notes are crammed onto them and come out
garbled; words with far fewer leave notes the singer fills with words of its own.  So past WORDS_PER_NOTE, or below
FEWEST_WORDS_PER_NOTE, the editor unticks Keep this tune and writes a new plan, unless ticked again."""
import json
import re
import subprocess
from pathlib import Path

APP_JS = (Path(__file__).resolve().parent.parent / "app" / "static" / "app.js").read_text(encoding="utf-8")


def function(name: str) -> str:
    start = APP_JS.index(f"function {name}(")
    depth, i = 0, APP_JS.index("{", start)
    while True:
        depth += {"{": 1, "}": -1}.get(APP_JS[i], 0)
        if depth == 0:
            return APP_JS[start:i + 1]
        i += 1


def run(expr: str):
    script = function("vocalNotes") + "\n" + function("lyricSyllables") + f"\nconsole.log(JSON.stringify({expr}));"
    return json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)


SCORE = """X:1
M:4/4
L:1/16
V: Vocal clef=treble
V: Ins clef=treble
K:C
% verse
V: Vocal
"C"c4 d4 e4 f4-|"G"f8 z4 g4|
V: Ins
C16|C16|
V: Vocal
"F"a4 !fermata!g4- g4 e4|"C"c16-|
V: Vocal
"C"c8 z8|
"""


def test_a_tied_note_is_one_note_held_and_other_voices_do_not_count():
    # c d e f g | a g e c : f held over the bar, g held, c held over two lines.
    assert run(f"vocalNotes({json.dumps(SCORE)})") == 9


def test_syllables_leave_out_section_tags():
    tagged, bare = run('[lyricSyllables("[Verse]\\nThe boardwalk lights are turning dim\\n[female vocal]\\nOne paper bag"),'
                       ' lyricSyllables("The boardwalk lights are turning dim\\nOne paper bag")]')
    assert tagged == bare > 0


def test_the_tune_is_kept_up_to_one_point_three_syllables_a_note():
    value = float(re.search(r"var WORDS_PER_NOTE = ([0-9.]+);", APP_JS).group(1))
    assert value == 1.3
    gap = function("tuneGap")
    assert "syllables > notes * WORDS_PER_NOTE" in gap


def gap_for(abc: str, lyrics: str):
    """tuneGap() for a score and words, with the editor's boxes stood in for and a score of one section."""
    values = re.search(r"var WORDS_PER_NOTE = [^\n]*\n(?:/\*[\s\S]*?\*/\n)?var FEWEST_WORDS_PER_NOTE = [^\n]*", APP_JS).group(0)
    script = "\n".join([
        values, function("vocalNotes"), function("lyricSyllables"), function("tuneGap"),
        "function tuneSectionGap() { return null; }",
        f"var boxes = {{abc: {{value: {json.dumps(abc)}}}, lyrics: {{value: {json.dumps(lyrics)}}}}};",
        "function $(id) { return boxes[id]; }",
        "console.log(JSON.stringify(tuneGap()));"])
    return json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)


def test_short_lines_on_a_long_tune_untick_keep_this_tune():
    tune = "X:1\nM:4/4\nL:1/8\nV: Vocal\nK:C\n% verse\nV: Vocal\n" + "|".join(["cdef gabc"] * 10) + "|\n"   # 80 notes
    fits = "\n".join(["The boardwalk lights are turning dim tonight"] * 8)                                 # 80 syllables
    short = "\n".join(["Dust in the light"] * 8)                                                          # 32
    assert gap_for(tune, fits) is None
    gap = gap_for(tune, short)
    assert "fills the rest with words of its own" in gap["keep"]
    assert "A new plan is written to fit them" in gap["fresh"]
