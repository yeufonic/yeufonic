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
    inputMode: 'mic', // extensible for 'midi' in future

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
      countInBars: 1, // 1 bar (4 beats), 2 bars, or 0
      beatsPerBar: 4,
      timerId: null,
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
      this.bindDOM();
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

        // Direct microphone input with zero echo/noise suppression latency
        if (!this.micStream) {
          this.micStream = await navigator.mediaDevices.getUserMedia({
            audio: {
              echoCancellation: false,
              noiseSuppression: false,
              autoGainControl: false,
              channelCount: 1
            }
          });
        }

        this.micSource = this.audioCtx.createMediaStreamSource(this.micStream);

        // Low-latency direct monitor path: mic -> monitorGain -> destination
        this.monitorGain = this.audioCtx.createGain();
        this.monitorGain.gain.value = this.monitorEnabled ? this.monitorVolume : 0.0;
        this.micSource.connect(this.monitorGain);
        this.monitorGain.connect(this.audioCtx.destination);

        // VU Analyser
        this.analyser = this.audioCtx.createAnalyser();
        this.analyser.fftSize = 512;
        this.micSource.connect(this.analyser);

        this.state = 'armed';
        this.updateTransportUI();
        this.startMeterLoop();
      } catch (err) {
        console.error('Failed to arm microphone:', err);
        var errEl = document.getElementById('rec-error-msg');
        if (errEl) {
          errEl.textContent = 'Could not access microphone: ' + (err.message || err);
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

    setMonitor: function (enabled, volume) {
      this.monitorEnabled = Boolean(enabled);
      if (typeof volume === 'number') { this.monitorVolume = volume; }
      if (this.monitorGain) {
        this.monitorGain.gain.value = this.monitorEnabled ? this.monitorVolume : 0.0;
      }
      var monBtn = document.getElementById('rec-monitor-btn');
      if (monBtn) {
        monBtn.classList.toggle('active', this.monitorEnabled);
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
      noteEl.textContent = noteName + octave + ' (' + Math.round(freq) + ' Hz ' + sign + cents + '¢)';
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
        var now = this.audioCtx.currentTime;

        var osc = this.audioCtx.createOscillator();
        var oscHarmonic = this.audioCtx.createOscillator();
        var gain = this.audioCtx.createGain();

        // Warm musical tone with clear harmonic definition
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now);

        oscHarmonic.type = 'sine';
        oscHarmonic.frequency.setValueAtTime(freq * (accent ? 1.0 : 2.0), now);

        var dur = accent ? 0.24 : 0.16;
        var peak = accent ? 0.65 : 0.45;

        gain.gain.setValueAtTime(0.001, now);
        gain.gain.linearRampToValueAtTime(peak, now + 0.012);
        gain.gain.setValueAtTime(peak * 0.75, now + dur * 0.35);
        gain.gain.exponentialRampToValueAtTime(0.001, now + dur);

        osc.connect(gain);
        oscHarmonic.connect(gain);
        gain.connect(this.audioCtx.destination);

        osc.start(now);
        oscHarmonic.start(now);
        osc.stop(now + dur + 0.02);
        oscHarmonic.stop(now + dur + 0.02);
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
      if (!this.audioCtx) {
        this.audioCtx = new AudioContextClass();
      }
      if (this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }

      var root = (this.autotune && this.autotune.root) || 'C';
      var freq = this.getRootFrequency(root, 4);

      var now = this.audioCtx.currentTime;
      var osc1 = this.audioCtx.createOscillator();
      var osc2 = this.audioCtx.createOscillator();
      var gain = this.audioCtx.createGain();

      // Fundamental in octave 4 (e.g. C4 = 261.6Hz, A4 = 440Hz)
      osc1.type = 'triangle';
      osc1.frequency.setValueAtTime(freq, now);

      // Sub-octave for warmth and pleasant timbre
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(freq * 0.5, now);

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.45, now + 0.025);
      gain.gain.setValueAtTime(0.4, now + 0.5);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.95);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + 1.0);
      osc2.stop(now + 1.0);

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

    toggleAutotune: function (forceVal) {
      var btn = document.getElementById('rec-auto-toggle');
      var on = forceVal !== undefined ? forceVal : !this.autotune.enabled;
      this.autotune.enabled = on;
      if (btn) {
        btn.classList.toggle('active', on);
        btn.textContent = on ? 'On' : 'Off';
      }
      if (on) {
        this.auditionRootNote();
      }
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
      var totalBeats = bars * this.metronome.beatsPerBar;
      var intervalMs = (60 / this.metronome.bpm) * 1000;
      var count = totalBeats;

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

      function beat() {
        var beatNum = ((totalBeats - count) % self.metronome.beatsPerBar) + 1;
        self.playCountInClick(beatNum === 1);
        if (numEl) {
          numEl.textContent = String(beatNum);
          numEl.classList.remove('pulse');
          void numEl.offsetWidth; // retrigger css animation
          numEl.classList.add('pulse');
        }
        count--;
        if (count >= 0) {
          self.metronome.timerId = setTimeout(beat, intervalMs);
        } else {
          if (overlay) { overlay.classList.add('hidden'); }
          self.startRecordingImmediate();
        }
      }
      beat();
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
        var bCount = 0;
        self.metronome.recTimerId = setInterval(function () {
          if (self.state !== 'recording') {
            clearInterval(self.metronome.recTimerId);
            return;
          }
          self.playClick(bCount % self.metronome.beatsPerBar === 0);
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

      this.micSource.connect(this.processorNode);
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
      var take = {
        id: takeId,
        title: 'Vocal Melody Take ' + takeNum,
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
      if (this.autotune.enabled) {
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
        take.autotuneStatus = 'done';
        take.isTuned = true;
      } catch (err) {
        console.error('Autotune processing failed:', err);
        take.autotuneStatus = 'failed';
      }
      this.renderTakesList();
    },

    toggleTakeTuning: function (takeId) {
      var take = this.takeById(takeId);
      if (!take || !take.tunedBlob) { return; }
      take.isTuned = !take.isTuned;
      if (this.previewPlayingId === takeId) {
        this.playTake(takeId);
      }
      this.renderTakesList();
    },

    // ------------------------------------------------- Audition / Preview
    playTake: function (takeId) {
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
      var title = take.title || 'Vocal Melody';

      var form = new FormData();
      form.append('file', blobToSave, 'melody.wav');
      form.append('title', title);
      form.append('origin', 'recording');

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
        container.innerHTML = '<div class="rec-no-takes">No recorded takes yet. Arm the microphone and press Record or Space to sing your melody.</div>';
        return;
      }

      var self = this;
      var html = this.sessionTakes.map(function (take) {
        var isPlaying = self.previewPlayingId === take.id;
        var durStr = Math.round(take.duration) + 's';
        var tuneBadge = '';
        if (take.autotuneStatus === 'tuning') {
          tuneBadge = '<span class="rec-tune-tag tuning">Tuning…</span>';
        } else if (take.autotuneStatus === 'done') {
          var label = take.isTuned ? 'Autotuned' : 'Raw Pitch';
          tuneBadge = '<button type="button" class="rec-tune-toggle' + (take.isTuned ? ' active' : '') + '" onclick="window.Recorder.toggleTakeTuning(\'' + take.id + '\')" title="Toggle A/B Autotune preview">' + label + '</button>';
        } else {
          tuneBadge = '<button type="button" class="rec-tune-action" onclick="window.Recorder.applyAutotune(\'' + take.id + '\')" title="Snap sung pitch to nearest semitones">Autotune</button>';
        }

        return '<div class="rec-take-card' + (self.activeTakeId === take.id ? ' active' : '') + '">' +
          '<div class="rec-take-meta">' +
            '<button type="button" class="rec-play-btn' + (isPlaying ? ' playing' : '') + '" onclick="window.Recorder.' + (isPlaying ? 'stopPreview()' : 'playTake(\'' + take.id + '\')') + '">' +
              (isPlaying ? '■' : '▶') +
            '</button>' +
            '<div class="rec-take-info">' +
              '<input type="text" class="rec-take-title-input" value="' + self.esc(take.title) + '" onchange="window.Recorder.renameTake(\'' + take.id + '\', this.value)">' +
              '<span class="rec-take-dur">' + durStr + '</span>' +
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
