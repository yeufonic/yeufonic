/* ============================================================================
   Jam — interactive desktop studio console for rolling iterative passes.
   Vocabulary:
     Feature: Jam
     Action button: Roll
     Timeline items: Pass #1, Pass #2, ... (Roll History)
     Sound chips: Parts
   ============================================================================ */
(function () {
  'use strict';

  var MAX_PARTS = 10;

  var STARTERS = [
    {
      id: 'lofi',
      name: 'Lo-fi Groove',
      bpm: 84,
      vibe: { x: 0.34, y: 0.36 },
      vocals: 'instrumental',
      tones: [],
      lyricTheme: 'Late nights',
      parts: [
        { name: 'Lo-fi', cat: 'genre', level: 3 },
        { name: 'Boom bap', cat: 'genre', level: 2 },
        { name: 'Fender Rhodes', cat: 'inst', level: 2 },
        { name: 'Vinyl crackle', cat: 'prod', level: 1 }
      ]
    },
    {
      id: 'synthwave',
      name: 'Synthwave Drive',
      bpm: 112,
      vibe: { x: 0.38, y: 0.72 },
      vocals: 'instrumental',
      tones: [],
      lyricTheme: 'Late nights',
      parts: [
        { name: 'Synthwave', cat: 'genre', level: 3 },
        { name: 'Analog synth', cat: 'inst', level: 3 },
        { name: 'Punchy drums', cat: 'rhythm', level: 2 },
        { name: 'Tape saturation', cat: 'prod', level: 2 }
      ]
    },
    {
      id: 'folk',
      name: 'Acoustic Folk',
      bpm: 96,
      vibe: { x: 0.62, y: 0.38 },
      vocals: 'female',
      tones: ['Warm', 'Intimate'],
      lyricTheme: 'Nostalgia',
      parts: [
        { name: 'Indie folk', cat: 'genre', level: 3 },
        { name: 'Fingerpicked guitar', cat: 'inst', level: 3 },
        { name: 'Upright bass', cat: 'inst', level: 2 },
        { name: 'Warm strings', cat: 'inst', level: 1 }
      ]
    },
    {
      id: 'neosoul',
      name: 'Neo-Soul Pocket',
      bpm: 90,
      vibe: { x: 0.56, y: 0.44 },
      vocals: 'female',
      tones: ['Smooth', 'Soulful'],
      lyricTheme: 'Confidence',
      parts: [
        { name: 'Neo-soul', cat: 'genre', level: 3 },
        { name: 'Fender Rhodes', cat: 'inst', level: 3 },
        { name: 'Funky bass', cat: 'inst', level: 2 },
        { name: 'Syncopated groove', cat: 'rhythm', level: 2 }
      ]
    },
    {
      id: 'bossa',
      name: 'Bossa Lounge',
      bpm: 108,
      vibe: { x: 0.72, y: 0.48 },
      vocals: 'instrumental',
      tones: [],
      lyricTheme: 'Freedom',
      parts: [
        { name: 'Bossa nova', cat: 'genre', level: 3 },
        { name: 'Nylon guitar', cat: 'inst', level: 3 },
        { name: 'Vibraphone', cat: 'inst', level: 2 },
        { name: 'Brush drums', cat: 'rhythm', level: 2 }
      ]
    },
    {
      id: 'cinematic',
      name: 'Cinematic Pulse',
      bpm: 100,
      vibe: { x: 0.25, y: 0.64 },
      vocals: 'instrumental',
      tones: [],
      lyricTheme: 'Chasing dreams',
      parts: [
        { name: 'Cinematic', cat: 'genre', level: 3 },
        { name: 'Cello', cat: 'inst', level: 3 },
        { name: 'Warm strings', cat: 'inst', level: 2 },
        { name: 'Sub bass', cat: 'prod', level: 2 }
      ]
    }
  ];

  var PALETTE = {
    inst: [
      'Acoustic piano', 'Fender Rhodes', 'Wurlitzer', 'Hammond organ', 'Clavinet',
      'Analog synth', 'Synth pad', 'Lead synth',
      'Acoustic guitar', 'Fingerpicked guitar', 'Nylon guitar', 'Clean guitar',
      'Distorted guitar', '12-string guitar', 'Pedal steel',
      'Bass guitar', 'Upright bass', 'Funky bass', 'Synth bass', '808 bass',
      'Warm strings', 'Violin', 'Cello', 'Harp',
      'Saxophone', 'Trumpet', 'Muted trumpet', 'Trombone', 'Brass section',
      'Flute', 'Clarinet', 'Oboe',
      'Vibraphone', 'Steel drums', 'Banjo', 'Mandolin', 'Ukulele',
      'Accordion', 'Harmonica', 'Choir'
    ],
    genre: [
      'Pop', 'Electro-pop', 'Dream pop', 'Chamber pop',
      'Indie rock', 'Classic rock', 'Alternative rock', 'Punk rock', 'Post-rock', 'Shoegaze', 'Metal',
      'Indie folk', 'Folk', 'Country', 'Blues',
      'Jazz', 'Jazz-funk', 'Acid jazz', 'Bossa nova',
      'Soul', 'Neo-soul', 'R&B', 'Funk', 'Disco',
      'Hip-hop', 'Boom bap', 'Lo-fi', 'Trip-hop', 'Synthwave',
      'House', 'Afro house', 'Drum and bass', 'Ambient', 'Cinematic', 'Reggae', 'Dub'
    ],
    prod: [
      'Vinyl crackle', 'Tape saturation', 'Lo-fi dust', 'Lo-fi cassette',
      'Warm analog', 'Vintage tube warmth', 'Lush reverb', 'Hall reverb',
      '80s gated reverb', 'Slapback delay', 'Dub delay', 'Chorus shimmer',
      'Atmospheric pads', 'Dreamy haze', 'Wide stereo', 'Sub bass',
      'Crisp studio mix', 'Punchy compression', 'Dry close-mic', 'Live room',
      'Intimate acoustic', 'Clean acoustic mix', 'Raw garage mix', 'Big arena sound'
    ],
    rhythm: [
      'Acoustic drums', 'Punchy drums', 'Brush drums', 'Electronic drums', '808 drums',
      'Four-on-the-floor', 'Driving beat', 'Breakbeat', 'Syncopated groove', 'Laid-back groove',
      'Half-time feel', 'Double-time', 'Swing pocket', 'Shuffle beat', 'Waltz 3/4',
      'Rimshot snare', 'Handclaps', 'Finger snaps', 'Shakers', 'Tambourine',
      'Congas', 'Bongos', 'Cajon', 'Minimal percussion'
    ]
  };

  var VOCAL_TONES = ['Airy', 'Smooth', 'Warm', 'Raspy', 'Low pitch', 'Soulful', 'Gritty', 'Intimate'];
  var LYRIC_THEMES = ['Confidence', 'Heartbreak', 'Late nights', 'Chasing dreams', 'Nostalgia', 'Freedom', 'Keep current'];

  // Fallback short lyrics if no LLM is configured so vocal rolls still work out of the box.
  var FALLBACK_LYRICS = {
    'Confidence': '[Verse]\nI walked in quiet but I knew my name\nSteady hands and a pocket full of flame\n\n[Chorus]\nNo looking back, I hold my ground\nTurn up the night and let it sound',
    'Heartbreak': '[Verse]\nLeft your key on the kitchen rail\nRain on the window, quiet and pale\n\n[Chorus]\nStill hear your echo down the hall\nLearning to stand after the fall',
    'Late nights': '[Verse]\nStreetlights humming on the wet concrete\nMidnight static and a slow heartbeat\n\n[Chorus]\nNobody sleeping in the neon glow\nDriving nowhere till the morning shows',
    'Chasing dreams': '[Verse]\nPaper maps on a crowded floor\nEvery closed window opens a door\n\n[Chorus]\nKeep the horizon in our sight\nRunning on sparks into the light',
    'Nostalgia': '[Verse]\nFaded Polaroids on the shelf\nSummer afternoons we kept to ourselves\n\n[Chorus]\nGolden light through an open screen\nHolding the quiet in between',
    'Freedom': '[Verse]\nOpen highway and the windows down\nLeaving the weight of a crowded town\n\n[Chorus]\nWind in the pines and a wide blue sky\nNothing to prove, just letting it fly'
  };

  // 4x4 grid of moods across X (Dark->Bright) and Y (Calm->Energetic)
  var VIBE_GRID = [
    // y=0 (Calm) .. y=3 (Energetic)
    ['Somber',     'Melancholic', 'Peaceful',   'Serene'],
    ['Sad',        'Mellow',      'Warm',       'Dreamy'],
    ['Moody',      'Tense',       'Groovy',     'Uplifting'],
    ['Fierce',     'Driven',      'Vibrant',    'Euphoric']
  ];

  var LEVEL_LABELS = { 1: 'Subtle', 2: 'Normal', 3: 'Prominent', 4: 'Lead' };

  /* ------------------------------------------------- Web Audio Loop & Crossfade */
  var JamAudio = {
    ctx: null,
    master: null,
    active: null,     // { takeId, source, gain, buffer, startedAt, offset }
    buffers: {},      // takeId -> AudioBuffer
    peaks: {},        // takeId -> Float32Array(60)
    playing: false,
    currentId: null,
    raf: null,

    ensure: function () {
      if (!this.ctx) {
        var AC = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AC();
        this.master = this.ctx.createGain();
        this.master.gain.value = 0.9;
        this.master.connect(this.ctx.destination);
      }
      if (this.ctx.state === 'suspended') { this.ctx.resume().catch(function () {}); }
    },

    pauseMainPlayer: function () {
      var a = document.getElementById('audio');
      if (a && !a.paused) { a.pause(); }
    },

    load: async function (takeId) {
      if (this.buffers[takeId]) { return this.buffers[takeId]; }
      this.ensure();
      var res = await fetch('/api/takes/' + encodeURIComponent(takeId) + '/audio');
      if (!res.ok) { throw new Error('Audio not ready'); }
      var arr = await res.arrayBuffer();
      var buf = await this.ctx.decodeAudioData(arr);
      this.buffers[takeId] = buf;
      this.peaks[takeId] = computePeaks(buf, 64);
      return buf;
    },

    play: async function (takeId, crossfadeSec) {
      this.pauseMainPlayer();
      this.ensure();
      var buf = await this.load(takeId);
      var now = this.ctx.currentTime;
      var fade = (this.active && this.playing && crossfadeSec) ? crossfadeSec : 0.06;

      var src = this.ctx.createBufferSource();
      src.buffer = buf;
      src.loop = true;
      var gain = this.ctx.createGain();
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.linearRampToValueAtTime(1.0, now + fade);
      src.connect(gain);
      gain.connect(this.master);
      src.start(now, 0);

      if (this.active) {
        var prev = this.active;
        try {
          prev.gain.gain.cancelScheduledValues(now);
          prev.gain.gain.setValueAtTime(Math.max(0.0001, prev.gain.gain.value), now);
          prev.gain.gain.linearRampToValueAtTime(0.0001, now + fade);
          prev.source.stop(now + fade + 0.05);
        } catch (err) { /* already stopped */ }
      }

      this.active = { takeId: takeId, source: src, gain: gain, buffer: buf, startedAt: now, offset: 0 };
      this.currentId = takeId;
      this.playing = true;
      this.startTick();
      paintStage();
      paintHistory();
    },

    seekFraction: function (frac) {
      if (!this.active || !this.active.buffer) { return; }
      var dur = this.active.buffer.duration || 1;
      var offset = Math.max(0, Math.min(dur - 0.05, frac * dur));
      var takeId = this.active.takeId;
      if (!this.playing) {
        this.active.offset = offset;
        paintWaveProgress();
        return;
      }
      var now = this.ctx.currentTime;
      try { this.active.source.stop(now); } catch (err) {}
      var src = this.ctx.createBufferSource();
      src.buffer = this.active.buffer;
      src.loop = true;
      var gain = this.ctx.createGain();
      gain.gain.setValueAtTime(1.0, now);
      src.connect(gain);
      gain.connect(this.master);
      src.start(now, offset);
      this.active = { takeId: takeId, source: src, gain: gain, buffer: this.active.buffer, startedAt: now, offset: offset };
      paintWaveProgress();
    },

    toggle: function () {
      if (!this.currentId) {
        var latestReady = JamState.passes.find(function (p) { return p.status === 'done' && p.hasAudio; });
        if (latestReady) { this.play(latestReady.id, 0.06); }
        return;
      }
      if (this.playing) {
        this.pause();
      } else {
        this.resume();
      }
    },

    pause: function () {
      if (!this.active || !this.playing) { return; }
      var pos = this.position();
      try { this.active.source.stop(); } catch (err) {}
      this.active.offset = pos;
      this.playing = false;
      this.stopTick();
      paintStage();
      paintHistory();
    },

    resume: function () {
      if (!this.currentId) { return; }
      var buf = this.buffers[this.currentId];
      if (!buf) { this.play(this.currentId, 0.06); return; }
      this.pauseMainPlayer();
      this.ensure();
      var now = this.ctx.currentTime;
      var off = this.active ? (this.active.offset || 0) : 0;
      var src = this.ctx.createBufferSource();
      src.buffer = buf;
      src.loop = true;
      var gain = this.ctx.createGain();
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.linearRampToValueAtTime(1.0, now + 0.05);
      src.connect(gain);
      gain.connect(this.master);
      src.start(now, off % Math.max(0.1, buf.duration));
      this.active = { takeId: this.currentId, source: src, gain: gain, buffer: buf, startedAt: now, offset: off };
      this.playing = true;
      this.startTick();
      paintStage();
      paintHistory();
    },

    stop: function () {
      if (this.active) {
        try { this.active.source.stop(); } catch (err) {}
      }
      this.active = null;
      this.playing = false;
      this.stopTick();
    },

    position: function () {
      if (!this.active || !this.active.buffer) { return 0; }
      var dur = this.active.buffer.duration || 1;
      if (!this.playing) { return (this.active.offset || 0) % dur; }
      return ((this.ctx.currentTime - this.active.startedAt) + (this.active.offset || 0)) % dur;
    },

    duration: function () {
      return (this.active && this.active.buffer && this.active.buffer.duration) || 0;
    },

    startTick: function () {
      if (this.raf) { return; }
      var self = this;
      var step = function () {
        if (!self.playing || !JamState.open) { self.raf = null; return; }
        paintWaveProgress();
        self.raf = requestAnimationFrame(step);
      };
      this.raf = requestAnimationFrame(step);
    },

    stopTick: function () {
      if (this.raf) { cancelAnimationFrame(this.raf); this.raf = null; }
    }
  };

  function computePeaks(buffer, bars) {
    var ch = buffer.getChannelData(0);
    var step = Math.max(1, Math.floor(ch.length / bars));
    var out = new Float32Array(bars);
    var max = 0.001;
    for (var i = 0; i < bars; i++) {
      var peak = 0;
      var start = i * step;
      var end = Math.min(ch.length, start + step);
      for (var j = start; j < end; j += Math.max(1, Math.floor(step / 64))) {
        var v = Math.abs(ch[j]);
        if (v > peak) { peak = v; }
      }
      out[i] = peak;
      if (peak > max) { max = peak; }
    }
    for (var k = 0; k < bars; k++) { out[k] = Math.max(0.14, out[k] / max); }
    return out;
  }

  /* ------------------------------------------------- Jam Session State */
  var JAM_STORAGE_KEY = 'yue2.jam.sessions';

  var JamState = {
    open: false,
    sessionKey: '__standalone__',
    starterName: 'Lo-fi Groove',
    parentId: null,
    spaceId: null,
    fastLoop: true,
    lockScore: false,
    parts: [],          // [{ name, cat, level }]
    vibe: { x: 0.34, y: 0.36 },
    bpm: 84,
    vocals: 'instrumental', // 'instrumental' | 'female' | 'male' | 'voice'
    voiceId: '',
    tones: [],
    lyricTheme: 'Late nights',
    lyrics: '',
    lyricsDirtyTheme: false,
    styleLora: '',
    styleLoraModel: 0.7,
    styleLoraClip: 0.7,
    paletteTab: 'inst',
    searchQuery: '',
    passes: [],         // newest first: [{ num, id, title, status, progress, stage, hasAudio, hasScore, isFullSong, duration, snapshot, diffs, error }]
    lastRolledSnapshot: null,
    cookingId: null,
    draftingLyrics: false,
    pollTimer: null
  };

  function readSavedSessions() {
    try {
      var raw = JSON.parse(localStorage.getItem(JAM_STORAGE_KEY) || '{}');
      return (raw && typeof raw === 'object') ? raw : {};
    } catch (err) { return {}; }
  }

  function saveSession() {
    if (!JamState.sessionKey) { return; }
    try {
      var all = readSavedSessions();
      all[JamState.sessionKey] = {
        savedAt: Date.now(),
        starterName: JamState.starterName,
        parentId: JamState.parentId,
        spaceId: JamState.spaceId,
        fastLoop: JamState.fastLoop,
        lockScore: JamState.lockScore,
        parts: JamState.parts,
        vibe: JamState.vibe,
        bpm: JamState.bpm,
        vocals: JamState.vocals,
        voiceId: JamState.voiceId,
        tones: JamState.tones,
        lyricTheme: JamState.lyricTheme,
        lyrics: JamState.lyrics,
        lyricsDirtyTheme: JamState.lyricsDirtyTheme,
        styleLora: JamState.styleLora,
        styleLoraModel: JamState.styleLoraModel,
        styleLoraClip: JamState.styleLoraClip,
        passes: JamState.passes.slice(0, 40),
        lastRolledSnapshot: JamState.lastRolledSnapshot,
        cookingId: JamState.cookingId
      };
      // Trim to 20 most recent sessions to keep localStorage tidy
      var keys = Object.keys(all).sort(function (a, b) { return (all[b].savedAt || 0) - (all[a].savedAt || 0); });
      if (keys.length > 20) {
        keys.slice(20).forEach(function (k) { delete all[k]; });
      }
      localStorage.setItem(JAM_STORAGE_KEY, JSON.stringify(all));
    } catch (err) { /* private mode / quota */ }
  }

  function loadSession(key) {
    var all = readSavedSessions();
    var s = all[key];
    if (!s || !Array.isArray(s.parts)) { return false; }
    JamState.sessionKey = key;
    JamState.starterName = s.starterName || 'Lo-fi Groove';
    JamState.parentId = s.parentId || null;
    JamState.spaceId = s.spaceId || null;
    JamState.fastLoop = s.fastLoop !== false;
    JamState.lockScore = Boolean(s.lockScore);
    JamState.parts = s.parts.slice();
    JamState.vibe = s.vibe || { x: 0.34, y: 0.36 };
    JamState.bpm = s.bpm || 96;
    JamState.vocals = s.vocals || 'instrumental';
    JamState.voiceId = s.voiceId || '';
    JamState.tones = Array.isArray(s.tones) ? s.tones.slice() : [];
    JamState.lyricTheme = s.lyricTheme || 'Late nights';
    JamState.lyrics = s.lyrics || '';
    JamState.lyricsDirtyTheme = Boolean(s.lyricsDirtyTheme);
    JamState.styleLora = s.styleLora || '';
    JamState.styleLoraModel = s.styleLoraModel != null ? Number(s.styleLoraModel) : 0.7;
    JamState.styleLoraClip = s.styleLoraClip != null ? Number(s.styleLoraClip) : 0.7;
    JamState.passes = Array.isArray(s.passes) ? s.passes.slice() : [];
    JamState.lastRolledSnapshot = s.lastRolledSnapshot || null;
    JamState.cookingId = s.cookingId || null;
    return true;
  }

  async function syncPassesFromServer() {
    if (!JamState.passes.length) { return; }
    var kept = [];
    var activeCook = null;
    for (var i = 0; i < JamState.passes.length; i++) {
      var p = JamState.passes[i];
      try {
        var rec = await api('/api/takes/' + encodeURIComponent(p.id));
        if (rec.space_id === 'trash') { continue; }
        p.status = rec.status;
        p.stage = rec.stage || rec.status;
        p.hasAudio = Boolean(rec.has_audio);
        p.hasScore = Boolean(rec.abc && rec.abc.trim());
        p.isSnippet = rec.space_id === '__jam__';
        p.isTopLevelTake = Boolean(rec.space_id && rec.space_id !== '__jam__' && !rec.parent_id);
        p.duration = rec.duration || p.duration || 0;
        if (rec.title) { p.title = rec.title; }
        if (rec.status === 'done') { p.progress = 100; }
        if (rec.status === 'queued' || rec.status === 'running') { activeCook = p.id; }
        kept.push(p);
      } catch (err) {
        // Take was permanently deleted; drop from history
      }
    }
    JamState.passes = kept;
    JamState.cookingId = activeCook;
    if (!JamState.passes.length) {
      JamState.parentId = null;
      JamState.lastRolledSnapshot = null;
      JamState.lockScore = false;
    }
    saveSession();
    paintAll();
    if (activeCook) { startPolling(); }
  }

  function cloneSnapshot() {
    return {
      fastLoop: JamState.fastLoop,
      lockScore: JamState.lockScore,
      parts: JamState.parts.map(function (p) { return { name: p.name, cat: p.cat, level: p.level }; }),
      vibe: { x: Math.round(JamState.vibe.x * 100) / 100, y: Math.round(JamState.vibe.y * 100) / 100 },
      bpm: JamState.bpm,
      vocals: JamState.vocals,
      voiceId: JamState.voiceId,
      tones: JamState.tones.slice(),
      lyricTheme: JamState.lyricTheme,
      lyrics: JamState.lyrics,
      styleLora: JamState.styleLora,
      styleLoraModel: JamState.styleLoraModel,
      styleLoraClip: JamState.styleLoraClip
    };
  }

  function vibeInfo(v) {
    var xi = Math.max(0, Math.min(3, Math.floor(v.x * 3.999)));
    var yi = Math.max(0, Math.min(3, Math.floor(v.y * 3.999)));
    var word = VIBE_GRID[yi][xi];
    var xWord = v.x < 0.38 ? 'Dark' : (v.x > 0.62 ? 'Bright' : 'Balanced');
    var yWord = v.y < 0.38 ? 'Calm' : (v.y > 0.62 ? 'Energetic' : 'Mid-energy');
    var harmony = yi >= 2 && xi <= 1 ? 2 : (yi >= 3 ? 2 : 1);
    var interpretation = yi >= 3 ? 'wide' : (yi === 0 && xi <= 1 ? 'settled' : 'standard');
    return { word: word, xWord: xWord, yWord: yWord, harmony: harmony, interpretation: interpretation };
  }

  function compileStyle(snap) {
    var s = snap || JamState;
    // Higher-level parts go first so YuE2 weights them more strongly.
    var sorted = s.parts.slice().sort(function (a, b) { return b.level - a.level; });
    var tokens = sorted.map(function (p) {
      if (p.level >= 4) { return 'lead ' + p.name.toLowerCase() + ' focus'; }
      if (p.level === 3) { return 'prominent ' + p.name.toLowerCase(); }
      if (p.level === 1) { return 'subtle ' + p.name.toLowerCase(); }
      return p.name.toLowerCase();
    });
    var vi = vibeInfo(s.vibe);
    var mood = [vi.word.toLowerCase()];
    if (vi.xWord !== 'Balanced') { mood.push(vi.xWord.toLowerCase()); }
    if (vi.yWord !== 'Mid-energy') { mood.push(vi.yWord.toLowerCase()); }
    tokens.push(mood.join(' ') + ' mood');

    if (s.vocals === 'instrumental') {
      tokens.push('instrumental');
    } else {
      var vLabel = s.vocals === 'male' ? 'male vocal' : (s.vocals === 'female' ? 'female vocal' : 'lead vocal');
      var tonePrefix = s.tones.length ? s.tones.map(function (t) { return t.toLowerCase(); }).join(', ') + ' ' : '';
      tokens.push(tonePrefix + vLabel);
    }
    if (s.bpm) { tokens.push(s.bpm + ' BPM'); }
    return tokens.join(', ');
  }

  function computeDiffs(prev, next) {
    if (!prev) {
      var seed = next.parts.slice(0, 3).map(function (p) { return { text: p.name, cls: '' }; });
      seed.push({ text: next.vocals === 'instrumental' ? 'Instrumental' : (next.vocals === 'male' ? 'Male vocal' : 'Female vocal'), cls: '' });
      seed.push({ text: next.bpm + ' BPM', cls: '' });
      return seed;
    }
    var diffs = [];
    var prevMap = {};
    prev.parts.forEach(function (p) { prevMap[p.name.toLowerCase()] = p; });
    var nextMap = {};
    next.parts.forEach(function (p) { nextMap[p.name.toLowerCase()] = p; });

    next.parts.forEach(function (p) {
      var old = prevMap[p.name.toLowerCase()];
      if (!old) {
        diffs.push({ text: '+ ' + p.name + (p.level >= 4 ? ' (Lead)' : ''), cls: 'add' });
      } else if (old.level !== p.level) {
        diffs.push({ text: p.name + (p.level > old.level ? ' \u2191' : ' \u2193'), cls: 'chg' });
      }
    });
    prev.parts.forEach(function (p) {
      if (!nextMap[p.name.toLowerCase()]) {
        diffs.push({ text: '\u2212 ' + p.name, cls: 'rem' });
      }
    });
    var oldVibe = vibeInfo(prev.vibe).word;
    var newVibe = vibeInfo(next.vibe).word;
    if (oldVibe !== newVibe) { diffs.push({ text: 'Vibe \u2192 ' + newVibe, cls: 'chg' }); }
    if (Math.abs((prev.bpm || 0) - (next.bpm || 0)) >= 3) { diffs.push({ text: next.bpm + ' BPM', cls: 'chg' }); }
    if (prev.vocals !== next.vocals) {
      diffs.push({ text: 'Vocals \u2192 ' + (next.vocals === 'instrumental' ? 'Instrumental' : (next.vocals === 'voice' ? 'My Voice' : next.vocals)), cls: 'chg' });
    }
    if (prev.vocals !== 'instrumental' && next.vocals !== 'instrumental' && prev.lyricTheme !== next.lyricTheme && next.lyricTheme !== 'Keep current') {
      diffs.push({ text: 'Lyrics \u2192 ' + next.lyricTheme, cls: 'chg' });
    }
    if ((prev.styleLora || '') !== (next.styleLora || '')) {
      diffs.push({ text: next.styleLora ? '+ LoRA' : '\u2212 LoRA', cls: next.styleLora ? 'add' : 'rem' });
    }
    if (!diffs.length) { diffs.push({ text: 'Fresh roll', cls: 'chg' }); }
    return diffs.slice(0, 6);
  }

  function pendingChangeCount() {
    if (!JamState.lastRolledSnapshot) { return 0; }
    var d = computeDiffs(JamState.lastRolledSnapshot, cloneSnapshot());
    if (d.length === 1 && d[0].text === 'Fresh roll') { return 0; }
    return d.length;
  }

  function isPartPending(name) {
    if (!JamState.lastRolledSnapshot) { return false; }
    var key = name.toLowerCase();
    var old = JamState.lastRolledSnapshot.parts.find(function (p) { return p.name.toLowerCase() === key; });
    var cur = JamState.parts.find(function (p) { return p.name.toLowerCase() === key; });
    return !old || (cur && old.level !== cur.level);
  }

  function applyStarter(starter) {
    JamState.starterName = starter.name;
    JamState.parentId = null;
    JamState.spaceId = null;
    JamState.parts = starter.parts.map(function (p) { return { name: p.name, cat: p.cat, level: p.level }; });
    JamState.vibe = { x: starter.vibe.x, y: starter.vibe.y };
    JamState.bpm = starter.bpm;
    JamState.vocals = starter.vocals;
    JamState.tones = starter.tones.slice();
    JamState.lyricTheme = starter.lyricTheme || 'Late nights';
    JamState.lyrics = '';
    JamState.lyricsDirtyTheme = true;
    JamState.lockScore = false;
    JamState.passes = [];
    JamState.lastRolledSnapshot = null;
    JamState.cookingId = null;
    JamAudio.stop();
    JamAudio.currentId = null;
    saveSession();
    paintAll();
  }

  function seedFromTake(take) {
    JamState.starterName = take.title || 'Selected take';
    JamState.parentId = take.parent_id || take.id;
    JamState.spaceId = (take.space_id && take.space_id !== 'trash') ? take.space_id : null;
    var rawTags = (take.style || '').split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    var parts = [];
    rawTags.forEach(function (tag) {
      if (/^\d+\s*bpm$/i.test(tag) || /^instrumental$/i.test(tag)) { return; }
      if (parts.length >= 7) { return; }
      var cat = 'genre';
      var low = tag.toLowerCase();
      if (PALETTE.inst.some(function (i) { return low.indexOf(i.toLowerCase()) >= 0; })) { cat = 'inst'; }
      else if (PALETTE.rhythm.some(function (i) { return low.indexOf(i.toLowerCase()) >= 0; })) { cat = 'rhythm'; }
      else if (PALETTE.prod.some(function (i) { return low.indexOf(i.toLowerCase()) >= 0; })) { cat = 'prod'; }
      parts.push({ name: tag.charAt(0).toUpperCase() + tag.slice(1), cat: cat, level: 2 });
    });
    if (!parts.length) {
      parts = [{ name: 'Indie pop', cat: 'genre', level: 2 }];
    }
    JamState.parts = parts;
    JamState.vibe = { x: 0.5, y: 0.5 };
    JamState.bpm = Number(take.target_bpm) || 100;
    JamState.vocals = take.kind === 'instrumental' ? 'instrumental' : (take.voice_id ? 'voice' : (/male vocal/i.test(take.style || '') && !/female/i.test(take.style || '') ? 'male' : 'female'));
    JamState.voiceId = take.voice_id || '';
    JamState.tones = [];
    JamState.lyricTheme = 'Keep current';
    JamState.lyrics = take.kind === 'instrumental' ? '' : (take.lyrics || '');
    JamState.lyricsDirtyTheme = false;
    JamState.styleLora = take.style_lora || '';
    JamState.styleLoraModel = take.style_lora_model != null ? Number(take.style_lora_model) : 0.7;
    JamState.styleLoraClip = take.style_lora_clip != null ? Number(take.style_lora_clip) : 0.7;
    JamState.lockScore = Boolean(take.abc && take.abc.trim());
    var snap = cloneSnapshot();
    JamState.lastRolledSnapshot = snap;
    JamState.passes = [{
      num: 0,
      isSeed: true,
      id: take.id,
      title: take.title || 'Starter Take',
      status: take.has_audio ? 'done' : take.status,
      progress: 100,
      stage: '',
      hasAudio: Boolean(take.has_audio),
      hasScore: Boolean(take.abc && take.abc.trim()),
      duration: take.duration || 0,
      snapshot: snap,
      diffs: computeDiffs(null, snap),
      error: null
    }];
    JamState.cookingId = null;
    saveSession();
    paintAll();
    if (take.has_audio) {
      JamAudio.play(take.id, 0.08).catch(function () {});
    }
  }

  /* ------------------------------------------------- Rolling & Lyrics Drafting */
  function llmAvailable() {
    return Boolean(window.State && State.options && State.options.lyrics);
  }

  async function draftJamLyrics(styleText, theme, fastLoop) {
    var brief = theme === 'Keep current' ? 'short evocative verses matching the mood' : ('a song about ' + theme.toLowerCase());
    var payload = {
      brief: brief,
      style: styleText,
      structure: fastLoop ? 'short' : 'standard',
      sections: fastLoop ? ['Verse', 'Chorus'] : null,
      feel: 'natural'
    };
    var created = await api('/api/lyrics', { method: 'POST', body: JSON.stringify(payload) });
    for (var attempt = 0; attempt < 90; attempt++) {
      await new Promise(function (r) { setTimeout(r, 1000); });
      if (!JamState.open) { return null; }
      var rec = await api('/api/lyrics/' + encodeURIComponent(created.id));
      if (rec.status === 'done' && rec.lyrics) {
        return { title: rec.title, lyrics: rec.lyrics };
      }
      if (rec.status === 'failed' || rec.status === 'cancelled') {
        throw new Error(rec.error || 'Could not draft lyrics');
      }
    }
    throw new Error('Lyrics draft timed out');
  }

  function isSeedPass(p) {
    return Boolean(p && (p.isSeed || (JamState.sessionKey && JamState.sessionKey === 'take:' + p.id)));
  }

  function isSpaceTake(p) {
    return Boolean(p && (isSeedPass(p) || p.isFullSong || p.isTopLevelTake));
  }

  function readyBaseTakeWithScore() {
    var cur = JamState.passes.find(function (p) { return p.id === JamAudio.currentId && p.hasScore; });
    if (cur) { return cur; }
    return JamState.passes.find(function (p) { return p.hasScore; }) || null;
  }

  function activeLoraKind(name) {
    if (!name || !window.State || !State.options || !State.options.loras) { return ''; }
    var list = State.options.loras;
    for (var i = 0; i < list.length; i++) {
      if (list[i].name === name) { return list[i].kind || ''; }
    }
    return '';
  }

  function jamSpaceId() {
    if (JamState.spaceId && JamState.spaceId !== 'trash') { return JamState.spaceId; }
    var sp = (window.State && State.spaceId) || 'default';
    return sp === 'trash' ? 'default' : sp;
  }

  async function rollPass(opts) {
    opts = opts || {};
    if (JamState.cookingId || JamState.draftingLyrics) {
      if (typeof toast === 'function') { toast('A pass is already rolling — wait for it or cancel it first.'); }
      return;
    }
    var fastLoop = opts.fullSong ? false : JamState.fastLoop;
    var snap = opts.snapshot ? JSON.parse(JSON.stringify(opts.snapshot)) : cloneSnapshot();
    snap.fastLoop = fastLoop;
    var styleText = compileStyle(snap);
    var vi = vibeInfo(snap.vibe);

    // Handle vocals & lyrics automatically
    var lyricsText = snap.lyrics || '';
    var draftedTitle = null;
    if (snap.vocals !== 'instrumental') {
      var needDraft = !lyricsText.trim() || (JamState.lyricsDirtyTheme && snap.lyricTheme !== 'Keep current');
      if (needDraft) {
        if (llmAvailable()) {
          JamState.draftingLyrics = true;
          paintStage();
          paintTopbar();
          try {
            var drafted = await draftJamLyrics(styleText, snap.lyricTheme, fastLoop);
            if (drafted && drafted.lyrics) {
              lyricsText = drafted.lyrics;
              draftedTitle = drafted.title;
              JamState.lyrics = lyricsText;
              JamState.lyricsDirtyTheme = false;
              snap.lyrics = lyricsText;
            }
          } catch (err) {
            lyricsText = FALLBACK_LYRICS[snap.lyricTheme] || FALLBACK_LYRICS['Late nights'];
            JamState.lyrics = lyricsText;
            snap.lyrics = lyricsText;
          } finally {
            JamState.draftingLyrics = false;
          }
        } else {
          lyricsText = FALLBACK_LYRICS[snap.lyricTheme] || FALLBACK_LYRICS['Late nights'];
          JamState.lyrics = lyricsText;
          JamState.lyricsDirtyTheme = false;
          snap.lyrics = lyricsText;
        }
      }
    }

    var isFullSong = Boolean(opts.fullSong || !fastLoop);
    var passNum = JamState.passes.filter(function (p) { return !isSeedPass(p); }).length + 1;
    var baseScorePass = snap.lockScore ? readyBaseTakeWithScore() : null;
    var passTitle = draftedTitle || (isFullSong
      ? (JamState.starterName + ' (Jam #' + passNum + ')')
      : (JamState.starterName + ' \u00B7 Pass #' + passNum));
    var loraKind = activeLoraKind(snap.styleLora);

    var payload = {
      title: passTitle,
      space_id: jamSpaceId(),
      parent_id: null,
      snippet: !isFullSong,
      base_take_id: baseScorePass ? baseScorePass.id : null,
      lock_score: Boolean(baseScorePass),
      instrumental: snap.vocals === 'instrumental',
      style: styleText,
      lyrics: snap.vocals === 'instrumental' ? '' : lyricsText,
      brief: snap.vocals === 'instrumental' ? null : snap.lyricTheme,
      max_duration: isFullSong ? 210 : 40,
      target_bpm: snap.bpm,
      harmony: vi.harmony,
      interpretation: vi.interpretation,
      sampler_steps: isFullSong ? 32 : 24,
      realaudio: true,
      normalise: true,
      style_lora: snap.styleLora || null,
      style_lora_model: (loraKind === 'decoder' || loraKind === 'both') ? snap.styleLoraModel : 0,
      style_lora_clip: (loraKind === 'planner' || loraKind === 'both') ? snap.styleLoraClip : 0,
      voice_id: snap.vocals === 'voice' && snap.voiceId ? snap.voiceId : null
    };

    try {
      var created = await api('/api/jam/roll', { method: 'POST', body: JSON.stringify(payload) });
      var diffs = computeDiffs(JamState.lastRolledSnapshot, snap);
      if (isFullSong) { diffs.unshift({ text: 'Full Song \u00B7 Space', cls: 'add' }); }
      JamState.lastRolledSnapshot = snap;
      JamState.cookingId = created.id;
      JamState.passes.push({
        num: passNum,
        id: created.id,
        title: created.title || passTitle,
        status: 'queued',
        progress: 2,
        stage: 'Queued',
        hasAudio: false,
        hasScore: Boolean(baseScorePass),
        isFullSong: isFullSong,
        isSnippet: !isFullSong,
        isTopLevelTake: isFullSong,
        duration: 0,
        snapshot: snap,
        diffs: diffs,
        error: null
      });
      saveSession();
      paintAll();
      startPolling();
      if (isFullSong && typeof toast === 'function') { toast('Full song queued as a take in your space.'); }
      if (typeof loadTakes === 'function') { loadTakes(); }
    } catch (err) {
      if (typeof toast === 'function') { toast('Roll failed: ' + err.message); }
      paintAll();
    }
  }

  async function cancelCooking() {
    if (!JamState.cookingId) { return; }
    var id = JamState.cookingId;
    try {
      await api('/api/takes/' + encodeURIComponent(id) + '/cancel', { method: 'POST' });
    } catch (err) { /* ignore */ }
    var pass = JamState.passes.find(function (p) { return p.id === id; });
    if (pass) {
      pass.status = 'cancelled';
      pass.stage = 'Cancelled';
    }
    JamState.cookingId = null;
    stopPolling();
    paintAll();
  }

  function startPolling() {
    if (JamState.pollTimer) { return; }
    JamState.pollTimer = setInterval(pollCooking, 1200);
  }

  function stopPolling() {
    if (JamState.pollTimer) { clearInterval(JamState.pollTimer); JamState.pollTimer = null; }
  }

  async function pollCooking() {
    if (!JamState.cookingId) { stopPolling(); return; }
    var id = JamState.cookingId;
    var pass = JamState.passes.find(function (p) { return p.id === id; });
    if (!pass) { JamState.cookingId = null; stopPolling(); return; }
    try {
      var rec = await api('/api/takes/' + encodeURIComponent(id));
      pass.status = rec.status;
      pass.stage = rec.stage || rec.status;
      pass.hasAudio = Boolean(rec.has_audio);
      pass.hasScore = Boolean(rec.abc && rec.abc.trim());
      pass.duration = rec.duration || 0;
      if (rec.title) { pass.title = rec.title; }

      // Pull live engine progress from /api/state when this take is running
      try {
        var st = await api('/api/state');
        var cur = st && st.current;
        if (cur && cur.id === id) {
          if (typeof cur.progress === 'number') {
            pass.progress = Math.max(4, Math.min(98, Math.round(cur.progress * 100)));
          }
          if (cur.label) { pass.stage = cur.label; }
        } else if (rec.status === 'running') {
          pass.progress = Math.min(92, (pass.progress || 8) + 3);
        }
      } catch (e) { /* keep last progress */ }

      if (rec.status === 'done' && rec.has_audio) {
        pass.progress = 100;
        JamState.cookingId = null;
        stopPolling();
        saveSession();
        if (typeof loadTakes === 'function') { loadTakes(); }
        paintAll();
        // Smoothly crossfade into the newly rolled pass!
        if (JamState.open) {
          JamAudio.play(id, 2.2).catch(function () {});
        }
        return;
      }
      if (rec.status === 'failed' || rec.status === 'cancelled') {
        pass.error = rec.error || 'Did not finish';
        JamState.cookingId = null;
        stopPolling();
        saveSession();
        paintAll();
        return;
      }
      paintStage();
      paintHistory();
    } catch (err) { /* retry next tick */ }
  }

  /* ------------------------------------------------- Rendering */
  function fmtTime(sec) {
    sec = Math.max(0, Math.floor(sec || 0));
    var m = Math.floor(sec / 60);
    var s = sec % 60;
    return m + ':' + (s < 10 ? '0' : '') + s;
  }

  function escHtml(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  var JAM_MAX_KEY = 'yue2.jamMax';

  function jamMax() {
    try { return localStorage.getItem(JAM_MAX_KEY) === '1'; } catch (e) { return false; }
  }

  function setJamMax(on) {
    var modal = document.getElementById('jam-modal');
    if (modal) { modal.classList.toggle('jam-max', Boolean(on)); }
    var btn = document.getElementById('jam-max');
    if (btn) {
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      btn.title = on ? 'Back to the usual size' : 'Fill the window';
      btn.setAttribute('aria-label', btn.title);
    }
    try { localStorage.setItem(JAM_MAX_KEY, on ? '1' : '0'); } catch (e) {}
  }

  function buildShellOnce() {
    var shell = document.getElementById('jam-shell');
    if (!shell || shell.dataset.built) { return; }
    shell.dataset.built = '1';
    shell.innerHTML =
      '<div class="jam-topbar" id="jam-topbar"></div>' +
      '<div class="jam-stage" id="jam-stage"></div>' +
      '<div class="jam-console">' +
        '<div class="jam-col col-parts" id="jam-col-parts"></div>' +
        '<div class="jam-col col-feel" id="jam-col-feel"></div>' +
        '<div class="jam-col col-hist" id="jam-col-hist"></div>' +
      '</div>' +
      '<div class="jam-foot" id="jam-foot"></div>';

    // Delegated click & input events across the whole Jam desk
    shell.addEventListener('click', onShellClick);
    shell.addEventListener('input', onShellInput);
    shell.addEventListener('change', onShellChange);
    shell.addEventListener('keydown', onShellKeydown);
    shell.addEventListener('pointerdown', onPointerDown);
    setJamMax(jamMax());
  }

  function paintAll() {
    buildShellOnce();
    paintTopbar();
    paintStage();
    paintPartsCol();
    paintFeelCol();
    paintHistory();
    paintFooter();
  }

  function paintTopbar() {
    var el = document.getElementById('jam-topbar');
    if (!el) { return; }
    var hasScore = Boolean(readyBaseTakeWithScore());
    var isMax = jamMax();

    var starterOpts = STARTERS.map(function (st) {
      return '<option value="' + escHtml(st.id) + '"' + (st.name === JamState.starterName ? ' selected' : '') + '>' + escHtml(st.name) + '</option>';
    }).join('');

    el.innerHTML =
      '<div class="jam-brand">' +
        '<span class="jam-bar"></span>' +
        '<h1 class="jam-title">Jam</h1>' +
        '<select id="jam-starter-select" class="jam-starter-select" title="Load a starter groove">' +
          (!STARTERS.some(function (s) { return s.name === JamState.starterName; })
            ? '<option value="__custom__" selected>Seeded: ' + escHtml(JamState.starterName) + '</option>' : '') +
          starterOpts +
        '</select>' +
      '</div>' +
      '<div class="jam-scope">' +
        '<div class="jam-seg-pill" title="35s Fast Loop renders 3–5× faster for rapid experimentation">' +
          '<button type="button" data-jam-act="scope-fast" class="' + (JamState.fastLoop ? 'active' : '') + '">35s Fast Loop</button>' +
          '<button type="button" data-jam-act="scope-full" class="' + (!JamState.fastLoop ? 'active' : '') + '">Full Song</button>' +
        '</div>' +
        '<button type="button" data-jam-act="toggle-lock" class="jam-lock-btn' + (JamState.lockScore ? ' on' : '') + '"' +
          (!hasScore ? ' disabled title="Roll at least one pass first to lock its melody & chords"' : ' title="Keep the same ABC melody and chords while rolling new Parts and vibe"') + '>' +
          '<span>' + (JamState.lockScore ? '\uD83D\uDD12' : '\uD83D\uDD13') + '</span> Lock Melody &amp; Chords' +
        '</button>' +
      '</div>' +
      '<div class="jam-head-actions">' +
        '<button type="button" class="ghost" data-jam-act="close" style="padding:7px 14px">Close</button>' +
        '<button type="button" id="jam-max" data-jam-act="toggle-max" class="ed-tool ed-max-btn" title="' + (isMax ? 'Back to the usual size' : 'Fill the window') + '" aria-label="' + (isMax ? 'Back to the usual size' : 'Fill the window') + '" aria-pressed="' + (isMax ? 'true' : 'false') + '">' +
          '<svg class="max-on" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>' +
          '<svg class="max-off" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/></svg>' +
        '</button>' +
      '</div>';
    paintFooter();
  }

  function paintFooter() {
    var el = document.getElementById('jam-foot');
    if (!el) { return; }
    var pending = pendingChangeCount();
    var cooking = Boolean(JamState.cookingId || JamState.draftingLyrics);
    var hasPlayable = JamState.passes.some(function (p) { return p.hasAudio; });

    el.innerHTML =
      '<span class="jam-foot-hint muted small">Space to play / pause \u00B7 Esc to close</span>' +
      '<div class="jam-foot-actions">' +
        (JamState.passes.length ? '<button type="button" class="jam-sec-btn" data-jam-act="reset-jam" title="Start a fresh Jam session">New Jam</button>' : '') +
        (hasPlayable && JamState.fastLoop ? '<button type="button" class="jam-sec-btn" data-jam-act="render-full" title="Render a full-length song as a take in your space"' + (cooking ? ' disabled' : '') + '>Render Full Song</button>' : '') +
        '<button type="button" class="jam-roll-btn" data-jam-act="roll"' + (cooking ? ' disabled' : '') + '>' +
          '<span>' + (JamState.draftingLyrics ? 'Drafting lyrics\u2026' : (JamState.cookingId ? 'Rolling\u2026' : '\u27F3 Roll')) + '</span>' +
          (!cooking && pending > 0 ? '<span class="jam-pending-badge">' + pending + (pending === 1 ? ' change' : ' changes') + '</span>' : '') +
        '</button>' +
      '</div>';
  }

  function paintStage() {
    var el = document.getElementById('jam-stage');
    if (!el) { return; }
    var playingPass = JamState.passes.find(function (p) { return p.id === JamAudio.currentId; });
    var cookingPass = JamState.cookingId ? JamState.passes.find(function (p) { return p.id === JamState.cookingId; }) : null;
    var peaks = (playingPass && JamAudio.peaks[playingPass.id]) || null;
    var dur = JamAudio.duration() || (playingPass && playingPass.duration) || 0;
    var pos = JamAudio.position();
    var frac = dur > 0 ? Math.min(1, pos / dur) : 0;

    var barsHtml = '';
    var count = 64;
    for (var i = 0; i < count; i++) {
      var h = peaks ? Math.round(peaks[i] * 88) : (22 + Math.round(Math.abs(Math.sin(i * 0.42)) * 46));
      var played = peaks && (i / count) <= frac;
      barsHtml += '<span class="jam-wave-bar' + (played ? ' played' : '') + '" style="height:' + h + '%"></span>';
    }

    var playIcon = JamAudio.playing
      ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>'
      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.4v13.2L19 12z"/></svg>';

    var statusPill = '';
    if (JamState.draftingLyrics) {
      statusPill = '<span class="jam-status-pill"><span class="jam-pulse-dot"></span> Drafting lyrics\u2026</span>';
    } else if (cookingPass) {
      statusPill = '<span class="jam-status-pill"><span class="jam-pulse-dot"></span> Rolling Pass #' + cookingPass.num + ' \u00B7 ' +
        escHtml(cookingPass.stage || 'Working') + ' (' + (cookingPass.progress || 0) + '%)' +
        ' <button type="button" class="jam-cancel-x" data-jam-act="cancel-cook" title="Cancel this roll">&times;</button></span>';
    } else {
      statusPill = '<span class="jam-xfade-pill">\u21C4 Crossfade on ready</span>';
    }

    el.innerHTML =
      '<button type="button" class="jam-play-btn" data-jam-act="toggle-play"' + (!playingPass && !JamState.passes.some(function (p) { return p.hasAudio; }) ? ' disabled' : '') + '>' + playIcon + '</button>' +
      '<div class="jam-stage-meta">' +
        '<div class="jam-stage-title">' +
          (playingPass ? escHtml(playingPass.title) + ' <span class="jam-pass-badge">' + (isSeedPass(playingPass) ? 'Seed' : 'Pass #' + playingPass.num) + '</span>' : 'Ready to roll your first pass') +
        '</div>' +
        '<div class="jam-stage-sub">' +
          (playingPass ? (JamAudio.playing ? 'Looping seamlessly' : 'Paused') + ' \u00B7 ' + JamState.bpm + ' BPM' : 'Tweak Parts, Vibe &amp; Tempo below, then click Roll') +
        '</div>' +
      '</div>' +
      '<span class="jam-wave-time" id="jam-t-now">' + fmtTime(pos) + '</span>' +
      '<div class="jam-wave" id="jam-wave" title="Click to seek">' + barsHtml + '</div>' +
      '<span class="jam-wave-time" id="jam-t-dur">' + fmtTime(dur) + '</span>' +
      statusPill;
  }

  function paintWaveProgress() {
    var wave = document.getElementById('jam-wave');
    var nowEl = document.getElementById('jam-t-now');
    if (!wave || !nowEl) { return; }
    var dur = JamAudio.duration();
    var pos = JamAudio.position();
    nowEl.textContent = fmtTime(pos);
    var frac = dur > 0 ? Math.min(1, pos / dur) : 0;
    var bars = wave.children;
    var cut = Math.floor(frac * bars.length);
    for (var i = 0; i < bars.length; i++) {
      bars[i].classList.toggle('played', i <= cut);
    }
  }

  function paintPartsCol() {
    var el = document.getElementById('jam-col-parts');
    if (!el) { return; }

    var activeHtml = JamState.parts.length
      ? JamState.parts.map(function (p, idx) {
          var pips = '';
          for (var lv = 1; lv <= 4; lv++) {
            pips += '<i class="jam-pip' + (lv <= p.level ? ' on' : '') + '"></i>';
          }
          var pending = isPartPending(p.name) ? ' pending' : '';
          return '<span class="jam-part-chip cat-' + escHtml(p.cat) + pending + '">' +
            '<span>' + escHtml(p.name) + '</span>' +
            '<span class="jam-pips" data-part-idx="' + idx + '" title="Strength: ' + LEVEL_LABELS[p.level] + ' (drag left/right)">' + pips + '</span>' +
            '<button type="button" class="jam-part-x" data-jam-act="remove-part" data-part-idx="' + idx + '" aria-label="Remove ' + escHtml(p.name) + '">&times;</button>' +
          '</span>';
        }).join('')
      : '<span class="muted small">No Parts yet — click any chip below or type your own.</span>';

    var q = JamState.searchQuery.trim().toLowerCase();
    var activeSet = {};
    JamState.parts.forEach(function (p) { activeSet[p.name.toLowerCase()] = true; });
    var tabItems = PALETTE[JamState.paletteTab] || [];
    var filtered = q
      ? Object.keys(PALETTE).reduce(function (acc, cat) {
          PALETTE[cat].forEach(function (name) {
            if (name.toLowerCase().indexOf(q) >= 0) { acc.push({ name: name, cat: cat }); }
          });
          return acc;
        }, [])
      : tabItems.map(function (name) { return { name: name, cat: JamState.paletteTab }; });

    var paletteHtml = filtered.map(function (item) {
      var added = Boolean(activeSet[item.name.toLowerCase()]);
      return '<button type="button" class="jam-pick-chip' + (added ? ' added' : '') + '" data-jam-act="toggle-part" data-part-name="' + escHtml(item.name) + '" data-part-cat="' + escHtml(item.cat) + '">' +
        (added ? '\u2713 ' : '+ ') + escHtml(item.name) + '</button>';
    }).join('');
    if (q && !filtered.some(function (i) { return i.name.toLowerCase() === q; })) {
      paletteHtml = '<button type="button" class="jam-pick-chip custom" data-jam-act="add-custom-part">+ Add "' + escHtml(JamState.searchQuery.trim()) + '"</button>' + paletteHtml;
    }

    // Build Style LoRA options from Yeufonic's loaded #style-lora select
    var loraSelect = document.getElementById('style-lora');
    var loraOptions = '<option value="">None</option>';
    if (loraSelect) {
      Array.prototype.forEach.call(loraSelect.querySelectorAll('option:not([data-parent])'), function (opt) {
        if (!opt.value) { return; }
        var title = opt.dataset.title || opt.textContent;
        loraOptions += '<option value="' + escHtml(opt.value) + '"' + (opt.value === JamState.styleLora ? ' selected' : '') + '>' + escHtml(title) + '</option>';
      });
    }
    var loraKind = activeLoraKind(JamState.styleLora);
    var hasSound = loraKind === 'decoder' || loraKind === 'both';
    var hasPlan = loraKind === 'planner' || loraKind === 'both';

    // Preserve search input focus if currently typing
    var searchFocused = document.activeElement && document.activeElement.id === 'jam-part-search';
    var selStart = searchFocused ? document.activeElement.selectionStart : null;

    el.innerHTML =
      '<div class="jam-col-head">' +
        '<div class="jam-col-head-l">' +
          '<h4>Sound &amp; Parts</h4>' +
          '<button type="button" class="jam-clear-btn" data-jam-act="clear-parts" title="Clear all active Parts"' + (JamState.parts.length ? '' : ' disabled') + '>Clear</button>' +
        '</div>' +
        '<span class="jam-col-meta">' + JamState.parts.length + ' / ' + MAX_PARTS + ' active \u00B7 drag bars for strength</span>' +
      '</div>' +
      '<div class="jam-parts-rack">' + activeHtml + '</div>' +
      '<div class="jam-palette">' +
        '<div class="picker-search-field">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>' +
          '<input type="search" id="jam-part-search" placeholder="Add any genre, instrument or texture\u2026" value="' + escHtml(JamState.searchQuery) + '" autocomplete="off">' +
        '</div>' +
        '<div class="jam-tabs">' +
          [['inst', 'Instruments'], ['genre', 'Genres'], ['prod', 'Production'], ['rhythm', 'Rhythm']].map(function (tab) {
            return '<button type="button" class="jam-tab' + (JamState.paletteTab === tab[0] ? ' active' : '') + '" data-jam-act="palette-tab" data-tab="' + tab[0] + '">' + tab[1] + '</button>';
          }).join('') +
        '</div>' +
        '<div class="jam-palette-chips">' + paletteHtml + '</div>' +
      '</div>' +
      '<div class="jam-lora-slot">' +
        '<div class="jam-kicker"><span>Style LoRA (optional)</span>' +
          (loraKind ? '<span class="kind-pill kind-' + escHtml(loraKind) + '">' + escHtml(loraKind === 'both' ? 'score & sound' : (loraKind === 'decoder' ? 'sound only' : 'score only')) + '</span>' : '') +
        '</div>' +
        '<select id="jam-lora-select" style="padding:7px 10px;font-size:12.5px">' + loraOptions + '</select>' +
        (JamState.styleLora
          ? '<div class="jam-lora-sliders">' +
              '<label>Sound <strong>' + (hasSound ? JamState.styleLoraModel.toFixed(2) : 'N/A') + '</strong>' +
                '<input id="jam-lora-sound" type="range" min="0" max="2" step="0.05" value="' + JamState.styleLoraModel + '"' + (hasSound ? '' : ' disabled') + '>' +
              '</label>' +
              '<label>Score <strong>' + (hasPlan ? JamState.styleLoraClip.toFixed(2) : 'N/A') + '</strong>' +
                '<input id="jam-lora-plan" type="range" min="0" max="2" step="0.05" value="' + JamState.styleLoraClip + '"' + (hasPlan ? '' : ' disabled') + '>' +
              '</label>' +
            '</div>' : '') +
      '</div>';

    if (searchFocused && document.getElementById('jam-part-search')) {
      var inp = document.getElementById('jam-part-search');
      inp.focus();
      if (selStart != null) { inp.setSelectionRange(selStart, selStart); }
    }
  }

  function paintFeelCol() {
    var el = document.getElementById('jam-col-feel');
    if (!el) { return; }
    var vi = vibeInfo(JamState.vibe);
    var px = Math.round(JamState.vibe.x * 100);
    var py = Math.round((1 - JamState.vibe.y) * 100);

    var readyVoices = (window.VOICES && VOICES.list ? VOICES.list : []).filter(function (v) { return v.state === 'ready'; });
    var hasVoices = Boolean(window.VOICES && VOICES.service && VOICES.service.ok && readyVoices.length);
    var voiceSelectHtml = '';
    if (JamState.vocals === 'voice') {
      voiceSelectHtml = '<select id="jam-voice-select" style="padding:6px 10px;font-size:12.5px">' +
        '<option value="">Choose a recorded voice\u2026</option>' +
        readyVoices.map(function (v) {
          return '<option value="' + escHtml(v.id) + '"' + (v.id === JamState.voiceId ? ' selected' : '') + '>' + escHtml(v.name) + '</option>';
        }).join('') + '</select>';
    }

    var vocalExtras = '';
    if (JamState.vocals !== 'instrumental') {
      vocalExtras =
        voiceSelectHtml +
        '<div class="jam-chip-row"><span class="jam-row-lbl">Tone:</span>' +
          VOCAL_TONES.map(function (tn) {
            var on = JamState.tones.indexOf(tn) >= 0;
            return '<button type="button" class="jam-mini-chip' + (on ? ' on' : '') + '" data-jam-act="toggle-tone" data-tone="' + escHtml(tn) + '">' + escHtml(tn) + '</button>';
          }).join('') +
        '</div>' +
        '<div class="jam-chip-row"><span class="jam-row-lbl">Theme:</span>' +
          LYRIC_THEMES.map(function (th) {
            var on = JamState.lyricTheme === th;
            return '<button type="button" class="jam-mini-chip' + (on ? ' on' : '') + '" data-jam-act="pick-theme" data-theme="' + escHtml(th) + '">' + escHtml(th) + '</button>';
          }).join('') +
        '</div>' +
        '<textarea id="jam-lyrics-box" class="jam-lyrics-box" rows="3" placeholder="' +
          (llmAvailable() ? 'Lyrics auto-draft when you Roll — or type your own here…' : 'Type short lyrics here (or leave blank for a quick starter verse)…') +
          '">' + escHtml(JamState.lyrics) + '</textarea>';
    }

    var lyricsFocused = document.activeElement && document.activeElement.id === 'jam-lyrics-box';

    el.innerHTML =
      '<div class="jam-col-head">' +
        '<h4>Vibe, Tempo &amp; Vocals</h4>' +
        '<span class="jam-col-meta">Direct studio controls</span>' +
      '</div>' +
      '<div class="jam-xy-wrap">' +
        '<div class="jam-xy-pad" id="jam-xy-pad" title="Drag or click to shift mood &amp; energy">' +
          '<div class="jam-xy-grid"></div>' +
          '<div class="jam-xy-axis-h"></div><div class="jam-xy-axis-v"></div>' +
          '<span class="jam-xy-lbl top">Energetic</span>' +
          '<span class="jam-xy-lbl bot">Calm</span>' +
          '<span class="jam-xy-lbl lft">Dark</span>' +
          '<span class="jam-xy-lbl rgt">Bright</span>' +
          '<div class="jam-xy-puck" id="jam-xy-puck" style="left:' + px + '%;top:' + py + '%"></div>' +
        '</div>' +
        '<div class="jam-xy-side">' +
          '<div class="jam-vibe-box">' +
            '<div class="jam-kicker"><span>Vibe</span><span style="color:var(--cover-a)">' + escHtml(vi.xWord) + ' \u00B7 ' + escHtml(vi.yWord) + '</span></div>' +
            '<div class="jam-vibe-word" id="jam-vibe-word">' + escHtml(vi.word) + '</div>' +
            '<div class="jam-vibe-hint">Drag pad to shape mood &amp; harmony</div>' +
          '</div>' +
          '<div class="jam-tempo-box">' +
            '<div class="jam-kicker"><span>Tempo</span><span class="jam-bpm-val" id="jam-bpm-val">' + JamState.bpm + ' BPM</span></div>' +
            '<input id="jam-bpm-slider" type="range" min="60" max="165" step="2" value="' + JamState.bpm + '">' +
            '<div class="jam-detents"><span>Slow</span><span>Med</span><span>Fast</span></div>' +
          '</div>' +
        '</div>' +
      '</div>' +
      '<div class="jam-vocal-card">' +
        '<div class="jam-kicker"><span>Vocals</span><span>' + (JamState.vocals === 'instrumental' ? 'No vocals' : (llmAvailable() ? 'Auto-drafts lyrics on Roll' : 'Editable lyrics')) + '</span></div>' +
        '<div class="jam-mini-seg">' +
          '<button type="button" data-jam-act="vocals" data-v="instrumental" class="' + (JamState.vocals === 'instrumental' ? 'active' : '') + '">Instrumental</button>' +
          '<button type="button" data-jam-act="vocals" data-v="female" class="' + (JamState.vocals === 'female' ? 'active' : '') + '">Female</button>' +
          '<button type="button" data-jam-act="vocals" data-v="male" class="' + (JamState.vocals === 'male' ? 'active' : '') + '">Male</button>' +
          '<button type="button" data-jam-act="vocals" data-v="voice" class="' + (JamState.vocals === 'voice' ? 'active' : '') + '"' + (!hasVoices ? ' disabled title="No ready recorded voices yet"' : '') + '>My Voice</button>' +
        '</div>' +
        vocalExtras +
      '</div>' +
      '<div class="jam-prompt-peek">' +
        '<strong>Compiled Style \u2192 YuE2</strong>' +
        '<span id="jam-compiled-style">' + escHtml(compileStyle()) + '</span>' +
      '</div>';

    if (lyricsFocused && document.getElementById('jam-lyrics-box')) {
      document.getElementById('jam-lyrics-box').focus();
    }
  }

  function paintHistory() {
    var el = document.getElementById('jam-col-hist');
    if (!el) { return; }
    // Seed take pinned at the top, followed by all rolled passes in chronological order below it.
    var ordered = JamState.passes.slice().sort(function (a, b) {
      var aSeed = isSeedPass(a) ? 0 : 1;
      var bSeed = isSeedPass(b) ? 0 : 1;
      if (aSeed !== bSeed) { return aSeed - bSeed; }
      return (a.num || 0) - (b.num || 0);
    });
    var rolledCount = ordered.filter(function (p) { return !isSeedPass(p); }).length;
    var hasSeed = ordered.some(isSeedPass);

    var cards = ordered.length
      ? ordered.map(function (p) {
          var seed = isSeedPass(p);
          var isPlaying = p.id === JamAudio.currentId && JamAudio.playing;
          var isActive = p.id === JamAudio.currentId;
          var isCooking = p.id === JamState.cookingId;
          var isFailed = p.status === 'failed' || p.status === 'cancelled';

          var statePill = isCooking
            ? '<span class="jam-hist-state cook">Rolling ' + (p.progress || 0) + '%</span>'
            : (isPlaying ? '<span class="jam-hist-state live">\u25B6 Playing</span>'
              : (isFailed ? '<span class="jam-hist-state bad">' + escHtml(p.status) + '</span>'
                : '<span class="jam-hist-num">' + (p.duration ? fmtTime(p.duration) : 'Ready') + '</span>'));

          var diffsHtml = (p.diffs || []).map(function (d) {
            return '<span class="jam-diff ' + escHtml(d.cls || '') + '">' + escHtml(d.text) + '</span>';
          }).join('');

          var actions = '';
          if (isCooking) {
            actions = '<div class="jam-cook-bar"><span style="width:' + (p.progress || 5) + '%"></span></div>' +
              '<div class="jam-hist-actions"><button type="button" class="jam-hist-btn" data-jam-act="cancel-cook">Cancel</button></div>';
          } else if (seed) {
            actions = p.hasAudio
              ? '<div class="jam-hist-actions">' +
                  (isPlaying
                    ? '<button type="button" class="jam-hist-btn stop" data-jam-act="stop-pass">\u25A0 Stop</button>'
                    : '<button type="button" class="jam-hist-btn" data-jam-act="play-pass" data-pass-id="' + escHtml(p.id) + '">\u25B6 Play</button>') +
                '</div>'
              : '';
          } else if (p.hasAudio) {
            var canDelete = !isSpaceTake(p);
            actions = '<div class="jam-hist-actions">' +
              (isPlaying
                ? '<button type="button" class="jam-hist-btn stop" data-jam-act="stop-pass">\u25A0 Stop</button>'
                : '<button type="button" class="jam-hist-btn" data-jam-act="play-pass" data-pass-id="' + escHtml(p.id) + '">\u25B6 Play</button>') +
              (!p.isFullSong ? '<button type="button" class="jam-hist-btn" data-jam-act="full-pass" data-pass-id="' + escHtml(p.id) + '">Full Song</button>' : '') +
              '<button type="button" class="jam-hist-btn" data-jam-act="open-editor" data-pass-id="' + escHtml(p.id) + '">Editor</button>' +
              (canDelete ? '<button type="button" class="jam-hist-btn danger" data-jam-act="delete-pass" data-pass-id="' + escHtml(p.id) + '" title="Move this nested pass to Trash">Delete</button>' : '') +
            '</div>';
          } else {
            actions = (p.error ? '<div class="small" style="color:var(--danger-text)">' + escHtml(p.error) + '</div>' : '') +
              '<div class="jam-hist-actions">' +
                '<button type="button" class="jam-hist-btn danger" data-jam-act="delete-pass" data-pass-id="' + escHtml(p.id) + '" title="Remove this pass">Delete</button>' +
              '</div>';
          }

          var tagHtml = seed
            ? '<span class="jam-seed-tag">Seed</span>'
            : '<span class="jam-hist-num">Pass #' + p.num + '</span>';

          return '<div class="jam-hist-card' + (seed ? ' is-seed' : '') + (isActive ? ' active' : '') + (isPlaying ? ' playing' : '') + (isCooking ? ' cooking' : '') + '">' +
            '<div class="jam-hist-top">' +
              '<span class="jam-hist-name">' + tagHtml + ' ' + escHtml(p.title) + '</span>' +
              statePill +
            '</div>' +
            '<div class="jam-hist-diffs">' + diffsHtml + '</div>' +
            actions +
          '</div>';
        }).join('')
      : '<div class="jam-hist-empty">' +
          '<strong>No passes yet</strong>' +
          '<p class="muted small">Shape your Parts, Vibe &amp; Tempo on the left, then click <b>Roll</b>. Each pass loops seamlessly while your next roll cooks and crossfades in.</p>' +
        '</div>';

    var countLabel = hasSeed
      ? ('Seed' + (rolledCount ? ' + ' + rolledCount + (rolledCount === 1 ? ' pass' : ' passes') : ''))
      : (rolledCount + (rolledCount === 1 ? ' pass' : ' passes'));

    el.innerHTML =
      '<div class="jam-col-head">' +
        '<h4>Roll History</h4>' +
        '<span class="jam-col-meta">' + countLabel + '</span>' +
      '</div>' +
      '<div class="jam-hist-list">' + cards + '</div>';
  }

  /* ------------------------------------------------- Interactions */
  function togglePart(name, cat) {
    var key = name.toLowerCase();
    var idx = JamState.parts.findIndex(function (p) { return p.name.toLowerCase() === key; });
    if (idx >= 0) {
      JamState.parts.splice(idx, 1);
    } else {
      if (JamState.parts.length >= MAX_PARTS) {
        if (typeof toast === 'function') { toast('Up to ' + MAX_PARTS + ' Parts per roll.'); }
        return;
      }
      JamState.parts.push({ name: name, cat: cat || 'inst', level: 2 });
    }
    paintPartsCol();
    paintTopbar();
    updateCompiledPreview();
  }

  function updateCompiledPreview() {
    var el = document.getElementById('jam-compiled-style');
    if (el) { el.textContent = compileStyle(); }
  }

  function onShellClick(event) {
    var wave = event.target.closest('#jam-wave');
    if (wave) {
      var rect = wave.getBoundingClientRect();
      JamAudio.seekFraction((event.clientX - rect.left) / Math.max(1, rect.width));
      return;
    }
    var btn = event.target.closest('[data-jam-act]');
    if (!btn) { return; }
    var act = btn.dataset.jamAct;
    if (act === 'close') { close(); return; }
    if (act === 'toggle-max') { setJamMax(!jamMax()); return; }
    if (act === 'reset-jam') {
      JamState.sessionKey = '__standalone__';
      applyStarter(STARTERS[0]);
      return;
    }
    if (act === 'roll') { rollPass(); return; }
    if (act === 'render-full') { rollPass({ fullSong: true }); return; }
    if (act === 'cancel-cook') { cancelCooking(); return; }
    if (act === 'toggle-play') { JamAudio.toggle(); return; }
    if (act === 'scope-fast') { JamState.fastLoop = true; paintTopbar(); return; }
    if (act === 'scope-full') { JamState.fastLoop = false; paintTopbar(); return; }
    if (act === 'toggle-lock') {
      if (!readyBaseTakeWithScore()) { return; }
      JamState.lockScore = !JamState.lockScore;
      paintTopbar();
      return;
    }
    if (act === 'palette-tab') {
      JamState.paletteTab = btn.dataset.tab;
      paintPartsCol();
      return;
    }
    if (act === 'toggle-part') {
      togglePart(btn.dataset.partName, btn.dataset.partCat);
      return;
    }
    if (act === 'add-custom-part') {
      var text = JamState.searchQuery.trim();
      if (text) {
        togglePart(text, JamState.paletteTab);
        JamState.searchQuery = '';
        paintPartsCol();
      }
      return;
    }
    if (act === 'clear-parts') {
      if (JamState.parts.length) {
        JamState.parts = [];
        paintPartsCol();
        paintTopbar();
        updateCompiledPreview();
      }
      return;
    }
    if (act === 'remove-part') {
      var rIdx = parseInt(btn.dataset.partIdx, 10);
      if (!isNaN(rIdx)) { JamState.parts.splice(rIdx, 1); paintPartsCol(); paintTopbar(); updateCompiledPreview(); }
      return;
    }
    if (act === 'vocals') {
      JamState.vocals = btn.dataset.v;
      if (JamState.vocals !== 'instrumental' && !JamState.lyrics.trim()) { JamState.lyricsDirtyTheme = true; }
      paintFeelCol();
      paintTopbar();
      return;
    }
    if (act === 'toggle-tone') {
      var tn = btn.dataset.tone;
      var ti = JamState.tones.indexOf(tn);
      if (ti >= 0) { JamState.tones.splice(ti, 1); } else if (JamState.tones.length < 3) { JamState.tones.push(tn); }
      paintFeelCol();
      paintTopbar();
      return;
    }
    if (act === 'pick-theme') {
      JamState.lyricTheme = btn.dataset.theme;
      JamState.lyricsDirtyTheme = (JamState.lyricTheme !== 'Keep current');
      paintFeelCol();
      paintTopbar();
      return;
    }
    if (act === 'play-pass') {
      JamAudio.play(btn.dataset.passId, 0.8).catch(function () {});
      return;
    }
    if (act === 'stop-pass') {
      JamAudio.pause();
      return;
    }
    if (act === 'delete-pass') {
      deletePass(btn.dataset.passId);
      return;
    }
    if (act === 'full-pass') {
      var fp = JamState.passes.find(function (p) { return p.id === btn.dataset.passId; });
      if (fp) { rollPass({ fullSong: true, snapshot: fp.snapshot }); }
      return;
    }
    if (act === 'open-editor') {
      openPassInEditor(btn.dataset.passId);
    }
  }

  async function deletePass(passId) {
    if (!passId) { return; }
    var target = JamState.passes.find(function (p) { return p.id === passId; });
    if (isSpaceTake(target) && target && target.hasAudio) { return; }
    // Verify with the server: only scratch snippets (__jam__) or nested child passes can be deleted from Jam.
    try {
      var check = await api('/api/takes/' + encodeURIComponent(passId));
      if (check && check.space_id !== '__jam__' && !check.parent_id && check.has_audio) {
        if (target) { target.isTopLevelTake = true; saveSession(); paintHistory(); }
        if (typeof toast === 'function') { toast('This pass is a saved take in your space — delete it from the library instead.'); }
        return;
      }
    } catch (err) { /* proceed to clean up local history if already gone */ }
    if (JamAudio.currentId === passId) {
      JamAudio.stop();
      JamAudio.currentId = null;
    }
    delete JamAudio.buffers[passId];
    delete JamAudio.peaks[passId];

    try {
      await api('/api/takes/' + encodeURIComponent(passId), { method: 'DELETE' });
    } catch (err) {
      if (typeof toast === 'function') { toast('Could not delete pass: ' + err.message); }
      return;
    }
    JamState.passes = JamState.passes.filter(function (p) { return p.id !== passId; });
    if (!JamState.passes.length) {
      JamState.lastRolledSnapshot = null;
      JamState.lockScore = false;
    }
    saveSession();
    paintAll();
    if (typeof loadTakes === 'function') { loadTakes(); }
  }

  async function openPassInEditor(targetId) {
    if (!targetId) { return; }
    try {
      var tObj = await api('/api/takes/' + encodeURIComponent(targetId));
      close();
      if (typeof loadTakes === 'function') { loadTakes(); }
      if (tObj && typeof selectTake === 'function') {
        selectTake(tObj);
        if (typeof openEditor === 'function') { openEditor('song'); }
      }
    } catch (err) {
      if (typeof toast === 'function') { toast('Could not open take in Editor: ' + err.message); }
    }
  }

  function handleKey(event) {
    if (!JamState.open) { return false; }
    var el = document.activeElement;
    var tag = (el && el.tagName) || '';
    if (tag === 'TEXTAREA' || tag === 'SELECT' || (el && el.isContentEditable)) { return false; }
    if (tag === 'INPUT' && el.type !== 'range' && el.type !== 'checkbox' && el.type !== 'button') { return false; }
    if (event.code === 'Space') {
      JamAudio.toggle();
      return true;
    }
    return false;
  }

  function onShellInput(event) {
    var t = event.target;
    if (t.id === 'jam-part-search') {
      JamState.searchQuery = t.value;
      paintPartsCol();
      return;
    }
    if (t.id === 'jam-bpm-slider') {
      JamState.bpm = parseInt(t.value, 10) || 96;
      var lbl = document.getElementById('jam-bpm-val');
      if (lbl) { lbl.textContent = JamState.bpm + ' BPM'; }
      updateCompiledPreview();
      paintTopbar();
      return;
    }
    if (t.id === 'jam-lyrics-box') {
      JamState.lyrics = t.value;
      JamState.lyricsDirtyTheme = false;
      JamState.lyricTheme = 'Keep current';
      return;
    }
    if (t.id === 'jam-lora-sound') {
      JamState.styleLoraModel = parseFloat(t.value);
      paintPartsCol();
      return;
    }
    if (t.id === 'jam-lora-plan') {
      JamState.styleLoraClip = parseFloat(t.value);
      paintPartsCol();
      return;
    }
  }

  function onShellChange(event) {
    var t = event.target;
    if (t.id === 'jam-starter-select') {
      var st = STARTERS.find(function (s) { return s.id === t.value; });
      if (st) { applyStarter(st); }
      return;
    }
    if (t.id === 'jam-lora-select') {
      JamState.styleLora = t.value;
      paintPartsCol();
      paintTopbar();
      return;
    }
    if (t.id === 'jam-voice-select') {
      JamState.voiceId = t.value;
      paintTopbar();
      return;
    }
  }

  function onShellKeydown(event) {
    if (event.target.id === 'jam-part-search' && event.key === 'Enter') {
      event.preventDefault();
      var text = JamState.searchQuery.trim();
      if (text) {
        togglePart(text, JamState.paletteTab);
        JamState.searchQuery = '';
        paintPartsCol();
      }
    }
  }

  function onPointerDown(event) {
    var pips = event.target.closest('.jam-pips');
    if (pips) {
      var pIdx = parseInt(pips.dataset.partIdx, 10);
      if (isNaN(pIdx) || !JamState.parts[pIdx]) { return; }
      event.preventDefault();
      var rect = pips.getBoundingClientRect();
      pips.classList.add('dragging');
      var applyLevel = function (clientX) {
        var frac = (clientX - rect.left) / Math.max(1, rect.width);
        var lv = frac <= 0.12 ? 1 : Math.max(1, Math.min(4, Math.ceil(frac * 4)));
        var part = JamState.parts[pIdx];
        if (!part || part.level === lv) { return; }
        part.level = lv;
        var bars = pips.children;
        for (var i = 0; i < bars.length; i++) {
          bars[i].classList.toggle('on', i < lv);
        }
        pips.title = 'Strength: ' + LEVEL_LABELS[lv] + ' (drag left/right)';
        updateCompiledPreview();
      };
      applyLevel(event.clientX);
      var movePips = function (e) { applyLevel(e.clientX); };
      var upPips = function () {
        pips.classList.remove('dragging');
        window.removeEventListener('pointermove', movePips);
        window.removeEventListener('pointerup', upPips);
        paintPartsCol();
        paintTopbar();
        updateCompiledPreview();
      };
      window.addEventListener('pointermove', movePips);
      window.addEventListener('pointerup', upPips);
      return;
    }
    var pad = event.target.closest('#jam-xy-pad');
    if (!pad) { return; }
    event.preventDefault();
    var move = function (e) {
      var r = pad.getBoundingClientRect();
      var x = Math.max(0.03, Math.min(0.97, (e.clientX - r.left) / Math.max(1, r.width)));
      var y = Math.max(0.03, Math.min(0.97, 1 - (e.clientY - r.top) / Math.max(1, r.height)));
      JamState.vibe = { x: x, y: y };
      var puck = document.getElementById('jam-xy-puck');
      if (puck) { puck.style.left = Math.round(x * 100) + '%'; puck.style.top = Math.round((1 - y) * 100) + '%'; }
      var vi = vibeInfo(JamState.vibe);
      var word = document.getElementById('jam-vibe-word');
      if (word) { word.textContent = vi.word; }
      updateCompiledPreview();
    };
    move(event);
    var up = function () {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      paintFeelCol();
      paintTopbar();
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  }

  /* ------------------------------------------------- Public API */
  function open() {
    var modal = document.getElementById('jam-modal');
    if (!modal) { return; }
    JamState.open = true;
    modal.classList.remove('hidden');
    var key = JamState.sessionKey || '__standalone__';
    if (JamState.passes.length) {
      paintAll();
      syncPassesFromServer();
    } else if (loadSession(key) || loadSession('__standalone__')) {
      paintAll();
      syncPassesFromServer();
    } else {
      JamState.sessionKey = '__standalone__';
      applyStarter(STARTERS[0]);
    }
  }

  function openFromTake(take) {
    var modal = document.getElementById('jam-modal');
    if (!modal || !take) { return; }
    JamState.open = true;
    modal.classList.remove('hidden');
    var rootId = take.parent_id || take.id;
    var key = 'take:' + rootId;
    if (JamState.sessionKey === key && JamState.passes.length) {
      paintAll();
      syncPassesFromServer();
      return;
    }
    if (loadSession(key)) {
      paintAll();
      syncPassesFromServer();
      var ready = JamState.passes.find(function (p) { return p.id === take.id && p.hasAudio; }) ||
                  JamState.passes.find(function (p) { return p.hasAudio; });
      if (ready && !JamAudio.playing) { JamAudio.play(ready.id, 0.08).catch(function () {}); }
      return;
    }
    JamState.sessionKey = key;
    seedFromTake(take);
  }

  function close() {
    var modal = document.getElementById('jam-modal');
    JamState.open = false;
    saveSession();
    JamAudio.pause();
    if (modal) { modal.classList.add('hidden'); }
  }

  function isOpen() { return JamState.open; }

  window.Jam = { open: open, openFromTake: openFromTake, close: close, isOpen: isOpen, handleKey: handleKey };
})();
