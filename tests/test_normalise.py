"""A quiet take can be brought up to the usual loudness when asked, and put back.
Nothing is normalised without being asked."""
import subprocess
from pathlib import Path

from app import config
from app.db import execute, one, set_setting
from app.library import loudness, normalised_path, original_path

from conftest import make_take


def quiet_tone(path):
    """A 44.1 kHz stereo tone far below the usual level, like a weak render."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "quiet", "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
                    "-af", "volume=0.15", "-ac", "2", "-ar", "44100", str(path)], check=True)
    return path


def rate_of(path):
    return subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "stream=sample_rate", "-of", "csv=p=0", str(path)],
                          capture_output=True, text=True, check=True).stdout.strip()


def test_normalising_lifts_a_weak_take_and_keeps_the_rendered_file(client, tmp_path):
    audio = quiet_tone(tmp_path / "takes" / "t1" / "song.flac")
    before = loudness(audio)
    take = make_take(audio_path=str(audio))
    assert before < config.WEAK_RENDER_DB

    execute("UPDATE takes SET loudness = ? WHERE id = ?", (before, take["id"]))

    assert client.post(f"/api/takes/{take['id']}/normalise").json() == {"normalised": True}
    louder_file = normalised_path(audio)
    louder = loudness(louder_file)
    assert louder > config.WEAK_RENDER_DB
    assert loudness(audio) == before, "the file as rendered is never changed"
    assert rate_of(louder_file) == "44100", "loudnorm works at 192 kHz; the take comes back at its own rate"
    row = one("SELECT normalised, loudness, audio_path FROM takes WHERE id = ?", (take["id"],))
    assert row["normalised"] == 1 and row["audio_path"] == str(louder_file)
    assert row["loudness"] == before, "the level recorded is the one it was rendered at"

    # Twice gives the same: it always starts from the file as rendered.
    client.post(f"/api/takes/{take['id']}/normalise")
    assert abs(loudness(louder_file) - louder) < 0.2


def test_undo_puts_back_the_rendered_level(client, tmp_path):
    audio = quiet_tone(tmp_path / "takes" / "t2" / "song.flac")
    before = loudness(audio)
    take = make_take(audio_path=str(audio))
    client.post(f"/api/takes/{take['id']}/normalise")

    answer = client.post(f"/api/takes/{take['id']}/normalise?undo=true").json()
    assert answer == {"normalised": False} and loudness(audio) == before
    assert not normalised_path(audio).exists()
    row = one("SELECT normalised, audio_path FROM takes WHERE id = ?", (take["id"],))
    assert row["normalised"] == 0 and row["audio_path"] == str(audio)
    assert client.post(f"/api/takes/{take['id']}/normalise?undo=true").status_code == 409


def test_a_take_is_left_as_rendered_unless_asked(client, tmp_path):
    audio = quiet_tone(tmp_path / "takes" / "t3" / "song.flac")
    make_take(audio_path=str(audio))
    listed = client.get("/api/takes").json()[0]
    assert listed["normalise"] == 0 and listed["normalised"] == 0 and not normalised_path(audio).exists()


def test_a_take_without_audio_cannot_be_normalised(client):
    take = make_take()
    assert client.post(f"/api/takes/{take['id']}/normalise").status_code == 404


def test_a_take_asked_to_be_normalised_is_when_its_render_finishes(monkeypatch, data_dir):
    import asyncio

    from app import jobs
    from test_jobs import ABC, FakeEngine, render_history, use

    rendered = quiet_tone(data_dir / "engine" / "take_00001_.flac")
    monkeypatch.setattr(config, "ENGINE_OUTPUT_DIR", data_dir / "engine-output")
    # A cap near the three-second tone: a render far shorter than its score would be
    # tried again, which is another test's business.
    take = make_take(status="queued", abc=ABC, title="Quiet", max_duration=10.0)
    execute("UPDATE takes SET cap_typed = 1 WHERE id = ?", (take["id"],))   # typed: not raised to fit the score
    execute("UPDATE takes SET normalise = 1 WHERE id = ?", (take["id"],))
    use(monkeypatch, FakeEngine([render_history()], audio=rendered))
    set_setting("normalise.level", "-16")
    asyncio.run(jobs.run_job("render", take["id"]))
    row = one("SELECT * FROM takes WHERE id = ?", (take["id"],))
    assert row["status"] == "done" and row["normalised"] == 1 and row["normalised_to"] == -16.0
    assert loudness(Path(row["audio_path"])) > config.WEAK_RENDER_DB
    assert row["loudness"] < config.WEAK_RENDER_DB, "still known as weak: the level is the one it was rendered at"
    assert row["audio_path"].endswith("quiet.normalised.flac")
    assert Path(row["audio_path"]).with_name("quiet.flac").exists()


def test_the_form_choice_is_kept_on_the_take(client):
    made = client.post("/api/songs", json={"lyrics": "[Verse]\nla la", "normalise": True}).json()
    assert one("SELECT normalise FROM takes WHERE id = ?", (made["id"],))["normalise"] == 1
    plain = client.post("/api/songs", json={"lyrics": "[Verse]\nla la"}).json()
    assert one("SELECT normalise FROM takes WHERE id = ?", (plain["id"],))["normalise"] == 0


def test_a_take_normalised_before_keeps_its_rendered_level_once_read_again(client, tmp_path):
    from app.library import fill_loudness

    audio = quiet_tone(tmp_path / "takes" / "t4" / "song.flac")
    before = loudness(audio)
    take = make_take(audio_path=str(audio))
    client.post(f"/api/takes/{take['id']}/normalise")
    execute("UPDATE takes SET loudness = NULL WHERE id = ?", (take["id"],))
    assert fill_loudness() == 1
    assert one("SELECT loudness FROM takes WHERE id = ?", (take["id"],))["loudness"] == before


def test_the_weak_note_on_a_normalised_take_can_be_dismissed(client, tmp_path):
    take = make_take(audio_path=str(quiet_tone(tmp_path / "takes" / "t5" / "song.flac")))
    assert client.get("/api/takes").json()[0]["weak_dismissed"] == 0
    assert client.post(f"/api/takes/{take['id']}/weak/dismiss").json() == {"dismissed": True}
    assert one("SELECT weak_dismissed FROM takes WHERE id = ?", (take["id"],))["weak_dismissed"] == 1
    assert client.post("/api/takes/nosuch/weak/dismiss").status_code == 404


def test_a_file_open_elsewhere_is_waited_for_then_reported(monkeypatch, tmp_path):
    """Windows will not replace a file another program has open.  A player lets go in
    a moment, so it is tried again; one that does not is reported as open."""
    import pytest

    from app import library

    src, dest = tmp_path / "new.flac", tmp_path / "old.flac"
    src.write_bytes(b"new")
    dest.write_bytes(b"old")
    real, refusals = library.os.replace, []

    def busy_twice(a, b):
        if len(refusals) < 2:
            refusals.append(1)
            raise PermissionError("in use")
        real(a, b)
    monkeypatch.setattr(library.os, "replace", busy_twice)
    monkeypatch.setattr(library.time, "sleep", lambda s: None)
    library.replace_file(src, dest)
    assert dest.read_bytes() == b"new" and len(refusals) == 2

    monkeypatch.setattr(library.os, "replace", lambda a, b: (_ for _ in ()).throw(PermissionError("in use")))
    with pytest.raises(PermissionError):
        library.replace_file(dest, tmp_path / "x.flac", tries=3)


def test_normalising_never_touches_the_file_being_played(client, tmp_path, monkeypatch):
    """On Windows a file that is open cannot be replaced, and a player keeps the take
    open while it streams.  The louder copy is a new file, so the one playing is left
    alone however long it is held."""
    from app import library

    audio = quiet_tone(tmp_path / "takes" / "t6" / "song.flac")
    take = make_take(audio_path=str(audio))
    replaced = []
    real = library.os.replace
    monkeypatch.setattr(library.os, "replace", lambda a, b: (replaced.append(Path(b)), real(a, b)))
    assert client.post(f"/api/takes/{take['id']}/normalise").status_code == 200
    assert audio not in replaced


def test_a_take_normalised_in_place_by_the_first_version_is_converted(client, tmp_path):
    """song.flac louder and song.original.flac as rendered become song.flac as rendered
    and song.normalised.flac louder."""
    from app.library import convert_old_normalised

    folder = tmp_path / "takes" / "t7"
    rendered = quiet_tone(folder / "song.original.flac")
    before = loudness(rendered)
    louder = folder / "song.flac"
    louder.write_bytes(b"louder")
    take = make_take(audio_path=str(louder))
    execute("UPDATE takes SET normalised = 1 WHERE id = ?", (take["id"],))
    assert convert_old_normalised() == 1
    assert loudness(folder / "song.flac") == before and (folder / "song.normalised.flac").read_bytes() == b"louder"
    assert one("SELECT audio_path FROM takes WHERE id = ?", (take["id"],))["audio_path"] == str(folder / "song.normalised.flac")
    assert convert_old_normalised() == 0


def test_renaming_files_at_start_keeps_a_normalised_take_on_its_louder_copy(client):
    from app.library import relayout, take_audio_path

    take = make_take(title="Loud One")
    rendered = quiet_tone(take_audio_path(take["id"], "Loud One"))
    louder = normalised_path(rendered)
    louder.write_bytes(rendered.read_bytes())
    execute("UPDATE takes SET audio_path = ?, normalised = 1 WHERE id = ?", (str(louder), take["id"]))
    relayout()
    assert one("SELECT audio_path FROM takes WHERE id = ?", (take["id"],))["audio_path"] == str(louder)


# ---------- one gain for the whole take ----------
def peaky_song(path):
    """A quiet opening, then a louder part with clicks near full scale: a take whose
    peaks are already high, so the gain it needs would push them past the ceiling."""
    path.parent.mkdir(parents=True, exist_ok=True)
    expr = "if(lt(t,8), 0.01, 0.08)*sin(2*PI*440*t) + if(gte(t,8)*lt(mod(t,1),0.002), 0.3, 0)"
    subprocess.run(["ffmpeg", "-v", "quiet", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d=20",
                    "-ac", "2", "-sample_fmt", "s16", str(path)], check=True)
    return path


def measure(path) -> dict:
    import json, re
    err = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(path), "-af",
                          "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    return json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err).group(0))


def short_term(path) -> list[float]:
    import re
    err = subprocess.run(["ffmpeg", "-v", "verbose", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return [float(s) for s in re.findall(r"t:\s*[\d.]+\s+TARGET.*?S:\s*(-?[\d.]+)", err)]


def test_the_gain_holds_steady_where_the_peaks_are_already_high(client, tmp_path):
    from app.library import NORMAL_LUFS, NORMAL_PEAK
    audio = peaky_song(tmp_path / "takes" / "peaky" / "peaky.flac")
    take = make_take(title="Peaky", audio_path=str(audio))
    assert client.post(f"/api/takes/{take['id']}/normalise").json() == {"normalised": True}
    louder = normalised_path(audio)

    got = measure(louder)
    assert abs(float(got["input_i"]) - NORMAL_LUFS) < 0.5
    assert float(got["input_tp"]) <= NORMAL_PEAK + 0.05
    # Lifted by the same amount from start to end, every two seconds. loudnorm's
    # dynamic mode rode the level: here by 1.7 dB, on a real take by 10 dB.
    before, after = short_term(audio), short_term(louder)
    gains = [after[i] - before[i] for i in range(30, min(len(before), len(after)), 20)]
    assert min(gains) > 5 and max(gains) - min(gains) < 0.5


def test_a_normalised_take_keeps_the_rendered_rate_and_depth(client, tmp_path):
    audio = peaky_song(tmp_path / "takes" / "depth" / "depth.flac")
    take = make_take(title="Depth", audio_path=str(audio))
    client.post(f"/api/takes/{take['id']}/normalise")
    fmt = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "stream=sample_rate,sample_fmt", "-of", "csv=p=0",
                          str(normalised_path(audio))], capture_output=True, text=True).stdout.strip()
    assert fmt == "s16,48000"


def test_a_silent_take_is_refused_rather_than_amplified(client, tmp_path):
    audio = tmp_path / "takes" / "silent" / "silent.flac"
    audio.parent.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-v", "quiet", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "3", str(audio)],
                   check=True)
    take = make_take(title="Silent", audio_path=str(audio))
    assert client.post(f"/api/takes/{take['id']}/normalise").status_code == 500
    assert not normalised_path(audio).exists()


# ---------- the level, from Settings ----------
def test_the_level_comes_from_settings_and_is_recorded(client, tmp_path):
    audio = peaky_song(tmp_path / "takes" / "level" / "level.flac")
    take = make_take(title="Level", audio_path=str(audio))
    listed = lambda: next(t for t in client.get("/api/takes").json() if t["id"] == take["id"])

    client.post(f"/api/takes/{take['id']}/normalise")
    assert abs(float(measure(normalised_path(audio))["input_i"]) + 14) < 0.5
    assert listed()["normalised_to"] == -14.0

    client.post(f"/api/takes/{take['id']}/normalise?undo=true")
    assert listed()["normalised_to"] is None
    assert client.put("/api/settings", json={"key": "normalise.level", "value": "-11"}).status_code == 200
    client.post(f"/api/takes/{take['id']}/normalise")
    assert abs(float(measure(normalised_path(audio))["input_i"]) + 11) < 0.5
    assert listed()["normalised_to"] == -11.0


def test_only_the_offered_levels_can_be_set(client):
    assert client.put("/api/settings", json={"key": "normalise.level", "value": "-3"}).status_code == 400
    item = {s["key"]: s for s in client.get("/api/settings").json()["settings"]}["normalise.level"]
    assert item["value"] == "-14" and [o["value"] for o in item["options"]] == ["-16", "-14", "-11"]


def test_a_take_stopped_by_its_cap_is_faded_out(tmp_path):
    """The model does not always stop at the end of its score; one the cap stopped is
    faded over its last seconds rather than cut off at full level (#24)."""
    import json
    from app.library import CAP_FADE, fade_out_end
    take = tmp_path / "take.flac"
    subprocess.run(["ffmpeg", "-v", "quiet", "-f", "lavfi", "-i", "sine=frequency=440:duration=12",
                    "-af", "volume=0.5", "-ac", "2", "-ar", "48000", "-sample_fmt", "s16", str(take)], check=True)
    fade_out_end(take)

    def level(start, length):
        out = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-ss", str(start), "-t", str(length), "-i", str(take),
                              "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
        return float(out.split("mean_volume:")[1].split("dB")[0])

    assert level(2, 1) > -40, "before the fade, the tone as it was"
    assert level(11.6, 0.35) < level(2, 1) - 20, "the last moments close to silence"
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=sample_fmt,sample_rate:format=duration",
                                       "-of", "json", str(take)], capture_output=True, text=True).stdout)
    assert abs(float(probe["format"]["duration"]) - 12) < 0.05 and CAP_FADE < 12
    assert probe["streams"][0]["sample_fmt"] == "s16" and probe["streams"][0]["sample_rate"] == "48000"
    assert not list(tmp_path.glob("*.fading.*")), "no work file left behind"
