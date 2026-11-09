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
