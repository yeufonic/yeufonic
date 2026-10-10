/**
 * Visual Piano Roll / MIDI Editor for Yeufonic
 * Bidirectional ABC notation <-> visual interactive note editing.
 */
(function (global) {
  'use strict';

  var MIN_PITCH = 24; // C1
  var MAX_PITCH = 96; // C7
  var NUM_PITCHES = MAX_PITCH - MIN_PITCH + 1; // 73 pitches
  var ROW_HEIGHT = 20; // px per semitone
  var TICK_WIDTH = 18; // px per tick (16th note default)

  var PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  var BLACK_KEYS = [false, true, false, true, false, false, true, false, true, false, true, false];

  var FLAT_PITCH_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"];

  function getKeyAccidentals(keyStr) {
    if (!keyStr || typeof keyStr !== "string") return {};
    var clean = keyStr.trim();
    var m = clean.match(/^([A-Ga-g])([#b]?)\s*(mix(?:olydian)?|dor(?:ian)?|lyd(?:ian)?|phr(?:ygian)?|loc(?:rian)?|maj(?:or)?|ion(?:ian)?|aeo(?:lian)?|min(?:or)?|m(?![a-z]))?/i);
    if (!m) return {};
    var letter = m[1].toUpperCase();
    var acc = m[2] || "";
    var modeStr = (m[3] || "").toLowerCase();

    var FIFTHS = { "F": -1, "C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5 };
    if (FIFTHS[letter] === undefined) return {};
    var fifth = FIFTHS[letter];
    if (acc === "#") fifth += 7;
    if (acc === "b") fifth -= 7;

    var offset = 0;
    if ((modeStr === "m" || modeStr.startsWith("min") || modeStr.startsWith("aeo")) && !modeStr.startsWith("maj") && !modeStr.startsWith("mix")) {
      offset = -3;
    } else if (modeStr.startsWith("dor")) {
      offset = -2;
    } else if (modeStr.startsWith("mix")) {
      offset = -1;
    } else if (modeStr.startsWith("lyd")) {
      offset = 1;
    } else if (modeStr.startsWith("phr")) {
      offset = -4;
    } else if (modeStr.startsWith("loc")) {
      offset = -5;
    }

    var sharps = fifth + offset;
    var SHARP_ORDER = "FCGDAEB";
    var FLAT_ORDER  = "BEADGCF";
    var res = {};
    if (sharps > 0) {
      var count = Math.min(sharps, 7);
      for (var i = 0; i < count; i++) {
        res[SHARP_ORDER.charAt(i)] = 1;
      }
    } else if (sharps < 0) {
      var count = Math.min(-sharps, 7);
      for (var j = 0; j < count; j++) {
        res[FLAT_ORDER.charAt(j)] = -1;
      }
    }
    return res;
  }

  var KEY_ACCIDENTALS = {
    'C': { flats: false }, 'G': { flats: false }, 'D': { flats: false }, 'A': { flats: false },
    'E': { flats: false }, 'B': { flats: false }, 'F#': { flats: false },
    'F': { flats: true }, 'Bb': { flats: true }, 'Eb': { flats: true },
    'Ab': { flats: true }, 'Db': { flats: true }, 'Gb': { flats: true },
    'Am': { flats: false }, 'Em': { flats: false }, 'Bm': { flats: false }, 'F#m': { flats: false },
    'Dm': { flats: true }, 'Gm': { flats: true }, 'Cm': { flats: true }, 'Fm': { flats: true }
  };

  var SHARP_NAMES = ["C", "^C", "D", "^D", "E", "F", "^F", "G", "^G", "A", "^A", "B"];
  var FLAT_NAMES  = ["C", "_D", "D", "_E", "E", "F", "_G", "G", "_A", "A", "_B", "B"];

  function isFlatKey(key) {
    if (!key) return false;
    if (KEY_ACCIDENTALS[key] && KEY_ACCIDENTALS[key].flats !== undefined) {
      return KEY_ACCIDENTALS[key].flats;
    }
    var accs = getKeyAccidentals(key);
    for (var k in accs) {
      if (accs[k] < 0) return true;
    }
    return false;
  }

  function midiToNoteName(pitch, key) {
    var semitone = ((pitch % 12) + 12) % 12;
    var octave = Math.floor(pitch / 12) - 1;
    var names = isFlatKey(key) ? FLAT_PITCH_NAMES : PITCH_NAMES;
    return names[semitone] + octave;
  }

  function escapeHtml(str) {
    if (!str) { return ''; }
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function midiToAbcNote(pitch, key) {
    var keyAccs = key ? getKeyAccidentals(key) : {};
    var isFlat = isFlatKey(key);
    var names = isFlat ? FLAT_NAMES : SHARP_NAMES;
    var oct = Math.floor(pitch / 12) - 1;
    var semitone = ((pitch % 12) + 12) % 12;
    var rawName = names[semitone];
    
    var acc = "";
    var letter = rawName;
    if (rawName.charAt(0) === '^' || rawName.charAt(0) === '_') {
      acc = rawName.charAt(0);
      letter = rawName.slice(1);
    } else if (keyAccs[rawName] !== undefined && keyAccs[rawName] !== 0) {
      // The note is natural on the keyboard, but the key signature has an accidental on this letter
      acc = "=";
    }

    var noteBody = "";
    if (oct < 4) {
      noteBody = letter;
      for (var i = 0; i < 4 - oct; i++) { noteBody += ","; }
    } else if (oct === 4) {
      noteBody = letter;
    } else if (oct === 5) {
      noteBody = letter.toLowerCase();
    } else {
      noteBody = letter.toLowerCase();
      for (var j = 0; j < oct - 5; j++) { noteBody += "'"; }
    }
    return acc + noteBody;
  }

  function abcNoteToMidi(accidental, letter, octaves, keyAccidentals, measureAccidentals) {
    var baseMap = { C: 60, D: 62, E: 64, F: 65, G: 67, A: 69, B: 71 };
    var isLower = letter === letter.toLowerCase();
    var upperLetter = letter.toUpperCase();
    var base = baseMap[upperLetter];
    if (base === undefined) { base = 60; }
    var oct = isLower ? 5 : 4;
    if (octaves) {
      for (var i = 0; i < octaves.length; i++) {
        var ch = octaves.charAt(i);
        if (ch === "'") { oct++; }
        else if (ch === ",") { oct--; }
      }
    }
    base += (oct - 4) * 12;

    var shift = 0;
    if (accidental && accidental.length > 0) {
      if (accidental.indexOf('=') !== -1) {
        shift = 0;
      } else {
        for (var j = 0; j < accidental.length; j++) {
          var a = accidental.charAt(j);
          if (a === '^') { shift += 1; }
          else if (a === '_') { shift -= 1; }
        }
      }
      if (measureAccidentals) {
        var octKey = upperLetter + '_' + oct;
        measureAccidentals[octKey] = shift;
        measureAccidentals[upperLetter] = shift;
      }
    } else {
      var octKey = upperLetter + '_' + oct;
      if (measureAccidentals && measureAccidentals[octKey] !== undefined) {
        shift = measureAccidentals[octKey];
      } else if (measureAccidentals && measureAccidentals[upperLetter] !== undefined) {
        shift = measureAccidentals[upperLetter];
      } else if (keyAccidentals && keyAccidentals[upperLetter] !== undefined) {
        shift = keyAccidentals[upperLetter];
      }
    }

    return base + shift;
  }

  /* ---------------------------------------------------- Web Audio Synth */
  var audioCtx = null;
  function getAudioContext() {
    if (typeof window === 'undefined') { return null; }
    if (!audioCtx) {
      var AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        audioCtx = new AudioContextClass();
      }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume().catch(function () {});
    }
    return audioCtx;
  }

  var activeOscillators = [];

  function stopAllAudio() {
    for (var i = 0; i < activeOscillators.length; i++) {
      try {
        activeOscillators[i].stop();
        activeOscillators[i].disconnect();
      } catch (err) {}
    }
    activeOscillators = [];
  }

  function midiToFreq(pitch) {
    return 440 * Math.pow(2, (pitch - 69) / 12);
  }

  var currentInstrument = 'acoustic_grand_piano';
  var sampleCache = {};
  var pendingFetches = {};
  var FLATS_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];

  function clampPitch(pitch) {
    if (typeof pitch !== 'number' || isNaN(pitch)) return 60;
    return Math.max(21, Math.min(108, Math.round(pitch)));
  }

  function midiToSampleName(pitch) {
    if (typeof pitch !== 'number' || isNaN(pitch)) return null;
    var clamped = clampPitch(pitch);
    var name = FLATS_NAMES[clamped % 12];
    var octave = Math.floor(clamped / 12) - 1;
    return name + octave;
  }

  function loadSamplePromise(instrument, noteName) {
    if (!instrument || !noteName || instrument === 'synth') return Promise.resolve(null);
    var key = instrument + '_' + noteName;
    if (sampleCache[key]) return Promise.resolve(sampleCache[key]);
    var ctx = getAudioContext();
    if (!ctx || typeof fetch === 'undefined') return Promise.resolve(null);

    if (pendingFetches[key]) {
      return pendingFetches[key];
    }

    var url = '/soundfonts/' + instrument + '-mp3/' + encodeURIComponent(noteName) + '.mp3';
    pendingFetches[key] = fetch(url)
      .then(function (res) { return res && res.ok ? res.arrayBuffer() : null; })
      .then(function (buf) {
        if (!buf) return null;
        return ctx.decodeAudioData(buf);
      })
      .then(function (decoded) {
        if (decoded) { sampleCache[key] = decoded; }
        return decoded;
      })
      .catch(function () { return null; })
      .finally(function () { delete pendingFetches[key]; });

    return pendingFetches[key];
  }

  function getOrPreloadSample(instrument, noteName) {
    if (!instrument || !noteName || instrument === 'synth') return null;
    var key = instrument + '_' + noteName;
    if (sampleCache[key]) { return sampleCache[key]; }
    loadSamplePromise(instrument, noteName);
    return null;
  }

  function preloadSamplesForNotes(items, instrument) {
    var inst = instrument || currentInstrument;
    if (inst === 'synth' || !items || !items.length) return Promise.resolve();
    var promises = [];
    var seen = {};
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      var pitch = (typeof item === 'number') ? item : (item ? item.pitch : null);
      if (typeof pitch !== 'number' || isNaN(pitch)) continue;
      var clamped = clampPitch(pitch);
      var name = midiToSampleName(clamped);
      if (name && !seen[name]) {
        seen[name] = true;
        promises.push(loadSamplePromise(inst, name));
      }
    }
    return Promise.all(promises);
  }

  function getAllModelPitches(model) {
    if (!model) return [];
    var pitches = [];
    if (model.notes) {
      for (var i = 0; i < model.notes.length; i++) {
        if (typeof model.notes[i].pitch === 'number') {
          pitches.push(model.notes[i].pitch);
        }
      }
    }
    if (model.chords) {
      for (var c = 0; c < model.chords.length; c++) {
        var chPitches = chordToMidiPitches(model.chords[c].name);
        for (var p = 0; p < chPitches.length; p++) {
          pitches.push(chPitches[p]);
        }
      }
    }
    return pitches;
  }

  function playTone(pitch, durationSec, voiceType, startTime, instrumentOverride) {
    var ctx = getAudioContext();
    if (!ctx) { return null; }
    var now = startTime !== undefined ? startTime : ctx.currentTime;
    var dur = durationSec || 0.25;

    var inst = instrumentOverride || currentInstrument;
    var clamped = clampPitch(pitch);
    var sampleName = midiToSampleName(clamped);
    var cachedBuf = (inst !== 'synth' && sampleName)
      ? (sampleCache[inst + '_' + sampleName] || getOrPreloadSample(inst, sampleName))
      : null;

    if (cachedBuf) {
      try {
        var src = ctx.createBufferSource();
        src.buffer = cachedBuf;
        if (pitch !== clamped) {
          src.playbackRate.setValueAtTime(Math.pow(2, (pitch - clamped) / 12), now);
        }
        var gain = ctx.createGain();
        var peakVol = (voiceType === 'Vocal') ? 0.35 : 0.26;
        gain.gain.setValueAtTime(peakVol, now);
        if (dur < cachedBuf.duration) {
          gain.gain.setValueAtTime(peakVol, now + dur);
          gain.gain.exponentialRampToValueAtTime(0.0001, now + dur + 0.08);
        } else {
          gain.gain.setValueAtTime(peakVol, now + cachedBuf.duration - 0.05);
          gain.gain.exponentialRampToValueAtTime(0.0001, now + cachedBuf.duration);
        }
        src.connect(gain);
        gain.connect(ctx.destination);
        src.start(now);
        src.stop(now + Math.min(cachedBuf.duration, dur + 0.1));
        activeOscillators.push(src);
        src.onended = function () {
          var idx = activeOscillators.indexOf(src);
          if (idx !== -1) { activeOscillators.splice(idx, 1); }
        };
        return src;
      } catch (err) {}
    }

    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    var filter = ctx.createBiquadFilter();


    osc.type = voiceType === 'Ins' ? 'sawtooth' : 'triangle';
    osc.frequency.setValueAtTime(midiToFreq(pitch), now);

    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(voiceType === 'Ins' ? 1400 : 2400, now);

    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.25, now + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.15, now + Math.min(0.08, dur * 0.5));
    gain.gain.exponentialRampToValueAtTime(0.0001, now + dur);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + dur + 0.04);

    activeOscillators.push(osc);
    osc.onended = function () {
      var idx = activeOscillators.indexOf(osc);
      if (idx !== -1) { activeOscillators.splice(idx, 1); }
    };
    return osc;
  }

  function playClick(isDownbeat, startTime) {
    var ctx = getAudioContext();
    if (!ctx) { return null; }
    var now = startTime !== undefined ? startTime : ctx.currentTime;
    var osc = ctx.createOscillator();
    var gain = ctx.createGain();

    var freq = isDownbeat ? 1400 : 900;
    var dur = isDownbeat ? 0.035 : 0.025;
    var vol = isDownbeat ? 0.28 : 0.16;

    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, now);
    osc.frequency.exponentialRampToValueAtTime(freq * 0.5, now + dur);

    gain.gain.setValueAtTime(vol, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + dur);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + dur + 0.01);

    activeOscillators.push(osc);
    osc.onended = function () {
      var idx = activeOscillators.indexOf(osc);
      if (idx !== -1) { activeOscillators.splice(idx, 1); }
    };
    return osc;
  }

  var NOTE_SEMITONES = {
    'C': 0, 'C#': 1, 'DB': 1, 'D': 2, 'D#': 3, 'EB': 3,
    'E': 4, 'F': 5, 'F#': 6, 'GB': 6, 'G': 7, 'G#': 8,
    'AB': 8, 'A': 9, 'A#': 10, 'BB': 10, 'B': 11
  };

  function chordToMidiPitches(chordName) {
    if (!chordName || typeof chordName !== 'string') { return []; }
    var clean = chordName.trim().replace(/^["\(\)]+|["\(\)]+$/g, '');
    if (!clean) { return []; }

    var slashBass = null;
    var slashIdx = clean.indexOf('/');
    if (slashIdx !== -1) {
      slashBass = clean.slice(slashIdx + 1).trim().toUpperCase();
      clean = clean.slice(0, slashIdx).trim();
    }

    var match = clean.match(/^([A-Ga-g][#b]?)(.*)$/);
    if (!match) { return []; }
    var rootStr = match[1].toUpperCase();
    var qual = match[2].toLowerCase();

    var rootSemi = NOTE_SEMITONES[rootStr];
    if (rootSemi === undefined) { return []; }

    var baseMidi = 48 + rootSemi;
    var intervals = [0, 4, 7];

    if (qual.startsWith('m7') || qual.startsWith('min7')) {
      intervals = [0, 3, 7, 10];
    } else if (qual.startsWith('maj7') || qual.startsWith('m7+')) {
      intervals = [0, 4, 7, 11];
    } else if (qual.startsWith('m') && !qual.startsWith('maj')) {
      intervals = [0, 3, 7];
    } else if (qual.startsWith('7')) {
      intervals = [0, 4, 7, 10];
    } else if (qual.startsWith('dim') || qual.startsWith('o')) {
      intervals = [0, 3, 6];
    } else if (qual.startsWith('aug') || qual.startsWith('+')) {
      intervals = [0, 4, 8];
    } else if (qual.startsWith('sus4') || qual.startsWith('sus')) {
      intervals = [0, 5, 7];
    } else if (qual.startsWith('sus2')) {
      intervals = [0, 2, 7];
    }

    var pitches = intervals.map(function (iv) { return baseMidi + iv; });
    var bassSemi = rootSemi;
    if (slashBass && NOTE_SEMITONES[slashBass] !== undefined) {
      bassSemi = NOTE_SEMITONES[slashBass];
    }
    pitches.unshift(36 + bassSemi);
    return pitches;
  }

  function playChord(pitches, durationSec, startTime) {
    var ctx = getAudioContext();
    if (!ctx || !pitches || pitches.length === 0) { return []; }
    var now = startTime !== undefined ? startTime : ctx.currentTime;
    var dur = durationSec || 1.0;
    var nodes = [];
    var inst = (currentInstrument === 'synth') ? 'synth' : (currentInstrument || 'acoustic_grand_piano');

    for (var i = 0; i < pitches.length; i++) {
      var pitch = pitches[i];
      var isBass = (i === 0);
      var clamped = clampPitch(pitch);
      var sampleName = midiToSampleName(clamped);
      var cachedBuf = (inst !== 'synth' && sampleName)
        ? (sampleCache[inst + '_' + sampleName] || getOrPreloadSample(inst, sampleName))
        : null;

      if (cachedBuf) {
        try {
          var src = ctx.createBufferSource();
          src.buffer = cachedBuf;
          if (pitch !== clamped) {
            src.playbackRate.setValueAtTime(Math.pow(2, (pitch - clamped) / 12), now);
          }
          var gainNode = ctx.createGain();
          var pVol = isBass ? 0.22 : (0.16 / Math.max(1, pitches.length - 1));
          gainNode.gain.setValueAtTime(pVol, now);
          gainNode.gain.setValueAtTime(pVol, now + dur);
          gainNode.gain.exponentialRampToValueAtTime(0.0001, now + dur + 0.12);
          src.connect(gainNode);
          gainNode.connect(ctx.destination);
          src.start(now);
          src.stop(now + Math.min(cachedBuf.duration, dur + 0.15));
          activeOscillators.push(src);
          nodes.push(src);
          (function (s) {
            s.onended = function () {
              var idx = activeOscillators.indexOf(s);
              if (idx !== -1) { activeOscillators.splice(idx, 1); }
            };
          })(src);
          continue;
        } catch (err) {}
      }

      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      var filter = ctx.createBiquadFilter();

      osc.type = isBass ? 'triangle' : 'sine';
      osc.frequency.setValueAtTime(midiToFreq(pitch), now);

      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(isBass ? 450 : 900, now);

      var peakVol = isBass ? 0.11 : (0.07 / Math.max(1, pitches.length - 1));
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(peakVol, now + 0.04);
      gain.gain.exponentialRampToValueAtTime(peakVol * 0.7, now + Math.min(0.2, dur * 0.4));
      gain.gain.exponentialRampToValueAtTime(0.0001, now + dur);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + dur + 0.05);

      activeOscillators.push(osc);
      nodes.push(osc);
      (function (o) {
        o.onended = function () {
          var idx = activeOscillators.indexOf(o);
          if (idx !== -1) { activeOscillators.splice(idx, 1); }
        };
      })(osc);
    }
    return nodes;
  }

  /* ---------------------------------------------------- ABC Parser */
  function parseAbc(abcText) {
    var lines = (abcText || "").split(/\r?\n/);
    var headers = [];
    var sections = [];
    var voices = [];
    var chords = [];
    var rawNotes = [];
    
    var key = "C";
    var currentVoice = "Vocal";
    var voiceBarIndex = {};
    var ticksPerBar = 16;
    var unitLength = 16;
    var meterNum = 4;
    var meterDen = 4;
    var bpm = 120;
    var inHeader = true;

    var currentKey = "C";
    var voiceKey = {};
    var voiceMeasureAccidentals = {};
    var voiceTieCarry = {};

    var tokenRe = /"([^"]*)"|([zZ])(\d*)|\[([A-Ga-g,=_^'\/\d\s]+)\](\d*)(-?)|([_^=]*[A-Ga-g][,']*)(\d*)(-?)|(\|)|\[K:\s*([^\]]+)\]/g;
    var nextId = 1;
    var lastMusicVoice = null;
    var lastMusicBars = null;

    for (var lineIndex = 0; lineIndex < lines.length; lineIndex++) {
      var raw = lines[lineIndex].trim();
      if (!raw) { continue; }

      if (raw.charAt(0) === "%") {
        inHeader = false;
        var currentBar = (voiceBarIndex["Vocal"] !== undefined) ? voiceBarIndex["Vocal"] : (voiceBarIndex[currentVoice] || 0);
        sections.push({ barIndex: currentBar, text: raw });
        lastMusicBars = null;
        continue;
      }

      if (raw.indexOf("V:") === 0) {
        var vMatch = raw.match(/^V:\s*(\S+)/);
        if (vMatch) {
          currentVoice = vMatch[1];
          if (voices.indexOf(currentVoice) === -1) { voices.push(currentVoice); }
          if (voiceBarIndex[currentVoice] === undefined) { voiceBarIndex[currentVoice] = 0; }
        }
        lastMusicBars = null;
        continue;
      }

      if (/^[A-Za-z]:/.test(raw) && raw.indexOf("V:") !== 0 && raw.indexOf("w:") !== 0 && raw.indexOf("W:") !== 0) {
        if (raw.indexOf("K:") === 0) {
          var km = raw.match(/^K:\s*([A-Ga-g][#b]?(?:mix|dor|lyd|phr|loc|maj|ion|aeo|min|m)?)/i);
          if (km) {
            currentKey = km[1];
            voiceKey[currentVoice] = currentKey;
            voiceMeasureAccidentals[currentVoice] = {};
            if (inHeader) {
              key = currentKey;
              headers.push(raw);
              inHeader = false;
              for (var vi = 0; vi < voices.length; vi++) {
                voiceKey[voices[vi]] = currentKey;
              }
            }
          }
          lastMusicBars = null;
          continue;
        }
        if (inHeader) {
          headers.push(raw);
        }
        if (raw.indexOf("Q:") === 0 && inHeader) {
          var qm = raw.match(/^Q:\s*(?:(\d+)\/(\d+)=)?(\d+)/);
          if (qm) {
            if (qm[1] && qm[2]) {
              bpm = Math.round(parseInt(qm[3], 10) * (parseInt(qm[1], 10) * 4 / parseInt(qm[2], 10)));
            } else {
              bpm = parseInt(qm[3], 10);
            }
          }
        }
        if (raw.indexOf("L:") === 0 && inHeader) {
          var lm = raw.match(/^L:\s*1\/(\d+)/);
          if (lm) {
            unitLength = parseInt(lm[1], 10);
            ticksPerBar = Math.round(meterNum * (unitLength / meterDen));
          }
        }
        if (raw.indexOf("M:") === 0 && inHeader) {
          var mm = raw.match(/^M:\s*(\d+)\/(\d+)/);
          if (mm) {
            meterNum = parseInt(mm[1], 10);
            meterDen = parseInt(mm[2], 10);
          } else if (/^M:\s*C\|/.test(raw)) {
            meterNum = 2; meterDen = 2;
          } else if (/^M:\s*C/.test(raw)) {
            meterNum = 4; meterDen = 4;
          }
          ticksPerBar = Math.round(meterNum * (unitLength / meterDen));
        }
        lastMusicBars = null;
        continue;
      }

      if (raw.indexOf("w:") === 0 || raw.indexOf("W:") === 0) {
        if (lastMusicBars && lastMusicVoice) {
          var barChunks = raw.slice(2).trim().split('|');
          if (barChunks.length > 1 && barChunks[barChunks.length - 1].trim() === '') {
            barChunks.pop();
          }
          for (var cIdx = 0; cIdx < barChunks.length; cIdx++) {
            var barNum = lastMusicBars.start + cIdx;
            if (barNum >= lastMusicBars.end) { break; }
            var chunkText = barChunks[cIdx];
            var tokRe = /([^\s-]+-?|\*|_)/g;
            var tokens = [];
            var tm;
            while ((tm = tokRe.exec(chunkText)) !== null) {
              var tok = tm[1].trim();
              if (tok && tok !== '-') {
                tokens.push(tok);
              }
            }
            var barNotes = rawNotes.filter(function (rn) {
              return rn.voice === lastMusicVoice && rn.barIndex === barNum;
            });
            barNotes.sort(function (a, b) { return a.tickInBar - b.tickInBar; });
            for (var bnIdx = 0; bnIdx < barNotes.length && bnIdx < tokens.length; bnIdx++) {
              var tVal = tokens[bnIdx];
              if (tVal === '*' || tVal === '_') {
                barNotes[bnIdx].lyric = '';
              } else {
                barNotes[bnIdx].lyric = tVal;
              }
            }
          }
        }
        continue;
      }

      if (voiceBarIndex[currentVoice] === undefined) { voiceBarIndex[currentVoice] = 0; }
      var effectiveKey = voiceKey[currentVoice] || currentKey || key || "C";
      var activeKeyAccs = getKeyAccidentals(effectiveKey);
      if (!voiceMeasureAccidentals[currentVoice]) {
        voiceMeasureAccidentals[currentVoice] = {};
      }
      var activeMeasureAccs = voiceMeasureAccidentals[currentVoice];

      var musicLineStartBar = voiceBarIndex[currentVoice];
      var tickInBar = 0;
      var sawZ = false;

      var match;
      tokenRe.lastIndex = 0;
      while ((match = tokenRe.exec(raw)) !== null) {
        if (match[1]) {
          sawZ = false;
          chords.push({
            voice: currentVoice,
            barIndex: voiceBarIndex[currentVoice],
            tickInBar: tickInBar,
            name: match[1]
          });
        } else if (match[2]) {
          var restType = match[2];
          if (restType === "Z") {
            var count = parseInt(match[3] || "1", 10);
            voiceBarIndex[currentVoice] += count;
            tickInBar = 0;
            sawZ = true;
          } else {
            var rDur = parseInt(match[3] || "1", 10);
            tickInBar += rDur;
            sawZ = false;
          }
        } else if (match[4]) {
          sawZ = false;
          var chordStr = match[4];
          var cDur = parseInt(match[5] || "1", 10);
          var tiedNext = match[6] === "-";
          var chordNoteRe = /([_^=]*[A-Ga-g][,']*)(\d*)/g;
          var cMatch;
          while ((cMatch = chordNoteRe.exec(chordStr)) !== null) {
            if (!cMatch[1]) { continue; }
            var noteParts = cMatch[1].match(/^([_^=]*)([A-Ga-g])([,']*)$/);
            if (noteParts) {
              var pitch = abcNoteToMidi(noteParts[1], noteParts[2], noteParts[3], activeKeyAccs, activeMeasureAccs);
              var nDur = cMatch[2] ? parseInt(cMatch[2], 10) : cDur;
              rawNotes.push({
                id: nextId++,
                voice: currentVoice,
                pitch: pitch,
                barIndex: voiceBarIndex[currentVoice],
                tickInBar: tickInBar,
                durationTicks: nDur,
                tiedNext: tiedNext,
                lyric: ''
              });
            }
          }
          tickInBar += cDur;
        } else if (match[7]) {
          sawZ = false;
          var noteStr = match[7];
          var nDur = parseInt(match[8] || "1", 10);
          var tiedNext = match[9] === "-";

          var noteParts = noteStr.match(/^([_^=]*)([A-Ga-g])([,']*)$/);
          if (noteParts) {
            var oct = (noteParts[2] === noteParts[2].toLowerCase()) ? 5 : 4;
            if (noteParts[3]) {
              for (var oi = 0; oi < noteParts[3].length; oi++) {
                if (noteParts[3].charAt(oi) === "'") oct++;
                else if (noteParts[3].charAt(oi) === ",") oct--;
              }
            }
            var upperLetter = noteParts[2].toUpperCase();
            var carry = voiceTieCarry[currentVoice];
            var pitch;
            if (!noteParts[1] && carry && carry.letter === upperLetter && carry.octave === oct) {
              pitch = carry.pitch;
            } else {
              pitch = abcNoteToMidi(noteParts[1], noteParts[2], noteParts[3], activeKeyAccs, activeMeasureAccs);
            }
            if (tiedNext) {
              voiceTieCarry[currentVoice] = { letter: upperLetter, octave: oct, pitch: pitch };
            } else {
              voiceTieCarry[currentVoice] = null;
            }

            rawNotes.push({
              id: nextId++,
              voice: currentVoice,
              pitch: pitch,
              barIndex: voiceBarIndex[currentVoice],
              tickInBar: tickInBar,
              durationTicks: nDur,
              tiedNext: tiedNext,
              lyric: ''
            });
          }
          tickInBar += nDur;
        } else if (match[10]) {
          if (sawZ) {
            sawZ = false;
          } else {
            voiceBarIndex[currentVoice] += 1;
          }
          tickInBar = 0;
          voiceMeasureAccidentals[currentVoice] = {};
          activeMeasureAccs = voiceMeasureAccidentals[currentVoice];
        } else if (match[11]) {
          currentKey = match[11].trim();
          voiceKey[currentVoice] = currentKey;
          activeKeyAccs = getKeyAccidentals(currentKey);
          voiceMeasureAccidentals[currentVoice] = {};
          activeMeasureAccs = voiceMeasureAccidentals[currentVoice];
        }
      }

      lastMusicVoice = currentVoice;
      lastMusicBars = { start: musicLineStartBar, end: voiceBarIndex[currentVoice] };
    }

    rawNotes.sort(function (a, b) {
      if (a.voice !== b.voice) { return a.voice.localeCompare(b.voice); }
      var aTick = a.barIndex * ticksPerBar + a.tickInBar;
      var bTick = b.barIndex * ticksPerBar + b.tickInBar;
      if (aTick !== bTick) { return aTick - bTick; }
      return a.pitch - b.pitch;
    });

    var notes = [];
    for (var i = 0; i < rawNotes.length; i++) {
      var rn = rawNotes[i];
      var absTick = rn.barIndex * ticksPerBar + rn.tickInBar;
      
      if (notes.length > 0) {
        var prev = notes[notes.length - 1];
        if (prev.voice === rn.voice && prev.pitch === rn.pitch && prev._tiedNext && (prev.startTick + prev.durationTicks === absTick)) {
          prev.durationTicks += rn.durationTicks;
          prev._tiedNext = rn.tiedNext;
          if (!prev.lyric && rn.lyric) { prev.lyric = rn.lyric; }
          continue;
        }
      }

      notes.push({
        id: rn.id,
        voice: rn.voice,
        pitch: rn.pitch,
        startTick: absTick,
        durationTicks: rn.durationTicks,
        lyric: rn.lyric || '',
        _tiedNext: rn.tiedNext
      });
    }

    for (var k = 0; k < notes.length; k++) {
      delete notes[k]._tiedNext;
    }

    if (voices.indexOf("Vocal") === -1) { voices.push("Vocal"); }
    if (voices.indexOf("Ins") === -1) { voices.push("Ins"); }

    return {
      headers: headers,
      key: key,
      bpm: bpm,
      meterNum: meterNum,
      meterDen: meterDen,
      meter: meterNum + "/" + meterDen,
      ticksPerBar: ticksPerBar,
      unitLength: unitLength,
      voices: voices,
      sections: sections,
      chords: chords,
      notes: notes
    };
  }

  /* ---------------------------------------------------- ABC Serializer */
  function serializeToAbc(model) {
    var lines = [];
    var ticksPerBar = model.ticksPerBar || 16;
    var key = model.key || "C";

    for (var h = 0; h < model.headers.length; h++) {
      lines.push(model.headers[h]);
    }

    if (!model.headers.some(function (x) { return /^V:\s*Vocal\b/.test(x); })) {
      lines.push('V: Vocal clef=treble name="Vocal Melody" snm="Vocal"');
    }
    if (!model.headers.some(function (x) { return /^V:\s*Ins\b/.test(x); })) {
      lines.push('V: Ins clef=treble name="Ins Melody" snm="Inst."');
    }
    if (!model.headers.some(function (x) { return /^K:/.test(x); })) {
      lines.push('K:' + key);
    }

    var maxBar = 3;
    for (var n = 0; n < model.notes.length; n++) {
      var note = model.notes[n];
      var endBar = Math.floor((note.startTick + note.durationTicks - 1) / ticksPerBar);
      if (endBar > maxBar) { maxBar = endBar; }
    }
    for (var c = 0; c < model.chords.length; c++) {
      if (model.chords[c].barIndex > maxBar) { maxBar = model.chords[c].barIndex; }
    }
    for (var s = 0; s < model.sections.length; s++) {
      if (model.sections[s].barIndex > maxBar) { maxBar = model.sections[s].barIndex; }
    }

    var voiceList = (model.voices && model.voices.length > 0) ? model.voices.slice() : ['Vocal', 'Ins'];
    if (voiceList.indexOf('Vocal') === -1) { voiceList.unshift('Vocal'); }
    if (voiceList.indexOf('Ins') === -1) { voiceList.push('Ins'); }
    for (var nIdx = 0; nIdx < model.notes.length; nIdx++) {
      var nVoice = model.notes[nIdx].voice || 'Vocal';
      if (voiceList.indexOf(nVoice) === -1) {
        voiceList.push(nVoice);
      }
    }

    var barSegments = {};
    for (var vIdx = 0; vIdx < voiceList.length; vIdx++) {
      var vName = voiceList[vIdx];
      barSegments[vName] = {};
      for (var b = 0; b <= maxBar; b++) {
        barSegments[vName][b] = [];
      }
    }

    for (var m = 0; m < model.notes.length; m++) {
      var curNote = model.notes[m];
      var remDur = curNote.durationTicks;
      var curTick = curNote.startTick;

      while (remDur > 0) {
        var bIndex = Math.floor(curTick / ticksPerBar);
        var tInBar = curTick % ticksPerBar;
        var spaceInBar = ticksPerBar - tInBar;
        var segDur = Math.min(remDur, spaceInBar);
        var isTied = remDur > segDur;

        if (!barSegments[curNote.voice]) { barSegments[curNote.voice] = {}; }
        if (!barSegments[curNote.voice][bIndex]) { barSegments[curNote.voice][bIndex] = []; }

        barSegments[curNote.voice][bIndex].push({
          tickInBar: tInBar,
          durationTicks: segDur,
          pitch: curNote.pitch,
          tied: isTied,
          lyric: (curTick === curNote.startTick) ? (curNote.lyric || '') : (curNote.lyric ? '_' : '')
        });

        remDur -= segDur;
        curTick += segDur;
      }
    }

    var sortedSections = model.sections.slice().sort(function (a, b) { return a.barIndex - b.barIndex; });
    if (sortedSections.length === 0) {
      sortedSections.push({ barIndex: 0, text: "% intro" });
    } else if (sortedSections[0].barIndex > 0) {
      sortedSections.unshift({ barIndex: 0, text: "% intro" });
    }

    var sectionIntervals = [];
    for (var si = 0; si < sortedSections.length; si++) {
      var secItem = sortedSections[si];
      var nextStart = (si + 1 < sortedSections.length) ? sortedSections[si + 1].barIndex : (maxBar + 1);
      sectionIntervals.push({
        text: secItem.text,
        startBar: secItem.barIndex,
        endBar: Math.max(secItem.barIndex + 1, nextStart)
      });
    }

    for (var intIdx = 0; intIdx < sectionIntervals.length; intIdx++) {
      var sec = sectionIntervals[intIdx];
      lines.push(sec.text);

      for (var vi = 0; vi < voiceList.length; vi++) {
        var voiceName = voiceList[vi];
        lines.push('V: ' + voiceName);
        var barBuffer = [];
        var lyricBarBuffer = [];

        for (var barNum = sec.startBar; barNum < sec.endBar && barNum <= maxBar; barNum++) {
          var segs = (barSegments[voiceName] && barSegments[voiceName][barNum]) ? barSegments[voiceName][barNum] : [];
          segs.sort(function (a, b) { return a.tickInBar - b.tickInBar; });

          var barChords = model.chords.filter(function (ch) {
            return ch.barIndex === barNum && (ch.voice === voiceName || (!ch.voice && voiceName === "Vocal"));
          });
          var chordMap = {};
          for (var ci = 0; ci < barChords.length; ci++) {
            chordMap[barChords[ci].tickInBar] = barChords[ci].name;
          }

          var curBarTick = 0;
          var barStr = "";

          if (segs.length === 0) {
            if (chordMap[0]) { barStr += '"' + chordMap[0] + '"'; }
            barStr += 'z' + ticksPerBar;
          } else {
            var byTick = {};
            for (var segIdx = 0; segIdx < segs.length; segIdx++) {
              var s = segs[segIdx];
              if (!byTick[s.tickInBar]) { byTick[s.tickInBar] = []; }
              byTick[s.tickInBar].push(s);
            }
            var sortedTicks = Object.keys(byTick).map(Number).sort(function (a, b) { return a - b; });

            for (var ti = 0; ti < sortedTicks.length; ti++) {
              var tVal = sortedTicks[ti];
              var group = byTick[tVal];
              if (tVal > curBarTick) {
                var rDur = tVal - curBarTick;
                if (chordMap[curBarTick]) { barStr += '"' + chordMap[curBarTick] + '"'; }
                barStr += 'z' + (rDur > 1 ? rDur : "");
                curBarTick = tVal;
              }
              if (chordMap[curBarTick]) {
                barStr += '"' + chordMap[curBarTick] + '"';
              }
              var dur = group[0].durationTicks;
              var dStr = dur > 1 ? String(dur) : "";
              var tStr = group[0].tied ? "-" : "";
              if (group.length === 1) {
                var nStr = midiToAbcNote(group[0].pitch, key);
                barStr += nStr + dStr + tStr;
              } else {
                group.sort(function (a, b) { return a.pitch - b.pitch; });
                var chordPitches = group.map(function (g) { return midiToAbcNote(g.pitch, key); }).join("");
                barStr += "[" + chordPitches + "]" + dStr + tStr;
              }
              curBarTick += dur;
            }
            if (curBarTick < ticksPerBar) {
              var endRest = ticksPerBar - curBarTick;
              if (chordMap[curBarTick]) { barStr += '"' + chordMap[curBarTick] + '"'; }
              barStr += 'z' + (endRest > 1 ? endRest : "");
            }
          }

          barBuffer.push(barStr);

          if (voiceName === "Vocal") {
            var barLyricTokens = [];
            for (var si = 0; si < segs.length; si++) {
              var segItem = segs[si];
              if (segItem.lyric) {
                barLyricTokens.push(segItem.lyric);
              } else {
                barLyricTokens.push("*");
              }
            }
            while (barLyricTokens.length > 0 && barLyricTokens[barLyricTokens.length - 1] === "*") {
              barLyricTokens.pop();
            }
            lyricBarBuffer.push(barLyricTokens.join(" "));
          }

          if (barBuffer.length === 4 || barNum === sec.endBar - 1 || barNum === maxBar) {
            lines.push(barBuffer.join(" | ") + " |");
            barBuffer = [];

            if (voiceName === "Vocal") {
              var hasAnyLyrics = lyricBarBuffer.some(function (bTxt) { return bTxt.length > 0; });
              if (hasAnyLyrics) {
                lines.push("w: " + lyricBarBuffer.join(" | ") + " |");
              }
              lyricBarBuffer = [];
            }
          }
        }
      }
    }

    return lines.join("\n") + "\n";
  }

  /* ---------------------------------------------------- PianoRoll Controller */
  var PianoRoll = {
    model: null,
    currentVoice: "Vocal",
    ghostOther: true,
    snapTicks: 1, // 1 = 1/16, 2 = 1/8, 4 = 1/4
    tickWidth: TICK_WIDTH,
    rowHeight: ROW_HEIGHT,
    selectedNoteId: null,
    selectedNoteIds: [],
    metronomeEnabled: true,
    chordsEnabled: true,
    isPlaying: false,
    playheadTick: 0,
    playTimer: null,
    playStartTime: 0,
    playStartTick: 0,
    listeners: [],
    initialized: false,

    ensureToolbar: function () {
      if (typeof document === 'undefined') { return; }
      var self = this;

      // Ensure selection buttons exist in toolbar
      var selectAllBtn = document.getElementById('roll-select-all');
      var selectRightBtn = document.getElementById('roll-select-right');
      if (!selectAllBtn) {
        var snapEl = document.querySelector('.roll-snap');
        if (snapEl && snapEl.parentNode) {
          var selGroup = document.createElement('div');
          selGroup.className = 'roll-select';
          selGroup.innerHTML =
            '<button id="roll-select-all" class="ghost compact" title="Select all notes across both Vocal and Instrument voices (Ctrl+A)">Select All</button>' +
            '<button id="roll-select-right" class="ghost compact" title="Select all notes from cursor/playhead to right across both voices (Ctrl+Shift+A or Alt+A)">From Cursor ▶</button>';
          snapEl.parentNode.insertBefore(selGroup, snapEl);
          selectAllBtn = document.getElementById('roll-select-all');
          selectRightBtn = document.getElementById('roll-select-right');
        }
      }

      if (selectAllBtn && !selectAllBtn._bound) {
        selectAllBtn._bound = true;
        selectAllBtn.addEventListener('click', function () { self.selectAll(); });
      }
      if (selectRightBtn && !selectRightBtn._bound) {
        selectRightBtn._bound = true;
        selectRightBtn.addEventListener('click', function () { self.selectRightOfPlayhead(); });
      }

      // Ensure voice selector exists and is visible
      var rollVoices = document.querySelector('.roll-voices');
      if (!rollVoices) {
        var toolbar = document.querySelector('.roll-toolbar');
        if (toolbar) {
          rollVoices = document.createElement('div');
          rollVoices.className = 'roll-voices';
          rollVoices.innerHTML =
            '<span class="roll-label" title="Active voice when adding new notes:">Voice:</span>' +
            '<button class="chip compact active" id="roll-voice-vocal" data-voice="Vocal" title="Add Vocal notes (Blue) • or convert selected notes to Vocal (V)">● Vocal</button>' +
            '<button class="chip compact" id="roll-voice-ins" data-voice="Ins" title="Add Instrument notes (Amber) • or convert selected notes to Instrument (V)">● Ins</button>';
          toolbar.insertBefore(rollVoices, toolbar.firstChild);
        }
      } else {
        rollVoices.style.display = '';
      }

      var vocalBtn = document.getElementById('roll-voice-vocal');
      var insBtn = document.getElementById('roll-voice-ins');
      if (vocalBtn && !vocalBtn._bound) {
        vocalBtn._bound = true;
        vocalBtn.addEventListener('click', function () { self.setVoice('Vocal', true); });
      }
      if (insBtn && !insBtn._bound) {
        insBtn._bound = true;
        insBtn.addEventListener('click', function () { self.setVoice('Ins', true); });
      }

      // Update zoom button tooltips
      var zOut = document.getElementById('roll-zoom-out');
      if (zOut) { zOut.title = 'Zoom out (− or _)'; }
      var zIn = document.getElementById('roll-zoom-in');
      if (zIn) { zIn.title = 'Zoom in (+ or =)'; }
      var zFit = document.getElementById('roll-zoom-fit');
      if (zFit) { zFit.title = 'Scroll to notes (F or 0)'; }

      // Update hint bar
      var hintBar = document.querySelector('.roll-hint-bar span');
      if (hintBar && hintBar.textContent.indexOf('V: toggle voice') === -1) {
        hintBar.textContent = 'Click: add note • Drag: move note • Edge: resize • Marquee select • V: toggle voice • +/−: zoom • L: edit lyric • C: click track • H: chords • Del: delete • Left/Right: step bar • Space: play';
      }
    },

    init: function () {
      if (this.initialized) { return; }
      this.initialized = true;

      var self = this;
      this.ensureToolbar();

      // Voice selectors (active voice for drawing new notes / converting selected notes)
      var vocalBtn = document.getElementById('roll-voice-vocal');
      var insBtn = document.getElementById('roll-voice-ins');
      if (vocalBtn && !vocalBtn._bound) {
        vocalBtn._bound = true;
        vocalBtn.addEventListener('click', function () { self.setVoice('Vocal', true); });
      }
      if (insBtn && !insBtn._bound) {
        insBtn._bound = true;
        insBtn.addEventListener('click', function () { self.setVoice('Ins', true); });
      }

      // Selection buttons
      var selectAllBtn = document.getElementById('roll-select-all');
      if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function () { self.selectAll(); });
      }
      var selectRightBtn = document.getElementById('roll-select-right');
      if (selectRightBtn) {
        selectRightBtn.addEventListener('click', function () { self.selectRightOfPlayhead(); });
      }

      // Ghost checkbox (optional backwards compatibility)
      var ghostCheck = document.getElementById('roll-ghost');
      if (ghostCheck) {
        ghostCheck.addEventListener('change', function () {
          self.ghostOther = ghostCheck.checked;
          self.renderNotes();
        });
      }

      // Snap dropdown
      var snapSel = document.getElementById('roll-snap-val');
      if (snapSel) {
        snapSel.addEventListener('change', function () {
          var val = parseInt(snapSel.value, 10);
          self.snapTicks = Math.round(16 / val);
        });
      }

      // Sound / Instrument dropdown
      var soundSel = document.getElementById('roll-sound-val');
      if (soundSel) {
        soundSel.value = currentInstrument;
        soundSel.addEventListener('change', function () {
          self.setInstrument(soundSel.value);
        });
      }

      // Transport Rewind / Prev / Play / Next / Metronome
      var rewindBtn = document.getElementById('roll-rewind');
      if (rewindBtn) {
        rewindBtn.addEventListener('click', function () { self.rewindToStart(); });
      }
      var prevBtn = document.getElementById('roll-prev');
      if (prevBtn) {
        prevBtn.addEventListener('click', function () { self.stepPrev(); });
      }
      var playBtn = document.getElementById('roll-play');
      if (playBtn) {
        playBtn.addEventListener('click', function () { self.togglePlay(); });
      }
      var nextBtn = document.getElementById('roll-next');
      if (nextBtn) {
        nextBtn.addEventListener('click', function () { self.stepNext(); });
      }
      var metroBtn = document.getElementById('roll-metronome');
      if (metroBtn) {
        metroBtn.addEventListener('click', function () { self.toggleMetronome(); });
      }
      var chordsBtn = document.getElementById('roll-chords');
      if (chordsBtn) {
        chordsBtn.addEventListener('click', function () { self.toggleChords(); });
      }

      // History Undo / Redo
      var undoBtn = document.getElementById('roll-undo-btn');
      if (undoBtn) {
        undoBtn.addEventListener('click', function () {
          if (global.undoScore) { global.undoScore(); }
        });
      }
      var redoBtn = document.getElementById('roll-redo-btn');
      if (redoBtn) {
        redoBtn.addEventListener('click', function () {
          if (global.redoScore) { global.redoScore(); }
        });
      }

      // Zoom controls
      var zoomIn = document.getElementById('roll-zoom-in');
      var zoomOut = document.getElementById('roll-zoom-out');
      var zoomFit = document.getElementById('roll-zoom-fit');
      if (zoomIn) {
        zoomIn.addEventListener('click', function () { self.zoomIn(); });
      }
      if (zoomOut) {
        zoomOut.addEventListener('click', function () { self.zoomOut(); });
      }
      if (zoomFit) {
        zoomFit.addEventListener('click', function () { self.scrollToNotes(); });
      }

      // Mouse wheel zoom (Ctrl + wheel or Alt + wheel on grid)
      var gridScroll = document.getElementById('roll-grid-scroll');
      if (gridScroll) {
        gridScroll.addEventListener('wheel', function (e) {
          if (e.ctrlKey || e.altKey || e.metaKey) {
            e.preventDefault();
            if (e.deltaY < 0) {
              self.zoomIn(2);
            } else if (e.deltaY > 0) {
              self.zoomOut(2);
            }
          }
        }, { passive: false });
      }

      // Maximize toggle
      var maxBtn = document.getElementById('roll-maximize');
      if (maxBtn) {
        maxBtn.addEventListener('click', function () {
          if (global.toggleScoreMaximized) {
            global.toggleScoreMaximized();
          }
        });
      }

      // Show / Hide ABC text split toggle
      var toggleTextBtn = document.getElementById('roll-toggle-text');
      if (toggleTextBtn) {
        toggleTextBtn.addEventListener('click', function () {
          var modalBox = document.querySelector('.modal-box.score');
          if (modalBox) {
            modalBox.classList.toggle('show-split');
            toggleTextBtn.textContent = modalBox.classList.contains('show-split') ? 'Hide ABC' : 'Show ABC';
          }
        });
      }

      // Match lyrics button
      var matchLyricsBtn = document.getElementById('roll-match-lyrics');
      if (matchLyricsBtn) {
        matchLyricsBtn.addEventListener('click', function () {
          self.matchSongLyrics();
        });
      }

      // Fill gaps and compact gaps buttons
      var fillGapsBtn = document.getElementById('roll-fill-gaps');
      if (fillGapsBtn) {
        fillGapsBtn.addEventListener('click', function () {
          self.fillGapsFromChords();
        });
      }
      var compactGapsBtn = document.getElementById('roll-compact-gaps');
      if (compactGapsBtn) {
        compactGapsBtn.addEventListener('click', function () {
          self.compactEmptyBars();
        });
      }

      // Synchronized scrolling
      var gridScroll = document.getElementById('roll-grid-scroll');
      var keysEl = document.getElementById('roll-keys');
      var timelineHeader = document.getElementById('roll-timeline-header');
      var lyricsFooter = document.getElementById('roll-lyrics-footer');
      if (gridScroll) {
        gridScroll.addEventListener('scroll', function () {
          if (keysEl) { keysEl.scrollTop = gridScroll.scrollTop; }
          if (timelineHeader) { timelineHeader.scrollLeft = gridScroll.scrollLeft; }
          if (lyricsFooter) { lyricsFooter.scrollLeft = gridScroll.scrollLeft; }
        });
      }

      // Grid interactions: note click, move, resize, add
      this.bindGridEvents();
    },

    setVoice: function (voiceName, convertSelected) {
      this.currentVoice = voiceName || 'Vocal';
      if (typeof document !== 'undefined') {
        var vocalBtn = document.getElementById('roll-voice-vocal');
        var insBtn = document.getElementById('roll-voice-ins');
        if (vocalBtn) { vocalBtn.classList.toggle('active', this.currentVoice === 'Vocal'); }
        if (insBtn) { insBtn.classList.toggle('active', this.currentVoice === 'Ins'); }
      }

      if (convertSelected && this.model && this.hasSelection && this.hasSelection()) {
        var changed = false;
        for (var i = 0; i < this.model.notes.length; i++) {
          var n = this.model.notes[i];
          if (this.isNoteSelected(n.id) && n.voice !== this.currentVoice) {
            n.voice = this.currentVoice;
            changed = true;
          }
        }
        if (changed) {
          if (this.selectedNoteId) {
            var lead = this.findNote(this.selectedNoteId);
            if (lead) { playTone(lead.pitch, 0.2, this.currentVoice); }
          }
          this.commitEdit();
        }
      }
    },

    toggleVoice: function () {
      var nextVoice = (this.currentVoice === 'Ins') ? 'Vocal' : 'Ins';
      if (this.model && this.hasSelection && this.hasSelection()) {
        var hasVocal = false;
        var hasIns = false;
        for (var i = 0; i < this.model.notes.length; i++) {
          var n = this.model.notes[i];
          if (this.isNoteSelected(n.id)) {
            if (n.voice === 'Ins') { hasIns = true; }
            else { hasVocal = true; }
          }
        }
        if (hasVocal && !hasIns) {
          nextVoice = 'Ins';
        } else if (hasIns && !hasVocal) {
          nextVoice = 'Vocal';
        }
      }
      this.setVoice(nextVoice, true);
    },

    setInstrument: function (inst) {
      currentInstrument = inst || 'acoustic_grand_piano';
      var select = document.getElementById('roll-sound-val');
      if (select && select.value !== currentInstrument) {
        select.value = currentInstrument;
      }
      if (currentInstrument !== 'synth' && this.model) {
        preloadSamplesForNotes(getAllModelPitches(this.model), currentInstrument);
      }
    },

    getInstrument: function () {
      return currentInstrument;
    },

    loadAbc: function (abcText) {
      this.model = parseAbc(abcText);
      if (this.model && currentInstrument !== 'synth') {
        preloadSamplesForNotes(getAllModelPitches(this.model), currentInstrument);
      }
      this.selectedNoteIds = [];
      this.selectedNoteId = null;
      if (this.model && this.model.voices) {
        if (this.model.voices.indexOf('Vocal') !== -1) {
          this.setVoice('Vocal', false);
        } else if (this.model.voices.length > 0) {
          this.setVoice(this.model.voices[0], false);
        } else {
          this.setVoice('Vocal', false);
        }
      } else {
        this.setVoice('Vocal', false);
      }

      // Auto-match song lyrics on load if score has no lyrics embedded yet
      var hasAnyLyrics = this.model.notes.some(function (n) { return n.voice === 'Vocal' && n.lyric; });
      if (!hasAnyLyrics) {
        var songLyrics = '';
        var bigLyricsEl = document.getElementById('lyrics-big');
        var stdLyricsEl = document.getElementById('lyrics');
        if (bigLyricsEl && bigLyricsEl.value && bigLyricsEl.value.trim()) {
          songLyrics = bigLyricsEl.value.trim();
        } else if (stdLyricsEl && stdLyricsEl.value && stdLyricsEl.value.trim()) {
          songLyrics = stdLyricsEl.value.trim();
        }
        if (songLyrics) {
          this.matchSongLyrics(songLyrics, true);
        }
      }

      this.renderAll();
      var self = this;
      setTimeout(function () { self.scrollToNotes(); }, 50);
    },

    render: function (abcText) {
      this.init();
      this.stop();
      this.loadAbc(abcText);
    },

    renderAll: function () {
      if (!this.model) { return; }
      if (typeof document === 'undefined') { return; }
      this.ensureToolbar();
      this.updateMetadata();
      this.renderKeys();
      this.renderTimeline();
      this.renderGrid();
      this.renderNotes();
      this.renderLyricsFooter();
      this.updatePlayhead();
    },

    updateMetadata: function () {
      var metaEl = document.getElementById('roll-meta');
      if (metaEl && this.model) {
        metaEl.textContent = 'Key ' + this.model.key + ' • ' + (this.model.meter || (this.model.ticksPerBar === 16 ? '4/4' : 'Metre')) + ' • ' + this.model.bpm + ' BPM';
      }
    },

    renderKeys: function () {
      var keysEl = document.getElementById('roll-keys');
      if (!keysEl) { return; }
      var self = this;
      var html = [];

      for (var p = MAX_PITCH; p >= MIN_PITCH; p--) {
        var semitone = ((p % 12) + 12) % 12;
        var isBlack = BLACK_KEYS[semitone];
        var name = midiToNoteName(p, self.model && self.model.key);
        var isC = semitone === 0;

        html.push(
          '<div class="roll-key ' + (isBlack ? 'black' : 'white') + (isC ? ' c-key' : '') + '" ' +
          'data-pitch="' + p + '" style="height:' + self.rowHeight + 'px; line-height:' + self.rowHeight + 'px">' +
          '<span class="key-label">' + (isC || isBlack ? name : '') + '</span>' +
          '</div>'
        );
      }
      keysEl.innerHTML = html.join('');

      // Key click to audition note
      var keyNodes = keysEl.querySelectorAll('.roll-key');
      Array.prototype.forEach.call(keyNodes, function (node) {
        node.addEventListener('pointerdown', function () {
          var pitch = parseInt(node.dataset.pitch, 10);
          node.classList.add('pressed');
          playTone(pitch, 0.35, self.currentVoice);
        });
        node.addEventListener('pointerup', function () { node.classList.remove('pressed'); });
        node.addEventListener('pointerleave', function () { node.classList.remove('pressed'); });
      });
    },

    renderTimeline: function () {
      var rulerEl = document.getElementById('roll-ruler');
      var chordsEl = document.getElementById('roll-chords-track');
      if (!rulerEl || !chordsEl || !this.model) { return; }

      var ticksPerBar = this.model.ticksPerBar || 16;
      var totalTicks = this.getTotalTicks();
      var totalBars = Math.ceil(totalTicks / ticksPerBar);
      var self = this;

      // Section markers
      var sectionMap = {};
      for (var s = 0; s < this.model.sections.length; s++) {
        var sec = this.model.sections[s];
        sectionMap[sec.barIndex] = sec.text.replace(/^%\s*/, '');
      }

      var rulerHtml = [];
      for (var b = 0; b < totalBars; b++) {
        var left = b * ticksPerBar * self.tickWidth;
        var width = ticksPerBar * self.tickWidth;
        var secName = sectionMap[b];

        rulerHtml.push(
          '<div class="roll-bar-marker" style="left:' + left + 'px; width:' + width + 'px">' +
          (secName ? '<span class="roll-sec-badge" data-bar="' + b + '">' + secName + '</span>' : '') +
          '<span class="roll-bar-num">' + (b + 1) + '</span>' +
          '</div>'
        );
      }
      rulerEl.style.width = (totalTicks * self.tickWidth) + 'px';
      rulerEl.innerHTML = rulerHtml.join('');

      // Click on ruler to move playhead
      rulerEl.onclick = function (e) {
        var rect = rulerEl.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var clickedTick = Math.max(0, Math.floor(x / self.tickWidth));
        self.seekTick(clickedTick);
      };

      // Click on section badge to edit section name
      var badges = rulerEl.querySelectorAll('.roll-sec-badge');
      Array.prototype.forEach.call(badges, function (badge) {
        badge.onclick = function (e) {
          e.stopPropagation();
          var barIndex = parseInt(badge.dataset.bar, 10);
          var current = badge.textContent.trim();
          var newName = window.prompt("Section name (e.g. intro, verse, chorus):", current);
          if (newName !== null) {
            newName = newName.trim();
            for (var si = 0; si < self.model.sections.length; si++) {
              if (self.model.sections[si].barIndex === barIndex) {
                self.model.sections[si].text = newName ? ("% " + newName) : "";
              }
            }
            self.model.sections = self.model.sections.filter(function (x) { return x.text; });
            self.commitEdit();
          }
        };
      });

      // Chords lane
      var chordHtml = [];
      for (var cb = 0; cb < totalBars; cb++) {
        var bLeft = cb * ticksPerBar * self.tickWidth;
        var bWidth = ticksPerBar * self.tickWidth;
        chordHtml.push(
          '<div class="roll-chord-slot" data-bar="' + cb + '" style="left:' + bLeft + 'px; width:' + bWidth + 'px"></div>'
        );
      }
      for (var ci = 0; ci < this.model.chords.length; ci++) {
        var ch = this.model.chords[ci];
        var chTick = ch.barIndex * ticksPerBar + (ch.tickInBar || 0);
        var chLeft = chTick * self.tickWidth;
        chordHtml.push(
          '<span class="roll-chord-tag" data-chord-idx="' + ci + '" style="left:' + chLeft + 'px">' +
          ch.name + '</span>'
        );
      }
      chordsEl.style.width = (totalTicks * self.tickWidth) + 'px';
      chordsEl.innerHTML = chordHtml.join('');

      // Click chord to edit, or slot to add
      chordsEl.onclick = function (e) {
        var tag = e.target.closest('.roll-chord-tag');
        if (tag) {
          var idx = parseInt(tag.dataset.chordIdx, 10);
          var chord = self.model.chords[idx];
          var newChord = window.prompt("Edit chord name (e.g. C, Dm7, G/B):", chord.name);
          if (newChord !== null) {
            newChord = newChord.trim();
            if (newChord) {
              chord.name = newChord;
            } else {
              self.model.chords.splice(idx, 1);
            }
            self.commitEdit();
          }
          return;
        }
        var slot = e.target.closest('.roll-chord-slot');
        if (slot) {
          var bar = parseInt(slot.dataset.bar, 10);
          var rectS = slot.getBoundingClientRect();
          var offsetTick = Math.floor((e.clientX - rectS.left) / self.tickWidth);
          var entered = window.prompt("Add chord for bar " + (bar + 1) + ":", "C");
          if (entered && entered.trim()) {
            self.model.chords.push({
              voice: self.currentVoice,
              barIndex: bar,
              tickInBar: offsetTick,
              name: entered.trim()
            });
            self.commitEdit();
          }
        }
      };
    },

    getTotalTicks: function () {
      if (!this.model) { return 64; }
      var ticksPerBar = this.model.ticksPerBar || 16;
      var maxTick = 16 * 4; // at least 4 bars
      for (var n = 0; n < this.model.notes.length; n++) {
        var end = this.model.notes[n].startTick + this.model.notes[n].durationTicks;
        if (end > maxTick) { maxTick = end; }
      }
      for (var c = 0; c < this.model.chords.length; c++) {
        var chEnd = (this.model.chords[c].barIndex + 1) * ticksPerBar;
        if (chEnd > maxTick) { maxTick = chEnd; }
      }
      // Round up to full bar + 2 extra empty bars for breathing room
      var bars = Math.ceil(maxTick / ticksPerBar) + 2;
      return bars * ticksPerBar;
    },

    renderGrid: function () {
      var gridEl = document.getElementById('roll-grid');
      var linesEl = document.getElementById('roll-grid-lines');
      if (!gridEl || !linesEl || !this.model) { return; }

      var totalTicks = this.getTotalTicks();
      var ticksPerBar = this.model.ticksPerBar || 16;
      var totalWidth = totalTicks * this.tickWidth;
      var totalHeight = NUM_PITCHES * this.rowHeight;
      var self = this;

      gridEl.style.width = totalWidth + 'px';
      gridEl.style.height = totalHeight + 'px';

      var linesHtml = [];
      // Horizontal row backgrounds
      for (var p = MAX_PITCH; p >= MIN_PITCH; p--) {
        var semitone = ((p % 12) + 12) % 12;
        var isBlack = BLACK_KEYS[semitone];
        var top = (MAX_PITCH - p) * self.rowHeight;
        linesHtml.push(
          '<div class="roll-row ' + (isBlack ? 'black-row' : 'white-row') + '" ' +
          'style="top:' + top + 'px; height:' + self.rowHeight + 'px"></div>'
        );
      }

      // Vertical tick / beat / bar lines
      var beatsPerBar = (this.model && this.model.meterNum) || 4;
      var ticksPerBeat = Math.max(1, Math.round(ticksPerBar / beatsPerBar));

      for (var t = 0; t <= totalTicks; t++) {
        var isBar = (t % ticksPerBar === 0);
        var isBeat = (t % ticksPerBeat === 0);
        var left = t * self.tickWidth;

        if (isBar || isBeat || self.tickWidth >= 16) {
          var barNum = Math.floor(t / ticksPerBar) + 1;
          linesHtml.push(
            '<div class="roll-vline ' + (isBar ? 'bar-line' : (isBeat ? 'beat-line' : 'tick-line')) + '" ' +
            (isBar ? ('data-bar="' + barNum + '" ') : '') +
            'style="left:' + left + 'px">' +
            (isBar && t < totalTicks ? ('<span class="roll-bar-line-tag">' + barNum + '</span>') : '') +
            '</div>'
          );
        }
      }

      linesEl.innerHTML = linesHtml.join('');
    },

    renderNotes: function () {
      if (typeof document === 'undefined') { return; }
      var notesLayer = document.getElementById('roll-notes-layer');
      if (!notesLayer || !this.model) { return; }
      var self = this;
      var html = [];

      for (var i = 0; i < this.model.notes.length; i++) {
        var note = this.model.notes[i];
        var left = note.startTick * self.tickWidth;
        var top = (MAX_PITCH - note.pitch) * self.rowHeight;
        var width = Math.max(4, note.durationTicks * self.tickWidth - 2);
        var height = self.rowHeight - 2;
        var isSelected = self.isNoteSelected(note.id);
        var noteName = midiToNoteName(note.pitch, self.model && self.model.key);
        var lyricText = (note.voice === 'Vocal' && note.lyric) ? note.lyric.trim() : '';

        var label = '';
        if (lyricText && width > 16) {
          if (width > 48) {
            label = noteName + ' • ' + lyricText;
          } else {
            label = lyricText;
          }
        } else if (width > 22) {
          label = noteName;
        }

        var voiceClass = (note.voice === 'Ins') ? 'ins' : 'vocal';
        var voiceLabel = (note.voice === 'Ins') ? 'Instrument' : 'Vocal';
        var selClass = isSelected ? 'selected' : '';
        var lyrClass = lyricText ? ' has-lyric' : '';
        var noteTitle = voiceLabel + ' Note (' + noteName + ') • Press V to flip voice';

        html.push(
          '<div class="roll-note ' + voiceClass + ' ' + selClass + lyrClass + '" ' +
          'data-note-id="' + note.id + '" ' +
          'title="' + escapeHtml(noteTitle) + '" ' +
          'style="left:' + left + 'px; top:' + top + 'px; width:' + width + 'px; height:' + height + 'px">' +
          '<span class="roll-note-title">' + label + '</span>' +
          '<div class="roll-note-resize"></div>' +
          '</div>'
        );
      }

      notesLayer.innerHTML = html.join('');

      // Bidirectional hover from vocal notes to footer lyric items
      var vocalNoteEls = notesLayer.querySelectorAll('.roll-note.vocal');
      Array.prototype.forEach.call(vocalNoteEls, function (vel) {
        var vid = vel.dataset.noteId;
        vel.addEventListener('pointerenter', function () {
          var lTag = document.querySelector('.roll-lyric-item[data-note-id="' + vid + '"]');
          if (lTag) { lTag.classList.add('highlight-from-note'); }
        });
        vel.addEventListener('pointerleave', function () {
          var lTag = document.querySelector('.roll-lyric-item[data-note-id="' + vid + '"]');
          if (lTag) { lTag.classList.remove('highlight-from-note'); }
        });
      });
    },

    renderLyricsFooter: function () {
      if (typeof document === 'undefined') { return; }
      var footerEl = document.getElementById('roll-lyrics-footer');
      var stripEl = document.getElementById('roll-lyrics-strip');
      var itemsEl = document.getElementById('roll-lyrics-items');
      if (!footerEl || !stripEl || !itemsEl || !this.model) { return; }

      var totalTicks = this.getTotalTicks();
      var totalWidth = totalTicks * this.tickWidth;
      stripEl.style.width = totalWidth + 'px';

      var vocalNotes = this.model.notes.filter(function (n) { return n.voice === 'Vocal'; });
      vocalNotes.sort(function (a, b) { return a.startTick - b.startTick; });

      var self = this;
      var html = [];

      var ticksPerBar = this.model.ticksPerBar || 16;
      var totalBars = Math.ceil(totalTicks / ticksPerBar);
      for (var b = 0; b < totalBars; b++) {
        var bLeft = b * ticksPerBar * self.tickWidth;
        html.push(
          '<div class="roll-lyric-bar-marker" style="left:' + bLeft + 'px" data-bar="' + (b + 1) + '">' +
          '<span class="roll-lyric-bar-num">' + (b + 1) + '</span>' +
          '</div>'
        );
      }

      for (var vi = 0; vi < vocalNotes.length; vi++) {
        var vNote = vocalNotes[vi];
        var vnLeft = vNote.startTick * self.tickWidth;
        var vnWidth = Math.max(18, vNote.durationTicks * self.tickWidth - 2);
        var hasLyr = Boolean(vNote.lyric && vNote.lyric.trim());
        var rawText = hasLyr ? vNote.lyric.trim() : '';
        var lyrText = hasLyr ? escapeHtml(rawText) : '+';
        var emptyClass = hasLyr ? '' : ' empty';
        var titleAttr = hasLyr
          ? ('Lyric: "' + escapeHtml(rawText) + '" (' + midiToNoteName(vNote.pitch, self.model && self.model.key) + ') • Click to edit')
          : ('Add lyric for ' + midiToNoteName(vNote.pitch, self.model && self.model.key) + ' • Click to edit');

        var itemWidth = Math.max(22, vnWidth);
        var maxW = Math.max(76, itemWidth + 24);

        html.push(
          '<span class="roll-lyric-item' + emptyClass + '" data-note-id="' + vNote.id + '" ' +
          'data-start-tick="' + vNote.startTick + '" ' +
          'data-end-tick="' + (vNote.startTick + vNote.durationTicks) + '" ' +
          'style="left:' + vnLeft + 'px; min-width:' + itemWidth + 'px; max-width:' + maxW + 'px" ' +
          'title="' + titleAttr + '">' +
          lyrText + '</span>'
        );
      }

      itemsEl.innerHTML = html.join('');

      // Click lyric item to edit; click empty footer space to seek
      footerEl.onclick = function (e) {
        var item = e.target.closest('.roll-lyric-item');
        if (item) {
          var nId = parseInt(item.dataset.noteId, 10);
          self.editLyricForNote(nId);
          return;
        }
        var rect = footerEl.getBoundingClientRect();
        var clickX = e.clientX - rect.left + footerEl.scrollLeft;
        var clickedTick = Math.max(0, Math.floor(clickX / self.tickWidth));
        self.seekTick(clickedTick);
      };

      // Hover highlighting between lyric items and grid notes
      var itemNodes = itemsEl.querySelectorAll('.roll-lyric-item');
      Array.prototype.forEach.call(itemNodes, function (tn) {
        var tnId = tn.dataset.noteId;
        tn.addEventListener('pointerenter', function () {
          var noteEl = document.querySelector('.roll-note[data-note-id="' + tnId + '"]');
          if (noteEl) { noteEl.classList.add('highlight-from-lyric'); }
        });
        tn.addEventListener('pointerleave', function () {
          var noteEl = document.querySelector('.roll-note[data-note-id="' + tnId + '"]');
          if (noteEl) { noteEl.classList.remove('highlight-from-lyric'); }
        });
      });

      // Synchronize scroll position
      var gridScroll = document.getElementById('roll-grid-scroll');
      if (gridScroll) {
        footerEl.scrollLeft = gridScroll.scrollLeft;
      }
    },

    /* ------------------------------------------------ Selection Helpers */
    hasSelection: function () {
      return Boolean(this.selectedNoteIds && this.selectedNoteIds.length > 0);
    },

    isNoteSelected: function (id) {
      if (this.selectedNoteIds && this.selectedNoteIds.length > 0) {
        return this.selectedNoteIds.indexOf(id) !== -1;
      }
      return this.selectedNoteId === id;
    },

    selectNote: function (id, addToSelection) {
      if (!this.selectedNoteIds) { this.selectedNoteIds = []; }
      if (addToSelection) {
        if (this.selectedNoteIds.indexOf(id) === -1) {
          this.selectedNoteIds.push(id);
        }
      } else {
        this.selectedNoteIds = [id];
      }
      this.selectedNoteId = this.selectedNoteIds.length > 0 ? this.selectedNoteIds[0] : null;
      this.renderNotes();
    },

    deselectNote: function (id) {
      if (!this.selectedNoteIds) { return; }
      var idx = this.selectedNoteIds.indexOf(id);
      if (idx !== -1) {
        this.selectedNoteIds.splice(idx, 1);
      }
      this.selectedNoteId = this.selectedNoteIds.length > 0 ? this.selectedNoteIds[0] : null;
      this.renderNotes();
    },

    clearSelection: function () {
      this.selectedNoteIds = [];
      this.selectedNoteId = null;
      this.renderNotes();
    },

    selectAll: function () {
      if (!this.model) { return; }
      var ids = [];
      for (var i = 0; i < this.model.notes.length; i++) {
        ids.push(this.model.notes[i].id);
      }
      this.selectedNoteIds = ids;
      this.selectedNoteId = ids.length > 0 ? ids[0] : null;
      this.renderNotes();
    },

    selectFromTick: function (fromTick) {
      if (!this.model) { return; }
      fromTick = (fromTick !== undefined && fromTick !== null) ? fromTick : (this.playheadTick || 0);
      var ids = [];
      for (var i = 0; i < this.model.notes.length; i++) {
        if (this.model.notes[i].startTick >= fromTick) {
          ids.push(this.model.notes[i].id);
        }
      }
      this.selectedNoteIds = ids;
      this.selectedNoteId = ids.length > 0 ? ids[0] : null;
      this.renderNotes();
    },

    selectRightOfPlayhead: function () {
      this.selectFromTick(this.playheadTick || 0);
    },

    selectNotesInBox: function (boxL, boxT, boxW, boxH, addToSelection) {
      if (!this.model) { return []; }
      var newSel = addToSelection ? (this.selectedNoteIds || []).slice() : [];
      for (var j = 0; j < this.model.notes.length; j++) {
        var note = this.model.notes[j];
        var nLeft = note.startTick * this.tickWidth;
        var nWidth = Math.max(4, note.durationTicks * this.tickWidth - 2);
        var nRight = nLeft + nWidth;
        var nTop = (MAX_PITCH - note.pitch) * this.rowHeight;
        var nBottom = nTop + (this.rowHeight - 2);

        if (nLeft < (boxL + boxW) && nRight > boxL && nTop < (boxT + boxH) && nBottom > boxT) {
          if (newSel.indexOf(note.id) === -1) {
            newSel.push(note.id);
          }
        }
      }
      this.selectedNoteIds = newSel;
      this.selectedNoteId = newSel.length > 0 ? newSel[0] : null;
      return newSel;
    },

    moveSelectedNotes: function (deltaTicks, deltaPitch) {
      if (!this.model || !this.hasSelection()) { return; }
      deltaTicks = deltaTicks || 0;
      deltaPitch = deltaPitch || 0;

      var selected = [];
      var minStart = Infinity;
      var minPitch = Infinity;
      var maxPitch = -Infinity;

      for (var i = 0; i < this.model.notes.length; i++) {
        var n = this.model.notes[i];
        if (this.isNoteSelected(n.id)) {
          selected.push(n);
          if (n.startTick < minStart) { minStart = n.startTick; }
          if (n.pitch < minPitch) { minPitch = n.pitch; }
          if (n.pitch > maxPitch) { maxPitch = n.pitch; }
        }
      }
      if (selected.length === 0) { return; }

      var clampedDTicks = Math.max(-minStart, deltaTicks);
      var clampedDPitch = Math.max(MIN_PITCH - minPitch, Math.min(MAX_PITCH - maxPitch, deltaPitch));

      for (var j = 0; j < selected.length; j++) {
        selected[j].startTick += clampedDTicks;
        selected[j].pitch += clampedDPitch;
      }
      this.commitEdit();
    },

    getSelectionBox: function () {
      var box = document.getElementById('roll-selection-box');
      if (!box) {
        var grid = document.getElementById('roll-grid');
        if (grid) {
          box = document.createElement('div');
          box.id = 'roll-selection-box';
          box.className = 'roll-selection-box hidden';
          grid.appendChild(box);
        }
      }
      return box;
    },

    updateSelectionVisuals: function () {
      var notesLayer = document.getElementById('roll-notes-layer');
      if (!notesLayer) { return; }
      var noteNodes = notesLayer.querySelectorAll('.roll-note');
      var self = this;
      for (var i = 0; i < noteNodes.length; i++) {
        var nid = parseInt(noteNodes[i].dataset.noteId, 10);
        noteNodes[i].classList.toggle('selected', self.isNoteSelected(nid));
      }
    },

    bindGridEvents: function () {
      var gridEl = document.getElementById('roll-grid');
      var gridScroll = document.getElementById('roll-grid-scroll');
      if (!gridEl || !gridScroll) { return; }
      var self = this;

      var dragState = null;

      gridEl.addEventListener('pointerdown', function (e) {
        var resizeHandle = e.target.closest('.roll-note-resize');
        var noteEl = e.target.closest('.roll-note');

        if (resizeHandle) {
          // Resize note duration
          e.preventDefault();
          e.stopPropagation();
          var pNoteEl = resizeHandle.closest('.roll-note');
          var rId = parseInt(pNoteEl.dataset.noteId, 10);
          var rNote = self.findNote(rId);
          if (!rNote) { return; }

          self.selectedNoteIds = [rId];
          self.selectedNoteId = rId;
          self.renderNotes();

          dragState = {
            type: 'resize',
            note: rNote,
            startX: e.clientX,
            origDuration: rNote.durationTicks
          };
          window.addEventListener('pointermove', onPointerMove);
          window.addEventListener('pointerup', onPointerUp);
          return;
        }

        if (noteEl) {
          // Move or select note(s)
          e.preventDefault();
          e.stopPropagation();
          var nId = parseInt(noteEl.dataset.noteId, 10);
          var mNote = self.findNote(nId);
          if (!mNote) { return; }

          var isShift = e.shiftKey || e.metaKey || e.ctrlKey;
          var wasAlreadySelected = self.isNoteSelected(nId);

          if (isShift) {
            if (wasAlreadySelected) {
              self.deselectNote(nId);
              return;
            } else {
              self.selectNote(nId, true);
            }
          } else {
            if (!wasAlreadySelected) {
              self.selectNote(nId, false);
            }
          }

          playTone(mNote.pitch, 0.2, mNote.voice || self.currentVoice);

          // Prepare list of all selected notes to move in lockstep across all voices
          var notesToMove = [];
          var minStart = Infinity;
          var minPitch = Infinity;
          var maxPitch = -Infinity;
          for (var i = 0; i < self.model.notes.length; i++) {
            var n = self.model.notes[i];
            if (self.isNoteSelected(n.id)) {
              notesToMove.push({
                note: n,
                origStartTick: n.startTick,
                origPitch: n.pitch
              });
              if (n.startTick < minStart) { minStart = n.startTick; }
              if (n.pitch < minPitch) { minPitch = n.pitch; }
              if (n.pitch > maxPitch) { maxPitch = n.pitch; }
            }
          }

          dragState = {
            type: 'move',
            leadNote: mNote,
            notesToMove: notesToMove,
            minStart: minStart,
            minPitch: minPitch,
            maxPitch: maxPitch,
            startX: e.clientX,
            startY: e.clientY,
            lastPitchDelta: 0,
            hasMoved: false,
            wasAlreadySelected: wasAlreadySelected,
            isShift: isShift
          };
          window.addEventListener('pointermove', onPointerMove);
          window.addEventListener('pointerup', onPointerUp);
          return;
        }

        // Click or marquee drag on empty grid space
        var rect = gridEl.getBoundingClientRect();
        var clickX = e.clientX - rect.left;
        var clickY = e.clientY - rect.top;

        dragState = {
          type: 'grid_down',
          startX: e.clientX,
          startY: e.clientY,
          clickGridX: clickX,
          clickGridY: clickY,
          shiftKey: e.shiftKey || e.metaKey || e.ctrlKey,
          origSelectedIds: (self.selectedNoteIds || []).slice()
        };
        window.addEventListener('pointermove', onPointerMove);
        window.addEventListener('pointerup', onPointerUp);
      });

      // Double click note to delete
      gridEl.addEventListener('dblclick', function (e) {
        var noteEl = e.target.closest('.roll-note');
        if (noteEl) {
          e.preventDefault();
          e.stopPropagation();
          var id = parseInt(noteEl.dataset.noteId, 10);
          self.deleteNote(id);
        }
      });

      function onPointerMove(e) {
        if (!dragState) { return; }
        var snap = self.snapTicks || 1;

        if (dragState.type === 'resize') {
          var deltaX = e.clientX - dragState.startX;
          var deltaTicks = Math.round(deltaX / self.tickWidth);
          var newDur = Math.max(snap, Math.round((dragState.origDuration + deltaTicks) / snap) * snap);
          if (newDur !== dragState.note.durationTicks) {
            dragState.note.durationTicks = newDur;
            self.renderNotes();
          }
        } else if (dragState.type === 'move') {
          var dX = e.clientX - dragState.startX;
          var dY = e.clientY - dragState.startY;
          if (Math.hypot(dX, dY) > 3) {
            dragState.hasMoved = true;
          }

          var rawDTicks = Math.round(dX / self.tickWidth);
          var rawDPitch = -Math.round(dY / self.rowHeight);
          var snappedDTicks = Math.round(rawDTicks / snap) * snap;

          var clampedDTicks = Math.max(-dragState.minStart, snappedDTicks);
          var clampedDPitch = Math.max(MIN_PITCH - dragState.minPitch, Math.min(MAX_PITCH - dragState.maxPitch, rawDPitch));

          var changed = false;
          for (var i = 0; i < dragState.notesToMove.length; i++) {
            var item = dragState.notesToMove[i];
            var newStart = item.origStartTick + clampedDTicks;
            var newPitch = item.origPitch + clampedDPitch;
            if (item.note.startTick !== newStart) {
              item.note.startTick = newStart;
              changed = true;
            }
            if (item.note.pitch !== newPitch) {
              item.note.pitch = newPitch;
              changed = true;
            }
          }

          if (clampedDPitch !== dragState.lastPitchDelta) {
            playTone(dragState.leadNote.pitch, 0.15, dragState.leadNote.voice || self.currentVoice);
            dragState.lastPitchDelta = clampedDPitch;
          }

          if (changed) {
            self.renderNotes();
          }
        } else if (dragState.type === 'grid_down' || dragState.type === 'marquee') {
          var dist = Math.hypot(e.clientX - dragState.startX, e.clientY - dragState.startY);
          if (dist > 4 && dragState.type === 'grid_down') {
            dragState.type = 'marquee';
          }
          if (dragState.type === 'marquee') {
            var gRect = gridEl.getBoundingClientRect();
            var curGridX = e.clientX - gRect.left;
            var curGridY = e.clientY - gRect.top;

            var boxL = Math.max(0, Math.min(dragState.clickGridX, curGridX));
            var boxT = Math.max(0, Math.min(dragState.clickGridY, curGridY));
            var boxW = Math.abs(curGridX - dragState.clickGridX);
            var boxH = Math.abs(curGridY - dragState.clickGridY);

            var boxEl = self.getSelectionBox();
            if (boxEl) {
              boxEl.style.left = boxL + 'px';
              boxEl.style.top = boxT + 'px';
              boxEl.style.width = boxW + 'px';
              boxEl.style.height = boxH + 'px';
              boxEl.classList.remove('hidden');
            }

            self.selectNotesInBox(boxL, boxT, boxW, boxH, dragState.shiftKey);
            self.updateSelectionVisuals();
          }
        }
      }

      function onPointerUp(e) {
        if (!dragState) { return; }
        window.removeEventListener('pointermove', onPointerMove);
        window.removeEventListener('pointerup', onPointerUp);

        var state = dragState;
        dragState = null;

        if (state.type === 'resize') {
          self.commitEdit();
        } else if (state.type === 'move') {
          if (state.hasMoved) {
            self.commitEdit();
          } else if (state.wasAlreadySelected && !state.isShift) {
            // User just clicked on a previously multi-selected note without moving:
            // reduce selection to just this note
            self.selectedNoteIds = [state.leadNote.id];
            self.selectedNoteId = state.leadNote.id;
            self.renderNotes();
          }
        } else if (state.type === 'marquee') {
          var boxEl = self.getSelectionBox();
          if (boxEl) { boxEl.classList.add('hidden'); }
          self.renderNotes();
        } else if (state.type === 'grid_down') {
          // Click on empty grid space without dragging
          if (self.selectedNoteIds && self.selectedNoteIds.length > 0 && !state.shiftKey) {
            // Deselect all
            self.clearSelection();
          } else {
            // Add note at clicked cell
            var snap = self.snapTicks || 1;
            var clickedTick = Math.max(0, Math.floor(state.clickGridX / self.tickWidth));
            var noteStartTick = Math.floor(clickedTick / snap) * snap;
            var clickedPitch = MAX_PITCH - Math.floor(state.clickGridY / self.rowHeight);
            clickedPitch = Math.max(MIN_PITCH, Math.min(MAX_PITCH, clickedPitch));

            var newNote = {
              id: Date.now(),
              voice: self.currentVoice,
              pitch: clickedPitch,
              startTick: noteStartTick,
              durationTicks: snap
            };

            self.model.notes.push(newNote);
            self.selectedNoteIds = [newNote.id];
            self.selectedNoteId = newNote.id;
            playTone(clickedPitch, 0.25, self.currentVoice);
            self.commitEdit();
          }
        }
      }
    },

    findNote: function (id) {
      if (!this.model) { return null; }
      for (var i = 0; i < this.model.notes.length; i++) {
        if (this.model.notes[i].id === id) { return this.model.notes[i]; }
      }
      return null;
    },

    deleteNote: function (id) {
      if (!this.model) { return; }
      this.model.notes = this.model.notes.filter(function (n) { return n.id !== id; });
      if (this.selectedNoteIds) {
        var idx = this.selectedNoteIds.indexOf(id);
        if (idx !== -1) { this.selectedNoteIds.splice(idx, 1); }
      }
      this.selectedNoteId = (this.selectedNoteIds && this.selectedNoteIds.length > 0) ? this.selectedNoteIds[0] : null;
      this.commitEdit();
    },

    deleteSelectedNotes: function () {
      if (!this.model) { return; }
      var idsToDelete = (this.selectedNoteIds && this.selectedNoteIds.length > 0)
        ? this.selectedNoteIds
        : (this.selectedNoteId ? [this.selectedNoteId] : []);
      if (idsToDelete.length === 0) { return; }

      this.model.notes = this.model.notes.filter(function (n) {
        return idsToDelete.indexOf(n.id) === -1;
      });
      this.selectedNoteIds = [];
      this.selectedNoteId = null;
      this.commitEdit();
    },

    deleteSelectedNote: function () {
      this.deleteSelectedNotes();
    },

    scrollToNotes: function () {
      if (!this.model || this.model.notes.length === 0) {
        // Default scroll to C4 / C5 area
        var centerTop = (MAX_PITCH - 65) * this.rowHeight - 150;
        var gridScroll = document.getElementById('roll-grid-scroll');
        if (gridScroll) { gridScroll.scrollTop = Math.max(0, centerTop); }
        return;
      }
      var sumPitch = 0;
      var count = 0;
      for (var i = 0; i < this.model.notes.length; i++) {
        sumPitch += this.model.notes[i].pitch;
        count++;
      }
      var avgPitch = Math.round(sumPitch / count);
      var rowTop = (MAX_PITCH - avgPitch) * this.rowHeight;
      var scrollEl = document.getElementById('roll-grid-scroll');
      if (scrollEl) {
        var viewH = scrollEl.clientHeight || 400;
        scrollEl.scrollTop = Math.max(0, rowTop - viewH / 2);
      }
    },

    zoomIn: function (step) {
      step = step || 4;
      return this.setZoom(this.tickWidth + step);
    },

    zoomOut: function (step) {
      step = step || 4;
      return this.setZoom(this.tickWidth - step);
    },

    setZoom: function (newTickWidth) {
      newTickWidth = Math.max(6, Math.min(48, Math.round(newTickWidth)));
      if (newTickWidth === this.tickWidth) { return this.tickWidth; }

      var gridScroll = (typeof document !== 'undefined') ? document.getElementById('roll-grid-scroll') : null;
      var anchorTick = (this.playheadTick !== undefined) ? this.playheadTick : 0;

      if (gridScroll) {
        var viewW = gridScroll.clientWidth || 600;
        var centerPixel = gridScroll.scrollLeft + viewW / 2;
        var playheadPixel = (this.playheadTick || 0) * this.tickWidth;
        if (playheadPixel >= gridScroll.scrollLeft && playheadPixel <= gridScroll.scrollLeft + viewW) {
          anchorTick = this.playheadTick || 0;
        } else {
          anchorTick = centerPixel / Math.max(1, this.tickWidth);
        }
      }

      this.tickWidth = newTickWidth;
      this.renderAll();

      if (gridScroll) {
        var viewW = gridScroll.clientWidth || 600;
        var newAnchorPixel = anchorTick * newTickWidth;
        gridScroll.scrollLeft = Math.max(0, Math.round(newAnchorPixel - viewW / 2));
      }
      return this.tickWidth;
    },

    toggleMetronome: function (forceState) {
      this.metronomeEnabled = (forceState !== undefined) ? Boolean(forceState) : !this.metronomeEnabled;
      if (typeof document !== 'undefined') {
        var btn = document.getElementById('roll-metronome');
        if (btn) {
          if (this.metronomeEnabled) {
            btn.classList.add('active');
            btn.title = 'Click track: ON (Press C or M to mute)';
          } else {
            btn.classList.remove('active');
            btn.title = 'Click track: OFF (Press C or M to enable)';
          }
        }
      }
      if (typeof window !== 'undefined' && window.toast) {
        window.toast('Click track: ' + (this.metronomeEnabled ? 'ON' : 'OFF'));
      }
      return this.metronomeEnabled;
    },

    toggleChords: function (forceState) {
      this.chordsEnabled = (forceState !== undefined) ? Boolean(forceState) : !this.chordsEnabled;
      if (typeof document !== 'undefined') {
        var btn = document.getElementById('roll-chords');
        if (btn) {
          if (this.chordsEnabled) {
            btn.classList.add('active');
            btn.title = 'Chord accompaniment: ON (Press H to mute)';
          } else {
            btn.classList.remove('active');
            btn.title = 'Chord accompaniment: OFF (Press H to enable)';
          }
        }
      }
      if (typeof window !== 'undefined' && window.toast) {
        window.toast('Chords playback: ' + (this.chordsEnabled ? 'ON' : 'OFF'));
      }
      return this.chordsEnabled;
    },

    togglePlay: function () {
      if (typeof window !== 'undefined' && window.studioAudio && window.studioAudio.toggle()) { return; }   // studio audio is on: it plays or pauses
      if (this.isPlaying) {
        this.stop();
      } else {
        this.play();
      }
    },

    play: function () {
      if (!this.model) { return; }
      this.stop();
      if (typeof window !== 'undefined' && window.studioAudio) { window.studioAudio.takeOver(); }   // one thing plays at a time

      var ctx = getAudioContext();
      if (ctx && ctx.state === 'suspended') {
        ctx.resume().catch(function () {});
      }

      var self = this;
      var playBtn = document.getElementById('roll-play');

      // Preload missing samples so playback never falls back to primitive beeps
      if (currentInstrument !== 'synth' && this.model) {
        var allPitches = getAllModelPitches(this.model);
        var missingPitches = [];
        for (var ni = 0; ni < allPitches.length; ni++) {
          var p = allPitches[ni];
          var sName = midiToSampleName(clampPitch(p));
          if (sName && !sampleCache[currentInstrument + '_' + sName]) {
            missingPitches.push(p);
          }
        }
        if (missingPitches.length > 0) {
          if (playBtn) { playBtn.textContent = '⏳ Loading...'; }
          preloadSamplesForNotes(missingPitches, currentInstrument).then(function () {
            self._startPlayback(ctx);
          }).catch(function () {
            self._startPlayback(ctx);
          });
          return;
        }
      }

      this._startPlayback(ctx);
    },

    _startPlayback: function (ctx) {
      var ticksPerBar = this.model.ticksPerBar || 16;
      var unitLength = this.model.unitLength || 16;
      var bpm = this.model.bpm || 120;
      var ticksPerBeat = Math.max(1, Math.round(unitLength / 4));
      var secondsPerTick = (60 / bpm) / ticksPerBeat;
      var totalTicks = this.getTotalTicks();

      if (this.playheadTick >= totalTicks) {
        this.playheadTick = 0;
      }

      this.isPlaying = true;
      var playBtn = document.getElementById('roll-play');
      if (playBtn) {
        playBtn.textContent = '⏸ Pause';
        playBtn.title = 'Pause (Space)';
      }

      var self = this;
      var startTick = this.playheadTick;
      var startTime = performance.now();
      var baseAudioTime = (ctx ? ctx.currentTime : 0) + 0.05;
      var LOOKAHEAD_TICKS = Math.max(8, Math.ceil(0.5 / secondsPerTick));
      var scheduledUpToTick = startTick;

      function scheduleNotes(fromTick, toTick) {
        if (!ctx || !self.model || !self.model.notes) { return; }
        for (var i = 0; i < self.model.notes.length; i++) {
          var note = self.model.notes[i];
          if (note.startTick >= fromTick && note.startTick < toTick) {
            var noteOffsetSec = (note.startTick - startTick) * secondsPerTick;
            var targetAudioTime = baseAudioTime + noteOffsetSec;
            if (targetAudioTime < ctx.currentTime) {
              targetAudioTime = ctx.currentTime;
            }
            var noteDur = note.durationTicks * secondsPerTick;
            playTone(note.pitch, noteDur, note.voice, targetAudioTime);
          }
        }
      }

      function scheduleClicks(fromTick, toTick) {
        if (!self.metronomeEnabled || !ctx) { return; }
        var startBeat = Math.ceil(fromTick / ticksPerBeat) * ticksPerBeat;
        for (var bt = startBeat; bt < toTick && bt < totalTicks; bt += ticksPerBeat) {
          var isDownbeat = (bt % ticksPerBar === 0);
          var clickOffsetSec = (bt - startTick) * secondsPerTick;
          var targetAudioTime = baseAudioTime + clickOffsetSec;
          if (targetAudioTime < ctx.currentTime) {
            targetAudioTime = ctx.currentTime;
          }
          playClick(isDownbeat, targetAudioTime);
        }
      }

      function scheduleChords(fromTick, toTick) {
        if (!self.chordsEnabled || !ctx || !self.model || !self.model.chords || self.model.chords.length === 0) { return; }
        var seen = {};
        var chords = [];
        for (var ci = 0; ci < self.model.chords.length; ci++) {
          var ch = self.model.chords[ci];
          var k = ch.barIndex + ':' + ch.tickInBar + ':' + ch.name;
          if (!seen[k]) {
            seen[k] = true;
            chords.push(ch);
          }
        }
        chords.sort(function (a, b) {
          var at = a.barIndex * ticksPerBar + a.tickInBar;
          var bt = b.barIndex * ticksPerBar + b.tickInBar;
          return at - bt;
        });

        for (var i = 0; i < chords.length; i++) {
          var chord = chords[i];
          var chordStartTick = chord.barIndex * ticksPerBar + chord.tickInBar;
          if (chordStartTick >= fromTick && chordStartTick < toTick) {
            var nextTick = (i + 1 < chords.length)
              ? (chords[i + 1].barIndex * ticksPerBar + chords[i + 1].tickInBar)
              : ((chord.barIndex + 1) * ticksPerBar);
            var chordDurTicks = Math.max(ticksPerBar / 4, nextTick - chordStartTick);
            var chordOffsetSec = (chordStartTick - startTick) * secondsPerTick;
            var targetAudioTime = baseAudioTime + chordOffsetSec;
            if (targetAudioTime < ctx.currentTime) {
              targetAudioTime = ctx.currentTime;
            }
            var chordDurSec = chordDurTicks * secondsPerTick;
            var pitches = chordToMidiPitches(chord.name);
            if (pitches.length > 0) {
              playChord(pitches, chordDurSec, targetAudioTime);
            }
          }
        }
      }

      // Schedule initial chunk
      scheduleNotes(startTick, startTick + LOOKAHEAD_TICKS);
      scheduleClicks(startTick, startTick + LOOKAHEAD_TICKS);
      scheduleChords(startTick, startTick + LOOKAHEAD_TICKS);
      scheduledUpToTick = startTick + LOOKAHEAD_TICKS;

      // Visual animation & scheduling loop
      function tickLoop() {
        if (!self.isPlaying) { return; }
        var now = performance.now();
        var elapsedSec = (now - startTime) / 1000;
        var currentTick = startTick + (elapsedSec / secondsPerTick);

        if (currentTick >= totalTicks) {
          self.stop();
          self.seekTick(0);
          return;
        }

        var lookaheadTick = currentTick + LOOKAHEAD_TICKS;
        if (lookaheadTick > scheduledUpToTick) {
          scheduleNotes(scheduledUpToTick, lookaheadTick);
          scheduleClicks(scheduledUpToTick, lookaheadTick);
          scheduleChords(scheduledUpToTick, lookaheadTick);
          scheduledUpToTick = lookaheadTick;
        }

        self.playheadTick = Math.floor(currentTick);
        self.updatePlayhead(currentTick);
        self.playTimer = requestAnimationFrame(tickLoop);
      }

      this.playTimer = requestAnimationFrame(tickLoop);
      this.updatePlayhead(startTick);
    },

    // The cursor for audio that plays elsewhere (the studio audio, which comes from the main
    // player): it follows that player's clock, which starts with the score's first tick.
    followAudio: function (audio) {
      if (!this.model || !audio || this._following) { return; }
      var self = this;
      var ticksPerBeat = Math.max(1, Math.round((this.model.unitLength || 16) / 4));
      var secondsPerTick = (60 / (this.model.bpm || 120)) / ticksPerBeat;
      this._following = true;
      function loop() {
        if (!self._following) { return; }
        if (audio.paused) { self._following = false; return; }
        var tick = Math.min(audio.currentTime / secondsPerTick, self.getTotalTicks());
        self.playheadTick = Math.floor(tick);
        self.updatePlayhead(tick);
        self._followTimer = requestAnimationFrame(loop);
      }
      loop();
    },

    stopFollowing: function () {
      this._following = false;
      if (this._followTimer) {
        cancelAnimationFrame(this._followTimer);
        this._followTimer = null;
      }
    },

    stop: function () {
      this.stopFollowing();
      this.isPlaying = false;
      if (this.playTimer) {
        cancelAnimationFrame(this.playTimer);
        this.playTimer = null;
      }
      stopAllAudio();
      if (typeof document !== 'undefined') {
        var playBtn = document.getElementById('roll-play');
        if (playBtn) {
          playBtn.textContent = '▶ Play';
          playBtn.title = 'Play (Space)';
        }
        var ballEl = document.getElementById('roll-dancing-ball');
        if (ballEl) { ballEl.classList.add('hidden'); }
        var oldLyr = document.querySelector('.roll-lyric-item.illuminated');
        if (oldLyr) { oldLyr.classList.remove('illuminated'); }
        var oldNote = document.querySelector('.roll-note.singing-now');
        if (oldNote) { oldNote.classList.remove('singing-now'); }
        this._currentIlluminatedNoteId = null;
      }
      this.updatePlayhead();
    },

    seekTick: function (tick) {
      if (typeof window !== 'undefined' && window.studioAudio && window.studioAudio.seekTick(tick)) {
        this.playheadTick = Math.max(0, tick);
        this.updatePlayhead();
        this.ensurePlayheadVisible();
        return;
      }
      var wasPlaying = this.isPlaying;
      if (wasPlaying) {
        this.stop();
      }
      this.playheadTick = Math.max(0, tick);
      this.updatePlayhead();
      this.ensurePlayheadVisible();
      if (wasPlaying) {
        this.play();
      }
    },

    stepPrev: function () {
      var ticksPerBar = (this.model && this.model.ticksPerBar) || 16;
      var curBar = Math.floor(this.playheadTick / ticksPerBar);
      var inBar = this.playheadTick % ticksPerBar;
      var targetBar = inBar > 0 ? curBar : Math.max(0, curBar - 1);
      this.seekTick(targetBar * ticksPerBar);
    },

    stepNext: function () {
      var ticksPerBar = (this.model && this.model.ticksPerBar) || 16;
      var curBar = Math.floor(this.playheadTick / ticksPerBar);
      var targetBar = curBar + 1;
      this.seekTick(targetBar * ticksPerBar);
    },

    rewindToStart: function () {
      this.seekTick(0);
    },

    ensurePlayheadVisible: function () {
      if (typeof document === 'undefined') { return; }
      var scrollEl = document.getElementById('roll-grid-scroll');
      if (!scrollEl) { return; }
      var left = this.playheadTick * this.tickWidth;
      var viewW = scrollEl.clientWidth || 600;
      var curScroll = scrollEl.scrollLeft;
      if (left < curScroll || left > curScroll + viewW - 60) {
        scrollEl.scrollLeft = Math.max(0, left - 60);
      }
    },

    updatePlayhead: function (continuousTick) {
      if (typeof document === 'undefined') { return; }
      var playhead = document.getElementById('roll-playhead');
      var rulerPlayhead = document.getElementById('roll-ruler-playhead');
      var timeEl = document.getElementById('roll-time');
      var ticksPerBar = (this.model && this.model.ticksPerBar) || 16;
      var unitLength = (this.model && this.model.unitLength) || 16;
      var bpm = (this.model && this.model.bpm) || 120;
      var ticksPerBeat = Math.max(1, unitLength / 4);
      var secondsPerTick = (60 / bpm) / ticksPerBeat;

      var curTick = continuousTick !== undefined ? continuousTick : this.playheadTick;
      var left = curTick * this.tickWidth;

      if (playhead) {
        playhead.style.left = left + 'px';
      }
      if (rulerPlayhead) {
        rulerPlayhead.style.left = left + 'px';
      }

      if (timeEl) {
        var intTick = Math.max(0, Math.floor(curTick));
        var beatsPerBar = (this.model && this.model.meterNum) || 4;
        var barNum = Math.floor(intTick / ticksPerBar) + 1;
        var beatNum = Math.floor((intTick % ticksPerBar) / Math.max(1, ticksPerBar / beatsPerBar)) + 1;
        var totalSec = Math.floor(intTick * secondsPerTick);
        var mins = Math.floor(totalSec / 60);
        var secs = totalSec % 60;
        var timeStr = mins + ':' + (secs < 10 ? '0' : '') + secs;
        timeEl.textContent = barNum + '.' + beatNum + ' (' + timeStr + ')';
      }

      // Dancing ball & singing illumination
      var ballEl = document.getElementById('roll-dancing-ball');
      var activeVocalNote = null;
      if (this.model && this.model.notes) {
        for (var ni = 0; ni < this.model.notes.length; ni++) {
          var vn = this.model.notes[ni];
          if (vn.voice === 'Vocal' && curTick >= vn.startTick && curTick < (vn.startTick + vn.durationTicks)) {
            activeVocalNote = vn;
            break;
          }
        }
      }

      if (activeVocalNote) {
        var activeId = activeVocalNote.id;
        if (this._currentIlluminatedNoteId !== activeId) {
          if (this._currentIlluminatedNoteId !== null) {
            var prevLyr = document.querySelector('.roll-lyric-item.illuminated');
            if (prevLyr) { prevLyr.classList.remove('illuminated'); }
            var prevNote = document.querySelector('.roll-note.singing-now');
            if (prevNote) { prevNote.classList.remove('singing-now'); }
          }
          var curLyr = document.querySelector('.roll-lyric-item[data-note-id="' + activeId + '"]');
          if (curLyr) { curLyr.classList.add('illuminated'); }
          var curNote = document.querySelector('.roll-note[data-note-id="' + activeId + '"]');
          if (curNote) { curNote.classList.add('singing-now'); }
          this._currentIlluminatedNoteId = activeId;
        }

        if (ballEl) {
          if (this.isPlaying) {
            var dur = Math.max(1, activeVocalNote.durationTicks);
            var progress = (curTick - activeVocalNote.startTick) / dur;
            progress = Math.max(0, Math.min(1, progress));
            var noteLeft = activeVocalNote.startTick * this.tickWidth;
            var noteWidth = activeVocalNote.durationTicks * this.tickWidth;
            var pad = Math.min(10, noteWidth * 0.25);
            var ballX = (noteLeft + pad) + progress * Math.max(0, noteWidth - 2 * pad);
            var bounceY = 6 - Math.sin(progress * Math.PI) * 6;
            ballEl.style.transform = 'translate3d(' + ballX + 'px, ' + bounceY + 'px, 0)';
            ballEl.classList.remove('hidden');
          } else {
            ballEl.classList.add('hidden');
          }
        }
      } else {
        if (this._currentIlluminatedNoteId !== null) {
          var oldLyr = document.querySelector('.roll-lyric-item.illuminated');
          if (oldLyr) { oldLyr.classList.remove('illuminated'); }
          var oldNote = document.querySelector('.roll-note.singing-now');
          if (oldNote) { oldNote.classList.remove('singing-now'); }
          this._currentIlluminatedNoteId = null;
        }
        if (ballEl) {
          ballEl.classList.add('hidden');
        }
      }

      if (this.isPlaying) {
        var scrollEl = document.getElementById('roll-grid-scroll');
        if (scrollEl) {
          var viewW = scrollEl.clientWidth || 600;
          var curScroll = scrollEl.scrollLeft;
          if (left > curScroll + viewW - 80) {
            scrollEl.scrollLeft = left - 60;
          } else if (left < curScroll) {
            scrollEl.scrollLeft = Math.max(0, left - 60);
          }
        }
      }
    },

    /* ------------------------------------------------ Score Gap Filling & Compaction */
    fillGapsFromChords: function (targetVoice) {
      if (!this.model) { return 0; }
      targetVoice = targetVoice || 'Ins';
      var ticksPerBar = this.model.ticksPerBar || 16;
      var maxBar = 0;
      for (var n = 0; n < this.model.notes.length; n++) {
        var note = this.model.notes[n];
        var endB = Math.floor((note.startTick + note.durationTicks - 1) / ticksPerBar);
        if (endB > maxBar) { maxBar = endB; }
      }
      for (var c = 0; c < this.model.chords.length; c++) {
        if (this.model.chords[c].barIndex > maxBar) { maxBar = this.model.chords[c].barIndex; }
      }

      var chordsByBar = {};
      for (var ci = 0; ci < this.model.chords.length; ci++) {
        var ch = this.model.chords[ci];
        if (!chordsByBar[ch.barIndex]) { chordsByBar[ch.barIndex] = []; }
        var exists = false;
        for (var cbi = 0; cbi < chordsByBar[ch.barIndex].length; cbi++) {
          if (chordsByBar[ch.barIndex][cbi].tickInBar === ch.tickInBar && chordsByBar[ch.barIndex][cbi].name === ch.name) {
            exists = true;
            break;
          }
        }
        if (!exists) { chordsByBar[ch.barIndex].push(ch); }
      }

      var filledBars = 0;
      var nextId = Date.now();

      for (var b = 0; b <= maxBar; b++) {
        var hasNotes = false;
        for (var ni = 0; ni < this.model.notes.length; ni++) {
          var nt = this.model.notes[ni];
          if (nt.voice !== targetVoice) { continue; }
          var nStart = Math.floor(nt.startTick / ticksPerBar);
          var nEnd = Math.floor((nt.startTick + nt.durationTicks - 1) / ticksPerBar);
          if (b >= nStart && b <= nEnd) {
            hasNotes = true;
            break;
          }
        }
        if (hasNotes) { continue; }

        var barChords = chordsByBar[b];
        if (!barChords || barChords.length === 0) {
          for (var pb = b - 1; pb >= 0; pb--) {
            if (chordsByBar[pb] && chordsByBar[pb].length > 0) {
              var lastKnown = chordsByBar[pb][chordsByBar[pb].length - 1];
              barChords = [{ barIndex: b, tickInBar: 0, name: lastKnown.name }];
              break;
            }
          }
        }
        if (!barChords || barChords.length === 0) { continue; }

        barChords.sort(function (x, y) { return x.tickInBar - y.tickInBar; });

        for (var bci = 0; bci < barChords.length; bci++) {
          var barCh = barChords[bci];
          var startT = b * ticksPerBar + barCh.tickInBar;
          var nextT = (bci + 1 < barChords.length)
            ? (b * ticksPerBar + barChords[bci + 1].tickInBar)
            : ((b + 1) * ticksPerBar);
          var chDur = nextT - startT;
          var pitches = chordToMidiPitches(barCh.name);
          if (pitches.length === 0) { continue; }

          var bassPitch = pitches[0];
          var triadRoot = pitches[1];
          var triadThird = pitches[2] || (triadRoot + 4);
          var triadFifth = pitches[3] || (triadRoot + 7);

          if (chDur >= 16) {
            var pat16 = [bassPitch + 12, triadThird, triadFifth, triadThird];
            for (var p1 = 0; p1 < 4; p1++) {
              this.model.notes.push({
                id: nextId++,
                voice: targetVoice,
                pitch: pat16[p1],
                startTick: startT + (p1 * 4),
                durationTicks: 4,
                lyric: ''
              });
            }
          } else if (chDur >= 8) {
            var pat8 = [bassPitch + 12, triadFifth];
            for (var p2 = 0; p2 < 2; p2++) {
              this.model.notes.push({
                id: nextId++,
                voice: targetVoice,
                pitch: pat8[p2],
                startTick: startT + (p2 * 4),
                durationTicks: 4,
                lyric: ''
              });
            }
          } else {
            this.model.notes.push({
              id: nextId++,
              voice: targetVoice,
              pitch: bassPitch + 12,
              startTick: startT,
              durationTicks: chDur,
              lyric: ''
            });
          }
        }
        filledBars++;
      }

      if (filledBars > 0) {
        this.commitEdit();
        if (typeof window !== 'undefined' && window.toast) {
          window.toast('Harmonized ' + filledBars + ' empty bar' + (filledBars > 1 ? 's' : '') + ' from chords in ' + targetVoice);
        }
      } else {
        if (typeof window !== 'undefined' && window.toast) {
          window.toast('No empty bars found to harmonize in ' + targetVoice);
        }
      }
      return filledBars;
    },

    compactEmptyBars: function () {
      if (!this.model) { return 0; }
      var ticksPerBar = this.model.ticksPerBar || 16;
      var maxBar = 0;
      for (var n = 0; n < this.model.notes.length; n++) {
        var note = this.model.notes[n];
        var endB = Math.floor((note.startTick + note.durationTicks - 1) / ticksPerBar);
        if (endB > maxBar) { maxBar = endB; }
      }
      for (var c = 0; c < this.model.chords.length; c++) {
        if (this.model.chords[c].barIndex > maxBar) { maxBar = this.model.chords[c].barIndex; }
      }

      var emptyBars = [];
      for (var b = 0; b <= maxBar; b++) {
        var hasAnyNote = false;
        for (var ni = 0; ni < this.model.notes.length; ni++) {
          var nt = this.model.notes[ni];
          var nStart = Math.floor(nt.startTick / ticksPerBar);
          var nEnd = Math.floor((nt.startTick + nt.durationTicks - 1) / ticksPerBar);
          if (b >= nStart && b <= nEnd) {
            hasAnyNote = true;
            break;
          }
        }
        if (!hasAnyNote) {
          emptyBars.push(b);
        }
      }

      if (emptyBars.length === 0) {
        if (typeof window !== 'undefined' && window.toast) {
          window.toast('No empty bars to compact');
        }
        return 0;
      }

      emptyBars.sort(function (a, b) { return b - a; });

      for (var ei = 0; ei < emptyBars.length; ei++) {
        var eb = emptyBars[ei];
        var shiftTicks = ticksPerBar;
        var barStartTick = eb * ticksPerBar;

        for (var nIdx = 0; nIdx < this.model.notes.length; nIdx++) {
          if (this.model.notes[nIdx].startTick >= (barStartTick + shiftTicks)) {
            this.model.notes[nIdx].startTick -= shiftTicks;
          }
        }

        this.model.chords = this.model.chords.filter(function (ch) { return ch.barIndex !== eb; });
        for (var chIdx = 0; chIdx < this.model.chords.length; chIdx++) {
          if (this.model.chords[chIdx].barIndex > eb) {
            this.model.chords[chIdx].barIndex -= 1;
          }
        }

        for (var sIdx = 0; sIdx < this.model.sections.length; sIdx++) {
          if (this.model.sections[sIdx].barIndex > eb) {
            this.model.sections[sIdx].barIndex -= 1;
          }
        }
      }

      this.commitEdit();
      if (typeof window !== 'undefined' && window.toast) {
        window.toast('Removed ' + emptyBars.length + ' empty bar' + (emptyBars.length > 1 ? 's' : '') + ' and compacted score');
      }
      return emptyBars.length;
    },

    /* ------------------------------------------------ Lyrics Management */
    editLyricForNote: function (noteId) {
      if (!this.model) { return; }
      var note = this.findNote(noteId);
      if (!note || note.voice !== 'Vocal') { return; }
      var currentVal = note.lyric || "";
      var pitchName = midiToNoteName(note.pitch, this.model && this.model.key);
      var entered = window.prompt("Lyric syllable/word for note " + pitchName + "\n(Tip: enter space- or hyphen-separated syllables to fill subsequent notes):", currentVal);
      if (entered === null) { return; }
      entered = entered.trim();

      if (!entered) {
        delete note.lyric;
        this.commitEdit();
        return;
      }

      var tokRe = /([^\s-]+-?|\*|_)/g;
      var tokens = [];
      var tm;
      while ((tm = tokRe.exec(entered)) !== null) {
        var tok = tm[1].trim();
        if (tok && tok !== '-') {
          tokens.push(tok);
        }
      }

      if (tokens.length <= 1) {
        if (entered === '*' || entered === '_') {
          delete note.lyric;
        } else {
          note.lyric = entered;
        }
        this.commitEdit();
        return;
      }

      // Distribute multiple tokens across subsequent vocal notes
      var vocalNotes = this.model.notes.filter(function (n) { return n.voice === 'Vocal'; });
      vocalNotes.sort(function (a, b) { return a.startTick - b.startTick; });
      var startIdx = -1;
      for (var vi = 0; vi < vocalNotes.length; vi++) {
        if (vocalNotes[vi].id === note.id) {
          startIdx = vi;
          break;
        }
      }

      if (startIdx !== -1) {
        for (var t = 0; t < tokens.length && (startIdx + t) < vocalNotes.length; t++) {
          var targetNote = vocalNotes[startIdx + t];
          var tokenVal = tokens[t];
          if (tokenVal === '*' || tokenVal === '_') {
            delete targetNote.lyric;
          } else {
            targetNote.lyric = tokenVal;
          }
        }
      } else {
        note.lyric = tokens[0];
      }

      this.commitEdit();
    },

    editSelectedNoteLyric: function () {
      var id = (this.selectedNoteIds && this.selectedNoteIds.length > 0) ? this.selectedNoteIds[0] : this.selectedNoteId;
      if (!id) { return; }
      this.editLyricForNote(id);
    },

    matchSongLyrics: function (explicitLyrics, silent) {
      if (!this.model) { return; }
      var lyricsText = explicitLyrics;
      if (typeof lyricsText !== 'string') {
        var bigLyricsEl = document.getElementById('lyrics-big');
        var stdLyricsEl = document.getElementById('lyrics');
        if (bigLyricsEl && bigLyricsEl.value && bigLyricsEl.value.trim()) {
          lyricsText = bigLyricsEl.value.trim();
        } else if (stdLyricsEl && stdLyricsEl.value && stdLyricsEl.value.trim()) {
          lyricsText = stdLyricsEl.value.trim();
        }
      }

      if (!lyricsText || !lyricsText.trim()) {
        if (silent) { return; }
        var entered = window.prompt("No song lyrics found in editor. Paste lyrics below to match to vocal melody notes:");
        if (!entered || !entered.trim()) { return; }
        lyricsText = entered.trim();
      }

      var vocalNotes = this.model.notes.filter(function (n) { return n.voice === 'Vocal'; });
      if (vocalNotes.length === 0) {
        if (!silent && window.alert) { window.alert("No Vocal notes in this score to match lyrics to."); }
        return;
      }
      vocalNotes.sort(function (a, b) { return a.startTick - b.startTick; });

      var lyricSections = extractLyricsSections(lyricsText);
      var ticksPerBar = this.model.ticksPerBar || 16;
      var assignedCount = 0;

      // Group vocal notes by score section
      var scoreSections = this.model.sections.slice().sort(function (a, b) { return a.barIndex - b.barIndex; });
      var vocalScoreSections = [];

      for (var si = 0; si < scoreSections.length; si++) {
        var sSec = scoreSections[si];
        var nextBar = (si + 1 < scoreSections.length) ? scoreSections[si + 1].barIndex : Infinity;
        var startTick = sSec.barIndex * ticksPerBar;
        var endTick = nextBar * ticksPerBar;

        var secNotes = vocalNotes.filter(function (n) {
          return n.startTick >= startTick && n.startTick < endTick;
        });
        if (secNotes.length > 0) {
          vocalScoreSections.push({
            barIndex: sSec.barIndex,
            text: sSec.text,
            notes: secNotes
          });
        }
      }

      // If the score has fewer vocal sections than the lyrics, subdivide coarse sections at vocal pauses
      if (vocalScoreSections.length > 0 && vocalScoreSections.length < lyricSections.length) {
        var refinedSections = [];
        for (var vi = 0; vi < vocalScoreSections.length; vi++) {
          var secItem = vocalScoreSections[vi];
          var notes = secItem.notes;
          var splits = [0];
          var lastB = Math.floor(notes[0].startTick / ticksPerBar);
          for (var ni = 0; ni < notes.length - 1; ni++) {
            var e1 = notes[ni].startTick + notes[ni].durationTicks;
            var s2 = notes[ni + 1].startTick;
            var gap = s2 - e1;
            var b2 = Math.floor(s2 / ticksPerBar);
            if ((gap >= 5 || (b2 - lastB) >= 14) && (b2 - lastB) >= 6) {
              splits.push(ni + 1);
              lastB = b2;
            }
          }
          splits.push(notes.length);
          if (splits.length > 2) {
            for (var sp = 0; sp < splits.length - 1; sp++) {
              var subNotes = notes.slice(splits[sp], splits[sp + 1]);
              if (subNotes.length > 0) {
                var subBar = Math.floor(subNotes[0].startTick / ticksPerBar);
                refinedSections.push({
                  barIndex: subBar,
                  text: sp === 0 ? secItem.text : "% verse",
                  notes: subNotes
                });
              }
            }
          } else {
            refinedSections.push(secItem);
          }
        }
        if (refinedSections.length > vocalScoreSections.length) {
          vocalScoreSections = refinedSections;
          // Reflect refined sections in model
          var newSecMap = {};
          for (var rsi = 0; rsi < refinedSections.length; rsi++) {
            newSecMap[refinedSections[rsi].barIndex] = refinedSections[rsi].text;
          }
          for (var osi = 0; osi < this.model.sections.length; osi++) {
            newSecMap[this.model.sections[osi].barIndex] = this.model.sections[osi].text;
          }
          this.model.sections = Object.keys(newSecMap).map(function (b) {
            return { barIndex: parseInt(b, 10), text: newSecMap[b] };
          }).sort(function (a, b) { return a.barIndex - b.barIndex; });
        }
      }

      // Chronological alignment: assign lyric sections monotonically to vocal score sections
      if (vocalScoreSections.length > 0 && lyricSections.length > 0) {
        var currLyricIdx = 0;
        var numScore = vocalScoreSections.length;
        var numLyric = lyricSections.length;

        for (var vsi = 0; vsi < numScore; vsi++) {
          var targetSec = vocalScoreSections[vsi];
          var targetNotes = targetSec.notes;
          if (!targetNotes || targetNotes.length === 0) { continue; }

          var remScore = numScore - vsi;
          var remLyric = numLyric - currLyricIdx;

          if (remLyric <= 0) {
            for (var ek = 0; ek < targetNotes.length; ek++) { delete targetNotes[ek].lyric; }
            continue;
          }

          var linesToAssign = [];
          if (remScore <= 1) {
            for (var li = currLyricIdx; li < numLyric; li++) {
              linesToAssign = linesToAssign.concat(lyricSections[li].lines);
            }
            currLyricIdx = numLyric;
          } else if (remScore <= remLyric) {
            var takeCount = Math.floor(remLyric / remScore);
            for (var li2 = currLyricIdx; li2 < currLyricIdx + takeCount; li2++) {
              linesToAssign = linesToAssign.concat(lyricSections[li2].lines);
            }
            currLyricIdx += takeCount;
          } else {
            linesToAssign = lyricSections[currLyricIdx].lines;
            currLyricIdx++;
          }

          if (linesToAssign.length > 0) {
            assignedCount += assignLyricsToVocalNotes(linesToAssign, targetNotes, ticksPerBar);
          }
        }
      }

      // If section-by-section didn't assign any notes, do phrase-aware global match
      if (assignedCount === 0) {
        var allLines = [];
        for (var lsi = 0; lsi < lyricSections.length; lsi++) {
          allLines = allLines.concat(lyricSections[lsi].lines);
        }
        assignedCount += assignLyricsToVocalNotes(allLines, vocalNotes, ticksPerBar);
      }

      this.commitEdit();
      if (!silent && global.toast) {
        global.toast('Matched ' + assignedCount + ' lyric words to vocal notes');
      }
    },

    /* ------------------------------------------------ Commit Changes */
    commitEdit: function () {
      if (!this.model) { return; }
      var newAbc = serializeToAbc(this.model);
      this.renderAll();

      // Notify external subscribers (e.g. app.js)
      for (var i = 0; i < this.listeners.length; i++) {
        try {
          this.listeners[i](newAbc);
        } catch (err) {
          console.error("PianoRoll listener error:", err);
        }
      }
    },

    onUpdate: function (cb) {
      this.listeners.push(cb);
    }
  };

  function extractLyricsSections(lyricsText) {
    var sections = [];
    var currentSec = { name: '', lines: [] };
    var rawLines = (lyricsText || '').split(/\r?\n/);
    var skippingScraper = false;
    for (var i = 0; i < rawLines.length; i++) {
      var line = rawLines[i].trim();
      if (!line) {
        if (skippingScraper) { skippingScraper = false; }
        continue;
      }
      var tagMatch = line.match(/^(?:(?:\*{1,2}\s*)?\[([^\]]+)\](?:\s*\*{1,2})?|(?:#{1,6}|\*{1,2})\s*([A-Za-z]+(?:\s+[A-Za-z0-9_-]+)*)\s*(?:\*{1,2})?)$/);
      if (tagMatch) {
        skippingScraper = false;
        var secName = (tagMatch[1] || tagMatch[2]).trim();
        var pendingDanglingLine = null;
        if (currentSec.lines.length > 0) {
          var lastLine = currentSec.lines[currentSec.lines.length - 1];
          if (/\b(?:the|a|an|and|to|it|of|in|that|with|for|or|as|by|on|at|so)\s*$/i.test(lastLine)) {
            pendingDanglingLine = currentSec.lines.pop();
          }
        }
        if (currentSec.name || currentSec.lines.length > 0) {
          sections.push(currentSec);
        }
        currentSec = { name: secName, lines: [] };
        if (pendingDanglingLine) {
          currentSec.pendingPrefix = pendingDanglingLine;
        }
      } else {
        if (/^(\d+\s+Contributors?|Embed|\d+\s+Translations?)$/i.test(line)) {
          continue;
        }
        if (/^You might also like/i.test(line)) {
          skippingScraper = true;
          continue;
        }
        if (skippingScraper) {
          continue;
        }
        if (currentSec.pendingPrefix) {
          var prefix = currentSec.pendingPrefix;
          delete currentSec.pendingPrefix;
          if (/^[a-z]/.test(line)) {
            line = prefix + ' ' + line;
          } else {
            currentSec.lines.push(prefix);
          }
        }
        currentSec.lines.push(line);
      }
    }
    if (currentSec.pendingPrefix) {
      currentSec.lines.unshift(currentSec.pendingPrefix);
      delete currentSec.pendingPrefix;
    }
    if (currentSec.name || currentSec.lines.length > 0) {
      sections.push(currentSec);
    }
    return sections;
  }

  function splitWordSyllables(word) {
    if (!word) { return []; }
    // If already hyphenated, keep existing hyphenation
    if (word.indexOf('-') !== -1) {
      var parts = word.split('-').filter(Boolean);
      if (parts.length === 0) { return []; }
      var endsWithHyphen = word.slice(-1) === '-';
      return parts.map(function (p, i) {
        if (i < parts.length - 1 || endsWithHyphen) {
          return p + '-';
        }
        return p;
      });
    }

    // Preserve leading and trailing punctuation
    var match = word.match(/^([^a-zA-Z]*)([a-zA-Z'’]+)([^a-zA-Z]*)$/);
    if (!match) { return [word]; }
    var prefix = match[1];
    var core = match[2];
    var suffix = match[3];

    if (core.length <= 3) { return [word]; }

    // Find vowel nuclei
    var vowels = /[aeiouy]+/gi;
    var indices = [];
    var m;
    while ((m = vowels.exec(core)) !== null) {
      indices.push({ start: m.index, end: m.index + m[0].length, str: m[0] });
    }

    var forcedCut = null;
    if (indices.length > 1) {
      var lastVowel = indices[indices.length - 1];
      var lowerCore = core.toLowerCase();
      // Silent trailing 'e' (e.g. dance, love, alone, life, take)
      if (lastVowel.end === core.length && lastVowel.str.toLowerCase() === 'e') {
        var isConsonantLe = (core.length >= 3 && lowerCore[core.length - 2] === 'l' && !/[aeiouy]/.test(lowerCore[core.length - 3]));
        if (!isConsonantLe) {
          indices.pop();
        }
      }
      // Silent 'e' in '-ed' unless preceded by 't' or 'd' (e.g. walked, dreamed vs wait-ed)
      else if (lastVowel.end === core.length - 1 && lowerCore.slice(-2) === 'ed') {
        var beforeE = lowerCore[core.length - 3];
        if (beforeE && beforeE !== 't' && beforeE !== 'd') {
          indices.pop();
        }
      }
      // Silent 'e' before suffixes -ment, -ful, -less, -ly, -ness (e.g. movement, lovely, careful, hopeless)
      else {
        var sufMatch = lowerCore.match(/^([a-z]+[aeiouy][a-z]*e)(ment|ful|less|ly|ness)$/);
        if (sufMatch) {
          var ePos = sufMatch[1].length - 1;
          for (var vi = 0; vi < indices.length; vi++) {
            if (indices[vi].start === ePos && indices[vi].str.toLowerCase() === 'e') {
              indices.splice(vi, 1);
              forcedCut = ePos + 1;
              break;
            }
          }
        }
      }
    }

    if (indices.length <= 1) { return [word]; }

    // Cut points between consecutive vowel nuclei
    var cuts = [];
    if (forcedCut !== null) {
      cuts.push(forcedCut);
    } else {
      for (var i = 0; i < indices.length - 1; i++) {
        var v1End = indices[i].end;
        var v2Start = indices[i + 1].start;
        var numConsonants = v2Start - v1End;

        if (numConsonants <= 0) {
          cuts.push(v1End);
        } else if (numConsonants === 1) {
          cuts.push(v1End);
        } else if (numConsonants === 2) {
          var pair = core.slice(v1End, v2Start).toLowerCase();
          if (/^(th|ch|sh|ph|wh|ck|qu)$/.test(pair)) {
            cuts.push(v1End);
          } else {
            cuts.push(v1End + 1);
          }
        } else {
          cuts.push(v1End + 1);
        }
      }
    }

    var syllables = [];
    var lastIdx = 0;
    for (var c = 0; c < cuts.length; c++) {
      var cutPos = cuts[c];
      if (cutPos > lastIdx && cutPos < core.length) {
        syllables.push(core.slice(lastIdx, cutPos) + '-');
        lastIdx = cutPos;
      }
    }
    if (lastIdx < core.length) {
      syllables.push(core.slice(lastIdx));
    }

    if (syllables.length === 0) { return [word]; }
    syllables[0] = prefix + syllables[0];
    syllables[syllables.length - 1] = syllables[syllables.length - 1] + suffix;
    return syllables;
  }

  function tokenizeLyricLines(lines) {
    var tokens = [];
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].replace(/\([^)]*\)/g, '').trim();
      if (!line) { continue; }
      var re = /([^\s-]+-?)/g;
      var m;
      while ((m = re.exec(line)) !== null) {
        var rawTok = m[1].trim();
        if (rawTok && rawTok !== '-') {
          var sylls = splitWordSyllables(rawTok);
          for (var s = 0; s < sylls.length; s++) {
            tokens.push(sylls[s]);
          }
        }
      }
    }
    return tokens;
  }

  function matchScoreSectionToLyricSection(scoreSecText, lyricSections, usedIndices) {
    var cleanScore = (scoreSecText || '').replace(/^%\s*/, '').toLowerCase().trim();
    if (!cleanScore) { return null; }
    for (var i = 0; i < lyricSections.length; i++) {
      if (usedIndices && usedIndices.indexOf(i) !== -1) { continue; }
      var cleanLyric = (lyricSections[i].name || '').toLowerCase().trim();
      if (cleanLyric === cleanScore) { return i; }
    }
    for (var j = 0; j < lyricSections.length; j++) {
      if (usedIndices && usedIndices.indexOf(j) !== -1) { continue; }
      var lName = (lyricSections[j].name || '').toLowerCase().trim();
      var sBase = cleanScore.replace(/\s*\d+$/, '');
      var lBase = lName.replace(/\s*\d+$/, '');
      if (sBase && lBase && (sBase === lBase || lName.indexOf(sBase) === 0 || cleanScore.indexOf(lBase) === 0)) {
        return j;
      }
    }
    // Fallback: if name differs (e.g. score has "chorus" or generic section), match next available unused section
    for (var k = 0; k < lyricSections.length; k++) {
      if (usedIndices && usedIndices.indexOf(k) !== -1) { continue; }
      return k;
    }
    return null;
  }

  function alignLinesToNotes(linesTokens, notes, ticksPerBar) {
    var L = linesTokens.length;
    var N = notes.length;
    if (L === 0 || N === 0) { return []; }
    if (L === 1) {
      return [{ lineIdx: 0, startIdx: 0, endIdx: N }];
    }

    var bScore = new Float32Array(N);
    for (var i = 1; i < N; i++) {
      var prev = notes[i - 1];
      var curr = notes[i];
      var rest = curr.startTick - (prev.startTick + prev.durationTicks);
      var s = 0;
      if (rest >= 16) { s += 100; }
      else if (rest >= 8) { s += 60; }
      else if (rest >= 4) { s += 40; }
      else if (rest >= 2) { s += 20; }
      else if (rest > 0) { s += 8; }

      if (prev.durationTicks >= 8) { s += 15; }
      else if (prev.durationTicks >= 6) { s += 8; }

      var prevBar = Math.floor(prev.startTick / ticksPerBar);
      var currBar = Math.floor(curr.startTick / ticksPerBar);
      if (currBar > prevBar) { s += 10 * (currBar - prevBar); }
      if ((curr.startTick % ticksPerBar) === 0) { s += 8; }
      bScore[i] = s;
    }

    function segCost(l, j, i) {
      var T = linesTokens[l].length;
      var M = i - j;
      if (M <= 0) { return 10000; }
      var diffCost = 0;
      if (M === T) {
        diffCost = 0;
      } else if (M > T) {
        diffCost = (M - T) * 2;
      } else {
        diffCost = (T - M) * 35;
      }
      var boundaryBonus = (j > 0) ? bScore[j] : 0;
      return diffCost - boundaryBonus;
    }

    var dp = [];
    var parent = [];
    for (var d = 0; d <= L; d++) {
      dp.push(new Float32Array(N + 1).fill(1e9));
      parent.push(new Int32Array(N + 1).fill(-1));
    }

    for (var bIdx = 1; bIdx <= N; bIdx++) {
      dp[1][bIdx] = segCost(0, 0, bIdx);
    }

    for (var l = 2; l <= L; l++) {
      for (var ni = l; ni <= N; ni++) {
        for (var pj = l - 1; pj < ni; pj++) {
          var c = dp[l - 1][pj] + segCost(l - 1, pj, ni);
          if (c < dp[l][ni]) {
            dp[l][ni] = c;
            parent[l][ni] = pj;
          }
        }
      }
    }

    var splits = [];
    var currI = N;
    for (var bl = L; bl >= 1; bl--) {
      var prevJ = (bl === 1) ? 0 : parent[bl][currI];
      if (prevJ < 0) { prevJ = 0; }
      splits.unshift({ lineIdx: bl - 1, startIdx: prevJ, endIdx: currI });
      currI = prevJ;
    }
    return splits;
  }

  function assignLyricsToVocalNotes(lines, secVocalNotes, ticksPerBar) {
    if (!lines || lines.length === 0 || !secVocalNotes || secVocalNotes.length === 0) {
      return 0;
    }
    var lineTokensList = [];
    for (var i = 0; i < lines.length; i++) {
      var toks = tokenizeLyricLines([lines[i]]);
      if (toks.length > 0) {
        lineTokensList.push(toks);
      }
    }
    if (lineTokensList.length === 0) { return 0; }

    var splits = alignLinesToNotes(lineTokensList, secVocalNotes, ticksPerBar);
    var count = 0;

    for (var s = 0; s < splits.length; s++) {
      var sp = splits[s];
      var toks = lineTokensList[sp.lineIdx];
      var segNotes = secVocalNotes.slice(sp.startIdx, sp.endIdx);
      if (segNotes.length === 0) { continue; }

      var limit = Math.min(segNotes.length, toks.length);
      for (var k = 0; k < limit; k++) {
        segNotes[k].lyric = toks[k];
        count++;
      }
      for (var ek = limit; ek < segNotes.length; ek++) {
        delete segNotes[ek].lyric;
      }
    }
    return count;
  }

  global.PianoRoll = PianoRoll;
  global.parseAbc = parseAbc;
  global.serializeToAbc = serializeToAbc;
  global.abcNoteToMidi = abcNoteToMidi;
  global.midiToAbcNote = midiToAbcNote;
  global.midiToNoteName = midiToNoteName;
  global.isFlatKey = isFlatKey;
  global.getKeyAccidentals = getKeyAccidentals;
  global.extractLyricsSections = extractLyricsSections;
  global.splitWordSyllables = splitWordSyllables;
  global.tokenizeLyricLines = tokenizeLyricLines;
  global.matchScoreSectionToLyricSection = matchScoreSectionToLyricSection;
  global.playClick = playClick;
  global.playChord = playChord;
  global.chordToMidiPitches = chordToMidiPitches;
  global.alignLinesToNotes = alignLinesToNotes;
  global.assignLyricsToVocalNotes = assignLyricsToVocalNotes;

})(typeof window !== 'undefined' ? window : this);
