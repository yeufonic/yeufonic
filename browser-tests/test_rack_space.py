"""The rack's Space module (headphones 3D): a scene puts it in, and what it plays reaches both ears from where it is
placed, at the loudness it came in at."""
import pytest

pytest.importorskip("playwright.sync_api")

RENDER = """async (space) => {
  const rate = 48000, len = rate * 2;
  const ctx = new OfflineAudioContext(2, len, rate);
  const buf = ctx.createBuffer(2, len, rate);
  const L = buf.getChannelData(0);
  for (let i = 0; i < len; i++) { L[i] = 0.3 * Math.sin(2 * Math.PI * 440 * i / rate); }   // the left channel only
  const src = ctx.createBufferSource(); src.buffer = buf;
  const s = JSON.parse(JSON.stringify(Rack.settings));
  s.space = Object.assign(Rack.defaultSpace(), space);
  const g = Rack.buildGraph(ctx, s);
  src.connect(g.inputNode); g.outputNode.connect(ctx.destination); src.start(0);
  const out = await ctx.startRendering();
  const rms = (ch) => { const d = out.getChannelData(ch); let t = 0; for (let i = rate; i < len; i++) { t += d[i] * d[i]; } return Math.sqrt(t / rate); };
  return [rms(0), rms(1)];
}"""


def test_a_scene_puts_space_in_and_the_left_channel_reaches_both_ears(page, app_server):
    page.evaluate("() => Rack.toggle(true)")
    page.locator('#space-scenes [data-scene="around"]').click()
    assert page.locator("#toggle-space").inner_text().strip() == "IN"
    assert page.evaluate("() => Rack.settings.space.surround") == 0.6
    assert page.locator('#space-scenes [data-scene="around"]').get_attribute("class").split().count("active") == 1
    off = page.evaluate(RENDER, {"enabled": False})
    on = page.evaluate(RENDER, {"enabled": True, "width": 30})
    assert off[1] == 0 and on[1] > 0.1 * on[0]          # out, the right ear hears nothing; in, the left speaker reaches it
    assert on[0] > on[1]                                  # and nearer the left


def test_a_module_folds_to_its_bar_and_the_take_keeps_it(page, app_server):
    # two takes that exist only here: what the rack keeps for them is answered, not stored
    page.route("**/api/takes/fold*/fx", lambda route: route.fulfill(json={"status": "ok"} if route.request.method == "PUT" else {}))
    page.evaluate("() => { Rack.toggle(true); Rack.onTake({ id: 'fold1', title: 'Folding' }); }")
    page.locator("#unit-comp .unit-fold").click()
    assert page.evaluate("() => document.getElementById('unit-comp').classList.contains('folded')")
    assert not page.locator("#unit-comp .unit-faceplate").is_visible()
    assert page.evaluate("() => Rack.settings.folded") == ["unit-comp"]          # kept with the take's settings
    page.evaluate("() => { Rack.currentTakeId = null; Rack.onTake({ id: 'fold2', title: 'Another' }); }")
    page.wait_for_function("() => !document.getElementById('unit-comp').classList.contains('folded')")   # none kept: all open
    page.evaluate("() => { Rack.currentTakeId = null; Rack.onTake({ id: 'fold1', title: 'Folding', fx_chain: JSON.stringify(Object.assign({}, Rack.settings, { folded: ['unit-comp'] })) }); }")
    assert page.evaluate("() => document.getElementById('unit-comp').classList.contains('folded')")
    page.locator("#unit-comp .unit-fold").click()
    assert page.locator("#unit-comp .unit-faceplate").is_visible()



BAND = """async ([space, hz]) => {
  const rate = 48000, len = rate * 3;
  const ctx = new OfflineAudioContext(2, len, rate);
  const buf = ctx.createBuffer(2, len, rate);
  let seed = 5; const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647 * 2 - 1; };
  const L = buf.getChannelData(0), R = buf.getChannelData(1);
  for (let i = 0; i < len; i++) { const c = rnd(); L[i] = 0.12 * (0.8 * c + 0.2 * rnd()); R[i] = 0.12 * (0.8 * c + 0.2 * rnd()); }
  const src = ctx.createBufferSource(); src.buffer = buf;
  const s = JSON.parse(JSON.stringify(Rack.settings)); s.space = Object.assign(Rack.defaultSpace(), space);
  const g = Rack.buildGraph(ctx, s);
  await g.chain.toneReady;
  const band = ctx.createBiquadFilter(); band.type = 'bandpass'; band.frequency.value = hz; band.Q.value = 1.4;
  src.connect(g.inputNode); g.outputNode.connect(band); band.connect(ctx.destination); src.start(0);
  const out = await ctx.startRendering();
  let t = 0; for (let ch = 0; ch < 2; ch++) { const d = out.getChannelData(ch); for (let i = rate; i < len; i++) t += d[i] * d[i]; }
  return 10 * Math.log10(t);
}"""


def test_space_keeps_the_takes_tone(page, app_server):
    """The browser's HRTF set dulls what passes through it (presence and air 8 to 15 dB down); Space undoes the broad
    colour, octave by octave, so the take keeps its brightness."""
    for hz in (125, 1000, 4000):
        off = page.evaluate(BAND, [{"enabled": False}, hz])
        on = page.evaluate(BAND, [{"enabled": True, "width": 30}, hz])
        assert abs(on - off) < 3, (hz, on - off)
