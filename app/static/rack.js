/* =====================================================================
   Yeufonic Vintage Mastering Rack & Channel Strip (rack.js)
   1073 DPX Parametric EQ · 76-LN Compressor · 670 Master Limiter
   Web Audio API · Ultra-low Latency (~2.9ms) · Photorealistic Skeuomorphic UI
   ===================================================================== */

(function (window, document) {
  'use strict';

  // The page's words come from i18n.js; a rack loaded on its own, as the tests load it, keeps its English.
  var I18N = window.I18N || {
    t: function (text, vars) {
      return vars ? text.replace(/\{(\w+)\}/g, function (whole, name) { return vars[name] !== undefined ? vars[name] : whole; }) : text;
    }
  };
  var t = I18N.t;

  // ------------------------------------------------------------- Defaults & Presets
  var PRESETS = {
    'default': {
      name: t('Flat / Transparent'),
      eq: {
        enabled: true,
        preGain: 0,
        hp: 20,
        lowFreq: 60,
        lowGain: 0,
        midFreq: 1600,
        midGain: 0,
        highGain: 0,
        outLevel: 0,
        phase: false,
        // legacy aliases
        mid1Freq: 1600, mid1Gain: 0, highFreq: 12000, airGain: 0
      },
      // out, and waiting at the OUTPUT that gives back what these settings take off: switched in, it
      // compresses without a drop in level, and OUTPUT at 0 is still no gain at all
      comp: { enabled: false, threshold: -18, ratio: 4, attack: 0.015, release: 0.25, makeup: 6.0, mix: 1.0, knee: 10 },
      imager: { enabled: false, bigness: 1, range: 5, stage: 5, harmonics: false, tubeHarmonics: 1, bass: false },
      limit: { enabled: false, drive: 0, ceiling: -0.1, release: 0.08, warmth: false },
      masterBypass: false,
      version: 3
    },
    /* The five below are set by measurement, not by ear alone.  A take arrives finished: at its loudness,
       with its peaks within a decibel or so of full scale.  So each preset turns the input down before it
       adds anything, comes out within about a decibel of the loudness it was given (Radio Ready a little
       more), and keeps its peaks under full scale all the way through, so that the limiter is a guard
       here and not what makes the sound.  The presets these replace came out a good deal louder than
       they went in, and were driven past full scale inside the rack.  The compressor's OUTPUT gives back
       about what its settings take off the loud parts, and no more.  Every ratio is one the rack has a
       button for, so the button is lit when the preset is chosen. */
    'vintage_warmth': {
      name: t('Vintage Tube Warmth'),
      eq: {
        enabled: true,
        preGain: -4,
        hp: 20,
        lowFreq: 110,
        lowGain: 1.5,
        midFreq: 700,
        midGain: 0.5,
        highGain: 1.0,
        outLevel: 0,
        phase: false,
        mid1Freq: 700, mid1Gain: 0.5, highFreq: 12000, airGain: 1.0
      },
      comp: { enabled: true, threshold: -22, ratio: 2, attack: 0.020, release: 0.35, makeup: 4.0, mix: 1.0, knee: 20 },
      imager: { enabled: true, bigness: 2, range: 6, stage: 5, harmonics: true, tubeHarmonics: 2, bass: false },
      limit: { enabled: true, drive: 0, ceiling: -0.5, release: 0.12, warmth: true },
      masterBypass: false,
      version: 3
    },
    'vocal_air': {
      name: t('Vocal Air & Glue'),
      eq: {
        enabled: true,
        preGain: -3,
        hp: 50,
        lowFreq: 110,
        lowGain: -0.5,
        midFreq: 3200,
        midGain: 1.5,
        highGain: 2.0,
        outLevel: 0,
        phase: false,
        mid1Freq: 3200, mid1Gain: 1.5, highFreq: 12000, airGain: 2.0
      },
      comp: { enabled: true, threshold: -20, ratio: 2, attack: 0.010, release: 0.20, makeup: 5.1, mix: 1.0, knee: 12 },
      imager: { enabled: true, bigness: 2, range: 3, stage: 6, harmonics: false, tubeHarmonics: 1, bass: false },
      limit: { enabled: true, drive: 0, ceiling: -0.3, release: 0.08, warmth: false },
      masterBypass: false,
      version: 3
    },
    'radio_master': {
      name: t('Radio Ready Master'),
      eq: {
        enabled: true,
        preGain: -3,
        hp: 50,
        lowFreq: 60,
        lowGain: 1.5,
        midFreq: 1600,
        midGain: 0.5,
        highGain: 1.5,
        outLevel: 0,
        phase: false,
        mid1Freq: 1600, mid1Gain: 0.5, highFreq: 12000, airGain: 1.5
      },
      comp: { enabled: true, threshold: -22, ratio: 4, attack: 0.003, release: 0.15, makeup: 8.8, mix: 1.0, knee: 10 },
      imager: { enabled: true, bigness: 3, range: 5, stage: 5, harmonics: true, tubeHarmonics: 2, bass: false },
      limit: { enabled: true, drive: 0, ceiling: -0.3, release: 0.06, warmth: false },
      masterBypass: false,
      version: 3
    },
    'punchy_bass': {
      name: t('Punchy Club & Bass'),
      eq: {
        enabled: true,
        preGain: -5,
        hp: 20,
        lowFreq: 60,
        lowGain: 2.0,
        midFreq: 3200,
        midGain: 1.0,
        highGain: 1.0,
        outLevel: -0.5,
        phase: false,
        mid1Freq: 3200, mid1Gain: 1.0, highFreq: 12000, airGain: 1.0
      },
      comp: { enabled: true, threshold: -16, ratio: 4, attack: 0.020, release: 0.12, makeup: 6.1, mix: 1.0, knee: 6 },
      imager: { enabled: true, bigness: 2, range: 5, stage: 5, harmonics: false, tubeHarmonics: 1, bass: true },
      limit: { enabled: true, drive: 0, ceiling: -0.3, release: 0.08, warmth: false },
      masterBypass: false,
      version: 3
    },
    'acoustic_clarity': {
      name: t('Acoustic Clarity'),
      eq: {
        enabled: true,
        preGain: -2,
        hp: 50,
        lowFreq: 110,
        lowGain: -1.0,
        midFreq: 4800,
        midGain: 1.0,
        highGain: 1.5,
        outLevel: -0.5,
        phase: false,
        mid1Freq: 4800, mid1Gain: 1.0, highFreq: 12000, airGain: 1.5
      },
      comp: { enabled: true, threshold: -20, ratio: 2, attack: 0.015, release: 0.30, makeup: 3.2, mix: 1.0, knee: 18 },
      imager: { enabled: true, bigness: 2, range: 4, stage: 6, harmonics: false, tubeHarmonics: 1, bass: false },
      limit: { enabled: true, drive: 0, ceiling: -0.3, release: 0.10, warmth: false },
      masterBypass: false,
      version: 3
    },
    /* Made by ear in the rack and kept as it was saved, not to the rules above (it replaced Boost, 2026-11-09): the
       mids and highs lifted, a slow gentle compressor, no limiter, and Space in, wide and high, with all of the
       ambience behind and a little room.  Space is for headphones and never in the take's own file; the rest is. */
    'surround': {
      name: t('Surround'),
      eq: {
        enabled: true,
        preGain: 3,
        hp: 20,
        lowFreq: 60,
        lowGain: 0,
        midFreq: 3200,
        midGain: 8,
        highGain: 5.5,
        outLevel: 1,
        phase: false,
        mid1Freq: 1600, mid1Gain: 0, highFreq: 12000, airGain: 0
      },
      comp: { enabled: true, threshold: -9, ratio: 2, attack: 0.015, release: 1.2, makeup: 2.5, mix: 1.0, knee: 10 },
      imager: { enabled: false, bigness: 1, range: 5, stage: 5, harmonics: false, tubeHarmonics: 1, bass: false },
      limit: { enabled: false, drive: 0, ceiling: -0.1, release: 0.08, warmth: false },
      space: { enabled: true, width: 90, surround: 1, height: 45, room: 0.1, output: 0 },
      masterBypass: false,
      version: 3
    }
  };

  // ------------------------------------------------------------- DSP Helpers & Waveshapers
  /* A waveshaper cuts off flat whatever reaches it outside -1 to 1: its curve covers that span and no more.
     So the tube curve is drawn over four times the span, and the signal is brought to a quarter before the
     shaper and back after it (SHAPER_SPAN): a peak over full scale is then bent like the rest, and
     flattens towards the curve's limit instead of being sliced at it.  Inside full scale the curve is the
     one it always was.  A shaper that is to do nothing has no curve at all, which passes the signal as it
     is; the straight line it used to be given sliced at full scale too. */
  var SHAPER_SPAN = 4;

  function makeTubeCurve() {
    var n = 1024 * SHAPER_SPAN;
    var curve = new Float32Array(n + 1);
    for (var i = 0; i <= n; i++) {
      var x = ((i * 2) / n - 1) * SHAPER_SPAN;          // the signal's own value
      curve[i] = Math.tanh(x * 1.15) / 1.12 / SHAPER_SPAN;
    }
    return curve;
  }

  /* The straight line from -1 to 1, which a shaper holds anything beyond to: the guard after the limiter,
     so that nothing leaves it over full scale whatever the limiter let through. */
  function makeGuardCurve() {
    return new Float32Array([-1, 1]);
  }

  /* The gain a DynamicsCompressorNode adds by itself, in decibels.  The node raises everything it puts
     out by an amount it works out from its threshold, knee and ratio, which nothing can switch off, so a
     compressor set to add nothing still made the sound louder, by more the harder it was set.  This is
     the node's own sum (the Web Audio specification's, as browsers carry it): the curve it compresses by,
     taken at full scale, and six tenths of the way back up from there.  The rack takes the same amount
     off again after the node, so that its OUTPUT is the only gain the compressor adds. */
  function nodeMakeupDb(thresholdDb, kneeDb, ratio) {
    function bound(v, low, high, fallback) { var x = Number(v); return isNaN(x) ? fallback : Math.min(high, Math.max(low, x)); }
    var T = bound(thresholdDb, -100, 0, -24), K = bound(kneeDb, 0, 40, 30), R = bound(ratio, 1, 20, 12);
    function lin(db) { return Math.pow(10, db / 20); }
    function dB(x) { return 20 * Math.log10(x); }
    var linT = lin(T), slope = 1 / R;
    // through the knee the curve bends over from the threshold; past the knee it rises at the ratio
    function knee(x, k) { return x < linT ? x : linT + (1 - Math.exp(-k * (x - linT))) / k; }
    function slopeAt(x, k) {
      if (x < linT) { return 1; }
      var x2 = x * 1.001;
      return (dB(knee(x2, k)) - dB(knee(x, k))) / (dB(x2) - dB(x));
    }
    // the bend that reaches the ratio's slope where the knee ends, found as the node finds it
    var kneeEnd = lin(T + K), low = 0.1, high = 10000, k = 5;
    for (var i = 0; i < 15; i++) {
      if (slopeAt(kneeEnd, k) < slope) { high = k; } else { low = k; }
      k = Math.sqrt(low * high);
    }
    var fullScale = 1 < kneeEnd ? knee(1, k) : lin(dB(knee(kneeEnd, k)) + slope * (0 - (T + K)));
    return -0.6 * dB(fullScale);
  }

  // ------------------------------------------------------------- Parametric equaliser
  /* Seven bands, each a filter of the user's choosing: a low cut, a low shelf, a bell, a notch, a high
     shelf or a high cut, at a frequency, with a gain where the kind has one and a width (Q) where it
     has one.  It sits after the 1073 and before the compressor: with that equaliser it is all filters
     and gains, so the order of the two makes no difference to the sound, and what follows compresses
     the corrected signal.  A band that changes nothing, a band switched off and the whole unit
     switched out are all the same filter, a bell with no gain, which passes the signal as it is. */
  var PEQ_TYPES = ['lowcut', 'lowshelf', 'bell', 'notch', 'highshelf', 'highcut'];
  var PEQ_FREQ = [20, 20000], PEQ_GAIN = [-18, 18], PEQ_Q = [0.3, 12];
  var PEQ_BUTTERWORTH = 0.71;      // the width at which a cut has no bump at its corner

  function defaultPeq() {
    // a cut at each end, waiting switched off, with shelves and bells between them
    return { enabled: false, bands: [
      { on: false, type: 'lowcut', freq: 30, gain: 0, q: PEQ_BUTTERWORTH },
      { on: true, type: 'lowshelf', freq: 90, gain: 0, q: 1 },
      { on: true, type: 'bell', freq: 250, gain: 0, q: 1 },
      { on: true, type: 'bell', freq: 1000, gain: 0, q: 1 },
      { on: true, type: 'bell', freq: 4000, gain: 0, q: 1 },
      { on: true, type: 'highshelf', freq: 10000, gain: 0, q: 1 },
      { on: false, type: 'highcut', freq: 18000, gain: 0, q: PEQ_BUTTERWORTH }
    ] };
  }

  /* The equaliser as settings hold it, whole and within its ranges: settings kept before there was
     one have none, and it is then out. */
  function peqOf(settings) {
    var kept = settings && settings.peq && typeof settings.peq === 'object' ? settings.peq : null;
    var bands = kept && Array.isArray(kept.bands) ? kept.bands : [];
    function within(v, range, fallback) {
      var x = Number(v);
      return (v === undefined || v === null || isNaN(x)) ? fallback : Math.min(range[1], Math.max(range[0], x));
    }
    return {
      enabled: kept ? kept.enabled !== false : false,
      bands: defaultPeq().bands.map(function (start, i) {
        var b = bands[i] && typeof bands[i] === 'object' ? bands[i] : {};
        return {
          on: b.on === undefined ? start.on : b.on !== false,
          type: PEQ_TYPES.indexOf(b.type) >= 0 ? b.type : start.type,
          freq: within(b.freq, PEQ_FREQ, start.freq),
          gain: within(b.gain, PEQ_GAIN, start.gain),
          q: within(b.q, PEQ_Q, start.q)
        };
      })
    };
  }

  function peqHasGain(type) { return type === 'lowshelf' || type === 'bell' || type === 'highshelf'; }
  function peqHasWidth(type) { return type === 'bell' || type === 'notch' || type === 'lowcut' || type === 'highcut'; }

  /* Whether a band changes the sound: a shelf or a bell with no gain does not. */
  function peqBandActive(band) {
    return band.on !== false && (!peqHasGain(band.type) || Number(band.gain) !== 0);
  }

  function peqActive(peq) {
    return Boolean(peq && peq.enabled !== false && peq.bands.some(peqBandActive));
  }

  /* What a band's biquad is given.  A Web Audio low-pass or high-pass takes its Q in decibels, the
     others as a plain figure, and a shelf takes none. */
  function peqBandShape(band, unitIn) {
    if (!unitIn || !peqBandActive(band)) { return { type: 'peaking', frequency: band.freq, Q: 1, gain: 0 }; }
    var cutQ = Math.round(2000 * Math.log10(band.q)) / 100;
    switch (band.type) {
      case 'lowcut': return { type: 'highpass', frequency: band.freq, Q: cutQ, gain: 0 };
      case 'highcut': return { type: 'lowpass', frequency: band.freq, Q: cutQ, gain: 0 };
      case 'lowshelf': return { type: 'lowshelf', frequency: band.freq, Q: 1, gain: band.gain };
      case 'highshelf': return { type: 'highshelf', frequency: band.freq, Q: 1, gain: band.gain };
      case 'notch': return { type: 'notch', frequency: band.freq, Q: band.q, gain: 0 };
      default: return { type: 'peaking', frequency: band.freq, Q: band.q, gain: band.gain };
    }
  }

  /* How much a biquad of this shape raises or lowers a frequency, in decibels: the Web Audio
     specification's own coefficients, so the curve drawn is the filter heard. */
  function biquadDb(shape, hz, rate) {
    var w0 = 2 * Math.PI * Math.min(shape.frequency, rate / 2) / rate, cos = Math.cos(w0), sin = Math.sin(w0);
    var A = Math.pow(10, shape.gain / 40), root = Math.sqrt(A);
    var aQ = sin / (2 * Math.max(shape.Q, 1e-4)), aQdb = sin / (2 * Math.pow(10, shape.Q / 20)), aS = sin / 2 * Math.SQRT2;
    var b0, b1, b2, a0, a1, a2;
    switch (shape.type) {
      case 'lowpass':
        b0 = (1 - cos) / 2; b1 = 1 - cos; b2 = b0; a0 = 1 + aQdb; a1 = -2 * cos; a2 = 1 - aQdb; break;
      case 'highpass':
        b0 = (1 + cos) / 2; b1 = -(1 + cos); b2 = b0; a0 = 1 + aQdb; a1 = -2 * cos; a2 = 1 - aQdb; break;
      case 'notch':
        b0 = 1; b1 = -2 * cos; b2 = 1; a0 = 1 + aQ; a1 = -2 * cos; a2 = 1 - aQ; break;
      case 'lowshelf':
        b0 = A * ((A + 1) - (A - 1) * cos + 2 * aS * root); b1 = 2 * A * ((A - 1) - (A + 1) * cos);
        b2 = A * ((A + 1) - (A - 1) * cos - 2 * aS * root);
        a0 = (A + 1) + (A - 1) * cos + 2 * aS * root; a1 = -2 * ((A - 1) + (A + 1) * cos);
        a2 = (A + 1) + (A - 1) * cos - 2 * aS * root; break;
      case 'highshelf':
        b0 = A * ((A + 1) + (A - 1) * cos + 2 * aS * root); b1 = -2 * A * ((A - 1) + (A + 1) * cos);
        b2 = A * ((A + 1) + (A - 1) * cos - 2 * aS * root);
        a0 = (A + 1) - (A - 1) * cos + 2 * aS * root; a1 = 2 * ((A - 1) - (A + 1) * cos);
        a2 = (A + 1) - (A - 1) * cos - 2 * aS * root; break;
      default:      // peaking
        b0 = 1 + aQ * A; b1 = -2 * cos; b2 = 1 - aQ * A; a0 = 1 + aQ / A; a1 = -2 * cos; a2 = 1 - aQ / A;
    }
    var w = 2 * Math.PI * hz / rate, c1 = Math.cos(w), s1 = Math.sin(w), c2 = Math.cos(2 * w), s2 = Math.sin(2 * w);
    var top = Math.pow(b0 + b1 * c1 + b2 * c2, 2) + Math.pow(b1 * s1 + b2 * s2, 2);
    var bottom = Math.pow(a0 + a1 * c1 + a2 * c2, 2) + Math.pow(a1 * s1 + a2 * s2, 2);
    return 10 * Math.log10(Math.max(top / bottom, 1e-12));
  }

  /* The whole equaliser's curve at a frequency, or one band's. */
  function peqDb(peq, hz, rate, only) {
    var total = 0;
    peq.bands.forEach(function (band, i) {
      if (only === undefined || only === i) { total += biquadDb(peqBandShape(band, peq.enabled !== false), hz, rate || 48000); }
    });
    return total;
  }

  // A preset is the whole rack: each one has the parametric equaliser flat and out.  (Here, and not
  // beside the presets, because the equaliser's own figures above have to exist first.)
  // a preset that sets the equaliser keeps its bands; the rest start from the default layout
  Object.keys(PRESETS).forEach(function (key) { PRESETS[key].peq = PRESETS[key].peq || defaultPeq(); });

  /* Space: the mix around the listener's head, for headphones (issue #65).  The left and right channels play from two
     virtual speakers in front, WIDTH degrees either side; what differs between them (the side signal, where a mix
     keeps its ambience) plays from two more behind, as much as SURROUND; HEIGHT lifts them all; ROOM lays a short
     diffuse room over it.  Each speaker is a Web Audio panner with the browser's own HRTF set, so what is heard is what
     a render writes.  It is for headphones only, so it is never part of the take's own file: Apply and the normal
     downloads leave it out, and it has a download of its own. */
  /* With stems (SOURCE: STEMS) each stem of the take is placed on its own: its left and right channels as a pair of
     speakers SPREAD degrees apart, centred at AZ (0 in front, positive to the right, 180 behind). */
  var SPACE_STEMS = {
    vocals: { az: 0, spread: 10 }, drums: { az: 0, spread: 50 }, bass: { az: 0, spread: 10 }, other: { az: 0, spread: 100 },
    guitar: { az: -40, spread: 20 }, piano: { az: 40, spread: 20 }, instruments: { az: 0, spread: 90 },
  };
  var SPACE_STEM_SCENES = {
    front: SPACE_STEMS,
    wide: { vocals: { az: 0, spread: 10 }, drums: { az: 0, spread: 90 }, bass: { az: 0, spread: 20 }, other: { az: 0, spread: 160 },
            guitar: { az: -70, spread: 30 }, piano: { az: 70, spread: 30 }, instruments: { az: 0, spread: 160 } },
    around: { vocals: { az: 0, spread: 10 }, drums: { az: 180, spread: 80 }, bass: { az: 0, spread: 10 }, other: { az: 0, spread: 220 },
              guitar: { az: -110, spread: 20 }, piano: { az: 110, spread: 20 }, instruments: { az: 0, spread: 220 } },
  };
  function defaultSpace() {
    return { enabled: false, width: 30, surround: 0, height: 0, room: 0, output: 0, source: 'mix',
             stems: JSON.parse(JSON.stringify(SPACE_STEMS)) };
  }
  function stemPlace(space, name) {
    var kept = (space && space.stems && space.stems[name]) || SPACE_STEMS[name] || { az: 0, spread: 30 };
    return { az: Number(kept.az) || 0, spread: Math.max(0, Math.min(300, Number(kept.spread) || 0)) };
  }
  /* What a pair of speakers sharing most of what they play adds at the ears (see the front pair, below), taken off. */
  function pairTrimDb(spread) { return -6.5 + (Math.min(90, Math.max(5, spread)) - 30) * 0.02; }

  /* 5.1: the speakers' angles, in WAV channel order (front left, front right, centre, LFE, back left, back right), and a
     direction's share of each by constant-power panning between the two speakers either side of it. */
  var SURROUND_SPEAKERS = [{ ch: 0, az: -30 }, { ch: 1, az: 30 }, { ch: 2, az: 0 }, { ch: 4, az: -110 }, { ch: 5, az: 110 }];
  function surroundGains(az) {
    var a = ((az % 360) + 540) % 360 - 180;                  // -180 .. 180
    var ring = SURROUND_SPEAKERS.slice().sort(function (x, y) { return x.az - y.az; });
    var gains = [0, 0, 0, 0, 0, 0];
    for (var i = 0; i < ring.length; i++) {
      var from = ring[i], to = ring[(i + 1) % ring.length];
      var start = from.az, end = to.az <= from.az ? to.az + 360 : to.az, at = a < start ? a + 360 : a;
      if (at >= start && at <= end) {
        var f = (at - start) / (end - start);
        gains[from.ch] += Math.cos(f * Math.PI / 2);
        gains[to.ch] += Math.sin(f * Math.PI / 2);
        return gains;
      }
    }
    gains[2] = 1;
    return gains;
  }
  Object.keys(PRESETS).forEach(function (key) { PRESETS[key].space = Object.assign(defaultSpace(), PRESETS[key].space || {}); });
  var SPACE_SCENES = {
    front:  { width: 30, surround: 0,    height: 0,  room: 0.15 },   // a pair of speakers in front of you
    wide:   { width: 60, surround: 0.25, height: 5,  room: 0.2 },    // a wider stage, a little around you
    around: { width: 45, surround: 0.6,  height: 10, room: 0.3 },    // inside the band
  };
  var SPACE_REAR = 110;            // the rear speakers' angle either side, as a 5.1 layout puts its surrounds
  var SPACE_REAR_DELAY = 0.018;    // and their sound a little later, so it reads as room rather than a second source

  function escHtml(v) {
    return String(v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function spaceOn(s) { return Boolean(s && !s.masterBypass && s.space && s.space.enabled); }

  /* Settings as the take's own file has them: Space out. */
  function withoutSpace(s) {
    var copy = JSON.parse(JSON.stringify(s || {}));
    if (copy.space) { copy.space.enabled = false; }
    return copy;
  }

  /* Where a virtual speaker sits: azimuth (degrees, right of centre is positive) and elevation, a metre away; the
     listener faces -z. */
  function spacePosition(azimuthDeg, elevationDeg) {
    var az = azimuthDeg * Math.PI / 180, el = elevationDeg * Math.PI / 180;
    return { x: Math.sin(az) * Math.cos(el), y: Math.sin(el), z: -Math.cos(az) * Math.cos(el) };
  }

  /* A short diffuse room: decaying noise, different in each ear, after a few milliseconds' gap, scaled to carry as
     much energy as it is given (so ROOM's level is the room's level against the music). */
  function makeRoomImpulse(ctx) {
    var seconds = 1.4, gap = Math.floor(0.008 * ctx.sampleRate);
    var length = Math.floor(seconds * ctx.sampleRate);
    var impulse = ctx.createBuffer(2, length, ctx.sampleRate);
    var seed = 7;
    function random() { seed = (seed * 16807) % 2147483647; return seed / 2147483647 * 2 - 1; }
    for (var ch = 0; ch < 2; ch++) {
      var data = impulse.getChannelData(ch), energy = 0, i;
      for (i = gap; i < length; i++) { data[i] = random() * Math.exp(-(i - gap) / (ctx.sampleRate * seconds / 6)); energy += data[i] * data[i]; }
      var scale = 1 / Math.sqrt(energy || 1);
      for (i = gap; i < length; i++) { data[i] *= scale; }
    }
    return impulse;
  }

  /* The sample rate a FLAC or WAV file says it has; 48000, what a take is made at, when the
     header is neither. */
  function fileSampleRate(arrayBuf) {
    var b = new Uint8Array(arrayBuf, 0, Math.min(arrayBuf.byteLength, 44));
    var rate = 0;
    if (b.length >= 21 && b[0] === 0x66 && b[1] === 0x4c && b[2] === 0x61 && b[3] === 0x43) {
      rate = (b[18] << 12) | (b[19] << 4) | (b[20] >> 4);          // fLaC: STREAMINFO
    } else if (b.length >= 28 && b[0] === 0x52 && b[1] === 0x49 && b[2] === 0x46 && b[3] === 0x46) {
      rate = b[24] | (b[25] << 8) | (b[26] << 16) | (b[27] << 24);  // RIFF: fmt
    }
    return (rate >= 8000 && rate <= 192000) ? rate : 48000;
  }

  function audioBufferToWav(buffer) {
    var numChannels = buffer.numberOfChannels;
    var sampleRate = buffer.sampleRate;
    var format = 1; // 16-bit PCM
    var bitDepth = 16;
    var bytesPerSample = bitDepth / 8;
    var blockAlign = numChannels * bytesPerSample;
    var length = buffer.length;
    var dataLength = length * blockAlign;
    var bufferLength = 44 + dataLength;

    var arrayBuffer = new ArrayBuffer(bufferLength);
    var view = new DataView(arrayBuffer);

    function writeString(offset, string) {
      for (var i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    }

    writeString(0, 'RIFF');
    view.setUint32(4, 36 + dataLength, true);
    writeString(8, 'WAVE');

    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, format, true);
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * blockAlign, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, bitDepth, true);

    writeString(36, 'data');
    view.setUint32(40, dataLength, true);

    var channels = [];
    for (var c = 0; c < numChannels; c++) {
      channels.push(buffer.getChannelData(c));
    }

    var offset = 44;
    for (var i = 0; i < length; i++) {
      for (var ch = 0; ch < numChannels; ch++) {
        var sample = channels[ch][i];
        if (sample < -1) { sample = -1; }
        else if (sample > 1) { sample = 1; }
        var s = sample < 0 ? sample * 32768 : sample * 32767;
        view.setInt16(offset, s, true);
        offset += 2;
      }
    }

    return new Blob([arrayBuffer], { type: 'audio/wav' });
  }

  /* Whether these settings change the sound at all.  When they do not, the take plays and
     saves untouched: the chain is not in the path.  It mirrors what applySettings does with
     each value, and playback, Save and Apply all ask it. */
  function chainEngaged(s) {
    if (!s || s.masterBypass) { return false; }
    function num(v) { var n = Number(v); return isNaN(n) ? 0 : n; }
    var eq = s.eq || {};
    if (num(eq.preGain) !== 0 || num(eq.outLevel) !== 0 || eq.phase) { return true; }
    if (s.eq && eq.enabled !== false) {
      var mid = eq.midGain !== undefined ? eq.midGain : eq.mid1Gain;
      var high = eq.highGain !== undefined ? eq.highGain : eq.airGain;
      if (num(eq.hp) > 20 || num(eq.lowGain) !== 0 || num(mid) !== 0 || num(high) !== 0) { return true; }
    }
    if (peqActive(peqOf(s))) { return true; }
    return Boolean((s.comp && s.comp.enabled !== false) ||
                   (s.imager && s.imager.enabled !== false) ||
                   (s.limit && s.limit.enabled !== false));
  }

  /* Settings kept before version 2 had every module switched in at values the rack called
     flat, though a compressor, an imager and a limiter at those values still change the sound.
     A module left exactly there was never touched, so it is read as out. */
  function upgradeSettings(stored) {
    if (!stored || typeof stored !== 'object') { return stored; }
    var s = JSON.parse(JSON.stringify(stored));
    if (s.version === 3) { return s; }
    if (s.version === 2) { return makeupAsHeard(s); }
    function is(v, want, fallback) { return Number(v === undefined ? fallback : v) === want; }
    var c = s.comp, i = s.imager, l = s.limit;
    if (c && c.enabled !== false && is(c.threshold, -18, -18) && is(c.ratio, 4, 4) &&
        is(c.attack, 0.015, 0.015) && is(c.release, 0.25, 0.25) && is(c.makeup, 0, 0) &&
        is(c.mix, 1, 1) && is(c.knee, 10, 10)) {
      c.enabled = false;
    }
    if (i && i.enabled !== false && is(i.bigness, 1, 1) && is(i.range, 5, 5) && is(i.stage, 5, 5) &&
        !i.harmonics && !i.bass) {
      i.enabled = false;
    }
    if (l && l.enabled !== false && is(l.drive, 0, 0) && is(l.ceiling, -0.1, -0.1) &&
        is(l.release, 0.08, 0.08) && !l.warmth) {
      l.enabled = false;
    }
    s.version = 2;
    return makeupAsHeard(s);
  }

  /* Settings kept before version 3 had a compressor's OUTPUT on top of the gain the node adds by itself.
     The rack now takes that gain off, so the amount is written into OUTPUT, to a tenth of a decibel:
     the settings sound as they did, and the knob reads all of the gain there is.  A compressor that is
     out is given it too, as the flat preset's is, so that switching it in sounds as it would have. */
  function makeupAsHeard(s) {
    var c = s.comp;
    if (c) {
      var hidden = nodeMakeupDb(c.threshold !== undefined ? c.threshold : -18, c.knee !== undefined ? c.knee : 10, c.ratio || 4);
      c.makeup = Math.round(((Number(c.makeup) || 0) + hidden) * 10) / 10;
    }
    s.version = 3;
    return s;
  }

  /* The values the chain reads, in one fixed shape, so two sets of settings can be compared:
     a name, an alias kept for older settings or the bypass switch does not make them differ. */
  function soundOf(settings) {
    var s = upgradeSettings(settings) || {};
    var eq = s.eq || {}, c = s.comp || {}, i = s.imager || {}, l = s.limit || {};
    function n(v, fallback) { var x = Number(v === undefined || v === null ? fallback : v); return isNaN(x) ? fallback : Math.round(x * 1e6) / 1e6; }
    return JSON.stringify([
      [eq.enabled !== false, n(eq.preGain, 0), Math.max(20, n(eq.hp, 20)), n(eq.lowFreq, 60), n(eq.lowGain, 0),
       n(eq.midFreq || eq.mid1Freq, 1600), n(eq.midGain !== undefined ? eq.midGain : eq.mid1Gain, 0),
       n(eq.highGain !== undefined ? eq.highGain : eq.airGain, 0), n(eq.outLevel, 0), Boolean(eq.phase)],
      [c.enabled !== false, n(c.threshold, -18), n(c.ratio, 4), n(c.attack, 0.015), n(c.release, 0.25),
       n(c.makeup, 0), n(c.mix, 1), n(c.knee, 10)],
      [i.enabled !== false, n(i.bigness, 1), n(i.range, 5), n(i.stage, 5), Boolean(i.harmonics),
       n(i.tubeHarmonics, 1), Boolean(i.bass)],
      [l.enabled !== false, n(l.drive, 0), n(l.ceiling, -0.1), n(l.release, 0.08), Boolean(l.warmth)],
      (function (sp) {
        return [Boolean(sp.enabled), n(sp.width, 30), n(sp.surround, 0), n(sp.height, 0), n(sp.room, 0), n(sp.output, 0)];
      })(s.space || {}),
      // the equaliser by what its filters do: a band that changes nothing is nothing, wherever it sits,
      // and so is the whole unit when it is out
      (function (p) {
        return p.bands.map(function (b) {
          var shape = peqBandShape(b, p.enabled);
          return shape.type === 'peaking' && shape.gain === 0 ? 0 : [shape.type, n(shape.frequency, 0), n(shape.Q, 1), n(shape.gain, 0)];
        });
      })(peqOf(s))
    ]);
  }

  /* The chain for an offline render: the same nodes and the same settings code as playback,
     on another context, with the values set at once rather than eased in. */
  function buildMasteringDspGraph(ctx, s) {
    var chain = Object.create(Engine);
    var entry = ctx.createGain();
    var out = ctx.createGain();
    chain.ctx = ctx;
    chain.build(ctx, entry, out);
    chain.applySettings(s || PRESETS['default'], true);
    return { inputNode: entry, outputNode: out, chain: chain };
  }

  // ------------------------------------------------------------- DSP Engine
  var Engine = {
    ctx: null,
    sourceNode: null,
    inputGain: null,

    // 1073 EQ Chain
    eqHP: null,
    eqLow: null,
    eqMid: null,
    eqMid1: null,
    eqHigh: null,
    eqAir: null,
    eqPhase: null,
    eqOutput: null,

    // Compressor
    peqBands: null,
    spectrum: null,
    compDryGain: null,
    compDryDelay: null,
    compWetGain: null,
    compressor: null,
    compMakeup: null,

    // Vintage Stereo Imager & Spatial Processor
    imagerDryGain: null,
    imagerWetGain: null,
    imagerSplitter: null,
    imagerMidBus: null,
    imagerSideBus: null,
    imagerBassFilter: null,
    imagerSideHP: null,
    imagerRangeFilter: null,
    imagerStageFilter: null,
    imagerWidthGain: null,
    imagerHarmonicsDrive: null,
    imagerShaper: null,
    imagerShaperIn: null,
    imagerShaperOut: null,
    imagerMerger: null,

    // Space (headphones 3D); and the take's stems, placed one by one, in place of the take when SOURCE is STEMS
    sourceToChain: null,
    stemBus: null,
    stemNodes: null,
    stemsReady: false,
    spaceDryGain: null,
    spaceWetGain: null,
    spaceFront: null,
    spaceRear: null,
    spaceRearGain: null,
    spaceRoomGain: null,
    spacePanGain: null,
    spaceOutput: null,

    // Limiter
    limitDrive: null,
    limitShaper: null,
    limitShaperIn: null,
    limitShaperOut: null,
    limitGuard: null,
    limiter: null,
    limitCeiling: null,
    limitDryGain: null,
    limitWetGain: null,

    // Master / Bypass crossfader
    masterDryGain: null,
    masterWetGain: null,
    analyser: null,

    // Telemetry
    needleVal: 0,
    needleVel: 0,

    init: function () {
      if (this.ctx) { return true; }
      var audioEl = document.getElementById('audio');
      if (!audioEl) { return false; }

      var AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) { return false; }
      this.ctx = new AudioContextClass();

      try {
        this.sourceNode = this.ctx.createMediaElementSource(audioEl);
      } catch (e) {
        return false;
      }

      var self = this;
      audioEl.addEventListener('play', function () {
        self.resume();
      });

      this.build(this.ctx, this.sourceNode, this.ctx.destination);
      return true;
    },

    /* The chain itself, from source to destination, on any context: the page's for playback,
       an offline one for a file.  Everything starts out of the path; applySettings switches
       in what the settings ask for. */
    build: function (ctx, source, destination) {
      // 1. Input Gain (Preamp Gain / Drive)
      this.inputGain = ctx.createGain();
      this.inputGain.gain.value = 1.0;

      // 2. 1073 Parametric EQ chain
      // High Pass Filter (Low cut: 20Hz, 50Hz, 80Hz, 160Hz, 300Hz)
      this.eqHP = ctx.createBiquadFilter();
      this.eqHP.type = 'highpass';
      this.eqHP.frequency.value = 20;
      this.eqHP.Q.value = 0.707;

      // Low Shelf (35Hz, 60Hz, 110Hz, 220Hz)
      this.eqLow = ctx.createBiquadFilter();
      this.eqLow.type = 'lowshelf';
      this.eqLow.frequency.value = 60;
      this.eqLow.gain.value = 0;

      // Mid Band Peaking (360Hz, 700Hz, 1.6kHz, 3.2kHz, 4.8kHz, 7.2kHz)
      this.eqMid = ctx.createBiquadFilter();
      this.eqMid.type = 'peaking';
      this.eqMid.frequency.value = 1600;
      this.eqMid.Q.value = 1.1;
      this.eqMid.gain.value = 0;
      this.eqMid1 = this.eqMid; // backward compat

      // High Shelf (fixed 12 kHz analog-modeled corner)
      this.eqHigh = ctx.createBiquadFilter();
      this.eqHigh.type = 'highshelf';
      this.eqHigh.frequency.value = 6800; // Analog 1073 12k shelf corner (slopes musically from 5k-14k)
      this.eqHigh.gain.value = 0;
      this.eqAir = this.eqHigh; // backward compat

      // Phase invert node
      this.eqPhase = ctx.createGain();
      this.eqPhase.gain.value = 1.0;

      // Output level trim node
      this.eqOutput = ctx.createGain();
      this.eqOutput.gain.value = 1.0;

      // Connect EQ chain
      this.inputGain.connect(this.eqHP);
      this.eqHP.connect(this.eqLow);
      this.eqLow.connect(this.eqMid);
      this.eqMid.connect(this.eqHigh);
      this.eqHigh.connect(this.eqPhase);
      this.eqPhase.connect(this.eqOutput);

      // 3. Vintage Compressor stage with parallel blend
      this.compDryGain = ctx.createGain();
      this.compWetGain = ctx.createGain();
      this.compressor = ctx.createDynamicsCompressor();
      this.compressor.threshold.value = -18;
      this.compressor.knee.value = 10;
      this.compressor.ratio.value = 4;
      this.compressor.attack.value = 0.015;
      this.compressor.release.value = 0.25;

      this.compMakeup = ctx.createGain();
      this.compMakeup.gain.value = 1.0;

      // 2b. The parametric equaliser: its biquads in a row, after the 1073 and before the compressor
      this.peqBands = [];
      var eqTail = this.eqOutput;
      for (var band = 0; band < defaultPeq().bands.length; band++) {
        var filter = ctx.createBiquadFilter();
        filter.type = 'peaking';
        filter.frequency.value = 1000;
        filter.Q.value = 1;
        filter.gain.value = 0;
        eqTail.connect(filter);
        eqTail = filter;
        this.peqBands.push(filter);
      }

      // The compressor looks ahead, so what it puts out is behind what goes in by the frames of 6 ms.
      // The dry signal waits the same, or a blend of the two (MIX) combs the sound.
      this.compDryDelay = ctx.createDelay(0.05);
      this.compDryDelay.delayTime.value = Math.floor(0.006 * ctx.sampleRate) / ctx.sampleRate;
      eqTail.connect(this.compDryDelay);
      this.compDryDelay.connect(this.compDryGain);
      eqTail.connect(this.compressor);
      this.compressor.connect(this.compMakeup);
      this.compMakeup.connect(this.compWetGain);

      this.compDryGain.gain.value = 1.0;
      this.compWetGain.gain.value = 0.0;

      var compSum = ctx.createGain();
      this.compDryGain.connect(compSum);
      this.compWetGain.connect(compSum);

      // 4. Vintage Stereo Imager & Spatial Processor stage
      this.imagerDryGain = ctx.createGain();
      this.imagerWetGain = ctx.createGain();
      this.imagerDryGain.gain.value = 1.0;
      this.imagerWetGain.gain.value = 0.0;

      // M/S Matrix
      this.imagerSplitter = ctx.createChannelSplitter(2);

      // Mid bus
      var lToM = ctx.createGain(); lToM.gain.value = 0.5;
      var rToM = ctx.createGain(); rToM.gain.value = 0.5;
      this.imagerMidBus = ctx.createGain();
      this.imagerBassFilter = ctx.createBiquadFilter();
      this.imagerBassFilter.type = 'lowshelf';
      this.imagerBassFilter.frequency.value = 85;
      this.imagerBassFilter.gain.value = 0;

      // Side bus
      var lToS = ctx.createGain(); lToS.gain.value = 0.5;
      var rToS = ctx.createGain(); rToS.gain.value = -0.5;
      this.imagerSideBus = ctx.createGain();

      // Side filtering & spatial processing
      this.imagerSideHP = ctx.createBiquadFilter();
      this.imagerSideHP.type = 'highpass';
      this.imagerSideHP.frequency.value = 90; // mono bass anchor
      this.imagerSideHP.Q.value = 0.707;

      this.imagerRangeFilter = ctx.createBiquadFilter();
      this.imagerRangeFilter.type = 'highpass';
      this.imagerRangeFilter.frequency.value = 800;
      this.imagerRangeFilter.Q.value = 0.707;

      this.imagerStageFilter = ctx.createBiquadFilter();
      this.imagerStageFilter.type = 'allpass';
      this.imagerStageFilter.frequency.value = 1200;

      this.imagerWidthGain = ctx.createGain();
      this.imagerWidthGain.gain.value = 1.0;

      // Tube Harmonics saturation
      this.imagerHarmonicsDrive = ctx.createGain();
      this.imagerHarmonicsDrive.gain.value = 1.0;
      this.imagerShaper = ctx.createWaveShaper();
      this.imagerShaper.oversample = '4x';
      this.imagerShaper.curve = null;
      this.imagerShaperIn = ctx.createGain();
      this.imagerShaperIn.gain.value = 1 / SHAPER_SPAN;
      this.imagerShaperOut = ctx.createGain();
      this.imagerShaperOut.gain.value = SHAPER_SPAN;

      // M/S reconstruction
      var midToL = ctx.createGain(); midToL.gain.value = 1.0;
      var midToR = ctx.createGain(); midToR.gain.value = 1.0;
      var sideToL = ctx.createGain(); sideToL.gain.value = 1.0;
      var sideToR = ctx.createGain(); sideToR.gain.value = -1.0;
      this.imagerMerger = ctx.createChannelMerger(2);

      // Connect M/S network
      this.imagerSplitter.connect(lToM, 0);
      this.imagerSplitter.connect(rToM, 1);
      lToM.connect(this.imagerMidBus);
      rToM.connect(this.imagerMidBus);
      this.imagerMidBus.connect(this.imagerBassFilter);

      this.imagerSplitter.connect(lToS, 0);
      this.imagerSplitter.connect(rToS, 1);
      lToS.connect(this.imagerSideBus);
      rToS.connect(this.imagerSideBus);
      this.imagerSideBus.connect(this.imagerSideHP);
      this.imagerSideHP.connect(this.imagerRangeFilter);
      this.imagerRangeFilter.connect(this.imagerStageFilter);
      this.imagerStageFilter.connect(this.imagerWidthGain);

      // Reconstruct to stereo
      this.imagerBassFilter.connect(midToL);
      this.imagerBassFilter.connect(midToR);
      this.imagerWidthGain.connect(sideToL);
      this.imagerWidthGain.connect(sideToR);

      midToL.connect(this.imagerMerger, 0, 0);
      sideToL.connect(this.imagerMerger, 0, 0);
      midToR.connect(this.imagerMerger, 0, 1);
      sideToR.connect(this.imagerMerger, 0, 1);

      // Harmonics post-merger
      this.imagerMerger.connect(this.imagerHarmonicsDrive);
      this.imagerHarmonicsDrive.connect(this.imagerShaperIn);
      this.imagerShaperIn.connect(this.imagerShaper);
      this.imagerShaper.connect(this.imagerShaperOut);
      this.imagerShaperOut.connect(this.imagerWetGain);

      // Route compSum into imager
      compSum.connect(this.imagerDryGain);
      compSum.connect(this.imagerSplitter);

      // Sum dry and wet
      var imagerSum = ctx.createGain();
      this.imagerDryGain.connect(imagerSum);
      this.imagerWetGain.connect(imagerSum);

      // 5. Master Limiter & Tube Warmth stage (Fed by imagerSum)
      this.limitDrive = ctx.createGain();
      this.limitDrive.gain.value = 1.0;

      this.limitShaper = ctx.createWaveShaper();
      this.limitShaper.oversample = '4x';
      this.limitShaper.curve = null;
      this.limitShaperIn = ctx.createGain();
      this.limitShaperIn.gain.value = 1 / SHAPER_SPAN;
      this.limitShaperOut = ctx.createGain();
      this.limitShaperOut.gain.value = SHAPER_SPAN;

      this.limiter = ctx.createDynamicsCompressor();
      this.limiter.threshold.value = -0.5;
      this.limiter.knee.value = 0.0;
      this.limiter.ratio.value = 20.0;
      this.limiter.attack.value = 0.001;
      this.limiter.release.value = 0.08;

      // What the limiter lets past full scale, a fraction of a decibel on a hard-driven peak, stops
      // here, so that the ceiling after it is the most the rack puts out.
      this.limitGuard = ctx.createWaveShaper();
      this.limitGuard.curve = makeGuardCurve();

      this.limitCeiling = ctx.createGain();
      this.limitCeiling.gain.value = Math.pow(10, -0.1 / 20); // -0.1 dB

      // Out means out: the limiter has a dry path of its own, like the other two
      this.limitDryGain = ctx.createGain();
      this.limitWetGain = ctx.createGain();
      this.limitDryGain.gain.value = 1.0;
      this.limitWetGain.gain.value = 0.0;
      var limitSum = ctx.createGain();

      // 4b. Space: four HRTF panners (a front pair from left and right, a rear pair from the side signal) and a room,
      // with a dry path of its own like the other modules.
      this.spaceDryGain = ctx.createGain();
      this.spaceWetGain = ctx.createGain();
      this.spaceDryGain.gain.value = 1.0;
      this.spaceWetGain.gain.value = 0.0;
      var spaceSplit = ctx.createChannelSplitter(2);
      var spaceBus = ctx.createGain();
      function panner() {
        var p = ctx.createPanner();
        p.panningModel = 'HRTF';
        p.distanceModel = 'inverse';
        p.refDistance = 1;
        p.rolloffFactor = 0;          // the angle places it; the distance does not turn it down
        p.channelCount = 1;
        p.channelCountMode = 'explicit';
        p.connect(spaceBus);
        return p;
      }
      this.spaceFront = [panner(), panner()];
      spaceSplit.connect(this.spaceFront[0], 0);
      spaceSplit.connect(this.spaceFront[1], 1);
      // the side signal, (L - R) / 2, above the bass, a little later, to the rear pair (the right one inverted)
      var sideL = ctx.createGain(); sideL.gain.value = 0.5;
      var sideR = ctx.createGain(); sideR.gain.value = -0.5;
      var side = ctx.createGain();
      spaceSplit.connect(sideL, 0);
      spaceSplit.connect(sideR, 1);
      sideL.connect(side);
      sideR.connect(side);
      var sideHP = ctx.createBiquadFilter();
      sideHP.type = 'highpass';
      sideHP.frequency.value = 150;
      var sideDelay = ctx.createDelay(0.1);
      sideDelay.delayTime.value = SPACE_REAR_DELAY;
      this.spaceRearGain = ctx.createGain();
      this.spaceRearGain.gain.value = 0;
      side.connect(sideHP);
      sideHP.connect(sideDelay);
      sideDelay.connect(this.spaceRearGain);
      this.spaceRear = [panner(), panner()];
      var invert = ctx.createGain(); invert.gain.value = -1;
      this.spaceRearGain.connect(this.spaceRear[0]);
      this.spaceRearGain.connect(invert);
      invert.connect(this.spaceRear[1]);
      // the room, over the whole
      var room = ctx.createConvolver();
      room.normalize = false;      // the impulse is scaled already (makeRoomImpulse)
      room.buffer = makeRoomImpulse(ctx);
      this.spaceRoomGain = ctx.createGain();
      this.spaceRoomGain.gain.value = 0;
      this.spaceOutput = ctx.createGain();
      this.spaceOutput.gain.value = 1.0;
      // What the two front speakers share (most of a mix) reaches each ear from both and adds up, as it does from real
      // speakers: about 6 dB more on a finished take, less the wider they stand.  It is taken off again here, so Space
      // keeps the take's loudness and its peaks where they were, and the room is set against the music as heard.
      this.spacePanGain = ctx.createGain();
      this.spacePanGain.gain.value = 1.0;
      imagerSum.connect(spaceSplit);
      imagerSum.connect(room);
      room.connect(this.spaceRoomGain);
      this.spaceRoomGain.connect(this.spaceOutput);
      spaceBus.connect(this.spacePanGain);
      this.spacePanGain.connect(this.spaceOutput);
      this.spaceOutput.connect(this.spaceWetGain);
      imagerSum.connect(this.spaceDryGain);
      var spaceSum = ctx.createGain();
      this.spaceDryGain.connect(spaceSum);
      this.spaceWetGain.connect(spaceSum);

      spaceSum.connect(this.limitDryGain);
      spaceSum.connect(this.limitDrive);
      // Drive, then the tube stage when it is in, then the limiter: an over reaches the limiter whole.
      this.limitDrive.connect(this.limitShaperIn);
      this.limitShaperIn.connect(this.limitShaper);
      this.limitShaper.connect(this.limitShaperOut);
      this.limitShaperOut.connect(this.limiter);
      this.limiter.connect(this.limitGuard);
      this.limitGuard.connect(this.limitCeiling);
      this.limitCeiling.connect(this.limitWetGain);
      this.limitDryGain.connect(limitSum);
      this.limitWetGain.connect(limitSum);

      // 6. Master Output / Bypass Routing
      this.masterDryGain = ctx.createGain();
      this.masterWetGain = ctx.createGain();
      this.masterDryGain.gain.value = 1.0;
      this.masterWetGain.gain.value = 0.0;

      this.analyser = ctx.createAnalyser();
      this.analyser.fftSize = 256;
      // What is heard, finely enough to draw behind the equaliser's curve: it only listens
      this.spectrum = ctx.createAnalyser();
      this.spectrum.fftSize = 4096;
      this.spectrum.smoothingTimeConstant = 0.82;

      this.sourceToChain = ctx.createGain();
      this.sourceToChain.gain.value = 1.0;
      this.stemBus = ctx.createGain();
      this.stemBus.gain.value = 0.0;
      this.stemNodes = {};
      source.connect(this.sourceToChain);
      this.sourceToChain.connect(this.inputGain);
      this.stemBus.connect(this.inputGain);
      source.connect(this.masterDryGain);

      limitSum.connect(this.masterWetGain);

      this.masterDryGain.connect(this.analyser);
      this.masterWetGain.connect(this.analyser);
      this.analyser.connect(destination);
      this.analyser.connect(this.spectrum);
    },

    makeTubeCurve: function () {
      return makeTubeCurve();
    },

    /* A stem's place: its stereo input split to two HRTF panners, a trim, into the stem bus (which feeds the chain where
       the take would). */
    stemNode: function (name) {
      if (this.stemNodes[name]) { return this.stemNodes[name]; }
      var ctx = this.ctx, bus = this.stemBus;
      var node = { input: ctx.createGain(), trim: ctx.createGain(), pans: [] };
      var split = ctx.createChannelSplitter(2);
      node.input.connect(split);
      for (var side = 0; side < 2; side++) {
        var p = ctx.createPanner();
        p.panningModel = 'HRTF'; p.distanceModel = 'inverse'; p.refDistance = 1; p.rolloffFactor = 0;
        p.channelCount = 1; p.channelCountMode = 'explicit';
        split.connect(p, side);
        p.connect(node.trim);
        node.pans.push(p);
      }
      node.trim.connect(bus);
      this.stemNodes[name] = node;
      return node;
    },

    /* A shaper as the tube stage, or as nothing.  Its curve is given only when that changes: a turned
       knob calls applySettings many times a second, and a curve handed over again restarts the shaper. */
    setShaper: function (shaper, tube) {
      if (shaper.tube === tube) { return; }
      shaper.curve = tube ? this.makeTubeCurve() : null;
      shaper.tube = tube;
    },

    resume: function () {
      if (this.ctx && this.ctx.state === 'suspended') {
        return this.ctx.resume().catch(function () {});
      }
      return Promise.resolve();
    },

    applySettings: function (s, atOnce) {
      if (!this.init()) { return; }
      var ctx = this.ctx;
      var now = ctx.currentTime;
      var ramp = 0.02;
      // Playback eases each value in, so a turned knob does not click; a render sets it.
      function set(param, value) {
        if (atOnce) { param.value = value; } else { param.setTargetAtTime(value, now, ramp); }
      }

      // The take's stems in place of the take: placed before the chain, so Space's own placing and the imager (whose
      // widening would undo the placing) stay out of the path.
      var useStems = Boolean(spaceOn(s) && s.space.source === 'stems' && this.stemsReady);
      set(this.sourceToChain.gain, useStems ? 0.0 : 1.0);
      set(this.stemBus.gain, useStems ? 1.0 : 0.0);

      // 1073 EQ Stage
      if (s.eq) {
        var eqOn = s.eq.enabled !== false;

        // Preamp Gain / Drive
        var preDb = s.eq.preGain !== undefined ? Number(s.eq.preGain) : 0;
        set(this.inputGain.gain, Math.pow(10, preDb / 20));

        // High Pass Filter (Low Cut)
        var hpVal = Number(s.eq.hp);
        if (isNaN(hpVal) || hpVal <= 20) { hpVal = 20; }
        set(this.eqHP.frequency, eqOn ? hpVal : 20);

        // Low Shelf
        var lowF = Number(s.eq.lowFreq);
        if (isNaN(lowF) || lowF <= 0) { lowF = 60; }
        var lowG = eqOn ? (s.eq.lowGain !== undefined ? Number(s.eq.lowGain) : 0) : 0;
        set(this.eqLow.frequency, lowF);
        set(this.eqLow.gain, lowG);

        // Mid Band
        var midF = Number(s.eq.midFreq || s.eq.mid1Freq);
        if (isNaN(midF) || midF <= 0) { midF = 1600; }
        var midG = eqOn ? (s.eq.midGain !== undefined ? Number(s.eq.midGain) : (s.eq.mid1Gain !== undefined ? Number(s.eq.mid1Gain) : 0)) : 0;
        set(this.eqMid.frequency, midF);
        set(this.eqMid.gain, midG);

        // High Shelf (Fixed 12 kHz analog-modeled corner)
        var hiG = eqOn ? (s.eq.highGain !== undefined ? Number(s.eq.highGain) : (s.eq.airGain !== undefined ? Number(s.eq.airGain) : 0)) : 0;
        set(this.eqHigh.frequency, 6800);
        set(this.eqHigh.gain, hiG);

        // Phase Invert
        var isPhaseInvert = Boolean(s.eq.phase);
        set(this.eqPhase.gain, isPhaseInvert ? -1.0 : 1.0);

        // Output Trim
        var outDb = s.eq.outLevel !== undefined ? Number(s.eq.outLevel) : 0;
        set(this.eqOutput.gain, Math.pow(10, outDb / 20));
      }

      // Parametric equaliser
      var peq = peqOf(s);
      for (var b = 0; b < this.peqBands.length; b++) {
        var shape = peqBandShape(peq.bands[b], peq.enabled);
        if (this.peqBands[b].type !== shape.type) { this.peqBands[b].type = shape.type; }
        set(this.peqBands[b].frequency, shape.frequency);
        set(this.peqBands[b].Q, shape.Q);
        set(this.peqBands[b].gain, shape.gain);
      }

      // Compressor
      if (s.comp) {
        // A module that is out keeps its values all the same: only its place in the path changes
        var compOn = s.comp.enabled !== false;
        var mix = typeof s.comp.mix === 'number' ? s.comp.mix : 1.0;
        set(this.compDryGain.gain, compOn ? 1.0 - mix : 1.0);
        set(this.compWetGain.gain, compOn ? mix : 0.0);
        var compThreshold = s.comp.threshold !== undefined ? s.comp.threshold : -18;
        var compRatio = s.comp.ratio || 4;
        var compKnee = s.comp.knee !== undefined ? s.comp.knee : 10;
        set(this.compressor.threshold, compThreshold);
        set(this.compressor.ratio, compRatio);
        set(this.compressor.attack, s.comp.attack || 0.015);
        set(this.compressor.release, s.comp.release || 0.25);
        set(this.compressor.knee, compKnee);
        // OUTPUT is all the gain the compressor adds: what the node adds by itself is taken off again
        var makeupDb = (s.comp.makeup || 0) - nodeMakeupDb(compThreshold, compKnee, compRatio);
        set(this.compMakeup.gain, Math.pow(10, makeupDb / 20));
      }

      // Vintage Stereo Imager Stage (Placed before Master Limiter)
      if (s.imager) {
        var imagerOn = s.imager.enabled !== false && !useStems;
        set(this.imagerDryGain.gain, imagerOn ? 0.0 : 1.0);
        set(this.imagerWetGain.gain, imagerOn ? 1.0 : 0.0);

        // Range knob: 1 ("HIGH", 2800 Hz) to 9 ("OPEN", 180 Hz)
        var rangeVal = Number(s.imager.range);
        if (isNaN(rangeVal) || rangeVal < 1) { rangeVal = 5; }
        var rangeNorm = (rangeVal - 1) / 8;
        var rangeHz = 2800 * Math.pow(180 / 2800, rangeNorm);
        set(this.imagerRangeFilter.frequency, rangeHz);

        // Stage knob: 1 ("BACK", 350 Hz) to 9 ("FRONT", 3200 Hz)
        var stageVal = Number(s.imager.stage);
        if (isNaN(stageVal) || stageVal < 1) { stageVal = 5; }
        var stageNorm = (stageVal - 1) / 8;
        var stageHz = 350 * Math.pow(3200 / 350, stageNorm);
        set(this.imagerStageFilter.frequency, stageHz);

        // Bigness knob: 1 ("MIN", 1.0x width) to 9 ("MAX", 2.4x width)
        var bignessVal = Number(s.imager.bigness);
        if (isNaN(bignessVal) || bignessVal < 0) { bignessVal = 1; }
        var widthFactor = (bignessVal <= 1) ? bignessVal : (1.0 + ((bignessVal - 1) / 8) * 1.4);
        set(this.imagerWidthGain.gain, widthFactor);

        // Bass punch circuit: +3.0 dB low shelf at 85 Hz
        var bassOn = Boolean(s.imager.bass);
        set(this.imagerBassFilter.gain, bassOn ? 3.0 : 0.0);

        // Harmonics toggle & Tube Harmonics drive
        var harmOn = Boolean(s.imager.harmonics);
        var tubeH = Number(s.imager.tubeHarmonics);
        if (isNaN(tubeH) || tubeH < 1) { tubeH = 1; }
        if (harmOn) {
          var driveLinear = 1.0 + ((tubeH - 1) / 8) * 0.8;
          set(this.imagerHarmonicsDrive.gain, driveLinear);
          this.setShaper(this.imagerShaper, true);
        } else {
          set(this.imagerHarmonicsDrive.gain, 1.0);
          this.setShaper(this.imagerShaper, false);
        }
      }

      // Limiter
      if (s.limit) {
        var limitOn = s.limit.enabled !== false;
        set(this.limitDryGain.gain, limitOn ? 0.0 : 1.0);
        set(this.limitWetGain.gain, limitOn ? 1.0 : 0.0);
        var driveLin = Math.pow(10, (s.limit.drive || 0) / 20);
        set(this.limitDrive.gain, driveLin);
        set(this.limiter.ratio, 20.0);
        set(this.limiter.release, s.limit.release || 0.08);
        var ceilDb = s.limit.ceiling !== undefined ? s.limit.ceiling : -0.1;
        set(this.limitCeiling.gain, Math.pow(10, ceilDb / 20));
        if (s.limit.warmth) {
          this.setShaper(this.limitShaper, true);
        } else {
          this.setShaper(this.limitShaper, false);
        }
      }

      // Space
      if (s.space) {
        var sp = s.space;
        // With stems the placing is done before the chain: here only the room is added, over the placed stems
        var spOn = Boolean(sp.enabled) && !useStems;
        set(this.spaceDryGain.gain, spOn ? 0.0 : 1.0);
        set(this.spaceWetGain.gain, spOn || useStems ? 1.0 : 0.0);
        var width = Math.max(5, Math.min(90, Number(sp.width) || 30));
        var height = Math.max(0, Math.min(45, Number(sp.height) || 0));
        function place(p, az, el) {
          var at = spacePosition(az, el);
          if (p.positionX) { set(p.positionX, at.x); set(p.positionY, at.y); set(p.positionZ, at.z); }
          else { p.setPosition(at.x, at.y, at.z); }
        }
        place(this.spaceFront[0], -width, height);
        place(this.spaceFront[1], width, height);
        place(this.spaceRear[0], -SPACE_REAR, height);
        place(this.spaceRear[1], SPACE_REAR, height);
        set(this.spaceRearGain.gain, useStems ? 0 : Math.max(0, Math.min(1, Number(sp.surround) || 0)) * 1.4);
        set(this.spaceRoomGain.gain, Math.max(0, Math.min(1, Number(sp.room) || 0)) * 0.45);
        // measured on finished takes: +6.5 dB with the speakers 30 degrees out, +5.3 dB at 90; and the rear pair and
        // the room add up to 0.4 and 0.7 dB at full, which OUTPUT at 0 takes off too
        set(this.spacePanGain.gain, useStems ? 0 : Math.pow(10, (-6.5 + (width - 30) * 0.02) / 20));
        var spaceExtraDb = (useStems ? 0 : 0.4 * Math.max(0, Math.min(1, Number(sp.surround) || 0))) + 0.7 * Math.max(0, Math.min(1, Number(sp.room) || 0));
        // OUTPUT is in each stem's trim when stems are placed; here it would be on the room alone
        set(this.spaceOutput.gain, Math.pow(10, ((useStems ? 0 : Number(sp.output) || 0) - spaceExtraDb) / 20));
        // each stem's pair, at its own angle and spread, all at HEIGHT
        for (var stemName in this.stemNodes) {
          if (!this.stemNodes.hasOwnProperty(stemName)) { continue; }
          var at = stemPlace(sp, stemName), node = this.stemNodes[stemName];
          place(node.pans[0], at.az - at.spread / 2, height);
          place(node.pans[1], at.az + at.spread / 2, height);
          set(node.trim.gain, Math.pow(10, (pairTrimDb(at.spread) + (Number(sp.output) || 0)) / 20));
        }
      }

      // Master: the chain is in the path only when something in it changes the sound, so a
      // rack left flat plays the take as it is, and so does Bypass; Space, which the take's own file
      // never has, puts it in the path too
      if (!chainEngaged(s) && !spaceOn(s)) {
        set(this.masterDryGain.gain, 1.0);
        set(this.masterWetGain.gain, 0.0);
      } else {
        set(this.masterDryGain.gain, 0.0);
        set(this.masterWetGain.gain, 1.0);
      }
    },

    getGainReduction: function () {
      if (!this.compressor) { return 0; }
      var red = this.compressor.reduction;
      if (typeof red === 'number') {
        return Math.abs(red);
      }
      return 0;
    }
  };

  // ------------------------------------------------------------- UI Controller
  var USER_PRESETS_KEY = 'yeufonic.mastering_user_presets';
  var FOLDED_KEY = 'yeufonic.rack.folded';
  var TRASH_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" ' +
    'stroke-linejoin="round" aria-hidden="true"><path d="M4.5 7h15M9.5 7V4.8h5V7M6.5 7l1 12.2h9l1-12.2"/></svg>';

  var Rack = {
    currentTakeId: null,
    settings: JSON.parse(JSON.stringify(PRESETS['default'])),
    saveTimer: null,
    isOpen: false,
    animFrame: null,

    getUserPresets: function () {
      try {
        var raw = localStorage.getItem(USER_PRESETS_KEY);
        if (!raw) { return {}; }
        return JSON.parse(raw) || {};
      } catch (e) {
        return {};
      }
    },

    /* The ids of the user's presets with this name, whatever its case. */
    userPresetsNamed: function (presets, name) {
      var wanted = String(name || '').trim().toLowerCase();
      return Object.keys(presets).filter(function (id) {
        return String((presets[id] && presets[id].name) || '').trim().toLowerCase() === wanted;
      });
    },

    saveUserPresets: function (presets) {
      try {
        localStorage.setItem(USER_PRESETS_KEY, JSON.stringify(presets));
      } catch (e) {}
    },

    init: function () {
      this.renderMarkup();
      this.installFolds();
      this.rebuildPresetDropdown('default');
      this.bindEvents();
      this.bindPeq();
      this.initDraggable();
      this.startMeterLoop();
    },

    /* Each module folds to its bar and opens again with the arrow at the left of the bar; which are folded is kept in
       this browser.  Folded or not, a module sounds the same. */
    installFolds: function () {
      var self = this;
      var folded = [];
      try { folded = JSON.parse(localStorage.getItem(FOLDED_KEY) || '[]') || []; } catch (e) { folded = []; }
      Array.prototype.forEach.call(document.querySelectorAll('#rack-panel .rack-unit'), function (unit) {
        var bar = unit.querySelector('.unit-bar');
        if (!bar || !unit.id || bar.querySelector('.unit-fold')) { return; }
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'unit-fold';
        button.innerHTML = '<svg viewBox="0 0 12 12" width="10" height="10" aria-hidden="true"><path d="M2.5 4.25 6 7.75l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
        bar.insertBefore(button, bar.firstChild);
        function paint() {
          var shut = unit.classList.contains('folded');
          button.setAttribute('aria-expanded', shut ? 'false' : 'true');
          button.title = shut ? t('Open this module') : t('Fold this module');
        }
        unit.classList.toggle('folded', folded.indexOf(unit.id) !== -1);
        paint();
        button.addEventListener('click', function (e) {
          e.stopPropagation();
          unit.classList.toggle('folded');
          paint();
          var now = Array.prototype.filter.call(document.querySelectorAll('#rack-panel .rack-unit.folded'), function (u) { return u.id; })
            .map(function (u) { return u.id; });
          try { localStorage.setItem(FOLDED_KEY, JSON.stringify(now)); } catch (err) { /* private mode */ }
          if (typeof self.fitToWindow === 'function') { self.fitToWindow(); }
        });
      });
    },

    rebuildPresetDropdown: function (selectedKey) {
      var group = document.getElementById('rack-user-presets-group');
      var select = document.getElementById('rack-preset-select');
      if (!group || !select) { return; }

      group.innerHTML = '';
      var userPresets = this.getUserPresets();
      var ids = Object.keys(userPresets);

      if (ids.length === 0) {
        var emptyOpt = document.createElement('option');
        emptyOpt.value = '';
        emptyOpt.disabled = true;
        emptyOpt.textContent = t('(No user presets)');
        group.appendChild(emptyOpt);
      } else {
        ids.forEach(function (id) {
          var opt = document.createElement('option');
          opt.value = id;
          opt.textContent = userPresets[id].name || id;
          group.appendChild(opt);
        });
      }

      if (selectedKey) {
        select.value = selectedKey;
      }
      this.paintPresetButton();
    },

    /* The preset box is a button and a menu drawn over the select, which stays (hidden) as what holds the
       choice: a select cannot put a bin beside each of the user's presets. */
    paintPresetButton: function () {
      var select = document.getElementById('rack-preset-select');
      var label = document.getElementById('rack-preset-label');
      if (!select || !label) { return; }
      var opt = select.options[select.selectedIndex];
      label.textContent = opt ? opt.textContent : t('Custom');
    },

    presetMenuOpen: function () {
      var menu = document.getElementById('rack-preset-menu');
      return !!menu && !menu.classList.contains('hidden');
    },

    paintPresetMenu: function () {
      var menu = document.getElementById('rack-preset-menu');
      var select = document.getElementById('rack-preset-select');
      if (!menu || !select) { return; }
      var html = [];
      var esc = function (t) {
        return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
      };
      Array.prototype.forEach.call(select.querySelectorAll('optgroup'), function (group) {
        var mine = group.id === 'rack-user-presets-group';
        html.push('<div class="rack-preset-group">' + esc(group.label) + '</div>');
        Array.prototype.forEach.call(group.querySelectorAll('option'), function (opt) {
          if (opt.disabled) {
            html.push('<div class="rack-preset-empty">' + esc(opt.textContent) + '</div>');
            return;
          }
          html.push('<div class="rack-preset-item' + (mine ? ' mine' : '') + (opt.value === select.value ? ' current' : '') +
            '" role="option" data-preset="' + esc(opt.value) + '" aria-selected="' + (opt.value === select.value) + '">' +
            '<span class="rack-preset-name">' + esc(opt.textContent) + '</span>' +
            (mine ? '<button type="button" class="rack-preset-del" data-preset-del="' + esc(opt.value) + '" title="' + t('Delete this preset') + '"' +
              ' aria-label="' + t('Delete the preset {textContent}', { textContent: esc(opt.textContent) }) + '">' + TRASH_ICON + '</button>' : '') +
            '</div>');
        });
      });
      menu.innerHTML = html.join('');
    },

    openPresetMenu: function (open) {
      var menu = document.getElementById('rack-preset-menu');
      var btn = document.getElementById('rack-preset-btn');
      if (!menu) { return; }
      if (open) { this.paintPresetMenu(); }
      menu.classList.toggle('hidden', !open);
      if (btn) { btn.setAttribute('aria-expanded', open ? 'true' : 'false'); }
    },

    /* A user preset goes, after asking.  The sound does not change: a rack holding the preset deleted keeps its
       settings, and the box then says Custom. */
    deleteUserPreset: async function (key) {
      var userPresets = this.getUserPresets();
      if (!userPresets[key]) { return; }
      var name = userPresets[key].name || 'preset';
      var confirmed = typeof window.confirmModal === 'function'
        ? await window.confirmModal({
          title: t('Delete Preset'),
          message: t('Delete custom preset “{name}”?\n\nThis cannot be undone.', { name: name }),
          confirmText: t('Delete'),
          danger: true
        })
        : window.confirm(t('Delete custom preset "{name}"?', { name: name }));
      if (!confirmed) { return; }
      userPresets = this.getUserPresets();   // as they are now: the question may have waited
      delete userPresets[key];
      this.saveUserPresets(userPresets);
      this.rebuildPresetDropdown();
      this.syncPresetSelect();
      this.showToast(t('Deleted preset "{name}"', { name: name }));
    },

    showToast: function (msg) {
      if (typeof window.toast === 'function') {
        window.toast(msg, 'good');
      }
    },

    renderMarkup: function () {
      if (document.getElementById('rack-panel')) { return; }

      var html = [
        '<div id="rack-panel" class="rack-panel" role="region" aria-label="' + t('Mastering Rack') + '">',
        '  <div class="rack-chassis">',
        '    <!-- Top Rack Header -->',
        '    <div class="rack-header">',
        '      <div class="rack-ears left"><span class="screw"></span><span class="screw"></span></div>',
        '      <div class="rack-title-block">',
        '        <span class="rack-drag-grip" title="' + t('Drag to move rack') + '"><svg viewBox="0 0 10 16" width="8" height="13" fill="currentColor" aria-hidden="true"><circle cx="2" cy="2" r="1.4"/><circle cx="8" cy="2" r="1.4"/><circle cx="2" cy="8" r="1.4"/><circle cx="8" cy="8" r="1.4"/><circle cx="2" cy="14" r="1.4"/><circle cx="8" cy="14" r="1.4"/></svg></span>',
        '        <span class="rack-badge">STUDIO</span>',
        '        <strong class="rack-title">VINTAGE MASTERING RACK</strong>',
        '        <span class="rack-take-label" id="rack-take-name">' + t('No take selected') + '</span>',
        '      </div>',
        '      <div class="rack-header-tools">',
        '        <div class="rack-preset-wrap">',
        '          <span>PRESET:</span>',
        '          <button type="button" id="rack-preset-btn" class="rack-select rack-preset-btn" title="' + t('Load mastering preset') + '" aria-haspopup="listbox" aria-expanded="false"><span id="rack-preset-label">' + t('Flat / Transparent') + '</span><span class="rack-preset-caret" aria-hidden="true">▾</span></button>',
        '          <div id="rack-preset-menu" class="rack-preset-menu hidden" role="listbox"></div>',
        '          <select id="rack-preset-select" class="rack-select hidden" tabindex="-1" aria-hidden="true">',
        '            <option value="custom" hidden disabled>' + t('Custom') + '</option>',
        '            <optgroup label="' + t('Factory Presets') + '">',
        '              <option value="default">' + t('Flat / Transparent') + '</option>',
        '              <option value="vintage_warmth">' + t('Vintage Tube Warmth') + '</option>',
        '              <option value="vocal_air">' + t('Vocal Air &amp; Glue') + '</option>',
        '              <option value="radio_master">' + t('Radio Ready Master') + '</option>',
        '              <option value="punchy_bass">' + t('Punchy Club &amp; Bass') + '</option>',
        '              <option value="acoustic_clarity">' + t('Acoustic Clarity') + '</option>',
        '              <option value="surround">' + t('Surround') + '</option>',
        '            </optgroup>',
        '            <optgroup id="rack-user-presets-group" label="' + t('User Presets') + '">',
        '            </optgroup>',
        '          </select>',
        '        </div>',
        '        <button type="button" class="rack-head-btn" id="rack-save-preset-btn" title="' + t('Save current settings as a user preset') + '">' + t('+ Save Preset') + '</button>',
        '        <button type="button" class="rack-head-btn" id="rack-reset-btn" title="' + t('Reset all rack settings to flat') + '">' + t('Reset') + '</button>',
        '        <button type="button" class="rack-head-btn bypass-btn" id="rack-master-bypass" title="' + t('Toggle Master Bypass (A/B audition)') + '">',
        '          <span class="led-dot" id="rack-master-led"></span> BYPASS',
        '        </button>',
        '        <button type="button" class="rack-head-btn dock-btn" id="rack-dock-btn" title="' + t('Float window (or drag header to move)') + '">' + t('Float') + '</button>',
        '        <button type="button" class="rack-head-btn" id="rack-fit-btn" title="' + t('Show the rack at full size, and scroll it') + '">' + t('Full size') + '</button>',
        '        <button type="button" class="rack-head-btn close-btn" id="rack-close-btn" title="' + t('Close Rack (Esc)') + '">&times;</button>',
        '      </div>',
        '      <div class="rack-ears right"><span class="screw"></span><span class="screw"></span></div>',
        '    </div>',

        '    <!-- Rack Modules Container -->',
        '    <div class="rack-bay">',

        '      <!-- MODULE 1: 1073 EQUALIZER (No company name/logo) -->',
        '      <div class="rack-unit unit-eq unit-1073" id="unit-eq">',
        '        <div class="unit-bar">',
        '          <div class="unit-brand"><span class="screw-mini"></span> 1073 EQUALIZER <span class="screw-mini"></span></div>',
        '          <div class="unit-bar-right">',
        '            <button type="button" class="unit-toggle on" id="toggle-eq" title="' + t('Toggle EQ in/out') + '"><span class="led"></span> IN</button>',
        '          </div>',
        '        </div>',
        '        <div class="unit-faceplate dpx-faceplate">',

        '          <!-- 1. Gain Knob -->',
        '          <div class="dpx-sec dpx-gain-sec">',
        '            <div class="knob-wrap marconi-wrap" data-param="eq.preGain" data-min="-15" data-max="20" data-step="1" data-default="0" data-unit="dB" title="' + t('Gain / Drive: Preamp saturation stage (-15 dB to +20 dB)') + '">',
        '              <div class="marconi-dial red"><div class="marconi-wing"></div><div class="marconi-stripe"></div><div class="marconi-cap"></div></div>',
        '              <span class="knob-name">GAIN</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '          </div>',

        '          <!-- 2. High Shelf (12 kHz fixed) -->',
        '          <div class="dpx-sec dpx-hf-sec">',
        '            <div class="filter-symbol high-shelf" title="' + t('High Shelf: Fixed 12 kHz boost/cut') + '">&#x2500;&#x256D;</div>',
        '            <div class="knob-wrap" data-param="eq.highGain" data-min="-16" data-max="16" data-step="0.5" data-default="0" data-unit="dB" title="' + t('High Shelf Gain: 12 kHz (&plusmn;16 dB)') + '">',
        '              <div class="knob-dial knob-neve-grey"><div class="knob-cap"></div><div class="knob-line"></div></div>',
        '              <span class="knob-name">' + t('HIGH 12k') + '</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '          </div>',

        '          <!-- 3. Mid Band (Stepped Frequency + Gain) -->',
        '          <div class="dpx-sec dpx-mid-sec">',
        '            <div class="filter-symbol mid-bell" title="' + t('Mid Band: Parametric bell filter') + '">&#x2500;&#x256D;&#x256E;&#x2500;</div>',
        '            <div class="dpx-concentric-group">',
        '              <div class="knob-wrap concentric-outer" data-param="eq.midFreq" data-default="3" data-values="OFF,360,700,1600,3200,4800,7200" data-labels="OFF,0.36k,0.7k,1.6k,3.2k,4.8k,7.2k" title="' + t('Mid Frequency: Stepped bell center (OFF, 0.36k to 7.2k Hz)') + '">',
        '                <div class="skirt-dial"><div class="skirt-ring"><div class="skirt-pointer"></div></div></div>',
        '                <span class="knob-name">FREQ</span>',
        '                <span class="knob-val">1.6 kHz</span>',
        '              </div>',
        '              <div class="knob-wrap concentric-inner" data-param="eq.midGain" data-min="-18" data-max="18" data-step="0.5" data-default="0" data-unit="dB" title="' + t('Mid Gain: Peaking boost/cut (&plusmn;18 dB)') + '">',
        '                <div class="knob-dial knob-neve-grey small"><div class="knob-cap"></div><div class="knob-line"></div></div>',
        '                <span class="knob-name">GAIN</span>',
        '                <span class="knob-val">0 dB</span>',
        '              </div>',
        '            </div>',
        '          </div>',

        '          <!-- 4. Low Shelf (Stepped Frequency + Gain) -->',
        '          <div class="dpx-sec dpx-lf-sec">',
        '            <div class="filter-symbol low-shelf" title="' + t('Low Shelf: Low frequency shelf filter') + '">&#x256D;&#x2500;</div>',
        '            <div class="dpx-concentric-group">',
        '              <div class="knob-wrap concentric-outer" data-param="eq.lowFreq" data-default="2" data-values="OFF,35,60,110,220" data-labels="OFF,35 Hz,60 Hz,110 Hz,220 Hz" title="' + t('Low Shelf Frequency: Stepped cutoff (OFF, 35 to 220 Hz)') + '">',
        '                <div class="skirt-dial"><div class="skirt-ring"><div class="skirt-pointer"></div></div></div>',
        '                <span class="knob-name">FREQ</span>',
        '                <span class="knob-val">60 Hz</span>',
        '              </div>',
        '              <div class="knob-wrap concentric-inner" data-param="eq.lowGain" data-min="-16" data-max="16" data-step="0.5" data-default="0" data-unit="dB" title="' + t('Low Shelf Gain: Low boost/cut (&plusmn;16 dB)') + '">',
        '                <div class="knob-dial knob-neve-grey small"><div class="knob-cap"></div><div class="knob-line"></div></div>',
        '                <span class="knob-name">GAIN</span>',
        '                <span class="knob-val">0 dB</span>',
        '              </div>',
        '            </div>',
        '          </div>',

        '          <!-- 5. High Pass Filter (Blue Fluted Marconi Knob) -->',
        '          <div class="dpx-sec dpx-hpf-sec">',
        '            <div class="filter-symbol hpf-symbol" title="' + t('High Pass: Low cut filter') + '">&#x250C;&#x2500;</div>',
        '            <div class="knob-wrap marconi-wrap" data-param="eq.hp" data-default="0" data-values="20,50,80,160,300" data-labels="OFF,50 Hz,80 Hz,160 Hz,300 Hz" title="' + t('High Pass Filter: Stepped low cut (OFF, 50, 80, 160, 300 Hz)') + '">',
        '              <div class="marconi-dial blue"><div class="marconi-wing"></div><div class="marconi-stripe"></div><div class="marconi-cap"></div></div>',
        '              <span class="knob-name">HPF</span>',
        '              <span class="knob-val">OFF</span>',
        '            </div>',
        '          </div>',

        '          <!-- 6. Chiclet Switches (Phase, EQ) -->',
        '          <div class="dpx-sec dpx-switch-sec">',
        '            <div class="dpx-chiclets vertical">',
        '              <button type="button" class="dpx-btn" id="dpx-btn-phase" title="' + t('Phase Invert (&Oslash;): Flips audio polarity 180&deg;') + '"><span>&Oslash;</span></button>',
        '              <button type="button" class="dpx-btn active" id="dpx-btn-eq" title="' + t('EQ In/Out (EQL): Toggles 1073 equalizer circuit on/off') + '"><span class="btn-led amber"></span><span>EQL</span></button>',
        '            </div>',
        '          </div>',

        '          <!-- 7. Output Level & 7-Segment LED Meter -->',
        '          <div class="dpx-sec dpx-output-sec">',
        '            <div class="dpx-status-leds">',
        '              <div class="status-led-item" title="' + t('Input signal detected') + '"><span class="mini-led red" id="dpx-led-ip"></span><span class="lbl">I/P</span></div>',
        '              <div class="status-led-item" title="' + t('EQ circuit active') + '"><span class="mini-led amber on" id="dpx-led-eq"></span><span class="lbl">EQ</span></div>',
        '              <div class="status-led-item" title="' + t('Output signal present') + '"><span class="mini-led green on" id="dpx-led-op"></span><span class="lbl">O/P</span></div>',
        '            </div>',
        '            <div class="knob-wrap" data-param="eq.outLevel" data-min="-12" data-max="12" data-step="0.5" data-default="0" data-unit="dB" title="' + t('Output Trim: Channel level adjustment (&plusmn;12 dB)') + '">',
        '              <div class="knob-dial knob-neve-grey small"><div class="knob-cap"></div><div class="knob-line"></div></div>',
        '              <span class="knob-name">LEVEL</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '            <div class="dpx-ladder-wrap" title="' + t('Output Peak Meter (dB)') + '">',
        '              <div class="dpx-ladder" id="dpx-led-ladder">',
        '                <div class="ladder-col"><span class="ladder-led green" data-db="-30"></span><span class="ladder-lbl">-30</span></div>',
        '                <div class="ladder-col"><span class="ladder-led green" data-db="-10"></span><span class="ladder-lbl">-10</span></div>',
        '                <div class="ladder-col"><span class="ladder-led yellow" data-db="0"></span><span class="ladder-lbl">0</span></div>',
        '                <div class="ladder-col"><span class="ladder-led yellow" data-db="5"></span><span class="ladder-lbl">+5</span></div>',
        '                <div class="ladder-col"><span class="ladder-led red" data-db="14"></span><span class="ladder-lbl">+14</span></div>',
        '                <div class="ladder-col"><span class="ladder-led red" data-db="18"></span><span class="ladder-lbl">+18</span></div>',
        '                <div class="ladder-col"><span class="ladder-led red" data-db="24"></span><span class="ladder-lbl">+24</span></div>',
        '              </div>',
        '            </div>',
        '          </div>',

        '          <!-- 8. Right Badge -->',
        '          <div class="dpx-sec dpx-badge-sec">',
        '            <div class="dpx-badge-plate">',
        '              <div class="dpx-badge-model">1073</div>',
        '              <div class="dpx-badge-desc">EQUALIZER</div>',
        '            </div>',
        '          </div>',

        '        </div>',
        '      </div>',

        '      <!-- PARAMETRIC EQUALIZER: a graph of five bands, each a node to drag -->',
        '      <div class="rack-unit unit-peq" id="unit-peq">',
        '        <div class="unit-bar">',
        '          <div class="unit-brand"><span class="screw-mini"></span> PARAMETRIC EQUALIZER <span class="screw-mini"></span></div>',
        '          <button type="button" class="unit-toggle" id="toggle-peq" title="' + t('Toggle the parametric equalizer in/out') + '"><span class="led"></span> OUT</button>',
        '        </div>',
        '        <div class="peq-screen">',
        '          <div class="peq-graph">',
        '            <canvas id="peq-canvas" class="peq-canvas" title="' + t('Drag a band to set its frequency and gain. The wheel sets its width. Double-click to reset it.') + '"></canvas>',
        '            <button type="button" class="peq-range" id="peq-range" title="' + t('How many decibels the graph shows') + '">&plusmn;12 dB</button>',
        '          </div>',
        '          <div class="peq-strip" id="peq-strip">',
        '            <div class="peq-dots" id="peq-dots" role="group" aria-label="' + t('Band') + '"></div>',
        '            <button type="button" class="peq-power" id="peq-band-on" title="' + t('Switch this band on or off') + '" aria-label="' + t('Band on or off') + '">',
        '              <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M12 3v8"/><path d="M6.3 6.8a8 8 0 1 0 11.4 0"/></svg>',
        '            </button>',
        '            <div class="peq-types" id="peq-types" role="group" aria-label="' + t('Kind of filter') + '"></div>',
        '            <button type="button" class="peq-flat" id="peq-flat" title="' + t('Flat: every band back to 0 dB, and the cuts and notches off. Each band stays where it is') + '">',
        '              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M3 12h18"/></svg>',
        '              <span>FLAT</span>',
        '            </button>',
        '            <div class="knob-wrap dummy-knob peq-knob" data-peq="freq" title="' + t('Frequency') + '">',
        '              <div class="knob-dial small"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">FREQ</span><span class="knob-val">1 kHz</span>',
        '            </div>',
        '            <div class="knob-wrap dummy-knob peq-knob" data-peq="gain" title="' + t('Gain') + '">',
        '              <div class="knob-dial small"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">GAIN</span><span class="knob-val">0 dB</span>',
        '            </div>',
        '            <div class="knob-wrap dummy-knob peq-knob" data-peq="q" title="' + t('Width (Q): higher is narrower') + '">',
        '              <div class="knob-dial small"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">Q</span><span class="knob-val">1.0</span>',
        '            </div>',
        '          </div>',
        '        </div>',
        '      </div>',

        '      <!-- MODULE 2: PEAK LIMITING AMPLIFIER -->',
        '      <div class="rack-unit unit-comp" id="unit-comp">',
        '        <div class="unit-bar">',
        '          <div class="unit-brand"><span class="screw-mini"></span> 76-LN PEAK LIMITING AMPLIFIER <span class="screw-mini"></span></div>',
        '          <button type="button" class="unit-toggle on" id="toggle-comp" title="' + t('Toggle Compressor on/off') + '"><span class="led"></span> IN</button>',
        '        </div>',
        '        <div class="unit-faceplate">',
        '          <div class="knob-group">',
        '            <div class="knob-wrap" data-param="comp.threshold" data-min="-45" data-max="0" data-step="1" data-default="-18" data-unit="dB">',
        '              <div class="knob-dial large"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">THRESHOLD</span>',
        '              <span class="knob-val">-18 dB</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="comp.makeup" data-min="-6" data-max="30" data-step="0.5" data-default="6" data-unit="dB" title="' + t('Output: all the gain the compressor adds (-6 dB to +30 dB). Double-click for +6 dB, where Reset leaves it') + '">',
        '              <div class="knob-dial large"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">OUTPUT</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '          </div>',

        '          <!-- Backlit Analog VU Meter -->',
        '          <div class="vu-meter-box" title="' + t('Analog Gain Reduction (dB)') + '">',
        '            <div class="vu-glass">',
        '              <canvas id="vu-canvas" width="200" height="110"></canvas>',
        '              <div class="vu-label">GAIN REDUCTION</div>',
        '            </div>',
        '          </div>',

        '          <!-- Push Button Ratios -->',
        '          <div class="ratio-bank">',
        '            <span class="ratio-title">RATIO</span>',
        '            <div class="ratio-buttons" id="comp-ratios">',
        '              <button type="button" class="ratio-btn" data-ratio="2">2:1</button>',
        '              <button type="button" class="ratio-btn on" data-ratio="4">4:1</button>',
        '              <button type="button" class="ratio-btn" data-ratio="8">8:1</button>',
        '              <button type="button" class="ratio-btn" data-ratio="12">12:1</button>',
        '              <button type="button" class="ratio-btn" data-ratio="20">20:1</button>',
        '              <button type="button" class="ratio-btn" data-ratio="all">ALL</button>',
        '            </div>',
        '          </div>',

        '          <div class="knob-group separator">',
        '            <div class="knob-wrap" data-param="comp.attack" data-min="0.001" data-max="0.08" data-step="0.002" data-default="0.015" data-unit="s" data-display="ms">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">ATTACK</span>',
        '              <span class="knob-val">15 ms</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="comp.release" data-min="0.05" data-max="1.2" data-step="0.05" data-default="0.25" data-unit="s" data-display="ms">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">RELEASE</span>',
        '              <span class="knob-val">250 ms</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="comp.mix" data-min="0" data-max="1" data-step="0.05" data-default="1" data-unit="" data-display="pct">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">MIX</span>',
        '              <span class="knob-val">100%</span>',
        '            </div>',
        '          </div>',
        '        </div>',
        '      </div>',

        '      <!-- MODULE 3: VINTAGE STEREO IMAGER & SPATIAL PROCESSOR -->',
        '      <div class="rack-unit unit-imager" id="unit-imager">',
        '        <div class="unit-bar">',
        '          <div class="unit-brand"><span class="screw-mini"></span> VINTAGE STEREO IMAGER & SPATIAL PROCESSOR <span class="screw-mini"></span></div>',
        '          <button type="button" class="unit-toggle on" id="toggle-imager" title="' + t('Toggle Stereo Imager on/off') + '"><span class="led"></span> IN</button>',
        '        </div>',
        '        <div class="unit-faceplate imager-faceplate">',
        '          <div class="knob-group">',
        '            <div class="knob-wrap" data-param="imager.range" data-values="1,2,3,4,5,6,7,8,9" data-labels="1 (HIGH),2,3,4,5,6,7,8,9 (OPEN)" data-default="4" title="' + t('Process Frequency Band (High to Open)') + '">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">RANGE</span>',
        '              <span class="knob-val">5</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="imager.stage" data-values="1,2,3,4,5,6,7,8,9" data-labels="1 (BACK),2,3,4,5,6,7,8,9 (FRONT)" data-default="4" title="' + t('Stereo Stage Placement (Back to Front)') + '">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">STAGE</span>',
        '              <span class="knob-val">5</span>',
        '            </div>',
        '          </div>',
        '          <div class="imager-harmonics-sec">',
        '            <div class="imager-push-wrap">',
        '              <span class="imager-hint-label">' + t('Tubes Warm-Up') + '</span>',
        '              <button type="button" class="imager-btn" id="toggle-imager-harmonics" title="' + t('Toggle Valve Tube Harmonics') + '">',
        '                <span class="imager-btn-led blue"></span>',
        '                <span class="imager-btn-txt">HARMONICS</span>',
        '              </button>',
        '            </div>',
        '            <div class="knob-wrap" data-param="imager.tubeHarmonics" data-values="1,2,3,4,5,6,7,8,9" data-labels="1 (MIN),2,3,4,5,6,7,8,9 (MAX)" data-default="0" title="' + t('Tube Harmonic Saturation Drive') + '">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">TUBE HARMONICS</span>',
        '              <span class="knob-val">1 (MIN)</span>',
        '            </div>',
        '          </div>',
        '          <div class="imager-center-box">',
        '            <span class="imager-window-title">STEREO IMAGE</span>',
        '            <div class="imager-tube-window" title="' + t('Stereo Valve Spatial Circuit') + '">',
        '              <div class="tube-mesh-grille"></div>',
        '              <div class="tube-glow-core" id="imager-tube-glow"></div>',
        '              <div class="tube-filament"></div>',
        '            </div>',
        '            <span class="imager-window-sub">BIGGER MAKER</span>',
        '          </div>',
        '          <div class="knob-group">',
        '            <div class="knob-wrap" data-param="imager.bigness" data-values="1,2,3,4,5,6,7,8,9" data-labels="1 (MIN),2,3,4,5,6,7,8,9 (MAX)" data-default="0" title="' + t('Stereo Width Intensity') + '">',
        '              <div class="knob-dial large"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">BIGNESS</span>',
        '              <span class="knob-val">1 (MIN)</span>',
        '            </div>',
        '          </div>',
        '          <div class="imager-push-wrap">',
        '            <button type="button" class="imager-btn" id="toggle-imager-bass" title="' + t('Active Bass Punch & Mono Sub Anchor') + '">',
        '              <span class="imager-btn-led blue"></span>',
        '              <span class="imager-btn-txt">BASS</span>',
        '            </button>',
        '          </div>',
        '          <div class="imager-right-sec">',
        '            <div class="imager-badge-block">',
        '              <div class="imager-badge-main">BiG</div>',
        '              <div class="imager-badge-sub">[ STUDIO ]</div>',
        '            </div>',
        '            <div class="imager-pwr-block">',
        '              <div class="pwr-indicator-wrap">',
        '                <span class="imager-pwr-led red on" id="imager-pwr-led"></span>',
        '                <span class="imager-pwr-lbl">PWR</span>',
        '              </div>',
        '              <button type="button" class="imager-on-btn on" id="toggle-imager-pwr" title="' + t('Toggle Imager Module Power') + '">',
        '                <span class="pwr-lamp amber"></span>',
        '                <span class="pwr-txt">ON</span>',
        '              </button>',
        '              <span class="imager-model-spec">' + t('Model 2420') + '</span>',
        '            </div>',
        '          </div>',
        '        </div>',
        '      </div>',

        '      <!-- MODULE 3b: SPACE (HEADPHONES 3D) -->',
        '      <div class="rack-unit unit-space" id="unit-space">',
        '        <div class="unit-bar">',
        '          <div class="unit-brand"><span class="screw-mini"></span> 3D SPACE <span class="screw-mini"></span></div>',
        '          <button type="button" class="unit-toggle" id="toggle-space" title="' + t('Toggle 3D Space on/off. For headphones: it is never part of the take\'s own file') + '"><span class="led"></span> OUT</button>',
        '        </div>',
        '        <div class="unit-faceplate space-faceplate">',
        '          <div class="space-scenes" id="space-scenes" role="group" aria-label="' + t('Space scenes') + '">',
        '            <button type="button" class="space-scene" data-scene="front" title="' + t('A pair of speakers in front of you') + '">FRONT</button>',
        '            <button type="button" class="space-scene" data-scene="wide" title="' + t('A wider stage, a little around you') + '">WIDE</button>',
        '            <button type="button" class="space-scene" data-scene="around" title="' + t('Inside the band') + '">AROUND</button>',
        '          </div>',
        '          <div class="space-stage-box">',
        '            <div class="space-source" id="space-source" role="group" aria-label="' + t('What Space places') + '">',
        '              <button type="button" class="space-scene" data-source="mix" title="' + t('The finished mix, from virtual speakers') + '">MIX</button>',
        '              <button type="button" class="space-scene" data-source="stems" title="' + t('The take\'s stems, each placed on its own') + '">STEMS</button>',
        '            </div>',
        '            <svg id="space-stage" class="space-stage" viewBox="0 0 140 140" role="img" aria-label="' + t('Where the sound comes from, seen from above') + '"></svg>',
        '            <span class="space-stage-note" id="space-stage-note"></span>',
        '            <button type="button" class="rack-head-btn hidden" id="space-make-stems">' + t('Make stems') + '</button>',
        '          </div>',
        '          <div class="knob-group">',
        '            <div class="knob-wrap" data-param="space.width" data-min="5" data-max="90" data-step="5" data-default="30" data-unit="°" title="' + t('How far either side the two front speakers stand') + '">',
        '              <div class="knob-dial large"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">WIDTH</span>',
        '              <span class="knob-val">30 °</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="space.surround" data-min="0" data-max="1" data-step="0.05" data-default="0" data-display="pct" title="' + t('How much of the mix\'s ambience comes from behind you') + '">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">SURROUND</span>',
        '              <span class="knob-val">0%</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="space.height" data-min="0" data-max="45" data-step="5" data-default="0" data-unit="°" title="' + t('How far above your ears the speakers are') + '">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">HEIGHT</span>',
        '              <span class="knob-val">0 °</span>',
        '            </div>',
        '          </div>',
        '          <div class="knob-group separator">',
        '            <div class="knob-wrap" data-param="space.room" data-min="0" data-max="1" data-step="0.05" data-default="0" data-display="pct" title="' + t('A short room around it all') + '">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">ROOM</span>',
        '              <span class="knob-val">0%</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="space.output" data-min="-6" data-max="6" data-step="0.5" data-default="0" data-unit="dB">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">OUTPUT</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '          </div>',
        '          <div class="space-export">',
        '            <span class="space-note" title="' + t('What you hear in the rack, and this download, are for headphones') + '">' + t('Headphones') + '</span>',
        '            <button type="button" class="rack-head-btn" id="space-download" title="' + t('Download this take with 3D Space, for headphones, as a WAV') + '">' + t('Download') + '</button>',
        '            <span class="space-note">' + t('5.1 speakers') + '</span>',
        '            <div class="space-surround">',
        '              <button type="button" class="rack-head-btn" data-surround="flac" title="' + t('Six-channel FLAC, for computers and media players') + '">FLAC</button>',
        '              <button type="button" class="rack-head-btn" data-surround="ac3" title="' + t('AC-3 (Dolby Digital), for TVs, soundbars and receivers') + '">AC-3</button>',
        '              <button type="button" class="rack-head-btn" data-surround="flac" data-surround-test="1" title="' + t('A channel test: a sound from each speaker in turn, to check a 5.1 player or a virtualiser') + '">' + t('Test') + '</button>',
        '            </div>',
        '          </div>',
        '        </div>',
        '      </div>',

        '      <!-- MODULE 4: MASTER LIMITER -->',
        '      <div class="rack-unit unit-limit" id="unit-limit">',
        '        <div class="unit-bar">',
        '          <div class="unit-brand"><span class="screw-mini"></span> 670 VARIABLE-MU MASTER LIMITER <span class="screw-mini"></span></div>',
        '          <button type="button" class="unit-toggle on" id="toggle-limit" title="' + t('Toggle Limiter on/off') + '"><span class="led"></span> IN</button>',
        '        </div>',
        '        <div class="unit-faceplate">',
        '          <div class="knob-group">',
        '            <div class="knob-wrap" data-param="limit.drive" data-min="0" data-max="8" data-step="0.2" data-default="0" data-unit="dB">',
        '              <div class="knob-dial large"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">DRIVE / THR</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="limit.ceiling" data-min="-2.0" data-max="0" data-step="0.1" data-default="-0.1" data-unit="dB">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">CEILING</span>',
        '              <span class="knob-val">-0.1 dB</span>',
        '            </div>',
        '          </div>',

        '          <div class="knob-group separator">',
        '            <div class="knob-wrap" data-param="limit.release" data-min="0.02" data-max="0.5" data-step="0.02" data-default="0.08" data-unit="s" data-display="ms">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">RECOVERY</span>',
        '              <span class="knob-val">80 ms</span>',
        '            </div>',
        '          </div>',

        '          <div class="warmth-box">',
        '            <span class="warmth-title">TUBE WARMTH</span>',
        '            <button type="button" class="switch-toggle" id="toggle-warmth" title="' + t('Toggle Analog Tube Saturation') + '">',
        '              <span class="switch-arm"></span>',
        '            </button>',
        '            <span class="warmth-status" id="warmth-status">OFF</span>',
        '          </div>',
        '        </div>',
        '      </div>',

        '    </div>',
        '  </div>',
        '</div>'
      ].join('\n');

      var container = document.createElement('div');
      container.innerHTML = html;
      var panel = container.firstElementChild;

      var player = document.querySelector('.player');
      if (player && player.parentNode) {
        player.parentNode.insertBefore(panel, player);
      } else {
        document.body.appendChild(panel);
      }
    },

    bindEvents: function () {
      var self = this;

      // Close button
      var closeBtn = document.getElementById('rack-close-btn');
      if (closeBtn) {
        closeBtn.addEventListener('click', function () { self.toggle(false); });
      }

      // Master Bypass
      var bypassBtn = document.getElementById('rack-master-bypass');
      if (bypassBtn) {
        bypassBtn.addEventListener('click', function () {
          self.settings.masterBypass = !self.settings.masterBypass;
          self.updateBypassUI();
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      // Preset Select
      var presetSelect = document.getElementById('rack-preset-select');
      var presetBtn = document.getElementById('rack-preset-btn');
      var presetMenu = document.getElementById('rack-preset-menu');
      if (presetBtn && presetMenu) {
        presetBtn.addEventListener('click', function () { self.openPresetMenu(!self.presetMenuOpen()); });
        presetMenu.addEventListener('click', function (e) {
          var bin = e.target.closest('[data-preset-del]');
          if (bin) {
            e.stopPropagation();
            self.openPresetMenu(false);
            self.deleteUserPreset(bin.getAttribute('data-preset-del'));
            return;
          }
          var item = e.target.closest('[data-preset]');
          if (!item || !presetSelect) { return; }
          self.openPresetMenu(false);
          presetSelect.value = item.getAttribute('data-preset');
          presetSelect.dispatchEvent(new Event('change'));
        });
        document.addEventListener('mousedown', function (e) {
          if (self.presetMenuOpen() && !e.target.closest('#rack-preset-menu, #rack-preset-btn')) { self.openPresetMenu(false); }
        });
      }
      if (presetSelect) {
        presetSelect.addEventListener('change', function () {
          var key = this.value;
          var userPresets = self.getUserPresets();
          if (PRESETS[key]) {
            self.settings = JSON.parse(JSON.stringify(PRESETS[key]));
          } else if (userPresets[key]) {
            self.settings = self.mergeSettings(PRESETS['default'], upgradeSettings(userPresets[key]));
          }
          self.paintPresetButton();
          self.syncKnobsToState();
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      // Save Custom Preset (using app's native confirmModal)
      var savePresetBtn = document.getElementById('rack-save-preset-btn');
      if (savePresetBtn) {
        savePresetBtn.addEventListener('click', async function () {
          var userPresets = self.getUserPresets();
          var count = Object.keys(userPresets).length + 1;
          var defaultName = t('My Preset {count}', { count: count });
          var name = null;
          if (typeof window.confirmModal === 'function') {
            name = await window.confirmModal({
              title: t('Save Preset'),
              message: t('Enter a name for this custom preset:'),
              input: true,
              defaultValue: defaultName,
              placeholder: t('Preset name'),
              confirmText: t('Save'),
              cancelText: t('Cancel')
            });
          } else {
            name = window.prompt(t('Enter name for your custom preset:'), defaultName);
          }
          if (!name || !name.trim()) { return; }
          name = name.trim().slice(0, 40);
          // A name already used is that preset saved again: it is written over, after asking, and not
          // added beside itself.  Presets left with the same name by earlier saves go with it.
          var same = self.userPresetsNamed(userPresets, name);
          if (same.length) {
            var kept = userPresets[same[0]].name || name;
            var replace = typeof window.confirmModal === 'function'
              ? await window.confirmModal({
                title: t('Save Preset'),
                message: t('There is already a preset called “{kept}”. Replace it?', { kept: kept }),
                confirmText: t('Replace')
              })
              : window.confirm(t('There is already a preset called "{kept}". Replace it?', { kept: kept }));
            if (!replace) { return; }
            userPresets = self.getUserPresets();   // as they are now: the question may have waited
            same = self.userPresetsNamed(userPresets, name);
          }
          var id = same.length ? same[0] : 'user_' + Date.now();
          same.slice(1).forEach(function (other) { delete userPresets[other]; });
          var snapshot = JSON.parse(JSON.stringify(self.settings));
          snapshot.name = name;
          userPresets[id] = snapshot;
          self.saveUserPresets(userPresets);
          self.rebuildPresetDropdown(id);
          self.showToast(t('{value} preset "{name}"', { value: same.length ? t('Replaced') : t('Saved'), name: name }));
        });
      }

      // Reset
      var resetBtn = document.getElementById('rack-reset-btn');
      if (resetBtn) {
        resetBtn.addEventListener('click', function () {
          self.settings = JSON.parse(JSON.stringify(PRESETS['default']));
          if (presetSelect) { presetSelect.value = 'default'; }
          self.paintPresetButton();
          self.syncKnobsToState();
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      // Module In/Out toggles
      var toggleEq = document.getElementById('toggle-eq');
      var dpxBtnEq = document.getElementById('dpx-btn-eq');
      function onToggleEq() {
        self.settings.eq.enabled = !self.settings.eq.enabled;
        var on = self.settings.eq.enabled;
        if (toggleEq) {
          toggleEq.classList.toggle('on', on);
          toggleEq.innerHTML = '<span class="led"></span> ' + (on ? 'IN' : 'OUT');
        }
        if (dpxBtnEq) {
          dpxBtnEq.classList.toggle('active', on);
        }
        var led = document.getElementById('dpx-led-eq');
        if (led) { led.classList.toggle('on', on); }
        Engine.applySettings(self.settings);
        self.debouncedSave();
      }
      if (toggleEq) { toggleEq.addEventListener('click', onToggleEq); }
      if (dpxBtnEq) { dpxBtnEq.addEventListener('click', onToggleEq); }

      // 1073 Chiclet Buttons
      var dpxBtnPhase = document.getElementById('dpx-btn-phase');
      if (dpxBtnPhase) {
        dpxBtnPhase.addEventListener('click', function () {
          self.settings.eq.phase = !self.settings.eq.phase;
          this.classList.toggle('active', self.settings.eq.phase);
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      var toggleComp = document.getElementById('toggle-comp');
      if (toggleComp) {
        toggleComp.addEventListener('click', function () {
          self.settings.comp.enabled = !self.settings.comp.enabled;
          this.classList.toggle('on', self.settings.comp.enabled);
          this.innerHTML = '<span class="led"></span> ' + (self.settings.comp.enabled ? 'IN' : 'OUT');
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      // Stereo Imager toggles
      var toggleImager = document.getElementById('toggle-imager');
      var toggleImagerPwr = document.getElementById('toggle-imager-pwr');
      function onToggleImager() {
        if (!self.settings.imager) { self.settings.imager = {}; }
        self.settings.imager.enabled = !self.settings.imager.enabled;
        var on = self.settings.imager.enabled;
        if (toggleImager) {
          toggleImager.classList.toggle('on', on);
          toggleImager.innerHTML = '<span class="led"></span> ' + (on ? 'IN' : 'OUT');
        }
        if (toggleImagerPwr) {
          toggleImagerPwr.classList.toggle('on', on);
        }
        Engine.applySettings(self.settings);
        self.debouncedSave();
      }
      if (toggleImager) { toggleImager.addEventListener('click', onToggleImager); }
      if (toggleImagerPwr) { toggleImagerPwr.addEventListener('click', onToggleImager); }

      // Imager Harmonics toggle
      var toggleImagerHarmonics = document.getElementById('toggle-imager-harmonics');
      if (toggleImagerHarmonics) {
        toggleImagerHarmonics.addEventListener('click', function () {
          if (!self.settings.imager) { self.settings.imager = {}; }
          self.settings.imager.harmonics = !self.settings.imager.harmonics;
          this.classList.toggle('active', self.settings.imager.harmonics);
          if (self.settings.imager.harmonics) { self.engage('imager'); }
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      // Imager Bass punch toggle
      var toggleImagerBass = document.getElementById('toggle-imager-bass');
      if (toggleImagerBass) {
        toggleImagerBass.addEventListener('click', function () {
          if (!self.settings.imager) { self.settings.imager = {}; }
          self.settings.imager.bass = !self.settings.imager.bass;
          this.classList.toggle('active', self.settings.imager.bass);
          if (self.settings.imager.bass) { self.engage('imager'); }
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      var toggleLimit = document.getElementById('toggle-limit');
      if (toggleLimit) {
        toggleLimit.addEventListener('click', function () {
          self.settings.limit.enabled = !self.settings.limit.enabled;
          this.classList.toggle('on', self.settings.limit.enabled);
          this.innerHTML = '<span class="led"></span> ' + (self.settings.limit.enabled ? 'IN' : 'OUT');
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      // Space: in or out, a scene, and its own download
      var toggleSpace = document.getElementById('toggle-space');
      if (toggleSpace) {
        toggleSpace.addEventListener('click', function () {
          self.settings.space = Object.assign(defaultSpace(), self.settings.space || {});
          self.settings.space.enabled = !self.settings.space.enabled;
          self.syncKnobsToState();
          Engine.applySettings(self.settings);
          self.syncStems();
          self.debouncedSave();
        });
      }
      var spaceScenes = document.getElementById('space-scenes');
      if (spaceScenes) {
        spaceScenes.addEventListener('click', function (e) {
          var button = e.target.closest('[data-scene]');
          if (!button || !SPACE_SCENES[button.dataset.scene]) { return; }
          self.settings.space = Object.assign(defaultSpace(), self.settings.space || {}, SPACE_SCENES[button.dataset.scene], { enabled: true });
          self.settings.space.stems = JSON.parse(JSON.stringify(SPACE_STEM_SCENES[button.dataset.scene]));
          self.syncKnobsToState();
          Engine.applySettings(self.settings);
          self.syncStems();
          self.debouncedSave();
        });
      }
      var spaceDownload = document.getElementById('space-download');
      if (spaceDownload) {
        spaceDownload.addEventListener('click', function () { self.downloadForHeadphones(); });
      }
      var spaceSource = document.getElementById('space-source');
      if (spaceSource) {
        spaceSource.addEventListener('click', function (e) {
          var button = e.target.closest('[data-source]');
          if (!button) { return; }
          self.settings.space = Object.assign(defaultSpace(), self.settings.space || {}, { source: button.dataset.source, enabled: true });
          self.syncKnobsToState();
          self.syncStems();
          self.debouncedSave();
        });
      }
      var makeStems = document.getElementById('space-make-stems');
      if (makeStems) {
        makeStems.addEventListener('click', async function () {
          var takeId = self.currentTakeId;
          if (!takeId) { return; }
          makeStems.disabled = true;
          try {
            var res = await fetch('/api/takes/' + takeId + '/stems', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
            if (!res.ok) { throw new Error(await res.text()); }
            self.showToast(t('Making the stems: Space will use them when they are ready'), 'good');
            self.waitForStems(takeId);
          } catch (err) {
            self.showToast(err.message, 'bad');
          } finally {
            makeStems.disabled = false;
          }
        });
      }
      Array.prototype.forEach.call(document.querySelectorAll('[data-surround]'), function (button) {
        button.addEventListener('click', function () { self.downloadSurround(button.dataset.surround, Boolean(button.dataset.surroundTest)); });
      });
      this.bindSpaceStage();
      this.hookStemPlayback();

      // Tube Warmth switch
      var toggleWarmth = document.getElementById('toggle-warmth');
      var warmthStatus = document.getElementById('warmth-status');
      if (toggleWarmth) {
        toggleWarmth.addEventListener('click', function () {
          self.settings.limit.warmth = !self.settings.limit.warmth;
          this.classList.toggle('on', self.settings.limit.warmth);
          if (self.settings.limit.warmth) { self.engage('limit'); }
          if (warmthStatus) {
            warmthStatus.textContent = self.settings.limit.warmth ? t('TUBE ON') : 'OFF';
            warmthStatus.classList.toggle('active', self.settings.limit.warmth);
          }
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      // Ratio buttons
      var ratioBank = document.getElementById('comp-ratios');
      if (ratioBank) {
        ratioBank.addEventListener('click', function (e) {
          var btn = e.target.closest('.ratio-btn');
          if (!btn) { return; }
          Array.prototype.forEach.call(ratioBank.querySelectorAll('.ratio-btn'), function (b) { b.classList.remove('on'); });
          btn.classList.add('on');
          var r = btn.dataset.ratio;
          if (r === 'all') {
            self.settings.comp.ratio = 20;
            self.settings.comp.knee = 0;
          } else {
            self.settings.comp.ratio = Number(r) || 4;
            self.settings.comp.knee = 10;
          }
          self.engage('comp');
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      // Setup Rotary Knobs
      this.bindKnobs();

      // Keyboard Esc to close
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && self.isOpen && self.presetMenuOpen()) {
          e.rackClosed = true;   // the menu was what Escape closed: the page leaves its windows open
          self.openPresetMenu(false);
          return;
        }
        if (e.key === 'Escape' && self.isOpen) {
          // Standing over the editor window, the rack is what Escape closes: the page reads this mark
          // and leaves the window open.
          if (document.body && document.body.classList.contains('rack-over-editor')) { e.rackClosed = true; }
          self.toggle(false);
        }
      });
    },

    bindKnobs: function () {
      var self = this;
      var knobWraps = document.querySelectorAll('.knob-wrap');

      Array.prototype.forEach.call(knobWraps, function (wrap) {
        if (wrap.classList.contains('dummy-knob')) { return; }

        var dial = wrap.querySelector('.knob-dial, .marconi-dial, .skirt-dial');
        if (!dial) { return; }

        var valLabel = wrap.querySelector('.knob-val');
        var param = wrap.dataset.param;
        if (!param) { return; }

        var valuesList = wrap.dataset.values ? wrap.dataset.values.split(',') : null;
        var labelsList = wrap.dataset.labels ? wrap.dataset.labels.split(',') : null;

        var min = valuesList ? 0 : Number(wrap.dataset.min);
        var max = valuesList ? (valuesList.length - 1) : Number(wrap.dataset.max);
        var step = valuesList ? 1 : (Number(wrap.dataset.step) || 1);
        var def = Number(wrap.dataset.default);
        var unit = wrap.dataset.unit || '';
        var display = wrap.dataset.display || '';

        var isDragging = false;
        var startY = 0;
        var startVal = def;

        function updateKnobDisplay(val) {
          if (valuesList) {
            var idx = Math.round(val);
            idx = Math.max(0, Math.min(valuesList.length - 1, idx));
            var normStep = idx / (valuesList.length - 1);
            var degStep = -135 + normStep * 270;
            dial.style.transform = 'rotate(' + degStep + 'deg)';
            if (valLabel) {
              valLabel.textContent = labelsList ? labelsList[idx] : valuesList[idx];
            }
            return;
          }

          var norm = (val - min) / (max - min);
          norm = Math.max(0, Math.min(1, norm));
          var deg = -135 + norm * 270;
          dial.style.transform = 'rotate(' + deg + 'deg)';

          if (valLabel) {
            if (display === 'ms') {
              valLabel.textContent = Math.round(val * 1000) + ' ms';
            } else if (display === 'pct') {
              valLabel.textContent = Math.round(val * 100) + '%';
            } else if (unit === 'dB') {
              valLabel.textContent = (val > 0 ? '+' : '') + (Math.round(val * 10) / 10) + ' dB';
            } else if (unit === 'Hz') {
              valLabel.textContent = val >= 1000 ? (Math.round(val / 100) / 10) + ' kHz' : Math.round(val) + ' Hz';
            } else {
              valLabel.textContent = (Math.round(val * 10) / 10) + (unit ? ' ' + unit : '');
            }
          }
        }

        wrap._updateDisplay = updateKnobDisplay;

        function setParamValue(val, quietly) {
          val = Math.max(min, Math.min(max, val));
          val = Math.round(val / step) * step;

          var parts = param.split('.');
          if (parts.length === 2 && self.settings[parts[0]]) {
            if (!quietly) { self.engage(parts[0]); }
            if (valuesList) {
              var rawVal = valuesList[val];
              self.settings[parts[0]][parts[1]] = isNaN(Number(rawVal)) ? rawVal : Number(rawVal);
            } else {
              self.settings[parts[0]][parts[1]] = val;
            }
          }

          updateKnobDisplay(val);
          Engine.applySettings(self.settings);
          self.debouncedSave();
        }

        function onMouseDown(e) {
          if (e.button !== 0) { return; }
          e.preventDefault();
          Engine.resume();
          isDragging = true;
          startY = e.clientY;

          var parts = param.split('.');
          if (valuesList) {
            var curStored = parts.length === 2 && self.settings[parts[0]] ? self.settings[parts[0]][parts[1]] : null;
            var curIdx = curStored !== null ? valuesList.indexOf(String(curStored)) : -1;
            startVal = curIdx >= 0 ? curIdx : def;
          } else {
            startVal = (parts.length === 2 && self.settings[parts[0]] && self.settings[parts[0]][parts[1]] !== undefined) ? Number(self.settings[parts[0]][parts[1]]) : def;
          }

          document.body.classList.add('knob-dragging');

          function onMouseMove(moveEvent) {
            if (!isDragging) { return; }
            var deltaY = startY - moveEvent.clientY;
            var sensitivity = moveEvent.shiftKey ? 800 : 200;
            var deltaVal = (deltaY / sensitivity) * (max - min);
            setParamValue(startVal + deltaVal);
          }

          function onMouseUp() {
            if (!isDragging) { return; }
            isDragging = false;
            document.body.classList.remove('knob-dragging');
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('mouseup', onMouseUp);
          }

          window.addEventListener('mousemove', onMouseMove);
          window.addEventListener('mouseup', onMouseUp);
        }

        dial.addEventListener('mousedown', onMouseDown);

        // Wheel support
        wrap.addEventListener('wheel', function (e) {
          e.preventDefault();
          Engine.resume();
          var parts = param.split('.');
          var curVal;
          if (valuesList) {
            var curStored = parts.length === 2 && self.settings[parts[0]] ? self.settings[parts[0]][parts[1]] : null;
            var curIdx = curStored !== null ? valuesList.indexOf(String(curStored)) : -1;
            curVal = curIdx >= 0 ? curIdx : def;
          } else {
            curVal = (parts.length === 2 && self.settings[parts[0]]) ? Number(self.settings[parts[0]][parts[1]]) : def;
          }
          var direction = e.deltaY < 0 ? 1 : -1;
          setParamValue(curVal + direction * step * (e.shiftKey ? 0.2 : 1.0));
        }, { passive: false });

        // Double-click to reset to default
        dial.addEventListener('dblclick', function (e) {
          e.preventDefault();
          setParamValue(def, true);
        });
      });
    },

    syncKnobsToState: function () {
      var self = this;
      var knobWraps = document.querySelectorAll('.knob-wrap');
      Array.prototype.forEach.call(knobWraps, function (wrap) {
        if (wrap.classList.contains('dummy-knob')) { return; }
        var param = wrap.dataset.param;
        if (!param) { return; }
        var parts = param.split('.');
        if (parts.length === 2 && self.settings[parts[0]] && self.settings[parts[0]][parts[1]] !== undefined) {
          var valuesList = wrap.dataset.values ? wrap.dataset.values.split(',') : null;
          if (valuesList) {
            var raw = String(self.settings[parts[0]][parts[1]]);
            var idx = valuesList.indexOf(raw);
            if (idx === -1) {
              var numRaw = Number(raw);
              for (var i = 0; i < valuesList.length; i++) {
                if (Number(valuesList[i]) === numRaw) { idx = i; break; }
              }
            }
            if (idx === -1) { idx = Number(wrap.dataset.default) || 0; }
            if (wrap._updateDisplay) { wrap._updateDisplay(idx); }
          } else {
            var val = Number(self.settings[parts[0]][parts[1]]);
            if (wrap._updateDisplay) { wrap._updateDisplay(val); }
          }
        }
      });

      // Update EQ toggles and chiclets
      var toggleEq = document.getElementById('toggle-eq');
      var dpxBtnEq = document.getElementById('dpx-btn-eq');
      var dpxLedEq = document.getElementById('dpx-led-eq');
      var eqOn = self.settings.eq ? self.settings.eq.enabled !== false : true;

      if (toggleEq) {
        toggleEq.classList.toggle('on', eqOn);
        toggleEq.innerHTML = '<span class="led"></span> ' + (eqOn ? 'IN' : 'OUT');
      }
      if (dpxBtnEq) { dpxBtnEq.classList.toggle('active', eqOn); }
      if (dpxLedEq) { dpxLedEq.classList.toggle('on', eqOn); }

      var dpxBtnPhase = document.getElementById('dpx-btn-phase');
      if (dpxBtnPhase && self.settings.eq) {
        dpxBtnPhase.classList.toggle('active', Boolean(self.settings.eq.phase));
      }

      // Update compressor toggles
      var toggleComp = document.getElementById('toggle-comp');
      if (toggleComp) {
        var compOn = self.settings.comp ? self.settings.comp.enabled !== false : true;
        toggleComp.classList.toggle('on', compOn);
        toggleComp.innerHTML = '<span class="led"></span> ' + (compOn ? 'IN' : 'OUT');
      }

      // Update stereo imager toggles
      var toggleImager = document.getElementById('toggle-imager');
      var toggleImagerPwr = document.getElementById('toggle-imager-pwr');
      var imagerOn = self.settings.imager ? self.settings.imager.enabled !== false : true;
      if (toggleImager) {
        toggleImager.classList.toggle('on', imagerOn);
        toggleImager.innerHTML = '<span class="led"></span> ' + (imagerOn ? 'IN' : 'OUT');
      }
      if (toggleImagerPwr) {
        toggleImagerPwr.classList.toggle('on', imagerOn);
      }
      var toggleImagerHarmonics = document.getElementById('toggle-imager-harmonics');
      if (toggleImagerHarmonics && self.settings.imager) {
        toggleImagerHarmonics.classList.toggle('active', Boolean(self.settings.imager.harmonics));
      }
      var toggleImagerBass = document.getElementById('toggle-imager-bass');
      if (toggleImagerBass && self.settings.imager) {
        toggleImagerBass.classList.toggle('active', Boolean(self.settings.imager.bass));
      }

      // Update limiter toggles
      var toggleLimit = document.getElementById('toggle-limit');
      if (toggleLimit) {
        var limOn = self.settings.limit ? self.settings.limit.enabled !== false : true;
        toggleLimit.classList.toggle('on', limOn);
        toggleLimit.innerHTML = '<span class="led"></span> ' + (limOn ? 'IN' : 'OUT');
      }

      self.syncStems();      // the stems in step with the settings, and the stage drawn
      var toggleSpaceBtn = document.getElementById('toggle-space');
      if (toggleSpaceBtn) {
        var spaceIn = spaceOn(self.settings) || Boolean(self.settings.space && self.settings.space.enabled);
        toggleSpaceBtn.classList.toggle('on', spaceIn);
        toggleSpaceBtn.innerHTML = '<span class="led"></span> ' + (spaceIn ? 'IN' : 'OUT');
      }
      Array.prototype.forEach.call(document.querySelectorAll('#space-scenes [data-scene]'), function (button) {
        var scene = SPACE_SCENES[button.dataset.scene], sp = self.settings.space || {};
        var lit = Boolean(sp.enabled) && Object.keys(scene).every(function (k) { return Math.abs(Number(sp[k]) - scene[k]) < 1e-6; });
        button.classList.toggle('active', lit);
      });

      var toggleWarmth = document.getElementById('toggle-warmth');
      var warmthStatus = document.getElementById('warmth-status');
      if (toggleWarmth && self.settings.limit) {
        var warm = Boolean(self.settings.limit.warmth);
        toggleWarmth.classList.toggle('on', warm);
        if (warmthStatus) {
          warmthStatus.textContent = warm ? t('TUBE ON') : 'OFF';
          warmthStatus.classList.toggle('active', warm);
        }
      }

      // Update ratio buttons
      var ratioBank = document.getElementById('comp-ratios');
      if (ratioBank && self.settings.comp) {
        var r = self.settings.comp.ratio;
        Array.prototype.forEach.call(ratioBank.querySelectorAll('.ratio-btn'), function (b) {
          b.classList.toggle('on', Number(b.dataset.ratio) === r);
        });
      }

      this.syncPeq();
      this.updateBypassUI();
      this.syncPresetSelect();
    },

    // ------------------------------------------------------------- The parametric equaliser's screen
    PEQ_COLOURS: ['#22d3ee', '#a3e635', '#fbbf24', '#fb7185', '#c084fc', '#34d399', '#60a5fa'],
    PEQ_RANGES: [6, 12, 18],
    PEQ_KINDS: {
      lowcut: [t('Low cut'), 'M3 17c5 0 6-10 10-10h8'],
      lowshelf: [t('Low shelf'), 'M3 15h5c3 0 3-6 6-6h7'],
      bell: [t('Bell'), 'M3 15h4c3 0 3-8 5-8s2 8 5 8h4'],
      notch: [t('Notch'), 'M3 9h5c3 0 3 9 4 9s1-9 4-9h5'],
      highshelf: [t('High shelf'), 'M3 9h7c3 0 3 6 6 6h5'],
      highcut: [t('High cut'), 'M3 7h8c4 0 5 10 10 10']
    },
    peqBand: 0,          // the band the strip's controls are for

    /* What a band does, in words, for its tooltip: a shelf or a cut acts on everything on one side of its
       frequency, which is easy to miss when it sits far from the end it is named for. */
    peqBandTip: function (band, i) {
      var hz = band.freq >= 1000 ? (Math.round(band.freq / 100) / 10) + ' kHz' : Math.round(band.freq) + ' Hz';
      var gain = Math.round(band.gain * 10) / 10, kind = this.PEQ_KINDS[band.type] ? this.PEQ_KINDS[band.type][0] : band.type;
      var head = t('Band {value}: {kind} at {hz}{value2}', { value: i + 1, kind: kind, hz: hz, value2: peqHasGain(band.type) ? ', ' + (gain > 0 ? '+' : '') + gain + ' dB' : '' });
      var how = gain > 0 ? 'raises' : 'lowers';
      var does = {
        lowcut: t('takes away everything below {hz}', { hz: hz }),
        highcut: t('takes away everything above {hz}', { hz: hz }),
        notch: t('takes out a narrow slice at {hz}', { hz: hz }),
        lowshelf: gain ? t('{how} everything below {hz}', { how: how, hz: hz }) : t('no change yet'),
        highshelf: gain ? t('{how} everything above {hz}', { how: how, hz: hz }) : t('no change yet'),
        bell: gain ? t('{how} the sound around {hz}', { how: how, hz: hz }) : t('no change yet')
      }[band.type] || '';
      return head + (does ? ': ' + does : '') + (band.on === false ? ' (off)' : '');
    },

    /* The settings' equaliser, made whole: older settings have none, and a preset replaces it. */
    peq: function () {
      var held = this.settings.peq;
      if (!held || !Array.isArray(held.bands) || held.bands.length !== defaultPeq().bands.length) {
        this.settings.peq = peqOf(this.settings);
      }
      return this.settings.peq;
    },

    /* Where the graph is drawn within the canvas, and the two scales: frequency by octaves along it,
       decibels up it. */
    peqPlot: function (canvas) {
      var w = canvas.clientWidth, h = canvas.clientHeight, type = this.rackType || 1;
      return { left: 8, top: 10, width: Math.max(10, w - 8 - 38 * type), height: Math.max(10, h - 10 - 20 * type), w: w, h: h,
               range: this.peqRange(), type: type };
    },
    /* How many decibels the graph shows either side of the middle: small for fine moves, large for broad
       ones.  It is how the graph is looked at, not part of the sound, so the browser keeps it. */
    peqRange: function () {
      var kept = 12;
      try { kept = Number(localStorage.getItem('yue2.peqRange')) || 12; } catch (err) { /* private mode */ }
      return this.PEQ_RANGES.indexOf(kept) >= 0 ? kept : 12;
    },
    peqX: function (plot, hz) { return plot.left + plot.width * Math.log(hz / PEQ_FREQ[0]) / Math.log(PEQ_FREQ[1] / PEQ_FREQ[0]); },
    peqHz: function (plot, x) {
      var t = Math.min(1, Math.max(0, (x - plot.left) / plot.width));
      return PEQ_FREQ[0] * Math.pow(PEQ_FREQ[1] / PEQ_FREQ[0], t);
    },
    peqY: function (plot, db) {
      var shown = Math.min(plot.range, Math.max(-plot.range, db));     // a value past the edge is drawn at it
      return plot.top + plot.height * (0.5 - shown / (2 * plot.range));
    },
    peqGainAt: function (plot, y) { return (0.5 - (y - plot.top) / plot.height) * 2 * plot.range; },
    /* A band's handle: at its gain, or on the middle line when its kind has none. */
    peqNode: function (plot, band) {
      return { x: this.peqX(plot, band.freq), y: this.peqY(plot, peqHasGain(band.type) ? band.gain : 0) };
    },

    /* A value of the equaliser has changed: heard at once, kept with the take, shown. */
    peqChanged: function (engage) {
      var peq = this.peq();
      if (engage && peq.enabled === false) { peq.enabled = true; }
      Engine.applySettings(this.settings);
      this.debouncedSave();
      this.syncPeq();
    },

    peqSet: function (index, key, value) {
      var band = this.peq().bands[index];
      if (!band) { return; }
      if (key === 'freq') { band.freq = Math.round(Math.min(PEQ_FREQ[1], Math.max(PEQ_FREQ[0], value))); }
      if (key === 'gain') { band.gain = Math.round(Math.min(PEQ_GAIN[1], Math.max(PEQ_GAIN[0], value)) * 10) / 10; }
      if (key === 'q') { band.q = Math.round(Math.min(PEQ_Q[1], Math.max(PEQ_Q[0], value)) * 100) / 100; }
      if (key === 'type' && PEQ_TYPES.indexOf(value) >= 0) {
        // a cut starts without a bump at its corner; a bell or a notch at a middling width
        if (!peqHasWidth(band.type) || (peqHasGain(band.type) !== peqHasGain(value))) {
          band.q = (value === 'lowcut' || value === 'highcut') ? PEQ_BUTTERWORTH : 1;
        }
        band.type = value;
      }
      band.on = true;
    },

    bindPeq: function () {
      var self = this;
      var canvas = document.getElementById('peq-canvas');
      var dots = document.getElementById('peq-dots');
      var types = document.getElementById('peq-types');
      if (!canvas || !dots || !types) { return; }

      dots.innerHTML = this.PEQ_COLOURS.map(function (colour, i) {
        return '<button type="button" class="peq-dot" data-band="' + i + '" style="--band:' + colour + '" title="' + t('Band {value}', { value: i + 1 }) + '">' + (i + 1) + '</button>';
      }).join('');
      types.innerHTML = PEQ_TYPES.map(function (kind) {
        return '<button type="button" class="peq-type" data-kind="' + kind + '" title="' + self.PEQ_KINDS[kind][0] + '" aria-label="' + self.PEQ_KINDS[kind][0] + '">' +
          '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + self.PEQ_KINDS[kind][1] + '"/></svg></button>';
      }).join('');

      dots.addEventListener('click', function (e) {
        var dot = e.target.closest('[data-band]');
        if (!dot) { return; }
        self.peqBand = Number(dot.dataset.band);
        self.syncPeq();
      });
      types.addEventListener('click', function (e) {
        var button = e.target.closest('[data-kind]');
        if (!button) { return; }
        self.peqSet(self.peqBand, 'type', button.dataset.kind);
        self.peqChanged(true);
      });
      var power = document.getElementById('peq-band-on');
      if (power) {
        power.addEventListener('click', function () {
          var band = self.peq().bands[self.peqBand];
          band.on = band.on === false;
          self.peqChanged(band.on);
        });
      }
      var toggle = document.getElementById('toggle-peq');
      if (toggle) {
        toggle.addEventListener('click', function () {
          var peq = self.peq();
          peq.enabled = peq.enabled === false;
          self.peqChanged(false);
        });
      }
      // Flat: the curve is a straight line again.  A band with a gain goes to 0 dB; a cut or a notch has
      // none, so it is switched off.  Each band keeps its place, its kind and its width, to be used again.
      var flat = document.getElementById('peq-flat');
      if (flat) {
        flat.addEventListener('click', function () {
          self.peq().bands.forEach(function (band) {
            if (peqHasGain(band.type)) { band.gain = 0; } else { band.on = false; }
          });
          self.peqChanged(false);
        });
      }
      var range = document.getElementById('peq-range');
      if (range) {
        range.addEventListener('click', function () {
          var next = self.PEQ_RANGES[(self.PEQ_RANGES.indexOf(self.peqRange()) + 1) % self.PEQ_RANGES.length];
          try { localStorage.setItem('yue2.peqRange', String(next)); } catch (err) { /* private mode */ }
          self.syncPeq();
        });
      }

      // The graph: a band's handle is dragged across for its frequency and up and down for its gain
      var drag = null;
      function at(e) {
        // the pointer is in the window's pixels and the graph in its own, which a rack drawn smaller makes larger
        var box = canvas.getBoundingClientRect(), scale = box.width ? canvas.clientWidth / box.width : 1;
        return { x: (e.clientX - box.left) * scale, y: (e.clientY - box.top) * scale };
      }
      function bandAt(point) {
        var plot = self.peqPlot(canvas), reach = 16 * plot.type, best = -1, nearest = reach;
        self.peq().bands.forEach(function (band, i) {
          var node = self.peqNode(plot, band), far = Math.hypot(node.x - point.x, node.y - point.y);
          // the chosen band wins where two handles lie together
          if (far < nearest || (far <= nearest + 0.5 && i === self.peqBand && far < reach)) { nearest = far; best = i; }
        });
        return best;
      }
      canvas.addEventListener('pointerdown', function (e) {
        if (e.button !== 0) { return; }
        var hit = bandAt(at(e));
        if (hit < 0) { return; }
        self.peqBand = hit;
        drag = { band: hit, moved: false };
        try { canvas.setPointerCapture(e.pointerId); } catch (err) {}
        self.syncPeq();
        e.preventDefault();
      });
      canvas.addEventListener('pointermove', function (e) {
        var point = at(e);
        if (!drag) {
          var over = bandAt(point);
          canvas.style.cursor = over >= 0 ? 'grab' : 'default';
          if (!canvas.dataset.tip) { canvas.dataset.tip = canvas.title; }
          canvas.title = over >= 0 ? self.peqBandTip(self.peq().bands[over], over) : canvas.dataset.tip;
          return;
        }
        var plot = self.peqPlot(canvas), band = self.peq().bands[drag.band];
        drag.moved = true;
        self.peqSet(drag.band, 'freq', self.peqHz(plot, point.x));
        if (peqHasGain(band.type)) { self.peqSet(drag.band, 'gain', self.peqGainAt(plot, point.y)); }
        self.peqChanged(true);
      });
      function drop(e) {
        if (!drag) { return; }
        try { canvas.releasePointerCapture(e.pointerId); } catch (err) {}
        drag = null;
      }
      canvas.addEventListener('pointerup', drop);
      canvas.addEventListener('pointercancel', drop);
      canvas.addEventListener('dblclick', function (e) {
        var hit = bandAt(at(e));
        if (hit < 0) { return; }
        self.peq().bands[hit] = defaultPeq().bands[hit];
        self.peqBand = hit;
        self.peqChanged(false);
      });
      canvas.addEventListener('wheel', function (e) {
        var hit = bandAt(at(e));
        if (hit < 0) { return; }
        var band = self.peq().bands[hit];
        if (!peqHasWidth(band.type)) { return; }
        e.preventDefault();
        self.peqBand = hit;
        self.peqSet(hit, 'q', band.q * Math.pow(1.12, e.deltaY < 0 ? 1 : -1));
        self.peqChanged(true);
      }, { passive: false });

      // The strip's three knobs, for the chosen band: frequency and width by ratio, gain by decibels
      Array.prototype.forEach.call(document.querySelectorAll('.peq-knob'), function (wrap) {
        var key = wrap.dataset.peq, start = null;
        function turned(from, steps) {
          if (key === 'freq') { return from * Math.pow(PEQ_FREQ[1] / PEQ_FREQ[0], steps / 220); }
          if (key === 'q') { return from * Math.pow(PEQ_Q[1] / PEQ_Q[0], steps / 180); }
          return from + steps * (PEQ_GAIN[1] - PEQ_GAIN[0]) / 180;
        }
        function usable() {
          var band = self.peq().bands[self.peqBand];
          return key === 'freq' || (key === 'gain' ? peqHasGain(band.type) : peqHasWidth(band.type));
        }
        wrap.addEventListener('pointerdown', function (e) {
          if (e.button !== 0 || !usable()) { return; }
          start = { y: e.clientY, value: self.peq().bands[self.peqBand][key] };
          try { wrap.setPointerCapture(e.pointerId); } catch (err) {}
          e.preventDefault();
        });
        wrap.addEventListener('pointermove', function (e) {
          if (!start) { return; }
          self.peqSet(self.peqBand, key, turned(start.value, start.y - e.clientY));
          self.peqChanged(true);
        });
        function let_go(e) {
          if (!start) { return; }
          try { wrap.releasePointerCapture(e.pointerId); } catch (err) {}
          start = null;
        }
        wrap.addEventListener('pointerup', let_go);
        wrap.addEventListener('pointercancel', let_go);
        wrap.addEventListener('dblclick', function () {
          if (!usable()) { return; }
          var first = defaultPeq().bands[self.peqBand], band = self.peq().bands[self.peqBand];
          var cut = band.type === 'lowcut' || band.type === 'highcut';
          self.peqSet(self.peqBand, key, key === 'q' ? (cut ? PEQ_BUTTERWORTH : 1) : first[key]);
          self.peqChanged(true);
        });
        wrap.addEventListener('wheel', function (e) {
          if (!usable()) { return; }
          e.preventDefault();
          self.peqSet(self.peqBand, key, turned(self.peq().bands[self.peqBand][key], e.deltaY < 0 ? 4 : -4));
          self.peqChanged(true);
        }, { passive: false });
      });
    },

    /* The unit's switch and the strip, from the settings. */
    syncPeq: function () {
      var peq = this.peq(), self = this;
      if (this.peqBand >= peq.bands.length) { this.peqBand = 0; }
      var band = peq.bands[this.peqBand], unitIn = peq.enabled !== false;
      var toggle = document.getElementById('toggle-peq');
      if (toggle) {
        toggle.classList.toggle('on', unitIn);
        toggle.innerHTML = '<span class="led"></span> ' + (unitIn ? 'IN' : 'OUT');
      }
      var range = document.getElementById('peq-range');
      if (range) { range.textContent = '\u00b1' + this.peqRange() + ' dB'; }
      var strip = document.getElementById('peq-strip');
      if (!strip) { return; }
      strip.style.setProperty('--band', this.PEQ_COLOURS[this.peqBand]);
      Array.prototype.forEach.call(strip.querySelectorAll('.peq-dot'), function (dot) {
        var i = Number(dot.dataset.band);
        dot.classList.toggle('chosen', i === self.peqBand);
        dot.classList.toggle('off', peq.bands[i].on === false);
        dot.title = self.peqBandTip(peq.bands[i], i);
      });
      Array.prototype.forEach.call(strip.querySelectorAll('.peq-type'), function (button) {
        button.classList.toggle('chosen', button.dataset.kind === band.type);
      });
      var power = document.getElementById('peq-band-on');
      if (power) { power.classList.toggle('on', band.on !== false); }
      Array.prototype.forEach.call(strip.querySelectorAll('.peq-knob'), function (wrap) {
        var key = wrap.dataset.peq, dial = wrap.querySelector('.knob-dial'), label = wrap.querySelector('.knob-val');
        var used = key === 'freq' || (key === 'gain' ? peqHasGain(band.type) : peqHasWidth(band.type));
        var turn = key === 'freq' ? Math.log(band.freq / PEQ_FREQ[0]) / Math.log(PEQ_FREQ[1] / PEQ_FREQ[0])
          : key === 'q' ? Math.log(band.q / PEQ_Q[0]) / Math.log(PEQ_Q[1] / PEQ_Q[0])
          : (band.gain - PEQ_GAIN[0]) / (PEQ_GAIN[1] - PEQ_GAIN[0]);
        wrap.classList.toggle('unused', !used);
        if (dial) { dial.style.transform = 'rotate(' + (-135 + Math.min(1, Math.max(0, used ? turn : 0.5)) * 270) + 'deg)'; }
        if (label) {
          label.textContent = !used ? '\u2013'
            : key === 'freq' ? (band.freq >= 1000 ? (Math.round(band.freq / 10) / 100) + ' kHz' : Math.round(band.freq) + ' Hz')
            : key === 'q' ? band.q.toFixed(2)
            : (band.gain > 0 ? '+' : '') + band.gain.toFixed(1) + ' dB';
        }
      });
      this.drawPeq();
    },

    /* The screen: the scales, what is being heard behind them, each band's own curve in its colour,
       and over them the one line that is all of them together. */
    drawPeq: function () {
      var canvas = document.getElementById('peq-canvas');
      if (!canvas || !canvas.getContext || !canvas.clientWidth) { return; }
      var ratio = (window.devicePixelRatio || 1) * (this.rackZoom || 1), plot = this.peqPlot(canvas), self = this;
      if (canvas.width !== Math.round(plot.w * ratio) || canvas.height !== Math.round(plot.h * ratio)) {
        canvas.width = Math.round(plot.w * ratio);
        canvas.height = Math.round(plot.h * ratio);
      }
      var g = canvas.getContext('2d');
      g.setTransform(ratio, 0, 0, ratio, 0, 0);
      g.clearRect(0, 0, plot.w, plot.h);
      var peq = this.peq(), unitIn = peq.enabled !== false;
      var rate = (Engine.ctx && Engine.ctx.sampleRate) || 48000;
      var right = plot.left + plot.width, bottom = plot.top + plot.height, zero = this.peqY(plot, 0);
      // the graph's colours are the unit's, so they follow the theme (styles.css, .unit-peq)
      var curTheme = (document.documentElement && document.documentElement.dataset.theme) || 'dark';
      if (!this._peqInk || this._peqInkTheme !== curTheme) {
        var look = window.getComputedStyle(canvas.closest('.unit-peq') || canvas);
        function colour(name, otherwise) { return (look.getPropertyValue(name) || '').trim() || otherwise; }
        this._peqInk = {
          grid: colour('--peq-grid', 'rgba(255,255,255,0.09)'), faint: colour('--peq-grid-faint', 'rgba(255,255,255,0.035)'),
          zero: colour('--peq-zero', 'rgba(255,255,255,0.22)'), line: colour('--peq-line', 'rgba(255,255,255,0.06)'),
          label: colour('--peq-label', 'rgba(148,163,184,0.75)'), labelZero: colour('--peq-label-zero', 'rgba(226,232,240,0.85)'),
          heard: colour('--peq-heard', 'rgba(148,163,184,0.13)'), heardEdge: colour('--peq-heard-edge', 'rgba(203,213,225,0.28)'),
          total: colour('--peq-total', '#f8fafc'), totalOut: colour('--peq-total-out', 'rgba(148,163,184,0.6)'),
          ring: colour('--peq-ring', 'rgba(15,17,22,0.9)'), ringChosen: colour('--peq-ring-chosen', '#ffffff'), number: colour('--peq-number', '#0b0c10')
        };
        this._peqInkTheme = curTheme;
      }
      var ink = this._peqInk;

      // scales
      g.font = Math.round(10 * plot.type * 10) / 10 + 'px ui-monospace, SFMono-Regular, Menlo, monospace';
      g.textBaseline = 'middle';
      [20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 2000, 3000, 4000, 5000,
       6000, 7000, 8000, 9000, 10000, 20000].forEach(function (hz) {
        var x = Math.round(self.peqX(plot, hz)) + 0.5, named = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000].indexOf(hz) >= 0;
        g.strokeStyle = named ? ink.grid : ink.faint;
        g.beginPath(); g.moveTo(x, plot.top); g.lineTo(x, bottom); g.stroke();
        if (named) {
          g.fillStyle = ink.label;
          g.textAlign = hz === 20 ? 'left' : hz === 20000 ? 'right' : 'center';
          g.fillText(hz >= 1000 ? (hz / 1000) + 'k' : String(hz), x, bottom + 11 * plot.type);
        }
      });
      var step = plot.range === 6 ? 2 : plot.range === 12 ? 3 : 6, lines = [0];
      for (var mark = step; mark < plot.range; mark += step) { lines.push(mark, -mark); }
      lines.forEach(function (db) {
        var y = Math.round(self.peqY(plot, db)) + 0.5;
        g.strokeStyle = db === 0 ? ink.zero : ink.line;
        g.beginPath(); g.moveTo(plot.left, y); g.lineTo(right, y); g.stroke();
        g.fillStyle = db === 0 ? ink.labelZero : ink.label;
        g.textAlign = 'left';
        g.fillText((db > 0 ? '+' : '') + db, right + 6, y);
      });

      // what is heard
      var heard = Engine.spectrum, audio = document.getElementById('audio');
      if (heard && heard.getFloatFrequencyData && audio && !audio.paused) {
        var bins = this.peqBins && this.peqBins.length === heard.frequencyBinCount ? this.peqBins : (this.peqBins = new Float32Array(heard.frequencyBinCount));
        heard.getFloatFrequencyData(bins);
        var perBin = rate / (2 * bins.length);
        g.beginPath(); g.moveTo(plot.left, bottom);
        for (var sx = 0; sx <= plot.width; sx += 2) {
          var from = Math.floor(this.peqHz(plot, plot.left + sx) / perBin), to = Math.max(from, Math.floor(this.peqHz(plot, plot.left + sx + 2) / perBin));
          var loud = -200;
          for (var bin = from; bin <= to && bin < bins.length; bin++) { if (bins[bin] > loud) { loud = bins[bin]; } }
          var level = Math.min(1, Math.max(0, (loud + 105) / 90));
          g.lineTo(plot.left + sx, bottom - level * plot.height);
        }
        g.lineTo(right, bottom); g.closePath();
        g.fillStyle = ink.heard; g.fill();
        g.strokeStyle = ink.heardEdge; g.lineWidth = 1; g.stroke();
      }

      // each band, then all of them
      var xs = [], total = [];
      for (var px = 0; px <= plot.width; px += 2) { xs.push(px); total.push(0); }
      g.save();
      g.beginPath(); g.rect(plot.left, plot.top, plot.width, plot.height); g.clip();
      peq.bands.forEach(function (band, i) {
        if (!peqBandActive(band)) { return; }
        var shape = peqBandShape(band, true), chosen = i === self.peqBand;
        g.beginPath(); g.moveTo(plot.left, zero);
        xs.forEach(function (px, n) {
          var db = biquadDb(shape, self.peqHz(plot, plot.left + px), rate);
          total[n] += db;
          g.lineTo(plot.left + px, self.peqY(plot, db));
        });
        g.lineTo(right, zero); g.closePath();
        g.globalAlpha = (unitIn ? 1 : 0.4) * (chosen ? 0.34 : 0.16);
        g.fillStyle = self.PEQ_COLOURS[i]; g.fill();
        g.globalAlpha = (unitIn ? 1 : 0.4) * (chosen ? 0.95 : 0.55);
        g.strokeStyle = self.PEQ_COLOURS[i]; g.lineWidth = 1.2; g.stroke();
      });
      g.globalAlpha = 1;
      g.beginPath();
      xs.forEach(function (px, n) {
        var y = self.peqY(plot, total[n]);
        if (n) { g.lineTo(plot.left + px, y); } else { g.moveTo(plot.left + px, y); }
      });
      g.strokeStyle = unitIn ? ink.total : ink.totalOut;
      g.lineWidth = 2;
      if (!unitIn) { g.setLineDash([5, 5]); }
      g.stroke();
      g.setLineDash([]);
      g.restore();

      // the handles
      peq.bands.forEach(function (band, i) {
        var node = self.peqNode(plot, band), chosen = i === self.peqBand, on = band.on !== false;
        g.globalAlpha = (unitIn ? 1 : 0.55) * (on ? 1 : 0.35);
        g.beginPath(); g.arc(node.x, node.y, (chosen ? 8 : 6) * plot.type, 0, Math.PI * 2);
        g.fillStyle = self.PEQ_COLOURS[i]; g.fill();
        g.lineWidth = chosen ? 2.5 : 1.5;
        g.strokeStyle = chosen ? ink.ringChosen : ink.ring; g.stroke();
        if (chosen) {
          g.fillStyle = ink.number; g.textAlign = 'center';
          g.font = 'bold ' + Math.round(9 * plot.type * 10) / 10 + 'px ui-monospace, SFMono-Regular, Menlo, monospace';
          g.fillText(String(i + 1), node.x, node.y + 0.5);
        }
      });
      g.globalAlpha = 1;
    },

    /* The preset whose values these settings are: a factory one, then one of the user's.
       Null when they are nobody's preset. */
    presetOf: function (settings) {
      var sound = soundOf(settings);
      var key;
      for (key in PRESETS) {
        if (PRESETS.hasOwnProperty(key) && soundOf(PRESETS[key]) === sound) { return key; }
      }
      var mine = this.getUserPresets();
      for (key in mine) {
        if (mine.hasOwnProperty(key) && soundOf(mine[key]) === sound) { return key; }
      }
      return null;
    },

    /* The preset box says what the rack holds, however it came to hold it: a preset chosen
       here, the settings kept with the take now playing, or Custom once a control has moved. */
    syncPresetSelect: function () {
      var select = document.getElementById('rack-preset-select');
      if (!select) { return; }
      var custom = select.querySelector('option[value="custom"]');
      if (!custom) {
        custom = document.createElement('option');
        custom.value = 'custom'; custom.hidden = true; custom.disabled = true; custom.textContent = t('Custom');
        select.insertBefore(custom, select.firstChild);
      }
      var key = this.presetOf(this.settings) || 'custom';
      if (select.value !== key) { select.value = key; }
      this.paintPresetButton();
    },

    updateBypassUI: function () {
      var bypassBtn = document.getElementById('rack-master-bypass');
      var bypassLed = document.getElementById('rack-master-led');
      var panel = document.getElementById('rack-panel');
      var activeDot = document.getElementById('rack-active-dot');

      var isBypassed = Boolean(this.settings.masterBypass);
      if (bypassBtn) { bypassBtn.classList.toggle('bypassed', isBypassed); }
      if (bypassLed) { bypassLed.classList.toggle('off', isBypassed); }
      if (panel) { panel.classList.toggle('master-bypassed', isBypassed); }
      if (activeDot) { activeDot.classList.toggle('hidden', isBypassed); }
    },

    /* Turning a control of a module that is out switches the module in: a knob that moved
       and changed nothing would be a puzzle.  Putting a knob back with a double click does not. */
    engage: function (module) {
      var m = this.settings[module];
      if (!m || m.enabled !== false) { return; }
      m.enabled = true;
      this.syncKnobsToState();
    },

    mergeSettings: function (base, override) {
      var out = JSON.parse(JSON.stringify(base));
      if (!override || typeof override !== 'object') { return out; }
      for (var k in override) {
        if (override.hasOwnProperty(k)) {
          if (override[k] && typeof override[k] === 'object' && !Array.isArray(override[k])) {
            out[k] = Object.assign({}, out[k] || {}, override[k]);
          } else {
            out[k] = override[k];
          }
        }
      }
      return out;
    },

    toggle: function (force) {
      var panel = document.getElementById('rack-panel');
      if (!panel) { return; }
      this.isOpen = (typeof force === 'boolean') ? force : !panel.classList.contains('is-open');
      panel.classList.toggle('is-open', this.isOpen);
      if (!this.isOpen) { this.openPresetMenu(false); }

      var btn = document.getElementById('btn-fx-rack');
      if (btn) { btn.classList.toggle('active', this.isOpen); }

      this.updateTakeCardsUI();

      if (this.isOpen) {
        if (!this.currentTakeId && window.State) {
          var tid = State.playing || State.loadedId || (typeof selectedTakeId === 'function' ? selectedTakeId() : null);
          if (tid && typeof takeById === 'function') {
            var t = takeById(tid);
            if (t) { this.onTake(t); }
          }
        }
        if (panel.classList.contains('is-floating')) {
          this.clampFloatingBounds();
        }
        Engine.resume();
        this.fitToWindow();
        this.syncKnobsToState();
        if (!this.animFrame) {
          this.startMeterLoop();
        }
      } else {
        if (this.animFrame) {
          cancelAnimationFrame(this.animFrame);
          this.animFrame = null;
        }
        this.flushSave();
      }
    },

    updateTakeCardsUI: function () {
      var activeTakeId = this.currentTakeId;
      var isOpen = this.isOpen;
      var cardBtns = document.querySelectorAll('button[data-act="mastering"]');
      var self = this;
      Array.prototype.forEach.call(cardBtns, function (b) {
        var card = b.closest('.take');
        var cardId = card ? card.dataset.id : null;
        b.classList.toggle('active', Boolean(isOpen && cardId && String(cardId) === String(activeTakeId)));
        // Lit while the rack changes how the take sounds: set here as well as when the cards are drawn,
        // so a card answers a switch in the rack at once and not when the list is next read.
        if (cardId) { b.classList.toggle('mastered', self.hasActiveMastering(cardId)); }
      });
      // The editor window has a button of its own for the take it holds, which the page paints.
      if (typeof paintEdMastering === 'function') { paintEdMastering(); }
    },

    openForTake: function (take) {
      if (!take) { return; }
      if (!this.currentTakeId || String(this.currentTakeId) !== String(take.id)) {
        this.flushSave();
        this.onTake(take);
      }
      this.toggle(true);
    },

    onTake: function (take) {
      if (!take) { return; }
      var audio = document.getElementById('audio');
      // If a different take is actively playing, never overwrite rack state or alter active playback DSP
      if (audio && !audio.paused && !audio.ended && window.State && State.playing && String(State.playing) !== String(take.id)) {
        return;
      }
      if (this.currentTakeId && String(this.currentTakeId) === String(take.id)) {
        return;
      }
      this.flushSave();
      this.currentTakeId = take.id;
      var label = document.getElementById('rack-take-name');
      if (label) { label.textContent = take.title || (t('Take #{id}', { id: take.id })); }
      this.updateTakeCardsUI();

      if (take.fx_chain) {
        try {
          var parsed = typeof take.fx_chain === 'string' ? JSON.parse(take.fx_chain) : take.fx_chain;
          if (parsed && typeof parsed === 'object') {
            this.settings = this.mergeSettings(PRESETS['default'], upgradeSettings(parsed));
            this.keptPayload = JSON.stringify(this.settings);
            this.syncKnobsToState();
            Engine.applySettings(this.settings);
            this.syncStems();
            return;
          }
        } catch (e) {}
      }

      var self = this;
      fetch('/api/takes/' + take.id + '/fx')
        .then(function (res) { return res.ok ? res.json() : {}; })
        .then(function (data) {
          if (self.currentTakeId !== take.id) { return; }
          if (data && Object.keys(data).length > 0) {
            self.settings = self.mergeSettings(PRESETS['default'], upgradeSettings(data));
          } else {
            self.settings = JSON.parse(JSON.stringify(PRESETS['default']));
          }
          self.keptPayload = JSON.stringify(self.settings);
          self.syncKnobsToState();
          Engine.applySettings(self.settings);
          self.syncStems();
        })
        .catch(function () {});
    },

    flushSave: function () {
      if (this.saveTimer) {
        clearTimeout(this.saveTimer);
        this.saveTimer = null;
      }
      if (!this.currentTakeId) { return Promise.resolve(); }
      var takeId = this.currentTakeId;
      var payload = JSON.stringify(this.settings);
      // A take that was only played or saved keeps no settings: nothing was changed
      if (payload === this.keptPayload) { return Promise.resolve(); }
      this.keptPayload = payload;

      // Immediately keep take object in State.takes and loadedTake in-sync
      if (window.State && State.takes) {
        var t = State.takes.find(function (x) { return String(x.id) === String(takeId); });
        if (t) { t.fx_chain = payload; }
      }
      if (window.State && State.loadedTake && String(State.loadedTake.id) === String(takeId)) {
        State.loadedTake.fx_chain = payload;
      }

      return fetch('/api/takes/' + takeId + '/fx', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: payload
      }).catch(function (err) {
        console.error('Failed to save mastering rack FX for take', takeId, err);
      });
    },

    debouncedSave: function () {
      var self = this;
      this.syncPresetSelect();
      if (!this.currentTakeId && window.State) {
        var tid = State.playing || State.loadedId || (typeof selectedTakeId === 'function' ? selectedTakeId() : null);
        if (tid) {
          self.currentTakeId = tid;
          var tObj = (typeof takeById === 'function') ? takeById(tid) : null;
          var label = document.getElementById('rack-take-name');
          if (label && tObj) { label.textContent = tObj.title || (I18N.t('Take #{id}', { id: tObj.id })); }
          self.updateTakeCardsUI();
        }
      }
      if (!this.currentTakeId) { return; }

      var takeId = this.currentTakeId;
      var payload = JSON.stringify(this.settings);

      // Immediately update in-memory
      if (window.State && State.takes) {
        var t = State.takes.find(function (x) { return String(x.id) === String(takeId); });
        if (t) { t.fx_chain = payload; }
      }
      if (window.State && State.loadedTake && String(State.loadedTake.id) === String(takeId)) {
        State.loadedTake.fx_chain = payload;
      }
      this.updateTakeCardsUI();

      if (this.saveTimer) { clearTimeout(this.saveTimer); }
      this.saveTimer = setTimeout(function () {
        self.saveTimer = null;
        self.keptPayload = payload;
        fetch('/api/takes/' + takeId + '/fx', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: payload
        }).catch(function (err) {
          console.error('Failed to save mastering rack FX for take', takeId, err);
        });
      }, 350);
    },

    /* The settings a take plays with: the rack's own while it holds that take, otherwise the
       ones kept with the take.  Null when the take has none. */
    settingsFor: function (takeId) {
      if (this.currentTakeId && String(this.currentTakeId) === String(takeId)) {
        return this.settings;
      }
      var kept = null;
      var state = (typeof window !== 'undefined' && window.State) || (typeof State !== 'undefined' ? State : null);
      var takes = (state && state.takes) || [];
      var t = takes.find(function (x) { return String(x.id) === String(takeId); });
      if (!t && state && state.loadedTake && String(state.loadedTake.id) === String(takeId)) {
        t = state.loadedTake;
      }
      if (!t && state && state.saveTake && String(state.saveTake.id) === String(takeId)) {
        t = state.saveTake;
      }
      if (t && t.fx_chain) {
        try {
          kept = typeof t.fx_chain === 'string' ? JSON.parse(t.fx_chain) : t.fx_chain;
        } catch (e) {}
      }
      if (!kept || typeof kept !== 'object') { return null; }
      return this.mergeSettings(PRESETS['default'], upgradeSettings(kept));
    },

    /* Resolves settings for a take, falling back to querying /api/takes/{id}/fx from the server if not held locally. */
    resolveSettings: async function (takeId) {
      var s = this.settingsFor(takeId);
      if (s) { return s; }
      try {
        var resp = await fetch('/api/takes/' + encodeURIComponent(takeId) + '/fx');
        if (resp.ok) {
          var data = await resp.json();
          if (data && Object.keys(data).length > 0) {
            var merged = this.mergeSettings(PRESETS['default'], upgradeSettings(data));
            var state = (typeof window !== 'undefined' && window.State) || (typeof State !== 'undefined' ? State : null);
            var takes = (state && state.takes) || [];
            var t = takes.find(function (x) { return String(x.id) === String(takeId); });
            if (t) { t.fx_chain = data; }
            if (state && state.loadedTake && String(state.loadedTake.id) === String(takeId)) {
              state.loadedTake.fx_chain = data;
            }
            return merged;
          }
        }
      } catch (e) {}
      return null;
    },

    /* Whether the rack changes how this take sounds, which is whether Save has to render it. */
    hasActiveMastering: function (takeId) {
      return chainEngaged(this.settingsFor(takeId));
    },

    /* Whether the rack changes how this take sounds, resolving from the server if not cached locally. */
    hasActiveMasteringAsync: async function (takeId) {
      if (this.hasActiveMastering(takeId)) { return true; }
      var s = await this.resolveSettings(takeId);
      return chainEngaged(s);
    },

    chainEngaged: chainEngaged,
    spaceOn: spaceOn,
    defaultSpace: defaultSpace,
    buildGraph: buildMasteringDspGraph,     // the chain on any context, for renders and for checks
    nodeMakeupDb: nodeMakeupDb,
    defaultPeq: defaultPeq,
    peqOf: peqOf,
    peqDb: peqDb,
    peqBandShape: peqBandShape,
    biquadDb: biquadDb,
    upgradeSettings: upgradeSettings,
    soundOf: soundOf,

    /* The take through the chain, as a WAV: the same nodes and settings as playback, rendered
       offline at the file's own sample rate. */
    /* The take through the chain, as an AudioBuffer: the same nodes and settings as playback, rendered offline at the
       file's own sample rate.  Space only when asked (the headphones download); with SOURCE: STEMS, the take's stems,
       placed. */
    renderMasterBuffer: async function (takeId, customSettings, withSpace) {
      var s = customSettings || (await this.resolveSettings(takeId)) || PRESETS['default'];
      if (!withSpace) { s = withoutSpace(s); }     // the take's own file never has Space: it is for headphones

      var resp = await fetch('/api/takes/' + takeId + '/audio');
      if (!resp.ok) {
        throw new Error(t('Failed to fetch audio for take {takeId}', { takeId: takeId }));
      }
      var arrayBuf = await resp.arrayBuffer();

      // Decoding resamples to the context's rate, so the context is given the file's
      var OfflineContextClass = window.OfflineAudioContext || window.webkitOfflineAudioContext;
      var rate = fileSampleRate(arrayBuf);
      var decodeCtx = new OfflineContextClass(2, 1, rate);
      var decodedBuffer = await decodeCtx.decodeAudioData(arrayBuf);
      var stems = spaceOn(s) && s.space.source === 'stems' ? await this.stemBuffers(takeId, decodeCtx) : null;

      var offlineCtx = new OfflineContextClass(
        decodedBuffer.numberOfChannels,
        decodedBuffer.length,
        decodedBuffer.sampleRate
      );

      var src = offlineCtx.createBufferSource();
      src.buffer = decodedBuffer;

      var graph = buildMasteringDspGraph(offlineCtx, s);
      src.connect(graph.inputNode);
      graph.outputNode.connect(offlineCtx.destination);
      if (stems) {
        graph.chain.stemsReady = true;
        Object.keys(stems).forEach(function (name) {
          var stemSrc = offlineCtx.createBufferSource();
          stemSrc.buffer = stems[name];
          stemSrc.connect(graph.chain.stemNode(name).input);
          stemSrc.start(0);
        });
        graph.chain.applySettings(s, true);
      }

      src.start(0);
      return await offlineCtx.startRendering();
    },

    renderMasterWav: async function (takeId, customSettings, withSpace) {
      return audioBufferToWav(await this.renderMasterBuffer(takeId, customSettings, withSpace));
    },

    /* The newest finished set of stems the take has, decoded on `ctx`: { name: AudioBuffer }.  An error says so when
       there are none. */
    stemBuffers: async function (takeId, ctx) {
      var sets = await (await fetch('/api/stem-sets?take_id=' + encodeURIComponent(takeId))).json();
      var set = (sets || []).filter(function (x) { return x.status === 'done' && x.files && x.files.length; })[0];
      if (!set) { throw new Error(t('This take has no stems yet: make them first')); }
      var out = {};
      await Promise.all(set.files.map(async function (f) {
        var res = await fetch('/api/stem-sets/' + set.id + '/' + encodeURIComponent(f.file));
        if (!res.ok) { throw new Error(t('Could not read the stem {name}', { name: f.name })); }
        out[f.name] = await ctx.decodeAudioData(await res.arrayBuffer());
      }));
      return out;
    },

    /* ------------------------------------------------------------ Space: the take's stems while it plays
       Decoded once per take on the page's own context and started with the take, from where it is, on play and seek;
       the take keeps playing (it is what the page follows) but out of the chain while the stems stand in for it. */
    stemPlayer: { takeId: null, names: [], buffers: null, sources: [], startedAt: 0, rate: 1, loading: null, error: '' },

    stemsWanted: function () {
      return Boolean(spaceOn(this.settings) && this.settings.space.source === 'stems');
    },

    syncStems: function () {
      var player = this.stemPlayer, takeId = this.currentTakeId;
      if (player.takeId !== takeId) {       // another take: what was loaded is not its stems
        this.stopLiveStems();
        player.takeId = takeId; player.buffers = null; player.names = []; player.error = ''; player.loading = null;
        if (Engine.ctx) { Engine.stemsReady = false; }
      }
      if (this.stemsWanted() && !player.buffers && !player.loading && takeId) { this.loadLiveStems(takeId); }
      if (!Engine.ctx) { return; }
      Engine.stemsReady = Boolean(player.buffers);
      Engine.applySettings(this.settings);
      // Started only when they are not already playing: a dot dragged, a knob turned, changes where they sit, and
      // starting them again for that would break the sound on every move.
      var audio = document.getElementById('audio');
      if (this.stemsWanted() && player.buffers && audio && !audio.paused) {
        if (!player.sources.length) { this.startLiveStems(); }
      } else {
        this.stopLiveStems();
      }
      this.paintSpaceStage();
    },

    /* Stems asked for from the rack: looked for every few seconds until the set is done, then used. */
    waitForStems: function (takeId) {
      var self = this;
      clearTimeout(this.stemWait);
      this.stemWait = setTimeout(async function () {
        if (self.currentTakeId !== takeId) { return; }
        try {
          var sets = await (await fetch('/api/stem-sets?take_id=' + encodeURIComponent(takeId))).json();
          var newest = (sets || [])[0];
          if (newest && newest.status === 'done') {
            self.stemPlayer.error = ''; self.stemPlayer.buffers = null; self.stemPlayer.loading = null;
            self.syncStems();
            return;
          }
          if (newest && newest.status !== 'failed' && newest.status !== 'cancelled') { self.waitForStems(takeId); }
        } catch (e) { self.waitForStems(takeId); }
      }, 4000);
    },

    loadLiveStems: function (takeId) {
      var self = this, player = this.stemPlayer;
      if (!Engine.init()) { return; }
      player.error = '';
      player.loading = this.stemBuffers(takeId, Engine.ctx).then(function (buffers) {
        if (player.takeId !== takeId) { return; }
        player.buffers = buffers;
        player.names = Object.keys(buffers);
        player.names.forEach(function (name) { Engine.stemNode(name); });
        player.loading = null;
        self.syncStems();
      }).catch(function (err) {
        if (player.takeId !== takeId) { return; }
        player.loading = null;
        player.error = err && err.message ? err.message : String(err);
        self.paintSpaceStage();
      });
      this.paintSpaceStage();
    },

    startLiveStems: function () {
      var player = this.stemPlayer, audio = document.getElementById('audio'), ctx = Engine.ctx;
      this.stopLiveStems();
      if (!player.buffers || !audio || !ctx) { return; }
      var when = ctx.currentTime + 0.03, offset = audio.currentTime + 0.03 * (audio.playbackRate || 1);
      player.rate = audio.playbackRate || 1;
      player.startedAt = when - offset / player.rate;
      player.sources = player.names.map(function (name) {
        var src = ctx.createBufferSource();
        src.buffer = player.buffers[name];
        src.playbackRate.value = player.rate;
        src.connect(Engine.stemNode(name).input);
        if (offset < src.buffer.duration) { src.start(when, Math.max(0, offset)); }
        return src;
      });
    },

    stopLiveStems: function () {
      this.stemPlayer.sources.forEach(function (src) { try { src.stop(); } catch (e) { /* not started */ } try { src.disconnect(); } catch (e) {} });
      this.stemPlayer.sources = [];
    },

    /* The stems follow the take: started on play and seek, stopped on pause, and started again should they drift. */
    hookStemPlayback: function () {
      var self = this, audio = document.getElementById('audio');
      if (!audio || audio.dataset.stemsHooked) { return; }
      audio.dataset.stemsHooked = '1';
      function restart() { if (self.stemsWanted() && self.stemPlayer.buffers && !audio.paused) { self.startLiveStems(); } }
      ['playing', 'seeked', 'ratechange'].forEach(function (name) { audio.addEventListener(name, restart); });
      ['pause', 'ended', 'emptied'].forEach(function (name) { audio.addEventListener(name, function () { self.stopLiveStems(); }); });
      audio.addEventListener('timeupdate', function () {
        var player = self.stemPlayer;
        if (!player.sources.length || audio.paused || !Engine.ctx) { return; }
        var heard = (Engine.ctx.currentTime - player.startedAt) * player.rate;
        if (Math.abs(heard - audio.currentTime) > 0.06) { self.startLiveStems(); }
      });
    },

    /* ------------------------------------------------------------ Space: 5.1
       Six channels in WAV order (front left, front right, centre, LFE, back left, back right).  With stems, each stem's
       two channels go to the speakers either side of where they are placed; from the mix, the take through the rack
       (Space out) to the front pair, its side signal to the back pair as much as SURROUND, and in both the bass,
       below 120 Hz, to the LFE.  The rack's other modules shape the mix; placed stems go to the speakers as they are. */
    renderSurroundBuffer: async function (takeId) {
      var s = JSON.parse(JSON.stringify(this.settings));
      s.space = Object.assign(defaultSpace(), s.space || {});
      var OfflineContextClass = window.OfflineAudioContext || window.webkitOfflineAudioContext;
      var fromStems = s.space.source === 'stems';
      var stereo = await this.renderMasterBuffer(takeId, s, false);
      var rate = stereo.sampleRate, length = stereo.length;
      var stems = fromStems ? await this.stemBuffers(takeId, new OfflineContextClass(2, 1, rate)) : null;
      var ctx = new OfflineContextClass(6, length, rate);
      ctx.destination.channelCount = 6;
      ctx.destination.channelInterpretation = 'discrete';
      var merger = ctx.createChannelMerger(6);
      merger.connect(ctx.destination);
      function lfeFrom(node, level) {
        var a = ctx.createBiquadFilter(), b = ctx.createBiquadFilter(), g = ctx.createGain();
        a.type = b.type = 'lowpass'; a.frequency.value = b.frequency.value = 120;
        g.gain.value = level;
        g.channelCount = 1; g.channelCountMode = 'explicit';     // both sides, as one
        node.connect(a); a.connect(b); b.connect(g); g.connect(merger, 0, 3);
      }
      function toSpeakers(mono, az) {
        surroundGains(az).forEach(function (gain, ch) {
          if (gain < 1e-4) { return; }
          var g = ctx.createGain(); g.gain.value = gain;
          mono.connect(g); g.connect(merger, 0, ch);
        });
      }
      if (stems) {
        Object.keys(stems).forEach(function (name) {
          var src = ctx.createBufferSource(); src.buffer = stems[name];
          var split = ctx.createChannelSplitter(2), at = stemPlace(s.space, name);
          src.connect(split);
          [0, 1].forEach(function (side) {
            var mono = ctx.createGain();
            split.connect(mono, side);
            toSpeakers(mono, at.az + (side ? 1 : -1) * at.spread / 2);
          });
          if (name === 'bass' || name === 'drums') { lfeFrom(src, 0.316); }
          src.start(0);
        });
      } else {
        var src = ctx.createBufferSource(); src.buffer = stereo;
        var split = ctx.createChannelSplitter(2);
        src.connect(split);
        split.connect(merger, 0, 0);
        split.connect(merger, 1, 1);
        var sideL = ctx.createGain(), sideR = ctx.createGain(), side = ctx.createGain();
        sideL.gain.value = 0.5; sideR.gain.value = -0.5;
        split.connect(sideL, 0); split.connect(sideR, 1); sideL.connect(side); sideR.connect(side);
        var hp = ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 150;
        var delay = ctx.createDelay(0.1); delay.delayTime.value = SPACE_REAR_DELAY;
        var amount = Math.max(0, Math.min(1, Number(s.space.surround) || 0)) * 1.4;
        var back = ctx.createGain(); back.gain.value = amount;
        var invert = ctx.createGain(); invert.gain.value = -amount;
        side.connect(hp); hp.connect(delay); delay.connect(back); delay.connect(invert);
        back.connect(merger, 0, 4); invert.connect(merger, 0, 5);
        lfeFrom(src, 0.316);
        src.start(0);
      }
      var out = await ctx.startRendering();
      // under -1 dBFS on every channel, all turned down together so the balance holds
      var peak = 0;
      for (var ch = 0; ch < out.numberOfChannels; ch++) {
        var d = out.getChannelData(ch);
        for (var i = 0; i < d.length; i++) { var v = Math.abs(d[i]); if (v > peak) { peak = v; } }
      }
      if (peak > 0.891) {
        var k = 0.891 / peak;
        for (var c2 = 0; c2 < out.numberOfChannels; c2++) { var d2 = out.getChannelData(c2); for (var j = 0; j < d2.length; j++) { d2[j] *= k; } }
      }
      return out;
    },

    /* A channel test: a burst of noise from each speaker in turn, the way round a room (front left, centre, front
       right, back right, back left), then a low tone from the LFE; twice.  For checking a 5.1 player or a virtualiser. */
    surroundTestBuffer: function () {
      var rate = 48000, order = [0, 2, 1, 5, 4, 3], burst = 1.2, gap = 0.4;
      var length = Math.ceil(rate * (burst + gap) * order.length * 2 + rate);
      var Ctx = window.OfflineAudioContext || window.webkitOfflineAudioContext;
      var buf = new Ctx(6, 1, rate).createBuffer(6, length, rate);
      var seed = 3, b0 = 0, b1 = 0, b2 = 0;
      function pink() {
        seed = (seed * 16807) % 2147483647;
        var w = seed / 2147483647 * 2 - 1;
        b0 = 0.99765 * b0 + w * 0.099; b1 = 0.963 * b1 + w * 0.2965; b2 = 0.57 * b2 + w * 1.0527;
        return (b0 + b1 + b2 + w * 0.1848) * 0.11;
      }
      for (var round = 0; round < 2; round++) {
        order.forEach(function (ch, n) {
          var start = Math.floor(rate * ((round * order.length + n) * (burst + gap) + 0.5)), data = buf.getChannelData(ch);
          for (var i = 0; i < rate * burst; i++) {
            var fade = Math.min(1, i / 2400, (rate * burst - i) / 2400);
            data[start + i] = 0.35 * fade * (ch === 3 ? Math.sin(2 * Math.PI * 50 * i / rate) : pink());
          }
        });
      }
      return buf;
    },

    downloadSurround: async function (format, test) {
      var takeId = this.currentTakeId;
      if (!takeId) { this.showToast(t('Select a take first')); return; }
      var buttons = document.querySelectorAll('[data-surround]');
      Array.prototype.forEach.call(buttons, function (b) { b.disabled = true; });
      var work = this.pageWork(test ? t('Making the 5.1 channel test') : t('Rendering 5.1 ({format})', { format: format === 'ac3' ? 'AC-3' : 'FLAC' }));
      try {
        var wav = audioBufferToWav(test ? this.surroundTestBuffer() : await this.renderSurroundBuffer(takeId));
        var form = new FormData();
        form.append('audio_file', wav, 'surround.wav');
        var res = await fetch('/api/takes/' + takeId + '/export-surround?format=' + encodeURIComponent(format) + (test ? '&test=1' : ''),
                              { method: 'POST', body: form });
        if (!res.ok) { throw new Error(await res.text()); }
        var data = await res.json();
        var link = document.createElement('a');
        link.href = data.download_url;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        setTimeout(function () { link.remove(); }, 1000);
      } catch (err) {
        this.showToast(t('Could not make the 5.1: {message}', { message: err.message }), 'bad');
      } finally {
        Array.prototype.forEach.call(buttons, function (b) { b.disabled = false; });
        work.done();
      }
    },

    /* ------------------------------------------------------------ Space: the stage
       Seen from above, the listener in the middle facing up.  From the mix: the speakers it plays from.  From stems:
       a dot for each, dragged round the circle to place it; the wheel over a dot spreads or narrows its pair. */
    paintSpaceStage: function () {
      var svg = document.getElementById('space-stage');
      if (!svg) { return; }
      var sp = Object.assign(defaultSpace(), this.settings.space || {});
      var stems = sp.source === 'stems', player = this.stemPlayer;
      var R = 52, C = 70;
      function pt(az, r) { var a = az * Math.PI / 180; return [C + Math.sin(a) * r, C - Math.cos(a) * r]; }
      var parts = ['<circle cx="70" cy="70" r="' + R + '" class="space-ring"/>',
                   '<circle cx="70" cy="70" r="11" class="space-head"/><path d="M66 60 70 54 74 60" class="space-nose"/>'];
      if (!stems) {
        var spk = [-sp.width, sp.width], rear = Number(sp.surround) || 0;
        spk.forEach(function (az) { var q = pt(az, R); parts.push('<rect x="' + (q[0] - 5) + '" y="' + (q[1] - 5) + '" width="10" height="10" rx="2" class="space-speaker"/>'); });
        [-SPACE_REAR, SPACE_REAR].forEach(function (az) {
          var q = pt(az, R);
          parts.push('<rect x="' + (q[0] - 5) + '" y="' + (q[1] - 5) + '" width="10" height="10" rx="2" class="space-speaker" style="opacity:' + (0.15 + rear * 0.85).toFixed(2) + '"/>');
        });
      } else {
        var names = player.names.length ? player.names : ['vocals', 'drums', 'bass', 'other'];
        // each stem on a ring of its own, so stems placed alike stay apart on the drawing (it is the angle that counts)
        var step = names.length > 1 ? Math.min(10, 28 / (names.length - 1)) : 0;
        names.forEach(function (name, n) {
          var at = stemPlace(sp, name), r = R - n * step;
          var a0 = pt(at.az - at.spread / 2, r), a1 = pt(at.az + at.spread / 2, r), big = at.spread > 180 ? 1 : 0;
          if (at.spread > 0) {
            parts.push('<path d="M' + a0[0].toFixed(1) + ' ' + a0[1].toFixed(1) + ' A' + r + ' ' + r + ' 0 ' + big + ' 1 ' + a1[0].toFixed(1) + ' ' + a1[1].toFixed(1) + '" class="space-arc space-' + escHtml(name) + '"/>');
          }
          var q = pt(at.az, r);
          parts.push('<g class="space-dot space-' + escHtml(name) + '" data-stem="' + escHtml(name) + '"><circle cx="' + q[0].toFixed(1) + '" cy="' + q[1].toFixed(1) + '" r="7"/>' +
                     '<text x="' + q[0].toFixed(1) + '" y="' + (q[1] + 3).toFixed(1) + '" font-size="8">' + escHtml(name.charAt(0).toUpperCase()) + '</text><title>' + escHtml(name) + '</title></g>');
        });
      }
      svg.innerHTML = parts.join('');
      svg.classList.toggle('stems', stems);
      var unit = document.getElementById('unit-space');
      if (unit) { unit.classList.toggle('stems-mode', stems); }      // WIDTH and SURROUND are the mix's: dimmed
      var note = document.getElementById('space-stage-note');
      if (note) {
        var text = !stems ? t('From the mix') : player.loading ? t('Loading stems…') : player.error ? player.error
          : player.names.length ? t('{n} stems: drag to place, wheel to spread', { n: player.names.length }) : (this.stemsWanted() ? '' : t('Stems, when Space is in'));
        note.textContent = text;
        note.classList.toggle('bad', Boolean(stems && player.error));
      }
      var make = document.getElementById('space-make-stems');
      if (make) { make.classList.toggle('hidden', !(stems && player.error)); }
      Array.prototype.forEach.call(document.querySelectorAll('#space-source [data-source]'), function (b) {
        b.classList.toggle('active', b.dataset.source === sp.source);
      });
    },

    bindSpaceStage: function () {
      var self = this, svg = document.getElementById('space-stage');
      if (!svg) { return; }
      var dragging = null;
      function angleAt(e) {
        var box = svg.getBoundingClientRect();
        var x = (e.clientX - box.left) / box.width * 140 - 70, y = (e.clientY - box.top) / box.height * 140 - 70;
        return Math.round(Math.atan2(x, -y) * 180 / Math.PI / 5) * 5;
      }
      function stems() {
        self.settings.space = Object.assign(defaultSpace(), self.settings.space || {});
        self.settings.space.stems = Object.assign(JSON.parse(JSON.stringify(SPACE_STEMS)), self.settings.space.stems || {});
        return self.settings.space.stems;
      }
      function changed() {
        var wasOut = !(self.settings.space && self.settings.space.enabled);
        self.settings.space.enabled = true;
        Engine.applySettings(self.settings);
        self.paintSpaceStage();
        if (wasOut) { self.syncKnobsToState(); }
        self.debouncedSave();
      }
      svg.addEventListener('pointerdown', function (e) {
        var dot = e.target.closest('[data-stem]');
        if (!dot) { return; }
        dragging = dot.dataset.stem;
        svg.setPointerCapture(e.pointerId);
        e.preventDefault();
      });
      svg.addEventListener('pointermove', function (e) {
        if (!dragging) { return; }
        var all = stems();
        all[dragging] = Object.assign({}, stemPlace(self.settings.space, dragging), { az: angleAt(e) });
        changed();
      });
      svg.addEventListener('pointerup', function () { dragging = null; });
      svg.addEventListener('wheel', function (e) {
        var dot = e.target.closest('[data-stem]');
        if (!dot) { return; }
        e.preventDefault();
        var all = stems(), name = dot.dataset.stem, at = stemPlace(self.settings.space, name);
        all[name] = { az: at.az, spread: Math.max(0, Math.min(300, at.spread + (e.deltaY < 0 ? 10 : -10))) };
        changed();
      }, { passive: false });
    },

    /* A render in this browser, shown in the job pill and card like the app's own jobs (app.js pageWork), with the
       take's name; done() takes it away. */
    pageWork: function (title) {
      var label = document.getElementById('rack-take-name');
      var take = label && this.currentTakeId ? label.textContent : '';
      if (typeof window.pageWork === 'function') { return window.pageWork(title + (take ? ': ' + take : ''), t('Rendering in this browser')); }
      this.showToast(title + '…', 'good');
      return { done: function () {} };
    },

    /* The take with Space, for headphones: rendered here with every module as set, Space in, and saved as a WAV named
       after the take.  Nothing on the server changes. */
    downloadForHeadphones: async function () {
      var takeId = this.currentTakeId;
      if (!takeId) { this.showToast(t('Select a take first')); return; }
      var settings = JSON.parse(JSON.stringify(this.settings));
      settings.space = Object.assign(defaultSpace(), settings.space || {}, { enabled: true });
      settings.masterBypass = false;
      var button = document.getElementById('space-download');
      if (button) { button.disabled = true; }
      var work = this.pageWork(t('Rendering for headphones'));
      try {
        var wav = await this.renderMasterWav(takeId, settings, true);
        var label = document.getElementById('rack-take-name');
        var name = ((label && label.textContent) || 'take').replace(/[\\/:*?"<>|]+/g, ' ').trim() || 'take';
        var link = document.createElement('a');
        link.href = URL.createObjectURL(wav);
        link.download = name + ' (headphones 3D).wav';
        document.body.appendChild(link);
        link.click();
        setTimeout(function () { URL.revokeObjectURL(link.href); link.remove(); }, 2000);
      } catch (err) {
        this.showToast(t('Could not render for headphones: {message}', { message: err.message }), 'bad');
      } finally {
        if (button) { button.disabled = false; }
        work.done();
      }
    },

    renderAndDownload: async function (takeId, format, withRecipe) {
      var wavBlob = await this.renderMasterWav(takeId);
      var formData = new FormData();
      formData.append('audio_file', wavBlob, 'master.wav');
      var res = await fetch('/api/takes/' + takeId + '/export-mastered?format=' + encodeURIComponent(format) + '&prepare=1', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        throw new Error(t('Server export failed: {status}', { status: res.status }));
      }
      var data = await res.json();
      if (!data || !data.download_url) {
        throw new Error(t('Invalid export response'));
      }
      var link = document.createElement('a');
      link.href = data.download_url + (withRecipe ? '&recipe=1' : '');
      link.download = '';
      document.body.appendChild(link);
      link.click();
      setTimeout(function () {
        link.remove();
      }, 1000);
    },

    applyToTake: async function () {
      if (!this.currentTakeId) {
        this.showToast(t('Select a take first'));
        return;
      }
      var takeId = this.currentTakeId;
      if (!chainEngaged(this.settings)) {
        this.showToast(t('Nothing to apply: the rack is flat'));
        return;
      }
      var applyBtn = document.getElementById('rack-apply-take-btn');
      if (applyBtn) {
        applyBtn.disabled = true;
        applyBtn.textContent = t('Baking...');
      }
      this.showToast(t('Rendering & baking master into take...'), 'good');

      try {
        var wavBlob = await this.renderMasterWav(takeId);
        var formData = new FormData();
        formData.append('audio_file', wavBlob, 'master.wav');
        var res = await fetch('/api/takes/' + takeId + '/bake-master', {
          method: 'POST',
          body: formData
        });
        if (!res.ok) {
          var errText = await res.text();
          throw new Error(t('Failed to bake master: {errText}', { errText: errText }));
        }
        var data = await res.json();

        // Reset rack settings for this take to default transparent so it is not double-processed; Space, which
        // was not baked in, stays as it was
        var keptSpace = this.settings.space;
        this.settings = JSON.parse(JSON.stringify(PRESETS['default']));
        if (keptSpace) { this.settings.space = keptSpace; }
        this.syncKnobsToState();
        Engine.applySettings(this.settings);
        await this.flushSave();

        // Reload the takes in the library
        if (typeof window.loadTakes === 'function') {
          await window.loadTakes();
        }

        // If this take was currently playing or loaded in transport, update audio and waveform
        if (window.State && (State.playing === takeId || State.loadedId === takeId)) {
          var audio = document.getElementById('audio');
          if (audio) {
            var curTime = audio.currentTime || 0;
            var wasPlaying = !audio.paused && !audio.ended;
            var version = '?v=' + Date.now();
            var audioUrl = '/api/takes/' + takeId + '/audio' + version;
            var peaksUrl = '/api/takes/' + takeId + '/peaks' + version;
            audio.src = audioUrl;
            if (typeof loadWave === 'function') {
              loadWave(audioUrl, peaksUrl);
            }
            if (wasPlaying) {
              audio.currentTime = curTime;
              audio.play().catch(function () {});
            }
          }
        }

        this.showToast(t('Mastered audio saved permanently to take!'), 'good');
      } catch (err) {
        console.error('Bake master failed:', err);
        this.showToast(t('Could not bake master: {message}', { message: err.message }), 'bad');
      } finally {
        if (applyBtn) {
          applyBtn.disabled = false;
          applyBtn.textContent = t('Apply to Take');
        }
      }
    },

    invalidateTheme: function () {
      this._peqInk = null;
    },

    startMeterLoop: function () {
      if (this.animFrame) {
        cancelAnimationFrame(this.animFrame);
        this.animFrame = null;
      }
      var canvas = document.getElementById('vu-canvas');
      var self = this;
      var ladderLeds = null;
      var ipLed = null;
      var opLed = null;
      var tubeGlow = null;
      var timeData = null;

      function drawMeters() {
        if (!self.isOpen) {
          self.animFrame = null;
          return;
        }
        // the equaliser's screen moves only with what is heard behind its curve
        var heardNow = document.getElementById('audio');
        if (heardNow && !heardNow.paused) { self.drawPeq(); }

        // 1. Draw 1073-DPX Output Meter & Telemetry
        if (Engine.analyser) {
          var binCount = Engine.analyser.frequencyBinCount;
          if (!timeData || timeData.length !== binCount) {
            timeData = new Uint8Array(binCount);
          }
          Engine.analyser.getByteTimeDomainData(timeData);
          var maxAmp = 0;
          for (var i = 0; i < timeData.length; i++) {
            var a = Math.abs(timeData[i] - 128) / 128;
            if (a > maxAmp) { maxAmp = a; }
          }
          // Signal dB estimate (-60 to +24 dB)
          var sigDb = maxAmp > 0.001 ? 20 * Math.log10(maxAmp) + 16 : -60;

          // 7-LED ladder
          if (!ladderLeds) {
            ladderLeds = document.querySelectorAll('#dpx-led-ladder .ladder-led');
          }
          Array.prototype.forEach.call(ladderLeds, function (led) {
            var th = Number(led.dataset.db);
            led.classList.toggle('lit', sigDb >= th);
          });

          // Miniature status LEDs
          if (!ipLed) { ipLed = document.getElementById('dpx-led-ip'); }
          if (!opLed) { opLed = document.getElementById('dpx-led-op'); }
          if (ipLed) { ipLed.classList.toggle('on', maxAmp > 0.02); }
          if (opLed) { opLed.classList.toggle('on', maxAmp > 0.02 && !self.settings.masterBypass); }
        }

        // 2. Backlit Analog VU Meter for Compressor Gain Reduction
        if (canvas) {
          var ctx = canvas.getContext('2d');
          var w = canvas.width;
          var h = canvas.height;
          ctx.clearRect(0, 0, w, h);

          // Analog Backlight Background (warm amber glow)
          var grad = ctx.createRadialGradient(w / 2, h * 0.8, 10, w / 2, h * 0.8, w * 0.7);
          grad.addColorStop(0, '#ffe89e');
          grad.addColorStop(0.65, '#f5c868');
          grad.addColorStop(1, '#cca048');
          ctx.fillStyle = grad;
          ctx.fillRect(0, 0, w, h);

          // Dial Arc & Scale
          var cx = w / 2;
          var cy = h + 20;
          var r = h * 0.94;

          ctx.strokeStyle = '#2d2212';
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(cx, cy, r, -Math.PI * 0.72, -Math.PI * 0.28, false);
          ctx.stroke();

          // Tick marks & Decibel numbers
          var ticks = [
            { val: 0, label: '0', angle: -0.32 },
            { val: 1, label: '1', angle: -0.36 },
            { val: 2, label: '2', angle: -0.40 },
            { val: 3, label: '3', angle: -0.44 },
            { val: 5, label: '5', angle: -0.50 },
            { val: 7, label: '7', angle: -0.56 },
            { val: 10, label: '10', angle: -0.62 },
            { val: 20, label: '20', angle: -0.70 }
          ];

          ctx.fillStyle = '#221608';
          ctx.font = 'bold 9.5px ui-sans-serif, system-ui, sans-serif';
          ctx.textAlign = 'center';

          ticks.forEach(function (t) {
            var a = t.angle * Math.PI;
            var x1 = cx + Math.cos(a) * r;
            var y1 = cy + Math.sin(a) * r;
            var x2 = cx + Math.cos(a) * (r - 7);
            var y2 = cy + Math.sin(a) * (r - 7);
            var tx = cx + Math.cos(a) * (r - 15);
            var ty = cy + Math.sin(a) * (r - 15);

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();

            ctx.fillText(t.label, tx, ty + 3);
          });

          // Current target reduction in dB
          var targetRed = Engine.getGainReduction();
          var norm = Math.min(20, Math.max(0, targetRed)) / 20;
          var targetAngle = (-0.32 - norm * 0.38) * Math.PI;

          // Needle Physics (spring + inertia ballistics)
          var curAngle = Engine.needleVal || (-0.32 * Math.PI);
          var vel = Engine.needleVel || 0;
          var diff = targetAngle - curAngle;
          var springK = 0.28;
          var damp = 0.72;

          vel = vel * damp + diff * springK;
          curAngle += vel;
          Engine.needleVal = curAngle;
          Engine.needleVel = vel;

          // Needle Shadow
          ctx.strokeStyle = 'rgba(0,0,0,0.18)';
          ctx.lineWidth = 1.6;
          ctx.beginPath();
          ctx.moveTo(cx + 2, cy);
          ctx.lineTo(cx + Math.cos(curAngle) * (r - 3) + 2, cy + Math.sin(curAngle) * (r - 3));
          ctx.stroke();

          // Needle (Vivid red pointer)
          ctx.strokeStyle = '#c9182b';
          ctx.lineWidth = 1.4;
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.lineTo(cx + Math.cos(curAngle) * (r - 3), cy + Math.sin(curAngle) * (r - 3));
          ctx.stroke();

          // Pivot cap
          ctx.fillStyle = '#1c150c';
          ctx.beginPath();
          ctx.arc(cx, cy, 6, 0, Math.PI * 2);
          ctx.fill();
        }

        // 3. Stereo Imager Tube Filament Glow Animation
        if (!tubeGlow) { tubeGlow = document.getElementById('imager-tube-glow'); }
        if (tubeGlow && self.settings.imager) {
          var imagerActive = self.settings.imager.enabled !== false && !self.settings.masterBypass;
          var harmActive = Boolean(self.settings.imager.harmonics);
          var tubeLvl = Number(self.settings.imager.tubeHarmonics || 1);
          var baseOpa = imagerActive ? (harmActive ? 0.65 + ((tubeLvl - 1) / 8) * 0.35 : 0.28) : 0.05;
          var sigPulse = (typeof maxAmp === 'number' && maxAmp > 0.02) ? (maxAmp * 0.25) : 0;
          var finalOpa = Math.min(1.0, baseOpa + sigPulse);
          tubeGlow.style.opacity = finalOpa.toFixed(2);
        }

        self.animFrame = requestAnimationFrame(drawMeters);
      }

      drawMeters();
    },

    initDraggable: function () {
      var self = this;
      var panel = document.getElementById('rack-panel');
      var header = document.querySelector('.rack-header');
      if (!panel || !header) { return; }

      var dockBtn = document.getElementById('rack-dock-btn');

      // Restore saved floating position if any
      this.restoreFloatingPosition();

      var isDragging = false;
      var startX = 0, startY = 0;
      var initialLeft = 0, initialTop = 0;
      var width = 0;

      header.addEventListener('pointerdown', function (e) {
        if (e.button !== 0) { return; }
        // A docked rack stays where it is: Float is what lets it be moved.
        if (!panel.classList.contains('is-floating')) { return; }
        // Do not initiate drag on interactive buttons, select dropdowns, or labels
        if (e.target.closest('button, select, input, label, a, .rack-head-btn, .rack-select, .rack-preset-menu')) { return; }

        var rect = panel.getBoundingClientRect();
        startX = e.clientX;
        startY = e.clientY;
        initialLeft = rect.left;
        initialTop = rect.top;
        width = rect.width;
        isDragging = false;

        function onPointerMove(moveEvent) {
          var dx = moveEvent.clientX - startX;
          var dy = moveEvent.clientY - startY;
          if (!isDragging && Math.hypot(dx, dy) > 3) {
            isDragging = true;
            panel.classList.add('is-floating');
            panel.classList.add('is-dragging');
            self.updateDockButtonUI();
          }
          if (!isDragging) { return; }

          var newLeft = initialLeft + dx;
          var newTop = initialTop + dy;

          // Constrain within viewport bounds
          var minLeft = 8;
          var maxLeft = Math.max(minLeft, window.innerWidth - width - 8);
          var minTop = 8;
          var maxTop = Math.max(minTop, window.innerHeight - 60);

          newLeft = Math.max(minLeft, Math.min(maxLeft, newLeft));
          newTop = Math.max(minTop, Math.min(maxTop, newTop));

          panel.style.left = Math.round(newLeft) + 'px';
          panel.style.top = Math.round(newTop) + 'px';
          panel.style.bottom = 'auto';
          panel.style.right = 'auto';
          panel.style.margin = '0';
          panel.style.transform = 'none';
          panel.style.width = Math.round(width) + 'px';
        }

        function onPointerUp(upEvent) {
          try { header.releasePointerCapture(e.pointerId); } catch (err) {}
          header.removeEventListener('pointermove', onPointerMove);
          header.removeEventListener('pointerup', onPointerUp);
          header.removeEventListener('pointercancel', onPointerUp);

          if (isDragging) {
            panel.classList.remove('is-dragging');
            var curRect = panel.getBoundingClientRect();
            self.saveFloatingPosition(curRect.left, curRect.top, width);
          }
          isDragging = false;
        }

        try { header.setPointerCapture(e.pointerId); } catch (err) {}
        header.addEventListener('pointermove', onPointerMove);
        header.addEventListener('pointerup', onPointerUp);
        header.addEventListener('pointercancel', onPointerUp);
      });

      if (dockBtn) {
        dockBtn.addEventListener('click', function () {
          if (panel.classList.contains('is-floating')) {
            self.dockToBottom();
          } else {
            self.floatToCenter();
          }
        });
      }

      var fitBtn = document.getElementById('rack-fit-btn');
      if (fitBtn) {
        fitBtn.addEventListener('click', function () {
          try { localStorage.setItem('yue2.rackFit', self.fitsWindow() ? '0' : '1'); } catch (err) { /* private mode */ }
          self.fitToWindow();
        });
      }

      window.addEventListener('resize', function () {
        if (panel.classList.contains('is-floating')) {
          self.clampFloatingBounds();
        }
        self.fitToWindow();
      });
      this.fitToWindow();
    },

    /* The rack is taller than most windows.  Unless asked for at full size it is drawn smaller, by as
       much as it takes for all of it to be seen at once and no less than RACK_FLOOR, and it is given
       all the height the window has; whatever still does not fit is scrolled to.  The choice is how the
       rack is looked at, so the browser keeps it. */
    RACK_FLOOR: 0.58,
    RACK_TYPE_KEPT: 0.92,      // the share of its full size the lettering keeps in a rack drawn smaller
    RACK_TYPE_MOST: 1.45,      // and the most it is set larger by
    rackZoom: 1,
    rackType: 1,
    fitsWindow: function () {
      try { return localStorage.getItem('yue2.rackFit') !== '0'; } catch (err) { return true; }
    },
    fitToWindow: function () {
      var panel = document.getElementById('rack-panel');
      var bay = panel && panel.querySelector('.rack-bay'), header = panel && panel.querySelector('.rack-header');
      if (!panel || !bay || !header) { return; }
      var floating = panel.classList.contains('is-floating'), fits = this.fitsWindow();
      var under = floating ? 8 : (parseFloat(window.getComputedStyle(panel).bottom) || 66);
      var room = window.innerHeight - under - 8;
      var zoom = 1, type = 1;
      // The lettering is set larger by what the rack is drawn smaller, short of all of it and up to a
      // limit the panels can hold; larger lettering makes the rack a little taller, so the two are
      // worked out together, in a few rounds.  Each round measures the rack at full size.
      for (var round = 0; round < 3; round++) {
        panel.style.setProperty('--rack-zoom', '1');
        panel.style.setProperty('--rack-type', String(type));
        var needed = header.offsetHeight + bay.scrollHeight + 2;
        zoom = fits ? Math.min(1, Math.max(this.RACK_FLOOR, room / needed)) : 1;
        var wanted = Math.round(Math.min(this.RACK_TYPE_MOST, Math.max(1, this.RACK_TYPE_KEPT / zoom)) * 100) / 100;
        if (wanted === type) { break; }
        type = wanted;
      }
      this.rackType = type;
      // larger lettering needs wider rows, so the panel is let out by part of what the lettering grew
      var wide = Math.round(Math.sqrt(type) * 100) / 100;
      panel.style.setProperty('--rack-wide', String(wide));
      var self = this;
      function drawnAt(size) {
        zoom = Math.floor(size * 100) / 100;
        self.rackZoom = zoom;
        panel.style.setProperty('--rack-zoom', String(zoom));
        // lengths inside the rack are drawn at its size, so the bay's limit is given at full size
        panel.style.setProperty('--rack-bay-max', Math.max(160, Math.floor(room / zoom) - header.offsetHeight - 2) + 'px');
      }
      drawnAt(zoom);
      // Drawn smaller, hairlines stay a whole pixel and the rack comes out a little taller than its
      // share: a step or two smaller takes that up.
      for (var again = 0; again < 4 && zoom > this.RACK_FLOOR && zoom < 1 && bay.scrollHeight > bay.clientHeight + 1; again++) {
        drawnAt(Math.max(this.RACK_FLOOR, zoom * bay.clientHeight / bay.scrollHeight - 0.005));
      }
      if (floating) {
        panel.style.width = Math.round(Math.min(1240 * zoom * wide, window.innerWidth - 24)) + 'px';
        var box = panel.getBoundingClientRect();
        if (box.bottom > window.innerHeight - 8) {
          panel.style.top = Math.max(8, Math.round(window.innerHeight - 8 - box.height)) + 'px';
        }
      }
      var fitBtn = document.getElementById('rack-fit-btn');
      if (fitBtn) {
        fitBtn.textContent = fits ? t('Full size') : t('Fit');
        fitBtn.title = fits ? t('Show the rack at full size, and scroll it') : t('Fit the whole rack in the window');
      }
      this.drawPeq();
    },

    dockToBottom: function () {
      var panel = document.getElementById('rack-panel');
      if (!panel) { return; }
      panel.classList.remove('is-floating');
      panel.classList.remove('is-dragging');
      panel.style.left = '';
      panel.style.top = '';
      panel.style.bottom = '';
      panel.style.right = '';
      panel.style.margin = '';
      panel.style.transform = '';
      panel.style.width = '';
      // Where it floated is kept, marked as docked, so Float puts it back there.
      try {
        var kept = JSON.parse(localStorage.getItem('yue2.rackFloat') || 'null');
        if (kept) {
          kept.isFloating = false;
          localStorage.setItem('yue2.rackFloat', JSON.stringify(kept));
        }
      } catch (err) {}
      this.updateDockButtonUI();
      this.fitToWindow();
    },

    /* Float: back where it last floated, or, the first time, in the middle of the window by its own
       height, which is most of a window's. */
    floatToCenter: function () {
      var panel = document.getElementById('rack-panel');
      if (!panel) { return; }
      var width = Math.min(1240, window.innerWidth - 24);
      var left = Math.max(10, Math.round((window.innerWidth - width) / 2));
      var height = panel.getBoundingClientRect().height || 560;
      var top = Math.max(8, Math.round((window.innerHeight - height) / 2));
      try {
        var last = JSON.parse(localStorage.getItem('yue2.rackFloat') || 'null');
        if (last && isFinite(last.left) && isFinite(last.top)) {
          width = Math.min(last.width || width, window.innerWidth - 24);
          left = Math.max(8, Math.min(window.innerWidth - width - 8, last.left));
          top = Math.max(8, Math.min(window.innerHeight - 60, last.top));
        }
      } catch (err) {}
      panel.classList.add('is-floating');
      panel.style.left = left + 'px';
      panel.style.top = top + 'px';
      panel.style.bottom = 'auto';
      panel.style.right = 'auto';
      panel.style.margin = '0';
      panel.style.transform = 'none';
      panel.style.width = width + 'px';
      this.saveFloatingPosition(left, top, width);
      this.updateDockButtonUI();
      this.fitToWindow();
    },

    saveFloatingPosition: function (left, top, width) {
      try {
        localStorage.setItem('yue2.rackFloat', JSON.stringify({
          isFloating: true,
          left: Math.round(left),
          top: Math.round(top),
          width: Math.round(width)
        }));
      } catch (err) {}
    },

    restoreFloatingPosition: function () {
      var panel = document.getElementById('rack-panel');
      if (!panel) { return; }
      try {
        var raw = localStorage.getItem('yue2.rackFloat');
        if (!raw) {
          this.updateDockButtonUI();
          return;
        }
        var data = JSON.parse(raw);
        if (data && data.isFloating) {
          var width = Math.min(data.width || 1240, window.innerWidth - 24);
          var left = Math.max(8, Math.min(window.innerWidth - width - 8, data.left || 20));
          var top = Math.max(8, Math.min(window.innerHeight - 60, data.top || 80));
          panel.classList.add('is-floating');
          panel.style.left = left + 'px';
          panel.style.top = top + 'px';
          panel.style.bottom = 'auto';
          panel.style.right = 'auto';
          panel.style.margin = '0';
          panel.style.transform = 'none';
          panel.style.width = width + 'px';
          this.updateDockButtonUI();
        }
      } catch (err) {}
    },

    clampFloatingBounds: function () {
      var panel = document.getElementById('rack-panel');
      if (!panel || !panel.classList.contains('is-floating')) { return; }
      var rect = panel.getBoundingClientRect();
      var width = Math.min(rect.width, window.innerWidth - 16);
      var left = Math.max(8, Math.min(window.innerWidth - width - 8, rect.left));
      var top = Math.max(8, Math.min(window.innerHeight - 60, rect.top));
      panel.style.left = Math.round(left) + 'px';
      panel.style.top = Math.round(top) + 'px';
      panel.style.width = Math.round(width) + 'px';
    },

    updateDockButtonUI: function () {
      var panel = document.getElementById('rack-panel');
      var dockBtn = document.getElementById('rack-dock-btn');
      if (!dockBtn || !panel) { return; }
      var isFloating = panel.classList.contains('is-floating');
      dockBtn.textContent = isFloating ? t('Dock') : t('Float');
      dockBtn.title = isFloating ? t('Dock rack to bottom of window') : t('Float rack window, to drag it by its header');
    },

    resume: function () {
      return Engine.resume();
    }
  };

  // Expose Rack on window
  window.Rack = Rack;
  window.RackEngine = Engine;

  // Global user-gesture unlock for AudioContext
  function unlockAudio() {
    if (Engine.ctx && Engine.ctx.state === 'suspended') {
      Engine.ctx.resume().catch(function () {});
    }
  }
  window.addEventListener('click', unlockAudio, { capture: true, passive: true });
  window.addEventListener('keydown', unlockAudio, { capture: true, passive: true });
  window.addEventListener('pointerdown', unlockAudio, { capture: true, passive: true });

  window.addEventListener('beforeunload', function () {
    if (window.Rack) { window.Rack.flushSave(); }
  });

})(window, document);
