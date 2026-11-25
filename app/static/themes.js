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

  function hexToRgb(hex) {
    var m = /^#?([0-9a-f]{6})$/i.exec(String(hex || '').trim());
    if (!m) { return null; }
    var n = parseInt(m[1], 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
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

  /* Expand a custom theme's { base, colors } into the full set of CSS custom
     properties needed by styles.css (including derived *-rgb and waveform alphas). */
  function expandVars(base, colors) {
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
    // Ensure Studio Slate panel/input backgrounds follow the custom theme too
    vars['--ui-panel-bg'] = merged['--panel'];
    vars['--ui-input-bg'] = merged['--input-bg'];
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
    var vars = expandVars(base, themeObj.colors || {});
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
    tab: 'main',          // 'main' | 'editor'
    liveApp: false,       // live-preview on the real page behind the modal
    openGroups: { surfaces: true, text: true, accents: true, origins: false, status: false, inputs: false, waveforms: false },
    saving: false,
    error: ''
  };

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
    } else {
      Builder.editId = null;
      Builder.name = '';
      Builder.base = currentActiveBase();
      Builder.colors = Object.assign({}, BASE_PRESETS[Builder.base]);
    }
    Builder.liveApp = false;
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
    if (Builder.liveApp) {
      Builder.liveApp = false;
      if (typeof applyTheme === 'function') { applyTheme(); }
    }
    if (modal) { modal.classList.add('hidden'); }
  }

  function applyDraftToStage() {
    var stage = document.getElementById('tm-stage');
    var vars = expandVars(Builder.base, Builder.colors);
    if (stage) {
      stage.dataset.theme = Builder.base;
      var uiStyle = (typeof setting === 'function') ? setting('appearance.ui_style', 'slate') : 'slate';
      if (uiStyle && uiStyle !== 'default') { stage.dataset.uiStyle = uiStyle; } else { delete stage.dataset.uiStyle; }
      Object.keys(vars).forEach(function (k) { stage.style.setProperty(k, vars[k]); });
    }
    if (Builder.liveApp) {
      applyCustomObject({ id: Builder.editId || 'preview', base: Builder.base, colors: Builder.colors }, false);
      if (typeof repaintTheme === 'function') { repaintTheme(); }
    }
  }

  function mockMainHtml() {
    var waveHeights = [26, 48, 72, 62, 85, 50, 38, 66, 90, 58, 44, 76, 82, 60, 42, 68, 92, 54, 40, 74, 62, 48, 36, 56, 78, 64, 46, 30];
    var waveBars = waveHeights.map(function (h, i) {
      var cls = i < 9 ? 'song' : (i < 16 ? 'cover' : (i < 22 ? 'inst' : 'def'));
      return '<span class="tm-wbar ' + cls + '" style="height:' + h + '%"></span>';
    }).join('');

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
            '<span class="tm-cbtn song">+ ' + t('Song') + '</span>' +
            '<span class="tm-cbtn cover">+ ' + t('Cover') + '</span>' +
            '<span class="tm-cbtn inst">+ ' + t('Instrumental') + '</span>' +
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
            '<span class="tm-search-box">' + t('Search takes…') + '</span>' +
            '<span class="tm-fchip song">' + t('Song') + '</span>' +
            '<span class="tm-fchip cover">' + t('Cover') + '</span>' +
            '<span class="tm-fchip inst">' + t('Instrumental') + '</span>' +
          '</div>' +
          '<div class="tm-cards">' +
            '<div class="tm-card playing">' +
              '<div class="tm-card-top"><span class="tm-art song"></span><div><div class="tm-ctitle">Harbour Light</div><div class="tm-csub">' + t('from a prompt') + ' &middot; 2:54</div></div></div>' +
              '<div class="tm-cbadges"><span class="tm-tag good">' + t('Playing') + '</span><span class="tm-tag info">' + t('Score') + '</span></div>' +
              '<div class="tm-cacts"><span class="tm-act play">&#9646;&#9646;</span><span class="tm-act">M</span><span class="tm-act">J</span><span class="tm-act star">&#9733;</span></div>' +
            '</div>' +
            '<div class="tm-card holds">' +
              '<div class="tm-card-top"><span class="tm-art cover"></span><div><div class="tm-ctitle">Midnight Train</div><div class="tm-csub">' + t('cover') + ' &middot; 3:18</div></div></div>' +
              '<div class="tm-cbadges"><span class="tm-tag lit">' + t('Inside') + ' 3</span><span class="tm-tag warn">' + t('Normalised') + '</span></div>' +
              '<div class="tm-cacts"><span class="tm-act">&#9654;</span><span class="tm-act">M</span><span class="tm-act lit">3</span><span class="tm-act">&#9734;</span></div>' +
            '</div>' +
            '<div class="tm-card">' +
              '<div class="tm-card-top"><span class="tm-art inst"></span><div><div class="tm-ctitle">Glass Horizon</div><div class="tm-csub">' + t('instrumental') + ' &middot; 2:20</div></div></div>' +
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
        '<div class="tm-wave">' + waveBars + '</div>' +
        '<span class="tm-p-time">1:12 / 2:54</span>' +
      '</div>' +
    '</div>';
  }

  function mockEditorHtml() {
    var waveHeights = [30, 56, 78, 60, 88, 52, 42, 74, 92, 64, 48, 80, 70, 50, 62, 84, 58, 40, 68, 52];
    var waveBars = waveHeights.map(function (h, i) {
      var cls = i < 8 ? 'song' : (i < 13 ? 'cover' : 'inst');
      return '<span class="tm-wbar ' + cls + '" style="height:' + h + '%"></span>';
    }).join('');

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
        '<div class="tm-wave">' + waveBars + '</div>' +
        '<span class="tm-p-time">1:12 / 2:54</span>' +
      '</div>' +
    '</div>';
  }

  function mockJamHtml() {
    var waveHeights = [26, 52, 74, 88, 60, 44, 78, 92, 66, 48, 82, 58, 70, 86, 54, 42, 76, 62, 46, 58];
    var waveBars = waveHeights.map(function (h, i) {
      var cls = i < 9 ? 'song' : (i < 15 ? 'cover' : 'inst');
      return '<span class="tm-wbar ' + cls + '" style="height:' + h + '%"></span>';
    }).join('');

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
        '<div class="tm-wave">' + waveBars + '</div>' +
        '<span class="tm-p-time">0:18 / 0:40</span>' +
      '</div>' +
    '</div>';
  }

  function mockStageHtml() {
    if (Builder.tab === 'editor') { return mockEditorHtml(); }
    if (Builder.tab === 'jam') { return mockJamHtml(); }
    return mockMainHtml();
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
        var tok = pair[0];
        var label = pair[1];
        var val = Builder.colors[tok] || preset[tok] || '#000000';
        var changed = val.toLowerCase() !== (preset[tok] || '').toLowerCase();
        return '<div class="tm-color-row' + (changed ? ' changed' : '') + '" data-token="' + tok + '">' +
          '<span class="tm-color-lbl">' + escHtml(label) + '</span>' +
          '<input type="color" class="tm-swatch" data-tm-color="' + tok + '" value="' + escHtml(val) + '" aria-label="' + escHtml(label) + '">' +
          '<input type="text" class="tm-hex" data-tm-hex="' + tok + '" value="' + escHtml(val) + '" maxlength="7" spellcheck="false" aria-label="' + escHtml(label) + ' hex">' +
          '<button type="button" class="tm-reset-one" data-tm-reset="' + tok + '" title="' + t('Reset to base colour') + '"' + (changed ? '' : ' disabled') + '>&circlearrowleft;</button>' +
        '</div>';
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
          '<label class="tm-live-chk" title="' + t('Temporarily preview this theme on the live app behind the window') + '">' +
            '<input type="checkbox" id="tm-live-app"' + (Builder.liveApp ? ' checked' : '') + '> ' + t('Preview on app') +
          '</label>' +
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

  function updateTokenValue(tok, hex) {
    Builder.colors[tok] = hex;
    var preset = BASE_PRESETS[Builder.base] || BASE_PRESETS.studio;
    var changed = hex.toLowerCase() !== (preset[tok] || '').toLowerCase();
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
          apply: true
        })
      });
      Builder.liveApp = false;
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
        Builder.liveApp = false;
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
      var resetOne = event.target.closest('[data-tm-reset]');
      if (resetOne && !resetOne.disabled) {
        var tok = resetOne.dataset.tmReset;
        var preset = BASE_PRESETS[Builder.base] || BASE_PRESETS.studio;
        if (preset[tok]) { updateTokenValue(tok, preset[tok]); }
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
            Builder.error = '';
            paintBuilder();
          }
        } else {
          Builder.editId = null;
          Builder.name = '';
          Builder.base = currentActiveBase();
          Builder.colors = Object.assign({}, BASE_PRESETS[Builder.base]);
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
      if (tg.id === 'tm-live-app') {
        Builder.liveApp = tg.checked;
        if (Builder.liveApp) {
          applyDraftToStage();
        } else if (typeof applyTheme === 'function') {
          applyTheme();
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
