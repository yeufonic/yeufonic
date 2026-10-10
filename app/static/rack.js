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
      imager: { enabled: true, bigness: 1, range: 5, stage: 5, harmonics: false, tubeHarmonics: 1, bass: false },
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
      imager: { enabled: true, bigness: 3, range: 6, stage: 6, harmonics: true, tubeHarmonics: 4, bass: true },
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
      imager: { enabled: true, bigness: 2, range: 2, stage: 7, harmonics: false, tubeHarmonics: 1, bass: false },
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
      imager: { enabled: true, bigness: 4, range: 5, stage: 6, harmonics: true, tubeHarmonics: 3, bass: true },
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
      imager: { enabled: true, bigness: 3, range: 5, stage: 5, harmonics: false, tubeHarmonics: 2, bass: true },
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
      imager: { enabled: true, bigness: 2, range: 4, stage: 6, harmonics: false, tubeHarmonics: 1, bass: false },
      limit: { enabled: true, drive: 0.5, ceiling: -0.2, release: 0.10, warmth: false },
      masterBypass: false
    }
  };

  // ------------------------------------------------------------- DSP Helpers & Waveshapers
  function makeLinearCurve() {
    var n = 1024;
    var curve = new Float32Array(n);
    for (var i = 0; i < n; i++) {
      curve[i] = (i * 2) / n - 1;
    }
    return curve;
  }

  function makeTubeCurve() {
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

  function buildMasteringDspGraph(ctx, s) {
    s = s || PRESETS['default'];

    // 1. Input Gain
    var inputGain = ctx.createGain();
    var preDb = (s.eq && s.eq.preGain !== undefined) ? Number(s.eq.preGain) : 0;
    inputGain.gain.value = Math.pow(10, preDb / 20);

    // 2. 1073 Parametric EQ chain
    var eqOn = s.eq && s.eq.enabled !== false;
    var eqHP = ctx.createBiquadFilter();
    eqHP.type = 'highpass';
    var hpVal = Number(s.eq && s.eq.hp);
    if (isNaN(hpVal) || hpVal <= 20) { hpVal = 20; }
    eqHP.frequency.value = eqOn ? hpVal : 20;
    eqHP.Q.value = 0.707;

    var eqLow = ctx.createBiquadFilter();
    eqLow.type = 'lowshelf';
    var lowF = Number(s.eq && s.eq.lowFreq);
    if (isNaN(lowF) || lowF <= 0) { lowF = 60; }
    eqLow.frequency.value = lowF;
    eqLow.gain.value = eqOn ? (s.eq && s.eq.lowGain !== undefined ? Number(s.eq.lowGain) : 0) : 0;

    var eqMid = ctx.createBiquadFilter();
    eqMid.type = 'peaking';
    var midF = Number(s.eq && (s.eq.midFreq || s.eq.mid1Freq));
    if (isNaN(midF) || midF <= 0) { midF = 1600; }
    eqMid.frequency.value = midF;
    eqMid.Q.value = 1.1;
    eqMid.gain.value = eqOn ? (s.eq && s.eq.midGain !== undefined ? Number(s.eq.midGain) : (s.eq && s.eq.mid1Gain !== undefined ? Number(s.eq.mid1Gain) : 0)) : 0;

    var eqHigh = ctx.createBiquadFilter();
    eqHigh.type = 'highshelf';
    eqHigh.frequency.value = 6800;
    eqHigh.gain.value = eqOn ? (s.eq && s.eq.highGain !== undefined ? Number(s.eq.highGain) : (s.eq && s.eq.airGain !== undefined ? Number(s.eq.airGain) : 0)) : 0;

    var eqPhase = ctx.createGain();
    eqPhase.gain.value = (s.eq && s.eq.phase) ? -1.0 : 1.0;

    var eqOutput = ctx.createGain();
    var outDb = (s.eq && s.eq.outLevel !== undefined) ? Number(s.eq.outLevel) : 0;
    eqOutput.gain.value = Math.pow(10, outDb / 20);

    inputGain.connect(eqHP);
    eqHP.connect(eqLow);
    eqLow.connect(eqMid);
    eqMid.connect(eqHigh);
    eqHigh.connect(eqPhase);
    eqPhase.connect(eqOutput);

    // 3. Vintage Compressor stage with parallel blend
    var compDryGain = ctx.createGain();
    var compWetGain = ctx.createGain();
    var compressor = ctx.createDynamicsCompressor();
    var compMakeup = ctx.createGain();
    var compSum = ctx.createGain();

    var compOn = s.comp && s.comp.enabled !== false;
    if (!compOn) {
      compDryGain.gain.value = 1.0;
      compWetGain.gain.value = 0.0;
    } else {
      var mix = (s.comp && typeof s.comp.mix === 'number') ? s.comp.mix : 1.0;
      compDryGain.gain.value = 1.0 - mix;
      compWetGain.gain.value = mix;
      compressor.threshold.value = (s.comp && s.comp.threshold !== undefined) ? s.comp.threshold : -18;
      compressor.ratio.value = (s.comp && s.comp.ratio) || 4;
      compressor.attack.value = (s.comp && s.comp.attack) || 0.015;
      compressor.release.value = (s.comp && s.comp.release) || 0.25;
      compressor.knee.value = (s.comp && s.comp.knee !== undefined) ? s.comp.knee : 10;
      compMakeup.gain.value = Math.pow(10, ((s.comp && s.comp.makeup) || 0) / 20);
    }

    eqOutput.connect(compDryGain);
    eqOutput.connect(compressor);
    compressor.connect(compMakeup);
    compMakeup.connect(compWetGain);
    compDryGain.connect(compSum);
    compWetGain.connect(compSum);

    // 4. Vintage Stereo Imager & Spatial Processor stage
    var imagerDryGain = ctx.createGain();
    var imagerWetGain = ctx.createGain();
    var imagerSplitter = ctx.createChannelSplitter(2);
    var lToM = ctx.createGain(); lToM.gain.value = 0.5;
    var rToM = ctx.createGain(); rToM.gain.value = 0.5;
    var imagerMidBus = ctx.createGain();
    var imagerBassFilter = ctx.createBiquadFilter();
    imagerBassFilter.type = 'lowshelf';
    imagerBassFilter.frequency.value = 85;

    var lToS = ctx.createGain(); lToS.gain.value = 0.5;
    var rToS = ctx.createGain(); rToS.gain.value = -0.5;
    var imagerSideBus = ctx.createGain();
    var imagerSideHP = ctx.createBiquadFilter();
    imagerSideHP.type = 'highpass';
    imagerSideHP.frequency.value = 90;
    imagerSideHP.Q.value = 0.707;

    var imagerRangeFilter = ctx.createBiquadFilter();
    imagerRangeFilter.type = 'highpass';
    imagerRangeFilter.Q.value = 0.707;

    var imagerStageFilter = ctx.createBiquadFilter();
    imagerStageFilter.type = 'allpass';

    var imagerWidthGain = ctx.createGain();
    var imagerHarmonicsDrive = ctx.createGain();
    var imagerShaper = ctx.createWaveShaper();
    imagerShaper.oversample = '4x';

    var midToL = ctx.createGain(); midToL.gain.value = 1.0;
    var midToR = ctx.createGain(); midToR.gain.value = 1.0;
    var sideToL = ctx.createGain(); sideToL.gain.value = 1.0;
    var sideToR = ctx.createGain(); sideToR.gain.value = -1.0;
    var imagerMerger = ctx.createChannelMerger(2);
    var imagerSum = ctx.createGain();

    var imagerOn = s.imager && s.imager.enabled !== false;
    if (!imagerOn) {
      imagerDryGain.gain.value = 1.0;
      imagerWetGain.gain.value = 0.0;
    } else {
      imagerDryGain.gain.value = 0.0;
      imagerWetGain.gain.value = 1.0;

      var rangeVal = Number(s.imager && s.imager.range);
      if (isNaN(rangeVal) || rangeVal < 1) { rangeVal = 5; }
      var rangeNorm = (rangeVal - 1) / 8;
      imagerRangeFilter.frequency.value = 2800 * Math.pow(180 / 2800, rangeNorm);

      var stageVal = Number(s.imager && s.imager.stage);
      if (isNaN(stageVal) || stageVal < 1) { stageVal = 5; }
      var stageNorm = (stageVal - 1) / 8;
      imagerStageFilter.frequency.value = 350 * Math.pow(3200 / 350, stageNorm);

      var bignessVal = Number(s.imager && s.imager.bigness);
      if (isNaN(bignessVal) || bignessVal < 0) { bignessVal = 1; }
      imagerWidthGain.gain.value = (bignessVal <= 1) ? bignessVal : (1.0 + ((bignessVal - 1) / 8) * 1.4);

      imagerBassFilter.gain.value = (s.imager && s.imager.bass) ? 3.0 : 0.0;

      var harmOn = Boolean(s.imager && s.imager.harmonics);
      var tubeH = Number(s.imager && s.imager.tubeHarmonics);
      if (isNaN(tubeH) || tubeH < 1) { tubeH = 1; }
      if (harmOn) {
        imagerHarmonicsDrive.gain.value = 1.0 + ((tubeH - 1) / 8) * 0.8;
        imagerShaper.curve = makeTubeCurve();
      } else {
        imagerHarmonicsDrive.gain.value = 1.0;
        imagerShaper.curve = makeLinearCurve();
      }
    }

    compSum.connect(imagerDryGain);
    imagerDryGain.connect(imagerSum);

    compSum.connect(imagerSplitter);
    imagerSplitter.connect(lToM, 0);
    imagerSplitter.connect(rToM, 1);
    lToM.connect(imagerMidBus);
    rToM.connect(imagerMidBus);
    imagerMidBus.connect(imagerBassFilter);

    imagerSplitter.connect(lToS, 0);
    imagerSplitter.connect(rToS, 1);
    lToS.connect(imagerSideBus);
    rToS.connect(imagerSideBus);
    imagerSideBus.connect(imagerSideHP);
    imagerSideHP.connect(imagerRangeFilter);
    imagerRangeFilter.connect(imagerStageFilter);
    imagerStageFilter.connect(imagerWidthGain);

    imagerBassFilter.connect(midToL);
    imagerBassFilter.connect(midToR);
    imagerWidthGain.connect(sideToL);
    imagerWidthGain.connect(sideToR);

    midToL.connect(imagerMerger, 0, 0);
    sideToL.connect(imagerMerger, 0, 0);
    midToR.connect(imagerMerger, 0, 1);
    sideToR.connect(imagerMerger, 0, 1);

    imagerMerger.connect(imagerHarmonicsDrive);
    imagerHarmonicsDrive.connect(imagerShaper);
    imagerShaper.connect(imagerWetGain);
    imagerWetGain.connect(imagerSum);

    // 5. Master Limiter & Tube Warmth stage
    var limitDrive = ctx.createGain();
    var limitShaper = ctx.createWaveShaper();
    limitShaper.oversample = '4x';
    var limiter = ctx.createDynamicsCompressor();
    var limitCeiling = ctx.createGain();

    var limitOn = s.limit && s.limit.enabled !== false;
    if (!limitOn) {
      limitDrive.gain.value = 1.0;
      limitShaper.curve = makeLinearCurve();
      limiter.ratio.value = 1.0;
      limitCeiling.gain.value = 1.0;
    } else {
      var driveLin = Math.pow(10, ((s.limit && s.limit.drive) || 0) / 20);
      limitDrive.gain.value = driveLin;
      limiter.threshold.value = -0.5;
      limiter.knee.value = 0.0;
      limiter.ratio.value = 20.0;
      limiter.attack.value = 0.001;
      limiter.release.value = (s.limit && s.limit.release) || 0.08;
      var ceilDb = (s.limit && s.limit.ceiling !== undefined) ? s.limit.ceiling : -0.1;
      limitCeiling.gain.value = Math.pow(10, ceilDb / 20);
      limitShaper.curve = (s.limit && s.limit.warmth) ? makeTubeCurve() : makeLinearCurve();
    }

    imagerSum.connect(limitDrive);
    limitDrive.connect(limitShaper);
    limitShaper.connect(limiter);
    limiter.connect(limitCeiling);

    // 6. Master Output / Bypass Routing
    var masterDryGain = ctx.createGain();
    var masterWetGain = ctx.createGain();
    var masterOut = ctx.createGain();

    var isBypassed = Boolean(s.masterBypass);
    masterDryGain.gain.value = isBypassed ? 1.0 : 0.0;
    masterWetGain.gain.value = isBypassed ? 0.0 : 1.0;

    inputGain.connect(masterDryGain);
    limitCeiling.connect(masterWetGain);

    masterDryGain.connect(masterOut);
    masterWetGain.connect(masterOut);

    return {
      inputNode: inputGain,
      outputNode: masterOut
    };
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
    compDryGain: null,
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
    imagerMerger: null,

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

      var self = this;
      audioEl.addEventListener('play', function () {
        self.resume();
      });

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

      this.eqOutput.connect(this.compDryGain);
      this.eqOutput.connect(this.compressor);
      this.compressor.connect(this.compMakeup);
      this.compMakeup.connect(this.compWetGain);

      var compSum = ctx.createGain();
      this.compDryGain.connect(compSum);
      this.compWetGain.connect(compSum);

      // 4. Vintage Stereo Imager & Spatial Processor stage
      this.imagerDryGain = ctx.createGain();
      this.imagerWetGain = ctx.createGain();
      this.imagerDryGain.gain.value = 0.0;
      this.imagerWetGain.gain.value = 1.0;

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
      this.imagerShaper.curve = this.makeLinearCurve();

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
      this.imagerHarmonicsDrive.connect(this.imagerShaper);
      this.imagerShaper.connect(this.imagerWetGain);

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
      this.limitShaper.curve = this.makeLinearCurve();

      this.limiter = ctx.createDynamicsCompressor();
      this.limiter.threshold.value = -0.5;
      this.limiter.knee.value = 0.0;
      this.limiter.ratio.value = 20.0;
      this.limiter.attack.value = 0.001;
      this.limiter.release.value = 0.08;

      this.limitCeiling = ctx.createGain();
      this.limitCeiling.gain.value = Math.pow(10, -0.1 / 20); // -0.1 dB

      imagerSum.connect(this.limitDrive);
      this.limitDrive.connect(this.limitShaper);
      this.limitShaper.connect(this.limiter);
      this.limiter.connect(this.limitCeiling);

      // 6. Master Output / Bypass Routing
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
      return makeLinearCurve();
    },

    makeTubeCurve: function () {
      return makeTubeCurve();
    },

    resume: function () {
      if (this.ctx && this.ctx.state === 'suspended') {
        return this.ctx.resume().catch(function () {});
      }
      return Promise.resolve();
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

        // High Shelf (Fixed 12 kHz analog-modeled corner)
        var hiG = eqOn ? (s.eq.highGain !== undefined ? Number(s.eq.highGain) : (s.eq.airGain !== undefined ? Number(s.eq.airGain) : 0)) : 0;
        this.eqHigh.frequency.setTargetAtTime(6800, now, ramp);
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

      // Vintage Stereo Imager Stage (Placed before Master Limiter)
      if (s.imager) {
        if (s.imager.enabled === false) {
          this.imagerDryGain.gain.setTargetAtTime(1.0, now, ramp);
          this.imagerWetGain.gain.setTargetAtTime(0.0, now, ramp);
        } else {
          this.imagerDryGain.gain.setTargetAtTime(0.0, now, ramp);
          this.imagerWetGain.gain.setTargetAtTime(1.0, now, ramp);

          // Range knob: 1 ("HIGH", 2800 Hz) to 9 ("OPEN", 180 Hz)
          var rangeVal = Number(s.imager.range);
          if (isNaN(rangeVal) || rangeVal < 1) { rangeVal = 5; }
          var rangeNorm = (rangeVal - 1) / 8;
          var rangeHz = 2800 * Math.pow(180 / 2800, rangeNorm);
          this.imagerRangeFilter.frequency.setTargetAtTime(rangeHz, now, ramp);

          // Stage knob: 1 ("BACK", 350 Hz) to 9 ("FRONT", 3200 Hz)
          var stageVal = Number(s.imager.stage);
          if (isNaN(stageVal) || stageVal < 1) { stageVal = 5; }
          var stageNorm = (stageVal - 1) / 8;
          var stageHz = 350 * Math.pow(3200 / 350, stageNorm);
          this.imagerStageFilter.frequency.setTargetAtTime(stageHz, now, ramp);

          // Bigness knob: 1 ("MIN", 1.0x width) to 9 ("MAX", 2.4x width)
          var bignessVal = Number(s.imager.bigness);
          if (isNaN(bignessVal) || bignessVal < 0) { bignessVal = 1; }
          var widthFactor = (bignessVal <= 1) ? bignessVal : (1.0 + ((bignessVal - 1) / 8) * 1.4);
          this.imagerWidthGain.gain.setTargetAtTime(widthFactor, now, ramp);

          // Bass punch circuit: +3.0 dB low shelf at 85 Hz
          var bassOn = Boolean(s.imager.bass);
          this.imagerBassFilter.gain.setTargetAtTime(bassOn ? 3.0 : 0.0, now, ramp);

          // Harmonics toggle & Tube Harmonics drive
          var harmOn = Boolean(s.imager.harmonics);
          var tubeH = Number(s.imager.tubeHarmonics);
          if (isNaN(tubeH) || tubeH < 1) { tubeH = 1; }
          if (harmOn) {
            var driveLinear = 1.0 + ((tubeH - 1) / 8) * 0.8;
            this.imagerHarmonicsDrive.gain.setTargetAtTime(driveLinear, now, ramp);
            this.imagerShaper.curve = this.makeTubeCurve();
          } else {
            this.imagerHarmonicsDrive.gain.setTargetAtTime(1.0, now, ramp);
            this.imagerShaper.curve = this.makeLinearCurve();
          }
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
      this.initDraggable();
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
        '        <span class="rack-drag-grip" title="Drag to move rack"><svg viewBox="0 0 10 16" width="8" height="13" fill="currentColor" aria-hidden="true"><circle cx="2" cy="2" r="1.4"/><circle cx="8" cy="2" r="1.4"/><circle cx="2" cy="8" r="1.4"/><circle cx="8" cy="8" r="1.4"/><circle cx="2" cy="14" r="1.4"/><circle cx="8" cy="14" r="1.4"/></svg></span>',
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
        '        <button type="button" class="rack-head-btn dock-btn" id="rack-dock-btn" title="Float window (or drag header to move)">Float</button>',
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

        '      <!-- MODULE 3: VINTAGE STEREO IMAGER & SPATIAL PROCESSOR -->',
        '      <div class="rack-unit unit-imager" id="unit-imager">',
        '        <div class="unit-bar">',
        '          <div class="unit-brand"><span class="screw-mini"></span> VINTAGE STEREO IMAGER & SPATIAL PROCESSOR <span class="screw-mini"></span></div>',
        '          <button type="button" class="unit-toggle on" id="toggle-imager" title="Toggle Stereo Imager on/off"><span class="led"></span> IN</button>',
        '        </div>',
        '        <div class="unit-faceplate imager-faceplate">',
        '          <div class="knob-group">',
        '            <div class="knob-wrap" data-param="imager.range" data-values="1,2,3,4,5,6,7,8,9" data-labels="1 (HIGH),2,3,4,5,6,7,8,9 (OPEN)" data-default="4" title="Process Frequency Band (High to Open)">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">RANGE</span>',
        '              <span class="knob-val">5</span>',
        '            </div>',
        '            <div class="knob-wrap" data-param="imager.stage" data-values="1,2,3,4,5,6,7,8,9" data-labels="1 (BACK),2,3,4,5,6,7,8,9 (FRONT)" data-default="4" title="Stereo Stage Placement (Back to Front)">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">STAGE</span>',
        '              <span class="knob-val">5</span>',
        '            </div>',
        '          </div>',
        '          <div class="imager-harmonics-sec">',
        '            <div class="imager-push-wrap">',
        '              <span class="imager-hint-label">Tubes Warm-Up</span>',
        '              <button type="button" class="imager-btn" id="toggle-imager-harmonics" title="Toggle Valve Tube Harmonics">',
        '                <span class="imager-btn-led blue"></span>',
        '                <span class="imager-btn-txt">HARMONICS</span>',
        '              </button>',
        '            </div>',
        '            <div class="knob-wrap" data-param="imager.tubeHarmonics" data-values="1,2,3,4,5,6,7,8,9" data-labels="1 (MIN),2,3,4,5,6,7,8,9 (MAX)" data-default="0" title="Tube Harmonic Saturation Drive">',
        '              <div class="knob-dial"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">TUBE HARMONICS</span>',
        '              <span class="knob-val">1 (MIN)</span>',
        '            </div>',
        '          </div>',
        '          <div class="imager-center-box">',
        '            <span class="imager-window-title">STEREO IMAGE</span>',
        '            <div class="imager-tube-window" title="Stereo Valve Spatial Circuit">',
        '              <div class="tube-mesh-grille"></div>',
        '              <div class="tube-glow-core" id="imager-tube-glow"></div>',
        '              <div class="tube-filament"></div>',
        '            </div>',
        '            <span class="imager-window-sub">BIGGER MAKER</span>',
        '          </div>',
        '          <div class="knob-group">',
        '            <div class="knob-wrap" data-param="imager.bigness" data-values="1,2,3,4,5,6,7,8,9" data-labels="1 (MIN),2,3,4,5,6,7,8,9 (MAX)" data-default="0" title="Stereo Width Intensity">',
        '              <div class="knob-dial large"><div class="knob-pointer"></div></div>',
        '              <span class="knob-name">BIGNESS</span>',
        '              <span class="knob-val">1 (MIN)</span>',
        '            </div>',
        '          </div>',
        '          <div class="imager-push-wrap">',
        '            <button type="button" class="imager-btn" id="toggle-imager-bass" title="Active Bass Punch & Mono Sub Anchor">',
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
        '              <button type="button" class="imager-on-btn on" id="toggle-imager-pwr" title="Toggle Imager Module Power">',
        '                <span class="pwr-lamp amber"></span>',
        '                <span class="pwr-txt">ON</span>',
        '              </button>',
        '              <span class="imager-model-spec">Model 2420</span>',
        '            </div>',
        '          </div>',
        '        </div>',
        '      </div>',

        '      <!-- MODULE 4: MASTER LIMITER -->',
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
        if (panel.classList.contains('is-floating')) {
          this.clampFloatingBounds();
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
      if (!this.currentTakeId) { return Promise.resolve(); }
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

    hasActiveMastering: function (takeId) {
      var s = null;
      if (this.currentTakeId && String(this.currentTakeId) === String(takeId)) {
        s = this.settings;
      } else if (window.State && State.takes) {
        var t = State.takes.find(function (x) { return String(x.id) === String(takeId); });
        if (t && t.fx_chain) {
          try {
            s = typeof t.fx_chain === 'string' ? JSON.parse(t.fx_chain) : t.fx_chain;
          } catch (e) {}
        }
      }
      if (!s) { return false; }
      if (s.masterBypass === true) { return false; }

      if (s.eq && s.eq.enabled !== false) {
        if (Number(s.eq.preGain || 0) !== 0 || Number(s.eq.lowGain || 0) !== 0 ||
            Number(s.eq.midGain || 0) !== 0 || Number(s.eq.highGain || 0) !== 0 ||
            Number(s.eq.outLevel || 0) !== 0 || Boolean(s.eq.phase) ||
            (Number(s.eq.hp || 20) > 20)) {
          return true;
        }
      }
      if (s.comp && s.comp.enabled !== false) {
        if (Number(s.comp.makeup || 0) !== 0 ||
            (s.comp.mix !== undefined && Number(s.comp.mix) < 0.999) ||
            Number(s.comp.threshold || -18) !== -18 ||
            Number(s.comp.ratio || 4) !== 4) {
          return true;
        }
      }
      if (s.imager && s.imager.enabled !== false) {
        if (Number(s.imager.bigness || 1) !== 1 || Boolean(s.imager.bass) ||
            Boolean(s.imager.harmonics) || Number(s.imager.range || 5) !== 5 ||
            Number(s.imager.stage || 5) !== 5) {
          return true;
        }
      }
      if (s.limit && s.limit.enabled !== false) {
        if (Number(s.limit.drive || 0) !== 0 || Boolean(s.limit.warmth) ||
            Number(s.limit.ceiling !== undefined ? s.limit.ceiling : -0.1) !== -0.1) {
          return true;
        }
      }
      return false;
    },

    renderMasterWav: async function (takeId, customSettings) {
      var s = customSettings;
      if (!s && this.currentTakeId && String(this.currentTakeId) === String(takeId)) {
        s = this.settings;
      }
      if (!s && window.State && State.takes) {
        var t = State.takes.find(function (x) { return String(x.id) === String(takeId); });
        if (t && t.fx_chain) {
          try {
            s = typeof t.fx_chain === 'string' ? JSON.parse(t.fx_chain) : t.fx_chain;
          } catch (e) {}
        }
      }
      if (!s && window.State && State.loadedTake && String(State.loadedTake.id) === String(takeId)) {
        if (State.loadedTake.fx_chain) {
          try {
            s = typeof State.loadedTake.fx_chain === 'string' ? JSON.parse(State.loadedTake.fx_chain) : State.loadedTake.fx_chain;
          } catch (e) {}
        }
      }
      if (!s) {
        try {
          var tResp = await fetch('/api/takes/' + takeId);
          if (tResp.ok) {
            var tData = await tResp.json();
            if (tData && tData.fx_chain) {
              s = typeof tData.fx_chain === 'string' ? JSON.parse(tData.fx_chain) : tData.fx_chain;
            }
          }
        } catch (e) {}
      }
      s = s || this.settings;

      var resp = await fetch('/api/takes/' + takeId + '/audio');
      if (!resp.ok) {
        throw new Error('Failed to fetch audio for take ' + takeId);
      }
      var arrayBuf = await resp.arrayBuffer();

      var AudioContextClass = window.AudioContext || window.webkitAudioContext;
      var tempCtx = new AudioContextClass();
      var decodedBuffer;
      try {
        decodedBuffer = await tempCtx.decodeAudioData(arrayBuf);
      } catch (decodeErr) {
        var wavResp = await fetch('/api/takes/' + takeId + '/audio?download=1&format=wav&raw=1');
        if (wavResp.ok) {
          var wavBuf = await wavResp.arrayBuffer();
          decodedBuffer = await tempCtx.decodeAudioData(wavBuf);
        } else {
          throw decodeErr;
        }
      }
      if (typeof tempCtx.close === 'function') {
        tempCtx.close().catch(function () {});
      }

      var OfflineContextClass = window.OfflineAudioContext || window.webkitOfflineAudioContext;
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

      src.start(0);
      var renderedBuffer = await offlineCtx.startRendering();
      return audioBufferToWav(renderedBuffer);
    },

    renderAndDownload: async function (takeId, format) {
      var wavBlob = await this.renderMasterWav(takeId);
      var formData = new FormData();
      formData.append('audio_file', wavBlob, 'master.wav');
      var res = await fetch('/api/takes/' + takeId + '/export-mastered?format=' + encodeURIComponent(format), {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        throw new Error('Server export failed: ' + res.status);
      }
      var blob = await res.blob();
      var disposition = res.headers.get('content-disposition') || '';
      var filename = 'master.' + format;
      var match = disposition.match(/filename\*=utf-8''([^;]+)/i);
      if (match && match[1]) {
        try { filename = decodeURIComponent(match[1]); } catch (e) { filename = match[1]; }
      } else {
        var m2 = disposition.match(/filename=["']?([^"';]+)["']?/i);
        if (m2 && m2[1]) { filename = m2[1]; }
      }
      if (filename === 'master.' + format && window.State && State.takes) {
        var t = State.takes.find(function (x) { return String(x.id) === String(takeId); });
        if (t && t.title) {
          var safe = t.title.replace(/[^a-zA-Z0-9 -_]/g, '').trim() || 'take';
          filename = safe + '.' + format;
        }
      }
      var link = document.createElement('a');
      var url = URL.createObjectURL(blob);
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      setTimeout(function () {
        URL.revokeObjectURL(url);
        link.remove();
      }, 1000);
    },

    applyToTake: async function () {
      if (!this.currentTakeId) {
        this.showToast('Select a take first');
        return;
      }
      var takeId = this.currentTakeId;
      var applyBtn = document.getElementById('rack-apply-take-btn');
      if (applyBtn) {
        applyBtn.disabled = true;
        applyBtn.textContent = 'Baking...';
      }
      this.showToast('Rendering & baking master into take...', 'good');

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
          throw new Error('Failed to bake master: ' + errText);
        }
        var data = await res.json();

        // Reset rack settings for this take to default transparent so it is not double-processed
        this.settings = JSON.parse(JSON.stringify(PRESETS['default']));
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

        this.showToast('Mastered audio saved permanently to take!', 'good');
      } catch (err) {
        console.error('Bake master failed:', err);
        this.showToast('Could not bake master: ' + err.message, 'bad');
      } finally {
        if (applyBtn) {
          applyBtn.disabled = false;
          applyBtn.textContent = 'Apply to Take';
        }
      }
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

        // 3. Stereo Imager Tube Filament Glow Animation
        var tubeGlow = document.getElementById('imager-tube-glow');
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
        // Do not initiate drag on interactive buttons, select dropdowns, or labels
        if (e.target.closest('button, select, input, label, a, .rack-head-btn, .rack-select')) { return; }

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

      window.addEventListener('resize', function () {
        if (panel.classList.contains('is-floating')) {
          self.clampFloatingBounds();
        }
      });
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
      try { localStorage.removeItem('yue2.rackFloat'); } catch (err) {}
      this.updateDockButtonUI();
    },

    floatToCenter: function () {
      var panel = document.getElementById('rack-panel');
      if (!panel) { return; }
      var width = Math.min(1240, window.innerWidth - 24);
      var left = Math.max(10, Math.round((window.innerWidth - width) / 2));
      var top = Math.max(20, Math.round((window.innerHeight - 560) / 2));
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
      dockBtn.textContent = isFloating ? 'Dock' : 'Float';
      dockBtn.title = isFloating ? 'Dock rack to bottom of window' : 'Float rack window (or drag header to move)';
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
