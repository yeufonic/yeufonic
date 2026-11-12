"""Hear it, stopped and started again with nothing changed, plays the voice it already has instead of staying silent."""
import pytest

pytest.importorskip("playwright.sync_api")

SETUP = """async () => {
  const rate = 8000, frames = rate;                       // a second of silence as a WAV, for the voice's answer
  const wav = new DataView(new ArrayBuffer(44 + frames * 2));
  const text = (at, s) => { for (let i = 0; i < s.length; i++) { wav.setUint8(at + i, s.charCodeAt(i)); } };
  text(0, 'RIFF'); wav.setUint32(4, 36 + frames * 2, true); text(8, 'WAVE'); text(12, 'fmt ');
  wav.setUint32(16, 16, true); wav.setUint16(20, 1, true); wav.setUint16(22, 1, true); wav.setUint32(24, rate, true);
  wav.setUint32(28, rate * 2, true); wav.setUint16(32, 2, true); wav.setUint16(34, 16, true);
  text(36, 'data'); wav.setUint32(40, frames * 2, true);
  window.__asked = 0;
  const real = window.fetch;
  window.fetch = (url, opts) => {
    if (String(url).endsWith('/audition')) { window.__asked++; return Promise.resolve(new Response(wav.buffer.slice(0))); }
    return real(url, opts);
  };
  window.paintPersonaField = () => {};
  window.pickedVoiceMix = () => ({ octave: 0, likeness: 0.75, protect: 0.33, dynamics: 'take', room: 'dry',
                                   brightness: 0, formant: 0, wet: 1 });
  VOICES.pick = 'voice-1';
  AUD.loop = 'male';
  AUD.ctx = new (window.AudioContext || window.webkitAudioContext)();
  AUD.dry.male = AUD.ctx.createBuffer(1, rate, rate);
}"""


def test_hear_it_plays_again_after_a_stop(page):
    page.evaluate(SETUP)
    page.evaluate("() => auditionStart()")
    page.wait_for_function("() => AUD.nodes !== null && AUD.nodes !== undefined")
    page.evaluate("() => auditionStop()")
    assert page.evaluate("() => AUD.nodes") is None

    page.evaluate("() => auditionStart()")
    page.wait_for_function("() => AUD.nodes !== null && AUD.nodes !== undefined", timeout=3000)
    assert page.evaluate("() => window.__asked") == 1     # the same settings are not sung again
    page.evaluate("() => auditionStop()")
