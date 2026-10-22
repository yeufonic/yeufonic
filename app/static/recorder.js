/* -------------------------------------------------------- Yeufonic Melody Recorder
   Microphone recording deck with low-latency live monitoring, metronome count-in,
   live VU meter & pitch tracker, selectable autotune, and take management.
   Saves vocal and hummed melodies directly into the Cover library.
   Structured for future MIDI instrument recording extension. */

(function () {
  'use strict';

  var AudioContextClass = window.AudioContext || window.webkitAudioContext;

  var Recorder = {
    audioCtx: null,
    micStream: null,
    micSource: null,
    monitorGain: null,
    analyser: null,
    processorNode: null,
    dummyDest: null,

    // Transport state: 'idle' | 'armed' | 'countin' | 'recording' | 'stopped'
    state: 'idle',
    // 'mic' (a voice, sung or hummed) or 'instrument' (a single-note line, e.g. a guitar into an interface)
    inputMode: 'mic',
    deviceId: '',          // '' is the system's default input
    inputChannel: 'both',  // 'both' (mixed to mono), 'left' or 'right': an interface's input 1 or 2
    inputGain: null,
    inputSplitter: null,

    // Recorded audio chunks
    recordedChunks: [],
    recordedLength: 0,
    startTime: 0,
    timerInterval: null,

    // Live monitoring & input settings
    monitorEnabled: false,
    monitorVolume: 0.8,
    inputGainVal: 1.0,

    // Metronome & Count-in
    metronome: {
      enabled: true,
      bpm: 120,
      timeSignature: '4/4',
      beatsPerBar: 4,
      countInBars: 1, // 1 bar (4 beats), 2 bars, or 0
      timerId: null,
      recTimerId: null,
      currentBeat: 0,
      countInRemaining: 0
    },

    // Autotune settings
    autotune: {
      enabled: false,
      scale: 'chromatic',
      root: 'C',
      strength: 0.85
    },

    // Session takes: array of { id, title, duration, blob, tunedBlob, isTuned, url, tunedUrl, pcm }
    sessionTakes: [],
    activeTakeId: null,
    previewAudio: null,
    previewPlayingId: null,

    // Animation frame for VU meter & pitch readout
    rafId: null,
    isOpen: false,

    init: function () {
      this.loadPrefs();
      this.bindDOM();
      this.paintInput();
    },

    // ------------------------------------------------- Input choice (remembered per browser)
    loadPrefs: function () {
      var saved = null;
      try { saved = JSON.parse(localStorage.getItem('yue2.recorderInput') || 'null'); } catch (e) { saved = null; }
      if (!saved) { return; }
      if (saved.mode === 'mic' || saved.mode === 'instrument') { this.inputMode = saved.mode; }
      if (typeof saved.deviceId === 'string') { this.deviceId = saved.deviceId; }
      if (['both', 'left', 'right'].indexOf(saved.channel) >= 0) { this.inputChannel = saved.channel; }
      if (typeof saved.gain === 'number' && saved.gain > 0) { this.inputGainVal = saved.gain; }
    },

    savePrefs: function () {
      try {
        localStorage.setItem('yue2.recorderInput', JSON.stringify({
          mode: this.inputMode, deviceId: this.deviceId, channel: this.inputChannel, gain: this.inputGainVal
        }));
      } catch (e) { /* no storage: the choice lasts this visit */ }
    },

    isInstrument: function () {
      return this.inputMode === 'instrument';
    },

    paintInput: function () {
      var inst = this.isInstrument();
      var voiceBtn = document.getElementById('rec-src-voice');
      var instBtn = document.getElementById('rec-src-instrument');
      if (voiceBtn) { voiceBtn.classList.toggle('active', !inst); }
      if (instBtn) { instBtn.classList.toggle('active', inst); }
      var channel = document.getElementById('rec-channel');
      if (channel) { channel.value = this.inputChannel; }
      var gain = document.getElementById('rec-gain');
      if (gain) { gain.value = String(this.inputGainVal); }
      // Snapping pitch is for a voice: an instrument is already in tune.
      var tuneCard = document.getElementById('rec-autotune-card');
      if (tuneCard) { tuneCard.classList.toggle('hidden', inst); }
      var hint = document.getElementById('rec-input-hint');
      if (hint) {
        hint.textContent = inst
          ? 'Play the melody one note at a time: it becomes the sung tune, and Write lyrics gives it words. Strummed chords give no tune to sing.'
          : 'Sing or hum your melody.';
      }
      var title = document.getElementById('recorder-modal-title');
      if (title) { title.textContent = inst ? 'Record Instrument' : 'Record Melody'; }
    },

    setInputMode: function (mode) {
      if (mode !== 'mic' && mode !== 'instrument') { return; }
      if (this.state === 'recording' || this.state === 'countin') { return; }
      this.inputMode = mode;
      if (mode === 'instrument' && this.autotune.enabled) { this.toggleAutotune(false); }
      this.savePrefs();
      this.paintInput();
    },

    setInputGain: function (value) {
      if (!(value > 0)) { return; }
      this.inputGainVal = value;
      if (this.inputGain && this.audioCtx) {
        this.inputGain.gain.setTargetAtTime(value, this.audioCtx.currentTime, 0.01);
      }
      this.savePrefs();
    },

    setInputChannel: function (channel) {
      if (['both', 'left', 'right'].indexOf(channel) < 0) { return; }
      this.inputChannel = channel;
      this.savePrefs();
      this.rearm();
    },

    setDevice: function (deviceId) {
      this.deviceId = deviceId || '';
      this.savePrefs();
      this.rearm();
    },

    // A new device or channel needs the input opened again; not in the middle of a take.
    rearm: function () {
      if (this.state !== 'armed') { return; }
      this.disarmRecorder();
      this.armRecorder();
    },

    // Devices are named only once the page may use one, so the list is filled after arming.
    refreshDevices: async function () {
      var select = document.getElementById('rec-device');
      if (!select || !navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) { return; }
      var inputs = [];
      try {
        inputs = (await navigator.mediaDevices.enumerateDevices()).filter(function (d) { return d.kind === 'audioinput'; });
      } catch (e) { return; }
      var self = this;
      select.innerHTML = '<option value="">Default input</option>' + inputs
        .filter(function (d) { return d.deviceId && d.deviceId !== 'default'; })
        .map(function (d, i) {
          return '<option value="' + self.esc(d.deviceId) + '">' + self.esc(d.label || ('Input ' + (i + 1))) + '</option>';
        }).join('');
      select.value = this.deviceId;
      if (select.value !== this.deviceId) { select.value = ''; }
    },

    bindDOM: function () {
      var self = this;

      // Global Space bar toggle when recorder modal is open
      window.addEventListener('keydown', function (e) {
        if (!self.isOpen) { return; }
        // Don't intercept if user is typing in an input
        var tag = (e.target && e.target.tagName) || '';
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') { return; }
        if (e.code === 'Space') {
          e.preventDefault();
          self.toggleRecordAction();
        } else if (e.code === 'Escape') {
          self.closeModal();
        }
      });
    },

    openModal: function () {
      this.isOpen = true;
      var modal = document.getElementById('recorder-modal');
      if (modal) {
        modal.classList.remove('hidden');
      }
      this.renderTakesList();
      this.updateTransportUI();
      this.updateCountInLabels();
      // Auto-arm on open if not already armed
      if (this.state === 'idle') {
        this.armRecorder();
      }
    },

    closeModal: function () {
      this.isOpen = false;
      var modal = document.getElementById('recorder-modal');
      if (modal) {
        modal.classList.add('hidden');
      }
      this.stopPreview();
      if (this.state === 'recording' || this.state === 'countin') {
        this.stopRecording();
      }
      this.disarmRecorder();
    },

    // ------------------------------------------------- Hardware Audio & Monitoring
    armRecorder: async function () {
      if (this.state === 'armed' || this.state === 'recording') { return; }
      var self = this;
      try {
        if (!this.audioCtx) {
          this.audioCtx = new AudioContextClass({ latencyHint: 'interactive' });
        }
        if (this.audioCtx.state === 'suspended') {
          await this.audioCtx.resume();
        }

        // Direct input with zero echo/noise suppression latency.  One side of a stereo
        // interface (a guitar in input 1) is asked for in stereo and taken apart below.
        if (!this.micStream) {
          var wanted = {
            echoCancellation: false,
            noiseSuppression: false,
            autoGainControl: false,
            channelCount: this.inputChannel === 'both' ? 1 : { ideal: 2 }
          };
          if (this.deviceId) { wanted.deviceId = { exact: this.deviceId }; }
          try {
            this.micStream = await navigator.mediaDevices.getUserMedia({ audio: wanted });
          } catch (err) {
            // The remembered device has gone: the default input will do.
            if (!this.deviceId || (err && err.name !== 'OverconstrainedError' && err.name !== 'NotFoundError')) { throw err; }
            delete wanted.deviceId;
            this.deviceId = '';
            this.savePrefs();
            this.micStream = await navigator.mediaDevices.getUserMedia({ audio: wanted });
          }
        }

        this.micSource = this.audioCtx.createMediaStreamSource(this.micStream);

        // Everything downstream (monitor, meter, recording) hears the input through its gain,
        // from one side of the input when a side is chosen and the device gives two.
        this.inputGain = this.audioCtx.createGain();
        this.inputGain.gain.value = this.inputGainVal;
        var track = this.micStream.getAudioTracks()[0];
        var channels = (track && track.getSettings && track.getSettings().channelCount) || this.micSource.channelCount || 1;
        if (this.inputChannel !== 'both' && channels >= 2) {
          this.inputSplitter = this.audioCtx.createChannelSplitter(2);
          this.micSource.connect(this.inputSplitter);
          this.inputSplitter.connect(this.inputGain, this.inputChannel === 'right' ? 1 : 0);
        } else {
          this.micSource.connect(this.inputGain);
        }

        // Low-latency direct monitor path: input -> monitorGain -> destination
        this.monitorGain = this.audioCtx.createGain();
        this.monitorGain.gain.value = this.monitorEnabled ? this.monitorVolume : 0.0;
        this.inputGain.connect(this.monitorGain);
        this.monitorGain.connect(this.audioCtx.destination);

        // VU Analyser
        this.analyser = this.audioCtx.createAnalyser();
        this.analyser.fftSize = 512;
        this.inputGain.connect(this.analyser);

        this.state = 'armed';
        var errShown = document.getElementById('rec-error-msg');
        if (errShown) { errShown.classList.add('hidden'); }
        this.updateTransportUI();
        this.startMeterLoop();
        this.refreshDevices();
      } catch (err) {
        console.error('Failed to arm input:', err);
        var errEl = document.getElementById('rec-error-msg');
        if (errEl) {
          errEl.textContent = 'Could not open the input: ' + (err.message || err);
          errEl.classList.remove('hidden');
        }
        this.state = 'idle';
        this.updateTransportUI();
      }
    },

    disarmRecorder: function () {
      if (this.rafId) {
        cancelAnimationFrame(this.rafId);
        this.rafId = null;
      }
      if (this.monitorGain) {
        try { this.monitorGain.disconnect(); } catch (e) {}
        this.monitorGain = null;
      }
      if (this.analyser) {
        try { this.analyser.disconnect(); } catch (e) {}
        this.analyser = null;
      }
      if (this.inputGain) {
        try { this.inputGain.disconnect(); } catch (e) {}
        this.inputGain = null;
      }
      if (this.inputSplitter) {
        try { this.inputSplitter.disconnect(); } catch (e) {}
        this.inputSplitter = null;
      }
      if (this.micSource) {
        try { this.micSource.disconnect(); } catch (e) {}
        this.micSource = null;
      }
      if (this.micStream) {
        this.micStream.getTracks().forEach(function (t) { t.stop(); });
        this.micStream = null;
      }
      this.state = 'idle';
      this.updateTransportUI();
      this.resetMeterUI();
    },

    toggleMonitor: function (forceVal) {
      var on = forceVal !== undefined ? forceVal : !this.monitorEnabled;
      this.setMonitor(on);
    },

    setMonitor: async function (enabled, volume) {
      this.monitorEnabled = Boolean(enabled);
      if (typeof volume === 'number') { this.monitorVolume = volume; }

      if (this.audioCtx && this.audioCtx.state === 'suspended') {
        try { await this.audioCtx.resume(); } catch (e) {}
      }

      if (this.monitorEnabled && (!this.micSource || !this.monitorGain)) {
        await this.armRecorder();
      }

      if (this.monitorGain && this.audioCtx) {
        try {
          this.monitorGain.gain.setValueAtTime(this.monitorEnabled ? this.monitorVolume : 0.0, this.audioCtx.currentTime);
        } catch (e) {
          this.monitorGain.gain.value = this.monitorEnabled ? this.monitorVolume : 0.0;
        }
      }
      var monBtn = document.getElementById('rec-monitor-btn');
      if (monBtn) {
        monBtn.classList.toggle('active', this.monitorEnabled);
        monBtn.textContent = this.monitorEnabled ? 'On' : 'Off';
      }
    },

    // ------------------------------------------------- Meter & Pitch Estimation
    startMeterLoop: function () {
      var self = this;
      var dataArray = new Float32Array(this.analyser ? this.analyser.fftSize : 256);

      function tick() {
        if (!self.isOpen || (self.state !== 'armed' && self.state !== 'recording' && self.state !== 'countin')) {
          return;
        }
        if (self.analyser) {
          self.analyser.getFloatTimeDomainData(dataArray);
          var peak = 0;
          var sumSq = 0;
          for (var i = 0; i < dataArray.length; i++) {
            var val = Math.abs(dataArray[i]);
            if (val > peak) { peak = val; }
            sumSq += val * val;
          }
          var rms = Math.sqrt(sumSq / dataArray.length);
          self.renderMeter(peak, rms);

          // Estimate pitch for live display when voiced
          if (peak > 0.03) {
            var pitch = self.estimatePitch(dataArray, self.audioCtx.sampleRate);
            self.renderPitchReadout(pitch);
          } else {
            self.renderPitchReadout(null);
          }
        }
        self.rafId = requestAnimationFrame(tick);
      }
      if (this.rafId) { cancelAnimationFrame(this.rafId); }
      this.rafId = requestAnimationFrame(tick);
    },

    estimatePitch: function (buffer, sampleRate) {
      // Autocorrelation pitch detector
      var SIZE = buffer.length;
      var MAX_SAMPLES = Math.floor(SIZE / 2);
      var bestOffset = -1;
      var bestCorrelation = 0;
      var rms = 0;
      for (var i = 0; i < SIZE; i++) {
        var val = buffer[i];
        rms += val * val;
      }
      rms = Math.sqrt(rms / SIZE);
      if (rms < 0.02) { return null; }

      var lastCorrelation = 1;
      for (var offset = 16; offset < MAX_SAMPLES; offset++) {
        var correlation = 0;
        for (var j = 0; j < MAX_SAMPLES; j++) {
          correlation += Math.abs(buffer[j] - buffer[j + offset]);
        }
        correlation = 1 - (correlation / MAX_SAMPLES);
        if (correlation > 0.85 && correlation > lastCorrelation) {
          if (correlation > bestCorrelation) {
            bestCorrelation = correlation;
            bestOffset = offset;
          }
        }
        lastCorrelation = correlation;
      }
      if (bestCorrelation > 0.82 && bestOffset > 0) {
        var fundamentalFreq = sampleRate / bestOffset;
        if (fundamentalFreq >= 60 && fundamentalFreq <= 1200) {
          return fundamentalFreq;
        }
      }
      return null;
    },

    renderMeter: function (peak, rms) {
      var bar = document.getElementById('rec-vu-fill');
      var peakEl = document.getElementById('rec-vu-peak');
      var clipEl = document.getElementById('rec-vu-clip');
      if (bar) {
        var pct = Math.min(100, Math.round(peak * 100));
        bar.style.width = pct + '%';
        bar.className = 'rec-vu-fill' + (pct > 92 ? ' vu-hot' : (pct > 75 ? ' vu-warn' : ''));
      }
      if (clipEl) {
        clipEl.classList.toggle('clipped', peak >= 0.99);
      }
    },

    resetMeterUI: function () {
      var bar = document.getElementById('rec-vu-fill');
      if (bar) { bar.style.width = '0%'; }
      var noteEl = document.getElementById('rec-live-pitch');
      if (noteEl) { noteEl.textContent = '—'; }
    },

    renderPitchReadout: function (freq) {
      var noteEl = document.getElementById('rec-live-pitch');
      if (!noteEl) { return; }
      if (!freq) {
        noteEl.textContent = this.state === 'recording' ? 'Listening…' : '—';
        return;
      }
      var noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
      var midi = 69 + 12 * (Math.log(freq / 440) / Math.LN2);
      var roundMidi = Math.round(midi);
      var noteName = noteNames[roundMidi % 12];
      var octave = Math.floor(roundMidi / 12) - 1;
      var cents = Math.round((midi - roundMidi) * 100);
      var sign = cents >= 0 ? '+' : '';
      noteEl.textContent = noteName + octave + ' (' + Math.round(freq) + 'Hz ' + sign + cents + '¢)';
    },

    // ------------------------------------------------- Metronome & Count-In
    getRootFrequency: function (rootName, octave) {
      if (octave === undefined) { octave = 4; }
      var map = {
        'C': 0, 'C#': 1, 'DB': 1, 'D': 2, 'D#': 3, 'EB': 3,
        'E': 4, 'F': 5, 'F#': 6, 'GB': 6, 'G': 7, 'G#': 8,
        'AB': 8, 'A': 9, 'A#': 10, 'BB': 10, 'B': 11
      };
      var clean = String(rootName || 'C').trim().toUpperCase().split('/')[0].trim();
      var semitone = map[clean] !== undefined ? map[clean] : 0;
      var midi = 12 * (octave + 1) + semitone;
      return 440.0 * Math.pow(2.0, (midi - 69) / 12.0);
    },

    playSineTone: function (freq, duration, volume) {
      if (!this.audioCtx) {
        this.audioCtx = new AudioContextClass();
      }
      if (this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }

      var now = this.audioCtx.currentTime;
      var dur = duration || 1.25;
      var vol = typeof volume === 'number' ? volume : 0.6;

      // Pure sine wave: 100% pure fundamental frequency, zero harmonics, zero ambiguity
      var osc = this.audioCtx.createOscillator();
      var gain = this.audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, now);

      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.linearRampToValueAtTime(vol, now + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + dur);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start(now);
      osc.stop(now + dur + 0.05);
    },

    playClick: function (accent) {
      if (!this.audioCtx) {
        this.audioCtx = new AudioContextClass();
      }
      if (this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }

      if (this.autotune && this.autotune.enabled) {
        var root = (this.autotune && this.autotune.root) || 'C';
        var freq = this.getRootFrequency(root, accent ? 5 : 4);
        var dur = accent ? 0.22 : 0.14;
        var vol = accent ? 0.7 : 0.5;
        this.playSineTone(freq, dur, vol);
      } else {
        var oscStd = this.audioCtx.createOscillator();
        var gainStd = this.audioCtx.createGain();
        oscStd.type = 'triangle';
        oscStd.frequency.value = accent ? 980 : 480;

        var nowStd = this.audioCtx.currentTime;
        gainStd.gain.setValueAtTime(0.7, nowStd);
        gainStd.gain.exponentialRampToValueAtTime(0.001, nowStd + 0.06);

        oscStd.connect(gainStd);
        gainStd.connect(this.audioCtx.destination);
        oscStd.start(nowStd);
        oscStd.stop(nowStd + 0.07);
      }
    },

    playCountInClick: function (accent) {
      this.playClick(accent);
    },

    auditionRootNote: function () {
      var root = (this.autotune && this.autotune.root) || 'C';
      var freq = this.getRootFrequency(root, 4);

      this.playSineTone(freq, 1.25, 0.6);

      // Visual feedback on audition button
      var btn = document.getElementById('rec-root-audition-btn');
      if (btn) {
        btn.classList.add('playing');
        setTimeout(function () {
          btn.classList.remove('playing');
        }, 800);
      }
    },

    setRoot: function (val) {
      if (val) {
        this.autotune.root = val;
      }
      this.auditionRootNote();
    },

    toggleMetronome: function (forceVal) {
      var btn = document.getElementById('rec-metro-toggle');
      var on = forceVal !== undefined ? forceVal : !this.metronome.enabled;
      this.metronome.enabled = on;
      if (btn) {
        btn.classList.toggle('active', on);
        btn.textContent = on ? 'On' : 'Off';
      }
    },

    toggleAutotune: function (forceVal) {
      var btn = document.getElementById('rec-auto-toggle');
      var on = forceVal !== undefined ? forceVal : !this.autotune.enabled;
      this.autotune.enabled = on;
      if (btn) {
        btn.classList.toggle('active', on);
        btn.textContent = on ? 'On' : 'Off';
      }
    },

    setTimeSignature: function (sigStr) {
      this.metronome.timeSignature = sigStr || '4/4';
      var num = parseInt((sigStr || '4/4').split('/')[0], 10) || 4;
      this.metronome.beatsPerBar = num;
      this.updateCountInLabels();
    },

    updateCountInLabels: function () {
      var select = document.getElementById('rec-countin');
      if (!select) { return; }
      var bpb = this.metronome.beatsPerBar || 4;
      var curVal = select.value || '1';
      select.innerHTML =
        '<option value="1">1 Bar (' + bpb + ' beats)</option>' +
        '<option value="2">2 Bars (' + (bpb * 2) + ' beats)</option>' +
        '<option value="0">None (Immediate)</option>';
      select.value = curVal;
    },

    startCountInThenRecord: function () {
      var self = this;
      var bars = Number(this.metronome.countInBars) || 0;
      if (bars <= 0) {
        self.startRecordingImmediate();
        return;
      }

      this.state = 'countin';
      this.updateTransportUI();
      var bpb = Math.max(1, parseInt(this.metronome.beatsPerBar, 10) || 4);
      var totalBeats = bars * bpb;
      var intervalMs = (60 / this.metronome.bpm) * 1000;
      var currentBeatIndex = 0;

      var overlay = document.getElementById('rec-countin-overlay');
      var numEl = document.getElementById('rec-countin-number');
      var rootEl = document.getElementById('rec-countin-root');
      if (overlay) { overlay.classList.remove('hidden'); }
      if (rootEl) {
        if (self.autotune && self.autotune.enabled) {
          rootEl.textContent = 'Root: ' + (self.autotune.root || 'C');
          rootEl.classList.remove('hidden');
        } else {
          rootEl.classList.add('hidden');
        }
      }

      function tick() {
        if (self.state !== 'countin') { return; }

        if (currentBeatIndex < totalBeats) {
          var beatInBar = (currentBeatIndex % bpb) + 1;
          self.playCountInClick(beatInBar === 1);
          if (numEl) {
            numEl.textContent = String(beatInBar);
            numEl.classList.remove('pulse');
            void numEl.offsetWidth; // retrigger css animation
            numEl.classList.add('pulse');
          }
          currentBeatIndex++;
          self.metronome.timerId = setTimeout(tick, intervalMs);
        } else {
          if (overlay) { overlay.classList.add('hidden'); }
          self.startRecordingImmediate();
        }
      }

      tick();
    },

    // ------------------------------------------------- Recording Engine
    toggleRecordAction: function () {
      if (this.state === 'recording' || this.state === 'countin') {
        this.stopRecording();
      } else {
        this.startRecording();
      }
    },

    startRecording: async function () {
      if (this.state === 'idle') {
        await this.armRecorder();
      }
      if (this.state !== 'armed') { return; }
      this.stopPreview();
      this.startCountInThenRecord();
    },

    startRecordingImmediate: function () {
      var self = this;
      this.state = 'recording';
      this.recordedChunks = [];
      this.recordedLength = 0;
      this.startTime = Date.now();
      this.updateTransportUI();

      // Start recording timer display
      var timerEl = document.getElementById('rec-timer');
      if (this.timerInterval) { clearInterval(this.timerInterval); }
      this.timerInterval = setInterval(function () {
        if (self.state !== 'recording') { return; }
        var elapsed = (Date.now() - self.startTime) / 1000;
        var mins = Math.floor(elapsed / 60);
        var secs = Math.floor(elapsed % 60);
        var ms = Math.floor((elapsed % 1) * 10);
        if (timerEl) {
          timerEl.textContent = (mins < 10 ? '0' : '') + mins + ':' + (secs < 10 ? '0' : '') + secs + '.' + ms;
        }
      }, 100);

      // Start metronome during recording if enabled
      if (this.metronome.enabled) {
        var intervalMs = (60 / this.metronome.bpm) * 1000;
        var bpb = Math.max(1, parseInt(this.metronome.beatsPerBar, 10) || 4);
        var bCount = 0;
        self.playClick(true);
        bCount = 1;
        self.metronome.recTimerId = setInterval(function () {
          if (self.state !== 'recording') {
            clearInterval(self.metronome.recTimerId);
            return;
          }
          self.playClick(bCount % bpb === 0);
          bCount++;
        }, intervalMs);
      }

      // Web Audio capture via ScriptProcessor
      var bufferSize = 4096;
      this.processorNode = this.audioCtx.createScriptProcessor(bufferSize, 1, 1);
      this.processorNode.onaudioprocess = function (e) {
        if (self.state !== 'recording') { return; }
        var inputData = e.inputBuffer.getChannelData(0);
        var chunk = new Float32Array(inputData.length);
        chunk.set(inputData);
        self.recordedChunks.push(chunk);
        self.recordedLength += chunk.length;
      };

      this.inputGain.connect(this.processorNode);
      // ScriptProcessor requires a destination connection to process audio
      this.dummyDest = this.audioCtx.createGain();
      this.dummyDest.gain.value = 0.0;
      this.processorNode.connect(this.dummyDest);
      this.dummyDest.connect(this.audioCtx.destination);
    },

    stopRecording: function () {
      if (this.metronome.timerId) {
        clearTimeout(this.metronome.timerId);
        this.metronome.timerId = null;
      }
      if (this.metronome.recTimerId) {
        clearInterval(this.metronome.recTimerId);
        this.metronome.recTimerId = null;
      }
      var overlay = document.getElementById('rec-countin-overlay');
      if (overlay) { overlay.classList.add('hidden'); }

      if (this.timerInterval) {
        clearInterval(this.timerInterval);
        this.timerInterval = null;
      }

      if (this.processorNode) {
        try {
          this.processorNode.disconnect();
          if (this.dummyDest) { this.dummyDest.disconnect(); }
        } catch (e) {}
        this.processorNode = null;
      }

      if (this.state === 'recording' && this.recordedLength > 0) {
        this.finishTake();
      }

      this.state = 'armed';
      this.updateTransportUI();
    },

    retakeCurrent: function () {
      this.stopPreview();
      if (this.state === 'recording' || this.state === 'countin') {
        this.stopRecording();
      }
      // Start recording a fresh take immediately
      this.startRecording();
    },

    finishTake: function () {
      var sampleRate = this.audioCtx.sampleRate;
      var fullBuffer = new Float32Array(this.recordedLength);
      var offset = 0;
      for (var i = 0; i < this.recordedChunks.length; i++) {
        fullBuffer.set(this.recordedChunks[i], offset);
        offset += this.recordedChunks[i].length;
      }

      var durationSec = this.recordedLength / sampleRate;
      if (durationSec < 0.5) {
        // Less than half a second ignored
        return;
      }

      var wavBlob = this.encodeWAV(fullBuffer, sampleRate);
      var takeNum = this.sessionTakes.length + 1;
      var takeId = 'rec_' + Date.now();
      var instrument = this.isInstrument();
      var take = {
        id: takeId,
        title: (instrument ? 'Instrument Melody Take ' : 'Vocal Melody Take ') + takeNum,
        instrument: instrument,
        duration: durationSec,
        blob: wavBlob,
        tunedBlob: null,
        isTuned: false,
        url: URL.createObjectURL(wavBlob),
        tunedUrl: null,
        pcm: fullBuffer,
        sampleRate: sampleRate,
        autotuneStatus: 'none' // 'none' | 'tuning' | 'done' | 'failed'
      };

      this.sessionTakes.unshift(take);
      this.activeTakeId = takeId;
      this.renderTakesList();

      // Automatically apply autotune if the autotune toggle is on
      if (this.autotune.enabled && !instrument) {
        this.applyAutotune(takeId);
      }
    },

    encodeWAV: function (samples, sampleRate) {
      var buffer = new ArrayBuffer(44 + samples.length * 2);
      var view = new DataView(buffer);

      function writeString(view, offset, string) {
        for (var i = 0; i < string.length; i++) {
          view.setUint8(offset + i, string.charCodeAt(i));
        }
      }

      writeString(view, 0, 'RIFF');
      view.setUint32(4, 36 + samples.length * 2, true);
      writeString(view, 8, 'WAVE');
      writeString(view, 12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true); // PCM
      view.setUint16(22, 1, true); // Mono
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * 2, true); // Byte rate (16-bit mono)
      view.setUint16(32, 2, true); // Block align
      view.setUint16(34, 16, true); // Bits per sample
      writeString(view, 36, 'data');
      view.setUint32(40, samples.length * 2, true);

      // Float to 16-bit PCM
      var index = 44;
      for (var i = 0; i < samples.length; i++) {
        var s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(index, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        index += 2;
      }
      return new Blob([view], { type: 'audio/wav' });
    },

    // ------------------------------------------------- Autotune Processing
    applyAutotune: async function (takeId) {
      var take = this.takeById(takeId);
      if (!take) { return; }
      take.autotuneStatus = 'tuning';
      this.renderTakesList();

      var formData = new FormData();
      formData.append('audio_file', take.blob, 'take.wav');
      formData.append('scale', this.autotune.scale);
      formData.append('root', this.autotune.root);
      formData.append('strength', String(this.autotune.strength));

      try {
        var resp = await fetch('/api/recorder/autotune', {
          method: 'POST',
          body: formData
        });
        if (!resp.ok) {
          throw new Error('Autotune server error ' + resp.status);
        }
        var tunedBlob = await resp.blob();
        take.tunedBlob = tunedBlob;
        take.tunedUrl = URL.createObjectURL(tunedBlob);

        var notesDetected = parseInt(resp.headers.get('x-notes-detected') || resp.headers.get('X-Notes-Detected') || '0', 10);
        var notesAdjusted = parseInt(resp.headers.get('x-notes-adjusted') || resp.headers.get('X-Notes-Adjusted') || '0', 10);
        var scale = resp.headers.get('x-scale') || resp.headers.get('X-Scale') || this.autotune.scale;
        var root = resp.headers.get('x-root') || resp.headers.get('X-Root') || this.autotune.root;

        take.tuneStats = {
          notesDetected: notesDetected,
          notesAdjusted: notesAdjusted,
          scale: scale,
          root: root
        };

        if (notesDetected === 0) {
          take.autotuneStatus = 'no_voice';
          take.isTuned = false;
        } else {
          take.autotuneStatus = 'done';
          take.isTuned = true;
          // Immediately play tuned version so the user hears what autotune did
          this.playTake(take.id);
        }
      } catch (err) {
        console.error('Autotune processing failed:', err);
        take.autotuneStatus = 'failed';
        take.tuneError = err.message || 'Processing failed';
      }
      this.renderTakesList();
    },

    toggleTakeTuning: function (takeId) {
      var take = this.takeById(takeId);
      if (!take || !take.tunedBlob) { return; }
      take.isTuned = !take.isTuned;
      // Continue or start preview so user immediately hears the difference between Raw and Autotuned
      var curTime = (this.previewAudio && this.previewPlayingId === takeId) ? this.previewAudio.currentTime : 0;
      this.playTake(takeId, curTime);
      this.renderTakesList();
    },

    // ------------------------------------------------- Audition / Preview
    playTake: function (takeId, seekSec) {
      var take = this.takeById(takeId);
      if (!take) { return; }
      this.stopPreview();

      var audioUrl = (take.isTuned && take.tunedUrl) ? take.tunedUrl : take.url;
      this.previewAudio = new Audio(audioUrl);
      var self = this;
      this.previewPlayingId = takeId;
      this.previewAudio.onended = function () {
        self.previewPlayingId = null;
        self.renderTakesList();
      };
      if (typeof seekSec === 'number' && seekSec > 0) {
        try { this.previewAudio.currentTime = seekSec; } catch (e) {}
      }
      this.previewAudio.play().catch(function () {});
      this.renderTakesList();
    },

    stopPreview: function () {
      if (this.previewAudio) {
        try {
          this.previewAudio.pause();
          this.previewAudio.currentTime = 0;
        } catch (e) {}
        this.previewAudio = null;
      }
      this.previewPlayingId = null;
      this.renderTakesList();
    },

    deleteTake: function (takeId) {
      if (this.previewPlayingId === takeId) {
        this.stopPreview();
      }
      this.sessionTakes = this.sessionTakes.filter(function (t) { return t.id !== takeId; });
      if (this.activeTakeId === takeId) {
        this.activeTakeId = this.sessionTakes.length ? this.sessionTakes[0].id : null;
      }
      this.renderTakesList();
    },

    takeById: function (id) {
      for (var i = 0; i < this.sessionTakes.length; i++) {
        if (this.sessionTakes[i].id === id) { return this.sessionTakes[i]; }
      }
      return null;
    },

    // ------------------------------------------------- Save & Send to Cover Workflow
    sendToCover: async function (takeId) {
      var take = this.takeById(takeId);
      if (!take) { return; }
      var blobToSave = (take.isTuned && take.tunedBlob) ? take.tunedBlob : take.blob;
      var title = take.title || (take.instrument ? 'Instrument Melody' : 'Vocal Melody');

      var form = new FormData();
      form.append('file', blobToSave, 'melody.wav');
      form.append('title', title);
      form.append('origin', 'recording');
      form.append('instrument', take.instrument ? '1' : '0');

      var sendBtn = document.getElementById('rec-send-btn-' + takeId);
      if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.textContent = 'Saving…';
      }

      try {
        var resp = await fetch('/api/sources', { method: 'POST', body: form });
        if (!resp.ok) {
          throw new Error('Upload failed with status ' + resp.status);
        }
        var newSource = await resp.json();

        // Refresh sources dropdown in app
        if (typeof window.loadSources === 'function') {
          await window.loadSources();
        }
        var select = document.getElementById('source-select');
        if (select) {
          select.value = newSource.id;
        }
        if (typeof window.paintSource === 'function') {
          window.paintSource();
        }

        // Switch form to Cover mode if not already
        var coverBtn = document.querySelector('button[data-mode="cover"]');
        if (coverBtn) { coverBtn.click(); }

        if (typeof window.statusLine === 'function') {
          window.statusLine('Recorded melody saved as cover source: “' + title + '”. Ready to transcribe or generate cover.', 'good');
        }

        this.closeModal();
      } catch (err) {
        console.error('Failed to save recording to cover:', err);
        alert('Could not save recording: ' + (err.message || err));
        if (sendBtn) {
          sendBtn.disabled = false;
          sendBtn.textContent = 'Use as Cover';
        }
      }
    },

    // ------------------------------------------------- UI Rendering
    updateTransportUI: function () {
      var recBtn = document.getElementById('rec-transport-record');
      var stopBtn = document.getElementById('rec-transport-stop');
      var armBtn = document.getElementById('rec-transport-arm');
      var retakeBtn = document.getElementById('rec-transport-retake');
      var statusBadge = document.getElementById('rec-status-badge');

      var isRec = this.state === 'recording';
      var isCount = this.state === 'countin';
      var isArmed = this.state === 'armed';

      if (recBtn) {
        recBtn.classList.toggle('is-recording', isRec);
        recBtn.classList.toggle('is-countin', isCount);
        recBtn.title = isRec ? 'Stop Recording (Space)' : 'Start Recording (Space)';
      }
      if (stopBtn) {
        stopBtn.disabled = !isRec && !isCount;
      }
      if (retakeBtn) {
        retakeBtn.disabled = !isRec && this.sessionTakes.length === 0;
      }
      if (armBtn) {
        armBtn.classList.toggle('active', isArmed || isRec || isCount);
      }
      if (statusBadge) {
        var text = 'Ready';
        var cls = 'status-ready';
        if (isRec) { text = '● RECORDING'; cls = 'status-rec'; }
        else if (isCount) { text = 'COUNT-IN'; cls = 'status-count'; }
        else if (isArmed) { text = 'ARMED'; cls = 'status-armed'; }
        statusBadge.textContent = text;
        statusBadge.className = 'rec-status-badge ' + cls;
      }
    },

    renderTakesList: function () {
      var container = document.getElementById('rec-takes-list');
      if (!container) { return; }
      if (this.sessionTakes.length === 0) {
        container.innerHTML = '<div class="rec-no-takes">No recorded takes yet. Press Record or Space and sing, hum or play your melody.</div>';
        return;
      }

      var self = this;
      var html = this.sessionTakes.map(function (take) {
        var isPlaying = self.previewPlayingId === take.id;
        var durStr = Math.round(take.duration) + 's';
        var tuneBadge = '';
        if (take.instrument) {
          tuneBadge = '<span class="rec-tune-tag" title="Played on an instrument">Instrument</span>';
        } else if (take.autotuneStatus === 'tuning') {
          tuneBadge = '<span class="rec-tune-tag tuning">Tuning…</span>';
        } else if (take.autotuneStatus === 'done') {
          var label = take.isTuned ? '✓ Autotuned' : 'Raw Pitch';
          var titleHint = take.isTuned ? 'Autotuned (click to audition Raw Pitch)' : 'Raw Pitch (click to audition Autotuned)';
          tuneBadge = '<button type="button" class="rec-tune-toggle' + (take.isTuned ? ' active' : '') + '" onclick="window.Recorder.toggleTakeTuning(\'' + take.id + '\')" title="' + titleHint + '">' + label + '</button>';
        } else if (take.autotuneStatus === 'no_voice') {
          tuneBadge = '<span class="rec-tune-tag muted" title="Pitch detector found no singing or humming in this take">No voice detected</span>' +
            '<button type="button" class="rec-tune-action" onclick="window.Recorder.applyAutotune(\'' + take.id + '\')" title="Retry autotune on this take">Retry</button>';
        } else if (take.autotuneStatus === 'failed') {
          tuneBadge = '<span class="rec-tune-tag err" title="' + self.esc(take.tuneError || 'Error') + '">Error</span>' +
            '<button type="button" class="rec-tune-action" onclick="window.Recorder.applyAutotune(\'' + take.id + '\')" title="Retry autotune">Retry</button>';
        } else {
          tuneBadge = '<button type="button" class="rec-tune-action" onclick="window.Recorder.applyAutotune(\'' + take.id + '\')" title="Snap sung pitch to nearest semitones (plays tuned audio upon completion)">Autotune</button>';
        }

        var tuneInfo = '';
        if (take.autotuneStatus === 'done' && take.tuneStats) {
          var sName = take.tuneStats.scale ? (take.tuneStats.scale.charAt(0).toUpperCase() + take.tuneStats.scale.slice(1)) : '';
          tuneInfo = '<span class="rec-tune-info" title="' + take.tuneStats.notesAdjusted + ' notes snapped to ' + take.tuneStats.root + ' ' + sName + '">(' + take.tuneStats.root + ' ' + sName + ' &middot; ' + take.tuneStats.notesAdjusted + ' tuned)</span>';
        }

        return '<div class="rec-take-card' + (self.activeTakeId === take.id ? ' active' : '') + '">' +
          '<div class="rec-take-meta">' +
            '<button type="button" class="rec-play-btn' + (isPlaying ? ' playing' : '') + '" onclick="window.Recorder.' + (isPlaying ? 'stopPreview()' : 'playTake(\'' + take.id + '\')') + '">' +
              (isPlaying ? '■' : '▶') +
            '</button>' +
            '<div class="rec-take-info">' +
              '<input type="text" class="rec-take-title-input" value="' + self.esc(take.title) + '" onchange="window.Recorder.renameTake(\'' + take.id + '\', this.value)">' +
              '<span class="rec-take-dur">' + durStr + '</span>' +
              tuneInfo +
            '</div>' +
          '</div>' +
          '<div class="rec-take-actions">' +
            tuneBadge +
            '<button type="button" id="rec-send-btn-' + take.id + '" class="rec-btn-use" onclick="window.Recorder.sendToCover(\'' + take.id + '\')" title="Add to Cover Sources">Use as Cover</button>' +
            '<button type="button" class="rec-btn-del" onclick="window.Recorder.deleteTake(\'' + take.id + '\')" title="Delete this take">&times;</button>' +
          '</div>' +
        '</div>';
      }).join('');

      container.innerHTML = html;
    },

    renameTake: function (takeId, newTitle) {
      var take = this.takeById(takeId);
      if (take && newTitle && newTitle.trim()) {
        take.title = newTitle.trim();
      }
    },

    esc: function (str) {
      return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
  };

  window.Recorder = Recorder;
  document.addEventListener('DOMContentLoaded', function () {
    Recorder.init();
  });
})();
