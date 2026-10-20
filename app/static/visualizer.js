/* ==============================================================
   Yeufonic Audio Visualizer & Synced Lyrics Engine
   High-performance WebGL / Canvas2D real-time visualizer,
   ambient mini player backdrop, Hipgnosis album cover integration,
   and synchronised lyrics display.
   ============================================================== */

(function (window, document) {
  'use strict';

  function $(id) { return document.getElementById(id); }
  function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

  var Visualizer = {
    isOpen: false,
    currentTake: null,
    mode: 'wave', // 'wave', 'aurora', 'cosmic', 'kaleidoscope'
    artMode: 'sleeve', // 'sleeve', 'aura', 'off'
    showLyrics: true,
    miniEnabled: true,
    fpsCap: 60,

    // Audio Analysis State
    audioCtx: null,
    analyser: null,
    dataFreq: null,
    dataTime: null,
    bassEnergy: 0,
    midEnergy: 0,
    trebleEnergy: 0,
    beatDetected: false,
    lastBeatTime: 0,
    beatThreshold: 0.15,

    // Rendering animation frame IDs
    fullAnimId: null,
    miniAnimId: null,
    lastFrameTime: 0,

    // Synced lyrics data
    lyricsLines: [],
    activeLineIdx: -1,

    // Stars for cosmic mode
    stars: null,

    /* ------------------------------------------------------------- Initialisation */
    init: function () {
      this.loadSettings();
      this.wireElements();
      this.initCosmicStars();
      this.startMini();
    },

    loadSettings: function () {
      try {
        var savedMode = localStorage.getItem('yue2.vis.mode');
        if (savedMode) { this.mode = savedMode; }
        var savedArt = localStorage.getItem('yue2.vis.artMode');
        if (savedArt) { this.artMode = savedArt; }
        var savedLyrics = localStorage.getItem('yue2.vis.lyrics');
        if (savedLyrics !== null) { this.showLyrics = savedLyrics === '1'; }
        var savedMini = localStorage.getItem('yue2.vis.mini');
        if (savedMini !== null) { this.miniEnabled = savedMini === '1'; }
      } catch (e) { /* ignore storage errors */ }
    },

    saveSettings: function () {
      try {
        localStorage.setItem('yue2.vis.mode', this.mode);
        localStorage.setItem('yue2.vis.artMode', this.artMode);
        localStorage.setItem('yue2.vis.lyrics', this.showLyrics ? '1' : '0');
        localStorage.setItem('yue2.vis.mini', this.miniEnabled ? '1' : '0');
      } catch (e) { /* ignore */ }
    },

    /* ------------------------------------------------------------- Audio Hook */
    ensureAudioNode: function () {
      var audio = $('audio');
      if (!audio) { return false; }

      // Prefer sharing Rack's AudioContext and Analyser
      if (window.RackEngine && window.RackEngine.ctx) {
        this.audioCtx = window.RackEngine.ctx;
        if (window.RackEngine.analyser) {
          this.analyser = window.RackEngine.analyser;
        }
      }

      if (!this.audioCtx) {
        var AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) { return false; }
        this.audioCtx = new AudioCtx();
      }

      if (!this.analyser) {
        this.analyser = this.audioCtx.createAnalyser();
        this.analyser.fftSize = 512;
        this.analyser.smoothingTimeConstant = 0.8;
        if (window.RackEngine && window.RackEngine.sourceNode) {
          try { window.RackEngine.sourceNode.connect(this.analyser); } catch (e) {}
        }
      }

      if (!this.dataFreq || this.dataFreq.length !== this.analyser.frequencyBinCount) {
        this.dataFreq = new Uint8Array(this.analyser.frequencyBinCount);
        this.dataTime = new Uint8Array(this.analyser.fftSize);
      }
      return true;
    },

    updateAudioMetrics: function () {
      if (!this.analyser || !this.dataFreq) { return; }
      this.analyser.getByteFrequencyData(this.dataFreq);
      this.analyser.getByteTimeDomainData(this.dataTime);

      var bins = this.dataFreq.length;
      if (!bins) { return; }

      // Bass: 20Hz - 160Hz (~first 8% of bins)
      var bassCount = Math.max(2, Math.floor(bins * 0.08));
      var bassSum = 0;
      for (var b = 0; b < bassCount; b++) { bassSum += this.dataFreq[b]; }
      var rawBass = bassSum / (bassCount * 255);

      // Mid: 300Hz - 2500Hz (~8% to ~35% of bins)
      var midStart = bassCount;
      var midEnd = Math.floor(bins * 0.35);
      var midSum = 0;
      for (var m = midStart; m < midEnd; m++) { midSum += this.dataFreq[m]; }
      var rawMid = midSum / ((midEnd - midStart || 1) * 255);

      // Treble: 3000Hz+ (~35% to ~85% of bins)
      var trebStart = midEnd;
      var trebEnd = Math.floor(bins * 0.85);
      var trebSum = 0;
      for (var t = trebStart; t < trebEnd; t++) { trebSum += this.dataFreq[t]; }
      var rawTreb = trebSum / ((trebEnd - trebStart || 1) * 255);

      // Smooth with envelope followers
      this.bassEnergy = this.bassEnergy * 0.7 + rawBass * 0.3;
      this.midEnergy = this.midEnergy * 0.75 + rawMid * 0.25;
      this.trebleEnergy = this.trebleEnergy * 0.8 + rawTreb * 0.2;

      // Transient beat detection
      var now = performance.now();
      if (rawBass > this.bassEnergy * 1.35 && rawBass > 0.35 && now - this.lastBeatTime > 220) {
        this.beatDetected = true;
        this.lastBeatTime = now;
      } else {
        this.beatDetected = false;
      }
    },

    /* ------------------------------------------------------------- DOM & UI Wiring */
    wireElements: function () {
      var self = this;
      var btnVis = $('btn-visualizer');
      if (btnVis) {
        btnVis.addEventListener('click', function () {
          self.toggle();
        });
      }

      var modal = $('visualizer-modal');
      if (modal) {
        var closeBtn = $('vis-btn-close');
        if (closeBtn) {
          closeBtn.addEventListener('click', function () { self.toggle(false); });
        }

        var fsBtn = $('vis-btn-fullscreen');
        if (fsBtn) {
          fsBtn.addEventListener('click', function () { self.toggleFullscreen(); });
        }

        var artBtn = $('vis-btn-art');
        if (artBtn) {
          artBtn.addEventListener('click', function () { self.cycleArtMode(); });
        }

        var lyricsBtn = $('vis-btn-lyrics');
        if (lyricsBtn) {
          lyricsBtn.addEventListener('click', function () { self.toggleLyrics(); });
        }

        // Mode switch buttons
        var modeBtns = modal.querySelectorAll('.vis-mode-btn');
        Array.prototype.forEach.call(modeBtns, function (btn) {
          btn.addEventListener('click', function () {
            self.setMode(btn.dataset.mode);
          });
        });

        // Hide controls on mouse idle
        var idleTimer = null;
        modal.addEventListener('mousemove', function () {
          modal.classList.remove('idle');
          clearTimeout(idleTimer);
          idleTimer = setTimeout(function () {
            if (self.isOpen) { modal.classList.add('idle'); }
          }, 3200);
        });

        // Click outside controls toggles play
        var canvas = $('visualizer-canvas');
        if (canvas) {
          canvas.addEventListener('click', function (e) {
            if (e.target === canvas) {
              var playBtn = $('btn-play');
              if (playBtn) { playBtn.click(); }
            }
          });
        }
      }

      window.addEventListener('resize', function () {
        if (self.isOpen) { self.resizeFull(); }
        self.resizeMini();
      });

      // Hook audio play/pause events
      var audio = $('audio');
      if (audio) {
        audio.addEventListener('play', function () {
          self.ensureAudioNode();
          self.startMini();
        });
        audio.addEventListener('timeupdate', function () {
          if (self.isOpen && self.hasTimings) { self.updateLyrics(audio.currentTime); }
        });
        audio.addEventListener('loadedmetadata', function () {
          if (self.currentTake) {
            self.parseLyrics();
            if (self.isOpen) { self.updateLyricsDisplay(); }
          }
        });
        audio.addEventListener('durationchange', function () {
          if (self.currentTake) {
            self.parseLyrics();
            if (self.isOpen) { self.updateLyricsDisplay(); }
          }
        });
      }
    },

    /* ------------------------------------------------------------- Modal Toggle */
    toggle: function (forceOpen) {
      var next = forceOpen !== undefined ? Boolean(forceOpen) : !this.isOpen;
      if (next === this.isOpen) { return; }
      this.isOpen = next;

      var modal = $('visualizer-modal');
      var btnVis = $('btn-visualizer');
      if (btnVis) { btnVis.classList.toggle('active', this.isOpen); }

      if (modal) {
        modal.classList.toggle('hidden', !this.isOpen);
        modal.setAttribute('aria-hidden', String(!this.isOpen));
      }

      document.body.classList.toggle('visualizer-open', this.isOpen);

      if (this.isOpen) {
        this.ensureAudioNode();
        this.resizeFull();
        this.updateTakeInfo();
        this.updateButtonsState();
        this.startFull();
      } else {
        this.stopFull();
        if (document.fullscreenElement) {
          try { document.exitFullscreen(); } catch (e) {}
        }
      }
    },

    toggleFullscreen: function () {
      var modal = $('visualizer-modal');
      if (!modal) { return; }
      if (!document.fullscreenElement) {
        if (modal.requestFullscreen) { modal.requestFullscreen().catch(function () {}); }
      } else {
        if (document.exitFullscreen) { document.exitFullscreen().catch(function () {}); }
      }
    },

    setMode: function (mode) {
      if (!mode) { return; }
      this.mode = mode;
      this.saveSettings();
      this.updateButtonsState();
    },

    cycleArtMode: function () {
      var modes = ['sleeve', 'aura', 'off'];
      var idx = modes.indexOf(this.artMode);
      this.artMode = modes[(idx + 1) % modes.length];
      this.saveSettings();
      this.updateButtonsState();
      this.updateArtworkDisplay();
    },

    toggleLyrics: function () {
      this.showLyrics = !this.showLyrics;
      this.saveSettings();
      this.updateButtonsState();
      this.updateLyricsDisplay();
    },

    updateButtonsState: function () {
      var modal = $('visualizer-modal');
      if (!modal) { return; }
      var modeBtns = modal.querySelectorAll('.vis-mode-btn');
      var self = this;
      Array.prototype.forEach.call(modeBtns, function (btn) {
        btn.classList.toggle('active', btn.dataset.mode === self.mode);
      });

      var artBtn = $('vis-btn-art');
      if (artBtn) {
        artBtn.textContent = 'Artwork: ' + (this.artMode === 'sleeve' ? 'Sleeve' : (this.artMode === 'aura' ? 'Aura' : 'Off'));
        artBtn.classList.toggle('active', this.artMode !== 'off');
      }

      var lyricsBtn = $('vis-btn-lyrics');
      if (lyricsBtn) {
        lyricsBtn.textContent = 'Lyrics: ' + (this.showLyrics ? 'On' : 'Off');
        lyricsBtn.classList.toggle('active', this.showLyrics);
      }
    },

    /* ------------------------------------------------------------- Take Metadata & Synced Lyrics */
    setTake: function (take) {
      this.currentTake = take || null;
      this.parseLyrics();
      if (this.isOpen) {
        this.updateTakeInfo();
        this.updateArtworkDisplay();
        this.updateLyricsDisplay();
      }
    },

    updateTakeInfo: function () {
      var take = this.currentTake;
      var titleEl = $('vis-title');
      var metaEl = $('vis-meta');
      if (titleEl) {
        titleEl.textContent = take ? (take.title || 'Untitled Take') : 'Nothing playing';
      }
      if (metaEl) {
        metaEl.textContent = take && take.style ? take.style : '';
      }
      this.updateArtworkDisplay();
      this.updateLyricsDisplay();
    },

    updateArtworkDisplay: function () {
      var wrap = $('vis-art-wrap');
      var img = $('vis-cover-img');
      var record = $('vis-vinyl-record');
      var aura = $('vis-art-aura');
      if (!wrap) { return; }

      var take = this.currentTake;
      var artUrl = take && take.art ? take.art : null;

      if (!artUrl || this.artMode === 'off') {
        wrap.classList.add('hidden');
        if (aura) { aura.classList.add('hidden'); }
        return;
      }

      wrap.classList.remove('hidden');
      wrap.classList.toggle('mode-sleeve', this.artMode === 'sleeve');
      wrap.classList.toggle('mode-aura', this.artMode === 'aura');

      if (img && img.src !== artUrl) {
        img.src = artUrl;
      }
      if (aura) {
        aura.classList.toggle('hidden', this.artMode !== 'aura');
        if (aura.style.backgroundImage !== 'url("' + artUrl + '")') {
          aura.style.backgroundImage = 'url("' + artUrl + '")';
        }
      }
    },

    parseLyrics: function () {
      this.lyricsLines = [];
      this.activeLineIdx = -1;
      this.hasTimings = false;
      var take = this.currentTake;
      if (!take || !take.lyrics) { return; }

      var raw = String(take.lyrics).split(/\r?\n/);
      var lrcRegex = /^\[(\d{1,2}):(\d{2}(?:\.\d+)?)\](.*)$/;
      var outLines = [];
      var lineIdx = 0;
      var foundTimed = false;

      // Check if explicit LRC timestamps exist
      for (var i = 0; i < raw.length; i++) {
        var trimmed = raw[i].trim();
        if (trimmed && lrcRegex.test(trimmed)) {
          foundTimed = true;
          break;
        }
      }

      if (foundTimed) {
        // Explicitly timed lyrics (karaoke mode)
        for (var j = 0; j < raw.length; j++) {
          var line = raw[j].trim();
          if (!line || line.charAt(0) === '%') { continue; }
          var match = line.match(lrcRegex);
          if (match) {
            var timeSec = parseInt(match[1], 10) * 60 + parseFloat(match[2]);
            var text = match[3].trim();
            var secMatch = text.match(/^\[(.*)\]$/);
            var isSec = Boolean(secMatch);
            outLines.push({
              id: lineIdx++,
              text: isSec ? secMatch[1].trim() : text,
              isSection: isSec,
              isCue: false,
              startTime: timeSec,
              endTime: timeSec + 4.0
            });
          }
        }
        for (var k = 0; k < outLines.length; k++) {
          if (outLines[k + 1]) {
            outLines[k].endTime = outLines[k + 1].startTime;
          }
        }
        this.hasTimings = outLines.length > 0;
      } else {
        // Clean untimed lyric sheet mode: readable presentation, no false highlighting
        for (var n = 0; n < raw.length; n++) {
          var plain = raw[n].trim();
          if (!plain || plain.charAt(0) === '%') { continue; }
          var sMatch = plain.match(/^\[(.*)\]$/);
          if (sMatch) {
            outLines.push({
              id: lineIdx++,
              text: sMatch[1].trim(),
              isSection: true,
              isCue: false
            });
          } else {
            var isCue = /^\(.*\)$/.test(plain);
            outLines.push({
              id: lineIdx++,
              text: plain,
              isSection: false,
              isCue: isCue
            });
          }
        }
        this.hasTimings = false;
      }

      this.lyricsLines = outLines;
    },

    updateLyricsDisplay: function () {
      var wrap = $('vis-lyrics-wrap');
      var list = $('vis-lyrics-list');
      if (!wrap || !list) { return; }

      if (!this.showLyrics || !this.lyricsLines.length) {
        wrap.classList.add('hidden');
        return;
      }

      wrap.classList.remove('hidden');
      wrap.classList.toggle('vis-lyrics-timed', Boolean(this.hasTimings));

      var html = '';
      for (var i = 0; i < this.lyricsLines.length; i++) {
        var line = this.lyricsLines[i];
        var cls = line.isSection ? 'vis-lyric-sec' : (line.isCue ? 'vis-lyric-cue' : 'vis-lyric-line');
        html += '<div class="' + cls + '" id="vis-line-' + line.id + '" data-idx="' + i + '">' +
                  escapeHtml(line.text) +
                '</div>';
      }
      list.innerHTML = html;
      list.scrollTop = 0;
    },

    updateLyrics: function (currentTime) {
      if (!this.showLyrics || !this.hasTimings || !this.lyricsLines || !this.lyricsLines.length) {
        return;
      }
      var active = -1;
      var activeSecIdx = -1;

      for (var i = 0; i < this.lyricsLines.length; i++) {
        var l = this.lyricsLines[i];
        if (l.isSection) {
          if (currentTime >= l.startTime && currentTime <= l.endTime) {
            activeSecIdx = i;
          }
          continue;
        }
        var activeEnd = l.activeUntil || (l.endTime + 0.5);
        if (currentTime >= l.startTime && currentTime < activeEnd) {
          active = i;
          break;
        }
      }

      if (active === -1 && this.activeLineIdx >= 0) {
        var prevL = this.lyricsLines[this.activeLineIdx];
        if (prevL && !prevL.isSection) {
          var holdEnd = prevL.activeUntil || (prevL.endTime + 2.5);
          if (currentTime >= prevL.startTime && currentTime < holdEnd) {
            active = this.activeLineIdx;
          }
        }
      }

      if (active === this.activeLineIdx) { return; }
      this.activeLineIdx = active;

      var list = $('vis-lyrics-list');
      if (!list) { return; }

      var all = list.querySelectorAll('.vis-lyric-line, .vis-lyric-sec, .vis-lyric-cue');
      var activeItem = (active >= 0) ? this.lyricsLines[active] : null;

      var self = this;
      Array.prototype.forEach.call(all, function (el, idx) {
        var item = self.lyricsLines[idx];
        if (!item) { return; }
        if (item.isSection) {
          var isCurSec = (activeSecIdx === idx) ||
            (activeItem && item.id < activeItem.id && (!self.lyricsLines[idx + 1] || self.lyricsLines[idx + 1].id <= activeItem.id));
          el.classList.toggle('current', Boolean(isCurSec));
        } else {
          var isAct = (idx === active);
          var isPast = active >= 0 ? (idx < active) : (item.endTime < currentTime);
          el.classList.toggle('active', isAct);
          el.classList.toggle('past', isPast);
        }
      });

      var activeEl = $('vis-line-' + (activeItem ? activeItem.id : -1));
      if (activeEl) {
        var targetY = activeEl.offsetTop - (list.clientHeight / 2) + (activeEl.clientHeight / 2);
        list.scrollTo({ top: Math.max(0, targetY), behavior: 'smooth' });
      }
    },

    /* ------------------------------------------------------------- Full Visualizer Render */
    resizeFull: function () {
      var canvas = $('visualizer-canvas');
      if (!canvas) { return; }
      var dpr = window.devicePixelRatio || 1;
      var w = window.innerWidth;
      var h = window.innerHeight;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
    },

    startFull: function () {
      if (this.fullAnimId) { cancelAnimationFrame(this.fullAnimId); }
      var self = this;
      function loop(now) {
        if (!self.isOpen) { return; }
        self.renderFullFrame(now);
        self.fullAnimId = requestAnimationFrame(loop);
      }
      this.fullAnimId = requestAnimationFrame(loop);
    },

    stopFull: function () {
      if (this.fullAnimId) {
        cancelAnimationFrame(this.fullAnimId);
        this.fullAnimId = null;
      }
    },

    renderFullFrame: function (now) {
      this.updateAudioMetrics();

      var audio = $('audio');
      if (this.showLyrics && this.hasTimings && audio && !audio.paused && this.lyricsLines.length) {
        this.updateLyrics(audio.currentTime);
      }

      var canvas = $('visualizer-canvas');
      if (!canvas) { return; }
      var ctx = canvas.getContext('2d');
      if (!ctx) { return; }

      var dpr = window.devicePixelRatio || 1;
      var w = canvas.width / dpr;
      var h = canvas.height / dpr;

      ctx.save();
      ctx.scale(dpr, dpr);

      // Render selected visualizer mode
      switch (this.mode) {
        case 'aurora':
          this.renderAurora(ctx, w, h, now);
          break;
        case 'cosmic':
          this.renderCosmic(ctx, w, h, now);
          break;
        case 'kaleidoscope':
          this.renderKaleidoscope(ctx, w, h, now);
          break;
        case 'wave':
        default:
          this.renderWave(ctx, w, h, now);
          break;
      }

      ctx.restore();

      // Dynamic reactive transform on Vinyl Sleeve
      this.applyArtworkDynamics();
    },

    applyArtworkDynamics: function () {
      var sleeve = $('vis-art-sleeve');
      var record = $('vis-vinyl-record');
      if (!sleeve) { return; }

      var scale = 1.0 + this.bassEnergy * 0.08;
      var rot = (performance.now() * 0.015) % 360;
      var shadowBlur = 24 + this.bassEnergy * 40;
      var shadowSpread = 4 + this.bassEnergy * 15;

      sleeve.style.transform = 'scale(' + scale.toFixed(3) + ')';
      sleeve.style.boxShadow = '0 20px ' + shadowBlur.toFixed(1) + 'px ' + shadowSpread.toFixed(1) + 'px rgba(0, 0, 0, 0.7), 0 0 ' + (shadowBlur * 1.5).toFixed(1) + 'px rgba(168, 85, 247, ' + (this.bassEnergy * 0.6).toFixed(2) + ')';

      if (record) {
        record.style.transform = 'translateX(' + (this.bassEnergy * 18).toFixed(1) + 'px) rotate(' + rot.toFixed(1) + 'deg)';
      }
    },

    /* Mode 1: Multi-Harmonic Wave Ribbon */
    renderWave: function (ctx, w, h, now) {
      // Background with trail decay
      ctx.fillStyle = 'rgba(7, 7, 13, 0.28)';
      ctx.fillRect(0, 0, w, h);

      var time = now * 0.0015;
      var cy = h * 0.5;
      var points = 160;
      var step = w / points;

      var bassMod = 1.0 + this.bassEnergy * 2.2;
      var midMod = 1.0 + this.midEnergy * 1.8;

      var waves = [
        { amp: 65 * bassMod, freq: 0.012, speed: 2.2, color: 'rgba(168, 85, 247, 0.75)', blur: 22 },
        { amp: 45 * midMod, freq: 0.018, speed: -1.7, color: 'rgba(56, 189, 248, 0.65)', blur: 16 },
        { amp: 30 * (1.0 + this.trebleEnergy * 3.0), freq: 0.026, speed: 3.1, color: 'rgba(236, 72, 153, 0.55)', blur: 12 },
        { amp: 20, freq: 0.04, speed: -2.8, color: 'rgba(52, 211, 153, 0.45)', blur: 8 }
      ];

      for (var wi = 0; wi < waves.length; wi++) {
        var wave = waves[wi];
        ctx.beginPath();
        ctx.shadowBlur = wave.blur;
        ctx.shadowColor = wave.color;
        ctx.strokeStyle = wave.color;
        ctx.lineWidth = 3.5;

        for (var i = 0; i <= points; i++) {
          var x = i * step;
          var audioDelta = 0;
          if (this.dataTime && this.dataTime.length) {
            var sampleIdx = Math.floor((i / points) * this.dataTime.length);
            audioDelta = ((this.dataTime[sampleIdx] - 128) / 128) * (wave.amp * 0.8);
          }
          var y = cy + Math.sin(x * wave.freq + time * wave.speed) * wave.amp +
                       Math.cos(x * wave.freq * 0.5 - time * 0.8) * (wave.amp * 0.4) +
                       audioDelta;
          if (i === 0) { ctx.moveTo(x, y); } else { ctx.lineTo(x, y); }
        }
        ctx.stroke();
      }
      ctx.shadowBlur = 0;
    },

    /* Mode 2: Chromatic Aurora Frequency Spectrum */
    renderAurora: function (ctx, w, h, now) {
      ctx.fillStyle = 'rgba(5, 5, 10, 0.35)';
      ctx.fillRect(0, 0, w, h);

      if (!this.dataFreq || !this.dataFreq.length) { return; }
      var bars = 64;
      var barWidth = (w / bars) * 0.75;
      var gap = (w / bars) * 0.25;

      var maxH = h * 0.65;
      var baseH = h * 0.88;

      for (var i = 0; i < bars; i++) {
        var dataIdx = Math.floor(Math.pow(i / bars, 1.4) * (this.dataFreq.length * 0.75));
        var val = (this.dataFreq[dataIdx] || 0) / 255;
        var barH = val * maxH + 4;
        var x = i * (barWidth + gap) + gap * 0.5;
        var y = baseH - barH;

        var hue = 180 + (i / bars) * 140; // Cyan -> Violet -> Pink
        var grad = ctx.createLinearGradient(x, y, x, baseH);
        grad.addColorStop(0, 'hsla(' + hue + ', 95%, 68%, 0.95)');
        grad.addColorStop(0.6, 'hsla(' + (hue + 20) + ', 85%, 55%, 0.7)');
        grad.addColorStop(1, 'hsla(' + hue + ', 80%, 40%, 0.15)');

        ctx.fillStyle = grad;
        ctx.shadowColor = 'hsla(' + hue + ', 90%, 65%, 0.8)';
        ctx.shadowBlur = 12 * val;
        ctx.fillRect(x, y, barWidth, barH);

        // Mirrored bottom reflection
        ctx.fillStyle = 'hsla(' + hue + ', 90%, 55%, ' + (val * 0.25).toFixed(2) + ')';
        ctx.fillRect(x, baseH + 2, barWidth, barH * 0.3);
      }
      ctx.shadowBlur = 0;
    },

    /* Mode 3: Cosmic Hyperspace */
    initCosmicStars: function () {
      this.stars = [];
      for (var i = 0; i < 280; i++) {
        this.stars.push({
          x: (Math.random() - 0.5) * 2000,
          y: (Math.random() - 0.5) * 2000,
          z: Math.random() * 1000 + 1,
          size: Math.random() * 2 + 1,
          color: i % 3 === 0 ? '#38bdf8' : (i % 3 === 1 ? '#c084fc' : '#f472b6')
        });
      }
    },

    renderCosmic: function (ctx, w, h, now) {
      ctx.fillStyle = 'rgba(4, 4, 8, 0.4)';
      ctx.fillRect(0, 0, w, h);

      if (!this.stars) { this.initCosmicStars(); }
      var cx = w * 0.5;
      var cy = h * 0.5;
      var speed = 4 + this.bassEnergy * 24;

      for (var i = 0; i < this.stars.length; i++) {
        var s = this.stars[i];
        s.z -= speed;
        if (s.z <= 1) {
          s.z = 1000;
          s.x = (Math.random() - 0.5) * 2000;
          s.y = (Math.random() - 0.5) * 2000;
        }

        var k = 250 / s.z;
        var px = s.x * k + cx;
        var py = s.y * k + cy;

        if (px >= 0 && px <= w && py >= 0 && py <= h) {
          var radius = Math.max(0.6, (1 - s.z / 1000) * s.size * 2.2);
          ctx.beginPath();
          ctx.arc(px, py, radius, 0, Math.PI * 2);
          ctx.fillStyle = s.color;
          ctx.shadowColor = s.color;
          ctx.shadowBlur = radius * 4;
          ctx.fill();
        }
      }
      ctx.shadowBlur = 0;
    },

    /* Mode 4: Geometric Kaleidoscope Mandala */
    renderKaleidoscope: function (ctx, w, h, now) {
      ctx.fillStyle = 'rgba(5, 5, 10, 0.25)';
      ctx.fillRect(0, 0, w, h);

      var cx = w * 0.5;
      var cy = h * 0.5;
      var petals = 8;
      var rot = now * 0.0006;
      var bassR = 60 + this.bassEnergy * 140;

      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(rot);

      for (var p = 0; p < petals; p++) {
        ctx.save();
        ctx.rotate((p * Math.PI * 2) / petals);

        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.bezierCurveTo(bassR * 0.5, -bassR * 0.6, bassR * 1.2, -bassR * 0.2, bassR * 1.5, 0);
        ctx.bezierCurveTo(bassR * 1.2, bassR * 0.2, bassR * 0.5, bassR * 0.6, 0, 0);

        var hue = (p * 45 + now * 0.04) % 360;
        ctx.fillStyle = 'hsla(' + hue + ', 85%, 60%, 0.45)';
        ctx.shadowColor = 'hsla(' + hue + ', 95%, 65%, 0.8)';
        ctx.shadowBlur = 18;
        ctx.fill();

        ctx.strokeStyle = 'hsla(' + (hue + 30) + ', 95%, 80%, 0.8)';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.restore();
      }
      ctx.restore();
      ctx.shadowBlur = 0;
    },

    /* ------------------------------------------------------------- Mini Player Backdrop */
    resizeMini: function () {
      var canvas = $('mini-vis');
      if (!canvas) { return; }
      var dpr = window.devicePixelRatio || 1;
      var rect = canvas.getBoundingClientRect();
      var w = Math.max(200, rect.width || window.innerWidth);
      var h = Math.max(40, rect.height || 64);
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
    },

    startMini: function () {
      if (this.miniAnimId) { return; }
      var self = this;
      function loop(now) {
        self.renderMiniFrame(now);
        self.miniAnimId = requestAnimationFrame(loop);
      }
      this.miniAnimId = requestAnimationFrame(loop);
    },

    stopMini: function () {
      if (this.miniAnimId) {
        cancelAnimationFrame(this.miniAnimId);
        this.miniAnimId = null;
      }
    },

    renderMiniFrame: function (now) {
      var canvas = $('mini-vis');
      if (!canvas || !this.miniEnabled) { return; }

      var audio = $('audio');
      var isPlaying = audio && !audio.paused && !audio.ended;

      var ctx = canvas.getContext('2d');
      if (!ctx) { return; }

      var dpr = window.devicePixelRatio || 1;
      var w = canvas.width / dpr;
      var h = canvas.height / dpr;

      ctx.clearRect(0, 0, w, h);

      if (!isPlaying) {
        // Draw resting baseline
        ctx.save();
        ctx.scale(dpr, dpr);
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.08)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, h * 0.5);
        ctx.lineTo(w, h * 0.5);
        ctx.stroke();
        ctx.restore();
        return;
      }

      this.updateAudioMetrics();

      ctx.save();
      ctx.scale(dpr, dpr);

      // Render ambient mirrored wave ribbon across the bottom player
      var points = 80;
      var step = w / points;
      var cy = h * 0.5;
      var time = now * 0.002;

      ctx.beginPath();
      for (var i = 0; i <= points; i++) {
        var x = i * step;
        var audioSample = 0;
        if (this.dataTime && this.dataTime.length) {
          var sIdx = Math.floor((i / points) * this.dataTime.length);
          audioSample = ((this.dataTime[sIdx] - 128) / 128) * (h * 0.38);
        }
        var waveY = Math.sin(x * 0.02 + time) * (h * 0.18 * (1.0 + this.bassEnergy * 1.5)) + audioSample;
        var y = cy + waveY;
        if (i === 0) { ctx.moveTo(x, y); } else { ctx.lineTo(x, y); }
      }

      var grad = ctx.createLinearGradient(0, 0, w, 0);
      grad.addColorStop(0, 'rgba(56, 189, 248, 0.25)');
      grad.addColorStop(0.5, 'rgba(168, 85, 247, 0.45)');
      grad.addColorStop(1, 'rgba(236, 72, 153, 0.25)');

      ctx.strokeStyle = grad;
      ctx.lineWidth = 2.5;
      ctx.shadowColor = 'rgba(168, 85, 247, 0.6)';
      ctx.shadowBlur = 10;
      ctx.stroke();

      ctx.restore();
    }
  };

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  window.Visualizer = Visualizer;

  // Auto-init on DOMContentLoaded or immediate
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { Visualizer.init(); });
  } else {
    Visualizer.init();
  }

})(window, document);
