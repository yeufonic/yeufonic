/* Custom Theme Builder & Live Mock-up (#82)
   Lets users create, edit, save, apply, and remove custom colour themes covering
   every token managed by Yeufonic's built-in themes, with an interactive mock-up
   of both the Main page and the Editor page. */
(function () {
  'use strict';

  var _I18N = window.I18N || { t: function (k) { return k; }, tr: function (k) { return k; } };
  var t = _I18N.t;
  var tr = _I18N.tr;

  function escHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  /* Exact hex defaults for each built-in theme, matching styles.css. */
  var BASE_DARK = {
    '--bg': '#08080b',
    '--bg-2': '#101014',
    '--panel': '#14141a',
    '--card': '#1a1a21',
    '--card-2': '#202028',
    '--card-3': '#24242e',
    '--text': '#f4f4f7',
    '--muted': '#9b9ba8',
    '--text-strong': '#ffffff',
    '--accent-a': '#7b5cff',
    '--accent-b': '#ff4d94',
    '--play-bg': '#f4f4f7',
    '--play-fg': '#101014',
    '--song-a': '#38bdf8',
    '--song-b': '#7b5cff',
    '--cover-a': '#ff4d94',
    '--cover-b': '#a855f7',
    '--inst-a': '#a3e635',
    '--inst-b': '#10b981',
    '--good': '#34d399',
    '--warn': '#fbbf24',
    '--bad': '#f87171',
    '--danger-text': '#ff8fa3',
    '--info': '#60a5fa',
    '--lit-take': '#ff9a3c',
    '--input-bg': '#0a0c11',
    '--input-border': '#2e3039',
    '--menu-bg': '#181c25',
    '--menu-head-bg': '#141820',
    '--menu-border': '#3d414d',
    '--wave-song': '#38afeb',
    '--wave-cover': '#dc649b',
    '--wave-inst': '#34c88c',
    '--wave-default': '#a78bfa'
  };

  var BASE_PRESETS = {
    dark: BASE_DARK,
    studio: Object.assign({}, BASE_DARK, {
      '--bg': '#0d0a07',
      '--bg-2': '#15110c',
      '--panel': '#1a150f',
      '--card': '#201a12',
      '--card-2': '#282016',
      '--card-3': '#30271b',
      '--text': '#f4ecdf',
      '--muted': '#ab9d86',
      '--text-strong': '#fffaf0',
      '--accent-a': '#f59e0b',
      '--accent-b': '#ef6c3a',
      '--play-bg': '#f4ecdf',
      '--play-fg': '#1a150f',
      '--input-bg': '#0c0906',
      '--input-border': '#382f26',
      '--menu-bg': '#1c1610',
      '--menu-head-bg': '#16110c',
      '--menu-border': '#44392e',
      '--wave-song': '#41afe6',
      '--wave-cover': '#e16996',
      '--wave-inst': '#3cc382',
      '--wave-default': '#af91f5'
    }),
    light: Object.assign({}, BASE_DARK, {
      '--bg': '#f4f4f8',
      '--bg-2': '#ebebf1',
      '--panel': '#ffffff',
      '--card': '#f7f7fa',
      '--card-2': '#ececf2',
      '--card-3': '#e2e2eb',
      '--text': '#17171f',
      '--muted': '#5d5d6c',
      '--text-strong': '#000000',
      '--play-bg': '#17171f',
      '--play-fg': '#ffffff',
      '--good': '#047857',
      '--warn': '#b45309',
      '--bad': '#dc2626',
      '--danger-text': '#be123c',
      '--info': '#1d4ed8',
      '--lit-take': '#c2570c',
      '--input-bg': '#edf1f7',
      '--input-border': '#bcc6d4',
      '--menu-bg': '#ffffff',
      '--menu-head-bg': '#f6f8fb',
      '--menu-border': '#aeb9c9',
      '--wave-song': '#0e74b9',
      '--wave-cover': '#b92d73',
      '--wave-inst': '#0f875a',
      '--wave-default': '#7332d7'
    }),
    contrast: Object.assign({}, BASE_DARK, {
      '--bg': '#000000',
      '--bg-2': '#000000',
      '--panel': '#0b0b0b',
      '--card': '#121212',
      '--card-2': '#1d1d1d',
      '--card-3': '#282828',
      '--text': '#ffffff',
      '--muted': '#d4d4d8',
      '--text-strong': '#ffffff',
      '--accent-a': '#a78bfa',
      '--good': '#4ade80',
      '--warn': '#fde047',
      '--bad': '#fb7185',
      '--info': '#93c5fd',
      '--play-bg': '#ffffff',
      '--play-fg': '#000000',
      '--input-bg': '#000000',
      '--input-border': '#8c8c8c',
      '--menu-bg': '#080808',
      '--menu-head-bg': '#000000',
      '--menu-border': '#a6a6a6',
      '--wave-song': '#38bdf8',
      '--wave-cover': '#ff4d94',
      '--wave-inst': '#4ade80',
      '--wave-default': '#a78bfa'
    })
  };

  function tokenGroups() {
    return [
      {
        id: 'surfaces',
        title: t('Surfaces & Chrome'),
        open: true,
        items: [
          ['--bg', t('Page background')],
          ['--bg-2', t('Secondary / player bar')],
          ['--panel', t('Panels & sidebar')],
          ['--card', t('Card surface')],
          ['--card-2', t('Card elevated')],
          ['--card-3', t('Card highlight')]
        ]
      },
      {
        id: 'text',
        title: t('Text'),
        open: true,
        items: [
          ['--text', t('Primary text')],
          ['--muted', t('Muted text')],
          ['--text-strong', t('Strong / headings')]
        ]
      },
      {
        id: 'accents',
        title: t('Accents & Play Button'),
        open: true,
        items: [
          ['--accent-a', t('Primary accent')],
          ['--accent-b', t('Secondary accent')],
          ['--play-bg', t('Play button fill')],
          ['--play-fg', t('Play button icon')]
        ]
      },
      {
        id: 'origins',
        title: t('Song, Cover & Instrumental'),
        open: false,
        items: [
          ['--song-a', t('Song primary')],
          ['--song-b', t('Song secondary')],
          ['--cover-a', t('Cover primary')],
          ['--cover-b', t('Cover secondary')],
          ['--inst-a', t('Instrumental primary')],
          ['--inst-b', t('Instrumental secondary')]
        ]
      },
      {
        id: 'status',
        title: t('Status & Highlights'),
        open: false,
        items: [
          ['--good', t('Good / playing')],
          ['--warn', t('Warning')],
          ['--bad', t('Error / danger')],
          ['--danger-text', t('Danger text')],
          ['--info', t('Info')],
          ['--lit-take', t('Inside badge')]
        ]
      },
      {
        id: 'inputs',
        title: t('Inputs & Menus'),
        open: false,
        items: [
          ['--input-bg', t('Input background')],
          ['--input-border', t('Input border')],
          ['--menu-bg', t('Menu background')],
          ['--menu-head-bg', t('Menu header')],
          ['--menu-border', t('Menu border')]
        ]
      },
      {
        id: 'waveforms',
        title: t('Waveforms'),
        open: false,
        items: [
          ['--wave-song', t('Song waveform')],
          ['--wave-cover', t('Cover waveform')],
          ['--wave-inst', t('Instrumental waveform')],
          ['--wave-default', t('Default waveform')]
        ]
      }
    ];
  }

  var GRADIENT_TOKENS = {
    '--bg': true,
    '--bg-2': true,
    '--panel': true,
    '--card': true,
    '--card-2': true,
    '--card-3': true,
    '--play-bg': true,
    '--input-bg': true,
    '--menu-bg': true,
    '--menu-head-bg': true
  };
  var GRADIENT_DIRS = ['135deg', '180deg', '90deg', 'radial'];

  function hexToRgb(hex) {
    var m = /^#?([0-9a-f]{6})$/i.exec(String(hex || '').trim());
    if (!m) { return null; }
    var n = parseInt(m[1], 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function rgbToHex(r, g, b) {
    function c(v) {
      var n = Math.max(0, Math.min(255, Math.round(v)));
      return (n < 16 ? '0' : '') + n.toString(16);
    }
    return '#' + c(r) + c(g) + c(b);
  }

  function rgbToHsl(r, g, b) {
    r /= 255; g /= 255; b /= 255;
    var max = Math.max(r, g, b), min = Math.min(r, g, b);
    var h = 0, s = 0, l = (max + min) / 2;
    if (max !== min) {
      var d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      if (max === r) { h = (g - b) / d + (g < b ? 6 : 0); }
      else if (max === g) { h = (b - r) / d + 2; }
      else { h = (r - g) / d + 4; }
      h *= 60;
    }
    return [h, s * 100, l * 100];
  }

  function hslToHex(h, s, l) {
    h = ((h % 360) + 360) % 360;
    s = Math.max(0, Math.min(100, s)) / 100;
    l = Math.max(0, Math.min(100, l)) / 100;
    var c = (1 - Math.abs(2 * l - 1)) * s;
    var x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    var m = l - c / 2;
    var r = 0, g = 0, b = 0;
    if (h < 60) { r = c; g = x; }
    else if (h < 120) { r = x; g = c; }
    else if (h < 180) { g = c; b = x; }
    else if (h < 240) { g = x; b = c; }
    else if (h < 300) { r = x; b = c; }
    else { r = c; b = x; }
    return rgbToHex((r + m) * 255, (g + m) * 255, (b + m) * 255);
  }

  function shiftHex(hex, dH, dS, dL) {
    var rgb = hexToRgb(hex);
    if (!rgb) { return hex; }
    var hsl = rgbToHsl(rgb[0], rgb[1], rgb[2]);
    return hslToHex(hsl[0] + dH, hsl[1] + dS, hsl[2] + dL);
  }

  function nudgeTowardHue(hex, targetHue) {
    var rgb = hexToRgb(hex);
    if (!rgb) { return hex; }
    var hsl = rgbToHsl(rgb[0], rgb[1], rgb[2]);
    if (hsl[1] < 8) {
      return hslToHex(targetHue, Math.min(26, hsl[1] + 18), hsl[2]);
    }
    var diff = ((targetHue - hsl[0] + 540) % 360) - 180;
    var step = Math.max(-22, Math.min(22, diff * 0.45));
    return hslToHex(hsl[0] + step, hsl[1], hsl[2]);
  }

  function suggestGradientEnd(hex) {
    var rgb = hexToRgb(hex);
    if (!rgb) { return '#1e2438'; }
    var hsl = rgbToHsl(rgb[0], rgb[1], rgb[2]);
    var dL = hsl[2] < 45 ? 11 : -10;
    var dS = hsl[1] < 12 ? 16 : 6;
    var nextH = hsl[1] < 12 ? 225 : hsl[0] + 24;
    return hslToHex(nextH, hsl[1] + dS, Math.max(4, Math.min(96, hsl[2] + dL)));
  }

  function buildGradientCss(fromHex, grad) {
    if (!fromHex || !grad || !grad.to) { return null; }
    var dir = GRADIENT_DIRS.indexOf(grad.dir) >= 0 ? grad.dir : '135deg';
    if (dir === 'radial') {
      return 'radial-gradient(circle at 18% 15%, ' + grad.to + ' 0%, ' + fromHex + ' 82%)';
    }
    return 'linear-gradient(' + dir + ', ' + fromHex + ', ' + grad.to + ')';
  }

  function rgbTriplet(hex) {
    var c = hexToRgb(hex);
    return c ? (c[0] + ' ' + c[1] + ' ' + c[2]) : null;
  }

  function rgbaStr(hex, alpha) {
    var c = hexToRgb(hex);
    return c ? ('rgba(' + c[0] + ', ' + c[1] + ', ' + c[2] + ', ' + alpha + ')') : null;
  }

  function normalizeHex(val) {
    var s = String(val || '').trim();
    if (/^#[0-9a-f]{3}$/i.test(s)) {
      return ('#' + s[1] + s[1] + s[2] + s[2] + s[3] + s[3]).toLowerCase();
    }
    if (/^#[0-9a-f]{6}$/i.test(s)) {
      return s.toLowerCase();
    }
    return null;
  }

  /* Expand a custom theme's { base, colors, gradients } into the full set of CSS custom
     properties needed by styles.css (including derived *-rgb, *-grad, and waveform alphas). */
  function expandVars(base, colors, gradients) {
    var preset = BASE_PRESETS[base] || BASE_PRESETS.studio;
    var merged = Object.assign({}, preset, colors || {});
    var vars = {};
    var direct = [
      '--bg', '--bg-2', '--panel', '--card', '--card-2', '--card-3',
      '--text', '--muted', '--text-strong',
      '--accent-a', '--accent-b', '--play-bg', '--play-fg',
      '--song-a', '--song-b', '--cover-a', '--cover-b', '--inst-a', '--inst-b',
      '--good', '--warn', '--bad', '--danger-text', '--info', '--lit-take',
      '--input-bg', '--input-border', '--menu-bg', '--menu-head-bg', '--menu-border'
    ];
    direct.forEach(function (k) {
      if (merged[k]) { vars[k] = merged[k]; }
    });
    // Optional surface & fill gradients (base hex remains intact for borders & color-mix)
    var grads = gradients || {};
    Object.keys(GRADIENT_TOKENS).forEach(function (k) {
      if (grads[k] && grads[k].to && merged[k]) {
        var css = buildGradientCss(merged[k], grads[k]);
        if (css) { vars[k + '-grad'] = css; }
      }
    });
    // Ensure Studio Slate panel/input backgrounds follow the custom theme too
    vars['--ui-panel-bg'] = vars['--panel-grad'] || merged['--panel'];
    vars['--ui-input-bg'] = vars['--input-bg-grad'] || merged['--input-bg'];
    vars['--accent'] = merged['--accent-a'];
    vars['--song'] = merged['--song-a'];
    vars['--play-bg-hover'] = merged['--text-strong'];

    // Derive RGB channel tokens for translucent borders, bars, glows, and hovers
    var rgbMap = {
      '--bar-rgb': merged['--bg'],
      '--bar-2-rgb': merged['--bg-2'],
      '--backdrop-rgb': merged['--bg'],
      '--ink': merged['--text'],
      '--accent-a-rgb': merged['--accent-a'],
      '--accent-b-rgb': merged['--accent-b'],
      '--song-a-rgb': merged['--song-a'],
      '--song-rgb': merged['--song-a'],
      '--good-rgb': merged['--good'],
      '--warn-rgb': merged['--warn'],
      '--bad-rgb': merged['--bad'],
      '--danger-rgb': merged['--bad'],
      '--info-rgb': merged['--info']
    };
    Object.keys(rgbMap).forEach(function (k) {
      var trip = rgbTriplet(rgbMap[k]);
      if (trip) { vars[k] = trip; }
    });

    // Derive waveform body & outline colours with base-appropriate opacity
    var bodyA = base === 'contrast' ? 0.85 : (base === 'light' ? 0.75 : 0.70);
    var outA = base === 'contrast' ? 0.45 : (base === 'light' ? 0.32 : 0.28);
    var waveMap = [
      ['--wave-song', '--wave-song-body', '--wave-song-outline'],
      ['--wave-cover', '--wave-cover-body', '--wave-cover-outline'],
      ['--wave-inst', '--wave-inst-body', '--wave-inst-outline'],
      ['--wave-default', '--wave-default-body', '--wave-default-outline']
    ];
    waveMap.forEach(function (entry) {
      var hex = merged[entry[0]];
      if (hex) {
        vars[entry[1]] = rgbaStr(hex, bodyA);
        vars[entry[2]] = rgbaStr(hex, outA);
      }
    });
    return vars;
  }

  /* Track inline custom properties applied to <html> so switching back to a
     built-in theme leaves zero leftover inline variables. */
  var APPLIED_KEYS = [];
  var CACHE_KEY = 'yue2.customThemeCache';

  function clearApplied() {
    var root = document.documentElement;
    if (!root) { return; }
    APPLIED_KEYS.forEach(function (k) { root.style.removeProperty(k); });
    APPLIED_KEYS = [];
    delete root.dataset.customTheme;
  }

  function applyCustomObject(themeObj, persistCache) {
    var root = document.documentElement;
    if (!root || !themeObj) { clearApplied(); return; }
    clearApplied();
    var base = BASE_PRESETS[themeObj.base] ? themeObj.base : 'studio';
    if (base === 'dark') { delete root.dataset.theme; } else { root.dataset.theme = base; }
    root.dataset.customTheme = themeObj.id || 'preview';
    var vars = expandVars(base, themeObj.colors || {}, themeObj.gradients || {});
    Object.keys(vars).forEach(function (k) {
      root.style.setProperty(k, vars[k]);
      APPLIED_KEYS.push(k);
    });
    if (persistCache) {
      try {
        localStorage.setItem(CACHE_KEY, JSON.stringify({ id: themeObj.id, base: base, vars: vars }));
      } catch (e) { /* private mode */ }
    }
  }

  function clearCache() {
    try { localStorage.removeItem(CACHE_KEY); } catch (e) {}
  }

  function getSavedThemes() {
    return (window.State && Array.isArray(State.customThemes)) ? State.customThemes : [];
  }

  function findSavedById(id) {
    var list = getSavedThemes();
    for (var i = 0; i < list.length; i++) {
      if (list[i].id === id) { return list[i]; }
    }
    return null;
  }

  /* ------------------------------------------------- Modal State & Rendering */
  var Builder = {
    open: false,
    editId: null,         // null when creating new, else saved theme id
    name: '',
    base: 'studio',
    colors: {},           // full hex map for all tokens
    gradients: {},        // { token: { to: '#rrggbb', dir: '135deg'|'180deg'|'90deg'|'radial' } }
    openTint: null,       // token name whose Grade/Tint drawer is expanded
    tab: 'main',          // 'main' | 'editor' | 'jam'
    waveKind: null,       // null = auto per tab, else 'song' | 'cover' | 'inst' | 'default'
    openGroups: { surfaces: true, text: true, accents: true, origins: false, status: false, inputs: false, waveforms: false },
    saving: false,
    error: ''
  };

  function cloneGradients(src) {
    var out = {};
    if (!src) { return out; }
    Object.keys(src).forEach(function (k) {
      if (GRADIENT_TOKENS[k] && src[k] && src[k].to) {
        out[k] = { to: src[k].to, dir: src[k].dir || '135deg' };
      }
    });
    return out;
  }

  function currentActiveBase() {
    var chosen = (typeof setting === 'function') ? setting('appearance.theme', 'studio') : 'studio';
    if (chosen && chosen.indexOf('custom:') === 0) {
      var found = findSavedById(chosen.slice(7));
      return (found && found.base) || 'studio';
    }
    if (chosen === 'system') {
      return (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) ? 'light' : 'dark';
    }
    return BASE_PRESETS[chosen] ? chosen : 'studio';
  }

  function openBuilder(themeId) {
    var modal = document.getElementById('theme-modal');
    if (!modal) { return; }
    var existing = themeId ? findSavedById(themeId) : null;
    if (existing) {
      Builder.editId = existing.id;
      Builder.name = existing.name;
      Builder.base = BASE_PRESETS[existing.base] ? existing.base : 'studio';
      Builder.colors = Object.assign({}, BASE_PRESETS[Builder.base], existing.colors || {});
      Builder.gradients = cloneGradients(existing.gradients);
    } else {
      Builder.editId = null;
      Builder.name = '';
      Builder.base = currentActiveBase();
      Builder.colors = Object.assign({}, BASE_PRESETS[Builder.base]);
      Builder.gradients = {};
    }
    Builder.openTint = null;
    Builder.waveKind = null;
    Builder.saving = false;
    Builder.error = '';
    Builder.open = true;
    modal.classList.remove('hidden');
    paintBuilder();
    var nameInp = document.getElementById('tm-name');
    if (nameInp && !existing) { nameInp.focus(); }
  }

  function closeBuilder() {
    var modal = document.getElementById('theme-modal');
    if (!Builder.open) { return; }
    Builder.open = false;
    if (modal) { modal.classList.add('hidden'); }
  }

  function applyDraftToStage() {
    var stage = document.getElementById('tm-stage');
    var vars = expandVars(Builder.base, Builder.colors, Builder.gradients);
    if (stage) {
      stage.dataset.theme = Builder.base;
      var uiStyle = (typeof setting === 'function') ? setting('appearance.ui_style', 'slate') : 'slate';
      if (uiStyle && uiStyle !== 'default') { stage.dataset.uiStyle = uiStyle; } else { delete stage.dataset.uiStyle; }
      Object.keys(GRADIENT_TOKENS).forEach(function (k) {
        if (!vars[k + '-grad']) { stage.style.removeProperty(k + '-grad'); }
      });
      Object.keys(vars).forEach(function (k) { stage.style.setProperty(k, vars[k]); });
    }
  }

  /* Deterministic realistic peak + RMS envelope matching app.js drawWave(). */
  var WAVE_PEAKS = [
    0.10, 0.14, 0.22, 0.30, 0.42, 0.36, 0.54, 0.62, 0.48, 0.70, 0.60, 0.44,
    0.52, 0.66, 0.58, 0.46, 0.74, 0.86, 0.78, 0.92, 0.84, 0.72, 0.88, 0.95,
    0.82, 0.76, 0.90, 0.85, 0.68, 0.74, 0.62, 0.50, 0.44, 0.56, 0.48, 0.38,
    0.46, 0.58, 0.64, 0.52, 0.68, 0.78, 0.86, 0.94, 0.88, 0.80, 0.92, 0.96,
    0.84, 0.78, 0.90, 0.82, 0.74, 0.86, 0.76, 0.64, 0.72, 0.60, 0.52, 0.46,
    0.38, 0.34, 0.28, 0.22, 0.18, 0.12, 0.08
  ];
  var WAVE_RMSS = WAVE_PEAKS.map(function (p, i) {
    var factor = 0.56 + 0.12 * Math.sin(i * 0.7);
    return Math.max(0.05, Math.min(p * 0.82, p * factor));
  });

  function wavePolygonPoints(arr, w, h) {
    var mid = h / 2;
    var amp = h * 0.46;
    var n = arr.length;
    var step = w / Math.max(1, n - 1);
    var top = [];
    var bot = [];
    for (var i = 0; i < n; i++) {
      var x = (i * step).toFixed(1);
      var dy = arr[i] * amp;
      top.push(x + ',' + (mid - dy).toFixed(1));
      bot.push(x + ',' + (mid + dy).toFixed(1));
    }
    bot.reverse();
    return top.concat(bot).join(' ');
  }

  var WAVE_OUTLINE_PTS = wavePolygonPoints(WAVE_PEAKS, 240, 32);
  var WAVE_BODY_PTS = wavePolygonPoints(WAVE_RMSS, 240, 32);

  function activeWaveKind() {
    if (Builder.waveKind) { return Builder.waveKind; }
    if (Builder.tab === 'editor') { return 'cover'; }
    if (Builder.tab === 'jam') { return 'inst'; }
    return 'song';
  }

  function mockWaveHtml(kind) {
    var k = kind || activeWaveKind();
    return '<div class="tm-wave tm-w-' + k + '" data-tm-wave="' + k + '" title="' + t('Waveforms') + '">' +
      '<svg class="tm-wave-svg" viewBox="0 0 240 32" preserveAspectRatio="none" aria-hidden="true">' +
        '<defs><clipPath id="tm-wclip"><rect x="0" y="0" width="108" height="32"/></clipPath></defs>' +
        '<polygon class="tm-w-unplayed-out" points="' + WAVE_OUTLINE_PTS + '"/>' +
        '<polygon class="tm-w-unplayed-body" points="' + WAVE_BODY_PTS + '"/>' +
        '<g clip-path="url(#tm-wclip)">' +
          '<polygon class="tm-w-played-out" points="' + WAVE_OUTLINE_PTS + '"/>' +
          '<polygon class="tm-w-played-body" points="' + WAVE_BODY_PTS + '"/>' +
        '</g>' +
        '<rect class="tm-w-head" x="108" y="0" width="1.8" height="32"/>' +
      '</svg>' +
    '</div>';
  }

  function mockMainHtml() {
    return '<div class="tm-app">' +
      '<div class="tm-topbar">' +
        '<div class="tm-brand"><span class="tm-y">Y</span><span class="tm-word">eufonic</span></div>' +
        '<div class="tm-nav"><span class="tm-nav-btn on">' + t('Library') + '</span><span class="tm-nav-btn">' + t('Playlists') + '</span></div>' +
        '<div class="tm-pills">' +
          '<span class="tm-pill good"><i class="tm-dot"></i>' + t('Engine ready') + '</span>' +
          '<span class="tm-pill info">' + t('Logs') + '</span>' +
        '</div>' +
      '</div>' +
      '<div class="tm-main-body">' +
        '<div class="tm-sidebar">' +
          '<div class="tm-create-row">' +
            '<span class="tm-cbtn tm-k-song">+ ' + t('Song') + '</span>' +
            '<span class="tm-cbtn tm-k-cover">+ ' + t('Cover') + '</span>' +
            '<span class="tm-cbtn tm-k-inst">+ ' + t('Instrumental') + '</span>' +
          '</div>' +
          '<div class="tm-side-kicker">' + t('Song from a prompt') + '</div>' +
          '<div class="tm-side-title">Harbour Light</div>' +
          '<div class="tm-side-meta">2:54 &middot; 108 BPM</div>' +
          '<div class="tm-side-btns">' +
            '<span class="tm-sbtn pri">' + t('Edit') + '</span>' +
            '<span class="tm-sbtn play">&#9654; ' + t('Play') + '</span>' +
            '<span class="tm-sbtn jam">' + t('Jam') + '</span>' +
          '</div>' +
          '<div class="tm-acc-row">' + t('Style') + '</div>' +
          '<div class="tm-acc-row">' + t('Sound') + '</div>' +
          '<div class="tm-acc-row">' + t('Words') + '</div>' +
          '<div class="tm-menu-sample">' +
            '<div class="tm-menu-head">' + t('Spaces') + '</div>' +
            '<div class="tm-menu-item on">' + t('Default') + '</div>' +
            '<div class="tm-menu-item">Sketches</div>' +
          '</div>' +
        '</div>' +
        '<div class="tm-grid-area">' +
          '<div class="tm-toolbar">' +
            '<span class="tm-space-lbl">' + t('Your takes') + ' &#9662;</span>' +
            '<span class="tm-search-box">' + t('Search takes…') + '</span>' +
            '<span class="tm-kinds">' +
              '<span class="tm-kbtn"><i class="tm-kdot tm-k-song"></i>' + t('Song') + '</span>' +
              '<span class="tm-kbtn"><i class="tm-kdot tm-k-cover"></i>' + t('Cover') + '</span>' +
              '<span class="tm-kbtn"><i class="tm-kdot tm-k-inst"></i>' + t('Instrumental') + '</span>' +
            '</span>' +
          '</div>' +
          '<div class="tm-cards">' +
            '<div class="tm-card playing">' +
              '<div class="tm-card-top"><span class="tm-art tm-k-song"></span><div><div class="tm-ctitle">Harbour Light</div><div class="tm-csub">' + t('from a prompt') + ' &middot; 2:54</div></div></div>' +
              '<div class="tm-cbadges"><span class="tm-tag good">' + t('Playing') + '</span><span class="tm-tag info">' + t('Score') + '</span></div>' +
              '<div class="tm-cacts"><span class="tm-act play">&#9646;&#9646;</span><span class="tm-act">M</span><span class="tm-act">J</span><span class="tm-act star">&#9733;</span></div>' +
            '</div>' +
            '<div class="tm-card holds">' +
              '<div class="tm-card-top"><span class="tm-art tm-k-cover"></span><div><div class="tm-ctitle">Midnight Train</div><div class="tm-csub">' + t('cover') + ' &middot; 3:18</div></div></div>' +
              '<div class="tm-cbadges"><span class="tm-tag lit">' + t('Inside') + ' 3</span><span class="tm-tag warn">' + t('Normalised') + '</span></div>' +
              '<div class="tm-cacts"><span class="tm-act">&#9654;</span><span class="tm-act">M</span><span class="tm-act lit">3</span><span class="tm-act">&#9734;</span></div>' +
            '</div>' +
            '<div class="tm-card">' +
              '<div class="tm-card-top"><span class="tm-art tm-k-inst"></span><div><div class="tm-ctitle">Glass Horizon</div><div class="tm-csub">' + t('instrumental') + ' &middot; 2:20</div></div></div>' +
              '<div class="tm-cbadges"><span class="tm-tag bad">' + t('Failed') + '</span></div>' +
              '<div class="tm-cacts"><span class="tm-act">&#9654;</span><span class="tm-act">M</span><span class="tm-act">J</span><span class="tm-act bad">&times;</span></div>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>' +
      '<div class="tm-player">' +
        '<span class="tm-p-art"></span>' +
        '<div class="tm-p-meta"><div class="tm-p-title">Harbour Light</div><div class="tm-p-sub">1 / 3 &middot; 2:54</div></div>' +
        '<span class="tm-chiclet info">?</span><span class="tm-chiclet good">M</span><span class="tm-chiclet acc">V</span>' +
        '<span class="tm-p-play">&#9646;&#9646;</span>' +
        mockWaveHtml() +
        '<span class="tm-p-time">1:12 / 2:54</span>' +
      '</div>' +
    '</div>';
  }

  function mockEditorHtml() {
    return '<div class="tm-app tm-ed-app">' +
      '<div class="tm-ed-shell">' +
        '<div class="tm-ed-bar"></div>' +
        '<div class="tm-ed-head">' +
          '<span class="tm-ed-title-box">Harbour Light</span>' +
          '<span class="tm-ed-pill good">' + t('Mastering') + '</span>' +
          '<span class="tm-ed-pill">' + t('Advanced') + '</span>' +
          '<div class="tm-ed-tabs"><span class="on">' + t('Song') + '</span><span>' + t('Score') + '</span></div>' +
        '</div>' +
        '<div class="tm-ed-cols">' +
          '<div class="tm-ed-col c1">' +
            '<h5>' + t('The sound') + '</h5>' +
            '<div class="tm-ed-lbl">' + t('Style') + '</div>' +
            '<div class="tm-ed-input tall">warm acoustic guitar, folk rock, brushed drums, intimate vocal</div>' +
            '<div class="tm-ed-lbl">' + t('Style LoRA') + '</div>' +
            '<div class="tm-ed-select">' + t('None') + ' &#9662;</div>' +
            '<div class="tm-ed-slider"><span>' + t('Sound') + '</span><i class="tm-track"><b style="width:70%"></b></i></div>' +
          '</div>' +
          '<div class="tm-ed-col c2">' +
            '<h5>' + t('The words') + '</h5>' +
            '<div class="tm-ed-lbl">' + t('Lyrics') + '</div>' +
            '<div class="tm-ed-input lyrics">[verse]\nThe lantern swings above the pier\nCold salt along the timber wall\n\n[chorus]\nCarry me across the tide</div>' +
            '<div class="tm-cbadges" style="margin-top:6px"><span class="tm-tag warn">' + t('Draft') + '</span><span class="tm-tag info">108 BPM</span></div>' +
          '</div>' +
          '<div class="tm-ed-col c3">' +
            '<h5>' + t('Settings') + '</h5>' +
            '<div class="tm-ed-lbl">' + t('Plan variety') + '</div>' +
            '<div class="tm-ed-select">' + t('Normal') + ' &#9662;</div>' +
            '<div class="tm-ed-lbl">' + t('Interpretation') + '</div>' +
            '<div class="tm-ed-select">' + t('Wide') + ' &#9662;</div>' +
            '<div class="tm-ed-menu-pop">' +
              '<div class="tm-menu-head">' + t('Saved styles') + '</div>' +
              '<div class="tm-menu-item on">Warm acoustic</div>' +
              '<div class="tm-menu-item">Neon synthwave</div>' +
            '</div>' +
            '<div class="tm-cbadges" style="margin-top:6px"><span class="tm-tag good">' + t('Ready') + '</span><span class="tm-tag bad">' + t('Failed') + '</span></div>' +
          '</div>' +
        '</div>' +
        '<div class="tm-ed-foot">' +
          '<span class="tm-ed-btn ghost">' + t('Write score plan') + '</span>' +
          '<span class="tm-ed-btn pri">' + t('Render') + '</span>' +
        '</div>' +
      '</div>' +
      '<div class="tm-player">' +
        '<span class="tm-p-art"></span>' +
        '<div class="tm-p-meta"><div class="tm-p-title">Harbour Light</div><div class="tm-p-sub">1 / 3 &middot; 2:54</div></div>' +
        '<span class="tm-chiclet info">?</span><span class="tm-chiclet good">M</span><span class="tm-chiclet acc">V</span>' +
        '<span class="tm-p-play">&#9646;&#9646;</span>' +
        mockWaveHtml() +
        '<span class="tm-p-time">1:12 / 2:54</span>' +
      '</div>' +
    '</div>';
  }

  function mockJamHtml() {
    function pipsHtml(level) {
      var out = '<span class="tm-jam-pips">';
      for (var i = 1; i <= 4; i++) {
        out += '<i class="tm-jam-pip' + (i <= level ? ' on' : '') + '"></i>';
      }
      return out + '</span>';
    }

    return '<div class="tm-app tm-jam-app">' +
      '<div class="tm-ed-shell">' +
        '<div class="tm-ed-bar"></div>' +
        '<div class="tm-ed-head">' +
          '<span class="tm-jam-title">' + t('Jam') + ' &middot; Harbour Light</span>' +
          '<span class="tm-tag warn"><i class="tm-dot"></i> ' + t('Rolling {progress}%', { progress: 64 }) + '</span>' +
          '<span class="tm-ed-pill" style="margin-left:auto">' + t('Close') + '</span>' +
        '</div>' +
        '<div class="tm-jam-cols">' +
          '<div class="tm-ed-col c1">' +
            '<h5>' + t('Sound &amp; Parts') + '</h5>' +
            '<div class="tm-jam-rack">' +
              '<span class="tm-jam-chip cat-genre">Indie rock' + pipsHtml(3) + '</span>' +
              '<span class="tm-jam-chip cat-inst">Fender Rhodes' + pipsHtml(4) + '</span>' +
              '<span class="tm-jam-chip cat-prod pending">Tape warmth' + pipsHtml(2) + '</span>' +
              '<span class="tm-jam-chip cat-rhythm">Shuffle groove' + pipsHtml(3) + '</span>' +
            '</div>' +
            '<div class="tm-jam-tabs">' +
              '<span class="on">' + t('Instruments') + '</span>' +
              '<span>' + t('Genres') + '</span>' +
              '<span>' + t('Production') + '</span>' +
            '</div>' +
            '<div class="tm-jam-picks">' +
              '<span class="tm-jam-pick added">&#10003; Fender Rhodes</span>' +
              '<span class="tm-jam-pick">+ Analog synth</span>' +
              '<span class="tm-jam-pick">+ Warm strings</span>' +
              '<span class="tm-jam-pick">+ Saxophone</span>' +
            '</div>' +
          '</div>' +
          '<div class="tm-ed-col c2">' +
            '<h5>' + t('Vibe, Tempo &amp; Vocals') + '</h5>' +
            '<div class="tm-jam-xy-row">' +
              '<div class="tm-jam-xy">' +
                '<div class="tm-jam-xy-grid"></div>' +
                '<span class="tm-jam-xy-lbl top">' + t('Energetic') + '</span>' +
                '<span class="tm-jam-xy-lbl bot">' + t('Calm') + '</span>' +
                '<span class="tm-jam-xy-lbl lft">' + t('Dark') + '</span>' +
                '<span class="tm-jam-xy-lbl rgt">' + t('Bright') + '</span>' +
                '<span class="tm-jam-puck" style="left:66%;top:34%"></span>' +
              '</div>' +
              '<div class="tm-jam-vibe">' +
                '<div class="tm-ed-lbl">' + t('Vibe') + '</div>' +
                '<div class="tm-jam-vword">Warm lift</div>' +
                '<div class="tm-ed-lbl" style="margin-top:4px">' + t('Tempo') + ' &middot; 108 BPM</div>' +
                '<i class="tm-track"><b style="width:58%"></b></i>' +
              '</div>' +
            '</div>' +
            '<div class="tm-jam-seg">' +
              '<span>' + t('Instrumental') + '</span>' +
              '<span class="on">' + t('Female') + '</span>' +
              '<span>' + t('Male') + '</span>' +
              '<span>' + t('My Voice') + '</span>' +
            '</div>' +
            '<div class="tm-jam-prompt">warm indie rock, fender rhodes, tape warmth, shuffle groove, 108 bpm</div>' +
          '</div>' +
          '<div class="tm-ed-col c3">' +
            '<h5>' + t('Roll History') + '</h5>' +
            '<div class="tm-jam-card is-seed">' +
              '<div class="tm-jam-ctop"><span class="tm-jam-stag">' + t('Seed') + '</span><span class="tm-jam-cname">Harbour Light</span><span class="tm-csub">0:40</span></div>' +
            '</div>' +
            '<div class="tm-jam-card is-base playing">' +
              '<div class="tm-jam-ctop"><span class="tm-jam-btag">' + t('Base') + '</span><span class="tm-jam-cname">' + t('Pass #{n}', { n: 2 }) + '</span><span class="tm-tag good">&#9654; ' + t('Playing') + '</span></div>' +
              '<div class="tm-jam-cmeta"><span class="tm-csub">+ Fender Rhodes &middot; 108 BPM</span><span class="tm-jam-star">&#9733;</span></div>' +
            '</div>' +
            '<div class="tm-jam-card cooking">' +
              '<div class="tm-jam-ctop"><span class="tm-jam-cname">' + t('Pass #{n}', { n: 3 }) + '</span><span class="tm-tag warn">' + t('Rolling {progress}%', { progress: 64 }) + '</span></div>' +
              '<div class="tm-jam-cmeta"><span class="tm-csub">+ Tape warmth</span></div>' +
            '</div>' +
          '</div>' +
        '</div>' +
        '<div class="tm-jam-foot">' +
          '<span class="tm-jam-base-pill"><span class="tm-jam-btag">' + t('Base') + '</span> ' + t('Pass #{n}', { n: 2 }) + '</span>' +
          '<span class="tm-ed-btn pri">' + t('Roll') + '</span>' +
        '</div>' +
      '</div>' +
      '<div class="tm-player">' +
        '<span class="tm-p-art"></span>' +
        '<div class="tm-p-meta"><div class="tm-p-title">Harbour Light</div><div class="tm-p-sub">' + t('Pass #{n}', { n: 2 }) + ' &middot; 0:40</div></div>' +
        '<span class="tm-chiclet info">?</span><span class="tm-chiclet good">M</span><span class="tm-chiclet acc">V</span>' +
        '<span class="tm-p-play">&#9646;&#9646;</span>' +
        mockWaveHtml() +
        '<span class="tm-p-time">0:18 / 0:40</span>' +
      '</div>' +
    '</div>';
  }

  function mockStageHtml() {
    if (Builder.tab === 'editor') { return mockEditorHtml(); }
    if (Builder.tab === 'jam') { return mockJamHtml(); }
    return mockMainHtml();
  }

  function tintDrawerHtml(tok, val) {
    var shadeSteps = [-24, -15, -7, 0, 8, 17, 28];
    var rampHtml = shadeSteps.map(function (dL) {
      var hex = dL === 0 ? val : shiftHex(val, 0, 0, dL);
      var isCur = dL === 0;
      return '<button type="button" class="tm-tint-chip' + (isCur ? ' current' : '') + '" data-tm-pick-tint="' + tok + '" data-hex="' + escHtml(hex) + '" style="background:' + escHtml(hex) + '" title="' + escHtml(hex) + '"></button>';
    }).join('');

    var nudges = [
      [t('Muted'), shiftHex(val, 0, -22, 0)],
      [t('Richer'), shiftHex(val, 0, 20, 0)],
      [t('Warmer'), nudgeTowardHue(val, 32)],
      [t('Cooler'), nudgeTowardHue(val, 215)]
    ];
    var nudgesHtml = nudges.map(function (item) {
      return '<button type="button" class="tm-tone-btn" data-tm-pick-tint="' + tok + '" data-hex="' + escHtml(item[1]) + '">' +
        '<i class="tm-tone-dot" style="background:' + escHtml(item[1]) + '"></i>' + escHtml(item[0]) +
      '</button>';
    }).join('');

    var gradHtml = '';
    if (GRADIENT_TOKENS[tok]) {
      var g = Builder.gradients[tok] || null;
      var toVal = (g && g.to) || suggestGradientEnd(val);
      var dirVal = (g && g.dir) || '135deg';
      var dirOpts = [
        ['135deg', '\u2198 135\u00B0'],
        ['180deg', '\u2193 180\u00B0'],
        ['90deg', '\u2192 90\u00B0'],
        ['radial', '\u25C9 ' + t('Glow')]
      ];
      gradHtml =
        '<div class="tm-grad-box">' +
          '<label class="tm-grad-toggle">' +
            '<input type="checkbox" data-tm-grad-toggle="' + tok + '"' + (g ? ' checked' : '') + '> ' +
            '<span>' + t('Gradient blend') + '</span>' +
          '</label>' +
          (g
            ? '<div class="tm-grad-controls">' +
                '<div class="tm-grad-stop">' +
                  '<span class="muted small">' + t('Second colour') + '</span>' +
                  '<input type="color" class="tm-swatch" data-tm-grad-color="' + tok + '" value="' + escHtml(toVal) + '" aria-label="' + t('Second colour') + '">' +
                  '<input type="text" class="tm-hex" data-tm-grad-hex="' + tok + '" value="' + escHtml(toVal) + '" maxlength="7" spellcheck="false" aria-label="' + t('Second colour') + ' hex">' +
                '</div>' +
                '<div class="tm-grad-dirs">' +
                  dirOpts.map(function (opt) {
                    return '<button type="button" class="tm-dir-btn' + (dirVal === opt[0] ? ' active' : '') + '" data-tm-grad-dir="' + tok + '" data-dir="' + opt[0] + '">' + escHtml(opt[1]) + '</button>';
                  }).join('') +
                '</div>' +
              '</div>'
            : '') +
        '</div>';
    }

    return '<div class="tm-tint-drawer" data-tm-drawer="' + tok + '">' +
      '<div class="tm-tint-lbl">' + t('Tints & shades') + '</div>' +
      '<div class="tm-tint-ramp">' + rampHtml + '</div>' +
      '<div class="tm-tone-row">' + nudgesHtml + '</div>' +
      gradHtml +
    '</div>';
  }

  function tokenItemHtml(tok, label, preset) {
    var val = Builder.colors[tok] || preset[tok] || '#000000';
    var grad = Builder.gradients[tok] || null;
    var hasGrad = Boolean(grad && grad.to);
    var changed = hasGrad || val.toLowerCase() !== (preset[tok] || '').toLowerCase();
    var isOpen = Builder.openTint === tok;
    var tintTitle = GRADIENT_TOKENS[tok] ? t('Tints, shades & gradient') : t('Tints & shades');
    return '<div class="tm-token-item" data-tm-item="' + tok + '">' +
      '<div class="tm-color-row' + (changed ? ' changed' : '') + (hasGrad ? ' has-grad' : '') + '" data-token="' + tok + '">' +
        '<span class="tm-color-lbl">' + escHtml(label) + '</span>' +
        '<input type="color" class="tm-swatch" data-tm-color="' + tok + '" value="' + escHtml(val) + '" aria-label="' + escHtml(label) + '">' +
        '<input type="text" class="tm-hex" data-tm-hex="' + tok + '" value="' + escHtml(val) + '" maxlength="7" spellcheck="false" aria-label="' + escHtml(label) + ' hex">' +
        '<button type="button" class="tm-tint-btn' + (isOpen ? ' open' : '') + (hasGrad ? ' has-grad' : '') + '" data-tm-tint="' + tok + '" title="' + tintTitle + '" aria-expanded="' + (isOpen ? 'true' : 'false') + '" aria-label="' + tintTitle + '">' +
          '<svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 2a6 6 0 0 1 0 12z" fill="currentColor"/></svg>' +
        '</button>' +
        '<button type="button" class="tm-reset-one" data-tm-reset="' + tok + '" title="' + t('Reset to base colour') + '"' + (changed ? '' : ' disabled') + '>&circlearrowleft;</button>' +
      '</div>' +
      (isOpen ? tintDrawerHtml(tok, val) : '') +
    '</div>';
  }

  function refreshTokenItem(tok) {
    var wrap = document.querySelector('#tm-controls .tm-token-item[data-tm-item="' + tok + '"]');
    if (!wrap) { return; }
    var labelEl = wrap.querySelector('.tm-color-lbl');
    var label = labelEl ? labelEl.textContent : tok;
    var preset = BASE_PRESETS[Builder.base] || BASE_PRESETS.studio;
    wrap.outerHTML = tokenItemHtml(tok, label, preset);
  }

  function paintBuilder() {
    var box = document.getElementById('theme-modal-box');
    if (!box) { return; }
    var saved = getSavedThemes();
    var preset = BASE_PRESETS[Builder.base] || BASE_PRESETS.studio;
    var groups = tokenGroups();

    var savedSelectHtml = '<select id="tm-load-select" class="tm-select" title="' + t('Edit a saved custom theme, or start a new one') + '">' +
      '<option value=""' + (!Builder.editId ? ' selected' : '') + '>' + t('+ New custom theme') + '</option>' +
      saved.map(function (item) {
        return '<option value="' + escHtml(item.id) + '"' + (Builder.editId === item.id ? ' selected' : '') + '>' + escHtml(item.name) + '</option>';
      }).join('') +
    '</select>';

    var baseSelectHtml = '<select id="tm-base-select" class="tm-select" title="' + t('Starting built-in theme and light/dark mode') + '">' +
      [
        ['studio', t('Studio (warm, dark)')],
        ['dark', t('Dark')],
        ['light', t('Light')],
        ['contrast', t('High contrast')]
      ].map(function (opt) {
        return '<option value="' + opt[0] + '"' + (Builder.base === opt[0] ? ' selected' : '') + '>' + escHtml(opt[1]) + '</option>';
      }).join('') +
    '</select>';

    var groupsHtml = groups.map(function (g) {
      var isOpen = Boolean(Builder.openGroups[g.id]);
      var rows = g.items.map(function (pair) {
        return tokenItemHtml(pair[0], pair[1], preset);
      }).join('');
      return '<details class="tm-group" data-tm-group="' + g.id + '"' + (isOpen ? ' open' : '') + '>' +
        '<summary>' + escHtml(g.title) + '</summary>' +
        '<div class="tm-group-rows">' + rows + '</div>' +
      '</details>';
    }).join('');

    box.innerHTML =
      '<div class="modal-head tm-head">' +
        '<div class="tm-head-l">' +
          '<strong>' + t('Custom theme') + '</strong>' +
          savedSelectHtml +
        '</div>' +
        '<button type="button" class="ghost" data-tm-act="close">' + t('Close') + '</button>' +
      '</div>' +
      '<div class="tm-meta-bar">' +
        '<label class="tm-field"><span>' + t('Name') + '</span>' +
          '<input type="text" id="tm-name" maxlength="48" placeholder="' + t('e.g. Midnight Teal') + '" value="' + escHtml(Builder.name) + '" autocomplete="off">' +
        '</label>' +
        '<label class="tm-field"><span>' + t('Base theme') + '</span>' + baseSelectHtml + '</label>' +
        '<div class="tm-meta-tools">' +
          '<button type="button" class="ghost small" data-tm-act="reset-all" title="' + t('Reset all colours to the selected base theme') + '">' + t('Reset colours') + '</button>' +
        '</div>' +
      '</div>' +
      '<div class="tm-body">' +
        '<div class="tm-controls" id="tm-controls">' + groupsHtml + '</div>' +
        '<div class="tm-preview-pane">' +
          '<div class="tm-preview-bar">' +
            '<div class="tm-preview-tabs" role="tablist">' +
              '<button type="button" role="tab" data-tm-tab="main" class="' + (Builder.tab === 'main' ? 'active' : '') + '">' + t('Main page') + '</button>' +
              '<button type="button" role="tab" data-tm-tab="editor" class="' + (Builder.tab === 'editor' ? 'active' : '') + '">' + t('Editor page') + '</button>' +
              '<button type="button" role="tab" data-tm-tab="jam" class="' + (Builder.tab === 'jam' ? 'active' : '') + '">' + t('Jam page') + '</button>' +
            '</div>' +
            '<span class="muted small">' + t('Live mock-up') + '</span>' +
          '</div>' +
          '<div class="tm-stage" id="tm-stage">' +
            mockStageHtml() +
          '</div>' +
        '</div>' +
      '</div>' +
      '<div class="tm-foot">' +
        '<span class="tm-error" id="tm-error">' + escHtml(Builder.error) + '</span>' +
        '<div class="tm-foot-actions">' +
          (Builder.editId ? '<button type="button" class="ghost danger-btn" data-tm-act="delete">' + t('Delete theme') + '</button>' : '') +
          '<button type="button" class="ghost" data-tm-act="close">' + t('Cancel') + '</button>' +
          '<button type="button" class="primary" data-tm-act="save"' + (Builder.saving ? ' disabled' : '') + '>' +
            (Builder.editId ? t('Save changes') : t('Save & apply')) +
          '</button>' +
        '</div>' +
      '</div>';

    applyDraftToStage();
  }

  function setError(msg) {
    Builder.error = msg || '';
    var el = document.getElementById('tm-error');
    if (el) { el.textContent = Builder.error; }
  }

  function setStageWaveKind(kind) {
    var waveEl = document.querySelector('#tm-stage .tm-wave');
    if (!waveEl) { return; }
    waveEl.className = 'tm-wave tm-w-' + kind;
    waveEl.dataset.tmWave = kind;
  }

  function updateTokenValue(tok, hex) {
    Builder.colors[tok] = hex;
    if (tok === '--wave-song') { Builder.waveKind = 'song'; setStageWaveKind('song'); }
    else if (tok === '--wave-cover') { Builder.waveKind = 'cover'; setStageWaveKind('cover'); }
    else if (tok === '--wave-inst') { Builder.waveKind = 'inst'; setStageWaveKind('inst'); }
    else if (tok === '--wave-default') { Builder.waveKind = 'default'; setStageWaveKind('default'); }
    var preset = BASE_PRESETS[Builder.base] || BASE_PRESETS.studio;
    var hasGrad = Boolean(Builder.gradients[tok] && Builder.gradients[tok].to);
    var changed = hasGrad || hex.toLowerCase() !== (preset[tok] || '').toLowerCase();
    var row = document.querySelector('#tm-controls .tm-color-row[data-token="' + tok + '"]');
    if (row) {
      row.classList.toggle('changed', changed);
      var sw = row.querySelector('[data-tm-color]');
      var hx = row.querySelector('[data-tm-hex]');
      var rs = row.querySelector('[data-tm-reset]');
      if (sw && sw.value.toLowerCase() !== hex) { sw.value = hex; }
      if (hx && document.activeElement !== hx) { hx.value = hex; }
      if (rs) { rs.disabled = !changed; }
    }
    if (Builder.openTint === tok) {
      var drawer = document.querySelector('#tm-controls .tm-tint-drawer[data-tm-drawer="' + tok + '"]');
      if (drawer && (!document.activeElement || !drawer.contains(document.activeElement))) {
        drawer.outerHTML = tintDrawerHtml(tok, hex);
      }
    }
    applyDraftToStage();
  }

  async function saveDraft() {
    var name = String(Builder.name || '').trim();
    if (!name) {
      setError(t('Give your theme a name first.'));
      var inp = document.getElementById('tm-name');
      if (inp) { inp.focus(); }
      return;
    }
    Builder.saving = true;
    setError('');
    try {
      var url = Builder.editId ? '/api/themes/' + encodeURIComponent(Builder.editId) : '/api/themes';
      var method = Builder.editId ? 'PUT' : 'POST';
      var res = await api(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name,
          base: Builder.base,
          colors: Builder.colors,
          gradients: Builder.gradients,
          apply: true
        })
      });
      if (res && res.settings && typeof adoptSettings === 'function') {
        adoptSettings(res.settings);
      }
      if (typeof paintSettings === 'function') { paintSettings(); }
      if (typeof toast === 'function') {
        toast(t('Saved theme “{name}”.', { name: (res && res.theme && res.theme.name) || name }));
      }
      closeBuilder();
    } catch (err) {
      Builder.saving = false;
      setError(tr(err.message) || t('Could not save theme.'));
    }
  }

  async function deleteSavedTheme(themeId, fromBuilder) {
    var target = findSavedById(themeId);
    if (!target) { return; }
    if (typeof confirmModal === 'function') {
      var yes = await confirmModal({
        title: t('Remove custom theme?'),
        message: t('“{name}” will be removed from your theme list.', { name: target.name }),
        confirmText: t('Remove'),
        danger: true
      });
      if (!yes) { return; }
    }
    try {
      var res = await api('/api/themes/' + encodeURIComponent(themeId), { method: 'DELETE' });
      if (res && res.settings && typeof adoptSettings === 'function') {
        adoptSettings(res.settings);
      }
      if (typeof paintSettings === 'function') { paintSettings(); }
      if (typeof toast === 'function') { toast(t('Removed theme “{name}”.', { name: target.name })); }
      if (fromBuilder) {
        closeBuilder();
      }
    } catch (err) {
      if (fromBuilder) { setError(tr(err.message) || t('Could not remove theme.')); }
      else if (typeof toast === 'function') { toast(tr(err.message) || t('Could not remove theme.'), 'bad'); }
    }
  }

  function wireBuilder() {
    var modal = document.getElementById('theme-modal');
    if (!modal || modal.dataset.wired) { return; }
    modal.dataset.wired = '1';

    modal.addEventListener('click', function (event) {
      var tabBtn = event.target.closest('[data-tm-tab]');
      if (tabBtn) {
        var nextTab = tabBtn.dataset.tmTab;
        Builder.tab = (nextTab === 'editor' || nextTab === 'jam') ? nextTab : 'main';
        Builder.waveKind = null;
        modal.querySelectorAll('[data-tm-tab]').forEach(function (btn) {
          btn.classList.toggle('active', btn.dataset.tmTab === Builder.tab);
        });
        var stage = document.getElementById('tm-stage');
        if (stage) {
          stage.innerHTML = mockStageHtml();
          applyDraftToStage();
        } else {
          paintBuilder();
        }
        return;
      }
      var waveEl = event.target.closest('[data-tm-wave]');
      if (waveEl) {
        var order = ['song', 'cover', 'inst', 'default'];
        var idx = order.indexOf(activeWaveKind());
        var nextKind = order[(idx + 1) % order.length];
        Builder.waveKind = nextKind;
        setStageWaveKind(nextKind);
        return;
      }
      var tintBtn = event.target.closest('[data-tm-tint]');
      if (tintBtn) {
        var tokT = tintBtn.dataset.tmTint;
        var prevOpen = Builder.openTint;
        Builder.openTint = (prevOpen === tokT) ? null : tokT;
        if (prevOpen && prevOpen !== tokT) { refreshTokenItem(prevOpen); }
        refreshTokenItem(tokT);
        return;
      }
      var pickTint = event.target.closest('[data-tm-pick-tint]');
      if (pickTint) {
        var tokP = pickTint.dataset.tmPickTint;
        var hexP = normalizeHex(pickTint.dataset.hex);
        if (tokP && hexP) { updateTokenValue(tokP, hexP); }
        return;
      }
      var dirBtn = event.target.closest('[data-tm-grad-dir]');
      if (dirBtn) {
        var tokD = dirBtn.dataset.tmGradDir;
        var dir = dirBtn.dataset.dir;
        if (GRADIENT_TOKENS[tokD] && Builder.gradients[tokD] && GRADIENT_DIRS.indexOf(dir) >= 0) {
          Builder.gradients[tokD].dir = dir;
          refreshTokenItem(tokD);
          applyDraftToStage();
        }
        return;
      }
      var resetOne = event.target.closest('[data-tm-reset]');
      if (resetOne && !resetOne.disabled) {
        var tok = resetOne.dataset.tmReset;
        var preset = BASE_PRESETS[Builder.base] || BASE_PRESETS.studio;
        delete Builder.gradients[tok];
        if (preset[tok]) { Builder.colors[tok] = preset[tok]; }
        refreshTokenItem(tok);
        applyDraftToStage();
        return;
      }
      var actBtn = event.target.closest('[data-tm-act]');
      if (!actBtn) { return; }
      var act = actBtn.dataset.tmAct;
      if (act === 'close') { closeBuilder(); return; }
      if (act === 'save') { saveDraft(); return; }
      if (act === 'delete' && Builder.editId) { deleteSavedTheme(Builder.editId, true); return; }
      if (act === 'reset-all') {
        Builder.colors = Object.assign({}, BASE_PRESETS[Builder.base] || BASE_PRESETS.studio);
        Builder.gradients = {};
        Builder.openTint = null;
        paintBuilder();
        return;
      }
    });

    modal.addEventListener('input', function (event) {
      var tg = event.target;
      if (tg.id === 'tm-name') {
        Builder.name = tg.value;
        if (Builder.error) { setError(''); }
        return;
      }
      if (tg.dataset && tg.dataset.tmColor) {
        var hex = normalizeHex(tg.value);
        if (hex) { updateTokenValue(tg.dataset.tmColor, hex); }
        return;
      }
      if (tg.dataset && tg.dataset.tmHex) {
        var norm = normalizeHex(tg.value);
        if (norm) { updateTokenValue(tg.dataset.tmHex, norm); }
        return;
      }
      if (tg.dataset && tg.dataset.tmGradColor) {
        var gTok = tg.dataset.tmGradColor;
        var gHex = normalizeHex(tg.value);
        if (gHex && GRADIENT_TOKENS[gTok]) {
          Builder.gradients[gTok] = { to: gHex, dir: (Builder.gradients[gTok] && Builder.gradients[gTok].dir) || '135deg' };
          var gHx = modal.querySelector('[data-tm-grad-hex="' + gTok + '"]');
          if (gHx && document.activeElement !== gHx) { gHx.value = gHex; }
          applyDraftToStage();
        }
        return;
      }
      if (tg.dataset && tg.dataset.tmGradHex) {
        var ghTok = tg.dataset.tmGradHex;
        var ghHex = normalizeHex(tg.value);
        if (ghHex && GRADIENT_TOKENS[ghTok]) {
          Builder.gradients[ghTok] = { to: ghHex, dir: (Builder.gradients[ghTok] && Builder.gradients[ghTok].dir) || '135deg' };
          var gSw = modal.querySelector('[data-tm-grad-color="' + ghTok + '"]');
          if (gSw) { gSw.value = ghHex; }
          applyDraftToStage();
        }
        return;
      }
    });

    modal.addEventListener('change', function (event) {
      var tg = event.target;
      if (tg.id === 'tm-load-select') {
        var picked = tg.value;
        if (picked) {
          var existing = findSavedById(picked);
          if (existing) {
            Builder.editId = existing.id;
            Builder.name = existing.name;
            Builder.base = BASE_PRESETS[existing.base] ? existing.base : 'studio';
            Builder.colors = Object.assign({}, BASE_PRESETS[Builder.base], existing.colors || {});
            Builder.gradients = cloneGradients(existing.gradients);
            Builder.openTint = null;
            Builder.error = '';
            paintBuilder();
          }
        } else {
          Builder.editId = null;
          Builder.name = '';
          Builder.base = currentActiveBase();
          Builder.colors = Object.assign({}, BASE_PRESETS[Builder.base]);
          Builder.gradients = {};
          Builder.openTint = null;
          Builder.error = '';
          paintBuilder();
        }
        return;
      }
      if (tg.id === 'tm-base-select') {
        var oldBase = Builder.base;
        var nextBase = BASE_PRESETS[tg.value] ? tg.value : 'studio';
        var oldPreset = BASE_PRESETS[oldBase] || BASE_PRESETS.studio;
        var nextPreset = BASE_PRESETS[nextBase] || BASE_PRESETS.studio;
        // Keep tokens the user explicitly tweaked; update untouched ones to the new base
        var nextColors = Object.assign({}, nextPreset);
        Object.keys(Builder.colors).forEach(function (k) {
          if (Builder.colors[k] && oldPreset[k] && Builder.colors[k].toLowerCase() !== oldPreset[k].toLowerCase()) {
            nextColors[k] = Builder.colors[k];
          }
        });
        Builder.base = nextBase;
        Builder.colors = nextColors;
        paintBuilder();
        return;
      }
      if (tg.dataset && tg.dataset.tmGradToggle) {
        var tTok = tg.dataset.tmGradToggle;
        if (GRADIENT_TOKENS[tTok]) {
          if (tg.checked) {
            var baseHex = Builder.colors[tTok] || (BASE_PRESETS[Builder.base] || BASE_PRESETS.studio)[tTok] || '#14141a';
            Builder.gradients[tTok] = { to: suggestGradientEnd(baseHex), dir: '135deg' };
          } else {
            delete Builder.gradients[tTok];
          }
          refreshTokenItem(tTok);
          applyDraftToStage();
        }
        return;
      }
      if (tg.dataset && tg.dataset.tmGradHex) {
        var ghTok2 = tg.dataset.tmGradHex;
        var ghNorm = normalizeHex(tg.value);
        if (ghNorm && GRADIENT_TOKENS[ghTok2]) {
          Builder.gradients[ghTok2] = { to: ghNorm, dir: (Builder.gradients[ghTok2] && Builder.gradients[ghTok2].dir) || '135deg' };
          applyDraftToStage();
        } else if (Builder.gradients[ghTok2]) {
          tg.value = Builder.gradients[ghTok2].to;
        }
        return;
      }
      if (tg.dataset && tg.dataset.tmHex) {
        var norm = normalizeHex(tg.value);
        var tok = tg.dataset.tmHex;
        if (norm) {
          updateTokenValue(tok, norm);
        } else {
          tg.value = Builder.colors[tok] || '#000000';
        }
        return;
      }
    });

    modal.addEventListener('toggle', function (event) {
      var det = event.target;
      if (det && det.dataset && det.dataset.tmGroup) {
        Builder.openGroups[det.dataset.tmGroup] = det.open;
      }
    }, true);
  }

  /* Settings row helper: buttons beside/under the Theme <select> to create, edit, or delete custom themes. */
  function themeActionsHtml(currentValue) {
    var isCustom = Boolean(currentValue && currentValue.indexOf('custom:') === 0);
    var customId = isCustom ? currentValue.slice(7) : '';
    return '<div class="theme-custom-actions">' +
      '<button type="button" class="ghost small" data-theme-act="new">' + t('Customise…') + '</button>' +
      (isCustom ? '<button type="button" class="ghost small" data-theme-act="edit" data-theme-id="' + escHtml(customId) + '">' + t('Edit') + '</button>' : '') +
      (isCustom ? '<button type="button" class="ghost small danger-btn" data-theme-act="delete" data-theme-id="' + escHtml(customId) + '">' + t('Remove') + '</button>' : '') +
    '</div>';
  }

  function handleSettingsClick(event) {
    var btn = event.target.closest('[data-theme-act]');
    if (!btn) { return false; }
    var act = btn.dataset.themeAct;
    if (act === 'new') { openBuilder(null); return true; }
    if (act === 'edit') { openBuilder(btn.dataset.themeId || null); return true; }
    if (act === 'delete') { deleteSavedTheme(btn.dataset.themeId, false); return true; }
    return false;
  }

  document.addEventListener('DOMContentLoaded', wireBuilder);
  if (document.readyState !== 'loading') { wireBuilder(); }

  window.CustomThemes = {
    BASE_PRESETS: BASE_PRESETS,
    expandVars: expandVars,
    applyCustomObject: applyCustomObject,
    clearApplied: clearApplied,
    clearCache: clearCache,
    findSavedById: findSavedById,
    openBuilder: openBuilder,
    closeBuilder: closeBuilder,
    isOpen: function () { return Builder.open; },
    themeActionsHtml: themeActionsHtml,
    handleSettingsClick: handleSettingsClick
  };
})();
