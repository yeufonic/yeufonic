"""A saved take carries the tempo and key its score states, where a DAW or DJ program reads them, and the rack's
24-bit mastered render stays 24-bit in a WAV."""
import subprocess

from app import library
from conftest import make_take, tone

SCORE = "X:1\nT:Night drive\nM:4/4\nL:1/8\nQ:1/4=92\nK:F#m\nV:Vocal\n|: A2 c2 e2 c2 :|\n"


def _probe(data: bytes, entries: str) -> str:
    return subprocess.run(["ffprobe", "-v", "error", "-show_entries", entries, "-of", "default=nw=1", "pipe:0"],
                          input=data, capture_output=True, check=True).stdout.decode()


def test_music_tags_from_the_score():
    assert library.music_tags(SCORE) == {"bpm": "92", "key": "F#m"}
    assert library.music_tags("X:1\nK:Bb\n") == {"key": "Bb"}
    assert library.music_tags("X:1\nK:Ddor\n") == {}, "a mode other than major or minor is not named"
    assert library.music_tags("") == {}


def test_flac_and_mp3_downloads_carry_tempo_and_key(client, tmp_path):
    take = make_take(title="Night drive", abc=SCORE, audio_path=str(tone(tmp_path / "t.flac", seconds=1.0)))
    flac = client.get(f"/api/takes/{take['id']}/audio?download=1&format=flac").content
    tags = _probe(flac, "format_tags").lower()
    assert "tag:bpm=92" in tags and "tag:initialkey=f#m" in tags
    mp3 = client.get(f"/api/takes/{take['id']}/audio?download=1&format=mp3").content
    assert b"TBPM" in mp3[:4000] and b"TKEY" in mp3[:4000]
    assert b"92" in mp3[:4000] and b"F#m" in mp3[:4000]


def test_a_take_with_no_score_has_no_tempo_or_key(client, tmp_path):
    take = make_take(title="Free", abc="", audio_path=str(tone(tmp_path / "t.flac", seconds=1.0)))
    tags = _probe(client.get(f"/api/takes/{take['id']}/audio?download=1&format=flac").content, "format_tags").lower()
    assert "bpm=" not in tags and "initialkey=" not in tags


def test_a_mastered_wav_keeps_24_bits(client, tmp_path):
    take = make_take(title="Night drive", abc=SCORE, audio_path=str(tone(tmp_path / "t.flac", seconds=1.0)))
    deep = tmp_path / "rack.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tone(tmp_path / "src.wav", seconds=1.0)),
                    "-c:a", "pcm_s24le", str(deep)], check=True)
    with open(deep, "rb") as fh:
        res = client.post(f"/api/takes/{take['id']}/export-mastered?format=wav",
                          files={"audio_file": ("master.wav", fh, "audio/wav")})
    assert res.status_code == 200
    assert "codec_name=pcm_s24le" in _probe(res.content, "stream=codec_name")
    with open(deep, "rb") as fh:
        flac = client.post(f"/api/takes/{take['id']}/export-mastered?format=flac",
                           files={"audio_file": ("master.wav", fh, "audio/wav")}).content
    assert "bits_per_raw_sample=24" in _probe(flac, "stream=bits_per_raw_sample")
