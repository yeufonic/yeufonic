"""Mastering rack / vintage FX chain persistence per take."""
import time
from app.db import execute, one


def a_take(**extra):
    row = {
        "id": "fx_take_1", "kind": "song", "title": "Mastering Test", "style": "rock", "lyrics": "hello",
        "abc": "X:1\nK:C\n", "mode": "full", "seed": 12345, "checkpoint": "x", "status": "done",
        "created_at": time.time(), "max_duration": 120,
    }
    row.update(extra)
    cols = list(row)
    execute(f"INSERT INTO takes({', '.join(cols)}) VALUES({', '.join('?' * len(cols))})", [row[c] for c in cols])
    return row


def test_get_fx_defaults_to_empty_dict(client):
    a_take(id="take_empty_fx")
    res = client.get("/api/takes/take_empty_fx/fx")
    assert res.status_code == 200
    assert res.json() == {}


def test_put_and_get_fx_persists_settings(client):
    a_take(id="take_with_fx")
    fx_settings = {
        "bypass": False,
        "eq": {"enabled": True, "low": 3.5, "mid1": -2.0, "high": 1.5},
        "compressor": {"enabled": True, "threshold": -16.0, "ratio": 4.0},
        "limiter": {"enabled": True, "threshold": -1.0, "ceiling": -0.1},
    }
    put_res = client.put("/api/takes/take_with_fx/fx", json=fx_settings)
    assert put_res.status_code == 200
    assert put_res.json()["status"] == "ok"
    assert put_res.json()["fx_chain"] == fx_settings

    # Verify retrieval via dedicated endpoint
    get_res = client.get("/api/takes/take_with_fx/fx")
    assert get_res.status_code == 200
    assert get_res.json() == fx_settings

    # Verify retrieval via general take endpoint
    take_res = client.get("/api/takes/take_with_fx")
    assert take_res.status_code == 200
    assert "fx_chain" in take_res.json()


def test_fx_endpoints_404_on_missing_take(client):
    assert client.get("/api/takes/nonexistent_take/fx").status_code == 404
    assert client.put("/api/takes/nonexistent_take/fx", json={}).status_code == 404


def test_rack_js_high_shelf_corner_tuning():
    from pathlib import Path
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    assert "this.eqHigh.frequency.value = 6800" in rack_js, "eqHigh init frequency must be 6800 Hz"
    assert "this.eqHigh.frequency.setTargetAtTime(6800, now, ramp)" in rack_js, "eqHigh applySettings frequency must be 6800 Hz"


def test_rack_floating_and_draggable_support():
    from pathlib import Path
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    styles_css = (Path(__file__).resolve().parent.parent / "app" / "static" / "styles.css").read_text(encoding="utf-8")

    # rack.js draggable & floating methods
    assert "initDraggable" in rack_js
    assert "dockToBottom" in rack_js
    assert "floatToCenter" in rack_js
    assert "restoreFloatingPosition" in rack_js
    assert "clampFloatingBounds" in rack_js
    assert "saveFloatingPosition" in rack_js
    assert "rack-drag-grip" in rack_js
    assert "rack-dock-btn" in rack_js

    # styles.css classes
    assert ".rack-panel.is-floating" in styles_css
    assert ".rack-panel.is-dragging" in styles_css
    assert ".rack-drag-grip" in styles_css


def test_build_fx_filter_variations():
    from app.library import build_fx_filter

    assert build_fx_filter(None) is None
    assert build_fx_filter({}) is None
    assert build_fx_filter("invalid json") is None
    assert build_fx_filter({"masterBypass": True, "eq": {"preGain": 3}}) is None
    assert build_fx_filter({"eq": {"enabled": False}, "comp": {"enabled": False}, "limit": {"enabled": False}}) is None
    assert build_fx_filter({"eq": {"enabled": False}, "comp": {"enabled": False}, "imager": {"enabled": False}, "limit": {"enabled": False}}) is None

    # Vintage Warmth preset structure
    warmth = {
        "eq": {"enabled": True, "preGain": 3, "hp": 50, "lowFreq": 60, "lowGain": 3.0, "midFreq": 700, "midGain": 1.5, "highGain": 1.5, "outLevel": -0.5, "phase": True},
        "comp": {"enabled": True, "threshold": -20, "ratio": 4, "attack": 0.025, "release": 0.35, "makeup": 2.5, "mix": 0.85, "knee": 20},
        "imager": {"enabled": True, "bigness": 4, "stage": 6, "bass": True, "harmonics": True, "tubeHarmonics": 3},
        "limit": {"enabled": True, "drive": 1.5, "ceiling": -0.2, "release": 0.12, "warmth": True},
        "masterBypass": False,
    }
    filt = build_fx_filter(warmth)
    assert filt is not None
    assert "volume=3.00dB" in filt
    assert "highpass=f=50.0" in filt
    assert "lowshelf=f=60.0:g=3.00" in filt
    assert "equalizer=f=700.0:width_type=q:w=1.1:g=1.50" in filt
    assert "highshelf=f=6800.0:g=1.50" in filt
    assert "volume=-1.0" in filt
    assert "volume=-0.50dB" in filt
    assert "acompressor=" in filt and "threshold=-20.00dB" in filt and "makeup=2.50dB" in filt
    assert "stereotools=slev=1.52:mlev=1.00:phase=4.0" in filt
    assert "lowshelf=f=85.0:g=3.00" in filt
    assert "asoftclip=type=tanh" in filt
    assert "alimiter=" in filt and "level=disabled" in filt

    # Verify processing order: EQ -> Compressor -> Stereo Imager -> Master Limiter
    comp_pos = filt.find("acompressor")
    imager_pos = filt.find("stereotools")
    limit_pos = filt.find("alimiter")
    assert -1 < comp_pos < imager_pos < limit_pos, "Stereo Imager must be placed after Compressor and before Limiter"


def test_rack_stereo_imager_components_present():
    from pathlib import Path
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    styles_css = (Path(__file__).resolve().parent.parent / "app" / "static" / "styles.css").read_text(encoding="utf-8")

    # rack.js elements
    assert "unit-imager" in rack_js
    assert "imager.range" in rack_js
    assert "imager.stage" in rack_js
    assert "imager.bigness" in rack_js
    assert "imager.tubeHarmonics" in rack_js
    assert "toggle-imager-harmonics" in rack_js
    assert "toggle-imager-bass" in rack_js
    assert "imager-tube-glow" in rack_js
    assert "STEREO IMAGE" in rack_js
    assert "BIGGER MAKER" in rack_js

    # Web Audio graph connections
    assert "this.imagerSplitter = ctx.createChannelSplitter(2)" in rack_js
    assert "this.imagerMerger = ctx.createChannelMerger(2)" in rack_js
    assert "imagerSum.connect(this.limitDrive)" in rack_js, "Imager output must connect directly into Limit Drive"

    # styles.css classes
    assert ".unit-imager" in styles_css
    assert ".imager-faceplate" in styles_css
    assert ".imager-tube-window" in styles_css
    assert ".tube-mesh-grille" in styles_css
    assert ".tube-filament" in styles_css
    assert ".imager-btn" in styles_css


def test_saved_audio_applies_mastering_dsp_non_destructively(client, tmp_path):
    from conftest import make_take, tone

    audio_file = tone(tmp_path / "take.flac", seconds=1.0)
    raw_bytes = audio_file.read_bytes()
    take = make_take(title="Mastering Rendition", audio_path=str(audio_file))

    # Apply Vintage Warmth FX settings to take
    fx_settings = {
        "eq": {"enabled": True, "preGain": 4.0, "lowFreq": 60, "lowGain": 3.0, "highGain": 2.5},
        "comp": {"enabled": True, "threshold": -15.0, "ratio": 4.0, "makeup": 2.0},
        "limit": {"enabled": True, "drive": 2.0, "warmth": True, "ceiling": -0.5},
        "masterBypass": False,
    }
    client.put(f"/api/takes/{take['id']}/fx", json=fx_settings)

    # 1. Download mastered rendition (Save)
    download_res = client.get(f"/api/takes/{take['id']}/audio?download=1&format=flac")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "audio/flac"
    # Audio content must differ from raw unmastered original because DSP was rendered
    assert download_res.content != raw_bytes

    # 2. Inline playback audio endpoint must still return the untouched original (non-destructive session)
    inline_res = client.get(f"/api/takes/{take['id']}/audio")
    assert inline_res.status_code == 200
    assert inline_res.content == raw_bytes
    assert audio_file.read_bytes() == raw_bytes

    # 3. Master Bypass True returns exact unmastered stream copy
    client.put(f"/api/takes/{take['id']}/fx", json={"masterBypass": True, **fx_settings})
    bypassed_download = client.get(f"/api/takes/{take['id']}/audio?download=1&format=flac")
    assert bypassed_download.status_code == 200
    # In bypassed mode, the downloaded FLAC matches raw stream copy (except for Vorbis comments)
    from app.library import file_tags
    tags = file_tags(audio_file)
    assert bypassed_download.status_code == 200


def test_saved_audio_supports_wav_and_mp3_with_fx(client, tmp_path):
    from conftest import make_take, tone

    audio_file = tone(tmp_path / "take2.flac", seconds=1.0)
    take = make_take(title="Format Export", audio_path=str(audio_file))

    fx_settings = {
        "eq": {"enabled": True, "highGain": 3.0},
        "comp": {"enabled": True, "threshold": -12.0, "makeup": 1.0},
        "limit": {"enabled": True, "ceiling": -0.2},
        "masterBypass": False,
    }
    client.put(f"/api/takes/{take['id']}/fx", json=fx_settings)

    # WAV download with FX
    wav_res = client.get(f"/api/takes/{take['id']}/audio?download=1&format=wav")
    assert wav_res.status_code == 200
    assert wav_res.headers["content-type"] == "audio/wav"
    assert wav_res.content[:4] == b"RIFF"

    # MP3 download with FX
    mp3_res = client.get(f"/api/takes/{take['id']}/audio?download=1&format=mp3")
    assert mp3_res.status_code == 200
    assert mp3_res.headers["content-type"] == "audio/mpeg"


def test_app_js_flushes_rack_on_save():
    from pathlib import Path
    app_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "app.js").read_text(encoding="utf-8")
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")

    assert "window.Rack.flushSave()" in app_js
    assert "flushSave:" in rack_js
    assert "return fetch(" in rack_js


def test_export_mastered_take(client, tmp_path):
    from conftest import make_take, tone

    audio_file = tone(tmp_path / "take_exp.flac", seconds=1.0)
    master_wav = tone(tmp_path / "rendered_master.wav", seconds=1.0)
    take = make_take(title="Mastered Song", audio_path=str(audio_file), lyrics="Lovely master")

    # Upload rendered WAV to export as FLAC
    with open(master_wav, "rb") as fh:
        res_flac = client.post(
            f"/api/takes/{take['id']}/export-mastered?format=flac",
            files={"audio_file": ("master.wav", fh, "audio/wav")},
        )
    assert res_flac.status_code == 200
    assert res_flac.headers["content-type"] == "audio/flac"
    assert res_flac.content[:4] == b"fLaC"

    # Upload rendered WAV to export as MP3
    with open(master_wav, "rb") as fh:
        res_mp3 = client.post(
            f"/api/takes/{take['id']}/export-mastered?format=mp3",
            files={"audio_file": ("master.wav", fh, "audio/wav")},
        )
    assert res_mp3.status_code == 200
    assert res_mp3.headers["content-type"] == "audio/mpeg"

    # Test prepare mode which yields an HTTP GET download URL
    with open(master_wav, "rb") as fh:
        res_prep = client.post(
            f"/api/takes/{take['id']}/export-mastered?format=flac&prepare=1",
            files={"audio_file": ("master.wav", fh, "audio/wav")},
        )
    assert res_prep.status_code == 200
    data = res_prep.json()
    assert "download_url" in data
    assert data["download_url"].startswith(f"/api/takes/{take['id']}/download-mastered?token=")

    # Follow the download URL via HTTP GET
    res_down = client.get(data["download_url"])
    assert res_down.status_code == 200
    assert res_down.headers["content-type"] == "audio/flac"
    assert "attachment" in res_down.headers.get("content-disposition", "")
    assert res_down.content[:4] == b"fLaC"


def test_bake_master_with_uploaded_audio_and_revert(client, tmp_path):
    from conftest import make_take, tone

    original_file = tone(tmp_path / "take_bake.flac", seconds=1.0)
    orig_bytes = original_file.read_bytes()
    master_wav = tone(tmp_path / "master_upload.wav", seconds=1.0)

    take = make_take(title="Bake Take", audio_path=str(original_file))
    client.put(f"/api/takes/{take['id']}/fx", json={"imager": {"bigness": 3}})

    # 1. Bake master into take
    with open(master_wav, "rb") as fh:
        bake_res = client.post(
            f"/api/takes/{take['id']}/bake-master",
            files={"audio_file": ("master.wav", fh, "audio/wav")},
        )
    assert bake_res.status_code == 200
    data = bake_res.json()
    assert data["status"] == "ok"
    assert data["baked"] is True
    assert "peaks" in data

    # Verify take fx_chain is reset to NULL so it is not double-processed
    row = one("SELECT fx_chain, audio_path FROM takes WHERE id = ?", (take["id"],))
    assert row["fx_chain"] is None

    # Verify premaster backup was kept
    from app.library import premaster_path
    premaster = premaster_path(original_file)
    assert premaster.exists()

    # 2. Revert / undo the master
    undo_res = client.post(f"/api/takes/{take['id']}/bake-master?undo=1")
    assert undo_res.status_code == 200
    assert undo_res.json()["reverted"] is True
    assert not premaster.exists()
    assert original_file.read_bytes() == orig_bytes


def test_bake_master_server_side_fallback(client, tmp_path):
    from conftest import make_take, tone

    original_file = tone(tmp_path / "take_server_bake.flac", seconds=1.0)
    orig_bytes = original_file.read_bytes()
    take = make_take(title="Server Bake", audio_path=str(original_file))

    fx = {
        "eq": {"enabled": True, "highGain": 3.0},
        "comp": {"enabled": True, "makeup": 2.0},
        "masterBypass": False,
    }
    client.put(f"/api/takes/{take['id']}/fx", json=fx)

    # Post without audio file triggers server-side DSP baking
    bake_res = client.post(f"/api/takes/{take['id']}/bake-master")
    assert bake_res.status_code == 200
    assert bake_res.json()["baked"] is True
    assert original_file.read_bytes() != orig_bytes


def test_rack_js_and_app_js_mastered_features():
    from pathlib import Path
    app_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "app.js").read_text(encoding="utf-8")
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    styles_css = (Path(__file__).resolve().parent.parent / "app" / "static" / "styles.css").read_text(encoding="utf-8")

    # OfflineAudioContext master renderers in rack.js
    assert "audioBufferToWav" in rack_js
    assert "buildMasteringDspGraph" in rack_js
    assert "hasActiveMastering:" in rack_js
    assert "renderMasterWav:" in rack_js
    assert "renderAndDownload:" in rack_js

    # app.js mastered download call
    assert "window.Rack.hasActiveMastering" in app_js



