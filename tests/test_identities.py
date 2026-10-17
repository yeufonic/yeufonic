"""Identities: scanning a folder (read only), flags, chunking, captions, the API."""
import numpy as np
import pytest

from app import config, identities, jobs, personas
from app.db import one
from app.jobs import IDENTITY_QUEUE, PERSONA_QUEUE

from conftest import tone


@pytest.fixture(autouse=True)
def corpora_built_in(monkeypatch):
    """Corpora are on by default; pinned on here so the tests do not depend on the
    environment. The tests for it switched off live in test_lora_training.py."""
    monkeypatch.setattr(config, "TRAINING_ENABLED", True)


def make_folder(tmp_path, monkeypatch):
    root = tmp_path / "import"
    songs = root / "Under"
    songs.mkdir(parents=True)
    monkeypatch.setattr(config, "IMPORT_ROOTS", [str(root)])
    tone(songs / "01 Modern Girl.wav", 100)
    (songs / "Modern Girl copy.wav").write_bytes((songs / "01 Modern Girl.wav").read_bytes())
    tone(songs / "02 Falling.wav", 95)
    tone(songs / "09 Falling (acoustic).wav", 96)
    tone(songs / "14. Did It Ever (Ft. Alan Williams on vocals).wav", 101)
    tone(songs / "08 It's Only Love Short.wav", 30)
    tone(songs / "did_it_ever.wav", 102)
    (songs / "cover.jpg").write_bytes(b"not audio")
    return root, songs


def test_scan_flags_copies_versions_other_singers_and_short_files(tmp_path, monkeypatch):
    _, folder = make_folder(tmp_path, monkeypatch)
    found = {s["file"]: s for s in identities.scan(folder)}
    assert "cover.jpg" not in found and len(found) == 7
    assert "names another singer" in found["did_it_ever.wav"]["flag"]
    assert found["01 Modern Girl.wav"]["include"] and found["01 Modern Girl.wav"]["title"] == "Modern Girl"
    assert "exact copy" in found["Modern Girl copy.wav"]["flag"]
    assert "another version" in found["09 Falling (acoustic).wav"]["flag"]
    assert "another singer" in found["14. Did It Ever (Ft. Alan Williams on vocals).wav"]["flag"]
    assert "shorter" in found["08 It's Only Love Short.wav"]["flag"]
    assert [s["file"] for s in found.values() if s["include"]] == ["01 Modern Girl.wav", "02 Falling.wav"]


def test_scan_reads_opus_and_other_formats_ffmpeg_decodes(tmp_path, monkeypatch):
    """Everything after the scan reads through ffmpeg, so any format it decodes can
    join a corpus; the engine is only ever sent a FLAC made from it."""
    import subprocess
    root = tmp_path / "import"
    songs = root / "Mixed"
    songs.mkdir(parents=True)
    monkeypatch.setattr(config, "IMPORT_ROOTS", [str(root)])
    tone(songs / "source.wav", 100)
    for name in ("Harbour Lights.opus", "Glass Orchard.aiff"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(songs / "source.wav"),
                        "-metadata", f"title={name.split('.')[0]} (tagged)", str(songs / name)], check=True)
    (songs / "source.wav").unlink()

    found = {s["file"]: s for s in identities.scan(songs)}
    assert set(found) == {"Harbour Lights.opus", "Glass Orchard.aiff"}
    assert found["Harbour Lights.opus"]["duration"] > 90
    # An Opus file's title tag is on its stream, not the file, and is still found.
    assert found["Harbour Lights.opus"]["title"] == "Harbour Lights (tagged)"
    assert found["Glass Orchard.aiff"]["title"] == "Glass Orchard (tagged)"
    assert identities.read_mono(songs / "Harbour Lights.opus").size > 0


def test_folders_outside_the_import_roots_are_refused(tmp_path, monkeypatch):
    make_folder(tmp_path, monkeypatch)
    assert not identities.allowed(tmp_path)
    # The drop folder is a root too, but it is not listed until it exists.
    assert identities.browse(None)["folders"] == [str(tmp_path / "import")]
    assert identities.browse(str(tmp_path / "import"))["folders"] == [str(tmp_path / "import" / "Under")]


def test_the_drop_folder_is_offered_and_readable(tmp_path, monkeypatch):
    """A user copies songs into one folder and needs to know nothing else."""
    make_folder(tmp_path, monkeypatch)
    config.CORPUS_INBOX.mkdir(parents=True, exist_ok=True)
    tone(config.CORPUS_INBOX / "My Song.wav", 100)

    assert identities.allowed(config.CORPUS_INBOX)
    assert str(config.CORPUS_INBOX) in identities.browse(None)["folders"]
    assert [s["file"] for s in identities.scan(config.CORPUS_INBOX)] == ["My Song.wav"]


def test_chunks_cut_at_quiet_points_and_skip_silence():
    rate = identities.CHUNK_RATE
    t = np.arange(rate * 70) / rate
    voice = 0.5 * np.sin(2 * np.pi * 220 * t)
    voice[: rate * 5] = 0                                  # 5 s of silence at the start
    voice[rate * 22: rate * 23] *= 0.001                   # a breath at 22 s
    chunks = identities.sung_chunks(voice.astype(np.float32))
    assert chunks[0][0] >= 4.9 and all(b - a <= identities.CHUNK_MAX + 0.1 for a, b in chunks)
    assert abs(chunks[0][1] - 22.0) < 1.1                  # the first cut lands on the breath


def test_key_tempo_and_caption():
    assert identities.key_and_tempo("X:1\nQ:1/4=70\nK:Dm\n") == ("D minor", 70)
    assert identities.key_and_tempo("K:Bb\n") == ("Bb major", None)
    assert identities.caption("pshields", "pop rock, guitars", "male", "D minor", 70) == "pshields, pop rock, guitars, male vocal, key of D minor, 70 BPM"
    assert identities.caption("pshields", "pop rock", "male", "D minor", 70, style_hint="acoustic guitar, harmonica") == (
        "pshields, acoustic guitar, harmonica, pop rock, male vocal, key of D minor, 70 BPM"
    )


def test_score_sections_count_bars_by_time_signature():
    abc = ("X:1\nM:4/4\nV: Vocal\nV: Ins\nK:C\n% intro\nV: Vocal\n|z4|z4|\nV: Ins\n|c4|c4|\n"
           "% verse\nV: Vocal\nM:2/4\n|c2|d2|e2|f2|\n% interlude\nV: Vocal\nM:4/4\n|z4|\n% nonsense\n|z4|\n")
    assert identities.score_sections(abc) == [("intro", 2.0), ("verse", 2.0), ("interlude", 2.0)]


def test_lines_are_tagged_by_the_section_playing():
    lines = [{"start": 1, "end": 4, "text": "first verse line"}, {"start": 28, "end": 30, "text": "a chorus line"},
             {"start": 31, "end": 34, "text": "the chorus again"}, {"start": 58, "end": 59, "text": "last words"}]
    sections = [("intro", 1.0), ("verse", 2.0), ("chorus", 2.0), ("interlude", 1.0), ("outro", 0.5)]
    # 60 s over 6.5 lengths: intro 0-9.2, verse 9.2-27.7, chorus 27.7-46.2, interlude as bridge, outro 55.4-60.
    assert identities.tag_lyrics(lines, sections, 60) == (
        "[Intro]\nfirst verse line\n\n[Verse]\n\n[Chorus]\na chorus line\nthe chorus again\n\n[Bridge]\n\n[Outro]\nlast words")
    assert identities.tag_lyrics(lines, [], 60).startswith("[Verse]\nfirst verse line")
    assert identities.tag_lyrics([], sections, 60) == ""


def test_a_boundary_moves_to_the_pause_before_a_line_sung_on_a_pickup():
    """The estimate lands a second or three late: the first verse line starts before
    the intro is over, and belongs to the verse, after the pause before it."""
    lines = [{"start": 9.2, "end": 11.8, "text": "the verse begins"}, {"start": 12.1, "end": 15.0, "text": "and goes on"},
             {"start": 16.0, "end": 19.0, "text": "to its end"}, {"start": 28.0, "end": 31.0, "text": "a chorus line"}]
    sections = [("intro", 12.6), ("verse", 14.4), ("chorus", 33.0)]     # intro 0-12.6, verse 12.6-27, chorus 27-60
    assert identities.tag_lyrics(lines, sections, 60) == (
        "[Intro]\n\n[Verse]\nthe verse begins\nand goes on\nto its end\n\n[Chorus]\na chorus line")
    # Too far away to reach: a pause more than four seconds early is not taken.
    far = [{"start": 3.0, "end": 12.0, "text": "a long held line"}, {"start": 12.2, "end": 20.0, "text": "then this"}]
    assert identities._snap(18.0, far, 0.0, 60.0) == 18.0


TAGGED = "[Intro]\n\n[Verse]\nfirst verse\n\n[Chorus]\nthe chorus\n\n[Outro]\nlast words"
CUT_LINES = [{"start": 24, "end": 28, "text": "first verse"}, {"start": 55, "end": 60, "text": "the chorus"},
             {"start": 90, "end": 95, "text": "last words"}]
CUT_SECTIONS = [("intro", 0.2), ("verse", 0.3), ("chorus", 0.3), ("outro", 0.2)]   # 0-20, 20-50, 50-80, 80-100 of 100 s


def test_a_song_over_the_training_limit_is_cut_at_a_section_end():
    """The trainer learns each song whole, so a long song was cut mid-bar with the whole
    song's words. The cut is the last section end within the limit, and the words of the
    sections cut away go (#7)."""
    assert identities.training_cut(CUT_LINES, CUT_SECTIONS, 100, 100, TAGGED) is None       # fits
    assert identities.training_cut(CUT_LINES, CUT_SECTIONS, 100, 99.5, TAGGED) is None      # within a second
    cut = identities.training_cut(CUT_LINES, CUT_SECTIONS, 100, 60, TAGGED)
    assert cut == {"seconds": 50.0, "lyrics": "[Intro]\n\n[Verse]\nfirst verse", "at_section": True}
    # A section end too early to keep much of the song is not taken: cut at the limit.
    cut = identities.training_cut(CUT_LINES, CUT_SECTIONS, 100, 40, TAGGED)     # the intro's end, at 20 s, is under 60% of 40
    assert cut == {"seconds": 40.0, "lyrics": "[Intro]\n\n[Verse]\nfirst verse", "at_section": False}


def test_a_cut_song_without_sections_or_tags_keeps_what_it_has():
    cut = identities.training_cut([], [], 100, 60, TAGGED)
    assert cut["seconds"] == 60.0 and not cut["at_section"]
    assert cut["lyrics"] == "[Intro]\n\n[Verse]\nfirst verse\n\n[Chorus]\nthe chorus"     # spread evenly: 0, 25, 50, 75
    plain = identities.training_cut(CUT_LINES, CUT_SECTIONS, 100, 60, "just some words")
    assert plain["lyrics"] == "just some words" and plain["seconds"] == 50.0


def test_the_export_cuts_a_long_song_with_a_fade_and_the_words_still_sung(client, tmp_path, monkeypatch):
    import json as _json
    _, folder = make_folder(tmp_path, monkeypatch)
    made = client.post("/api/identities", json={"name": "Me", "trigger_word": "me", "voice": "male", "folder": str(folder), "consent": True}).json()
    song = next(s for s in made["songs"] if s["file"] == "01 Modern Girl.wav")
    jobs.set_song(song["id"], stored_path=str(folder / "01 Modern Girl.wav"), lyrics=TAGGED)
    (folder / "whisper.json").write_text(_json.dumps(CUT_LINES))
    (folder / "score.abc").write_text(
        "X:1\nM:4/4\nL:1/4\nQ:1/4=120\nV: Vocal\nK:C\n% intro\n" + "z4|" * 2 + "\n% verse\n" + "c4|" * 3 +
        "\n% chorus\n" + "c4|" * 3 + "\n% outro\n" + "z4|" * 2 + "\n")
    monkeypatch.setattr(config, "TRAIN_MINUTES_AUTO", False)
    monkeypatch.setattr(config, "TRAIN_MAX_MINUTES", 1.0)                 # 60 s
    view = client.get(f"/api/identities/{made['id']}").json()
    assert next(s for s in view["songs"] if s["id"] == song["id"])["trained_to"] == 50.0
    assert next(s for s in view["songs"] if s["file"] == "02 Falling.wav")["trained_to"] is None    # under the limit
    out = client.post(f"/api/identities/{made['id']}/export").json()
    assert out["cut"] == [{"title": "Modern Girl", "seconds": 50.0, "at_section": True}]
    dataset = config.DATA_DIR / "identities" / made["id"] / "dataset"
    audio = next(dataset.glob("*.flac"))
    assert abs(identities.probe(audio)["duration"] - 50.0) < 0.5
    assert next(dataset.glob("*.lyrics.txt")).read_text().strip() == "[Intro]\n\n[Verse]\nfirst verse"
    assert _json.loads((dataset / "manifest.json").read_text())["cut_for_training"][0]["title"] == "Modern Girl"


def test_api_needs_consent_scans_and_queues(client, tmp_path, monkeypatch):
    async def hold(song_id):   # the worker is running: keep it from separating test tones
        return None
    monkeypatch.setattr(jobs, "prepare_song", hold)
    _, folder = make_folder(tmp_path, monkeypatch)
    body = {"name": "Me", "trigger_word": "P Shields!", "description": "pop rock", "voice": "Male", "folder": str(folder)}
    assert client.post("/api/identities", json=body).status_code == 400
    assert client.post("/api/identities", json={**body, "consent": True, "folder": str(tmp_path)}).status_code == 400
    made = client.post("/api/identities", json={**body, "consent": True}).json()
    assert made["trigger_word"] == "pshields" and made["summary"]["included"] == 2
    song = next(s for s in made["songs"] if s["include"])
    assert song["caption"].startswith("pshields, pop rock, male vocal")
    assert client.put(f"/api/identities/{made['id']}/songs/{song['id']}", json={"lyrics": "[Verse]\nla", "lyrics_checked": True}).status_code == 200
    client.put(f"/api/identities/{made['id']}/songs/{song['id']}", json={"description": "  stripped back,   acoustic guitar "})
    view = client.get(f"/api/identities/{made['id']}").json()
    caption = next(s["caption"] for s in view["songs"] if s["id"] == song["id"])
    assert caption.startswith("pshields, stripped back, acoustic guitar, male vocal")     # this song's own sound
    from app.db import execute
    execute("UPDATE identity_songs SET style_hint = 'harmonica, acoustic' WHERE id = ?", (song["id"],))
    view = client.get(f"/api/identities/{made['id']}").json()
    caption = next(s["caption"] for s in view["songs"] if s["id"] == song["id"])
    assert caption.startswith("pshields, harmonica, acoustic, stripped back, acoustic guitar, male vocal")
    other = next(s for s in view["songs"] if s["include"] and s["id"] != song["id"])
    assert other["caption"].startswith("pshields, pop rock, male vocal")                  # the rest keep the identity's
    while not IDENTITY_QUEUE.empty():
        IDENTITY_QUEUE.get_nowait()
    assert client.post(f"/api/identities/{made['id']}/analyse").json() == {"queued": 2}
    assert one("SELECT vocals_state FROM identity_songs WHERE id = ?", (song["id"],))["vocals_state"] == "queued"
    # Backward compatibility view also works
    assert one("SELECT vocals_state FROM persona_songs WHERE id = ?", (song["id"],))["vocals_state"] == "queued"
    assert client.post(f"/api/identities/{made['id']}/analyse").json() == {"queued": 0}   # nothing twice
    while not IDENTITY_QUEUE.empty():
        IDENTITY_QUEUE.get_nowait()
    assert client.delete(f"/api/identities/{made['id']}").json() == {"deleted": True}
    assert (folder / "01 Modern Girl.wav").exists()           # the original folder is untouched


def test_a_song_unticked_while_it_waits_is_skipped(client, tmp_path, monkeypatch):
    import asyncio
    _, folder = make_folder(tmp_path, monkeypatch)
    made = client.post("/api/identities", json={"name": "Me", "trigger_word": "me", "folder": str(folder), "consent": True}).json()
    song = next(s for s in made["songs"] if s["include"])
    jobs.set_song(song["id"], include=0, vocals_state="queued", lyrics_state="queued", score_state="queued")
    asyncio.run(jobs.prepare_song(song["id"]))
    asyncio.run(jobs.run_identity_job("identity_score", song["id"]))
    row = one("SELECT * FROM identity_songs WHERE id = ?", (song["id"],))
    assert (row["vocals_state"], row["lyrics_state"], row["score_state"], row["stored_path"]) == ("none", "none", "none", None)


def test_editing_the_identity_changes_captions_and_export_names_the_host_folder(client, tmp_path, monkeypatch):
    _, folder = make_folder(tmp_path, monkeypatch)
    made = client.post("/api/identities", json={"name": "Me", "trigger_word": "me", "voice": "male", "folder": str(folder), "consent": True}).json()
    edited = client.put(f"/api/identities/{made['id']}", json={"description": "pop rock, electric guitars, bass, drums"}).json()
    assert all(s["caption"].startswith("me, pop rock, electric guitars, bass, drums, male vocal") for s in edited["songs"])
    song = next(s for s in edited["songs"] if s["include"])
    jobs.set_song(song["id"], stored_path=str(folder / "01 Modern Girl.wav"), lyrics="[Verse]\nla")
    monkeypatch.setattr(config, "DATA_DIR_HOST", "/home/me/yue2/data")
    out = client.post(f"/api/identities/{made['id']}/export").json()
    assert out["folder"] == f"/home/me/yue2/data/identities/{made['id']}/dataset" and len(out["written"]) == 1


def test_parse_stem_and_lrclib_lookup_with_transcript_verification(tmp_path, monkeypatch):
    import asyncio
    from pathlib import Path
    from app.db import set_setting

    assert identities.parse_stem("03 The Harbour Band - Glass Orchard [Official Audio]") == ("The Harbour Band", "Glass Orchard")
    assert identities.parse_stem("01_Morning_Light_(Official_Video)") == (None, "Morning Light")

    lrc_text = "[00:10.00] Walking down the harbour wall\n[00:14.50] Watching all the seagulls fall\n"
    parsed = identities.parse_lrc(lrc_text, duration=20.0)
    assert parsed == [
        {"start": 10.0, "end": 14.5, "text": "Walking down the harbour wall"},
        {"start": 14.5, "end": 20.0, "text": "Watching all the seagulls fall"},
    ]

    studio_plain = (
        "Walking down the harbour wall\nWatching all the seagulls fall\n\n"
        "Silver water in the bay\nCarry all the clouds away\n\n"
        "Silver water in the bay\nCarry all the clouds away"
    )
    whisper_lines = [
        {"start": 10.0, "end": 14.0, "text": "Walking down the harbour wall"},
        {"start": 14.5, "end": 18.0, "text": "Watching all the seagulls fall"},
        {"start": 22.0, "end": 26.0, "text": "Silver water in the bay"},
        {"start": 26.5, "end": 30.0, "text": "Carry all the clouds away"},
    ]
    assert identities.lyrics_match_transcript(studio_plain, " ".join(l["text"] for l in whisper_lines)) >= 0.8
    assert identities.lyrics_match_transcript("Completely unrelated words about spaceships", " ".join(l["text"] for l in whisper_lines)) == 0.0

    monkeypatch.setattr(identities, "transcribe", lambda *a, **kw: list(whisper_lines))
    monkeypatch.setattr(identities, "fetch_lrclib", lambda artist, title, dur: {
        "lyrics": studio_plain,
        "synced": None,
        "lines": None,
        "artist": artist or "The Harbour Band",
        "title": title,
        "duration": 180.0,
    })
    set_setting("lyrics.lrclib", "on")
    found = asyncio.run(jobs.hear_all(Path("/nowhere/vocals.flac"), 180.0, title="Glass Orchard", artist="The Harbour Band"))
    assert found["model"] == "LRCLIB"
    assert "LRCLIB" in found["method"]
    assert found["lrclib"] == studio_plain
    assert len(found["lines"]) == 6

    # Rejects an LRCLIB hit whose words do not match what Whisper heard on the recording
    monkeypatch.setattr(identities, "fetch_lrclib", lambda artist, title, dur: {
        "lyrics": "Completely different song with unrelated words that do not appear in the vocal track at all",
        "synced": None,
        "lines": None,
        "artist": "Wrong Artist",
        "title": title,
        "duration": 180.0,
    })
    rejected = asyncio.run(jobs.hear_all(Path("/nowhere/vocals.flac"), 180.0, title="Glass Orchard", artist="The Harbour Band"))
    assert rejected["method"] == "Whisper" and rejected["llm"] is None


def test_heuristic_sections_and_plain_to_sections_tag_repeated_choruses():
    plain = (
        "First verse walking down the road\nCarrying a heavy load\n\n"
        "Shine on silver moon tonight\nGuide us through the fading light\n\n"
        "Second verse waiting by the gate\nHoping that it's not too late\n\n"
        "Shine on silver moon tonight\nGuide us through the fading light"
    )
    tagged = identities.plain_to_sections(plain)
    assert tagged == (
        "[Verse]\nFirst verse walking down the road\nCarrying a heavy load\n\n"
        "[Chorus]\nShine on silver moon tonight\nGuide us through the fading light\n\n"
        "[Verse]\nSecond verse waiting by the gate\nHoping that it's not too late\n\n"
        "[Chorus]\nShine on silver moon tonight\nGuide us through the fading light"
    )

    timed = [
        {"start": 10.0, "end": 13.0, "text": "First verse walking down the road"},
        {"start": 13.5, "end": 16.5, "text": "Carrying a heavy load"},
        {"start": 20.0, "end": 23.0, "text": "Shine on silver moon tonight"},
        {"start": 23.5, "end": 26.5, "text": "Guide us through the fading light"},
        {"start": 31.0, "end": 34.0, "text": "Second verse waiting by the gate"},
        {"start": 34.5, "end": 37.5, "text": "Hoping that it's not too late"},
        {"start": 42.0, "end": 45.0, "text": "Shine on silver moon tonight"},
        {"start": 45.5, "end": 48.5, "text": "Guide us through the fading light"},
    ]
    # Without SheetSage sections, tag_lyrics uses the repetition heuristic and marks [Intro], [Verse], [Chorus]
    auto_tagged = identities.tag_lyrics(timed, [], 60.0)
    assert auto_tagged.startswith("[Intro]\n\n[Verse]\nFirst verse")
    assert auto_tagged.count("[Chorus]") == 2
    assert auto_tagged.count("[Verse]") == 2


def test_audio_key_and_tempo_krumhansl_schmuckler_and_fallback():
    sr = identities.CHUNK_RATE
    duration = 12.0
    t = np.arange(int(sr * duration), dtype=np.float32) / sr
    # Synthesize A minor triad (A3=220, C4=261.63, E4=329.63, A4=440) pulsed at 120 BPM (2 Hz)
    chord = (
        1.0 * np.sin(2 * np.pi * 220.0 * t)
        + 0.8 * np.sin(2 * np.pi * 261.63 * t)
        + 0.8 * np.sin(2 * np.pi * 329.63 * t)
        + 0.6 * np.sin(2 * np.pi * 440.0 * t)
    )
    beat_phase = (t * 2.0) % 1.0
    envelope = np.exp(-6.0 * beat_phase)
    wave = (chord * envelope * 0.3).astype(np.float32)

    key, bpm = identities.audio_key_and_tempo(wave, sr=sr)
    assert key == "A minor"
    assert bpm is not None and abs(bpm - 120) <= 3

    # key_and_tempo fills in missing K: or Q: from audio when ABC omits them
    assert identities.key_and_tempo("X:1\nM:4/4\n", wave) == ("A minor", bpm)
    assert identities.key_and_tempo("X:1\nK:G\n", wave) == ("G major", bpm)

