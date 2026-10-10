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
                  localStorage: { getItem: () => null, setItem() {} },
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


def rack(settings: list[dict], rate: int = 48000) -> dict:
    res = subprocess.run(["node", "-e", HARNESS], capture_output=True, text=True,
                         input=json.dumps({"rack": str(STATIC / "rack.js"), "settings": settings, "rate": rate}))
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


@pytest.fixture(scope="module")
def flat() -> dict:
    return rack([])["flat"]


def test_the_rack_starts_flat_and_out_of_the_path(flat):
    """A compressor, an imager and a limiter change the sound at any setting, so a rack nobody
    has touched has all three out, and the take plays through none of it."""
    assert [flat[m]["enabled"] for m in ("comp", "imager", "limit")] == [False, False, False]
    assert flat["version"] == 2
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
    assert old["version"] == some["version"] == 2
    # read raw, the old settings would have put the chain in the path
    assert got["engaged"][0] is True
    assert rack([old])["engaged"] == [False]
