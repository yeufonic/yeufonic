/* =====================================================================
   Yeufonic Vintage Mastering Rack & Channel Strip (rack.js)
   1073 DPX Parametric EQ · 76-LN Compressor · 670 Master Limiter
   Web Audio API · Ultra-low Latency (~2.9ms) · Photorealistic Skeuomorphic UI
   ===================================================================== */

(function (window, document) {
  'use strict';

  // ------------------------------------------------------------- Defaults & Presets
  var PRESETS = {
    'default': {
      name: 'Flat / Transparent',
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
      comp: { enabled: true, threshold: -18, ratio: 4, attack: 0.015, release: 0.25, makeup: 0, mix: 1.0, knee: 10 },
      limit: { enabled: true, drive: 0, ceiling: -0.1, release: 0.08, warmth: false },
      masterBypass: false
    },
    'vintage_warmth': {
      name: 'Vintage Tube Warmth',
      eq: {
        enabled: true,
        preGain: 3,
        hp: 50,
        lowFreq: 60,
        lowGain: 3.0,
        midFreq: 700,
        midGain: 1.5,
        highGain: 1.5,
        outLevel: -0.5,
        phase: false,
        mid1Freq: 700, mid1Gain: 1.5, highFreq: 12000, airGain: 1.5
      },
      comp: { enabled: true, threshold: -20, ratio: 4, attack: 0.025, release: 0.35, makeup: 2.5, mix: 0.85, knee: 20 },
      limit: { enabled: true, drive: 1.5, ceiling: -0.2, release: 0.12, warmth: true },
      masterBypass: false
    },
    'vocal_air': {
      name: 'Vocal Air & Glue',
      eq: {
        enabled: true,
        preGain: 1,
        hp: 80,
        lowFreq: 110,
        lowGain: -1.0,
        midFreq: 3200,
        midGain: 2.5,
        highGain: 3.0,
        outLevel: 0,
        phase: false,
        mid1Freq: 3200, mid1Gain: 2.5, highFreq: 12000, airGain: 3.0
      },
      comp: { enabled: true, threshold: -22, ratio: 4, attack: 0.008, release: 0.20, makeup: 3.0, mix: 0.90, knee: 12 },
      limit: { enabled: true, drive: 1.0, ceiling: -0.1, release: 0.08, warmth: false },
      masterBypass: false
    },
    'radio_master': {
      name: 'Radio Ready Master',
      eq: {
        enabled: true,
        preGain: 2,
        hp: 50,
        lowFreq: 60,
        lowGain: 2.0,
        midFreq: 1600,
        midGain: 1.0,
        highGain: 2.0,
        outLevel: 0,
        phase: false,
        mid1Freq: 1600, mid1Gain: 1.0, highFreq: 12000, airGain: 2.0
      },
      comp: { enabled: true, threshold: -24, ratio: 8, attack: 0.010, release: 0.15, makeup: 4.0, mix: 1.0, knee: 8 },
      limit: { enabled: true, drive: 2.5, ceiling: -0.1, release: 0.06, warmth: true },
      masterBypass: false
    },
    'punchy_bass': {
      name: 'Punchy Club & Bass',
      eq: {
        enabled: true,
        preGain: 2,
        hp: 50,
        lowFreq: 60,
        lowGain: 4.5,
        midFreq: 3200,
        midGain: 2.0,
        highGain: 1.5,
        outLevel: 0,
        phase: false,
        mid1Freq: 3200, mid1Gain: 2.0, highFreq: 12000, airGain: 1.5
      },
      comp: { enabled: true, threshold: -16, ratio: 8, attack: 0.030, release: 0.12, makeup: 2.0, mix: 0.95, knee: 6 },
      limit: { enabled: true, drive: 2.0, ceiling: -0.1, release: 0.08, warmth: false },
      masterBypass: false
    },
    'acoustic_clarity': {
      name: 'Acoustic Clarity',
      eq: {
        enabled: true,
        preGain: 0,
        hp: 80,
        lowFreq: 110,
        lowGain: -1.5,
        midFreq: 4800,
        midGain: 1.5,
        highGain: 2.0,
        outLevel: 0,
        phase: false,
        mid1Freq: 4800, mid1Gain: 1.5, highFreq: 12000, airGain: 2.0
      },
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
        return false;
      }

      var ctx = this.ctx;

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

      // High Shelf (fixed 12 kHz)
      this.eqHigh = ctx.createBiquadFilter();
      this.eqHigh.type = 'highshelf';
      this.eqHigh.frequency.value = 12000;
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

      this.eqOutput.connect(this.compDryGain);
      this.eqOutput.connect(this.compressor);
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

      // 1073 EQ Stage
      if (s.eq) {
        var eqOn = s.eq.enabled !== false;

        // Preamp Gain / Drive
        var preDb = s.eq.preGain !== undefined ? Number(s.eq.preGain) : 0;
        this.inputGain.gain.setTargetAtTime(Math.pow(10, preDb / 20), now, ramp);

        // High Pass Filter (Low Cut)
        var hpVal = Number(s.eq.hp);
        if (isNaN(hpVal) || hpVal <= 20) { hpVal = 20; }
        this.eqHP.frequency.setTargetAtTime(eqOn ? hpVal : 20, now, ramp);

        // Low Shelf
        var lowF = Number(s.eq.lowFreq);
        if (isNaN(lowF) || lowF <= 0) { lowF = 60; }
        var lowG = eqOn ? (s.eq.lowGain !== undefined ? Number(s.eq.lowGain) : 0) : 0;
        this.eqLow.frequency.setTargetAtTime(lowF, now, ramp);
        this.eqLow.gain.setTargetAtTime(lowG, now, ramp);

        // Mid Band
        var midF = Number(s.eq.midFreq || s.eq.mid1Freq);
        if (isNaN(midF) || midF <= 0) { midF = 1600; }
        var midG = eqOn ? (s.eq.midGain !== undefined ? Number(s.eq.midGain) : (s.eq.mid1Gain !== undefined ? Number(s.eq.mid1Gain) : 0)) : 0;
        this.eqMid.frequency.setTargetAtTime(midF, now, ramp);
        this.eqMid.gain.setTargetAtTime(midG, now, ramp);

        // High Shelf (Fixed 12 kHz)
        var hiG = eqOn ? (s.eq.highGain !== undefined ? Number(s.eq.highGain) : (s.eq.airGain !== undefined ? Number(s.eq.airGain) : 0)) : 0;
        this.eqHigh.gain.setTargetAtTime(hiG, now, ramp);

        // Phase Invert
        var isPhaseInvert = Boolean(s.eq.phase);
        this.eqPhase.gain.setTargetAtTime(isPhaseInvert ? -1.0 : 1.0, now, ramp);

        // Output Trim
        var outDb = s.eq.outLevel !== undefined ? Number(s.eq.outLevel) : 0;
        this.eqOutput.gain.setTargetAtTime(Math.pow(10, outDb / 20), now, ramp);
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
      var red = this.compressor.reduction;
      if (typeof red === 'number') {
        return Math.abs(red);
      }
      return 0;
    }
  };

  // ------------------------------------------------------------- UI Controller
  var USER_PRESETS_KEY = 'yeufonic.mastering_user_presets';

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

    saveUserPresets: function (presets) {
      try {
        localStorage.setItem(USER_PRESETS_KEY, JSON.stringify(presets));
      } catch (e) {}
    },

    init: function () {
      this.renderMarkup();
      this.rebuildPresetDropdown('default');
      this.bindEvents();
      this.startMeterLoop();
    },

    rebuildPresetDropdown: function (selectedKey) {
      var group = document.getElementById('rack-user-presets-group');
      var delBtn = document.getElementById('rack-del-preset-btn');
      var select = document.getElementById('rack-preset-select');
      if (!group || !select) { return; }

      group.innerHTML = '';
      var userPresets = this.getUserPresets();
      var ids = Object.keys(userPresets);

      if (ids.length === 0) {
        var emptyOpt = document.createElement('option');
        emptyOpt.value = '';
        emptyOpt.disabled = true;
        emptyOpt.textContent = '(No user presets)';
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

      if (delBtn) {
        var curVal = select.value;
        delBtn.classList.toggle('hidden', !userPresets[curVal]);
      }
    },

    showToast: function (msg) {
      if (typeof window.toast === 'function') {
        window.toast(msg, 'good');
      }
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
        '            <optgroup label="Factory Presets">',
        '              <option value="default">Flat / Transparent</option>',
        '              <option value="vintage_warmth">Vintage Tube Warmth</option>',
        '              <option value="vocal_air">Vocal Air &amp; Glue</option>',
        '              <option value="radio_master">Radio Ready Master</option>',
        '              <option value="punchy_bass">Punchy Club &amp; Bass</option>',
        '              <option value="acoustic_clarity">Acoustic Clarity</option>',
        '            </optgroup>',
        '            <optgroup id="rack-user-presets-group" label="User Presets">',
        '            </optgroup>',
        '          </select>',
        '        </label>',
        '        <button type="button" class="rack-head-btn" id="rack-save-preset-btn" title="Save current settings as a user preset">+ Save Preset</button>',
        '        <button type="button" class="rack-head-btn delete-btn hidden" id="rack-del-preset-btn" title="Delete selected user preset">&times; Delete</button>',
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

        '      <!-- MODULE 1: 1073 EQUALIZER (No company name/logo) -->',
        '      <div class="rack-unit unit-eq unit-1073" id="unit-eq">',
        '        <div class="unit-bar">',
        '          <div class="unit-brand"><span class="screw-mini"></span> 1073 EQUALIZER <span class="screw-mini"></span></div>',
        '          <div class="unit-bar-right">',
        '            <button type="button" class="unit-toggle on" id="toggle-eq" title="Toggle EQ in/out"><span class="led"></span> IN</button>',
        '          </div>',
        '        </div>',
        '        <div class="unit-faceplate dpx-faceplate">',

        '          <!-- 1. Gain Knob -->',
        '          <div class="dpx-sec dpx-gain-sec">',
        '            <div class="knob-wrap marconi-wrap" data-param="eq.preGain" data-min="-15" data-max="20" data-step="1" data-default="0" data-unit="dB" title="Gain / Drive: Preamp saturation stage (-15 dB to +20 dB)">',
        '              <div class="marconi-dial red"><div class="marconi-wing"></div><div class="marconi-stripe"></div><div class="marconi-cap"></div></div>',
        '              <span class="knob-name">GAIN</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '          </div>',

        '          <!-- 2. High Shelf (12 kHz fixed) -->',
        '          <div class="dpx-sec dpx-hf-sec">',
        '            <div class="filter-symbol high-shelf" title="High Shelf: Fixed 12 kHz boost/cut">&#x2500;&#x256D;</div>',
        '            <div class="knob-wrap" data-param="eq.highGain" data-min="-16" data-max="16" data-step="0.5" data-default="0" data-unit="dB" title="High Shelf Gain: 12 kHz (&plusmn;16 dB)">',
        '              <div class="knob-dial knob-neve-grey"><div class="knob-cap"></div><div class="knob-line"></div></div>',
        '              <span class="knob-name">HIGH 12k</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '          </div>',

        '          <!-- 3. Mid Band (Stepped Frequency + Gain) -->',
        '          <div class="dpx-sec dpx-mid-sec">',
        '            <div class="filter-symbol mid-bell" title="Mid Band: Parametric bell filter">&#x2500;&#x256D;&#x256E;&#x2500;</div>',
        '            <div class="dpx-concentric-group">',
        '              <div class="knob-wrap concentric-outer" data-param="eq.midFreq" data-default="3" data-values="OFF,360,700,1600,3200,4800,7200" data-labels="OFF,0.36k,0.7k,1.6k,3.2k,4.8k,7.2k" title="Mid Frequency: Stepped bell center (OFF, 0.36k to 7.2k Hz)">',
        '                <div class="skirt-dial"><div class="skirt-ring"><div class="skirt-pointer"></div></div></div>',
        '                <span class="knob-name">FREQ</span>',
        '                <span class="knob-val">1.6 kHz</span>',
        '              </div>',
        '              <div class="knob-wrap concentric-inner" data-param="eq.midGain" data-min="-18" data-max="18" data-step="0.5" data-default="0" data-unit="dB" title="Mid Gain: Peaking boost/cut (&plusmn;18 dB)">',
        '                <div class="knob-dial knob-neve-grey small"><div class="knob-cap"></div><div class="knob-line"></div></div>',
        '                <span class="knob-name">GAIN</span>',
        '                <span class="knob-val">0 dB</span>',
        '              </div>',
        '            </div>',
        '          </div>',

        '          <!-- 4. Low Shelf (Stepped Frequency + Gain) -->',
        '          <div class="dpx-sec dpx-lf-sec">',
        '            <div class="filter-symbol low-shelf" title="Low Shelf: Low frequency shelf filter">&#x256D;&#x2500;</div>',
        '            <div class="dpx-concentric-group">',
        '              <div class="knob-wrap concentric-outer" data-param="eq.lowFreq" data-default="2" data-values="OFF,35,60,110,220" data-labels="OFF,35 Hz,60 Hz,110 Hz,220 Hz" title="Low Shelf Frequency: Stepped cutoff (OFF, 35 to 220 Hz)">',
        '                <div class="skirt-dial"><div class="skirt-ring"><div class="skirt-pointer"></div></div></div>',
        '                <span class="knob-name">FREQ</span>',
        '                <span class="knob-val">60 Hz</span>',
        '              </div>',
        '              <div class="knob-wrap concentric-inner" data-param="eq.lowGain" data-min="-16" data-max="16" data-step="0.5" data-default="0" data-unit="dB" title="Low Shelf Gain: Low boost/cut (&plusmn;16 dB)">',
        '                <div class="knob-dial knob-neve-grey small"><div class="knob-cap"></div><div class="knob-line"></div></div>',
        '                <span class="knob-name">GAIN</span>',
        '                <span class="knob-val">0 dB</span>',
        '              </div>',
        '            </div>',
        '          </div>',

        '          <!-- 5. High Pass Filter (Blue Fluted Marconi Knob) -->',
        '          <div class="dpx-sec dpx-hpf-sec">',
        '            <div class="filter-symbol hpf-symbol" title="High Pass: Low cut filter">&#x250C;&#x2500;</div>',
        '            <div class="knob-wrap marconi-wrap" data-param="eq.hp" data-default="0" data-values="20,50,80,160,300" data-labels="OFF,50 Hz,80 Hz,160 Hz,300 Hz" title="High Pass Filter: Stepped low cut (OFF, 50, 80, 160, 300 Hz)">',
        '              <div class="marconi-dial blue"><div class="marconi-wing"></div><div class="marconi-stripe"></div><div class="marconi-cap"></div></div>',
        '              <span class="knob-name">HPF</span>',
        '              <span class="knob-val">OFF</span>',
        '            </div>',
        '          </div>',

        '          <!-- 6. Chiclet Switches (Phase, EQ) -->',
        '          <div class="dpx-sec dpx-switch-sec">',
        '            <div class="dpx-chiclets vertical">',
        '              <button type="button" class="dpx-btn" id="dpx-btn-phase" title="Phase Invert (&Oslash;): Flips audio polarity 180&deg;"><span>&Oslash;</span></button>',
        '              <button type="button" class="dpx-btn active" id="dpx-btn-eq" title="EQ In/Out (EQL): Toggles 1073 equalizer circuit on/off"><span class="btn-led amber"></span><span>EQL</span></button>',
        '            </div>',
        '          </div>',

        '          <!-- 7. Output Level & 7-Segment LED Meter -->',
        '          <div class="dpx-sec dpx-output-sec">',
        '            <div class="dpx-status-leds">',
        '              <div class="status-led-item" title="Input signal detected"><span class="mini-led red" id="dpx-led-ip"></span><span class="lbl">I/P</span></div>',
        '              <div class="status-led-item" title="EQ circuit active"><span class="mini-led amber on" id="dpx-led-eq"></span><span class="lbl">EQ</span></div>',
        '              <div class="status-led-item" title="Output signal present"><span class="mini-led green on" id="dpx-led-op"></span><span class="lbl">O/P</span></div>',
        '            </div>',
        '            <div class="knob-wrap" data-param="eq.outLevel" data-min="-12" data-max="12" data-step="0.5" data-default="0" data-unit="dB" title="Output Trim: Channel level adjustment (&plusmn;12 dB)">',
        '              <div class="knob-dial knob-neve-grey small"><div class="knob-cap"></div><div class="knob-line"></div></div>',
        '              <span class="knob-name">LEVEL</span>',
        '              <span class="knob-val">0 dB</span>',
        '            </div>',
        '            <div class="dpx-ladder-wrap" title="Output Peak Meter (dB)">',
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

      // Preset Select
      var presetSelect = document.getElementById('rack-preset-select');
      var delBtn = document.getElementById('rack-del-preset-btn');
      if (presetSelect) {
        presetSelect.addEventListener('change', function () {
          var key = this.value;
          var userPresets = self.getUserPresets();
          if (PRESETS[key]) {
            self.settings = JSON.parse(JSON.stringify(PRESETS[key]));
            if (delBtn) { delBtn.classList.add('hidden'); }
          } else if (userPresets[key]) {
            self.settings = JSON.parse(JSON.stringify(userPresets[key]));
            if (delBtn) { delBtn.classList.remove('hidden'); }
          }
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
          var defaultName = 'My Preset ' + count;
          var name = null;
          if (typeof window.confirmModal === 'function') {
            name = await window.confirmModal({
              title: 'Save Preset',
              message: 'Enter a name for this custom preset:',
              input: true,
              defaultValue: defaultName,
              placeholder: 'Preset name',
              confirmText: 'Save',
              cancelText: 'Cancel'
            });
          } else {
            name = window.prompt('Enter name for your custom preset:', defaultName);
          }
          if (!name || !name.trim()) { return; }
          name = name.trim().slice(0, 40);
          var id = 'user_' + Date.now();
          var snapshot = JSON.parse(JSON.stringify(self.settings));
          snapshot.name = name;
          userPresets[id] = snapshot;
          self.saveUserPresets(userPresets);
          self.rebuildPresetDropdown(id);
          self.showToast('Saved preset "' + name + '"');
        });
      }

      // Delete Custom Preset (using app's native confirmModal)
      if (delBtn) {
        delBtn.addEventListener('click', async function () {
          if (!presetSelect) { return; }
          var key = presetSelect.value;
          var userPresets = self.getUserPresets();
          if (!userPresets[key]) { return; }
          var name = userPresets[key].name || 'preset';
          var confirmed = false;
          if (typeof window.confirmModal === 'function') {
            confirmed = await window.confirmModal({
              title: 'Delete Preset',
              message: 'Delete custom preset \u201c' + name + '\u201d?\n\nThis cannot be undone.',
              confirmText: 'Delete',
              danger: true
            });
          } else {
            confirmed = window.confirm('Delete custom preset "' + name + '"?');
          }
          if (!confirmed) { return; }
          delete userPresets[key];
          self.saveUserPresets(userPresets);
          self.rebuildPresetDropdown('default');
          self.settings = JSON.parse(JSON.stringify(PRESETS['default']));
          self.syncKnobsToState();
          Engine.applySettings(self.settings);
          self.debouncedSave();
          self.showToast('Deleted preset "' + name + '"');
        });
      }

      // Reset
      var resetBtn = document.getElementById('rack-reset-btn');
      if (resetBtn) {
        resetBtn.addEventListener('click', function () {
          self.settings = JSON.parse(JSON.stringify(PRESETS['default']));
          if (presetSelect) { presetSelect.value = 'default'; }
          if (delBtn) { delBtn.classList.add('hidden'); }
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
            self.settings.comp.knee = 0;
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

        function setParamValue(val) {
          val = Math.max(min, Math.min(max, val));
          val = Math.round(val / step) * step;

          var parts = param.split('.');
          if (parts.length === 2 && self.settings[parts[0]]) {
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
          setParamValue(def);
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

      // Update limiter toggles
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
        Engine.resume();
        this.syncKnobsToState();
      } else {
        this.flushSave();
      }
    },

    updateTakeCardsUI: function () {
      var activeTakeId = this.currentTakeId;
      var isOpen = this.isOpen;
      var cardBtns = document.querySelectorAll('button[data-act="mastering"]');
      Array.prototype.forEach.call(cardBtns, function (b) {
        var card = b.closest('.take');
        var cardId = card ? card.dataset.id : null;
        b.classList.toggle('active', Boolean(isOpen && cardId && String(cardId) === String(activeTakeId)));
      });
    },

    openForTake: function (take) {
      if (!take) { return; }
      this.flushSave();
      this.onTake(take);
      this.toggle(true);
    },

    onTake: function (take) {
      if (!take) { return; }
      this.flushSave();
      this.currentTakeId = take.id;
      var label = document.getElementById('rack-take-name');
      if (label) { label.textContent = take.title || ('Take #' + take.id); }
      this.updateTakeCardsUI();

      if (take.fx_chain) {
        try {
          var parsed = typeof take.fx_chain === 'string' ? JSON.parse(take.fx_chain) : take.fx_chain;
          if (parsed && typeof parsed === 'object') {
            this.settings = this.mergeSettings(PRESETS['default'], parsed);
            this.syncKnobsToState();
            Engine.applySettings(this.settings);
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
            self.settings = self.mergeSettings(PRESETS['default'], data);
          } else {
            self.settings = JSON.parse(JSON.stringify(PRESETS['default']));
          }
          self.syncKnobsToState();
          Engine.applySettings(self.settings);
        })
        .catch(function () {});
    },

    flushSave: function () {
      if (this.saveTimer) {
        clearTimeout(this.saveTimer);
        this.saveTimer = null;
      }
      if (!this.currentTakeId) { return; }
      var takeId = this.currentTakeId;
      var payload = JSON.stringify(this.settings);

      // Immediately keep take object in State.takes and loadedTake in-sync
      if (window.State && State.takes) {
        var t = State.takes.find(function (x) { return String(x.id) === String(takeId); });
        if (t) { t.fx_chain = payload; }
      }
      if (window.State && State.loadedTake && String(State.loadedTake.id) === String(takeId)) {
        State.loadedTake.fx_chain = payload;
      }

      fetch('/api/takes/' + takeId + '/fx', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: payload
      }).catch(function (err) {
        console.error('Failed to save mastering rack FX for take', takeId, err);
      });
    },

    debouncedSave: function () {
      var self = this;
      if (!this.currentTakeId && window.State) {
        var tid = State.playing || State.loadedId || (typeof selectedTakeId === 'function' ? selectedTakeId() : null);
        if (tid) {
          self.currentTakeId = tid;
          var tObj = (typeof takeById === 'function') ? takeById(tid) : null;
          var label = document.getElementById('rack-take-name');
          if (label && tObj) { label.textContent = tObj.title || ('Take #' + tObj.id); }
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

      if (this.saveTimer) { clearTimeout(this.saveTimer); }
      this.saveTimer = setTimeout(function () {
        self.saveTimer = null;
        fetch('/api/takes/' + takeId + '/fx', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: payload
        }).catch(function (err) {
          console.error('Failed to save mastering rack FX for take', takeId, err);
        });
      }, 350);
    },

    startMeterLoop: function () {
      var canvas = document.getElementById('vu-canvas');
      var self = this;

      function drawMeters() {
        if (!self.isOpen) {
          self.animFrame = requestAnimationFrame(drawMeters);
          return;
        }

        // 1. Draw 1073-DPX Output Meter & Telemetry
        if (Engine.analyser) {
          var timeData = new Uint8Array(Engine.analyser.frequencyBinCount);
          Engine.analyser.getByteTimeDomainData(timeData);
          var maxAmp = 0;
          for (var i = 0; i < timeData.length; i++) {
            var a = Math.abs(timeData[i] - 128) / 128;
            if (a > maxAmp) { maxAmp = a; }
          }
          // Signal dB estimate (-60 to +24 dB)
          var sigDb = maxAmp > 0.001 ? 20 * Math.log10(maxAmp) + 16 : -60;

          // 7-LED ladder
          var ladderLeds = document.querySelectorAll('#dpx-led-ladder .ladder-led');
          Array.prototype.forEach.call(ladderLeds, function (led) {
            var th = Number(led.dataset.db);
            led.classList.toggle('lit', sigDb >= th);
          });

          // Miniature status LEDs
          var ipLed = document.getElementById('dpx-led-ip');
          var opLed = document.getElementById('dpx-led-op');
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

        self.animFrame = requestAnimationFrame(drawMeters);
      }

      drawMeters();
    }
  };

  // Expose Rack on window
  window.Rack = Rack;
  window.RackEngine = Engine;

  window.addEventListener('beforeunload', function () {
    if (window.Rack) { window.Rack.flushSave(); }
  });

})(window, document);
