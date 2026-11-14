"""The Score window's MIDI file, written by app/static/midiwrite.js from the sequence abcjs builds to play a score.

abcjs's own file writer garbled the drums (their pitches and volumes reach it as strings), wrote every instrument
change on channel 1 and left the bass without an instrument. These tests read the file back with a strict parser
of their own, which rejects anything a strict MIDI reader would."""
import base64
import json
import subprocess
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"
WRITER = STATIC / "midiwrite.js"


def write(seq: dict, info: dict | None = None) -> bytes | None:
    # The sequence goes in on stdin: a long song does not fit on a command line.
    script = (
        f"const {{ writeMidi }} = require({json.dumps(str(WRITER))});"
        "let text = '';"
        "process.stdin.setEncoding('utf8'); process.stdin.on('data', (c) => text += c);"
        "process.stdin.on('end', () => {"
        "  const input = JSON.parse(text);"
        "  const out = writeMidi(input.seq, input.info);"
        "  console.log(JSON.stringify(out ? Buffer.from(out).toString('base64') : null));"
        "});"
    )
    res = subprocess.run(["node", "-e", script], input=json.dumps({"seq": seq, "info": info or {}}),
                         capture_output=True, text=True, check=True)
    value = json.loads(res.stdout)
    return base64.b64decode(value) if value else None


def read(data: bytes) -> dict:
    """A strict reader: every data byte must be 0..127, every track must end exactly where it says."""
    assert data[:4] == b"MThd" and int.from_bytes(data[4:8], "big") == 6
    fmt, count, division = (int.from_bytes(data[8:10], "big"), int.from_bytes(data[10:12], "big"),
                            int.from_bytes(data[12:14], "big"))
    pos, tracks = 14, []
    for _ in range(count):
        assert data[pos:pos + 4] == b"MTrk", "a track header is missing"
        length = int.from_bytes(data[pos + 4:pos + 8], "big")
        body, pos = data[pos + 8:pos + 8 + length], pos + 8 + length
        assert len(body) == length, "a track is shorter than it says"
        i, tick, notes, programs, names, tempos, meters, ended = 0, 0, [], [], [], [], [], False
        open_ = {}
        while i < len(body):
            delta = 0
            while True:
                byte = body[i]; i += 1
                delta = (delta << 7) | (byte & 0x7F)
                if not byte & 0x80:
                    break
            tick += delta
            status = body[i]; i += 1
            if status == 0xFF:
                kind = body[i]; i += 1
                size = 0
                while True:
                    byte = body[i]; i += 1
                    size = (size << 7) | (byte & 0x7F)
                    if not byte & 0x80:
                        break
                payload, i = body[i:i + size], i + size
                if kind == 0x03:
                    names.append(payload.decode("ascii"))
                elif kind == 0x51:
                    tempos.append(int.from_bytes(payload, "big"))
                elif kind == 0x58:
                    meters.append((payload[0], 2 ** payload[1]))
                elif kind == 0x2F:
                    ended = i == len(body)
                continue
            assert status & 0x80, f"running status or a stray data byte at {i}"
            kind, channel = status >> 4, status & 15
            size = 1 if kind in (0xC, 0xD) else 2
            data_bytes = list(body[i:i + size]); i += size
            assert all(b < 0x80 for b in data_bytes), f"a data byte above 127: {data_bytes}"
            if kind == 0xC:
                programs.append((channel + 1, data_bytes[0]))
            elif kind == 0x9 and data_bytes[1] > 0:
                open_[(channel, data_bytes[0])] = (tick, data_bytes[1])
            elif kind in (0x8, 0x9) and (channel, data_bytes[0]) in open_:
                start, velocity = open_.pop((channel, data_bytes[0]))
                notes.append({"channel": channel + 1, "pitch": data_bytes[0], "velocity": velocity,
                              "start": start, "length": tick - start})
        assert ended, "a track does not end with the end-of-track marker"
        assert not open_, "a note was never ended"
        tracks.append({"names": names, "notes": notes, "programs": programs, "tempos": tempos, "meters": meters})
    assert pos == len(data), "bytes left over after the last track"
    return {"format": fmt, "division": division, "tracks": tracks}


def note(pitch, volume, start, duration, instrument, **more):
    return {"cmd": "note", "pitch": pitch, "volume": volume, "start": start, "duration": duration,
            "instrument": instrument, "gap": 0, **more}


# The shape abcjs's tune.setUpAudio gives for a score with a vocal line, an instrument line, chords with a bass,
# and drums: the drum pitches and volumes are strings, which is what broke abcjs's own writer.
SEQ = {"tempo": 92, "instrument": 0, "totalDuration": 25, "tracks": [
    [{"cmd": "text", "type": "name", "text": "Vocal Melody"}, {"cmd": "program", "channel": 0, "instrument": 53},
     note(74, 105, 4.5, 0.25, 53), note(77, 95, 4.75, 0.25, 53)],
    [{"cmd": "text", "type": "name", "text": "Ins Melody"}, {"cmd": "program", "channel": 1, "instrument": 25},
     note(58, 105, 0.5, 0.125, 25), note(70, 85, 0.625, 0.1875, 25)],
    [{"cmd": "program", "channel": 2, "instrument": 25},
     note(34, 64, 0.375, 0.125, 34), note(34, 64, 0.5, 0.125, 34), note(46, 48, 0.75, 0.125, 25),
     note(50, 48, 0.75, 0.125, 25)],
    [{"cmd": "program", "channel": 3, "instrument": 128},
     note("36", "80", 0, 0.0625, 128), note("38", "76", 0.125, 0.0625, 128), note("36", "80", 0.25, 0.0625, 128)],
]}


def parts(result: dict) -> dict:
    return {t["names"][0]: t for t in result["tracks"][1:]}


def test_the_file_is_valid_and_has_one_track_for_each_part():
    result = read(write(SEQ, {"meter": {"num": 2, "den": 4}, "title": "A song"}))
    assert result["format"] == 1 and result["division"] == 480
    assert [t["names"][0] for t in result["tracks"]] == ["A song", "Vocal Melody", "Ins Melody", "Chords", "Bass", "Drums"]


def test_each_part_has_its_instrument_set_on_its_own_channel():
    result = read(write(SEQ))
    got = parts(result)
    assert got["Vocal Melody"]["programs"] == [(1, 53)] and {n["channel"] for n in got["Vocal Melody"]["notes"]} == {1}
    assert got["Ins Melody"]["programs"] == [(2, 25)] and {n["channel"] for n in got["Ins Melody"]["notes"]} == {2}
    # Not channel 1 for everything, which is what abcjs wrote.
    assert got["Chords"]["programs"] == [(3, 25)] and {n["channel"] for n in got["Chords"]["notes"]} == {3}


def test_the_bass_is_its_own_part_with_its_own_instrument():
    got = parts(read(write(SEQ)))
    assert got["Bass"]["programs"] == [(4, 34)]
    assert sorted(n["pitch"] for n in got["Bass"]["notes"]) == [34, 34]
    assert sorted(n["pitch"] for n in got["Chords"]["notes"]) == [46, 50]


def test_drums_are_on_channel_ten_at_the_pitches_and_velocities_asked_for():
    drums = parts(read(write(SEQ)))["Drums"]
    assert drums["programs"] == []
    assert {n["channel"] for n in drums["notes"]} == {10}
    assert [(n["pitch"], n["velocity"]) for n in sorted(drums["notes"], key=lambda n: n["start"])] == [(36, 80), (38, 76), (36, 80)]


def test_nothing_that_is_not_a_drum_uses_the_drum_channel():
    seq = {"tempo": 120, "tracks": [[note(60 + i, 80, 0, 0.25, 0)] for i in range(12)]}
    channels = {n["channel"] for t in read(write(seq))["tracks"][1:] for n in t["notes"]}
    assert 10 not in channels and len(channels) == 12


def test_timing_is_the_whole_note_counted_in_ticks():
    ins = parts(read(write(SEQ)))["Ins Melody"]["notes"]
    assert (ins[0]["start"], ins[0]["length"]) == (960, 240)          # 0.5 and 0.125 of a whole note at 480 to a quarter
    assert (ins[1]["start"], ins[1]["length"]) == (1200, 360)


def test_tempo_and_metre_are_written():
    conductor = read(write(SEQ, {"meter": {"num": 6, "den": 8}}))["tracks"][0]
    assert conductor["tempos"] == [round(60000000 / 92)]
    assert conductor["meters"] == [(6, 8)]


def test_a_tempo_change_in_the_sequence_is_kept():
    seq = {"tempo": 100, "tracks": [[{"cmd": "tempo", "qpm": 140, "start": 2}, note(60, 80, 0, 0.25, 0)]]}
    assert read(write(seq))["tracks"][0]["tempos"] == [600000, round(60000000 / 140)]


def test_values_outside_what_midi_allows_are_brought_inside():
    seq = {"tempo": 120, "tracks": [[note(300, 200, 0, 0.25, 0), note(-5, 0, 0.25, 0.25, 0), note("61", "999", 0.5, 0, 0)]]}
    notes = read(write(seq))["tracks"][1]["notes"]                    # the reader fails on any byte above 127
    assert [(n["pitch"], n["velocity"]) for n in notes] == [(127, 127), (0, 1), (61, 127)]
    assert notes[2]["length"] == 1                                    # a note of no length still lasts a tick


def test_a_score_with_no_notes_gives_nothing_to_save():
    assert write({"tempo": 120, "tracks": [[{"cmd": "program", "channel": 0, "instrument": 0}], []]}) is None
    assert write({"tempo": 120, "tracks": []}) is None


def test_a_long_song_is_written_whole():
    seq = {"tempo": 120, "tracks": [[note(40 + i % 40, 80, i * 0.0625, 0.0625, 0) for i in range(30000)]]}
    result = read(write(seq))
    assert len(result["tracks"][1]["notes"]) == 30000


def test_non_ascii_text_cannot_put_a_high_byte_in_a_name():
    seq = {"tempo": 120, "tracks": [[{"cmd": "text", "type": "name", "text": "Café ♪"}, note(60, 80, 0, 0.25, 0)]]}
    assert read(write(seq, {"title": "Chanson à la plage"}))["tracks"][1]["names"][0].startswith("Caf")


def test_the_page_loads_the_writer_before_the_script_that_uses_it_and_falls_back_without_it():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert html.index("midiwrite.js") < html.index("/static/app.js")
    app = (STATIC / "app.js").read_text(encoding="utf-8")
    body = app[app.index("function notationMidiBytes("):app.index("function notationDownloadMidi(")]
    assert "typeof writeMidi === 'function'" in body and "getMidiFile" in body      # abcjs's own file stays the fallback
