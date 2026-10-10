"""Tests for the visual Piano Roll / MIDI editor and ABC bidirectional conversion."""
import json
import subprocess
from pathlib import Path

from app import score

PIANOROLL_JS = Path(__file__).resolve().parent.parent / "app" / "static" / "pianoroll.js"


def run_node_script(js_code: str) -> dict:
    """Run a small JS snippet importing pianoroll.js and return parsed JSON result."""
    script = f"""
    const {{ parseAbc, serializeToAbc, abcNoteToMidi, midiToAbcNote, getKeyAccidentals, PianoRoll, extractLyricsSections, tokenizeLyricLines, matchScoreSectionToLyricSection, splitWordSyllables, playClick, playChord, chordToMidiPitches, alignLinesToNotes, assignLyricsToVocalNotes }} = require({json.dumps(str(PIANOROLL_JS))});
    {js_code}
    """
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def test_abc_to_piano_roll_roundtrip():
    """Verify that an ABC score converts to Piano Roll model and serializes back without loss."""
    raw_abc = (
        "X:1\n"
        "T:Melody Test\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=128\n"
        "V: Vocal clef=treble name=\"Vocal Melody\" snm=\"Vocal\"\n"
        "V: Ins clef=treble name=\"Ins Melody\" snm=\"Inst.\"\n"
        "K:C\n"
        "% intro\n"
        "V: Vocal\n"
        "\"C\"z4 c4 d4 e4 | \"G\"d8 \"C\"c8 | \"F\"a4 g4 f4 e4 | \"C\"c16 |\n"
        "V: Ins\n"
        "\"C\"C8 E8 | \"G\"G8 C8 | \"F\"F8 A8 | \"C\"C16 |\n"
    )

    js = f"""
    const input = {json.dumps(raw_abc)};
    const model = parseAbc(input);
    const output = serializeToAbc(model);
    console.log(JSON.stringify({{
        noteCount: model.notes.length,
        voices: model.voices,
        sections: model.sections,
        chords: model.chords,
        outputAbc: output
    }}));
    """
    data = run_node_script(js)

    assert data["noteCount"] == 17
    assert "Vocal" in data["voices"] and "Ins" in data["voices"]
    assert len(data["sections"]) >= 1
    assert len(data["chords"]) >= 4

    out_abc = data["outputAbc"]
    assert score.problems(out_abc) == []
    est_orig = score.estimate(raw_abc)
    est_out = score.estimate(out_abc)
    assert est_orig == est_out
    assert est_out["bars"] == 4
    assert est_out["bpm"] == 128


def test_piano_roll_note_editing():
    """Verify modifying note pitch, timing, duration, adding and deleting notes in Piano Roll."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "% intro\n"
        "V: Vocal\n"
        "\"C\"c4 d4 e4 f4 | \"G\"g16 | \"Am\"a8 e8 | \"F\"f16 |\n"
        "V: Ins\n"
        "z16 | z16 | z16 | z16 |\n"
    )

    js = f"""
    const input = {json.dumps(raw_abc)};
    const model = parseAbc(input);

    // 1. Move pitch of first note (C5/72 -> D5/74)
    model.notes[0].pitch = 74;

    // 2. Lengthen second note from 4 ticks to 6 ticks
    model.notes[1].durationTicks = 6;

    // 3. Shift third note later by 2 ticks
    model.notes[2].startTick += 2;
    model.notes[2].durationTicks = 2;

    // 4. Delete fourth note
    model.notes.splice(3, 1);

    // 5. Add a new note in Ins voice at bar 1 (tick 16)
    model.notes.push({{
        id: 999,
        voice: 'Ins',
        pitch: 60,
        startTick: 16,
        durationTicks: 8
    }});

    const output = serializeToAbc(model);
    console.log(JSON.stringify({{ outputAbc: output }}));
    """
    data = run_node_script(js)
    edited_abc = data["outputAbc"]

    assert score.problems(edited_abc) == []
    est = score.estimate(edited_abc)
    assert est["bars"] == 4
    assert est["bpm"] == 120


def test_piano_roll_tied_notes_across_bars():
    """Verify notes crossing measure boundaries are tied with '-' in ABC and re-merged on read."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=100\n"
        "K:C\n"
        "% intro\n"
        "V: Vocal\n"
        "\"C\"z16 | \"G\"z16 | \"F\"z16 | \"C\"z16 |\n"
        "V: Ins\n"
        "z16 | z16 | z16 | z16 |\n"
    )

    js = f"""
    const input = {json.dumps(raw_abc)};
    const model = parseAbc(input);

    // Create a note spanning across bar 0 into bar 1:
    // Starts at tick 12 of bar 0, lasts 20 ticks (ends at tick 16 of bar 1)
    model.notes.push({{
        id: 101,
        voice: 'Vocal',
        pitch: 65, // F4
        startTick: 12,
        durationTicks: 20
    }});

    const outAbc = serializeToAbc(model);
    const reparsed = parseAbc(outAbc);

    console.log(JSON.stringify({{
        outAbc: outAbc,
        reparsedNoteCount: reparsed.notes.length,
        firstNote: reparsed.notes[0]
    }}));
    """
    data = run_node_script(js)
    out_abc = data["outAbc"]

    assert "F4-" in out_abc or "f4-" in out_abc or "F" in out_abc
    assert score.problems(out_abc) == []

    # Verify re-parsing merges it back into one continuous 20-tick note
    assert data["reparsedNoteCount"] == 1
    assert data["firstNote"]["startTick"] == 12
    assert data["firstNote"]["durationTicks"] == 20
    assert data["firstNote"]["pitch"] == 65


def test_key_accidentals_flats_and_sharps():
    """Verify flat keys (F, Bb, Dm) and sharp keys (G, D, A) format accidentals cleanly."""
    js = """
    const inputF = `X:1\\nM:4/4\\nL:1/16\\nQ:1/4=110\\nK:F\\n% intro\\nV: Vocal\\n\"F\"z16|\"Bb\"z16|\"C\"z16|\"F\"z16|\\nV: Ins\\nz16|z16|z16|z16|\\n`;
    const modelF = parseAbc(inputF);
    // Add Bb4 (pitch 70)
    modelF.notes.push({ id: 1, voice: 'Vocal', pitch: 70, startTick: 0, durationTicks: 4 });
    const outF = serializeToAbc(modelF);

    const inputG = `X:1\\nM:4/4\\nL:1/16\\nQ:1/4=110\\nK:G\\n% intro\\nV: Vocal\\n\"G\"z16|\"D\"z16|\"C\"z16|\"G\"z16|\\nV: Ins\\nz16|z16|z16|z16|\\n`;
    const modelG = parseAbc(inputG);
    // Add F#4 (pitch 66)
    modelG.notes.push({ id: 2, voice: 'Vocal', pitch: 66, startTick: 0, durationTicks: 4 });
    const outG = serializeToAbc(modelG);

    console.log(JSON.stringify({ outF, outG }));
    """
    data = run_node_script(js)

    assert score.problems(data["outF"]) == []
    assert "_B" in data["outF"] or "_b" in data["outF"]

    assert score.problems(data["outG"]) == []
    assert "^F" in data["outG"] or "^f" in data["outG"]


def test_good_score_roundtrip_and_editing():
    """Verify that a real YuE2 plan (like GOOD in test_score) roundtrips with 0 problems."""
    good_abc = (
        'X:1\nT:\nM:4/4\nL:1/32\nQ:1/4=97\n'
        'V: Vocal clef=treble name="Vocal Melody" snm="Vocal"\n'
        'V: Ins clef=treble name="Ins Melody" snm="Inst."\nK:Dm\n'
        '% intro\nV: Vocal\n'
        '"Dm"d8f8a8z8|"Dm"z32|"Dm"z32|"Bbmaj7"z32|\n'
        'V: Ins\n'
        'Z|D2F2E2F2|D,4D,4|B,,4A,4|\n'
        'V: Vocal\n'
        '"Gm"z32|"Bm7b5"z32|"C7/Bb"z16"Bm7"z16|"Bm7"z32|\n'
    )
    assert score.problems(good_abc) == []
    est_orig = score.estimate(good_abc)

    js = f"""
    const input = {json.dumps(good_abc)};
    const model = parseAbc(input);
    const out = serializeToAbc(model);

    // Edit in piano roll: add a note in Vocal voice in bar 1
    model.notes.push({{
        id: 777,
        voice: 'Vocal',
        pitch: 62, // D4
        startTick: 32, // Bar 1 (since L:1/32 has 32 ticks per bar)
        durationTicks: 8
    }});
    const edited = serializeToAbc(model);

    console.log(JSON.stringify({{ out, edited }}));
    """
    data = run_node_script(js)

    assert score.problems(data["out"]) == []
    est_out = score.estimate(data["out"])
    assert est_out["bars"] == est_orig["bars"]
    assert est_out["bpm"] == est_orig["bpm"]

    assert score.problems(data["edited"]) == []
    est_edited = score.estimate(data["edited"])
    assert est_edited["bars"] == est_orig["bars"]


def test_piano_roll_transport_stepping():
    """Verify transport operations: stepNext, stepPrev (at boundary vs mid-bar), and rewindToStart."""
    js = """
    PianoRoll.model = parseAbc("X:1\\nM:4/4\\nL:1/16\\nQ:1/4=120\\nK:C\\n% intro\\nV: Vocal\\nz16|z16|z16|z16|\\n");
    PianoRoll.playheadTick = 0;

    // 1. Step forward 1 bar (16 ticks per bar in 4/4 with L:1/16)
    PianoRoll.stepNext();
    const tick1 = PianoRoll.playheadTick;

    // 2. Step forward another bar
    PianoRoll.stepNext();
    const tick2 = PianoRoll.playheadTick;

    // 3. Move playhead midway into bar 2 (tick 37)
    PianoRoll.seekTick(37);

    // 4. Stepping back while midway into bar 2 rewinds to the start of bar 2 (tick 32)
    PianoRoll.stepPrev();
    const tick3 = PianoRoll.playheadTick;

    // 5. Stepping back while at the start of bar 2 steps back to bar 1 (tick 16)
    PianoRoll.stepPrev();
    const tick4 = PianoRoll.playheadTick;

    // 6. Rewind to start returns to bar 0 (tick 0)
    PianoRoll.rewindToStart();
    const tick5 = PianoRoll.playheadTick;

    console.log(JSON.stringify({ tick1, tick2, tick3, tick4, tick5 }));
    """
    data = run_node_script(js)

    assert data["tick1"] == 16
    assert data["tick2"] == 32
    assert data["tick3"] == 32
    assert data["tick4"] == 16
    assert data["tick5"] == 0


def test_piano_roll_multi_selection_and_mass_deletion():
    """Verify multi-selection, select all, deselect, and mass deletion of selected notes."""
    js = """
    PianoRoll.model = parseAbc("X:1\\nM:4/4\\nL:1/16\\nQ:1/4=120\\nK:C\\n% intro\\nV: Vocal\\n\\"C\\"c4 d4 e4 f4 | \\"G\\"g16 |\\nV: Ins\\nz16|z16|\\n");
    PianoRoll.currentVoice = "Vocal";
    PianoRoll.clearSelection();

    const noteCountInitial = PianoRoll.model.notes.length; // 5 notes (c4, d4, e4, f4, g16)

    // 1. Select all in active voice
    PianoRoll.selectAll();
    const allSelectedCount = PianoRoll.selectedNoteIds.length;

    // 2. Clear selection
    PianoRoll.clearSelection();
    const hasSelAfterClear = PianoRoll.hasSelection();

    // 3. Select first 2 notes
    const id0 = PianoRoll.model.notes[0].id;
    const id1 = PianoRoll.model.notes[1].id;
    PianoRoll.selectNote(id0, false);
    PianoRoll.selectNote(id1, true); // add to selection
    const twoSelected = PianoRoll.selectedNoteIds.length;
    const is0Sel = PianoRoll.isNoteSelected(id0);
    const is1Sel = PianoRoll.isNoteSelected(id1);

    // 4. Delete selected notes (mass deletion)
    PianoRoll.deleteSelectedNotes();
    const countAfterDelete = PianoRoll.model.notes.length;
    const hasSelAfterDelete = PianoRoll.hasSelection();

    const outAbc = serializeToAbc(PianoRoll.model);

    console.log(JSON.stringify({
        noteCountInitial,
        allSelectedCount,
        hasSelAfterClear,
        twoSelected,
        is0Sel,
        is1Sel,
        countAfterDelete,
        hasSelAfterDelete,
        outAbc
    }));
    """
    data = run_node_script(js)

    assert data["noteCountInitial"] == 5
    assert data["allSelectedCount"] == 5
    assert data["hasSelAfterClear"] is False
    assert data["twoSelected"] == 2
    assert data["is0Sel"] is True
    assert data["is1Sel"] is True
    assert data["countAfterDelete"] == 3
    assert data["hasSelAfterDelete"] is False
    assert score.problems(data["outAbc"]) == []


def test_piano_roll_group_moving_and_gap_filling():
    """Verify selecting multiple notes and shifting them together across the timeline."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "% intro\n"
        "V: Vocal\n"
        "\"C\"c4 d4 e4 f4 | \"G\"g4 a4 b4 c'4 |\n"
        "V: Ins\n"
        "z16 | z16 |\n"
    )
    js = f"""
    PianoRoll.model = parseAbc({json.dumps(raw_abc)});
    PianoRoll.currentVoice = "Vocal";

    // Delete notes 2 and 3 (e4, f4 at ticks 8 and 12)
    const id2 = PianoRoll.model.notes[2].id;
    const id3 = PianoRoll.model.notes[3].id;
    PianoRoll.selectedNoteIds = [id2, id3];
    PianoRoll.deleteSelectedNotes();

    // Select all the notes to the right of the gap (g4, a4, b4, c'4)
    PianoRoll.selectedNoteIds = [
        PianoRoll.model.notes[2].id,
        PianoRoll.model.notes[3].id,
        PianoRoll.model.notes[4].id,
        PianoRoll.model.notes[5].id
    ];

    // Shift them left by 8 ticks to close the gap
    const shiftTicks = -8;
    for (let i = 0; i < PianoRoll.model.notes.length; i++) {{
        const n = PianoRoll.model.notes[i];
        if (PianoRoll.isNoteSelected(n.id)) {{
            n.startTick += shiftTicks;
        }}
    }}

    const newStartTicks = PianoRoll.model.notes.map(n => n.startTick);
    const outAbc = serializeToAbc(PianoRoll.model);

    console.log(JSON.stringify({{
        newStartTicks,
        outAbc
    }}));
    """
    data = run_node_script(js)

    assert data["newStartTicks"] == [0, 4, 8, 12, 16, 20]
    assert score.problems(data["outAbc"]) == []


def test_abc_lyrics_parsing_and_serialization_roundtrip():
    """Verify that ABC with w: lyric lines parses syllables onto Vocal notes and roundtrips cleanly."""
    raw_abc = (
        "X:1\n"
        "T:Lyrics Test\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "% verse\n"
        "V: Vocal\n"
        "\"C\"C4 D4 E4 G4 | \"G\"G4 F4 E4 D4 | \"Am\"A4 G4 E4 D4 | \"F\"C16 |\n"
        "w: Hel- lo beau- ti- | ful morn- ing light | shin- ing so bright | _ |\n"
        "V: Ins\n"
        "\"C\"C16 | \"G\"G16 | \"Am\"A16 | \"F\"F16 |\n"
    )
    js = f"""
    const model = parseAbc({json.dumps(raw_abc)});
    const vocalNotes = model.notes.filter(n => n.voice === 'Vocal');
    const lyrics = vocalNotes.map(n => n.lyric);
    const outputAbc = serializeToAbc(model);
    const reparsed = parseAbc(outputAbc);
    const reparsedLyrics = reparsed.notes.filter(n => n.voice === 'Vocal').map(n => n.lyric);

    console.log(JSON.stringify({{
        lyrics,
        reparsedLyrics,
        outputAbc
    }}));
    """
    data = run_node_script(js)

    expected = ["Hel-", "lo", "beau-", "ti-", "ful", "morn-", "ing", "light", "shin-", "ing", "so", "bright", ""]
    assert data["lyrics"] == expected
    assert data["reparsedLyrics"] == expected
    assert "w: Hel- lo beau- ti- | ful morn- ing light | shin- ing so bright |" in data["outputAbc"]
    assert score.problems(data["outputAbc"]) == []


def test_piano_roll_edit_lyrics_and_distribution():
    """Verify editLyricForNote updates single notes or distributes multiple words across notes."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "% verse\n"
        "V: Vocal\n"
        "\"C\"C4 D4 E4 G4 | \"G\"G4 F4 E4 D4 |\n"
        "V: Ins\n"
        "z16 | z16 |\n"
    )
    js = f"""
    PianoRoll.model = parseAbc({json.dumps(raw_abc)});
    PianoRoll.currentVoice = "Vocal";
    const vocalNotes = PianoRoll.model.notes.filter(n => n.voice === 'Vocal');

    // 1. Single syllable edit
    global.window = {{ prompt: () => "Sing" }};
    PianoRoll.editLyricForNote(vocalNotes[0].id);

    // 2. Multi-syllable distribution starting at note 1
    global.window = {{ prompt: () => "to the morn- ing sun" }};
    PianoRoll.editLyricForNote(vocalNotes[1].id);

    const resultingLyrics = PianoRoll.model.notes.filter(n => n.voice === 'Vocal').map(n => n.lyric);
    const outAbc = serializeToAbc(PianoRoll.model);

    console.log(JSON.stringify({{
        resultingLyrics,
        outAbc
    }}));
    """
    data = run_node_script(js)

    assert data["resultingLyrics"][:6] == ["Sing", "to", "the", "morn-", "ing", "sun"]
    assert "w: Sing to the morn- | ing sun |" in data["outAbc"]
    assert score.problems(data["outAbc"]) == []


def test_piano_roll_match_song_lyrics():
    """Verify auto-matching song lyrics text to vocal melody notes section by section."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "% verse\n"
        "V: Vocal\n"
        "\"C\"C4 D4 E4 G4 | \"G\"G4 F4 E4 D4 |\n"
        "V: Ins\n"
        "z16 | z16 |\n"
        "% chorus\n"
        "V: Vocal\n"
        "\"F\"A4 B4 c4 d4 | \"C\"e16 |\n"
        "V: Ins\n"
        "z16 | z16 |\n"
    )
    song_lyrics = (
        "[Verse]\n"
        "Walk-ing down the lone-ly ave-nue\n\n"
        "[Chorus]\n"
        "We are fly-ing high\n"
    )
    js = f"""
    PianoRoll.model = parseAbc({json.dumps(raw_abc)});
    PianoRoll.matchSongLyrics({json.dumps(song_lyrics)});

    const verseNotes = PianoRoll.model.notes.filter(n => n.voice === 'Vocal' && n.startTick < 32);
    const chorusNotes = PianoRoll.model.notes.filter(n => n.voice === 'Vocal' && n.startTick >= 32);
    const outAbc = serializeToAbc(PianoRoll.model);

    console.log(JSON.stringify({{
        verseLyrics: verseNotes.map(n => n.lyric),
        chorusLyrics: chorusNotes.map(n => n.lyric),
        outAbc
    }}));
    """
    data = run_node_script(js)

    assert data["verseLyrics"][:6] == ["Walk-", "ing", "down", "the", "lone-", "ly"]
    assert data["chorusLyrics"][:4] == ["We", "are", "fly-", "ing"]
    assert "w: Walk- ing down the | lone- ly ave- nue |" in data["outAbc"]
    assert "w: We are fly- ing | high |" in data["outAbc"]
    assert score.problems(data["outAbc"]) == []


def test_lyrics_move_and_delete_with_notes():
    """Verify moving or deleting notes updates lyric alignment and ABC serialization."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "% verse\n"
        "V: Vocal\n"
        "\"C\"C4 D4 E4 G4 | \"G\"G4 F4 E4 D4 |\n"
        "w: Hel- lo beau- ti- | ful morn- ing light |\n"
        "V: Ins\n"
        "z16 | z16 |\n"
    )
    js = f"""
    PianoRoll.model = parseAbc({json.dumps(raw_abc)});
    PianoRoll.currentVoice = "Vocal";

    // Delete note with lyric 'beau-' (3rd note, index 2)
    const delId = PianoRoll.model.notes[2].id;
    PianoRoll.deleteNote(delId);

    // Move first note from tick 0 to tick 2
    PianoRoll.model.notes[0].startTick = 2;

    const outAbc = serializeToAbc(PianoRoll.model);
    const reparsed = parseAbc(outAbc);
    const remainingLyrics = reparsed.notes.filter(n => n.voice === 'Vocal').map(n => n.lyric);

    console.log(JSON.stringify({{
        remainingLyrics,
        outAbc
    }}));
    """
    data = run_node_script(js)

    assert "beau-" not in data["remainingLyrics"]
    assert data["remainingLyrics"] == ["Hel-", "lo", "ti-", "ful", "morn-", "ing", "light"]
    assert score.problems(data["outAbc"]) == []


def test_syllable_splitting():
    """Verify rule-based syllable hyphenation splits unhyphenated English words."""
    js = """
    console.log(JSON.stringify({
        walking: splitWordSyllables("walking"),
        avenue: splitWordSyllables("avenue"),
        tonight: splitWordSyllables("tonight"),
        manual: splitWordSyllables("walk-ing"),
        dont: splitWordSyllables("don't"),
        waited: splitWordSyllables("waited"),
        walked: splitWordSyllables("walked")
    }));
    """
    data = run_node_script(js)
    assert data["walking"] == ["wal-", "king"]
    assert data["avenue"] == ["a-", "ve-", "nue"]
    assert data["tonight"] == ["to-", "night"]
    assert data["manual"] == ["walk-", "ing"]
    assert data["dont"] == ["don't"]
    assert data["waited"] == ["wai-", "ted"]
    assert data["walked"] == ["walked"]


def test_unhyphenated_lyrics_matching_expands_to_vocal_notes():
    """Verify plain unhyphenated text splits across vocal notes without leaving large gaps."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/8\n"
        "Q:1/4=120\n"
        "K:C\n"
        "V: Vocal\n"
        "C D E F | G A B c |\n"
    )
    song_lyrics = "Walking down the avenue tonight"
    js = f"""
    PianoRoll.model = parseAbc({json.dumps(raw_abc)});
    PianoRoll.matchSongLyrics({json.dumps(song_lyrics)});
    const assigned = PianoRoll.model.notes.filter(n => n.voice === 'Vocal').map(n => n.lyric);
    console.log(JSON.stringify({{ assigned }}));
    """
    data = run_node_script(js)
    assigned = data["assigned"]
    # 8 vocal notes should all receive syllables
    assert len(assigned) == 8
    assert assigned[0] == "Wal-"
    assert assigned[1] == "king"
    assert assigned[2] == "down"
    assert assigned[3] == "the"
    assert assigned[4] == "a-"
    assert assigned[5] == "ve-"
    assert assigned[6] == "nue"
    assert assigned[7] == "to-"


def test_lyrics_footer_and_dancing_ball_dom_rendering():
    """Verify lyrics footer DOM items and real-time dancing ball/illumination updates."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/8\n"
        "Q:1/4=120\n"
        "K:C\n"
        "V: Vocal\n"
        "C2 D2 E2 F2 |\n"
        "w: Hel- lo world now |\n"
    )
    js = f"""
    // Minimal DOM environment for node
    class MockClassList {{
      constructor() {{ this.classes = new Set(); }}
      add(c) {{ this.classes.add(c); }}
      remove(c) {{ this.classes.delete(c); }}
      contains(c) {{ return this.classes.has(c); }}
    }}
    class MockElement {{
      constructor(id = '', tag = 'div') {{
        this.id = id;
        this.tagName = tag;
        this.classList = new MockClassList();
        this.style = {{}};
        this.dataset = {{}};
        this.children = [];
        this.innerHTML = '';
        this.textContent = '';
      }}
      addEventListener() {{}}
      removeEventListener() {{}}
      getBoundingClientRect() {{ return {{ left: 0, top: 0, width: 400, height: 44 }}; }}
      querySelector() {{ return null; }}
      querySelectorAll() {{ return []; }}
    }}

    const elements = {{
      'roll-lyrics-footer': new MockElement('roll-lyrics-footer'),
      'roll-lyrics-strip': new MockElement('roll-lyrics-strip'),
      'roll-lyrics-items': new MockElement('roll-lyrics-items'),
      'roll-dancing-ball': new MockElement('roll-dancing-ball'),
      'roll-playhead': new MockElement('roll-playhead'),
      'roll-ruler-playhead': new MockElement('roll-ruler-playhead'),
      'roll-time': new MockElement('roll-time'),
      'roll-grid-scroll': new MockElement('roll-grid-scroll'),
    }};
    elements['roll-dancing-ball'].classList.add('hidden');

    global.document = {{
      getElementById: (id) => elements[id] || null,
      querySelector: (sel) => {{
        if (sel === '.roll-lyric-item.illuminated') return null;
        if (sel === '.roll-note.singing-now') return null;
        return null;
      }},
      querySelectorAll: () => []
    }};

    PianoRoll.model = parseAbc({json.dumps(raw_abc)});
    PianoRoll.renderLyricsFooter();

    const footerHtml = elements['roll-lyrics-items'].innerHTML;
    const hasItems = footerHtml.includes('roll-lyric-item') && footerHtml.includes('Hel-') && footerHtml.includes('world');

    // Test playhead at tick 1.5 during playback
    PianoRoll.isPlaying = true;
    PianoRoll.updatePlayhead(1.5);
    const ballHiddenDuringSinging = elements['roll-dancing-ball'].classList.contains('hidden');
    const ballTransform = elements['roll-dancing-ball'].style.transform;

    // Test stop()
    PianoRoll.stop();
    const ballHiddenAfterStop = elements['roll-dancing-ball'].classList.contains('hidden');

    console.log(JSON.stringify({{
      hasItems,
      ballHiddenDuringSinging,
      ballTransform,
      ballHiddenAfterStop
    }}));
    """
    data = run_node_script(js)
    assert data["hasItems"] is True
    assert data["ballHiddenDuringSinging"] is False
    assert "translate3d" in data["ballTransform"]
    assert data["ballHiddenAfterStop"] is True


def test_metronome_click_track():
    """Verify metronome toggle, default enabled state, and audio click synthesis."""
    js = """
    // Mock Web Audio Context
    class MockAudioParam {
      constructor() { this.value = 0; }
      setValueAtTime(v, t) { this.value = v; }
      exponentialRampToValueAtTime(v, t) { this.value = v; }
    }
    class MockNode {
      constructor() {
        this.frequency = new MockAudioParam();
        this.gain = new MockAudioParam();
      }
      connect() {}
      disconnect() {}
      start() {}
      stop() {}
    }
    class MockAudioContext {
      constructor() {
        this.currentTime = 1.0;
        this.destination = new MockNode();
        this.state = 'running';
      }
      createOscillator() { return new MockNode(); }
      createGain() { return new MockNode(); }
      createBiquadFilter() { return new MockNode(); }
    }

    global.window = {
      AudioContext: MockAudioContext
    };

    const initialEnabled = PianoRoll.metronomeEnabled;
    const toggledOff = PianoRoll.toggleMetronome();
    const toggledOn = PianoRoll.toggleMetronome();

    // Verify click synthesis works without error for both downbeat and regular beat
    const downbeatOsc = playClick(true, 1.0);
    const beatOsc = playClick(false, 1.5);

    console.log(JSON.stringify({
      initialEnabled,
      toggledOff,
      toggledOn,
      hasDownbeat: Boolean(downbeatOsc),
      hasBeat: Boolean(beatOsc)
    }));
    """
    data = run_node_script(js)
    assert data["initialEnabled"] is True
    assert data["toggledOff"] is False
    assert data["toggledOn"] is True
    assert data["hasDownbeat"] is True
    assert data["hasBeat"] is True


def test_chord_to_midi_pitches():
    """Verify chord name parsing into root bass and triad/seventh MIDI pitches."""
    js = """
    console.log(JSON.stringify({
        c: chordToMidiPitches('C'),
        am: chordToMidiPitches('Am'),
        g: chordToMidiPitches('G'),
        gb: chordToMidiPitches('G/B'),
        fmaj7: chordToMidiPitches('Fmaj7'),
        dm7: chordToMidiPitches('Dm7'),
        e7: chordToMidiPitches('E7'),
        bb: chordToMidiPitches('Bb'),
        csus4: chordToMidiPitches('Csus4'),
        bdim: chordToMidiPitches('Bdim')
    }));
    """
    data = run_node_script(js)
    # C major: bass C2 (36), C3 (48), E3 (52), G3 (55)
    assert data["c"] == [36, 48, 52, 55]
    # Am: bass A2 (45), A3 (57), C4 (60), E4 (64)
    assert data["am"] == [45, 57, 60, 64]
    # G/B slash chord: slash bass B2 (47), triad G3 (55), B3 (59), D4 (62)
    assert data["gb"] == [47, 55, 59, 62]
    # Fmaj7: bass F2 (41), F3 (53), A3 (57), C4 (60), E4 (64)
    assert data["fmaj7"] == [41, 53, 57, 60, 64]
    # Dm7: bass D2 (38), D3 (50), F3 (53), A3 (57), C4 (60)
    assert data["dm7"] == [38, 50, 53, 57, 60]


def test_chord_accompaniment_playback_and_toggle():
    """Verify chords playback toggle, default enabled state, and polyphonic audio synthesis."""
    js = """
    class MockAudioParam {
      constructor() { this.value = 0; }
      setValueAtTime(v, t) { this.value = v; }
      exponentialRampToValueAtTime(v, t) { this.value = v; }
    }
    class MockNode {
      constructor() {
        this.frequency = new MockAudioParam();
        this.gain = new MockAudioParam();
      }
      connect() {}
      disconnect() {}
      start() {}
      stop() {}
    }
    class MockAudioContext {
      constructor() {
        this.currentTime = 1.0;
        this.destination = new MockNode();
        this.state = 'running';
      }
      createOscillator() { return new MockNode(); }
      createGain() { return new MockNode(); }
      createBiquadFilter() { return new MockNode(); }
    }

    global.window = {
      AudioContext: MockAudioContext
    };

    const initialChords = PianoRoll.chordsEnabled;
    const toggledOff = PianoRoll.toggleChords();
    const toggledOn = PianoRoll.toggleChords();

    // Verify playChord creates multiple polyphonic oscillators for chord pitches
    const oscs = playChord([36, 48, 52, 55], 1.0, 1.0);

    console.log(JSON.stringify({
      initialChords,
      toggledOff,
      toggledOn,
      oscCount: oscs.length
    }));
    """
    data = run_node_script(js)
    assert data["initialChords"] is True
    assert data["toggledOff"] is False
    assert data["toggledOn"] is True
    assert data["oscCount"] == 4


def test_phrase_aware_lyrics_alignment_across_rests():
    """Verify lyrics do not spill across musical rests into subsequent phrases."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "% verse\n"
        "V: Vocal\n"
        "\"C\"C4 D4 E4 G4 | \"C\"G16 | \"G\"z16 | \"F\"F4 E4 D4 C4 |\n"
        "V: Ins\n"
        "z16 | z16 | z16 | z16 |\n"
    )
    # Line 1 has 4 syllables, Phrase 1 has 5 notes (bar 0: 4 notes, bar 1: 1 whole note)
    # Bar 2 is 16 ticks of rest
    # Line 2 has 4 syllables, Phrase 2 has 4 notes in bar 3
    song_lyrics = (
        "[verse]\n"
        "Walk down the lane\n"
        "Look at the moon\n"
    )

    js = f"""
    PianoRoll.model = parseAbc({json.dumps(raw_abc)});
    PianoRoll.matchSongLyrics({json.dumps(song_lyrics)});

    const vocalNotes = PianoRoll.model.notes.filter(n => n.voice === 'Vocal');
    vocalNotes.sort((a, b) => a.startTick - b.startTick);

    const outAbc = serializeToAbc(PianoRoll.model);

    console.log(JSON.stringify({{
        noteLyrics: vocalNotes.map(n => ({{ tick: n.startTick, lyric: n.lyric || '' }})),
        outAbc
    }}));
    """
    data = run_node_script(js)
    lyrics_by_tick = {item["tick"]: item["lyric"] for item in data["noteLyrics"]}

    # Line 1 assigned to phrase 1
    assert lyrics_by_tick[0] == "Walk"
    assert lyrics_by_tick[4] == "down"
    assert lyrics_by_tick[8] == "the"
    assert lyrics_by_tick[12] == "lane"
    # Held note in bar 1 does NOT take the first word of Line 2!
    assert lyrics_by_tick[16] == ""

    # Line 2 strictly starts after the 16-tick rest in bar 2 (at tick 48 in bar 3)
    assert lyrics_by_tick[48] == "Look"
    assert lyrics_by_tick[52] == "at"
    assert lyrics_by_tick[56] == "the"
    assert lyrics_by_tick[60] == "moon"

    assert score.problems(data["outAbc"]) == []


def test_fill_gaps_from_chords():
    """Verify fillGapsFromChords populates empty bars in Ins voice with accompaniment matching chords."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "% verse\n"
        "V: Vocal\n"
        "\"C\"C4 D4 E4 G4 | \"G\"z16 | \"Am\"z16 | \"F\"F4 E4 D4 C4 |\n"
        "V: Ins\n"
        "\"C\"z16 | \"G\"z16 | \"Am\"z16 | \"F\"z16 |\n"
    )

    js = f"""
    PianoRoll.model = parseAbc({json.dumps(raw_abc)});
    const insNotesBefore = PianoRoll.model.notes.filter(n => n.voice === 'Ins').length;

    const filledCount = PianoRoll.fillGapsFromChords('Ins');
    const insNotesAfter = PianoRoll.model.notes.filter(n => n.voice === 'Ins').length;
    const outAbc = serializeToAbc(PianoRoll.model);

    console.log(JSON.stringify({{
        insNotesBefore,
        filledCount,
        insNotesAfter,
        outAbc
    }}));
    """
    data = run_node_script(js)

    assert data["insNotesBefore"] == 0
    assert data["filledCount"] == 4
    assert data["insNotesAfter"] == 16  # 4 notes per bar across 4 bars
    assert score.problems(data["outAbc"]) == []
    est = score.estimate(data["outAbc"])
    assert est["bars"] == 4


def test_compact_empty_bars():
    """Verify compactEmptyBars removes completely empty measures and shifts later notes and chords."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "% verse\n"
        "V: Vocal\n"
        "\"C\"C4 D4 E4 G4 | \"G\"z16 | \"Am\"z16 | \"F\"F4 E4 D4 C4 |\n"
        "V: Ins\n"
        "\"C\"z16 | \"G\"z16 | \"Am\"z16 | \"F\"z16 |\n"
    )

    js = f"""
    PianoRoll.model = parseAbc({json.dumps(raw_abc)});
    const removedCount = PianoRoll.compactEmptyBars();
    const outAbc = serializeToAbc(PianoRoll.model);

    // After compacting 2 empty bars (bars 1 and 2), the F chord and phrase 2 should be at bar 1 (tick 16)
    const phrase2Notes = PianoRoll.model.notes.filter(n => n.voice === 'Vocal' && n.pitch === 65); // F4
    const fChord = PianoRoll.model.chords.find(c => c.name === 'F');

    console.log(JSON.stringify({{
        removedCount,
        phrase2StartTick: phrase2Notes.length ? phrase2Notes[0].startTick : -1,
        fChordBarIndex: fChord ? fChord.barIndex : -1,
        outAbc
    }}));
    """
    data = run_node_script(js)

    assert data["removedCount"] == 2
    assert data["phrase2StartTick"] == 16  # Shifted from tick 48 to tick 16
    assert data["fChordBarIndex"] == 1    # Shifted from bar 3 to bar 1
    assert score.problems(data["outAbc"]) == []


def test_meter_and_unit_length_header_order_independent():
    """Verify ticksPerBar is correctly calculated regardless of M: and L: header ordering."""
    # M: before L:
    abc_m_before_l = "X:1\nM:4/4\nL:1/32\nQ:1/4=166\nK:C\n% intro\nV: Vocal\nz32|\n"
    # L: before M:
    abc_l_before_m = "X:1\nL:1/32\nM:4/4\nQ:1/4=166\nK:C\n% intro\nV: Vocal\nz32|\n"

    js = f"""
    const m1 = parseAbc({json.dumps(abc_m_before_l)});
    const m2 = parseAbc({json.dumps(abc_l_before_m)});
    console.log(JSON.stringify({{
        m1Ticks: m1.ticksPerBar,
        m1Unit: m1.unitLength,
        m1Bpm: m1.bpm,
        m1Meter: m1.meter,
        m2Ticks: m2.ticksPerBar,
        m2Unit: m2.unitLength
    }}));
    """
    data = run_node_script(js)
    assert data["m1Ticks"] == 32
    assert data["m1Unit"] == 32
    assert data["m1Bpm"] == 166
    assert data["m1Meter"] == "4/4"
    assert data["m2Ticks"] == 32
    assert data["m2Unit"] == 32


def test_multimeasure_rest_bar_index_alignment():
    """Verify multimeasure rests Z| or Z2| do not insert phantom bars that desync voices."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "K:C\n"
        "% intro\n"
        "V: Vocal\n"
        "z16|z16|z16|z16|\n"
        "V: Ins\n"
        "z16|Z|z16|z16|\n"
        "% verse\n"
        "V: Vocal\n"
        "c4 d4 e4 f4|g16|z16|z16|\n"
        "V: Ins\n"
        "Z2|z16|z16|\n"
    )
    js = f"""
    const model = parseAbc({json.dumps(raw_abc)});
    const verseSec = model.sections.find(s => s.text.includes("verse"));
    const vocalNotes = model.notes.filter(n => n.voice === 'Vocal');
    console.log(JSON.stringify({{
        verseBar: verseSec ? verseSec.barIndex : -1,
        firstNoteStartTick: vocalNotes.length ? vocalNotes[0].startTick : -1
    }}));
    """
    data = run_node_script(js)
    # Intro is 4 bars (bars 0..3), so verse must start at bar 4 (tick 64)
    assert data["verseBar"] == 4
    assert data["firstNoteStartTick"] == 64


def test_lyrics_matching_with_32_tick_bars_and_tied_notes():
    """Verify lyrics matching on score with L:1/32, tied notes across bars, and multi-sections."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/32\n"
        "Q:1/4=166\n"
        "K:E\n"
        "% intro\n"
        "V: Vocal\n"
        "z32|z32|\n"
        "V: Ins\n"
        "Z2|\n"
        "% verse\n"
        "V: Vocal\n"
        "\"E\"z8B8B8B4B4-|\"G\"B8B8=d8c8|\"A\"A8z24|\"A\"z32|\n"
        "V: Ins\n"
        "E8z24|Z|z12A4z16|A8z4A8A4A4A4|\n"
        "% chorus\n"
        "V: Vocal\n"
        "\"E\"z8B8B8B4B4-|\"G\"B8B8=d8c8|\"A\"A16z16|\"A\"z32|\n"
        "V: Ins\n"
        "Z4|\n"
    )
    song_lyrics = (
        "[Verse]\n"
        "We bought the boy a na-vy suit\n\n"
        "[Chorus]\n"
        "We mapped the route for Ni-gel's feet\n"
    )
    js = f"""
    PianoRoll.model = parseAbc({json.dumps(raw_abc)});
    PianoRoll.matchSongLyrics({json.dumps(song_lyrics)});
    const vocalNotes = PianoRoll.model.notes.filter(n => n.voice === 'Vocal');
    vocalNotes.sort((a,b) => a.startTick - b.startTick);
    
    // Check start ticks strictly monotonic
    let monotonic = true;
    for (let i = 1; i < vocalNotes.length; i++) {{
        if (vocalNotes[i].startTick <= vocalNotes[i-1].startTick) {{
            monotonic = false;
        }}
    }}

    const matched = vocalNotes.filter(n => n.lyric);
    console.log(JSON.stringify({{
        ticksPerBar: PianoRoll.model.ticksPerBar,
        vocalNotesCount: vocalNotes.length,
        isMonotonic: monotonic,
        lyrics: matched.map(n => n.lyric),
        startTicks: matched.map(n => n.startTick)
    }}));
    """
    data = run_node_script(js)
    assert data["ticksPerBar"] == 32
    assert data["isMonotonic"] is True
    # Verse words: We (bar 2), bought, the, boy, a (bar 3), na-, vy, suit
    assert data["lyrics"][:8] == ["We", "bought", "the", "boy", "a", "na-", "vy", "suit"]
    # Chorus words: We, mapped, the, route, for, Ni-, gel's, feet
    assert data["lyrics"][8:16] == ["We", "mapped", "the", "route", "for", "Ni-", "gel's", "feet"]


def test_piano_roll_vertical_bar_markers_rendering():
    """Verify vertical bar markers and bar numbers are rendered across the grid, ruler, and lyrics footer."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "% intro\n"
        "V: Vocal\n"
        "c16 | d16 | e16 | f16 |\n"
        "w: one | two | three | four |\n"
    )
    js = f"""
    class MockClassList {{
      constructor() {{ this.classes = new Set(); }}
      add(c) {{ this.classes.add(c); }}
      remove(c) {{ this.classes.delete(c); }}
      contains(c) {{ return this.classes.has(c); }}
    }}
    class MockElement {{
      constructor(id = '', tag = 'div') {{
        this.id = id;
        this.tagName = tag;
        this.classList = new MockClassList();
        this.style = {{}};
        this.dataset = {{}};
        this.innerHTML = '';
      }}
      addEventListener() {{}}
      removeEventListener() {{}}
      getBoundingClientRect() {{ return {{ left: 0, top: 0, width: 400, height: 44 }}; }}
      querySelector() {{ return null; }}
      querySelectorAll() {{ return []; }}
    }}

    const elements = {{
      'roll-grid': new MockElement('roll-grid'),
      'roll-grid-lines': new MockElement('roll-grid-lines'),
      'roll-notes-layer': new MockElement('roll-notes-layer'),
      'roll-ruler': new MockElement('roll-ruler'),
      'roll-chords-track': new MockElement('roll-chords-track'),
      'roll-lyrics-footer': new MockElement('roll-lyrics-footer'),
      'roll-lyrics-strip': new MockElement('roll-lyrics-strip'),
      'roll-lyrics-items': new MockElement('roll-lyrics-items'),
      'roll-meta': new MockElement('roll-meta'),
      'roll-keys': new MockElement('roll-keys')
    }};

    global.document = {{
      getElementById: (id) => elements[id] || null,
      querySelector: () => null,
      querySelectorAll: () => []
    }};

    PianoRoll.model = parseAbc({json.dumps(raw_abc)});
    PianoRoll.renderGrid();
    PianoRoll.renderTimeline();
    PianoRoll.renderLyricsFooter();

    const gridLinesHtml = elements['roll-grid-lines'].innerHTML;
    const rulerHtml = elements['roll-ruler'].innerHTML;
    const lyricsHtml = elements['roll-lyrics-items'].innerHTML;

    // Check bar lines in grid
    const hasBar1Line = gridLinesHtml.includes('bar-line') && gridLinesHtml.includes('data-bar="1"');
    const hasBar2Line = gridLinesHtml.includes('bar-line') && gridLinesHtml.includes('data-bar="2"');
    const hasBarTags = gridLinesHtml.includes('roll-bar-line-tag');

    // Check bar markers in ruler
    const hasRulerBars = rulerHtml.includes('roll-bar-marker') && rulerHtml.includes('roll-bar-num');

    // Check bar markers in lyrics footer
    const hasLyricBarMarkers = lyricsHtml.includes('roll-lyric-bar-marker') && lyricsHtml.includes('roll-lyric-bar-num');

    console.log(JSON.stringify({{
      hasBar1Line,
      hasBar2Line,
      hasBarTags,
      hasRulerBars,
      hasLyricBarMarkers
    }}));
    """
    data = run_node_script(js)
    assert data["hasBar1Line"] is True
    assert data["hasBar2Line"] is True
    assert data["hasBarTags"] is True
    assert data["hasRulerBars"] is True
    assert data["hasLyricBarMarkers"] is True


def test_piano_roll_unified_multi_voice_selection_and_drag_left():
    """Verify selecting notes across both Vocal and Ins voices and moving them left in lockstep."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "% intro\n"
        "V: Vocal\n"
        "\"C\"c4 d4 e4 f4 | z16 | \"G\"g4 a4 b4 c'4 | \"C\"c'16 |\n"
        "w: Hel- lo to you | | sing with the band | yes |\n"
        "V: Ins\n"
        "\"C\"C8 E8 | z16 | \"G\"G8 B8 | \"C\"C16 |\n"
    )

    js = f"""
    const input = {json.dumps(raw_abc)};
    PianoRoll.model = parseAbc(input);
    PianoRoll.tickWidth = 10;
    PianoRoll.rowHeight = 16;
    PianoRoll.playheadTick = 32; // at bar 2

    // 1. selectAll selects ALL notes across both Vocal and Ins
    PianoRoll.selectAll();
    const totalNoteCount = PianoRoll.model.notes.length; // 4 vocal (bar 0) + 4 vocal (bar 2) + 1 vocal (bar 3) + 2 ins (bar 0) + 2 ins (bar 2) + 1 ins (bar 3) = 14
    const selectAllCount = PianoRoll.selectedNoteIds.length;
    const vocalSelected = PianoRoll.model.notes.filter(n => PianoRoll.isNoteSelected(n.id) && n.voice === 'Vocal').length;
    const insSelected = PianoRoll.model.notes.filter(n => PianoRoll.isNoteSelected(n.id) && n.voice === 'Ins').length;

    // 2. selectRightOfPlayhead (from tick 32 onwards)
    PianoRoll.selectRightOfPlayhead();
    const rightSelectedIds = PianoRoll.selectedNoteIds.slice();
    const rightVocalCount = PianoRoll.model.notes.filter(n => PianoRoll.isNoteSelected(n.id) && n.voice === 'Vocal').length;
    const rightInsCount = PianoRoll.model.notes.filter(n => PianoRoll.isNoteSelected(n.id) && n.voice === 'Ins').length;
    // Earliest startTick among right-selected notes should be >= 32
    const minRightTick = Math.min(...PianoRoll.model.notes.filter(n => PianoRoll.isNoteSelected(n.id)).map(n => n.startTick));

    // 3. Move selected notes left by 1 bar (16 ticks) to close the silent gap at bar 1 (ticks 16-31)
    const prevVocalTicks = PianoRoll.model.notes.filter(n => PianoRoll.isNoteSelected(n.id) && n.voice === 'Vocal').map(n => n.startTick);
    PianoRoll.moveSelectedNotes(-16, 0);
    const newVocalTicks = PianoRoll.model.notes.filter(n => PianoRoll.isNoteSelected(n.id) && n.voice === 'Vocal').map(n => n.startTick);

    // 4. Marquee box selection: select box covering bar 1 (tick 16 to 32)
    // In our coordinate space: x = tick * 10 -> x from 160 to 320
    PianoRoll.clearSelection();
    PianoRoll.selectNotesInBox(150, 0, 180, 2000, false);
    const boxVocalCount = PianoRoll.model.notes.filter(n => PianoRoll.isNoteSelected(n.id) && n.voice === 'Vocal').length;
    const boxInsCount = PianoRoll.model.notes.filter(n => PianoRoll.isNoteSelected(n.id) && n.voice === 'Ins').length;

    const outAbc = serializeToAbc(PianoRoll.model);
    const reparsed = parseAbc(outAbc);
    const reparsedVocalMoved = reparsed.notes.filter(n => n.voice === 'Vocal' && n.startTick >= 16 && n.startTick < 32);
    const reparsedInsMoved = reparsed.notes.filter(n => n.voice === 'Ins' && n.startTick >= 16 && n.startTick < 32);

    console.log(JSON.stringify({{
        totalNoteCount,
        selectAllCount,
        vocalSelected,
        insSelected,
        rightVocalCount,
        rightInsCount,
        minRightTick,
        prevVocalTicks,
        newVocalTicks,
        boxVocalCount,
        boxInsCount,
        reparsedVocalCount: reparsedVocalMoved.length,
        reparsedInsCount: reparsedInsMoved.length,
        lyricsMoved: reparsedVocalMoved.map(n => n.lyric),
        outAbc
    }}));
    """
    data = run_node_script(js)

    # 1. selectAll includes ALL notes
    assert data["selectAllCount"] == data["totalNoteCount"]
    assert data["vocalSelected"] > 0
    assert data["insSelected"] > 0

    # 2. selectRightOfPlayhead includes both voices starting from tick 32
    assert data["rightVocalCount"] > 0
    assert data["rightInsCount"] > 0
    assert data["minRightTick"] >= 32

    # 3. moving left by 16 ticks shifted all selected notes by exactly 16 ticks
    for prev_t, new_t in zip(data["prevVocalTicks"], data["newVocalTicks"]):
        assert new_t == prev_t - 16

    # 4. Box selection captured both vocal and instrument notes in the moved bar
    assert data["boxVocalCount"] > 0
    assert data["boxInsCount"] > 0

    # 5. Serialized ABC is valid and preserves moved notes and lyrics
    assert data["reparsedVocalCount"] == 4
    assert data["reparsedInsCount"] == 2
    assert data["lyricsMoved"] == ["sing", "with", "the", "band"]
    assert score.problems(data["outAbc"]) == []


def test_piano_roll_unified_multi_voice_deletion():
    """Verify deleting selected notes removes notes across both Vocal and Ins in unison."""
    raw_abc = (
        "X:1\n"
        "M:4/4\n"
        "L:1/16\n"
        "Q:1/4=120\n"
        "K:C\n"
        "V: Vocal\n"
        "\"C\"c4 d4 e4 f4 | \"G\"g16 |\n"
        "V: Ins\n"
        "\"C\"C8 E8 | \"G\"G16 |\n"
    )

    js = f"""
    const input = {json.dumps(raw_abc)};
    PianoRoll.model = parseAbc(input);

    const initialTotal = PianoRoll.model.notes.length;
    // Select bar 0 notes across both voices (startTick < 16)
    PianoRoll.selectFromTick(0);
    // Keep only bar 0
    PianoRoll.selectedNoteIds = PianoRoll.model.notes.filter(n => n.startTick < 16).map(n => n.id);
    const selectedBar0Count = PianoRoll.selectedNoteIds.length;
    const vocalInBar0 = PianoRoll.model.notes.filter(n => PianoRoll.isNoteSelected(n.id) && n.voice === 'Vocal').length;
    const insInBar0 = PianoRoll.model.notes.filter(n => PianoRoll.isNoteSelected(n.id) && n.voice === 'Ins').length;

    // Mass delete
    PianoRoll.deleteSelectedNotes();

    const remainingTotal = PianoRoll.model.notes.length;
    const remainingVocal = PianoRoll.model.notes.filter(n => n.voice === 'Vocal').length;
    const remainingIns = PianoRoll.model.notes.filter(n => n.voice === 'Ins').length;

    const outAbc = serializeToAbc(PianoRoll.model);

    console.log(JSON.stringify({{
        initialTotal,
        selectedBar0Count,
        vocalInBar0,
        insInBar0,
        remainingTotal,
        remainingVocal,
        remainingIns,
        outAbc
    }}));
    """
    data = run_node_script(js)

    assert data["vocalInBar0"] == 4
    assert data["insInBar0"] == 2
    assert data["remainingTotal"] == data["initialTotal"] - data["selectedBar0Count"]
    assert data["remainingVocal"] == 1  # only g16 remains
    assert data["remainingIns"] == 1    # only G16 remains
    assert score.problems(data["outAbc"]) == []


def test_piano_roll_zoom_in_and_out():
    """Verify zooming in (+) and out (-) adjusts tickWidth within bounds."""
    raw_abc = "X:1\nM:4/4\nL:1/16\nQ:1/4=120\nK:C\n\"C\"c4 d4 e4 f4 | \"G\"g16 |\n"

    js = f"""
    const input = {json.dumps(raw_abc)};
    PianoRoll.model = parseAbc(input);
    PianoRoll.tickWidth = 12;

    // Zoom in by default step (4)
    PianoRoll.zoomIn();
    const zoomedIn1 = PianoRoll.tickWidth; // 16

    // Zoom in again
    PianoRoll.zoomIn(8);
    const zoomedIn2 = PianoRoll.tickWidth; // 24

    // Zoom out by 4
    PianoRoll.zoomOut();
    const zoomedOut1 = PianoRoll.tickWidth; // 20

    // Zoom out to lower clamp bound (min 6)
    for (let i = 0; i < 10; i++) {{ PianoRoll.zoomOut(); }}
    const minClamped = PianoRoll.tickWidth;

    // Zoom in to upper clamp bound (max 48)
    for (let i = 0; i < 20; i++) {{ PianoRoll.zoomIn(); }}
    const maxClamped = PianoRoll.tickWidth;

    console.log(JSON.stringify({{
        zoomedIn1,
        zoomedIn2,
        zoomedOut1,
        minClamped,
        maxClamped
    }}));
    """
    data = run_node_script(js)

    assert data["zoomedIn1"] == 16
    assert data["zoomedIn2"] == 24
    assert data["zoomedOut1"] == 20
    assert data["minClamped"] == 6
    assert data["maxClamped"] == 48


def test_parse_and_serialize_chords_in_abc():
    """Verify chords in brackets [...] parse simultaneous notes with shared ticks and serialize back as chords."""
    js = """
    const abc = 'X:1\\nM:4/4\\nL:1/16\\nK:C\\nV: Ins\\n[CF]2 [A,DF]2 z12 |';
    const model = parseAbc(abc);
    const serialized = serializeToAbc(model);
    console.log(JSON.stringify({ notes: model.notes, serialized }));
    """
    res = run_node_script(js)
    notes = res["notes"]
    assert len(notes) == 5
    # Notes in first chord start at tick 0 with duration 2
    assert notes[0]["pitch"] == 60 and notes[0]["startTick"] == 0 and notes[0]["durationTicks"] == 2
    assert notes[1]["pitch"] == 65 and notes[1]["startTick"] == 0 and notes[1]["durationTicks"] == 2
    # Notes in second chord start at tick 2 with duration 2
    assert notes[2]["pitch"] == 57 and notes[2]["startTick"] == 2 and notes[2]["durationTicks"] == 2
    assert notes[3]["pitch"] == 62 and notes[3]["startTick"] == 2 and notes[3]["durationTicks"] == 2
    assert notes[4]["pitch"] == 65 and notes[4]["startTick"] == 2 and notes[4]["durationTicks"] == 2
    # Serialized output preserves chords in brackets and exact bar duration
    assert "[CF]2" in res["serialized"]
    assert "[A,DF]2" in res["serialized"]
    assert "z12" in res["serialized"]


def test_extract_lyrics_sections_with_markdown_headers():
    """Verify markdown headers like **[Verse 1]** and ## Chorus are extracted as section tags, not lyric words."""
    js = """
    const text = '**[Verse 1]**\\nMorning light, all my worries seemed far away\\n[Verse 2]\\nSlowly, I\\x27m not the one I used to be\\n## Chorus\\nWhy the road had to end';
    const sections = extractLyricsSections(text);
    console.log(JSON.stringify({ sections }));
    """
    res = run_node_script(js)
    sections = res["sections"]
    assert len(sections) == 3
    assert sections[0]["name"] == "Verse 1"
    assert sections[0]["lines"] == ["Morning light, all my worries seemed far away"]
    assert sections[1]["name"] == "Verse 2"
    assert sections[1]["lines"] == ["Slowly, I'm not the one I used to be"]
    assert sections[2]["name"] == "Chorus"
    assert sections[2]["lines"] == ["Why the road had to end"]


def test_key_signature_accidentals_lookup():
    """Verify circle of fifths key signature accidentals for major, minor, and modal keys."""
    js = """
    const keys = ["C", "G", "D", "A", "E", "B", "F#", "F", "Bb", "Eb", "Ab", "Db", "Am", "Em", "Bm", "Dm", "Gm", "Cm", "Fm", "Ddor", "Dmix"];
    const results = {};
    for (const k of keys) {
        results[k] = getKeyAccidentals(k);
    }
    console.log(JSON.stringify(results));
    """
    res = run_node_script(js)
    assert res["C"] == {}
    assert res["G"] == {"F": 1}
    assert res["D"] == {"F": 1, "C": 1}
    assert res["F"] == {"B": -1}
    assert res["Bb"] == {"B": -1, "E": -1}
    assert res["Eb"] == {"B": -1, "E": -1, "A": -1}
    assert res["Ab"] == {"B": -1, "E": -1, "A": -1, "D": -1}
    assert res["Am"] == {}
    assert res["Em"] == {"F": 1}
    assert res["Dm"] == {"B": -1}
    assert res["Gm"] == {"B": -1, "E": -1}
    assert res["Cm"] == {"B": -1, "E": -1, "A": -1}
    assert res["Ddor"] == {}
    assert res["Dmix"] == {"F": 1}


def test_abc_note_to_midi_with_key_and_measure_accidentals():
    """Verify abcNoteToMidi applies active key signature, explicit accidentals, and bar scope."""
    js = """
    const keyBb = getKeyAccidentals("Bb");
    const keyG = getKeyAccidentals("G");
    const barAccs = {};

    // In K:Bb, unmarked B4 and e5 are flatted to Bb4 (70) and Eb5 (75)
    const bInBb = abcNoteToMidi("", "B", "", keyBb, barAccs);
    const eInBb = abcNoteToMidi("", "e", "", keyBb, barAccs);

    // In K:Bb, explicit =B is natural B4 (71)
    const bNatInBb = abcNoteToMidi("=", "B", "", keyBb, barAccs);

    // In K:G, unmarked F4 is sharped to F#4 (66), =F is natural (65)
    const fInG = abcNoteToMidi("", "F", "", keyG, {});
    const fNatInG = abcNoteToMidi("=", "F", "", keyG, {});

    // Bar accidental persistence: _A in bar sets bar accidental for subsequent A in same bar
    const barAccs2 = {};
    const aFlat = abcNoteToMidi("_", "A", ",", keyBb, barAccs2); // _A, -> 56 (Ab3)
    const aSubsequent = abcNoteToMidi("", "A", ",", keyBb, barAccs2); // A, in same bar -> 56 (Ab3)

    console.log(JSON.stringify({ bInBb, eInBb, bNatInBb, fInG, fNatInG, aFlat, aSubsequent }));
    """
    res = run_node_script(js)
    assert res["bInBb"] == 70  # Bb4
    assert res["eInBb"] == 75  # Eb5
    assert res["bNatInBb"] == 71  # B4
    assert res["fInG"] == 66  # F#4
    assert res["fNatInG"] == 65  # F4
    assert res["aFlat"] == 56  # Ab3
    assert res["aSubsequent"] == 56  # Ab3 in same bar inherits flat


def test_bushy_take_score_pitches_in_key_bb_and_cm():
    """Verify take 'bushy' (c81c76e329dd) with K:Bb and K:Cm parses to correct MIDI pitches."""
    bushy_json = Path(__file__).resolve().parent.parent / "data" / "takes" / "bushy-c81c76e329dd" / "take.json"
    if not bushy_json.exists():
        return
    with open(bushy_json, "r") as f:
        take_data = json.load(f)
    score_abc = take_data["score"]

    js = f"""
    const abc = {json.dumps(score_abc)};
    const model = parseAbc(abc);

    // Opening Ins notes in bar 1: E2B2e2g4B2e2g2-
    const insNotesBar1 = model.notes.filter(n => n.voice === 'Ins' && n.startTick >= 16 && n.startTick < 32);
    insNotesBar1.sort((a,b) => a.startTick - b.startTick);

    // Vocal verse notes in bar 17: "Ebmaj7"e4f4f4e2g2-
    const vocalVerseNotes = model.notes.filter(n => n.voice === 'Vocal' && n.startTick >= 17*16 && n.startTick < 18*16);
    vocalVerseNotes.sort((a,b) => a.startTick - b.startTick);

    console.log(JSON.stringify({{
        key: model.key,
        insPitches: insNotesBar1.map(n => n.pitch),
        vocalPitches: vocalVerseNotes.map(n => n.pitch)
    }}));
    """
    res = run_node_script(js)
    assert res["key"] == "Bb"
    # Opening Ins notes must be Eb4 (63), Bb4 (70), Eb5 (75), G5 (79)
    assert res["insPitches"][:4] == [63, 70, 75, 79]
    # Vocal verse in Ebmaj7 begins on Eb5 (75), F5 (77), F5 (77), Eb5 (75), G5 (79)
    assert res["vocalPitches"][0] == 75  # Eb5 (NOT 76 E natural)
    assert res["vocalPitches"][1] == 77  # F5
    assert res["vocalPitches"][3] == 75  # Eb5


def test_midi_to_abc_note_naturals_in_key():
    """Verify midiToAbcNote produces = natural accidentals for natural notes in non-C keys."""
    js = """
    // In K:Bb, B natural (71) and E natural (64) need =B and =E
    const bNatInBb = midiToAbcNote(71, "Bb");
    const eNatInBb = midiToAbcNote(64, "Bb");

    // In K:G, F natural (65) needs =F
    const fNatInG = midiToAbcNote(65, "G");

    // In K:Bb, Bb4 (70) and Eb4 (63) format cleanly as _B and _E
    const bFlatInBb = midiToAbcNote(70, "Bb");
    const eFlatInBb = midiToAbcNote(63, "Bb");

    console.log(JSON.stringify({ bNatInBb, eNatInBb, fNatInG, bFlatInBb, eFlatInBb }));
    """
    res = run_node_script(js)
    assert res["bNatInBb"] == "=B"
    assert res["eNatInBb"] == "=E"
    assert res["fNatInG"] == "=F"
    assert res["bFlatInBb"] == "_B"
    assert res["eFlatInBb"] == "_E"
