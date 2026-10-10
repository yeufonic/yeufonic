/* =====================================================================
   Yeufonic Vintage Mastering Rack & Channel Strip (rack.js)
   Parametric EQ · Vintage Compressor · Master Limiter
   Web Audio API · Ultra-low Latency (~2.9ms) · Photorealistic Skeuomorphic UI
   ===================================================================== */

(function (window, document) {
  'use strict';

  // ------------------------------------------------------------- Defaults & Presets
  var PRESETS = {
    'default': {
      name: 'Flat / Transparent',
      eq: { enabled: true, hp: 20, lowFreq: 60, lowGain: 0, mid1Freq: 800, mid1Gain: 0, mid1Q: 1.0, mid2Freq: 3000, mid2Gain: 0, mid2Q: 1.0, highFreq: 10000, highGain: 0, airGain: 0 },
      comp: { enabled: true, threshold: -18, ratio: 4, attack: 0.015, release: 0.25, makeup: 0, mix: 1.0, knee: 10 },
      limit: { enabled: true, drive: 0, ceiling: -0.1, release: 0.08, warmth: false },
      masterBypass: false
    },
    'vintage_warmth': {
      name: 'Vintage Tube Warmth',
      eq: { enabled: true, hp: 30, lowFreq: 60, lowGain: 3.0, mid1Freq: 650, mid1Gain: 1.5, mid1Q: 0.8, mid2Freq: 3200, mid2Gain: -1.0, mid2Q: 1.2, highFreq: 10000, highGain: 1.0, airGain: 1.5 },
      comp: { enabled: true, threshold: -20, ratio: 4, attack: 0.025, release: 0.35, makeup: 2.5, mix: 0.85, knee: 20 },
      limit: { enabled: true, drive: 1.5, ceiling: -0.2, release: 0.12, warmth: true },
      masterBypass: false
    },
    'vocal_air': {
      name: 'Vocal Air & Glue',
      eq: { enabled: true, hp: 80, lowFreq: 100, lowGain: -1.0, mid1Freq: 400, mid1Gain: -1.5, mid1Q: 1.4, mid2Freq: 3500, mid2Gain: 2.0, mid2Q: 1.0, highFreq: 12000, highGain: 2.5, airGain: 3.5 },
      comp: { enabled: true, threshold: -22, ratio: 4, attack: 0.008, release: 0.20, makeup: 3.0, mix: 0.90, knee: 12 },
      limit: { enabled: true, drive: 1.0, ceiling: -0.1, release: 0.08, warmth: false },
      masterBypass: false
    },
    'radio_master': {
      name: 'Radio Ready Master',
      eq: { enabled: true, hp: 35, lowFreq: 80, lowGain: 2.0, mid1Freq: 500, mid1Gain: -1.0, mid1Q: 1.2, mid2Freq: 2800, mid2Gain: 1.5, mid2Q: 1.0, highFreq: 8000, highGain: 2.0, airGain: 2.0 },
      comp: { enabled: true, threshold: -24, ratio: 8, attack: 0.010, release: 0.15, makeup: 4.0, mix: 1.0, knee: 8 },
      limit: { enabled: true, drive: 2.5, ceiling: -0.1, release: 0.06, warmth: true },
      masterBypass: false
    },
    'punchy_bass': {
      name: 'Punchy Club & Bass',
      eq: { enabled: true, hp: 28, lowFreq: 60, lowGain: 4.5, mid1Freq: 250, mid1Gain: -2.0, mid1Q: 1.6, mid2Freq: 4000, mid2Gain: 2.0, mid2Q: 1.1, highFreq: 10000, highGain: 1.5, airGain: 1.0 },
      comp: { enabled: true, threshold: -16, ratio: 8, attack: 0.030, release: 0.12, makeup: 2.0, mix: 0.95, knee: 6 },
      limit: { enabled: true, drive: 2.0, ceiling: -0.1, release: 0.08, warmth: false },
      masterBypass: false
    },
    'acoustic_clarity': {
      name: 'Acoustic Clarity',
      eq: { enabled: true, hp: 60, lowFreq: 120, lowGain: -1.5, mid1Freq: 350, mid1Gain: -2.0, mid1Q: 1.5, mid2Freq: 2500, mid2Gain: 1.0, mid2Q: 0.9, highFreq: 12000, highGain: 2.0, airGain: 2.5 },
      comp: { enabled: true, threshold: -18, ratio: 2, attack: 0.020, release: 0.30, makeup: 1.5, mix: 0.80, knee: 18 },
      limit: { enabled: true, drive: 0.5, ceiling: -0.2, release: 0.10, warmth: false },
      masterBypass: false
    }
  };

  // ------------------------------------------------------------- DSP Engine
  var Engine = {
    ctx: null,
    sourceNode: null,
    inputGain: null,

    // EQ
    eqHP: null,
    eqLow: null,
    eqMid1: null,
    eqMid2: null,
    eqHigh: null,
    eqAir: null,

    // Compressor
    compDryGain: null,
    compWetGain: null,
    compressor: null,
    compMakeup: null,

    // Limiter
    limitDrive: null,
    limitShaper: null,
    limiter: null,
    limitCeiling: null,

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
        // Element already hooked or invalid
        return false;
      }

      var ctx = this.ctx;

      // 1. Input Gain
      this.inputGain = ctx.createGain();
      this.inputGain.gain.value = 1.0;

      // 2. Parametric EQ chain
      this.eqHP = ctx.createBiquadFilter();
      this.eqHP.type = 'highpass';
      this.eqHP.frequency.value = 20;
      this.eqHP.Q.value = 0.707;

      this.eqLow = ctx.createBiquadFilter();
      this.eqLow.type = 'lowshelf';
      this.eqLow.frequency.value = 60;
      this.eqLow.gain.value = 0;

      this.eqMid1 = ctx.createBiquadFilter();
      this.eqMid1.type = 'peaking';
      this.eqMid1.frequency.value = 800;
      this.eqMid1.Q.value = 1.0;
      this.eqMid1.gain.value = 0;

      this.eqMid2 = ctx.createBiquadFilter();
      this.eqMid2.type = 'peaking';
      this.eqMid2.frequency.value = 3000;
      this.eqMid2.Q.value = 1.0;
      this.eqMid2.gain.value = 0;

      this.eqHigh = ctx.createBiquadFilter();
      this.eqHigh.type = 'highshelf';
      this.eqHigh.frequency.value = 10000;
      this.eqHigh.gain.value = 0;

      this.eqAir = ctx.createBiquadFilter();
      this.eqAir.type = 'peaking';
      this.eqAir.frequency.value = 12000;
      this.eqAir.Q.value = 0.7;
      this.eqAir.gain.value = 0;

      // Connect EQ chain
      this.inputGain.connect(this.eqHP);
      this.eqHP.connect(this.eqLow);
      this.eqLow.connect(this.eqMid1);
      this.eqMid1.connect(this.eqMid2);
      this.eqMid2.connect(this.eqHigh);
      this.eqHigh.connect(this.eqAir);

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

      this.eqAir.connect(this.compDryGain);
      this.eqAir.connect(this.compressor);
      this.compressor.connect(this.compMakeup);
      this.compMakeup.connect(this.compWetGain);

      var compSum = ctx.createGain();
      this.compDryGain.connect(compSum);
      this.compWetGain.connect(compSum);

      // 4. Master Limiter & Tube Warmth stage
      this.limitDrive = ctx.createGain();
      this.limitDrive.gain.value = 1.0;

      this.limitShaper = ctx.createWaveShaper();
      this.limitShaper.oversample = '4x';
      this.limitShaper.curve = this.makeLinearCurve();

      this.limiter = ctx.createDynamicsCompressor();
      this.limiter.threshold.value = -0.5;
      this.limiter.knee.value = 0.0;
      this.limiter.ratio.value = 20.0;
      this.limiter.attack.value = 0.001;
      this.limiter.release.value = 0.08;

      this.limitCeiling = ctx.createGain();
      this.limitCeiling.gain.value = Math.pow(10, -0.1 / 20); // -0.1 dB

      compSum.connect(this.limitDrive);
      this.limitDrive.connect(this.limitShaper);
      this.limitShaper.connect(this.limiter);
      this.limiter.connect(this.limitCeiling);

      // 5. Master Output / Bypass Routing
      this.masterDryGain = ctx.createGain();
      this.masterWetGain = ctx.createGain();
      this.masterDryGain.gain.value = 0.0;
      this.masterWetGain.gain.value = 1.0;

      this.analyser = ctx.createAnalyser();
      this.analyser.fftSize = 256;

      this.sourceNode.connect(this.inputGain);
      this.sourceNode.connect(this.masterDryGain);

      this.limitCeiling.connect(this.masterWetGain);

      this.masterDryGain.connect(this.analyser);
      this.masterWetGain.connect(this.analyser);
      this.analyser.connect(ctx.destination);

      return true;
    },

    makeLinearCurve: function () {
      var n = 1024;
      var curve = new Float32Array(n);
      for (var i = 0; i < n; i++) {
        var x = (i * 2) / n - 1;
        curve[i] = x;
      }
      return curve;
    },

    makeTubeCurve: function () {
      var n = 1024;
      var curve = new Float32Array(n);
      for (var i = 0; i < n; i++) {
        var x = (i * 2) / n - 1;
        // Warm asymmetrical tube curve (subtle 2nd harmonic rounding)
        if (x < -1) { curve[i] = -1; }
        else if (x > 1) { curve[i] = 1; }
        else {
          curve[i] = Math.tanh(x * 1.15) / 1.12;
        }
      }
      return curve;
    },

    resume: function () {
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume().catch(function () {});
      }
    },

    applySettings: function (s) {
      if (!this.init()) { return; }
      var ctx = this.ctx;
      var now = ctx.currentTime;
      var ramp = 0.02;

      // EQ
      if (s.eq) {
        if (s.eq.enabled === false) {
          this.eqLow.gain.setTargetAtTime(0, now, ramp);
          this.eqMid1.gain.setTargetAtTime(0, now, ramp);
          this.eqMid2.gain.setTargetAtTime(0, now, ramp);
          this.eqHigh.gain.setTargetAtTime(0, now, ramp);
          this.eqAir.gain.setTargetAtTime(0, now, ramp);
          this.eqHP.frequency.setTargetAtTime(20, now, ramp);
        } else {
          this.eqHP.frequency.setTargetAtTime(s.eq.hp || 20, now, ramp);
          this.eqLow.frequency.setTargetAtTime(s.eq.lowFreq || 60, now, ramp);
          this.eqLow.gain.setTargetAtTime(s.eq.lowGain || 0, now, ramp);
          this.eqMid1.frequency.setTargetAtTime(s.eq.mid1Freq || 800, now, ramp);
          this.eqMid1.gain.setTargetAtTime(s.eq.mid1Gain || 0, now, ramp);
          this.eqMid1.Q.setTargetAtTime(s.eq.mid1Q || 1.0, now, ramp);
          this.eqMid2.frequency.setTargetAtTime(s.eq.mid2Freq || 3000, now, ramp);
          this.eqMid2.gain.setTargetAtTime(s.eq.mid2Gain || 0, now, ramp);
          this.eqMid2.Q.setTargetAtTime(s.eq.mid2Q || 1.0, now, ramp);
          this.eqHigh.frequency.setTargetAtTime(s.eq.highFreq || 10000, now, ramp);
          this.eqHigh.gain.setTargetAtTime(s.eq.highGain || 0, now, ramp);
          this.eqAir.gain.setTargetAtTime(s.eq.airGain || 0, now, ramp);
        }
      }

      // Compressor
      if (s.comp) {
        if (s.comp.enabled === false) {
          this.compDryGain.gain.setTargetAtTime(1.0, now, ramp);
          this.compWetGain.gain.setTargetAtTime(0.0, now, ramp);
        } else {
          var mix = typeof s.comp.mix === 'number' ? s.comp.mix : 1.0;
          this.compDryGain.gain.setTargetAtTime(1.0 - mix, now, ramp);
          this.compWetGain.gain.setTargetAtTime(mix, now, ramp);
          this.compressor.threshold.setTargetAtTime(s.comp.threshold !== undefined ? s.comp.threshold : -18, now, ramp);
          this.compressor.ratio.setTargetAtTime(s.comp.ratio || 4, now, ramp);
          this.compressor.attack.setTargetAtTime(s.comp.attack || 0.015, now, ramp);
          this.compressor.release.setTargetAtTime(s.comp.release || 0.25, now, ramp);
          this.compressor.knee.setTargetAtTime(s.comp.knee !== undefined ? s.comp.knee : 10, now, ramp);
          var makeupLinear = Math.pow(10, (s.comp.makeup || 0) / 20);
          this.compMakeup.gain.setTargetAtTime(makeupLinear, now, ramp);
        }
      }

      // Limiter
      if (s.limit) {
        if (s.limit.enabled === false) {
          this.limitDrive.gain.setTargetAtTime(1.0, now, ramp);
          this.limiter.ratio.setTargetAtTime(1.0, now, ramp);
          this.limitCeiling.gain.setTargetAtTime(1.0, now, ramp);
        } else {
          var driveLin = Math.pow(10, (s.limit.drive || 0) / 20);
          this.limitDrive.gain.setTargetAtTime(driveLin, now, ramp);
          this.limiter.ratio.setTargetAtTime(20.0, now, ramp);
          this.limiter.release.setTargetAtTime(s.limit.release || 0.08, now, ramp);
          var ceilDb = s.limit.ceiling !== undefined ? s.limit.ceiling : -0.1;
          this.limitCeiling.gain.setTargetAtTime(Math.pow(10, ceilDb / 20), now, ramp);
          if (s.limit.warmth) {
            this.limitShaper.curve = this.makeTubeCurve();
          } else {
            this.limitShaper.curve = this.makeLinearCurve();
          }
        }
      }

      // Master Bypass
      if (s.masterBypass) {
        this.masterDryGain.gain.setTargetAtTime(1.0, now, ramp);
        this.masterWetGain.gain.setTargetAtTime(0.0, now, ramp);
      } else {
        this.masterDryGain.gain.setTargetAtTime(0.0, now, ramp);
        this.masterWetGain.gain.setTargetAtTime(1.0, now, ramp);
      }
    },

    getGainReduction: function () {
      if (!this.compressor) { return 0; }
      // DynamicsCompressorNode.reduction returns current reduction in negative dB
      var red = this.compressor.reduction;
      if (typeof red === 'number') {
        return Math.abs(red);
      }
      return 0;
    }
  };

  // ------------------------------------------------------------- UI Controller
  var Rack = {
    currentTakeId: null,
    settings: JSON.parse(JSON.stringify(PRESETS['default'])),
    saveTimer: null,
    isOpen: false,
    animFrame: null,

    init: function () {
      this.renderMarkup();
      this.bindEvents();
      this.startMeterLoop();
    },

    renderMarkup: function () {
      if (document.getElementById('rack-panel')) { return; }

      var html = [
        '<div id="rack-panel" class="rack-panel" role="region" aria-label="Mastering Rack">',
        '  <div class="rack-chassis">',
        '    <!-- Top Rack Header -->',
        '    <div class="rack-header">',
        '      <div class="rack-ears left"><span class="screw"></span><span class="screw"></span></div>',
        '      <div class="rack-title-block">',
        '        <span class="rack-badge">STUDIO</span>',
        '        <strong class="rack-title">VINTAGE MASTERING RACK</strong>',
        '        <span class="rack-take-label" id="rack-take-name">No take selected</span>',
        '      </div>',
        '      <div class="rack-header-tools">',
        '        <label class="rack-preset-wrap" title="Load mastering preset">',
        '          <span>PRESET:</span>',
        '          <select id="rack-preset-select" class="rack-select">',
        '            <option value="default">Flat / Transparent</option>',
        '            <option value="vintage_warmth">Vintage Tube Warmth</option>',
        '            <option value="vocal_air">Vocal Air &amp; Glue</option>',
        '            <option value="radio_master">Radio Ready Master</option>',
        '            <option value="punchy_bass">Punchy Club &amp; Bass</option>',
        '            <option value="acoustic_clarity">Acoustic Clarity</option>',
        '          </select>',
        '        </label>',
        '        <button type="button" class="rack-head-btn" id="rack-reset-btn" title="Reset all rack settings to flat">Reset</button>',
        '        <button type="button" class="rack-head-btn bypass-btn" id="rack-master-bypass" title="Toggle Master Bypass (A/B audition)">',
        '          <span class="led-dot" id="rack-master-led"></span> BYPASS',
        '        </button>',
        '        <button type="button" class="rack-head-btn close-btn" id="rack-close-btn" title="Close Rack (Esc)">&times;</button>',
        '      </div>',
        '      <div class="rack-ears right"><span class="screw"></span><span class="screw"></span></div>',
        '    </div>',

        '    <!-- Rack Modules Container -->',
        '    <div class="rack-bay">',

        '      <!-- MODULE 1: PARAMETRIC EQUALISER -->',
        '      <div class="rack-unit unit-eq" id="unit-eq">',
        '        <div class="unit-bar">',
        '          <div class="unit-brand"><span class="screw-mini"></span> 1073 PARAMETRIC EQUALISER <span class="screw-mini"></span></div>',
        '          <button type="button" class="unit-toggle on" id="toggle-eq" title="Toggle EQ on/off"><span class="led"></span> IN</button>',
        '        </div>',
        '        <div class="unit-faceplate">',
        '          <div class="knob-group">',
        '            <div class="knob-wrap" data-param="eq.hp" data-min="20" data-max="300" data-step="5" data-default="20" data-unit="Hz">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">LOW CUT</span>',
        '              <span class="knob-val">20 Hz</span>',
        '            </div>',
        '          </div>',
        '          <div class="knob-group separator">',
        '            <div class="knob-wrap" data-param="eq.lowFreq" data-min="30" data-max="400" data-step="10" data-default="60" data-unit="Hz">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">LOW FREQ</span>',
        '              <span class="knob-val">60 Hz</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="eq.lowGain" data-min="-15" data-max="15" data-step="0.5" data-default="0" data-unit="dB">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">LOW GAIN</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '          </div>',
        '          <div class="knob-group separator">',
        '            <div class="knob-wrap" data-param="eq.mid1Freq" data-min="200" data-max="2500" data-step="25" data-default="800" data-unit="Hz">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">LO-MID</span>',
        '              <span class="knob-val">800 Hz</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="eq.mid1Gain" data-min="-15" data-max="15" data-step="0.5" data-default="0" data-unit="dB">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">GAIN</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="eq.mid1Q" data-min="0.5" data-max="4.0" data-step="0.1" data-default="1.0" data-unit="Q">',
        '              <div class="knob-dial small"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">Q</span>',
        '              <span class="knob-val">1.0</span>',
        '            </div>',
        '          </div>',
        '          <div class="knob-group separator">',
        '            <div class="knob-wrap" data-param="eq.mid2Freq" data-min="1000" data-max="8000" data-step="50" data-default="3000" data-unit="Hz">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">HI-MID</span>',
        '              <span class="knob-val">3000 Hz</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="eq.mid2Gain" data-min="-15" data-max="15" data-step="0.5" data-default="0" data-unit="dB">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">GAIN</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="eq.mid2Q" data-min="0.5" data-max="4.0" data-step="0.1" data-default="1.0" data-unit="Q">',
        '              <div class="knob-dial small"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">Q</span>',
        '              <span class="knob-val">1.0</span>',
        '            </div>',
        '          </div>',
        '          <div class="knob-group separator">',
        '            <div class="knob-wrap" data-param="eq.highGain" data-min="-15" data-max="15" data-step="0.5" data-default="0" data-unit="dB">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">HIGH 10k</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="eq.airGain" data-min="-10" data-max="12" data-step="0.5" data-default="0" data-unit="dB">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">AIR 12k</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '          </div>',
        '        </div>',
        '      </div>',

        '      <!-- MODULE 2: PEAK LIMITING AMPLIFIER -->',
        '      <div class="rack-unit unit-comp" id="unit-comp">',
        '        <div class="unit-bar">',
        '          <div class="unit-brand"><span class="screw-mini"></span> 76-LN PEAK LIMITING AMPLIFIER <span class="screw-mini"></span></div>',
        '          <button type="button" class="unit-toggle on" id="toggle-comp" title="Toggle Compressor on/off"><span class="led"></span> IN</button>',
        '        </div>',
        '        <div class="unit-faceplate">',
        '          <div class="knob-group">',
        '            <div class="knob-wrap" data-param="comp.threshold" data-min="-45" data-max="0" data-step="1" data-default="-18" data-unit="dB">',
        '              <div class="knob-dial large"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">THRESHOLD</span>',
        '              <span class="knob-val">-18 dB</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="comp.makeup" data-min="-6" data-max="20" data-step="0.5" data-default="0" data-unit="dB">',
        '              <div class="knob-dial large"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">OUTPUT</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '          </div>',

        '          <!-- Backlit Analog VU Meter -->',
        '          <div class="vu-meter-box" title="Analog Gain Reduction (dB)">',
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

        '      <!-- MODULE 3: MASTER LIMITER -->',
        '      <div class="rack-unit unit-limit" id="unit-limit">',
        '        <div class="unit-bar">',
        '          <div class="unit-brand"><span class="screw-mini"></span> 670 VARIABLE-MU MASTER LIMITER <span class="screw-mini"></span></div>',
        '          <button type="button" class="unit-toggle on" id="toggle-limit" title="Toggle Limiter on/off"><span class="led"></span> IN</button>',
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
        '            <button type="button" class="switch-toggle" id="toggle-warmth" title="Toggle Analog Tube Saturation">',
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

      // Presets
      var presetSelect = document.getElementById('rack-preset-select');
      if (presetSelect) {
        presetSelect.addEventListener('change', function () {
          var key = this.value;
          if (PRESETS[key]) {
            self.settings = JSON.parse(JSON.stringify(PRESETS[key]));
            self.syncKnobsToState();
            Engine.applySettings(self.settings);
            self.debouncedSave();
          }
        });
      }

      // Reset
      var resetBtn = document.getElementById('rack-reset-btn');
      if (resetBtn) {
        resetBtn.addEventListener('click', function () {
          self.settings = JSON.parse(JSON.stringify(PRESETS['default']));
          presetSelect.value = 'default';
          self.syncKnobsToState();
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      // Module In/Out toggles
      var toggleEq = document.getElementById('toggle-eq');
      if (toggleEq) {
        toggleEq.addEventListener('click', function () {
          self.settings.eq.enabled = !self.settings.eq.enabled;
          this.classList.toggle('on', self.settings.eq.enabled);
          this.innerHTML = '<span class="led"></span> ' + (self.settings.eq.enabled ? 'IN' : 'OUT');
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

      // Tube Warmth switch
      var toggleWarmth = document.getElementById('toggle-warmth');
      var warmthStatus = document.getElementById('warmth-status');
      if (toggleWarmth) {
        toggleWarmth.addEventListener('click', function () {
          self.settings.limit.warmth = !self.settings.limit.warmth;
          this.classList.toggle('on', self.settings.limit.warmth);
          if (warmthStatus) {
            warmthStatus.textContent = self.settings.limit.warmth ? 'TUBE ON' : 'OFF';
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
            self.settings.comp.knee = 0; // Hard limiting British mode
          } else {
            self.settings.comp.ratio = Number(r) || 4;
            self.settings.comp.knee = 10;
          }
          Engine.applySettings(self.settings);
          self.debouncedSave();
        });
      }

      // Setup Rotary Knobs
      this.bindKnobs();

      // Keyboard Esc to close
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && self.isOpen) {
          self.toggle(false);
        }
      });
    },

    bindKnobs: function () {
      var self = this;
      var knobWraps = document.querySelectorAll('.knob-wrap');

      Array.prototype.forEach.call(knobWraps, function (wrap) {
        var dial = wrap.querySelector('.knob-dial');
        var valLabel = wrap.querySelector('.knob-val');
        var param = wrap.dataset.param;
        var min = Number(wrap.dataset.min);
        var max = Number(wrap.dataset.max);
        var step = Number(wrap.dataset.step) || 1;
        var def = Number(wrap.dataset.default);
        var unit = wrap.dataset.unit || '';
        var display = wrap.dataset.display || '';

        var isDragging = false;
        var startY = 0;
        var startVal = def;

        function updateKnobDisplay(val) {
          // Normalise to 0..1
          var norm = (val - min) / (max - min);
          norm = Math.max(0, Math.min(1, norm));
          // Rotate from -135deg to +135deg (270deg range)
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

        function setParamValue(val) {
          val = Math.max(min, Math.min(max, val));
          val = Math.round(val / step) * step;

          // Set in settings object (supports path like 'eq.hp')
          var parts = param.split('.');
          if (parts.length === 2 && self.settings[parts[0]]) {
            self.settings[parts[0]][parts[1]] = val;
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
          startVal = (parts.length === 2 && self.settings[parts[0]]) ? Number(self.settings[parts[0]][parts[1]]) : def;

          document.body.classList.add('knob-dragging');

          function onMouseMove(moveEvent) {
            if (!isDragging) { return; }
            var deltaY = startY - moveEvent.clientY;
            // 200px drag = full range (shift for fine control)
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
          var curVal = (parts.length === 2 && self.settings[parts[0]]) ? Number(self.settings[parts[0]][parts[1]]) : def;
          var direction = e.deltaY < 0 ? 1 : -1;
          setParamValue(curVal + direction * step * (e.shiftKey ? 0.2 : 1.0));
        }, { passive: false });

        // Double-click to reset to default
        dial.addEventListener('dblclick', function (e) {
          e.preventDefault();
          setParamValue(def);
        });
      });
    },

    syncKnobsToState: function () {
      var self = this;
      var knobWraps = document.querySelectorAll('.knob-wrap');
      Array.prototype.forEach.call(knobWraps, function (wrap) {
        var param = wrap.dataset.param;
        var parts = param.split('.');
        if (parts.length === 2 && self.settings[parts[0]] && self.settings[parts[0]][parts[1]] !== undefined) {
          var val = Number(self.settings[parts[0]][parts[1]]);
          if (wrap._updateDisplay) { wrap._updateDisplay(val); }
        }
      });

      // Update toggles
      var toggleEq = document.getElementById('toggle-eq');
      if (toggleEq) {
        var eqOn = self.settings.eq ? self.settings.eq.enabled !== false : true;
        toggleEq.classList.toggle('on', eqOn);
        toggleEq.innerHTML = '<span class="led"></span> ' + (eqOn ? 'IN' : 'OUT');
      }

      var toggleComp = document.getElementById('toggle-comp');
      if (toggleComp) {
        var compOn = self.settings.comp ? self.settings.comp.enabled !== false : true;
        toggleComp.classList.toggle('on', compOn);
        toggleComp.innerHTML = '<span class="led"></span> ' + (compOn ? 'IN' : 'OUT');
      }

      var toggleLimit = document.getElementById('toggle-limit');
      if (toggleLimit) {
        var limOn = self.settings.limit ? self.settings.limit.enabled !== false : true;
        toggleLimit.classList.toggle('on', limOn);
        toggleLimit.innerHTML = '<span class="led"></span> ' + (limOn ? 'IN' : 'OUT');
      }

      var toggleWarmth = document.getElementById('toggle-warmth');
      var warmthStatus = document.getElementById('warmth-status');
      if (toggleWarmth && self.settings.limit) {
        var warm = Boolean(self.settings.limit.warmth);
        toggleWarmth.classList.toggle('on', warm);
        if (warmthStatus) {
          warmthStatus.textContent = warm ? 'TUBE ON' : 'OFF';
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

      this.updateBypassUI();
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

    toggle: function (force) {
      var panel = document.getElementById('rack-panel');
      if (!panel) { return; }
      this.isOpen = (typeof force === 'boolean') ? force : !panel.classList.contains('is-open');
      panel.classList.toggle('is-open', this.isOpen);

      var btn = document.getElementById('btn-fx-rack');
      if (btn) { btn.classList.toggle('active', this.isOpen); }

      if (this.isOpen) {
        Engine.resume();
        this.syncKnobsToState();
      }
    },

    onTake: function (take) {
      if (!take) { return; }
      this.currentTakeId = take.id;
      var label = document.getElementById('rack-take-name');
      if (label) { label.textContent = take.title || ('Take #' + take.id); }

      if (take.fx_chain) {
        try {
          var parsed = typeof take.fx_chain === 'string' ? JSON.parse(take.fx_chain) : take.fx_chain;
          if (parsed && typeof parsed === 'object') {
            this.settings = Object.assign({}, PRESETS['default'], parsed);
            this.syncKnobsToState();
            Engine.applySettings(this.settings);
            return;
          }
        } catch (e) {}
      }

      // Fetch from API if not embedded
      var self = this;
      fetch('/api/takes/' + take.id + '/fx')
        .then(function (res) { return res.ok ? res.json() : {}; })
        .then(function (data) {
          if (self.currentTakeId !== take.id) { return; }
          if (data && Object.keys(data).length > 0) {
            self.settings = Object.assign({}, PRESETS['default'], data);
          } else {
            self.settings = JSON.parse(JSON.stringify(PRESETS['default']));
          }
          self.syncKnobsToState();
          Engine.applySettings(self.settings);
        })
        .catch(function () {});
    },

    debouncedSave: function () {
      var self = this;
      if (!this.currentTakeId) { return; }
      if (this.saveTimer) { clearTimeout(this.saveTimer); }
      this.saveTimer = setTimeout(function () {
        if (!self.currentTakeId) { return; }
        fetch('/api/takes/' + self.currentTakeId + '/fx', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(self.settings)
        }).catch(function () {});
      }, 350);
    },

    startMeterLoop: function () {
      var canvas = document.getElementById('vu-canvas');
      if (!canvas) { return; }
      var ctx = canvas.getContext('2d');
      var self = this;

      function drawMeter() {
        if (!self.isOpen) {
          self.animFrame = requestAnimationFrame(drawMeter);
          return;
        }

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
        // Scale arc from -45deg to +45deg
        ctx.arc(cx, cy, r, -Math.PI * 0.72, -Math.PI * 0.28, false);
        ctx.stroke();

        // Tick marks & Decibel numbers
        // 0dB at center-right, -20dB at far left
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
        // Target angle interpolation
        var norm = Math.min(20, Math.max(0, targetRed)) / 20;
        // 0 dB -> angle -0.32PI, 20 dB -> angle -0.70PI
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

        // Draw Needle Shadow
        ctx.strokeStyle = 'rgba(0,0,0,0.18)';
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(cx + 2, cy);
        ctx.lineTo(cx + Math.cos(curAngle) * (r - 3) + 2, cy + Math.sin(curAngle) * (r - 3));
        ctx.stroke();

        // Draw Needle (Classic vivid red pointer)
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

        self.animFrame = requestAnimationFrame(drawMeter);
      }

      drawMeter();
    }
  };

  // Expose Rack on window
  window.Rack = Rack;
  window.RackEngine = Engine;

})(window, document);
