"""A take for a DAW: one zip with its audio as a 24-bit WAV, its stems, the score as ABC and MIDI, a chord chart and
its recipe."""
import io
import subprocess
import zipfile

from app import daw
from conftest import make_take, tone

SCORE = """X:1
T:
M:4/4
L:1/16
Q:1/4=103
V: Vocal clef=treble name="Vocal Melody" snm="Vocal"
V: Ins clef=treble name="Ins Melody" snm="Inst."
K:D
% intro
V: Vocal
Z|"Dmaj7"z16|"Bm7"z16|
V: Ins
Z|f2f2z12|e2f2z12|
% chorus
V: Vocal
"G/A"z16|"Dmaj7"a4a4a4a4|z16|Z2|
V: Ins
Z4|
"""
MIDI = b"MThd\x00\x00\x00\x06\x00\x01\x00\x01\x01\xe0MTrk\x00\x00\x00\x04\x00\xff\x2f\x00"


def test_the_chart_reads_tempo_key_and_each_sections_chords():
    text = daw.chart({"title": "Night drive", "abc": SCORE, "duration": 192.4, "kind": "song",
                      "lyrics": "[Chorus]\nLights along the harbour wall"})
    lines = text.splitlines()
    assert lines[0] == "Night drive"
    assert lines[1] == "Tempo: 103 BPM   Key: D   Time: 4/4   Length: 3:12"
    assert "Intro" in lines and "| % | Dmaj7 | Bm7 |" in lines
    chorus = lines.index("Chorus")
    assert lines[chorus + 1] == "| G/A | Dmaj7 | % | % |" and lines[chorus + 2] == "| % |"
    assert "Lights along the harbour wall" in text


def test_the_bundle_holds_audio_score_midi_chart_and_recipe(client, tmp_path):
    take = make_take(title="Night drive", abc=SCORE, audio_path=str(tone(tmp_path / "t.flac", seconds=1.0)))
    res = client.post(f"/api/takes/{take['id']}/daw-bundle", files={"midi_file": ("score.mid", MIDI, "audio/midi")})
    assert res.status_code == 200
    data = client.get(res.json()["download_url"]).content
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert set(names) == {"Night drive.wav", "Night drive.mid", "Night drive.abc", "Night drive - chart.txt",
                          "Night drive.yeufonic.json"}
    wav = zipfile.ZipFile(io.BytesIO(data)).read("Night drive.wav")
    codec = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name", "-of", "default=nw=1",
                            "pipe:0"], input=wav, capture_output=True, check=True).stdout.decode()
    assert "pcm_s24le" in codec


def test_a_file_that_is_not_midi_is_refused(client, tmp_path):
    take = make_take(title="Night drive", abc=SCORE, audio_path=str(tone(tmp_path / "t.flac", seconds=1.0)))
    res = client.post(f"/api/takes/{take['id']}/daw-bundle", files={"midi_file": ("x.mid", b"nope", "audio/midi")})
    assert res.status_code == 400
