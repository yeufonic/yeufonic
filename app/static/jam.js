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
  // 4x4 grid of moods across X (Dark->Bright) and Y (Calm->Energetic), with concrete
  // tonal, dynamic, arrangement, vocal, and avoid cues so Vibe shifts are audibly distinct.
  var VIBE_GRID = [
    // y=0 (Calm)
    [
      {
        word: 'Somber',
        cue: 'somber dark melancholic mood, minor key, slow sparse quiet arrangement, solemn brooding atmosphere, subdued soft dynamics',
        vocal: 'solemn hushed subdued',
        avoid: 'upbeat, bright, cheerful, energetic, loud, driving drums, euphoric',
        harmony: 0,
        interpretation: 'settled'
      },
      {
        word: 'Melancholic',
        cue: 'melancholic bittersweet mood, minor key, gentle sparse slow arrangement, wistful delicate soft dynamics',
        vocal: 'wistful soft emotional',
        avoid: 'upbeat, cheerful, aggressive, loud, energetic, driving drums',
        harmony: 1,
        interpretation: 'settled'
      },
      {
        word: 'Peaceful',
        cue: 'peaceful tranquil calm mood, warm major key, gentle unhurried airy arrangement, soft relaxed dynamics',
        vocal: 'calm gentle soft',
        avoid: 'aggressive, harsh, loud, dark, heavy, tense, fast drums',
        harmony: 1,
        interpretation: 'settled'
      },
      {
        word: 'Serene',
        cue: 'serene bright luminous calm mood, major key, airy delicate floating arrangement, crystalline spacious soft dynamics',
        vocal: 'airy gentle serene',
        avoid: 'dark, heavy, aggressive, loud, tense, distorted, gloomy',
        harmony: 1,
        interpretation: 'settled'
      }
    ],
    // y=1 (Calm-Mid)
    [
      {
        word: 'Sad',
        cue: 'sad dark aching mood, minor key, stripped-back intimate arrangement, heavy-hearted low-key dynamics',
        vocal: 'vulnerable sad intimate',
        avoid: 'cheerful, happy, upbeat, party, energetic, bright',
        harmony: 1,
        interpretation: 'settled'
      },
      {
        word: 'Mellow',
        cue: 'mellow laid-back cool mood, warm relaxed groove, smooth understated dynamics',
        vocal: 'relaxed smooth laid-back',
        avoid: 'aggressive, frantic, harsh, loud, chaotic',
        harmony: 1,
        interpretation: 'standard'
      },
      {
        word: 'Warm',
        cue: 'warm comforting heartfelt mood, rich major harmony, inviting organic arrangement, balanced smooth dynamics',
        vocal: 'warm expressive heartfelt',
        avoid: 'cold, harsh, aggressive, gloomy, chaotic',
        harmony: 1,
        interpretation: 'standard'
      },
      {
        word: 'Dreamy',
        cue: 'dreamy bright ethereal shimmering mood, lush major seventh harmony, floating hazy sparkling atmosphere',
        vocal: 'dreamy airy silky',
        avoid: 'aggressive, harsh, dry, heavy metal, angry, dark',
        harmony: 2,
        interpretation: 'standard'
      }
    ],
    // y=2 (Mid-Energetic)
    [
      {
        word: 'Moody',
        cue: 'moody dark brooding noir mood, minor key, shadowed pulsing groove, atmospheric tension',
        vocal: 'brooding moody dark',
        avoid: 'cheerful, bright, bubblegum, sunny, happy',
        harmony: 2,
        interpretation: 'restless'
      },
      {
        word: 'Tense',
        cue: 'tense suspenseful dramatic mood, dark minor tension, tight urgent pulsing rhythm, edgy restless dynamics',
        vocal: 'urgent tense edgy',
        avoid: 'peaceful, relaxed, cheerful, sunny, sleepy, mellow',
        harmony: 2,
        interpretation: 'restless'
      },
      {
        word: 'Groovy',
        cue: 'groovy upbeat infectious mood, lively tight rhythmic pocket, bouncy energetic feel, bright punchy mix',
        vocal: 'confident lively soulful',
        avoid: 'somber, slow, sluggish, gloomy, sparse, sleepy',
        harmony: 2,
        interpretation: 'standard'
      },
      {
        word: 'Uplifting',
        cue: 'uplifting bright hopeful mood, soaring major key, radiant energetic arrangement, crisp driving rhythm, joyful lift',
        vocal: 'bright uplifting soaring',
        avoid: 'somber, dark, sad, gloomy, depressing, slow, sparse',
        harmony: 2,
        interpretation: 'wide'
      }
    ],
    // y=3 (Energetic)
    [
      {
        word: 'Fierce',
        cue: 'fierce dark aggressive intense mood, minor key, heavy hard-hitting driving drums, gritty raw loud high-energy dynamics',
        vocal: 'fierce gritty powerful intense',
        avoid: 'calm, gentle, peaceful, cheerful, soft, sparse, mellow',
        harmony: 2,
        interpretation: 'restless'
      },
      {
        word: 'Driven',
        cue: 'driven urgent relentless high-energy mood, punchy propulsive beat, forceful intense momentum, loud dynamic push',
        vocal: 'commanding urgent powerful',
        avoid: 'calm, slow, sleepy, sparse, gentle, peaceful',
        harmony: 2,
        interpretation: 'restless'
      },
      {
        word: 'Vibrant',
        cue: 'vibrant bright exhilarating high-energy mood, major key, punchy kinetic danceable rhythm, vivid full-bodied dynamics',
        vocal: 'energetic bright lively',
        avoid: 'somber, dark, slow, gloomy, sparse, muted, quiet',
        harmony: 2,
        interpretation: 'wide'
      },
      {
        word: 'Euphoric',
        cue: 'euphoric ecstatic joyous anthemic mood, bright major key, soaring high-energy full lush arrangement, driving punchy drums, explosive radiant dynamics',
        vocal: 'soaring ecstatic joyful powerful',
        avoid: 'somber, dark, sad, slow, sparse, quiet, melancholic, subdued',
        harmony: 2,
        interpretation: 'wide'
      }
    ]
  ];

  var LEVEL_LABELS = { 1: t('Subtle'), 2: t('Normal'), 3: t('Prominent'), 4: t('Lead') };
  // The Vibe pad's words, as shown (the cues sent to the model stay in English).
  var VIBE_LABELS = {
    Somber: t('Somber'), Melancholic: t('Melancholic'), Peaceful: t('Peaceful'), Serene: t('Serene'),
    Sad: t('Sad'), Mellow: t('Mellow'), Warm: t('Warm'), Dreamy: t('Dreamy'),
    Moody: t('Moody'), Tense: t('Tense'), Groovy: t('Groovy'), Uplifting: t('Uplifting'),
    Fierce: t('Fierce'), Driven: t('Driven'), Vibrant: t('Vibrant'), Euphoric: t('Euphoric'),
    Dark: t('Dark'), Bright: t('Bright'), Balanced: t('Balanced'), Calm: t('Calm'), Energetic: t('Energetic'), 'Mid-energy': t('Mid-energy')
  };
  function vibeLabel(word) { return VIBE_LABELS[word] || word; }
  function vocalsLabel(v) {
    return v === 'instrumental' ? t('Instrumental') : (v === 'male' ? t('Male') : (v === 'female' ? t('Female') : t('My Voice')));
  }

  /* ------------------------------------------------- Unified Main-Player Audio Adapter */
  function seedTakeRecord() {
    var sid = seedId();
    if (!sid) { return null; }
    if (window.State && Array.isArray(State.takes)) {
      for (var i = 0; i < State.takes.length; i++) {
        if (State.takes[i].id === sid) { return State.takes[i]; }
      }
    }
    return (window.State && State.loadedTake && State.loadedTake.id === sid) ? State.loadedTake : null;
  }

  function passTakeObject(passId) {
    var p = passById(passId);
    var seedRec = seedTakeRecord();
    if (!p) { return seedRec && seedRec.id === passId ? seedRec : null; }
    if (isSeedPass(p) && seedRec) {
      return Object.assign({}, seedRec, { _jamLabel: passLabel(p) });
    }
    return {
      id: p.id,
      title: p.title || (JamState.starterName + ' \u00B7 ' + passLabel(p)),
      kind: (p.snapshot && p.snapshot.vocals === 'instrumental') ? 'instrumental' : ((seedRec && seedRec.kind) || 'song'),
      art: seedRec ? seedRec.art : null,
      duration: p.duration || 0,
      has_audio: true,
      normalised: Boolean(JamState.seedNormalise),
      space_id: isSeedPass(p) ? (JamState.spaceId || 'default') : '__jam__',
      _jamLabel: passLabel(p),
      _jamSeedId: seedId()
    };
  }

  function passAudioUrl(passId) {
    var take = passTakeObject(passId);
    return '/api/takes/' + encodeURIComponent(passId) + '/audio' + (take && take.normalised ? '?level=normalised' : '');
  }

  /* Synchronised instant-switch audio engine, modelled on Compare:
     every playable pass in Roll History is decoded into memory and started on the same
     AudioContext frame, each through its own gain node. Switching tracks only ramps
     gains over 8 ms, so changing between Seed and any pass lands on the exact same
     moment with no gap or drift. */
  var JamSync = {
    enabled: false,
    handoffFromAudio: false,
    ctx: null,
    master: null,
    items: {},
    activeId: null,
    playing: false,
    wantPlay: false,
    startedAt: 0,
    offset: 0,
    rate: 1,
    token: 0,
    raf: null,
    timer: null,

    isOwning: function () {
      return Boolean(this.enabled && !this.handoffFromAudio);
    },

    applyVolume: function () {
      if (!this.master || !this.ctx) { return; }
      var a = JamAudio.audio();
      var vol = (a && !a.muted) ? (typeof a.volume === 'number' ? a.volume : 1) : 0;
      this.master.gain.setValueAtTime(vol, this.ctx.currentTime);
    },

    rawPosition: function () {
      if (!this.playing || !this.ctx) { return this.offset; }
      return this.offset + Math.max(0, this.ctx.currentTime - this.startedAt) * this.rate;
    },

    activeDuration: function () {
      var active = this.activeId ? this.items[this.activeId] : null;
      if (active && active.buffer) { return active.buffer.duration; }
      var p = passById(this.activeId);
      return (p && p.duration) || 0;
    },

    position: function () {
      var pos = this.rawPosition();
      var dur = this.activeDuration();
      if (dur > 0 && pos > dur) { return dur; }
      return pos;
    },

    clock: function () {
      return {
        currentTime: this.position(),
        duration: this.activeDuration(),
        playing: this.playing
      };
    },

    loadProgress: function () {
      var list = playablePasses();
      var total = list.length;
      var done = 0;
      for (var i = 0; i < list.length; i++) {
        var item = this.items[list[i].id];
        if (item && (item.buffer || item.failed)) { done += 1; }
      }
      return { done: done, total: total };
    },

    applyGains: function (instant) {
      var ctx = this.ctx;
      if (!ctx) { return; }
      var now = ctx.currentTime;
      var ids = Object.keys(this.items);
      for (var i = 0; i < ids.length; i++) {
        var item = this.items[ids[i]];
        if (!item || !item.gain) { continue; }
        var param = item.gain.gain;
        var target = item.id === this.activeId ? 1 : 0;
        param.cancelScheduledValues(now);
        if (instant) {
          param.setValueAtTime(target, now);
        } else {
          param.setValueAtTime(param.value, now);
          param.linearRampToValueAtTime(target, now + 0.008);
        }
      }
    },

    stopSources: function () {
      var ids = Object.keys(this.items);
      for (var i = 0; i < ids.length; i++) {
        var item = this.items[ids[i]];
        if (item && item.source) {
          try { item.source.stop(); } catch (err) { /* not started */ }
          try { item.source.disconnect(); } catch (err) {}
          item.source = null;
        }
      }
    },

    attachRunningSource: function (item) {
      if (!this.playing || !this.ctx || !item || !item.buffer || item.source) { return; }
      var now = this.ctx.currentTime;
      if (now < this.startedAt) {
        if (this.offset < item.buffer.duration) {
          var s0 = this.ctx.createBufferSource();
          s0.buffer = item.buffer;
          s0.playbackRate.value = this.rate;
          s0.connect(item.gain);
          s0.start(this.startedAt, this.offset);
          item.source = s0;
        }
        return;
      }
      var when = now + 0.02;
      var at = this.offset + (when - this.startedAt) * this.rate;
      if (at >= item.buffer.duration) { return; }
      var source = this.ctx.createBufferSource();
      source.buffer = item.buffer;
      source.playbackRate.value = this.rate;
      source.connect(item.gain);
      source.start(when, at);
      item.source = source;
    },

    stopLoop: function () {
      if (this.raf !== null) { cancelAnimationFrame(this.raf); this.raf = null; }
      if (this.timer !== null) { clearInterval(this.timer); this.timer = null; }
    },

    tick: function (fromTimer) {
      if (!this.enabled || !this.playing) { this.stopLoop(); return; }
      if (typeof abLoopCheck === 'function') { abLoopCheck(); }
      var raw = this.rawPosition();
      var dur = this.activeDuration();
      if (dur > 0 && raw >= dur) {
        this.start(0);
        return;
      }
      if (!fromTimer && !document.body.classList.contains('visualizer-open')) {
        if (typeof syncWaveRatio === 'function') { syncWaveRatio(); }
        if (typeof drawWave === 'function') { drawWave(); }
        if (typeof updateTimes === 'function') { updateTimes(); }
      }
    },

    startLoop: function () {
      var self = this;
      this.stopLoop();
      var frame = function () {
        if (!self.enabled || !self.playing) { self.raf = null; return; }
        self.tick(false);
        if (self.enabled && self.playing) {
          self.raf = requestAnimationFrame(frame);
        } else {
          self.raf = null;
        }
      };
      this.raf = requestAnimationFrame(frame);
      this.timer = setInterval(function () { self.tick(true); }, 200);
    },

    syncUi: function (passId) {
      var take = passTakeObject(passId);
      if (!take) { return; }
      if (window.State) {
        State.loadedTake = take;
        State.loadedId = passId;
        State.playing = this.playing ? passId : null;
        State.audition = null;
      }
      if (typeof wave === 'object' && wave) { wave.kind = take.kind; }
      var version = take.normalised ? '?level=normalised' : '';
      var url = '/api/takes/' + encodeURIComponent(passId) + '/audio' + version;
      var peaksUrl = '/api/takes/' + encodeURIComponent(passId) + '/peaks' + version;
      if (typeof loadWave === 'function') {
        loadWave(url, peaksUrl, { keepLoop: true, keepRatio: true });
      }
      if (typeof npTitle === 'function') {
        npTitle(take.title, passId, take.space_id === '__jam__' ? t('Open in Jam') : '');
      }
      var metaEl = document.getElementById('np-meta');
      if (metaEl) {
        var dur = this.activeDuration() || take.duration || 0;
        metaEl.textContent = (take._jamLabel || '') + (dur ? (take._jamLabel ? ' \u00B7 ' : '') + (typeof secs === 'function' ? secs(dur) : fmtTime(dur)) : '');
      }
      if (typeof paintNpCover === 'function') { paintNpCover(take); }
      if (typeof updateMediaSession === 'function') { updateMediaSession(take); }
      if (window.Visualizer && typeof window.Visualizer.setTake === 'function') { window.Visualizer.setTake(take); }
      if (typeof updateTimes === 'function') { updateTimes(); }
      if (typeof paintTakes === 'function') { paintTakes(); }
      if (typeof paintTransport === 'function') {
        paintTransport();
      } else {
        paintHistory();
      }
    },

    ensurePass: function (passId) {
      if (!this.enabled || !this.ctx || !passId) { return null; }
      var existing = this.items[passId];
      if (existing) { return existing; }
      var gain = this.ctx.createGain();
      gain.gain.value = 0;
      gain.connect(this.master);
      var item = {
        id: passId,
        url: passAudioUrl(passId),
        buffer: null,
        gain: gain,
        source: null,
        loading: true,
        failed: false
      };
      this.items[passId] = item;
      var self = this;
      var token = this.token;
      var ctx = this.ctx;
      fetch(item.url).then(function (res) {
        if (!res.ok) { throw new Error(String(res.status)); }
        return res.arrayBuffer();
      }).then(function (data) {
        return ctx.decodeAudioData(data);
      }).then(function (buffer) {
        if (token !== self.token || !self.enabled || self.items[passId] !== item) { return; }
        item.buffer = buffer;
        item.loading = false;
        if (self.handoffFromAudio && passId === self.activeId) {
          var a = JamAudio.audio();
          var handoffPlaying = Boolean(a && (a.currentSrc || a.src) && !a.paused && !a.ended);
          var handoffAt = (a && isFinite(a.currentTime)) ? a.currentTime : self.offset;
          self.handoffFromAudio = false;
          if (handoffPlaying) {
            self.start(handoffAt);
          } else {
            self.offset = handoffAt;
            self.wantPlay = false;
            paintHistory();
          }
          return;
        }
        if (self.wantPlay && passId === self.activeId) {
          self.start(self.offset);
          return;
        }
        if (self.playing) {
          self.attachRunningSource(item);
          if (passId === self.activeId) {
            if (self.rawPosition() >= buffer.duration) {
              self.start(0);
            } else {
              self.applyGains(false);
              self.syncUi(passId);
            }
            return;
          }
        }
        paintHistory();
      }).catch(function () {
        if (token !== self.token || !self.enabled || self.items[passId] !== item) { return; }
        item.loading = false;
        item.failed = true;
        if (passId === self.activeId && (self.wantPlay || self.handoffFromAudio)) {
          self.wantPlay = false;
          self.handoffFromAudio = false;
        }
        paintHistory();
      });
      return item;
    },

    syncList: function () {
      if (!this.enabled) { return; }
      var list = playablePasses();
      var keep = {};
      for (var i = 0; i < list.length; i++) {
        keep[list[i].id] = true;
        this.ensurePass(list[i].id);
      }
      var ids = Object.keys(this.items);
      for (var j = 0; j < ids.length; j++) {
        if (!keep[ids[j]]) { this.removePass(ids[j]); }
      }
    },

    removePass: function (passId) {
      var item = this.items[passId];
      if (!item) { return; }
      if (this.activeId === passId) {
        if (this.playing) { this.pause(); }
        this.activeId = null;
      }
      if (item.source) {
        try { item.source.stop(); } catch (err) {}
        try { item.source.disconnect(); } catch (err) {}
        item.source = null;
      }
      if (item.gain) {
        try { item.gain.disconnect(); } catch (err) {}
      }
      delete this.items[passId];
    },

    start: function (at) {
      var ctx = this.ctx;
      if (!ctx || !this.enabled) { return; }
      var active = this.activeId ? this.items[this.activeId] : null;
      if (!active || !active.buffer) {
        this.offset = Math.max(0, at || 0);
        this.wantPlay = true;
        paintHistory();
        return;
      }
      var dur = active.buffer.duration;
      at = Math.max(0, at || 0);
      if (dur > 0 && at >= dur) { at = 0; }
      var mainAudio = JamAudio.audio();
      this.handoffFromAudio = false;
      if (mainAudio && !mainAudio.paused) { mainAudio.pause(); }
      this.stopSources();
      if (ctx.state === 'suspended') { ctx.resume().catch(function () {}); }
      this.rate = (mainAudio && mainAudio.playbackRate) || 1;
      this.applyVolume();
      this.applyGains(true);
      var when = ctx.currentTime + 0.04;
      var ids = Object.keys(this.items);
      for (var i = 0; i < ids.length; i++) {
        var item = this.items[ids[i]];
        if (!item || !item.buffer || at >= item.buffer.duration) { continue; }
        var source = ctx.createBufferSource();
        source.buffer = item.buffer;
        source.playbackRate.value = this.rate;
        source.connect(item.gain);
        source.start(when, at);
        item.source = source;
      }
      this.startedAt = when;
      this.offset = at;
      this.playing = true;
      this.wantPlay = false;
      this.startLoop();
      this.syncUi(this.activeId);
    },

    play: function (passId) {
      if (!this.enabled || !passId) { return; }
      var item = this.ensurePass(passId);
      if (!item || item.failed) { return; }
      if (this.handoffFromAudio) {
        var a = JamAudio.audio();
        var handoffAt = (a && isFinite(a.currentTime)) ? a.currentTime : this.offset;
        this.offset = handoffAt;
        this.activeId = passId;
        if (item.buffer) {
          this.handoffFromAudio = false;
          this.start(handoffAt);
        } else {
          this.wantPlay = true;
          paintHistory();
        }
        return;
      }
      if (this.playing) {
        var raw = this.rawPosition();
        this.activeId = passId;
        if (!item.buffer) {
          this.wantPlay = true;
          paintHistory();
          return;
        }
        if (raw >= item.buffer.duration) {
          // Current time is past this shorter pass's end: restart synced playback from the top.
          this.start(0);
          return;
        }
        if (!item.source) {
          this.attachRunningSource(item);
        }
        this.applyGains(false);
        this.syncUi(passId);
        return;
      }
      this.activeId = passId;
      this.start(this.offset);
    },

    pause: function () {
      if (!this.enabled) { return; }
      if (this.handoffFromAudio) {
        var a = JamAudio.audio();
        this.handoffFromAudio = false;
        this.wantPlay = false;
        if (a && isFinite(a.currentTime)) { this.offset = a.currentTime; }
        if (a && !a.paused) { a.pause(); }
        if (window.State && State.playing) { State.playing = null; }
        if (typeof paintTakes === 'function') { paintTakes(); }
        if (typeof paintTransport === 'function') { paintTransport(); } else { paintHistory(); }
        return;
      }
      if (!this.playing && !this.wantPlay) { return; }
      this.offset = this.position();
      this.playing = false;
      this.wantPlay = false;
      this.stopSources();
      this.stopLoop();
      if (window.State && State.playing) { State.playing = null; }
      if (typeof syncWaveRatio === 'function') { syncWaveRatio(); }
      if (typeof drawWave === 'function') { drawWave(); }
      if (typeof updateTimes === 'function') { updateTimes(); }
      if (typeof paintTakes === 'function') { paintTakes(); }
      if (typeof paintTransport === 'function') { paintTransport(); } else { paintHistory(); }
    },

    resume: function () {
      if (!this.enabled) { return; }
      if (this.playing) { return; }
      var targetId = this.activeId;
      if (!targetId || !passById(targetId)) {
        var base = buildOn();
        var fallback = (base && base.hasAudio) ? base : playablePasses()[0];
        targetId = fallback ? fallback.id : null;
      }
      if (!targetId) { return; }
      this.activeId = targetId;
      this.ensurePass(targetId);
      var dur = this.activeDuration();
      var at = (dur > 0 && this.offset >= dur) ? 0 : this.offset;
      this.start(at);
    },

    seek: function (at) {
      if (!this.enabled) { return; }
      var dur = this.activeDuration();
      at = Math.max(0, dur > 0 ? Math.min(dur, at) : at);
      if (this.playing) {
        this.start(at);
      } else {
        this.offset = at;
        if (typeof syncWaveRatio === 'function') { syncWaveRatio(); }
        if (typeof drawWave === 'function') { drawWave(); }
        if (typeof updateTimes === 'function') { updateTimes(); }
      }
    },

    nudge: function (seconds) {
      this.seek(this.position() + seconds);
    },

    setRate: function (newRate) {
      newRate = Number(newRate) || 1;
      if (!this.enabled || newRate === this.rate) { return; }
      if (this.playing && this.ctx) {
        var now = this.ctx.currentTime;
        if (now >= this.startedAt) {
          this.offset = this.offset + (now - this.startedAt) * this.rate;
          this.startedAt = now;
        }
        this.rate = newRate;
        var ids = Object.keys(this.items);
        for (var i = 0; i < ids.length; i++) {
          var item = this.items[ids[i]];
          if (item && item.source) {
            try { item.source.playbackRate.setValueAtTime(newRate, now); } catch (err) { item.source.playbackRate.value = newRate; }
          }
        }
      } else {
        this.rate = newRate;
      }
    },

    enable: function () {
      if (this.enabled) { return; }
      var list = playablePasses();
      if (list.length < 2) { return; }
      var Context = window.AudioContext || window.webkitAudioContext;
      if (!Context) { return; }
      var a = JamAudio.audio();
      var wasPlaying = Boolean(a && (a.currentSrc || a.src) && !a.paused && !a.ended);
      var curId = JamAudio.currentId;
      var curInJam = Boolean(curId && list.some(function (p) { return p.id === curId; }));
      this.enabled = true;
      this.token += 1;
      this.ctx = new Context();
      this.master = this.ctx.createGain();
      this.master.connect(this.ctx.destination);
      this.applyVolume();
      this.items = {};
      var base = buildOn();
      this.activeId = curInJam ? curId : ((base && base.hasAudio) ? base.id : list[0].id);
      this.offset = (curInJam && a && isFinite(a.currentTime)) ? a.currentTime : 0;
      this.rate = (a && a.playbackRate) || 1;
      this.playing = false;
      this.wantPlay = Boolean(wasPlaying && curInJam);
      this.handoffFromAudio = Boolean(wasPlaying && curInJam);
      JamState.sync = true;
      this.syncList();
      paintHistory();
    },

    disable: function (opts) {
      var handoff = !opts || opts.handoff !== false;
      if (!this.enabled) { return; }
      var wasPlaying = this.playing;
      var wasHandoff = this.handoffFromAudio;
      var at = this.position();
      var activeId = this.activeId;
      this.enabled = false;
      this.handoffFromAudio = false;
      this.playing = false;
      this.wantPlay = false;
      this.token += 1;
      this.stopLoop();
      this.stopSources();
      var ctx = this.ctx;
      this.ctx = null;
      this.master = null;
      this.items = {};
      if (ctx) { ctx.close().catch(function () {}); }
      JamState.sync = false;

      if (handoff && !wasHandoff && activeId) {
        var a = JamAudio.audio();
        var take = passTakeObject(activeId);
        if (a && take && typeof playTake === 'function') {
          var targetUrl = passAudioUrl(activeId);
          var sameSrc = Boolean((a.currentSrc || a.src) && (a.currentSrc || a.src).indexOf(targetUrl) !== -1);
          var applySeek = function () {
            if (isFinite(a.duration) && at > 0 && at < a.duration) {
              try { a.currentTime = at; } catch (err) {}
            }
          };
          if (wasPlaying) {
            if (!sameSrc && window.State) { State.loadedId = null; }
            playTake(activeId, take);
            if (sameSrc && a.readyState >= 1) {
              applySeek();
            } else {
              a.addEventListener('loadedmetadata', function () {
                applySeek();
                if (typeof updateTimes === 'function') { updateTimes(); }
              }, { once: true });
            }
          } else if (!sameSrc) {
            a.src = targetUrl;
            if (window.State) { State.loadedId = activeId; State.loadedTake = take; State.playing = null; }
            a.addEventListener('loadedmetadata', function () {
              applySeek();
              if (typeof updateTimes === 'function') { updateTimes(); }
            }, { once: true });
          } else {
            applySeek();
          }
        }
      }
      if (JamState.open) { paintHistory(); }
      if (typeof paintTransport === 'function') { paintTransport(); }
    },

    toggle: function () {
      if (this.enabled) {
        this.disable({ handoff: true });
      } else {
        this.enable();
      }
      // Remembered: Sync is on unless the person turned it off, and comes on by itself once there is a pass to
      // switch to (it needs two tracks).
      try { localStorage.setItem(SYNC_KEY, this.enabled ? '1' : '0'); } catch (err) { /* private mode */ }
    },

    /* On, if the person has not turned it off and there are two tracks to switch between: when Jam opens, and when a
       new pass is ready.  Off is the person's choice and stays off. */
    autoEnable: function () {
      if (this.enabled || !JamState.open || !syncWanted() || playablePasses().length < 2) { return; }
      var self = this;
      setTimeout(function () {
        if (!self.enabled && JamState.open && syncWanted() && playablePasses().length >= 2) { self.enable(); }
      }, 0);
    }
  };

  var SYNC_KEY = 'yue2.jam.sync';
  function syncWanted() {
    try { return localStorage.getItem(SYNC_KEY) !== '0'; } catch (err) { return true; }
  }

  var JamAudio = {
    audio: function () {
      return document.getElementById('audio');
    },

    get currentId() {
      if (JamSync.isOwning()) { return JamSync.activeId; }
      return (window.State && (State.playing || State.loadedId)) || null;
    },

    get playing() {
      if (JamSync.isOwning()) { return JamSync.playing; }
      var a = this.audio();
      return Boolean(a && (a.currentSrc || a.src) && !a.paused && !a.ended);
    },

    play: function (takeId) {
      if (!takeId) { return Promise.resolve(); }
      if (JamSync.enabled) {
        JamSync.play(takeId);
        return Promise.resolve();
      }
      if (typeof playTake !== 'function') { return Promise.resolve(); }
      playTake(takeId, passTakeObject(takeId));
      paintHistory();
      return Promise.resolve();
    },

    // Space acts immediately on whatever is sounding (pausing it), or plays/resumes the chosen base pass.
    toggle: function () {
      if (this.playing) { this.pause(); return; }
      if (JamSync.enabled) { JamSync.resume(); return; }
      var a = this.audio();
      var base = buildOn();
      var target = (base && base.hasAudio) ? base : JamState.passes.find(function (p) { return p.hasAudio; });
      if (target && target.id === this.currentId && a && (a.currentSrc || a.src)) {
        this.resume();
        return;
      }
      if (target) {
        this.play(target.id);
        return;
      }
      if (a && (a.currentSrc || a.src)) { this.resume(); }
    },

    pause: function () {
      if (JamSync.enabled) { JamSync.pause(); return; }
      var a = this.audio();
      if (!a || a.paused) { return; }
      a.pause();
      if (window.State && State.playing) { State.playing = null; }
      if (typeof paintTakes === 'function') { paintTakes(); }
      if (typeof paintTransport === 'function') { paintTransport(); }
      paintHistory();
    },

    resume: function () {
      if (JamSync.enabled) { JamSync.resume(); return; }
      var a = this.audio();
      if (a && (a.currentSrc || a.src)) {
        if (window.Rack && typeof window.Rack.resume === 'function') { window.Rack.resume(); }
        if (a.ended) { a.currentTime = 0; }
        if (window.State && State.loadedId) { State.playing = State.loadedId; }
        a.play().catch(function () {});
        if (typeof paintTakes === 'function') { paintTakes(); }
        if (typeof paintTransport === 'function') { paintTransport(); }
        paintHistory();
        return;
      }
      var base = buildOn();
      var target = (base && base.hasAudio) ? base : JamState.passes.find(function (p) { return p.hasAudio; });
      if (target) { this.play(target.id); }
    },

    stopIfPlaying: function (id) {
      if (!id) { return; }
      if (JamSync.enabled) { JamSync.removePass(id); }
      if (!window.State) { return; }
      if (State.loadedId !== id && State.playing !== id) { return; }
      var a = this.audio();
      if (a && !a.paused) { a.pause(); }
      if (State.playing === id) { State.playing = null; }
      if (typeof paintTakes === 'function') { paintTakes(); }
      if (typeof paintTransport === 'function') { paintTransport(); }
      paintHistory();
    }
  };

  /* ------------------------------------------------- Jam Session State */
  var JAM_STORAGE_KEY = 'yue2.jam.sessions';

  var JamState = {
    open: false,
    sessionKey: null,   // 'take:' + the Seed's id: a Jam is always of a take
    starterName: '',    // the Seed's title, which passes are named after
    parentId: null,
    spaceId: null,
    fastLoop: true,
    parts: [],          // [{ name, cat, level }]
    vibe: { x: 0.34, y: 0.36 },
    bpm: 84,
    vocals: 'instrumental', // 'instrumental' | 'female' | 'male' | 'voice'
    voiceId: '',
    tones: [],
    lyrics: '',         // working lyrics for the next roll (starts from the Seed, saved per pass)
    seedLyrics: '',     // the Seed's own original lyrics (for Reset to Seed and edited state)
    seedStructure: '',  // an instrumental Seed's sections, planned again by Plan & Roll
    styleLora: '',
    styleLoraModel: 0.7,
    styleLoraClip: 0.7,
    // Sculpting (the Feel card): each empty means "as the Vibe pad, or the take, has it".
    key: '',            // a key to move the score to
    startSection: '',   // the section of the score a short pass starts at
    performance: '',    // an interpretation, in place of the Vibe pad's
    grip: '',           // how firmly the style is followed (CFG), in place of the Vibe pad's
    polish: 'polished', // polished (32 steps, default) or draft (24)
    chords: '',         // Plan & Roll's harmony, in place of the Vibe pad's
    voiceMix: {},       // a recorded voice's per-Jam settings overrides (all 10 voiceControls fields)
    voiceSettingsOpen: false,
    feelOpen: false,
    holdSeed: true,     // roll with the base's seed by default, so a pass differs only by what was changed
    paletteTab: 'inst',
    searchQuery: '',
    passes: [],         // [{ num, id, title, status, progress, stage, hasAudio, hasScore, duration, snapshot, diffs, error }; the Seed and scratch passes]
    lastPassNum: 0,
    lastRolledSnapshot: null,
    baseId: null,       // the pass the next roll builds on: its score and, once chosen, its settings
    sync: false,        // synchronised instant-switch playback across Roll History
    cookingId: null,
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
        parts: JamState.parts,
        vibe: JamState.vibe,
        bpm: JamState.bpm,
        vocals: JamState.vocals,
        voiceId: JamState.voiceId,
        tones: JamState.tones,
        lyrics: JamState.lyrics,
        seedLyrics: JamState.seedLyrics,
        seedStructure: JamState.seedStructure,
        styleLora: JamState.styleLora,
        styleLoraModel: JamState.styleLoraModel,
        styleLoraClip: JamState.styleLoraClip,
        key: JamState.key, startSection: JamState.startSection, performance: JamState.performance, grip: JamState.grip,
        polish: JamState.polish, chords: JamState.chords, voiceMix: JamState.voiceMix, holdSeed: JamState.holdSeed,
        passes: JamState.passes.slice(0, 40),
        lastPassNum: JamState.lastPassNum || 0,
        lastRolledSnapshot: JamState.lastRolledSnapshot,
        baseId: JamState.baseId,
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
    JamState.starterName = s.starterName || '';
    JamState.parentId = s.parentId || null;
    JamState.spaceId = s.spaceId || null;
    JamState.fastLoop = s.fastLoop !== false;
    JamState.parts = s.parts.slice();
    JamState.vibe = s.vibe || { x: 0.34, y: 0.36 };
    JamState.bpm = s.bpm || 96;
    JamState.vocals = s.vocals || 'instrumental';
    JamState.voiceId = s.voiceId || '';
    JamState.tones = Array.isArray(s.tones) ? s.tones.slice() : [];
    JamState.lyrics = s.lyrics || '';
    JamState.seedLyrics = typeof s.seedLyrics === 'string' ? s.seedLyrics : (s.lyrics || '');
    JamState.seedStructure = s.seedStructure || '';
    JamState.styleLora = s.styleLora || '';
    JamState.styleLoraModel = s.styleLoraModel != null ? Number(s.styleLoraModel) : 0.7;
    JamState.styleLoraClip = s.styleLoraClip != null ? Number(s.styleLoraClip) : 0.7;
    loadSculpt(s);
    JamState.holdSeed = s.holdSeed !== false;
    JamState.passes = Array.isArray(s.passes) ? s.passes.slice() : [];
    var maxLoaded = JamState.passes.reduce(function (m, p) {
      return (p && p.isSeed) ? m : Math.max(m, Number(p && p.num) || 0);
    }, 0);
    JamState.lastPassNum = Math.max(Number(s.lastPassNum) || 0, maxLoaded);
    JamState.lastRolledSnapshot = s.lastRolledSnapshot || null;
    JamState.baseId = s.baseId || null;
    JamState.cookingId = s.cookingId || null;
    return true;
  }

  async function syncPassesFromServer() {
    if (!JamState.passes.length) { return; }
    var wasCooking = JamState.cookingId;
    var prevSeedLyrics = JamState.seedLyrics;
    var kept = [];
    var activeCook = null;
    for (var i = 0; i < JamState.passes.length; i++) {
      var p = JamState.passes[i];
      try {
        var rec = await api('/api/takes/' + encodeURIComponent(p.id));
        if (rec.space_id === 'trash') { continue; }
        // Roll History is the Seed and the scratch passes: a pass that is a take in a space (a Full Song once it
        // has finished, or one moved there) is in the library.  The Full Song being made stays, for its progress.
        if (!isSeedPass(p) && rec.space_id !== '__jam__' && !(p.id === wasCooking && (rec.status === 'queued' || rec.status === 'running'))) { continue; }
        if (isSeedPass(p)) {
          var seedWords = rec.kind === 'instrumental' ? '' : (rec.lyrics || '');
          if (rec.title) { JamState.starterName = rec.title; }
          if (rec.space_id && rec.space_id !== 'trash' && rec.space_id !== '__jam__') { JamState.spaceId = rec.space_id; }
          JamState.seedLyrics = seedWords;
          JamState.seedStructure = rec.kind === 'instrumental' ? (rec.lyrics || '') : '';
          JamState.seedNormalise = Boolean(rec.normalise);
          JamState.seedRealaudio = rec.realaudio == null ? true : Boolean(rec.realaudio);
          if (p.snapshot) { p.snapshot.lyrics = seedWords; }
        } else if (p.snapshot && typeof p.snapshot.lyrics !== 'string') {
          p.snapshot.lyrics = rec.kind === 'instrumental' ? '' : (rec.lyrics || '');
        }
        p.status = rec.status;
        p.stage = rec.stage || rec.status;
        p.hasAudio = Boolean(rec.has_audio);
        p.hasScore = Boolean(rec.abc && rec.abc.trim());
        p.seed = rec.seed;
        p.samplerSteps = rec.sampler_steps;
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
    if (!JamState.passes.some(function (p) { return !isSeedPass(p); })) {
      JamState.lastPassNum = 0;
    }
    if (!passById(JamState.baseId)) { JamState.baseId = seedId(); }
    // Drop a deleted recorded voice ID left behind by an older saved session.
    if (JamState.voiceId && window.VOICES && Array.isArray(VOICES.list) &&
        !readyVoicesList().some(function (v) { return v.id === JamState.voiceId; })) {
      var seedRec = seedTakeRecord();
      var seedVoice = seedRec && seedRec.voice_id && readyVoicesList().some(function (v) { return v.id === seedRec.voice_id; })
        ? seedRec.voice_id : '';
      JamState.voiceId = seedVoice;
      if (!seedVoice && JamState.vocals === 'voice') { JamState.vocals = 'female'; }
    }
    var base = buildOn();
    if (base && isSeedPass(base) && (JamState.lyrics || '') === (prevSeedLyrics || '')) {
      JamState.lyrics = JamState.seedLyrics || '';
    }
    if (!(JamState.lyrics || '').trim() && JamState.vocals !== 'instrumental') {
      JamState.vocals = 'instrumental';
    }
    JamState.cookingId = activeCook;
    if (!JamState.passes.length) {
      JamState.parentId = null;
      JamState.lastRolledSnapshot = null;
    }
    saveSession();
    if (JamSync.enabled) {
      if (playablePasses().length < 2) { JamSync.disable({ handoff: true }); }
      else { JamSync.syncList(); }
    }
    paintAll();
    if (activeCook) { startPolling(); }
  }

  function cloneSnapshot() {
    return {
      fastLoop: JamState.fastLoop,
      lockScore: scoreLocked(),
      parts: JamState.parts.map(function (p) { return { name: p.name, cat: p.cat, level: p.level }; }),
      vibe: { x: Math.round(JamState.vibe.x * 100) / 100, y: Math.round(JamState.vibe.y * 100) / 100 },
      bpm: JamState.bpm,
      vocals: JamState.vocals,
      voiceId: JamState.voiceId,
      tones: JamState.tones.slice(),
      lyrics: JamState.lyrics,
      styleLora: JamState.styleLora,
      styleLoraModel: JamState.styleLoraModel,
      styleLoraClip: JamState.styleLoraClip,
      key: JamState.key, startSection: JamState.startSection, performance: JamState.performance, grip: JamState.grip,
      polish: JamState.polish, chords: JamState.chords, voiceMix: JSON.parse(JSON.stringify(JamState.voiceMix || {}))
    };
  }

  /* The Feel card's settings from a snapshot or a saved session; any missing are the defaults. */
  function loadSculpt(s) {
    s = s || {};
    JamState.key = s.key || '';
    JamState.startSection = s.startSection || '';
    JamState.performance = s.performance || '';
    JamState.grip = s.grip || '';
    JamState.polish = s.polish === 'draft' ? 'draft' : 'polished';
    JamState.chords = s.chords === undefined || s.chords === null ? '' : String(s.chords);
    JamState.voiceMix = s.voiceMix && typeof s.voiceMix === 'object' ? JSON.parse(JSON.stringify(s.voiceMix)) : {};
  }

  function vibeInfo(v) {
    var xi = Math.max(0, Math.min(3, Math.floor(v.x * 3.999)));
    var yi = Math.max(0, Math.min(3, Math.floor(v.y * 3.999)));
    var cell = VIBE_GRID[yi][xi];
    var xWord = v.x < 0.38 ? 'Dark' : (v.x > 0.62 ? 'Bright' : 'Balanced');
    var yWord = v.y < 0.38 ? 'Calm' : (v.y > 0.62 ? 'Energetic' : 'Mid-energy');
    var dist = Math.hypot(v.x - 0.5, v.y - 0.5);
    // Boost CFG style adherence smoothly as the puck moves away from center so mood shifts
    // genuinely reshape timbre, dynamics and delivery even when the score is locked.
    var cfgScale = dist < 0.22
      ? null
      : Math.round((1.2 + Math.min(1, (dist - 0.22) / 0.44) * 0.45) * 100) / 100;
    return {
      word: cell.word,
      cue: cell.cue,
      vocal: cell.vocal,
      avoid: dist >= 0.18 ? cell.avoid : null,
      xWord: xWord,
      yWord: yWord,
      dist: dist,
      cfgScale: cfgScale,
      harmony: cell.harmony,
      interpretation: cell.interpretation
    };
  }

  function compileStyle(snap) {
    var s = snap || JamState;
    var vi = vibeInfo(s.vibe);
    var tokens = [];
    // A LoRA does little without its trigger word, which has to be the style's first tag.
    var lora = s.styleLora ? jamLora(s.styleLora) : null;
    if (lora && lora.trigger) { tokens.push(lora.trigger); }
    // Lead with concrete musical, tonal & dynamic descriptors so YuE2 weights Vibe strongly.
    if (vi.cue) { tokens.push(vi.cue); }
    // Higher-level parts go next so YuE2 weights them strongly alongside the mood.
    var sorted = s.parts.slice().sort(function (a, b) { return b.level - a.level; });
    var trigger = lora && lora.trigger ? lora.trigger.toLowerCase() : '';
    sorted.forEach(function (p) {
      if (trigger && p.name.toLowerCase() === trigger) { return; }   // a session from before the trigger led
      if (p.level >= 4) { tokens.push('lead ' + p.name.toLowerCase() + ' focus'); }
      else if (p.level === 3) { tokens.push('prominent ' + p.name.toLowerCase()); }
      else if (p.level === 1) { tokens.push('subtle ' + p.name.toLowerCase()); }
      else { tokens.push(p.name.toLowerCase()); }
    });

    if (s.vocals === 'instrumental') {
      tokens.push('instrumental');
    } else {
      var vLabel = s.vocals === 'male' ? 'male vocal' : (s.vocals === 'female' ? 'female vocal' : 'lead vocal');
      var toneBits = s.tones.map(function (t) { return t.toLowerCase(); });
      if (vi.vocal && vi.dist >= 0.22) { toneBits.unshift(vi.vocal); }
      var tonePrefix = toneBits.length ? toneBits.join(', ') + ' ' : '';
      tokens.push(tonePrefix + vLabel);
    }
    if (s.bpm) { tokens.push(s.bpm + ' BPM'); }
    // Deduplicate comma-separated tags (e.g. a Seed rendered from an earlier Jam already carries Vibe cues).
    var seen = {};
    var out = [];
    tokens.join(', ').split(',').forEach(function (part) {
      var trimmed = part.trim();
      if (!trimmed) { return; }
      var key = trimmed.toLowerCase();
      if (seen[key]) { return; }
      seen[key] = true;
      out.push(trimmed);
    });
    return out.join(', ');
  }

  function computeDiffs(prev, next) {
    if (!prev) {
      var seed = next.parts.slice(0, 3).map(function (p) { return { text: p.name, cls: '' }; });
      seed.push({ text: next.vocals === 'instrumental' ? t('Instrumental') : (next.vocals === 'male' ? t('Male vocal') : t('Female vocal')), cls: '' });
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
        diffs.push({ text: p.level >= 4 ? t('+ {name} (Lead)', { name: p.name }) : '+ ' + p.name, cls: 'add' });
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
    if (oldVibe !== newVibe) { diffs.push({ text: t('Vibe \u2192 {word}', { word: vibeLabel(newVibe) }), cls: 'chg' }); }
    if (Math.abs((prev.bpm || 0) - (next.bpm || 0)) >= 3) { diffs.push({ text: next.bpm + ' BPM', cls: 'chg' }); }
    if (prev.vocals !== next.vocals) {
      diffs.push({ text: t('Vocals \u2192 {value}', { value: vocalsLabel(next.vocals) }), cls: 'chg' });
    }
    if ((prev.lyrics || '').trim() !== (next.lyrics || '').trim()) {
      diffs.push({ text: (next.lyrics || '').trim() ? t('Lyrics edited') : t('Lyrics cleared'), cls: 'chg' });
    }
    if ((prev.key || '') !== (next.key || '')) { diffs.push({ text: t('Key \u2192 {value}', { value: next.key || t('as the score') }), cls: 'chg' }); }
    if ((prev.startSection || '') !== (next.startSection || '')) {
      diffs.push({ text: next.startSection ? t('From the {section}', { section: sectionLabel(next.startSection) }) : t('From the top'), cls: 'chg' });
    }
    if ((prev.performance || '') !== (next.performance || '')) { diffs.push({ text: t('Performance \u2192 {value}', { value: performanceLabel(next.performance) }), cls: 'chg' }); }
    if ((prev.grip || '') !== (next.grip || '')) { diffs.push({ text: t('Style grip \u2192 {value}', { value: gripLabel(next.grip) }), cls: 'chg' }); }
    if ((prev.polish || 'polished') !== (next.polish || 'polished')) { diffs.push({ text: next.polish === 'draft' ? t('Draft') : t('Polished'), cls: 'chg' }); }
    if (JSON.stringify(prev.voiceMix || {}) !== JSON.stringify(next.voiceMix || {})) { diffs.push({ text: t('Voice settings'), cls: 'chg' }); }
    if ((prev.styleLora || '') !== (next.styleLora || '')) {
      diffs.push({ text: next.styleLora ? t('+ LoRA') : t('\u2212 LoRA'), cls: next.styleLora ? 'add' : 'rem' });
    }
    if (!diffs.length) { diffs.push({ text: t('Fresh roll'), cls: 'chg', fresh: true }); }
    return diffs.slice(0, 6);
  }

  function pendingChangeCount() {
    if (!JamState.lastRolledSnapshot) { return 0; }
    var d = computeDiffs(JamState.lastRolledSnapshot, cloneSnapshot());
    if (d.length === 1 && d[0].fresh) { return 0; }
    return d.length;
  }

  function isPartPending(name) {
    if (!JamState.lastRolledSnapshot) { return false; }
    var key = name.toLowerCase();
    var old = JamState.lastRolledSnapshot.parts.find(function (p) { return p.name.toLowerCase() === key; });
    var cur = JamState.parts.find(function (p) { return p.name.toLowerCase() === key; });
    return !old || (cur && old.level !== cur.level);
  }

  /* The chosen LoRA as the app knows it: its trigger word, and the songs it learned (`styles`). */
  function jamLora(name) {
    if (!name || typeof loraCatalogue !== 'function') { return null; }
    try {
      return loraCatalogue().filter(function (l) { return l.name === name; })[0] || null;
    } catch (err) { return null; }
  }

  function knownTriggers() {
    try {
      return typeof loraCatalogue === 'function'
        ? loraCatalogue().map(function (l) { return (l.trigger || '').toLowerCase(); }).filter(Boolean) : [];
    } catch (err) { return []; }
  }

  /* A style's tags as Parts.  The tempo, the key and a LoRA's trigger word are not Parts: the slider, the score
     and the LoRA slot say those.  `skipVocals`: a learned song's singer is not this Jam's. */
  function partsFromStyle(text, skipVocals, limit) {
    var triggers = knownTriggers();
    var parts = [];
    String(text || '').split(',').map(function (t) { return t.trim(); }).filter(Boolean).forEach(function (tag) {
      var low = tag.toLowerCase();
      if (/^\d+\s*bpm$/.test(low) || low === 'instrumental' || /^key of /.test(low) || triggers.indexOf(low) >= 0) { return; }
      if (skipVocals && /\bvocals?\b/.test(low)) { return; }
      if (parts.length >= (limit || 7) || parts.some(function (p) { return p.name.toLowerCase() === low; })) { return; }
      var cat = 'genre';
      if (PALETTE.inst.some(function (i) { return low.indexOf(i.toLowerCase()) >= 0; })) { cat = 'inst'; }
      else if (PALETTE.rhythm.some(function (i) { return low.indexOf(i.toLowerCase()) >= 0; })) { cat = 'rhythm'; }
      else if (PALETTE.prod.some(function (i) { return low.indexOf(i.toLowerCase()) >= 0; })) { cat = 'prod'; }
      parts.push({ name: tag.charAt(0).toUpperCase() + tag.slice(1), cat: cat, level: 2 });
    });
    return parts;
  }

  /* A learned song's pill, as on the editor's learned styles: its sound as the Parts.  The tempo stays the Seed's: a pass
     is the same song with another sound. */
  function applyLoraSong(index) {
    var lora = jamLora(JamState.styleLora);
    var song = lora && lora.styles ? lora.styles[index] : null;
    if (!song) { return; }
    var parts = partsFromStyle(song.prompt, true, MAX_PARTS);
    if (parts.length) { JamState.parts = parts; }
    JamState.loraSong = lora.name + '#' + index;
    JamState.styleName = null;
    paintAll();
  }

  /* The tempo a Jam starts at: the take's tempo lock, else its score's tempo line (in quarter notes, whatever the
     line's beat), else "NN BPM" in its style, else 100.  The slider's range is the editor's tempo box's. */
  var BPM_MIN = 40, BPM_MAX = 240;
  function seedTempo(take) {
    var bpm = Number(take.target_bpm) || 0;
    if (!bpm) {
      var q = /^Q:\s*(?:(\d+)\/(\d+)\s*=\s*)?(\d+(?:\.\d+)?)/m.exec(String(take.abc || ''));
      if (q) { bpm = Number(q[3]) * (q[1] ? 4 * Number(q[1]) / Number(q[2]) : 1); }
    }
    if (!bpm) {
      var named = /(\d{2,3})\s*bpm\b/i.exec(take.style || '');
      if (named) { bpm = Number(named[1]); }
    }
    bpm = Math.round(bpm) || 100;
    return Math.min(BPM_MAX, Math.max(BPM_MIN, bpm));
  }

  function seedFromTake(take) {
    JamState.starterName = take.title || t('Selected take');
    JamState.parentId = take.parent_id || take.id;
    JamState.spaceId = (take.space_id && take.space_id !== 'trash') ? take.space_id : null;
    var parts = partsFromStyle(take.style || '', false);
    if (!parts.length) {
      parts = [{ name: 'Indie pop', cat: 'genre', level: 2 }];
    }
    JamState.parts = parts;
    JamState.vibe = { x: 0.5, y: 0.5 };
    JamState.bpm = seedTempo(take);
    JamState.vocals = take.kind === 'instrumental' ? 'instrumental' : (take.voice_id ? 'voice' : (/male vocal/i.test(take.style || '') && !/female/i.test(take.style || '') ? 'male' : 'female'));
    JamState.voiceId = take.voice_id || '';
    JamState.tones = [];
    var seedWords = take.kind === 'instrumental' ? '' : (take.lyrics || '');
    JamState.lyrics = seedWords;
    JamState.seedLyrics = seedWords;
    JamState.seedStructure = take.kind === 'instrumental' ? (take.lyrics || '') : '';   // an instrumental's sections, for Plan & Roll
    var seedMix = {};
    if (take.voice_id && take.voice_mix) {
      if (typeof take.voice_mix === 'string') {
        try { seedMix = JSON.parse(take.voice_mix) || {}; } catch (err) { seedMix = {}; }
      } else if (typeof take.voice_mix === 'object') {
        seedMix = JSON.parse(JSON.stringify(take.voice_mix));
      }
    }
    loadSculpt({ voiceMix: seedMix });   // the Feel card starts as the take is: nothing moved
    JamState.voiceSettingsOpen = false;
    JamState.feelOpen = false;
    JamState.holdSeed = true;
    JamState.seedNormalise = Boolean(take.normalise);
    JamState.seedRealaudio = take.realaudio == null ? true : Boolean(take.realaudio);
    JamState.styleLora = take.style_lora || '';
    JamState.styleLoraModel = take.style_lora_model != null ? Number(take.style_lora_model) : 0.7;
    JamState.styleLoraClip = take.style_lora_clip != null ? Number(take.style_lora_clip) : 0.7;
    var snap = cloneSnapshot();
    JamState.lastRolledSnapshot = snap;
    JamState.passes = [{
      num: 0,
      isSeed: true,
      id: take.id,
      title: take.title || t('Selected take'),
      status: take.has_audio ? 'done' : take.status,
      progress: 100,
      stage: '',
      hasAudio: Boolean(take.has_audio),
      hasScore: Boolean(take.abc && take.abc.trim()),
      seed: take.seed,
      samplerSteps: take.sampler_steps,
      duration: take.duration || 0,
      snapshot: snap,
      diffs: computeDiffs(null, snap),
      error: null
    }];
    if (JamSync.enabled) { JamSync.disable({ handoff: false }); }
    JamState.lastPassNum = 0;
    JamState.cookingId = null;
    JamState.baseId = take.id;
    saveSession();
    paintAll();
    var audio = JamAudio.audio();
    if (take.has_audio && !JamAudio.playing && !(audio && (audio.currentSrc || audio.src)) && typeof activateTakeRecording === 'function') {
      activateTakeRecording(take);
    }
    if (typeof paintTransport === 'function') { paintTransport(); }
  }

  /* ------------------------------------------------- Rolling */
  function isSeedPass(p) {
    return Boolean(p && (p.isSeed || (JamState.sessionKey && JamState.sessionKey === 'take:' + p.id)));
  }

  /* A finished take in one of the person's spaces (a Full Song, or a pass kept from Jam).  Roll History
     shows the Seed and the scratch passes only: anything that has become a take is in the library. */
  function isLibraryTake(rec) {
    return Boolean(rec && rec.space_id && rec.space_id !== '__jam__' && rec.space_id !== 'trash' &&
      rec.status === 'done' && rec.has_audio);
  }

  function dropPass(passId) {
    JamAudio.stopIfPlaying(passId);
    JamState.passes = JamState.passes.filter(function (p) { return p.id !== passId; });
    if (!JamState.passes.some(function (p) { return !isSeedPass(p); })) { JamState.lastPassNum = 0; }
    if (JamState.baseId === passId) { JamState.baseId = seedId(); }
  }

  /* A Jam makes flavours of its Seed, so every roll keeps the Seed's melody and chords (its score).
     Only a Seed with no score yet has its first roll planned. */
  function scoreLocked() {
    return Boolean(readyBaseTakeWithScore());
  }

  /* New Jam: back to the Seed's own sound, with Roll History emptied.  The scratch passes are
     deleted, as nothing else can reach them. */
  async function newJamFromSeed() {
    var seed = JamState.passes.find(isSeedPass);
    if (!seed || JamState.cookingId) { return; }
    var scratch = JamState.passes.filter(function (p) { return !isSeedPass(p); });
    if (scratch.length && typeof confirmModal === 'function') {
      var yes = await confirmModal({
        title: t('Start a new Jam?'),
        message: tn(scratch.length, 'Back to the sound of {title}. The {n} pass in Roll History will be deleted.',
          'Back to the sound of {title}. The {n} passes in Roll History will be deleted.', { title: seed.title || t('the Seed') }),
        confirmText: t('New Jam'), danger: true
      });
      if (!yes) { return; }
    }
    var take;
    try {
      take = await api('/api/takes/' + encodeURIComponent(seed.id));
    } catch (err) {
      if (typeof toast === 'function') { toast(t('Could not reload the Seed: {message}', { message: err.message }), 'bad'); }
      return;
    }
    for (var i = 0; i < scratch.length; i++) {
      JamAudio.stopIfPlaying(scratch[i].id);
      try {
        var rec = await api('/api/takes/' + encodeURIComponent(scratch[i].id));
        if (rec.space_id === '__jam__') {
          await api('/api/takes/' + encodeURIComponent(scratch[i].id), { method: 'DELETE' });
        }
      } catch (err) { /* already gone */ }
    }
    seedFromTake(take);
  }

  /* The base: the pass the next roll builds on, chosen by clicking its card (the Seed until then).  A pass that
     is gone, or not yet made, gives way to the Seed. */
  function passById(id) { return id ? (JamState.passes.find(function (p) { return p.id === id; }) || null) : null; }
  function seedId() { var seed = JamState.passes.find(isSeedPass); return seed ? seed.id : null; }
  function buildOn() {
    var p = passById(JamState.baseId);
    if (p && (isSeedPass(p) || (p.hasAudio && p.id !== JamState.cookingId))) { return p; }
    return JamState.passes.find(isSeedPass) || null;
  }
  function passLabel(p) { return !p ? t('the Seed') : (isSeedPass(p) ? t('Seed') : t('Pass #{n}', { n: p.num })); }
  // A pass (or Seed) made instrumental has no sung vocal melody on the Vocal voice.
  function passUnsung(p) { return Boolean(p && p.snapshot && p.snapshot.vocals === 'instrumental'); }

  /* The score a roll is made from: the base's.  A sung roll on an instrumental base would have nothing to sing,
     so it walks back to the vocal score that base came from (or returns null when the Seed itself is instrumental,
     letting the planner write a vocal melody for the new lyrics).  A Seed with no score: the first pass that has one. */
  function readyBaseTakeWithScore(sings) {
    if (sings === undefined) { sings = JamState.vocals !== 'instrumental'; }
    var p = buildOn();
    if (sings && isSeedPass(p) && passUnsung(p)) { return null; }
    for (var guard = 0; p && sings && passUnsung(p) && !isSeedPass(p) && guard < 50; guard++) {
      p = passById(p.scoreFromId) || passById(p.fromId) || JamState.passes.find(isSeedPass);
    }
    if (p && p.hasScore && !(sings && passUnsung(p))) { return p; }
    var seed = JamState.passes.find(isSeedPass);
    if (seed && seed.hasScore && !(sings && passUnsung(seed))) { return seed; }
    return JamState.passes.find(function (x) { return !isSeedPass(x) && x.hasScore && !(sings && passUnsung(x)); }) || null;
  }

  /* A card clicked: that pass is the base, and its settings go into the controls to build on.  The change
     count on Roll then counts from it. */
  function selectBase(id) {
    var p = passById(id);
    if (!p || p.id === JamState.cookingId || (!isSeedPass(p) && !p.hasAudio)) { return; }
    JamState.baseId = p.id;
    var s = p.snapshot;
    if (s) {
      JamState.parts = (s.parts || []).map(function (x) { return { name: x.name, cat: x.cat, level: x.level }; });
      if (s.vibe) { JamState.vibe = { x: s.vibe.x, y: s.vibe.y }; }
      if (s.bpm) { JamState.bpm = s.bpm; }
      if (typeof s.lyrics === 'string') { JamState.lyrics = s.lyrics; }
      if (s.vocals && (s.vocals === 'instrumental' || (JamState.lyrics || '').trim())) { JamState.vocals = s.vocals; }
      else if (!(JamState.lyrics || '').trim()) { JamState.vocals = 'instrumental'; }
      JamState.voiceId = s.voiceId || '';
      JamState.tones = (s.tones || []).slice();
      JamState.styleLora = s.styleLora || '';
      if (s.styleLoraModel != null) { JamState.styleLoraModel = Number(s.styleLoraModel); }
      if (s.styleLoraClip != null) { JamState.styleLoraClip = Number(s.styleLoraClip); }
      loadSculpt(s);
      JamState.lastRolledSnapshot = cloneSnapshot();
    }
    JamState.styleName = null;
    JamState.loraSong = null;
    saveSession();
    paintAll();
  }

  function activeLoraKind(name) {
    if (!name || !window.State || !State.options || !State.options.loras) { return ''; }
    var list = State.options.loras;
    for (var i = 0; i < list.length; i++) {
      if (list[i].name === name) { return list[i].kind || ''; }
    }
    return '';
  }

  /* How much of the song a short pass renders (Settings, Audio: Length of a Jam pass). */
  /* How much of the song a short pass renders: the length chosen in the top bar for this Jam, or, until one is
     chosen, the one in Settings (Audio: Length of a Jam pass). */
  var PASS_LENGTHS = [20, 30, 40, 60, 90];
  function settingPassSeconds() {
    var value = parseInt(typeof setting === 'function' ? setting('jam.pass_seconds', 40) : 40, 10);
    return value >= 10 && value <= 900 ? value : 40;
  }
  function passSeconds() {
    return JamState.passChoice || settingPassSeconds();
  }

  /* A Full Song's cap: the one in Settings for a new take, which the server raises to fit a longer plan.
     It was 210 s, which cut a longer Seed short. */
  function fullSongCap() {
    var value = parseInt(typeof setting === 'function' ? setting('takes.cap', 360) : 360, 10);
    return value >= 10 && value <= 900 ? value : 360;
  }

  function jamSpaceId() {
    if (JamState.spaceId && JamState.spaceId !== 'trash') { return JamState.spaceId; }
    var sp = (window.State && State.spaceId) || 'default';
    return sp === 'trash' ? 'default' : sp;
  }

  async function rollPass(opts) {
    opts = opts || {};
    if (JamState.cookingId) {
      if (typeof toast === 'function') { toast(t('A pass is already rolling. Wait for it, or cancel it first.')); }
      return;
    }
    var fastLoop = opts.fullSong ? false : JamState.fastLoop;
    var snap = opts.snapshot ? JSON.parse(JSON.stringify(opts.snapshot)) : cloneSnapshot();
    snap.fastLoop = fastLoop;
    // Plan & Roll plans this one pass again; Full Song on such a pass keeps the score it was given.
    var basePass = opts.basePassId ? JamState.passes.find(function (p) { return p.id === opts.basePassId && p.hasScore; }) : null;
    var from = opts.basePassId ? passById(opts.basePassId) : buildOn();
    if (opts.replan) { snap.lockScore = false; }
    if (basePass) { snap.lockScore = true; }
    var styleText = compileStyle(snap);
    var vi = vibeInfo(snap.vibe);

    // Each pass carries its own lyrics in its snapshot (starting from the Seed's words).
    var lyricsText = snap.vocals === 'instrumental' ? '' : (typeof snap.lyrics === 'string' ? snap.lyrics : (JamState.lyrics || ''));
    if (snap.vocals !== 'instrumental' && !lyricsText.trim()) {
      if (typeof toast === 'function') { toast(t('Add lyrics first, or choose Instrumental.'), 'bad'); }
      return;
    }

    var isFullSong = Boolean(opts.fullSong || !fastLoop);
    var passNum = nextPassNum();
    JamState.lastPassNum = passNum;
    var baseScorePass = basePass || (snap.lockScore ? readyBaseTakeWithScore(snap.vocals !== 'instrumental') : null);
    var passTitle = (isFullSong
      ? (opts.title || fullSongTitle(passNum))
      : JamState.starterName + ' \u00B7 ' + t('Pass #{n}', { n: passNum }));
    var loraKind = activeLoraKind(snap.styleLora);

    var fullVoiceMix = null;
    if (snap.vocals === 'voice') {
      if (isFullSong && snap.voiceId) {
        var pickedForSnap = readyVoicesList().filter(function (v) { return v.id === snap.voiceId; })[0] || null;
        fullVoiceMix = Object.assign({}, jamVoiceDefaults(pickedForSnap), snap.voiceMix || {});
      } else if (snap.voiceMix && Object.keys(snap.voiceMix).length) {
        fullVoiceMix = snap.voiceMix;
      }
    }

    var payload = {
      title: passTitle,
      space_id: jamSpaceId(),
      snippet: !isFullSong,
      base_take_id: baseScorePass ? baseScorePass.id : null,
      lock_score: Boolean(baseScorePass),
      instrumental: snap.vocals === 'instrumental',
      style: styleText,
      lyrics: snap.vocals === 'instrumental' ? '' : lyricsText,
      structure: snap.vocals === 'instrumental' && !baseScorePass ? (JamState.seedStructure || '') : '',
      max_duration: isFullSong ? fullSongCap() : passSeconds(),
      target_bpm: snap.bpm,
      harmony: snap.chords !== '' && snap.chords != null ? Number(snap.chords) : vi.harmony,
      interpretation: snap.performance || vi.interpretation,
      avoid: vi.avoid,
      cfg_scale: effectiveGrip(snap, vi),
      target_key: snap.key || null,
      start_section: !isFullSong && snap.startSection ? snap.startSection : null,
      voice_mix: fullVoiceMix,
      sampler_steps: basePass && opts.basePassId && basePass.samplerSteps ? basePass.samplerSteps
        : (isFullSong ? 32 : (snap.polish === 'draft' ? 24 : 32)),
      // As the Seed was made: a Jam does not normalise, or change the real-audio setting, unless the Seed did.
      realaudio: JamState.seedRealaudio !== false,
      normalise: Boolean(JamState.seedNormalise),
      style_lora: snap.styleLora || null,
      style_lora_model: (loraKind === 'decoder' || loraKind === 'both') ? snap.styleLoraModel : 0,
      style_lora_clip: (loraKind === 'planner' || loraKind === 'both') ? snap.styleLoraClip : 0,
      voice_id: snap.vocals === 'voice' && snap.voiceId ? snap.voiceId : null
    };
    // A Full Song of a pass is that pass made whole: its seed and its sampler steps, so it plays as the pass did.
    if (basePass && opts.basePassId && basePass.seed != null) { payload.seed = basePass.seed; }
    // Same seed: the pass is made with its base's seed, so what differs is what was changed.  The dice beside Roll
    // asks for a new one this once, everything else held.
    else if (JamState.holdSeed && !opts.newSeed) {
      var seedOf = baseScorePass || from;
      if (seedOf && seedOf.seed != null) { payload.seed = seedOf.seed; }
    }

    try {
      var created = await api('/api/jam/roll', { method: 'POST', body: JSON.stringify(payload) });
      // What changed from the pass it was built on.
      var diffs = computeDiffs((from && from.snapshot) || JamState.lastRolledSnapshot, snap);
      if (opts.replan) { diffs.unshift({ text: t('New arrangement'), cls: 'add' }); }
      if (payload.seed == null && !isFullSong) { diffs.unshift({ text: t('New seed'), cls: 'add' }); }
      if (isFullSong) { diffs.unshift({ text: t('Full Song'), cls: 'add' }); }
      JamState.lastRolledSnapshot = snap;
      JamState.cookingId = created.id;
      JamState.passes.push({
        num: passNum,
        id: created.id,
        title: created.title || passTitle,
        status: 'queued',
        progress: 2,
        stage: t('Queued'),
        hasAudio: false,
        hasScore: Boolean(baseScorePass),
        duration: 0,
        snapshot: snap,
        diffs: diffs,
        fromId: from ? from.id : null,
        seed: created.seed,
        samplerSteps: created.sampler_steps,
        scoreFromId: baseScorePass ? baseScorePass.id : null,
        replanned: !baseScorePass,
        error: null
      });
      saveSession();
      paintAll();
      startPolling();
      if (isFullSong && typeof toast === 'function') { toast(t('Full song queued as a take in your space.')); }
      if (typeof loadTakes === 'function') { loadTakes(); }
    } catch (err) {
      if (typeof toast === 'function') { toast(t('Roll failed: {message}', { message: tr(err.message) }), 'bad'); }
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
      pass.stage = t('Cancelled');
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

      if (rec.status === 'done' && rec.has_audio && isLibraryTake(rec)) {
        // A Full Song is a take in the space now: it leaves Roll History and the loop plays on.
        JamState.cookingId = null;
        stopPolling();
        dropPass(id);
        saveSession();
        if (typeof loadTakes === 'function') { loadTakes(); }
        paintAll();
        if (typeof toast === 'function') { toast(t('{title} is ready in your space.', { title: rec.title || t('The full song') })); }
        return;
      }
      if (rec.status === 'done' && rec.has_audio) {
        pass.progress = 100;
        JamState.cookingId = null;
        stopPolling();
        saveSession();
        if (typeof loadTakes === 'function') { loadTakes(); }
        if (JamSync.enabled) { JamSync.syncList(); }
        paintAll();
        // Switch the bottom player into the newly rolled pass, which, playing, is the base to build on next.
        if (JamState.open) {
          selectBase(id);
          JamAudio.play(id);
        }
        return;
      }
      if (rec.status === 'failed' || rec.status === 'cancelled') {
        pass.error = rec.error ? tr(rec.error) : t('Did not finish');
        JamState.cookingId = null;
        stopPolling();
        saveSession();
        paintAll();
        return;
      }
      paintTopbar();
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
  var JAM_COL_MIN = 260;
  var JAM_COL_KEY = 'yue2.jamColumns';

  function jamColumnShares() {
    try {
      var shares = JSON.parse(localStorage.getItem(JAM_COL_KEY) || 'null');
      if (Array.isArray(shares) && shares.length === 3 && shares.every(function (n) { return typeof n === 'number' && n > 0; })) {
        return shares;
      }
    } catch (e) {}
    return null;
  }

  function jamColumnsSideBySide(cols) {
    return cols.length === 3 && cols[0].offsetParent !== null && Math.abs(cols[0].offsetTop - cols[1].offsetTop) < 2 &&
      Math.abs(cols[1].offsetTop - cols[2].offsetTop) < 2;
  }

  function placeJamColumnHandles() {
    var box = document.querySelector('#jam-shell .jam-console');
    if (!box) { return; }
    var cols = box.querySelectorAll(':scope > .jam-col');
    var handles = box.querySelectorAll(':scope > .jam-col-handle');
    var side = jamColumnsSideBySide(cols);
    Array.prototype.forEach.call(handles, function (handle, i) {
      if (!side) { handle.style.display = 'none'; return; }
      handle.style.display = '';
      var left = cols[i].offsetLeft + cols[i].offsetWidth;
      handle.style.left = (left + (cols[i + 1].offsetLeft - left) / 2) + 'px';
    });
  }

  function applyJamColumns(shares) {
    var box = document.querySelector('#jam-shell .jam-console');
    if (!box) { return; }
    ['--jam-c1', '--jam-c2', '--jam-c3'].forEach(function (name, i) {
      if (shares) { box.style.setProperty(name, shares[i].toFixed(4) + 'fr'); } else { box.style.removeProperty(name); }
    });
    placeJamColumnHandles();
  }

  function setupJamColumns() {
    var box = document.querySelector('#jam-shell .jam-console');
    if (!box || box.querySelector(':scope > .jam-col-handle')) { return; }
    var cols = box.querySelectorAll(':scope > .jam-col');
    if (cols.length !== 3) { return; }
    [0, 1].forEach(function (i) {
      var handle = document.createElement('div');
      handle.className = 'jam-col-handle';
      handle.setAttribute('role', 'separator');
      handle.setAttribute('aria-orientation', 'vertical');
      handle.title = t('Drag to widen or narrow the columns. Double-click for the usual widths.');
      handle.addEventListener('pointerdown', function (event) {
        if (event.button !== 0 || !jamColumnsSideBySide(cols)) { return; }
        event.preventDefault();
        event.stopPropagation();
        var widths = Array.prototype.map.call(cols, function (col) { return col.offsetWidth; });
        var startX = event.clientX;
        var pair = widths[i] + widths[i + 1];
        handle.classList.add('dragging');
        document.body.classList.add('ed-col-dragging');
        if (handle.setPointerCapture) { handle.setPointerCapture(event.pointerId); }
        function move(ev) {
          var left = Math.max(JAM_COL_MIN, Math.min(pair - JAM_COL_MIN, widths[i] + ev.clientX - startX));
          var now = widths.slice();
          now[i] = left;
          now[i + 1] = pair - left;
          var total = now[0] + now[1] + now[2];
          applyJamColumns(now.map(function (w) { return w / total * 3; }));
        }
        function end() {
          handle.classList.remove('dragging');
          document.body.classList.remove('ed-col-dragging');
          handle.removeEventListener('pointermove', move);
          handle.removeEventListener('pointerup', end);
          handle.removeEventListener('pointercancel', end);
          var now = Array.prototype.map.call(cols, function (col) { return col.offsetWidth; });
          var total = now[0] + now[1] + now[2];
          try { localStorage.setItem(JAM_COL_KEY, JSON.stringify(now.map(function (w) { return w / total * 3; }))); } catch (e) {}
        }
        handle.addEventListener('pointermove', move);
        handle.addEventListener('pointerup', end);
        handle.addEventListener('pointercancel', end);
      });
      handle.addEventListener('dblclick', function () {
        try { localStorage.removeItem(JAM_COL_KEY); } catch (e) {}
        applyJamColumns(null);
      });
      box.appendChild(handle);
    });
    applyJamColumns(jamColumnShares());
    if (typeof ResizeObserver === 'function') { new ResizeObserver(placeJamColumnHandles).observe(box); }
    window.addEventListener('resize', placeJamColumnHandles);
  }

  function jamMax() {
    // Filling the window unless the person chose the usual size (stored as '0').
    try { return localStorage.getItem(JAM_MAX_KEY) !== '0'; } catch (e) { return true; }
  }

  function setJamMax(on) {
    var modal = document.getElementById('jam-modal');
    if (modal) { modal.classList.toggle('jam-max', Boolean(on)); }
    var btn = document.getElementById('jam-max');
    if (btn) {
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      btn.title = on ? t('Back to the usual size') : t('Fill the window');
      btn.setAttribute('aria-label', btn.title);
    }
    try { localStorage.setItem(JAM_MAX_KEY, on ? '1' : '0'); } catch (e) {}
    placeJamColumnHandles();
  }

  function buildShellOnce() {
    var shell = document.getElementById('jam-shell');
    if (!shell || shell.dataset.built) { return; }
    shell.dataset.built = '1';
    shell.innerHTML =
      '<div class="jam-topbar" id="jam-topbar"></div>' +
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
    setupJamColumns();
  }

  /* A column is repainted whole, which would put it, and any list in it that scrolls, back at the top.
     keepScroll notes where they are; the function it gives back puts them there again. */
  var SCROLLERS = ['jam-hist-list', 'jam-palette-chips', 'jam-lora-songs', 'jam-style-list', 'jam-lora-list'];
  function keepScroll(el) {
    var tops = { self: el.scrollTop };
    SCROLLERS.forEach(function (cls) {
      var node = el.querySelector('.' + cls);
      if (node) { tops[cls] = node.scrollTop; }
    });
    return function () {
      el.scrollTop = tops.self;
      SCROLLERS.forEach(function (cls) {
        var node = el.querySelector('.' + cls);
        if (node && tops[cls] != null) { node.scrollTop = tops[cls]; }
      });
    };
  }

  function paintAll() {
    buildShellOnce();
    paintTopbar();
    paintPartsCol();
    paintFeelCol();
    paintHistory();
    paintFooter();
    placeJamColumnHandles();
  }

  function paintTopbar() {
    var el = document.getElementById('jam-topbar');
    if (!el) { return; }
    var isMax = jamMax();
    var cookingPass = JamState.cookingId ? JamState.passes.find(function (p) { return p.id === JamState.cookingId; }) : null;
    var statusPill = cookingPass
      ? '<span class="jam-status-pill"><span class="jam-pulse-dot"></span> ' +
          t('Rolling {pass} \u00B7 {stage} ({progress}%)', { pass: escHtml(passLabel(cookingPass)), stage: escHtml(tr(cookingPass.stage || t('Working'))), progress: cookingPass.progress || 0 }) +
          ' <button type="button" class="jam-cancel-x" data-jam-act="cancel-cook" title="' + t('Cancel this roll') + '">&times;</button></span>'
      : '';

    el.innerHTML =
      '<div class="jam-brand">' +
        '<span class="jam-bar"></span>' +
        '<h1 class="jam-title">' + t('Jam') + '</h1>' +
        '<span class="jam-seed-name" title="' + t('The take this Jam plays with') + '">' + escHtml(JamState.starterName) + '</span>' +
      '</div>' +
      '<div class="jam-scope">' +
        '<div class="jam-seg-pill" title="' + t('Short passes of the song: their length is in Settings \u2192 Audio, Takes &amp; Stems') + '">' +
          '<select id="jam-pass-len" class="jam-seg-select' + (JamState.fastLoop ? ' active' : '') + '" title="' + t('How long a pass runs. Settings sets where each Jam starts') + '">' +
            PASS_LENGTHS.concat(PASS_LENGTHS.indexOf(passSeconds()) < 0 ? [passSeconds()] : []).sort(function (a, b) { return a - b; }).map(function (n) {
              return '<option value="' + n + '"' + (n === passSeconds() ? ' selected' : '') + '>' + t('{seconds}s Fast Loop', { seconds: n }) + '</option>';
            }).join('') +
          '</select>' +
          '<button type="button" data-jam-act="scope-full" class="' + (!JamState.fastLoop ? 'active' : '') + '">' + t('Full Song') + '</button>' +
        '</div>' +
      '</div>' +
      statusPill +
      '<div class="jam-head-actions">' +
        '<button type="button" class="ghost" data-jam-act="close" style="padding:7px 14px">' + t('Close') + '</button>' +
        '<button type="button" id="jam-max" data-jam-act="toggle-max" class="ed-tool ed-max-btn" title="' + (isMax ? t('Back to the usual size') : t('Fill the window')) + '" aria-label="' + (isMax ? t('Back to the usual size') : t('Fill the window')) + '" aria-pressed="' + (isMax ? 'true' : 'false') + '">' +
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
    var cooking = Boolean(JamState.cookingId);

    el.innerHTML =
      '<span class="jam-foot-hint muted small">' + t('Space to play or pause \u00B7 Esc to close') + '</span>' +
      '<div class="jam-foot-actions">' +
        // The base, as on its card: what the next roll builds on.  Clicking a card in Roll History changes it.
        '<span class="jam-roll-from" title="' + t('The next roll builds on this. Click a card in Roll History to change it') + '">' +
          '<span class="jam-base-tag">' + t('Base') + '</span>' + escHtml(passLabel(buildOn())) +
          (buildOn() && isSeedPass(buildOn()) && buildOn().title ? ' <span class="muted">\u00B7 ' + escHtml(buildOn().title) + '</span>' : '') +
        '</span>' +
        (JamState.passes.some(function (p) { return !isSeedPass(p); }) || pending > 0
          ? '<button type="button" class="jam-sec-btn" data-jam-act="reset-jam" title="' + t('Start again from the Seed: its sound, and no passes') + '"' + (cooking ? ' disabled' : '') + '>' + t('New Jam') + '</button>' : '') +
        (scoreLocked() ? '<button type="button" class="jam-rr-btn" data-jam-act="plan-roll" title="' + t('Plan &amp; Roll: plan this pass again from the Seed\u2019s words with your settings. New chords, groove and structure, so it can change a lot, and it takes longer than Roll.') + '"' + (cooking ? ' disabled' : '') + '>' + t('Plan &amp; Roll') + '</button>' : '') +
        // Again, differently: a new seed with every setting held (Same seed stays on for the rolls after).
        '<button type="button" class="jam-dice-btn" data-jam-act="roll-new-seed" title="' + t('Roll with a new seed: the same settings, a fresh take on them') + '" aria-label="' + t('Roll with a new seed') + '"' + (cooking ? ' disabled' : '') + '>' +
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true">' +
          '<rect x="3.5" y="3.5" width="17" height="17" rx="3.5"/><circle cx="8.5" cy="8.5" r="1.3" fill="currentColor" stroke="none"/>' +
          '<circle cx="15.5" cy="8.5" r="1.3" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.3" fill="currentColor" stroke="none"/>' +
          '<circle cx="8.5" cy="15.5" r="1.3" fill="currentColor" stroke="none"/><circle cx="15.5" cy="15.5" r="1.3" fill="currentColor" stroke="none"/></svg>' +
        '</button>' +
        '<button type="button" class="jam-roll-btn" data-jam-act="roll"' + (cooking ? ' disabled' : '') + '>' +
          '<span>' + (JamState.cookingId ? t('Rolling\u2026') : '\u27F3 ' + t('Roll')) + '</span>' +
          (!cooking && pending > 0 ? '<span class="jam-pending-badge">' + tn(pending, '{n} change', '{n} changes') + '</span>' : '') +
        '</button>' +
      '</div>';
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
            '<span class="jam-pips" data-part-idx="' + idx + '" title="' + t('Strength: {level} (drag left or right)', { level: LEVEL_LABELS[p.level] }) + '">' + pips + '</span>' +
            '<button type="button" class="jam-part-x" data-jam-act="remove-part" data-part-idx="' + idx + '" aria-label="' + t('Remove {name}', { name: escHtml(p.name) }) + '">&times;</button>' +
          '</span>';
        }).join('')
      : '<span class="muted small">' + t('No Parts yet. Click any chip below or type your own.') + '</span>';

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
      paletteHtml = '<button type="button" class="jam-pick-chip custom" data-jam-act="add-custom-part">' + t('+ Add \u201C{text}\u201D', { text: escHtml(JamState.searchQuery.trim()) }) + '</button>' + paletteHtml;
    }

    var loraKind = activeLoraKind(JamState.styleLora);
    var hasSound = loraKind === 'decoder' || loraKind === 'both';
    var hasPlan = loraKind === 'planner' || loraKind === 'both';

    // Preserve search input focus if currently typing
    var focusedId = document.activeElement && /^jam-(part-search|lora-song-filter|style-search|lora-filter)$/.test(document.activeElement.id) ? document.activeElement.id : null;
    var selStart = focusedId ? document.activeElement.selectionStart : null;
    var keptScroll = keepScroll(el);

    el.innerHTML =
      '<div class="jam-col-head">' +
        '<div class="jam-col-head-l">' +
          '<h4>' + t('Sound &amp; Parts') + '</h4>' +
          '<button type="button" class="jam-clear-btn" data-jam-act="clear-parts" title="' + t('Clear all active Parts') + '"' + (JamState.parts.length ? '' : ' disabled') + '>' + t('Clear') + '</button>' +
        '</div>' +
        '<span class="jam-col-meta">' + t('{count} / {max} active \u00B7 drag bars for strength', { count: JamState.parts.length, max: MAX_PARTS }) + '</span>' +
      '</div>' +
      '<div class="jam-parts-rack">' + activeHtml + '</div>' +
      '<div class="jam-palette">' +
        '<div class="picker-search-field">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>' +
          '<input type="search" id="jam-part-search" placeholder="' + t('Add any genre, instrument or texture\u2026') + '" value="' + escHtml(JamState.searchQuery) + '" autocomplete="off">' +
        '</div>' +
        '<div class="jam-tabs">' +
          [['inst', t('Instruments')], ['genre', t('Genres')], ['prod', t('Production')], ['rhythm', t('Rhythm')]].map(function (tab) {
            return '<button type="button" class="jam-tab' + (JamState.paletteTab === tab[0] ? ' active' : '') + '" data-jam-act="palette-tab" data-tab="' + tab[0] + '">' + tab[1] + '</button>';
          }).join('') +
        '</div>' +
        '<div class="jam-palette-chips">' + paletteHtml + '</div>' +
      '</div>' +
      stylePickerHtml() +
      '<div class="jam-lora-slot">' +
        '<div class="jam-kicker"><span>' + t('Style LoRA (optional)') + '</span>' +
          (loraKind && typeof loraKindPillHtml === 'function' ? loraKindPillHtml(loraKind) : '') +
        '</div>' +
        loraPickerHtml() +
        (JamState.styleLora
          ? '<div class="jam-lora-sliders">' +
              '<label>' + t('Sound') + ' <strong>' + (hasSound ? JamState.styleLoraModel.toFixed(2) : t('N/A')) + '</strong>' +
                '<input id="jam-lora-sound" type="range" min="0" max="2" step="0.05" value="' + JamState.styleLoraModel + '"' + (hasSound ? '' : ' disabled') + '>' +
              '</label>' +
              '<label>' + t('Score') + ' <strong>' + (hasPlan ? JamState.styleLoraClip.toFixed(2) : t('N/A')) + '</strong>' +
                '<input id="jam-lora-plan" type="range" min="0" max="2" step="0.05" value="' + JamState.styleLoraClip + '"' + (hasPlan ? '' : ' disabled') + '>' +
              '</label>' +
            '</div>' : '') +
        loraSongsHtml() +
      '</div>';

    keptScroll();
    if (focusedId && document.getElementById(focusedId)) {
      var inp = document.getElementById(focusedId);
      inp.focus();
      if (selStart != null) { inp.setSelectionRange(selStart, selStart); }
    }
  }

  /* The style menu, as in the editor: the styles saved there and the built-in presets.  One chosen sets the
     Parts from its tags (not its vocal, key or tempo: the Vocals card, the score and the Seed say those). */
  function cannedStyles() { return typeof CANNED_STYLES !== 'undefined' && Array.isArray(CANNED_STYLES) ? CANNED_STYLES : []; }
  function savedStyles() { return window.State && Array.isArray(State.savedStyles) ? State.savedStyles : []; }

  function stylePickerHtml() {
    var chev = '<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>';
    var html = '<div class="jam-style-picker">' +
      '<button type="button" class="source-picker-btn style-picker-btn" data-jam-act="style-menu" aria-expanded="' + (JamState.styleMenuOpen ? 'true' : 'false') + '" title="' + t('Choose a style: one you saved, or a built-in one. It sets the Parts; the tempo stays the song\u2019s') + '">' +
        '<span class="source-picker-label">' + escHtml(JamState.styleName || t('Choose a style\u2026')) + '</span>' + chev +
      '</button>';
    if (!JamState.styleMenuOpen) { return html + '</div>'; }
    var q = (JamState.styleQuery || '').trim().toLowerCase();
    var has = function (st) { return !q || (st.name || '').toLowerCase().indexOf(q) >= 0 || (st.prompt || '').toLowerCase().indexOf(q) >= 0; };
    var row = function (kind, key, st) {
      var on = JamState.styleName === st.name;
      return '<div class="style-picker-item' + (on ? ' selected' : '') + '" role="option" data-jam-act="style-pick" data-style-kind="' + kind + '" data-style-key="' + escHtml(key) + '" title="' + escHtml(st.prompt) + '">' +
        '<div class="style-item-top"><span class="style-item-name">' + escHtml(st.name) + '</span></div>' +
        '<div class="style-item-preview">' + escHtml(st.prompt) + '</div></div>';
    };
    var saved = savedStyles().filter(has);
    var canned = cannedStyles().filter(has);
    var openSaved = q ? saved.length > 0 : Boolean(JamState.styleSavedOpen);
    var list = '';
    if (!q || saved.length) {
      list += '<div class="style-picker-group' + (openSaved ? ' open' : '') + '" data-jam-act="style-saved-toggle" role="button">' + chev +
        '<span>' + t('Saved styles') + '</span><span class="count">' + (q ? saved.length + '/' : '') + savedStyles().length + '</span></div>';
      if (openSaved) {
        list += '<div class="picker-children">' + (saved.length ? saved.map(function (st) { return row('saved', st.id, st); }).join('')
          : '<div class="style-picker-empty muted">' + t('None yet. The editor\u2019s Save keeps a style here.') + '</div>') + '</div>';
      }
    }
    if (canned.length) {
      list += '<div class="style-picker-group open static"><span>' + t('Built-in presets') + '</span><span class="count">' + canned.length + '</span></div>' +
        '<div class="picker-children">' + canned.map(function (st) { return row('canned', st.name, st); }).join('') + '</div>';
    } else if (!saved.length) {
      list += '<div class="style-picker-empty muted">' + t('No matching styles') + '</div>';
    }
    return html +
      '<div class="jam-style-menu">' +
        '<div class="picker-search-field">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>' +
          '<input type="search" id="jam-style-search" placeholder="' + t('Search styles\u2026') + '" value="' + escHtml(JamState.styleQuery || '') + '" autocomplete="off">' +
        '</div>' +
        '<div class="style-picker-list jam-style-list" role="listbox">' + list + '</div>' +
      '</div></div>';
  }

  /* The Style LoRA picker, as the editor's: its groups, a LoRA's checkpoints, the kind of each and the search, built
     by app.js's loraMenuList from the same list (and the same open groups), with Jam's own choice. */
  function loraTitle(name) {
    var select = document.getElementById('style-lora');
    var option = select && name ? Array.prototype.filter.call(select.options, function (o) { return o.value === name; })[0] : null;
    return !name ? t('None') : (option ? (option.dataset.title || option.textContent) : name);
  }

  function loraPickerHtml() {
    var chev = '<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>';
    var html = '<div class="jam-lora-picker">' +
      '<button type="button" class="source-picker-btn" data-jam-act="lora-menu" aria-expanded="' + (JamState.loraMenuOpen ? 'true' : 'false') + '">' +
        '<span class="source-picker-label">' + escHtml(loraTitle(JamState.styleLora)) + '</span>' + chev + '</button>';
    if (!JamState.loraMenuOpen || typeof loraMenuList !== 'function') { return html + '</div>'; }
    var built = loraMenuList(JamState.styleLora || '', JamState.loraFilter || '');
    return html +
      '<div class="source-picker-menu lora-picker-menu jam-lora-menu" role="listbox">' +
        '<div class="picker-search-bar">' +
          '<div class="picker-search-field">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>' +
            '<input type="search" id="jam-lora-filter" placeholder="' + t('Search LoRAs\u2026') + '" value="' + escHtml(JamState.loraFilter || '') + '" autocomplete="off">' +
          '</div>' +
          (built.groupLabels.length >= 2 && !built.searching
            ? '<button type="button" class="picker-fold-btn" data-lora-fold-all="1">' + (built.anyOpen ? t('Collapse all') : t('Expand all')) + '</button>' : '') +
        '</div>' +
        '<div class="picker-scroll lora-picker-list jam-lora-list">' + built.html + '</div>' +
      '</div></div>';
  }

  /* A click in the LoRA menu: a heading or steps toggle folds, Fold all, or a LoRA chosen. */
  function loraMenuClick(event) {
    if (!event.target.closest('.jam-lora-menu')) { return false; }
    if (event.target.closest('#jam-lora-filter')) { return true; }
    if (event.target.closest('[data-lora-fold-all]')) {
      if (typeof foldAllLoraGroups === 'function') { foldAllLoraGroups(); }
      paintPartsCol();
      return true;
    }
    var group = event.target.closest('.lora-group, .lora-steps-toggle');
    if (group) {
      if (typeof toggleLoraGroup === 'function') { toggleLoraGroup(group.dataset.group || 'steps:' + group.dataset.steps); }
      paintPartsCol();
      return true;
    }
    var entry = event.target.closest('.lora-item');
    if (entry) {
      JamState.styleLora = entry.dataset.value || '';
      JamState.loraMenuOpen = false;
      JamState.loraSong = null;
      JamState.loraSongFilter = '';
      JamState.loraSongsAll = false;
      paintPartsCol();
      paintTopbar();
      updateCompiledPreview();
    }
    return true;
  }

  /* A Full Song is a whole render and a new take in the space, so it is asked about first. */
  // The number the next pass will carry: one past the highest a pass of this Jam has had.
  function nextPassNum() {
    var maxNum = JamState.passes.reduce(function (m, p) {
      return isSeedPass(p) ? m : Math.max(m, Number(p.num) || 0);
    }, 0);
    return Math.max(maxNum, Number(JamState.lastPassNum) || 0) + 1;
  }
  function fullSongTitle(n) { return t('{title} (Jam #{n})', { title: JamState.starterName, n: n }); }

  /* Asks before a full song, with its name ready to change (selected, so typing replaces it).  Resolves to
     { title } to go ahead (the name given, or the usual one when emptied), or null. */
  function confirmFullSong(full, title) {
    if (!full) { return Promise.resolve({}); }
    var usual = fullSongTitle(nextPassNum());
    if (typeof confirmModal !== 'function') { return Promise.resolve({ title: usual }); }
    return confirmModal({
      title: t('Render a full song?'),
      message: title ? t('This renders the whole song from {title} as a new take in your space. It takes longer than a pass.', { title: title })
        : t('This renders the whole song as a new take in your space. It takes longer than a pass.'),
      confirmText: t('Render'),
      input: true,
      defaultValue: usual,
      placeholder: usual
    }).then(function (name) {
      if (name === null || name === undefined || name === false) { return null; }
      return { title: String(name).trim() || usual };
    });
  }

  function focusById(id) {
    var input = document.getElementById(id);
    if (input) { input.focus({ preventScroll: true }); }
  }

  function focusStyleSearch() {
    var input = document.getElementById('jam-style-search');
    if (input) { input.focus({ preventScroll: true }); }
  }

  function applyPickedStyle(kind, key) {
    var st = kind === 'saved'
      ? savedStyles().filter(function (x) { return String(x.id) === String(key); })[0]
      : cannedStyles().filter(function (x) { return x.name === key; })[0];
    if (!st || !st.prompt) { return; }
    var parts = partsFromStyle(st.prompt, true, MAX_PARTS);
    if (parts.length) { JamState.parts = parts; }
    JamState.styleName = st.name;
    JamState.loraSong = null;
    JamState.styleMenuOpen = false;
    JamState.styleQuery = '';
    paintAll();
  }

  /* The songs the chosen LoRA learned, as pills (the editor's learned styles).  A big corpus has a filter and
     shows its first dozen until asked for the rest. */
  var LORA_SONGS_FOLD = 12;
  function loraSongsHtml() {
    var lora = jamLora(JamState.styleLora);
    var songs = (lora && lora.styles) || [];
    if (!songs.length) { return ''; }
    var q = (JamState.loraSongFilter || '').trim().toLowerCase();
    var matching = songs.map(function (song, i) { return { song: song, i: i }; }).filter(function (x) {
      return !q || ((x.song.title || '') + ' ' + (x.song.prompt || '')).toLowerCase().indexOf(q) >= 0;
    });
    var shown = q || JamState.loraSongsAll ? matching : matching.slice(0, LORA_SONGS_FOLD);
    var pills = shown.map(function (x) {
      var song = x.song;
      var hint = song.hint ? song.hint.split(',')[0].trim() : '';
      var label = song.title ? escHtml(song.title) + (hint ? ' <span class="muted">\u00B7 ' + escHtml(hint) + '</span>' : '') : escHtml(hint || song.prompt || '');
      var tip = (song.title ? song.title + ': ' : '') + (song.prompt || '') + (song.tempo ? ', ' + Math.round(song.tempo) + ' BPM' : '');
      var on = JamState.loraSong === lora.name + '#' + x.i;
      return '<button type="button" class="jam-pick-chip' + (on ? ' added' : '') + '" data-jam-act="lora-song" data-idx="' + x.i + '" title="' + escHtml(tip) + '">' + label + '</button>';
    }).join('');
    if (shown.length < matching.length) {
      pills += '<button type="button" class="jam-pick-chip custom" data-jam-act="lora-songs-all">' + t('Show all {matchingCount}', { matchingCount: matching.length }) + '</button>';
    }
    if (q && !matching.length) { pills = '<span class="muted small">' + t('No song matches.') + '</span>'; }
    return '<div class="jam-lora-songs-head"><span>' + t('Songs it learned \u00B7 click for that sound') + '</span>' +
        (songs.length > LORA_SONGS_FOLD ? '<input type="search" id="jam-lora-song-filter" placeholder="' + t('Filter {count} songs', { count: songs.length }) + '" value="' + escHtml(JamState.loraSongFilter || '') + '" autocomplete="off">' : '') +
      '</div>' +
      '<div class="jam-lora-songs">' + pills + '</div>';
  }

  /* ------------------------------------------------- The Feel card: sculpting beyond the Vibe pad */
  var KEYS = [['C', 'C'], ['C#', 'C# / Db'], ['D', 'D'], ['Eb', 'D# / Eb'], ['E', 'E'], ['F', 'F'], ['F#', 'F# / Gb'],
              ['G', 'G'], ['Ab', 'G# / Ab'], ['A', 'A'], ['Bb', 'A# / Bb'], ['B', 'B']];
  var PERFORMANCES = ['tight', 'standard', 'loose', 'settled', 'restless', 'wide'];
  var GRIPS = { gentle: 1.0, firm: 1.3, strong: 1.65, strict: 2.2 };
  var CHORDS = ['Familiar', 'Varied', 'Colourful', 'Adventurous', 'Outside'];
  function performanceLabel(v) {
    var names = { tight: t('Tight'), standard: t('Standard'), loose: t('Loose'), settled: t('Settled'), restless: t('Restless'), wide: t('Wide') };
    return v ? (names[v] || v) : t('As the Vibe has it');
  }
  function gripLabel(v) {
    var names = { gentle: t('Gentle'), firm: t('Firm'), strong: t('Strong'), strict: t('Strict') };
    return v ? (names[v] || v) : t('As the Vibe has it');
  }
  function chordsLabel(i) {
    var names = [t('Familiar'), t('Varied'), t('Colourful'), t('Adventurous'), t('Outside')];
    return names[i] || CHORDS[i];
  }
  function sectionLabel(name) {
    var names = { intro: t('Intro'), verse: t('Verse'), 'pre-chorus': t('Pre-chorus'), chorus: t('Chorus'), bridge: t('Bridge'),
                  outro: t('Outro'), interlude: t('Interlude') };
    return names[name] || name;
  }
  function effectiveGrip(s, vi) {
    return s && s.grip && GRIPS[s.grip] ? GRIPS[s.grip] : vi.cfgScale;
  }

  // The sections of the score a roll is made from, read from its `% name` lines once per take.
  var SECTION_CACHE = {};
  function sectionsOfBase() {
    var src = readyBaseTakeWithScore();
    if (!src) { return []; }
    if (SECTION_CACHE[src.id]) { return SECTION_CACHE[src.id]; }
    SECTION_CACHE[src.id] = [];
    api('/api/takes/' + encodeURIComponent(src.id)).then(function (rec) {
      var seen = [];
      String(rec.abc || '').split('\n').forEach(function (line) {
        var m = /^%\s+([a-z-]+)\s*$/i.exec(line);
        if (m && seen.indexOf(m[1].toLowerCase()) < 0) { seen.push(m[1].toLowerCase()); }
      });
      SECTION_CACHE[src.id] = seen;
      if (JamState.open && seen.length) { paintFeelCol(); }
    }).catch(function () {});
    return [];
  }

  function feelSelect(id, value, options, title) {
    return '<select id="' + id + '" class="jam-feel-select' + (value !== '' && value != null ? ' set' : '') + '"' + (title ? ' title="' + escHtml(title) + '"' : '') + '>' +
      options.map(function (o) { return '<option value="' + escHtml(o[0]) + '"' + (String(o[0]) === String(value == null ? '' : value) ? ' selected' : '') + '>' + escHtml(o[1]) + '</option>'; }).join('') +
      '</select>';
  }

  function readyVoicesList() {
    return (window.VOICES && VOICES.list ? VOICES.list : []).filter(function (v) { return v.state === 'ready'; });
  }

  function pickedJamVoice() {
    if (!JamState.voiceId) { return null; }
    var list = readyVoicesList();
    for (var i = 0; i < list.length; i++) {
      if (list[i].id === JamState.voiceId) { return list[i]; }
    }
    return null;
  }

  function jamVoiceDefaults(v) {
    if (!v) { return {}; }
    if (typeof voiceDefaults === 'function') { return voiceDefaults(v); }
    return {
      octave: v.octave || 0, level_db: v.level_db || 0, backing_db: v.backing_db || 0,
      likeness: v.likeness == null ? 0.75 : v.likeness,
      room: v.room == null ? 0.14 : v.room, brightness: v.brightness == null ? 1 : v.brightness,
      protect: v.protect == null ? 0.33 : v.protect, dynamics: v.dynamics == null ? 0.25 : v.dynamics,
      formant: v.formant == null ? 1 : v.formant, wet: v.wet == null ? 1 : v.wet,
      tail_gate: v.tail_gate || 'standard', rmvpe_thred: v.rmvpe_thred == null ? 0.08 : v.rmvpe_thred,
      f0_floor: v.f0_floor == null ? 75 : v.f0_floor
    };
  }

  function jamVoiceMixChanged(picked) {
    if (!picked || !JamState.voiceMix) { return false; }
    var own = jamVoiceDefaults(picked);
    return Object.keys(own).some(function (k) {
      if (JamState.voiceMix[k] == null) { return false; }
      if (k === 'tail_gate') { return String(JamState.voiceMix[k]) !== String(own[k]); }
      return Math.abs(Number(JamState.voiceMix[k]) - Number(own[k])) >= 0.001;
    });
  }

  // Whether anything in the Feel card is moved from its default.
  function feelIsSet() {
    return Boolean(JamState.key || JamState.startSection || JamState.performance || JamState.grip || JamState.chords !== '' ||
      JamState.polish === 'draft' || !JamState.holdSeed);
  }

  function feelSummaryParts() {
    var parts = [];
    if (JamState.key) { parts.push(JamState.key); }
    if (JamState.startSection) { parts.push(sectionLabel(JamState.startSection)); }
    if (JamState.performance) { parts.push(performanceLabel(JamState.performance)); }
    if (JamState.grip) { parts.push(gripLabel(JamState.grip)); }
    if (JamState.polish === 'draft') { parts.push(t('Draft')); }
    if (JamState.chords !== '') { parts.push(chordsLabel(Number(JamState.chords))); }
    return parts;
  }

  function feelCardHtml() {
    var sections = sectionsOfBase().filter(function (n) { return n !== 'silence'; });
    var locked = scoreLocked();
    var row = function (label, control, hint) {
      return '<label class="jam-feel-row"' + (hint ? ' title="' + escHtml(hint) + '"' : '') + '><span>' + label + '</span>' + control + '</label>';
    };
    var open = Boolean(JamState.feelOpen);
    var summary = !open ? feelSummaryParts() : [];
    return '<div class="jam-feel-card' + (open ? ' is-open' : '') + '">' +
      '<div class="jam-kicker jam-feel-head">' +
        '<button type="button" class="jam-feel-toggle" data-jam-act="feel-toggle" aria-expanded="' + (open ? 'true' : 'false') + '">' +
          '<span class="jam-fold-caret" aria-hidden="true">&#9662;</span>' +
          '<span>' + t('Feel') + '</span>' +
          (summary.length ? '<span class="jam-feel-summary">' + escHtml(summary.join(' \u00B7 ')) + '</span>' : '') +
        '</button>' +
        '<span class="jam-feel-tools">' +
        '<button type="button" class="jam-clear-btn" data-jam-act="feel-reset" title="' + t('Back to the Vibe pad\u2019s and the take\u2019s own') + '"' +
          (feelIsSet() ? '' : ' disabled') + '>' + t('Reset to defaults') + '</button>' +
        '<label class="jam-hold-seed" title="' + t('Make the next pass with its base\u2019s seed, so it differs only by what you changed') + '">' +
          '<input type="checkbox" id="jam-hold-seed"' + (JamState.holdSeed ? ' checked' : '') + '> ' + t('Same seed') + '</label>' +
        '</span>' +
      '</div>' +
      (open
        ? '<div class="jam-feel-grid">' +
            row(t('Key'), feelSelect('jam-key', JamState.key, [['', t('As the score')]].concat(KEYS)), t('Move the melody and chords to another key')) +
            row(t('Start at'), feelSelect('jam-start', JamState.startSection,
              [['', t('The top')]].concat(sections.map(function (n) { return [n, sectionLabel(n)]; }))),
              locked ? t('Which part of the song a short pass plays') : t('A pass starts at a section only when it keeps the score')) +
            row(t('Performance'), feelSelect('jam-performance', JamState.performance,
              [['', t('As the Vibe has it')]].concat(PERFORMANCES.map(function (n) { return [n, performanceLabel(n)]; }))),
              t('How loosely the music is played')) +
            row(t('Style grip'), feelSelect('jam-grip', JamState.grip,
              [['', t('As the Vibe has it')]].concat(Object.keys(GRIPS).map(function (n) { return [n, gripLabel(n) + ' (' + GRIPS[n] + ')']; }))),
              t('How firmly the sound follows the Parts and the Vibe')) +
            row(t('Polish'), feelSelect('jam-polish', JamState.polish === 'draft' ? 'draft' : '',
              [['', t('Polished')], ['draft', t('Draft')]]), t('Polished takes more steps over each pass')) +
            row(t('Chords (Plan & Roll)'), feelSelect('jam-chords', JamState.chords,
              [['', t('As the Vibe has it')]].concat(CHORDS.map(function (n, i) { return [String(i), chordsLabel(i)]; }))),
              t('How adventurous the chords are when Plan & Roll writes a new plan. Roll keeps the chords')) +
          '</div>'
        : '') +
    '</div>';
  }

  function paintFeelCol() {
    var el = document.getElementById('jam-col-feel');
    if (!el) { return; }
    var vi = vibeInfo(JamState.vibe);
    var px = Math.round(JamState.vibe.x * 100);
    var py = Math.round((1 - JamState.vibe.y) * 100);

    var readyVoices = readyVoicesList();
    var hasVoices = Boolean(window.VOICES && VOICES.service && VOICES.service.ok && readyVoices.length);
    var voiceSelectHtml = '';
    var voiceSettingsHtml = '';
    if (JamState.vocals === 'voice') {
      var picked = pickedJamVoice();
      var own = jamVoiceDefaults(picked);
      var effectiveMix = picked ? Object.assign({}, own, JamState.voiceMix || {}) : {};
      var voiceChanged = jamVoiceMixChanged(picked);
      var settingsOpen = Boolean(picked && JamState.voiceSettingsOpen);
      voiceSelectHtml = '<select id="jam-voice-select" style="padding:6px 10px;font-size:12.5px">' +
        '<option value="">Choose a recorded voice\u2026</option>' +
        readyVoices.map(function (v) {
          return '<option value="' + escHtml(v.id) + '"' + (v.id === JamState.voiceId ? ' selected' : '') + '>' + escHtml(v.name) + '</option>';
        }).join('') + '</select>';
      if (picked) {
        voiceSettingsHtml =
          '<div class="jam-voice-settings-wrap">' +
            '<div class="jam-kicker jam-voice-head">' +
              '<button type="button" class="jam-voice-link' + (voiceChanged ? ' changed' : '') + '" data-jam-act="voice-settings-toggle" aria-expanded="' + (settingsOpen ? 'true' : 'false') + '" title="' + escHtml(t("This take's settings for the voice")) + '">' +
                '<span class="jam-fold-caret" aria-hidden="true">&#9662;</span>' +
                '<span class="jam-voice-link-text">' + escHtml(t('Voice settings')) + '</span>' +
                (voiceChanged ? '<span class="voice-toggle-note">' + escHtml(t('own settings')) + '</span>' : '') +
              '</button>' +
              '<button type="button" class="jam-clear-btn" data-jam-act="voice-mix-reset"' + (voiceChanged ? '' : ' disabled') + '>' + t('Reset to defaults') + '</button>' +
            '</div>' +
            (settingsOpen && typeof voiceControls === 'function'
              ? '<div class="voice-panel jam-voice-panel">' +
                  '<div class="voice-mix" id="jam-voice-mix">' + voiceControls(effectiveMix, false) + '</div>' +
                  (typeof likenessCaution === 'function' ? likenessCaution(effectiveMix.likeness) : '') +
                '</div>'
              : '') +
          '</div>';
      }
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
        voiceSettingsHtml;
    }

    var keptScroll = keepScroll(el);
    var hasWords = Boolean((JamState.lyrics || '').trim());
    var lyricsEdited = (JamState.lyrics || '').trim() !== (JamState.seedLyrics || '').trim();
    var noWords = hasWords ? '' : ' disabled title="' + t('Add lyrics first to use vocals') + '"';
    var vocalMeta = !hasWords
      ? t('No words yet')
      : (JamState.vocals === 'instrumental'
        ? (lyricsEdited ? t('Lyrics ready \u2014 pick a voice') : t('No vocals'))
        : (lyricsEdited ? t('Sings edited lyrics') : t('Sings the Seed\u2019s words')));

    el.innerHTML =
      '<div class="jam-col-head">' +
        '<h4>' + t('Vibe, Tempo &amp; Vocals') + '</h4>' +
        '<span class="jam-col-meta">' + t('Direct studio controls') + '</span>' +
      '</div>' +
      '<div class="jam-xy-wrap">' +
        '<div class="jam-xy-pad" id="jam-xy-pad" title="' + t('Drag or click to shift mood &amp; energy') + '">' +
          '<div class="jam-xy-grid"></div>' +
          '<div class="jam-xy-axis-h"></div><div class="jam-xy-axis-v"></div>' +
          '<span class="jam-xy-lbl top">' + t('Energetic') + '</span>' +
          '<span class="jam-xy-lbl bot">' + t('Calm') + '</span>' +
          '<span class="jam-xy-lbl lft">' + t('Dark') + '</span>' +
          '<span class="jam-xy-lbl rgt">' + t('Bright') + '</span>' +
          '<div class="jam-xy-puck" id="jam-xy-puck" style="left:' + px + '%;top:' + py + '%"></div>' +
        '</div>' +
        '<div class="jam-xy-side">' +
          '<div class="jam-vibe-box">' +
            '<div class="jam-kicker"><span>' + t('Vibe') + '</span><span style="color:var(--cover-a)">' + escHtml(vibeLabel(vi.xWord)) + ' \u00B7 ' + escHtml(vibeLabel(vi.yWord)) + '</span></div>' +
            '<div class="jam-vibe-word" id="jam-vibe-word">' + escHtml(vi.word) + '</div>' +
            '<div class="jam-vibe-hint">' + (scoreLocked() ? t('Melody &amp; chords kept: shapes sound &amp; dynamics') : t('Shapes key, chords, arrangement &amp; dynamics')) + '</div>' +
          '</div>' +
          '<div class="jam-tempo-box">' +
            '<div class="jam-kicker"><span>' + t('Tempo') + '</span><span class="jam-bpm-val" id="jam-bpm-val">' + JamState.bpm + ' BPM</span></div>' +
            '<input id="jam-bpm-slider" type="range" min="' + BPM_MIN + '" max="' + BPM_MAX + '" step="1" value="' + JamState.bpm + '">' +
            '<div class="jam-detents"><span>' + t('Slow') + '</span><span>' + t('Med') + '</span><span>' + t('Fast') + '</span></div>' +
          '</div>' +
        '</div>' +
      '</div>' +
      '<div class="jam-vocal-card">' +
        '<div class="jam-kicker"><span>' + t('Vocals') + '</span><span>' + vocalMeta + '</span></div>' +
        '<div class="jam-vocal-row">' +
          '<div class="jam-mini-seg">' +
            '<button type="button" data-jam-act="vocals" data-v="instrumental" class="' + (JamState.vocals === 'instrumental' ? 'active' : '') + '">' + t('Instrumental') + '</button>' +
            '<button type="button" data-jam-act="vocals" data-v="female" class="' + (JamState.vocals === 'female' ? 'active' : '') + '"' + noWords + '>' + t('Female') + '</button>' +
            '<button type="button" data-jam-act="vocals" data-v="male" class="' + (JamState.vocals === 'male' ? 'active' : '') + '"' + noWords + '>' + t('Male') + '</button>' +
            '<button type="button" data-jam-act="vocals" data-v="voice" class="' + (JamState.vocals === 'voice' ? 'active' : '') + '"' + (!hasWords ? noWords : (!hasVoices ? ' disabled title="' + t('No ready recorded voices yet') + '"' : '')) + '>' + t('My Voice') + '</button>' +
          '</div>' +
          '<button type="button" class="jam-lyrics-btn' + (lyricsEdited ? ' edited' : '') + '" data-jam-act="edit-lyrics" title="' + (hasWords ? t('View or edit lyrics for the next roll') : t('Add lyrics to sing on the next roll')) + '">' + t('Lyrics') + '</button>' +
        '</div>' +
        vocalExtras +
      '</div>' +
      feelCardHtml() +
      '<div class="jam-prompt-peek">' +
        '<strong>' + t('Compiled style \u2192 YuE2') + (effectiveGrip(JamState, vi) ? ' \u00B7 CFG ' + effectiveGrip(JamState, vi) : '') + '</strong>' +
        '<span id="jam-compiled-style">' + escHtml(compileStyle()) + '</span>' +
        '<span class="jam-prompt-avoid" id="jam-compiled-avoid">' + (vi.avoid ? t('Avoid: {value}', { value: escHtml(vi.avoid) }) : '') + '</span>' +
      '</div>';
    keptScroll();
  }

  function paintHistory() {
    JamSync.autoEnable();
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
          var isBase = p.id === (buildOn() || {}).id;
          var isCooking = p.id === JamState.cookingId;
          var selectable = !isCooking && (seed || p.hasAudio);
          var isFailed = p.status === 'failed' || p.status === 'cancelled';

          var statePill = isCooking
            ? '<span class="jam-hist-state cook">' + t('Rolling {progress}%', { progress: p.progress || 0 }) + '</span>'
            : (isPlaying ? '<span class="jam-hist-state live">\u25B6 ' + t('Playing') + '</span>'
              : (isFailed ? '<span class="jam-hist-state bad">' + (p.status === 'cancelled' ? t('Cancelled') : t('Failed')) + '</span>'
                : '<span class="jam-hist-num">' + (p.duration ? fmtTime(p.duration) : t('Ready')) + '</span>'));

          var fromPass = passById(p.fromId);
          var diffsHtml = (fromPass && !seed ? '<span class="jam-from">' + t('from {pass}', { pass: escHtml(passLabel(fromPass)) }) + '</span>' : '') +
            (p.diffs || []).map(function (d) {
              return '<span class="jam-diff ' + escHtml(d.cls || '') + '">' + escHtml(d.text) + '</span>';
            }).join('');

          var actions = '';
          if (isCooking) {
            actions = '<div class="jam-cook-bar"><span style="width:' + (p.progress || 5) + '%"></span></div>' +
              '<div class="jam-hist-actions"><button type="button" class="jam-hist-btn" data-jam-act="cancel-cook">' + t('Cancel') + '</button></div>';
          } else if (seed) {
            actions = p.hasAudio
              ? '<div class="jam-hist-actions">' +
                  (isPlaying
                    ? '<button type="button" class="jam-hist-btn stop" data-jam-act="stop-pass">\u25A0 ' + t('Stop') + '</button>'
                    : '<button type="button" class="jam-hist-btn" data-jam-act="play-pass" data-pass-id="' + escHtml(p.id) + '">\u25B6 ' + t('Play') + '</button>') +
                '</div>'
              : '';
          } else if (p.hasAudio) {
            // A pass with sound here is a scratch pass: a finished Full Song or kept pass has left the list.
            actions = '<div class="jam-hist-actions">' +
              (isPlaying
                ? '<button type="button" class="jam-hist-btn stop" data-jam-act="stop-pass">\u25A0 ' + t('Stop') + '</button>'
                : '<button type="button" class="jam-hist-btn" data-jam-act="play-pass" data-pass-id="' + escHtml(p.id) + '">\u25B6 ' + t('Play') + '</button>') +
              '<button type="button" class="jam-hist-btn" data-jam-act="full-pass" data-pass-id="' + escHtml(p.id) + '">' + t('Full Song') + '</button>' +
              '<button type="button" class="jam-hist-btn danger" data-jam-act="delete-pass" data-pass-id="' + escHtml(p.id) + '" title="' + t('Delete this pass for good') + '">' + t('Delete') + '</button>' +
            '</div>';
          } else {
            actions = (p.error ? '<div class="small" style="color:var(--danger-text)">' + escHtml(p.error) + '</div>' : '') +
              '<div class="jam-hist-actions">' +
                '<button type="button" class="jam-hist-btn danger" data-jam-act="delete-pass" data-pass-id="' + escHtml(p.id) + '" title="' + t('Delete this pass for good') + '">' + t('Delete') + '</button>' +
              '</div>';
          }

          var tagHtml = (seed
            ? '<span class="jam-seed-tag">' + t('Seed') + '</span>'
            : '<span class="jam-hist-num">' + escHtml(passLabel(p)) + '</span>') +
            (isBase ? '<span class="jam-base-tag" title="' + t('The next roll builds on this') + '">' + t('Base') + '</span>' : '');

          return '<div class="jam-hist-card' + (seed ? ' is-seed' : '') + (isBase ? ' is-base' : '') + (selectable ? ' selectable' : '') + (isPlaying ? ' playing' : '') + (isCooking ? ' cooking' : '') + '"' +
            (selectable ? ' data-pass-id="' + escHtml(p.id) + '" title="' + (isBase ? t('The next roll builds on this') : t('Click to build the next roll on this')) +
              (p.seed != null ? ' \u00B7 ' + t('seed {seed}', { seed: p.seed }) : '') + '"' : '') + '>' +
            '<div class="jam-hist-top">' +
              '<span class="jam-hist-name">' + tagHtml + ' ' + escHtml(p.title) + '</span>' +
              '<span class="jam-hist-end">' + statePill +
                (seed ? '' : '<button type="button" class="jam-star' + (p.starred ? ' on' : '') + '" data-jam-act="star-pass" data-pass-id="' + escHtml(p.id) +
                  '" aria-pressed="' + (p.starred ? 'true' : 'false') + '" title="' + (p.starred ? t('Marked as one you like. Click to unmark') : t('Mark as one you like, to find it again')) +
                  '" aria-label="' + t('Mark as one you like') + '">' +
                  '<svg width="15" height="15" viewBox="0 0 24 24" fill="' + (p.starred ? 'currentColor' : 'none') + '" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true">' +
                  '<path d="M12 3.5l2.6 5.3 5.9.9-4.25 4.1 1 5.85L12 16.9l-5.25 2.75 1-5.85L3.5 9.7l5.9-.9z"/></svg></button>') +
              '</span>' +
            '</div>' +
            '<div class="jam-hist-diffs">' + diffsHtml + '</div>' +
            actions +
          '</div>';
        }).join('')
      : '<div class="jam-hist-empty">' +
          '<strong>' + t('No passes yet') + '</strong>' +
          '<p class="muted small">' + t('Shape your Parts, Vibe &amp; Tempo on the left, then click <b>Roll</b>. The pass playing loops while the next one is made, and the new one fades in when it is ready.') + '</p>' +
        '</div>';

    var countLabel = hasSeed
      ? (rolledCount ? tn(rolledCount, 'Seed + {n} pass', 'Seed + {n} passes') : t('Seed'))
      : tn(rolledCount, '{n} pass', '{n} passes');
    var playableCount = playablePasses().length;
    var syncDisabled = !JamSync.enabled && playableCount < 2;
    var syncTitle = syncDisabled
      ? t('Roll a pass to switch between tracks in sync')
      : (JamSync.enabled
        ? t('Synced playback is on \u2014 Play, Previous/Next, or 0 (Seed) and 1\u20139 switch tracks at the same moment')
        : t('Switch between Roll History tracks instantly at the same point in playback'));
    var syncProg = JamSync.enabled ? JamSync.loadProgress() : null;
    var metaLabel = (syncProg && syncProg.done < syncProg.total)
      ? t('Loading {done} of {all}\u2026', { done: syncProg.done, all: syncProg.total })
      : countLabel;

    // Repainted on every poll while a pass cooks: where the person had scrolled to stays put.
    var keptScroll = keepScroll(el);
    el.innerHTML =
      '<div class="jam-col-head">' +
        '<div class="jam-col-head-l">' +
          '<h4>' + t('Roll History') + '</h4>' +
          '<button type="button" class="jam-sync-btn' + (JamSync.enabled ? ' on' : '') + '" data-jam-act="toggle-sync" aria-pressed="' + (JamSync.enabled ? 'true' : 'false') + '" title="' + syncTitle + '"' + (syncDisabled ? ' disabled' : '') + '>' + t('Sync') + '</button>' +
        '</div>' +
        '<span class="jam-col-meta">' + metaLabel + '</span>' +
      '</div>' +
      '<div class="jam-hist-list">' + cards + '</div>';
    keptScroll();
  }

  /* ------------------------------------------------- Interactions */
  function togglePart(name, cat) {
    var key = name.toLowerCase();
    var idx = JamState.parts.findIndex(function (p) { return p.name.toLowerCase() === key; });
    if (idx >= 0) {
      JamState.parts.splice(idx, 1);
    } else {
      if (JamState.parts.length >= MAX_PARTS) {
        if (typeof toast === 'function') { toast(t('Up to {max} Parts per roll.', { max: MAX_PARTS })); }
        return;
      }
      JamState.parts.push({ name: name, cat: cat || 'inst', level: 2 });
    }
    JamState.styleName = null;
    paintPartsCol();
    paintTopbar();
    updateCompiledPreview();
  }

  function updateCompiledPreview() {
    var el = document.getElementById('jam-compiled-style');
    if (el) { el.textContent = compileStyle(); }
    var av = document.getElementById('jam-compiled-avoid');
    if (av) {
      var vi = vibeInfo(JamState.vibe);
      av.textContent = vi.avoid ? t('Avoid: {value}', { value: vi.avoid }) : '';
    }
  }

  function onShellClick(event) {
    if (loraMenuClick(event)) { return; }
    // Picking the pass length is choosing short passes: lit at once, without redrawing the list being opened.
    if (event.target.id === 'jam-pass-len' && !JamState.fastLoop) {
      JamState.fastLoop = true;
      event.target.classList.add('active');
      var full = document.querySelector('[data-jam-act="scope-full"]');
      if (full) { full.classList.remove('active'); }
      paintFooter();
      return;
    }
    var card = event.target.closest('.jam-hist-card.selectable');
    if (card && !event.target.closest('button')) { selectBase(card.dataset.passId); return; }
    var btn = event.target.closest('[data-jam-act]');
    if (!btn) { return; }
    var act = btn.dataset.jamAct;
    if (act === 'close') { close(); return; }
    if (act === 'lora-menu') { JamState.loraMenuOpen = !JamState.loraMenuOpen; JamState.loraFilter = ''; paintPartsCol(); focusById('jam-lora-filter'); return; }
    if (act === 'toggle-max') { setJamMax(!jamMax()); return; }
    if (act === 'reset-jam') { newJamFromSeed(); return; }
    if (act === 'roll') { confirmFullSong(!JamState.fastLoop).then(function (go) { if (go) { rollPass({ title: go.title }); } }); return; }
    if (act === 'roll-new-seed') {
      confirmFullSong(!JamState.fastLoop).then(function (go) { if (go) { rollPass({ title: go.title, newSeed: true }); } });
      return;
    }
    if (act === 'plan-roll') { confirmFullSong(!JamState.fastLoop).then(function (go) { if (go) { rollPass({ replan: true, title: go.title }); } }); return; }
    if (act === 'cancel-cook') { cancelCooking(); return; }
    if (act === 'scope-fast') { JamState.fastLoop = true; paintTopbar(); return; }
    if (act === 'scope-full') { JamState.fastLoop = false; paintTopbar(); return; }
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
    if (act === 'style-menu') { JamState.styleMenuOpen = !JamState.styleMenuOpen; JamState.styleQuery = ''; paintPartsCol(); focusStyleSearch(); return; }
    if (act === 'style-saved-toggle') { JamState.styleSavedOpen = !JamState.styleSavedOpen; paintPartsCol(); return; }
    if (act === 'style-pick') { applyPickedStyle(btn.dataset.styleKind, btn.dataset.styleKey); return; }
    if (act === 'lora-song') { applyLoraSong(Number(btn.dataset.idx)); return; }
    if (act === 'lora-songs-all') { JamState.loraSongsAll = true; paintPartsCol(); return; }
    if (act === 'star-pass') {
      // A mark within the Jam only, to pick out the passes worth keeping; it is not the library's star.
      var marked = passById(btn.dataset.passId);
      if (marked) { marked.starred = !marked.starred; saveSession(); paintHistory(); }
      return;
    }
    if (act === 'feel-toggle') {
      JamState.feelOpen = !JamState.feelOpen;
      paintFeelCol();
      return;
    }
    if (act === 'feel-reset') {
      loadSculpt({ voiceMix: JamState.voiceMix });
      JamState.holdSeed = true;
      saveSession();
      paintFeelCol();
      paintFooter();
      return;
    }
    if (act === 'voice-settings-toggle') {
      JamState.voiceSettingsOpen = !JamState.voiceSettingsOpen;
      paintFeelCol();
      return;
    }
    if (act === 'voice-mix-reset') {
      JamState.voiceMix = {};
      saveSession();
      paintFeelCol();
      paintFooter();
      return;
    }
    if (act === 'clear-parts') {
      if (JamState.parts.length) {
        JamState.parts = [];
        JamState.styleName = null;
        paintPartsCol();
        paintTopbar();
        updateCompiledPreview();
      }
      return;
    }
    if (act === 'remove-part') {
      var rIdx = parseInt(btn.dataset.partIdx, 10);
      if (!isNaN(rIdx)) { JamState.parts.splice(rIdx, 1); JamState.styleName = null; paintPartsCol(); paintTopbar(); updateCompiledPreview(); }
      return;
    }
    if (act === 'vocals') {
      if (btn.dataset.v !== 'instrumental' && !(JamState.lyrics || '').trim()) { return; }
      JamState.vocals = btn.dataset.v;
      paintFeelCol();
      paintTopbar();
      return;
    }
    if (act === 'edit-lyrics') {
      if (typeof window.openLyricsEditor === 'function') {
        window.openLyricsEditor({
          title: t('Lyrics for next roll'),
          value: JamState.lyrics || '',
          seedValue: JamState.seedLyrics || '',
          onChange: function (text) {
            JamState.lyrics = text;
            if (!text.trim() && JamState.vocals !== 'instrumental') {
              JamState.vocals = 'instrumental';
            }
            paintFeelCol();
            paintTopbar();
          },
          onClose: function () {
            saveSession();
          },
          // Write lyrics, as in the editor: a whole new set of words for this Jam's next rolls.  New words do not fit
          // the Seed's melody, which Roll keeps, so the window says to use Plan & Roll.
          write: {
            caution: t('New words may not fit the melody Roll keeps and can come out garbled. If they do, use Plan & Roll, which writes a melody for them.'),
            getExisting: function () { var big = document.getElementById('lyrics-big'); return big ? big.value : (JamState.lyrics || ''); },
            getStyle: function () { return compileStyle(cloneSnapshot()); },
            // The sections of the words in the box; with none, an instrumental Seed's own sections.
            getSections: function () {
              var big = document.getElementById('lyrics-big');
              var words = big ? big.value : (JamState.lyrics || '');
              var own = typeof expandSectionsOf === 'function' ? expandSectionsOf(words) : [];
              return own.length || typeof expandSectionsOf !== 'function' ? own : expandSectionsOf(JamState.seedStructure || '');
            },
            onLand: function (text) {
              JamState.lyrics = text;
              if (text.trim() && JamState.vocals === 'instrumental') { JamState.vocals = 'female'; }
              saveSession();
              paintFeelCol();
              paintTopbar();
              paintFooter();
            }
          }
        });
      }
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
    if (act === 'toggle-sync') {
      JamSync.toggle();
      return;
    }
    if (act === 'play-pass') {
      var pid = btn.dataset.passId;
      // Switch audio first so Sync's 8 ms crossfade fires immediately, before DOM repaint.
      if (pid === JamAudio.currentId && !JamAudio.playing) { JamAudio.resume(); } else { JamAudio.play(pid); }
      // The pass played is the one being worked on: it becomes the base, its settings in the controls.
      if (pid !== (buildOn() || {}).id) { selectBase(pid); }
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
      if (fp) {
        confirmFullSong(true, fp.title).then(function (go) {
          if (go) { rollPass({ fullSong: true, snapshot: fp.snapshot, basePassId: fp.id, title: go.title }); }
        });
      }
      return;
    }
  }

  async function deletePass(passId) {
    if (!passId) { return; }
    var target = JamState.passes.find(function (p) { return p.id === passId; });
    if (isSeedPass(target)) { return; }
    // Check with the server: Jam never deletes a take that is in the library.  One that has become one
    // since (kept from another window, say) just leaves Roll History.
    try {
      var check = await api('/api/takes/' + encodeURIComponent(passId));
      if (isLibraryTake(check)) {
        dropPass(passId);
        saveSession();
        paintAll();
        return;
      }
    } catch (err) { /* proceed to clean up local history if already gone */ }
    JamAudio.stopIfPlaying(passId);

    try {
      await api('/api/takes/' + encodeURIComponent(passId), { method: 'DELETE' });
    } catch (err) {
      if (typeof toast === 'function') { toast(t('Could not delete the pass: {message}', { message: tr(err.message) }), 'bad'); }
      return;
    }
    JamState.passes = JamState.passes.filter(function (p) { return p.id !== passId; });
    if (!JamState.passes.some(function (p) { return !isSeedPass(p); })) { JamState.lastPassNum = 0; }
    if (JamState.baseId === passId) { JamState.baseId = seedId(); }
    if (JamSync.enabled && playablePasses().length < 2) { JamSync.disable({ handoff: true }); }
    if (!JamState.passes.length) {
      JamState.lastRolledSnapshot = null;
    }
    saveSession();
    paintAll();
    if (typeof paintTransport === 'function') { paintTransport(); }
    if (typeof loadTakes === 'function') { loadTakes(); }
  }

  function playablePasses() {
    return JamState.passes.slice().sort(function (a, b) {
      var aSeed = isSeedPass(a) ? 0 : 1;
      var bSeed = isSeedPass(b) ? 0 : 1;
      if (aSeed !== bSeed) { return aSeed - bSeed; }
      return (a.num || 0) - (b.num || 0);
    }).filter(function (p) { return p.hasAudio && p.id !== JamState.cookingId; });
  }

  function canStep() { return playablePasses().length >= 2; }

  function stepPass(delta) {
    var list = playablePasses();
    if (list.length < 2) { return false; }
    var cur = JamAudio.currentId || (buildOn() && buildOn().id);
    var idx = -1;
    for (var i = 0; i < list.length; i++) {
      if (list[i].id === cur) { idx = i; break; }
    }
    var nextIdx = idx === -1 ? (delta > 0 ? 0 : list.length - 1) : (idx + delta + list.length) % list.length;
    var next = list[nextIdx];
    JamAudio.play(next.id);
    selectBase(next.id);
    return true;
  }

  function jumpToSyncPass(num) {
    if (!JamSync.enabled) { return false; }
    var list = playablePasses();
    var target = null;
    for (var i = 0; i < list.length; i++) {
      var p = list[i];
      if (num === 0 ? isSeedPass(p) : (!isSeedPass(p) && p.num === num)) {
        target = p;
        break;
      }
    }
    if (!target) { return false; }
    if (target.id === JamAudio.currentId && !JamAudio.playing) {
      JamAudio.resume();
    } else if (target.id !== JamAudio.currentId || !JamAudio.playing) {
      JamAudio.play(target.id);
    }
    if (target.id !== (buildOn() || {}).id) { selectBase(target.id); }
    return true;
  }

  function shouldLoop(id) {
    return Boolean(JamState.open && id && JamState.passes.some(function (p) { return p.id === id; }));
  }

  function onTransportChange() {
    if (JamState.open) { paintHistory(); }
  }

  function handleKey(event) {
    if (!JamState.open) { return false; }
    var el = document.activeElement;
    var tag = (el && el.tagName) || '';
    var aimed = (event.target && event.target.tagName) || '';
    if (tag === 'TEXTAREA' || tag === 'SELECT' || aimed === 'TEXTAREA' || aimed === 'SELECT' ||
        (el && el.isContentEditable) || (event.target && event.target.isContentEditable)) { return false; }
    if (tag === 'INPUT' && el.type !== 'range' && el.type !== 'checkbox' && el.type !== 'button') { return false; }
    if (aimed === 'INPUT' && event.target.type !== 'range' && event.target.type !== 'checkbox' && event.target.type !== 'button') { return false; }
    if (event.code === 'Space') {
      if (tag === 'BUTTON') { el.blur(); }
      JamAudio.toggle();
      return true;
    }
    if ((event.key === 'f' || event.key === 'F') && !event.ctrlKey && !event.metaKey && !event.altKey && !event.repeat) {
      if (typeof toggleFullscreen === 'function') { toggleFullscreen(); }
      return true;
    }
    if ((event.key === 'v' || event.key === 'V') && !event.shiftKey && !event.ctrlKey && !event.metaKey && !event.altKey && !event.repeat) {
      if (window.Visualizer) { window.Visualizer.toggle(); }
      return true;
    }
    if (!event.ctrlKey && !event.metaKey && !event.altKey && !event.repeat && /^[0-9]$/.test(event.key)) {
      return jumpToSyncPass(Number(event.key));
    }
    if (event.shiftKey && event.key === 'ArrowLeft') { return stepPass(-1); }
    if (event.shiftKey && event.key === 'ArrowRight') { return stepPass(1); }
    if (event.key === 'ArrowLeft' && tag !== 'INPUT') { if (typeof nudge === 'function') { nudge(-5); } return true; }
    if (event.key === 'ArrowRight' && tag !== 'INPUT') { if (typeof nudge === 'function') { nudge(5); } return true; }
    if (event.key === 'ArrowUp' && tag !== 'INPUT') {
      var volUp = document.getElementById('volume');
      if (volUp) { volUp.value = Math.min(100, Number(volUp.value) + 5); volUp.dispatchEvent(new Event('input')); }
      return true;
    }
    if (event.key === 'ArrowDown' && tag !== 'INPUT') {
      var volDn = document.getElementById('volume');
      if (volDn) { volDn.value = Math.max(0, Number(volDn.value) - 5); volDn.dispatchEvent(new Event('input')); }
      return true;
    }
    return false;
  }

  function onShellInput(event) {
    var tg = event.target;
    if (tg.id === 'jam-lora-filter') {
      JamState.loraFilter = tg.value;
      paintPartsCol();
      return;
    }
    if (tg.id === 'jam-style-search') {
      JamState.styleQuery = tg.value;
      paintPartsCol();
      return;
    }
    if (tg.id === 'jam-lora-song-filter') {
      JamState.loraSongFilter = tg.value;
      paintPartsCol();
      return;
    }
    if (tg.id === 'jam-part-search') {
      JamState.searchQuery = tg.value;
      paintPartsCol();
      return;
    }
    if (tg.id === 'jam-bpm-slider') {
      JamState.bpm = parseInt(tg.value, 10) || 96;
      var lbl = document.getElementById('jam-bpm-val');
      if (lbl) { lbl.textContent = JamState.bpm + ' BPM'; }
      updateCompiledPreview();
      paintTopbar();
      return;
    }
    if (tg.id === 'jam-lora-sound') {
      JamState.styleLoraModel = parseFloat(tg.value);
      paintPartsCol();
      return;
    }
    if (tg.id === 'jam-lora-plan') {
      JamState.styleLoraClip = parseFloat(tg.value);
      paintPartsCol();
      return;
    }
  }

  function onShellChange(event) {
    var tg = event.target;
    var feel = { 'jam-key': 'key', 'jam-start': 'startSection', 'jam-performance': 'performance', 'jam-grip': 'grip', 'jam-chords': 'chords' };
    if (feel[tg.id]) {
      JamState[feel[tg.id]] = tg.value;
      paintFeelCol();
      paintFooter();
      return;
    }
    if (tg.id === 'jam-polish') { JamState.polish = tg.value === 'draft' ? 'draft' : 'polished'; paintFeelCol(); paintFooter(); return; }
    if (tg.id === 'jam-hold-seed') { JamState.holdSeed = tg.checked; saveSession(); paintFeelCol(); return; }
    if (tg.dataset && tg.dataset.mix && tg.closest('#jam-voice-mix')) {
      var field = tg.dataset.mix;
      var isStr = field === 'tail_gate';
      var nextVal = isStr ? String(tg.value) : Number(tg.value);
      var picked = pickedJamVoice();
      var own = jamVoiceDefaults(picked);
      JamState.voiceMix = Object.assign({}, JamState.voiceMix || {});
      var sameAsOwn = own[field] != null && (isStr ? nextVal === String(own[field]) : Math.abs(nextVal - Number(own[field])) < 0.001);
      if (sameAsOwn) {
        delete JamState.voiceMix[field];
      } else {
        JamState.voiceMix[field] = nextVal;
      }
      saveSession();
      paintFeelCol();
      paintFooter();
      var again = document.querySelector('#jam-voice-mix [data-mix="' + field + '"]');
      if (again) { again.focus(); }
      return;
    }
    if (tg.id === 'jam-pass-len') {
      JamState.passChoice = parseInt(tg.value, 10) || null;
      JamState.fastLoop = true;
      paintTopbar();
      return;
    }
    if (tg.id === 'jam-voice-select') {
      JamState.voiceId = tg.value;
      JamState.voiceMix = {};
      if (!JamState.voiceId) { JamState.voiceSettingsOpen = false; }
      saveSession();
      paintFeelCol();
      paintTopbar();
      paintFooter();
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
        pips.title = t('Strength: {level} (drag left or right)', { level: LEVEL_LABELS[lv] });
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
  function openFromTake(take) {
    var modal = document.getElementById('jam-modal');
    if (!modal || !take) { return; }
    JamState.open = true;
    JamState.passChoice = null;       // each Jam starts at the length in Settings
    modal.classList.remove('hidden');
    document.body.classList.add('jam-open');
    if (typeof window.syncPlayerHeight === 'function') { window.syncPlayerHeight(); }
    // A Jam is the take's own, a take inside another included: keyed by its mother, opening one showed the
    // other's Seed and words.  A session whose Seed is another take (saved that way before) starts afresh.
    var key = 'take:' + take.id;
    var ownSeed = function () {
      return JamState.passes.some(function (p) { return p.isSeed && p.id === take.id; });
    };
    var cueIfIdle = function () {
      var audio = JamAudio.audio();
      if (take.has_audio && !JamAudio.playing && !(audio && (audio.currentSrc || audio.src)) && typeof activateTakeRecording === 'function') {
        activateTakeRecording(take);
      }
      if (typeof paintTransport === 'function') { paintTransport(); }
    };
    var syncSeedIdentity = function () {
      if (take.title) { JamState.starterName = take.title; }
      if (take.space_id && take.space_id !== 'trash' && take.space_id !== '__jam__') { JamState.spaceId = take.space_id; }
      var seedPass = JamState.passes.find(isSeedPass);
      if (seedPass && take.title) { seedPass.title = take.title; }
    };
    if (JamState.sessionKey === key && JamState.passes.length && ownSeed()) {
      syncSeedIdentity();
      paintAll();
      syncPassesFromServer();
      cueIfIdle();
      return;
    }
    if (JamSync.enabled) { JamSync.disable({ handoff: false }); }
    if (loadSession(key) && ownSeed()) {
      syncSeedIdentity();
      paintAll();
      syncPassesFromServer();
      cueIfIdle();
      return;
    }
    JamState.sessionKey = key;
    seedFromTake(take);
  }

  function close() {
    var modal = document.getElementById('jam-modal');
    if (JamSync.enabled) { JamSync.disable({ handoff: true }); }
    JamState.open = false;
    saveSession();
    document.body.classList.remove('jam-open');
    if (modal) { modal.classList.add('hidden'); }
    if (typeof paintTransport === 'function') { paintTransport(); }
    // The take's card shows whether it has a Jam: painted again now, since an unchanged list is not repainted.
    if (typeof paintTakes === 'function') { paintTakes(); }
  }

  async function openPass(passId, seedTakeId) {
    var sid = seedTakeId || null;
    if (!sid && passId) {
      if (JamState.passes.some(function (p) { return p.id === passId; })) {
        sid = seedId();
      } else {
        var saved = readSavedSessions();
        var keys = Object.keys(saved);
        for (var i = 0; i < keys.length; i++) {
          var s = saved[keys[i]];
          if (s && Array.isArray(s.passes) && s.passes.some(function (p) { return p.id === passId; })) {
            var sp = s.passes.find(function (p) { return p && p.isSeed; });
            sid = (sp && sp.id) || (keys[i].indexOf('take:') === 0 ? keys[i].slice(5) : null);
            break;
          }
        }
      }
    }
    if (!sid) { return false; }
    if (typeof editorOpen === 'function' && editorOpen() && typeof closeEditor === 'function') { closeEditor(); }
    if (window.Visualizer && window.Visualizer.isOpen) { window.Visualizer.toggle(false); }
    var take = null;
    if (window.State && Array.isArray(State.takes)) {
      for (var j = 0; j < State.takes.length; j++) {
        if (State.takes[j].id === sid) { take = State.takes[j]; break; }
      }
    }
    if (!take) {
      try { take = await api('/api/takes/' + encodeURIComponent(sid)); } catch (err) { return false; }
    }
    if (!take) { return false; }
    openFromTake(take);
    setTimeout(function () {
      var card = document.querySelector('#jam-col-hist .jam-hist-card[data-pass-id="' + passId + '"]');
      if (card) { card.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
    }, 60);
    return true;
  }

  function isOpen() { return JamState.open; }

  window.Jam = {
    openFromTake: openFromTake,
    openPass: openPass,
    close: close,
    isOpen: isOpen,
    handleKey: handleKey,
    onTransportChange: onTransportChange,
    shouldLoop: shouldLoop,
    canStep: canStep,
    stepPass: stepPass,
    togglePlay: function () { JamAudio.toggle(); },
    isSyncActive: function () { return JamSync.isOwning(); },
    isSyncPlaying: function () { return JamSync.isOwning() && JamSync.playing; },
    syncClock: function () { return JamSync.clock(); },
    syncSeek: function (at) { JamSync.seek(at); },
    syncNudge: function (sec) { JamSync.nudge(sec); },
    onVolumeChange: function () { JamSync.applyVolume(); },
    onRateChange: function (rate) { JamSync.setRate(rate); },
    stopSyncForMain: function () { if (JamSync.enabled) { JamSync.disable({ handoff: false }); } }
  };
})();
