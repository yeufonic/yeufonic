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
    mode: 'yeufonic', // 'yeufonic' is the fresh install's default; 'wave', 'aurora', 'cosmic', ...
    artMode: 'sleeve', // 'sleeve', 'aura', 'off'
    showLyrics: true,
    miniEnabled: true,
    fpsCap: 60,
    artPollTimer: null,
    lastArtCheckTime: 0,

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
    lyricsRenderedForTake: null,
    hasTimings: false,

    // Artwork animation & dynamic motion state
    artX: 0,
    artY: 0,
    lastDriftX: 0,
    lastDriftY: 0,
    lastDynamicsTime: 0,
    smoothBankX: 0,
    smoothBankY: 0,
    smoothSlideX: 65,
    vinylAngle: 0,
    vinylDegPerSec: 200,
    beatTarget: 0,
    beatImpulse: 0,
    ring1Scale: 1,
    ring1Opacity: 0,
    ring2Scale: 1,
    ring2Opacity: 0,

    // Additional visualizer mode states
    gridOffset: 0,
    liquidCanvas: null,
    swarmParticles: null,
    barLevels: null,
    barPeaks: null,
    barPeakTimes: null,

    // Stars for cosmic mode
    stars: null,

    /* ------------------------------------------------------------- Initialisation */
    init: function () {
      this.loadSettings();
      this.wireElements();
      this.initCosmicStars();
      this.initSwarmParticles();
      this.initBars();
      this.resizeMini();
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

    saveSettings: function (which) {
      try {
        localStorage.setItem('yue2.vis.mode', this.mode);
        localStorage.setItem('yue2.vis.artMode', this.artMode);
        localStorage.setItem('yue2.vis.lyrics', this.showLyrics ? '1' : '0');
        localStorage.setItem('yue2.vis.mini', this.miniEnabled ? '1' : '0');
      } catch (e) { /* ignore */ }

      // The page takes up a setting only when the server's value changes (adoptVisualizerSettings), so a choice made
      // here holds while its save is on the way, or if the save is refused.

      // Persist to backend settings
      if (typeof window.api === 'function') {
        if (!which || which === 'mode') {
          window.api('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: 'appearance.visualizer_mode', value: this.mode })
          }).catch(function () {});
        }
        if (!which || which === 'art') {
          window.api('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: 'appearance.visualizer_art', value: this.artMode })
          }).catch(function () {});
        }
        if (!which || which === 'mini') {
          window.api('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: 'appearance.mini_visualizer', value: this.miniEnabled ? 'on' : 'off' })
          }).catch(function () {});
        }
      }
    },

    /* ------------------------------------------------------------- Audio Hook */
    ensureAudioNode: function () {
      var audio = $('audio');
      if (!audio) { return false; }

      // Prefer sharing Rack's AudioContext and Analyser
      if (window.RackEngine && !window.RackEngine.ctx && typeof window.RackEngine.init === 'function') {
        try { window.RackEngine.init(); } catch (e) {}
      }
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

      if (this.audioCtx && this.audioCtx.state === 'suspended') {
        this.audioCtx.resume().catch(function () {});
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

        var lyricsClose = $('vis-lyrics-close');
        if (lyricsClose) {
          lyricsClose.addEventListener('click', function (e) {
            e.stopPropagation();
            self.toggleLyrics(false);
          });
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
              if (self.mode === 'yeufonic' && self.seekWaveStrip(e)) { return; }
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

      document.addEventListener('fullscreenchange', function () {
        if (self.isOpen) { self.resizeFull(); }
      });

      // Hook audio play/pause events
      var audio = $('audio');
      if (audio) {
        audio.addEventListener('play', function () {
          self.ensureAudioNode();
          self.startMini();
        });
        audio.addEventListener('pause', function () {
          self.renderMiniFrame(performance.now());
        });
        audio.addEventListener('ended', function () {
          self.renderMiniFrame(performance.now());
        });
        audio.addEventListener('timeupdate', function () {
          if (self.isOpen && self.hasTimings) { self.updateLyrics(audio.currentTime); }
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
      }
    },

    toggleFullscreen: function () {
      if (typeof window.toggleFullscreen === 'function') {
        window.toggleFullscreen();
        return;
      }
      var modal = $('visualizer-modal') || document.documentElement;
      if (!modal) { return; }
      if (!document.fullscreenElement) {
        if (modal.requestFullscreen) { modal.requestFullscreen().catch(function () {}); }
      } else {
        if (document.exitFullscreen) { document.exitFullscreen().catch(function () {}); }
      }
    },

    setMode: function (mode) {
      if (!mode || this.mode === mode) { return; }
      this.mode = mode;
      this.saveSettings('mode');
      this.updateButtonsState();
    },

    cycleArtMode: function () {
      var modes = ['sleeve', 'aura', 'off'];
      var idx = modes.indexOf(this.artMode);
      this.artMode = modes[(idx + 1) % modes.length];
      this.saveSettings('art');
      this.updateButtonsState();
      this.updateArtworkDisplay();
    },

    toggleLyrics: function (force) {
      var next = (force !== undefined) ? Boolean(force) : !this.showLyrics;
      if (this.showLyrics === next) { return; }
      this.showLyrics = next;
      this.saveSettings('lyrics');
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
      var isSame = this.currentTake && take && this.currentTake.id === take.id &&
                   this.currentTake.lyrics === take.lyrics && this.currentTake.art === take.art;
      this.currentTake = take || null;
      if (isSame) { return; }

      if (this.currentTake && this.currentTake.id && !this.currentTake.art) {
        this.startArtPolling();
      } else {
        this.stopArtPolling();
      }

      this.lyricsRenderedForTake = null;
      this.parseLyrics();
      if (this.isOpen) {
        this.updateTakeInfo();
      }
    },

    startArtPolling: function () {
      this.stopArtPolling();
      if (!this.currentTake || !this.currentTake.id || this.currentTake.art) { return; }
      var self = this;
      var takeId = this.currentTake.id;

      var check = function () {
        if (!self.currentTake || self.currentTake.id !== takeId) {
          self.stopArtPolling();
          return;
        }
        if (self.currentTake.art) {
          self.stopArtPolling();
          return;
        }

        // 1. Check if main app state already discovered artwork for this take
        if (typeof window.takeById === 'function') {
          var local = window.takeById(takeId);
          if (local && local.art) {
            self.applyArtwork(local.art);
            return;
          }
        }

        // 2. Poll server for take artwork status
        fetch('/api/takes/' + encodeURIComponent(takeId) + '/art')
          .then(function (res) { return res.ok ? res.json() : null; })
          .then(function (data) {
            if (!data || !self.currentTake || self.currentTake.id !== takeId) { return; }
            if (data.has) {
              var v = data.v || Date.now();
              var artUrl = '/api/takes/' + encodeURIComponent(takeId) + '/art.png?v=' + v;
              self.applyArtwork(artUrl);
            } else if (data.plain || data.state === 'failed') {
              self.stopArtPolling();
            }
          })
          .catch(function () {});
      };

      this.artPollTimer = setInterval(check, 2500);
      setTimeout(check, 1000);
    },

    stopArtPolling: function () {
      if (this.artPollTimer) {
        clearInterval(this.artPollTimer);
        this.artPollTimer = null;
      }
    },

    applyArtwork: function (artUrl) {
      if (!this.currentTake || !artUrl) { return; }
      this.currentTake.art = artUrl;
      this.stopArtPolling();

      if (typeof window.takeById === 'function') {
        var local = window.takeById(this.currentTake.id);
        if (local) { local.art = artUrl; }
      }

      this.updateArtworkDisplay();

      if (typeof window.paintNpCover === 'function') {
        window.paintNpCover(this.currentTake);
      }
      if (typeof window.updateMediaSession === 'function') {
        window.updateMediaSession(this.currentTake);
      }
      if (typeof window.paintTakes === 'function') {
        window.paintTakes();
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
      if (take && take.id && !take.art && !this.artPollTimer) {
        this.startArtPolling();
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

      if (img && img.getAttribute('src') !== artUrl) {
        img.src = artUrl;
      }
      if (aura) {
        aura.classList.toggle('hidden', this.artMode !== 'aura');
        var auraCss = 'url("' + artUrl.replace(/"/g, '') + '")';
        if (aura.style.backgroundImage.indexOf(artUrl) === -1) {
          aura.style.backgroundImage = auraCss;
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

      var curTakeId = this.currentTake ? this.currentTake.id : null;
      if (this.lyricsRenderedForTake === curTakeId && list.childNodes.length > 0) {
        return;
      }
      this.lyricsRenderedForTake = curTakeId;

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
      this.lastDynamicsTime = 0;
      this.lastDriftX = undefined;
      this.lastDriftY = undefined;
    },

    renderFullFrame: function (now) {
      this.updateAudioMetrics();

      if (this.currentTake && !this.currentTake.art && (!this.lastArtCheckTime || now - this.lastArtCheckTime > 3000)) {
        this.lastArtCheckTime = now;
        if (typeof window.takeById === 'function') {
          var updated = window.takeById(this.currentTake.id);
          if (updated && updated.art) {
            this.applyArtwork(updated.art);
          }
        }
      }

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
        case 'yeufonic':
          this.renderYeufonic(ctx, w, h, now);
          break;
        case 'aurora':
          this.renderAurora(ctx, w, h, now);
          break;
        case 'cosmic':
          this.renderCosmic(ctx, w, h, now);
          break;
        case 'kaleidoscope':
          this.renderKaleidoscope(ctx, w, h, now);
          break;
        case 'grid':
          this.renderGrid(ctx, w, h, now);
          break;
        case 'liquid':
          this.renderLiquid(ctx, w, h, now);
          break;
        case 'swarm':
          this.renderSwarm(ctx, w, h, now);
          break;
        case 'bars':
          this.renderBars(ctx, w, h, now);
          break;
        case 'wave':
        default:
          this.renderWave(ctx, w, h, now);
          break;
      }

      ctx.restore();

      // Dynamic reactive transform, 3D tilt, and wandering on Vinyl Sleeve
      this.applyArtworkDynamics(now);
    },

    applyArtworkDynamics: function (now) {
      var wrap = $('vis-art-wrap');
      var sleeve = $('vis-art-sleeve');
      var record = $('vis-vinyl-record');
      var glare = $('vis-art-glare');
      var ring1 = $('vis-art-ring-1');
      var ring2 = $('vis-art-ring-2');
      var aura = $('vis-art-aura');

      if (!wrap || !sleeve) { return; }

      var audio = $('audio');
      var isPlaying = audio && !audio.paused && !audio.ended;
      var currTime = (now !== undefined && now !== null) ? now : performance.now();
      var t = currTime * 0.001;

      // Delta-time normalization: bounds dt between 1ms and 64ms (~15fps min) to prevent physics jumps
      var dt = this.lastDynamicsTime ? Math.min(0.064, Math.max(0.001, (currTime - this.lastDynamicsTime) * 0.001)) : (1 / 60);
      this.lastDynamicsTime = currTime;

      // Smooth transient beat impulse with fast attack and natural musical decay
      if (this.beatDetected) {
        this.beatTarget = 1.0;
        // Trigger expanding shockwave rings (alternating between ring 1 and 2)
        if (this.ring1Opacity < 0.2) {
          this.ring1Scale = 1.0;
          this.ring1Opacity = 0.85;
        } else {
          this.ring2Scale = 1.0;
          this.ring2Opacity = 0.75;
        }
      } else {
        this.beatTarget = (this.beatTarget || 0) * Math.exp(-8.0 * dt);
      }

      var impulseRate = ((this.beatTarget || 0) > (this.beatImpulse || 0)) ? 32.0 : 7.5;
      var impulseLerp = 1.0 - Math.exp(-impulseRate * dt);
      this.beatImpulse = (this.beatImpulse || 0) + ((this.beatTarget || 0) - (this.beatImpulse || 0)) * impulseLerp;

      // Handle Aura mode breathing dynamics
      if (this.artMode === 'aura' && aura) {
        var auraScale = 1.04 + this.bassEnergy * 0.08 + this.beatImpulse * 0.04;
        var auraSat = 1.6 + this.bassEnergy * 0.8;
        var auraBright = 0.5 + this.bassEnergy * 0.25;
        aura.style.transform = 'scale(' + auraScale.toFixed(3) + ')';
        aura.style.filter = 'blur(75px) saturate(' + auraSat.toFixed(2) + ') brightness(' + auraBright.toFixed(2) + ')';
        return;
      }

      if (this.artMode !== 'sleeve') { return; }

      // Canvas wandering / orbital drift calculations:
      // When lyrics are visible: smoothly float on the left side of the stage.
      // When lyrics are closed: orbit widely around the canvas perimeter, keeping the centre
      // clear so central visualizer graphics (mandala, waves, cosmic, swarm) remain unobstructed!
      var isLyricsVisible = this.showLyrics && this.lyricsLines && this.lyricsLines.length > 0;
      var stage = $('vis-stage') || document.querySelector('.vis-stage');
      var stageW = stage ? stage.clientWidth : window.innerWidth;
      var stageH = stage ? stage.clientHeight : window.innerHeight;

      var targetX = 0;
      var targetY = 0;

      if (isLyricsVisible) {
        // Floating drift on the left half of the stage
        var rangeX = Math.min(80, Math.max(25, stageW * 0.07));
        var rangeY = Math.min(60, Math.max(20, stageH * 0.08));
        targetX = Math.sin(t * 0.35) * rangeX + Math.cos(t * 0.78) * (rangeX * 0.35);
        targetY = Math.cos(t * 0.30) * rangeY + Math.sin(t * 0.65) * (rangeY * 0.30);
      } else {
        // Wide orbital wander around the canvas perimeter
        var maxTravelX = Math.max(160, (stageW * 0.5) - 330);
        var maxTravelY = Math.max(110, (stageH * 0.5) - 250);

        // Orbital angle around the canvas with subtle harmonic pacing
        var orbAngle = t * 0.21 + Math.sin(t * 0.09) * 0.22;
        // Radial breathing: maintains a healthy minimum distance from the centre (58% to 98% of max travel)
        var radMod = 0.78 + 0.20 * Math.cos(t * 0.14);

        targetX = Math.cos(orbAngle) * (maxTravelX * radMod) + Math.sin(t * 0.43) * (maxTravelX * 0.10);
        targetY = Math.sin(orbAngle) * (maxTravelY * radMod) + Math.cos(t * 0.37) * (maxTravelY * 0.12);
      }

      // Smooth exponential lerp towards target position (frame-rate independent)
      var posLerp = 1.0 - Math.exp(-2.6 * dt);
      if (this.artX === undefined || isNaN(this.artX)) {
        this.artX = targetX;
        this.artY = targetY;
      } else {
        this.artX += (targetX - this.artX) * posLerp;
        this.artY += (targetY - this.artY) * posLerp;
      }

      // Compute travel velocity normalized per second (px/sec)
      var instantVx = (this.artX - (this.lastDriftX !== undefined ? this.lastDriftX : this.artX)) / Math.max(0.001, dt);
      var instantVy = (this.artY - (this.lastDriftY !== undefined ? this.lastDriftY : this.artY)) / Math.max(0.001, dt);
      this.lastDriftX = this.artX;
      this.lastDriftY = this.artY;

      // Target banking angles derived from normalized velocity
      var targetBankY = Math.max(-11, Math.min(11, instantVx * 0.045));
      var targetBankX = Math.max(-8.5, Math.min(8.5, -instantVy * 0.040));

      // Low-pass exponential filter on banking angles to eliminate micro-jitter
      var bankLerp = 1.0 - Math.exp(-4.2 * dt);
      this.smoothBankX = (this.smoothBankX !== undefined ? this.smoothBankX : targetBankX) + (targetBankX - (this.smoothBankX !== undefined ? this.smoothBankX : targetBankX)) * bankLerp;
      this.smoothBankY = (this.smoothBankY !== undefined ? this.smoothBankY : targetBankY) + (targetBankY - (this.smoothBankY !== undefined ? this.smoothBankY : targetBankY)) * bankLerp;

      var swayZ = Math.sin(t * 0.6) * 3.0;

      // Audio-reactive forward kick tilt and dynamic scale with smoothed impulse
      var kickTiltX = (this.bassEnergy * 7.5) + (this.beatImpulse * 4.2);
      var kickScale = 1.0 + (this.bassEnergy * 0.05) + (this.beatImpulse * 0.035);

      var rotX = this.smoothBankX + kickTiltX;
      var rotY = this.smoothBankY + Math.sin(t * 0.35) * 3.5;
      var rotZ = swayZ;

      // Move wrap in 2D space across the canvas
      wrap.style.transform = 'translate3d(' + this.artX.toFixed(2) + 'px, ' + this.artY.toFixed(2) + 'px, 0)';

      // 3D perspective tilt, rotation, and spring-scale on sleeve
      sleeve.style.transform = 'perspective(900px) rotateX(' + rotX.toFixed(2) + 'deg) rotateY(' + rotY.toFixed(2) + 'deg) rotateZ(' + rotZ.toFixed(2) + 'deg) scale(' + kickScale.toFixed(3) + ')';

      // Audio-reactive shadow depth and colored glow
      var shadowBlur = 24 + this.bassEnergy * 45;
      var shadowSpread = 4 + this.bassEnergy * 14;
      var glowAlpha = (0.2 + this.bassEnergy * 0.55).toFixed(2);
      sleeve.style.boxShadow = '0 25px ' + shadowBlur.toFixed(1) + 'px ' + shadowSpread.toFixed(1) + 'px rgba(0, 0, 0, 0.85), 0 0 ' + (shadowBlur * 1.3).toFixed(1) + 'px rgba(56, 189, 248, ' + glowAlpha + ')';

      // Holographic glare tracking 3D tilt
      if (glare) {
        var glareX = (rotY * 4.0).toFixed(1);
        var glareY = (-rotX * 3.6).toFixed(1);
        glare.style.transform = 'translate(' + glareX + '%, ' + glareY + '%) rotate(' + (45 + rotZ * 1.5).toFixed(1) + 'deg)';
        var glareOpacity = 0.18 + this.bassEnergy * 0.35 + this.beatImpulse * 0.20;
        glare.style.opacity = glareOpacity.toFixed(2);
      }

      // Vinyl record spin and slide
      if (record) {
        var targetRpmSpeed = isPlaying ? 200.0 : 0.0; // 33 1/3 RPM = 200 deg/sec
        var spinLerp = 1.0 - Math.exp(-3.0 * dt);
        this.vinylDegPerSec = (this.vinylDegPerSec !== undefined ? this.vinylDegPerSec : 200.0) + (targetRpmSpeed - (this.vinylDegPerSec !== undefined ? this.vinylDegPerSec : 200.0)) * spinLerp;
        this.vinylAngle = ((this.vinylAngle || 0) + this.vinylDegPerSec * dt) % 360;

        // Smooth physical slide out on bass and beats
        var targetSlideX = 65 + (this.bassEnergy * 20) + (this.beatImpulse * 10);
        var slideLerp = 1.0 - Math.exp(-8.0 * dt);
        this.smoothSlideX = (this.smoothSlideX !== undefined ? this.smoothSlideX : targetSlideX) + (targetSlideX - (this.smoothSlideX !== undefined ? this.smoothSlideX : targetSlideX)) * slideLerp;
        record.style.transform = 'translateX(' + this.smoothSlideX.toFixed(1) + 'px) rotate(' + this.vinylAngle.toFixed(1) + 'deg)';
      }

      // Update shockwave pulse rings
      if (this.ring1Opacity > 0.01 && ring1) {
        this.ring1Scale += 1.5 * dt;
        this.ring1Opacity *= Math.exp(-5.0 * dt);
        ring1.style.transform = 'scale(' + this.ring1Scale.toFixed(3) + ')';
        ring1.style.opacity = this.ring1Opacity.toFixed(3);
      } else if (ring1 && ring1.style.opacity !== '0') {
        ring1.style.opacity = '0';
      }

      if (this.ring2Opacity > 0.01 && ring2) {
        this.ring2Scale += 1.35 * dt;
        this.ring2Opacity *= Math.exp(-4.5 * dt);
        ring2.style.transform = 'scale(' + this.ring2Scale.toFixed(3) + ')';
        ring2.style.opacity = this.ring2Opacity.toFixed(3);
      } else if (ring2 && ring2.style.opacity !== '0') {
        ring2.style.opacity = '0';
      }
    },

    /* The brand scene: the mark itself, breathing.

       The tile's glow follows the bass and expands on the beat, each fork arm is a meter with
       its own half of the spectrum (left the lows, right the mids and highs, so the arms move
       independently), and the green dot — the one accent the logo has — flares on the beat.
       The fork stays white and the arms only widen, so it reads as the logo rather than as a
       redrawing of it. */
    spectrumLevel: function (from, to) {
      var data = this.dataFreq;
      if (!data || !data.length) { return 0; }
      var start = Math.floor(from * data.length);
      var end = Math.max(start + 1, Math.floor(to * data.length));
      end = Math.min(end, data.length);
      var sum = 0;
      for (var i = start; i < end; i++) { sum += data[i]; }
      return sum / ((end - start) * 255);
    },

    renderYeufonic: function (ctx, w, h, now) {
      ctx.fillStyle = 'rgba(11, 11, 16, 0.32)';
      ctx.fillRect(0, 0, w, h);

      var bass = this.bassEnergy || 0;
      var mid = this.midEnergy || 0;

      // A beat is a flare of the dot and a ripple leaving the tile.
      if (this.beatDetected) {
        this.yfDot = 1;
        if (!this.yfRipples) { this.yfRipples = []; }
        this.yfRipples.push(now);
        if (this.yfRipples.length > 6) { this.yfRipples.shift(); }
      }
      this.yfDot = (this.yfDot || 0) * 0.90;
      var dot = this.yfDot;
      this.yfRipples = (this.yfRipples || []).filter(function (born) { return now - born < 1200; });

      // Two hues turning slowly: the fork keeps near white and only takes a tint, the dot keeps a
      // fixed distance from it so the accent stays distinct from the body.
      var hueFork = (now * 0.008) % 360;          // a full turn every 45 seconds
      var hueDot = (hueFork + 145) % 360;

      var size = Math.min(w, h) * 0.34;
      var cx = w * 0.5;
      var cy = h * 0.46;
      var unit = size / 64;
      var breathe = 1 + bass * 0.09 + dot * 0.04;

      // The halo behind the tile, in the two brand colours.
      var haloR = size * (1.0 + bass * 0.6);
      var halo = ctx.createRadialGradient(cx, cy, size * 0.08, cx, cy, haloR);
      halo.addColorStop(0, 'rgba(123, 92, 255, ' + (0.15 + bass * 0.32).toFixed(3) + ')');
      halo.addColorStop(0.55, 'rgba(255, 77, 148, ' + (0.07 + mid * 0.18).toFixed(3) + ')');
      halo.addColorStop(1, 'rgba(255, 77, 148, 0)');
      ctx.fillStyle = halo;
      ctx.fillRect(0, 0, w, h);

      // Ripples on the beat, in the dot's green.
      var ripples = this.yfRipples;
      for (var r = 0; r < ripples.length; r++) {
        var age = (now - ripples[r]) / 1200;
        ctx.strokeStyle = 'hsla(' + hueDot.toFixed(0) + ', 85%, 62%, ' + ((1 - age) * 0.22).toFixed(3) + ')';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(cx, cy, size * (0.60 + age * 0.9), 0, Math.PI * 2);
        ctx.stroke();
      }

      ctx.save();
      ctx.translate(cx, cy);
      ctx.scale(unit * breathe, unit * breathe);
      ctx.translate(-32, -32);

      // The tile, built once: a rounded square of 15 in the mark's own 64 units.
      if (!this.yfTile) {
        var tile = new Path2D(), rad = 15;
        tile.moveTo(rad, 0); tile.lineTo(64 - rad, 0); tile.quadraticCurveTo(64, 0, 64, rad);
        tile.lineTo(64, 64 - rad); tile.quadraticCurveTo(64, 64, 64 - rad, 64);
        tile.lineTo(rad, 64); tile.quadraticCurveTo(0, 64, 0, 64 - rad);
        tile.lineTo(0, rad); tile.quadraticCurveTo(0, 0, rad, 0);
        tile.closePath();
        this.yfTile = tile;
      }

      var grad = ctx.createLinearGradient(0, 0, 64, 64);
      grad.addColorStop(0, '#7b5cff');
      grad.addColorStop(1, '#ff4d94');
      ctx.shadowColor = 'rgba(123, 92, 255, ' + (0.30 + bass * 0.45).toFixed(3) + ')';
      ctx.shadowBlur = size * (0.10 + bass * 0.28);
      ctx.fillStyle = grad;
      ctx.fill(this.yfTile);
      ctx.shadowBlur = 0;

      ctx.lineCap = 'round';
      ctx.strokeStyle = 'hsl(' + hueFork.toFixed(0) + ', 62%, 88%)';
      var glowFork = 'hsla(' + hueFork.toFixed(0) + ', 60%, 96%, ';

      // The stem, at the mark's own weight (7.5 of 64 units, as the logo has it).
      ctx.lineWidth = 7.5;
      ctx.shadowColor = glowFork + '0.35)';
      ctx.shadowBlur = size * 0.05;
      ctx.beginPath();
      ctx.moveTo(32, 54);
      ctx.lineTo(32, 36);
      ctx.stroke();
      ctx.shadowBlur = 0;

      // The arms: sampled along their own curves, each step as wide as its part of the spectrum.
      var arms = [
        { p: [[32, 36], [32, 26], [20, 23], [15, 12]], from: 0.00, to: 0.30 },
        { p: [[32, 36], [32, 26], [44, 23], [49, 12]], from: 0.30, to: 0.85 },
      ];
      var steps = 14;
      var self = this;
      // The level for each step, smoothed over its neighbours: measured per step alone the arm
      // looked lumpy, and widening much past the logo's own weight made the fork knot at the join.
      function armWidths(arm) {
        var raw = [];
        for (var i = 0; i < steps; i++) {
          var t0 = i / steps, t1 = (i + 1) / steps;
          raw.push(self.spectrumLevel(arm.from + (arm.to - arm.from) * t0,
                                      arm.from + (arm.to - arm.from) * t1 + 0.02));
        }
        var smooth = [];
        for (var j = 0; j < steps; j++) {
          var a = raw[Math.max(0, j - 1)], b = raw[j], c = raw[Math.min(steps - 1, j + 1)];
          smooth.push((a + 2 * b + c) / 4);
        }
        return smooth.map(function (lvl) { return { lvl: lvl, width: 7.5 * (1 + lvl * 0.22) }; });
      }
      function point(p, t) {
        var u = 1 - t;
        return [
          u * u * u * p[0][0] + 3 * u * u * t * p[1][0] + 3 * u * t * t * p[2][0] + t * t * t * p[3][0],
          u * u * u * p[0][1] + 3 * u * u * t * p[1][1] + 3 * u * t * t * p[2][1] + t * t * t * p[3][1],
        ];
      }
      for (var a = 0; a < arms.length; a++) {
        var arm = arms[a];
        var widths = armWidths(arm);
        for (var i = 0; i < steps; i++) {
          var level = widths[i].lvl;
          var q0 = point(arm.p, i / steps), q1 = point(arm.p, (i + 1) / steps);
          ctx.lineWidth = widths[i].width;
          // The glow carries the spectrum now, not the thickness.
          ctx.shadowColor = glowFork + (0.22 + level * 0.55).toFixed(3) + ')';
          ctx.shadowBlur = size * (0.025 + level * 0.075);
          ctx.beginPath();
          ctx.moveTo(q0[0], q0[1]);
          ctx.lineTo(q1[0], q1[1]);
          ctx.stroke();
        }
      }
      ctx.shadowBlur = 0;

      // The dot: the accent, pulsing with the music rather than only on detected beats — the bass
      // envelope sets its size continuously and a beat adds a flare on top — and turning with the
      // fork's hue, a fixed distance from it.
      var pulse = Math.min(1, bass * 0.9 + dot * 0.8);
      var dotR = 4.6 * (1 + bass * 0.45 + dot * 0.7);
      var dotHueText = hueDot.toFixed(0);
      var bloomR = 15 + pulse * 16;
      var bloom = ctx.createRadialGradient(49, 12, 2, 49, 12, bloomR);
      bloom.addColorStop(0, 'hsla(' + dotHueText + ', 90%, 60%, ' + (0.16 + pulse * 0.40).toFixed(3) + ')');
      bloom.addColorStop(1, 'hsla(' + dotHueText + ', 90%, 60%, 0)');
      ctx.fillStyle = bloom;
      ctx.beginPath();
      ctx.arc(49, 12, bloomR, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = 'hsl(' + dotHueText + ', 88%, 55%)';
      ctx.shadowColor = 'hsla(' + dotHueText + ', 90%, 62%, ' + (0.40 + pulse * 0.5).toFixed(3) + ')';
      ctx.shadowBlur = size * (0.03 + pulse * 0.12);
      ctx.beginPath();
      ctx.arc(49, 12, dotR, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      ctx.restore();

      // Where the song is up to, from the same peaks the main page draws.
      this.loadWaveStrip(this.currentTake);
      this.drawWaveStrip(ctx, w, h, now);
    },

    /* The waveform under the mark: the take's own peaks, the played part filled in, and a
       playhead — the one thing a full-screen scene otherwise never says.  The peaks come from
       the same endpoint the main page's waveform uses, fetched once per take. */
    loadWaveStrip: function (take) {
      var id = take && take.id;
      if (!id) { return; }
      if (!this.waveStrip) {
        this.waveStrip = { id: null, peaks: null, rmss: null, pending: false, path: null };
      }
      var strip = this.waveStrip;
      if (strip.id === id || strip.pending) { return; }
      if (!window.api) { return; }
      strip.pending = true;
      var self = this;
      window.api('/api/takes/' + encodeURIComponent(id) + '/peaks')
        .then(function (data) {
          if (data && data.peaks && data.peaks.length) {
            strip.id = id;
            strip.peaks = data.peaks;
            strip.rmss = (data.rms && data.rms.length) ? data.rms : data.peaks;
            strip.path = null;
          }
        })
        .catch(function () { /* no waveform is fine: the strip simply does not appear */ })
        .then(function () { if (self.waveStrip === strip) { strip.pending = false; } });
    },

    drawWaveStrip: function (ctx, w, h, now) {
      var take = this.currentTake;
      var strip = this.waveStrip;
      if (!take || !strip || strip.id !== take.id || !strip.peaks) { return; }
      var audio = $('audio');
      if (!audio) { return; }

      var margin = Math.max(24, Math.min(90, w * 0.07));
      var x0 = margin;
      var x1 = w - margin;
      var bandH = Math.max(14, Math.min(26, h * 0.032));
      var midY = h - bandH - 62;              // clear of the hint line at the bottom
      if (x1 - x0 < 80) { return; }

      var key = [Math.round(x0), Math.round(x1), Math.round(midY), Math.round(bandH), strip.peaks.length].join(':');
      if (!strip.path || strip.path.key !== key) {
        // A column every two CSS pixels: transients as the outline, loudness as the body, as the
        // main page draws it.
        var cols = Math.max(40, Math.floor((x1 - x0) / 2));
        var outline = new Path2D();
        var body = new Path2D();
        for (var i = 0; i < cols; i++) {
          var x = x0 + (i / (cols - 1)) * (x1 - x0);
          var idx = Math.min(strip.peaks.length - 1, Math.floor((i / cols) * strip.peaks.length));
          var p = Math.max(0.02, Math.min(1, strip.peaks[idx] || 0));
          var r = Math.max(0.01, Math.min(1, strip.rmss[idx] || 0));
          outline.rect(x, midY - p * bandH, 1.2, p * bandH * 2);
          body.rect(x, midY - r * bandH, 1.2, r * bandH * 2);
        }
        strip.path = { key: key, outline: outline, body: body, x0: x0, x1: x1, midY: midY, bandH: bandH };
      }
      var P = strip.path;

      var dur = (isFinite(audio.duration) && audio.duration > 0) ? audio.duration : (take.seconds || take.duration || 0);
      var frac = dur ? Math.max(0, Math.min(1, audio.currentTime / dur)) : 0;
      var hueDot = (now * 0.008 + 145) % 360;

      ctx.fillStyle = 'rgba(255, 255, 255, 0.20)';
      ctx.fill(P.outline);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.11)';
      ctx.fill(P.body);

      if (frac > 0) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(P.x0 - 2, P.midY - P.bandH - 4, (P.x1 - P.x0) * frac + 2, P.bandH * 2 + 8);
        ctx.clip();
        ctx.fillStyle = 'hsla(' + hueDot.toFixed(0) + ', 82%, 58%, 0.92)';
        ctx.fill(P.outline);
        ctx.fillStyle = 'hsla(' + hueDot.toFixed(0) + ', 82%, 74%, 0.55)';
        ctx.fill(P.body);
        ctx.restore();
      }

      var px = P.x0 + (P.x1 - P.x0) * frac;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(px, P.midY - P.bandH - 3);
      ctx.lineTo(px, P.midY + P.bandH + 3);
      ctx.stroke();
    },

    // A click on the strip seeks there; anything else falls through to the play toggle.
    seekWaveStrip: function (e) {
      var strip = this.waveStrip;
      var take = this.currentTake;
      if (!this.isOpen || !strip || !strip.path || !take || strip.id !== take.id) { return false; }
      var canvas = $('visualizer-canvas');
      var audio = $('audio');
      if (!canvas || !audio) { return false; }
      var P = strip.path;
      var rect = canvas.getBoundingClientRect();
      var x = e.clientX - rect.left;
      var y = e.clientY - rect.top;
      if (y < P.midY - P.bandH - 12 || y > P.midY + P.bandH + 12) { return false; }
      if (x < P.x0 - 12 || x > P.x1 + 12) { return false; }
      var dur = (isFinite(audio.duration) && audio.duration > 0) ? audio.duration : 0;
      if (!dur) { return false; }
      audio.currentTime = Math.max(0, Math.min(dur, ((x - P.x0) / (P.x1 - P.x0)) * dur));
      return true;
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

    /* Mode 5: Neon Synthwave Grid (Outrun) */
    renderGrid: function (ctx, w, h, now) {
      var bgGrad = ctx.createLinearGradient(0, 0, 0, h);
      bgGrad.addColorStop(0, '#04020a');
      bgGrad.addColorStop(0.5, '#0c041c');
      bgGrad.addColorStop(1, '#05020d');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, w, h);

      var cx = w * 0.5;
      var hy = h * 0.52; // Horizon line

      // Distant twinkling stars
      ctx.fillStyle = 'rgba(255, 255, 255, 0.45)';
      for (var s = 0; s < 40; s++) {
        var sx = (Math.sin(s * 91.7 + 12) * 0.5 + 0.5) * w;
        var sy = (Math.cos(s * 43.1 + 5) * 0.5 + 0.5) * (hy * 0.88);
        var sAlpha = 0.2 + Math.sin(now * 0.002 + s) * 0.25;
        ctx.globalAlpha = Math.max(0.05, sAlpha);
        ctx.fillRect(sx, sy, 1.5, 1.5);
      }
      ctx.globalAlpha = 1.0;

      // 80s Synthwave Sunset Sun
      var sunR = Math.min(w, h) * 0.16 * (1.0 + this.bassEnergy * 0.12);
      var sunY = hy - sunR * 0.35;
      var sunGrad = ctx.createLinearGradient(cx, sunY - sunR, cx, sunY + sunR);
      sunGrad.addColorStop(0, '#fef08a');
      sunGrad.addColorStop(0.5, '#f43f5e');
      sunGrad.addColorStop(1, '#a855f7');

      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, sunY, sunR, 0, Math.PI * 2);
      ctx.fillStyle = sunGrad;
      ctx.shadowColor = '#f43f5e';
      ctx.shadowBlur = 35 + this.bassEnergy * 30;
      ctx.fill();

      // Horizontal slats slicing through lower half of sun
      var slats = 7;
      ctx.fillStyle = '#0c041c';
      ctx.shadowBlur = 0;
      for (var si = 0; si < slats; si++) {
        var slatY = sunY + (si / slats) * sunR;
        var slatH = (si + 1) * 1.8;
        ctx.fillRect(cx - sunR - 10, slatY, (sunR + 10) * 2, slatH);
      }
      ctx.restore();

      // Horizon glow bar
      var horizGrad = ctx.createLinearGradient(0, hy - 15, 0, hy + 25);
      horizGrad.addColorStop(0, 'rgba(244, 63, 94, 0)');
      horizGrad.addColorStop(0.4, 'rgba(6, 182, 212, 0.55)');
      horizGrad.addColorStop(1, 'rgba(6, 182, 212, 0)');
      ctx.fillStyle = horizGrad;
      ctx.fillRect(0, hy - 15, w, 40);

      // 3D Perspective Wireframe Grid
      var lines = 22;
      this.gridOffset = ((this.gridOffset || 0) + 0.006 + this.bassEnergy * 0.012) % 1;

      ctx.lineWidth = 1.8;
      ctx.shadowBlur = 10;
      ctx.shadowColor = '#06b6d4';

      // Horizontal perspective lines moving forward
      for (var li = 0; li < lines; li++) {
        var z = (li + this.gridOffset) / lines;
        var gy = hy + Math.pow(z, 2.8) * (h - hy);
        var alpha = Math.min(1.0, z * 1.4);

        ctx.strokeStyle = 'rgba(6, 182, 212, ' + alpha.toFixed(3) + ')';
        ctx.beginPath();

        // Terrain mountain ripples on left and right edges
        var segments = 40;
        var segW = w / segments;
        for (var seg = 0; seg <= segments; seg++) {
          var px = seg * segW;
          var edgeFactor = Math.abs(px - cx) / cx;
          var elev = 0;
          if (edgeFactor > 0.3) {
            var waveX = Math.sin(px * 0.02 + now * 0.003);
            elev = Math.pow(edgeFactor - 0.3, 1.6) * (35 + this.bassEnergy * 85) * z * waveX;
          }
          var py = gy - elev;
          if (seg === 0) { ctx.moveTo(px, py); } else { ctx.lineTo(px, py); }
        }
        ctx.stroke();
      }

      // Vertical converging perspective lines
      var vCols = 24;
      ctx.strokeStyle = 'rgba(217, 70, 239, 0.45)';
      ctx.shadowColor = '#d946ef';
      for (var vi = -vCols; vi <= vCols; vi++) {
        var bottomX = cx + vi * (w / (vCols * 0.65));
        ctx.beginPath();
        ctx.moveTo(cx, hy);
        ctx.lineTo(bottomX, h);
        ctx.stroke();
      }
      ctx.shadowBlur = 0;
    },

    /* Mode 6: Liquid Warp (Milkdrop / Psychedelic Tunnel) */
    renderLiquid: function (ctx, w, h, now) {
      if (!this.liquidCanvas) {
        this.liquidCanvas = document.createElement('canvas');
      }
      if (this.liquidCanvas.width !== w || this.liquidCanvas.height !== h) {
        this.liquidCanvas.width = w;
        this.liquidCanvas.height = h;
      }
      var lctx = this.liquidCanvas.getContext('2d');

      var cx = w * 0.5;
      var cy = h * 0.5;

      // Recursive feedback warp
      var zoom = 1.018 + this.bassEnergy * 0.038;
      var rot = (this.midEnergy - 0.15) * 0.012;

      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(rot);
      ctx.scale(zoom, zoom);
      ctx.drawImage(this.liquidCanvas, -cx, -cy, w, h);
      ctx.restore();

      // Trail decay
      ctx.fillStyle = 'rgba(5, 5, 12, 0.14)';
      ctx.fillRect(0, 0, w, h);

      // Central fluid ripples and audio curves
      var points = 48;
      var baseR = 70 + this.bassEnergy * 110;
      var hue = (now * 0.06 + this.trebleEnergy * 90) % 360;

      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(now * 0.001);

      for (var layer = 0; layer < 3; layer++) {
        var lRadius = baseR * (0.6 + layer * 0.45);
        var lHue = (hue + layer * 55) % 360;

        ctx.beginPath();
        ctx.lineWidth = 3.5 + layer * 1.5;
        ctx.strokeStyle = 'hsla(' + lHue + ', 95%, 65%, 0.75)';
        ctx.shadowColor = 'hsla(' + lHue + ', 100%, 65%, 0.85)';
        ctx.shadowBlur = 20 + this.bassEnergy * 25;

        for (var p = 0; p <= points; p++) {
          var angle = (p / points) * Math.PI * 2;
          var waveMod = Math.sin(angle * (4 + layer * 2) + now * 0.004) * (15 + this.midEnergy * 30);
          var audioMod = 0;
          if (this.dataTime && this.dataTime.length) {
            var sIdx = Math.floor((p / points) * (this.dataTime.length - 1));
            audioMod = ((this.dataTime[sIdx] - 128) / 128) * (20 + this.bassEnergy * 40);
          }
          var r = lRadius + waveMod + audioMod;
          var x = Math.cos(angle) * r;
          var y = Math.sin(angle) * r;
          if (p === 0) { ctx.moveTo(x, y); } else { ctx.lineTo(x, y); }
        }
        ctx.closePath();
        ctx.stroke();
      }
      ctx.restore();
      ctx.shadowBlur = 0;

      // Copy to feedback buffer
      lctx.clearRect(0, 0, w, h);
      lctx.drawImage(ctx.canvas, 0, 0, w, h);
    },

    /* Mode 7: Particle Swarm (Cosmic Nebula) */
    initSwarmParticles: function () {
      this.swarmParticles = [];
      var count = 380;
      var colors = [
        'rgba(56, 189, 248, 0.85)',
        'rgba(168, 85, 247, 0.85)',
        'rgba(236, 72, 153, 0.85)',
        'rgba(250, 204, 21, 0.85)',
        'rgba(52, 211, 153, 0.85)'
      ];

      for (var i = 0; i < count; i++) {
        var angle = Math.random() * Math.PI * 2;
        var dist = 30 + Math.pow(Math.random(), 1.5) * 450;
        this.swarmParticles.push({
          angle: angle,
          dist: dist,
          baseDist: dist,
          speed: (0.004 + Math.random() * 0.012) * (Math.random() < 0.5 ? 1 : -1),
          radialSpeed: 0,
          size: 1.2 + Math.random() * 2.8,
          color: colors[Math.floor(Math.random() * colors.length)],
          seed: Math.random() * 100
        });
      }
    },

    renderSwarm: function (ctx, w, h, now) {
      if (!this.swarmParticles) {
        this.initSwarmParticles();
      }

      ctx.fillStyle = 'rgba(6, 6, 14, 0.28)';
      ctx.fillRect(0, 0, w, h);

      var cx = w * 0.5;
      var cy = h * 0.5;
      var bass = this.bassEnergy || 0;

      var positions = [];

      for (var i = 0; i < this.swarmParticles.length; i++) {
        var p = this.swarmParticles[i];

        p.angle += p.speed * (1.0 + this.midEnergy * 1.5);

        // Transient outward explosion on beats
        if (this.beatDetected) {
          p.radialSpeed = 12 + Math.random() * 25;
        }
        p.dist += p.radialSpeed;
        p.radialSpeed *= 0.88;

        // Spring return towards base orbit
        p.dist += (p.baseDist - p.dist) * 0.04;

        var breath = Math.sin(now * 0.003 + p.seed) * (15 + bass * 35);
        var r = Math.max(10, p.dist + breath);

        var px = cx + Math.cos(p.angle) * r;
        var py = cy + Math.sin(p.angle) * r;

        positions.push({ x: px, y: py, color: p.color, size: p.size });

        ctx.beginPath();
        var pSize = p.size * (1.0 + bass * 0.8);
        ctx.arc(px, py, pSize, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = pSize * 3;
        ctx.fill();
      }

      // Constellation connection lines
      if (this.midEnergy > 0.25) {
        ctx.lineWidth = 0.8;
        var maxLines = 60;
        var drawn = 0;
        for (var a = 0; a < positions.length && drawn < maxLines; a += 3) {
          for (var b = a + 1; b < positions.length && drawn < maxLines; b += 5) {
            var dx = positions[a].x - positions[b].x;
            var dy = positions[a].y - positions[b].y;
            var d2 = dx * dx + dy * dy;
            if (d2 < 2500) {
              var alpha = (1 - Math.sqrt(d2) / 50) * (this.midEnergy * 0.7);
              ctx.strokeStyle = 'rgba(255, 255, 255, ' + alpha.toFixed(3) + ')';
              ctx.beginPath();
              ctx.moveTo(positions[a].x, positions[a].y);
              ctx.lineTo(positions[b].x, positions[b].y);
              ctx.stroke();
              drawn++;
            }
          }
        }
      }
      ctx.shadowBlur = 0;
    },

    /* Mode 8: Hi-Fi Studio Bars (Vintage Spectrum) */
    initBars: function () {
      var count = 54;
      this.barLevels = new Float32Array(count);
      this.barPeaks = new Float32Array(count);
      this.barPeakTimes = new Float32Array(count);
    },

    renderBars: function (ctx, w, h, now) {
      if (!this.barLevels) {
        this.initBars();
      }

      ctx.fillStyle = 'rgba(5, 5, 10, 0.32)';
      ctx.fillRect(0, 0, w, h);

      if (!this.dataFreq || !this.dataFreq.length) { return; }

      var barCount = this.barLevels.length;
      var totalW = Math.min(w * 0.92, 1200);
      var startX = (w - totalW) * 0.5;
      var barW = (totalW / barCount) * 0.72;
      var gap = (totalW / barCount) * 0.28;

      var baseY = h * 0.84;
      var maxH = h * 0.55;

      // Floor glass line
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(startX - 20, baseY + 2);
      ctx.lineTo(startX + totalW + 20, baseY + 2);
      ctx.stroke();

      for (var i = 0; i < barCount; i++) {
        var binIdx = Math.min(this.dataFreq.length - 1, Math.floor(Math.pow(i / barCount, 1.4) * (this.dataFreq.length - 1)));
        var targetLevel = (this.dataFreq[binIdx] / 255);

        if (targetLevel > this.barLevels[i]) {
          this.barLevels[i] = this.barLevels[i] * 0.3 + targetLevel * 0.7;
        } else {
          this.barLevels[i] = this.barLevels[i] * 0.85;
        }

        var barH = Math.max(4, this.barLevels[i] * maxH);

        // Peak hold
        if (this.barLevels[i] >= this.barPeaks[i]) {
          this.barPeaks[i] = this.barLevels[i];
          this.barPeakTimes[i] = now;
        } else if (now - this.barPeakTimes[i] > 320) {
          this.barPeaks[i] = Math.max(0, this.barPeaks[i] - 0.016);
        }

        var bx = startX + i * (barW + gap);

        // Segmented LED blocks
        var segH = 4.5;
        var segGap = 2;
        var totalSegments = Math.floor(barH / (segH + segGap));

        for (var s = 0; s < totalSegments; s++) {
          var sy = baseY - (s + 1) * (segH + segGap);
          var ratio = s / (maxH / (segH + segGap));

          var color = '#10b981'; // Green
          if (ratio > 0.78) {
            color = '#ef4444'; // Red
          } else if (ratio > 0.52) {
            color = '#f59e0b'; // Amber
          }

          ctx.fillStyle = color;
          ctx.fillRect(bx, sy, barW, segH);
        }

        // Floating peak indicator
        var peakY = baseY - (this.barPeaks[i] * maxH) - 4;
        if (peakY < baseY) {
          ctx.fillStyle = '#ffffff';
          ctx.shadowColor = '#38bdf8';
          ctx.shadowBlur = 8;
          ctx.fillRect(bx, peakY, barW, 2.5);
          ctx.shadowBlur = 0;
        }

        // Mirrored glass floor reflection
        var reflH = barH * 0.28;
        var reflGrad = ctx.createLinearGradient(bx, baseY + 2, bx, baseY + 2 + reflH);
        reflGrad.addColorStop(0, 'rgba(16, 185, 129, 0.25)');
        reflGrad.addColorStop(1, 'rgba(16, 185, 129, 0)');
        ctx.fillStyle = reflGrad;
        ctx.fillRect(bx, baseY + 3, barW, reflH);
      }
    },

    /* ------------------------------------------------------------- Mini Player Backdrop */
    resizeMini: function () {
      var canvas = $('mini-vis');
      if (!canvas) { return; }
      var dpr = window.devicePixelRatio || 1;
      var rect = canvas.getBoundingClientRect();
      var w = Math.max(200, Math.round(rect.width || canvas.clientWidth || window.innerWidth || 1200));
      var h = Math.max(30, Math.round(rect.height || canvas.clientHeight || 64));
      var targetW = Math.round(w * dpr);
      var targetH = Math.round(h * dpr);
      if (canvas.width !== targetW || canvas.height !== targetH) {
        canvas.width = targetW;
        canvas.height = targetH;
      }
    },

    startMini: function () {
      if (this.miniAnimId) { return; }
      this.resizeMini();
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
      var canvas = $('mini-vis');
      if (canvas) {
        var ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.setTransform(1, 0, 0, 1, 0, 0);
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
      }
    },

    renderMiniFrame: function (now) {
      var canvas = $('mini-vis');
      if (!canvas || !this.miniEnabled) {
        if (canvas) {
          var c = canvas.getContext('2d');
          if (c) {
            c.setTransform(1, 0, 0, 1, 0, 0);
            c.clearRect(0, 0, canvas.width, canvas.height);
          }
        }
        return;
      }

      var dpr = window.devicePixelRatio || 1;
      var rect = canvas.getBoundingClientRect();
      var w = Math.max(200, Math.round(rect.width || canvas.clientWidth || window.innerWidth || 1200));
      var h = Math.max(30, Math.round(rect.height || canvas.clientHeight || 64));
      var targetW = Math.round(w * dpr);
      var targetH = Math.round(h * dpr);
      if (canvas.width !== targetW || canvas.height !== targetH) {
        canvas.width = targetW;
        canvas.height = targetH;
      }

      var ctx = canvas.getContext('2d');
      if (!ctx) { return; }

      // Clear the physical canvas buffer completely in untransformed device pixels
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      var audio = $('audio');
      var isPlaying = audio && !audio.paused && !audio.ended;
      if (!isPlaying) {
        return;
      }

      if (!this.analyser) {
        this.ensureAudioNode();
      }
      this.updateAudioMetrics();

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Render smooth ambient audio-reactive wave across the full width of the player
      var points = Math.max(120, Math.floor(w / 8));
      var step = w / points;
      var cy = h * 0.5;
      var time = now * 0.002;
      var timeData = this.dataTime;
      var timeLen = timeData ? timeData.length : 0;
      var bass = this.bassEnergy || 0;

      // Primary flowing ribbon across full player width
      ctx.beginPath();
      for (var i = 0; i <= points; i++) {
        var x = i * step;
        var audioSample = 0;
        if (timeLen > 0) {
          var sIdx = Math.floor((i / points) * timeLen);
          audioSample = ((timeData[sIdx] - 128) / 128) * (h * 0.28);
        }
        var waveY = Math.sin(x * 0.015 + time) * (h * 0.14 * (1.0 + bass * 1.3)) + audioSample;
        var y = cy + waveY;
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }

      var grad = ctx.createLinearGradient(0, 0, w, 0);
      grad.addColorStop(0, 'rgba(56, 189, 248, 0.40)');
      grad.addColorStop(0.5, 'rgba(168, 85, 247, 0.55)');
      grad.addColorStop(1, 'rgba(236, 72, 153, 0.40)');

      ctx.strokeStyle = grad;
      ctx.lineWidth = 2.0;
      ctx.shadowColor = 'rgba(168, 85, 247, 0.5)';
      ctx.shadowBlur = 8;
      ctx.stroke();

      // Secondary subtle harmonic counter-wave for rich depth
      ctx.beginPath();
      for (var j = 0; j <= points; j++) {
        var x2 = j * step;
        var audioSample2 = 0;
        if (timeLen > 0) {
          var sIdx2 = Math.floor(((points - j) / points) * timeLen);
          audioSample2 = ((timeData[sIdx2] - 128) / 128) * (h * 0.18);
        }
        var waveY2 = Math.sin(x2 * 0.022 - time * 0.8) * (h * 0.10 * (1.0 + bass)) + audioSample2;
        var y2 = cy + waveY2;
        if (j === 0) {
          ctx.moveTo(x2, y2);
        } else {
          ctx.lineTo(x2, y2);
        }
      }

      var grad2 = ctx.createLinearGradient(0, 0, w, 0);
      grad2.addColorStop(0, 'rgba(168, 85, 247, 0.20)');
      grad2.addColorStop(0.5, 'rgba(56, 189, 248, 0.35)');
      grad2.addColorStop(1, 'rgba(168, 85, 247, 0.20)');

      ctx.strokeStyle = grad2;
      ctx.lineWidth = 1.2;
      ctx.shadowColor = 'rgba(56, 189, 248, 0.4)';
      ctx.shadowBlur = 6;
      ctx.stroke();

      ctx.shadowBlur = 0;
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
