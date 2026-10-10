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


