"""The mastering rack: a take's settings, and a saved file that sounds as the take plays.

The rack is Web Audio in the page (app/static/rack.js). The server keeps a take's settings and
converts a file the page rendered; it never processes the sound itself, because a second
implementation of the chain cannot sound the same as the first."""
import json
import subprocess
import time
from pathlib import Path

import pytest

from app.db import execute, one

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


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
    assert "set(this.eqHigh.frequency, 6800)" in rack_js, "eqHigh applySettings frequency must be 6800 Hz"


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

    # a docked rack is not moved by its header: the drag starts only on a floating one, which alone has the hand
    drag = rack_js[rack_js.index("header.addEventListener('pointerdown'"):rack_js.index("function onPointerMove")]
    assert "if (!panel.classList.contains('is-floating')) { return; }" in drag
    assert ".rack-panel.is-floating .rack-header { cursor: grab; }" in styles_css
    assert ".rack-panel:not(.is-floating) .rack-drag-grip { display: none; }" in styles_css
    # docking keeps where it floated, so Float goes back there, and the first Float is centred by its real height
    dock = rack_js[rack_js.index("dockToBottom: function"):rack_js.index("floatToCenter: function")]
    assert "removeItem('yue2.rackFloat')" not in dock and "kept.isFloating = false" in dock
    centre = rack_js[rack_js.index("floatToCenter: function"):rack_js.index("saveFloatingPosition: function")]
    assert "getBoundingClientRect().height" in centre and "last.top" in centre
    assert ".rack-drag-grip" in styles_css


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


def pcm(source) -> bytes:
    """The samples in a file or in a response's bytes, whatever its tags say."""
    data = source.read_bytes() if isinstance(source, Path) else source
    return subprocess.run(["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "s16le", "-"], input=data,
                          capture_output=True, check=True).stdout


def test_the_server_never_processes_a_download(client, tmp_path):
    """A plain download is the take as kept, whatever settings the take has or the request carries:
    the page renders a mastered file itself and sends it to another route."""
    from conftest import make_take, tone

    audio_file = tone(tmp_path / "take.flac", seconds=1.0)
    raw_bytes = audio_file.read_bytes()
    take = make_take(title="Mastering Rendition", audio_path=str(audio_file))
    fx_settings = {
        "eq": {"enabled": True, "preGain": 4.0, "lowFreq": 60, "lowGain": 3.0, "highGain": 2.5},
        "comp": {"enabled": True, "threshold": -15.0, "ratio": 4.0, "makeup": 2.0},
        "limit": {"enabled": True, "drive": 2.0, "warmth": True, "ceiling": -0.5},
        "masterBypass": False,
    }
    client.put(f"/api/takes/{take['id']}/fx", json=fx_settings)

    download = client.get(f"/api/takes/{take['id']}/audio?download=1&format=flac")
    assert download.status_code == 200
    assert download.headers["content-type"] == "audio/flac"
    assert pcm(download.content) == pcm(audio_file)

    # A page from before this sent its settings to be applied here. It is still open from before an
    # update, and it is told so rather than handed a file without the mastering it asked for.
    sent = client.get(f"/api/takes/{take['id']}/audio",
                      params={"download": 1, "format": "flac", "fx": json.dumps(fx_settings)})
    assert sent.status_code == 409
    assert "reload" in sent.json()["detail"]

    inline = client.get(f"/api/takes/{take['id']}/audio")
    assert inline.content == raw_bytes
    assert audio_file.read_bytes() == raw_bytes


def test_a_download_converts_whatever_the_take_settings(client, tmp_path):
    from conftest import make_take, tone

    audio_file = tone(tmp_path / "take2.flac", seconds=1.0)
    take = make_take(title="Format Export", audio_path=str(audio_file))
    client.put(f"/api/takes/{take['id']}/fx", json={"comp": {"enabled": True, "threshold": -12.0, "makeup": 1.0}})

    wav_res = client.get(f"/api/takes/{take['id']}/audio?download=1&format=wav")
    assert wav_res.status_code == 200
    assert wav_res.headers["content-type"] == "audio/wav"
    assert pcm(wav_res.content) == pcm(audio_file)

    mp3_res = client.get(f"/api/takes/{take['id']}/audio?download=1&format=mp3")
    assert mp3_res.status_code == 200
    assert mp3_res.headers["content-type"] == "audio/mpeg"


def test_no_second_implementation_of_the_chain():
    """The ffmpeg approximation of the rack is gone, and nothing may bring one back unnoticed."""
    import app.library as library

    assert not hasattr(library, "build_fx_filter")
    source = (Path(library.__file__).parent / "library.py").read_text(encoding="utf-8")
    for name in ("acompressor", "stereotools", "asoftclip"):
        assert name not in source, f"{name}: the server must not process the sound"


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
    # what the page rendered is what comes back: converted and tagged, not processed
    assert pcm(res_flac.content) == pcm(master_wav)

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


def test_bake_master_needs_the_rendered_audio(client, tmp_path):
    """Apply to Take sends the file the rack rendered. Without it there is nothing to bake:
    the server does not process the sound, and the take is left alone."""
    from conftest import make_take, tone

    original_file = tone(tmp_path / "take_server_bake.flac", seconds=1.0)
    orig_bytes = original_file.read_bytes()
    take = make_take(title="Server Bake", audio_path=str(original_file))
    fx = {"eq": {"enabled": True, "highGain": 3.0}, "comp": {"enabled": True, "makeup": 2.0}, "masterBypass": False}
    client.put(f"/api/takes/{take['id']}/fx", json=fx)

    bake_res = client.post(f"/api/takes/{take['id']}/bake-master")
    assert bake_res.status_code == 400
    assert original_file.read_bytes() == orig_bytes
    assert one("SELECT fx_chain FROM takes WHERE id = ?", (take["id"],))["fx_chain"] is not None


def test_rack_js_and_app_js_mastered_features():
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    rack_js = (STATIC / "rack.js").read_text(encoding="utf-8")

    # OfflineAudioContext master renderers in rack.js
    assert "audioBufferToWav" in rack_js
    assert "buildMasteringDspGraph" in rack_js
    assert "hasActiveMastering:" in rack_js
    assert "renderMasterWav:" in rack_js
    assert "renderAndDownload:" in rack_js

    # Save asks the rack, and a mastered take goes through the rack's own render
    save = app_js[app_js.index("function runSave()"):app_js.index("function statusLine(")]
    assert "window.Rack.hasActiveMastering" in save
    assert "window.Rack.renderAndDownload(id, fmt)" in save
    assert "fx=" not in save, "settings are not sent to the server to be applied there"


def test_a_page_can_tell_it_is_older_than_the_app(client):
    """The state names the scripts a page loaded now would get, in the words the page's own script
    address carries, so a page left open across an update can see that it is out of date."""
    import re

    assets = client.get("/api/state").json()["assets"]
    page = client.get("/").text
    for script in ("app.js", "rack.js"):
        assert re.search(rf'src="/static/{re.escape(script)}\?v=([^"]+)"', page).group(1) == assets

    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "paintStalePage(data.assets)" in app_js
    assert "document.currentScript" in app_js


# ------------------------------------------------------------------ the chain itself, in node
#
# rack.js runs here against a stand-in for Web Audio that records every node made and every
# value set, so the tests can ask what the chain would do without a browser.

HARNESS = r"""
const fs = require('fs'), vm = require('vm');
// Playback eases a value towards its target and a render sets it, as the real ones do: a render
// that only eased would start from the values the nodes were made with.
function param(v) { return { value: v, setTargetAtTime(x) { this.target = x; } }; }
function heading(p) { return p.target !== undefined ? p.target : p.value; }
function context(rate) {
  const made = [];
  function node(kind, extra) {
    const n = Object.assign({ kind, to: [], connect(other) { this.to.push(other); return other; }, disconnect() {} }, extra || {});
    made.push(n);
    return n;
  }
  return {
    made, sampleRate: rate || 44100, currentTime: 0, state: 'running',
    destination: { kind: 'destination', to: [] },
    createGain: () => node('gain', { gain: param(1) }),
    createBiquadFilter: () => node('biquad', { type: 'lowpass', frequency: param(350), Q: param(1), gain: param(0) }),
    createDynamicsCompressor: () => node('dynamics', { threshold: param(-24), knee: param(30), ratio: param(12),
                                                       attack: param(0.003), release: param(0.25), reduction: 0 }),
    createWaveShaper: () => node('shaper', { curve: null, oversample: 'none' }),
    createDelay: () => node('delay', { delayTime: param(0) }),
    createChannelSplitter: () => node('splitter'),
    createChannelMerger: () => node('merger'),
    createAnalyser: () => node('analyser', { fftSize: 2048 }),
    createMediaElementSource: () => node('element'),
    createBufferSource: () => node('buffer', { start() {} }),
    resume: () => Promise.resolve(),
    decodeAudioData: async () => ({ numberOfChannels: 2, length: 8, sampleRate: rate,
                                     getChannelData: () => new Float32Array(8) }),
    startRendering: async function () { return { numberOfChannels: 2, length: 8, sampleRate: rate,
                                                 getChannelData: () => new Float32Array(8) }; },
  };
}
const offline = [];
const window = {
  addEventListener() {},
  AudioContext: function () { return context(44100); },
  OfflineAudioContext: function (channels, length, rate) { const c = context(rate); c.length = length; offline.push(c); return c; },
  State: { takes: [] },
};
const document = { getElementById: (id) => id === 'audio' ? { addEventListener() {} } : null, querySelectorAll: () => [] };
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const header = new Uint8Array(64);
header.set([0x66, 0x4c, 0x61, 0x43]);                      // fLaC, then STREAMINFO's sample rate
header[18] = input.rate >> 12; header[19] = (input.rate >> 4) & 255; header[20] = (input.rate & 15) << 4;
const sandbox = { window, document, console, setTimeout, clearTimeout, Promise, JSON, Math, Blob, FormData: function () {},
                  localStorage: { getItem: () => input.userPresets ? JSON.stringify(input.userPresets) : null, setItem() {} },
                  fetch: async (url) => ({ ok: true, url, arrayBuffer: async () => header.buffer.slice(0), json: async () => ({}) }) };
vm.runInNewContext(fs.readFileSync(input.rack, 'utf8'), sandbox);
const Rack = window.Rack, Engine = window.RackEngine;

// every value a chain holds (or, for playback, is heading for), in the order its nodes were made
function values(made, live) {
  return made.map((n) => {
    const out = { kind: n.kind };
    for (const k of ['gain', 'frequency', 'Q', 'threshold', 'knee', 'ratio', 'attack', 'release']) {
      if (n[k]) { out[k] = Math.round((live ? heading(n[k]) : n[k].value) * 1e6) / 1e6; }
    }
    if (n.kind === 'biquad') { out.type = n.type; }
    if (n.kind === 'shaper') { out.bent = n.curve ? Math.abs(n.curve[1000] - (1000 * 2 / 1024 - 1)) > 1e-6 : null; }
    return out;
  });
}
(async () => {
  const out = { flat: JSON.parse(JSON.stringify(Rack.settings)), cases: [] };
  out.engaged = input.settings.map((s) => Rack.chainEngaged(s));
  out.upgraded = input.settings.map((s) => Rack.upgradeSettings(s));
  out.presets = input.settings.map((s) => Rack.presetOf(s));
  for (const s of input.settings) {
    Engine.applySettings(s);
    const live = values(Engine.ctx.made, true);
    offline.length = 0;
    await Rack.renderMasterWav('take1', s);
    const render = offline[offline.length - 1];
    out.cases.push({
      // past playback's media element, and the render's buffer source and the two nodes it joins on by
      live: live.slice(1), render: values(render.made.slice(3)), ends: [live[0].kind, render.made[0].kind],
      liveNodes: live.length, masterDry: heading(Engine.masterDryGain.gain), masterWet: heading(Engine.masterWetGain.gain),
      rates: offline.map((c) => c.sampleRate),
    });
  }
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(e && e.stack || e); process.exit(1); });
"""

FLAT_BEFORE_2 = {   # what every played take was given before version 2: all in, at "flat" values
    "eq": {"enabled": True, "preGain": 0, "hp": 20, "lowFreq": 60, "lowGain": 0, "midFreq": 1600, "midGain": 0,
           "highGain": 0, "outLevel": 0, "phase": False},
    "comp": {"enabled": True, "threshold": -18, "ratio": 4, "attack": 0.015, "release": 0.25, "makeup": 0,
             "mix": 1.0, "knee": 10},
    "imager": {"enabled": True, "bigness": 1, "range": 5, "stage": 5, "harmonics": False, "tubeHarmonics": 1,
               "bass": False},
    "limit": {"enabled": True, "drive": 0, "ceiling": -0.1, "release": 0.08, "warmth": False},
    "masterBypass": False,
}


def changed(base: dict, **modules) -> dict:
    out = json.loads(json.dumps(base))
    for name, values in modules.items():
        if isinstance(values, dict):
            out.setdefault(name, {}).update(values)
        else:
            out[name] = values
    return out


def rack(settings: list[dict], rate: int = 48000, user_presets: dict | None = None) -> dict:
    res = subprocess.run(["node", "-e", HARNESS], capture_output=True, text=True,
                         input=json.dumps({"rack": str(STATIC / "rack.js"), "settings": settings, "rate": rate,
                                           "userPresets": user_presets}))
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


@pytest.fixture(scope="module")
def flat() -> dict:
    return rack([])["flat"]


def test_the_rack_starts_flat_and_out_of_the_path(flat):
    """A compressor, an imager and a limiter change the sound at any setting, so a rack nobody
    has touched has all three out, and the take plays through none of it."""
    assert [flat[m]["enabled"] for m in ("comp", "imager", "limit")] == [False, False, False]
    assert flat["version"] == 3
    got = rack([flat])
    assert got["engaged"] == [False]
    assert (got["cases"][0]["masterDry"], got["cases"][0]["masterWet"]) == (1, 0)


def test_what_counts_as_changing_the_sound(flat):
    settings = [
        flat,
        changed(flat, eq={"lowGain": 2}),
        changed(flat, eq={"outLevel": -1}),
        changed(flat, eq={"phase": True}),
        changed(flat, eq={"lowGain": 2, "enabled": False}),        # the EQ is out: its bands do nothing
        changed(flat, eq={"preGain": 3, "enabled": False}),        # but the input gain is before it
        changed(flat, comp={"enabled": True}),
        changed(flat, imager={"enabled": True}),
        changed(flat, limit={"enabled": True}),
        changed(flat, comp={"enabled": True}, limit={"enabled": True}, masterBypass=True),
    ]
    got = rack(settings)
    assert got["engaged"] == [False, True, True, True, False, True, True, True, True, False]
    for case, engaged in zip(got["cases"], got["engaged"]):
        assert (case["masterDry"], case["masterWet"]) == ((0, 1) if engaged else (1, 0))


def test_a_saved_file_is_rendered_by_the_chain_that_plays_it(flat):
    """One chain, made by one function and set by one function, on two contexts. Every value in
    the render equals the one in playback, for settings that use every module."""
    loud = changed(flat, eq={"preGain": 2, "hp": 80, "lowGain": 6, "midGain": -3, "highGain": 5, "outLevel": -1},
                   comp={"enabled": True, "threshold": -32, "ratio": 8, "makeup": 4, "mix": 0.8},
                   imager={"enabled": True, "bigness": 9, "range": 2, "stage": 8, "harmonics": True,
                           "tubeHarmonics": 9, "bass": True},
                   limit={"enabled": True, "drive": 6, "ceiling": -0.3, "warmth": True})
    got = rack([loud, changed(loud, imager={"enabled": False}), changed(flat, eq={"highGain": 3}), flat])
    for case in got["cases"]:
        assert case["ends"] == ["element", "buffer"]
        assert case["liveNodes"] > 40
        assert case["render"] == case["live"]
    # and the settings reach it: the loud case differs from the flat one
    assert got["cases"][0]["live"] != got["cases"][3]["live"]


def test_a_render_keeps_the_sample_rate_of_the_file(flat):
    for rate in (48000, 44100):
        got = rack([changed(flat, comp={"enabled": True})], rate=rate)
        assert got["cases"][0]["rates"] == [rate, rate], "decoded and rendered at the file's own rate"


def test_settings_kept_before_version_2_are_read_as_untouched(flat):
    """Every take played before version 2 was given settings with all three processors in at the
    values the rack called flat. A module left exactly there was never touched and is read as
    out; one that was adjusted stays in, and version 2 settings are taken as they are."""
    touched = changed(FLAT_BEFORE_2, comp={"threshold": -24}, limit={"warmth": True})
    deliberate = changed(FLAT_BEFORE_2, version=2)
    got = rack([FLAT_BEFORE_2, touched, deliberate])
    old, some, new = got["upgraded"]
    assert [old[m]["enabled"] for m in ("comp", "imager", "limit")] == [False, False, False]
    assert [some[m]["enabled"] for m in ("comp", "imager", "limit")] == [True, False, True]
    assert [new[m]["enabled"] for m in ("comp", "imager", "limit")] == [True, True, True]
    assert old["version"] == some["version"] == new["version"] == 3
    # and a compressor has what its node adds by itself written into its OUTPUT, so it sounds as it did now
    # that the rack takes that gain off: one that is out as well, for when it is switched in
    assert (old["comp"]["makeup"], some["comp"]["makeup"], new["comp"]["makeup"]) == (6.0, 8.7, 6.0)
    assert flat["comp"]["makeup"] == 6.0 and flat["comp"]["enabled"] is False
    # read raw, the old settings would have put the chain in the path
    assert got["engaged"][0] is True
    assert rack([old])["engaged"] == [False]


def test_the_preset_box_names_the_preset_the_settings_are(flat):
    """Settings come to the rack from a preset chosen there, or with the take now playing. Either
    way the box names the preset they are, a factory one or the user's own, and nothing when a
    control has been moved since. A name, the bypass switch and the older spellings of a value
    do not stop settings being a preset."""
    warm = {   # the factory preset, as an older build kept it with a take: no version, older names too
        "name": "anything", "masterBypass": True,
        "eq": {"enabled": True, "preGain": -4, "hp": 20, "lowFreq": 110, "lowGain": 1.5, "mid1Freq": 700,
               "mid1Gain": 0.5, "airGain": 1.0, "outLevel": 0, "phase": False},
        "comp": {"enabled": True, "threshold": -18, "ratio": 3, "attack": 0.02, "release": 0.35, "makeup": 1.0,
                 "mix": 1.0, "knee": 20},
        "imager": {"enabled": True, "bigness": 2, "range": 6, "stage": 5, "harmonics": True, "tubeHarmonics": 2,
                   "bass": False},
        "limit": {"enabled": True, "drive": 0, "ceiling": -0.5, "release": 0.12, "warmth": True},
    }
    mine = changed(flat, name="Mine", comp={"enabled": True, "threshold": -30})
    got = rack([flat, FLAT_BEFORE_2, warm, changed(warm, comp={"makeup": 3}), mine, changed(mine, eq={"lowGain": 1})],
               user_presets={"user_1": mine})
    assert got["presets"] == ["default", "default", "vintage_warmth", None, "user_1", None]
    # with no presets of the user's own, theirs is nobody's
    assert rack([mine])["presets"] == [None]


def test_saving_a_preset_under_a_name_already_used_writes_it_over():
    from pathlib import Path
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    save = rack_js[rack_js.index("savePresetBtn.addEventListener('click'"):rack_js.index("// Delete Custom Preset")]
    # the name is looked for among the user's presets, whatever its case, and the user is asked first
    assert "self.userPresetsNamed(userPresets, name)" in save and "Replace it?" in save
    assert "if (!replace) { return; }" in save
    # the preset found keeps its id; a new one is made only for a new name; older doubles of the name go
    assert "var id = same.length ? same[0] : 'user_' + Date.now();" in save
    assert "same.slice(1).forEach(function (other) { delete userPresets[other]; });" in save
    named = rack_js[rack_js.index("userPresetsNamed: function"):rack_js.index("saveUserPresets: function")]
    assert named.count(".trim().toLowerCase()") == 2


def test_the_factory_presets_leave_room_for_what_they_add():
    """A take reaches the rack finished, its peaks close to full scale.  So a factory preset turns the input
    down before it boosts anything, does not drive the limiter, and keeps its make-up small (the compressor's
    node adds its own): it comes out about as loud as it went in, and the limiter is only a guard."""
    import re
    from pathlib import Path
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    block = rack_js[rack_js.index("var PRESETS = {"):rack_js.index("// ------------------------------------------------------------- DSP Helpers")]
    names = re.findall(r"^    '(\w+)': \{", block, flags=re.M)
    assert names == ["default", "vintage_warmth", "vocal_air", "radio_master", "punchy_bass", "acoustic_clarity"]
    sum_of_the_node = rack_js[rack_js.index("  function nodeMakeupDb("):rack_js.index("  // ------------------------------------------------------------- Parametric equaliser")]
    bodies = re.split(r"^    '\w+': \{", block, flags=re.M)[1:]
    for name, body in zip(names, bodies):
        if name == "default":
            continue
        def value(key):
            return float(re.search(r"\b" + key + r": (-?[0-9.]+)", body).group(1))
        # OUTPUT gives back about what the compressor's own curve takes off full scale, and no more
        own = float(subprocess.run(["node", "-e", sum_of_the_node + "console.log(nodeMakeupDb(%s, %s, %s))" % (
            value("threshold"), value("knee"), value("ratio"))], capture_output=True, text=True, check=True).stdout)
        assert -0.05 <= value("makeup") - own <= 1.05, name
        boost = sum(max(0.0, value(k)) for k in ("lowGain", "midGain", "highGain"))
        assert value("preGain") <= -boost / 2 and value("preGain") <= -2, name     # turned down by at least half of what is added
        assert value("drive") == 0 and value("ceiling") <= -0.3, name
        assert value("mix") == 1.0 and value("outLevel") <= 0, name
        assert value("bigness") <= 3 and value("tubeHarmonics") <= 2, name


def test_nothing_is_sliced_before_the_limiter_and_the_dry_signal_waits_for_the_compressor():
    """Two faults of the chain, mended.  Each waveshaper used to hold a straight line when it was to do nothing,
    and a shaper cuts off flat whatever is outside its curve: so an over was sliced before the limiter saw it.
    And the compressor's node looks ahead, putting out its signal the frames of 6 ms late, while the dry signal
    it is blended with (MIX) was not delayed: the blend combed."""
    import json as _json
    from pathlib import Path
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    build = rack_js[rack_js.index("    build: function (ctx, source, destination) {"):rack_js.index("    makeTubeCurve: function () {")]
    assert "makeLinearCurve" not in rack_js
    # a shaper that is to do nothing has no curve, and is given one only when that changes
    assert build.count(".curve = null;") == 2
    assert "shaper.curve = tube ? this.makeTubeCurve() : null;" in rack_js and "if (shaper.tube === tube) { return; }" in rack_js
    # the order at the limiter: drive, the tube stage, the limiter, the guard, the ceiling
    order = ["this.limitDrive.connect(this.limitShaperIn);", "this.limitShaperIn.connect(this.limitShaper);",
             "this.limitShaper.connect(this.limitShaperOut);", "this.limitShaperOut.connect(this.limiter);",
             "this.limiter.connect(this.limitGuard);", "this.limitGuard.connect(this.limitCeiling);"]
    assert [build.index(line) for line in order] == sorted(build.index(line) for line in order)
    # the dry signal goes through a delay of the compressor's own frames
    assert "this.compDryDelay.delayTime.value = Math.floor(0.006 * ctx.sampleRate) / ctx.sampleRate;" in build
    assert build.index("eqTail.connect(this.compDryDelay);") < build.index("this.compDryDelay.connect(this.compDryGain);")
    assert "connect(this.compDryGain);" in build and "eqTail.connect(this.compDryGain);" not in build
    # the tube curve, drawn over four times the span: the old curve inside full scale, and no corner beyond it
    curves = rack_js[rack_js.index("  var SHAPER_SPAN = 4;"):rack_js.index("  /* The gain a DynamicsCompressorNode adds by itself")]
    script = curves + """
      var c = makeTubeCurve(), n = c.length - 1;
      function at(x) { return c[Math.round((x / SHAPER_SPAN + 1) * n / 2)] * SHAPER_SPAN; }
      var rising = true; for (var i = 1; i <= n; i++) { if (c[i] < c[i - 1]) { rising = false; } }
      console.log(JSON.stringify({ n: c.length, half: at(0.5), one: at(1), two: at(2), four: at(4), minus: at(-1), zero: at(0),
                                   rising: rising, guard: Array.from(makeGuardCurve()) }));
    """
    got = _json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
    import math
    def tube(x):
        return math.tanh(1.15 * x) / 1.12
    assert got["n"] == 4097 and got["rising"] and got["zero"] == 0 and got["guard"] == [-1, 1]
    for key, x in (("half", 0.5), ("one", 1), ("two", 2), ("four", 4), ("minus", -1)):
        assert abs(got[key] - tube(x)) < 1e-6, key
    assert got["one"] < got["two"] < got["four"] < 1 / 1.12 + 1e-6     # still bending past full scale, towards its limit


def test_the_compressors_output_is_all_the_gain_it_adds():
    """A DynamicsCompressorNode raises what it puts out by an amount of its own, from its threshold, knee and
    ratio.  The rack works the same amount out and takes it off after the node.  The figures here are the
    node's, measured in a browser from a tone far under the threshold."""
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    own = rack_js[rack_js.index("  function nodeMakeupDb("):rack_js.index("  // ------------------------------------------------------------- Parametric equaliser")]
    measured = {(-18, 10, 4): 6.028, (-18, 20, 3): 2.601, (-24, 8, 8): 10.937, (-45, 0, 20): 25.650, (-45, 40, 20): 10.532,
                (0, 0, 1): 0.0, (-0.5, 0, 20): 0.285, (-30, 30, 12): 6.556, (-6, 3, 2): 1.390, (-10, 40, 20): 0.171}
    script = own + "console.log(JSON.stringify(%s.map(function (g) { return nodeMakeupDb(g[0], g[1], g[2]); })));" % (
        json.dumps([list(key) for key in measured]))
    got = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
    for (key, want), have in zip(measured.items(), got):
        assert abs(have - want) < 0.005, (key, have, want)
    # taken off where the settings are applied, from the same three values the node is given
    apply = rack_js[rack_js.index("    applySettings: function (s, atOnce) {"):rack_js.index("    getGainReduction: function () {")]
    assert "var makeupDb = (s.comp.makeup || 0) - nodeMakeupDb(compThreshold, compKnee, compRatio);" in apply
    assert "set(this.compressor.threshold, compThreshold);" in apply and "set(this.compressor.knee, compKnee);" in apply
    assert "set(this.compressor.ratio, compRatio);" in apply


# ------------------------------------------------------------------ the parametric equaliser
def equalised(flat: dict, unit_in: bool = True, **bands) -> dict:
    """The flat rack with some bands of the parametric equaliser set: band3={"gain": 4} and so on."""
    out = json.loads(json.dumps(flat))
    out["peq"]["enabled"] = unit_in
    for name, values in bands.items():
        out["peq"]["bands"][int(name[4:]) - 1].update(values)
    return out


def test_the_parametric_equaliser_starts_out_with_a_cut_waiting_at_each_end(flat):
    peq = flat["peq"]
    assert peq["enabled"] is False and len(peq["bands"]) == 7
    assert [band["type"] for band in peq["bands"]] == ["lowcut", "lowshelf", "bell", "bell", "bell", "highshelf", "highcut"]
    assert [band["on"] for band in peq["bands"]] == [False, True, True, True, True, True, False]
    assert all(band["gain"] == 0 for band in peq["bands"])
    assert [band["freq"] for band in peq["bands"]] == sorted(band["freq"] for band in peq["bands"])


def test_a_band_that_changes_nothing_is_nothing(flat):
    """The unit switched in with every band flat, a band set and then switched off, and bands set in a unit that
    is out all leave the sound alone: the chain stays out of the path, the rack is still the flat preset, and
    every one of the equaliser's filters is a bell with no gain."""
    cases = [equalised(flat),                                                   # in, and flat
             equalised(flat, band3={"gain": 5, "on": False}),                   # a band set, and off
             equalised(flat, False, band3={"gain": 5}, band1={"on": True}),     # set, in a unit that is out
             equalised(flat, band4={"freq": 2500, "q": 6})]                     # a flat band moved about
    got = rack(cases)
    assert got["engaged"] == [False] * 4 and got["presets"] == ["default"] * 4
    for case in got["cases"]:
        mine = [n for n in case["render"] if n["kind"] == "biquad"][4:11]     # after the 1073's four
        assert all(n["type"] == "peaking" and n["gain"] == 0 for n in mine)


def test_the_equalisers_bands_reach_the_chain_and_the_render_holds_what_playback_does(flat):
    busy = equalised(flat, band1={"on": True, "freq": 45}, band2={"gain": 2.5}, band3={"gain": -4, "q": 2, "freq": 250},
                     band5={"type": "notch", "freq": 3200, "q": 6}, band6={"gain": 4}, band7={"on": True, "freq": 16000, "q": 1})
    got = rack([busy])
    assert got["engaged"] == [True] and got["presets"] == [None]
    case = got["cases"][0]
    assert case["live"] == case["render"]
    mine = [n for n in case["render"] if n["kind"] == "biquad"][4:11]     # after the 1073's four
    assert [n["type"] for n in mine] == ["highpass", "lowshelf", "peaking", "peaking", "notch", "highshelf", "lowpass"]
    assert [n["frequency"] for n in mine] == [45, 90, 250, 1000, 3200, 10000, 16000]
    assert [n["gain"] for n in mine] == [0, 2.5, -4, 0, 0, 4, 0]
    # a cut's Q goes to its filter in decibels, a bell's and a notch's as they are, a shelf has none
    assert mine[0]["Q"] == pytest.approx(-2.97, abs=0.01) and mine[6]["Q"] == 0
    assert (mine[2]["Q"], mine[4]["Q"]) == (2, 6)
    # and it is kept as part of the rack: a preset of the user's own holds it
    assert rack([busy], user_presets={"user_1": busy})["presets"] == ["user_1"]


def test_the_curve_drawn_is_the_filter_heard():
    """The screen works a band's curve out with the Web Audio specification's own coefficients; in a browser the
    sum agrees with the node's getFrequencyResponse to the thousandth of a decibel.  Here, the things any
    equaliser must do."""
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    section = rack_js[rack_js.index("  var PEQ_TYPES = "):rack_js.index("  // A preset is the whole rack: each one has")]
    script = section + """
      function band(type, freq, gain, q) { return { on: true, type: type, freq: freq, gain: gain, q: q }; }
      function db(b, hz) { return biquadDb(peqBandShape(b, true), hz, 48000); }
      var settings = { peq: { enabled: true, bands: [band('lowcut', 60, 0, 0.71), band('lowshelf', 200, 4, 1), band('bell', 1000, 6, 1.5),
                                                      band('bell', 1000, -6, 1.5), band('notch', 4000, 0, 4), band('highshelf', 6000, -3, 1),
                                                      band('highcut', 15000, 0, 0.71)] } };
      var peq = peqOf(settings);
      console.log(JSON.stringify({
        bell: [db(peq.bands[2], 1000), db(peq.bands[2], 50), db(peq.bands[2], 16000)],
        opposite: db(peq.bands[2], 700) + db(peq.bands[3], 700),
        lowshelf: [db(peq.bands[1], 20), db(peq.bands[1], 200), db(peq.bands[1], 10000)],
        highshelf: [db(peq.bands[5], 20000), db(peq.bands[5], 100)],
        lowcut: [db(peq.bands[0], 60), db(peq.bands[0], 30), db(peq.bands[0], 2000)],
        highcut: [db(peq.bands[6], 15000), db(peq.bands[6], 1000)],
        notch: [db(peq.bands[4], 4000), db(peq.bands[4], 400)],
        whole: peqDb(peq, 1000, 48000),
        out: peqDb(peqOf({ peq: { enabled: false, bands: peq.bands } }), 1000, 48000),
        none: peqOf({}), odd: peqOf({ peq: { bands: [{ type: 'wah', freq: 5, gain: 99, q: 0 }] } }).bands[0]
      }));
    """
    got = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
    near = lambda want, tolerance=0.05: pytest.approx(want, abs=tolerance)
    assert got["bell"][0] == near(6) and got["bell"][1] == near(0) and got["bell"][2] == near(0, 0.1)
    assert got["opposite"] == near(0, 1e-6)                    # a boost and the same cut undo each other
    assert got["lowshelf"][0] == near(4, 0.1) and got["lowshelf"][1] == near(2, 0.1) and got["lowshelf"][2] == near(0)
    assert got["highshelf"][0] == near(-3, 0.1) and got["highshelf"][1] == near(0)
    assert got["lowcut"][0] == near(-3, 0.1) and got["lowcut"][1] < -11 and got["lowcut"][2] == near(0)
    assert got["highcut"][0] == near(-3, 0.1) and got["highcut"][1] == near(0)
    assert got["notch"][0] < -40 and got["notch"][1] == near(0, 0.1)
    assert got["whole"] == near(0, 0.2)                        # the two bells cancel at 1 kHz; the rest are far off
    assert got["out"] == 0
    # settings with no equaliser have one that is out; values out of range come within it, a kind not known is the band's own
    assert got["none"]["enabled"] is False and len(got["none"]["bands"]) == 7
    assert got["odd"] == {"on": False, "type": "lowcut", "freq": 20, "gain": 18, "q": 0.3}


def test_the_equaliser_sits_after_the_1073_and_before_the_compressor_and_the_bay_scrolls():
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    build = rack_js[rack_js.index("    build: function (ctx, source, destination) {"):rack_js.index("    makeTubeCurve: function () {")]
    order = ["this.eqPhase.connect(this.eqOutput);", "var eqTail = this.eqOutput;", "eqTail.connect(filter);",
             "eqTail.connect(this.compDryDelay);", "eqTail.connect(this.compressor);"]
    assert [build.index(line) for line in order] == sorted(build.index(line) for line in order)
    # the analyser behind the curve only listens
    assert "this.analyser.connect(this.spectrum);" in build and "this.spectrum.connect(" not in build
    # the unit is in the rack between the two, and has no brand or preset of its own
    markup = rack_js[rack_js.index('id="unit-peq"'):rack_js.index('id="unit-comp"')]
    assert rack_js.index('id="unit-eq"') < rack_js.index('id="unit-peq"') < rack_js.index('id="unit-comp"')
    assert "PARAMETRIC EQUALIZER" in markup and "<select" not in markup
    css = (Path(__file__).resolve().parent.parent / "app" / "static" / "styles.css").read_text(encoding="utf-8")
    unit = css[css.index("\n.rack-unit {"):css.index(".unit-bar {")]
    assert "flex-shrink: 0;" in unit       # or five units are squeezed into the bay and their controls cut off


def test_the_rack_is_drawn_to_fit_the_window_unless_asked_for_at_full_size():
    """Five units are taller than most windows.  The rack is given the window's height and drawn smaller until
    all of it shows, down to a floor; Full size and Fit in its header choose, and the browser remembers."""
    rack_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "rack.js").read_text(encoding="utf-8")
    css = (Path(__file__).resolve().parent.parent / "app" / "static" / "styles.css").read_text(encoding="utf-8")
    fit = rack_js[rack_js.index("    fitToWindow: function () {"):rack_js.index("    dockToBottom: function () {")]
    # measured at full size, never under the floor or over full size, and the choice is kept
    assert fit.index("panel.style.setProperty('--rack-zoom', '1');") < fit.index("var needed = header.offsetHeight + bay.scrollHeight + 2;")
    assert "Math.min(1, Math.max(this.RACK_FLOOR, room / needed)) : 1;" in fit
    assert "RACK_FLOOR: 0.58," in rack_js and "localStorage.getItem('yue2.rackFit') !== '0'" in rack_js
    # the lettering is set larger by what the rack is drawn smaller, up to a limit, and worked out with the size,
    # since larger lettering makes the rack taller; the panel is let out sideways for it
    assert "Math.min(this.RACK_TYPE_MOST, Math.max(1, this.RACK_TYPE_KEPT / zoom))" in fit
    assert "panel.style.setProperty('--rack-type', String(type));" in fit and "panel.style.setProperty('--rack-wide', String(wide));" in fit
    sizes = css[css.index("/* --rack-zoom is the size the rack is drawn at"):]
    import re as _re
    plain = [px for px in _re.findall(r"font-size: ([0-9.]+)px", sizes) if float(px) < 14]
    assert plain == [], plain                # every label's size follows --rack-type; only badge lettering is fixed
    assert sizes.count("* var(--rack-type, 1))") >= 30
    # hairlines do not shrink, so it is checked again once drawn
    assert "bay.scrollHeight > bay.clientHeight + 1" in fit
    # it is fitted when opened, floated, docked and when the window changes
    assert rack_js.count("this.fitToWindow();") >= 4 and "self.fitToWindow();" in rack_js
    # the panel narrows with it and the bay's limit comes from the fit
    assert "max-width: calc(1240px * var(--rack-zoom, 1) * var(--rack-wide, 1));" in css and "zoom: var(--rack-zoom, 1);" in css
    assert "max-height: var(--rack-bay-max, calc(84vh - 75px));" in css
    # the equaliser's graph reads the pointer in its own pixels, which a smaller rack makes larger
    assert "scale = box.width ? canvas.clientWidth / box.width : 1;" in rack_js
