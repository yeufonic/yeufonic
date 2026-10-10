'use strict';

/* A script error or a rejected promise in this page is sent to the server's log, where
   it can be read later; otherwise it lives only in the browser console. Twenty a page
   load at most, each different one once. */
(function () {
  var sent = 0;
  var seen = {};
  function report(payload) {
    var key = payload.message + '|' + payload.source + '|' + payload.line;
    if (sent >= 20 || seen[key]) { return; }
    seen[key] = true;
    sent += 1;
    try {
      fetch('/api/logs/client', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload), keepalive: true }).catch(function () { /* nowhere to report it */ });
    } catch (err) { /* nowhere to report it */ }
  }
  window.addEventListener('error', function (event) {
    if (!event.message) { return; }
    report({ message: String(event.message).slice(0, 300), source: String(event.filename || '').split('/').pop().split('?')[0],
             line: event.lineno || 0, column: event.colno || 0,
             stack: event.error && event.error.stack ? String(event.error.stack).slice(0, 1000) : '',
             page: window.location.pathname });
  });
  window.addEventListener('unhandledrejection', function (event) {
    var reason = event.reason;
    report({ message: 'Unhandled promise: ' + String((reason && reason.message) || reason).slice(0, 300), source: '',
             line: 0, column: 0, stack: reason && reason.stack ? String(reason.stack).slice(0, 1000) : '',
             page: window.location.pathname });
  });
}());

/* What the left column is about. One object, and only setSelection may write it.
   Four separate fields used to say this (editorTakeId, editorSourceId, leftTakeId,
   planTakeId) and they drifted apart three times: a cover was rendered from another
   recording's score, a new plan was never shown, and a card's score was credited to
   a recording that had never been transcribed. Reads go through the helpers below.

     formTakeId  the take the form describes, and whose card is highlighted
     boxKind     who owns the score in the box: 'none', 'take' or 'source'
     boxId       that take's or recording's id
     awaiting    a take whose plan is being written; it owns nothing until it lands */
var Selection = { formTakeId: null, boxKind: 'none', boxId: null, awaiting: null };

function paintTakeHighlights() {
  if (typeof selectedTakeId !== 'function' || !document.getElementById('takes')) { return; }
  var activeId = selectedTakeId() || (typeof takeIdInEditor === 'function' ? takeIdInEditor() : '');
  var activeTake = typeof takeById === 'function' ? takeById(activeId) : null;
  var tone = activeTake ? ({ song: 'tone-song', instrumental: 'tone-inst' }[activeTake.kind] || 'tone-cover') : '';
  var cards = document.querySelectorAll('#takes .take');
  Array.prototype.forEach.call(cards, function (card) {
    var isCur = card.dataset.id === activeId;
    card.classList.toggle('editing', isCur);
    card.classList.remove('tone-song', 'tone-inst', 'tone-cover');
    if (isCur && tone) {
      card.classList.add(tone);
    }
  });
  if (typeof paintSheet === 'function') { paintSheet(); }
}

function setSelection(next) {
  Selection = {
    formTakeId: next.formTakeId || null,
    boxKind: next.boxKind || 'none',
    boxId: next.boxId || null,
    awaiting: next.awaiting || null
  };
  syncEditor();
  paintTakeHighlights(); // the highlight follows the form without re-rendering card DOM
  setScoreActions();     // so do Render and Replan
  saveForm();
  if (next.formTakeId && typeof activateTakeRecording === 'function') {
    var t = (typeof takeById === 'function' ? takeById(next.formTakeId) : null) ||
            (State.formTake && State.formTake.id === next.formTakeId ? State.formTake : null);
    if (t) { activateTakeRecording(t); }
  }
}

/* Used when restoring the form on a reload, before the painters are ready. */
function restoreSelection(saved) {
  Selection = { formTakeId: null, boxKind: 'none', boxId: null, awaiting: null };
  if (saved && saved.boxKind && saved.boxId) { Selection.boxKind = saved.boxKind; Selection.boxId = saved.boxId; }
  if (saved && saved.formTakeId) { Selection.formTakeId = saved.formTakeId; }
  if (saved && saved.awaiting) { Selection.awaiting = saved.awaiting; }
}

function selectedTakeId() { return Selection.formTakeId; }
function scoreTakeId() { return Selection.boxKind === 'take' ? Selection.boxId : null; }
function awaitingPlanId() { return Selection.awaiting; }

/* Is the score in the box this recording's? A cover take's transcribed score came
   from its recording, so the take owns the box while the recording still matches. */
function boxShowsSource(sourceId) {
  if (!sourceId) { return false; }
  if (Selection.boxKind === 'source') { return Selection.boxId === sourceId; }
  if (Selection.boxKind === 'take') {
    var take = takeById(Selection.boxId);
    return Boolean(take && take.source_id === sourceId);
  }
  return false;
}

var State = { normalising: {}, sources: [], takes: [], options: {}, filter: 'all', playing: null, busy: false, mode: 'cover',
  layout: 'compact',
  takesRaw: '', takesTotal: 0, takeLimit: 300, takesAt: 0, paintedAt: 0, draft: null, audition: null,
  picked: {},
  formEdited: false, spaces: [], spaceId: 'default', moveTakeId: null, search: '', searchAll: false };
var LAYOUT_KEY = 'yue2.layout';
var SHEET_KEY = 'yue2.sheet';   // the take panel folded away, or not
// Set here, before the page is wired, which happens partway through this file.
var SHEET_KIND = { song: 'Song from a prompt', cover: 'Cover of a recording', instrumental: 'Instrumental' };
var Editor = { page: 'song', step: 0 };   // the editor window's page and step
var WIDTH_KEY = 'yue2.width';
var SPACE_KEY = 'yue2.space';
var FILTER_KEY = 'yue2.filter';
var KINDS_KEY = 'yue2.kinds';
var SEARCHES_KEY = 'yue2.searches';
var COMPARE_MOST = 6;   // takes the compare window holds

/* All or Starred, kept across a reload like the layout. */
function applyFilter(filter) {
  State.filter = filter === 'favourite' ? 'favourite' : 'all';
  Array.prototype.forEach.call(document.querySelectorAll('.filters [data-filter]'), function (chip) {
    chip.classList.toggle('active', chip.dataset.filter === State.filter);
  });
  try { localStorage.setItem(FILTER_KEY, State.filter); } catch (err) { /* private mode */ }
}

/* Song, Cover and Instrumental toggles: the kinds shown, none ticked meaning every kind.  Kept across a reload, and the
   same in every space. */
function applyKinds(kinds) {
  State.kinds = ['song', 'cover', 'instrumental'].filter(function (kind) { return (kinds || []).indexOf(kind) >= 0; });
  Array.prototype.forEach.call(document.querySelectorAll('.filters [data-takekind]'), function (chip) {
    var on = State.kinds.indexOf(chip.dataset.takekind) >= 0;
    chip.classList.toggle('active', on);
    chip.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  try { localStorage.setItem(KINDS_KEY, JSON.stringify(State.kinds)); } catch (err) { /* private mode */ }
}

/* Search: every word typed must appear in a take's title, style, lyrics or LoRA
   name. It looks through this space, or every space with the All spaces chip.
   The search starts empty on a reload; the last few are kept to pick from. */
function searchingEverywhere() {
  return !!(State.search && State.searchAll);
}

function spaceName(id) {
  var space = State.spaces.filter(function (s) { return s.id === id; })[0];
  return space ? space.name : 'another space';
}

function recentSearches() {
  try {
    var got = JSON.parse(localStorage.getItem(SEARCHES_KEY) || '[]');
    return Array.isArray(got) ? got.filter(function (s) { return typeof s === 'string'; }) : [];
  } catch (err) {
    return [];
  }
}

/* Kept once it has found something, so a typo is not offered again. */
function rememberSearch(text) {
  text = (text || '').trim().replace(/\s+/g, ' ');
  if (!text) { return; }
  var kept = recentSearches().filter(function (s) { return s.toLowerCase() !== text.toLowerCase(); });
  kept.unshift(text);
  try { localStorage.setItem(SEARCHES_KEY, JSON.stringify(kept.slice(0, 8))); } catch (err) { /* private mode */ }
}

function paintSearchCount() {
  var wrap = $('take-search-wrap');
  if (!wrap) { return; }
  var on = !!State.search;
  wrap.classList.toggle('has-text', on || !!$('take-search').value);
  $('take-search-count').textContent = on ? State.takesTotal + ' found' : '';
  paintTakesHeading();
  var all = $('search-all');
  if (all) {
    all.classList.toggle('hidden', !on);
    all.classList.toggle('active', State.searchAll);
  }
}

/* The recent searches, under the box while it has focus. Those that contain what
   is typed so far, and not the search already showing. */
function paintRecent() {
  var list = $('take-search-recent');
  var box = $('take-search');
  var typed = box.value.trim().toLowerCase();
  var items = recentSearches().filter(function (s) {
    var low = s.toLowerCase();
    return low !== typed && (!typed || low.indexOf(typed) !== -1);
  });
  State.recentPick = -1;
  if (document.activeElement !== box || !items.length) {
    list.classList.add('hidden');
    return;
  }
  list.innerHTML = '<div class="search-recent-head">Recent searches</div>' +
    items.map(function (s, i) {
      return '<button type="button" class="search-recent-item" data-search="' + esc(s) + '" data-i="' + i + '">' + esc(s) + '</button>';
    }).join('') +
    '<button type="button" class="search-recent-clear" data-clear-recent="1">Clear recent searches</button>';
  list.classList.remove('hidden');
}

function runSearch(text) {
  var search = (text || '').trim().replace(/\s+/g, ' ');
  if (search === State.search) { paintSearchCount(); return; }
  State.search = search;
  State.takesRaw = '';
  State.takeLimit = 300;
  clearPicked();
  paintSearchCount();
  loadTakes();
}

function wireSearch() {
  var box = $('take-search');
  if (!box) { return; }   // a page from before the search, on a new script
  var list = $('take-search-recent');
  var timer = null;
  var pick = function (text) {
    box.value = text;
    clearTimeout(timer);
    var search = text.trim().replace(/\s+/g, ' ');
    if (search === State.search) {
      if (State.takesTotal) { rememberSearch(search); }
    } else {
      State.rememberWhenFound = search;   // kept when its answer arrives, if it found any
    }
    runSearch(text);
    paintRecent();
  };
  box.addEventListener('input', function () {
    $('take-search-wrap').classList.toggle('has-text', !!box.value);
    clearTimeout(timer);
    timer = setTimeout(function () { runSearch(box.value); }, 250);
    paintRecent();
  });
  box.addEventListener('focus', paintRecent);
  box.addEventListener('blur', function () {
    if (State.search && State.takesTotal) { rememberSearch(State.search); }
    list.classList.add('hidden');
  });
  box.addEventListener('keydown', function (event) {
    var items = list.classList.contains('hidden') ? [] : list.querySelectorAll('.search-recent-item');
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      if (!items.length) { return; }
      event.preventDefault();
      // Down from the box goes to the first; past either end, back to the box.
      var next = State.recentPick + (event.key === 'ArrowDown' ? 1 : -1);
      State.recentPick = next < -1 ? items.length - 1 : (next >= items.length ? -1 : next);
      Array.prototype.forEach.call(items, function (item, i) { item.classList.toggle('on', i === State.recentPick); });
    } else if (event.key === 'Enter') {
      event.preventDefault();
      pick(State.recentPick >= 0 && items[State.recentPick] ? items[State.recentPick].dataset.search : box.value);
    } else if (event.key === 'Escape') {
      if (!list.classList.contains('hidden')) {
        list.classList.add('hidden');
      } else {
        box.value = '';
        clearTimeout(timer);
        runSearch('');
      }
    }
  });
  // Held on mousedown, so the box keeps its focus and the list is still there for the click.
  list.addEventListener('mousedown', function (event) { event.preventDefault(); });
  list.addEventListener('click', function (event) {
    var item = event.target.closest('[data-search]');
    if (item) { pick(item.dataset.search); return; }
    if (event.target.closest('[data-clear-recent]')) {
      try { localStorage.removeItem(SEARCHES_KEY); } catch (err) { /* private mode */ }
      paintRecent();
    }
  });
  $('take-search-clear').addEventListener('click', function () {
    box.value = '';
    clearTimeout(timer);
    runSearch('');
    box.focus();
  });
  if ($('search-all')) {
    $('search-all').addEventListener('click', function () {
      State.searchAll = !State.searchAll;
      State.takesRaw = '';
      clearPicked();
      paintSearchCount();
      loadTakes();
    });
  }
}

function applyLayout(mode) {
  State.layout = mode === 'comfy' ? 'comfy' : 'compact';
  var wide = State.layout === 'comfy';
  $('takes').classList.toggle('comfy', wide);
  var button = $('layout-toggle');
  button.textContent = wide ? 'Comfy' : 'Compact';
  button.title = wide
    ? 'Wide cards with more of the prompt. Click for compact.'
    : 'Compact cards, three across. Click for wide.';
  try { localStorage.setItem(LAYOUT_KEY, State.layout); } catch (err) { /* private mode */ }
}

/* How wide the dashboard is. Wide fills the window and fits the most cards;
   fit centres the same 1500px column the app used before. Separate from the card
   size, so the two combine. */
function applyWidth(mode) {
  State.width = mode === 'fit' ? 'fit' : 'wide';
  var fit = State.width === 'fit';
  document.querySelector('main').classList.toggle('fit', fit);
  var button = $('width-toggle');
  button.textContent = fit ? 'Fit' : 'Wide';
  button.title = fit
    ? 'A centred column. Click to fill the window.'
    : 'Fills the window, most cards at once. Click for a centred column.';
  try { localStorage.setItem(WIDTH_KEY, State.width); } catch (err) { /* private mode */ }
}

function loadWidth() {
  var saved = null;
  try { saved = localStorage.getItem(WIDTH_KEY); } catch (err) { /* private mode */ }
  applyWidth(saved || 'wide');
}

function loadLayout() {
  var saved = null;
  try { saved = localStorage.getItem(LAYOUT_KEY); } catch (err) { saved = null; }
  applyLayout(saved === 'comfy' ? 'comfy' : 'compact');
  var filter = null;
  try { filter = localStorage.getItem(FILTER_KEY); } catch (err) { filter = null; }
  applyFilter(filter);
  var kinds = [];
  try { kinds = JSON.parse(localStorage.getItem(KINDS_KEY) || '[]'); } catch (err) { kinds = []; }
  applyKinds(Array.isArray(kinds) ? kinds : []);
}

function $(id) { return document.getElementById(id); }
function esc(text) {
  return String(text == null ? '' : text)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function secs(value) {
  if (!value && value !== 0) { return '--:--'; }
  var total = Math.round(value);
  var m = Math.floor(total / 60);
  var s = total % 60;
  return m + ':' + (s < 10 ? '0' : '') + s;
}
function age(ts) {
  var d = Math.floor(Date.now() / 1000 - ts);
  if (d < 60) { return 'just now'; }
  if (d < 3600) { return Math.floor(d / 60) + ' min ago'; }
  if (d < 86400) { return Math.floor(d / 3600) + ' h ago'; }
  return Math.floor(d / 86400) + ' d ago';
}
function initials(text) {
  var clean = String(text || '?').trim();
  return clean ? clean[0].toUpperCase() : '?';
}

async function api(path, options) {
  options = options || {};
  if (options.body && typeof options.body === 'string' && (!options.headers || !options.headers['Content-Type'])) {
    options.headers = Object.assign({}, options.headers, { 'Content-Type': 'application/json' });
  }
  var response = await fetch(path, options);
  if (!response.ok) {
    var detail = await response.text();
    try {
      var parsed = JSON.parse(detail);
      if (typeof parsed.detail === 'string') { detail = parsed.detail; }
      else if (Array.isArray(parsed.detail)) {
        detail = parsed.detail.map(function (item) { return (item.loc || []).slice(-1)[0] + ': ' + item.msg; }).join('; ');
      }
    } catch (err) { /* plain text */ }
    throw new Error(String(detail).slice(0, 300));
  }
  var type = response.headers.get('content-type') || '';
  return type.indexOf('application/json') >= 0 ? response.json() : response.text();
}

/* ------------------------------------------------------------------ state */
async function pollState() {
  try {
    var data = await api('/api/state');
    var pill = $('engine-pill');
    var engine = data.engine;
    State.options = data.options || {};
    State.training = data.training || null;
    State.currentJob = data.current || null;
    State.gpu = engine.online ? engine.gpu || null : null;
    if ($('train-modal') && !$('train-modal').classList.contains('hidden')) { paintTrainMemory(); }
    // No way in to a workflow that is switched off. Here rather than at
    // wiring time, because the options this reads arrive with the state, not before it.
    // Hidden rather than disabled: a greyed-out row invites a hunt for how to enable it.
    var corporaRow = $('menu-identities');
    if (corporaRow) { corporaRow.classList.toggle('hidden', !trainingAvailable()); }
    paintCorporaBadge();
    lockGpuControls();
    pill.title = '';
    if (engine.stuck) {
      // Its job thread died and it stayed up: it takes jobs and never runs them.
      pill.className = 'pill pill-off';
      pill.textContent = 'Engine needs a restart';
      pill.title = 'A job ran out of GPU memory and the engine stopped running jobs. Restart the engine; jobs wait until then.';
    } else if (engine.online && engine.compat && engine.compat.ok) {
      if (State.training) {
        pill.className = 'pill pill-wait';
        var pct = State.training.progress ? ' ' + Math.round(State.training.progress * 100) + '%' : '';
        pill.textContent = 'Training LoRA' + pct;
        pill.title = 'LoRA \u201c' + (State.training.lora_name || 'custom') + '\u201d is training and holds the GPU. Click to view in Corpora.';
        pill.style.cursor = 'pointer';
      } else {
        pill.className = 'pill pill-on';
        pill.textContent = 'Engine ready' + (engine.gpu ? ' \u00b7 ' + Math.round(engine.gpu.vram_free / 1073741824) + ' GB free' : '');
        pill.style.cursor = '';
      }
    } else if (engine.starting) {
      // Up before the engine: the page opens early, and a job asked for now waits.
      pill.className = 'pill pill-wait';
      pill.textContent = 'Engine starting\u2026';
    } else if (engine.online) {
      pill.className = 'pill pill-off';
      pill.textContent = 'Engine incompatible: ' + ((engine.compat.missing || []).join(', ') || (engine.compat.notes || []).join('; '));
    } else {
      pill.className = 'pill pill-off';
      pill.textContent = 'Engine offline';
    }
    State.stemsOptions = data.stems || State.stemsOptions || {};
    if (data.settings) { adoptSettings(data.settings); }
    if (data.version) { $('app-version').textContent = 'v' + data.version; }
    State.about = { version: data.version || '', build: data.build || '', model: data.model || '' };
    paintSystemStats(data.system);
    paintUpdate(data.update);
    paintOptions();
    paintJob(data.current, data.queue || [], data.options);
    watchPlan();
  } catch (err) {
    paintSystemStats(null);
    $('engine-pill').className = 'pill pill-off';
    $('engine-pill').textContent = 'App unreachable';
  }
}

function paintSystemStats(sys) {
  var gpuEl = $('gpu-stat');
  var gpuText = $('gpu-stat-text');
  if (gpuEl && gpuText) {
    if (sys && typeof sys.gpu === 'number' && !isNaN(sys.gpu)) {
      gpuText.textContent = sys.gpu + '%';
      gpuEl.title = 'GPU usage: ' + sys.gpu + '%';
      gpuEl.classList.remove('hidden');
    } else {
      gpuEl.classList.add('hidden');
    }
  }
  var cpuEl = $('cpu-stat');
  var cpuText = $('cpu-stat-text');
  if (cpuEl && cpuText) {
    if (sys && typeof sys.cpu === 'number' && !isNaN(sys.cpu)) {
      cpuText.textContent = sys.cpu + '%';
      cpuEl.title = 'CPU usage: ' + sys.cpu + '%';
      cpuEl.classList.remove('hidden');
    } else {
      cpuEl.classList.add('hidden');
    }
  }
}

/* How the render reads the score.  The same six the server knows, by id. */
var INTERPRETATIONS = {
  standard: { name: 'Standard', hint: 'YuE2\u2019s usual reading of the score.' },
  tight: { name: 'Tight', hint: 'More controlled and polished.' },
  loose: { name: 'Loose', hint: 'Rougher and more spontaneous.' },
  settled: { name: 'Settled', hint: 'Free to repeat a figure and sit in a groove.' },
  restless: { name: 'Restless', hint: 'Keeps the parts moving and avoids repeating itself.' },
  wide: { name: 'Wide', hint: 'Reaches for less obvious sounds.' }
};

function paintInterpretation() {
  var item = INTERPRETATIONS[$('interpretation').value] || INTERPRETATIONS.standard;
  $('interpretation-hint').textContent = item.hint;
  // What each option does, on the option itself, so it can be read before choosing it.
  Array.prototype.forEach.call($('interpretation').options, function (option) {
    var each = INTERPRETATIONS[option.value];
    if (each) { option.title = each.name + ': ' + each.hint; }
  });
}

function paintOptions() {
  paintHarmony();
  paintInterpretation();
  var canInst = State.options.instrumental_available !== false;
  $('create-inst').disabled = !canInst;
  $('create-inst').title = canInst ? '' : 'The engine has no instrumental LoRA. Run scripts/fetch-models.sh, then restart the engine.';
  var canWrite = State.options.lyrics_available !== false;
  $('lyrics-write').disabled = !canWrite;
  $('lyrics-write').title = canWrite
    ? (WRITE.id ? 'Drafting lyrics in progress\u2026 Click to view status or stop' : 'Draft lyrics from a short description')
    : 'The engine has no lyric writer. Run scripts/fetch-models.sh, then restart the engine.';
  if (canWrite) {
    $('lyrics-write').textContent = WRITE.id ? 'Drafting\u2026' : 'Write lyrics';
  }
  var canRealaudio = State.options.realaudio !== false;
  $('realaudio').disabled = !canRealaudio;
  if (!canRealaudio) {
    $('realaudio').checked = false;
    $('realaudio-field').title = 'The engine has no Realaudio LoRA. Run scripts/fetch-models.sh, then restart the engine.';
  } else {
    var tip = 'Applies Mothersuperior v9 real-audio decoder LoRA for studio-grade acoustic clarity, frequency separation, and clean lead vocals.';
    $('realaudio-field').title = tip;
    var raw = null;
    try { raw = localStorage.getItem(FORM_KEY); } catch (e) {}
    if (!raw || raw.indexOf('"realaudio"') === -1) {
      $('realaudio').checked = true;
    }
  }
  paintStyleLoras();
}

/* The style LoRA picker: whatever the engine can load, minus the two the app
   applies itself.  A file tells us which halves it holds, so a strength that
   would do nothing is not offered. */
var LORA_KINDS = { both: 'score and sound', planner: 'score only', decoder: 'sound only',
  other: 'not a YuE2 LoRA', unknown: '' };

/* Every LoRA that belongs to one of the Identities.  Those have a control of
   their own, where both of their strengths now live, so offering them here as
   well would be the same file in two places with two sets of settings. */
/* LoRAs trained here, from a corpus. They are ordinary LoRAs and belong in the one
   list with the rest: the picker already carries a planner strength and a sound
   strength, which is everything the corpus screen used to offer separately. */
function corpusLoras() {
  var found = {};
  (IDENTITIES_LIST || []).forEach(function (identity) {
    getIdentityLoRAs(identity).forEach(function (name) {
      found[name] = { trigger: identity.trigger_word || '', corpus: identity.name || '' };
    });
  });
  return found;
}

function loraCatalogue() {
  var mine = corpusLoras();
  return (State.options.loras || []).filter(function (item) {
    return item && !item.reserved && item.kind !== 'other';
  }).map(function (item) {
    var own = mine[item.name];
    if (!own) { return item; }
    var merged = {};
    for (var key in item) { merged[key] = item[key]; }
    merged.trigger = merged.trigger || own.trigger;
    merged.corpus = own.corpus;
    merged.title = merged.title || item.name;
    return merged;
  });
}

function loraKind(name) {
  var found = loraCatalogue().filter(function (item) { return item.name === name; })[0];
  return found ? found.kind : 'unknown';
}

/* A collection grows into dozens, and authors already name a set for what it
   is: mltnt_roots, chnsn_cabaret, slider-metal.  The word in front is the
   family, so the list groups itself without anything being hard-coded here.
   A family of one is no help to anyone, so those gather under Other. */
function loraFamily(name) {
  var head = name.replace(/\.safetensors$/i, '').split(/[-_]/)[0];
  return head.length > 1 ? head.toLowerCase() : 'other';
}

/* A named family is the set its author published, so two prefixes that share a
   name share a group: qwwl and drksf are one repository and belong together.
   Only the unnamed fall back to the word in the file name, and a lone one of
   those has nothing to head a group with. */
function loraGroupKey(item) {
  return item.family || loraFamily(item.name);
}

var LORA_CHECKPOINTS = 'Training checkpoints';

/* A training run's checkpoint (name_stepN) and the finished LoRA it belongs to. */
function loraCheckpoint(name) {
  var found = /^(.*)_step(\d+)\.safetensors$/i.exec(name || '');
  return found ? { parent: found[1] + '.safetensors', step: parseInt(found[2], 10) } : null;
}

function loraGroups(list) {
  var counts = {};
  list.forEach(function (item) {
    var key = loraGroupKey(item);
    counts[key] = (counts[key] || 0) + 1;
  });
  var groups = {};
  list.forEach(function (item) {
    var key = loraGroupKey(item);
    if (!item.family && counts[key] < 2) { key = 'other'; }
    (groups[key] = groups[key] || []).push(item);
  });
  return groups;
}

function paintStyleLoras() {
  var select = $('style-lora');
  if (!select) { return; }
  var list = loraCatalogue();
  $('style-lora-field').classList.remove('hidden');
  var chosen = select.value;
  var groups = loraGroups(list);
  // A run's checkpoints go under the LoRA they belong to, not in a heap of their
  // own: four runs came to 61 entries there. A previous run's go under its dated
  // LoRA the same way. Only one whose LoRA is gone stays where it was.
  var byName = {};
  list.forEach(function (item) { byName[item.name] = item; });
  var stepsOf = {};
  Object.keys(groups).forEach(function (key) {
    groups[key] = groups[key].filter(function (item) {
      var run = loraCheckpoint(item.name);
      if (!run || !byName[run.parent] || loraCheckpoint(run.parent)) { return true; }
      (stepsOf[run.parent] = stepsOf[run.parent] || []).push(item);
      return false;
    });
    if (!groups[key].length) { delete groups[key]; }
  });
  // Other goes last, and a training run's checkpoints just above it, under every
  // finished LoRA.  Their steps are counted, not spelt: 50 comes before 100.
  var rank = function (name) { return name === 'other' ? 2 : name === LORA_CHECKPOINTS ? 1 : 0; };
  var names = Object.keys(groups).sort(function (a, b) {
    return rank(a) - rank(b) || a.localeCompare(b);
  });
  if (groups[LORA_CHECKPOINTS]) {
    groups[LORA_CHECKPOINTS].sort(function (a, b) {
      return (a.title || a.name).localeCompare(b.title || b.name, undefined, { numeric: true });
    });
  }
  var option = function (item, parent) {
    var note = LORA_KINDS[item.kind] ? ' \u2014 ' + LORA_KINDS[item.kind] : '';
    // The author's own name for it beats a file name every time.
    var label = item.title || loraShortLabel(item.name);
    // On the option itself, so the list can be read before anything is chosen.
    var tip = [item.trigger ? 'Trigger: ' + item.trigger : '', plainNote(item.note), item.name]
      .filter(Boolean).join('\n\n');
    // A step keeps its full name here, for the picker's button, and a short one
    // for the menu, where its LoRA is the row above it.
    var step = parent ? ' data-parent="' + esc(parent) + '" data-short="step ' + loraCheckpoint(item.name).step + '"' : '';
    return '<option value="' + esc(item.name) + '" title="' + esc(tip) + '"' + step + '>' +
      esc(label) + esc(note) + '</option>';
  };
  var withSteps = function (item) {
    var steps = (stepsOf[item.name] || []).slice().sort(function (a, b) {
      return loraCheckpoint(a.name).step - loraCheckpoint(b.name).step;
    });
    return option(item) + steps.map(function (step) { return option(step, item.name); }).join('');
  };
  select.innerHTML = '<option value="">None</option>' + names.map(function (family) {
    var inner = groups[family].map(withSteps).join('');
    // One group and nothing to compare it with: the heading is noise.
    if (names.length < 2) { return inner; }
    // A named family is already its heading; an unnamed one is a bare file-name
    // prefix, and Other is a bag of odds and ends that must not borrow a name
    // from whichever of them happens to be first.
    var heading = family === 'other' ? 'Other'
      : (groups[family][0].family ? family : family.charAt(0).toUpperCase() + family.slice(1));
    return '<optgroup label="' + esc(heading) + '">' + inner + '</optgroup>';
  }).join('');
  // A remembered name waits here only until the list it names exists, and is
  // then spent.  Left in place it outlives the choice: the state poll repaints
  // this picker every couple of seconds, and would put the old LoRA back every
  // time None was chosen.
  if (!chosen && select.dataset.wanted) { chosen = select.dataset.wanted; }
  delete select.dataset.wanted;
  if (chosen) {
    select.value = chosen;
    var item = loraChosen();
    if (item && item.trigger) { State.loraTrigger = item.trigger; }
  }
  paintStyleLoraStrengths();
  paintLoraPicker();
}

/* A note is written for a web page, so it arrives with emphasis and code
   marks in it.  Nothing here renders those, and a stray asterisk reads as a
   mistake, so they come out. */
function plainNote(text) {
  return String(text || '')
    .replace(/\*\*/g, '').replace(/`/g, '')
    // A blank line is a paragraph and is kept; a single wrap is not and is not.
    .replace(/[ \t]*\n[ \t]*\n\s*/g, '\u0001')
    .replace(/\s*\n\s*/g, ' ')
    .replace(/\u0001/g, '\n')
    .trim();
}

/* The file name is what the engine wants, but not what anyone wants to read. */
function loraLabel(name) {
  return name.replace(/\.safetensors$/i, '').replace(/[_-]+/g, ' ');
}

/* Inside a family the shared word is already the heading above it. */
function loraShortLabel(name) {
  var label = loraLabel(name);
  var family = loraFamily(name);
  var head = label.split(' ')[0];
  return (head.toLowerCase() === family && label.indexOf(' ') > 0) ? label.slice(head.length + 1) : label;
}

/* A file name says nothing about what a LoRA does, so whatever its author
   wrote is shown under the picker, and the trigger word is shown as something
   to click, because it has to reach the style box to do anything. */
/* Training is offered when the engine image carries the trainer node pack and the
   app has TRAINING_ENABLED set, both the defaults. The server answers both in one
   flag, so the page never offers a button that would 501. */
function trainingAvailable() {
  return Boolean(State.options && State.options.training_available);
}

/* Is this one of ours?  A file trained by this app is labelled custom; one
   downloaded from elsewhere is not. */
function loraTrainedHere(name) {
  return Boolean(name && corpusLoras()[name]);
}

/* ------------------------------------------------------ Style LoRA picker
   The select stays the source of truth: every path that sets or reads the style
   LoRA goes through it, and this draws its groups as a menu that folds.  Which groups
   are open is remembered in the browser.  If drawing fails, the select is left in
   view and works as it always did. */
var LORA_OPEN_KEY = 'yue2.lora-groups';

function loraOpenGroups() {
  try { return JSON.parse(localStorage.getItem(LORA_OPEN_KEY) || '[]') || []; } catch (err) { return []; }
}

function saveLoraOpenGroups(list) {
  try { localStorage.setItem(LORA_OPEN_KEY, JSON.stringify(list)); } catch (err) { /* private mode */ }
}

function chosenLoraGroup() {
  var select = $('style-lora');
  var option = select && select.options[select.selectedIndex];
  return option && option.parentNode && option.parentNode.tagName === 'OPTGROUP' ? option.parentNode.label : null;
}

function paintLoraPicker() {
  var select = $('style-lora');
  var picker = $('lora-picker');
  var menu = $('lora-picker-menu');
  if (!select || !picker || !menu) { return; }
  try {
    var chosen = select.value;
    var current = select.options[select.selectedIndex];
    $('lora-picker-label').textContent = current ? current.textContent : 'None';
    var open = loraOpenGroups();
    // A LoRA with a run's checkpoints folds them under its own row, remembered
    // with the groups as "steps:" and its name.
    var stepCount = {};
    Array.prototype.forEach.call(select.querySelectorAll('option[data-parent]'), function (option) {
      stepCount[option.dataset.parent] = (stepCount[option.dataset.parent] || 0) + 1;
    });
    var entry = function (option, flat) {
      var parent = option.dataset.parent;
      if (parent && open.indexOf('steps:' + parent) < 0) { return ''; }
      var count = stepCount[option.value];
      var stepsOpen = open.indexOf('steps:' + option.value) >= 0;
      var toggle = count ? '<span class="lora-steps-toggle" role="button" aria-expanded="' + stepsOpen + '" data-steps="' +
        esc(option.value) + '" title="' + (stepsOpen ? 'Hide' : 'Show') + ' the checkpoints its training run kept">' +
        (stepsOpen ? '\u25BE' : '\u25B8') + ' ' + count + ' step' + (count === 1 ? '' : 's') + '</span>' : '';
      return '<div class="source-picker-item lora-item' + (flat ? ' flat' : '') + (parent ? ' lora-step' : '') +
        (option.value === chosen ? ' selected' : '') +
        '" role="option" data-value="' + esc(option.value) + '" title="' + esc(option.title || '') + '">' +
        '<span class="source-item-title">' + esc(parent ? option.dataset.short : option.textContent) + '</span>' + toggle + '</div>';
    };
    var html = '';
    Array.prototype.forEach.call(select.children, function (child) {
      if (child.tagName !== 'OPTGROUP') { html += entry(child, true); return; }
      var isOpen = open.indexOf(child.label) >= 0;
      html += '<div class="lora-group" role="button" aria-expanded="' + isOpen + '" data-group="' + esc(child.label) + '">' +
        '<span class="fold">' + (isOpen ? '\u25BE' : '\u25B8') + '</span><span>' + esc(child.label) + '</span>' +
        '<span class="count">' + child.querySelectorAll('option:not([data-parent])').length + '</span></div>';
      if (isOpen) { Array.prototype.forEach.call(child.children, function (option) { html += entry(option, false); }); }
    });
    // The state poll repaints every few seconds; an unchanged menu is left alone so
    // it does not jump under the pointer.
    if (menu.dataset.html !== html) { menu.innerHTML = html; menu.dataset.html = html; }
    select.classList.add('hidden');
    picker.classList.remove('hidden');
  } catch (err) {
    select.classList.remove('hidden');
    picker.classList.add('hidden');
  }
}

function openLoraPicker() {
  var menu = $('lora-picker-menu');
  var btn = $('lora-picker-btn');
  // The group holding the current choice opens with the menu, so it is never hidden.
  var group = chosenLoraGroup();
  var open = loraOpenGroups();
  if (group && open.indexOf(group) < 0) { open.push(group); saveLoraOpenGroups(open); }
  // And a chosen checkpoint's LoRA opens its steps.
  var select = $('style-lora');
  var current = select && select.options[select.selectedIndex];
  var parent = current && current.dataset.parent;
  if (parent && open.indexOf('steps:' + parent) < 0) { open.push('steps:' + parent); saveLoraOpenGroups(open); }
  paintLoraPicker();
  // It sits near the bottom of the column, so it opens whichever way has the room.
  var box = btn.getBoundingClientRect();
  var panel = btn.closest('.panel');
  var bounds = panel ? panel.getBoundingClientRect() : { top: 0, bottom: window.innerHeight };
  var below = Math.min(bounds.bottom, window.innerHeight) - box.bottom;
  var above = box.top - Math.max(bounds.top, 0);
  var up = above > below;
  menu.classList.toggle('up', up);
  menu.style.maxHeight = Math.max(160, Math.min(360, (up ? above : below) - 12)) + 'px';
  menu.classList.remove('hidden');
  btn.setAttribute('aria-expanded', 'true');
  var selected = menu.querySelector('.selected');
  if (selected) { selected.scrollIntoView({ block: 'nearest' }); }
}

function closeLoraPicker() {
  var menu = $('lora-picker-menu');
  var btn = $('lora-picker-btn');
  if (!menu || !btn) { return; }
  menu.classList.add('hidden');
  btn.setAttribute('aria-expanded', 'false');
}

function paintStyleLoraNote() {
  paintLoraPicker();
  var item = loraChosen();
  var download = $('lora-download');
  if (download) {
    download.classList.toggle('hidden', !item);
    download.href = item ? '/api/loras/' + encodeURIComponent(item.name) + '/download' : '#';
  }
  if ($('lora-delete')) { $('lora-delete').classList.toggle('hidden', !item); }
  var steps = $('lora-steps');
  if (steps) {
    var hasSteps = Boolean(item) && loraSteps(item.name).length > 0;
    steps.classList.toggle('hidden', !item);
    steps.disabled = !hasSteps;
    steps.title = hasSteps
      ? 'Render what this panel makes once on each training checkpoint of this LoRA, to compare them by ear'
      : 'This LoRA has no training checkpoints';
  }
  if ($('lora-strengths')) { $('lora-strengths').classList.toggle('hidden', !item); }
  var label = document.querySelector('label[for="style-lora"]');
  if (label) {
    label.textContent = loraTrainedHere(item && item.name) ? 'Style LoRA \u2014 custom' : 'Style LoRA';
  }
  // The list is read from the engine, so a file added by hand needs a nudge. The app
  // looks again every five minutes; this is for when five minutes is too long.
  var hint = $('style-lora-hint');
  if (!item) {
    hint.innerHTML = 'Planner shapes what is played, Sound how it sounds.';
    return;
  }
  var parts = [];
  if (item.trigger) {
    parts.push(styleHas($('style').value, item.trigger)
      ? 'Trigger word <b>' + esc(item.trigger) + '</b> is in the style.'
      : '<b>' + esc(item.trigger) + '</b> goes in the style when you render.');
  }
  if (item.strengths) {
    var pair = 'Planner ' + Number(item.strengths.planner).toFixed(2) + ' / Sound ' + Number(item.strengths.sound).toFixed(2);
    // Off its saved pair (a take made at other strengths, or the sliders moved): offer
    // the way back, here rather than as another button in the row.
    var held = loraKind(item.name);
    var off = ((held === 'both' || held === 'planner') && Math.abs(Number($('style-lora-clip').value) - item.strengths.planner) > 0.004) ||
              ((held === 'both' || held === 'decoder') && Math.abs(Number($('style-lora-model').value) - item.strengths.sound) > 0.004);
    parts.push(off
      ? 'Saved: <b>' + pair + '</b> <button type="button" id="lora-use-saved" class="chip action compact" title="Put this LoRA\u2019s saved strengths back on the sliders">use</button>'
      : 'Starts at <b>' + pair + '</b>.');
  }
  if (item.styles && item.styles.length) {
    parts.push('<b>Learned styles:</b> ' + item.styles.length + ' corpus songs. Click any style chip under the Style box to write in that sound.');
  }
  if (item.note) { parts.push(esc(plainNote(item.note)).replace(/\n/g, '<br>')); }
  // What the file needs to do anything, and whether it currently is.
  var kind = loraKind(item.name);
  // A file with both halves is the usual case and needs no remark.
  var holds = { planner: 'Planner only: Sound has no effect with this file.',
                decoder: 'Sound only: Planner has no effect with this file.' }[kind];
  if (holds) { parts.push(holds); }
  var asleep = [];
  if ((kind === 'both' || kind === 'planner') && Number($('style-lora-clip').value) === 0) { asleep.push('Planner'); }
  if ((kind === 'both' || kind === 'decoder') && Number($('style-lora-model').value) === 0) { asleep.push('Sound'); }
  if (asleep.length) {
    parts.push('<b>' + asleep.join(' and ') + ' at 0.00</b>, so this file is doing nothing.');
  }
  if (State.mode === 'inst') {
    var clipVal = Number($('style-lora-clip') ? $('style-lora-clip').value : 0);
    var harmVal = Number($('harmony') ? $('harmony').value : 0);
    if (clipVal > 0.70 || harmVal > 0) {
      var warnings = [];
      if (clipVal > 0.70) { warnings.push('Planner above 0.70 (' + clipVal.toFixed(2) + ')'); }
      if (harmVal > 0) { warnings.push('Varied harmony'); }
      parts.push('<span style="color: #f59e0b;">⚠️ <b>Instrumental note:</b> The instrumental model is already active on the planner. ' + warnings.join(' and ') + ' can cause token conflicts during score planning. Recommended: <b>Planner ~0.50–0.60</b> with <b>Familiar</b> harmony.</span>');
    } else {
      parts.push('<b>Instrumental note:</b> with the instrumental model active, keeping style Planner around <b>0.50–0.60</b> avoids score planner conflicts.');
    }
    if (loraTrainedHere(item.name)) {
      parts.push('<b>Sound texture:</b> Sound strength around <b>~0.55–0.60</b> applies the corpus acoustic texture cleanly.');
    }
  } else if (loraTrainedHere(item.name) && !item.strengths) {
    // General advice, until the LoRA has strengths of its own.
    parts.push(State.mode === 'cover'
      ? '<b>In a cover</b>, keep Sound near 0.50: your recording sets the tune.'
      : '<b>Trained from a corpus:</b> up to about 0.70 / 0.70, with Plan variety Calm or Normal.');
  }
  hint.innerHTML = parts.join('<br>');
}

/* The engine's list is read once, and looked at again every few minutes. A file
   added by hand can wait; this is for when it should not. */
async function reloadLoras() {
  var button = $('lora-reload');
  if (button) { button.textContent = 'Scanning\u2026'; }
  try {
    var found = await api('/api/engine/reload-options', { method: 'POST' });
    await pollState();
    paintStyleLoras();
    statusLine('The engine lists ' + found.loras + ' LoRAs.', 'good');
  } catch (err) {
    statusLine('Could not read the engine\u2019s list: ' + err.message, 'bad');
  }
  if (button) { button.textContent = 'Rescan'; }
}

/* A strength of zero on a half the file does hold is the same as not choosing the
   file at all: it loads and multiplies by nothing.  saveForm stores a zero for a half
   a file cannot use, so choosing a file that needs that half brought the zero with
   it.  Choosing a file now wakes the strengths it can use, once, at the moment of
   choosing — never on a repaint, so a slider deliberately left at zero stays there. */
function wakeStyleLoraStrengths() {
  var name = $('style-lora').value;
  if (!name) { return; }
  var kind = loraKind(name);
  var hasPlanner = kind === 'both' || kind === 'planner' || kind === 'unknown';
  var hasSound = kind === 'both' || kind === 'decoder' || kind === 'unknown';
  var isInst = State.mode === 'inst';
  // A LoRA with strengths of its own starts at them.
  var item = loraChosen();
  if (item && item.strengths) {
    if (hasPlanner) { $('style-lora-clip').value = item.strengths.planner; }
    if (hasSound) { $('style-lora-model').value = item.strengths.sound; }
    return;
  }
  if (hasPlanner && (Number($('style-lora-clip').value) === 0 || (isInst && $('style-lora-clip').value === '1'))) {
    $('style-lora-clip').value = isInst ? 0.6 : 1;
  }
  if (hasSound && Number($('style-lora-model').value) === 0) {
    $('style-lora-model').value = isInst ? 0.6 : 1;
  }
}

/* One strength: an editable number and a slider that agree with each other.  A half
   the file does not hold has no number to edit, so the box goes empty and says why on
   hover; the note under the picker says it in words as well. */
function paintStrengthValue(sliderId, held, force) {
  var slider = $(sliderId);
  var box = $(sliderId + '-value');
  if (!slider || !box) { return; }
  box.disabled = !held;
  if (!held) {
    box.value = '';
    box.placeholder = '\u2014';
    box.title = 'This file holds no ' + (sliderId.indexOf('clip') >= 0 ? 'planner' : 'sound') + ' half';
    return;
  }
  // Skipped while the box has focus, so a half-typed number is not overwritten — but
  // not when the slider itself moved, which is the user saying the opposite.
  if (force || document.activeElement !== box) { box.value = Number(slider.value).toFixed(2); }
  box.title = 'Type an exact strength';
}

function setStrength(sliderId, value) {
  var slider = $(sliderId);
  if (!slider) { return; }
  var number = Number(value);
  if (!isFinite(number)) { return; }
  slider.value = String(Math.max(0, Math.min(3, number)));
  paintStyleLoraStrengths();
  saveForm();
}

function paintStyleLoraStrengths() {
  paintStyleLoraNote();
  paintPresets();
  var name = $('style-lora').value;
  var kind = name ? loraKind(name) : '';
  $('style-lora-strengths').classList.toggle('hidden', !name);
  if (!name) { return; }
  // A strength for a half the file does not hold is a control that lies.
  var hasPlanner = kind === 'both' || kind === 'planner' || kind === 'unknown';
  var hasSound = kind === 'both' || kind === 'decoder' || kind === 'unknown';
  $('style-lora-clip').disabled = !hasPlanner;
  $('style-lora-model').disabled = !hasSound;
  // The number beside each slider is editable: typing sets the slider; the slider updates the number.
  paintStrengthValue('style-lora-clip', hasPlanner);
  paintStrengthValue('style-lora-model', hasSound);
}

/* Adds the chosen LoRA to a request body, or nothing at all when none is
   chosen.  A strength whose half is missing from the file is sent as zero. */
/* A LoRA trained on captions that begin with its trigger does very little
   without it, and the app knows which word it needs, so the app puts it there.
   Choosing a different LoRA takes the old word out again; one already typed is
   left where it is. */
function removeStyleWord(text, word) {
  if (!word || !text) { return text || ''; }
  var w = word.trim().toLowerCase();
  var tags = text.split(',').map(function (t) { return t.trim(); }).filter(Boolean);
  var filtered = tags.filter(function (t) { return t.toLowerCase() !== w; });
  var joined = filtered.join(', ');
  if (styleHas(joined, w)) {
    joined = joined.replace(new RegExp('\\b' + w + '\\b', 'gi'), '');
  }
  return tidyStyle(joined);
}

function allKnownLoraTriggers() {
  var triggers = {};
  if (State.loraTrigger) {
    triggers[State.loraTrigger.trim().toLowerCase()] = true;
  }
  (loraCatalogue() || []).forEach(function (item) {
    if (item && item.trigger) {
      triggers[item.trigger.trim().toLowerCase()] = true;
    }
  });
  (IDENTITIES_LIST || []).forEach(function (id) {
    if (id && id.trigger_word) {
      triggers[id.trigger_word.trim().toLowerCase()] = true;
    }
  });
  return Object.keys(triggers);
}

function applyLoraTrigger(trigger) {
  var style = $('style');
  if (!style) { return; }
  var text = style.value || '';
  var newTrigger = (trigger || '').trim().toLowerCase();

  // Strip any other known LoRA or identity trigger words currently in the style
  var known = allKnownLoraTriggers();
  known.forEach(function (t) {
    if (t && t !== newTrigger) {
      text = removeStyleWord(text, t);
    }
  });

  if (State.loraTrigger) {
    var prev = State.loraTrigger.trim().toLowerCase();
    if (prev && prev !== newTrigger) {
      text = removeStyleWord(text, prev);
    }
  }

  // Prepend new trigger word to the style text if specified and not already present
  if (newTrigger && !styleHas(text, newTrigger)) {
    text = tidyStyle(newTrigger + (text ? ', ' + text : ''));
  }

  text = tidyStyle(text);
  State.loraTrigger = trigger ? trigger.trim() : null;
  if (text !== style.value) {
    style.value = text;
    style.dataset.touched = '1';
    saveForm();
  }
}

/* Put a take's LoRA back in the picker.  Its style already carries the trigger
   word, so the word is remembered rather than inserted: nothing about the text
   changes, but choosing a different LoRA can still take the old one out. */
function showStyleLora(take) {
  var select = $('style-lora');
  if (!select) { return; }
  select.value = take.style_lora || '';
  select.dataset.wanted = take.style_lora || '';
  if (take.style_lora) {
    $('style-lora-model').value = take.style_lora_model === undefined ? 1 : take.style_lora_model;
    $('style-lora-clip').value = take.style_lora_clip === undefined ? 1 : take.style_lora_clip;
  }
  var item = loraChosen();
  State.loraTrigger = (item && item.trigger) || null;
  paintStyleLoraStrengths();
  saveForm();
}

function loraChosen() {
  var select = $('style-lora');
  if (!select || !select.value) { return null; }
  return loraCatalogue().filter(function (entry) { return entry.name === select.value; })[0] || null;
}

function withStyleLora(data) {
  var select = $('style-lora');
  if (!select || !select.value) { return data; }
  var item = loraChosen();
  if (item && item.trigger) {
    // A style typed or restored without it would render as if no LoRA were on.
    applyLoraTrigger(item.trigger);
    if (typeof data.style === 'string') { data.style = $('style').value; }
  }
  data.style_lora = select.value;
  data.style_lora_model = $('style-lora-model').disabled ? 0 : parseFloat($('style-lora-model').value);
  data.style_lora_clip = $('style-lora-clip').disabled ? 0 : parseFloat($('style-lora-clip').value);
  return data;
}

/* ============================================== advanced take settings (#32) */
var ADVANCED_DEFAULTS = {
  sampler_steps: 32,
  avoid: '',
  target_key: '',
  target_bpm: null,
  max_abc_tokens: 8192,
  chord_hold_limit: 8,
  chord_outside_bonus: 0.0,
  chord_sections: null,
  follow_structure: null,
  target_lufs: -14.0,
  fade_out_seconds: 3.0
};

function readAdvancedSettings() {
  if (!$('adv-sampler-steps')) { return Object.assign({}, ADVANCED_DEFAULTS); }
  var steps = parseInt($('adv-sampler-steps').value, 10);
  if (isNaN(steps) || steps < 16 || steps > 64) { steps = ADVANCED_DEFAULTS.sampler_steps; }
  var avoid = ($('adv-avoid').value || '').trim();
  var targetKey = ($('adv-target-key').value || '').trim();
  var bpmRaw = parseInt($('adv-target-bpm').value, 10);
  var targetBpm = (!isNaN(bpmRaw) && bpmRaw >= 20 && bpmRaw <= 400) ? bpmRaw : null;
  var tokens = parseInt($('adv-max-abc-tokens').value, 10);
  if (isNaN(tokens) || tokens < 512 || tokens > 8192) { tokens = ADVANCED_DEFAULTS.max_abc_tokens; }
  var hold = parseInt($('adv-chord-hold-limit').value, 10);
  if (isNaN(hold) || hold < 1 || hold > 32) { hold = ADVANCED_DEFAULTS.chord_hold_limit; }
  var outside = parseFloat($('adv-chord-outside-bonus').value);
  if (isNaN(outside) || outside < 0.0 || outside > 10.0) { outside = ADVANCED_DEFAULTS.chord_outside_bonus; }
  var sectionsRaw = $('adv-chord-sections') ? $('adv-chord-sections').value : '';
  var sections = sectionsRaw === '1' ? 1 : (sectionsRaw === '0' ? 0 : null);
  var follow = $('follow-structure') && $('follow-structure').checked ? 1 : null;
  var lufs = parseFloat($('adv-target-lufs').value);
  if (isNaN(lufs) || lufs < -30.0 || lufs > -4.0) { lufs = ADVANCED_DEFAULTS.target_lufs; }
  var fade = parseFloat($('adv-fade-out-seconds').value);
  if (isNaN(fade) || fade < 0.5 || fade > 15.0) { fade = ADVANCED_DEFAULTS.fade_out_seconds; }
  return {
    sampler_steps: steps,
    avoid: avoid,
    target_key: targetKey,
    target_bpm: targetBpm,
    max_abc_tokens: tokens,
    chord_hold_limit: hold,
    chord_outside_bonus: outside,
    chord_sections: sections,
    follow_structure: follow,
    target_lufs: lufs,
    fade_out_seconds: fade
  };
}

function isAdvancedDirty() {
  var cur = readAdvancedSettings();
  return cur.sampler_steps !== ADVANCED_DEFAULTS.sampler_steps ||
    cur.avoid !== ADVANCED_DEFAULTS.avoid ||
    cur.target_key !== ADVANCED_DEFAULTS.target_key ||
    cur.target_bpm !== ADVANCED_DEFAULTS.target_bpm ||
    cur.max_abc_tokens !== ADVANCED_DEFAULTS.max_abc_tokens ||
    cur.chord_hold_limit !== ADVANCED_DEFAULTS.chord_hold_limit ||
    Math.abs(cur.chord_outside_bonus - ADVANCED_DEFAULTS.chord_outside_bonus) > 0.001 ||
    cur.chord_sections !== ADVANCED_DEFAULTS.chord_sections ||
    Math.abs(cur.target_lufs - ADVANCED_DEFAULTS.target_lufs) > 0.001 ||
    Math.abs(cur.fade_out_seconds - ADVANCED_DEFAULTS.fade_out_seconds) > 0.001;
}

function updateAdvancedButtonState() {
  var btn = $('btn-advanced-toggle');
  var dot = $('adv-active-dot');
  var resetBtn = $('adv-reset-btn');
  if (!btn) { return; }
  var dirty = isAdvancedDirty();
  if (dirty) {
    btn.classList.add('is-active');
    if (dot) { dot.classList.remove('hidden'); }
    btn.title = 'Advanced take settings (custom values active)';
    if (resetBtn) { resetBtn.disabled = false; }
  } else {
    btn.classList.remove('is-active');
    if (dot) { dot.classList.add('hidden'); }
    btn.title = 'Advanced take settings (all defaults)';
    if (resetBtn) { resetBtn.disabled = true; }
  }
}

function writeAdvancedSettings(data) {
  if (!$('adv-sampler-steps')) { return; }
  data = data || {};
  var steps = data.sampler_steps != null ? data.sampler_steps : ADVANCED_DEFAULTS.sampler_steps;
  $('adv-sampler-steps').value = steps;
  if ($('adv-sampler-steps-range')) { $('adv-sampler-steps-range').value = steps; }
  $('adv-avoid').value = data.avoid || '';
  $('adv-target-key').value = data.target_key || '';
  $('adv-target-bpm').value = data.target_bpm != null ? data.target_bpm : '';
  $('adv-max-abc-tokens').value = data.max_abc_tokens != null ? data.max_abc_tokens : ADVANCED_DEFAULTS.max_abc_tokens;
  $('adv-chord-hold-limit').value = data.chord_hold_limit != null ? data.chord_hold_limit : ADVANCED_DEFAULTS.chord_hold_limit;
  $('adv-chord-outside-bonus').value = data.chord_outside_bonus != null ? data.chord_outside_bonus : ADVANCED_DEFAULTS.chord_outside_bonus;
  if ($('adv-chord-sections')) { $('adv-chord-sections').value = data.chord_sections === 1 ? '1' : (data.chord_sections === 0 ? '0' : ''); }
  if ($('follow-structure')) { $('follow-structure').checked = data.follow_structure === 1; }
  $('adv-target-lufs').value = data.target_lufs != null ? data.target_lufs : ADVANCED_DEFAULTS.target_lufs;
  $('adv-fade-out-seconds').value = data.fade_out_seconds != null ? data.fade_out_seconds : ADVANCED_DEFAULTS.fade_out_seconds;
  updateAdvancedButtonState();
}

function resetAdvancedSettings() {
  var follow = $('follow-structure') && $('follow-structure').checked;    // lives under the lyrics, not in this window
  writeAdvancedSettings(ADVANCED_DEFAULTS);
  if ($('follow-structure')) { $('follow-structure').checked = follow; }
  saveForm();
}

function loadAdvancedTakeSettings(take) {
  if (!take) {
    writeAdvancedSettings(ADVANCED_DEFAULTS);
    return;
  }
  writeAdvancedSettings({
    sampler_steps: take.sampler_steps != null ? take.sampler_steps : ADVANCED_DEFAULTS.sampler_steps,
    avoid: take.avoid || '',
    target_key: take.target_key || '',
    target_bpm: take.target_bpm != null ? take.target_bpm : null,
    max_abc_tokens: take.max_abc_tokens != null ? take.max_abc_tokens : ADVANCED_DEFAULTS.max_abc_tokens,
    chord_hold_limit: take.chord_hold_limit != null ? take.chord_hold_limit : ADVANCED_DEFAULTS.chord_hold_limit,
    chord_outside_bonus: take.chord_outside_bonus != null ? take.chord_outside_bonus : ADVANCED_DEFAULTS.chord_outside_bonus,
    chord_sections: take.chord_sections === 1 || take.chord_sections === 0 ? take.chord_sections : null,
    follow_structure: take.follow_structure === 1 ? 1 : null,
    target_lufs: take.target_lufs != null ? take.target_lufs : ADVANCED_DEFAULTS.target_lufs,
    fade_out_seconds: take.fade_out_seconds != null ? take.fade_out_seconds : ADVANCED_DEFAULTS.fade_out_seconds
  });
}

function withAdvancedSettings(body) {
  var adv = readAdvancedSettings();
  body.sampler_steps = adv.sampler_steps;
  body.avoid = adv.avoid || null;
  body.target_key = adv.target_key || null;
  body.target_bpm = adv.target_bpm != null ? adv.target_bpm : null;
  body.max_abc_tokens = adv.max_abc_tokens;
  body.chord_hold_limit = adv.chord_hold_limit;
  body.chord_outside_bonus = adv.chord_outside_bonus;
  body.chord_sections = adv.chord_sections;
  body.follow_structure = adv.follow_structure;
  body.target_lufs = Math.abs(adv.target_lufs - ADVANCED_DEFAULTS.target_lufs) > 0.001 ? adv.target_lufs : null;
  body.fade_out_seconds = adv.fade_out_seconds;
  return body;
}

function openAdvancedModal() {
  if ($('advanced-take-modal')) {
    updateAdvancedButtonState();
    $('advanced-take-modal').classList.remove('hidden');
  }
}

function closeAdvancedModal() {
  if ($('advanced-take-modal')) {
    $('advanced-take-modal').classList.add('hidden');
  }
}

function wireAdvancedSettings() {
  var toggleBtn = $('btn-advanced-toggle');
  var modal = $('advanced-take-modal');
  var closeBtn = $('adv-close-btn');
  var doneBtn = $('adv-done-btn');
  var resetBtn = $('adv-reset-btn');

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      if (modal && !modal.classList.contains('hidden')) {
        closeAdvancedModal();
      } else {
        openAdvancedModal();
      }
    });
  }

  if (closeBtn) { closeBtn.addEventListener('click', closeAdvancedModal); }
  if (doneBtn) { doneBtn.addEventListener('click', closeAdvancedModal); }
  if (resetBtn) {
    resetBtn.addEventListener('click', function () {
      resetAdvancedSettings();
      updateAdvancedButtonState();
    });
  }

  if (modal) {
    modal.addEventListener('click', function (event) {
      if (backdropClick(event, modal)) { closeAdvancedModal(); }
    });
  }

  var syncRangeNum = function (rangeId, numId) {
    var r = $(rangeId);
    var n = $(numId);
    if (!r || !n) { return; }
    r.addEventListener('input', function () {
      n.value = r.value;
      updateAdvancedButtonState();
      saveForm();
    });
    n.addEventListener('input', function () {
      r.value = n.value;
      updateAdvancedButtonState();
      saveForm();
    });
  };

  syncRangeNum('adv-sampler-steps-range', 'adv-sampler-steps');

  var inputs = [
    'adv-sampler-steps', 'adv-avoid', 'adv-target-key', 'adv-target-bpm',
    'adv-max-abc-tokens', 'adv-chord-hold-limit',
    'adv-chord-outside-bonus', 'adv-chord-sections', 'follow-structure', 'adv-target-lufs', 'adv-fade-out-seconds'
  ];
  inputs.forEach(function (id) {
    var el = $(id);
    if (!el) { return; }
    el.addEventListener('input', function () {
      updateAdvancedButtonState();
      saveForm();
    });
    if (el.tagName === 'SELECT') {
      el.addEventListener('change', function () {
        updateAdvancedButtonState();
        saveForm();
      });
    }
  });

  updateAdvancedButtonState();
}

/* The form survives a reload. Nothing here is precious, but losing a verse is annoying. */
var FORM_KEY = 'yue2.form.v1';
var FORM_FIELDS = ['title', 'style', 'lyrics', 'mode', 'seed', 'interpretation', 'max-duration', 'variety', 'harmony'];

/* The page's HTML is read once at start-up and the script on every load, so the
   box may not exist yet; then nothing is normalised, as before it was added. */
function normaliseWanted() {
  var box = $('normalise');
  return Boolean(box && box.checked);
}

function saveForm() {
  try {
    var data = {};
    FORM_FIELDS.forEach(function (id) { data[id] = $(id).value; });
    data.auto_render = $('auto-render').checked;
    data.seed_fixed = $('seed-fixed').checked;
    data.realaudio = $('realaudio').checked;
    data.normalise = normaliseWanted();
    data.source = $('source-select') ? $('source-select').value : '';
    data.style_lora = $('style-lora') ? $('style-lora').value : '';
    data.style_lora_model = $('style-lora-model') ? $('style-lora-model').value : '1';
    data.style_lora_clip = $('style-lora-clip') ? $('style-lora-clip').value : '1';
    data.lora_trigger = State.loraTrigger || '';
    data.left_take = selectedTakeId() || '';
    data.box_kind = Selection.boxKind;
    data.box_id = Selection.boxId || '';
    data.awaiting = awaitingPlanId() || '';
    data.structure = { kind: STRUCTURE.kind, sections: STRUCTURE.sections };
    data.song_plan = SONGPLAN.sections;
    data.feel = FEEL.value;
    data.ui_mode = State.mode;
    data.advanced = readAdvancedSettings();
    localStorage.setItem(FORM_KEY, JSON.stringify(data));
  } catch (err) { /* private mode, or storage full. Not worth a message. */ }
}

/* Cover, Song or Instrumental, as the page was left.  Cover the first time. */
function savedMode() {
  try {
    var mode = JSON.parse(localStorage.getItem(FORM_KEY) || '{}').ui_mode;
    return ['cover', 'song', 'inst'].indexOf(mode) >= 0 ? mode : 'cover';
  } catch (err) { return 'cover'; }
}

function loadForm() {
  var raw;
  try { raw = localStorage.getItem(FORM_KEY); } catch (err) { return; }
  if (!raw) { return; }
  var data;
  try { data = JSON.parse(raw); } catch (err) { return; }
  FORM_FIELDS.forEach(function (id) {
    if (typeof data[id] === 'string' && data[id]) { $(id).value = data[id]; }
  });
  paintVocals();
  if (typeof data.auto_render === 'boolean') { $('auto-render').checked = data.auto_render; }
  if (typeof data.seed_fixed === 'boolean') { $('seed-fixed').checked = data.seed_fixed; }
  if (typeof data.realaudio === 'boolean') { $('realaudio').checked = data.realaudio; }
  else { $('realaudio').checked = true; }
  if ($('normalise')) { $('normalise').checked = data.normalise === true; }
  // The list arrives from the server, so the name is held until it exists.
  if (typeof data.source === 'string') { State.wantedSource = data.source; }
  if (data.lora_trigger) { State.loraTrigger = data.lora_trigger; }
  if ($('style-lora')) {
    if (data.style_lora_model) { $('style-lora-model').value = data.style_lora_model; }
    if (data.style_lora_clip) { $('style-lora-clip').value = data.style_lora_clip; }
    // The list arrives with the options, so the name is held until it can be set.
    $('style-lora').dataset.wanted = data.style_lora || '';
  }
  if (data.style) { $('style').dataset.touched = '1'; }
  restoreSelection({ formTakeId: data.left_take || null, boxKind: data.box_kind || 'none',
                     boxId: data.box_id || null, awaiting: data.awaiting || null });
  if (FEELS[data.feel]) { FEEL.value = data.feel; }
  if (data.structure && Array.isArray(data.structure.sections)) {
    STRUCTURE.kind = ['free', 'sections', 'timed'].indexOf(data.structure.kind) >= 0 ? data.structure.kind : 'free';
    STRUCTURE.sections = data.structure.sections.filter(function (item) {
      return item && SECTIONS.indexOf(item.name) >= 0;
    }).map(function (item) { return { name: item.name, seconds: Math.max(4, Math.min(180, Number(item.seconds) || 20)) }; });
  }
  if (Array.isArray(data.song_plan)) {
    var kept = data.song_plan.filter(function (name) { return SONG_SECTIONS.indexOf(name) >= 0; });
    if (kept.length) { SONGPLAN.sections = kept; }
  }
  if (data.advanced) { writeAdvancedSettings(data.advanced); }
  else { updateAdvancedButtonState(); }
}

/* A title from the first real lyric line. Section tags and genre tags do not count. */
function guessTitle(lyrics) {
  var lines = String(lyrics || '').split('\n');
  for (var i = 0; i < lines.length; i++) {
    var text = lines[i].trim();
    if (!text) { continue; }
    if (text.charAt(0) === '[' || text.charAt(0) === '(' || text.charAt(0) === '#') { continue; }
    return text.slice(0, 60);
  }
  return '';
}

/* ------------------------------------------------------------ lyrics editor */
function lyricsStats(text) {
  var lines = String(text || '').split('\n');
  var words = String(text || '').trim() ? String(text).trim().split(/\s+/).length : 0;
  return { lines: lines.length, words: words, chars: String(text || '').length };
}

function updateLyricsCount() {
  var stats = lyricsStats($('lyrics-big').value);
  $('lyrics-count').textContent = stats.words + ' words \u00b7 ' + stats.lines + ' lines \u00b7 ' + stats.chars + ' characters';
}

/* The score gets the same full size editor as the lyrics, for long ABC. */
function updateScoreCount() {
  var text = $('score-big').value;
  var bars = text.split('\n').length;
  $('score-count').textContent = text.length + ' characters, ' + bars + ' lines';
}

/* Three ways to read the score: the chord chart, real staves, and the lyrics
   with each section's chords. The lyrics view stops at the section on purpose:
   measured words per melody note runs from 0.41 to 1.25 between sections, so a
   word-by-word alignment would drift. */
/* Undo for the score text. A global chord replace cannot be undone by the browser,
   because setting .value directly drops its own history. Kept per editing session and
   reset when a different score is loaded. Typing runs coalesce; a replace does not. */
var SCORE_HISTORY_LIMIT = 120;
var scoreStack = { items: [], index: -1, at: 0, applying: false };

function pushScoreHistory(text) {
  if (scoreStack.applying) { return; }
  var now = Date.now();
  var top = scoreStack.items[scoreStack.index];
  if (top === text) { return; }
  // Coalesce a typing run, but never the entry the editor opened on, and never
  // when there is a redo tail to cut off.
  var atTip = scoreStack.index === scoreStack.items.length - 1;
  var smallEdit = atTip && scoreStack.index > 0 && typeof top === 'string' &&
                  Math.abs(top.length - text.length) <= 3 && now - scoreStack.at < 900;
  if (smallEdit) {
    scoreStack.items[scoreStack.index] = text;
  } else {
    scoreStack.items = scoreStack.items.slice(0, scoreStack.index + 1);
    scoreStack.items.push(text);
    if (scoreStack.items.length > SCORE_HISTORY_LIMIT) { scoreStack.items.shift(); }
    scoreStack.index = scoreStack.items.length - 1;
  }
  scoreStack.at = now;
  paintScoreHistory();
}

function scoreReset(text) {
  scoreStack.items = [text];
  scoreStack.index = 0;
  scoreStack.at = Date.now();
  paintScoreHistory();
}

/* The tempo lives in the score, as Q:1/4=. This edits that line, which is what the
   render follows: YuE2 keeps the tempo its plan carries, within a couple of BPM. */
function scoreTempo() {
  var match = /^Q:1\/4=(\d+)/m.exec($('score-big').value || '');
  return match ? parseInt(match[1], 10) : null;
}

function paintScoreTempo() {
  var field = $('score-tempo');
  if (!field || document.activeElement === field) { return; }
  var bpm = scoreTempo();
  field.value = bpm === null ? '' : String(bpm);
  field.disabled = ($('score-big').value || '').length < 20;
}

function setScoreTempo(bpm) {
  var box = $('score-big');
  var text = box.value || '';
  if (!text.trim() || !bpm) { return; }
  var line = 'Q:1/4=' + bpm;
  if (/^Q:1\/4=\d+/m.test(text)) {
    box.value = text.replace(/^Q:1\/4=\d+.*$/m, line);
  } else {
    // A score with no tempo line: put one under the note length, where ABC wants it.
    var lines = text.split('\n');
    var at = lines.findIndex(function (l) { return /^L:/.test(l.trim()); });
    lines.splice(at >= 0 ? at + 1 : 1, 0, line);
    box.value = lines.join('\n');
  }
  syncScoreFromBig();
}

function paintScoreHistory() {
  var canUndo = scoreStack.index > 0;
  var canRedo = scoreStack.index < scoreStack.items.length - 1;
  if ($('score-undo')) { $('score-undo').disabled = !canUndo; }
  if ($('score-redo')) { $('score-redo').disabled = !canRedo; }
  if ($('roll-undo-btn')) { $('roll-undo-btn').disabled = !canUndo; }
  if ($('roll-redo-btn')) { $('roll-redo-btn').disabled = !canRedo; }
}

function applyScoreHistory() {
  var text = scoreStack.items[scoreStack.index];
  scoreStack.applying = true;
  $('abc').value = text;
  $('score-big').value = text;
  $('abc').dispatchEvent(new Event('input'));
  scoreStack.applying = false;
  scoreStack.at = Date.now();
  paintScoreHistory();
  if (scoreView() === 'roll' && window.PianoRoll) {
    window.PianoRoll.loadAbc(text || '');
  }
}

function undoScore() {
  if (scoreStack.index <= 0) { return; }
  scoreStack.index -= 1;
  applyScoreHistory();
}

function redoScore() {
  if (scoreStack.index >= scoreStack.items.length - 1) { return; }
  scoreStack.index += 1;
  applyScoreHistory();
}

var SCORE_VIEW_KEY = 'yue2.scoreview';

function scoreView() {
  return State.scoreView || 'chart';
}

function abcSections(abc) {
  var sections = [];
  var current = null;
  var voice = null;
  (abc || '').split('\n').forEach(function (raw) {
    var line = raw.trim();
    if (!line) { return; }
    if (line.charAt(0) === '%') {
      current = { name: line.replace(/^%\s*/, ''), bars: [] };
      sections.push(current);
      return;
    }
    var v = line.match(/^V:\s*(\S+)/);
    if (v) { voice = v[1]; return; }
    if (!current) { current = { name: 'song', bars: [] }; sections.push(current); }
    if (voice !== 'Vocal' && voice !== 'Ins') { return; }
    line.split('|').forEach(function (chunk) {
      if (!chunk.trim()) { return; }
      var chords = chunk.match(/"([^"]+)"/g);
      current.bars.push(chords ? chords.map(function (c) { return c.replace(/"/g, ''); }) : []);
    });
  });
  return sections;
}

function sectionChords(section) {
  var out = [];
  section.bars.forEach(function (bar) {
    bar.forEach(function (chord) {
      if (out[out.length - 1] !== chord) { out.push(chord); }
    });
  });
  return out;
}

/* --------------------------------------------------------------- hearing a plan
   The Notation tab draws the score with abcjs, whose vendored build carries a
   synthesiser as well: it fetches one small MP3 per note it needs from
   /soundfonts/, plays the score, and writes the same score out as a MIDI file.
   Nothing here goes near the engine: it is the ABC in the box, as you edited it. */
var NOTATION = { synth: null, tune: null, tuned: null, tunedChords: null, transpose: 0, notes: 0,
                 playable: false, hasScore: false, empty: true, text: '', marked: [], sounds: null, message: '',
                 busy: false, at: -1, shift: 0, lead: 0, inserts: [], choice: null, fetching: 0,
                 tunedRange: null, preparing: false };
// The note samples are one file per key of a piano, A0 to C8.
var PIANO_LOW = 21, PIANO_HIGH = 108;

/* ------------------------------------------------- what each voice plays with
   A score names no instruments: YuE2 writes a melody, a second line and chord symbols.
   The style the take was made with does name them, so the preview reads it and plays
   each voice with something that fits instead of a piano throughout.  First match wins,
   so the list runs from the most particular word to the most general.  The number is a
   General MIDI program and the id is the sample set of that name (app/soundfonts.py);
   the score, the staves and the box are untouched — this is how the preview sounds. */
var PREVIEW_PIANO = { id: 'acoustic_grand_piano', label: 'piano', program: 0, words: ['piano', 'keys', 'ballad'] };
var PREVIEW_INSTRUMENTS = [
  { id: 'distortion_guitar', label: 'distorted guitar', program: 30,
    words: ['distortion', 'distorted', 'heavy metal', 'hard rock', 'punk', 'grunge', 'metal'] },
  { id: 'overdriven_guitar', label: 'overdriven guitar', program: 29, words: ['overdriven', 'fuzz', 'garage'] },
  { id: 'acoustic_guitar_nylon', label: 'nylon guitar', program: 24,
    words: ['nylon', 'classical guitar', 'flamenco', 'spanish guitar'] },
  { id: 'acoustic_guitar_steel', label: 'steel guitar', program: 25,
    words: ['acoustic guitar', 'fingerpick', 'fingerpicking', 'strummed', 'unplugged', 'singer-songwriter'] },
  { id: 'banjo', label: 'banjo', program: 105, words: ['banjo', 'bluegrass'] },
  { id: 'violin', label: 'violin', program: 40, words: ['violin', 'fiddle'] },
  { id: 'cello', label: 'cello', program: 42, words: ['cello'] },
  { id: 'string_ensemble_1', label: 'strings', program: 48,
    words: ['string', 'orchestral', 'orchestra', 'chamber', 'cinematic', 'baroque'] },
  { id: 'brass_section', label: 'brass', program: 61,
    words: ['brass', 'trumpet', 'trombone', 'horn section', 'big band'] },
  { id: 'alto_sax', label: 'saxophone', program: 65, words: ['sax'] },
  { id: 'flute', label: 'flute', program: 73, words: ['flute', 'whistle', 'recorder'] },
  { id: 'marimba', label: 'marimba', program: 12, words: ['marimba', 'kalimba', 'mallet'] },
  { id: 'vibraphone', label: 'vibraphone', program: 11, words: ['vibraphone', 'glockenspiel', 'xylophone', 'bells'] },
  { id: 'drawbar_organ', label: 'organ', program: 16, words: ['organ', 'hammond', 'gospel', 'church'] },
  { id: 'electric_piano_1', label: 'electric piano', program: 4,
    words: ['rhodes', 'wurlitzer', 'electric piano', 'lo-fi', 'lofi', 'lo fi'] },
  { id: 'pad_2_warm', label: 'warm pad', program: 89, words: ['pad', 'ambient', 'atmospheric', 'shoegaze'] },
  { id: 'lead_2_sawtooth', label: 'synth lead', program: 81,
    words: ['synth', 'synthesizer', 'electronic', 'edm', 'dance', 'techno', 'house'] },
  { id: 'electric_guitar_clean', label: 'clean guitar', program: 27,
    words: ['electric guitar', 'jangly', 'jangle', 'twangy', 'guitar'] },
  PREVIEW_PIANO
];
// What plays the chord symbols, and their bass notes.
var PREVIEW_COMP = [
  { id: 'electric_piano_1', label: 'electric piano', program: 4,
    words: ['rhodes', 'electric piano', 'lo-fi', 'lofi', 'lo fi', 'soul'] },
  { id: 'drawbar_organ', label: 'organ', program: 16, words: ['organ', 'hammond', 'gospel', 'church'] },
  { id: 'pad_2_warm', label: 'warm pad', program: 89, words: ['synth', 'electronic', 'ambient', 'dream pop'] },
  // The strummed ones come before the electric: "acoustic guitar" has "guitar" in it,
  // and a folk or country song wants the steel, not a clean electric.
  { id: 'acoustic_guitar_steel', label: 'steel guitar', program: 25,
    words: ['acoustic guitar', 'folk', 'country', 'bluegrass', 'banjo', 'strummed', 'unplugged'] },
  { id: 'electric_guitar_clean', label: 'clean guitar', program: 27,
    words: ['indie', 'rock', 'jangle', 'punk', 'grunge', 'guitar'] }
];
var PREVIEW_BASS = [
  { id: 'slap_bass_1', label: 'slap bass', program: 36, words: ['slap', 'funk'] },
  { id: 'synth_bass_1', label: 'synth bass', program: 38,
    words: ['synth', 'electronic', 'edm', 'dance', 'techno', 'house', 'hip hop', 'hip-hop'] },
  { id: 'acoustic_bass', label: 'upright bass', program: 32, words: ['jazz', 'upright', 'double bass', 'swing'] },
  { id: 'electric_bass_pick', label: 'pick bass', program: 34, words: ['pick', 'punk', 'rock'] }
];
var PREVIEW_BASS_DEFAULT = { id: 'electric_bass_finger', label: 'finger bass', program: 33 };
/* The drums, when the style names them.  abcjs writes the part itself from one of
   these: a rhythm of hits and rests, then a pitch and a volume for each hit, scaled to
   fit a bar of the score's own metre.  C2 is a kick, D2 a snare, Gb2 a closed hi-hat,
   F#3 a ride — the usual general-MIDI drum numbers. */
var PREVIEW_DRUMS = [
  { id: 'club', label: 'drums',
    words: ['dance', 'house', 'techno', 'edm', 'disco', 'electronic', 'trance', 'club', 'synth-pop', 'synthpop'],
    rhythm: 'd2d2d2d2d2d2d2d2', pitches: [36, 42, 36, 42, 36, 42, 36, 42],
    volumes: [104, 50, 100, 50, 104, 50, 100, 50] },
  { id: 'jazz', label: 'drums', words: ['jazz', 'swing', 'bebop', 'big band', 'blues'],
    rhythm: 'd2d2d2d2d2d2d2d2', pitches: [51, 51, 38, 51, 51, 51, 38, 51],
    volumes: [70, 60, 90, 60, 70, 60, 90, 60] },
  { id: 'sparse', label: 'drums',
    words: ['ballad', 'gentle', 'slow', 'soft', 'acoustic', 'singer-songwriter', 'lullaby', 'ambient'],
    rhythm: 'd2z2d2z2d2z2d2z2', pitches: [36, 38, 36, 38],
    volumes: [80, 76, 80, 76] },
  { id: 'backbeat', label: 'drums', words: ['drum', 'percussion', 'breakbeat', 'shaker'],
    rhythm: 'd2d2d2d2d2d2d2d2', pitches: [36, 42, 38, 42, 36, 42, 38, 42],
    volumes: [100, 52, 104, 52, 100, 52, 104, 52] }
];
// Words that mean a kit or a drum machine is there.  A dance style rarely says "drums",
// and one that says "no drums" means it.
var PREVIEW_DRUM_WORDS = ['drum', 'percussion', 'breakbeat', 'beat', 'shaker', 'brushes', '808',
                          'house', 'techno', 'edm', 'dance', 'disco', 'trance', 'club',
                          'jazz', 'swing', 'bebop'];
var PREVIEW_NO_DRUMS = ['no drums', 'no percussion', 'without drums', 'drumless', 'no beat', 'unaccompanied'];

// A sung line wants a voice, and a style that asks for a choir gets one.
var PREVIEW_VOICE = { id: 'voice_oohs', label: 'voice', program: 53 };
var PREVIEW_CHOIR = { id: 'choir_aahs', label: 'choir', program: 52,
                      words: ['choir', 'choral', 'harmonies', 'backing vocals', 'vocal harmony'] };

function notationStyleText() { return (($('style') && $('style').value) || '').toLowerCase(); }

function notationMatch(list, style) {
  var found = null;
  list.some(function (item) {
    if (item.words.some(function (word) { return style.indexOf(word) >= 0; })) { found = item; return true; }
    return false;
  });
  return found;
}

/* Whether a voice has any notes in it — the Vocal voice of an instrumental is rests
   carrying the chords, and a stand-in for a singer would be wrong there. */
function notationVoiceHasNotes(text, name) {
  var inside = false;
  var lines = (text || '').split('\n');
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i].trim();
    var voice = /^V:\s*(\w+)/.exec(line);
    if (voice) { inside = voice[1] === name; continue; }
    if (!inside || /^[A-Za-z]:/.test(line) || line.charAt(0) === '%') { continue; }
    var bare = line.replace(/"[^"]*"/g, ' ');
    if (/[A-Ga-g]/.test(bare)) { return true; }
  }
  return false;
}

/* What the preview will play, or null to leave it the piano it always was.  Nothing is
   guessed from the audio: this reads the style the take was made with, which is the
   only thing here that names instruments. */
function notationChoice(text) {
  var box = $('notation-instruments');
  var style = notationStyleText();
  if ((box && !box.checked) || !style) { return null; }
  var lead = notationMatch(PREVIEW_INSTRUMENTS, style);
  var comp = notationMatch(PREVIEW_COMP, style);
  var bass = notationMatch(PREVIEW_BASS, style);
  var drum = null;
  var drumless = PREVIEW_NO_DRUMS.some(function (word) { return style.indexOf(word) >= 0; });
  if (!drumless && PREVIEW_DRUM_WORDS.some(function (word) { return style.indexOf(word) >= 0; })) {
    drum = notationMatch(PREVIEW_DRUMS, style) || PREVIEW_DRUMS[PREVIEW_DRUMS.length - 1];
  }
  // A style can name only the backing — a jazz trio is its bass and its drums, with the
  // piano understood.  So the melody falls back to a piano rather than giving up on all
  // of it; only a style that names nothing we can play is left alone.
  if (!lead && !comp && !bass && !drum) { return null; }
  if (!lead) { lead = PREVIEW_PIANO; }
  if (!comp) { comp = PREVIEW_PIANO; }
  if (!bass) { bass = PREVIEW_BASS_DEFAULT; }
  var choir = notationMatch([PREVIEW_CHOIR], style) || null;
  var sung = notationVoiceHasNotes(text || (($('score-big') && $('score-big').value) || ''), 'Vocal');
  var voice = sung ? (choir || PREVIEW_VOICE) : null;
  var chordsOn = !$('notation-chords') || $('notation-chords').checked;
  var words = [];
  if (voice) { words.push(voice.label); }
  words.push(lead.label);
  if (drum) { words.push(drum.label); }
  if (chordsOn) { words.push(comp.label, bass.label); }
  return { voice: voice ? voice.program : null, voiceId: voice ? voice.id : null, voiceLabel: voice ? voice.label : '',
           lead: lead.program, leadId: lead.id, leadLabel: lead.label,
           chord: chordsOn ? comp.program : null, chordId: chordsOn ? comp.id : null, chordLabel: comp.label,
           bass: chordsOn ? bass.program : null, bassId: chordsOn ? bass.id : null, bassLabel: bass.label,
           // abcjs writes the drum part from this: a rhythm, then a pitch and a volume
           // for each of its hits.
           drumId: drum ? 'percussion' : null, drumBars: 1,
           drumPattern: drum ? [drum.rhythm].concat(drum.pitches, drum.volumes).join(' ') : null,
           words: words.filter(function (w, i) { return words.indexOf(w) === i; }).join(', ') };
}

/* What the preview can make of a score: how many notes it holds, and how far it has to
   shift to fit the piano's 88 keys.  A plan can carry a note outside them — a runaway
   one does — and one missing sample stops the whole preview, so the tune is moved by
   whole octaves until it fits.  The score is untouched: this is how it sounds here.
   No notes at all is a different answer from notes nothing can reach.

   The instruments are not all the same size — a bass stops at Gb5 and a voice at Gb6 —
   so the range to fit comes from the sets this score will play through, and a set that
   is not here yet is taken as a piano's.  The chord track's bass part is left out of it:
   abcjs writes that low by itself, and a bass's narrow range would otherwise drag a
   whole song down an octave. */
function notationFitRange() {
  var low = PIANO_LOW, high = PIANO_HIGH;
  var choice = NOTATION.choice;
  var ranges = (NOTATION.sounds && NOTATION.sounds.ranges) || {};
  var ids = choice ? [choice.voiceId, choice.leadId, choice.chordId] : ['acoustic_grand_piano'];
  ids.forEach(function (id) {
    var range = id ? ranges[id] : null;
    if (range && range.length === 2) { low = Math.max(low, range[0]); high = Math.min(high, range[1]); }
  });
  return high >= low ? { low: low, high: high } : { low: PIANO_LOW, high: PIANO_HIGH };
}

function notationPlayable(chordsOff) {
  var fit = notationFitRange();
  var range = function (shift) {
    var flat = NOTATION.tune.setUpAudio({ chordsOff: chordsOff, midiTranspose: shift });
    var lo = 999, hi = -1, count = 0, inRange = 0;
    flat.tracks.forEach(function (track) {
      track.forEach(function (note) {
        if (typeof note.pitch !== 'number') { return; }
        count += 1;
        lo = Math.min(lo, note.pitch);
        hi = Math.max(hi, note.pitch);
        if (note.pitch >= fit.low && note.pitch <= fit.high) {
          inRange += 1;
        }
      });
    });
    return { notes: count, lo: lo, hi: hi, inRange: inRange };
  };
  var plain = range(0);
  if (!plain.notes) { return { notes: 0, shift: 0, fits: false, partial: false }; }
  var bestShift = 0;
  var bestInRange = -1;
  var exactFit = false;
  var shifts = [0, -12, 12, -24, 24, -36, 36];
  for (var i = 0; i < shifts.length; i++) {
    var cand = shifts[i];
    var found = range(cand);
    if (found.lo >= fit.low && found.hi <= fit.high) {
      bestShift = cand;
      bestInRange = found.inRange;
      exactFit = true;
      break;
    }
    if (found.inRange > bestInRange) {
      bestInRange = found.inRange;
      bestShift = cand;
    }
  }
  return {
    notes: plain.notes,
    shift: bestShift,
    fits: true,
    partial: !exactFit
  };
}

/* The score as it is drawn, and where the lines the preview added went in.  It is drawn
   as it is written: filtering the header out lost the per-voice M: lines a plan uses for
   a change of metre.  Only an empty T: is filled, and each voice is told what to play;
   both are recorded, so a click on a note still finds its place in the box. */
function notationAbc() {
  var raw = ($('score-big') && $('score-big').value) || '';
  var lead = raw.length - raw.replace(/^\s+/, '').length;
  var title = (($('title') && $('title').value) || '').trim() || 'Score';
  var lines = raw.slice(lead).split('\n');
  var choice = notationChoice(raw);
  NOTATION.choice = choice;      // what the sounds and the hand-over read after this
  var out = [], inserts = [], at = -1, shift = 0, pos = 0, chars = 0, inBody = false, given = {};
  var hasTitle = lines.some(function (line) { return /^T:/.test(line); });
  function emit(line, injected) {
    // the line and the newline it brought, which is what the offsets have to take off
    if (injected) { inserts.push({ at: chars, len: line.length + 1 }); }
    out.push(line);
    chars += line.length + 1;
  }
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];
    var trimmed = line.trim();
    if (!hasTitle && (i === 0 || /^X:/.test(trimmed))) {
      // No title line at all: abcjs would call the tune Untitled.  It goes after X:.
      emit(line, false);
      pos += line.length + 1;
      at = pos;
      shift = ('T: ' + title + '\n').length;
      emit('T: ' + title, true);
      continue;
    }
    if (/^T:/.test(trimmed) && !line.slice(2).trim()) {
      var filled = 'T: ' + title;
      at = pos;
      shift = filled.length - line.length;
      line = filled;
    }
    if (/^K:/.test(trimmed)) {
      if (choice && choice.chord !== null) { emit('%%MIDI chordprog ' + choice.chord, true); }
      if (choice && choice.bass !== null) { emit('%%MIDI bassprog ' + choice.bass, true); }
      inBody = true;
    }
    emit(line, false);
    var voice = /^V:\s*(\w+)/.exec(trimmed);
    if (inBody && voice && choice && !given[voice[1]]) {
      var program = voice[1] === 'Vocal' ? choice.voice : choice.lead;
      if (program !== null && program !== undefined) { given[voice[1]] = true; emit('%%MIDI program ' + program, true); }
    }
    pos += lines[i].length + 1;
  }
  return { text: out.join('\n'), at: at, shift: shift, lead: lead, inserts: inserts };
}

/* Where a character in what is drawn came from in the box: the preview's own lines come
   back off, then the title that was filled in, then the blank space the drawing skipped. */
function notationSourceIndex(index) {
  var removed = 0;
  (NOTATION.inserts || []).forEach(function (ins) { if (ins.at < index) { removed += ins.len; } });
  var trimmed = index - removed - NOTATION.lead;
  if (NOTATION.at >= 0 && trimmed >= NOTATION.at) { trimmed -= NOTATION.shift; }
  return Math.max(0, trimmed + NOTATION.lead);
}

/* Clicking a note puts the cursor on the ABC it came from. */
function notationPickNote(abcelem) {
  var box = $('score-big');
  if (!box || !abcelem || typeof abcelem.startChar !== 'number' || typeof abcelem.endChar !== 'number') { return; }
  var start = notationSourceIndex(abcelem.startChar);
  var end = Math.max(start, notationSourceIndex(abcelem.endChar));
  try {
    box.focus();
    box.setSelectionRange(start, end);
  } catch (err) { /* a hidden box cannot take a selection */ }
}

function notationUnmark() {
  NOTATION.marked.forEach(function (el) { if (el && el.classList) { el.classList.remove('notation-playing'); } });
  NOTATION.marked = [];
}

function notationMark(event) {
  if (!event || !event.elements) { return; }
  notationUnmark();
  event.elements.forEach(function (group) {
    Array.prototype.forEach.call(group || [], function (el) {
      if (el && el.classList) { el.classList.add('notation-playing'); NOTATION.marked.push(el); }
    });
  });
}

var NOTATION_CURSOR = {
  // The first moment there is sound: until this fires the page is preparing the song.
  onStart: function () {
    NOTATION.preparing = false;
    notationPaintNote();
    // Two transports over one pair of speakers is unusable: the player stops.
    var main = $('audio');
    if (main && !main.paused) { main.pause(); }
  },
  onEvent: notationMark,
  onFinished: function () { NOTATION.preparing = false; notationUnmark(); notationPaintNote(); }
};

function notationNote(text) { NOTATION.message = text || ''; notationPaintNote(); }

/* The sample sets this score is about to use: what the style chose, or the piano when it
   chose nothing.  A set is fetched whole or not at all, so readiness is per instrument. */
function notationNeeded() {
  var choice = NOTATION.choice;
  var ids = choice ? [choice.voiceId, choice.leadId, choice.chordId, choice.bassId, choice.drumId]
                   : ['acoustic_grand_piano'];
  ids = ids.filter(function (id) { return Boolean(id); });
  return ids.filter(function (id, i) { return ids.indexOf(id) === i; });
}

function notationMissing() {
  var have = (NOTATION.sounds && NOTATION.sounds.installed) || [];
  return notationNeeded().filter(function (id) { return have.indexOf(id) < 0; });
}

function notationSoundSize(count) {
  var each = (NOTATION.sounds && NOTATION.sounds.megabytes) || 7;
  return each * (count === undefined ? notationMissing().length : count);
}

function notationSoundsReady() { return Boolean(NOTATION.sounds) && notationMissing().length === 0; }

function notationTransposeWords(shift) {
  var octaves = Math.abs(shift) / 12;
  var how = octaves === 1 ? 'an octave' : octaves + ' octaves';
  return 'Played ' + how + (shift < 0 ? ' lower' : ' higher') + ', to fit what these instruments can play.';
}

/* What the line beside the player says.  Everything here is worked out from the state
   as it is now: a message kept from an earlier look at the score would outlive it, and
   the line would go on saying a score has no notes while it plays.  NOTATION.message
   holds a failure only — a fetch that did not work, a file that would not write. */
function notationPaintNote() {
  var note = $('notation-note');
  if (!note) { return; }
  if (NOTATION.message) { note.textContent = NOTATION.message; return; }
  if (NOTATION.busy) {
    var many = notationMissing().length;
    note.textContent = many > 1
      ? 'Getting the note samples (' + NOTATION.fetching + ' of ' + many + ')…'
      : 'Getting the note samples…';
    return;
  }
  // Building the song for the first time takes a moment — a whole score is prepared as one
  // buffer before any of it sounds — and a control that looks dead while that happens reads
  // as broken.
  if (NOTATION.preparing) { note.textContent = 'Getting the preview ready…'; return; }
  if (NOTATION.empty) { note.textContent = ''; return; }        // the staves say "No score yet."
  if (!NOTATION.hasScore) { note.textContent = 'This score has no notes in it yet.'; return; }
  if (NOTATION.playable && NOTATION.partial) {
    note.textContent = 'Some notes exceed browser piano range. Use Studio Audio (SF2) for complete orchestral playback.';
    return;
  }
  if (!NOTATION.playable) {
    note.textContent = 'Some notes exceed browser piano range. Use Studio Audio (SF2) for complete orchestral playback.';
    return;
  }
  if (!notationSoundsReady()) {
    var short = notationMissing().length;
    note.textContent = 'Play, or Get the sounds, fetches ' +
      (short === 1 ? 'one instrument' : short + ' instruments') + ' once — about ' +
      notationSoundSize(short) + ' MB — and it works offline afterwards.';
    return;
  }
  var said = [];
  if (NOTATION.choice) { said.push('Played as ' + NOTATION.choice.words + ', from the style.'); }
  if (NOTATION.transpose) { said.push(notationTransposeWords(NOTATION.transpose)); }
  note.textContent = said.join(' ');
}

function notationPaintBar() {
  var ready = notationSoundsReady();
  var button = $('notation-sounds');
  if (button) {
    button.textContent = NOTATION.busy ? 'Getting the sounds…'
      : 'Get the sounds (' + notationSoundSize() + ' MB)';
    button.classList.toggle('hidden', ready);
    button.disabled = NOTATION.busy;
  }
  // The transport stays on screen from the first look: hiding it until the samples
  // arrive reads as controls that are missing rather than one step still to take.
  var widget = $('notation-audio');
  if (widget) { widget.classList.toggle('hidden', !NOTATION.hasScore); }
  notationPaintNote();
}

async function notationSoundsState() {
  try { NOTATION.sounds = await api('/api/soundfonts'); }
  catch (err) { NOTATION.sounds = null; }
  // The answer decides whether the controls are live and what can be played at all, so
  // the score is handed over first and the bar painted from what that settled.
  notationSetTune();
  notationPaintBar();
  return NOTATION.sounds;
}

async function notationGetSounds(thenPlay, thenAt) {
  if (NOTATION.busy) { return; }
  var missing = notationMissing();
  if (!missing.length) {
    if (thenPlay) { notationResume(thenAt || 0, true); }
    return;
  }
  NOTATION.busy = true;
  NOTATION.fetching = 0;
  notationNote('');
  notationPaintBar();
  try {
    for (var i = 0; i < missing.length; i++) {
      NOTATION.fetching = i + 1;
      notationPaintBar();
      await api('/api/soundfonts/' + encodeURIComponent(missing[i]) + '/download', { method: 'POST' });
    }
    NOTATION.message = '';      // whatever went wrong before, it is here now
    await notationSoundsState();
    notationSetTune();          // they are here now: hand the score over
    if (thenPlay) { notationResume(thenAt || 0, true); }
  } catch (err) {
    notationNote('Could not fetch the sounds: ' + err.message);
  } finally {
    NOTATION.busy = false;
    notationPaintBar();
  }
}

/* Carry on from where the preview was.  Handing the score over stops it — that is how
   abcjs changes a tune — so playing resumes, and the place in the song comes back with
   it; one that was paused keeps its place instead. */
function notationResume(at, playing) {
  var synth = NOTATION.synth;
  if (!synth || !NOTATION.playable) { return; }
  if (playing) {
    NOTATION.preparing = true;
    notationPaintNote();
    var started = synth.play();
    if (started && typeof started.then === 'function') {
      started.then(function () { if (at) { synth.seek(at); } });
    }
  } else if (at) {
    synth.setProgress(at, 1);
    synth.seek(at);
  }
}

/* A tick-box changed: look at the score again, for the lines it plays and the samples
   it needs, and let it carry on rather than fall silent under the pointer. */
function notationRepaint() {
  var synth = NOTATION.synth;
  var playing = Boolean(synth && synth.isStarted);
  var at = synth ? (synth.percent || 0) : 0;
  renderNotationView();
  notationPaintBar();
  if (!playing && !at) { return; }
  if (!notationSoundsReady()) { notationGetSounds(playing, at); return; }
  notationResume(at, playing);
}

/* The score as a MIDI file: the two written voices, and, unless Chords is unticked,
   the part abcjs writes from the chord symbols, which is the only way the harmony
   reaches a DAW as notes. */
function notationMidiBytes(abc) {
  var options = notationPlayOptions();
  // The octave shift is only there to fit the sample sets: a DAW has no such limit, so
  // the file is written as the score stands.
  delete options.midiTranspose;
  delete options.soundFontUrl;
  // The file is written from the sequence that plays the preview (midiwrite.js), because abcjs's
  // own file writer garbles the drums and puts every instrument change on channel 1. A page
  // loaded before that script existed has no writer, and falls back to abcjs's.
  if (typeof writeMidi === 'function') {
    try {
      var tune = ABCJS.renderAbc('*', abc, {})[0];
      var meter = tune && tune.getMeterFraction ? tune.getMeterFraction() : null;
      var made = writeMidi(tune.setUpAudio(options), {
        meter: meter ? { num: meter.num, den: meter.den } : null,
        title: (($('title') && $('title').value) || '').trim()
      });
      if (made && made.length) { return made; }
    } catch (err) { /* fall through to abcjs's own writer */ }
  }
  options.midiOutputType = 'binary';
  var result = ABCJS.synth.getMidiFile(abc, options);
  var first = Array.isArray(result) ? result[0] : result;      // abcjs hands back [Uint8Array]
  if (first instanceof Uint8Array) { return first; }
  if (typeof first === 'string') { return new Uint8Array(first.split(',').map(Number)); }
  if (Array.isArray(first)) { return new Uint8Array(first); }
  if (first && first.data) { return new Uint8Array(first.data); }
  return null;
}

function notationDownloadMidi() {
  if (typeof ABCJS === 'undefined' || !ABCJS.synth || !ABCJS.synth.getMidiFile) { return; }
  var score = notationAbc();
  if (!score.text.trim()) { notationNote('There is no score to save yet.'); return; }
  var bytes = null;
  try { bytes = notationMidiBytes(score.text); } catch (err) { bytes = null; }
  if (!bytes || !bytes.length) { notationNote('This score could not be written as MIDI.'); return; }
  var name = (($('title') && $('title').value) || 'score').trim().toLowerCase()
    .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'score';
  var url = URL.createObjectURL(new Blob([bytes], { type: 'audio/midi' }));
  var link = document.createElement('a');
  link.href = url;
  link.download = name + '.mid';
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
}

async function initScoreSf2Select() {
  var sel = $('score-sf2-select');
  if (!sel) return;
  try {
    var data = await api('/api/soundfonts/sf2');
    sel.innerHTML = '';
    if (!data.soundfonts || data.soundfonts.length === 0) {
      var opt = document.createElement('option');
      opt.value = '';
      opt.textContent = '(No .sf2 SoundFonts installed)';
      sel.appendChild(opt);
      sel.disabled = true;
      var hint = 'Place .sf2 files in data/models/soundfonts/sf2 to enable studio rendering';
      if ($('score-render-sf2')) $('score-render-sf2').title = hint;
      if ($('notation-render-sf2')) $('notation-render-sf2').title = hint;
      return;
    }
    sel.disabled = false;
    data.soundfonts.forEach(function (sf) {
      var opt = document.createElement('option');
      opt.value = sf.filename;
      opt.textContent = sf.name + ' (' + sf.size_mb + 'MB)';
      if (sf.filename === data.selected) {
        opt.selected = true;
      }
      sel.appendChild(opt);
    });
    sel.onchange = function () {
      api('/api/soundfonts/sf2/select', {
        method: 'POST',
        body: JSON.stringify({ filename: sel.value })
      }).then(function () {
        var opt = sel.selectedOptions && sel.selectedOptions[0];
        statusLine('Active SoundFont set to ' + (opt ? opt.textContent : sel.value), 'ok');
      }).catch(function (err) {
        statusLine('Could not select SoundFont: ' + err.message, 'bad');
      });
    };
  } catch (err) {
    sel.innerHTML = '<option value="">(SoundFonts unavailable)</option>';
    sel.disabled = true;
  }
}

function studioScoreAbc() {
  var score = notationAbc();
  return (window.PianoRoll && scoreView() === 'roll')
    ? (window.PianoRoll.model ? window.serializeToAbc(window.PianoRoll.model) : '')
    : (score.text || ($('score-big') && $('score-big').value) || '');
}

async function renderScoreSf2() {
  // The button is a switch: pressed again, it puts the score back on the ordinary preview.
  if (STUDIO.mode) { studioModeOff(); return; }
  var abc = studioScoreAbc();

  if (!abc.trim()) {
    notationNote('There is no score to render yet.');
    return;
  }

  var sel = $('score-sf2-select');
  var chosenSf2 = sel && sel.value ? sel.value : null;

  // The same score with the same SoundFont is already rendered: play that.
  var held = $('audio');
  if (STUDIO.url && STUDIO.abc === abc && STUDIO.sf2 === chosenSf2 && held &&
      (held.src || held.currentSrc || '').indexOf(STUDIO.url) >= 0) {
    if (window.PianoRoll && window.PianoRoll.isPlaying) { window.PianoRoll.stop(); }
    notationStop();
    STUDIO.mode = true;
    held.currentTime = 0;
    held.play().catch(function () {});
    paintRollStudio();
    return;
  }

  var btns = [$('score-render-sf2'), $('notation-render-sf2')].filter(Boolean);
  btns.forEach(function (b) { b.disabled = true; b.textContent = 'Rendering...'; });

  try {
    var bytes = null;
    try { bytes = notationMidiBytes(abc); } catch (e) { bytes = null; }
    if (!bytes || !bytes.length) {
      notationNote('Could not convert score to MIDI.');
      return;
    }

    var binary = '';
    var len = bytes.byteLength;
    for (var i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    var b64 = window.btoa(binary);

    var res = await api('/api/score/render-sf2', {
      method: 'POST',
      body: JSON.stringify({ midi_base64: b64, sf2: chosenSf2 || undefined })
    });

    if (res.status === 'unavailable') {
      notationNote(res.detail || 'No SoundFonts installed. Place .sf2 files in data/models/soundfonts/sf2.');
      return;
    }

    if (res.status === 'ok' && res.audio_url) {
      var audio = $('audio');
      if (audio) {
        if (window.PianoRoll && window.PianoRoll.isPlaying) { window.PianoRoll.stop(); }
        notationStop();
        State.audition = null;
        State.loadedId = null;
        audio.src = res.audio_url;
        STUDIO.url = res.audio_url;
        STUDIO.abc = abc;
        STUDIO.sf2 = chosenSf2;
        STUDIO.mode = true;
        audio.play().catch(function () {});
        var sfLabel = res.soundfont ? res.soundfont.replace(/_/g, ' ').replace(/\.sf2$/i, '') : 'SoundFont';
        $('np-title').textContent = ($('title') && $('title').value) || 'Score';
        $('np-meta').textContent = 'Score (Studio Audio: ' + sfLabel + ')';
        $('np-cover').className = 'np-cover grad-cover';
        if (res.peaks_url) {
          loadWave(res.audio_url, res.peaks_url);
        }
        notationNote('Playing studio audio rendered with ' + sfLabel);
      }
    }
  } catch (err) {
    notationNote('Render failed: ' + (err.message || err));
  } finally {
    btns.forEach(function (b) {
      b.disabled = false;
      if (b.id === 'score-render-sf2') b.textContent = 'Studio Audio';
      else b.textContent = 'Studio Audio (SF2)';
    });
    paintRollStudio();
  }
}
window.renderScoreSf2 = renderScoreSf2;

/* Only one thing plays at a time.  Studio Audio runs through the main player, the roll and
   the notation preview each have a transport of their own, and starting any of them stops the
   others.  Studio Audio is a mode: while it is on its button is lit, and the roll's Play, Pause
   and seek controls act on the studio audio instead of the roll's own sounds. */
var STUDIO = { url: null, abc: null, sf2: null, mode: false };

function studioAudioPlaying() {
  var audio = $('audio');
  return !!(STUDIO.url && audio && !audio.paused && (audio.src || audio.currentSrc || '').indexOf(STUDIO.url) >= 0);
}

function paintStudioButtons() {
  ['score-render-sf2', 'notation-render-sf2'].forEach(function (id) {
    var el = $(id);
    if (!el) { return; }
    el.classList.toggle('active', STUDIO.mode);
    el.title = STUDIO.mode ? 'Studio audio is on. Press to go back to the ordinary preview'
                          : 'Render score with SoundFont via FluidSynth';
  });
  // The roll's own instrument is not what is heard while the studio audio plays.
  var sound = $('roll-sound-val');
  if (sound) {
    sound.disabled = STUDIO.mode;
    sound.title = STUDIO.mode ? 'Not used while studio audio is on' : 'Interactive piano roll preview instrument';
  }
}

function paintRollStudio() {
  var audio = $('audio');
  if (STUDIO.mode && !(STUDIO.url && audio && (audio.src || audio.currentSrc || '').indexOf(STUDIO.url) >= 0)) {
    STUDIO.mode = false;       // something else has taken the main player
  }
  if (window.PianoRoll && window.PianoRoll.followAudio) {
    // The roll's cursor follows the studio audio while it plays, and lets go when it stops.
    if (studioAudioPlaying()) { window.PianoRoll.followAudio(audio); }
    else { window.PianoRoll.stopFollowing(); }
  }
  paintStudioButtons();
  var btn = $('roll-play');
  if (!btn) { return; }
  if (STUDIO.mode) {
    var playing = studioAudioPlaying();
    btn.dataset.studio = '1';
    btn.textContent = playing ? '\u23f8 Pause' : '\u25b6 Play';
    btn.title = playing ? 'Pause the studio audio (Space)' : 'Play the studio audio (Space)';
  } else if (btn.dataset.studio === '1') {
    delete btn.dataset.studio;
    var rolling = window.PianoRoll && window.PianoRoll.isPlaying;
    btn.textContent = rolling ? '\u23f8 Pause' : '\u25b6 Play';
    btn.title = rolling ? 'Pause (Space)' : 'Play (Space)';
  }
}

function studioModeOff() {
  var audio = $('audio');
  STUDIO.mode = false;
  if (audio && !audio.paused && (audio.src || audio.currentSrc || '').indexOf(STUDIO.url || '\u0000') >= 0) { audio.pause(); }
  paintRollStudio();
}

window.studioAudio = {
  playing: studioAudioPlaying,
  mode: function () { return STUDIO.mode; },
  stop: studioModeOff,
  // The roll's Play button while the mode is on: pause or resume the studio audio.  False
  // when the mode is off, or the score has been edited since the render, and the roll plays.
  toggle: function () {
    if (!STUDIO.mode) { return false; }
    var audio = $('audio');
    if (!audio) { return false; }
    if (STUDIO.abc !== studioScoreAbc()) {
      studioModeOff();
      notationNote('The score has changed since the studio render, so this is the ordinary preview.');
      return false;
    }
    if (studioAudioPlaying()) {
      audio.pause();
    } else {
      if (window.PianoRoll && window.PianoRoll.isPlaying) { window.PianoRoll.stop(); }
      notationStop();
      audio.play().catch(function () {});
    }
    return true;
  },
  // The roll's seek controls move the studio audio too.
  seekTick: function (tick) {
    var model = window.PianoRoll && window.PianoRoll.model;
    var audio = $('audio');
    if (!STUDIO.mode || !model || !audio) { return false; }
    var perBeat = Math.max(1, Math.round((model.unitLength || 16) / 4));
    audio.currentTime = Math.max(0, tick * (60 / (model.bpm || 120)) / perBeat);
    return true;
  },
  // Called by whatever is about to play: the main player and the notation preview give way.
  takeOver: function () {
    var audio = $('audio');
    if (audio && !audio.paused) { audio.pause(); }
    notationStop();
    paintRollStudio();
  }
};

function notationInit() {
  if (NOTATION.synth) { return NOTATION.synth; }
  if (typeof ABCJS === 'undefined' || !ABCJS.synth || !ABCJS.synth.SynthController || !$('notation-audio')) { return null; }
  NOTATION.synth = new ABCJS.synth.SynthController();
  NOTATION.synth.load('#notation-audio', NOTATION_CURSOR, {
    displayPlay: true, displayProgress: true, displayWarp: true, displayRestart: true, displayLoop: false
  });
  // abcjs's own words for these are not the app's: say what they do, in its voice.
  var words = { '.abcjs-midi-start': 'Play the score, or pause it',
                '.abcjs-midi-reset': 'Back to the beginning',
                '.abcjs-midi-progress-background': 'Click or drag to move through the score',
                '.abcjs-midi-tempo': 'Speed of this preview only: the score keeps its own tempo' };
  Object.keys(words).forEach(function (selector) {
    var el = document.querySelector('#notation-audio ' + selector);
    if (el) { el.title = words[selector]; el.setAttribute('aria-label', words[selector]); }
  });
  // abcjs would run its own play and fail on samples that are not there yet, so the
  // first press fetches them and then starts: the transport is never a dead control.
  var holder = $('notation-audio');
  if (holder) {
    holder.addEventListener('click', function (event) {
      if (NOTATION.synth && !NOTATION.synth.isStarted) {
        if (window.PianoRoll && window.PianoRoll.isPlaying) { window.PianoRoll.stop(); }
        studioModeOff();
      }
      if (notationSoundsReady()) {
        // Let abcjs handle it, but say what is happening until sound starts.
        if (!NOTATION.synth.isStarted && !NOTATION.preparing) { NOTATION.preparing = true; notationPaintNote(); }
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      notationGetSounds(true);
    }, true);
  }
  var midi = $('notation-midi');
  if (midi) { midi.addEventListener('click', notationDownloadMidi); }
  var notSf2 = $('notation-render-sf2');
  if (notSf2) { notSf2.addEventListener('click', renderScoreSf2); }
  var sounds = $('notation-sounds');
  if (sounds) { sounds.addEventListener('click', function () { notationGetSounds(true, 0); }); }
  var chords = $('notation-chords');
  var instruments = $('notation-instruments');
  // Both of these change what plays, and which samples it needs, without stopping it.
  if (chords) { chords.addEventListener('change', notationRepaint); }
  if (instruments) { instruments.addEventListener('change', notationRepaint); }
  notationSoundsState();
  return NOTATION.synth;
}

/* What the preview plays with, as abcjs options: the same set feeds the synthesiser and
   the MIDI file, so what is heard is what is exported.  The chord part, its bass notes
   and the drums are abcjs's own writing rather than lines in the score, and this is how
   it is told about them. */
function notationPlayOptions() {
  var chords = $('notation-chords');
  var choice = NOTATION.choice;
  var options = {
    soundFontUrl: '/soundfonts/',
    chordsOff: chords ? !chords.checked : false,
    program: 0,
    midiTranspose: NOTATION.transpose
  };
  if (choice) {
    if (choice.chord !== null) { options.chordprog = choice.chord; }
    if (choice.bass !== null) { options.bassprog = choice.bass; }
    if (choice.drumPattern) { options.drum = choice.drumPattern; options.drumBars = choice.drumBars; }
  }
  return options;
}

/* Hand the drawn score to the synthesiser.  What the score can do is worked out whatever
   state the samples are in — that answer decides whether the transport is on screen at all —
   and only the hand-over itself waits for them, so Play cannot fail quietly on a 404. */
function notationSetTune() {
  if (!NOTATION.synth || !NOTATION.tune) { return; }
  var chords = $('notation-chords');
  // A score other than the one handed over last: abcjs keeps both the buffer it primed
  // and the flags that say the tune is ready, and setTune resets neither, so Play would
  // sound the take before this one.  Clearing the flag primes this tune on the next
  // Play; setTune has already stopped whatever was playing, and the marks the cursor
  // left on the drawing that has just gone are cleared here.
  var chordsOff = chords ? !chords.checked : false;
  var rangeKey = JSON.stringify(notationFitRange());
  if (NOTATION.tuned !== NOTATION.tune || NOTATION.tunedChords !== chordsOff || NOTATION.tunedRange !== rangeKey) {
    NOTATION.synth.isLoaded = false;
    notationUnmark();
    NOTATION.tuned = NOTATION.tune;
    NOTATION.tunedChords = chordsOff;
    NOTATION.tunedRange = rangeKey;
    var playable = notationPlayable(chordsOff);
    NOTATION.notes = playable.notes;
    NOTATION.transpose = playable.shift;
    NOTATION.playable = playable.fits;
    NOTATION.partial = playable.partial;
    NOTATION.hasScore = playable.notes > 0;
  }
  if (!NOTATION.hasScore) {
    // Nothing in the score. What the line says about it is worked out
    // in notationPaintNote from the state as it stands, not kept from an earlier look.
    NOTATION.synth.disable(true);
    notationPaintNote();
    return;
  }
  if (!notationSoundsReady()) {
    // One fetch away rather than a fault: the transport stays as it is, and pressing Play
    // fetches the samples and starts (see the click interceptor in notationInit).
    NOTATION.synth.disable(false);
    notationPaintNote();
    return;
  }
  NOTATION.synth.disable(false);
  NOTATION.synth.setTune(NOTATION.tune, false, notationPlayOptions());
  notationPaintNote();
}

/* Stop the preview.  abcjs has no stop of its own: handing the same score over again
   pauses it, rewinds it and clears the flag its play button toggles — which pausing
   alone leaves set, so the next click would only pause it again. */
function notationStop() {
  var synth = NOTATION.synth;
  if (synth && synth.isStarted) { notationSetTune(); }
  notationUnmark();
}

function renderNotationView() {
  var host = $('notation-big');
  if (!host) { return; }
  var box = (($('score-big') && $('score-big').value) || '').trim();
  var score = notationAbc();
  var abc = score.text.trim();
  if (!box || !abc || typeof ABCJS === 'undefined') {
    host.innerHTML = '<p class="hint">No score yet.</p>';
    // Nothing to hand over, and nothing to leave behind from the last one either.
    NOTATION.tune = null;
    NOTATION.tuned = null;
    NOTATION.hasScore = false;
    NOTATION.playable = false;
    NOTATION.empty = true;
    NOTATION.message = '';
    notationUnmark();
    if (NOTATION.synth) { NOTATION.synth.disable(true); }
    notationPaintBar();
    return;
  }
  // A score other than the one looked at last: a failure kept from that one is not this
  // one's, and the line is worked out again from what is here now.
  if (NOTATION.text !== abc) { NOTATION.message = ''; }
  NOTATION.empty = false;
  NOTATION.at = score.at;
  NOTATION.shift = score.shift;
  NOTATION.lead = score.lead;
  NOTATION.inserts = score.inserts || [];
  var drawn = null;
  try {
    // No responsive mode: abcjs then positions the SVG in the flow, so it scrolls
    // inside its pane instead of painting over the editor.
    drawn = ABCJS.renderAbc('notation-big', abc, {
      scale: 1.15, staffwidth: 980,
      foregroundColor: themeColour('--text') || '#f4f4f7', staffColor: themeColour('--muted') || '#9b9ba8',
      clickListener: notationPickNote
    });
  } catch (err) {
    host.innerHTML = '<p class="hint">This score will not render as notation.</p>';
    return;
  }
  NOTATION.tune = drawn && drawn[0] ? drawn[0] : null;
  NOTATION.text = abc;
  NOTATION.hasScore = Boolean(NOTATION.tune);
  notationInit();
  notationSetTune();
  notationPaintBar();
}

/* An instrumental's third view: each section of the plan with its chords.  The
   lyrics box is hidden in this mode and may hold another take's words. */
function renderSectionsView() {
  var sections = abcSections($('score-big').value || '');
  $('score-view-note').textContent = 'Sections as the plan names them, with the chords of their bars.';
  $('lyrics-view').innerHTML = sections.length ? sections.map(function (section) {
    var chords = sectionChords(section);
    return '<div class="lyric-section"><span class="lyric-head">' + esc(section.name) + '</span>' +
      (chords.length ? '<span class="lyric-chords">' + esc(chords.join('  ')) + '</span>' : '') + '</div>';
  }).join('') : '<p class="hint">No sections in this score yet.</p>';
}

function renderLyricsView() {
  if (State.mode === 'inst') { renderSectionsView(); return; }
  var host = $('lyrics-view');
  var lyrics = ($('lyrics-big').value || $('lyrics').value || '').trim();
  if (!lyrics) {
    host.innerHTML = '<p class="hint">No lyrics yet.</p>';
    return;
  }
  var sections = abcSections($('score-big').value || '');
  var out = [];
  var current = null;
  lyrics.split('\n').forEach(function (raw) {
    var line = raw.trim();
    if (!line) { return; }
    var tag = line.match(/^\[(.+)\]$/);
    if (tag) {
      current = tag[1];
      var key = current.toLowerCase().replace(/\s*\d+$/, '');
      var match = null;
      for (var i = 0; i < sections.length; i++) {
        var name = sections[i].name.toLowerCase();
        if (name === key || name === current.toLowerCase()) { match = sections[i]; }
      }
      var chords = match ? sectionChords(match) : [];
      out.push('<div class="lyric-section"><span class="lyric-head">' + esc(current) + '</span>' +
        (chords.length ? '<span class="lyric-chords">' + esc(chords.join('  ')) + '</span>' : '') + '</div>');
      return;
    }
    out.push('<div class="lyric-line">' + esc(line) + '</div>');
  });
  $('score-view-note').textContent =
    'Chords are per section, from the bars of that section. The model does not place words on notes, so no word level alignment is claimed.';
  host.innerHTML = out.join('');
}

function paintScoreView() {
  var view = scoreView();
  $('score-views').querySelector('[data-view="lyrics"]').textContent = State.mode === 'inst' ? 'Sections' : 'Lyrics';
  Array.prototype.forEach.call(document.querySelectorAll('#score-views .chip'), function (chip) {
    chip.classList.toggle('active', chip.dataset.view === view);
  });
  ['chart', 'notation', 'roll', 'lyrics'].forEach(function (name) {
    var box = $('view-' + name);
    if (box) { box.classList.toggle('hidden', name !== view); }
  });
  var scoreModalBox = $('score-modal') ? $('score-modal').querySelector('.modal-box.score') : null;
  if (scoreModalBox) {
    scoreModalBox.classList.toggle('roll-active', view === 'roll');
  }
  if (view === 'chart') {
    notationStop();          // nothing on screen would stop it
    if (window.PianoRoll) { window.PianoRoll.stop(); }
    $('chart-big').textContent = chordChart($('score-big').value || '') || '';
    $('score-view-note').textContent = '';
  } else if (view === 'notation') {
    if (window.PianoRoll) { window.PianoRoll.stop(); }
    $('score-view-note').textContent = '';
    renderNotationView();
  } else if (view === 'roll') {
    notationStop();
    $('score-view-note').textContent = '';
    if (window.PianoRoll) {
      window.PianoRoll.render($('score-big').value || $('abc').value || '');
    }
  } else {
    notationStop();
    if (window.PianoRoll) { window.PianoRoll.stop(); }
    renderLyricsView();
  }
}

function setScoreView(name) {
  State.scoreView = name;
  try { localStorage.setItem(SCORE_VIEW_KEY, name); } catch (err) { /* private mode */ }
  paintScoreView();
}

function isScoreMaximized() {
  var modal = $('score-modal');
  return modal ? modal.classList.contains('maximized') : false;
}

function paintScoreMaximized() {
  var isMax = isScoreMaximized();
  var scoreMaxBtn = $('score-maximize');
  var rollMaxBtn = $('roll-maximize');
  if (scoreMaxBtn) {
    scoreMaxBtn.textContent = isMax ? 'Restore' : 'Maximize';
    scoreMaxBtn.title = isMax ? 'Restore standard size' : 'Maximize (Full width)';
  }
  if (rollMaxBtn) {
    rollMaxBtn.textContent = isMax ? 'Restore' : 'Maximize';
    rollMaxBtn.title = isMax ? 'Restore standard size' : 'Maximize to full browser width';
  }
}

function toggleScoreMaximized() {
  var modal = $('score-modal');
  var box = modal ? modal.querySelector('.modal-box.score') : null;
  if (!modal || !box) { return; }
  var nextState = !modal.classList.contains('maximized');
  modal.classList.toggle('maximized', nextState);
  box.classList.toggle('maximized', nextState);
  try {
    localStorage.setItem('yeufonic_score_max', nextState ? '1' : '0');
  } catch (err) {}
  paintScoreMaximized();
  if (window.PianoRoll && scoreView() === 'roll') {
    window.PianoRoll.ensurePlayheadVisible();
  }
}
window.toggleScoreMaximized = toggleScoreMaximized;

function loadScoreMaximized() {
  var saved = null;
  try { saved = localStorage.getItem('yeufonic_score_max'); } catch (err) {}
  if (saved === '1') {
    var modal = $('score-modal');
    var box = modal ? modal.querySelector('.modal-box.score') : null;
    if (modal && box) {
      modal.classList.add('maximized');
      box.classList.add('maximized');
    }
  }
  paintScoreMaximized();
}

function openScoreEditor(view) {
  $('score-big').value = $('abc').value;
  initScoreSf2Select();
  paintScoreTempo();
  if (scoreStack.items[scoreStack.index] !== $('abc').value) { scoreReset($('abc').value); }
  if (view) { State.scoreView = view; }
  paintScoreView();
  paintScoreMaximized();
  updateScoreCount();
  $('score-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
  setTimeout(function () { $('score-big').focus(); }, 30);
}

function closeScoreEditor() {
  notationStop();            // a preview left playing has no controls to stop it with
  if (window.PianoRoll) { window.PianoRoll.stop(); }
  if (scoreIsDirty() && (takeIdInEditor() || (State.mode === 'cover' && currentSource()))) {
    saveScore(true);
  }
  $('score-modal').classList.add('hidden');
  document.body.style.overflow = '';
  $('abc').focus();
}

function syncScoreFromBig() {
  $('abc').value = $('score-big').value;
  // Fire the event the small box would, so the chart, the length and the save all run.
  $('abc').dispatchEvent(new Event('input'));
  paintScoreView();
  updateScoreCount();
  scheduleScoreAutoSave();
}

/* A window closes when its backdrop is clicked, but only a click that began there.
   Pressing inside a window (to select text, or drag its scrollbar) and letting go a
   little outside it makes the browser report a click on the backdrop, and the window
   closed under the pointer. */
var PRESSED_ON = null;
document.addEventListener('pointerdown', function (event) { PRESSED_ON = event.target; }, true);

function backdropClick(event, backdrop) {
  return event.target === backdrop && PRESSED_ON === backdrop;
}

/* ----------------------------------------------------------- confirm modal */
var CONFIRM_RESOLVE = null;
var CONFIRM_PREV_FOCUS = null;
var CONFIRM_IS_INPUT = false;

function closeConfirmModal(result) {
  var modal = $('confirm-modal');
  var inputEl = $('confirm-input');
  if (modal) { modal.classList.add('hidden'); }
  if (inputEl) { inputEl.classList.add('hidden'); }
  if (CONFIRM_RESOLVE) {
    var resolve = CONFIRM_RESOLVE;
    CONFIRM_RESOLVE = null;
    if (CONFIRM_IS_INPUT) {
      resolve(result ? (inputEl ? inputEl.value.trim() : '') : null);
    } else {
      resolve(Boolean(result));
    }
    CONFIRM_IS_INPUT = false;
  }
  if (CONFIRM_PREV_FOCUS && typeof CONFIRM_PREV_FOCUS.focus === 'function') {
    try { CONFIRM_PREV_FOCUS.focus(); } catch (e) {}
    CONFIRM_PREV_FOCUS = null;
  }
}

function confirmModal(options) {
  var modal = $('confirm-modal');
  if (!modal) {
    if (options && options.input) {
      return Promise.resolve(window.prompt(options.message || options.title || '', options.defaultValue || ''));
    }
    var msg = typeof options === 'string' ? options : (options && options.message) || '';
    return Promise.resolve(window.confirm(msg));
  }
  if (typeof options === 'string') {
    options = { message: options };
  }
  options = options || {};
  var title = options.title || 'Confirm';
  var message = options.message || '';
  var confirmText = options.confirmText || 'OK';
  var cancelText = options.cancelText || 'Cancel';
  var danger = Boolean(options.danger);
  var isInput = Boolean(options.input);

  $('confirm-title').textContent = title;
  $('confirm-message').textContent = message;

  var okBtn = $('confirm-ok');
  var cancelBtn = $('confirm-cancel');
  var inputEl = $('confirm-input');

  okBtn.textContent = confirmText;
  cancelBtn.textContent = cancelText;

  if (danger) {
    okBtn.className = 'primary danger';
  } else {
    okBtn.className = 'primary';
  }

  if (inputEl) {
    if (isInput) {
      inputEl.value = options.defaultValue || '';
      inputEl.placeholder = options.placeholder || '';
      inputEl.classList.remove('hidden');
    } else {
      inputEl.value = '';
      inputEl.classList.add('hidden');
    }
  }

  if (CONFIRM_RESOLVE) {
    CONFIRM_RESOLVE(isInput ? null : false);
  }

  CONFIRM_IS_INPUT = isInput;
  CONFIRM_PREV_FOCUS = document.activeElement;

  return new Promise(function (resolve) {
    CONFIRM_RESOLVE = resolve;
    modal.classList.remove('hidden');

    if (isInput && inputEl) {
      setTimeout(function () {
        inputEl.focus();
        inputEl.select();
      }, 20);
    } else if (danger) {
      cancelBtn.focus();
    } else {
      okBtn.focus();
    }
  });
}
if (typeof window !== 'undefined') {
  window.confirmModal = confirmModal;
}

function openLyricsEditor() {
  $('lyrics-big').value = $('lyrics').value;
  updateLyricsCount();
  $('lyrics-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
  setTimeout(function () { $('lyrics-big').focus(); }, 30);
}

function closeLyricsEditor() {
  $('lyrics-modal').classList.add('hidden');
  document.body.style.overflow = '';
  $('lyrics').focus();
}

function syncLyricsFromBig() {
  $('lyrics').value = $('lyrics-big').value;
  // Fire the same event the small box would, so saving and the title hint still run.
  $('lyrics').dispatchEvent(new Event('input'));
  updateLyricsCount();
}

function insertTag(tag) {
  var box = $('lyrics-big');
  var text = box.value;
  var start = box.selectionStart;
  var before = text.slice(0, start);
  var prefix = (!before || before.endsWith('\n')) ? '' : '\n';
  var insert = prefix + tag + '\n';
  box.value = before + insert + text.slice(start);
  box.selectionStart = box.selectionEnd = start + insert.length;
  box.focus();
  syncLyricsFromBig();
}

function refreshTitleHint() {
  // An instrumental has no words to borrow a title from.
  if (State.mode === 'inst') { $('title').placeholder = 'Name the piece, or leave blank'; return; }
  var guess = guessTitle($('lyrics').value);
  $('title').placeholder = guess ? 'Leave blank to use: ' + guess : 'Leave blank and the first lyric line is used';
}

var JOB_KINDS = { render: 'Render', plan: 'Score plan', transcribe: 'Transcription', separate: 'Stem separation', hear: 'Lyric hearing', lyrics: 'Lyrics', text: 'Text generation', train: 'LoRA training', other: 'Engine job',
  identity_score: 'Corpus analysis', identity_style: 'Corpus analysis', persona_score: 'Corpus analysis', persona_style: 'Corpus analysis' };

/* While a LoRA trains it holds the GPU — 12.5 GB of 16, measured — so everything
   else that would ask for the card is disabled rather than left to fail. The server
   refuses them too; this is so nobody has to find out that way. */
function lockGpuControls() {
  var training = Boolean(State.training);
  var loraName = (State.training && State.training.lora_name) || 'a LoRA';
  var title = training
    ? 'LoRA \u201c' + loraName + '\u201d is currently training and holds the GPU. Planning and rendering are paused until training finishes or is stopped.'
    : '';

  // The buttons' own tooltips are put back when training ends, not blanked: a button that says what it does
  // keeps saying it, and only while the GPU is held does the reason replace it.
  var hold = function (button) {
    button.disabled = training;
    if (training) {
      if (button.dataset.idleTitle === undefined) { button.dataset.idleTitle = button.title || ''; }
      button.title = title;
    } else if (button.dataset.idleTitle !== undefined) {
      button.title = button.dataset.idleTitle;
      delete button.dataset.idleTitle;
    }
  };
  ['create-song', 'create-cover', 'create-inst', 'render-take', 'steps-go'].forEach(function (id) {
    var button = $(id);
    if (button) { hold(button); }
  });
  Array.prototype.forEach.call(document.querySelectorAll('.takes [data-act]'), function (button) {
    var act = button.dataset.act || '';
    if (['render', 'again', 'variations', 'tries', 'revoice', 'replan', 'reroll'].indexOf(act) >= 0) { hold(button); }
  });

  paintEditorTrainingNotice(training);
}

function paintEditorTrainingNotice(training) {
  var status = $('render-status');
  if (!status) { return; }
  if (training && State.training) {
    var name = State.training.lora_name || 'custom';
    var pct = State.training.progress ? Math.round(State.training.progress * 100) + '%' : '';
    status.dataset.training = '1';
    status.className = 'status wait';
    var html = '<span class="status-training-msg">LoRA <strong>' + esc(name) + '</strong> is training' +
      (pct ? ' (' + pct + ')' : '') + ' \u2014 GPU is reserved</span> ' +
      '<button type="button" class="link status-training-view" id="ed-training-view">View / Stop</button>';
    if (status.innerHTML !== html) {
      status.innerHTML = html;
      var viewBtn = $('ed-training-view');
      if (viewBtn) {
        viewBtn.addEventListener('click', function () {
          if (State.training && State.training.identity_id) {
            openIdentities();
            showIdentity(State.training.identity_id);
          }
        });
      }
    }
  } else if (status.dataset.training) {
    delete status.dataset.training;
    status.className = 'status';
    status.innerHTML = '';
  }
}

function weakRender(take) {
  var limit = State.options && typeof State.options.weak_render_db === 'number' ? State.options.weak_render_db : -24;
  return typeof take.loudness === 'number' && take.loudness < limit;
}

function queueWhat(item) {
  var kind = '<span class="q-kind">' + esc(JOB_KINDS[item.kind] || 'Engine job') + '</span>';
  if (item.outside) {
    return kind + ' <span class="q-outside">from outside the app' + (item.client ? ' (' + esc(item.client) + ')' : '') + '</span>';
  }
  if (!item.title) {
    return kind + ' <span class="q-outside">' + esc(item.note || 'from the app') + '</span>';
  }
  return kind + ' \u00b7 ' + esc(item.title);
}

function queueWhen(item) {
  if (item.state === 'running') { return 'running ' + secs(item.seconds || 0); }
  if (item.state === 'pending') { return 'sent' + (item.seconds ? ', waiting ' + secs(item.seconds) : ''); }
  return 'queued in the app';
}

/* The card shows the job the GPU is on, whoever sent it, and lists what follows.
   The engine shares live progress only with the app that sent a job, so a job from
   outside the app gets a time estimate instead of a stage. */
/* The transcription's progress under the recording's own buttons, as the main
   page's job card shows it: the editor covers that card, in Cover and Instrumental
   alike. Made here when the page predates it, so an unrestarted app still gets it. */
function paintTranscribeJob(current, queue) {
  var source = currentSource();
  var box = $('transcribe-job');
  if (!box) {
    var row = $('cover-only') ? $('cover-only').querySelector('.source-row') : null;
    if (!row) { return; }
    box = document.createElement('div');
    box.id = 'transcribe-job';
    box.className = 'hear-job hidden';
    box.innerHTML = '<div class="bar"><div id="transcribe-bar"></div></div>' +
      '<div class="hear-job-line"><span id="transcribe-stage" class="muted">Waiting</span><span id="transcribe-time" class="muted"></span></div>';
    row.parentNode.insertBefore(box, row.nextSibling);
  }
  var mine = function (item) { return item && item.kind === 'transcribe' && source && item.id === source.id; };
  var running = mine(current) ? current : null;
  var waiting = !running && (queue || []).some(mine);
  box.classList.toggle('hidden', !running && !waiting);
  if (running) {
    $('transcribe-bar').style.width = Math.max(3, Math.round((running.progress || 0) * 100)) + '%';
    var label = running.label || 'Transcribing';
    if (running.value && running.max) { label += ' \u00b7 ' + running.value + '/' + running.max; }
    $('transcribe-stage').textContent = label;
    $('transcribe-time').textContent = secs(running.elapsed || 0);
  } else if (waiting) {
    $('transcribe-bar').style.width = '0%';
    $('transcribe-stage').textContent = 'Queued behind another job';
    $('transcribe-time').textContent = '';
  }
}

/* And a plan or render of the take the editor shows, say one opened from its card while it
   plans or renders: the editor's bottom bar carries its progress, in the status line's place. */
function paintRenderJob(current, queue) {
  var target = Selection.formTakeId || awaitingPlanId();
  var box = $('render-job');
  if (!box) {
    var status = $('render-status');
    if (!status || !status.parentNode) { return; }
    box = document.createElement('div');
    box.id = 'render-job';
    box.className = 'hear-job hidden';
    box.innerHTML = '<div class="bar"><div id="render-bar"></div></div>' +
      '<div class="hear-job-line"><span id="render-stage" class="muted">Waiting</span><span id="render-time" class="muted"></span></div>';
    status.parentNode.insertBefore(box, status);
  }
  var mine = function (item) {
    return item && (item.kind === 'render' || item.kind === 'plan') && target && item.id === target;
  };
  var running = mine(current) ? current : null;
  var waitingItem = !running && (queue || []).find(mine);
  var shown = Boolean(running || waitingItem);
  box.classList.toggle('hidden', !shown);
  if ($('render-status')) { $('render-status').classList.toggle('hidden', shown); }
  if (running) {
    $('render-bar').style.width = Math.max(3, Math.round((running.progress || 0) * 100)) + '%';
    var defaultLabel = running.kind === 'plan' ? 'Writing the score plan' : 'Rendering';
    var label = running.label || defaultLabel;
    if (running.value && running.max) { label += ' \u00b7 ' + running.value + '/' + running.max; }
    $('render-stage').textContent = label;
    $('render-time').textContent = secs(running.elapsed || 0);
  } else if (waitingItem) {
    $('render-bar').style.width = '0%';
    $('render-stage').textContent = (waitingItem.kind === 'plan' ? 'Score plan' : 'Render') + ' queued behind another job';
    $('render-time').textContent = '';
  }
}

function paintWriteJob(current, queue) {
  var box = $('lyrics-write-job');
  if (!box) {
    var field = $('lyrics-field');
    var labelRow = field ? field.querySelector('.label-row') : null;
    if (!field || !labelRow) { return; }
    box = document.createElement('div');
    box.id = 'lyrics-write-job';
    box.className = 'hear-job hidden';
    box.innerHTML = '<div class="bar indeterminate"><div id="lyrics-write-bar"></div></div>' +
      '<div class="hear-job-line"><span id="lyrics-write-stage" class="muted">Drafting lyrics\u2026</span>' +
      '<span style="display:inline-flex;gap:8px;align-items:center"><span id="lyrics-write-time" class="muted"></span>' +
      '<button type="button" id="lyrics-write-stop-btn" class="chip action compact">stop</button></span></div>';
    labelRow.parentNode.insertBefore(box, labelRow.nextSibling);
    var stopBtn = $('lyrics-write-stop-btn');
    if (stopBtn) { stopBtn.addEventListener('click', stopWrite); }
  }

  if (box.classList.contains('bad')) { return; }

  var targetId = WRITE.id;
  var mine = function (item) {
    if (!item || item.kind !== 'lyrics') { return false; }
    return targetId ? item.id === targetId : true;
  };
  var running = mine(current) ? current : null;
  var waitingItem = !running && (queue || []).find(mine);
  var isActive = Boolean(targetId || running || waitingItem);

  box.classList.toggle('hidden', !isActive);
  if (!isActive) { return; }

  var bar = box.querySelector('.bar');
  var barFill = $('lyrics-write-bar');
  var stageEl = $('lyrics-write-stage');
  var timeEl = $('lyrics-write-time');
  var stopBtn = $('lyrics-write-stop-btn');
  if (stopBtn) { stopBtn.style.display = ''; }

  var elapsed = 0;
  if (WRITE.started) {
    elapsed = Math.round((Date.now() - WRITE.started) / 1000);
  } else if (running && running.elapsed) {
    elapsed = running.elapsed;
  }
  if (timeEl) { timeEl.textContent = elapsed ? secs(elapsed) : ''; }

  if (running && running.progress && running.progress > 0) {
    if (bar) { bar.classList.remove('indeterminate'); }
    if (barFill) { barFill.style.width = Math.max(5, Math.round(running.progress * 100)) + '%'; }
    var label = running.label || 'Writing lyrics';
    if (running.value && running.max) { label += ' \u00b7 ' + running.value + '/' + running.max; }
    if (stageEl) { stageEl.textContent = label; }
  } else if (waitingItem) {
    if (bar) { bar.classList.remove('indeterminate'); }
    if (barFill) { barFill.style.width = '0%'; }
    if (stageEl) { stageEl.textContent = 'Queued behind another job'; }
  } else {
    if (bar) { bar.classList.add('indeterminate'); }
    if (barFill) { barFill.style.width = ''; }
    var text = (WRITE.status === 'running' || (running && running.stage))
      ? 'Writing lyrics\u2026'
      : 'Waiting for the engine\u2026';
    if (stageEl) { stageEl.textContent = text; }
  }
}

function showWriteError(message) {
  var box = $('lyrics-write-job');
  if (!box) { return; }
  box.classList.remove('hidden');
  box.classList.add('bad');
  var bar = box.querySelector('.bar');
  if (bar) { bar.classList.remove('indeterminate'); }
  var fill = $('lyrics-write-bar');
  if (fill) { fill.style.width = '100%'; }
  var stage = $('lyrics-write-stage');
  if (stage) { stage.textContent = message; }
  var time = $('lyrics-write-time');
  if (time) { time.textContent = ''; }
  var stopBtn = $('lyrics-write-stop-btn');
  if (stopBtn) { stopBtn.style.display = 'none'; }
  setTimeout(function () {
    if (!WRITE.id && box.classList.contains('bad')) {
      box.classList.add('hidden');
      box.classList.remove('bad');
      if (stopBtn) { stopBtn.style.display = ''; }
    }
  }, 6000);
}

function paintJob(current, queue, options) {
  var oldPlanBox = $('plan-job');
  if (oldPlanBox) { oldPlanBox.remove(); }
  paintTranscribeJob(current, queue);
  paintRenderJob(current, queue);
  paintWriteJob(current, queue);
  var card = $('job-card');
  if (!current && !queue.length) {
    if (State.training) {
      State.busy = true;
      card.className = 'job';
      $('job-stop').style.display = '';
      $('job-title').textContent = 'Training LoRA: ' + (State.training.lora_name || 'custom');
      var p = State.training.progress || 0;
      var elapsed = State.training.elapsed || 0;
      var eta = p > 0.02 && elapsed ? Math.max(0, (elapsed / p) - elapsed) : 0;
      $('job-time').textContent = secs(elapsed) + (eta ? ' / about ' + secs(elapsed + eta) : '');
      $('job-bar').style.width = Math.max(3, Math.round(p * 100)) + '%';
      var stageText = State.training.stage || 'Training';
      if (State.training.steps) { stageText += ' \u00b7 ' + State.training.steps + ' steps'; }
      $('job-stage').textContent = stageText;
      $('job-next').classList.add('hidden');
      return;
    }
    if (State.busy) { State.busy = false; loadTakes(); loadSources(); }
    card.className = 'job hidden';
    return;
  }
  if (current) { State.busy = true; }
  card.className = 'job';
  var head = queue[0] && queue[0].state === 'running' ? queue[0] : null;
  var mineRunning = current && head && !head.outside && head.id === current.id;
  var titles = { render: 'Rendering your song', plan: 'Writing the score plan', transcribe: 'Transcribing the recording',
    lyrics: 'Writing lyrics', train: 'Training the LoRA', identity_score: 'Analysing a corpus song',
    identity_style: 'Analysing a corpus song', persona_score: 'Analysing a corpus song', persona_style: 'Analysing a corpus song' };
  // Only the render has an average, measured from this machine's own history.
  // The others show the time they have taken and claim nothing about the rest.
  var average = function (kind) {
    // Training says how far through it is, step by step, so the rest of it can be
    // worked out rather than guessed.  A render uses this machine's own history.
    if (kind === 'train') {
      var p = (current && current.progress) || 0;
      return p > 0.02 && current.elapsed ? current.elapsed / p : 0;
    }
    return kind === 'render' ? (options.avg_render_seconds || 0) : 0;
  };
  var rest = queue;
  $('job-stop').style.display = current ? '' : 'none';
  if (current && (mineRunning || !head)) {
    rest = head ? queue.slice(1) : queue.filter(function (item) { return item.id !== current.id; });
    $('job-title').textContent = (titles[current.kind] || 'Working') + (head && head.title ? ': ' + head.title : '');
    var avg = average(current.kind);
    var eta = avg > 0 ? Math.max(0, avg - (current.elapsed || 0)) : 0;
    $('job-time').textContent = secs(current.elapsed) + (eta ? ' / about ' + secs(avg) : '');
    $('job-bar').style.width = Math.max(3, Math.round((current.progress || 0) * 100)) + '%';
    var label = head ? (current.label || 'Starting') : 'Waiting for the engine';
    if (current.value && current.max) { label += ' \u00b7 ' + current.value + '/' + current.max; }
    $('job-stage').textContent = label;
  } else if (head) {
    rest = queue.slice(1);
    $('job-title').textContent = head.outside
      ? 'Engine busy: ' + (JOB_KINDS[head.kind] || 'Engine job').toLowerCase() + ' from outside the app'
      : (titles[head.kind] || 'Working') + (head.title ? ': ' + head.title : '');
    var guess = average(head.kind);
    $('job-time').textContent = secs(head.seconds || 0) + (guess ? ' / about ' + secs(guess) : '');
    $('job-bar').style.width = (guess ? Math.max(3, Math.min(95, Math.round(100 * (head.seconds || 0) / guess))) : 3) + '%';
    $('job-stage').textContent = head.outside
      ? 'Sent by ' + (head.client || 'another program') + '. Its progress is estimated from your average ' + (JOB_KINDS[head.kind] || 'job').toLowerCase() + ' time.'
      : (head.note || 'Working');
  } else {
    $('job-title').textContent = 'Queued';
    $('job-time').textContent = '';
    $('job-bar').style.width = '0%';
    $('job-stage').textContent = 'Waiting for the engine';
  }
  $('job-next').classList.toggle('hidden', !rest.length);
  var html = rest.map(function (item) {
    // Only the app's own jobs that have not started can be taken back here; the one
    // running has the card's stop, and a job from outside the app is not ours.
    var cancel = item.state === 'waiting' && !item.outside && item.id
      ? '<button class="link q-cancel" data-kind="' + esc(item.kind) + '" data-id="' + esc(item.id) + '" title="Take this job out of the queue">cancel</button>'
      : '';
    return '<li><span class="q-what">' + queueWhat(item) + '</span><span class="q-when">' + esc(queueWhen(item)) + '</span>' + cancel + '</li>';
  }).join('');
  if ($('job-queue').dataset.html !== html) {
    $('job-queue').innerHTML = html;
    $('job-queue').dataset.html = html;
  }
}

/* --------------------------------------------------------------- sources */
async function loadSources() {
  State.sources = await api('/api/sources');
  var select = $('source-select');
  var previous = select.value;
  select.innerHTML = '<option value="">Choose a recording\u2026</option>' + State.sources.map(function (source) {
    var mark = source.has_score ? ' \u2713 score' : '';
    return '<option value="' + source.id + '">' + esc(source.title) + mark + '</option>';
  }).join('');
  if (previous) { select.value = previous; }
  // Spent on use, like the LoRA picker's: left in place it would put the
  // remembered recording back every time another was chosen.
  // Only a cover must have a recording: an instrumental starts without one.
  var needsOne = State.mode !== 'inst';
  if (!select.value && needsOne && State.wantedSource) { select.value = State.wantedSource; }
  if (needsOne) { State.wantedSource = null; }
  // A first visit has nothing to remember, and the newest recording is the one
  // most likely wanted.
  if (!select.value && needsOne && State.sources.length) { select.value = State.sources[0].id; }
  paintSourcePickerMenu();
  paintSource();
}

function paintSourcePickerMenu() {
  var menu = $('source-picker-menu');
  if (!menu) { return; }
  var currentId = $('source-select') ? $('source-select').value : '';
  var itemsHtml = '<div class="source-picker-item' + (!currentId ? ' selected' : '') + '" data-id="" role="option">' +
    '<div class="source-item-main"><span class="source-item-title muted">' +
      (State.mode === 'inst' ? 'No recording: write a score plan' : 'Choose a recording\u2026') + '</span></div>' +
    '</div>';
  itemsHtml += State.sources.map(function (source) {
    var isMidi = Boolean(source.filename && source.filename.match(/\.midi?$/i));
    var scoreBadge = isMidi
      ? '<span class="source-item-score midi-tag">MIDI</span>'
      : (source.has_score ? '<span class="source-item-score">\u2713 score</span>' : '');
    var isSel = source.id === currentId ? ' selected' : '';
    return '<div class="source-picker-item' + isSel + '" data-id="' + esc(source.id) + '" role="option">' +
      '<div class="source-item-main">' +
        '<span class="source-item-title">' + esc(source.title) + '</span>' +
        scoreBadge +
      '</div>' +
      '<button type="button" class="source-item-del" data-del="' + esc(source.id) + '" title="Delete this recording" aria-label="Delete ' + esc(source.title) + '">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
          '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>' +
          '<line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>' +
        '</svg>' +
      '</button>' +
    '</div>';
  }).join('');
  itemsHtml += corpusSongsHtml(currentId);
  // Typing in the filter redraws the menu; the box it redraws keeps the caret.
  var typing = document.activeElement && document.activeElement.id === 'source-corpus-filter';
  menu.innerHTML = itemsHtml;
  if (typing && $('source-corpus-filter')) {
    var box = $('source-corpus-filter');
    box.focus();
    box.setSelectionRange(box.value.length, box.value.length);
  }
}

/* ------------------------------------------ corpus songs, to cover as they are
   A corpus's analysis already made what a cover needs from a recording: the score,
   the heard words and the separated vocal. Its songs are offered below the
   recordings, folded by corpus, and picking one makes it a recording in one step. */
var SOURCE_CORPORA_KEY = 'yue2.source-corpora';

function sourceCorporaOpen() {
  try { return JSON.parse(localStorage.getItem(SOURCE_CORPORA_KEY) || '[]') || []; } catch (err) { return []; }
}

function saveSourceCorporaOpen(list) {
  try { localStorage.setItem(SOURCE_CORPORA_KEY, JSON.stringify(list)); } catch (err) { /* private mode */ }
}

async function loadCorpusSongs() {
  try {
    State.corpusSongs = await api('/api/corpus-songs');
  } catch (err) {
    State.corpusSongs = [];   // a server from before this: nothing to offer
  }
  paintSourcePickerMenu();
}

function corpusSongsHtml(currentId) {
  var groups = State.corpusSongs || [];
  var total = groups.reduce(function (sum, group) { return sum + group.songs.length; }, 0);
  if (!total) { return ''; }
  var filter = (State.corpusFilter || '').trim().toLowerCase();
  var open = sourceCorporaOpen();
  var html = '<div class="source-corpora-head"><span>From your corpora</span>' +
    (total > 12 ? '<input id="source-corpus-filter" type="search" placeholder="Filter songs" value="' +
      esc(State.corpusFilter || '') + '">' : '') + '</div>';
  var shown = 0;
  groups.forEach(function (group) {
    var songs = group.songs.filter(function (song) { return !filter || song.title.toLowerCase().indexOf(filter) >= 0; });
    if (!songs.length) { return; }
    shown += songs.length;
    var isOpen = Boolean(filter) || open.indexOf(group.id) >= 0;
    html += '<div class="lora-group" role="button" aria-expanded="' + isOpen + '" data-cgroup="' + esc(group.id) + '">' +
      '<span class="fold">' + (isOpen ? '\u25BE' : '\u25B8') + '</span><span>' + esc(group.name) + '</span>' +
      '<span class="count">' + songs.length + '</span></div>';
    if (!isOpen) { return; }
    songs.forEach(function (song) {
      var meta = [song.key, song.tempo ? song.tempo + ' BPM' : ''].filter(Boolean).join(', ');
      var tip = song.source_id ? 'Already one of your recordings' :
        'Use this song as a recording: its score and words come from the corpus, with nothing run again';
      html += '<div class="source-picker-item corpus-song' + (song.source_id && song.source_id === currentId ? ' selected' : '') +
        '" role="option" data-corpus-song="' + esc(song.id) + '" title="' + esc(tip) + '">' +
        '<div class="source-item-main"><span class="source-item-title">' + esc(song.title) + '</span>' +
        (song.source_id ? '<span class="source-item-score">\u2713 added</span>' : '') +
        (meta ? '<span class="source-item-meta">' + esc(meta) + '</span>' : '') +
        (song.caveat ? '<span class="source-item-caveat" title="Transcribe it again for the whole score with its chords">score: ' +
          esc(song.caveat) + '</span>' : '') +
        '</div></div>';
    });
  });
  if (!shown) { html += '<div class="source-corpora-none muted">No corpus song matches.</div>'; }
  return html;
}

async function useCorpusSong(songId) {
  var song = null;
  (State.corpusSongs || []).forEach(function (group) {
    group.songs.forEach(function (item) { if (item.id === songId) { song = item; } });
  });
  var id = song && song.source_id;
  closeSourcePicker();
  try {
    if (!id) {
      statusLine('Adding \u201c' + (song ? song.title : 'the song') + '\u201d from its corpus\u2026');
      var made = await api('/api/sources/from-corpus/' + encodeURIComponent(songId), { method: 'POST' });
      id = made.id;
      await loadSources();
      loadCorpusSongs();
      statusLine('Added \u201c' + made.title + '\u201d with its score' + (made.lyrics ? ' and words' : '') +
        ' from the corpus.', 'good');
    }
    $('source-select').value = id;
    $('source-select').dispatchEvent(new Event('change'));
    fillCorpusSongStyle(songId, true);
    await takeRecordingWords(id);
  } catch (err) {
    statusLine('Could not add it: ' + err.message, 'bad');
  }
}

function openSourcePicker() {
  var menu = $('source-picker-menu');
  var btn = $('source-picker-btn');
  if (!menu || !btn) { return; }
  menu.classList.remove('hidden');
  btn.setAttribute('aria-expanded', 'true');
  loadCorpusSongs();
}

function closeSourcePicker() {
  var menu = $('source-picker-menu');
  var btn = $('source-picker-btn');
  if (!menu || !btn) { return; }
  menu.classList.add('hidden');
  btn.setAttribute('aria-expanded', 'false');
}

function toggleSourcePicker() {
  var menu = $('source-picker-menu');
  if (!menu) { return; }
  if (menu.classList.contains('hidden')) {
    openSourcePicker();
  } else {
    closeSourcePicker();
  }
}

function currentSource() {
  var id = $('source-select') ? $('source-select').value : '';
  for (var i = 0; i < State.sources.length; i++) { if (State.sources[i].id === id) { return State.sources[i]; } }
  return null;
}

/* The words follow the recording.  Words the app put in from one recording, unedited,
   give way to the next one's, or go if it has none: left in, a cover of one song
   was sung with another's words.  Words typed or edited in the box stay unless the
   user agrees to replace them, as Extract lyrics asks. */
var RECORDING_WORDS_KEY = 'yue2.recordingWords';

function sameWords(a, b) {
  return String(a || '').replace(/\r\n?/g, '\n').trim() === String(b || '').replace(/\r\n?/g, '\n').trim();
}

function recordingWords(text) {
  try {
    if (arguments.length) { localStorage.setItem(RECORDING_WORDS_KEY, text || ''); return text; }
    return localStorage.getItem(RECORDING_WORDS_KEY) || '';
  } catch (err) {
    if (arguments.length) { State.recordingWords = text || ''; }
    return State.recordingWords || '';
  }
}

async function takeRecordingWords(sourceId) {
  var box = $('lyrics');
  if (!box || State.mode !== 'cover' || !sourceId) { return; }
  var source = sourceById(sourceId);
  var words = '';
  try {
    // The words heard in the recording, else the words last used for a cover of it.
    var heard = await api('/api/sources/' + encodeURIComponent(sourceId) + '/lyrics');
    words = (heard && (heard.lyrics || heard.last_used)) || '';
  } catch (err) { return; }
  if ($('source-select').value !== sourceId || sameWords(box.value, words)) { return; }
  var theirs = !box.value.trim() || sameWords(box.value, recordingWords());
  if (!theirs) {
    if (!words) { return; }
    var name = source && source.title ? '\u201c' + source.title + '\u201d' : 'this recording';
    if (!await confirmModal({
      title: 'Replace lyrics',
      message: 'Replace the words in the box with the words of ' + name + '?',
      confirmText: 'Replace',
      danger: true
    })) { return; }
  }
  box.value = words;
  recordingWords(words);
  box.dispatchEvent(new Event('input'));
  saveForm();
}

function sourceById(id) {
  for (var i = 0; i < State.sources.length; i++) { if (State.sources[i].id === id) { return State.sources[i]; } }
  return null;
}

function paintSource() {
  var source = currentSource();
  var badge = $('score-badge');
  paintHearButton();
  paintAudition();

  var pickerLabel = $('source-picker-label');
  var isMidi = Boolean(source && source.filename && source.filename.match(/\.midi?$/i));
  if (pickerLabel) {
    pickerLabel.textContent = source
      ? source.title + (isMidi ? ' [MIDI]' : (source.has_score ? ' \u2713 score' : ''))
      : 'Choose a recording\u2026';
  }
  var items = document.querySelectorAll('.source-picker-item');
  items.forEach(function (el) {
    el.classList.toggle('selected', el.dataset.id === (source ? source.id : ''));
  });
  if ($('transcribe')) {
    $('transcribe').disabled = !source || isMidi;
    $('transcribe').title = isMidi ? 'MIDI files are converted to score on upload and do not need transcription' : '';
  }
  if ($('source-lyrics')) {
    $('source-lyrics').disabled = !source || isMidi;
    $('source-lyrics').title = isMidi ? 'MIDI files do not have audio vocals for lyric extraction' : 'Write down the words this recording sings';
  }
  if ($('audition')) { $('audition').disabled = !source; }
  if ($('source-delete')) { $('source-delete').disabled = !source; }
  if ($('source-tracks')) {
    $('source-tracks').classList.toggle('hidden', !source || !isMidi);
    $('source-tracks').disabled = !source || !isMidi;
  }

  if (!source) {
    badge.textContent = 'no score';
    badge.className = 'badge';
    // An instrumental let go of its recording: the recording's score goes with it.
    if (State.mode === 'inst' && Selection.boxKind === 'source') { clearRecordingScore(); }
    followRecordingCap();
    paintInstSource();
    if (State.mode === 'cover') {
      statusLine('Choose a recording to start a cover.');
    }
    return;
  }
  if (isMidi) {
    badge.className = 'badge ok';
    badge.textContent = 'MIDI score';
    if (State.mode === 'cover') {
      statusLine('Imported MIDI file. Score is ready to edit or cover.', 'good');
    }
  } else {
    badge.className = 'badge' + (source.has_score ? ' ok' : '');
    badge.textContent = source.has_score ? 'score ready' : 'no score';
    if (State.mode === 'cover') {
      var map = {
        none: 'Not transcribed yet. Transcribe it to get a score.',
        queued: 'Queued for transcription.',
        running: 'Transcribing\u2026',
        done: 'Transcribed. The score is ready to edit.',
        failed: 'Transcription failed: ' + (source.transcribe_error || 'unknown error')
      };
      var kind = source.transcribe_state === 'failed' ? 'bad' : (source.transcribe_state === 'done' ? 'good' : (source.transcribe_state === 'running' || source.transcribe_state === 'queued' ? 'wait' : ''));
      statusLine(map[source.transcribe_state] || (source.has_score ? 'Score ready to edit or cover.' : ''), kind);
    }
  }
  paintSourceTempo(source);
  // The box must hold this recording's score or nothing. Comparing ids matters:
  // this tested whether editorSourceId was set at all, so choosing a second
  // recording left the first one's score in the box, and a cover of the second was
  // rendered from the first one's melody.
  if ((State.mode === 'cover' || State.mode === 'inst') && !scoreTakeId() && !boxShowsSource(source.id)) {
    if (source.transcribe_state === 'done') {
      loadScore();
    } else if ($('abc').value.trim()) {
      $('abc').value = '';
      scoreBaseline('');
      setSelection({ formTakeId: Selection.formTakeId });
      setChart('');
      syncEditor();
    }
  }
  followRecordingCap();
  paintInstSource();
}

/* A score transcribed from a recording can describe a different length of music,
   and then its tempo is wrong: the cover follows the score, so it plays too slow
   or too fast. Both numbers are known here, so say so, with the tempo that fits. */
function paintSourceTempo(source) {
  var node = $('source-tempo');
  if (!node) { return; }
  var seconds = source && source.duration ? Number(source.duration) : 0;
  var estimate = source && source.score_seconds
    ? { seconds: Number(source.score_seconds), bpm: Number(source.score_bpm) || 120 }
    : null;
  if (!estimate || !seconds) { node.textContent = ''; node.className = 'status'; return; }
  var ratio = estimate.seconds / seconds;
  if (ratio > 0.85 && ratio < 1.15) { node.textContent = ''; node.className = 'status'; return; }
  var fits = Math.round(estimate.bpm / ratio);
  node.textContent = 'The score describes ' + Math.round(estimate.seconds) + 's of music for a '
    + Math.round(seconds) + 's recording (' + ratio.toFixed(2) + 'x), so its tempo is probably wrong. '
    + 'The score says ' + estimate.bpm + ' BPM and about ' + fits + ' fits the recording. '
    + 'A cover follows the score, so it plays at that tempo. Expand the score to change it.';
  node.className = 'status bad';
}

async function deleteSource() {
  var source = currentSource();
  if (!source) { return; }
  await deleteSourceById(source.id);
}

async function deleteSourceById(id) {
  var source = sourceById(id);
  if (!source) { return; }
  var covers = source.take_count ? ' Its ' + source.take_count + ' cover take(s) keep their audio and score, but cannot be rendered again from it.' : '';
  if (!await confirmModal({
    title: 'Delete recording',
    message: 'Delete the recording \u201c' + source.title + '\u201d and its stems?' + covers,
    confirmText: 'Delete',
    danger: true
  })) { return; }
  try {
    await api('/api/sources/' + id, { method: 'DELETE' });
  } catch (err) {
    statusLine('Could not delete: ' + err.message, 'bad');
    return;
  }
  if ($('source-select').value === id) {
    $('source-select').value = '';
    // The box held this recording's score, or a cover take's copy of it.
    if (boxShowsSource(id)) {
      $('abc').value = '';
      scoreBaseline('');
      setChart('');
    }
    claimEditorFor(null);
  }
  await loadSources();
}

async function loadScore() {
  var source = currentSource();
  if (!source) { return; }
  // A take in the editor outranks a source transcription.  Without this guard a
  // finished job (paintJob reloads the sources) overwrites the plan that just
  // landed, and the render button then has nothing to point at.
  if (scoreTakeId()) { return; }
  // Already showing this recording's score: leave the box alone, edits and all.
  // This is the same mistake as in paintSource below it: the test was whether
  // editorSourceId was set, not whether it named THIS recording, so a cover of a
  // second recording was rendered from the first one's melody.
  if (boxShowsSource(source.id)) { return; }
  var selected = selectedTakeId();
  var full = await api('/api/sources/' + source.id);
  // Selecting a cover take switches to cover mode, which starts this load, and the
  // take is loaded into the column before the score arrives.  The take wins.  Going
  // on here cleared leftTakeId, and the next card click then took the take's own
  // words for an unsaved draft.
  if (scoreTakeId() || selectedTakeId() !== selected || currentSource() !== source) { return; }
  $('abc').value = full.abc || '';
  scoreBaseline(full.abc || '');
  // The recording owns the box now, empty score and all, so this does not fetch again.
  setSelection({ formTakeId: null, boxKind: 'source', boxId: source.id });
  setChart('');
  followRecordingCap();
  paintInstSource();
}

/* ------------------------------------------------ an instrumental from a recording
   The recording's transcription is the score, as a cover's is, so there is no plan
   to write. The score's own sections are the structure, one tag each, in the names
   the instrumental LoRA knows: a render pairs the two, and a tag short it stops a
   section early. Worked out here from the score in the box, which is what is sent;
   the server works them out again from the same score. */
var SCORE_SECTION_AS = { interlude: 'bridge', prechorus: 'pre-chorus', 'pre chorus': 'pre-chorus', solo: 'bridge',
  'break': 'bridge', breakdown: 'bridge', coda: 'outro', ending: 'outro' };

/* The length cap follows a recording's score: the score fixes the length, and 360
   seconds would cut a longer one short. Rounded up with about ten seconds to spare:
   a render that doesn't stop at the end of its score plays on to the cap, so the
   less room past the score, the shorter that overrun (#24). A cap typed by hand, or
   a take's own, is left alone; letting go of the recording goes back to the default. */
var DEFAULT_CAP = 360;

function capForScore(abc) {
  var length = planLength(abc);
  if (!length || !length.seconds) { return null; }
  return Math.min(900, Math.ceil((length.seconds + 10) / 10) * 10);
}

function followRecordingCap() {
  var box = $('max-duration');
  if (!box || State.capTyped) { return; }
  var fromRecording = (State.mode === 'cover' || State.mode === 'inst') && Selection.boxKind === 'source' &&
    Boolean(currentSource()) && Selection.boxId === currentSource().id;
  var cap = fromRecording ? capForScore($('abc').value) : null;
  if (cap) {
    box.value = cap;
    State.capFromScore = true;
  } else if (State.capFromScore && !fromRecording) {
    box.value = DEFAULT_CAP;
    State.capFromScore = false;
  } else {
    return;
  }
  if (State.mode === 'inst') { paintStructure(); }
  saveForm();
}

function clearRecordingScore() {
  $('abc').value = '';
  scoreBaseline('');
  setSelection({ formTakeId: Selection.formTakeId });
  setChart('');
  syncEditor();
}

function instFromRecording() { return State.mode === 'inst' && Boolean(currentSource()); }

/* A planned instrumental open in the editor: its score has sections, so they are listed to rearrange,
   as a recording's are. Without a plan, the structure is still only the brief for one. */
function instPlanned() {
  return State.mode === 'inst' && !currentSource() && Boolean(takeIdInEditor()) &&
    typeof scoreSectionSpans === 'function' && scoreSectionSpans($('abc').value).length > 0;
}

function scoreSections(abc) {
  var names = [];
  String(abc || '').replace(/^%[ \t]*([A-Za-z][\w -]*?)[ \t]*$/gm, function (whole, name) { names.push(name.trim().toLowerCase()); return whole; });
  return names.map(function (name, index) {
    if (SECTIONS.indexOf(name) >= 0) { return name; }
    if (name === 'silence') { return index === 0 ? 'intro' : (index === names.length - 1 ? 'outro' : 'bridge'); }
    return SCORE_SECTION_AS[name] || 'verse';
  });
}

/* Each section of the score, where it runs and what it was called there: the
   header, then that section alone, measured as planLength measures a whole score. */
function scoreSectionSpans(abc) {
  var text = String(abc || '');
  var pattern = /^%[ \t]*([A-Za-z][\w -]*?)[ \t]*$/gm;
  var marks = [];
  var found;
  while ((found = pattern.exec(text))) { marks.push({ at: found.index, after: pattern.lastIndex, was: found[1].trim().toLowerCase() }); }
  if (!marks.length) { return []; }
  var header = text.slice(0, marks[0].at);
  var names = scoreSections(text);
  var clockAt = 0;
  return marks.map(function (mark, index) {
    var body = text.slice(mark.after, index + 1 < marks.length ? marks[index + 1].at : text.length);
    var length = planLength(header + '\n' + body);
    var span = { name: names[index], was: mark.was, start: clockAt, end: clockAt + (length ? length.seconds : 0) };
    clockAt = span.end;
    return span;
  });
}

/* Notes in the Vocal voice: an instrumental whose score has any would sing, so the
   server gives them to the Ins voice first. */
function vocalNotes(abc) {
  var voice = null, notes = 0;
  String(abc || '').split('\n').forEach(function (raw) {
    var line = raw.trim();
    if (line.indexOf('V:') === 0) { voice = line.slice(2).trim().split(/\s+/)[0] || null; return; }
    if (!line || line.charAt(0) === '%' || /^[A-Za-z]:/.test(line) || voice !== 'Vocal') { return; }
    notes += (line.replace(/"[^"]*"/g, '').match(/[A-Ga-g]/g) || []).length;
  });
  return notes;
}

function instRecordingProblem() {
  if (!$('abc').value.trim()) { return 'Transcribe this recording first: its score is what the instrumental plays.'; }
  return '';
}

/* What an instrumental shows with a recording chosen and without: the planner's
   controls go, since nothing is planned, and the main button renders. */
function paintInstSource() {
  if (State.mode !== 'inst') { return; }
  var fromRecording = instFromRecording();
  ['harmony-field', 'variety-field', 'plan-actions'].forEach(function (id) {
    if ($(id)) { $(id).style.display = fromRecording ? 'none' : ''; }
  });
  if ($('auto-wrap')) { $('auto-wrap').style.display = fromRecording ? 'none' : ''; }
  if ($('create-inst')) { $('create-inst').textContent = fromRecording ? 'Create instrumental' : (instPlanned() ? 'Render this score' : 'Write score plan'); }
  // The hint the mode switch left says to write a plan, which a recording does without.
  var hint = 'Write a score plan to start a song from scratch.';
  var played = 'Create instrumental plays the recording\'s score, with no vocal and no plan to write.';
  var shown = $('render-status') ? $('render-status').textContent : '';
  if (fromRecording && shown === hint) { statusLine(played); }
  if (!fromRecording && shown === played) { statusLine(hint); }
  // A sung melody is given to an instrument by the server, as the tune the render plays.
  if (fromRecording && $('abc').value.trim() && vocalNotes($('abc').value)) {
    statusLine('The score has a sung melody: the instrumental plays it on an instrument.');
  }
  paintStructure();
}

/* Each mode keeps its own recording: a cover's is not an instrumental's, and an
   instrumental starts with none. */
function rememberSourceFor(before, after) {
  var select = $('source-select');
  if (!select || before === after) { return; }
  State.sourceByMode = State.sourceByMode || {};
  if (before === 'inst' || select.value) { State.sourceByMode[before] = select.value; }
  if (after === 'inst') {
    select.value = State.sourceByMode.inst || '';
  } else if (after === 'cover') {
    if (State.sourceByMode.cover) { select.value = State.sourceByMode.cover; }
    if (!select.value && State.sources.length) { select.value = State.sources[0].id; }
  }
}

/* ------------------------------------------------------------------ vocal ---
   YuE2 has no vocal parameter: the model reads a [Tags] block, which is the style
   field, and a [Lyrics] block. So these chips edit the style text itself. That way
   the take stores the choice and a re-render reproduces it. */
var VOCAL_SEX = [
  { value: 'any', label: 'Any', phrase: '' },
  { value: 'female', label: 'Female', phrase: 'female vocal' },
  { value: 'male', label: 'Male', phrase: 'male vocal' },
  { value: 'duet', label: 'Duet', phrase: 'duet, male and female voices' }
];
var VOCAL_TONE = ['breathy', 'raspy', 'powerful', 'soft', 'deep', 'youthful', 'airy', 'gritty'];

function styleHas(text, word) {
  return new RegExp('\\b' + word + '\\b', 'i').test(text);
}

function tidyStyle(text) {
  return text
    .replace(/\s*,\s*,+/g, ', ')
    .replace(/^[\s,]+/, '')
    .replace(/[\s,]+$/, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

/* A style can say "female" anywhere, not only in the chips' own phrase: a learned
   style reads "intimate female lead vocals". Whichever the text names last is the
   voice it asks for. \bmale\b does not match inside "female". */
function currentVocalSex() {
  var style = $('style').value;
  if (/\bduet\b/i.test(style)) { return 'duet'; }
  var female = style.toLowerCase().lastIndexOf('female');
  var male = -1;
  style.replace(/\bmale\b/gi, function (word, at) { male = at; return word; });
  if (female < 0 && male < 0) { return 'any'; }
  return female > male ? 'female' : 'male';
}

/* Edits the style part by part, keeping what each part says about the voice: choosing
   Male turns "intimate female lead vocals" into "intimate male lead vocals" rather than
   leaving it to contradict a "male vocal" added at the end. Any drops the word; Duet
   drops it and adds its own phrase. */
function setVocalSex(value) {
  var option = VOCAL_SEX.filter(function (item) { return item.value === value; })[0] || VOCAL_SEX[0];
  var bare = /^(vocal|vocals|voice|voices|lead|lead vocal|lead vocals|singer)$/i;
  var parts = $('style').value.split(',').map(function (part) { return part.trim(); }).filter(function (part) {
    // The chips' own phrases go; they are put back below if still wanted.
    return part && !/^(male|female)\s+(vocal|vocals|voice|voices)$/i.test(part) && !/^duet\b/i.test(part) &&
      !/^male and female voices$/i.test(part) &&
      // Scraps of the duet phrase ("male and") that an earlier version left behind.
      !/^((fe)?male|and|\s)+$/i.test(part);
  }).map(function (part) {
    if (value === 'male') { return part.replace(/\bfemale\b/gi, function (w) { return w[0] === 'F' ? 'Male' : 'male'; }); }
    if (value === 'female') { return part.replace(/\bmale\b/gi, function (w) { return w[0] === 'M' ? 'Female' : 'female'; }); }
    return part.replace(/\b(fe)?male\b\s*/gi, '').replace(/\s{2,}/g, ' ').trim();
  }).filter(function (part) { return part && !bare.test(part); });
  var said = parts.some(function (part) { return value !== 'any' && value !== 'duet' && new RegExp('\\b' + value + '\\b', 'i').test(part); });
  if (option.phrase && !said) { parts.push(option.phrase); }
  $('style').value = tidyStyle(parts.join(', '));
  paintVocals();
}

function toggleVocalTone(word) {
  var style = $('style').value;
  if (styleHas(style, word)) {
    style = style.replace(new RegExp('\\s*,?\\s*' + word + '\\b', 'i'), '');
  } else {
    style = style ? style + ', ' + word : word;
  }
  $('style').value = tidyStyle(style);
  paintVocals();
}

function paintVocals() {
  var sex = currentVocalSex();
  var style = $('style').value;
  $('vocal-sex').innerHTML = VOCAL_SEX.map(function (item) {
    return '<button class="chip' + (item.value === sex ? ' active' : '') + '" data-sex="' + item.value + '">' +
      esc(item.label) + '</button>';
  }).join('');
  $('vocal-tone').innerHTML = VOCAL_TONE.map(function (word) {
    return '<button class="chip' + (styleHas(style, word) ? ' active' : '') + '" data-tone="' + word + '">' +
      esc(word) + '</button>';
  }).join('');
  if (typeof syncStylePickerLabel === 'function') { syncStylePickerLabel(); }
}

var IDENTITIES_LIST = [];
var PERSONAS_LIST = IDENTITIES_LIST;

async function loadVocalIdentities(preferredId, preferredLora) {
  try {
    IDENTITIES_LIST = await api('/api/identities');
  } catch (err) {
    IDENTITIES_LIST = [];
  }
  PERSONAS_LIST = IDENTITIES_LIST;
  paintStyleLoras();
}

var loadVocalPersonas = loadVocalIdentities;

/* The main page says what the app is doing. Renders and plans show on the engine card
   already; a corpus being prepared works on the CPU lane and says nothing outside its
   own screen, so closing that screen leaves the app looking idle while it works.
   This badge is that missing line: the corpus name is not shown because there is one
   number worth reading — how many of its songs are done. */
var CORPUS_POLL_BUSY = 4000;
var CORPUS_POLL_IDLE = 30000;

/* A stage that has settled is finished, whether it worked or not. Counting only
   successes would leave a corpus that failed one song reading "10 of 11" for ever,
   with nothing running and no way to tell it from work in progress.  So the count
   is what has settled, and a failure lands where it can be seen: on the corpus. */
var CORPUS_STAGES = ['vocals_state', 'lyrics_state', 'score_state', 'style_state'];

function corpusProgressOf(detail) {
  var songs = (detail.songs || []).filter(function (song) { return song.include; });
  var settled = 0;
  var failed = 0;
  var active = 0;
  var started = false;
  songs.forEach(function (song) {
    var states = CORPUS_STAGES.map(function (key) { return song[key]; });
    if (states.some(function (state) { return state && state !== 'none'; })) { started = true; }
    if (states.indexOf('queued') >= 0 || states.indexOf('running') >= 0) { active += 1; return; }
    if (states.every(function (state) { return state === 'done' || state === 'failed'; })) {
      settled += 1;
      if (states.indexOf('failed') >= 0) { failed += 1; }
    }
  });
  return {
    id: detail.id,
    name: detail.name,
    done: settled,
    total: songs.length || Number((detail.summary || {}).included) || 0,
    failed: failed,
    started: started,
    busy: Boolean(detail.busy) || active > 0
  };
}

/* The page's HTML is read into memory once at start-up, so a change to it needs a
   restart; the scripts and styles are read from disk every time. This builds the
   badge when the markup does not have it yet, so the page and the script can be
   deployed separately and the badge appears either way. */
function corporaBadge() {
  var button = $('corpora-badge');
  if (button) { return button; }
  var right = document.querySelector('.topbar-right');
  if (!right) { return null; }
  button = document.createElement('button');
  button.id = 'corpora-badge';
  button.className = 'pill corpora hidden';
  button.title = 'Corpora, and what the app is preparing';
  button.innerHTML = '<span class="corpora-dot" aria-hidden="true"></span>' +
    '<span id="corpora-text">Corpora</span>';
  right.appendChild(button);
  wireCorporaBadge(button);
  return button;
}

/* The listener goes on once, from whichever path produced the element: the markup
   has it now, the script may have built it, and only one of those runs. */
function wireCorporaBadge(button) {
  if (!button || button.dataset.wired) { return; }
  button.dataset.wired = '1';
  button.addEventListener('click', function () {
    openIdentities();
    var target = State.activeCorpus || State.openCorpus;
    if (target) { showIdentity(target); }
  });
}

function paintCorporaBadge() {
  var button = corporaBadge();
  if (!button) { return; }
  // Only hide if options have definitively arrived and training is not available.
  if (State.options && !trainingAvailable()) {
    button.classList.add('hidden');
    button.classList.remove('shown');
    return;
  }
  var progress = State.corpusProgress || {};
  var ids = Object.keys(progress);
  if (!ids.length) {
    button.classList.add('hidden');
    button.classList.remove('shown');
    return;
  }
  var busy = null;
  var unfinished = null;
  var started = null;
  ids.forEach(function (id) {
    var item = progress[id];
    if (item.busy && !busy) { busy = item; }
    if (item.total && item.done < item.total && !unfinished) { unfinished = item; }
    if (item.started && !started) { started = item; }
  });
  // A corpus whose LoRA is training is the one to show, and it is busy until it ends.
  var training = State.training ? progress[State.training.identity_id] : null;
  var savedActive = null;
  try { savedActive = localStorage.getItem('yue2_active_corpus'); } catch (e) {}
  // Active corpus takes precedence: training, open in view, busy working, unfinished,
  // recently active/opened, saved in storage, or most recent.
  var active = training || (IDENTITY.id && progress[IDENTITY.id]) ||
               busy ||
               unfinished ||
               (State.activeCorpus && progress[State.activeCorpus]) ||
               (savedActive && progress[savedActive]) ||
               (State.openCorpus && progress[State.openCorpus]) ||
               started ||
               progress[ids[0]];
  var shown = active || progress[ids[0]];
  State.openCorpus = shown ? shown.id : null;
  State.activeCorpus = shown ? shown.id : null;
  button.classList.remove('hidden');
  button.classList.add('shown');
  var isBusy = Boolean((shown && shown.busy) || training);
  button.classList.toggle('busy', isBusy);
  var failed = shown ? (Number(shown.failed) || 0) : 0;
  // A settled failure is not work in progress, so it gets its own mark rather than
  // a pulse: the count alone would read as a corpus that never finished.
  button.classList.toggle('trouble', failed > 0 && !isBusy);
  var name = shown ? shown.name : 'Corpora';
  var text = esc(name || 'Corpora');
  var job = training && State.currentJob && State.currentJob.kind === 'train' ? State.currentJob : null;
  var trainPct = job && job.progress ? ' ' + Math.round(job.progress * 100) + '%' : '';
  if (training) {
    text += ' <span class="count">training' + trainPct + '</span>';
  } else if (shown && (shown.started || shown.total)) {
    text += ' <span class="count">' + shown.done + ' of ' + shown.total + '</span>';
  }
  if ($('corpora-text').innerHTML !== text) { $('corpora-text').innerHTML = text; }
  var trouble = failed ? ' ' + failed + (failed === 1 ? ' song did not analyse.' : ' songs did not analyse.') : '';
  button.title = training
    ? training.name + ': training its LoRA' + (job && job.value && job.max ? ', step ' + job.value + ' of ' + job.max : '') + '. Click to open it.'
    : (shown && shown.busy)
    ? shown.name + ': ' + shown.done + ' of ' + shown.total + ' songs settled, still working. Click to open it.'
    : (shown ? shown.name + ': ' + shown.done + ' of ' + shown.total + ' settled.' + trouble + ' Click to open it.'
             : 'Your corpora. Click to open them.');
}

async function pollCorpora() {
  var busy = false;
  try {
    IDENTITIES_LIST = await api('/api/identities');
  } catch (err) {
    // Try again: returning here without a next time left the badge frozen on its last
    // count, still pulsing, after one failed call during a restart.
    clearTimeout(State.corpusTimer);
    State.corpusTimer = setTimeout(pollCorpora, CORPUS_POLL_IDLE);
    return;
  }
  var progress = {};
  for (var i = 0; i < IDENTITIES_LIST.length; i++) {
    var id = IDENTITIES_LIST[i].id;
    try {
      var detail = await api('/api/identities/' + id);
      progress[id] = corpusProgressOf(detail);
      IDENTITIES_LIST[i] = detail;      // the list route carries no progress
      if (detail.busy) { busy = true; }
    } catch (err) { /* leave this one out rather than lie about it */ }
  }
  State.corpusProgress = progress;
  PERSONAS_LIST = IDENTITIES_LIST;
  paintCorporaBadge();
  paintCorpusCards();
  if (typeof paintStyleLoras === 'function') { paintStyleLoras(); }
  clearTimeout(State.corpusTimer);
  State.corpusTimer = setTimeout(pollCorpora, busy ? CORPUS_POLL_BUSY : CORPUS_POLL_IDLE);
}

/* Whether a newer release is out.  The app asks once a day on its own — the answer rides
   in the state it already polls — and the menu's Check for updates asks now, whatever the
   daily setting says.  The item answers where it was clicked: a notice that sends you
   somewhere else to read it is a notice nobody reads. */
State.updateChecking = false;
State.updateAnswer = null;

function updatePill() {
  var pill = $('update-pill');
  if (pill) { return pill; }
  var right = document.querySelector('.topbar-right');
  if (!right) { return null; }
  pill = document.createElement('button');
  pill.id = 'update-pill';
  pill.className = 'pill update hidden';
  pill.innerHTML = '<span class="update-dot" aria-hidden="true"></span><span id="update-text"></span>';
  var version = $('app-version');
  if (version && version.parentNode === right) { right.insertBefore(pill, version.nextSibling); }
  else { right.insertBefore(pill, right.firstChild); }
  pill.addEventListener('click', function () { actOnUpdate(); });
  return pill;
}

/* Built here as well as in the markup, so the script and the page can be deployed apart:
   the page's HTML is read at start-up, the script on every load. */
function updateMenuItem() {
  var item = $('menu-update');
  if (!item) {
    var menu = $('brand-menu');
    if (!menu) { return null; }
    item = document.createElement('button');
    item.id = 'menu-update';
    item.className = 'menu-item';
    item.setAttribute('role', 'menuitem');
    item.innerHTML = '<svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="2"><path d="M21 12a9 9 0 1 1-2.6-6.4"/><polyline points="21 3 21 9 15 9"/></svg>' +
      '<span id="menu-update-text">Check for updates</span>';
    menu.appendChild(item);
  }
  if (!item.dataset.wired) {
    item.dataset.wired = '1';
    item.addEventListener('click', function () {
      // A version to get is the action: the same click gets it, as the pill does.  Asking
      // is for when there is nothing to act on yet.
      if ((State.update || {}).newer) { actOnUpdate(); return; }
      checkForUpdates();
    });
  }
  return item;
}

/* Open a link in the system's default browser rather than inside the launcher's
   app window, so downloads and SmartScreen prompts appear in the user's regular browser. */
function openExternal(url) {
  if (!url) { return; }
  api('/api/update/open', {
    method: 'POST',
    body: JSON.stringify({ url: url })
  }).then(function (res) {
    if (!res || !res.opened) {
      window.open(url, '_blank', 'noopener');
    }
  }).catch(function () {
    window.open(url, '_blank', 'noopener');
  });
}

/* Somewhere to go.  A Windows install has an installer to run, which is the whole of its
   update; a Docker copy has to be pulled and rebuilt, so what it wants is the release page
   — its notes end with the two commands — and the installer beside it would be no use to it
   at all.  Neither install updates itself: the app only ever tells you. */
function updateLink() {
  var info = State.update || {};
  if (info.install === 'windows') { return info.installer || info.notes || ''; }
  return info.notes || info.installer || '';
}

function updateAdvice(info) {
  if (info.install === 'windows') { return 'Download the installer and run it over this one; your library and models are kept.'; }
  return 'Then ' + (info.line || 'git pull && docker compose up -d --build') + '.';
}

/* The installer is not signed, so its hash is the one thing that says a download arrived
   whole.  Nobody memorises a SHA-256, but showing it costs nothing and it is checkable. */
function updateHash(info) {
  return info.sha256 ? ' SHA-256 ' + String(info.sha256).replace(/^sha256:/, '') : '';
}

/* Two lines for a terminal, on the clipboard.  A Docker copy is updated by hand, and
   sending someone to a page to copy them out of it is a step for nothing.  The page is
   still there to read what changed. */
function copyForTerminal(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  }
  // A copy served over plain http on a LAN address has no clipboard API at all, so the
  // old way, with a box nobody sees.
  var box = document.createElement('textarea');
  box.value = text;
  box.setAttribute('readonly', '');
  box.style.position = 'fixed';
  box.style.top = '-1000px';
  document.body.appendChild(box);
  box.select();
  var copied = false;
  try { copied = document.execCommand('copy'); } catch (err) { copied = false; }
  document.body.removeChild(box);
  return copied ? Promise.resolve() : Promise.reject(new Error('the browser refused the copy'));
}

var UPDATE_MODAL_POLL = null;

function formatUpdateBytes(bytes) {
  if (!bytes || bytes <= 0) { return '0 B'; }
  if (bytes < 1024 * 1024) { return (bytes / 1024).toFixed(1) + ' KB'; }
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function closeUpdateModal() {
  if (UPDATE_MODAL_POLL) {
    clearInterval(UPDATE_MODAL_POLL);
    UPDATE_MODAL_POLL = null;
  }
  var modal = $('update-modal');
  if (modal) { modal.classList.add('hidden'); }
}

function openUpdateModal(info) {
  info = info || State.update || {};
  var modal = $('update-modal');
  if (!modal) { return; }

  var titleEl = $('update-modal-title');
  var closeBtn = $('update-modal-close');
  var bodyEl = $('update-modal-body');
  var actionsEl = $('update-modal-actions');
  var version = info.latest || '';

  closeBtn.onclick = function () {
    closeUpdateModal();
  };

  function renderPrompt() {
    titleEl.textContent = 'Update to Yeufonic ' + version;
    closeBtn.textContent = 'Cancel';
    closeBtn.onclick = closeUpdateModal;

    bodyEl.innerHTML =
      '<p class="update-modal-desc">A newer version of Yeufonic is available (<strong>v' + (info.current || '0.0.0') + '</strong> \u2192 <strong>v' + version + '</strong>).</p>' +
      '<p class="update-modal-desc" style="margin-top: 8px;">Yeufonic will download the installer directly to your <strong>Downloads</strong> folder and verify it.</p>' +
      '<p class="muted small" style="margin-top: 8px;">Your library, settings, LoRAs and models will all be kept.</p>';

    actionsEl.innerHTML = '';

    var cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'ghost';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.onclick = closeUpdateModal;
    actionsEl.appendChild(cancelBtn);

    var dlBtn = document.createElement('button');
    dlBtn.type = 'button';
    dlBtn.className = 'primary';
    dlBtn.textContent = 'Download update';
    dlBtn.onclick = function () { startDownloadFlow(); };
    actionsEl.appendChild(dlBtn);
  }

  function renderDownloading(dlState) {
    titleEl.textContent = 'Downloading Yeufonic ' + version;
    closeBtn.textContent = 'Cancel';
    closeBtn.onclick = function () {
      api('/api/update/download/cancel', { method: 'POST' }).catch(function () {});
      closeUpdateModal();
    };

    var progress = Math.min(100, Math.round((dlState.progress || 0) * 100));
    var bytesInfo = formatUpdateBytes(dlState.downloaded_bytes);
    if (dlState.total_bytes > 0) {
      bytesInfo += ' / ' + formatUpdateBytes(dlState.total_bytes);
    }

    bodyEl.innerHTML =
      '<p class="update-modal-desc">Downloading <code>' + (dlState.filename || ('Yeufonic-Setup-' + version + '.exe')) + '</code>...</p>' +
      '<div class="update-progress-wrap">' +
        '<div class="update-progress-bar">' +
          '<div class="update-progress-fill" style="width: ' + progress + '%;"></div>' +
        '</div>' +
        '<div class="update-progress-info">' +
          '<span>' + bytesInfo + '</span>' +
          '<span>' + progress + '%</span>' +
        '</div>' +
      '</div>';

    actionsEl.innerHTML = '';
    var cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'ghost';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.onclick = function () {
      api('/api/update/download/cancel', { method: 'POST' }).catch(function () {});
      closeUpdateModal();
    };
    actionsEl.appendChild(cancelBtn);
  }

  function renderDone(dlState) {
    if (UPDATE_MODAL_POLL) {
      clearInterval(UPDATE_MODAL_POLL);
      UPDATE_MODAL_POLL = null;
    }
    titleEl.textContent = 'Update ready to install';
    closeBtn.textContent = '✕';
    closeBtn.onclick = closeUpdateModal;

    var fname = dlState.filename || ('Yeufonic-Setup-' + version + '.exe');
    bodyEl.innerHTML =
      '<div class="update-success-badge">' +
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>' +
        '<span>Download complete &amp; verified</span>' +
      '</div>' +
      '<p class="update-modal-desc"><strong>' + fname + '</strong> has been saved to your <strong>Downloads</strong> folder.</p>' +
      '<p class="muted small" style="margin-top: 8px;">Click <strong>Run installer</strong> to start updating now. The installer will ask you to quit Yeufonic first (right-click its icon by the clock, then Quit), and carries on when you have.</p>';

    actionsEl.innerHTML = '';

    var revealBtn = document.createElement('button');
    revealBtn.type = 'button';
    revealBtn.className = 'ghost';
    revealBtn.textContent = 'Show in folder';
    revealBtn.onclick = function () {
      api('/api/update/reveal', { method: 'POST' }).catch(function (err) {
        statusLine('Could not open folder: ' + (err.message || err), 'bad');
      });
    };
    actionsEl.appendChild(revealBtn);

    var closeActionBtn = document.createElement('button');
    closeActionBtn.type = 'button';
    closeActionBtn.className = 'ghost';
    closeActionBtn.textContent = 'Close';
    closeActionBtn.onclick = closeUpdateModal;
    actionsEl.appendChild(closeActionBtn);

    var installBtn = document.createElement('button');
    installBtn.type = 'button';
    installBtn.className = 'primary';
    installBtn.textContent = 'Run installer';
    installBtn.onclick = async function () {
      installBtn.disabled = true;
      installBtn.textContent = 'Starting installer…';
      try {
        await api('/api/update/launch', { method: 'POST' });
        bodyEl.innerHTML =
          '<p class="update-modal-desc">Starting installer... You may close this Yeufonic window.</p>';
      } catch (err) {
        installBtn.disabled = false;
        installBtn.textContent = 'Run installer';
        statusLine('Could not launch installer: ' + (err.message || err), 'bad');
      }
    };
    actionsEl.appendChild(installBtn);
  }

  function renderError(msg) {
    if (UPDATE_MODAL_POLL) {
      clearInterval(UPDATE_MODAL_POLL);
      UPDATE_MODAL_POLL = null;
    }
    titleEl.textContent = 'Download failed';
    closeBtn.textContent = '✕';
    closeBtn.onclick = closeUpdateModal;

    bodyEl.innerHTML =
      '<p class="update-error-text">Could not complete download:</p>' +
      '<p class="muted small" style="margin-top: 6px; word-break: break-word;">' + (msg || 'Unknown error occurred.') + '</p>' +
      '<p class="update-modal-desc" style="margin-top: 10px;">You can retry, or download the installer directly via your browser.</p>';

    actionsEl.innerHTML = '';

    var browserBtn = document.createElement('button');
    browserBtn.type = 'button';
    browserBtn.className = 'ghost';
    browserBtn.textContent = 'Download in browser';
    browserBtn.onclick = function () {
      openExternal(info.installer || info.notes);
      closeUpdateModal();
    };
    actionsEl.appendChild(browserBtn);

    var closeActionBtn = document.createElement('button');
    closeActionBtn.type = 'button';
    closeActionBtn.className = 'ghost';
    closeActionBtn.textContent = 'Close';
    closeActionBtn.onclick = closeUpdateModal;
    actionsEl.appendChild(closeActionBtn);

    var retryBtn = document.createElement('button');
    retryBtn.type = 'button';
    retryBtn.className = 'primary';
    retryBtn.textContent = 'Try again';
    retryBtn.onclick = function () { startDownloadFlow(); };
    actionsEl.appendChild(retryBtn);
  }

  async function pollDownload() {
    try {
      var dl = await api('/api/update/download');
      if (!dl) { return; }
      if (dl.status === 'downloading') {
        renderDownloading(dl);
      } else if (dl.status === 'done') {
        renderDone(dl);
      } else if (dl.status === 'error') {
        renderError(dl.error);
      }
    } catch (err) {
      // transient network error while polling local backend
    }
  }

  async function startDownloadFlow() {
    renderDownloading({ progress: 0, downloaded_bytes: 0, total_bytes: 0, filename: 'Yeufonic-Setup-' + version + '.exe' });
    try {
      var res = await api('/api/update/download', { method: 'POST' });
      if (res && res.status === 'done') {
        renderDone(res);
        return;
      }
    } catch (err) {
      renderError(err.message || 'Could not initiate download.');
      return;
    }
    if (UPDATE_MODAL_POLL) { clearInterval(UPDATE_MODAL_POLL); }
    UPDATE_MODAL_POLL = setInterval(pollDownload, 400);
  }

  modal.classList.remove('hidden');

  // Check current status before deciding view:
  api('/api/update/download').then(function (dl) {
    if (dl && dl.status === 'downloading') {
      renderDownloading(dl);
      if (UPDATE_MODAL_POLL) { clearInterval(UPDATE_MODAL_POLL); }
      UPDATE_MODAL_POLL = setInterval(pollDownload, 400);
    } else if (dl && dl.status === 'done' && dl.filename && dl.filename.indexOf(version) !== -1) {
      renderDone(dl);
    } else {
      renderPrompt();
    }
  }).catch(function () {
    renderPrompt();
  });
}

/* Acting on it: a Windows install runs the installer, and a Docker copy gets the commands
   to paste.  Neither updates itself, so this is as far as the app can take anyone. */
async function actOnUpdate() {
  var info = State.update || {};
  if (info.install !== 'windows' && info.line) {
    copyForTerminal(info.line).then(function () {
      State.updateAnswer = 'Copied \u2014 paste it in a terminal';
      paintUpdateMenuItem();
      seenUpdate();
    }).catch(function () {
      var url = updateLink();
      if (url) { openExternal(url); }
      State.updateAnswer = 'Could not copy \u2014 here is the release page';
      paintUpdateMenuItem();
      seenUpdate();
    });
    return;
  }
  var url = updateLink();
  if (!url) { return; }

  if (info.install === 'windows') {
    openUpdateModal(info);
    seenUpdate();
    return;
  }

  openExternal(url);
  seenUpdate();
}

function seenUpdate() {
  var info = State.update || {};
  if (!info.newer || info.seen) { return; }
  info.seen = true;
  paintUpdate(info);
  api('/api/update/seen', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ version: info.latest }) }).catch(function () {});
}

async function checkForUpdates() {
  if (State.updateChecking) { return; }
  State.updateChecking = true;
  var label = $('menu-update-text');
  if (label) { label.textContent = 'Checking…'; }
  try {
    var info = await api('/api/update/check', { method: 'POST' });
    State.updateAnswer = updateAnswerOf(info);
    paintUpdate(info);
  } catch (err) {
    State.updateAnswer = 'Could not check for updates.';
  } finally {
    State.updateChecking = false;
    paintUpdateMenuItem();
  }
}

function updateAnswerOf(info) {
  if (!info || !info.latest) { return 'Could not check for updates.'; }
  if (!info.newer) { return 'Up to date (v' + info.current + ').'; }
  return info.latest + ' is out — get it.';
}

function paintUpdateMenuItem() {
  var label = $('menu-update-text');
  if (!label || State.updateChecking) { return; }
  var info = State.update || {};
  if (State.updateAnswer) { label.textContent = State.updateAnswer; return; }
  // Something to get is an action, so it says so, in one line; otherwise the item asks.
  label.textContent = (info.newer && info.latest) ? 'Get ' + info.latest : 'Check for updates';
  var item = $('menu-update');
  if (item) {
    if (info.newer && info.latest) {
      item.title = 'Version ' + info.latest + ' is out. ' + updateAdvice(info) + updateHash(info);
    } else {
      item.removeAttribute('title');
    }
  }
}

function paintUpdate(info) {
  if (info) { State.update = info; }
  var known = State.update || {};
  var pill = updatePill();
  var show = Boolean(known.newer && known.latest && !known.seen);
  if (pill) {
    pill.classList.toggle('hidden', !show);
    pill.classList.toggle('shown', show);
    var text = $('update-text');
    if (text && show) { text.textContent = known.latest + ' available'; }
    if (show) {
      pill.title = 'Version ' + known.latest + ' is out; this build is v' + known.current + '. ' +
        updateAdvice(known) + updateHash(known);
    } else {
      pill.removeAttribute('title');
    }
  }
  updateMenuItem();
  paintUpdateMenuItem();
}

function identityName(id) {
  if (!id) { return null; }
  for (var i = 0; i < IDENTITIES_LIST.length; i++) {
    if (IDENTITIES_LIST[i].id === id) { return IDENTITIES_LIST[i].name; }
  }
  return null;
}

var personaName = identityName;

/* The LoRA a training run's other files belong to, as loras.run_lora on the server:
   its checkpoints (name_step950), the trainer's best copy, and a previous run set
   aside under a date (name_20260920_step50). */
function loraRunOf(file) {
  var stem = String(file || '').replace(/\.safetensors$/i, '');
  var found = /^(.+?)(?:_\d{8}(?:_\d{4})?)?(?:_step\d+|_best)?$/.exec(stem);
  return (found ? found[1] : stem) + '.safetensors';
}

function getIdentityLoRAs(identity) {
  if (!identity) { return []; }
  // The engine's list became a catalogue of entries when the style picker was
  // added; this one only ever wanted the names.
  var allLoras = ((State.options && State.options.loras) || []).map(function (item) {
    return typeof item === 'string' ? item : item.name;
  });
  var matches;
  if (identity.lora) {
    // The corpus records its LoRA's file name: that file, its checkpoints and any
    // previous run set aside. A name search missed "First Second" in first_second_lora.
    matches = allLoras.filter(function (l) { return l === identity.lora || loraRunOf(l) === identity.lora; });
  } else {
    var trigger = (identity.trigger_word || '').toLowerCase();
    var name = (identity.name || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    matches = allLoras.filter(function (l) {
      var lower = l.toLowerCase();
      return (trigger && lower.indexOf(trigger) !== -1) || (name && lower.indexOf(name) !== -1);
    });
  }
  matches.sort(function (a, b) {
    var aBest = a.indexOf('_best') !== -1;
    var bBest = b.indexOf('_best') !== -1;
    if (aBest && !bBest) { return -1; }
    if (!aBest && bBest) { return 1; }
    var aStep = (a.match(/step(\d+)/) || [])[1];
    var bStep = (b.match(/step(\d+)/) || [])[1];
    if (aStep && bStep) { return parseInt(bStep, 10) - parseInt(aStep, 10); }
    return a.localeCompare(b);
  });
  return matches;
}

var getPersonaLoRAs = getIdentityLoRAs;


/* ---------------------------------------------------------------- settings */
function setting(key, fallback) {
  var value = (State.settings || {})[key];
  return value === undefined || value === null || value === '' ? fallback : value;
}

function paintSettings() {
  // The settings about disk space live in the Storage window, beside what they act on.
  var list = (State.settingSpec || []).filter(function (item) { return item.section !== 'storage'; });
  $('settings-list').innerHTML = list.map(function (item) {
    var control;
    if (item.type === 'select') {
      control = '<select data-key="' + esc(item.key) + '">' + item.options.map(function (option) {
        return '<option value="' + esc(option.value) + '"' +
          (option.value === item.value ? ' selected' : '') + '>' + esc(option.label) + '</option>';
      }).join('') + '</select>';
    } else if (item.type === 'password') {
      // The saved key never comes back from the server, only whether there is one,
      // so the box starts empty and a new key typed into it replaces the old.
      control = '<div class="api-key-control">' +
        '<input type="text" class="setting-masked-input" autocomplete="off" spellcheck="false" ' +
        'data-lpignore="true" data-1p-ignore="true" data-bwignore="true" data-form-type="other" ' +
        'data-secret="1" data-key="' + esc(item.key) + '" value="" placeholder="' +
        (item.saved ? 'Saved. Type a new key to replace it' : 'Paste your key') + '">' +
        '<button type="button" class="ghost small btn-toggle-mask" title="Reveal or hide what you type">Show</button>' +
        (item.saved ? '<button type="button" class="ghost small btn-remove-secret" data-remove="' + esc(item.key) + '">Remove</button>' : '') +
      '</div>';
    } else if (item.key === 'llm.model') {
      var models = State.llmModels || [];
      var hasModels = models.length > 0;
      var curVal = item.value || '';
      var selectHtml = '<select id="select-llm-model" class="llm-model-select' + (hasModels ? '' : ' hidden') + '" style="' + (hasModels ? 'display:block;' : 'display:none;') + '">' +
        '<option value="">-- ' + (hasModels ? 'Select from ' + models.length + ' available models' : 'Select model') + ' --</option>' +
        models.map(function (m) {
          var isSel = (m.id === curVal);
          return '<option value="' + esc(m.id) + '"' + (isSel ? ' selected' : '') + '>' + esc(m.label || m.name || m.id) + '</option>';
        }).join('') +
      '</select>';

      control = '<div class="llm-model-control">' +
        '<div class="llm-model-input-group">' +
          '<input type="text" spellcheck="false" data-key="' + esc(item.key) + '" id="input-llm-model" value="' + esc(item.value) + '" placeholder="e.g. gemini-2.5-flash">' +
          '<button type="button" id="btn-fetch-models" class="ghost small" title="Fetch available models from provider API">Fetch Models</button>' +
        '</div>' +
        selectHtml +
        '<div id="fetch-models-status" class="hint llm-models-status">' +
          (hasModels ? '\u2713 Loaded ' + models.length + ' models' : '') +
        '</div>' +
      '</div>';
    } else {
      control = '<input type="text" spellcheck="false" data-key="' + esc(item.key) + '" value="' + esc(item.value) + '">';
    }
    // A setting that only means something when another one has a given value, such
    // as the lyrics method with an external LLM, carries a note saying what it needs.
    var needs = item.requires
      ? '<div class="setting-help hidden" data-needs="' + esc(item.key) + '">' + esc(item.requires_note || '') + '</div>'
      : '';
    return '<div class="setting-row">' +
      '<div class="setting-text">' +
        '<div class="setting-label">' + esc(item.label) + '</div>' +
        '<div class="setting-help">' + esc(item.help || '') + '</div>' +
        needs +
      '</div>' +
      '<div class="setting-control">' + control + '<span class="saved" data-saved="' + esc(item.key) + '"></span></div>' +
    '</div>';
  }).join('');
  paintSettingRequirements();
}

/* Grey out a setting whose requirement is not met, and say why.  Separate from
   paintSettings because a save updates the values without redrawing the sheet,
   which would take the cursor out of a field being typed in. */
function paintSettingRequirements() {
  var list = $('settings-list');
  if (!list) { return; }
  (State.settingSpec || []).forEach(function (item) {
    if (!item.requires) { return; }
    var met = Object.keys(item.requires).every(function (key) {
      return setting(key, '') === item.requires[key];
    });
    var control = list.querySelector('[data-key="' + item.key + '"]');
    if (control) { control.disabled = !met; }
    var note = list.querySelector('[data-needs="' + item.key + '"]');
    if (note) { note.classList.toggle('hidden', met); }
  });
}

async function fetchLLMModels(isBackground) {
  var btn = $('btn-fetch-models');
  var status = $('fetch-models-status');
  var sel = $('select-llm-model');
  var urlEl = $('settings-list') ? $('settings-list').querySelector('input[data-key="llm.api_url"]') : null;
  var keyEl = $('settings-list') ? $('settings-list').querySelector('input[data-key="llm.api_key"]') : null;
  var modelInput = $('input-llm-model');

  var apiUrl = (urlEl ? urlEl.value.trim() : '') || setting('llm.api_url', '');
  var apiKey = (keyEl ? keyEl.value.trim() : '') || setting('llm.api_key', '');

  if (isBackground && !apiKey && apiUrl.indexOf('localhost') === -1 && apiUrl.indexOf('127.0.0.1') === -1) {
    return;
  }

  if (btn) { btn.disabled = true; }
  if (status) {
    status.style.color = 'var(--muted)';
    status.textContent = 'Fetching models\u2026';
  }

  try {
    var body = {};
    if (apiUrl) { body.api_url = apiUrl; }
    if (apiKey) { body.api_key = apiKey; }

    var res = await api('/api/settings/llm-models', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    var models = (res && res.models) || [];
    State.llmModels = models;

    if (sel) {
      var currentVal = (modelInput ? modelInput.value.trim() : '') || setting('llm.model', '');
      var optionsHtml = '<option value="">-- Select from ' + models.length + ' available models --</option>';
      models.forEach(function (m) {
        var isSel = (m.id === currentVal);
        optionsHtml += '<option value="' + esc(m.id) + '"' + (isSel ? ' selected' : '') + '>' + esc(m.label || m.name || m.id) + '</option>';
      });
      sel.innerHTML = optionsHtml;
      sel.classList.remove('hidden');
      sel.style.display = 'block';
    }

    if (status) {
      status.style.color = 'var(--good, #4ade80)';
      status.textContent = '\u2713 Found ' + models.length + ' models';
    }
  } catch (err) {
    if (!isBackground) {
      if (status) {
        status.style.color = 'var(--bad, #f87171)';
        status.textContent = '\u2717 ' + (err.message || 'Could not fetch models');
      }
    } else {
      if (status) { status.textContent = ''; }
    }
  } finally {
    if (btn) { btn.disabled = false; }
  }
}

async function testLLMConnection() {
  var btn = $('btn-test-llm');
  var status = $('test-llm-status');
  if (!btn || !status) { return; }
  btn.disabled = true;
  status.style.color = 'var(--muted)';
  status.textContent = 'Testing connection\u2026';
  try {
    var body = {};
    var urlEl = $('settings-list') ? $('settings-list').querySelector('input[data-key="llm.api_url"]') : null;
    var keyEl = $('settings-list') ? $('settings-list').querySelector('input[data-key="llm.api_key"]') : null;
    var modelEl = $('settings-list') ? $('settings-list').querySelector('input[data-key="llm.model"]') : null;
    if (urlEl && urlEl.value) { body.api_url = urlEl.value.trim(); }
    if (keyEl && keyEl.value) { body.api_key = keyEl.value.trim(); }
    if (modelEl && modelEl.value) { body.model = modelEl.value.trim(); }

    var res = await api('/api/settings/test-llm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    status.style.color = 'var(--good, #4ade80)';
    status.textContent = '\u2713 Connected! (' + (res.model || '') + ', ' + (res.latency_ms || 0) + 'ms)';
  } catch (err) {
    status.style.color = 'var(--bad, #f87171)';
    status.textContent = '\u2717 ' + (err.message || 'Connection failed');
  } finally {
    btn.disabled = false;
  }
}

async function saveSetting(input) {
  var key = input.dataset.key;
  // An empty secret box means "keep the saved one": it starts empty, so leaving it
  // must not wipe the key. Remove is the way to clear it.
  if (input.dataset.secret && !input.value.trim()) { return; }
  var mark = $('settings-list').querySelector('[data-saved="' + key + '"]');
  try {
    var data = await api('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: key, value: input.value })
    });
    adoptSettings(data.settings);
    paintSettingRequirements();
    if (input.dataset.secret) {
      // Saved, so it leaves the page: the box goes back to saying there is one.
      input.value = '';
      input.placeholder = 'Saved. Type a new key to replace it';
    }
    if (key === 'llm.model') {
      var sel = $('select-llm-model');
      if (sel) { sel.value = input.value; }
    }
    if (mark) {
      mark.textContent = 'saved';
      setTimeout(function () { if (mark) { mark.textContent = ''; } }, 1800);
    }
  } catch (err) {
    if (mark) { mark.textContent = err.message; mark.style.color = 'var(--bad)'; }
  }
}

function adoptSettings(spec) {
  State.settingSpec = spec || [];
  var values = {};
  State.settingSpec.forEach(function (item) { values[item.key] = item.value; });
  State.settings = values;
  applyTheme();
  if (typeof editorOpen === 'function' && editorOpen()) { paintEditor(); }
}

/* ------------------------------------------------------------------- themes
   The theme is a setting, shown as data-theme on the page's root, which the style
   sheet's theme blocks key on. Dark is the style sheet's own. "Match the computer"
   follows the system's light or dark, and changes with it. Remembered in the
   browser too, so a reload paints in the right theme before the settings arrive. */
var THEMES = ['dark', 'light', 'studio', 'contrast'];
var SYSTEM_LIGHT = window.matchMedia ? window.matchMedia('(prefers-color-scheme: light)') : null;

function applyTheme() {
  var chosen = setting('appearance.theme', 'dark');
  var theme = chosen === 'system' ? (SYSTEM_LIGHT && SYSTEM_LIGHT.matches ? 'light' : 'dark') : chosen;
  if (THEMES.indexOf(theme) < 0) { theme = 'dark'; }
  try { localStorage.setItem('yue2.theme', chosen); } catch (err) { /* private mode */ }
  var root = document.documentElement;
  var before = root.dataset.theme || 'dark';
  if (theme === 'dark') { delete root.dataset.theme; } else { root.dataset.theme = theme; }
  if (before !== theme) { repaintTheme(); }
}

if (SYSTEM_LIGHT && SYSTEM_LIGHT.addEventListener) {
  SYSTEM_LIGHT.addEventListener('change', function () {
    if (setting('appearance.theme', 'dark') === 'system') { applyTheme(); }
  });
}

/* A colour the theme sets, for what the script draws itself. */
function themeColour(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/* What the script draws in colour, drawn again in the new theme's. */
function repaintTheme() {
  if (typeof drawWave === 'function') { try { drawWave(); } catch (err) { /* nothing on show */ } }
  var big = $('notation-big');
  if (big && big.offsetParent && typeof renderNotationView === 'function') { try { renderNotationView(); } catch (err) { /* ditto */ } }
}

function openBrandMenu() {
  var menu = $('brand-menu');
  if (menu) { menu.classList.remove('hidden'); }
  var brand = $('brand');
  if (brand) { brand.setAttribute('aria-expanded', 'true'); }
}

/* About: who made it, how it is licensed, and which build this is.  The same version number can
   be rebuilt, so the build (a commit and a date) is what pins a copy down. */
/* ------------------------------------------------------------ what a take was made with
   Everything the take stores about how it was made, in words, for reading, comparing two takes or pasting into a message. */
var MODE_WORDS = { full: 'full: keeps the chords', melody: 'melody: free accompaniment' };

/* What the take was asked to be, and what the planner wrote: the lyrics' tags, with how many lines each has, and the
   score's sections with where each begins.  A song planned from an instrumental's structure has tags only. */
function structureDetails(take) {
  var pairs = [];
  var asked = [];
  String(take.lyrics || '').split(/\n(?=\[)/).forEach(function (block) {
    var lines = block.split('\n');
    var tag = /^\[([^\]]+)\]/.exec(lines[0]);
    if (!tag) { return; }
    var count = lines.slice(1).filter(function (line) { return line.trim(); }).length;
    asked.push(tag[1] + (take.kind === 'instrumental' || !count ? '' : ' (' + count + ')'));
  });
  if (asked.length) { pairs.push([take.kind === 'instrumental' ? 'Structure sent' : 'Lyrics asked for', asked.join(', ')]); }
  var spans = typeof scoreSectionSpans === 'function' ? scoreSectionSpans(take.abc) : [];
  if (spans.length) {
    pairs.push(['Plan wrote', spans.map(function (span) { return (span.was || span.name) + ' ' + clock(span.start); }).join(', ')]);
    pairs.push(['Plan length', clock(spans[spans.length - 1].end)]);
  }
  return pairs;
}

function detailGroups(take) {
  var yes = function (flag) { return flag ? 'yes' : 'no'; };
  var kind = take.kind === 'song' ? 'Song from a prompt' : (take.kind === 'instrumental' ? 'Instrumental' : 'Cover');
  var made = [['Kind', kind]];
  if (take.created_at) { made.push(['Made', new Date(take.created_at * 1000).toLocaleString()]); }
  if (take.duration) { made.push(['Length', secs(take.duration)]); }
  if (take.max_duration) { made.push(['Length cap', secs(take.max_duration)]); }
  if (take.checkpoint) { made.push(['Model', take.checkpoint.replace(/\.safetensors$/, '')]); }
  if (take.kind !== 'cover' || take.mode) { made.push(['Mode', MODE_WORDS[take.mode] || take.mode || 'full']); }
  if (take.seed != null) { made.push(['Seed', String(take.seed)]); }
  if (take.sound_seed) { made.push(['Sound seed', String(take.sound_seed)]); }

  var sound = [['Interpretation', (INTERPRETATIONS[take.interpretation] || INTERPRETATIONS.standard).name]];
  if (take.kind !== 'cover') {
    sound.push(['Harmony', HARMONY_WORDS[take.harmony || 0] || HARMONY_WORDS[0]]);
    sound.push(['Plan variety', take.variety || 'normal']);
  }
  sound.push(['Production polish', yes(take.realaudio)]);
  sound.push(['Normalise volume', yes(take.normalise)]);
  if (take.normalised) {
    var level = take.normalised_to == null ? -14 : take.normalised_to;
    sound.push(['Normalised to', (level < 0 ? '\u2212' : '') + Math.abs(level) + ' LUFS']);
  }
  if (take.style_lora) {
    sound.push(['Style LoRA', take.style_lora.replace(/\.safetensors$/, '') + ' (planner ' + Number(take.style_lora_clip || 0).toFixed(2) +
      ', sound ' + Number(take.style_lora_model || 0).toFixed(2) + ')']);
  }
  if (take.voice_lora) {
    sound.push(['Voice LoRA', take.voice_lora.replace(/\.safetensors$/, '') + ' (' + Number(take.voice_lora_strength || 0).toFixed(2) + ')']);
  }
  var groups = [['Made', made], ['Sound', sound]];
  var structure = structureDetails(take);
  if (structure.length) { groups.push(['Structure', structure]); }

  var advanced = [];
  var set = function (label, value, shown) { if (value != null && value !== '' && value !== false) { advanced.push([label, shown || String(value)]); } };
  set('Sampler steps', take.sampler_steps);
  set('Avoid', take.avoid);
  set('Key lock', take.target_key);
  set('Tempo lock', take.target_bpm, take.target_bpm ? take.target_bpm + ' BPM' : '');
  set('Longest score', take.max_abc_tokens, take.max_abc_tokens ? take.max_abc_tokens + ' tokens' : '');
  set('Chord hold limit', take.chord_hold_limit);
  set('Out-of-key chord bonus', take.chord_outside_bonus);
  set('Follow my structure', take.follow_structure === 1 ? 1 : null, 'exactly');
  set('Sections open differently', take.chord_sections, take.chord_sections === 1 ? 'always' : (take.chord_sections === 0 ? 'never' : ''));
  set('Loudness target', take.target_lufs, take.target_lufs != null ? take.target_lufs + ' LUFS' : '');
  set('Fade out', take.fade_out_seconds, take.fade_out_seconds != null ? take.fade_out_seconds + ' s' : '');
  groups.push(['Advanced', advanced.length ? advanced : [['', 'none changed']]]);
  if (take.style) { groups.push(['Style', [['', take.style]]]); }
  return groups;
}

function detailsText(take) {
  return [take.title].concat(detailGroups(take).map(function (group) {
    return group[0] + '\n' + group[1].map(function (pair) { return pair[0] ? '  ' + pair[0] + ': ' + pair[1] : '  ' + pair[1]; }).join('\n');
  })).join('\n\n');
}

function openDetails(take) {
  if (!take || !$('details-modal')) { return; }
  State.detailsTake = take;
  $('details-title').textContent = take.title || 'Take';
  $('details-body').innerHTML = detailGroups(take).map(function (group) {
    return '<div class="sheet-blk"><h3>' + esc(group[0]) + '</h3><dl class="sheet-pairs">' + group[1].map(function (pair) {
      return pair[0] ? '<dt>' + esc(pair[0]) + '</dt><dd>' + esc(pair[1]) + '</dd>' : '<dd class="wide">' + esc(pair[1]) + '</dd>';
    }).join('') + '</dl></div>';
  }).join('');
  $('details-copied').textContent = '';
  $('details-modal').classList.remove('hidden');
}

function closeDetails() {
  $('details-modal').classList.add('hidden');
}

async function copyDetails() {
  var text = State.detailsTake ? detailsText(State.detailsTake) : '';
  try {
    await navigator.clipboard.writeText(text);
    $('details-copied').textContent = 'Copied';
  } catch (err) {
    // No clipboard here: select the text so Ctrl+C takes it.
    var range = document.createRange();
    range.selectNodeContents($('details-body'));
    var picked = window.getSelection();
    picked.removeAllRanges();
    picked.addRange(range);
    $('details-copied').textContent = 'Selected: press Ctrl+C';
  }
}

function wireDetails() {
  if (!$('details-modal')) { return; }
  $('details-close').addEventListener('click', closeDetails);
  $('details-copy').addEventListener('click', copyDetails);
  $('details-modal').addEventListener('click', function (event) { if (event.target === $('details-modal')) { closeDetails(); } });
}

function openAbout() {
  var about = State.about || {};
  var line = about.version ? 'Version ' + about.version : '';
  if (about.build) { line += (line ? ' \u00b7 build ' : 'Build ') + about.build; }
  $('about-build').textContent = line;
  if ($('about-model')) { $('about-model').textContent = about.model ? 'Model: ' + about.model : ''; }
  $('about-modal').classList.remove('hidden');
}

function closeAbout() {
  $('about-modal').classList.add('hidden');
}

function wireAbout() {
  var item = $('menu-about');
  if (item) {
    item.addEventListener('click', function (event) {
      event.stopPropagation();
      closeBrandMenu();
      openAbout();
    });
  }
  var modal = $('about-modal');
  if (!modal) { return; }
  if ($('about-close')) { $('about-close').addEventListener('click', closeAbout); }
  modal.addEventListener('click', function (event) {
    // Links open in the system's browser, as the update links do, not inside the app's window.
    var link = event.target.closest('a[data-external]');
    if (link) { event.preventDefault(); openExternal(link.href); return; }
    if (backdropClick(event, modal)) { closeAbout(); }
  });
}

function closeBrandMenu() {
  var menu = $('brand-menu');
  if (menu) { menu.classList.add('hidden'); }
  var brand = $('brand');
  if (brand) { brand.setAttribute('aria-expanded', 'false'); }
}

function toggleBrandMenu() {
  var menu = $('brand-menu');
  if (!menu) { return; }
  if (menu.classList.contains('hidden')) {
    openBrandMenu();
  } else {
    closeBrandMenu();
  }
}

/* ------------------------------------------------------------------ Storage
   What is using disk space and what can be given back.  The server measures; this lists the items
   that were made by Yeufonic and can be made again, each with what it costs to remove, and removes
   the ones that are ticked after one more look. */
var STORAGE = { report: null };

function sizeText(bytes) {
  if (bytes === null || bytes === undefined) { return '?'; }
  var units = ['B', 'KB', 'MB', 'GB', 'TB'];
  var value = bytes, i = 0;
  while (value >= 1024 && i < units.length - 1) { value /= 1024; i += 1; }
  return (i < 2 ? Math.round(value) : value.toFixed(1)) + ' ' + units[i];
}

// Items that cost the person nothing they would notice: the ones the button ticks.
var STORAGE_FREE_IDS = ['working-copies', 'engine-uploads', 'engine-training-copies'];

async function openStorage() {
  $('settings-modal').classList.add('hidden');
  $('storage-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
  await loadStorage();
}

function closeStorage() {
  clearTimeout(STORAGE.timer);
  $('storage-modal').classList.add('hidden');
  document.body.style.overflow = '';
}

async function loadStorage() {
  $('storage-summary').textContent = 'Measuring… a large library takes a few seconds.';
  $('storage-result').textContent = '';
  try {
    STORAGE.report = await api('/api/storage');
    paintStorage();
  } catch (err) {
    $('storage-summary').textContent = 'Could not measure: ' + err.message;
  }
}

function paintStorage() {
  var report = STORAGE.report;
  if (!report) { return; }
  var total = report.areas.reduce(function (sum, area) { return sum + area.bytes; }, 0);
  var disk = report.disk && report.disk.free !== null
    ? ' The disk has ' + sizeText(report.disk.free) + ' free of ' + sizeText(report.disk.total) + '.' : '';
  $('storage-summary').textContent = 'Yeufonic is using ' + sizeText(total) + '.' + disk + ' ' +
    sizeText(report.reclaimable) + ' of it can be given back.';

  $('storage-items').innerHTML = report.items.length ? report.items.map(function (item) {
    if (item.kind === 'compress') {
      // Not ticked and removed with the rest: it converts in the background and says how far it has got.
      return '<div class="storage-item' + (item.blocked ? ' blocked' : '') + '"><span></span>' +
        '<span class="storage-title"><span>' + esc(item.title) + '</span><span class="storage-size">' +
          sizeText(item.bytes) + ' \u00b7 ' + item.files + ' files</span></span>' +
        '<p>' + esc(item.what) + ' It frees about ' + sizeText(item.saves) + '.</p><p><b>If you convert them:</b> ' + esc(item.consequence) + '</p>' +
        '<div class="storage-convert"><button type="button" id="storage-convert" class="ghost small"' +
          (item.blocked ? ' disabled data-blocked="1"' : '') + '>Convert to FLAC</button>' +
          '<button type="button" id="storage-convert-stop" class="ghost small hidden">Stop</button>' +
          '<span id="storage-convert-status" class="hint"></span></div>' +
        (item.blocked ? '<span class="storage-why">Not now: ' + esc(item.blocked) + '.</span>' : '') + '</div>';
    }
    return '<label class="storage-item' + (item.blocked ? ' blocked' : '') + '">' +
      '<input type="checkbox" data-item="' + esc(item.id) + '"' + (item.blocked ? ' disabled' : '') + '>' +
      '<span class="storage-title"><span>' + esc(item.title) + '</span><span class="storage-size">' +
        sizeText(item.bytes) + ' · ' + item.files + (item.files === 1 ? ' file' : ' files') + '</span></span>' +
      '<p>' + esc(item.what) + '</p>' +
      '<p><b>If you remove it:</b> ' + esc(item.consequence) + '</p>' +
      (item.blocked ? '<span class="storage-why">Not now: ' + esc(item.blocked) + '.</span>' : '') +
      '</label>';
  }).join('') : '<p class="hint">Nothing here can be given back at the moment.</p>';
  paintStorageSelection();
  pollCompress();

  var spec = (State.settingSpec || []).filter(function (item) { return item.section === 'storage'; });
  $('storage-auto').innerHTML = spec.map(function (item) {
    return '<div class="storage-auto-row"><label for="auto-' + esc(item.key) + '">' + esc(item.label) + '</label>' +
      '<select id="auto-' + esc(item.key) + '" data-storage-key="' + esc(item.key) + '">' +
      item.options.map(function (option) {
        return '<option value="' + esc(option.value) + '"' + (option.value === item.value ? ' selected' : '') + '>' +
          esc(option.label) + '</option>';
      }).join('') + '</select><p>' + esc(item.help || '') + '</p></div>';
  }).join('');

  var biggest = Math.max.apply(null, report.areas.map(function (a) { return a.bytes; }).concat([1]));
  $('storage-areas').innerHTML = report.areas.map(function (area) {
    return '<div class="storage-area"><span>' + esc(area.name) + '</span>' +
      '<span class="storage-bar"><i style="width:' + Math.max(1, Math.round(100 * area.bytes / biggest)) + '%"></i></span>' +
      '<span style="text-align:right">' + sizeText(area.bytes) + '</span><small>' + esc(area.note) + '</small></div>';
  }).join('');

  $('storage-corpora').innerHTML = report.corpora.length ?
    '<table class="storage-table"><tr><th>Corpus</th><th>Songs and vocals</th><th>Working copies</th>' +
    '<th>Training set</th><th>Checkpoints</th><th>Total</th></tr>' + report.corpora.map(function (c) {
      return '<tr><td>' + esc(c.name) + '</td><td>' + sizeText(c.songs) + '</td><td>' + sizeText(c.working_copies) +
        '</td><td>' + sizeText(c.training_set) + '</td><td>' + sizeText(c.checkpoints) + '</td><td>' +
        sizeText(c.songs + c.working_copies + c.training_set + c.checkpoints) + '</td></tr>';
    }).join('') + '</table>' : '<p class="hint">No corpora yet.</p>';
}

function storageChosen() {
  return Array.prototype.map.call(document.querySelectorAll('#storage-items input[data-item]:checked'),
    function (box) { return box.dataset.item; });
}

function paintStorageSelection() {
  var chosen = storageChosen();
  var items = (STORAGE.report && STORAGE.report.items) || [];
  var bytes = items.filter(function (i) { return chosen.indexOf(i.id) >= 0; })
    .reduce(function (sum, i) { return sum + i.bytes; }, 0);
  $('storage-reclaim').disabled = !chosen.length;
  $('storage-selected').textContent = chosen.length ? chosen.length + ' selected · ' + sizeText(bytes) : '';
}

async function reclaimStorage() {
  var chosen = storageChosen();
  var items = ((STORAGE.report && STORAGE.report.items) || []).filter(function (i) { return chosen.indexOf(i.id) >= 0; });
  if (!items.length) { return; }
  var total = items.reduce(function (sum, i) { return sum + i.bytes; }, 0);
  var message = 'Remove ' + items.length + (items.length === 1 ? ' item' : ' items') + ', ' + sizeText(total) + '?\n\n' +
    items.map(function (i) { return '• ' + i.title + ' (' + sizeText(i.bytes) + '): ' + i.consequence; }).join('\n\n') +
    '\n\nThis cannot be undone.';
  var yes = await confirmModal({ title: 'Remove these files?', message: message, confirmText: 'Remove', danger: true });
  if (!yes) { return; }
  $('storage-reclaim').disabled = true;
  try {
    var result = await api('/api/storage/reclaim', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids: chosen })
    });
    var text = 'Freed ' + sizeText(result.freed) + '.';
    if (result.skipped.length) {
      text += ' Left alone: ' + result.skipped.map(function (s) { return s.reason; }).join('; ') + '.';
    }
    await loadStorage();
    $('storage-result').textContent = text;
  } catch (err) {
    $('storage-result').textContent = 'Could not remove: ' + err.message;
    paintStorageSelection();
  }
}

/* Converting the vocals runs in the background, so this asks how far it has got until it ends. */
async function pollCompress() {
  clearTimeout(STORAGE.timer);
  var status = $('storage-convert-status');
  if (!status || $('storage-modal').classList.contains('hidden')) { return; }
  var state;
  try { state = await api('/api/storage/compress-vocals'); } catch (err) { return; }
  var running = state.state === 'running';
  $('storage-convert').disabled = running || $('storage-convert').dataset.blocked === '1';
  $('storage-convert-stop').classList.toggle('hidden', !running);
  if (running) {
    STORAGE.watching = true;      // one that finishes while this window is open is announced; an old result is not
    status.textContent = 'Converting ' + (state.done + 1) + ' of ' + state.total + '\u2026 ' + sizeText(state.saved) + ' saved so far.';
    STORAGE.timer = setTimeout(pollCompress, 2000);
  } else if ((state.state === 'done' || state.state === 'stopped') && STORAGE.watching) {
    STORAGE.watching = false;
    var text = (state.state === 'stopped' ? 'Stopped. ' : 'Done. ') + state.done + ' converted, ' +
      sizeText(state.saved) + ' saved' + (state.kept ? '; ' + state.kept + ' left as WAV because they did not check out' : '') + '.';
    await loadStorage();
    $('storage-result').textContent = text;
  } else if (state.state === 'failed') {
    status.textContent = 'Stopped by an error: ' + state.error;
  }
}

async function startCompress() {
  try {
    await api('/api/storage/compress-vocals', { method: 'POST' });
    STORAGE.watching = true;
    pollCompress();
  } catch (err) {
    $('storage-result').textContent = err.message;
  }
}

async function saveStorageSetting(select) {
  try {
    var data = await api('/api/settings', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: select.dataset.storageKey, value: select.value })
    });
    adoptSettings(data.settings);
    $('storage-result').textContent = 'Saved.';
  } catch (err) {
    $('storage-result').textContent = 'Could not save: ' + err.message;
  }
}

function wireStorage() {
  var open = $('open-storage');
  if (!open || !$('storage-modal')) { return; }
  open.addEventListener('click', openStorage);
  $('storage-close').addEventListener('click', closeStorage);
  $('storage-refresh').addEventListener('click', loadStorage);
  $('storage-reclaim').addEventListener('click', reclaimStorage);
  $('storage-free-ones').addEventListener('click', function () {
    Array.prototype.forEach.call(document.querySelectorAll('#storage-items input[data-item]'), function (box) {
      box.checked = !box.disabled && STORAGE_FREE_IDS.indexOf(box.dataset.item) >= 0;
    });
    paintStorageSelection();
  });
  $('storage-items').addEventListener('change', paintStorageSelection);
  $('storage-items').addEventListener('click', function (event) {
    if (event.target.id === 'storage-convert') { startCompress(); }
    if (event.target.id === 'storage-convert-stop') { api('/api/storage/compress-vocals/stop', { method: 'POST' }); }
  });
  $('storage-auto').addEventListener('change', function (event) {
    if (event.target.dataset && event.target.dataset.storageKey) { saveStorageSetting(event.target); }
  });
  $('storage-modal').addEventListener('click', function (event) {
    if (backdropClick(event, $('storage-modal'))) { closeStorage(); }
  });
}

function openSettings() {
  closeBrandMenu();
  paintSettings();
  $('settings-note').textContent = '';
  $('settings-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
  if (setting('llm.provider') === 'external' && (!State.llmModels || !State.llmModels.length)) {
    fetchLLMModels(true);
  }
}

function closeSettings() {
  $('settings-modal').classList.add('hidden');
  var list = $('settings-list');
  if (list) { list.innerHTML = ''; }
  document.body.style.overflow = '';
}

/* ------------------------------------------------ lyrics from a recording */
/* Separating a vocal and listening to it takes minutes, so it is asked for, runs
   in the CPU lane beside stems, and shows how far along it is. A recording keeps
   what was heard, so asking twice costs nothing. */
var HEAR = { id: null, timer: 0 };

function paintHearButton() {
  var button = $('source-lyrics');
  if (!button) { return; }
  var source = currentSource();
  button.disabled = !source;
  // The label stays an instruction. "Lyrics heard" read as a status, and a
  // status is not something anyone thinks to press.
  button.title = !source ? 'Choose a recording first'
    : source.has_lyrics ? 'Put the words heard earlier in the box, and offer to hear them again'
    : 'Separate the vocal from this recording and write down what it sings. English recordings only: '
      + 'Whisper hears nothing else, and would write down nonsense.';
}

/* Auditioning the recording itself, through the player at the foot of the page.
   It is not a take, so it owns no score and no card. */
function playRecording() {
  var source = currentSource();
  if (!source) { return; }
  var isMidi = Boolean(source.filename && source.filename.match(/\.midi?$/i));
  var audio = $('audio');

  if (isMidi) {
    if (window.PianoRoll && window.PianoRoll.isPlaying) {
      window.PianoRoll.stop();
    }
    if (State.audition === source.id && !audio.paused) {
      audio.pause();
      State.audition = null;
      State.auditionLoading = false;
      paintAudition();
      return;
    }
    var sel = $('score-sf2-select');
    var activeSf2 = sel && sel.value ? sel.value : '';
    var sf2Param = activeSf2 ? '?sf2=' + encodeURIComponent(activeSf2) : '';
    var url = '/api/sources/' + source.id + '/rendered-audio' + sf2Param;
    var sfLabel = (sel && sel.selectedOptions && sel.selectedOptions[0])
      ? sel.selectedOptions[0].textContent
      : (activeSf2 ? activeSf2.replace(/_/g, ' ').replace(/\.sf2$/i, '') : 'SoundFont');

    State.loadedId = null;
    State.playing = null;
    State.audition = source.id;
    State.auditionLoading = true;
    State.playRequestedAt = Date.now();
    audio.src = url;
    audio.play().catch(function (err) {
      console.warn("MIDI audio audition play failed:", err);
      State.auditionLoading = false;
      paintAudition();
      statusLine("Could not play MIDI audio: " + (err.message || err), "bad");
    });
    $('np-title').textContent = source.title;
    $('np-meta').textContent = 'Synthesizing with ' + sfLabel + '…';
    $('np-cover').className = 'np-cover grad-cover';
    updateMediaSession({ title: source.title, style: 'MIDI Recording (' + sfLabel + ')' });
    statusLine('Preparing MIDI audio with ' + sfLabel + '…', 'hint');
    loadWave(url, '/api/sources/' + source.id + '/peaks' + sf2Param);
    paintTakes();
    paintAudition();
    return;
  }

  if (window.PianoRoll && window.PianoRoll.isPlaying) {
    window.PianoRoll.stop();
  }
  if (State.audition === source.id && !audio.paused) {
    audio.pause();
    State.audition = null;
    State.auditionLoading = false;
    paintAudition();
    return;
  }
  var url = '/api/sources/' + source.id + '/audio';
  State.loadedId = null;      // a recording is not a take, so Play must not resume one
  State.playing = null;
  State.audition = source.id;
  State.auditionLoading = false;
  State.playRequestedAt = Date.now();
  audio.src = url;
  audio.play().catch(function () {});
  $('np-title').textContent = source.title;
  $('np-meta').textContent = 'the recording being covered';
  $('np-cover').className = 'np-cover grad-cover';
  updateMediaSession({ title: source.title, style: 'the recording being covered' });
  loadWave(url, '/api/sources/' + source.id + '/peaks');
  paintTakes();
  paintAudition();
}

function paintAudition() {
  var button = $('audition');
  if (!button) { return; }
  var source = currentSource();
  var playing = Boolean(source && State.audition === source.id && !$('audio').paused);
  var loading = Boolean(source && State.audition === source.id && $('audio').paused && State.auditionLoading);
  button.disabled = !source || loading;
  button.title = !source ? 'Choose a recording first'
    : loading ? 'Synthesizing studio MIDI audio with SoundFont...'
    : playing ? 'Pause this recording'
    : 'Play this recording through the player, to hear what you are covering';
  button.classList.toggle('on', playing);
  button.classList.toggle('loading', loading);
  if (loading) {
    button.textContent = '⏳ Preparing…';
  } else if (playing) {
    button.textContent = '⏸ Audition';
  } else {
    button.textContent = 'Audition';
  }
}

function paintHearJob(state) {
  var box = $('lyrics-hear-job');
  var running = state && (state.state === 'queued' || state.state === 'running');
  box.classList.toggle('hidden', !running);
  box.classList.remove('bad');
  if (!running) { return; }
  $('lyrics-hear-bar').style.width = Math.round((state.progress || 0) * 100) + '%';
  $('lyrics-hear-stage').textContent = state.stage || 'Waiting';
}

/* A job that fails says so where the bar was, not only in the status line at the
   far end of the panel: a bar that stops at nought reads as a hang. */
function showHearError(message) {
  clearInterval(HEAR.timer);
  HEAR.timer = 0;
  HEAR.id = null;
  var box = $('lyrics-hear-job');
  box.classList.remove('hidden');
  box.classList.add('bad');
  $('lyrics-hear-bar').style.width = '100%';
  $('lyrics-hear-stage').textContent = message;
  paintHearButton();
  paintAudition();
}

async function useHeardLyrics(text) {
  var box = $('lyrics');
  // Another recording's words, as the app put them in, go without asking.
  if (box.value.trim() && !sameWords(box.value, text) && !sameWords(box.value, recordingWords())) {
    if (!await confirmModal({
      title: 'Replace lyrics',
      message: 'Replace the lyrics in the box with the words heard in the recording?',
      confirmText: 'Replace',
      danger: true
    })) { return; }
  }
  box.value = text;
  recordingWords(text);
  State.formEdited = true;
  saveForm();
  refreshTitleHint();
}

async function pollHear(id) {
  var state;
  try {
    state = await api('/api/sources/' + id + '/lyrics');
  } catch (err) {
    showHearError('Lost touch with the job: ' + err.message);
    return;
  }
  paintHearJob(state);
  if (state.state === 'done') {
    stopHearPoll();
    if (state.lyrics) { await useHeardLyrics(state.lyrics); }
    statusLine('Wrote down what the recording sings' + (state.method ? ', heard by ' + state.method : '') +
      '. Read it before you plan.', 'good');
    loadSources();
  } else if (state.state === 'failed') {
    showHearError(state.error === 'cancelled' ? 'Stopped.' : 'Could not hear the words: ' + (state.error || 'unknown'));
  }
}

function stopHearPoll() {
  clearInterval(HEAR.timer);
  HEAR.timer = 0;
  HEAR.id = null;
  paintHearJob(null);
  paintHearButton();
  paintAudition();
}

/* Which method a new extraction would use, as the server decides it: the external
   LLM only when Settings asks for it and an external LLM is the provider. */
function hearMethodNow() {
  var wanted = setting('lyrics.transcriber', 'whisper') === 'llm';
  var external = setting('llm.provider', 'local') === 'external';
  return wanted && external ? setting('llm.model', 'the external LLM') + ', timed by Whisper' : 'Whisper';
}

async function hearLyrics() {
  var source = currentSource();
  if (!source) { return; }
  // Words heard before go straight back in the box, which is often all that was
  // wanted.  But there are two ways to hear them now, so a second try is offered
  // rather than refused: the button used to stop here, and so looked dead.
  // By the words, not the state: a second try that failed or was stopped leaves the
  // first try's words in place, and they should still come back first.
  var state = await api('/api/sources/' + source.id + '/lyrics');
  var busy = state.state === 'queued' || state.state === 'running';
  if (state.lyrics && !busy) {
    await useHeardLyrics(state.lyrics);
    var before = state.method ? ' (heard by ' + state.method + ')' : '';
    if (!await confirmModal({
      title: 'Extract lyrics again',
      message: 'Lyrics already present' + before + '. Extract again with ' + hearMethodNow() + '?',
      confirmText: 'Extract again',
      danger: false
    })) {
      statusLine('These words were heard in the recording earlier.', 'good');
      return;
    }
  }
  await api('/api/sources/' + source.id + '/lyrics', { method: 'POST' });
  HEAR.id = source.id;
  paintHearJob({ state: 'queued', progress: 0, stage: 'Waiting' });
  clearInterval(HEAR.timer);
  HEAR.timer = setInterval(function () { pollHear(source.id); }, 1500);
}

/* ------------------------------------------------------------------- stems */
/* Builds the model and format lists, then the stem checkboxes for the chosen model.
   Preferred values come from Settings when the sheet opens, and are left alone when
   the user changes the model by hand. The lists must exist before a value is set on
   them, or the assignment is silently dropped. */
function paintStemChoices(preferred) {
  var options = State.stemsOptions || {};
  var models = options.models || [];
  var select = $('stems-model');
  var formatSelect = $('stems-format');
  var firstFill = select.dataset.filled !== '1';
  if (firstFill) {
    select.innerHTML = models.map(function (m) {
      return '<option value="' + esc(m.id) + '">' + esc(m.label) + '</option>';
    }).join('');
    formatSelect.innerHTML = (options.formats || ['wav']).map(function (f) {
      return '<option value="' + esc(f) + '">' + (f === 'mp3' ? 'mp3, 320 kbps' : esc(f)) + '</option>';
    }).join('');
    select.dataset.filled = '1';
  }
  if (preferred && preferred.model) {
    select.value = preferred.model;
  } else if (firstFill) {
    select.value = setting('stems.model', options.default_model || 'htdemucs');
  }
  if (preferred && preferred.format) {
    formatSelect.value = preferred.format;
  } else if (firstFill) {
    formatSelect.value = setting('stems.format', options.default_format || 'flac');
  }
  var chosen = null;
  for (var i = 0; i < models.length; i++) { if (models[i].id === select.value) { chosen = models[i]; } }
  if (!chosen) { chosen = models[0] || { stems: [] }; }
  var all = [];
  models.forEach(function (m) { m.stems.forEach(function (s) { if (all.indexOf(s) < 0) { all.push(s); } }); });
  // Beside the vocal it is the other half of.
  if (all.indexOf('instruments') > 1) { all.splice(all.indexOf('instruments'), 1); all.splice(1, 0, 'instruments'); }
  $('stems-list').innerHTML = all.map(function (name) {
    var on = chosen.stems.indexOf(name) >= 0;
    return '<label class="stem-choice' + (on ? '' : ' off') + '">' +
      '<input type="checkbox" value="' + esc(name) + '"' + (on ? ' checked' : ' disabled') + '> ' + esc(name) + '</label>';
  }).join('');
}

/* target: { kind: 'take' | 'source', id, title } */
function openStemsModal(target) {
  var options = State.stemsOptions || {};
  if (!options.available) {
    statusLine('Stem separation is not available in this container.', 'bad');
    return;
  }
  State.stemsTarget = target;
  $('stems-heading').textContent = 'Extract stems: ' + target.title;
  // Settings decide what a new run starts with; the sheet can still override.
  $('stems-dir').value = setting('stems.folder', options.default_dir || '/data/stems');
  paintStemChoices({
    model: setting('stems.model', options.default_model || 'htdemucs'),
    format: setting('stems.format', options.default_format || 'flac')
  });
  var estimate = options.avg_seconds
    ? 'The last run took ' + Math.round(options.avg_seconds) + ' seconds.'
    : 'A four minute song takes about three minutes.';
  $('stems-note').textContent = 'Runs on this machine on ' + (options.threads || 4) + ' CPU threads, so the GPU stays free for renders. ' + estimate;
  $('stems-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeStemsModal() {
  $('stems-modal').classList.add('hidden');
  document.body.style.overflow = '';
  State.stemsTarget = null;
}

async function runStems() {
  var target = State.stemsTarget;
  if (!target) { return; }
  var wanted = Array.prototype.slice.call($('stems-list').querySelectorAll('input:checked'))
    .map(function (box) { return box.value; });
  if (!wanted.length) {
    $('stems-note').textContent = 'Choose at least one stem.';
    return;
  }
  $('stems-run').disabled = true;
  try {
    var base = target.kind === 'source' ? '/api/sources/' : '/api/takes/';
    await api(base + target.id + '/stems', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: $('stems-model').value,
        stems: wanted,
        format: $('stems-format').value,
        save_dir: $('stems-dir').value
      })
    });
    closeStemsModal();
    loadTakes();
  } catch (err) {
    $('stems-note').textContent = 'Could not start: ' + err.message;
  } finally {
    $('stems-run').disabled = false;
  }
}

function playStem(setId, file) {
  var audio = $('audio');
  State.loadedId = null;   // a stem is not a take, so Play must not resume a take
  State.playing = null;
  State.audition = null;
  wave.kind = null;        // and it gets the neutral tone
  audio.src = '/api/stem-sets/' + setId + '/' + encodeURIComponent(file);
  audio.play().catch(function () {});
  $('np-title').textContent = file.replace(/\.[a-z0-9]+$/i, '');
  $('np-meta').textContent = 'stem from take ' + setId;
  $('np-cover').className = 'np-cover grad-cover';
  loadWave(audio.src, '/api/stem-sets/' + setId + '/' + encodeURIComponent(file) + '/peaks');
}

/* ---------------------------------------------------------------- save */
/* Asks for the format, starting from the one set in Settings; the server converts
   as it hands the file over. */
function openSaveModal(take) {
  State.saveTakeId = take.id;
  $('save-heading').textContent = 'Save \u201c' + take.title + '\u201d';
  pickSaveFormat(setting('stems.format', 'flac'));
  $('save-modal').classList.remove('hidden');
  $('save-run').focus();
}

function pickSaveFormat(format) {
  Array.prototype.forEach.call($('save-format').querySelectorAll('button'), function (b) {
    var on = b.dataset.format === format;
    b.classList.toggle('active', on);
    b.setAttribute('aria-checked', on ? 'true' : 'false');
  });
}

function closeSaveModal() {
  State.saveTakeId = null;
  $('save-modal').classList.add('hidden');
}

function runSave() {
  var id = State.saveTakeId;
  var chosen = $('save-format').querySelector('button.active');
  if (!id || !chosen) { return; }
  var link = document.createElement('a');
  link.href = '/api/takes/' + id + '/audio?download=1&format=' + chosen.dataset.format;
  link.download = '';
  document.body.appendChild(link);
  link.click();
  link.remove();
  closeSaveModal();
}

function statusLine(message, kind) {
  var node = $('render-status');
  if (node) {
    node.textContent = message || '';
    node.className = 'status' + (kind ? ' ' + kind : '');
  }
}

if (typeof window !== 'undefined') {
  window.toast = function (msg, kind) {
    statusLine(msg, kind || 'good');
  };
}

/* ---------------------------------------------------------------- harmony ---
   How predictable the chords of a score plan are. Each step is a setting of the
   engine's yue2_harmony node; the server holds the mapping, and these are only the
   words. Songs from a prompt only: a cover takes its chords from the recording. */
var HARMONY_WORDS = ['Familiar', 'Varied', 'Colourful', 'Adventurous', 'Outside'];
var HARMONY_HINTS = [
  'YuE2\u2019s own chords. Often one four-chord loop for the whole song.',
  'Avoids repeating the same chords. Stays in the key.',
  'Verse and chorus get different progressions, with richer chords.',
  'Keeps the harmony moving, and borrows chords from outside the key.',
  'Adventurous, and reaches further outside the key.'
];

function harmonyStep() {
  var step = parseInt($('harmony').value, 10);
  return isNaN(step) ? 0 : Math.max(0, Math.min(HARMONY_WORDS.length - 1, step));
}

function paintHarmony() {
  var available = State.options.harmony_available !== false;
  var step = harmonyStep();
  $('harmony').disabled = !available;
  $('harmony-word').textContent = HARMONY_WORDS[step];
  $('harmony-hint').textContent = available
    ? HARMONY_HINTS[step]
    : 'The engine has no harmony node. Rebuild the engine to use this.';
  if ($('style-lora') && $('style-lora').value) { paintStyleLoraNote(); }
}

function setMode(mode) {
  rememberSourceFor(State.mode, mode);
  State.mode = mode;
  Array.prototype.forEach.call(document.querySelectorAll('.modes .mode'), function (button) {
    button.classList.toggle('active', button.dataset.mode === mode);
  });
  var cover = mode === 'cover';
  var inst = mode === 'inst';
  var show = function (id, on) { $(id).style.display = on ? '' : 'none'; };
  // An instrumental can be played from a recording's score, as a cover is.
  show('cover-only', cover || inst);
  if ($('source-lyrics')) { show('source-lyrics', cover); }
  var sourceLabel = $('cover-only') ? $('cover-only').querySelector('label') : null;
  if (sourceLabel) { sourceLabel.textContent = inst ? 'From a recording (optional)' : 'Source recording'; }
  paintSourcePickerMenu();
  show('lyrics-write', mode === 'song');
  // It acts on a recording, so it lives with the recording's own buttons, which
  // the whole cover-only block already shows and hides.
  show('auto-wrap', !cover);
  // Both steer the score writer, which a cover never uses: its score is the transcription.
  show('harmony-field', !cover);
  show('variety-field', !cover);
  // A cover has no plan to write or render again, but its score can still be played as an instrumental.
  show('plan-actions', true);
  ['render-take', 'reroll'].forEach(function (id) { if ($(id)) { $(id).style.display = cover ? 'none' : ''; } });
  // An instrumental has no words and no voice; its structure takes the lyrics' place.
  show('lyrics-field', !inst);
  show('vocal-field', !inst);
  show('structure-field', inst);
  show('follow-wrap', State.mode === 'song');
  paintSongPlan();
  if (cover) { paintStructure(); }
  show('mode-field', !inst);
  $('headline').textContent = cover ? 'Cover a song' : (inst ? 'Write an instrumental' : 'Write a song');
  $('sub').textContent = cover
    ? 'Your own recording in. A new arrangement, new vocals, and an editable score out.'
    : inst ? 'Style and structure in. YuE2 writes the melody and the chords, then plays it with no vocal.'
    : 'Style and lyrics in. YuE2 writes the melody and the chords, then sings it.';
  $('score-label').textContent = cover ? 'Score' : 'Score plan';
  show('create-cover', cover);
  show('create-song', mode === 'song');
  show('create-inst', inst);
  var button = $('start-fresh');
  button.textContent = cover ? 'New cover' : (inst ? 'New instrumental' : 'New song');
  button.classList.remove('type-cover', 'type-song', 'type-inst');
  button.classList.add(inst ? 'type-inst' : (cover ? 'type-cover' : 'type-song'));
  refreshTitleHint();
  paintPresets();
  if (inst) {
    if (typeof paintInstSource === 'function') { paintInstSource(); } else { paintStructure(); }
    paintFeel();
    if ($('style-lora') && $('style-lora').value && $('style-lora-clip') && $('style-lora-clip').value === '1') {
      $('style-lora-clip').value = 0.6;
      paintStyleLoraStrengths();
    }
  }
  paintStyleLoraNote();
  var ownedByTake = Boolean(takeIdInEditor());
  if (cover) {
    claimEditorFor(null);
    $('score-badge').textContent = 'no score';
    $('score-badge').className = 'badge';
    paintSource();
  } else if (inst && currentSource()) {
    // Its recording's score, as a cover's: a song's plan must not stay in the box.
    claimEditorFor(null);
    paintSource();
  } else if (!ownedByTake) {
    // The editor held a transcription of an uploaded recording. A song must not reuse it.
    // Cleared by the app, not by anyone's edit, so nothing is left unsaved: without the
    // baseline going too, + Song asked whether to discard changes nobody had made.
    $('abc').value = '';
    scoreBaseline('');
    setSelection({});
    $('score-badge').textContent = 'no plan yet';
    $('score-badge').className = 'badge';
    setChart('');
    statusLine(inst ? 'Choose an instrument and structure to start an instrumental.' : 'Write a score plan to start a song from scratch.');
  }
  followRecordingCap();
  if (inst) { paintInstSource(); }
}

/* The working score and the take it belongs to survive a reload, so the render
   button still knows what it is rendering. */
function saveWorkingScore() {
  try {
    localStorage.setItem('yue2.abc', $('abc').value);
    localStorage.setItem('yue2.take', takeIdInEditor() || '');
  } catch (err) { /* private mode */ }
}

function loadWorkingScore() {
  var abc = null;
  var id = null;
  try {
    abc = localStorage.getItem('yue2.abc');
    id = localStorage.getItem('yue2.take');
  } catch (err) { return; }
  if (abc) { $('abc').value = abc; scoreBaseline(abc); }
  if (id) {
    // The box holds this take's score, and the form describes it.
    restoreSelection({ formTakeId: id, boxKind: 'take', boxId: id });
  }
}

/* Say why the buttons are unusable instead of doing nothing when clicked. */
/* The Save score button says when there is something to save, and says so when it
   has saved. The baseline is the text the editor last loaded or saved, so a plan
   that arrives from the engine counts as already saved. */
function scoreBaseline(text) {
  State.savedAbc = text || '';
  State.sectionsOriginal = '';
  if (State.mode === 'cover' && $('structure-body')) { paintStructure(); }
  if (State.mode === 'inst' && $('structure-body')) { paintInstSource(); }
  paintStructureNotice();
  paintScoreDirty();
}

function scoreIsDirty() {
  if (!State.savedAbc) { return false; }
  return ($('abc').value || '') !== State.savedAbc;
}

function paintScoreDirty() {
  var dirty = scoreIsDirty();
  ['save-score', 'score-save'].forEach(function (id) {
    var button = $(id);
    if (!button || button.dataset.confirming === '1') { return; }
    button.classList.toggle('needs-save', dirty);
    button.textContent = dirty ? (id === 'score-save' ? 'Save' : 'Save score') : 'Saved';
    button.title = dirty ? 'This score has changes that are not saved yet'
                         : 'No changes since the last save';
    button.disabled = !dirty;
  });
}

function confirmScoreSaved() {
  ['save-score', 'score-save'].forEach(function (id) {
    var button = $(id);
    if (!button) { return; }
    button.dataset.confirming = '1';
    button.classList.remove('needs-save');
    button.textContent = 'Saved';
    button.disabled = true;
    setTimeout(function () {
      delete button.dataset.confirming;
      paintScoreDirty();
    }, 1600);
  });
}

var scoreAutoSaveTimer = null;
function scheduleScoreAutoSave() {
  if (scoreAutoSaveTimer) { clearTimeout(scoreAutoSaveTimer); }
  if (!takeIdInEditor() && !(State.mode === 'cover' && currentSource())) { return; }
  scoreAutoSaveTimer = setTimeout(function () {
    if (scoreIsDirty()) {
      saveScore(true);
    }
  }, 1200);
}

async function saveScore(silent) {
  if (scoreAutoSaveTimer) { clearTimeout(scoreAutoSaveTimer); scoreAutoSaveTimer = null; }
  if (!scoreIsDirty()) { return true; }
  var takeId = takeIdInEditor();
  var source = currentSource();
  var url = takeId ? '/api/takes/' + takeId + '/score'
                   : (State.mode === 'cover' && source ? '/api/sources/' + source.id + '/score' : '');
  if (!url) {
    if (!silent) {
      statusLine(State.mode !== 'cover'
        ? 'A score plan is saved with its take. Write a score plan first.'
        : 'Choose a recording to save this score to.', 'bad');
    }
    return false;
  }
  var abcVal = $('abc').value;
  var oldBaseline = State.savedAbc;
  scoreBaseline(abcVal);
  var t = takeId ? takeById(takeId) : null;
  var oldTakeAbc = t ? t.abc : null;
  if (t) { t.abc = abcVal; }
  if (State.formTake && State.formTake.id === takeId) { State.formTake.abc = abcVal; }
  if (source && (!takeId || State.mode === 'cover')) { source.abc = abcVal; }
  confirmScoreSaved();
  paintScoreDirty();

  try {
    await api(url, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ abc: abcVal })
    });
    if (!silent) { statusLine('Score saved.', 'good'); }
    loadSources();
    loadTakes();
    return true;
  } catch (err) {
    scoreBaseline(oldBaseline);
    if (t) { t.abc = oldTakeAbc; }
    paintScoreDirty();
    statusLine('Could not save the score: ' + err.message, 'bad');
    return false;
  }
}

function setScoreActions() {
  var enabled = Boolean(takeIdInEditor());
  ['render-take', 'reroll', 'make-instrumental'].forEach(function (name) {
    var node = $(name);
    if (!node) { return; }
    node.disabled = !enabled;
    node.style.opacity = enabled ? '' : '0.45';
    node.style.cursor = enabled ? '' : 'not-allowed';
  });
  var fresh = enabled && wordsChanged();
  // Words with more sections than the tune has: the tune cannot sing them, so a new plan is written unless asked otherwise.
  var gap = fresh && State.mode === 'song' ? tuneGap() : null;
  var owner = scoreOwner();
  if (gap && owner && State.gapSeen !== owner.id) {
    State.gapSeen = owner.id;
    if ($('keep-tune')) { $('keep-tune').checked = false; }
  }
  if (!gap) { State.gapSeen = null; }
  if ($('keep-tune-note')) {
    $('keep-tune-note').classList.toggle('hidden', !gap);
    if (gap) {
      $('keep-tune-note').textContent = $('keep-tune') && $('keep-tune').checked ? gap.keep : gap.fresh;
    }
  }
  var keep = keepTune();
  $('render-take').textContent = fresh ? 'Sing with new words' : 'Render this score';
  // Already an instrumental: nothing to make.
  if ($('make-instrumental')) { $('make-instrumental').style.display = State.mode === 'inst' ? 'none' : ''; }
  // The switch is for a song: its main button would otherwise write a new tune.
  if ($('words-changed')) { $('words-changed').classList.toggle('hidden', !(fresh && State.mode === 'song')); }
  $('create-song').textContent = keep ? 'Sing with new words' : 'Write score plan';
  if ($('auto-wrap')) { $('auto-wrap').style.visibility = keep ? 'hidden' : ''; }
  $('score-note').textContent = !enabled
    ? 'Nothing to render yet. Write a score plan, or press Score on a take in the library.'
    : (State.mode === 'cover'
      ? 'Make an instrumental plays this score on an instrument, with no voice, in a new take; the cover stays as it is.'
      : (fresh
        ? 'The words have changed. Sing with new words keeps this score\'s tune and makes a new take; the original stays as it is.'
        : 'Render this score makes audio from the score above, keeping its melody and chords. Write a new plan asks YuE2 for a different melody, same words.'));
}

/* Changed words on a song with a score, and Keep this tune ticked: the main button
   sings the score with them rather than writing a new plan. A page from before the
   switch had a button in its place, which does the same. */
function keepTune() {
  if (State.mode !== 'song' || !wordsChanged()) { return false; }
  return !$('keep-tune') || $('keep-tune').checked;
}

/* Everything the editor shows that a render uses, so a render is made from what is
   on screen rather than from what the take last had. */
function editorRenderSettings() {
  var data = withStyleLora({
    style: $('style').value,
    max_duration: parseFloat($('max-duration').value) || 360,
    mode: $('mode').value,
    seed: pickSeed(),
    interpretation: $('interpretation').value,
    realaudio: $('realaudio').checked, normalise: normaliseWanted()
  });
  if ($('style-lora') && !data.style_lora) {
    // None, chosen from a list that holds the take's LoRA, turns it off. A list
    // without it, not loaded yet or with the file gone, is no choice at all.
    var had = (scoreOwner() || {}).style_lora;
    var listed = had && Array.prototype.some.call($('style-lora').options, function (o) { return o.value === had; });
    if (!had || listed) { data.style_lora = ''; }
  }
  return withAdvancedSettings(data);
}

/* Same tune, new words. The planner reads every word before it writes a note, so a
   plan for changed words is a new tune. Sung to the score in the box instead, they
   keep this one: the take that owns the score, and whether the words have moved on. */
function scoreOwner() {
  var id = takeIdInEditor();
  if (!id) { return null; }
  return (State.takes || []).find(function (t) { return t.id === id; }) ||
    (State.formTake && State.formTake.id === id ? State.formTake : null);
}

/* How many sections the words ask for against how many the tune's score has, when the words ask for more. */
function tuneSectionGap() {
  var spans = scoreSectionSpans($('abc').value);
  var asked = String($('lyrics').value || '').split('\n').filter(function (line) { return /^\[[^\]]+\]\s*$/.test(line.trim()); }).length;
  return spans.length && asked > spans.length ? { asked: asked, have: spans.length } : null;
}

/* A rough count of the syllables in some lyrics: runs of vowels in each word, the silent final e left out.  Close enough to
   compare with the notes a tune has, which is all it is for. */
function lyricSyllables(text) {
  var total = 0;
  String(text || '').split('\n').forEach(function (line) {
    line = line.trim();
    if (!line || line.charAt(0) === '[' || /^title\s*:/i.test(line)) { return; }
    (line.toLowerCase().match(/[a-z']+/g) || []).forEach(function (word) {
      var base = word.length > 3 && !/(le|ee)$/.test(word) ? word.replace(/e$/, '') : word;
      total += Math.max(1, (base.match(/[aeiouy]+/g) || []).length);
    });
  });
  return total;
}

/* Why the take's tune cannot sing the words in the box, if it cannot: more sections than it has, or far more
   syllables than it has notes (long lines on a tune made for short ones).  Songs written to fit run at about
   one syllable to a note; well beyond that the lines are repeated or dropped. */
function tuneGap() {
  var sections = tuneSectionGap();
  if (sections) {
    return { keep: 'Your words have ' + sections.asked + ' sections and this tune has ' + sections.have + '. Keeping the tune sings only the first ' + sections.have + '.',
             fresh: 'Your words have ' + sections.asked + ' sections and this tune has ' + sections.have + '. A new plan is written, so all of them are used.' };
  }
  var notes = vocalNotes($('abc').value);
  var syllables = lyricSyllables($('lyrics').value);
  if (notes >= 20 && syllables >= 40 && syllables > notes * 1.8) {
    var about = Math.round(syllables / 10) * 10;
    return { keep: 'Your words need about ' + about + ' syllables and this tune has ' + notes + ' notes, so it cannot sing them all: expect repeated or dropped lines.',
             fresh: 'Your words need about ' + about + ' syllables and this tune has ' + notes + ' notes. A new plan is written to fit them.' };
  }
  return null;
}

function wordsChanged() {
  var take = scoreOwner();
  if (!take || take.kind === 'instrumental' || State.mode === 'inst') { return false; }
  if (($('abc').value || '').trim().length <= 50) { return false; }
  var norm = function (text) { return (text || '').replace(/\r\n/g, '\n').trim(); };
  var words = norm($('lyrics').value);
  return Boolean(words) && words !== norm(take.lyrics);
}

async function doSingNewWords() {
  var take = scoreOwner();
  if (!take) { statusLine('Nothing to sing yet. Write a score plan first.', 'bad'); return; }
  var payload = editorRenderSettings();
  payload.lyrics = $('lyrics').value;
  payload.brief = $('write-brief') ? $('write-brief').value.trim() : undefined;
  payload.abc = $('abc').value;
  payload.title = $('title').value.trim();
  try {
    var made = await api('/api/takes/' + take.id + '/words', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    // The form now describes the new take, which owns the score and the words.
    State.formTake = { id: made.id, kind: take.kind, lyrics: payload.lyrics, abc: payload.abc };
    $('title').value = made.title;
    scoreBaseline($('abc').value);
    setSelection({ formTakeId: made.id, boxKind: 'take', boxId: made.id });
    State.formEdited = false;
    saveForm();
    statusLine('Singing the same tune with the new words\u2026');
    loadTakes();
    closeEditor();
  } catch (err) {
    statusLine('Could not sing: ' + err.message, 'bad');
  }
}

function syncEditor() {
  saveWorkingScore();
  setScoreActions();
}

/* Which take owns the score currently in the box.  A take we are still waiting on
   does NOT own it: there is nothing to render until its score arrives. */
function takeIdInEditor() {
  return scoreTakeId() || selectedTakeId() || (State.formTake ? State.formTake.id : '') || '';
}

function claimEditorFor(takeId) {
  setSelection({ formTakeId: takeId || null, boxKind: takeId ? 'take' : 'none', boxId: takeId || null });
}

function stopAwaiting() {
  if (!Selection.awaiting) { return; }
  setSelection({ formTakeId: Selection.formTakeId, boxKind: Selection.boxKind, boxId: Selection.boxId });
}

async function watchPlan() {
  var waiting = awaitingPlanId();
  if (!waiting) { return; }
  var take;
  try {
    take = await api('/api/takes/' + waiting);
  } catch (err) {
    stopAwaiting();
    return;
  }
  if (take.abc && take.abc.length > 50 && scoreTakeId() !== take.id) {
    $('abc').value = take.abc;
    scoreBaseline(take.abc);
    // The plan is here, so the take owns the box from now on.
    setSelection({ formTakeId: take.id, boxKind: 'take', boxId: take.id });
    $('score-badge').textContent = 'plan ready';
    $('score-badge').className = 'badge ok';
    $('score-box').open = true;
    setChart(chordChart(take.abc));
    showPlanLength(take.abc);
    statusLine('Plan ready. Edit it, or press render.', 'good');
    loadTakes();
    return;
  }
  if (take.status === 'failed') {
    statusLine('Plan failed: ' + (take.error || 'unknown error'), 'bad');
    stopAwaiting();
    loadTakes();
  } else if (take.status === 'planned' || take.status === 'done') {
    // It finished between two polls: if the box never received the plan, it is
    // still on the take, and the call above will have filled it.
    stopAwaiting();
    loadTakes();
  }
}

/* The seed field's value when it is fixed, else a new one, shown in the field. */
function pickSeed() {
  var seed = parseInt($('seed').value, 10);
  if (!($('seed-fixed').checked) || isNaN(seed)) {
    seed = Math.floor(Math.random() * 4294967295);
    $('seed').value = seed;
  }
  return seed;
}

function songProblem() {
  return $('lyrics').value.trim() ? '' : 'Write some lyrics first. The planner needs words to shape the melody.';
}

function songBody(seed) {
  return withAdvancedSettings(withStyleLora({
    title: $('title').value.trim() || guessTitle($('lyrics').value),
    style: $('style').value,
    lyrics: $('lyrics').value,
    brief: $('write-brief') ? $('write-brief').value.trim() || null : null,
    seed: seed,
    interpretation: $('interpretation').value,
    max_duration: parseFloat($('max-duration').value) || 360,
    auto_render: $('auto-render').checked,
    variety: $('variety').value,
    harmony: harmonyStep(),
    space_id: State.spaceId,
    realaudio: $('realaudio').checked, normalise: normaliseWanted()
  }));
}

async function doPlan() {
  if (keepTune()) { await doSingNewWords(); return; }
  var problem = songProblem();
  if (problem) { statusLine(problem, 'bad'); return; }
  var seed = pickSeed();
  statusLine('Queued…');
  try {
    var take = await api('/api/songs', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(songBody(seed))
    });
    setSelection({ formTakeId: take.id, boxKind: 'none', boxId: null, awaiting: take.id });
    statusLine('Writing the score plan…');
    loadTakes();
    editorAfterPlan();
  } catch (err) {
    statusLine('Could not start: ' + err.message, 'bad');
  }
}

/* Render this score: a take that already has audio gets a new take beside it, so a render never
   overwrites one that may be worth keeping.  A take with no audio yet is filled in. */
async function doRenderTake() {
  var take = scoreOwner();
  if (!take || take.status !== 'done' || take.kind === 'cover' || wordsChanged()) { await renderInPlace(); return; }
  var payload = editorRenderSettings();
  payload.abc = $('abc').value;
  payload.title = $('title').value.trim();
  try {
    var made = await api('/api/takes/' + take.id + '/rearrange', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    setSelection({ formTakeId: made.id, boxKind: 'take', boxId: made.id });
    statusLine('Rendering\u2026');
    loadTakes();
    closeEditor();
  } catch (err) {
    statusLine('Could not render: ' + err.message, 'bad');
  }
}

async function renderInPlace() {
  var id = takeIdInEditor();
  if (!id) {
    statusLine('Nothing to render yet. Write a score plan first.', 'bad');
    $('score-note').textContent = 'Nothing to render yet. Write a score plan, or press Score on a take in the library.';
    return;
  }
  if (wordsChanged()) { await doSingNewWords(); return; }
  try {
    await api('/api/takes/' + id + '/score', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ abc: $('abc').value })
    });
    var payload = editorRenderSettings();
    await api('/api/takes/' + id + '/render', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    setSelection({ formTakeId: takeIdInEditor() || selectedTakeId(), boxKind: 'take', boxId: takeIdInEditor() || selectedTakeId() });
    statusLine('Rendering…');
    loadTakes();
    closeEditor();
  } catch (err) {
    statusLine('Could not render: ' + err.message, 'bad');
  }
}

/* A new plan is on its way for this take.  The old score leaves the box and the
   take gives up the editor, so watchPlan loads the new plan when it lands instead
   of treating the old one as current. */
function awaitNewPlan(id) {
  $('abc').value = '';
  scoreBaseline('');
  // The take is what the form describes, but it owns nothing until the plan lands.
  setSelection({ formTakeId: id, boxKind: 'none', boxId: null, awaiting: id });
  $('score-badge').textContent = 'writing a new plan';
  $('score-badge').className = 'badge';
  setChart('');
  showPlanLength('');
}

async function doMakeInstrumental() {
  var id = takeIdInEditor();
  if (!id) {
    statusLine('Nothing to make an instrumental of yet. Write a score plan first.', 'bad');
    return;
  }
  try {
    // The score as the box has it, without saving it over the original's.
    await api('/api/takes/' + id + '/instrumental', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ abc: $('abc').value })
    });
    statusLine('Making the instrumental\u2026', 'good');
    loadTakes();
    closeEditor();
  } catch (err) {
    statusLine('Could not make it: ' + err.message, 'bad');
  }
}

async function doReroll() {
  var id = takeIdInEditor();
  if (!id) { statusLine('Nothing to replan yet.', 'bad'); setScoreActions(); return; }
  try {
    // The slider and the variety menu apply to the new plan.
    var payload = withAdvancedSettings({ harmony: harmonyStep(), variety: $('variety').value });
    await api('/api/takes/' + id + '/replan', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    awaitNewPlan(id);
    statusLine('Writing a new plan for the same words\u2026');
    loadTakes();
  } catch (err) {
    statusLine('Could not replan: ' + err.message, 'bad');
  }
}

/* ------------------------------------------------------------------ takes */
async function loadTakes() {
  var space = State.spaceId, search = State.search, everywhere = searchingEverywhere();
  var url = '/api/takes?limit=' + State.takeLimit +
    (everywhere ? '' : '&space_id=' + encodeURIComponent(space)) +
    (search ? '&q=' + encodeURIComponent(search) : '') +
    (State.filter === 'favourite' ? '&favourite=true' : '') +
    (State.kinds && State.kinds.length ? '&kinds=' + State.kinds.join(',') : '');
  var response = await fetch(url, { cache: 'no-cache' });   // revalidates: unchanged is a 304
  if (!response.ok) { return; }
  var text = await response.text();
  // The space or the search changed while this was on its way: the answer is out of date.
  if (space !== State.spaceId || search !== State.search || everywhere !== searchingEverywhere()) { return; }
  if (text !== State.takesRaw) { loadSpaces(); }   // the counts in the menu may have moved
  State.takesAt = Date.now();
  State.takesTotal = parseInt(response.headers.get('X-Total-Count') || '0', 10) || 0;
  paintSearchCount();
  if (State.rememberWhenFound === search) {
    if (State.takesTotal) { rememberSearch(search); }
    State.rememberWhenFound = '';
  }
  // Nothing new: leave the cards alone, so hover, focus and the play pulse survive.
  // Repaint once a minute anyway, so "2 min ago" keeps moving.
  if (text === State.takesRaw && Date.now() - State.paintedAt < 60000) { return; }
  State.takesRaw = text;
  State.takes = JSON.parse(text);
  paintTakes();
  if (!State.loadedId && !State.audition && !State.playing && typeof activateTakeRecording === 'function') {
    var activeTake = typeof selectedTakeId === 'function' && selectedTakeId() && typeof takeById === 'function' ? takeById(selectedTakeId()) : null;
    if (activeTake) {
      activateTakeRecording(activeTake);
    }
  }
}

/* ----------------------------------------------------------------- spaces
   Each take lives in one space. Which space is on show is this browser's choice. */
async function loadSpaces() {
  var spaces = await api('/api/spaces');
  State.spaces = spaces;
  if (!spaces.some(function (space) { return space.id === State.spaceId; })) {
    showSpace('default');   // deleted elsewhere, or never existed here
  }
  paintSpaces();
}

function currentSpace() {
  return State.spaces.filter(function (space) { return space.id === State.spaceId; })[0] || null;
}

function paintSpaces() {
  var select = $('space');
  var html = State.spaces.map(function (space) {
    return '<option value="' + esc(space.id) + '">' + esc(space.name) + ' (' + space.takes + ')</option>';
  }).join('');
  if (select.dataset.html !== html) {
    select.innerHTML = html;
    select.dataset.html = html;
  }
  select.value = State.spaceId;
  $('space-delete').disabled = State.spaceId === 'default';
  paintTakesHeading();
}

function paintTakesHeading() {
  var space = currentSpace();
  $('takes-heading').textContent = searchingEverywhere() ? 'All spaces' : (space ? space.name : 'Your takes');
}

function showSpace(id) {
  if (id === State.spaceId) { return; }
  State.spaceId = id;
  try { localStorage.setItem(SPACE_KEY, id); } catch (err) { /* private mode */ }
  State.takes = [];
  State.takesRaw = '';
  State.takesTotal = 0;
  State.takeLimit = 300;
  clearPicked();          // a pick belongs to the space it was made in
  paintSpaces();
  paintTakes();
  loadTakes();
}

function loadSpaceChoice() {
  try { State.spaceId = localStorage.getItem(SPACE_KEY) || 'default'; } catch (err) { State.spaceId = 'default'; }
}

async function newSpace() {
  var name = await confirmModal({
    title: 'New space',
    message: 'Name the new space:',
    input: true,
    confirmText: 'Create space'
  });
  if (name === null || !name.trim()) { return; }
  try {
    var space = await api('/api/spaces', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: name.trim() })
    });
    State.spaces.push(space);
    showSpace(space.id);
    await loadSpaces();
    statusLine('New space ' + space.name + '. Takes you create now land here.', 'good');
  } catch (err) {
    statusLine('Could not create the space: ' + err.message, 'bad');
  }
}

async function renameSpace() {
  var space = currentSpace();
  if (!space) { return; }
  var name = await confirmModal({
    title: 'Rename space',
    message: 'Rename the space:',
    input: true,
    defaultValue: space.name,
    confirmText: 'Rename'
  });
  if (name === null || !name.trim() || name.trim() === space.name) { return; }
  try {
    await api('/api/spaces/' + space.id, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: name.trim() })
    });
    await loadSpaces();
  } catch (err) {
    statusLine('Could not rename the space: ' + err.message, 'bad');
  }
}

async function deleteSpace() {
  var space = currentSpace();
  if (!space || space.id === 'default') { return; }
  var held = space.takes ? ' Its ' + space.takes + ' take' + (space.takes === 1 ? '' : 's') + ' move to Default.' : '';
  if (!await confirmModal({
    title: 'Delete space',
    message: 'Delete the space \u201c' + space.name + '\u201d?' + held,
    confirmText: 'Delete',
    danger: true
  })) { return; }
  try {
    await api('/api/spaces/' + space.id, { method: 'DELETE' });
    showSpace('default');
    await loadSpaces();
  } catch (err) {
    statusLine('Could not delete the space: ' + err.message, 'bad');
  }
}

function openMoveModal(take) {
  State.moveTakeId = take.id;
  $('move-heading').textContent = 'Move \u201c' + take.title + '\u201d to';
  $('move-name').value = '';
  $('move-status').textContent = '';
  $('move-list').innerHTML = State.spaces.map(function (space) {
    var here = space.id === take.space_id;
    return '<button class="ghost" data-space="' + esc(space.id) + '"' + (here ? ' disabled' : '') + '>' +
      '<span>' + esc(space.name) + '</span><span class="muted">' +
      (here ? 'here now' : space.takes + ' take' + (space.takes === 1 ? '' : 's')) + '</span></button>';
  }).join('');
  $('move-modal').classList.remove('hidden');
}

function closeMoveModal() {
  State.moveTakeId = null;
  $('move-modal').classList.add('hidden');
}

async function moveTake(spaceId) {
  var id = State.moveTakeId;
  if (!id) { return; }
  var moved = await api('/api/takes/' + id + '/move', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ space_id: spaceId })
  });
  closeMoveModal();
  statusLine('Moved to ' + moved.name + '.', 'good');
  loadTakes();
  loadSpaces();
}

/* Style presets: songs name a voice, instrumentals name the lead instrument. */
var PRESETS = {
  vocal: [
    'English, warm indie rock, expressive male vocal, guitars, bass, drums, 110 BPM',
    'English, soulful jazz-pop, expressive male vocal, Rhodes, upright bass, brushed drums, 88 BPM',
    'English, synthwave, female vocal, analog pads, gated drums, 100 BPM',
    'English, acoustic ballad, intimate vocal, fingerpicked guitar, strings',
    'English, heavy rock, gritty male vocal, distorted guitars, driving drums',
    'English, modern pop, bright female vocal, punchy drums, synth bass, catchy hooks, 118 BPM',
    'English, country, warm male vocal, acoustic guitar, pedal steel, upright bass, brushed drums, 96 BPM',
    'English, hip hop, rhythmic male rap vocal, heavy 808 bass, crisp hi-hats, dark piano loop, 90 BPM',
    'English, smooth R&B, silky female vocal, electric piano, deep bass, laid-back drums, 78 BPM',
    'English, dance pop, energetic female vocal, four-on-the-floor kick, bright synths, pumping bass, 124 BPM'
  ],
  inst: [
    'cinematic, ambient, piano, strings, slow build, 70 BPM',
    'lo-fi hip hop, Rhodes, vinyl crackle, mellow drums, 85 BPM',
    'surf rock, twangy lead guitar, spring reverb, driving drums, 160 BPM',
    'synthwave, analog synth lead, arpeggios, gated drums, 110 BPM',
    'jazz trio, piano, upright bass, brushed drums, swing, 120 BPM',
    'acoustic pop, strummed acoustic guitar, piano, warm bass, light drums, 96 BPM',
    'piano ballad, grand piano, soft strings, gentle, emotional, 66 BPM',
    'rock band, electric guitars, bass guitar, punchy drums, driving, 128 BPM',
    'worship ballad, piano, ambient pads, electric guitar swells, building drums, 72 BPM',
    'country, acoustic guitar, pedal steel, fiddle, brushed drums, 104 BPM',
    'funk, slap bass, clean rhythm guitar, horn section, tight drums, 108 BPM',
    'blues, electric guitar, Hammond organ, bass, shuffle drums, 92 BPM',
    'reggae, offbeat guitar, deep bass, organ, one drop drums, 76 BPM',
    'dance, four-on-the-floor kick, synth bass, bright synth lead, 124 BPM',
    'orchestral, full orchestra, strings, brass, timpani, epic, 90 BPM'
  ]
};

/* Canned styles dropdown: 200 styles alphabetized by short name. */
var CANNED_STYLES = [
  {
    name: '80s synth-pop',
    prompt: '1980s Synth-Pop, new romantic pop, shimmering analog synth leads, punchy drum machine, pulsing sequenced bassline, glossy chorus-drenched pads, neon nostalgic mood, 118 BPM, yearning melodic male vocals'
  },
  {
    name: '90s r&b',
    prompt: '90s R&B, new jack swing, smooth synth bass, snappy programmed drums, lush keyboard pads, silky guitar licks, sleek romantic groove, 96 BPM, soulful layered female vocals with ad-libs'
  },
  {
    name: 'acid jazz',
    prompt: 'Acid Jazz, groove-driven jazz-funk, warm Hammond organ, wah-wah rhythm guitar, fat round bass, crisp breakbeat drums, tight horn stabs, cool urban swagger, 105 BPM, smooth soulful male vocals'
  },
  {
    name: 'adult contemporary',
    prompt: 'Adult Contemporary, polished soft pop, warm electric piano, clean acoustic guitar, gentle string pads, restrained drums, heartfelt romantic mood, 84 BPM, smooth sincere female vocals'
  },
  {
    name: 'afro house',
    prompt: 'Afro House, deep house with African percussion, rolling congas and shakers, warm sub-bass, hypnotic chord stabs, sunset dancefloor vibe, 120 BPM, chanted soulful vocal phrases'
  },
  {
    name: 'afro trap',
    prompt: 'Afro Trap, trap with African rhythm, log-drum bass, bright guitar plucks, rolling hi-hats, shaker percussion, sunny late-night mood, 130 BPM, autotuned melodic male vocals in French'
  },
  {
    name: 'afro-cuban jazz',
    prompt: 'Afro-Cuban Jazz, salsa fusion, energetic conga and bongo tumbao, intricate montuno piano riffs, blazing trumpet solos, tight walking upright bass, vibrant 130 BPM, rhythmic Spanish vocal improvisations'
  },
  {
    name: 'afrobeats',
    prompt: 'Afrobeats, West African dance-pop, syncopated log-drum percussion, melodic kalimba accents, warm sub-bass, buoyant infectious groove, 104 BPM, auto-tuned smooth male vocals'
  },
  {
    name: 'alt-country',
    prompt: 'Alt-Country, Americana, jangly electric guitar, weeping pedal steel, rootsy upright bass, shuffling drums, wistful dusty mood, 100 BPM, raspy heartfelt male vocals'
  },
  {
    name: 'alternative hip-hop',
    prompt: 'Alternative Hip-Hop, left-field production, off-kilter sampled loops, warm tape-saturated drums, quirky synth bass, playful experimental mood, 94 BPM, laid-back offbeat male rap vocals'
  },
  {
    name: 'alternative rock',
    prompt: '90s Alternative Rock, guitar-driven rock, crunchy distorted guitars, melodic bass, dynamic loud-quiet drums, restless moody energy, 124 BPM, earnest raw male vocals'
  },
  {
    name: 'amapiano',
    prompt: 'South African Amapiano, deep house fusion, iconic resonant log-drum basslines, airy piano keys, syncopated shaker percussion, lounge club vibe, hypnotic 113 BPM, smooth soulful Zulu vocal phrases'
  },
  {
    name: 'ambient drone',
    prompt: 'Ambient Drone, dark ambient, massive evolving synthesizer textures, subterranean sub-bass rumbles, bowed acoustic instruments, zero-tempo, meditative vast atmosphere, wordless distant female vocal chants'
  },
  {
    name: 'arena rock',
    prompt: 'Arena Rock, stadium anthem, soaring layered guitars, big gated drums, driving bass, shimmering synth pads, singalong chorus, 118 BPM, powerful soaring male vocals'
  },
  {
    name: 'bachata',
    prompt: 'Bachata, Dominican romantic guitar music, bright arpeggiated lead guitar, rounded bass, bongo and guira percussion, sensual dance mood, 130 BPM, passionate tender male vocals'
  },
  {
    name: 'baile funk',
    prompt: 'Rio Baile Funk, favela funk, syncopated tamborzão beat pattern, distorted vocal horn stabs, booming sub-bass punches, raw DIY street party chaos, high-energy 130 BPM, rhythmic Portuguese call-and-response MC chants'
  },
  {
    name: 'baroque pop',
    prompt: 'Baroque Pop, chamber pop, harpsichord runs, lush string quartet, gentle timpani, sophisticated brass flourishes, whimsical theatrical mood, 112 BPM, theatrical warm tenor vocals'
  },
  {
    name: 'bass house',
    prompt: 'Bass House, club bass music, growling mid-bass wobbles, thumping four-on-the-floor kick, snappy claps, sharp sub-drops, sweaty club energy, 126 BPM, chopped vocal shouts'
  },
  {
    name: 'bebop',
    prompt: 'Bebop, fast small-group jazz, blazing saxophone and trumpet unison lines, walking upright bass, swinging ride cymbal, angular piano comping, smoky late-night energy, 200 BPM, agile scat vocal improvisation'
  },
  {
    name: 'bedroom pop',
    prompt: 'Bedroom Pop, lo-fi indie pop, dreamy detuned guitar, soft drum machine, warm tape-saturated bass, intimate hushed production, cozy introspective mood, 92 BPM, breathy whispered female vocals'
  },
  {
    name: 'big room edm',
    prompt: 'Big Room EDM, festival main stage, massive supersaw drops, pumping sidechained kick, rising white-noise risers, huge snare builds, euphoric crowd energy, 128 BPM, anthemic processed female vocals'
  },
  {
    name: 'black metal',
    prompt: 'Second-Wave Black Metal, atmospheric raw black metal, relentless tremolo-picked minor chord guitars, icy blast-beat drums, freezing lo-fi production, misanthropic bleak mood, frantic 180 BPM, high-pitched shrieking male vocals'
  },
  {
    name: 'blues rock',
    prompt: 'Blues Rock, electric blues-rock, overdriven guitar riffs and bending solos, growling Hammond organ, thick bass, heavy shuffling drums, sweaty barroom energy, 108 BPM, gritty powerful male vocals'
  },
  {
    name: 'bolero',
    prompt: 'Bolero, Latin romantic ballad, nylon string guitar arpeggios, soft bongo and maracas, warm upright bass, gentle string swells, candlelit slow-dance mood, 72 BPM, tender velvety male vocals in Spanish'
  },
  {
    name: 'bollywood',
    prompt: 'Bollywood Pop, Hindi film music, lush sweeping strings, tabla and dholak rhythms, sitar and bansuri accents, glossy synth bass, colourful romantic mood, 110 BPM, expressive melodic female vocals'
  },
  {
    name: 'boom bap',
    prompt: '90s Boom Bap, East Coast hip-hop, dusty sampled drums, hard-hitting kick and snare, jazzy piano loop, deep upright bass sample, vinyl scratches, gritty confident mood, 92 BPM, sharp rhythmic male rap vocals'
  },
  {
    name: 'bossa nova',
    prompt: 'Bossa Nova, Brazilian jazz, classical nylon-string guitar, soft syncopated brushes on snare, upright acoustic bass, warm gentle flute, relaxing 95 BPM, intimate whispery Portuguese female vocals'
  },
  {
    name: 'breakcore',
    prompt: 'Breakcore, digital hardcore, chaotic hyper-chopped Amen breakbeats, abrupt rhythmic glitches, aggressive screeching acid bass, manic overload, blistering 200 BPM, frantic distorted vocal chops'
  },
  {
    name: 'britpop',
    prompt: 'Britpop, 90s British guitar pop, jangly bright guitars, melodic bassline, big singalong drums, chiming piano, cheeky anthemic mood, 116 BPM, nasal swaggering male vocals'
  },
  {
    name: 'bubblegum pop',
    prompt: 'Bubblegum Pop, bright teen pop, sparkling synths, bouncy programmed drums, handclaps, sugary hooks, carefree sunny mood, 120 BPM, sweet cheerful female vocals'
  },
  {
    name: 'cabaret',
    prompt: 'Cabaret, 1930s theatrical chanson, tinkling upright piano, oompah bass, brushed snare, muted trumpet, sultry smoky club mood, 96 BPM, dramatic expressive female vocals'
  },
  {
    name: 'calypso',
    prompt: 'Trinidadian Calypso, Caribbean carnival, steel pan melodies, bright acoustic guitar, hand percussion, bouncing bassline, sunny playful mood, 118 BPM, witty rhythmic male vocals'
  },
  {
    name: 'carnival samba',
    prompt: 'Rio de Janeiro Samba Enredo, carnival batucada, massive surdo bass drums, ringing agogô bells, rattling tamborims, sweeping cavaquinho chords, explosive celebratory euphoria, high-energy 140 BPM, ecstatic Portuguese group vocal chants'
  },
  {
    name: 'celtic punk',
    prompt: 'Celtic Punk, folk punk, distorted electric power chords, fast tin whistle leads, raucous fiddle, pounding drum cadence, rowdy tavern energy, 155 BPM, gravelly gang-chorus male vocals'
  },
  {
    name: 'chicago blues',
    prompt: 'Chicago Blues, electric city blues, slide guitar, wailing blues harmonica, walking bass, shuffling backbeat drums, honky barrelhouse piano, smoky juke joint mood, 96 BPM, gravelly soulful male vocals'
  },
  {
    name: 'chicago drill',
    prompt: 'Drill Rap, dark trap, sliding pitch-bent 808 glides, sinister minor-key piano loops, rapid-fire hi-hat triplets, gritty street tension, aggressive 142 BPM, cold monotone rap delivery'
  },
  {
    name: 'children\'s song',
    prompt: 'Children\'s Song, playful nursery pop, bright ukulele, xylophone and glockenspiel, bouncy bass, simple clapping drums, cheerful singalong mood, 112 BPM, warm friendly female vocals with children\'s chorus'
  },
  {
    name: 'chillout lounge',
    prompt: 'Chillout Lounge, downtempo electronica, warm ambient pads, soft fingered bass, gentle brushed beat, soft Rhodes chords, relaxed sunset mood, 90 BPM, breathy ethereal female vocals'
  },
  {
    name: 'chiptune bitpop',
    prompt: '8-Bit Chiptune, tracker video-game pop, NES square-wave melodies, noisy 4-bit white-noise percussion, rapid arpeggiator chord runs, hyperactive retro nostalgia, upbeat 152 BPM, sweet glitched-out vocoder female vocals'
  },
  {
    name: 'chopped and screwed',
    prompt: 'Chopped and Screwed, Houston slowed-down hip-hop, syrupy pitched-down samples, heavy sub-bass, skipping record-scratch edits, hazy codeine-slow mood, 64 BPM, drawled deep male rap vocals'
  },
  {
    name: 'choral sacred',
    prompt: 'Sacred Polyphony, Renaissance choral, cavernous cathedral acoustic reverb, intricate counterpoint vocal lines, solemn transcendent peace, non-metric fluid tempo, pure unadorned mixed SATB choir'
  },
  {
    name: 'christmas',
    prompt: 'Classic Christmas, festive holiday pop, sleigh bells, warm orchestral strings, jazzy piano, gentle brushed drums, upright bass, cozy joyful mood, 100 BPM, warm crooning male vocals'
  },
  {
    name: 'city pop',
    prompt: '80s Japanese City Pop, funk-pop fusion, bright brass section, crisp slap bass, shimmering electric piano, breezy groove, 118 BPM, silky melodic female vocals'
  },
  {
    name: 'classic funk',
    prompt: 'Classic Funk, 70s groove, slap bass, choppy clean rhythm guitar, tight syncopated drums, punchy horn section, clavinet stabs, infectious dancefloor groove, 104 BPM, energetic call-and-response male vocals'
  },
  {
    name: 'classic rock',
    prompt: 'Classic Rock, 70s guitar rock, crunchy riffs, bluesy lead guitar, thumping bass, hard-hitting drums, Hammond organ swells, raw live energy, 122 BPM, powerful gritty male vocals'
  },
  {
    name: 'cloud rap',
    prompt: 'Cloud Rap, ethereal hip-hop, hazy reverb-soaked synth pads, slow trap hi-hats, deep 808 bass, dreamy sampled vocal chops, woozy drifting mood, 70 BPM, mumbled melodic male rap vocals'
  },
  {
    name: 'conscious rap',
    prompt: 'Conscious Rap, lyrical hip-hop, soulful sampled keys, warm round bass, crisp dusty breakbeats, reflective urgent mood, 88 BPM, introspective articulate male rap vocals'
  },
  {
    name: 'contemporary worship',
    prompt: 'Contemporary Worship, modern church anthem, shimmering delay guitars, ambient pads, steady piano chords, building drums, soaring dynamic crescendos, uplifting reverent mood, 74 BPM, earnest powerful vocals with congregation backing'
  },
  {
    name: 'cool jazz',
    prompt: 'Cool Jazz, 1950s West Coast jazz, muted trumpet, mellow tenor saxophone, light brushed drums, gentle walking bass, understated piano, relaxed sophisticated mood, 108 BPM, smooth understated male vocals'
  },
  {
    name: 'country bluegrass',
    prompt: 'Bluegrass, traditional Appalachian folk, lightning-fast banjo rolls, acoustic flatpicked guitar, rhythmic upright slap bass, lively fiddle leads, high-tempo 145 BPM, twangy high-lonesome male vocal harmonies'
  },
  {
    name: 'crunk',
    prompt: 'Crunk, Southern hip-hop club anthem, aggressive 808 kick, booming bass, repetitive synth stabs, hard snare claps, call-and-response chants, rowdy party energy, 76 BPM, shouted hype male vocals'
  },
  {
    name: 'dancehall',
    prompt: 'Dancehall, Jamaican digital riddim, hard punchy drum machine, deep bass pulses, skanking synth stabs, sparse dubby effects, sweaty sunny dance mood, 98 BPM, rhythmic patois male toasting'
  },
  {
    name: 'dark synthpop',
    prompt: 'Dark Synthpop, coldwave, icy analog synthesizers, punchy vintage LinnDrum beats, detached pulsing bassline, moody nocturnal dance aesthetic, driving 122 BPM, aloof melancholic female vocals'
  },
  {
    name: 'dark trap',
    prompt: 'Dark Trap, horror-tinged trap, ominous minor-key piano, distorted 808 bass, sparse hi-hats, eerie reverb stabs, menacing mood, 140 BPM, low menacing male rap vocals'
  },
  {
    name: 'death metal',
    prompt: 'Death Metal, brutal technical metal, down-tuned chugging riffs, rapid double-bass drums, blast beats, tremolo-picked guitar runs, dark crushing mood, 190 BPM, deep guttural growled male vocals'
  },
  {
    name: 'deathcore',
    prompt: 'Modern Deathcore, extreme metal, downtuned eight-string guitar chugs, massive drop-tune breakdowns, thunderous double-kick bass drums, terrifying oppressive heaviness, brutal 130 BPM, pig-squeal gutturals and demonic screams'
  },
  {
    name: 'deep house',
    prompt: 'Deep House, warm club music, soft Rhodes chords, round sub-bass, crisp hi-hats, steady four-on-the-floor kick, late-night smooth groove, 122 BPM, soulful airy female vocals'
  },
  {
    name: 'delta blues',
    prompt: 'Pre-War Delta Blues, country blues, slide resonator guitar in open tuning, rhythmic foot-stomping percussion, warm raw vinyl hiss, lonesome porch atmosphere, unhurried 80 BPM, raspy gravelly male holler'
  },
  {
    name: 'desert blues',
    prompt: 'Saharan Desert Blues, Tishoumaren, hypnotic interlocking electric guitar grooves, clapping rhythm, hand-percussion calabash, expansive barren landscape feel, meditative 108 BPM, soulful call-and-response Tuareg male vocals'
  },
  {
    name: 'desert rock',
    prompt: 'Desert Rock, stoner rock, fuzz-heavy drop-tuned guitar riffs, hypnotic groove, thunderous loose drumming, dry psychedelic atmosphere, 95 BPM, howling bluesy male vocals'
  },
  {
    name: 'disco funk',
    prompt: 'Nu-Disco, 70s funk revival, bouncy energetic slap bassline, chic rhythm guitar chops, lush string sweeps, soaring brass stabs, four-on-the-floor 122 BPM, vibrant falsetto male vocals'
  },
  {
    name: 'doo-wop',
    prompt: '1950s Doo-Wop, vocal group harmony, gentle triplet piano, soft upright bass, light brushed drums, finger snaps, wistful malt-shop romance, 76 BPM, tight smooth male vocal harmonies with falsetto lead'
  },
  {
    name: 'downtempo illbient',
    prompt: '90s Illbient, Brooklyn dark dub, sluggish vinyl-dusted hip-hop beat, heavily modulated sub-bass rumble, eerie turntable scratches, smoky industrial loft tension, gritty 78 BPM, murmuring spoken-word male voice'
  },
  {
    name: 'dreampop',
    prompt: 'Dream Pop, ethereal wave, lush chorus-soaked guitars, wash of analog synthesizer pads, delicate muted drum machine, hazy romantic daydream mood, slow-drifting 88 BPM, whispery reverb-drenched female vocals'
  },
  {
    name: 'drum and bass',
    prompt: 'Liquid Drum and Bass, jungle, fast rolling breakbeats at 174 BPM, deep sub-bass reese, ambient lush pads, soul-sampled piano chords, smooth soulful female vocals'
  },
  {
    name: 'dubstep',
    prompt: '2010s Brostep, heavy dubstep, aggressive screeching wavetable growl bass, punchy snare on the third beat, massive sub-bass drops, intense robotic violence, half-time 140 BPM, hype vocal riser shouts'
  },
  {
    name: 'electro house',
    prompt: 'Electro House, big-room club banger, buzzing detuned saw leads, distorted pumping bass, rolling kick, white-noise sweeps, peak-time energy, 128 BPM, processed hype vocal chants'
  },
  {
    name: 'electro swing',
    prompt: 'Electro Swing, vintage big band dance, 1930s swing clarinet and brass samples, driving 128 BPM house kick drum, bouncy sub-bassline, theatrical speakeasy energy, jazzy energetic female vocals'
  },
  {
    name: 'electropop',
    prompt: 'Electropop, glossy modern pop, bright synth hooks, punchy electronic drums, pulsing sub-bass, shimmering pads, euphoric glittering mood, 116 BPM, sleek airy female vocals'
  },
  {
    name: 'eurobeat',
    prompt: '90s Eurobeat, high-speed electronic dance, aggressive brass synth leads, unrelenting four-on-the-floor kick, dramatic key shifts, adrenaline-fueled racing mood, 158 BPM, operatic soaring male vocals'
  },
  {
    name: 'fado',
    prompt: 'Portuguese Fado, melancholic urban folk, Portuguese guitar arpeggios, gentle classical guitar, soft double bass, sorrowful saudade mood, 64 BPM, deeply expressive female vocals'
  },
  {
    name: 'festival trap',
    prompt: 'Festival Trap, EDM-trap hybrid, huge distorted 808 drops, rising snare rolls, brass stabs, aggressive crowd-jumping energy, 150 BPM, shouted hype male vocal chants'
  },
  {
    name: 'flamenco nuevo',
    prompt: 'Nuevo Flamenco, Spanish guitar fusion, rapid rasgueado nylon-guitar, cajón percussive rhythm, hand claps, emotional acoustic bass, fiery 110 BPM, raspy impassioned cante jondo vocals'
  },
  {
    name: 'flamenco trap',
    prompt: 'Spanish Flamenco Trap, urbano fusion, rapid nylon-string guitar rasgueado, snappy 808 sub-bass, stuttering hi-hat rolls, palmas handclaps, seductive dark swagger, 130 BPM, autotuned passionate Melisma vocals'
  },
  {
    name: 'folk singer-songwriter',
    prompt: 'Folk Singer-Songwriter, intimate acoustic folk, fingerpicked acoustic guitar, soft harmonica, warm upright bass, light brushed percussion, honest storytelling mood, 90 BPM, gentle earnest male vocals'
  },
  {
    name: 'forro',
    prompt: 'Brazilian Forro, Northeastern dance music, lively accordion, zabumba bass drum, bright triangle, rhythmic acoustic guitar, festive sunny mood, 132 BPM, joyful sing-along male vocals in Portuguese'
  },
  {
    name: 'french chanson',
    prompt: 'Classic 1950s French Chanson, Paris cabaret, romantic musette accordion sweeps, walking acoustic upright bass, brush-snare waltz timing, nostalgic bohemian street cafe vibe, sentimental 84 BPM, expressive dramatic French female vocals'
  },
  {
    name: 'french house',
    prompt: 'French House, filter disco, side-chained vinyl sample loops, funky slap bassline, 909 four-on-the-floor kick, euphoric club energy, 126 BPM, pitched-down soulful vocal chops'
  },
  {
    name: 'future bass',
    prompt: 'Future Bass, emotional festival EDM, wide detuned supersaw chords, pitched vocal chops, bouncing sidechained drums, heavy sub drops, bittersweet euphoric mood, 150 BPM, airy pitched female vocals'
  },
  {
    name: 'future garage',
    prompt: 'Future Garage, atmospheric UK bass, syncopated skippy percussion, heavy reese bass swells, rain ambience, melancholic vinyl warmth, 134 BPM, chopped pitched-up R&B female vocal fragments'
  },
  {
    name: 'g-funk',
    prompt: '90s West Coast G-Funk, hip-hop, high-pitched Portamento sine synth leads, deep rolling Moog bassline, classic Parliament-style groove, laid-back sunny atmosphere, 92 BPM, smooth relaxed male rap flow'
  },
  {
    name: 'gangsta rap',
    prompt: 'Gangsta Rap, hard-hitting drum machine, menacing synth bass, sampled funk guitar, sirens, gritty street mood, 94 BPM, aggressive gruff male rap vocals'
  },
  {
    name: 'garage rock',
    prompt: 'Garage Rock, raw lo-fi rock and roll, fuzzy overdriven guitars, simple pounding drums, buzzing bass, jangly organ, rowdy basement energy, 150 BPM, snarling shouted male vocals'
  },
  {
    name: 'glam rock',
    prompt: '70s Glam Rock, glitter rock, stomp-stomp-clap drum groove, fuzz-laden crunchy electric guitar riffs, theatrical piano flourishes, flamboyant stadium energy, stomping 116 BPM, theatrical high-register male vocals'
  },
  {
    name: 'glitch hop',
    prompt: '2010s Glitch Hop, neuro-funk, squelchy neuro-bass stabs, swing-quantized heavy boombap beat, vinyl scratching, razor-sharp digital chops, swaggering funk groove, bouncing 108 BPM, robotic processed hip-hop hype vocals'
  },
  {
    name: 'goa trance',
    prompt: '90s Oldschool Goa Trance, psychedelic dance, spiraling 303 acid lines, hypnotic layered sitar synth arpeggios, punchy four-on-the-floor kick, mystical cosmic momentum, relentless 145 BPM, pitched transcendental vocal samples'
  },
  {
    name: 'gospel choir',
    prompt: 'Gospel Choir, uplifting black gospel, thundering Hammond organ, rolling piano, handclap backbeat, tambourine, full choir harmonies, joyful testifying mood, 96 BPM, powerful soulful lead vocals with call-and-response choir'
  },
  {
    name: 'gqom',
    prompt: 'South African Gqom, dark minimal club, menacing repetitive sub-bass thuds, syncopated dry tribal percussion, ominous synth stabs, raw basement rave tension, raw 127 BPM, sporadic echoing male chant shouts'
  },
  {
    name: 'grime',
    prompt: 'UK Grime, London MC music, cold square-wave synths, sparse stuttering drums, heavy sub-bass, dark militant energy, 140 BPM, fast aggressive British male rap vocals'
  },
  {
    name: 'grunge',
    prompt: 'Grunge, 90s alternative rock, sludgy heavy-gain electric guitars, dynamic quiet-loud transitions, raw room drums, gritty aggressive mood, 110 BPM, raspy passionate male vocals'
  },
  {
    name: 'gypsy jazz',
    prompt: '1930s Gypsy Jazz, jazz manouche, blistering acoustic Selmer guitar arpeggios, steady'
  },
  {
    name: 'hair metal',
    prompt: '80s Hair Metal, glam rock, shredding lead guitar solos, chunky palm-muted riffs, pounding gated drums, shiny keyboards, party anthem mood, 128 BPM, high-pitched screaming male vocals with gang chorus'
  },
  {
    name: 'hard rock',
    prompt: 'Hard Rock, heavy riff-driven rock, thick distorted guitar riffs, wailing guitar solos, punchy bass, powerful backbeat drums, swaggering aggressive mood, 130 BPM, raspy high-energy male vocals'
  },
  {
    name: 'hardstyle',
    prompt: 'Hardstyle, hard dance, distorted reverse bass kick, euphoric supersaw synth melodies, dramatic build-ups and risers, intense festival energy, 150 BPM, pitched energetic hype-man vocals'
  },
  {
    name: 'heavy metal',
    prompt: 'Classic Heavy Metal, galloping twin guitar riffs, harmonised lead solos, thundering bass, fast double-kick drums, epic dark mood, 144 BPM, soaring powerful male vocals'
  },
  {
    name: 'highlife',
    prompt: 'West African Highlife, palm-wine guitar, bright interlocking guitar lines, bubbling bass, horn section, shuffling hand percussion, joyful festive mood, 112 BPM, smooth warm male vocals with chorus'
  },
  {
    name: 'hip-hop soul',
    prompt: 'Hip-Hop Soul, gritty hip-hop drums with R&B, smooth sampled soul loop, warm bass, vinyl crackle, sultry street-romance mood, 92 BPM, soulful female vocals with a guest male rap verse'
  },
  {
    name: 'honky-tonk',
    prompt: 'Classic 50s Honky-Tonk, traditional country, weeping pedal steel guitar, twangy Fender Telecaster leads, bouncing two-step upright bass, smoky Texas dancehall swing, lively 126 BPM, nasal sorrowful male vocal drawl'
  },
  {
    name: 'house',
    prompt: 'Classic House, Chicago four-on-the-floor, driving kick drum, offbeat open hi-hats, piano stabs, rolling bassline, handclaps, euphoric dancefloor mood, 124 BPM, uplifting soulful female vocals'
  },
  {
    name: 'hyperpop',
    prompt: 'Hyperpop, glitch pop, distorted 808 bass, metallic synth leads, erratic pitch-shifted vocal chops, manic energy, 160 BPM, autotuned sugary female vocals'
  },
  {
    name: 'indie folk',
    prompt: 'Indie Folk, warm acoustic folk, fingerpicked guitar, soft banjo, gentle upright bass, stomping kick drum, layered group harmonies, wistful woodland mood, 96 BPM, hushed tender male vocals'
  },
  {
    name: 'indie pop',
    prompt: 'Indie Pop, bright jangly guitars, buoyant bass, light danceable drums, glockenspiel and synth accents, breezy charming mood, 120 BPM, sweet quirky female vocals'
  },
  {
    name: 'indie rock',
    prompt: 'Indie Rock, 2000s guitar rock, angular overdriven guitars, driving bassline, tight punchy drums, reverberant chorus, urgent youthful mood, 138 BPM, cool detached male vocals'
  },
  {
    name: 'indie sleaze',
    prompt: '2000s Electroclash, indie dance-punk, raw distorted bass synthesizer, blown-out four-on-the-floor acoustic drums, scratchy garage rock guitar riff, messy sweaty club hedonism, rowdy 128 BPM, bratty detached female vocals'
  },
  {
    name: 'industrial metal',
    prompt: 'Industrial Metal, cyber-metal, down-tuned mechanical guitar riffs, distorted electronic beats, pounding factory percussion, dark hostile atmosphere, 135 BPM, harsh processed male vocals'
  },
  {
    name: 'irish folk',
    prompt: 'Irish Folk, traditional pub session, lively fiddle, tin whistle, bodhran frame drum, strummed acoustic guitar, accordion, spirited foot-stomping mood, 120 BPM, hearty rousing male vocals'
  },
  {
    name: 'italo disco',
    prompt: '80s Italo Disco, Euro disco, spacey synthesizer arpeggios, punchy LinnDrum patterns, melodic electric bass pulse, romantic campy electronic groove, 124 BPM, heavily accented passionate male vocals'
  },
  {
    name: 'j-pop',
    prompt: 'J-Pop, Japanese pop, bright layered synths, upbeat bouncy drums, funky bass, crisp electric guitar, catchy hooks, sparkling optimistic mood, 128 BPM, high clear female vocals in Japanese'
  },
  {
    name: 'jazz rap',
    prompt: 'Jazz Rap, hip-hop over live jazz, muted trumpet sample, walking upright bass, dusty swung drums, vibraphone, smooth cerebral mood, 90 BPM, relaxed fluent male rap vocals'
  },
  {
    name: 'jump blues',
    prompt: 'Jump Blues, 1940s swing-blues, honking tenor saxophone, boogie-woogie piano, walking upright bass, swinging shuffle drums, lively dancehall mood, 148 BPM, shouting playful male vocals'
  },
  {
    name: 'jungle',
    prompt: 'Jungle, 90s UK breakbeat, chopped Amen break, deep rolling sub-bass, ragga sirens, atmospheric pads, dark rave energy, 165 BPM, ragga MC chants'
  },
  {
    name: 'k-pop boy band',
    prompt: 'K-Pop Boy Band, polished Korean pop, hard-hitting trap beat, glossy synth hooks, deep bass drops, dramatic pre-chorus build, high-energy choreographed mood, 125 BPM, layered male vocals alternating melodic singing and rap'
  },
  {
    name: 'k-pop girl group',
    prompt: 'Modern K-Pop, dance-pop, bubblegum EDM, punchy 808 bass, brass stabs, clean synth arpeggios, dynamic beat switches, hyper-energetic 128 BPM, bright crisp female vocals and tight syncopated rap delivery'
  },
  {
    name: 'kawaii future bass',
    prompt: 'Kawaii Future Bass, anime pop EDM, bright detuned supersaws, bubbly water-drop synth effects, bouncy syncopated kicks, cheerful high-energy mood, 150 BPM, high-pitched cute female vocals'
  },
  {
    name: 'klezmer',
    prompt: 'Klezmer, Eastern European Jewish folk, soulful clarinet runs, lively fiddle, accordion, tuba oompah bass, bouncing frame drum, wedding celebration mood, 130 BPM, joyful chanting male vocals'
  },
  {
    name: 'krautrock',
    prompt: '70s Krautrock, kosmische musik, continuous hypnotic motorik 4/4 drum pulse, swirling modular synthesizer loops, repetitive minimal bassline, driving experimental groove, trance-inducing 124 BPM, detached monotone German male vocals'
  },
  {
    name: 'latin jazz',
    prompt: 'Latin Jazz, Afro-Cuban jazz groove, congas and timbales, virtuosic piano montuno, muted trumpet, walking upright bass, smoky nightclub mood, 120 BPM, smooth scatting male vocals'
  },
  {
    name: 'latin pop',
    prompt: 'Latin Pop, glossy modern pop with Latin rhythm, nylon string guitar, dembow-tinged drums, warm synth bass, bright brass hits, sunny romantic mood, 100 BPM, sensual melodic male vocals in Spanish'
  },
  {
    name: 'latin trap',
    prompt: 'Latin Trap, Spanish-language trap, rolling 808 bass, skittering hi-hats, dark minor-key synth bells, atmospheric pads, moody street swagger, 140 BPM, autotuned melodic male vocals in Spanish'
  },
  {
    name: 'liquid drum and bass',
    prompt: 'Liquid Drum and Bass, smooth melodic dnb, rolling breakbeats, warm deep sub-bass, lush Rhodes and string pads, uplifting soulful mood, 174 BPM, silky emotive female vocals'
  },
  {
    name: 'lo-fi hip-hop',
    prompt: 'Lo-Fi Hip Hop, chillhop, dusty tape-wobbly Rhodes chords, muted vinyl-crackle boombap drums, warm hollow bass, mellow nostalgic study vibe, 82 BPM, soft melancholic spoken-word male samples'
  },
  {
    name: 'lullaby',
    prompt: 'Lullaby, gentle bedtime song, soft music box, light fingerpicked acoustic guitar, warm harp, whisper-quiet strings, peaceful sleepy mood, 60 BPM, soft soothing female vocals'
  },
  {
    name: 'mariachi',
    prompt: 'Mexican Mariachi, traditional ranchera, bright trumpets, sweeping violins, vihuela and guitarron rhythm, proud romantic mood, 108 BPM, powerful dramatic male vocals in Spanish'
  },
  {
    name: 'math rock',
    prompt: 'Math Rock, progressive indie rock, clean twangy dual guitars, metric modulation and complex 7/8 time signatures, tight dynamic drumming, bright playful mood, 138 BPM, clean earnest male vocals'
  },
  {
    name: 'melodic dubstep',
    prompt: 'Melodic Dubstep, emotive half-time bass music, soaring piano and strings, crisp heavy snare, warm wobbling bass, cinematic drop, 150 BPM, soaring emotional female vocals'
  },
  {
    name: 'melodic rap',
    prompt: 'Melodic Rap, sung-rap hybrid, emotive guitar loop, soft 808 bass, rolling hi-hats, lonely late-night mood, 138 BPM, autotuned sing-rap male vocals'
  },
  {
    name: 'melodic techno',
    prompt: 'Melodic Techno, emotive driving techno, arpeggiated synth sequences, deep rolling bassline, crisp hypnotic drums, wide cinematic pads, nocturnal euphoric mood, 124 BPM, ethereal wordless female vocals'
  },
  {
    name: 'melodic trap',
    prompt: 'Melodic Trap, emotional trap, shimmering guitar and bell melodies, deep 808 bass, rolling hi-hats, sad late-night mood, 142 BPM, autotuned melodic male vocals'
  },
  {
    name: 'merengue',
    prompt: 'Dominican Merengue, fast Caribbean dance, tambora and guira percussion, blaring saxophones, accordion runs, bouncing bass, festive party mood, 150 BPM, energetic call-and-response male vocals in Spanish'
  },
  {
    name: 'metalcore',
    prompt: 'Metalcore, heavy melodic hardcore, down-tuned chugging breakdowns, melodic twin guitar leads, double-kick drums, dark intense mood, 150 BPM, alternating screamed and soaring clean male vocals'
  },
  {
    name: 'miami bass',
    prompt: 'Miami Bass, booty-bass party music, booming 808 kick, electro synth stabs, rapid handclaps, car-stereo energy, 130 BPM, shouted playful male and female chants'
  },
  {
    name: 'mid-tempo bass',
    prompt: 'Cyberpunk Midtempo Bass, dark synthwave, crunchy distorted saw bass stabs, industrial clockwork percussion, aggressive cybernetic drive, brooding sci-fi mood, 105 BPM, processed vocoderized male whispering'
  },
  {
    name: 'midwest emo',
    prompt: 'Midwest Emo, math rock, intricate clean guitar tapping, odd-time signatures, dynamic build-ups, raw emotional energy, 140 BPM, strained confessional male vocals'
  },
  {
    name: 'modern country',
    prompt: 'Modern Country Pop, radio-ready Nashville, bright acoustic strumming, slick electric guitar, programmed drums, stomp-clap groove, feel-good truck-bed mood, 98 BPM, relaxed warm male vocals'
  },
  {
    name: 'moombahton',
    prompt: 'Moombahton, slowed-down dance, Dutch-house synths with dembow drums, heavy bass, tropical percussion, sweaty summer club mood, 108 BPM, sensual Spanish-language male vocals'
  },
  {
    name: 'motown soul',
    prompt: 'Motown, 60s classic soul, melodic walking bassline, tambourine backbeat, vibrant horn section, clean rhythm guitar chops, uplifting 120 BPM, powerful gospel-infused female vocals'
  },
  {
    name: 'musical theatre',
    prompt: 'Broadway Musical Theatre, show tune, grand piano, full pit orchestra, sweeping strings, bright brass, dramatic key changes, show-stopping emotional mood, 104 BPM, big expressive belted female vocals'
  },
  {
    name: 'neo-soul',
    prompt: 'Neo-Soul, 90s organic R&B, warm Rhodes chords, deep rounded bass, loose behind-the-beat drums, jazzy guitar licks, intimate groove, 84 BPM, smooth melismatic female vocals'
  },
  {
    name: 'neoclassical piano',
    prompt: 'Neoclassical Piano, modern minimalist classical, intimate solo grand piano, slow-building string quartet, soft felt hammers, reflective cinematic mood, 68 BPM, soft wordless female vocalise'
  },
  {
    name: 'neofolk',
    prompt: 'Neofolk, dark folk, acoustic fingerpicked twelve-string guitar, militaristic snare marches, mournful cello, atmospheric field recordings, solemn 90 BPM, deep ritualistic baritone vocals'
  },
  {
    name: 'new age',
    prompt: 'New Age, meditative ambient, flowing synthesizer pads, soft harp, gentle flutes, crystal bowl chimes, nature textures, serene spiritual mood, 60 BPM, gentle wordless choir vocals'
  },
  {
    name: 'new wave',
    prompt: 'New Wave, late 70s art-pop, angular jangly guitar, driving synth riffs, tight dance drums, melodic bass, quirky cool mood, 134 BPM, deadpan stylish male vocals'
  },
  {
    name: 'norteno',
    prompt: 'Norteno, northern Mexican folk, bright button accordion, bajo sexto rhythm, tuba bass, polka-driven drums, rustic cantina mood, 118 BPM, heartfelt nasal male vocals in Spanish'
  },
  {
    name: 'nu-disco',
    prompt: 'Nu-Disco, modern disco revival, funky slap bass, shimmering rhythm guitar, lush strings, four-on-the-floor kick, glittering sunset mood, 118 BPM, silky falsetto male vocals'
  },
  {
    name: 'nu-metal',
    prompt: 'Nu-Metal, 2000s downtuned groove metal, heavy syncopated riffs, rapped verses, turntable scratches, thumping bass, aggressive angsty mood, 98 BPM, alternating rapped and screamed male vocals'
  },
  {
    name: 'old school rap',
    prompt: '1980s Old School Rap, early hip-hop, boxy 808 drum machine, electro funk bass, turntable scratching, handclaps, block party energy, 100 BPM, boastful rhythmic male rap vocals in call-and-response'
  },
  {
    name: 'orchestral pop',
    prompt: 'Orchestral Pop, cinematic chamber pop, sweeping strings, grand piano, french horn swells, soft timpani, gentle acoustic guitar, bittersweet uplifting mood, 76 BPM, rich emotional female vocals'
  },
  {
    name: 'outlaw country',
    prompt: 'Outlaw Country, 70s rebel Nashville, twangy telecaster, weeping pedal steel, walking bass, boom-chick snare, rugged rambling mood, 112 BPM, deep weathered male vocals'
  },
  {
    name: 'phonk',
    prompt: 'Drift Phonk, Memphis rap revival, heavily distorted cowbell melody, chopped 808 sub-bass slides, lo-fi drum machine patterns, aggressive dark energy, 140 BPM, pitched-down gritty rap samples'
  },
  {
    name: 'piano ballad pop',
    prompt: 'Piano Ballad Pop, emotional power pop ballad, expressive grand piano, swelling strings, soft kick and brushes, building dynamic climax, heartfelt tearful mood, 70 BPM, soaring emotional female vocals'
  },
  {
    name: 'pop punk',
    prompt: 'Pop Punk, fast melodic punk, palm-muted power chords, bright guitar leads, driving bass, energetic snare-heavy drums, youthful restless energy, 168 BPM, catchy nasal male vocals with gang backing'
  },
  {
    name: 'pop rap',
    prompt: 'Pop Rap, radio hip-hop, catchy piano riff, bouncy 808 bass, crisp claps, glossy feel-good mood, 100 BPM, charismatic male rap verses with a sung female hook'
  },
  {
    name: 'pop rock',
    prompt: 'Pop Rock, radio-friendly guitar pop, bright strummed guitars, punchy drums, melodic bass, tasteful synth layers, catchy singalong hooks, upbeat feel-good mood, 122 BPM, clear energetic male vocals'
  },
  {
    name: 'post-punk',
    prompt: 'Post-Punk, darkwave, chorus-drenched jangly guitar, prominent driving bassline, motorik drum machine, moody gothic aesthetic, 130 BPM, deadpan baritone male vocals'
  },
  {
    name: 'post-rock',
    prompt: 'Post-Rock, cinematic crescendo rock, ambient volume-swell guitars, shimmering tremolo melodies, gradual slow-burn build-up to thunderous drum explosion, cathartic 90 BPM, wordless ethereal vocal textures'
  },
  {
    name: 'power ballad',
    prompt: '80s Power Ballad, big emotional rock ballad, clean arpeggiated guitar into soaring overdriven solo, lush synth strings, slow thundering drums, dramatic build, 68 BPM, powerful passionate high male vocals'
  },
  {
    name: 'power metal',
    prompt: 'European Power Metal, speed metal, blistering twin-guitar harmonized leads, galloping double-kick drum assault, triumphant orchestral symphonic pads, heroic fantasy atmosphere, epic 165 BPM, soaring operatic wide-vibrato male tenor'
  },
  {
    name: 'progressive house',
    prompt: 'Progressive House, melodic club epic, pulsing arpeggios, evolving layered pads, warm rolling bassline, steady four-on-the-floor kick, slow euphoric build, 126 BPM, emotive airy male vocals'
  },
  {
    name: 'progressive metal',
    prompt: 'Progressive Metal, technical odd-meter metal, intricate downtuned riffs, shifting time signatures, virtuosic guitar solos, double-kick drum patterns, atmospheric keyboards, epic cerebral mood, 132 BPM, dynamic clean-to-harsh male vocals'
  },
  {
    name: 'progressive rock',
    prompt: 'Progressive Rock, 70s symphonic art rock, sprawling Mellotron, analog synth solos, intricate bass runs, complex odd-meter drums, clean electric guitar, epic cerebral mood, 112 BPM, high ethereal male vocals'
  },
  {
    name: 'psychedelic rock',
    prompt: 'Psychedelic Rock, 60s acid rock, swirling phaser guitars, fuzz bass, hypnotic drums, wobbly organ, sitar drones, trippy kaleidoscopic mood, 118 BPM, dreamy reverb-soaked male vocals'
  },
  {
    name: 'psychobilly',
    prompt: 'Psychobilly, horror punk rockabilly, furious slap acoustic upright bass, twangy overdriven Gretsch guitar, frantic surf drum rhythms, campy sinister energy, 175 BPM, snarling theatrical male vocals'
  },
  {
    name: 'psytrance',
    prompt: 'Full-On Psytrance, psy-electronic, rolling 16th-note rolling bassline, laser-like squelch synth leads, galloping kick drum, hypnotic psychedelic momentum, relentless 142 BPM, trippy robotic voice samples'
  },
  {
    name: 'punk rock',
    prompt: 'Punk Rock, fast raw punk, buzzsaw power chords, simple pounding drums, thudding bass, rebellious snarling energy, 184 BPM, shouted defiant male vocals with gang backing'
  },
  {
    name: 'rage rap',
    prompt: 'Rage Rap, hyper-aggressive trap, blown-out distorted synth leads, hard-clipped 808s, rapid hi-hats, chaotic mosh-pit energy, 150 BPM, shouted ad-lib-heavy male vocals'
  },
  {
    name: 'reggae dub',
    prompt: 'Dub Reggae, roots reggae, heavy syncopated sub-bass, rimshot snare drenched in spring reverb, tape-echo guitar skank, spacious psychedelic mix, 75 BPM, meditative chanted male vocals'
  },
  {
    name: 'reggaeton',
    prompt: 'Neo-Reggaeton, perreo, heavy Dembow drum rhythm, booming 808 sub kick, synthetic steel-drum synth hooks, sensual club atmosphere, infectious dance groove, 94 BPM, melodic autotuned Spanish male vocals'
  },
  {
    name: 'rock and roll',
    prompt: '1950s Rock and Roll, early rock, twangy hollow-body guitar, rolling boogie piano, slap upright bass, lively backbeat drums, honking saxophone, jukebox dance mood, 160 BPM, energetic youthful male vocals'
  },
  {
    name: 'rockabilly',
    prompt: 'Rockabilly, 50s Memphis rock, slapback-echo electric guitar, slap upright bass, snappy snare drums, hiccuping energy, greaser dancehall mood, 150 BPM, playful twangy male vocals'
  },
  {
    name: 'roots reggae',
    prompt: 'Roots Reggae, 70s Jamaican reggae, deep melodic bass, one drop drums, offbeat rhythm guitar skank, warm organ bubble, mellow spiritual mood, 72 BPM, soulful male vocals with harmonies'
  },
  {
    name: 'salsa',
    prompt: 'Salsa, New York Latin dance, driving congas and timbales, bright trumpets and trombones, piano montuno, rolling bass tumbao, hot dancefloor mood, 180 BPM, powerful call-and-response male vocals in Spanish'
  },
  {
    name: 'sea shanty',
    prompt: '19th Century Sea Shanty, maritime folk, wooden deck foot-stomping, rhythmic rigging-rope pulls, lone accordion drones, raw nautical camaraderie, buoyant marching 100 BPM, booming baritone lead with rowdy call-and-response pirate gang chorus'
  },
  {
    name: 'shoegaze',
    prompt: 'Shoegaze, dream pop, wall of fuzzy distorted guitars, heavy reverb and delay, wash of white noise, buried drums, ethereal 100 BPM, soft whispering female vocals'
  },
  {
    name: 'ska punk',
    prompt: '90s Ska Punk, skate punk, fast upstroke guitar skanks, punchy trumpet and trombone horn lines, galloping walking bassline, high-speed energetic drums, rowdy 165 BPM, raspy upbeat male vocals'
  },
  {
    name: 'smooth jazz',
    prompt: 'Smooth Jazz, 80s radio fusion, silky soprano saxophone, polished electric piano, mellow fretless bass, light programmed groove, lush sunset mood, 92 BPM, warm breathy female vocals'
  },
  {
    name: 'soca',
    prompt: 'Soca, Caribbean carnival dance, fast synthesized drums, bouncing electric bass, bright horn riffs, steel pan accents, jubilant fete mood, 128 BPM, energetic call-to-dance male vocals'
  },
  {
    name: 'soft rock',
    prompt: 'Soft Rock, 70s California easy listening, mellow acoustic guitar, warm Rhodes, soft rounded bass, gentle laid-back drums, silky harmonies, nostalgic sunny mood, 94 BPM, smooth gentle male vocals'
  },
  {
    name: 'southern hip-hop',
    prompt: 'Southern Hip-Hop, Atlanta club rap, slow rolling 808 bass, snapping snares, eerie synth keys, laid-back swagger, 76 BPM, drawling melodic male rap vocals'
  },
  {
    name: 'southern rock',
    prompt: 'Southern Rock, 70s boogie rock, twin lead guitars, slide guitar, honky-tonk piano, shuffling drums, thick bass, sweet-tea sunset mood, 118 BPM, raspy soulful male vocals'
  },
  {
    name: 'speed garage',
    prompt: 'Late 90s UK Speed Garage, 4x4 bassline, warped time-stretched vocal chops, heavy bouncing 808 sub-bass glides, swinging snare rolls, euphoric underground pirate radio energy, driving 136 BPM, soulful pitched-up female vocal loops'
  },
  {
    name: 'stoner doom',
    prompt: 'Stoner Doom Metal, sludge, massive wall of fuzz-drenched drop-F guitars, agonizingly slow groove, cavernous room reverb drums, hypnotic monolithic weight, 55 BPM, raw bellowing male vocals'
  },
  {
    name: 'surf rock',
    prompt: '60s Surf Rock, instrumental rock, Fender Jaguar spring-reverb drippy guitars, fast tremolo picking, energetic rolling tom-tom drums, sun-drenched retro beach vibe, 148 BPM, sporadic wild male vocal shouts'
  },
  {
    name: 'symphonic metal',
    prompt: 'Symphonic Metal, orchestral power metal, crushing palm-muted guitars, full orchestra and choir, fast double-kick drums, dramatic string runs, epic gothic mood, 140 BPM, soaring operatic female vocals'
  },
  {
    name: 'synthwave',
    prompt: 'Synthwave, 80s retrowave, analog synthesizers, punchy gated reverb snare, driving arpeggiated bassline, nostalgic atmosphere, 115 BPM, smooth emotive male vocals'
  },
  {
    name: 'tango nuevo',
    prompt: 'Tango Nuevo, contemporary Argentine tango, expressive bandoneon runs, dramatic piano accents, virtuosic violin solos, romantic tension, syncopated 120 BPM, rich passionate baritone vocals'
  },
  {
    name: 'techno',
    prompt: 'Techno, Detroit-inspired club techno, relentless pounding kick, metallic hi-hats, hypnotic acid sequences, dark industrial atmosphere, warehouse mood, 132 BPM, sparse processed spoken male vocal samples'
  },
  {
    name: 'trance',
    prompt: 'Uplifting Trance, euphoric club anthem, soaring supersaw leads, rolling offbeat bassline, driving four-on-the-floor kick, building snare rolls, emotional breakdown, 138 BPM, ethereal soaring female vocals'
  },
  {
    name: 'trap',
    prompt: 'Trap, modern hip-hop, rapid rolling hi-hats, booming 808 bass, sharp snares, dark synth melodies, bell accents, menacing confident mood, 140 BPM, autotuned melodic male rap vocals'
  },
  {
    name: 'trap metal',
    prompt: 'Trap Metal, aggressive trap, distorted metal guitar riffs, hard 808 bass, double-time hi-hats, mosh-pit energy, 145 BPM, screamed and shouted male vocals'
  },
  {
    name: 'trap soul',
    prompt: 'Trap Soul, moody R&B-trap, lush Rhodes chords, slow 808 bass, sparse crisp hi-hats, dim late-night mood, 66 BPM, silky autotuned melodic male vocals'
  },
  {
    name: 'trip-hop',
    prompt: 'Trip-Hop, downtempo, dusty vinyl-sampled breakbeats, deep sub-bass, moody upright piano, cinematic noir strings, hazy 85 BPM, sultry breathy female vocals'
  },
  {
    name: 'tropical house',
    prompt: 'Tropical House, sunny chill dance, marimba plucks, steel drum synth, warm deep bass, soft four-on-the-floor kick, breezy beach mood, 100 BPM, light airy female vocals'
  },
  {
    name: 'twee pop',
    prompt: '90s Twee Pop, indie pop, clean jangly Rickenbacker guitar, playful toy piano and glockenspiel, simple four-on-the-floor drumming, naive innocent charm, bouncy 132 BPM, delicate breathy boy-girl vocal duets'
  },
  {
    name: 'two-tone ska',
    prompt: 'Two-Tone Ska, late 70s British ska, bright offbeat guitar, bouncing walking bass, punchy horn section, lively skank organ, upbeat checkerboard dance mood, 140 BPM, energetic male vocals'
  },
  {
    name: 'uk drill',
    prompt: 'UK Drill, dark London street rap, sliding 808 bass, bouncy staccato hi-hats, ominous piano and string loop, cold menacing mood, 142 BPM, deadpan British male rap vocals'
  },
  {
    name: 'uk garage',
    prompt: 'UK Garage, 2-step, skippy shuffled drums, warm sub-bass, chopped pitched-up vocal samples, bright organ stabs, late-night London mood, 132 BPM, smooth soulful female vocals'
  },
  {
    name: 'vaporwave',
    prompt: 'Vaporwave, mallsoft, slowed and pitched-down 80s adult contemporary samples, heavy phaser and chorus modulation, lush luxury synth pads, eerie consumerist nostalgia, sluggish 78 BPM, distorted pitched-down male vocals'
  },
  {
    name: 'vocal jazz',
    prompt: 'Vocal Jazz, classic standards, upright bass, brushed drums, warm jazz guitar, soft piano, muted horn, intimate supper-club mood, 90 BPM, silky expressive female vocals'
  },
  {
    name: 'yacht rock',
    prompt: 'Late 70s Yacht Rock, West Coast soft rock, smooth electric piano Rhodes, clean compressed guitar solos, breezy syncopated drums, glossy studio production, laid-back 96 BPM, silky harmonized male vocals'
  },
  {
    name: 'zydeco',
    prompt: 'Louisiana Zydeco, Creole folk, fast syncopated button accordion, rasping metal frottoir washboard, funky backbeat drums, buoyant party groove, 135 BPM, lively call-and-response Creole French male vocals'
  }
];

function formatCannedStyle(prompt) {
  var item = typeof loraChosen === 'function' ? loraChosen() : null;
  if (item && item.trigger) {
    return item.trigger + ', ' + prompt;
  }
  return prompt;
}

function currentCannedStyle() {
  var val = tidyStyle($('style') ? $('style').value : '');
  if (!val) { return null; }
  var cleanVal = val;
  if (typeof allKnownLoraTriggers === 'function') {
    allKnownLoraTriggers().forEach(function (t) { cleanVal = removeStyleWord(cleanVal, t); });
    cleanVal = tidyStyle(cleanVal);
  }
  for (var i = 0; i < CANNED_STYLES.length; i++) {
    var s = CANNED_STYLES[i];
    if (tidyStyle(s.prompt) === val || tidyStyle(s.prompt) === cleanVal || tidyStyle(formatCannedStyle(s.prompt)) === val) {
      return s;
    }
  }
  return null;
}

function syncStylePickerLabel() {
  var lbl = $('style-picker-label');
  if (!lbl) { return; }
  var match = currentCannedStyle();
  lbl.textContent = match ? match.name : 'Choose a style\u2026';
}

function paintStylePickerMenu(filterText) {
  var menu = $('style-picker-menu');
  if (!menu) { return; }
  var searchInput = $('style-picker-search');
  var query = typeof filterText === 'string' ? filterText : (searchInput ? searchInput.value : '');
  query = (query || '').trim().toLowerCase();
  var match = currentCannedStyle();
  var filtered = CANNED_STYLES.filter(function (s) {
    if (!query) { return true; }
    return s.name.toLowerCase().indexOf(query) >= 0 || s.prompt.toLowerCase().indexOf(query) >= 0;
  });

  var listHtml = filtered.length ? filtered.map(function (s) {
    var isSelected = match && match.name === s.name;
    return '<div class="style-picker-item' + (isSelected ? ' selected' : '') + '" role="option" data-style-name="' + esc(s.name) + '" title="' + esc(s.prompt) + '">' +
      '<span class="style-item-name">' + esc(s.name) + '</span>' +
      '<span class="style-item-preview">' + esc(s.prompt) + '</span>' +
      '</div>';
  }).join('') : '<div class="style-picker-empty muted">No matching styles</div>';

  var listEl = menu.querySelector('.style-picker-list');
  if (!searchInput || !listEl) {
    menu.innerHTML = '<div class="style-picker-search-wrap">' +
      '<input type="search" id="style-picker-search" class="style-picker-search" placeholder="Search styles\u2026" autocomplete="off" />' +
      '</div>' +
      '<div class="style-picker-list" role="listbox">' + listHtml + '</div>';
  } else {
    listEl.innerHTML = listHtml;
  }
}

function openStylePicker() {
  var menu = $('style-picker-menu');
  var btn = $('style-picker-btn');
  if (!menu || !btn) { return; }
  paintStylePickerMenu('');
  var searchInput = $('style-picker-search');
  if (searchInput) { searchInput.value = ''; }
  paintStylePickerMenu('');
  var box = btn.getBoundingClientRect();
  var panel = btn.closest('.panel');
  var bounds = panel ? panel.getBoundingClientRect() : { top: 0, bottom: window.innerHeight };
  var below = Math.min(bounds.bottom, window.innerHeight) - box.bottom;
  var above = box.top - Math.max(bounds.top, 0);
  var up = above > below && below < 280;
  menu.classList.toggle('up', up);
  menu.classList.remove('hidden');
  btn.setAttribute('aria-expanded', 'true');
  var selected = menu.querySelector('.selected');
  if (selected) {
    selected.scrollIntoView({ block: 'nearest' });
  } else if (searchInput) {
    searchInput.focus();
  }
}

function closeStylePicker() {
  var menu = $('style-picker-menu');
  var btn = $('style-picker-btn');
  if (!menu || !btn) { return; }
  menu.classList.add('hidden');
  btn.setAttribute('aria-expanded', 'false');
}

function toggleStylePicker() {
  var menu = $('style-picker-menu');
  if (menu && menu.classList.contains('hidden')) {
    openStylePicker();
  } else {
    closeStylePicker();
  }
}

function applyCannedStyle(styleName) {
  var found = null;
  for (var i = 0; i < CANNED_STYLES.length; i++) {
    if (CANNED_STYLES[i].name === styleName) {
      found = CANNED_STYLES[i];
      break;
    }
  }
  if (!found) { return; }
  var item = typeof loraChosen === 'function' ? loraChosen() : null;
  var trigger = (item && item.trigger) || '';
  if (trigger) {
    $('style').value = trigger + ', ' + found.prompt;
    State.loraTrigger = trigger;
  } else {
    $('style').value = found.prompt;
    State.loraTrigger = null;
  }
  $('style').dataset.touched = '1';
  paintVocals();
  paintStyleLoraNote();
  saveForm();
  syncStylePickerLabel();
  closeStylePicker();
}

/* ----------------------------------------------- a big LoRA's learned styles
   A corpus gives a chip per song, 136 of them for a big one. Past a dozen, a filter
   box and a row of the tags that recur across the corpus narrow them, and the list
   shows its first dozen until asked for the rest. The tags come from the analysis,
   so every corpus gets its own. Kept per LoRA, reset when another is chosen. */
var LORA_STYLES_FOLD = 12;
var LORA_STYLE_VIEW = { lora: null, text: '', tags: [], all: false };

function loraStyleTags(styles) {
  var count = {};
  styles.forEach(function (s) {
    var seen = {};
    (s.prompt || '').split(',').forEach(function (raw) {
      var tag = raw.trim().toLowerCase();
      // The key and the voice say nothing about what a song is like.
      if (!tag || seen[tag] || /^key of /.test(tag) || /\bvocals?\b/.test(tag)) { return; }
      seen[tag] = true;
      count[tag] = (count[tag] || 0) + 1;
    });
  });
  // Worth a button when it picks out a few songs but not nearly all of them.
  return Object.keys(count).filter(function (tag) {
    return count[tag] >= 3 && count[tag] < styles.length * 0.9;
  }).sort(function (a, b) { return count[b] - count[a] || a.localeCompare(b); }).slice(0, 14)
    .map(function (tag) { return { tag: tag, count: count[tag] }; });
}

function loraStyleMatches(s, view) {
  var text = ((s.title || '') + ' ' + (s.prompt || '')).toLowerCase();
  var tags = (s.prompt || '').toLowerCase().split(',').map(function (t) { return t.trim(); });
  if (view.text && text.indexOf(view.text.toLowerCase()) < 0) { return false; }
  return view.tags.every(function (tag) { return tags.indexOf(tag) >= 0; });
}

function loraStylesShown(lora, wrap, box) {
  var view = LORA_STYLE_VIEW;
  if (view.lora !== lora.name) { LORA_STYLE_VIEW = view = { lora: lora.name, text: '', tags: [], all: false }; }
  var tools = $('lora-style-tools');
  var all = lora.styles || [];
  if (all.length <= LORA_STYLES_FOLD) {
    if (tools) { tools.classList.add('hidden'); }
    return { shown: all, more: '' };
  }
  if (!tools) {
    // Made here rather than in the page, so a page loaded before this still gets it.
    tools = document.createElement('div');
    tools.id = 'lora-style-tools';
    tools.className = 'lora-style-tools';
    wrap.insertBefore(tools, box);
    tools.addEventListener('input', function (event) {
      if (event.target.id !== 'lora-style-filter') { return; }
      LORA_STYLE_VIEW.text = event.target.value.trim();
      paintPresets();
    });
    tools.addEventListener('click', function (event) {
      var button = event.target.closest('[data-style-tag]');
      if (!button) { return; }
      var at = LORA_STYLE_VIEW.tags.indexOf(button.dataset.styleTag);
      if (at >= 0) { LORA_STYLE_VIEW.tags.splice(at, 1); } else { LORA_STYLE_VIEW.tags.push(button.dataset.styleTag); }
      paintPresets();
    });
    box.addEventListener('click', function (event) {
      if (!event.target.closest('[data-style-more]')) { return; }
      LORA_STYLE_VIEW.all = true;
      paintPresets();
    });
  }
  tools.classList.remove('hidden');
  var matching = all.filter(function (s) { return loraStyleMatches(s, view); });
  var tagHtml = loraStyleTags(all).map(function (item) {
    var on = view.tags.indexOf(item.tag) >= 0;
    return '<button type="button" class="chip compact style-tag' + (on ? ' active' : '') + '" data-style-tag="' + esc(item.tag) +
      '" title="' + item.count + ' songs">' + esc(item.tag) + '</button>';
  }).join('');
  var head = '<div class="lora-style-find"><input id="lora-style-filter" type="search" placeholder="Filter ' + all.length +
    ' styles" value="' + esc(view.text) + '"><span class="muted small">' +
    (view.text || view.tags.length ? matching.length + ' of ' + all.length : '') + '</span></div>' +
    '<div class="chips style-tags">' + tagHtml + '</div>';
  // Rebuilt only when the tags change, so the filter box keeps its caret while typing.
  var key = lora.name + '|' + view.tags.join(',') + '|' + (view.text || view.tags.length ? matching.length : '');
  if (tools.dataset.key !== key) {
    var typing = document.activeElement && document.activeElement.id === 'lora-style-filter';
    tools.innerHTML = head;
    tools.dataset.key = key;
    if (typing) {
      var input = $('lora-style-filter');
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
  }
  var narrowed = Boolean(view.text || view.tags.length);
  var shown = narrowed || view.all ? matching : matching.slice(0, LORA_STYLES_FOLD);
  var more = shown.length < matching.length
    ? '<button type="button" class="chip action compact" data-style-more="1">Show all ' + matching.length + '</button>'
    : (narrowed && !matching.length ? '<span class="muted small">No style matches.</span>' : '');
  return { shown: shown, more: more };
}

function loraStylePrompt(s) {
  return (s.prompt || '') + (s.tempo ? ', ' + s.tempo + ' BPM' : '');
}

/* What a style chip does: its style in the box, after the LoRA's trigger word. */
function applyLoraStyle(prompt, trigger) {
  if (trigger) {
    $('style').value = trigger + ', ' + prompt;
    State.loraTrigger = trigger;
  } else {
    $('style').value = prompt;
    State.loraTrigger = null;
  }
  $('style').dataset.touched = '1';
  paintVocals();
  paintStyleLoraNote();
  saveForm();
}

/* A corpus song as the recording: the style it was captioned with in training goes in
   the box, as its chip would put it, after the chosen LoRA's trigger word if there is
   one.  Choosing the song replaces whatever style was there; choosing a LoRA afterwards
   only replaces an empty style or a learned one, never one someone wrote. */
function corpusSong(test) {
  var found = null;
  (State.corpusSongs || []).forEach(function (group) {
    (group.songs || []).forEach(function (song) { if (!found && test(song)) { found = song; } });
  });
  return found;
}

function corpusSongStyle(song) {
  return song && song.style ? loraStylePrompt({ prompt: song.style, tempo: song.tempo }) : '';
}

function styleIsReplaceable() {
  var text = $('style').value || '';
  allKnownLoraTriggers().forEach(function (t) { text = removeStyleWord(text, t); });
  text = tidyStyle(text);
  if (!text) { return true; }
  var learned = function (prompt) { return tidyStyle(prompt) === text; };
  return loraCatalogue().some(function (lora) {
    return (lora.styles || []).some(function (s) { return learned(loraStylePrompt(s)); });
  }) || Boolean(corpusSong(function (song) { return learned(corpusSongStyle(song)); }));
}

function fillCorpusSongStyle(songId, chosen) {
  if (State.mode !== 'cover') { return; }
  var sourceId = $('source-select') ? $('source-select').value : '';
  if (!songId && !sourceId) { return; }
  if (!State.corpusSongs) {
    // A recording restored with the page, before the picker has listed the corpora.
    loadCorpusSongs().then(function () { if (State.corpusSongs) { fillCorpusSongStyle(songId, chosen); } });
    return;
  }
  var song = corpusSong(function (item) { return songId ? item.id === songId : item.source_id === sourceId; });
  var style = corpusSongStyle(song);
  if (!style || (!chosen && !styleIsReplaceable())) { return; }
  var lora = loraChosen();
  applyLoraStyle(style, (lora && lora.trigger) || '');
}

function paintPresets() {
  var lora = loraChosen();
  var wrap = $('lora-presets-wrap');
  var labelEl = $('lora-presets-label');
  var loraBox = $('lora-presets');
  if (wrap && labelEl && loraBox) {
    if (lora && lora.styles && lora.styles.length) {
      wrap.classList.remove('hidden');
      // Its own name: the group is shared by every corpus LoRA.
      var artistName = lora.title || lora.family || lora.name.replace(/\.safetensors$/, '');
      labelEl.textContent = 'Learned styles for ' + artistName + ' (click to apply):';
      var styles = loraStylesShown(lora, wrap, loraBox);
      var loraHtml = styles.shown.map(function (s) {
        var prompt = loraStylePrompt(s);
        // Labelled by the song's own style, not the corpus description every chip shares.
        var genreHint = s.hint ? s.hint.split(',')[0].trim() : '';
        var chipLabel = s.title ? esc(s.title) + (genreHint ? ' <span class="muted">\u00b7 ' + esc(genreHint) + '</span>' : '') : esc(genreHint || s.prompt);
        var fullTitle = (s.title ? s.title + ': ' : '') + prompt;
        return '<button type="button" class="chip lora-style-chip" data-lora-style="' + esc(prompt) + '" data-trigger="' + esc(lora.trigger || '') + '" title="' + esc(fullTitle) + '">' + chipLabel + '</button>';
      }).join('') + styles.more;
      if (loraBox.dataset.html !== loraHtml) {
        loraBox.innerHTML = loraHtml;
        loraBox.dataset.html = loraHtml;
      }
    } else {
      wrap.classList.add('hidden');
      loraBox.innerHTML = '';
      loraBox.dataset.html = '';
    }
  }

  var list = State.mode === 'inst' ? PRESETS.inst : PRESETS.vocal;
  var html = list.map(function (text) {
    var label = State.mode === 'inst' ? text.split(',')[0] : (text.split(',')[1] || text);
    return '<button class="chip" data-preset="' + esc(text) + '">' + esc(label.trim()) + '</button>';
  }).join('');
  if ($('presets').dataset.html !== html) { $('presets').innerHTML = html; $('presets').dataset.html = html; }
}

/* ------------------------------------------------------ instrumental structure
   What goes into the lyrics slot for an instrumental: [instrumental], a list of
   section tags, or tags with times.  The LoRA only knows these six sections. */
var SECTIONS = ['intro', 'verse', 'pre-chorus', 'chorus', 'bridge', 'outro'];
/* How firmly the instrumental LoRA holds the model: Steady at full strength, Varied a little looser. */
/* There was a Feel control here, loosening the instrumental LoRA for more
   movement between sections. Measured at real song lengths, any loosening let
   the vocal back in, so it is gone: instrumentals always render at full
   strength. Takes made while it existed keep their saved feel, which now
   renders the same as Steady. */
var FEELS = { steady: 'Sticks to its loop: repetitive and laid-back.' };
var FEEL = { value: 'steady' };

function paintFeel() {}
var SECTION_SECONDS = { intro: 15, verse: 30, 'pre-chorus': 15, chorus: 25, bridge: 20, outro: 15 };
var STRUCTURE = {
  kind: 'free',
  sections: ['intro', 'verse', 'chorus', 'verse', 'chorus', 'bridge', 'chorus', 'outro'].map(function (name) {
    return { name: name, seconds: SECTION_SECONDS[name] };
  })
};

function clock(total) {
  var whole = Math.round(total);          // rounded first, so 119.6 s reads 2:00 and not 1:60
  var m = Math.floor(whole / 60);
  var s = whole % 60;
  return m + ':' + (s < 10 ? '0' : '') + s;
}

function structureText() {
  if (STRUCTURE.kind === 'free') { return '[instrumental]'; }
  var at = 0;
  return STRUCTURE.sections.map(function (item) {
    if (STRUCTURE.kind === 'sections') { return '[' + item.name + ']'; }
    var tag = '[' + item.name + ' ' + clock(at) + '-' + clock(at + item.seconds) + ']';
    at += item.seconds;
    return tag;
  }).join('\n');
}

/* An instrumental take's structure back into the builder: '[instrumental]', tags, or
   tags with times.  Lengths come from the times when there are any. */
function loadStructure(text) {
  var lines = String(text || '').split('\n').map(function (line) { return line.trim(); }).filter(Boolean);
  var parsed = [];
  var timed = false;
  lines.forEach(function (line) {
    var m = /^\[([a-z-]+)(?:\s+(\d+):(\d\d)-(\d+):(\d\d))?\]$/.exec(line);
    if (!m || SECTIONS.indexOf(m[1]) < 0) { return; }
    var seconds = SECTION_SECONDS[m[1]];
    if (m[2] !== undefined) {
      timed = true;
      seconds = (Number(m[4]) * 60 + Number(m[5])) - (Number(m[2]) * 60 + Number(m[3]));
    }
    parsed.push({ name: m[1], seconds: seconds });
  });
  if (parsed.length) {
    STRUCTURE.sections = parsed;
    STRUCTURE.kind = timed ? 'timed' : 'sections';
  } else {
    STRUCTURE.kind = 'free';
  }
  paintStructure();
}

function instProblem() {
  return STRUCTURE.kind !== 'free' && !STRUCTURE.sections.length ? 'Add at least one section, or choose Let YuE2 decide.' : '';
}

function instBody(seed) {
  return withAdvancedSettings(withStyleLora({
    title: $('title').value.trim(),
    style: $('style').value,
    structure: structureText(),
    seed: seed,
    interpretation: $('interpretation').value,
    feel: FEEL.value,
    max_duration: parseFloat($('max-duration').value) || 360,
    auto_render: $('auto-render').checked,
    variety: $('variety').value,
    harmony: harmonyStep(),
    space_id: State.spaceId,
    realaudio: $('realaudio').checked, normalise: normaliseWanted()
  }));
}

async function doInstrumental() {
  if (instFromRecording()) { await doInstrumentalFromRecording(); return; }
  if (instPlanned()) { await doRenderPlanned(); return; }
  var problem = instProblem();
  if (problem) { statusLine(problem, 'bad'); return; }
  var seed = pickSeed();
  statusLine('Queued\u2026');
  try {
    var take = await api('/api/instrumentals', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(instBody(seed))
    });
    setSelection({ formTakeId: take.id, boxKind: 'none', boxId: null, awaiting: take.id });
    statusLine('Writing the score plan\u2026');
    loadTakes();
    editorAfterPlan();
  } catch (err) {
    statusLine('Could not start: ' + err.message, 'bad');
  }
}

var doRenderPlanned = doRenderTake;   // a planned instrumental's main button is Render this score too

async function doInstrumentalFromRecording() {
  var problem = instRecordingProblem();
  if (problem) { statusLine(problem, 'bad'); return; }
  var body = instBody(pickSeed());
  body.source_id = currentSource().id;
  body.abc = $('abc').value;
  body.auto_render = false;
  statusLine('Queued\u2026');
  try {
    await api('/api/instrumentals', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    statusLine('Rendering\u2026');
    loadTakes();
    closeEditor();
  } catch (err) {
    statusLine('Could not start: ' + err.message, 'bad');
  }
}

/* The sections of a recording's score, in the list the structure uses: for an instrumental made from a
   recording, and for a cover. They come from the "% name" lines of the score in the box, and each row can
   be moved, copied or taken out, which rewrites the score (the Score window shows it). */
function sectionsFromScore() {
  if (State.mode === 'inst') { return instFromRecording() || instPlanned(); }
  return State.mode === 'cover' && scoreSectionSpans($('abc').value).length > 0;
}

/* What a cover's words need after its sections changed (see ScoreSections.wordsNote). */
function sectionWordsNote(spans) {
  if (typeof ScoreSections === 'undefined' || !State.sectionsOriginal) { return ''; }
  var before = scoreSectionSpans(State.sectionsOriginal).map(function (span) { return span.was; });
  var after = spans.map(function (span) { return span.was; });
  var reordered = before.length === after.length && before.join('|') !== after.join('|');
  var text = ScoreSections.wordsNote(before.length, after.length, reordered);
  return text ? '<p class="struct-note over">' + esc(text) + '</p>' : '';
}

/* A render that ends well before its score has its sections right early and out later, since the music it made is shorter than
   the music it was given.  Said once under the list, in the take's own terms. */
function endedShortNote(total) {
  var take = editorTake();
  var heard = take && take.status === 'done' && take.duration ? Number(take.duration) : 0;
  if (!heard || !total) { return ''; }
  var gap = total - heard;
  if (gap < 6 || heard > total * 0.95) { return ''; }
  return '<p class="struct-note over">This take ended ' + Math.round(gap) + ' s short of its score, so the list can be out of step with the audio, more so later in the song.</p>';
}

function paintStructure() {
  var cover = State.mode === 'cover';
  if ($('structure-field') && (cover || State.mode === 'inst')) {
    $('structure-field').style.display = (State.mode === 'inst' || sectionsFromScore()) ? '' : 'none';
  }
  var sent = $('structure-preview') ? $('structure-preview').parentNode : null;
  if (sent) { sent.style.display = cover ? 'none' : ''; }
  if ($('structure-kind')) { $('structure-kind').style.display = (cover || sectionsFromScore()) ? 'none' : ''; }
  if (cover && !sectionsFromScore()) { return; }
  if (sectionsFromScore()) {
    var spans = scoreSectionSpans($('abc').value);
    var total = spans.length ? spans[spans.length - 1].end : 0;
    var cap = parseFloat($('max-duration').value) || 0;
    var fit = typeof ScoreSections !== 'undefined' ? ScoreSections.capCheck(total, cap) : { over: false };
    $('structure-total').textContent = total ? clock(total) + ' in all' + (cap ? ' \u00b7 cap ' + clock(cap) : '') : '';
    $('structure-total').classList.toggle('over', fit.over);
    var changed = Boolean(State.sectionsOriginal) && State.sectionsOriginal !== $('abc').value;
    var button = function (act, index, label, title, off) {
      return '<button type="button" class="struct-btn" data-sec-act="' + act + '" data-i="' + index + '" title="' + title + '"' +
        (off ? ' disabled' : '') + '>' + label + '</button>';
    };
    $('structure-body').innerHTML = spans.length
      ? '<ol class="struct-list">' + spans.map(function (span, index) {
          return '<li class="struct-row struct-fixed" draggable="true" data-i="' + index + '" title="Drag to move"><span class="struct-name">' + esc(span.name) +
            (span.was !== span.name ? ' <span class="struct-was">' + esc(span.was) + ' in the score</span>' : '') + '</span>' +
            '<span class="struct-time">' + clock(span.start) + '\u2013' + clock(span.end) + '</span>' +
            '<span class="struct-acts">' +
            button('up', index, '\u2191', 'Move up', index === 0) +
            button('down', index, '\u2193', 'Move down', index === spans.length - 1) +
            button('copy', index, 'copy', 'Add a copy of this section after it') +
            button('remove', index, '\u2715', 'Take this section out', spans.length < 2) +
            '</span></li>';
        }).join('') + '</ol><p class="struct-note">The sections of the recording\'s score' +
          (cover ? '. The words are matched to them in order, so change those to suit.' : '.') +
          ' Moving, copying or removing one rewrites the score.</p>' +
          (changed ? '' : endedShortNote(total)) +
          (fit.over ? '<p class="struct-note over">The cap is ' + clock(cap) + ', so the render would stop ' + clock(fit.short) +
            ' before the end of the score. <button type="button" class="chip action" data-sec-act="cap">Raise the cap to ' + clock(fit.raiseTo) + '</button></p>' : '') +
          (cover && changed ? sectionWordsNote(spans) : '') +
          (changed ? '<p class="struct-note"><button type="button" class="chip action" data-sec-act="restore">Restore the original sections</button></p>' : '')
      : '<p class="struct-note">The sections come from the recording\'s score once it is transcribed.</p>';
    if (!cover) { $('structure-preview').textContent = spans.length ? spans.map(function (span) { return '[' + span.name + ']'; }).join(' ') : '[instrumental]'; }
    paintEdTransport();
    return;
  }
  Array.prototype.forEach.call(document.querySelectorAll('#structure-kind button'), function (button) {
    button.classList.toggle('active', button.dataset.kind === STRUCTURE.kind);
  });
  var body = $('structure-body');
  var total = STRUCTURE.sections.reduce(function (sum, item) { return sum + item.seconds; }, 0);
  var cap = parseFloat($('max-duration').value) || 360;
  $('structure-total').textContent = STRUCTURE.kind === 'timed' ? clock(total) + ' in all' + (total > cap ? ', longer than the length cap' : '') : '';
  $('structure-total').classList.toggle('over', STRUCTURE.kind === 'timed' && total > cap);
  if (STRUCTURE.kind === 'free') {
    body.innerHTML = '<p class="struct-note">YuE2 chooses the sections and how long each one runs.</p>';
  } else {
    var at = 0;
    var rows = STRUCTURE.sections.map(function (item, index) {
      var options = SECTIONS.map(function (name) {
        return '<option value="' + name + '"' + (name === item.name ? ' selected' : '') + '>' + name + '</option>';
      }).join('');
      var timed = '';
      if (STRUCTURE.kind === 'timed') {
        timed = '<input type="number" min="4" max="180" step="1" value="' + item.seconds + '" data-row="' + index + '" data-field="seconds" title="Seconds">' +
          '<span class="struct-time">' + clock(at) + '\u2013' + clock(at + item.seconds) + '</span>';
        at += item.seconds;
      }
      return '<li class="struct-row"><select data-row="' + index + '" data-field="name">' + options + '</select>' + timed +
        '<button class="struct-btn" data-row="' + index + '" data-move="-1" title="Move up">\u2191</button>' +
        '<button class="struct-btn" data-row="' + index + '" data-move="1" title="Move down">\u2193</button>' +
        '<button class="struct-btn" data-row="' + index + '" data-remove="1" title="Remove">\u00d7</button></li>';
    }).join('');
    var adds = SECTIONS.map(function (name) {
      return '<button class="chip" data-add="' + name + '">+ ' + name + '</button>';
    }).join('');
    body.innerHTML = '<ol class="struct-list">' + rows + '</ol><div class="struct-add">' + adds + '</div>' +
      (STRUCTURE.kind === 'sections' ? '<p class="struct-note">YuE2 chooses how long each section runs.</p>' : '');
  }
  $('structure-preview').textContent = structureText().replace(/\n/g, ' ');
  saveForm();
}

/* A render's sections begin a little before the score's times say (measured: a beat or so, and steady
   through a song), so the take is taken, and the list lit, a beat and a half early (the score's own
   tempo): landing a touch before a section is heard as its start, landing after it as late. */
function sectionLead(abc) {
  var found = /^Q:\s*(?:\d+\/\d+\s*=\s*)?(\d+(?:\.\d+)?)/m.exec(String(abc || ''));
  var tempo = found ? Number(found[1]) : 120;
  var beat = tempo > 0 ? 60 / tempo : 0.5;
  return Math.min(0.9, Math.max(0.3, beat * 1.5));
}

function sectionStart(span, index, lead) { return index === 0 ? 0 : Math.max(0, span.start - lead); }

/* While a take plays and the sections have been rearranged since, the status line says the audio is the old
   arrangement and what makes the new one. It stays when playback stops and goes when the sections are put
   back or another score is loaded, and only if it is still the message on show, so nothing else is wiped. */
function paintStructureNotice() {
  var node = $('render-status');
  var audio = $('audio');
  var take = editorTake();
  if (!node || !audio) { return; }
  var playing = Boolean(take && State.loadedId === take.id && !audio.paused && !audio.ended);
  var changed = Boolean(State.sectionsOriginal) && State.sectionsOriginal !== $('abc').value;
  var message = 'Song structure has changed. ' + (State.mode === 'inst' ? 'Create instrumental' : 'Create cover') +
    ' to render this into a take.';
  if (changed && (playing || State.sectionNotice)) {
    if (playing && node.textContent !== message) { statusLine(message, 'wait'); }
    State.sectionNotice = message;
  } else if (State.sectionNotice) {
    if (node.textContent === State.sectionNotice) { statusLine(''); }
    State.sectionNotice = '';
  }
}

/* Double-clicking a section takes the take to where that section starts. The list's times are the score's,
   which the render follows closely; once the sections are rearranged the audio is still in its first order,
   so this says so and does nothing. */
function jumpToSection(index) {
  var take = editorTake();
  if (!take || !take.has_audio) { return; }
  if (State.sectionsOriginal && State.sectionsOriginal !== $('abc').value) {
    statusLine('The sections have been rearranged; the take still plays in its first order.');
    return;
  }
  var spans = scoreSectionSpans($('abc').value);
  if (!spans[index]) { return; }
  var audio = $('audio');
  var start = sectionStart(spans[index], index, sectionLead($('abc').value));
  var seek = function () {
    var limit = audio.duration && isFinite(audio.duration) ? Math.max(0, audio.duration - 0.2) : start;
    try { audio.currentTime = Math.min(start, limit); } catch (e) { /* not ready: the next one will do */ }
    paintTransport();
  };
  if (State.loadedId === take.id && audio.src && audio.readyState > 0) {
    seek();
    if (audio.paused || audio.ended) { audio.play().catch(function () {}); State.playing = take.id; paintTransport(); paintTakes(); }
  } else {
    playTake(take.id);
    audio.addEventListener('loadedmetadata', function once() { audio.removeEventListener('loadedmetadata', once); seek(); });
  }
}

/* One change to the score's sections, written into the score box as if typed there. The score as it was
   before the first change is kept, so the original sections can be put back until another score is loaded. */
function changeSections(act, index, to) {
  var box = $('abc');
  if (act === 'cap') {
    var need = ScoreSections.capCheck(planLength(box.value) ? planLength(box.value).seconds : 0, parseFloat($('max-duration').value) || 0);
    if (need.over) {
      $('max-duration').value = need.raiseTo;
      $('max-duration').dispatchEvent(new Event('input'));      // typed by hand from here on, as if the person had
    }
    paintStructure();
    return;
  }
  if (act === 'restore') {
    if (!State.sectionsOriginal) { return; }
    box.value = State.sectionsOriginal;
  } else {
    if (typeof ScoreSections === 'undefined') { return; }
    var next = ScoreSections.change(box.value, { act: act, index: index, to: to });
    if (next === null || next === box.value) { return; }
    if (!State.sectionsOriginal) { State.sectionsOriginal = box.value; }
    box.value = next;
  }
  box.dispatchEvent(new Event('input'));
  followRecordingCap();               // a cap the score set follows the score, as it does when the recording is chosen
  setChart(chordChart(box.value));
  showPlanLength(box.value);
  paintStructure();
  paintStructureNotice();
}

function wireStructure() {
  /* Dragging a row to a new place: the row under the pointer shows a line above or below it, and dropping
     moves the section there. Touch screens have no drag, so the arrows stay. */
  var body = $('structure-body');
  var clearDrop = function () {
    Array.prototype.forEach.call(body.querySelectorAll('.drop-before, .drop-after, .dragging'), function (el) {
      el.classList.remove('drop-before', 'drop-after', 'dragging');
    });
  };
  var dropAt = function (event) {
    var row = event.target.closest ? event.target.closest('.struct-row[data-i]') : null;
    if (!row || State.dragSection === undefined || State.dragSection === null) { return null; }
    var box = row.getBoundingClientRect();
    var after = event.clientY > box.top + box.height / 2;
    var target = Number(row.dataset.i) + (after ? 1 : 0);
    if (State.dragSection < target) { target -= 1; }
    return { row: row, after: after, to: target };
  };
  body.addEventListener('dragstart', function (event) {
    var row = event.target.closest ? event.target.closest('.struct-row[data-i]') : null;
    if (!row) { return; }
    State.dragSection = Number(row.dataset.i);
    row.classList.add('dragging');
    if (event.dataTransfer) { event.dataTransfer.effectAllowed = 'move'; event.dataTransfer.setData('text/plain', String(State.dragSection)); }
  });
  body.addEventListener('dragover', function (event) {
    var drop = dropAt(event);
    if (!drop) { return; }
    event.preventDefault();
    Array.prototype.forEach.call(body.querySelectorAll('.drop-before, .drop-after'), function (el) { el.classList.remove('drop-before', 'drop-after'); });
    if (drop.to !== State.dragSection) { drop.row.classList.add(drop.after ? 'drop-after' : 'drop-before'); }
  });
  body.addEventListener('drop', function (event) {
    var drop = dropAt(event);
    var from = State.dragSection;
    State.dragSection = null;
    clearDrop();
    if (!drop) { return; }
    event.preventDefault();
    if (drop.to !== from) { changeSections('move', from, drop.to); }
  });
  body.addEventListener('dragend', function () { State.dragSection = null; clearDrop(); });
  body.addEventListener('dblclick', function (event) {
    if (event.target.closest('button')) { return; }
    var row = event.target.closest('.struct-row[data-i]');
    if (row) { jumpToSection(Number(row.dataset.i)); }
  });
  $('structure-kind').addEventListener('click', function (event) {
    var button = event.target.closest('[data-kind]');
    if (!button) { return; }
    STRUCTURE.kind = button.dataset.kind;
    paintStructure();
  });
  $('structure-body').addEventListener('click', function (event) {
    var button = event.target.closest('button');
    if (!button) { return; }
    if (button.dataset.secAct) { changeSections(button.dataset.secAct, Number(button.dataset.i)); return; }
    var list = STRUCTURE.sections;
    if (button.dataset.add) {
      list.push({ name: button.dataset.add, seconds: SECTION_SECONDS[button.dataset.add] });
    } else if (button.dataset.remove) {
      list.splice(Number(button.dataset.row), 1);
    } else if (button.dataset.move) {
      var from = Number(button.dataset.row);
      var to = from + Number(button.dataset.move);
      if (to < 0 || to >= list.length) { return; }
      list.splice(to, 0, list.splice(from, 1)[0]);
    }
    paintStructure();
  });
  $('structure-body').addEventListener('change', function (event) {
    var field = event.target.dataset.field;
    if (!field) { return; }
    var item = STRUCTURE.sections[Number(event.target.dataset.row)];
    if (field === 'name') { item.name = event.target.value; }
    if (field === 'seconds') { item.seconds = Math.max(4, Math.min(180, Math.round(Number(event.target.value) || 0))); }
    paintStructure();
  });
  $('max-duration').addEventListener('input', function () {
    // Typed by hand: a recording's score no longer sets it.
    State.capTyped = true;
    State.capFromScore = false;
    if (State.mode === 'inst' || State.mode === 'cover') { paintStructure(); }
  });
  $('create-inst').addEventListener('click', doInstrumental);
}


/* ------------------------------------------------- the structure of a song
   Before any words exist, a song's sections are built here, as an instrumental's are: the lyric writer
   follows them, and they can be put in the lyrics box as empty sections to write under.  Once the box has
   words, the lyrics are what is sung and the builder steps aside. */
var SONGPLAN = { sections: ['Verse', 'Chorus', 'Verse', 'Chorus', 'Bridge', 'Chorus'], dragged: null };
var SONGPLAN_USUAL = 10;               // measured: a plan comes out with 8 to 10 sections whatever the words ask for
var SONGPLAN_USUAL_WORDS = '8 to 10';
var SONG_SECTIONS = ['Intro', 'Verse', 'Pre-Chorus', 'Chorus', 'Bridge', 'Interlude', 'Outro'];

function lyricsHaveWords(text) {
  return String(text || '').split('\n').some(function (line) {
    line = line.trim();
    return line && !/^\[[^\]]*\]$/.test(line);
  });
}

function paintSongPlan() {
  var field = $('song-structure-field');
  if (!field) { return; }
  var shown = State.mode === 'song' && !lyricsHaveWords($('lyrics').value);
  field.style.display = shown ? '' : 'none';
  if (!shown) { return; }
  var preset = $('song-structure-preset');
  var shapes = (State.options && State.options.lyric_structures) || [];
  if (preset && shapes.length && preset.options.length !== shapes.length + 1) {
    preset.innerHTML = '<option value="">Start from\u2026</option>' + shapes.map(function (shape) {
      return '<option value="' + esc(shape.id) + '" title="' + esc(shape.hint || '') + '">' + esc(shape.sections.join(', ')) + '</option>';
    }).join('');
  }
  var rows = SONGPLAN.sections.map(function (name, index) {
    var options = SONG_SECTIONS.map(function (item) {
      return '<option value="' + item + '"' + (item === name ? ' selected' : '') + '>' + item + '</option>';
    }).join('');
    return '<li class="struct-row" draggable="true" data-sp="' + index + '"><select data-sp-row="' + index + '">' + options + '</select>' +
      '<button type="button" class="struct-btn" data-sp-act="up" data-sp-row="' + index + '" title="Move up"' + (index === 0 ? ' disabled' : '') + '>\u2191</button>' +
      '<button type="button" class="struct-btn" data-sp-act="down" data-sp-row="' + index + '" title="Move down"' + (index === SONGPLAN.sections.length - 1 ? ' disabled' : '') + '>\u2193</button>' +
      '<button type="button" class="struct-btn" data-sp-act="remove" data-sp-row="' + index + '" title="Remove"' + (SONGPLAN.sections.length < 2 ? ' disabled' : '') + '>\u00d7</button></li>';
  }).join('');
  var adds = SONG_SECTIONS.map(function (name) {
    return '<button type="button" class="chip" data-sp-add="' + name + '"' +
      (name === 'Interlude' ? ' title="An instrumental passage: no lines are written under it"' : '') + '>+ ' + name.toLowerCase() + '</button>';
  }).join('');
  var long = SONGPLAN.sections.length > SONGPLAN_USUAL
    ? '<p class="struct-note over">The planner usually writes ' + SONGPLAN_USUAL_WORDS + ' sections, so a longer list gets condensed and the words of the sections it drops are not sung. ' +
      'For a longer song, give each section more lines when you write the lyrics.</p>' : '';
  $('song-structure-body').innerHTML = '<ol class="struct-list">' + rows + '</ol><div class="struct-add">' + adds + '</div>' + long;
}

function wireSongPlan() {
  var body = $('song-structure-body');
  if (!body) { return; }
  $('lyrics').addEventListener('input', paintSongPlan);
  $('song-structure-preset').addEventListener('change', function (event) {
    var shape = ((State.options && State.options.lyric_structures) || []).filter(function (item) { return item.id === event.target.value; })[0];
    if (shape) { SONGPLAN.sections = shape.sections.slice(); }
    event.target.value = '';
    paintSongPlan();
    saveForm();
  });
  body.addEventListener('click', function (event) {
    var add = event.target.closest('[data-sp-add]');
    var act = event.target.closest('[data-sp-act]');
    if (add) { SONGPLAN.sections.push(add.dataset.spAdd); }
    else if (act) {
      var from = Number(act.dataset.spRow);
      if (act.dataset.spAct === 'remove') { SONGPLAN.sections.splice(from, 1); }
      else {
        var to = from + (act.dataset.spAct === 'up' ? -1 : 1);
        if (to < 0 || to >= SONGPLAN.sections.length) { return; }
        SONGPLAN.sections.splice(to, 0, SONGPLAN.sections.splice(from, 1)[0]);
      }
    } else { return; }
    paintSongPlan();
    saveForm();
  });
  body.addEventListener('change', function (event) {
    if (event.target.dataset.spRow === undefined) { return; }
    SONGPLAN.sections[Number(event.target.dataset.spRow)] = event.target.value;
    paintSongPlan();
    saveForm();
  });
  body.addEventListener('dragstart', function (event) {
    var row = event.target.closest ? event.target.closest('[data-sp]') : null;
    if (row) { SONGPLAN.dragged = Number(row.dataset.sp); if (event.dataTransfer) { event.dataTransfer.effectAllowed = 'move'; event.dataTransfer.setData('text/plain', String(SONGPLAN.dragged)); } }
  });
  body.addEventListener('dragover', function (event) {
    if (SONGPLAN.dragged !== null && event.target.closest && event.target.closest('[data-sp]')) { event.preventDefault(); }
  });
  body.addEventListener('drop', function (event) {
    var row = event.target.closest ? event.target.closest('[data-sp]') : null;
    var from = SONGPLAN.dragged;
    SONGPLAN.dragged = null;
    if (!row || from === null) { return; }
    event.preventDefault();
    var to = Number(row.dataset.sp);
    if (to !== from) { SONGPLAN.sections.splice(to, 0, SONGPLAN.sections.splice(from, 1)[0]); paintSongPlan(); saveForm(); }
  });
  $('song-structure-fill').addEventListener('click', function () {
    var box = $('lyrics');
    box.value = SONGPLAN.sections.map(function (name) {
      return '[' + name + ']' + (name === 'Interlude' ? '' : '\n');
    }).join('\n\n').replace(/\n+$/, '') + '\n';
    box.dispatchEvent(new Event('input'));
    box.focus();
  });
}

/* ---------------------------------------------------------------- variations
   The same score and seed, rendered in other interpretations, each as a new take. */
var VARIATIONS = { take: null };

function openVariations(take) {
  VARIATIONS.take = take;
  $('variations-heading').textContent = 'Variations of \u201c' + take.title + '\u201d';
  var own = INTERPRETATIONS[take.interpretation] ? take.interpretation : 'standard';
  $('variations-list').innerHTML = Object.keys(INTERPRETATIONS).filter(function (key) { return key !== own; })
    .map(function (key) {
      return '<label><input type="checkbox" value="' + key + '" checked><strong>' + INTERPRETATIONS[key].name +
        '</strong><span class="muted">' + esc(INTERPRETATIONS[key].hint) + '</span></label>';
    }).join('');
  $('variations-status').textContent = '';
  // Starts from the left panel's cap; a change here is for these takes only.
  $('variations-cap').value = parseFloat($('max-duration').value) || 360;
  paintVariationsEstimate();
  $('variations-modal').classList.remove('hidden');
}

function closeVariations() {
  VARIATIONS.take = null;
  $('variations-modal').classList.add('hidden');
}

function chosenVariations() {
  return Array.prototype.map.call(document.querySelectorAll('#variations-list input:checked'), function (box) { return box.value; });
}

function paintVariationsEstimate() {
  var count = chosenVariations().length;
  var average = State.options.avg_render_seconds || 0;
  $('variations-go').disabled = !count;
  $('variations-go').textContent = count === 1 ? 'Render 1 variation' : 'Render ' + count + ' variations';
  $('variations-estimate').textContent = count && average ? 'about ' + Math.max(1, Math.round(count * average / 60)) + ' min of rendering' : '';
}

async function doVariations() {
  var take = VARIATIONS.take;
  var chosen = chosenVariations();
  if (!take || !chosen.length) { return; }
  var cap = parseFloat($('variations-cap').value);
  if (!(cap >= 10 && cap <= 900)) {
    $('variations-status').textContent = 'The length cap must be between 10 and 900 seconds.';
    $('variations-status').className = 'status bad';
    return;
  }
  var body = { interpretations: chosen, max_duration: cap };
  try {
    var reply = await api('/api/takes/' + take.id + '/variations', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    closeVariations();
    statusLine('Queued ' + reply.created.length + ' variation' + (reply.created.length === 1 ? '' : 's') + ' of ' + take.title +
      '. Each appears as its own take when it finishes.', 'good');
    loadTakes();
  } catch (err) {
    $('variations-status').textContent = 'Could not queue: ' + err.message;
    $('variations-status').className = 'status bad';
  }
}

async function openTracksModal() {
  var source = currentSource();
  if (!source) { return; }
  var modal = $('tracks-modal');
  var listEl = $('tracks-list');
  var statusEl = $('tracks-status');
  if (!modal || !listEl) { return; }
  modal.classList.remove('hidden');
  statusEl.textContent = 'Loading MIDI tracks\u2026';
  statusEl.className = 'status';
  try {
    var res = await api('/api/sources/' + source.id + '/tracks');
    var tracks = res.tracks || [];
    if (!tracks.length) {
      statusEl.textContent = 'No tracks found in this MIDI file.';
      listEl.innerHTML = '';
      return;
    }
    statusEl.textContent = '';
    listEl.innerHTML = tracks.map(function (t) {
      var isVocal = t.role === 'vocal';
      var octNote = (isVocal && t.avg_pitch < 64) ? ' \u00b7 +1 oct vocal transposed' : '';
      return '<div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:var(--card-2); color:var(--text); border-radius:6px; border:1px solid ' + (isVocal ? 'var(--accent-a)' : 'var(--line)') + '">' +
        '<div><strong>Track ' + t.track + ': ' + esc(t.name || 'Unnamed') + '</strong>' +
        '<div class="muted small">' + t.note_count + ' notes \u00b7 ' + esc(t.role) + octNote + ' \u00b7 mono ' + Math.round(t.mono_ratio * 100) + '% \u00b7 score ' + t.vocal_score + '</div></div>' +
        '<button class="chip action select-vocal-track" data-track="' + t.track + '">' + (isVocal ? 'Lead Vocal \u2713' : 'Set as Vocal') + '</button>' +
        '</div>';
    }).join('');

    listEl.querySelectorAll('.select-vocal-track').forEach(function (btn) {
      btn.addEventListener('click', async function () {
        var trk = parseInt(btn.dataset.track, 10);
        statusEl.textContent = 'Retracking with Track ' + trk + ' as Vocal\u2026';
        statusEl.className = 'status';
        try {
          var updated = await api('/api/sources/' + source.id + '/retrack', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vocal_track: trk })
          });
          $('abc').value = updated.abc || '';
          scoreBaseline(updated.abc || '');
          statusEl.textContent = 'Vocal track updated!';
          statusEl.className = 'status good';
          source.abc = updated.abc;
          setTimeout(function () { closeTracksModal(); }, 600);
        } catch (err) {
          statusEl.textContent = 'Error: ' + err.message;
          statusEl.className = 'status bad';
        }
      });
    });
  } catch (err) {
    statusEl.textContent = 'Could not load tracks: ' + err.message;
    statusEl.className = 'status bad';
  }
}

function closeTracksModal() {
  if ($('tracks-modal')) {
    $('tracks-modal').classList.add('hidden');
  }
}


/* ------------------------------------------------------------- compare
   Two to six takes on one shared position: switching keeps the place in the song, so
   the same moment is heard in each.  Each take has an audio element of its own, loaded
   up front, and only the chosen one plays.  Levels can be matched (quieter takes always
   sound better to the ear, so the louder ones are turned down to the quietest), and the
   names hidden, for a blind listen. */
var COMPARE = { items: [], active: 0, timer: null };

function compareOpen() {
  return !!$('compare-modal') && !$('compare-modal').classList.contains('hidden');
}

/* The picked takes that have audio to play. */
function comparable() {
  return pickedIds().map(takeById).filter(function (take) {
    return take && take.status === 'done' && take.has_audio;
  });
}

function paintCompareButton() {
  var button = $('compare-picked');
  if (!button) { return; }
  var picked = pickedIds().length, ready = comparable().length;
  button.classList.toggle('hidden', picked < 2);
  button.textContent = 'Compare ' + ready;
  button.disabled = ready < 2 || ready > COMPARE_MOST;
  button.title = ready > COMPARE_MOST ? 'Compare holds up to ' + COMPARE_MOST + ' takes: untick some'
    : ready < 2 ? 'Waiting for two ticked takes to finish rendering'
    : 'Play the ticked takes against each other, from the same place in the song';
}

/* The level a take plays at, in dB, or null when the app has not read it. */
function compareLevel(take) {
  var level = take.normalised ? take.normalised_to : take.loudness;
  return typeof level === 'number' && isFinite(level) ? level : null;
}

function compareGain(take, quietest) {
  var level = compareLevel(take);
  if (!$('compare-level').checked || level === null || quietest === null) { return 1; }
  return Math.max(0.05, Math.min(1, Math.pow(10, (quietest - level) / 20)));
}

function applyCompareLevels() {
  var levels = COMPARE.items.map(function (item) { return compareLevel(item.take); });
  var quietest = levels.every(function (level) { return level !== null; }) ? Math.min.apply(null, levels) : null;
  COMPARE.items.forEach(function (item) { item.audio.volume = compareGain(item.take, quietest); });
}

function openCompare() {
  var takes = comparable();
  if (takes.length < 2 || takes.length > COMPARE_MOST) { return; }
  // The main player would talk over it.
  var main = $('audio');
  if (main && !main.paused) { main.pause(); }
  if ($('compare-blind').checked) { shuffleInPlace(takes); }
  COMPARE.items = takes.map(function (take) {
    var audio = new Audio();
    audio.preload = 'auto';
    audio.src = '/api/takes/' + take.id + '/audio' + (take.normalised ? '?level=normalised' : '');
    audio.addEventListener('ended', paintCompareTransport);
    audio.addEventListener('pause', paintCompareTransport);
    audio.addEventListener('play', paintCompareTransport);
    return { take: take, audio: audio };
  });
  COMPARE.active = 0;
  applyCompareLevels();
  paintCompare();
  $('compare-modal').classList.remove('hidden');
  COMPARE.timer = setInterval(paintCompareTransport, 120);
}

function closeCompare() {
  clearInterval(COMPARE.timer);
  COMPARE.items.forEach(function (item) { item.audio.pause(); item.audio.removeAttribute('src'); item.audio.load(); });
  COMPARE.items = [];
  $('compare-modal').classList.add('hidden');
}

function shuffleInPlace(list) {
  for (var i = list.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1)), swap = list[i];
    list[i] = list[j];
    list[j] = swap;
  }
}

function compareMeta(take) {
  var bits = ['seed ' + take.seed];
  if (take.style_lora) { bits.push('Planner ' + Number(take.style_lora_clip != null ? take.style_lora_clip : 1).toFixed(2)); }
  return bits.join(' \u00b7 ');
}

function paintCompare() {
  var blind = $('compare-blind').checked;
  $('compare-list').innerHTML = COMPARE.items.map(function (item, i) {
    var take = item.take;
    return '<div class="compare-item' + (i === COMPARE.active ? ' active' : '') + '" role="button" tabindex="0" data-i="' + i + '">' +
      '<kbd>' + (i + 1) + '</kbd>' +
      '<span class="ci-name">' + (blind ? 'Take ' + String.fromCharCode(65 + i) : esc(take.title)) + '</span>' +
      (blind ? '' : '<span class="ci-meta">' + esc(compareMeta(take)) + '</span>') +
      '<span class="ci-star' + (take.favourite ? ' on' : '') + '" role="button" data-star="' + i + '" title="' +
        (take.favourite ? 'Starred. Click to remove the star' : 'Star this take') + '">' + (take.favourite ? '\u2605' : '\u2606') + '</span>' +
    '</div>';
  }).join('');
  paintCompareTransport();
}

function paintCompareTransport() {
  if (!COMPARE.items.length) { return; }
  var audio = COMPARE.items[COMPARE.active].audio;
  var length = isFinite(audio.duration) ? audio.duration : 0;
  $('compare-play').textContent = audio.paused ? 'Play' : 'Pause';
  if (document.activeElement !== $('compare-seek')) {
    $('compare-seek').value = length ? Math.round(1000 * audio.currentTime / length) : 0;
  }
  $('compare-time').textContent = secs(audio.currentTime) + ' / ' + secs(length);
}

function compareSwitch(i) {
  if (i === COMPARE.active || !COMPARE.items[i]) { return; }
  var from = COMPARE.items[COMPARE.active].audio, to = COMPARE.items[i].audio;
  var at = from.currentTime, playing = !from.paused;
  from.pause();
  COMPARE.active = i;
  var go = function () {
    try { to.currentTime = at; } catch (err) { /* not seekable yet */ }
    if (playing) { to.play().catch(function () {}); }
    paintCompare();
  };
  if (to.readyState >= 1) { go(); } else { to.addEventListener('loadedmetadata', go, { once: true }); paintCompare(); }
}

function compareToggle() {
  var audio = COMPARE.items[COMPARE.active].audio;
  if (audio.paused) { if (audio.ended) { audio.currentTime = 0; } audio.play().catch(function () {}); } else { audio.pause(); }
}

function compareNudge(seconds) {
  var audio = COMPARE.items[COMPARE.active].audio;
  audio.currentTime = Math.max(0, Math.min(isFinite(audio.duration) ? audio.duration : 0, audio.currentTime + seconds));
  paintCompareTransport();
}

async function compareStar(i) {
  var item = COMPARE.items[i];
  if (!item) { return; }
  var take = item.take, want = !take.favourite;
  try {
    await api('/api/takes/' + take.id + '/favourite?value=' + (want ? 'true' : 'false'), { method: 'POST' });
    take.favourite = want ? 1 : 0;
    var listed = takeById(take.id);
    if (listed) { listed.favourite = take.favourite; }
    paintCompare();
    loadTakes();
  } catch (err) {
    statusLine('Could not star that take: ' + err.message, 'bad');
  }
}

function compareKey(event) {
  var digit = /^[1-9]$/.test(event.key) ? Number(event.key) - 1 : -1;
  var tag = (document.activeElement && document.activeElement.tagName) || '';
  if (event.key === 'Escape') { closeCompare(); return true; }
  if (tag === 'INPUT' && document.activeElement.type !== 'range' && document.activeElement.type !== 'checkbox') { return false; }
  if (digit >= 0 && digit < COMPARE.items.length) { compareSwitch(digit); return true; }
  if (event.code === 'Space') { compareToggle(); return true; }
  if (event.key === 'ArrowLeft') { compareNudge(-5); return true; }
  if (event.key === 'ArrowRight') { compareNudge(5); return true; }
  return false;
}

function wireCompare() {
  if (!$('compare-modal')) { return; }   // a page from before Compare, on a new script
  $('compare-picked').addEventListener('click', openCompare);
  $('compare-close').addEventListener('click', closeCompare);
  $('compare-modal').addEventListener('click', function (event) {
    if (backdropClick(event, $('compare-modal'))) { closeCompare(); return; }
    var star = event.target.closest('[data-star]');
    if (star) { compareStar(Number(star.dataset.star)); return; }
    var item = event.target.closest('[data-i]');
    if (item) { compareSwitch(Number(item.dataset.i)); }
  });
  $('compare-play').addEventListener('click', compareToggle);
  $('compare-level').addEventListener('change', applyCompareLevels);
  $('compare-blind').addEventListener('change', function () {
    // Hiding the names shuffles the takes, so their order gives nothing away; the take
    // playing keeps playing, wherever it lands.
    if ($('compare-blind').checked && COMPARE.items.length) {
      var playing = COMPARE.items[COMPARE.active];
      shuffleInPlace(COMPARE.items);
      COMPARE.active = COMPARE.items.indexOf(playing);
    }
    paintCompare();
  });
  $('compare-seek').addEventListener('input', function () {
    var audio = COMPARE.items[COMPARE.active].audio;
    if (isFinite(audio.duration)) { audio.currentTime = audio.duration * Number($('compare-seek').value) / 1000; }
    paintCompareTransport();
  });
}

/* ------------------------------------------------------------- try more
   The same score and words again as a set of new takes: with fresh seeds, or at other
   Planner strengths on this take's seed.  Which roll suits a song is heard, not
   predicted, so the set is made together, and picked ready to compare. */
var TRIES = { take: null };
var TRY_PLANNER = [0.6, 0.8, 1.0];

function triesMode() {
  var chosen = document.querySelector('#tries-modes input:checked');
  return chosen ? chosen.value : 'seeds';
}

function triesPlannerValues() {
  return Array.prototype.map.call(document.querySelectorAll('#tries-values input:checked'), function (box) {
    return parseFloat(box.value);
  });
}

function openTries(take) {
  if (!$('tries-of')) { statusLine('Try more needs the app restarted: this page is from before it.', 'bad'); return; }
  TRIES.take = take;
  $('tries-of').textContent = '\u201c' + take.title + '\u201d';
  // Planner strengths only make sense for a style LoRA with a planner half.
  var kind = take.style_lora ? loraKind(take.style_lora) : '';
  var canPlan = !!take.style_lora && kind !== 'decoder' && kind !== 'other';
  var own = take.style_lora_clip != null ? Number(take.style_lora_clip) : 1;
  $('tries-planner-row').classList.toggle('off', !canPlan);
  $('tries-planner-row').querySelector('input').disabled = !canPlan;
  $('tries-planner-hint').textContent = canPlan
    ? 'this seed, at other Planner strengths (this take: ' + own.toFixed(2) + ')'
    : (take.style_lora ? 'this LoRA has no planner half' : 'needs a style LoRA');
  $('tries-values').innerHTML = TRY_PLANNER.map(function (value) {
    var same = Math.abs(value - own) < 0.005;
    return '<label' + (same ? ' class="own"' : '') + '><input type="checkbox" value="' + value.toFixed(2) + '"' +
      (same ? ' disabled' : ' checked') + '>' + value.toFixed(2) + '</label>';
  }).join('');
  document.querySelector('#tries-modes input[value="seeds"]').checked = true;
  $('tries-count').value = 4;
  $('tries-cap').value = Math.round(take.max_duration || parseFloat($('max-duration').value) || 360);
  $('tries-status').textContent = '';
  paintTries();
  $('tries-modal').classList.remove('hidden');
}

function closeTries() {
  TRIES.take = null;
  $('tries-modal').classList.add('hidden');
}

function triesCount() {
  if (triesMode() === 'planner') { return triesPlannerValues().length; }
  var n = parseInt($('tries-count').value, 10);
  return n >= 1 ? Math.min(n, 8) : 0;
}

function paintTries() {
  var planner = triesMode() === 'planner';
  $('tries-count-field').classList.toggle('hidden', planner);
  $('tries-planner-field').classList.toggle('hidden', !planner);
  var count = triesCount();
  var average = State.options.avg_render_seconds || 0;
  $('tries-go').disabled = !count;
  $('tries-go').textContent = count === 1 ? 'Render 1 take' : 'Render ' + count + ' takes';
  $('tries-estimate').textContent = count && average ? 'about ' + Math.max(1, Math.round(count * average / 60)) + ' min of rendering' : '';
}

async function doTries() {
  var take = TRIES.take;
  if (!take || !triesCount()) { return; }
  var cap = parseFloat($('tries-cap').value);
  if (!(cap >= 10 && cap <= 900)) {
    $('tries-status').textContent = 'The length cap must be between 10 and 900 seconds.';
    $('tries-status').className = 'status bad';
    return;
  }
  var planner = triesMode() === 'planner';
  var body = { mode: planner ? 'planner' : 'seeds', max_duration: cap };
  if (planner) { body.planner = triesPlannerValues(); } else { body.count = triesCount(); }
  try {
    var reply = await api('/api/takes/' + take.id + '/tries', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    closeTries();
    // Ticked, with the original, so they are ready to compare once they have finished.
    var ids = [take.id].concat(reply.created.map(function (made) { return made.id; }));
    if (ids.length <= COMPARE_MOST) {
      State.picked = {};
      ids.forEach(function (made) { State.picked[made] = true; });
    }
    statusLine('Queued ' + reply.created.length + ' take' + (reply.created.length === 1 ? '' : 's') + ' of ' + take.title +
      '.' + (ids.length <= COMPARE_MOST ? ' They are ticked with the original: Compare opens when they have finished.' : ''), 'good');
    loadTakes();
    paintBulk();
  } catch (err) {
    $('tries-status').textContent = 'Could not queue: ' + err.message;
    $('tries-status').className = 'status bad';
  }
}

/* ------------------------------------------------------------- checkpoints
   What this panel would make, once on each checkpoint a training run kept for the
   chosen LoRA, all with one seed, so the LoRA is what differs between them. */
var STEPS = { mode: null };

/* The finished LoRA and its run's checkpoints (name_stepN), in step order, the
   finished one last.  Empty when there are no checkpoints to compare. */
function loraSteps(name) {
  var base = (name || '').replace(/\.safetensors$/i, '').replace(/_step\d+$/i, '');
  if (!base) { return []; }
  var pattern = new RegExp('^' + base.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(_step(\\d+))?\\.safetensors$', 'i');
  var steps = [];
  (State.options.loras || []).forEach(function (item) {
    var found = item && pattern.exec(item.name);
    if (found) { steps.push({ name: item.name, step: found[2] ? parseInt(found[2], 10) : null }); }
  });
  if (!steps.some(function (s) { return s.step !== null; })) { return []; }
  steps.sort(function (a, b) {
    return (a.step === null ? Infinity : a.step) - (b.step === null ? Infinity : b.step);
  });
  return steps;
}

function stepLabel(step) {
  return step.step === null ? 'full' : 'step ' + step.step;
}

var STEP_MODES = {
  cover: { problem: coverProblem, body: coverBody, url: '/api/takes',
           hint: 'Covers this recording once on each checkpoint, with one seed.' },
  song: { problem: songProblem, body: songBody, url: '/api/songs',
          hint: 'Writes and renders a plan on each checkpoint, with one seed. The LoRA shapes the plan too, so each has its own tune.' },
  inst: { problem: instProblem, body: instBody, url: '/api/instrumentals',
          hint: 'Writes and renders a plan on each checkpoint, with one seed. The LoRA shapes the plan too, so each has its own tune.' }
};

function openLoraSteps() {
  var item = loraChosen();
  var steps = item ? loraSteps(item.name) : [];
  var mode = STEP_MODES[State.mode] ? State.mode : 'song';
  if (!steps.length) { return; }
  var problem = STEP_MODES[mode].problem();
  if (problem) { statusLine(problem, 'bad'); return; }
  STEPS.mode = mode;
  // Named after the finished LoRA, whichever step is chosen.
  var finished = steps.filter(function (s) { return s.step === null; })[0];
  var named = finished && loraCatalogue().filter(function (e) { return e.name === finished.name; })[0];
  $('steps-heading').textContent = 'Checkpoints of ' +
    ((named && named.title) || item.name.replace(/\.safetensors$/i, '').replace(/_step\d+$/i, ''));
  $('steps-hint').textContent = STEP_MODES[mode].hint + ' Each lands as its own take, named after its step.';
  $('steps-cap').value = parseFloat($('max-duration').value) || 360;
  $('steps-list').innerHTML = steps.map(function (s) {
    return '<label><input type="checkbox" value="' + esc(s.name) + '" data-label="' + stepLabel(s) + '" checked><strong>' +
      (s.step === null ? 'Full' : 'Step ' + s.step) + '</strong><span class="muted">' +
      (s.step === null ? 'The LoRA the training run kept' : '') + '</span></label>';
  }).join('');
  $('steps-status').textContent = '';
  paintStepsEstimate();
  $('steps-modal').classList.remove('hidden');
}

function closeLoraSteps() {
  STEPS.mode = null;
  $('steps-modal').classList.add('hidden');
}

function chosenSteps() {
  return Array.prototype.slice.call(document.querySelectorAll('#steps-list input:checked'));
}

function paintStepsEstimate() {
  var count = chosenSteps().length;
  var average = (State.options.avg_render_seconds || 0) + (STEPS.mode === 'cover' ? 0 : State.options.avg_plan_seconds || 0);
  $('steps-go').disabled = !count;
  $('steps-go').textContent = count === 1 ? 'Render 1 take' : 'Render ' + count + ' takes';
  $('steps-estimate').textContent = count && average ? 'about ' + Math.max(1, Math.round(count * average / 60)) + ' min of rendering' : '';
}

async function runLoraSteps() {
  var mode = STEP_MODES[STEPS.mode];
  var chosen = chosenSteps();
  if (!mode || !chosen.length) { return; }
  var cap = parseFloat($('steps-cap').value);
  if (!(cap >= 10 && cap <= 900)) {
    $('steps-status').textContent = 'The length cap must be between 10 and 900 seconds.';
    $('steps-status').className = 'status bad';
    return;
  }
  var problem = mode.problem();
  if (problem) { $('steps-status').textContent = problem; $('steps-status').className = 'status bad'; return; }
  var seed = pickSeed();
  $('steps-go').disabled = true;
  var queued = 0;
  try {
    for (var i = 0; i < chosen.length; i++) {
      var body = mode.body(seed);
      body.style_lora = chosen[i].value;
      body.title = (body.title || (STEPS.mode === 'inst' ? 'Untitled instrumental' : 'Untitled')) + ' \u00b7 ' + chosen[i].dataset.label;
      body.max_duration = cap;
      // To be heard, so a plan goes straight on to its render.
      if (STEPS.mode !== 'cover') { body.auto_render = true; }
      await api(mode.url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      queued += 1;
    }
    closeLoraSteps();
    statusLine('Queued ' + queued + ' take' + (queued === 1 ? '' : 's') + ', one on each checkpoint, with seed ' + seed + '.', 'good');
  } catch (err) {
    $('steps-status').textContent = (queued ? 'Queued ' + queued + ', then could not queue the rest: ' : 'Could not queue: ') + err.message;
    $('steps-status').className = 'status bad';
  } finally {
    $('steps-go').disabled = false;
    loadTakes();
  }
}

/* ------------------------------------------------------------------ lyrics
   A draft from a short brief, written on the engine.  It lands in the lyrics box
   even if this window was closed while it was being written. */
var WRITE = { id: null, timer: null, started: null, status: null };

var FEEL_KEY = 'yue2.lyricfeel';

/* The choices for how the lines sound come with the page's options; the last one picked is remembered. */
function paintWriteFeel() {
  var select = $('write-feel');
  var feels = (State.options && State.options.lyric_feels) || [];
  if (!select || !feels.length) { return; }
  if (select.options.length !== feels.length) {
    var saved = null;
    try { saved = localStorage.getItem(FEEL_KEY); } catch (err) { saved = null; }
    select.innerHTML = feels.map(function (feel) {
      return '<option value="' + esc(feel.id) + '" title="' + esc(feel.hint) + '">' + esc(feel.label) + '</option>';
    }).join('');
    if (saved && feels.some(function (feel) { return feel.id === saved; })) { select.value = saved; }
  }
  var picked = feels.filter(function (feel) { return feel.id === select.value; })[0];
  if ($('write-feel-hint')) { $('write-feel-hint').textContent = picked ? picked.hint : ''; }
}

function openWrite() {
  paintWriteFeel();
  if ($('write-structure-sent')) { $('write-structure-sent').textContent = SONGPLAN.sections.join(', '); }
  $('write-modal').classList.remove('hidden');
  if (!WRITE.id) { $('write-status').textContent = ''; }
  $('write-brief').focus();
}

function closeWrite() {
  $('write-modal').classList.add('hidden');
}

function setWriting(on) {
  $('write-go').disabled = on;
  $('write-stop').classList.toggle('hidden', !on);
  var btn = $('lyrics-write');
  if (btn) {
    btn.textContent = on ? 'Drafting\u2026' : 'Write lyrics';
    btn.classList.toggle('active', on);
  }
  if (!on) {
    var box = $('lyrics-write-job');
    if (box && !box.classList.contains('bad')) {
      box.classList.add('hidden');
    }
  }
}

function writeStatus(text, tone) {
  $('write-status').textContent = text;
  $('write-status').className = 'status' + (tone ? ' ' + tone : '');
}

async function doWrite() {
  var brief = $('write-brief').value.trim();
  if (!brief) { writeStatus('Say in a few words what the song is about.', 'bad'); $('write-brief').focus(); return; }
  if ($('lyrics').value.trim() && !await confirmModal({
    title: 'Replace lyrics',
    message: 'The draft will replace the lyrics in the box. Write it?',
    confirmText: 'Write lyrics',
    danger: true
  })) { return; }
  try {
    var draft = await api('/api/lyrics', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brief: brief, style: $('style').value, sections: SONGPLAN.sections, lines: Number($('write-lines').value) || 6, feel: $('write-feel') ? $('write-feel').value : undefined })
    });
    WRITE.id = draft.id;
    WRITE.started = Date.now();
    WRITE.status = draft.status || 'queued';
    setWriting(true);
    writeStatus('Waiting for the engine\u2026 The words land in the lyrics box.');
    statusLine('Drafting lyrics\u2026 The words land in the lyrics box.', 'wait');
    paintWriteJob(State.currentJob, []);
    closeWrite();      // the progress is shown beside the lyrics box now
    clearTimeout(WRITE.timer);
    WRITE.timer = setTimeout(pollWrite, 1500);
  } catch (err) {
    writeStatus('Could not start: ' + err.message, 'bad');
  }
}

async function pollWrite() {
  if (!WRITE.id) { return; }
  var draft;
  try {
    draft = await api('/api/lyrics/' + WRITE.id);
  } catch (err) {
    WRITE.id = null;
    WRITE.started = null;
    setWriting(false);
    var errText = 'Lost the draft: ' + err.message;
    writeStatus(errText, 'bad');
    statusLine(errText, 'bad');
    showWriteError(errText);
    return;
  }
  WRITE.status = draft.status;
  if (draft.status === 'done' || draft.status === 'failed') {
    WRITE.id = null;
    WRITE.started = null;
    setWriting(false);
    if (draft.status === 'done') {
      var box = $('lyrics-write-job');
      if (box) { box.classList.add('hidden'); box.classList.remove('bad'); }
      landDraft(draft);
    } else {
      var msg = draft.error === 'cancelled' ? 'Stopped drafting lyrics.' : ('Could not write the lyrics: ' + draft.error);
      writeStatus(msg, 'bad');
      statusLine(msg, 'bad');
      showWriteError(msg);
    }
    return;
  }
  var statusMsg = draft.status === 'running' ? 'Writing lyrics\u2026'
    : 'Waiting for the engine\u2026 The words land in the lyrics box.';
  writeStatus(statusMsg);
  paintWriteJob(State.currentJob, []);
  WRITE.timer = setTimeout(pollWrite, 2000);
}

function landDraft(draft) {
  $('lyrics').value = draft.lyrics; paintSongPlan();
  if (!$('title').value.trim() && draft.title) { $('title').value = draft.title; }
  State.formEdited = true;
  $('lyrics').dispatchEvent(new Event('input'));
  saveForm();
  closeWrite();
  writeStatus('');
  statusLine('Draft lyrics are in the box. Read them and make them yours, then Write score plan.', 'good');
}

async function stopWrite() {
  if (!WRITE.id) { return; }
  var stageEl = $('lyrics-write-stage');
  if (stageEl) { stageEl.textContent = 'Stopping\u2026'; }
  writeStatus('Stopping\u2026');
  statusLine('Stopping lyrics draft\u2026', 'wait');
  try { await api('/api/lyrics/' + WRITE.id + '/cancel', { method: 'POST' }); } catch (err) { /* the poll reports it */ }
}

/* ---------------------------------------------------------------- identities
   A folder of songs (an artist, a genre, a few similar artists), prepared for
   training a style LoRA.  The folder is only read;
   the app keeps its own copies, and the review happens here, song by song. */
var IDENTITY = { view: 'list', id: null, data: null, open: {}, timer: null, browse: null };
var PERSONA = IDENTITY;
var STEP_NAMES_ALL = [['vocals_state', 'Vocal'], ['score_state', 'Key & tempo'], ['lyrics_state', 'Lyrics'], ['style_state', 'Style']];
var STEP_NAMES = STEP_NAMES_ALL;
var STEP_MARKS = { none: '', queued: '· queued', running: '…', done: '✓', failed: '✕' };

function getIdentityModal() { return $('identities-modal') || $('personas-modal'); }
function getIdentityHeading() { return $('identities-heading') || $('personas-heading'); }
function getIdentityBack() { return $('identities-back') || $('personas-back'); }
function getIdentityClose() { return $('identities-close') || $('personas-close'); }
function getIdentityBody() { return $('identities-body') || $('personas-body'); }

function openIdentities() {
  closeBrandMenu();
  var modal = getIdentityModal();
  if (modal) { modal.classList.remove('hidden'); }
  document.body.style.overflow = 'hidden';
  showIdentityList();
}
var openPersonas = openIdentities;

function closeIdentities() {
  var modal = getIdentityModal();
  if (modal) {
    modal.classList.add('hidden');
    // Hidden, a song under review would play on with no way to stop it.
    Array.prototype.forEach.call(modal.querySelectorAll('audio'), function (audio) { audio.pause(); });
  }
  document.body.style.overflow = '';
  clearTimeout(IDENTITY.timer);
  IDENTITY.timer = null;
  loadVocalIdentities();
}
var closePersonas = closeIdentities;

async function showIdentityList() {
  IDENTITY.view = 'list';
  IDENTITY.id = null;
  clearTimeout(IDENTITY.timer);
  var heading = getIdentityHeading();
  if (heading) { heading.textContent = 'Corpora'; }
  var back = getIdentityBack();
  if (back) { back.classList.add('hidden'); }
  var list = [];
  try { list = await api('/api/identities'); } catch (err) {
    try { list = await api('/api/personas'); } catch (e) { list = []; }
  }
  var body = getIdentityBody();
  if (!body) { return; }
  body.innerHTML =
    '<p class="identity-intro persona-intro">A corpus is a folder of recordings, prepared as a training set. ' +
    'Point at a folder: the app separates each vocal, finds its key and tempo, and drafts its lyrics for you ' +
    'to check. Then export the set and train it' + (trainingAvailable() ? ' — here, or anywhere else' : ' with the trainer of your choice') + '.</p>' +
    '<div class="row"><button id="identity-new" class="ghost">New corpus</button>' +
    '<button id="identity-import" class="ghost" title="Add a LoRA someone shared: the zip from their Download LoRA, or a .safetensors file">Import LoRA</button>' +
    '<input id="identity-import-file" type="file" accept=".zip,.safetensors" class="hidden">' +
    '<span id="identity-import-status" class="status"></span></div>' +
    '<div class="identity-cards persona-cards">' + list.map(function (item) {
      // The dot and the word are always here and shown by the card's class: the poll marks
      // a card rather than redrawing the list, which would move it out from under a click.
      return '<div class="identity-card persona-card" data-identity="' + esc(item.id) + '" data-persona="' + esc(item.id) + '">' +
        '<strong><span class="corpus-dot" aria-hidden="true"></span>' + esc(item.name) + '</strong>' +
        '<span class="muted">trigger <code>' + esc(item.trigger_word) + '</code> · ' + (item.included || 0) + ' of ' +
        (item.songs || 0) + ' songs' + (item.exported_at ? ' · exported' : '') + '</span>' +
        '<span class="corpus-preparing">preparing…</span></div>';
    }).join('') + '</div>';
  paintCorpusCards();
}

/* Which corpora are being prepared, said on their own cards.  The top bar's badge knows it
   already, but it shows one corpus and this screen may hold a dozen: whoever is looking at
   the cards is looking here.  Marking rather than redrawing keeps clicks and the scroll
   where they were, and the progress comes from the poll that is already running. */
function paintCorpusCards() {
  var cards = document.querySelectorAll('.identity-card[data-identity]');
  Array.prototype.forEach.call(cards, function (card) {
    var item = (State.corpusProgress || {})[card.getAttribute('data-identity')];
    var busy = Boolean(item && item.busy);
    card.classList.toggle('busy', busy);
    if (busy) {
      card.title = esc(item.name) + ': ' + item.done + ' of ' + item.total + ' songs settled, still working.';
    } else if (card.title) {
      card.removeAttribute('title');
    }
  });
}
var showPersonaList = showIdentityList;

function triggerFrom(name) {
  return String(name || '').toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 24);
}

async function showIdentityNew() {
  IDENTITY.view = 'new';
  var heading = getIdentityHeading();
  if (heading) { heading.textContent = 'New corpus'; }
  var back = getIdentityBack();
  if (back) { back.classList.remove('hidden'); }
  var body = getIdentityBody();
  if (!body) { return; }
  body.innerHTML =
    '<div class="identity-form persona-form">' +
      '<div class="field"><label for="pn-name">Name</label><input id="pn-name" type="text" maxlength="80" placeholder="Paul Shields"></div>' +
      '<div class="field"><label for="pn-trigger">Trigger word</label><input id="pn-trigger" type="text" maxlength="40" placeholder="paulshields">' +
        '<div class="hint">Starts every style caption, so a trained LoRA knows when to act. Letters and digits only.</div></div>' +
      '<div class="field"><label for="pn-voice">Voice</label><select id="pn-voice"><option value="male">male</option>' +
        '<option value="female">female</option><option value="">not stated</option><option value="none">none</option></select>' +
        '<div class="hint">None is for songs without vocals: they are not separated or listened to for words.</div></div>' +
      '<div class="field"><label for="pn-desc">The sound, for every song</label><input id="pn-desc" type="text" maxlength="400" ' +
        'placeholder="pop rock, electric guitars, bass, drums">' +
        '<div class="hint">Goes into each caption, with each song’s own key and tempo.</div></div>' +
      '<div class="field wide"><label>Folder of songs</label><div id="pn-folder" class="folder-pick"></div>' +
        '<div class="hint">Only read: nothing in it is changed.</div></div>' +
      '<label class="check wide"><input id="pn-consent" type="checkbox"> I have the right to train on these recordings.</label>' +
      '<div class="wide row" style="margin-top:10px"><button id="pn-scan" class="ghost">Scan the folder</button>' +
        '<span id="pn-status" class="status"></span></div>' +
    '</div>';
  $('pn-name').addEventListener('input', function () {
    if (!$('pn-trigger').dataset.touched) { $('pn-trigger').value = triggerFrom($('pn-name').value); }
  });
  $('pn-trigger').addEventListener('input', function () { $('pn-trigger').dataset.touched = '1'; });
  browseFolder(null);
  $('pn-name').focus();
}
var showPersonaNew = showIdentityNew;

async function browseFolder(path) {
  var host = $('pn-folder');
  try {
    var data = await api('/api/import/browse' + (path ? '?path=' + encodeURIComponent(path) : ''));
    IDENTITY.browse = data;
    // Up a level, and from the top of an import folder back to the list of them: the
    // server gives no parent there, and without this the only way back was to close
    // the window and start again. It sits in the header, apart from the folders, and
    // the header stays in view while the list scrolls.
    var back = data.parent ? '<button class="folder-back" data-folder="' + esc(data.parent) + '">\u2190 up</button>'
      : '<button class="folder-back" data-folder="">\u2190 all folders</button>';
    var html = data.path ? '<div class="here"><span>' + esc(data.path) + ' · ' + data.songs + ' song' +
      (data.songs === 1 ? '' : 's') + ' here</span>' + back + '</div>' : '';
    html += data.folders.map(function (folder) {
      // The list of import folders shows them whole; inside one, a folder is its own
      // name. Windows paths use backslashes, which a split on "/" never found.
      var name = data.path ? folder.split(/[\\/]/).filter(Boolean).pop() || folder : folder;
      return '<button data-folder="' + esc(folder) + '">▸ ' + esc(name) + '</button>';
    }).join('');
    if (!data.path && !data.folders.length) { html = '<div class="here">No import folders are mounted. See the README.</div>'; }
    host.innerHTML = html;
  } catch (err) {
    host.innerHTML = '<div class="here">' + esc(err.message) + '</div>';
  }
}

async function scanNewIdentity() {
  var status = $('pn-status');
  var folder = IDENTITY.browse && IDENTITY.browse.path;
  if (!folder) { status.textContent = 'Open the folder that holds the songs.'; status.className = 'status bad'; return; }
  if (!$('pn-consent').checked) { status.textContent = 'Confirm that the voice is yours, or that you have permission.'; status.className = 'status bad'; return; }
  status.textContent = 'Scanning…';
  status.className = 'status';
  $('pn-scan').disabled = true;
  try {
    var made = await api('/api/identities', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: $('pn-name').value.trim() || 'My voice', trigger_word: $('pn-trigger').value || triggerFrom($('pn-name').value) || 'myvoice',
        voice: $('pn-voice').value, description: $('pn-desc').value, folder: folder, consent: true })
    });
    showIdentity(made.id, made);
  } catch (err) {
    status.textContent = err.message;
    status.className = 'status bad';
    $('pn-scan').disabled = false;
  }
}
var scanNewPersona = scanNewIdentity;

function stepChips(song) {
  // A corpus without vocals has no vocal to separate, and its lyrics are section tags.
  var names = IDENTITY.data && IDENTITY.data.vocalless
    ? [['score_state', 'Key & tempo'], ['lyrics_state', 'Sections'], ['style_state', 'Style']] : STEP_NAMES_ALL;
  return names.map(function (step) {
    var state = song[step[0]] || 'none';
    return '<span class="step ' + state + '">' + step[1] + (STEP_MARKS[state] ? ' ' + STEP_MARKS[state] : '') + '</span>';
  }).join('');
}

function identitySummary(data) {
  var sum = data.summary;
  return '<span><strong>' + sum.included + '</strong> of ' + sum.songs + ' songs included · ' + sum.minutes + ' min</span>' +
    '<span>' + sum.analysed + ' analysed' + (data.vocalless ? '' : ' · ' + sum.checked + ' lyrics checked') + '</span>' +
    '<span class="muted">trigger <code>' + esc(data.trigger_word) + '</code> · ' + esc(data.vocalless ? 'no vocals' : (data.voice || 'voice not stated')) +
    ' · ' + esc(data.description || 'no description') + '</span>';
}
var personaSummary = identitySummary;

function songRow(song) {
  var detail = IDENTITY.open[song.id]
    ? '<tr class="identity-detail persona-detail" data-detail="' + song.id + '"><td colspan="5">' + songDetail(song) + '</td></tr>' : '';
  return '<tr data-song="' + song.id + '"' + (song.include ? '' : ' class="off"') + '>' +
    '<td><input type="checkbox" data-include="' + song.id + '"' + (song.include ? ' checked' : '') +
      (song.too_long ? ' disabled title="Too long to analyse: split it into tracks first"' : ' title="Include in the training set"') + '></td>' +
    // A track cut from an album is stored by its full path; its name is enough here.
    '<td>' + esc(song.title) + '<span class="file">' + esc(String(song.file).split('/').pop()) + '</span>' +
      (song.flag ? '<span class="flag">' + esc(song.flag) + '</span>' : '') +
      (song.cue ? ' <button class="link" data-split="' + song.id + '" title="' + esc(song.cue.file) +
        ' says where each track starts. Each becomes a song in this corpus; the folder is not changed">Split into ' +
        song.cue.tracks + ' tracks</button>' : '') + '</td>' +
    '<td>' + secs(song.duration) + (song.trained_to
      ? '<div class="muted" title="Songs longer than the training limit are cut for training, at the end of a section where one is near, and faded out. Its words stop there too.">first ' +
        secs(song.trained_to) + ' trained</div>' : '') + '</td>' +
    '<td data-steps="' + song.id + '">' + stepChips(song) + '<div class="muted" data-keytempo="' + song.id + '">' +
      esc([song.key, song.tempo ? song.tempo + ' BPM' : ''].filter(Boolean).join(', ')) + '</div></td>' +
    '<td><button class="link" data-open="' + song.id + '">' + (IDENTITY.open[song.id] ? 'Close' : 'Review') + '</button></td>' +
  '</tr>' + detail;
}

/* When both versions of a song's words were kept, a switch for which one is in use. */
function lyricsSourceRow(song) {
  var v = song.lyrics_versions;
  if (!v || !v.llm || !v.whisper) { return ''; }
  var chip = function (key, label, words) {
    return '<button type="button" class="chip' + (v.active === key ? ' active' : '') + '" data-lyrics-source="' + key +
      '" data-song="' + song.id + '" title="Use the words ' + (key === 'llm' ? 'the external model heard' : 'Whisper heard') +
      '. They go in the box, replacing what is there">' + esc(label) + ' \u00b7 ' + words + ' words</button>';
  };
  return '<div class="lyrics-source" data-for="' + song.id + '" data-active="' + esc(v.active || '') + '">Words from ' + chip('llm', v.llm.model || 'the external model', v.llm.words) +
    chip('whisper', 'Whisper', v.whisper.words) + '</div>';
}

function songDetail(song) {
  var vocalless = Boolean(IDENTITY.data && IDENTITY.data.vocalless);
  var base = '/api/identities/' + IDENTITY.id + '/songs/' + song.id + '/audio';
  var players = song.stored_path
    ? '<div class="muted">Your recording</div><audio controls preload="none" src="' + base + '?which=original"></audio>' +
      (song.vocals_state === 'done' && !vocalless ? '<div class="muted">The separated vocal</div><audio controls preload="none" src="' + base + '?which=vocals"></audio>' : '')
    : '<p class="muted">Press Analyse to copy this song in.</p>';
  return '<div class="grid"><div>' +
      (vocalless
        ? '<div class="label-row"><label>Sections</label></div>'
        : '<div class="label-row"><label>Lyrics' + (song.lyrics_state === 'done' && !song.lyrics_checked ? ' <span class="muted">(a draft)</span>' : '') +
          '</label><label class="check"><input type="checkbox" data-checked="' + song.id + '"' + (song.lyrics_checked ? ' checked' : '') + '> checked</label></div>' +
          lyricsSourceRow(song)) +
      '<textarea data-lyrics="' + song.id + '" spellcheck="false" placeholder="[Verse]&#10;...">' + esc(song.lyrics || '') + '</textarea>' +
      '<div class="row" style="margin-top:6px"><button class="ghost" data-save="' + song.id + '">Save</button>' +
      (song.lyrics_state === 'done' && !vocalless && IDENTITY.data && IDENTITY.data.external_llm
        ? '<button class="ghost" data-redraft="' + song.id + '" title="Draft the lyrics again from what was heard: the same words, with the sections marked afresh. Replaces what is in the box">Redraft</button>'
        : '') +
      '<span class="status" data-saved="' + song.id + '"></span></div>' +
    '</div><div>' + players +
      '<div class="field" style="margin:10px 0 0"><label for="pd-' + song.id + '">This song\u2019s sound</label>' +
      '<input id="pd-' + song.id + '" type="text" maxlength="400" data-description="' + song.id + '" value="' + esc(song.description || '') + '" ' +
      'placeholder="' + esc((IDENTITY.data && IDENTITY.data.description) || 'the corpus\u2019s description') + '">' +
      '<div class="hint">Only where it differs from the rest, say stripped back or acoustic. Blank uses the corpus\u2019s. Saved with Save.</div></div>' +
      '<div class="muted" style="margin-top:8px">Style caption</div><div class="caption" data-caption="' + song.id + '">' + esc(song.caption) + '</div>' +
      (song.style_hint ? '<div class="muted" style="margin-top:8px; display:flex; justify-content:space-between; align-items:center"><span>Style suggestion</span><button class="restyle" data-restyle="' + song.id + '">Re-analyse</button></div><div class="caption">' + esc(song.style_hint) + '</div>' : '<div style="margin-top:8px"><button class="restyle" data-restyle="' + song.id + '">Analyse style</button></div>') +
      (song.error ? '<div class="status bad" style="margin-top:8px">' + esc(song.error) + '</div>' : '') +
    '</div></div>';
}

function renderIdentityActions(data) {
  var sum = data.summary || {};
  var included = sum.included || 0;
  var analysed = sum.analysed || 0;
  var isAnalysed = included > 0 && analysed >= included;
  var isAnalysing = Boolean(data.busy && !isAnalysed);
  var isExported = Boolean(data.exported_at);
  var isTrained = Boolean(data.lora);
  var isTraining = Boolean(State.training && State.training.identity_id === data.id);

  // Determine current active step (1: analyse, 2: export, 3: train, 4: all done)
  var nextStep = 1;
  if (isAnalysed) {
    nextStep = isExported ? 3 : 2;
  }
  if (isTrained) {
    nextStep = 4;
  }

  // 1. Analyse button
  var analyseLabel = isAnalysing ? 'Analysing\u2026' : (isAnalysed ? 'Analysed \u2713' : 'Analyse');
  var analyseClass = 'ghost' + (isAnalysed ? ' done' : (nextStep === 1 ? ' next-step' : ''));
  var analyseTitle = isAnalysed ? 'All ' + included + ' songs analysed (click to re-analyse)' : 'Analyse vocals, chords, key, tempo and lyrics';

  // 2. Export button
  var isExporting = Boolean(data.exporting);
  var exportLabel = isExporting ? 'Exporting\u2026' : (isExported ? 'Exported \u2713' : 'Export training set');
  var exportClass = 'ghost' + (isExported ? ' done' : (nextStep === 2 ? ' next-step' : ''));
  var exportDisabled = ((!isAnalysed && !isExported) || isExporting) ? ' disabled' : '';
  var exportTitle = isExported ? 'Training set exported (click to export again)' : (isAnalysed ? 'Export audio and captions for training' : 'Analyse songs first');

  // 3. Train button (if training available)
  var trainHtml = '';
  if (trainingAvailable()) {
    var trainLabel = isTraining ? 'Training\u2026' : (isTrained ? 'Trained \u2713' : 'Train a LoRA');
    var trainClass = 'ghost' + (isTrained ? ' done' : (nextStep === 3 ? ' next-step' : ''));
    var trainDisabled = (!isExported || isTraining || isExporting) ? ' disabled' : '';
    var trainTitle = isTrained ? 'LoRA trained (' + esc(data.lora) + '). Click to re-train.' : (isExported ? 'Train a dual-branch LoRA from this corpus' : 'Export the training set first');
    trainHtml = '<span class="pipeline-sep">\u203a</span><button id="identity-train" class="' + trainClass + '"' + trainDisabled + ' title="' + trainTitle + '">' + trainLabel + '</button>';
  }

  // 4. Run all: the three, one after the other, on the server. It stays plain, so it
  // still stands out once the three have turned green.
  var runAll = data.run_all || null;
  var chaining = Boolean(runAll && ['analysing', 'exporting', 'waiting'].indexOf(runAll.stage) >= 0);
  var runAllHtml = '';
  if (trainingAvailable()) {
    var runAllBusy = chaining || isAnalysing || isExporting || Boolean(State.training);
    runAllHtml = '<button id="identity-run-all" class="ghost run-all"' + (runAllBusy ? ' disabled' : '') +
      ' title="Analyse, export and train, one after the other, without waiting for each">' +
      (chaining ? 'Running all\u2026' : 'Run all') + '</button>';
  }

  return '<div class="identity-actions persona-actions">' +
    '<div class="identity-pipeline">' +
      '<button id="identity-analyse" class="' + analyseClass + '"' + (isAnalysing ? ' disabled' : '') + ' title="' + analyseTitle + '">' + analyseLabel + '</button>' +
      (isAnalysing && !chaining ? '<button id="identity-stop" class="ghost small" title="Stop the analysis. Finished steps are kept, and Analyse carries on from here">Stop</button>' : '') +
      '<span class="pipeline-sep">\u203a</span>' +
      '<button id="identity-export" class="' + exportClass + '"' + exportDisabled + ' title="' + exportTitle + '">' + exportLabel + '</button>' +
      trainHtml + runAllHtml +
    '</div>' +
    '<div class="identity-utils">' +
      '<button id="identity-edit-open" class="ghost small">Edit</button>' +
      '<button id="identity-install" class="ghost small" title="Install an external LoRA safetensors file">Install a LoRA</button>' +
      (data.lora ? '<button id="identity-download" class="ghost small" title="This corpus\u2019s LoRA and its note, learned styles included, in one zip to give to someone else">Download LoRA</button>' : '') +
      '<button id="identity-delete" class="ghost small danger">Delete corpus</button>' +
    '</div>' +
    '<input id="identity-lora-file" type="file" accept=".safetensors" class="hidden">' +
    '<span id="identity-status" class="status"></span>' +
    (isAnalysing ? '<div class="identity-working">' + identityWorking(data) + '</div>' : '') +
    (isExporting ? '<div class="identity-working">' + identityExporting(data.exporting) + '</div>' : '') +
    (isTraining ? '<div class="identity-working">' + identityTraining(State.training) + '</div>' : '') +
    identityRunAll(runAll) +
    (isTraining ? '' : identityLastRun(data)) +
  '</div>';
}

/* How the corpus's last training run ended, when it did not simply finish: when,
   why, how far it got, and, when it saved enough, a way to finish it from that
   without training again. */
function identityLastRun(data) {
  var run = data.last_run;
  if (!run) { return ''; }
  var when = function (stamp) {
    if (!stamp) { return ''; }
    var at = new Date(stamp * 1000);
    var today = at.toDateString() === new Date().toDateString();
    return ' at ' + at.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) +
      (today ? '' : ' on ' + at.toLocaleDateString([], { day: 'numeric', month: 'short' }));
  };
  if (run.state === 'failed' || run.state === 'cancelled') {
    var saved = run.saved || {};
    var why = run.state === 'cancelled' || run.error === 'cancelled' ? 'stopped' : (run.error || 'failed');
    var after = saved.last_step ? ', after step ' + saved.last_step + ' of ' + run.steps : '';
    return '<div class="identity-working bad">Training ended early' + when(run.finished_at) + ': ' + esc(why) + esc(after) + '.' +
      (saved.finishable ? ' <button id="identity-finish-run" class="ghost small" data-run="' + esc(run.id) + '" title="' +
        'Make what it saved the LoRA, as a finished run does, with its checkpoints under it. No GPU time.">' +
        'Finish with what it saved</button>' : '') + '</div>';
  }
  if (run.state === 'done' && run.stage && run.stage.indexOf('finished from') === 0) {
    return '<div class="identity-working muted">The LoRA was ' + esc(run.stage) + when(run.finished_at) + '.</div>';
  }
  return '';
}

/* Where Run all has got to, with its Stop, and the songs it had to leave out. */
function identityRunAll(run) {
  if (!run) { return ''; }
  var next = { analysing: 'analysing, then export and train', exporting: 'exporting, then train',
               waiting: 'waiting for the engine to be free, then train' }[run.stage];
  var html = '';
  if (next) {
    html += '<div class="identity-working">Run all: ' + next + '. ' +
      '<button id="identity-run-all-stop" class="ghost small" title="Stop here. Finished steps are kept">Stop</button></div>';
  } else if (run.stage === 'failed') {
    html += '<div class="identity-working bad">Run all stopped: ' + esc(run.error || 'unknown error') + '</div>';
  }
  if (run.left_out && run.left_out.length && run.stage !== 'analysing') {
    html += '<div class="identity-working muted">Left out, as their analysis did not finish: ' +
      esc(run.left_out.join(', ')) + '.</div>';
  }
  return html;
}

/* Training, from the corpus window: what it will do, and what happens to a LoRA an
   earlier run left under the same name -- kept under a dated name, or deleted. */
function openTrain(all) {
  var data = IDENTITY.data || {};
  var included = (data.songs || []).filter(function (song) { return song.include; }).length;
  State.trainAll = Boolean(all);
  $('train-heading').textContent = (all ? 'Run all for ' : 'Train a LoRA from ') + (data.name || 'this corpus');
  if (all) {
    var unchecked = data.vocalless ? 0 : included - ((data.summary && data.summary.checked) || 0);
    $('train-about').textContent = 'Analyses the ' + included + ' included song' + (included === 1 ? '' : 's') +
      ' where they still need it, writes the training set, then trains a LoRA from it, one after the other. It carries on ' +
      'with this page closed. A song whose analysis fails is left out, and named.' +
      (unchecked > 0 ? ' ' + unchecked + ' song' + (unchecked === 1 ? '\u2019s lyrics haven\u2019t' : 's\u2019 lyrics haven\u2019t') +
        ' been checked: their drafts are used as they are.' : '');
  } else {
    $('train-about').textContent = 'From ' + included + ' song' + (included === 1 ? '' : 's') + '. It can take a long time, and the GPU ' +
      'is not available to the app until it finishes. Progress shows here and on the main screen, where you can stop it.';
  }
  $('train-go').textContent = all ? 'Run all' : 'Train';
  var previous = data.previous_lora;
  $('train-previous').classList.toggle('hidden', !previous);
  if (previous) {
    $('train-previous-label').textContent = 'This corpus already has a LoRA, trained ' + previous.day + '.';
    $('train-keep-text').textContent = 'Keep it, as \u201c' + previous.keep_as + '\u201d';
    document.querySelector('input[name="train-previous"][value="keep"]').checked = true;
  }
  $('train-status').textContent = '';
  $('train-go').disabled = false;
  paintTrainMemory();
  $('train-modal').classList.remove('hidden');
}

/* Training needs about 12.5 GB of GPU memory, measured on a 16 GB card, most of it
   while it prepares the songs, so short of that it can fail some minutes in. Said
   before it starts, and kept current while the window is open. A warning, not a
   refusal: whatever holds the memory may let go of it in time. */
var TRAIN_NEEDS_GB = 12.5;

function paintTrainMemory() {
  var note = $('train-memory');
  if (!note) { return; }
  var gpu = State.gpu;
  var gb = function (bytes) { return bytes / 1073741824; };
  var text = '';
  if (gpu && gpu.vram_total) {
    // What the engine holds itself, it lets go of before training.
    var usable = gb((gpu.vram_free || 0) + (gpu.engine_vram || 0));
    if (gb(gpu.vram_total) < TRAIN_NEEDS_GB) {
      text = 'This GPU has ' + gb(gpu.vram_total).toFixed(1) + ' GB, and training needs about ' + TRAIN_NEEDS_GB +
        ' GB. It may run out of memory.';
    } else if (usable < TRAIN_NEEDS_GB) {
      text = 'Only ' + usable.toFixed(1) + ' GB of GPU memory is free, and training needs about ' + TRAIN_NEEDS_GB +
        ' GB. Close anything else using the GPU first, or it may run out.';
    }
  }
  note.textContent = text;
  note.classList.toggle('hidden', !text);
}

function closeTrain() { $('train-modal').classList.add('hidden'); }

async function runTrain() {
  var data = IDENTITY.data || {};
  var body = {};
  if (data.previous_lora) { body.previous = document.querySelector('input[name="train-previous"]:checked').value; }
  $('train-go').disabled = true;
  try {
    if (State.trainAll) {
      await api('/api/identities/' + IDENTITY.id + '/run-all', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
      });
      closeTrain();
      pollIdentity();
      return;
    }
    var started = await api('/api/identities/' + IDENTITY.id + '/train', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    closeTrain();
    await pollState();
    pollIdentity();
    var note = $('identity-status');
    if (note) {
      note.textContent = 'Training ' + started.lora_name + ' from ' + started.songs + ' songs, ' + started.steps + ' steps.';
      note.className = 'status good';
    }
  } catch (err) {
    $('train-status').textContent = err.message;
    $('train-status').className = 'status bad';
    $('train-go').disabled = false;
  }
}

/* How far the training of this corpus's LoRA has got. */
function identityTraining(run) {
  var job = State.currentJob && State.currentJob.kind === 'train' ? State.currentJob : null;
  var what = (job && (job.label || job.stage)) || run.stage || (run.state === 'queued' ? 'Waiting for the engine' : 'Starting');
  var steps = job && job.value && job.max ? ' \u00b7 ' + job.value + ' of ' + job.max : '';
  var progress = job && job.progress ? job.progress : run.progress;
  var pct = progress > 0 ? ', ' + Math.round(progress * 100) + '%' : '';
  var elapsed = (job && job.elapsed) || run.elapsed;
  var since = elapsed ? ' \u00b7 ' + clock(elapsed) : '';
  return 'Training ' + esc(run.lora_name || 'the LoRA') + ': ' + esc(what) + steps + pct + since;
}

/* How far writing the training set has got. */
function identityExporting(e) {
  var since = e.since ? ' \u00b7 ' + clock(Math.max(0, Date.now() / 1000 - e.since)) : '';
  return 'Exporting the training set: \u201c' + esc(e.song || '') + '\u201d, ' + Math.min(e.done + 1, e.total) + ' of ' + e.total + since;
}

/* What the analysis is doing right now, so a long step does not look stuck. */
function identityWorking(data) {
  var w = data.working;
  if (!w) { return 'Waiting for its turn behind other jobs\u2026'; }
  var pct = typeof w.progress === 'number' ? ', ' + Math.round(w.progress * 100) + '%' : '';
  var since = w.since ? ' \u00b7 ' + clock(Math.max(0, Date.now() / 1000 - w.since)) : '';
  return esc(w.stage || 'Working') + ': \u201c' + esc(w.song || '') + '\u201d' + pct + since;
}

async function showIdentity(id, preloaded) {
  IDENTITY.view = 'identity';
  IDENTITY.id = id;
  IDENTITY.open = {};
  State.activeCorpus = id;
  State.openCorpus = id;
  try { localStorage.setItem('yue2_active_corpus', id); } catch (e) {}
  paintCorporaBadge();
  var back = getIdentityBack();
  if (back) { back.classList.remove('hidden'); }
  var data = preloaded || await api('/api/identities/' + id);
  IDENTITY.data = data;
  var heading = getIdentityHeading();
  if (heading) { heading.textContent = data.name; }
  var body = getIdentityBody();
  if (!body) { return; }
  body.innerHTML =
    '<div id="identity-summary" class="identity-summary persona-summary">' + identitySummary(data) + '</div>' +
    '<div id="identity-edit" class="identity-form persona-form hidden"></div>' +
    renderIdentityActions(data) +
    (data.lora ? '<p class="hint">LoRA installed from this corpus: <b>' + esc(data.lora) + '</b>. ' +
      'Choose it in the Style LoRA list to write with it.</p>' : '') +
    (trainingAvailable()
      ? '<p class="hint"><b>Dual-branch LoRA training:</b> Trains a combined Planner LoRA (musical structure and chords) and Sound LoRA (audio timbre). A single-era corpus can take Planner ~0.85 / Sound ~0.80; a mixed one up to about 0.70 / 0.70.</p>'
      : '') +
    '<p class="hint"><b>Export training set</b> writes the audio, lyrics, and style caption per song — the layout a trainer ' +
    'reads — and <b>Install a LoRA</b> takes a trained file back, naming it and giving it this corpus\u2019s ' +
    'trigger word.</p>' +
    '<p class="hint">Analyse separates each included song’s vocal, finds its key, tempo and sections with ' +
    'SheetSage, and drafts its lyrics with Whisper, tagged by section. Songs with no detected vocals ' +
    'are automatically tagged as <b>[instrumental]</b> so they train cleanly for instrumental workflows.</p>' +
    '<table class="identity-songs persona-songs"><thead><tr><th></th><th>Song</th><th>Length</th><th>Progress</th><th></th></tr></thead>' +
    '<tbody id="identity-rows">' + data.songs.map(songRow).join('') + '</tbody></table>' +
    '<div id="identity-export-result" class="identity-export persona-export"></div>';
  pollIdentity();
}
var showPersona = showIdentity;

/* Keeps the table current without touching what is being typed: only the progress,
   key and tempo, and a lyrics draft that lands in a box nobody has edited. */
async function pollIdentity() {
  clearTimeout(IDENTITY.timer);
  var modal = getIdentityModal();
  if (IDENTITY.view !== 'identity' || (modal && modal.classList.contains('hidden'))) { return; }
  var data;
  try { data = await api('/api/identities/' + IDENTITY.id); } catch (err) { data = null; }
  if (data && IDENTITY.view === 'identity' && data.id === IDENTITY.id) {
    IDENTITY.data = data;
    var sumEl = $('identity-summary') || $('persona-summary');
    if (sumEl) { sumEl.innerHTML = identitySummary(data); }
    var actionsEl = document.querySelector('.identity-actions');
    if (actionsEl && (!document.activeElement || !actionsEl.contains(document.activeElement))) {
      actionsEl.outerHTML = renderIdentityActions(data);
    }
    data.songs.forEach(function (song) {
      var steps = document.querySelector('[data-steps="' + song.id + '"]');
      if (steps) {
        steps.innerHTML = stepChips(song) + '<div class="muted" data-keytempo="' + song.id + '">' +
          esc([song.key, song.tempo ? song.tempo + ' BPM' : ''].filter(Boolean).join(', ')) + '</div>';
      }
      var box = document.querySelector('[data-lyrics="' + song.id + '"]');
      if (box && !box.dataset.edited && document.activeElement !== box && box.value !== (song.lyrics || '')) { box.value = song.lyrics || ''; }
      var drafting = document.querySelector('[data-saved="' + song.id + '"]');
      if (drafting && song.lyrics_state !== 'running' && drafting.textContent === 'Drafting\u2026') {
        drafting.textContent = 'Redrafted.';
        drafting.className = 'status good';
      }
      var cap = document.querySelector('[data-caption="' + song.id + '"]');
      if (cap) { cap.textContent = song.caption; }
      // Which version of the words is in use may have been switched.
      var sourceRow = document.querySelector('.lyrics-source[data-for="' + song.id + '"]');
      if (sourceRow && song.lyrics_versions && sourceRow.dataset.active !== (song.lyrics_versions.active || '')) {
        sourceRow.outerHTML = lyricsSourceRow(song);
      } else if (!sourceRow && box && song.lyrics_versions && song.lyrics_versions.llm && song.lyrics_versions.whisper) {
        box.insertAdjacentHTML('beforebegin', lyricsSourceRow(song));
      }
    });
  }
  var trainingHere = State.training && data && State.training.identity_id === data.id;
  IDENTITY.timer = setTimeout(pollIdentity, data && (data.busy || data.exporting || trainingHere) ? 2000 : 8000);
}
var pollPersona = pollIdentity;

/* The identity's own settings.  Changing the description or trigger word changes every
   caption that has no song description of its own; export again afterwards. */
function openIdentityEdit() {
  var data = IDENTITY.data;
  var box = $('identity-edit') || $('persona-edit');
  if (!box) { return; }
  box.innerHTML =
    '<div class="field"><label for="pe-name">Name</label><input id="pe-name" type="text" maxlength="80" value="' + esc(data.name) + '"></div>' +
    '<div class="field"><label for="pe-trigger">Trigger word</label><input id="pe-trigger" type="text" maxlength="40" value="' + esc(data.trigger_word) + '"></div>' +
    '<div class="field"><label for="pe-voice">Voice</label><select id="pe-voice"><option value="male">male</option>' +
      '<option value="female">female</option><option value="">not stated</option><option value="none">none</option></select></div>' +
    '<div class="field"><label for="pe-desc">The sound, for every song</label><input id="pe-desc" type="text" maxlength="400" ' +
      'value="' + esc(data.description || '') + '" placeholder="pop rock, electric guitars, bass, drums"></div>' +
    '<div class="wide row"><button id="pe-save" class="ghost">Save</button><button id="pe-cancel" class="ghost">Cancel</button>' +
      '<span id="pe-status" class="status"></span></div>' +
    '<div class="wide identity-checkpoints" id="pe-checkpoints"></div>';
  $('pe-voice').value = data.voice || '';
  box.classList.remove('hidden');
  loadCorpusCheckpoints();
  $('pe-desc').focus();
}
var openPersonaEdit = openIdentityEdit;

/* The checkpoints this corpus's training runs kept, to clear out: a run keeps one
   every 50 steps, and they add up. Step files only: the finished LoRA has Delete
   LoRA of its own. Deleting acts at once, apart from Save and Cancel above. */
function bytesLabel(bytes) {
  return bytes >= 1e9 ? (bytes / 1e9).toFixed(1) + ' GB' : Math.max(1, Math.round(bytes / 1e6)) + ' MB';
}

async function loadCorpusCheckpoints(note) {
  var box = $('pe-checkpoints');
  if (!box) { return; }
  var data;
  try {
    data = await api('/api/identities/' + IDENTITY.id + '/checkpoints');
  } catch (err) {
    box.innerHTML = '<label>Training checkpoints</label><p class="status bad">' + esc(err.message) + '</p>';
    return;
  }
  var all = [];
  data.runs.forEach(function (run) { all = all.concat(run.checkpoints); });
  var total = all.reduce(function (sum, item) { return sum + item.bytes; }, 0);
  var status = '<span id="pe-ck-status" class="status' + (note ? ' good' : '') + '">' + esc(note || '') + '</span>';
  if (!all.length) {
    box.innerHTML = '<label>Training checkpoints</label><p class="hint">' +
      (data.visible ? 'None kept.' : 'The app cannot see the LoRA folder, so it cannot list them.') + ' ' + status + '</p>';
    return;
  }
  box.innerHTML =
    '<div class="label-row"><label>Training checkpoints</label><span class="muted">' + all.length + ' kept, ' +
      bytesLabel(total) + ' \u00b7 select <a href="#" data-ck-all="1">all</a> \u00b7 <a href="#" data-ck-all="0">none</a></span></div>' +
    data.runs.map(function (run) {
      return '<div class="ck-run"><div class="ck-run-head">' + esc(run.label) + ' <span class="muted">' +
        run.checkpoints.length + ' \u00d7 ' + bytesLabel(run.checkpoints[0].bytes) + '</span></div><div class="ck-steps">' +
        run.checkpoints.map(function (item) {
          return '<label class="ck-step"><input type="checkbox" class="ck-box" value="' + esc(item.name) + '" data-bytes="' +
            item.bytes + '"> step ' + item.step + '</label>';
        }).join('') + '</div></div>';
    }).join('') +
    '<div class="row"><button id="pe-ck-delete" class="ghost danger" disabled>Delete selected</button>' + status + '</div>';
}

function checkpointsPicked() {
  return Array.prototype.slice.call(document.querySelectorAll('#pe-checkpoints .ck-box:checked'));
}

function paintCheckpointsPicked() {
  var button = $('pe-ck-delete');
  if (!button) { return; }
  var picked = checkpointsPicked();
  var bytes = picked.reduce(function (sum, box) { return sum + Number(box.dataset.bytes || 0); }, 0);
  button.disabled = !picked.length;
  button.textContent = picked.length
    ? 'Delete ' + picked.length + ' checkpoint' + (picked.length === 1 ? '' : 's') + ' (' + bytesLabel(bytes) + ')'
    : 'Delete selected';
}

async function deleteCorpusCheckpoints() {
  var picked = checkpointsPicked();
  if (!picked.length) { return; }
  var bytes = picked.reduce(function (sum, box) { return sum + Number(box.dataset.bytes || 0); }, 0);
  var what = picked.length + ' checkpoint' + (picked.length === 1 ? '' : 's');
  if (!await confirmModal({
    title: 'Delete checkpoints',
    message: 'Delete ' + what + ' of ' + (IDENTITY.data.name || 'this corpus') + ', ' + bytesLabel(bytes) + '?\n\n' +
      'Takes made with them keep their audio but cannot be rendered with them again.',
    confirmText: 'Delete',
    danger: true
  })) { return; }
  var button = $('pe-ck-delete');
  button.disabled = true;
  button.textContent = 'Deleting\u2026';
  try {
    var done = await api('/api/identities/' + IDENTITY.id + '/checkpoints/delete', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ names: picked.map(function (box) { return box.value; }) })
    });
    await loadCorpusCheckpoints('Deleted ' + done.deleted + ' checkpoint' + (done.deleted === 1 ? '' : 's') + ', ' +
      bytesLabel(done.bytes) + ' freed.');
    // The Style LoRA list loses them too.
    await pollState();
    paintStyleLoras();
  } catch (err) {
    paintCheckpointsPicked();
    var status = $('pe-ck-status');
    if (status) { status.textContent = err.message; status.className = 'status bad'; }
  }
}

async function saveIdentityEdit() {
  try {
    var data = await api('/api/identities/' + IDENTITY.id, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: $('pe-name').value.trim() || IDENTITY.data.name, trigger_word: $('pe-trigger').value,
        voice: $('pe-voice').value, description: $('pe-desc').value })
    });
    IDENTITY.data = data;
    var heading = getIdentityHeading();
    if (heading) { heading.textContent = data.name; }
    var editBox = $('identity-edit') || $('persona-edit');
    if (editBox) { editBox.classList.add('hidden'); }
    var status = $('identity-status') || $('persona-status');
    if (status) {
      status.textContent = IDENTITY.data.exported_at ? 'Saved. Export again to update the training set.' : 'Saved.';
      status.className = 'status good';
    }
    pollIdentity();
  } catch (err) {
    $('pe-status').textContent = err.message;
    $('pe-status').className = 'status bad';
  }
}
var savePersonaEdit = saveIdentityEdit;

function identitySong(id) {
  return ((IDENTITY.data && IDENTITY.data.songs) || []).filter(function (song) { return song.id === id; })[0] || null;
}
var personaSong = identitySong;

async function identityClick(event) {
  var target = event.target;
  var card = target.closest('[data-identity]') || target.closest('[data-persona]');
  if (card) { showIdentity(card.dataset.identity || card.dataset.persona); return; }
  if (target.closest('#identity-new') || target.closest('#persona-new')) { showIdentityNew(); return; }
  if (target.closest('#identity-import')) { $('identity-import-file').click(); return; }
  var folder = target.closest('[data-folder]');
  if (folder) { browseFolder(folder.dataset.folder); return; }
  if (target.closest('#pn-scan')) { scanNewIdentity(); return; }
  var open = target.closest('[data-open]');
  if (open) {
    IDENTITY.open[open.dataset.open] = !IDENTITY.open[open.dataset.open];
    var rows = $('identity-rows') || $('persona-rows');
    if (rows) { rows.innerHTML = IDENTITY.data.songs.map(songRow).join(''); }
    return;
  }
  var save = target.closest('[data-save]');
  if (save) {
    var sid = save.dataset.save;
    var box = document.querySelector('[data-lyrics="' + sid + '"]');
    var note = document.querySelector('[data-saved="' + sid + '"]');
    try {
      var sound = document.querySelector('[data-description="' + sid + '"]');
      await api('/api/identities/' + IDENTITY.id + '/songs/' + sid, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lyrics: box.value, description: sound ? sound.value : undefined })
      });
      delete box.dataset.edited;
      note.textContent = 'Saved.';
      pollIdentity();
      note.className = 'status good';
    } catch (err) { note.textContent = err.message; note.className = 'status bad'; }
    return;
  }
  var picked = target.closest('[data-lyrics-source]');
  if (picked) {
    var pickedId = picked.dataset.song, wanted = picked.dataset.lyricsSource;
    var held = identitySong(pickedId);
    if (held && held.lyrics_versions && held.lyrics_versions.active === wanted) { return; }
    var pickedBox = document.querySelector('[data-lyrics="' + pickedId + '"]');
    var pickedSaid = document.querySelector('[data-saved="' + pickedId + '"]');
    // What was saved comes back when this version does; only changes not yet saved would be lost.
    if (pickedBox && pickedBox.dataset.edited &&
        !await confirmModal({
          title: 'Unsaved changes',
          message: 'The box has changes that are not saved. Switch and lose them?',
          confirmText: 'Switch',
          danger: true
        })) { return; }
    picked.disabled = true;
    try {
      var reply = await api('/api/identities/' + IDENTITY.id + '/songs/' + pickedId + '/lyrics/source', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source: wanted })
      });
      if (pickedBox) { delete pickedBox.dataset.edited; }
      var pickedTick = document.querySelector('[data-checked="' + pickedId + '"]');
      if (reply && reply.restored) {
        // Drafted before: its words are back as they were left, with nothing to wait for.
        if (pickedBox) { pickedBox.value = reply.lyrics; }
        if (pickedTick) { pickedTick.checked = Boolean(reply.checked); }
        if (pickedSaid) { pickedSaid.textContent = 'Words restored.'; pickedSaid.className = 'status good'; }
      } else {
        if (pickedTick) { pickedTick.checked = false; }
        if (pickedSaid) { pickedSaid.textContent = 'Drafting\u2026'; pickedSaid.className = 'status'; }
      }
      pollIdentity();
    } catch (err) {
      if (pickedSaid) { pickedSaid.textContent = err.message; pickedSaid.className = 'status bad'; }
    } finally {
      picked.disabled = false;
    }
    return;
  }
  var redraft = target.closest('[data-redraft]');
  if (redraft) {
    var redraftId = redraft.dataset.redraft;
    var box = document.querySelector('[data-lyrics="' + redraftId + '"]');
    var said = document.querySelector('[data-saved="' + redraftId + '"]');
    var was = identitySong(redraftId);
    if (((was && was.lyrics_checked) || (box && box.dataset.edited)) &&
        !await confirmModal({
          title: 'Replace lyrics',
          message: 'Replace the lyrics in the box with a new draft?',
          confirmText: 'Replace',
          danger: true
        })) { return; }
    redraft.disabled = true;
    try {
      await api('/api/identities/' + IDENTITY.id + '/songs/' + redraftId + '/lyrics/redraft', { method: 'POST' });
      // The new draft lands in the box when it is ready, as the first one did.
      if (box) { delete box.dataset.edited; }
      var tick = document.querySelector('[data-checked="' + redraftId + '"]');
      if (tick) { tick.checked = false; }
      if (said) { said.textContent = 'Drafting\u2026'; said.className = 'status'; }
      pollIdentity();
    } catch (err) {
      if (said) { said.textContent = err.message; said.className = 'status bad'; }
    } finally {
      redraft.disabled = false;
    }
    return;
  }
  var restyle = target.closest('[data-restyle]');
  if (restyle) {
    var restyleId = restyle.dataset.restyle;
    var label = restyle.textContent;
    restyle.disabled = true;
    restyle.textContent = 'Queueing\u2026';
    try {
      await api('/api/identities/' + IDENTITY.id + '/songs/' + restyleId + '/style', { method: 'POST' });
      pollIdentity();
    } catch (err) {
      // In the screen's status line, like its other failures, not a modal.
      var failed = $('identity-status') || $('persona-status');
      if (failed) { failed.textContent = err.message; failed.className = 'status bad'; }
      restyle.disabled = false;
      restyle.textContent = label;
    }
    return;
  }
  if (target.closest('#identity-edit-open') || target.closest('#persona-edit-open')) { openIdentityEdit(); return; }
  if (target.closest('#pe-cancel')) {
    var editBox = $('identity-edit') || $('persona-edit');
    if (editBox) { editBox.classList.add('hidden'); }
    return;
  }
  if (target.closest('#pe-save')) { saveIdentityEdit(); return; }
  var every = target.closest('[data-ck-all]');
  if (every) {
    event.preventDefault();
    Array.prototype.forEach.call(document.querySelectorAll('#pe-checkpoints .ck-box'), function (box) {
      box.checked = every.dataset.ckAll === '1';
    });
    paintCheckpointsPicked();
    return;
  }
  if (target.closest('.ck-box')) { paintCheckpointsPicked(); return; }
  if (target.closest('#pe-ck-delete')) { deleteCorpusCheckpoints(); return; }
  var status = $('identity-status') || $('persona-status');
  if (target.closest('#identity-stop')) {
    try {
      await api('/api/identities/' + IDENTITY.id + '/stop', { method: 'POST' });
      if (status) { status.textContent = 'Stopped. Finished steps are kept; Analyse carries on from here.'; status.className = 'status good'; }
    } catch (err) { if (status) { status.textContent = err.message; status.className = 'status bad'; } }
    pollIdentity();
    return;
  }
  var split = target.closest('[data-split]');
  if (split) {
    var album = identitySong(split.dataset.split);
    var before = (IDENTITY.data && IDENTITY.data.songs.length) || 1;
    split.disabled = true;
    split.textContent = 'Splitting\u2026';
    try {
      var after = await api('/api/identities/' + IDENTITY.id + '/songs/' + split.dataset.split + '/split', { method: 'POST' });
      showIdentity(IDENTITY.id, after);
      var note = $('identity-status');
      if (note) {
        var made = after.songs.length - before + 1;
        note.textContent = (album ? album.title : 'The album') + ' is now ' + made + ' songs in this corpus. Press Analyse when ready.';
        note.className = 'status good';
      }
    } catch (err) {
      split.disabled = false;
      split.textContent = 'Split into tracks';
      if (status) { status.textContent = err.message; status.className = 'status bad'; }
    }
    return;
  }
  if (target.closest('#identity-analyse') || target.closest('#persona-analyse')) {
    try {
      var queued = await api('/api/identities/' + IDENTITY.id + '/analyse', { method: 'POST' });
      if (status) {
        status.textContent = queued.queued ? 'Queued ' + queued.queued + ' step' + (queued.queued === 1 ? '' : 's') + '. It carries on if you close this window.'
          : 'Nothing left to analyse.';
        status.className = 'status good';
      }
      pollIdentity();
    } catch (err) { if (status) { status.textContent = err.message; status.className = 'status bad'; } }
    return;
  }
  if (target.closest('#identity-export') || target.closest('#persona-export')) {
    // Shown at once; the window's refresh then keeps the progress line current.
    IDENTITY.data.exporting = { done: 0, total: (IDENTITY.data.songs || []).filter(function (s) { return s.include; }).length,
                                song: '', since: Date.now() / 1000 };
    var rowEl = document.querySelector('.identity-actions');
    if (rowEl) { rowEl.outerHTML = renderIdentityActions(IDENTITY.data); }
    pollIdentity();
    try {
      var out = await api('/api/identities/' + IDENTITY.id + '/export', { method: 'POST' });
      IDENTITY.data.exporting = null;
      if (status) { status.textContent = ''; }
      // The action row was drawn before this export existed, so Train a LoRA was
      // disabled — and a disabled button says nothing when it is pressed.  It is
      // enabled here rather than redrawing the row, which would clear this message.
      IDENTITY.data.exported_at = IDENTITY.data.exported_at || out.exported_at || 1;
      var actionsEl = document.querySelector('.identity-actions');
      if (actionsEl) {
        actionsEl.outerHTML = renderIdentityActions(IDENTITY.data);
      }
      var expRes = $('identity-export-result') || $('persona-export-result');
      if (expRes) {
        expRes.innerHTML = 'Wrote ' + out.written.length + ' song' + (out.written.length === 1 ? '' : 's') +
          ' to <code>' + esc(out.folder) + '</code>.' +
          // Drafts are a fair choice, not a fault: said, not flagged.
          (out.unchecked.length ? '<br><span class="muted">' + out.unchecked.length + ' song' + (out.unchecked.length === 1 ? ' uses its' : 's use their') +
            ' lyric draft as drafted.</span>' : '') +
          (out.cut && out.cut.length ? '<br><span class="muted">' + out.cut.length + ' song' + (out.cut.length === 1 ? ' is' : 's are') +
            ' longer than the training limit, and cut to fit.</span>' : '') +
          (out.skipped.length ? '<br><span class="muted">Skipped, not analysed or no lyrics: ' + esc(out.skipped.join(', ')) + '</span>' : '');
      }
    } catch (err) {
      IDENTITY.data.exporting = null;
      var row = document.querySelector('.identity-actions');
      if (row) { row.outerHTML = renderIdentityActions(IDENTITY.data); }
      var failed = $('identity-status');
      if (failed) { failed.textContent = err.message; failed.className = 'status bad'; }
    }
    return;
  }
  if (target.closest('#identity-train') || target.closest('#persona-train')) {
    openTrain();
    return;
  }
  var finishRun = target.closest('#identity-finish-run');
  if (finishRun) {
    finishRun.disabled = true;
    finishRun.textContent = 'Finishing\u2026';
    try {
      var finished = await api('/api/lora-runs/' + encodeURIComponent(finishRun.dataset.run) + '/finish', { method: 'POST' });
      var said = $('identity-status');
      if (said) { said.textContent = 'Finished: ' + finished.lora + ' is in the Style LoRA list.'; said.className = 'status good'; }
      await pollState();
      paintStyleLoras();
    } catch (err) {
      var bad = $('identity-status');
      if (bad) { bad.textContent = err.message; bad.className = 'status bad'; }
    }
    pollIdentity();
    return;
  }
  if (target.closest('#identity-run-all')) {
    openTrain(true);
    return;
  }
  if (target.closest('#identity-run-all-stop')) {
    try {
      await api('/api/identities/' + IDENTITY.id + '/run-all/stop', { method: 'POST' });
    } catch (err) {
      var said = $('identity-status');
      if (said) { said.textContent = err.message; said.className = 'status bad'; }
    }
    pollIdentity();
    return;
  }
  if (target.closest('#identity-install') || target.closest('#persona-install')) {
    $('identity-lora-file').click();
    return;
  }
  if (target.closest('#identity-download')) {
    if (IDENTITY.data && IDENTITY.data.lora) { window.location.href = '/api/loras/' + encodeURIComponent(IDENTITY.data.lora) + '/download'; }
    return;
  }
  if (target.closest('#identity-delete') || target.closest('#persona-delete')) {
    // The corpus and the copies the app made go; a trained LoRA is a model file, and
    // nothing here deletes those. So say which ones look like they came from it.
    var matching = getIdentityLoRAs(IDENTITY.data);
    var leftover = matching.length
      ? '\n\nNot deleted: ' + matching.length + ' LoRA file' + (matching.length === 1 ? '' : 's') +
        ' in models/loras that look like they came from this corpus —\n' + matching.slice(0, 6).join('\n')
      : '';
    if (!await confirmModal({
      title: 'Delete corpus',
      message: 'Delete the corpus “' + IDENTITY.data.name + '” and the app’s copies of its songs?\n\n' +
        'The original files are not touched.' + leftover,
      confirmText: 'Delete',
      danger: true
    })) { return; }
    try {
      await api('/api/identities/' + IDENTITY.id, { method: 'DELETE' });
      showIdentityList();
    } catch (err) { if (status) { status.textContent = err.message; status.className = 'status bad'; } }
  }
}
var personaClick = identityClick;

async function saveLoraStrengths() {
  var item = loraChosen();
  if (!item) { return; }
  var planner = Number($('style-lora-clip').value);
  var sound = Number($('style-lora-model').value);
  var status = $('lora-install-status');
  try {
    await api('/api/loras/' + encodeURIComponent(item.name) + '/strengths', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ planner: planner, sound: sound })
    });
    await pollState();
    paintStyleLoras();
    status.textContent = 'Saved: it starts at Planner ' + planner.toFixed(2) + ' / Sound ' + sound.toFixed(2) + '.';
    status.className = 'status good';
  } catch (err) {
    status.textContent = err.message;
    status.className = 'status bad';
  }
}

async function deleteLora() {
  var item = loraChosen();
  if (!item) { return; }
  var label = item.title || loraLabel(item.name);
  if (!await confirmModal({
    title: 'Delete LoRA',
    message: 'Delete ' + label + '?\n\n' + item.name + ' and its note are removed from models/loras. ' +
      'Takes made with it keep their audio but cannot be rendered with it again.',
    confirmText: 'Delete',
    danger: true
  })) { return; }
  var status = $('lora-install-status');
  try {
    await api('/api/loras/' + encodeURIComponent(item.name), { method: 'DELETE' });
    $('style-lora').value = '';
    $('style-lora').dispatchEvent(new Event('change', { bubbles: true }));
    await pollState();
    paintStyleLoras();
    status.textContent = 'Deleted ' + label + '.';
    status.className = 'status good';
  } catch (err) {
    status.textContent = err.message;
    status.className = 'status bad';
  }
}

async function installSharedLora(event) {
  var picked = event.target.files && event.target.files[0];
  event.target.value = '';
  if (!picked) { return; }
  var status = $('lora-install-status');
  status.textContent = 'Installing ' + picked.name + '\u2026';
  status.className = 'status';
  try {
    var form = new FormData();
    form.append('file', picked);
    var done = await api('/api/loras/install', { method: 'POST', body: form });
    await pollState();
    paintStyleLoras();
    $('style-lora').value = done.name;
    $('style-lora').dispatchEvent(new Event('change', { bubbles: true }));
    status.textContent = 'Installed' + (done.styles ? ', with ' + done.styles + ' learned styles.' : '.');
    status.className = 'status good';
  } catch (err) {
    status.textContent = err.message;
    status.className = 'status bad';
  }
}

async function identityChange(event) {
  var target = event.target;
  if (target.id === 'identity-import-file') {
    var chosen = target.files && target.files[0];
    target.value = '';
    if (!chosen) { return; }
    var said = $('identity-import-status');
    said.textContent = 'Installing ' + chosen.name + '\u2026';
    said.className = 'status';
    try {
      var data = new FormData();
      data.append('file', chosen);
      var made = await api('/api/loras/install', { method: 'POST', body: data });
      await pollState();
      said.textContent = 'Installed ' + made.name + (made.styles ? ', with ' + made.styles + ' learned styles' : '') + '. It is in the Style LoRA list.';
      said.className = 'status good';
    } catch (err) {
      said.textContent = err.message;
      said.className = 'status bad';
    }
    return;
  }
  if (target.id === 'identity-lora-file') {
    var picked = target.files && target.files[0];
    target.value = '';
    if (!picked) { return; }
    var status = $('identity-status');
    status.textContent = 'Installing ' + picked.name + '\u2026';
    status.className = 'status';
    try {
      var form = new FormData();
      form.append('file', picked);
      var done = await api('/api/identities/' + IDENTITY.id + '/lora', { method: 'POST', body: form });
      status.textContent = 'Installed ' + done.name + ' (' + done.kind + '). It is in the Style LoRA list.';
      status.className = 'status good';
      await pollState();
      paintStyleLoras();
      showIdentity(IDENTITY.id);
    } catch (err) {
      status.textContent = err.message;
      status.className = 'status bad';
    }
    return;
  }
  if (target.dataset.include) {
    await api('/api/identities/' + IDENTITY.id + '/songs/' + target.dataset.include, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ include: target.checked })
    });
    var song = identitySong(target.dataset.include);
    if (song) { song.include = target.checked ? 1 : 0; }
    target.closest('tr').classList.toggle('off', !target.checked);
    pollIdentity();
  }
  if (target.dataset.checked) {
    await api('/api/identities/' + IDENTITY.id + '/songs/' + target.dataset.checked, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ lyrics_checked: target.checked })
    });
    pollIdentity();
  }
}
var personaChange = identityChange;

/* Action tiles. Colour carries meaning: green acts, violet inspects, blue keeps,
   amber reworks, gold remembers, red removes. */
var ICONS = {
  play: '<path d="M8 5.4v13.2L19 12z" fill="currentColor" stroke="none"/>',
  pause: '<path d="M9 5.5v13M15 5.5v13" stroke-width="2.4" stroke-linecap="round"/>',
  render: '<path d="M12 3.5v11m0 0l-4-4m4 4l4-4M5 19.5h14"/>',
  score: '<circle cx="7" cy="17.6" r="2.2"/><circle cx="17" cy="15.6" r="2.2"/><path d="M9.2 17.6V6l10-2v11.4"/>',
  save: '<path d="M12 4v10m0 0l-4-4m4 4l4-4M5 19h14"/>',
  again: '<path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20 4.2v3.9h-3.9"/>',
  star: '<path d="M12 3.6l2.6 5.5 6.1.9-4.4 4.3 1 6-5.3-2.9-5.3 2.9 1-6L3.4 10l6-.9z"/>',
  check: '<path d="M20 6.5L9.5 17 4 11.5"/>',
  trash: '<path d="M4.5 7h15M9.5 7V4.8h5V7M6.5 7l1 12.2h9l1-12.2"/>',
  stems: '<path d="M12 3.2l8 4.2-8 4.2-8-4.2z"/><path d="M4 12.4l8 4.2 8-4.2"/><path d="M4 16.6l8 4.2 8-4.2"/>',
  move: '<path d="M3.5 7.5V18a1.5 1.5 0 0 0 1.5 1.5h14a1.5 1.5 0 0 0 1.5-1.5V9.5A1.5 1.5 0 0 0 19 8h-7l-2-2.5H5A1.5 1.5 0 0 0 3.5 7v.5"/><path d="M10 13.5h6m0 0l-2.5-2.5m2.5 2.5L13.5 16"/>',
  voice: '<path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3z"/><path d="M19 11a7 7 0 0 1-14 0"/><path d="M12 18v3"/>',
  variations: '<path d="M12 3.5l1.9 5.1 5.1 1.9-5.1 1.9L12 17.5l-1.9-5.1L5 10.5l5.1-1.9z"/><path d="M18.5 15.2l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/>',
  stop: '<rect x="6.5" y="6.5" width="11" height="11" rx="1.6"/>',
  dice: '<path d="M12 2.8l7.8 4.5v9.4L12 21.2l-7.8-4.5V7.3z"/><path d="M4.2 7.3L12 12l7.8-4.7M12 12v9.2"/><circle cx="12" cy="7.55" r="1.05" fill="currentColor" stroke="none"/><circle cx="7.4" cy="12.9" r="1.05" fill="currentColor" stroke="none"/><circle cx="9.5" cy="16.3" r="1.05" fill="currentColor" stroke="none"/><circle cx="14.6" cy="13" r="1.05" fill="currentColor" stroke="none"/><circle cx="16.6" cy="15.4" r="1.05" fill="currentColor" stroke="none"/>',
  info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.2"/><circle cx="12" cy="7.9" r="0.6" fill="currentColor"/>',
  mastering: '<circle cx="12" cy="12" r="8.5"/><path d="M8 15.5V8.5l4 3.8 4-3.8v7"/>',
  level: '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4 4 0 0 1 0 6"/><path d="M18 6.5a7.5 7.5 0 0 1 0 11"/>'
};

function icon(name) {
  return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" ' +
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ICONS[name] + '</svg>';
}

function tile(kind, iconName, label, attrs, title) {
  var tip = title || label;
  return '<button class="act ' + kind + '" ' + (attrs || '') + ' title="' + esc(tip) + '" aria-label="' + esc(tip) + '">' +
    icon(iconName) + '<span>' + label + '</span></button>';
}

function downloadTile(take) {
  return tile('save', 'save', 'Save', 'data-act="save" data-id="' + take.id + '"', 'Save \u2014 Download the audio file (FLAC)');
}

function stemsBlock(take) {
  var sets = take.stem_sets || [];
  if (!sets.length) { return ''; }
  var rows = sets.map(function (set) {
    var busy = set.status === 'queued' || set.status === 'running';
    var remove = '<button class="stem-chip" data-act="stem-del" data-set="' + set.id + '" title="' +
      (busy ? 'Stop and delete these stems' : 'Delete these stems') + '">x</button>';
    if (set.status === 'done') {
      var chips = (set.files || []).map(function (file) {
        return '<button class="stem-chip" data-act="stem-play" data-set="' + set.id + '" data-file="' + esc(file.file) + '">' +
          esc(file.name) + '</button>';
      }).join('');
      return '<div class="stem-row"><span class="stem-label">stems</span>' + chips +
        '<a class="stem-chip" href="/api/stem-sets/' + set.id + '/zip" download>zip</a>' + remove + '</div>';
    }
    if (set.status === 'failed') {
      return '<div class="stem-row"><span class="stem-label" style="color:var(--bad)">stems failed: ' +
        esc((set.error || '').slice(0, 70)) + '</span>' + remove + '</div>';
    }
    var pct = Math.round((set.progress || 0) * 100);
    return '<div class="stem-row"><span class="stem-label">stems: ' + esc(set.stage || set.status) + ' ' + pct + '%</span>' + remove + '</div>';
  });
  return '<div class="take-stems">' + rows.join('') + '</div>';
}

/* Load a take into the left column: the matching mode, its title, style, lyrics,
   score and settings, and the highlight on its card. Every tile that acts on a
   take calls this first, so the panel always describes the take you just touched. */
function selectTake(take) {
  if (!take) { return; }
  // The take already on show, with words typed over it: leave the form as it is. Play,
  // Score and the other buttons on a card select their take first, and reloading it
  // here threw the edit away in favour of words that were already there.
  if (take.id === selectedTakeId() && formIsDraft()) {
    paintTakeHighlights();
    activateTakeRecording(take);
    return;
  }
  if (formIsDraft()) { stashDraft(); }
  State.formTake = take;
  if ($('write-brief')) { $('write-brief').value = take.brief || ''; }   // what this song was said to be about
  if ($('keep-tune')) { $('keep-tune').checked = true; }
  // Songs and instrumentals are both written from a prompt; only a cover has a recording.
  var isInst = take.kind === 'instrumental';
  var isSong = take.kind === 'song' || isInst;
  var hasScore = Boolean(take.abc && take.abc.length > 50);
  var planning = isSong && !hasScore && (take.status === 'queued' || take.status === 'running');
  setMode(isInst ? 'inst' : (isSong ? 'song' : 'cover'));
  if (!isSong && take.source_id) { $('source-select').value = take.source_id; }
  if (isInst && $('source-select')) { $('source-select').value = take.source_id || ''; }
  $('title').value = take.title;
  $('style').value = take.style || '';
  $('style').dataset.touched = '1';
  paintVocals();
  // Before the structure: timed sections are laid out against the cap.
  if (take.max_duration) { $('max-duration').value = Math.round(take.max_duration); }
  // The take's own cap, which a recording's score does not replace.
  State.capTyped = false;
  State.capFromScore = false;
  // An instrumental keeps its structure where a song keeps its lyrics.  The lyrics box
  // is left alone, so browsing instrumentals cannot wipe the words of a song.
  if (isInst) {
    loadStructure(take.lyrics);
    FEEL.value = FEELS[take.feel] ? take.feel : 'steady';
    paintFeel();
  } else {
    $('lyrics').value = take.lyrics || ''; paintSongPlan();
  }
  $('abc').value = take.abc || '';
  scoreBaseline(take.abc || '');
  if (take.mode) { $('mode').value = take.mode; }
  if (isSong) {
    $('harmony').value = take.harmony || 0;
    if (take.variety) { $('variety').value = take.variety; }
    paintHarmony();
  }
  if (take.realaudio !== undefined) {
    $('realaudio').checked = Boolean(take.realaudio);
  }
  if (take.normalise !== undefined && $('normalise')) {
    $('normalise').checked = Boolean(take.normalise);
  }
  if (take.seed != null) {
    $('seed').value = take.seed;
    $('seed-fixed').checked = true;
  }
  if (take.style_lora !== undefined) { showStyleLora(take); }
  $('interpretation').value = INTERPRETATIONS[take.interpretation] ? take.interpretation : 'standard';
  paintInterpretation();
  loadAdvancedTakeSettings(take);
  // The take owns the score in the box: its own for a song, its recording's
  // transcription for a cover, which boxShowsSource recognises by the take's
  // source_id. A plan still being written owns nothing until it lands.
  setSelection({
    formTakeId: take.id,
    boxKind: planning ? 'none' : 'take',
    boxId: planning ? null : take.id,
    awaiting: planning ? take.id : null
  });
  $('score-badge').textContent = take.abc
    ? (take.status === 'planned' ? 'plan ready' : 'saved score')
    : 'no plan yet';
  $('score-badge').className = take.abc ? 'badge ok' : 'badge';
  if (take.abc) { $('score-box').open = true; }
  setChart(chordChart(take.abc || ''));
  showPlanLength(take.abc || '');
  if (isInst) { paintSource(); }
  syncEditor();
  refreshTitleHint();
  paintSource();
  State.formEdited = false;
  saveForm();
  paintTakeHighlights();
  activateTakeRecording(take);
}

/* One click on a card replaces the form.  If the form holds words that are not
   simply the take it already shows, keep them, so a click cannot lose a verse. */
function formIsDraft() {
  // Moving between takes must not look like an unsaved draft.  Only words the user
  // typed, or took back with Restore, count; loading a take or a recording clears it.
  if (!State.formEdited) { return false; }
  // A text box turns \r\n into \n, so compare text the way the box holds it.
  var same = function (a, b) { return String(a || '').replace(/\r\n?/g, '\n') === String(b || '').replace(/\r\n?/g, '\n'); };
  var title = $('title').value;
  var style = $('style').value;
  var lyrics = State.mode === 'inst' ? '' : $('lyrics').value;
  if (!lyrics.trim() && !title.trim()) { return false; }
  var shown = selectedTakeId() ? takeById(selectedTakeId()) : null;
  if (State.mode === 'inst') { return Boolean(shown) && (!same(title, shown.title) || !same(style, shown.style)); }
  if (!shown) { return Boolean(lyrics.trim()); }
  return !same(title, shown.title) || !same(style, shown.style) || !same(lyrics, shown.lyrics);
}

function stashDraft() {
  var next = { mode: State.mode, title: $('title').value, style: $('style').value, lyrics: $('lyrics').value };
  var current = State.draft;
  // The words may be stashed again on the next card click.  Only keep one copy, so
  // the bar does not churn through the same verse.
  if (current && current.title === next.title && current.style === next.style && current.lyrics === next.lyrics) { return; }
  State.draft = next;
  paintDraft();
}

function paintDraft() {
  var bar = $('draft-bar');
  if (!bar) { return; }
  bar.classList.toggle('hidden', !State.draft);
  if (State.draft) {
    var words = (State.draft.title || State.draft.lyrics || '').trim().split('\n')[0].slice(0, 40);
    $('draft-text').textContent = 'Your unsaved words were kept' + (words ? ': \u201c' + words + '\u201d' : '') + '.';
  }
}

function restoreDraft() {
  var draft = State.draft;
  if (!draft) { return; }
  setMode(draft.mode === 'song' ? 'song' : 'cover');
  setSelection({});
  $('title').value = draft.title || '';
  $('style').value = draft.style || '';
  $('lyrics').value = draft.lyrics || ''; paintSongPlan();
  dismissDraft();
  paintVocals();
  refreshTitleHint();
  // The words are back in the form and nowhere else, so a later card click must
  // offer them again rather than drop them.
  State.formEdited = true;
  saveForm();
  paintTakes();
  statusLine('Your words are back.', 'good');
}

function dismissDraft() {
  State.draft = null;
  paintDraft();
}

/* Start a new song, or a new cover, from the take on show.  The words and the score
   go; the settings stay (style, vocal, Harmony, plan variety, length, interpretation,
   seed), so the next song can be in the same vein.  The loaded take lets go of the
   column, so Render and Replan cannot act on it by mistake.  A cover keeps its
   recording and goes back to that recording's own transcription. */
async function startFresh() {
  var noun = { cover: 'cover', song: 'song', inst: 'instrumental' }[State.mode] || 'song';
  if (scoreIsDirty() && !await confirmModal({
    title: 'Discard score changes',
    message: 'The score has changes that are not saved. Start a new ' + noun + ' and discard them?',
    confirmText: 'Discard changes',
    danger: true
  })) {
    return false;
  }
  if (formIsDraft()) { stashDraft(); }
  var cover = State.mode === 'cover';
  setSelection({});
  // The editor reads its take from here: left behind, it kept the last take's player on a new one.
  State.formTake = null;
  $('title').value = '';
  if (State.mode !== 'inst') {
    $('lyrics').value = '';
    if ($('write-brief')) { $('write-brief').value = ''; }
    paintSongPlan();
  }   // an instrumental keeps its structure, like a setting
  $('abc').value = '';
  scoreBaseline('');
  setChart('');
  showPlanLength('');
  if (cover) {
    // A new cover starts with no recording, like any new take: its score, words and sections go with it.
    if ($('source-select')) { $('source-select').value = ''; }
    State.sourceByMode = State.sourceByMode || {};
    State.sourceByMode.cover = '';
    paintSource();
    paintStructure();
  } else {
    $('score-badge').textContent = 'no plan yet';
    $('score-badge').className = 'badge';
  }
  // A new take starts from the defaults, not from whatever the last one used.
  $('style').value = '';
  delete $('style').dataset.touched;
  // No style LoRA either: one chosen for the last take would bring its trigger word back into the style.
  showStyleLora({});
  $('max-duration').value = DEFAULT_CAP;
  State.capTyped = false;
  State.capFromScore = false;
  followRecordingCap();
  if ($('variety')) { $('variety').value = 'normal'; }
  // Varied and Wide: where a new song starts (our own testing found it a good starting point).
  if ($('harmony')) { $('harmony').value = 1; paintHarmony(); }
  $('interpretation').value = 'wide';
  paintInterpretation();
  if ($('realaudio') && !$('realaudio').disabled) { $('realaudio').checked = true; }
  if ($('normalise')) { $('normalise').checked = false; }
  // A fresh seed, and not held: opening a take ticks "keep this seed" with its seed,
  // and a new take would otherwise reuse it.
  $('seed-fixed').checked = false;
  $('seed').value = Math.floor(Math.random() * 4294967295);
  paintVocals();
  if (State.mode === 'inst' && typeof paintStructure === 'function') { paintStructure(); }
  State.formEdited = false;
  refreshTitleHint();
  syncEditor();
  saveForm();
  paintTakes();
  statusLine(cover
    ? 'New cover. Choose a recording, then add a title and lyrics.'
    : State.mode === 'inst' ? (instFromRecording()
      ? 'New instrumental. The recording stays selected: choose a style, then Create instrumental.'
      : 'New instrumental. Choose a style and a structure, then Write score plan.')
    : 'New song. Write a title, style and lyrics, then Write score plan.', 'good');
  $('title').focus();
  return true;
}

function takeById(id) {
  return State.takes.filter(function (take) { return take.id === id; })[0] || null;
}

/* Deleting takes one at a time is slow in a space with many, so cards can be
   picked and one button removes the lot. The button names the count and the
   confirmation names the takes, because this cannot be undone. */
function pickedIds() {
  return Object.keys(State.picked).filter(function (id) { return State.picked[id]; });
}

function visibleTakes() {
  return State.takes.filter(function (take) {
    if (State.kinds && State.kinds.length && State.kinds.indexOf(take.kind) < 0) { return false; }
    return State.filter === 'all' || (State.filter === 'favourite' && take.favourite);
  });
}

function paintBulk() {
  paintCompareButton();
  var count = pickedIds().length;
  var button = $('bulk-delete');
  if (button) {
    button.classList.toggle('hidden', !count);
    button.textContent = count ? 'Delete ' + count : 'Delete';
    button.disabled = !count;
  }
  var selAll = $('select-all');
  if (selAll) {
    var visible = visibleTakes();
    var allPicked = visible.length > 0 && visible.every(function (take) {
      return !!State.picked[take.id];
    });
    selAll.disabled = visible.length === 0;
    selAll.textContent = allPicked ? 'Deselect all' : 'Select all';
    selAll.classList.toggle('active', allPicked);
    selAll.title = allPicked
      ? 'Deselect all takes in this space'
      : (visible.length === 0 ? 'No takes to select'
        : 'Select all ' + visible.length + (State.search ? ' takes found' : ' takes in this space'));
  }
}

function toggleSelectAll() {
  var visible = visibleTakes();
  if (!visible.length) { return; }
  var allPicked = visible.every(function (take) {
    return !!State.picked[take.id];
  });
  if (allPicked) {
    visible.forEach(function (take) {
      delete State.picked[take.id];
    });
  } else {
    visible.forEach(function (take) {
      State.picked[take.id] = true;
    });
  }
  var cards = document.querySelectorAll('#takes .take');
  Array.prototype.forEach.call(cards, function (card) {
    var id = card.dataset.id;
    var box = card.querySelector('input[data-act="pick"]');
    var isPicked = !!State.picked[id];
    if (box) { box.checked = isPicked; }
    card.classList.toggle('picked', isPicked);
  });
  paintBulk();
}

function clearPicked() {
  State.picked = {};
  paintBulk();
}

async function bulkDelete() {
  var ids = pickedIds();
  if (!ids.length) { return; }
  var names = ids.map(function (id) {
    var take = takeById(id);
    return take ? take.title : id;
  });
  var shown = names.slice(0, 8).map(function (name) { return '• ' + name; }).join('\n');
  var more = names.length > 8 ? '\nand ' + (names.length - 8) + ' more' : '';
  if (!await confirmModal({
    title: 'Delete ' + ids.length + ' take' + (ids.length === 1 ? '' : 's'),
    message: 'Delete ' + ids.length + ' take' + (ids.length === 1 ? '' : 's') + '?\n\n' + shown + more
      + '\n\nTheir audio and stems go with them. This cannot be undone.',
    confirmText: 'Delete',
    danger: true
  })) {
    return;
  }
  if (State.playing && ids.indexOf(State.playing) !== -1) {
    var audio = $('audio');
    if (audio) { audio.pause(); }
    State.playing = null;
    paintTransport();
  }
  var done = 0;
  for (var i = 0; i < ids.length; i++) {
    statusLine('Deleting ' + (done + 1) + ' of ' + ids.length + '…');
    try {
      await api('/api/takes/' + ids[i], { method: 'DELETE' });
      done += 1;
    } catch (err) {
      statusLine('Could not delete ' + (takeById(ids[i]) ? takeById(ids[i]).title : ids[i]) + ': ' + err.message, 'bad');
      break;
    }
  }
  clearPicked();
  loadTakes();
  statusLine('Deleted ' + done + ' take' + (done === 1 ? '' : 's') + '.', 'good');
}

function paintTakes() {
  if (document.querySelector('.take-title-input')) { return; }
  var list = visibleTakes();
  State.paintedAt = Date.now();
  $('empty').style.display = list.length ? 'none' : 'block';
  var others = State.spaces.some(function (space) { return space.id !== State.spaceId && space.takes; });
  var kindWords = (State.kinds || []).map(function (kind) { return kind === 'instrumental' ? 'instrumental' : kind; }).join(' or ');
  $('empty').textContent = State.kinds && State.kinds.length && !State.search
    ? 'No ' + (State.filter === 'favourite' ? 'starred ' : '') + kindWords + ' takes in this space.'
    : State.search
    ? 'No ' + (State.filter === 'favourite' ? 'starred ' : '') + 'takes match \u201c' + State.search + '\u201d' +
      (searchingEverywhere() ? ' in any space.' : ' in this space.')
    : State.filter === 'favourite' ? 'No starred takes in this space.'
    : others ? 'This space is empty. Create a take while it is on show, or move takes here with Move.'
    : 'Nothing yet. Load a recording, write some lyrics, and press create.';
  var more = State.takesTotal - State.takes.length;
  $('takes-more').classList.toggle('hidden', more <= 0);
  $('takes-more').textContent = 'Show ' + Math.min(more, 300) + ' more of ' + more + ' older takes';
  $('takes').innerHTML = list.map(function (take) {
    var status = take.status;
    var meta = [];
    if (take.space_id && take.space_id !== State.spaceId) { meta.push('In ' + spaceName(take.space_id)); }
    meta.push(take.kind === 'song' ? 'from a prompt' : (take.kind === 'instrumental' ? 'instrumental' : 'cover'));
    if (take.duration) { meta.push(secs(take.duration)); }
    // The settings that shaped it come first, named, so a card can be read back
    // as the recipe that made it. Always shown, defaults included, so two cards
    // can be compared at a glance. A cover's plan is its recording, so Harmony and
    // Plan are only for takes whose plan was written.
    var written = take.kind === 'song' || take.kind === 'instrumental';
    if (written) { meta.push('Harmony: ' + (HARMONY_WORDS[take.harmony || 0] || HARMONY_WORDS[0]).toLowerCase()); }
    meta.push('Interpretation: ' + (INTERPRETATIONS[take.interpretation] || INTERPRETATIONS.standard).name.toLowerCase());
    if (written) { meta.push('Plan: ' + (take.variety || 'normal')); }
    if (take.style_lora) {
      var kind = loraKind(take.style_lora);
      var clip = Number(take.style_lora_clip != null ? take.style_lora_clip : 1).toFixed(2);
      var model = Number(take.style_lora_model != null ? take.style_lora_model : 1).toFixed(2);
      var str = (kind === 'planner') ? ' (' + clip + ')'
              : (kind === 'decoder') ? ' (' + model + ')'
              : ' (' + clip + '/' + model + ')';
      meta.push('Style: ' + loraLabel(take.style_lora) + str);
    }
    if (take.realaudio) { meta.push('realaudio'); }
    meta.push('seed ' + take.seed);
    if (take.sound_seed) { meta.push('voice ' + take.sound_seed); }
    meta.push(age(take.created_at));
    var live = '';
    if (status === 'running' && take.live) {
      live = '<div class="take-meta">' + esc(take.live.label || 'working') + ' \u00b7 ' + Math.round((take.live.progress || 0) * 100) + '%</div>';
    } else if (status === 'failed') {
      live = '<div class="take-status failed" title="' + esc(take.error || 'failed') + '">' + esc(take.error || 'failed') + '</div>';
    } else if (status === 'planned') {
      // An instrumental whose plan holds a vocal line is flagged before it is
      // rendered, so the warning arrives while it still saves you something.
      live = take.error
        ? '<button class="take-status sung" data-act="render" data-id="' + take.id + '">' + esc(take.error) + '</button>'
        : '<div class="take-status ready">plan ready</div>';
    } else if (status !== 'done') {
      live = '<div class="take-meta">' + esc(status === 'queued' ? 'waiting for the engine' : status) + '</div>';
    } else if (State.normalising[take.id]) {
      // Takes a few seconds, and the cards are redrawn meanwhile, so the state is
      // kept here rather than on the button that was clicked.
      live = '<div class="take-status working">Normalising\u2026</div>';
    } else if (weakRender(take) && !(take.normalised && take.weak_dismissed)) {
      // A render that loses its footing comes out quiet from end to end, and
      // sounds thin or distorted. Another seed usually fixes it.
      // Normalising raises the level and nothing else, so a take that was quiet as
      // rendered keeps saying so, and a listen tells a good quiet take from a bad one.
      live = take.normalised
        ? '<div class="take-status weak with-x" title="Came out at ' + take.loudness.toFixed(1) + ' dB as rendered, far below the usual level, and has been normalised. Takes like this often sound thin or distorted, and some were only quiet.">' +
          '<button class="status-undo" data-act="unnormalise" data-id="' + take.id + '" title="' + normalisedTo(take) + ' Click to undo it.">' +
          'Weak render, normalised: try another seed if it sounds thin</button>' +
          '<button class="status-x" data-act="dismiss-weak" data-id="' + take.id + '" title="It sounds fine: dismiss" aria-label="Dismiss">\u00d7</button></div>'
        : '<button class="take-status weak" data-act="normalise"' + ' data-id="' + take.id + '" title="Came out at ' + take.loudness.toFixed(1) +
          ' dB, far below the usual level. Takes like this often sound thin or distorted, and some are only quiet. If it still sounds wrong once normalised, try another seed.">Weak render: click here to normalise, or try another seed</button>';
    } else if (take.stopped_early && !take.note_dismissed) {
      // The model wrote the song's end before its score's last section, twice: the app
      // had already tried once more with a new seed.
      live = '<div class="take-status weak with-x" title="The render ended at ' + clock(take.duration || 0) +
        ', before the last section of its score began, and did again when the app tried once more with a new seed. Render again for another try.">' +
        '<span>Stopped before the last section: render again for the full song</span>' +
        '<button class="status-x" data-act="dismiss-note" data-id="' + take.id + '" title="The end is fine: dismiss" aria-label="Dismiss">\u00d7</button></div>';
    } else if (take.ran_to_cap && !take.note_dismissed) {
      // The model never wrote the song's end, so it ran on until the Length cap, and was faded out there.
      live = '<div class="take-status weak with-x" title="The score ends well before the ' + Math.round(take.max_duration) +
        ' s cap, but the music kept going until the cap, where it was faded out. The end may loop or wander. Another seed usually ends properly.">' +
        '<span>Ran to the length cap: may not end cleanly</span>' +
        '<button class="status-x" data-act="dismiss-note" data-id="' + take.id + '" title="The end is fine: dismiss" aria-label="Dismiss">\u00d7</button></div>';
    } else if (take.normalised) {
      live = '<button class="take-status normalised" data-act="unnormalise" data-id="' + take.id +
        '" title="' + normalisedTo(take) + ' Click to go back to the level it was rendered at.">Normalised</button>';
    }
    var id = ' data-id="' + take.id + '"';
    var actions = '';
    if (status === 'queued' || status === 'running') {
      actions += tile('del', 'stop', 'Cancel', 'data-act="cancel"' + id,
                      'Cancel \u2014 Stop this job and remove from queue');
    }
    if (status === 'planned') {
      actions += tile('go', 'render', 'Render', 'data-act="render"' + id,
                      'Render \u2014 Synthesize audio for this take');
      actions += tile('again', 'again', 'Replan', 'data-act="replan"' + id,
                      'Replan \u2014 Generate a new song plan from prompt');
    }
    if (status === 'failed') {
      // A failure leaves a dead end unless it can be retried. A take with a score
      // failed while rendering; one without failed while planning.
      if (take.abc && take.abc.length > 50) {
        actions += tile('go', 'render', 'Render', 'data-act="render"' + id,
                        'Render \u2014 Retry synthesizing audio for this take');
      } else {
        actions += tile('again', 'again', 'Replan', 'data-act="replan"' + id,
                        'Replan \u2014 Try planning again from prompt');
      }
      // A restarted job leaves a take that often still holds its audio or its score.
      // Clear puts it back to whatever it reached, without another run.  A take that
      // failed while planning holds neither, so there is nothing to go back to: the
      // server refuses, and the button would only look broken.
      if (take.has_audio || (take.abc && take.abc.trim())) {
        actions += tile('go', 'check', 'Clear', 'data-act="clear"' + id,
                        'Clear \u2014 Reset failed state and restore take');
      }
      // Again comes from the branches below when there is audio, and from here when
      // there is not, so a failed take never shows it twice.
      if (!take.has_audio) {
        actions += tile('again', 'again', 'Again', 'data-act="again"' + id,
                        'Again \u2014 Re-plan this song with a fresh seed');
      }
    }
    if (take.abc && take.abc.length > 50) {
      actions += tile('score', 'score', 'Score', 'data-act="open"' + id,
                      'Score \u2014 View and edit the ABC score notation and piano roll');
    }
    if (take.has_audio) {
      // Named carefully: `live` above already holds the status line for this card,
      // and var is function scoped, so reusing the name printed true or false there.
      var isLive = State.playing === take.id;
      actions += tile('play' + (isLive ? ' playing' : ''), isLive ? 'pause' : 'play',
                      isLive ? 'Pause' : 'Play', 'data-act="play"' + id,
                      isLive ? 'Pause \u2014 Pause audio playback' : 'Play \u2014 Listen to this take (Spacebar)');
      actions += downloadTile(take);
      actions += tile('stems', 'stems', 'Stems', 'data-act="stems"' + id,
                      'Stems \u2014 Separate vocals, instruments, drums, and bass tracks');
      actions += tile('again', 'again', 'Again', 'data-act="again"' + id,
                      'Again \u2014 Re-plan this song with a fresh seed');
    }
    actions += tile('star' + (take.favourite ? ' on' : ''), 'star', 'Star', 'data-act="star"' + id,
                    take.favourite ? 'Starred \u2014 Click to remove from favourites' : 'Star \u2014 Add to favourites');
    actions += tile('del', 'trash', 'Delete', 'data-act="del"' + id,
                    'Delete \u2014 Remove this take permanently');
    var classes = 'take';
    if (State.picked[take.id]) { classes += ' picked'; }
    if (State.playing === take.id) { classes += ' playing'; }
    // The left column points at a take either through the editor, or through a
    // cover retake, where the score in the box belongs to the source.
    if ((selectedTakeId() || takeIdInEditor()) === take.id) {
      // tone-*, not song/cover: a plain .cover class belongs to the 46px tile.
      classes += ' editing ' + ({ song: 'tone-song', instrumental: 'tone-inst' }[take.kind] || 'tone-cover');
    }
    var coverTip = take.kind === 'song'
      ? 'Song \u2014 written from a prompt'
      : (take.kind === 'instrumental'
          ? 'Instrumental \u2014 created without vocal tracks'
          : 'Cover \u2014 reimagined from a source recording');
    return '<article class="' + classes + '" data-id="' + take.id + '">' +
      '<div class="take-head">' +
        '<div class="take-icon">' +
          '<div class="cover ' + ({ song: 'grad-song', instrumental: 'grad-inst' }[take.kind] || 'grad-cover') + '" title="' + esc(coverTip) + '" aria-label="' + esc(coverTip) + '">' + initials(take.title) + '</div>' +
          '<label class="pick" title="Select this take for bulk actions or batch deleting">' +
            '<input type="checkbox" data-act="pick"' + id + (State.picked[take.id] ? ' checked' : '') + '>' +
          '</label>' +
        '</div>' +
        '<div class="take-headtext">' +
          '<div class="take-title" data-act="rename" data-id="' + take.id + '" title="' + esc(take.title) + ' \u2014 double-click to rename">' + esc(take.title) + '</div>' +
          '<div class="take-meta" title="' + esc(meta.join(' \u00b7 ')) + '">' + esc(meta.join(' \u00b7 ')) + '</div>' +
        '</div>' +
        // Occasional, so small corner buttons rather than tiles in an already full row.
        '<div class="take-corner">' +
          (take.abc && take.abc.length > 50 && status !== 'queued' && status !== 'running'
            ? '<button class="take-move" data-act="revoice"' + id + ' title="Sing again \u2014 The same score with a new seed. The backing and phrasing come out new; with a style LoRA the voice usually stays close"' +
              ' aria-label="Sing again">' + icon('voice') + '</button>' +
              '<button class="take-move" data-act="variations"' + id + ' title="Variations \u2014 Render this score in other interpretations"' +
              ' aria-label="Variations">' + icon('variations') + '</button>' +
              '<button class="take-move" data-act="tries"' + id + ' title="Try more \u2014 The same score and words again with new seeds, or at other Planner strengths"' +
              ' aria-label="Try more">' + icon('dice') + '</button>'
            : '') +
          // Once normalised it has nothing left to offer, so it goes.
          (status === 'done' && take.has_audio && !take.normalised && !State.normalising[take.id]
            ? '<button class="take-move" data-act="normalise"' + id + ' title="Normalise \u2014 Bring this take to the usual loudness. The file as rendered is kept"' +
              ' aria-label="Normalise">' + icon('level') + '</button>'
            : '') +
          '<button class="take-move' + (window.Rack && window.Rack.isOpen && window.Rack.currentTakeId === take.id ? ' active' : '') + '" data-act="mastering"' + id + ' title="Mastering Rack \u2014 Vintage EQ, Compressor, Limiter" aria-label="Mastering Rack">' +
            icon('mastering') + '</button>' +
          '<button class="take-move" data-act="move"' + id + ' title="Move \u2014 Move to another space" aria-label="Move">' +
            icon('move') + '</button>' +
        '</div>' +
      '</div>' +
      '<div class="take-style" title="' + esc(take.style) + '">' + esc(take.style) + '</div>' +
      '<div class="take-live">' + live + '</div>' +
      '<div class="take-actions">' + actions + '</div>' +
      stemsBlock(take) +
    '</article>';
  }).join('');
  paintBulk();
  paintSheet();
}

/* Takes normalised before the level could be chosen have none recorded; all were -14. */
function normalisedTo(take) {
  var level = take.normalised_to == null ? -14 : take.normalised_to;
  return 'Normalised to ' + (level < 0 ? '\u2212' : '') + Math.abs(level) + ' LUFS.';
}

function startRenameTake(titleEl, takeId) {
  var take = takeById(takeId);
  if (!take) { return; }
  if (titleEl.querySelector('input')) { return; }

  var currentTitle = take.title;
  var input = document.createElement('input');
  input.type = 'text';
  input.className = 'take-title-input';
  input.value = currentTitle;
  input.maxLength = 200;
  input.title = 'Press Enter to save, Esc to cancel';

  titleEl.textContent = '';
  titleEl.appendChild(input);
  if (window.getSelection) {
    var sel = window.getSelection();
    if (sel && sel.removeAllRanges) { sel.removeAllRanges(); }
  }
  input.focus();
  input.select();

  var finished = false;

  async function finish(save) {
    if (finished) { return; }
    finished = true;
    var newTitle = input.value.trim();
    if (save && newTitle && newTitle !== currentTitle) {
      try {
        var updated = await api('/api/takes/' + takeId + '/rename', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: newTitle })
        });
        take.title = updated.title;
        if ((selectedTakeId() || takeIdInEditor()) === takeId) {
          $('title').value = updated.title;
          saveForm();
        }
        var card = titleEl.closest('.take');
        if (card) {
          var cover = card.querySelector('.cover');
          if (cover) { cover.textContent = initials(updated.title); }
        }
        statusLine('Renamed take to \u201c' + updated.title + '\u201d.', 'good');
      } catch (err) {
        statusLine('Could not rename take: ' + err.message, 'bad');
      }
    }
    titleEl.textContent = take.title;
  }

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      finish(true);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
      finish(false);
    }
  });

  input.addEventListener('blur', function () {
    finish(true);
  });

  input.addEventListener('click', function (e) {
    e.stopPropagation();
  });
  input.addEventListener('dblclick', function (e) {
    e.stopPropagation();
  });
}

/* The play tile is a toggle. The active one pulses, shows a pause icon, and stops
   the audio when pressed again, so the live take is obvious at a glance. */
function togglePlay(id) {
  var audio = $('audio');
  if (State.playing === id && !audio.paused) {
    audio.pause();          // keeps currentTime, so Play resumes where it stopped
    State.playing = null;
    paintTakes();
    paintBulk();
    paintTransport();
    return;
  }
  playTake(id);
}

function playTake(id) {
  if (window.PianoRoll && window.PianoRoll.isPlaying) {
    window.PianoRoll.stop();
  }
  var take = State.takes.filter(function (t) { return t.id === id; })[0];
  // The take loaded in the player may belong to a space no longer on screen.
  if (!take && State.loadedTake && State.loadedTake.id === id) { take = State.loadedTake; }
  if (!take) { return; }
  State.loadedTake = take;
  State.playing = id;
  State.audition = null;
  State.playRequestedAt = Date.now();
  wave.kind = take.kind;   // the waveform takes the colour of what is playing
  var audio = $('audio');
  var version = take.normalised ? '?level=normalised' : '';
  var url = '/api/takes/' + id + '/audio' + version;
  if (State.loadedId === id && audio.src) {
    // Same take: resume.  Assigning src again would reload the media and throw the
    // position away, which is what made Pause behave like Stop.
    if (audio.ended) { audio.currentTime = 0; }
    audio.play().catch(function () {});
  } else {
    State.loadedId = id;
    audio.src = url;
    audio.play().catch(function () {});
    loadWave(url, '/api/takes/' + id + '/peaks' + version);
  }
  $('np-title').textContent = take.title;
  var position = takePosition(id);
  $('np-meta').textContent = (position ? 'take ' + position.index + ' of ' + position.total + ' \u00b7 ' : '') +
    (take.duration ? secs(take.duration) : take.style.slice(0, 60));
  $('np-cover').className = 'np-cover ' + ({ song: 'grad-song', instrumental: 'grad-inst' }[take.kind] || 'grad-cover');
  updateMediaSession(take);
  if (window.Rack) { window.Rack.onTake(take); }
  paintTransport();
  paintTakes();
}

/* ------------------------------------------------------------- transport ---
   The bar is the only way to control playback: the native audio element is
   hidden, so these buttons are it. Previous and next walk the library in the
   order the cards are shown. */
var SPEEDS = [0.75, 1, 1.25, 1.5];
var SPEED_LABELS = ['0.75x', '1.0x', '1.25x', '1.5x'];
var speedIndex = 1;

function playableTakes() {
  return State.takes.filter(function (take) { return take.has_audio; });
}

function currentTakeId() {
  return State.playing || State.loadedId || null;
}

function currentTake() {
  var id = currentTakeId();
  for (var i = 0; i < State.takes.length; i++) {
    if (State.takes[i].id === id) { return State.takes[i]; }
  }
  return State.loadedTake && State.loadedTake.id === id ? State.loadedTake : null;
}

function takePosition(id) {
  var list = playableTakes();
  for (var i = 0; i < list.length; i++) {
    if (list[i].id === id) { return { index: i + 1, total: list.length }; }
  }
  return null;
}

function activateTakeRecording(take) {
  if (!take) { return; }
  var audio = $('audio');
  if (!audio) { return; }

  // If audio is currently playing, do not stop or interrupt playback,
  // and do not alter the active playback's mastering rack settings.
  // The selected take remains highlighted and will be played if Spacebar or the play icon is pressed.
  if (!audio.paused && !audio.ended) {
    return;
  }

  // 1. If the take has rendered audio, load its audio into the transport bar
  if (take.has_audio) {
    var version = take.normalised ? '?level=normalised' : '';
    var url = '/api/takes/' + take.id + '/audio' + version;
    var peaksUrl = '/api/takes/' + take.id + '/peaks' + version;
    var isLoaded = (State.loadedId === take.id && (audio.src || audio.currentSrc));

    if (audio && !audio.paused) {
      audio.pause();
    }
    State.playing = null;
    State.audition = null;
    State.loadedId = take.id;
    State.loadedTake = take;
    wave.kind = take.kind;

    if (!isLoaded) {
      audio.src = url;
      loadWave(url, peaksUrl);
    }
    $('np-title').textContent = take.title;
    var position = takePosition(take.id);
    $('np-meta').textContent = (position ? 'take ' + position.index + ' of ' + position.total + ' \u00b7 ' : '') +
      (take.duration ? secs(take.duration) : (take.style || '').slice(0, 60));
    $('np-cover').className = 'np-cover ' + ({ song: 'grad-song', instrumental: 'grad-inst' }[take.kind] || 'grad-cover');
    $('t-now').textContent = secs(audio.currentTime || 0);
    $('t-total').textContent = take.duration ? secs(take.duration) : '--:--';
    updateMediaSession(take);
    if (window.Rack) { window.Rack.onTake(take); }
    paintTransport();
    paintTakes();
    return;
  }

  // 2. Otherwise if the take has a source recording (cover / instrumental from recording), load that
  if (take.source_id && typeof sourceById === 'function') {
    var source = sourceById(take.source_id);
    if (source) {
      if (State.audition === source.id && !audio.paused && !audio.ended) {
        return;
      }
      var isMidi = Boolean(source.filename && source.filename.match(/\.midi?$/i));
      var sel = $('score-sf2-select');
      var activeSf2 = sel && sel.value ? sel.value : '';
      var sf2Param = activeSf2 ? '?sf2=' + encodeURIComponent(activeSf2) : '';
      var sfLabel = (sel && sel.selectedOptions && sel.selectedOptions[0])
        ? sel.selectedOptions[0].textContent
        : (activeSf2 ? activeSf2.replace(/_/g, ' ').replace(/\.sf2$/i, '') : 'SoundFont');
      var url = isMidi
        ? '/api/sources/' + source.id + '/rendered-audio' + sf2Param
        : '/api/sources/' + source.id + '/audio';
      var peaksUrl = '/api/sources/' + source.id + '/peaks' + (isMidi ? sf2Param : '');
      var isLoaded = (State.audition === source.id && (audio.src || audio.currentSrc));

      if (audio && !audio.paused) {
        audio.pause();
      }
      State.playing = null;
      State.loadedId = null;
      State.loadedTake = null;
      State.audition = source.id;
      State.auditionLoading = false;
      wave.kind = 'cover';

      if (!isLoaded) {
        audio.src = url;
        loadWave(url, peaksUrl);
      }
      $('np-title').textContent = source.title;
      $('np-meta').textContent = isMidi ? ('MIDI Recording (' + sfLabel + ')') : 'the recording being covered';
      $('np-cover').className = 'np-cover grad-cover';
      updateMediaSession({ title: source.title, style: isMidi ? ('MIDI Recording (' + sfLabel + ')') : 'the recording being covered' });
      paintTransport();
      paintTakes();
      paintAudition();
      return;
    }
  }

  // 3. Take has neither rendered audio nor a source recording (planned / queued prompt song)
  if (audio && !audio.paused) {
    audio.pause();
  }
  State.playing = null;
  State.audition = null;
  State.loadedId = null;
  State.loadedTake = take;
  audio.removeAttribute('src');
  wave.peaks = null;
  wave.rmss = null;
  wave.ratio = 0;
  drawWave();
  $('np-title').textContent = take.title || 'Untitled take';
  $('np-meta').textContent = take.status === 'planned' ? 'plan ready (no audio yet)' : (take.status ? take.status + ' (no audio yet)' : 'no audio yet');
  $('np-cover').className = 'np-cover ' + ({ song: 'grad-song', instrumental: 'grad-inst' }[take.kind] || 'grad-cover');
  $('t-now').textContent = '0:00';
  $('t-total').textContent = '--:--';
  if (window.Rack) { window.Rack.onTake(take); }
  paintTransport();
  paintTakes();
}

function stepTake(delta) {
  var list = playableTakes();
  if (!list.length) { return; }
  var id = currentTakeId();
  var index = -1;
  for (var i = 0; i < list.length; i++) { if (list[i].id === id) { index = i; } }
  var next = index === -1 ? 0 : (index + delta + list.length) % list.length;
  // The left column follows, as it does for Play on a card: a take you are hearing
  // is the take whose seed and settings you see.
  selectTake(list[next]);
  playTake(list[next].id);
}

function nudge(seconds) {
  var audio = $('audio');
  if (!audio.duration || !isFinite(audio.duration)) { return; }
  audio.currentTime = Math.max(0, Math.min(audio.duration, audio.currentTime + seconds));
  updateTimes();
}

function editorTake() {
  if (State.formTake && State.formTake.id) {
    return takeById(State.formTake.id) || State.formTake;
  }
  var id = selectedTakeId();
  return id ? takeById(id) : null;
}

function updateTimes() {
  var audio = $('audio');
  var cur = audio.currentTime || 0;
  var dur = audio.duration;
  var hasDur = dur && isFinite(dur);
  $('t-now').textContent = secs(cur);
  $('t-total').textContent = hasDur ? secs(dur) : '--:--';
  var edTake = editorTake();
  if (edTake && State.loadedId === edTake.id) {
    var edNow = $('ed-t-now');
    if (edNow) { edNow.textContent = secs(cur); }
    var edTotal = $('ed-t-total');
    if (edTotal) { edTotal.textContent = hasDur ? secs(dur) : '--:--'; }
    var edSeek = $('ed-seek');
    if (edSeek && !edSeek.dataset.dragging) {
      edSeek.value = (hasDur && dur > 0) ? Math.round((cur / dur) * 1000) : 0;
    }
  }
}

function paintTransport() {
  var audio = $('audio');
  // What is playing may be a stem rather than a take, and a stem deliberately
  // owns no take. The button follows the sound, so it shows Pause whenever
  // something is sounding.
  var playing = Boolean(audio.currentSrc || audio.src) && !audio.paused && !audio.ended;
  var playBtn = $('btn-play');
  var playState = playing ? 'pause' : 'play';
  var playSvg = playing
    ? '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M9 5h2.6v14H9zM13.4 5H16v14h-2.6z"/></svg>'
    : '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.4v13.2L19 12z"/></svg>';
  var playTitle = playing ? 'Pause' : 'Play';
  if (playBtn) {
    if (playBtn.dataset.state !== playState) {
      playBtn.dataset.state = playState;
      playBtn.innerHTML = playSvg;
      playBtn.title = playTitle;
      playBtn.setAttribute('aria-label', playTitle);
    }
  }
  $('btn-repeat').classList.toggle('on', Boolean(audio.loop));
  var take = currentTake();
  $('btn-star').disabled = !take;
  $('btn-star').classList.toggle('on', Boolean(take && take.favourite));
  var canStep = playableTakes().length >= 2;
  $('btn-prev').disabled = !canStep;
  $('btn-next').disabled = !canStep;
  if ($('ed-btn-prev')) { $('ed-btn-prev').disabled = !canStep; }
  if ($('ed-btn-next')) { $('ed-btn-next').disabled = !canStep; }
  $('btn-mute').classList.toggle('on', Boolean(audio.muted || audio.volume === 0));
  paintEdTransport();
}

function paintEdTransport() {
  var box = $('ed-transport');
  if (!box) { return; }
  var take = editorTake();
  var shouldShow = Boolean(editorOpen() && take && take.has_audio);
  box.classList.toggle('hidden', !shouldShow);
  if (!shouldShow) { paintPlayingSection(-1); return; }

  var audio = $('audio');
  var isPlaying = Boolean(take && State.playing === take.id && audio && !audio.paused && !audio.ended);
  var isLoaded = Boolean(take && State.loadedId === take.id && audio && (audio.currentSrc || audio.src));

  var edPlayBtn = $('ed-btn-play');
  if (edPlayBtn) {
    var playState = isPlaying ? 'pause' : 'play';
    if (edPlayBtn.dataset.state !== playState) {
      edPlayBtn.dataset.state = playState;
      edPlayBtn.innerHTML = isPlaying
        ? '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M9 5h2.6v14H9zM13.4 5H16v14h-2.6z"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.4v13.2L19 12z"/></svg>';
      edPlayBtn.title = isPlaying ? 'Pause' : 'Play';
      edPlayBtn.setAttribute('aria-label', isPlaying ? 'Pause' : 'Play');
    }
  }

  var titleEl = $('ed-np-title');
  if (titleEl && take) {
    var pos = takePosition(take.id);
    var label = take.title || 'Untitled take';
    if (pos) { label += ' \u00b7 take ' + pos.index + ' of ' + pos.total; }
    titleEl.textContent = label;
    titleEl.title = label;
  }

  var cur = (isLoaded && audio) ? (audio.currentTime || 0) : 0;
  var dur = (isLoaded && audio && audio.duration && isFinite(audio.duration)) ? audio.duration : (take.duration || 0);
  var hasDur = dur && isFinite(dur) && dur > 0;
  var edNow = $('ed-t-now');
  if (edNow) { edNow.textContent = secs(cur); }
  var edTotal = $('ed-t-total');
  if (edTotal) { edTotal.textContent = hasDur ? secs(dur) : '--:--'; }
  var edSeek = $('ed-seek');
  if (edSeek && !edSeek.dataset.dragging) {
    edSeek.value = (hasDur && dur > 0) ? Math.round((cur / dur) * 1000) : 0;
  }
  paintPlayingSection(isLoaded ? cur : -1);
}

/* The section the take is at, lit in the list above the player. The list's times are those of the score,
   which the render follows closely, so this is the section a listener would name; it is not drawn once the
   sections have been rearranged, since the audio is still the original order. */
function paintPlayingSection(seconds) {
  var body = $('structure-body');
  if (!body) { return; }
  var rows = body.querySelectorAll('.struct-row[data-i]');
  if (!rows.length) { return; }
  var at = -1;
  var original = !State.sectionsOriginal || State.sectionsOriginal === $('abc').value;
  if (seconds >= 0 && original) {
    var text = $('abc').value;
    if (!State.sectionSpans || State.sectionSpans.text !== text) { State.sectionSpans = { text: text, spans: scoreSectionSpans(text) }; }
    var spans = State.sectionSpans.spans;
    var lead = sectionLead(text);
    for (var i = 0; i < spans.length; i++) {
      var from = sectionStart(spans[i], i, lead);
      var to = i + 1 < spans.length ? sectionStart(spans[i + 1], i + 1, lead) : Infinity;
      if (seconds >= from && seconds < to) { at = i; break; }
    }
  }
  Array.prototype.forEach.call(rows, function (row) {
    row.classList.toggle('now', Number(row.dataset.i) === at);
  });
}

function updateMediaSession(take) {
  if (!('mediaSession' in navigator) || typeof MediaMetadata === 'undefined') { return; }
  try {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: take.title,
      artist: (take.style || '').split(',')[0],
      album: 'Yeufonic'
    });
  } catch (err) { /* older browsers */ }
}

/* ------------------------------------------------------------- waveform ---
   Drawn from the decoded audio. Click or drag anywhere to seek, and the played
   part fills in as the song runs. */
var audioCtx = null;
var wave = { peaks: null, ratio: 0, raf: null, seeking: false };
// One column per device pixel at draw time, sampled from a fixed 1024 column
// analysis, so a window resize does not re-decode the audio.
var WAVE_COLS = 1024;
var WAVE_HEIGHT = 56;

function waveCanvas() {
  var canvas = $('wave');
  var dpr = window.devicePixelRatio || 1;
  var width = Math.max(120, canvas.clientWidth || 600);
  var targetW = Math.round(width * dpr);
  var targetH = Math.round(WAVE_HEIGHT * dpr);
  if (canvas.width !== targetW || canvas.height !== targetH) {
    canvas.width = targetW;
    canvas.height = targetH;
  }
  return canvas;
}

function drawWave() {
  var canvas = waveCanvas();
  var ctx = canvas.getContext('2d');
  var w = canvas.width;
  var h = canvas.height;
  var dpr = window.devicePixelRatio || 1;
  ctx.clearRect(0, 0, w, h);
  if (!wave.peaks) { return; }

  // A mirrored envelope from the peak values, with an inner body from the RMS.
  // The outline shows transients, the body shows loudness, which is what makes a
  // thin or squashed mix visible before you listen to it.
  var columns = Math.max(1, Math.floor(w / dpr));
  var mid = h / 2;
  var amp = h * 0.46;
  var outline = new Path2D();
  var body = new Path2D();
  var i;
  var x;
  var p;
  var r;
  for (i = 0; i < columns; i++) {
    p = column(wave.peaks, i, columns) * amp;
    r = column(wave.rmss, i, columns) * amp;
    x = i * dpr;
    if (i === 0) {
      outline.moveTo(x, mid - p);
      body.moveTo(x, mid - r);
    } else {
      outline.lineTo(x, mid - p);
      body.lineTo(x, mid - r);
    }
  }
  for (i = columns - 1; i >= 0; i--) {
    p = column(wave.peaks, i, columns) * amp;
    r = column(wave.rmss, i, columns) * amp;
    x = i * dpr;
    outline.lineTo(x, mid + p);
    body.lineTo(x, mid + r);
  }
  outline.closePath();
  body.closePath();

  // The played part wears the take's own colour: blue for a song from a prompt,
  // pink for a cover. Stems and anything else keep the neutral violet.
  var tone = waveTone();
  // The unplayed part and the playhead are drawn in the theme's own ink and text.
  var ink = themeColour('--ink') || '255 255 255';
  function paint(played) {
    ctx.fillStyle = played ? tone.outline : 'rgb(' + ink + ' / 0.10)';
    ctx.fill(outline);
    ctx.fillStyle = played ? tone.body : 'rgb(' + ink + ' / 0.24)';
    ctx.fill(body);
  }

  paint(false);
  var head = Math.round(wave.ratio * w);
  ctx.save();
  ctx.beginPath();
  ctx.rect(0, 0, head, h);
  ctx.clip();
  paint(true);
  ctx.restore();

  // The theme's text colour, so the playhead shows on a pink waveform as well as a
  // blue one, in any theme.
  ctx.fillStyle = themeColour('--text') || '#f4f4f7';
  ctx.fillRect(Math.max(0, Math.min(w - 2, head - 1)), 0, Math.max(2, 2 * dpr), h);
}

function waveTone() {
  var prefix = wave.kind === 'song' ? '--wave-song'
             : wave.kind === 'instrumental' ? '--wave-inst'
             : wave.kind === 'cover' ? '--wave-cover'
             : '--wave-default';
  var body = themeColour(prefix + '-body');
  var outline = themeColour(prefix + '-outline');
  if (body && outline) { return { body: body, outline: outline }; }
  if (wave.kind === 'song') { return { body: 'rgba(56, 175, 235, 0.70)', outline: 'rgba(56, 175, 235, 0.28)' }; }
  if (wave.kind === 'instrumental') { return { body: 'rgba(52, 200, 140, 0.70)', outline: 'rgba(52, 200, 140, 0.28)' }; }
  if (wave.kind === 'cover') { return { body: 'rgba(220, 100, 155, 0.70)', outline: 'rgba(220, 100, 155, 0.28)' }; }
  return { body: 'rgba(167, 139, 250, 0.70)', outline: 'rgba(167, 139, 250, 0.28)' };
}

function normalise(values) {
  var max = 0;
  for (var i = 0; i < values.length; i++) { if (values[i] > max) { max = values[i]; } }
  if (!max) { return values; }
  return values.map(function (v) { return v / max; });
}

/* The server computes the waveform once and caches it.  Decoding the file here is
   the fallback, for a server that cannot. */
async function loadWave(url, peaksUrl) {
  wave.peaks = null;
  wave.rmss = null;
  wave.ratio = 0;
  wave.token = (wave.token || 0) + 1;
  var token = wave.token;
  drawWave();
  if (peaksUrl) {
    try {
      var cached = await api(peaksUrl);
      if (token !== wave.token) { return; }   // another take started meanwhile
      if (cached && cached.peaks && cached.peaks.length) {
        wave.peaks = cached.peaks;
        wave.rmss = cached.rms;
        drawWave();
        return;
      }
    } catch (err) { /* decode it here instead */ }
  }
  try {
    var response = await fetch(url);
    var buffer = await response.arrayBuffer();
    if (!audioCtx) { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); }
    if (audioCtx.state === 'suspended') { audioCtx.resume(); }
    var decoded = await audioCtx.decodeAudioData(buffer.slice(0));
    var data = decoded.getChannelData(0);
    var per = Math.max(1, Math.floor(data.length / WAVE_COLS));
    var peaks = [];
    var rmss = [];
    for (var i = 0; i < WAVE_COLS; i++) {
      var start = i * per;
      var peak = 0;
      var sum = 0;
      var count = 0;
      for (var j = 0; j < per; j += 16) {
        var value = data[start + j] || 0;
        var magnitude = value < 0 ? -value : value;
        if (magnitude > peak) { peak = magnitude; }
        sum += value * value;
        count += 1;
      }
      peaks.push(peak);
      rmss.push(count ? Math.sqrt(sum / count) : 0);
    }
    if (token !== wave.token) { return; }
    wave.peaks = normalise(peaks);
    wave.rmss = normalise(rmss);
    drawWave();
  } catch (err) { /* the waveform is optional. The player still works. */ }
}

function column(values, index, columns) {
  if (!values) { return 0; }
  return values[Math.min(values.length - 1, Math.floor(index * values.length / columns))];
}

function syncWaveRatio() {
  var audio = $('audio');
  if (audio.duration && isFinite(audio.duration)) {
    wave.ratio = Math.max(0, Math.min(1, audio.currentTime / audio.duration));
  }
}

function waveLoop() {
  syncWaveRatio();
  drawWave();
  updateTimes();
  if (!$('audio').paused && !$('audio').ended) {
    wave.raf = requestAnimationFrame(waveLoop);
  } else {
    wave.raf = null;
  }
}

function startWaveLoop() {
  if (wave.raf === null) { wave.raf = requestAnimationFrame(waveLoop); }
}

function stopWaveLoop() {
  if (wave.raf !== null) { cancelAnimationFrame(wave.raf); wave.raf = null; }
  syncWaveRatio();
  drawWave();
  updateTimes();
}

function seekFromPointer(event) {
  var canvas = $('wave');
  var audio = $('audio');
  var rect = canvas.getBoundingClientRect();
  if (!rect.width || !audio.duration || !isFinite(audio.duration)) { return; }
  var ratio = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
  audio.currentTime = ratio * audio.duration;
  wave.ratio = ratio;
  drawWave();
  updateTimes();
}

function wireTransport() {
  var audio = $('audio');
  var lastPauseAt = 0;
  $('btn-play').addEventListener('click', function () {
    if (window.PianoRoll && window.PianoRoll.isPlaying) {
      window.PianoRoll.stop();
      State.audition = null;
      paintAudition();
      paintTransport();
      return;
    }
    var now = Date.now();
    var activeId = typeof selectedTakeId === 'function' ? selectedTakeId() : null;
    var activeTake = (activeId && typeof takeById === 'function' ? takeById(activeId) : null) ||
                     (activeId && State.formTake && State.formTake.id === activeId ? State.formTake : null);

    // 1. Audio is currently sounding (take, source audition, or stem)
    if (!audio.paused && !audio.ended) {
      // If a different take is highlighted/selected, switch to and play that take!
      if (activeTake && activeTake.id !== State.playing) {
        if (activeTake.has_audio) {
          playTake(activeTake.id);
          return;
        }
        if (activeTake.source_id && typeof sourceById === 'function') {
          var src = sourceById(activeTake.source_id);
          if (src) {
            if ($('source-select')) { $('source-select').value = src.id; }
            playRecording();
            return;
          }
        }
        statusLine('This take has not been rendered yet.', 'hint');
        lastPauseAt = now;
        audio.pause();
        if (State.playing) { State.playing = null; paintTakes(); }
        paintTransport();
        return;
      }

      // Otherwise (the selected take is the one currently playing, or no different take is selected), pause it:
      lastPauseAt = now;
      audio.pause();
      if (State.playing) { State.playing = null; paintTakes(); }
      paintTransport();
      return;
    }

    // Prevent accidental rapid double-clicks immediately restarting playback right after pause
    if (now - lastPauseAt < 300) {
      return;
    }

    // 2. Audio is not playing: start or resume the selected take if one is highlighted
    if (activeTake) {
      if (activeTake.has_audio) {
        if (State.loadedId === activeTake.id && audio.src && !audio.ended && audio.currentTime > 0) {
          audio.play().catch(function () {});
          State.playing = activeTake.id;
          paintTakes();
          paintTransport();
          return;
        }
        playTake(activeTake.id);
        return;
      }
      if (activeTake.source_id && typeof sourceById === 'function') {
        var src = sourceById(activeTake.source_id);
        if (src) {
          if ($('source-select')) { $('source-select').value = src.id; }
          playRecording();
          return;
        }
      }
      statusLine('This take has not been rendered yet.', 'hint');
      return;
    }

    var id = currentTakeId();
    if (id) { togglePlay(id); return; }
    if (audio.src && !audio.ended) { audio.play().catch(function () {}); return; }
    var list = playableTakes();
    if (list.length) { playTake(list[0].id); }
  });
  $('btn-prev').addEventListener('click', function () { stepTake(-1); });
  $('btn-next').addEventListener('click', function () { stepTake(1); });
  $('btn-back').addEventListener('click', function () { nudge(-10); });
  $('btn-fwd').addEventListener('click', function () { nudge(10); });
  if ($('ed-btn-play')) {
    $('ed-btn-play').addEventListener('click', function () {
      var take = editorTake();
      if (!take || !take.has_audio) { return; }
      var audio = $('audio');
      if (State.playing === take.id && audio && !audio.paused && !audio.ended) {
        audio.pause();
        State.playing = null;
        paintTransport();
        paintTakes();
        return;
      }
      playTake(take.id);
    });
  }
  if ($('ed-btn-prev')) {
    $('ed-btn-prev').addEventListener('click', function () {
      var list = playableTakes();
      if (list.length < 2) { return; }
      var take = editorTake();
      var currentId = (take && take.has_audio) ? take.id : currentTakeId();
      var index = -1;
      for (var i = 0; i < list.length; i++) { if (list[i].id === currentId) { index = i; } }
      var prev = index === -1 ? 0 : (index - 1 + list.length) % list.length;
      selectTake(list[prev]);
      playTake(list[prev].id);
      paintEditor();
    });
  }
  if ($('ed-btn-next')) {
    $('ed-btn-next').addEventListener('click', function () {
      var list = playableTakes();
      if (list.length < 2) { return; }
      var take = editorTake();
      var currentId = (take && take.has_audio) ? take.id : currentTakeId();
      var index = -1;
      for (var i = 0; i < list.length; i++) { if (list[i].id === currentId) { index = i; } }
      var next = index === -1 ? 0 : (index + 1) % list.length;
      selectTake(list[next]);
      playTake(list[next].id);
      paintEditor();
    });
  }
  if ($('ed-btn-back')) {
    $('ed-btn-back').addEventListener('click', function () {
      var take = editorTake();
      if (!take || !take.has_audio) { return; }
      if (State.loadedId === take.id) { nudge(-10); }
    });
  }
  if ($('ed-btn-fwd')) {
    $('ed-btn-fwd').addEventListener('click', function () {
      var take = editorTake();
      if (!take || !take.has_audio) { return; }
      if (State.loadedId === take.id) { nudge(10); }
    });
  }
  var edSeek = $('ed-seek');
  if (edSeek) {
    edSeek.addEventListener('input', function () {
      edSeek.dataset.dragging = '1';
      var take = editorTake();
      var a = $('audio');
      var dur = (take && State.loadedId === take.id && a && a.duration && isFinite(a.duration) && a.duration > 0)
        ? a.duration
        : (take ? (take.duration || 0) : 0);
      if (dur > 0) {
        var pos = (Number(edSeek.value) / 1000) * dur;
        var edNow = $('ed-t-now');
        if (edNow) { edNow.textContent = secs(pos); }
      }
    });
    edSeek.addEventListener('change', function () {
      delete edSeek.dataset.dragging;
      var take = editorTake();
      if (!take || !take.has_audio) { return; }
      var a = $('audio');
      var dur = (State.loadedId === take.id && a && a.duration && isFinite(a.duration) && a.duration > 0)
        ? a.duration
        : (take.duration || 0);
      if (dur <= 0) { return; }
      var targetTime = (Number(edSeek.value) / 1000) * dur;
      if (State.loadedId === take.id && a) {
        a.currentTime = targetTime;
        updateTimes();
      } else {
        playTake(take.id);
        if (a) { a.currentTime = targetTime; }
        updateTimes();
      }
    });
  }
  $('btn-repeat').addEventListener('click', function () {
    audio.loop = !audio.loop;
    paintTransport();
  });
  $('btn-speed').addEventListener('click', function () {
    speedIndex = (speedIndex + 1) % SPEEDS.length;
    audio.playbackRate = SPEEDS[speedIndex];
    $('btn-speed').textContent = SPEED_LABELS[speedIndex];
    $('btn-speed').classList.toggle('on', SPEEDS[speedIndex] !== 1);
  });
  $('btn-star').addEventListener('click', async function () {
    var take = currentTake();
    if (!take) { return; }
    try {
      await api('/api/takes/' + take.id + '/favourite?value=' + (take.favourite ? 'false' : 'true'), { method: 'POST' });
      take.favourite = take.favourite ? 0 : 1;
      paintTransport();
      loadTakes();
    } catch (err) { /* leave the star as it was */ }
  });
  if ($('btn-fx-rack')) {
    $('btn-fx-rack').addEventListener('click', function () {
      if (window.Rack) { window.Rack.toggle(); }
    });
  }
  $('btn-mute').addEventListener('click', function () {
    audio.muted = !audio.muted;
    paintTransport();
  });
  $('volume').addEventListener('input', function () {
    audio.volume = Number($('volume').value) / 100;
    audio.muted = false;
    try { localStorage.setItem('yue2.volume', $('volume').value); } catch (err) { /* private mode */ }
    paintTransport();
  });
  var saved = null;
  try { saved = localStorage.getItem('yue2.volume'); } catch (err) { saved = null; }
  if (saved !== null) {
    $('volume').value = saved;
    audio.volume = Number(saved) / 100;
  }

  if ('mediaSession' in navigator) {
    var handlers = {
      play: function () { var id = currentTakeId(); if (id && audio.paused) { togglePlay(id); } },
      pause: function () { var id = currentTakeId(); if (id && !audio.paused) { togglePlay(id); } },
      previoustrack: function () { stepTake(-1); },
      nexttrack: function () { stepTake(1); },
      seekbackward: function () { nudge(-10); },
      seekforward: function () { nudge(10); }
    };
    Object.keys(handlers).forEach(function (name) {
      try { navigator.mediaSession.setActionHandler(name, handlers[name]); } catch (err) { /* unsupported action */ }
    });
  }

  ['play', 'playing', 'pause', 'ended', 'loadedmetadata', 'durationchange', 'seeking', 'error'].forEach(function (name) {
    audio.addEventListener(name, function () {
      if (name === 'playing' && State.auditionLoading) {
        State.auditionLoading = false;
        var sel = $('score-sf2-select');
        var sfLabel = (sel && sel.selectedOptions && sel.selectedOptions[0]) ? sel.selectedOptions[0].textContent : 'SoundFont';
        $('np-meta').textContent = 'MIDI Recording (SoundFont: ' + sfLabel + ')';
        statusLine('Playing MIDI audio (' + sfLabel + ')', 'ok');
      }
      if (name === 'error' || name === 'ended' || name === 'pause') {
        State.auditionLoading = false;
      }
      updateTimes(); paintTransport(); paintAudition();
    });
  });
  audio.addEventListener('timeupdate', updateTimes);
  paintTransport();
}

function wireWave() {
  var canvas = $('wave');
  canvas.addEventListener('pointerdown', function (event) {
    wave.seeking = true;
    try { canvas.setPointerCapture(event.pointerId); } catch (err) { /* older browsers */ }
    seekFromPointer(event);
  });
  canvas.addEventListener('pointermove', function (event) {
    if (wave.seeking) { seekFromPointer(event); }
  });
  canvas.addEventListener('pointerup', function () { wave.seeking = false; });
  canvas.addEventListener('pointercancel', function () { wave.seeking = false; });
  window.addEventListener('resize', function () { drawWave(); });
  var audio = $('audio');
  audio.addEventListener('play', startWaveLoop);
  audio.addEventListener('playing', startWaveLoop);
  audio.addEventListener('pause', stopWaveLoop);
  audio.addEventListener('ended', function () {
    stopWaveLoop(); wave.ratio = 1; drawWave();
    State.playing = null; State.audition = null;
    var activeId = typeof selectedTakeId === 'function' ? selectedTakeId() : null;
    var activeTake = (activeId && typeof takeById === 'function' ? takeById(activeId) : null) ||
                     (activeId && State.formTake && State.formTake.id === activeId ? State.formTake : null);
    if (activeTake && typeof activateTakeRecording === 'function') {
      activateTakeRecording(activeTake);
    } else {
      paintTakes();
      paintBulk(); paintTransport(); paintAudition();
    }
  });
  audio.addEventListener('pause', function () {
    // Ignore the pause that fires while a new track is being loaded.
    if (Date.now() - (State.playRequestedAt || 0) < 800) { return; }
    if (State.playing) { State.playing = null; paintTakes(); paintTransport(); }
    // A recording being auditioned stays loaded while paused, so the bar and the
    // space bar resume it rather than starting a take. Only the sound stops.
    paintAudition();
  });
  ['play', 'playing', 'pause', 'ended'].forEach(function (name) { audio.addEventListener(name, paintStructureNotice); });
  audio.addEventListener('seeking', function () { syncWaveRatio(); drawWave(); });
  audio.addEventListener('timeupdate', function () { syncWaveRatio(); drawWave(); });
}

/* ------------------------------------------------------------------- form */
async function uploadFile(file) {
  if (!file) { return; }
  statusLine('Uploading ' + file.name + '\u2026', 'wait');
  var form = new FormData();
  form.append('file', file);
  try {
    var source = await api('/api/sources', { method: 'POST', body: form });
    await loadSources();
    $('source-select').value = source.id;
    setSelection({ formTakeId: Selection.formTakeId });
    paintSource();
    var msg = source.duplicate
      ? 'That recording is already in the library.'
      : (source.transcribe_state === 'done'
         ? 'Uploaded MIDI file. Score is ready.'
         : 'Uploaded. Transcribe it to get a score.');
    statusLine(msg, 'good');
  } catch (err) {
    statusLine('Upload failed: ' + err.message, 'bad');
  }
}

async function doTranscribe() {
  var source = currentSource();
  if (!source) { statusLine('Choose a recording first.', 'bad'); return; }
  try {
    await api('/api/sources/' + source.id + '/transcribe', { method: 'POST' });
    source.transcribe_state = 'queued';
    paintSource();
  } catch (err) {
    statusLine('Could not start: ' + err.message, 'bad');
  }
}

function coverProblem() {
  var source = currentSource();
  if (!source) { return 'Choose a recording first.'; }
  // A cover follows the recording's own melody, so it needs a score: the one
  // transcribed from it, or one in the box. With neither, rendering used to go
  // ahead and the model wrote its own melody, which is not a cover and sounded
  // like a different song.
  if (!source.has_score && !$('abc').value.trim()) {
    return 'This recording has not been transcribed, so there is no melody to cover. '
      + 'Press Transcribe first. For a melody YuE2 writes itself, use Song from a prompt.';
  }
  return '';
}

function coverBody(seed) {
  var source = currentSource();
  return withAdvancedSettings(withStyleLora({
    source_id: source.id,
    title: $('title').value.trim() || guessTitle($('lyrics').value) || source.title,
    style: $('style').value,
    lyrics: $('lyrics').value,
    abc: $('abc').value,
    mode: $('mode').value,
    seed: seed,
    interpretation: $('interpretation').value,
    max_duration: parseFloat($('max-duration').value) || 360,
    space_id: State.spaceId,
    realaudio: $('realaudio').checked, normalise: normaliseWanted()
  }));
}

async function doRender() {
  var status = $('render-status');
  var problem = coverProblem();
  if (problem) { status.textContent = problem; status.className = 'status bad'; return; }
  var body = coverBody(pickSeed());
  status.textContent = 'Queued\u2026';
  status.className = 'status';
  try {
    await api('/api/takes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    status.textContent = '';
    loadTakes();
    closeEditor();
  } catch (err) {
    status.textContent = 'Could not queue: ' + err.message;
    status.className = 'status bad';
  }
}

/* The score itself decides the length: bars, meter and tempo. Measured against six
   finished renders, this lands within about 5 per cent, unless the cap cuts the song short. */
/* As score.estimate on the server: a bar lasts its meter in quarter notes (6/8 is
   three, not six), Z4 is four bars of rest, and a voice can change meter part way. */
function planLength(abc) {
  if (!abc) { return null; }
  var tempo = /^Q:1\/4=(\d+)/m.exec(abc);
  var bpm = tempo ? parseInt(tempo[1], 10) : 120;
  var meterOf = function (found) { return [parseInt(found[1], 10), parseInt(found[2], 10) || 4]; };
  var headerMeter = [4, 4];
  var meters = {}, quarters = {}, bars = {};
  var voice = null;
  abc.split('\n').forEach(function (raw) {
    var line = raw.trim();
    if (line.indexOf('V:') === 0) { voice = line.slice(2).trim().split(/\s+/)[0] || null; return; }
    var meter = /^M:\s*(\d+)\/(\d+)/.exec(line);
    if (meter) {
      if (voice) { meters[voice] = meterOf(meter); } else { headerMeter = meterOf(meter); }
      return;
    }
    if (!line || line.charAt(0) === '%' || /^[A-Za-z]:/.test(line) || !voice) { return; }
    line.split('|').forEach(function (bar) {
      if (/^[\s:\[\]]*$/.test(bar)) { return; }
      var inline = /\[M:\s*(\d+)\/(\d+)/.exec(bar);
      if (inline) { meters[voice] = meterOf(inline); }
      var m = meters[voice] || headerMeter;
      var rest = /^\s*Z(\d*)\s*$/.exec(bar);
      var count = rest ? (parseInt(rest[1], 10) || 1) : 1;
      bars[voice] = (bars[voice] || 0) + count;
      quarters[voice] = (quarters[voice] || 0) + count * m[0] * 4 / m[1];
    });
  });
  var longest = null;
  Object.keys(quarters).forEach(function (name) { if (longest === null || quarters[name] > quarters[longest]) { longest = name; } });
  if (longest === null || !bpm) { return null; }
  return { bars: bars[longest], bpm: bpm, seconds: quarters[longest] * 60 / bpm };
}

/* The chart is a toggle. The button says what the next click will do. */
function setChart(text) {
  var hasChart = Boolean(text);
  $('chart').textContent = hasChart ? text : '';
  $('chord-chart').textContent = hasChart ? 'Hide chart' : 'Chord chart';
}

function showPlanLength(abc) {
  var node = $('plan-length');
  if (!node) { return; }
  var info = planLength(abc);
  if (!info) { node.textContent = ''; return; }
  var cap = parseFloat($('max-duration').value) || 360;
  var text = 'Score is ' + info.bars + ' bars at ' + info.bpm + ' BPM, so about ' + secs(info.seconds);
  if (info.seconds > cap) {
    text += '. Your cap of ' + secs(cap) + ' will cut it short.';
  } else {
    text += '. Cap ' + secs(cap) + ', so it will fit.';
  }
  node.textContent = text;
}

function chordChart(abc) {
  var section = 'song';
  var voice = null;
  var chart = {};
  var order = [];
  abc.split('\n').forEach(function (raw) {
    var line = raw.trim();
    if (line.charAt(0) === '%') { section = line.replace(/^%\s*/, '') || 'section'; return; }
    if (line.indexOf('V:') === 0) { voice = line.slice(2).trim().split(/\s+/)[0]; return; }
    if (!line || voice !== 'Vocal' || /^[XTM LQK]:/.test(line)) { return; }
    var last = null;
    line.split('|').forEach(function (bar) {
      if (!bar.trim()) { return; }
      // Any symbol that starts with a note: Cmaj7, Bm7b5, and slash chords such as C7/Bb.
      var found = bar.match(/"([A-G][#b]?[^"\s]*)"/g);
      // One bar can carry more than one chord, for example "F#"z8"E"z8. Keep every symbol.
      var list = found ? found.map(function (chord) { return chord.replace(/"/g, ''); })
                       : (last === null ? [] : [last]);
      list.forEach(function (chord) {
        if (!chart[section]) { chart[section] = []; order.push(section); }
        chart[section].push(chord);
        last = chord;
      });
    });
  });
  if (!order.length) {
    return State.mode !== 'cover'
      ? 'No chord symbols in this score. The plan may have come out broken: write a new plan, or choose a calmer Plan variety.'
      : 'No chord symbols in this score. Use full mode when you transcribe to get chords.';
  }
  var total = 0;
  var lines = order.map(function (name) {
    var bars = chart[name];
    total += bars.length;
    var folded = [];
    for (var i = 0; i < bars.length; i++) {
      var count = 1;
      while (i + 1 < bars.length && bars[i + 1] === bars[i]) { count += 1; i += 1; }
      folded.push(count > 1 ? bars[i] + ' x' + count : bars[i]);
    }
    var padded = (name + '            ').slice(0, 12);
    return padded + '| ' + folded.join('  ');
  });
  var distinct = {};
  order.forEach(function (name) { chart[name].forEach(function (chord) { distinct[chord] = 1; }); });
  lines.push('');
  lines.push(total + ' bars, ' + Object.keys(distinct).length + ' different chords. ' + (State.mode !== 'cover'
    ? 'A short loop that repeats all song is the model being lazy. Raise Harmony, or edit the symbols.'
    : 'These are the recording\u2019s chords. Edit the symbols, or render in melody mode to let YuE2 choose its own.'));
  return lines.join('\n');
}

/* ---- an instrumental that plans a vocal line ---------------------------- */
/* The instrumental LoRA writes the vocal part as rests. When it writes a melody
   there instead, the render often sings — not always, which is why this asks
   rather than refuses. */
function openSungWarning(take) {
  State.sungTakeId = take.id;
  $('sung-title').textContent = 'This plan may sing';
  // The same sentence is a status line on the card and the opening line here,
  // so it starts a sentence properly in the window.
  var why = take.error || 'The plan has a melody in the vocal part.';
  $('sung-text').textContent = why.charAt(0).toUpperCase() + why.slice(1) + '.';
  $('sung-advice').textContent = 'It may be fine. A new plan is quick, and uses a new seed.';
  $('sung-render').textContent = 'Render anyway';
  $('sung-variety').value = take.variety || 'normal';
  $('sung-modal').classList.remove('hidden');
}

function closeSungWarning() {
  State.sungTakeId = null;
  $('sung-modal').classList.add('hidden');
}

async function renderAnyway() {
  var id = State.sungTakeId;
  closeSungWarning();
  if (!id) { return; }
  selectTake(takeById(id));
  await api('/api/takes/' + id + '/render', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ realaudio: $('realaudio').checked, normalise: normaliseWanted() })
  });
  loadTakes();
}

async function replanInstead() {
  var id = State.sungTakeId;
  var variety = $('sung-variety').value;
  closeSungWarning();
  if (!id) { return; }
  selectTake(takeById(id));
  await api('/api/takes/' + id + '/replan', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ variety: variety })
  });
  awaitNewPlan(id);
  statusLine('Writing a new plan, with a new seed\u2026');
  loadTakes();
}

/* ------------------------------------------------------------------ Logs viewer */
var LogsState = {
  open: false,
  level: 'ALL',
  source: 'ALL',
  search: '',
  timer: null
};

function openLogsModal() {
  LogsState.open = true;
  var panel = $('logs-panel');
  if (panel) {
    panel.style.left = '';
    panel.style.right = '';
    panel.style.top = '';
    panel.style.bottom = '';
    panel.style.width = '';
    panel.classList.remove('hidden');
  }
  if ($('open-logs')) { $('open-logs').classList.add('active'); }
  var consoleEl = $('logs-console');
  if (consoleEl && !consoleEl.children.length) { consoleEl.innerHTML = '<div class="logs-empty">Loading logs\u2026</div>'; }
  fetchLogs();
  if (LogsState.timer) { clearInterval(LogsState.timer); }
  // Live off pauses the panel, so the lines stay put while they are read. A filter or a
  // search still fetches once; ticking Live again catches up at once.
  LogsState.timer = setInterval(function () {
    if ($('logs-tail') && !$('logs-tail').checked) { return; }
    fetchLogs();
  }, 1500);
}

/* The pop-out window beats every two seconds while it is open.  A stale beat means
   it was closed without saying so. */
function logsPoppedOut() {
  try {
    var beat = parseInt(localStorage.getItem('yue2.logs-popout') || '0', 10);
    return Date.now() - beat < 5000;
  } catch (err) { return false; }
}

/* The Logs button and menu item: with the pop-out open, bring it forward. Opening it
   by name finds the window that is already there, without reloading it. */
function showLogs() {
  if (logsPoppedOut()) {
    var popout = window.open('', 'yue2_logs');
    if (popout) {
      // A window of that name that is not the pop-out (a blank one, if it had gone)
      // is sent to it.
      try {
        if (!popout.location.pathname || popout.location.pathname.indexOf('/logs') !== 0) { popout.location = '/logs'; }
      } catch (err) { /* another origin: leave it */ }
      popout.focus();
      return;
    }
  }
  openLogsModal();
}

function closeLogsModal() {
  LogsState.open = false;
  var panel = $('logs-panel');
  if (panel) { panel.classList.add('hidden'); }
  if ($('open-logs')) { $('open-logs').classList.remove('active'); }
  if (LogsState.timer) {
    clearInterval(LogsState.timer);
    LogsState.timer = null;
  }
}

/* The style box is a textarea so its corner can be dragged to show more of a long
   style. At one row it behaves as the text input it replaced: one line that scrolls
   sideways. Taller, it wraps. A style still goes to the model as one line of tags, so
   Enter adds no line and pasted line breaks become spaces. The height is kept per browser. */
var STYLE_HEIGHT_KEY = 'yue2.styleHeight';
function wireStyleBox() {
  var box = $('style');
  if (!box || box.tagName !== 'TEXTAREA') { return; }   // an index.html from before the change
  function fit() {
    var line = parseFloat(window.getComputedStyle(box).lineHeight) || 20;
    // Hidden (another mode's form) it measures 0 and is left as it is.
    if (box.clientHeight) { box.wrap = box.clientHeight < line * 1.8 + 20 ? 'off' : 'soft'; }
  }
  function keep() {
    fit();
    if (!box.offsetHeight) { return; }
    try { localStorage.setItem(STYLE_HEIGHT_KEY, String(box.offsetHeight)); } catch (err) { /* not kept */ }
  }
  try {
    var kept = parseInt(localStorage.getItem(STYLE_HEIGHT_KEY), 10);
    if (kept > 0) { box.style.height = kept + 'px'; }
  } catch (err) { /* storage unavailable: one row */ }
  fit();
  box.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') { event.preventDefault(); }
  });
  box.addEventListener('input', function () {
    if (box.value.indexOf('\n') === -1) { return; }
    var at = box.selectionStart;
    var before = box.value.length;
    box.value = box.value.replace(/[ \t]*[\r\n]+[ \t]*/g, ' ');
    box.selectionStart = box.selectionEnd = Math.max(0, at - (before - box.value.length));
  });
  // A drag of the corner ends with the button let go over the box.
  box.addEventListener('mouseup', keep);
  if (window.ResizeObserver) {
    var timer = null;
    new ResizeObserver(function () { clearTimeout(timer); timer = setTimeout(keep, 300); }).observe(box);
  }
}

async function fetchLogs() {
  if (!LogsState.open) { return; }
  try {
    var url = '/api/logs?limit=300';
    if (LogsState.level && LogsState.level !== 'ALL') {
      url += '&level=' + encodeURIComponent(LogsState.level);
    }
    if (LogsState.source && LogsState.source !== 'ALL') {
      url += '&source=' + encodeURIComponent(LogsState.source);
    }
    if (LogsState.search) {
      url += '&search=' + encodeURIComponent(LogsState.search);
    }
    var res = await fetch(url);
    if (!res.ok) { return; }
    var data = await res.json();
    renderLogs(data.logs || []);
  } catch (err) { /* quiet on fetch error */ }
}

function renderLogs(logs) {
  var consoleEl = $('logs-console');
  if (!consoleEl) { return; }
  if (!logs || !logs.length) {
    consoleEl.innerHTML = '<div class="logs-empty">No logs matching filter.</div>';
    return;
  }
  var html = logs.map(function (entry) {
    var lvl = esc(entry.level || 'INFO');
    var badgeClass = lvl === 'WARNING' ? 'WARN' : lvl;
    var src = esc((entry.source || 'app').toLowerCase());
    return '<div class="log-row">' +
      '<span class="log-time">' + esc(entry.timestamp || '') + '</span> ' +
      '<span class="log-source ' + src + '">' + src + '</span> ' +
      '<span class="log-badge ' + badgeClass + '">' + badgeClass + '</span> ' +
      '<span class="log-logger">[' + esc(entry.logger || '') + ']</span> ' +
      '<span class="log-msg ' + badgeClass + '">' + esc(entry.message || '') + '</span>' +
      '</div>';
  }).join('');
  consoleEl.innerHTML = html;
  if ($('logs-tail') && $('logs-tail').checked) {
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }
}

function wireLogs() {
  var openBtn = $('open-logs');
  if (openBtn) { openBtn.addEventListener('click', showLogs); }
  var menuBtn = $('menu-logs');
  if (menuBtn) {
    menuBtn.addEventListener('click', function () {
      var menu = $('brand-menu');
      if (menu) { menu.classList.add('hidden'); }
      showLogs();
    });
  }
  // The guide opens in its own tab, so this page stays, and so would the menu.
  var guideLink = $('menu-guide');
  if (guideLink) { guideLink.addEventListener('click', closeBrandMenu); }
  var closeBtn = $('logs-close');
  if (closeBtn) { closeBtn.addEventListener('click', closeLogsModal); }
  var clearBtn = $('logs-clear');
  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      var consoleEl = $('logs-console');
      if (consoleEl) { consoleEl.innerHTML = '<div class="logs-empty">Cleared.</div>'; }
    });
  }
  var popoutBtn = $('logs-popout');
  if (popoutBtn) {
    popoutBtn.addEventListener('click', function () {
      window.open('/logs', 'yue2_logs', 'width=1050,height=750,menubar=no,toolbar=no');
      closeLogsModal();
    });
  }
  Array.prototype.forEach.call(document.querySelectorAll('.logs-filter-btn'), function (btn) {
    btn.addEventListener('click', function () {
      Array.prototype.forEach.call(document.querySelectorAll('.logs-filter-btn'), function (b) {
        b.classList.remove('active');
      });
      btn.classList.add('active');
      LogsState.level = btn.dataset.level || 'ALL';
      fetchLogs();
    });
  });
  Array.prototype.forEach.call(document.querySelectorAll('.logs-source-btn'), function (btn) {
    btn.addEventListener('click', function () {
      Array.prototype.forEach.call(document.querySelectorAll('.logs-source-btn'), function (b) {
        b.classList.remove('active');
      });
      btn.classList.add('active');
      LogsState.source = btn.dataset.source || 'ALL';
      fetchLogs();
    });
  });
  if ($('logs-tail')) {
    $('logs-tail').addEventListener('change', function () { if ($('logs-tail').checked) { fetchLogs(); } });
  }
  var searchInput = $('logs-search');
  if (searchInput) {
    var searchTimer = null;
    searchInput.addEventListener('input', function () {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(function () {
        LogsState.search = (searchInput.value || '').trim();
        fetchLogs();
      }, 250);
    });
  }
  // Dragging support for moving the logs window anywhere on screen
  var head = $('logs-panel') ? $('logs-panel').querySelector('.logs-head') : null;
  var box = $('logs-panel');
  if (head && box) {
    var isDragging = false, startX = 0, startY = 0, startLeft = 0, startTop = 0;
    head.addEventListener('mousedown', function (e) {
      if (e.target.closest('button, input, a, select, label')) { return; }
      isDragging = true;
      var rect = box.getBoundingClientRect();
      startX = e.clientX;
      startY = e.clientY;
      startLeft = rect.left;
      startTop = rect.top;
      box.style.position = 'fixed';
      box.style.width = rect.width + 'px';
      box.style.left = startLeft + 'px';
      box.style.top = startTop + 'px';
      box.style.right = 'auto';
      box.style.bottom = 'auto';
      box.style.margin = '0';
      document.body.style.userSelect = 'none';
    });
    document.addEventListener('mousemove', function (e) {
      if (!isDragging) { return; }
      var dx = e.clientX - startX;
      var dy = e.clientY - startY;
      var maxLeft = window.innerWidth - 100;
      var maxTop = window.innerHeight - 80;
      box.style.left = Math.max(10, Math.min(maxLeft, startLeft + dx)) + 'px';
      box.style.top = Math.max(10, Math.min(maxTop, startTop + dy)) + 'px';
    });
    document.addEventListener('mouseup', function () {
      if (isDragging) {
        isDragging = false;
        document.body.style.userSelect = '';
      }
    });
  }
}

/* ------------------------------------------------------------------ wiring */
function wire() {
  wireLogs();
  if ($('engine-pill')) {
    $('engine-pill').addEventListener('click', function () {
      if (State.training && State.training.identity_id) {
        openIdentities();
        showIdentity(State.training.identity_id);
      }
    });
  }
  paintPresets();
  if ($('lora-presets')) {
    $('lora-presets').addEventListener('click', function (event) {
      var button = event.target.closest('[data-lora-style]');
      if (!button || !button.dataset.loraStyle) { return; }
      applyLoraStyle(button.dataset.loraStyle, button.dataset.trigger);
    });
  }
  $('presets').addEventListener('click', function (event) {
    var button = event.target.closest('[data-preset]');
    if (button) {
      var item = loraChosen();
      if (item && item.trigger) {
        $('style').value = item.trigger + ', ' + button.dataset.preset;
        State.loraTrigger = item.trigger;
      } else {
        $('style').value = button.dataset.preset;
        State.loraTrigger = null;
      }
      $('style').dataset.touched = '1';
      paintVocals();
      paintStyleLoraNote();
      saveForm();
    }
  });
  if ($('style-picker-btn')) {
    $('style-picker-btn').addEventListener('click', toggleStylePicker);
  }
  if ($('style-picker-menu')) {
    $('style-picker-menu').addEventListener('click', function (event) {
      var item = event.target.closest('[data-style-name]');
      if (item) {
        applyCannedStyle(item.dataset.styleName);
      }
    });
    $('style-picker-menu').addEventListener('input', function (event) {
      if (event.target.id === 'style-picker-search') {
        paintStylePickerMenu(event.target.value);
      }
    });
    $('style-picker-menu').addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        var first = $('style-picker-menu').querySelector('.style-picker-item');
        if (first && first.dataset.styleName) {
          event.preventDefault();
          applyCannedStyle(first.dataset.styleName);
        }
      }
    });
  }
  $('vocal-sex').addEventListener('click', function (event) {
    var button = event.target.closest('[data-sex]');
    if (button) { setVocalSex(button.dataset.sex); }
  });
  $('vocal-tone').addEventListener('click', function (event) {
    var button = event.target.closest('[data-tone]');
    if (button) { toggleVocalTone(button.dataset.tone); }
  });
  $('style').addEventListener('input', paintVocals);
  $('harmony').addEventListener('input', paintHarmony);

  $('browse').addEventListener('click', function () { $('file').click(); });
  $('file').addEventListener('change', function (event) { uploadFile(event.target.files[0]); });
  var drop = $('drop');
  drop.addEventListener('dragover', function (event) { event.preventDefault(); drop.classList.add('over'); });
  drop.addEventListener('dragleave', function () { drop.classList.remove('over'); });
  drop.addEventListener('drop', function (event) {
    event.preventDefault();
    drop.classList.remove('over');
    if (event.dataTransfer.files.length) { uploadFile(event.dataTransfer.files[0]); }
  });

  $('source-select').addEventListener('change', function () {
    var boxTake = scoreTakeId() ? takeById(scoreTakeId()) : null;
    var recordingScore = Selection.boxKind === 'source' || Boolean(boxTake && boxTake.source_id);
    // Choosing a recording the box's take did not come from lets go of that take:
    // its words and its score are not this recording's, and covering one with the
    // other's score is how a render came out as a different song.
    if (scoreTakeId() && !boxShowsSource($('source-select').value)) { setSelection({}); }
    // An instrumental set to no recording: a recording's score in the box goes too.
    if (State.mode === 'inst' && !$('source-select').value && recordingScore) { clearRecordingScore(); }
    paintSource();
  });
  $('transcribe').addEventListener('click', doTranscribe);
  $('create-cover').addEventListener('click', doRender);
  wireEditor();
  $('create-song').addEventListener('click', doPlan);
  $('render-take').addEventListener('click', doRenderTake);
  if ($('make-instrumental')) { $('make-instrumental').addEventListener('click', doMakeInstrumental); }
  $('lyrics').addEventListener('input', setScoreActions);
  if ($('keep-tune')) {
    $('keep-tune').addEventListener('change', function () {
      setScoreActions();
      if (typeof editorOpen === 'function' && editorOpen()) { paintEditor(); }
    });
  }
  if ($('sing-new-words')) { $('sing-new-words').addEventListener('click', doSingNewWords); }
  $('sung-cancel').addEventListener('click', closeSungWarning);
  $('sung-render').addEventListener('click', renderAnyway);
  $('sung-replan').addEventListener('click', replanInstead);
  $('sung-modal').addEventListener('click', function (event) {
    if (backdropClick(event, $('sung-modal'))) { closeSungWarning(); }
  });
  $('reroll').addEventListener('click', doReroll);
  document.querySelector('.modes').addEventListener('click', function (event) {
    var button = event.target.closest('[data-mode]');
    if (button) { setMode(button.dataset.mode); saveForm(); }
  });

  $('save-score').addEventListener('click', function () { saveScore(false); });
  if ($('score-save')) {
    $('score-save').addEventListener('click', function () { saveScore(false); });
  }

  $('do-replace').addEventListener('click', function () {
    var find = $('find-chord').value.trim();
    var replace = $('replace-chord').value.trim();
    if (!find) { statusLine('Type the chord to find first.', 'bad'); return; }
    var text = $('abc').value;
    var quoted = '"' + find + '"';
    var count = text.split(quoted).length - 1;
    if (!count) { statusLine('This score has no chord "' + find + '".', 'bad'); return; }
    $('abc').value = text.split(quoted).join('"' + replace + '"');
    setChart(chordChart($('abc').value));
    syncEditor();
    statusLine('Replaced ' + count + ' with "' + replace + '". Now save the score, then render.', 'good');
  });

  $('chord-chart').addEventListener('click', function () {
    if ($('chart').textContent) { setChart(''); return; }
    setChart(chordChart($('abc').value));
    showPlanLength($('abc').value);
  });

  $('dice').addEventListener('click', function () {
    $('seed').value = Math.floor(Math.random() * 4294967295);
    $('seed-fixed').checked = true;
  });

  $('width-toggle').addEventListener('click', function () {
    applyWidth(State.width === 'wide' ? 'fit' : 'wide');
  });
  $('layout-toggle').addEventListener('click', function () {
    applyLayout(State.layout === 'comfy' ? 'compact' : 'comfy');
  });

  document.querySelector('.filters').addEventListener('click', function (event) {
    var kindChip = event.target.closest('[data-takekind]');
    if (kindChip) {
      var now = (State.kinds || []).slice();
      var at = now.indexOf(kindChip.dataset.takekind);
      if (at >= 0) { now.splice(at, 1); } else { now.push(kindChip.dataset.takekind); }
      applyKinds(now);
      State.takesRaw = '';
      clearPicked();
      loadTakes();
      return;
    }
    var button = event.target.closest('[data-filter]');
    if (!button) { return; }
    applyFilter(button.dataset.filter);
    State.takesRaw = '';
    clearPicked();
    loadTakes();
  });
  if ($('select-all')) {
    $('select-all').addEventListener('click', toggleSelectAll);
  }
  wireSearch();
  $('takes-more').addEventListener('click', function () {
    State.takeLimit += 300;
    loadTakes();
  });

  $('takes').addEventListener('change', function (event) {
    var box = event.target.closest('input[data-act="pick"]');
    if (!box) { return; }
    var id = box.dataset.id;
    if (box.checked) { State.picked[id] = true; } else { delete State.picked[id]; }
    // Mark the card itself rather than repainting the list, so the box keeps focus
    // and the page does not jump.
    var card = box.closest('.take');
    if (card) { card.classList.toggle('picked', box.checked); }
    paintBulk();
  });
  $('bulk-delete').addEventListener('click', function () { bulkDelete(); });

  var lastTitleClick = { time: 0, id: null };
  $('takes').addEventListener('click', function (event) {
    var titleEl = event.target.closest('.take-title');
    if (titleEl && !titleEl.querySelector('input')) {
      var id = titleEl.dataset.id || (titleEl.closest('.take') && titleEl.closest('.take').dataset.id);
      var now = Date.now();
      if (id && (event.detail >= 2 || (lastTitleClick.id === id && now - lastTitleClick.time < 500))) {
        event.preventDefault();
        event.stopPropagation();
        lastTitleClick = { time: 0, id: null };
        startRenameTake(titleEl, id);
        return;
      }
      lastTitleClick = { time: now, id: id };
    }

    // Clicking anywhere on the card, except on a control inside it, makes that
    // take the one the left column describes.
    if (event.target.closest('button, a, input, select, textarea, label, .take-title-input')) { return; }
    var card = event.target.closest('.take');
    if (card && card.dataset.id) { selectTake(takeById(card.dataset.id)); }
  });

  $('takes').addEventListener('dblclick', function (event) {
    var titleEl = event.target.closest('.take-title');
    if (!titleEl) {
      // Anywhere else on a card, away from its controls, opens it in the editor, on the
      // page its sheet's main button would: the plan to review, or the song.
      if (event.target.closest('button, a, input, select, textarea, label, .take-title-input')) { return; }
      var card = event.target.closest('.take');
      var take = card && takeById(card.dataset.id);
      if (!take || typeof openEditor !== 'function' || !$('editor-modal')) { return; }
      if (window.getSelection) { window.getSelection().removeAllRanges(); }   // the word the double-click picked
      selectTake(take);
      openEditor(take.status === 'planned' ? 'score' : 'song');
      return;
    }
    var id = titleEl.dataset.id || (titleEl.closest('.take') && titleEl.closest('.take').dataset.id);
    if (id) {
      event.preventDefault();
      event.stopPropagation();
      startRenameTake(titleEl, id);
    }
  });

  $('takes').addEventListener('click', function (event) {
    var button = event.target.closest('button[data-act]');
    if (!button) { return; }
    takeAction(button).catch(function (err) {
      statusLine('Could not ' + button.textContent.trim().toLowerCase() + ': ' + err.message, 'bad');
      loadTakes();
    });
  });
  $('source-delete').addEventListener('click', deleteSource);
  if ($('source-picker-btn')) {
    $('source-picker-btn').addEventListener('click', function (event) {
      event.stopPropagation();
      toggleSourcePicker();
    });
  }
  if ($('source-picker-menu')) {
    $('source-picker-menu').addEventListener('input', function (event) {
      if (event.target.id !== 'source-corpus-filter') { return; }
      State.corpusFilter = event.target.value;
      paintSourcePickerMenu();
    });
    $('source-picker-menu').addEventListener('click', function (event) {
      // Folding and filtering redraw the menu, which detaches what was clicked; left
      // to bubble, the outside-click check would no longer find it and close the menu.
      if (event.target.closest('#source-corpus-filter')) { event.stopPropagation(); return; }
      var fold = event.target.closest('[data-cgroup]');
      if (fold) {
        event.stopPropagation();
        var open = sourceCorporaOpen();
        var at = open.indexOf(fold.dataset.cgroup);
        if (at >= 0) { open.splice(at, 1); } else { open.push(fold.dataset.cgroup); }
        saveSourceCorporaOpen(open);
        paintSourcePickerMenu();
        return;
      }
      var fromCorpus = event.target.closest('[data-corpus-song]');
      if (fromCorpus) {
        event.stopPropagation();
        useCorpusSong(fromCorpus.dataset.corpusSong);
        return;
      }
      var delBtn = event.target.closest('[data-del]');
      if (delBtn) {
        event.stopPropagation();
        deleteSourceById(delBtn.dataset.del);
        return;
      }
      var item = event.target.closest('[data-id]');
      if (item) {
        var id = item.dataset.id;
        $('source-select').value = id;
        closeSourcePicker();
        $('source-select').dispatchEvent(new Event('change'));
        fillCorpusSongStyle(null, true);
        takeRecordingWords(id);
      }
    });
  }
  document.addEventListener('click', function (event) {
    if (!event.target.closest('#source-picker')) {
      closeSourcePicker();
    }
    if (!event.target.closest('#lora-picker')) { closeLoraPicker(); }
    if (!event.target.closest('#style-picker')) { closeStylePicker(); }
  });
  $('lora-picker-btn').addEventListener('click', function () {
    if ($('lora-picker-menu').classList.contains('hidden')) { openLoraPicker(); } else { closeLoraPicker(); }
  });
  $('lora-picker-menu').addEventListener('click', function (event) {
    // Folding redraws the menu, which detaches the heading clicked; left to bubble, the
    // outside-click check above would no longer find it inside and close the menu.
    event.stopPropagation();
    var group = event.target.closest('.lora-group, .lora-steps-toggle');
    if (group) {
      var name = group.dataset.group || 'steps:' + group.dataset.steps;
      var open = loraOpenGroups();
      var at = open.indexOf(name);
      if (at >= 0) { open.splice(at, 1); } else { open.push(name); }
      saveLoraOpenGroups(open);
      paintLoraPicker();
      return;
    }
    var entry = event.target.closest('.lora-item');
    if (entry) {
      closeLoraPicker();
      $('style-lora').value = entry.dataset.value;
      $('style-lora').dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
  $('start-fresh').addEventListener('click', startFresh);
  wireCorporaBadge(corporaBadge());
  pollCorpora();
  var openBtn = $('identities-open') || $('personas-open');
  if (openBtn) { openBtn.addEventListener('click', openIdentities); }
  var closeBtn = $('identities-close') || $('personas-close');
  if (closeBtn) { closeBtn.addEventListener('click', closeIdentities); }
  var backBtn = $('identities-back') || $('personas-back');
  if (backBtn) { backBtn.addEventListener('click', showIdentityList); }
  var bodyEl = $('identities-body') || $('personas-body');
  if (bodyEl) {
    bodyEl.addEventListener('click', function (event) {
      identityClick(event).catch(function (err) { statusLine(err.message, 'bad'); });
    });
    bodyEl.addEventListener('change', function (event) {
      identityChange(event).catch(function (err) { statusLine(err.message, 'bad'); });
    });
    bodyEl.addEventListener('input', function (event) {
      if (event.target.dataset.lyrics) { event.target.dataset.edited = '1'; }
    });
  }
  wireStructure();
  wireSongPlan();
  $('interpretation').addEventListener('change', paintInterpretation);
  $('lyrics-write').addEventListener('click', openWrite);
  $('audition').addEventListener('click', function () { playRecording(); });
  $('source-lyrics').addEventListener('click', function () {
    hearLyrics().catch(function (err) { statusLine('Could not start: ' + err.message, 'bad'); });
  });
  $('lyrics-hear-stop').addEventListener('click', function () {
    var source = currentSource();
    if (!source) { return; }
    api('/api/sources/' + source.id + '/lyrics', { method: 'DELETE' })
      .then(stopHearPoll)
      .catch(function () { stopHearPoll(); });
  });
  $('write-close').addEventListener('click', closeWrite);
  $('write-go').addEventListener('click', doWrite);
  if ($('write-feel')) {
    $('write-feel').addEventListener('change', function () {
      try { localStorage.setItem(FEEL_KEY, $('write-feel').value); } catch (err) { /* private mode */ }
      paintWriteFeel();
    });
  }
  $('write-stop').addEventListener('click', stopWrite);
  if ($('lyrics-write-stop-btn')) { $('lyrics-write-stop-btn').addEventListener('click', stopWrite); }
  $('write-modal').addEventListener('click', function (event) { if (backdropClick(event, $('write-modal'))) { closeWrite(); } });
  $('lora-steps').addEventListener('click', openLoraSteps);
  $('steps-close').addEventListener('click', closeLoraSteps);
  $('steps-go').addEventListener('click', runLoraSteps);
  $('steps-list').addEventListener('change', paintStepsEstimate);
  $('steps-modal').addEventListener('click', function (event) {
    if (backdropClick(event, $('steps-modal'))) { closeLoraSteps(); }
  });
  // Guarded: the page is read once when the app starts and the script on every load,
  // so a new script can meet an old page until the app restarts.  Missing parts of the
  // page must not stop the rest of it being wired.
  if ($('train-modal')) {
    $('train-close').addEventListener('click', closeTrain);
    $('train-go').addEventListener('click', runTrain);
    $('train-modal').addEventListener('click', function (event) {
      if (backdropClick(event, $('train-modal'))) { closeTrain(); }
    });
  }
  $('variations-close').addEventListener('click', closeVariations);
  $('variations-go').addEventListener('click', doVariations);
  $('variations-list').addEventListener('change', paintVariationsEstimate);
  $('variations-modal').addEventListener('click', function (event) {
    if (backdropClick(event, $('variations-modal'))) { closeVariations(); }
  });
  if ($('source-tracks')) {
    $('source-tracks').addEventListener('click', openTracksModal);
  }
  if ($('tracks-close')) {
    $('tracks-close').addEventListener('click', closeTracksModal);
  }
  if ($('tracks-modal')) {
    $('tracks-modal').addEventListener('click', function (event) {
      if (backdropClick(event, $('tracks-modal'))) { closeTracksModal(); }
    });
  }
  wireCompare();
  if ($('tries-modal')) {
    $('tries-close').addEventListener('click', closeTries);
    $('tries-go').addEventListener('click', doTries);
    $('tries-modal').addEventListener('input', paintTries);
    $('tries-modal').addEventListener('change', paintTries);
    $('tries-modal').addEventListener('click', function (event) {
      if (backdropClick(event, $('tries-modal'))) { closeTries(); }
    });
  }
  $('space').addEventListener('change', function () { showSpace($('space').value); });
  $('space-new').addEventListener('click', newSpace);
  $('space-rename').addEventListener('click', renameSpace);
  $('space-delete').addEventListener('click', deleteSpace);
  $('move-close').addEventListener('click', closeMoveModal);
  $('move-modal').addEventListener('click', function (event) {
    if (backdropClick(event, $('move-modal'))) { closeMoveModal(); }
  });
  $('move-list').addEventListener('click', function (event) {
    var button = event.target.closest('button[data-space]');
    if (!button) { return; }
    moveTake(button.dataset.space).catch(function (err) { $('move-status').textContent = err.message; $('move-status').className = 'status bad'; });
  });
  async function createAndMove() {
    var name = $('move-name').value.trim();
    if (!name) { $('move-name').focus(); return; }
    try {
      var space = await api('/api/spaces', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: name })
      });
      State.spaces.push(space);
      await moveTake(space.id);
    } catch (err) {
      $('move-status').textContent = err.message;
      $('move-status').className = 'status bad';
    }
  }
  $('move-create').addEventListener('click', createAndMove);
  $('move-name').addEventListener('keydown', function (event) { if (event.key === 'Enter') { createAndMove(); } });
  $('draft-restore').addEventListener('click', restoreDraft);
  $('draft-dismiss').addEventListener('click', dismissDraft);

  async function takeAction(button) {
    var id = button.dataset.id;
    var act = button.dataset.act;
    if (act === 'cancel') {
      await api('/api/takes/' + id + '/cancel', { method: 'POST' });
      loadTakes();
    }
    if (act === 'play') {
      selectTake(takeById(id));
      togglePlay(id);
    }
    if (act === 'star') {
      var take = State.takes.filter(function (t) { return t.id === id; })[0];
      await api('/api/takes/' + id + '/favourite?value=' + (take && take.favourite ? 'false' : 'true'), { method: 'POST' });
      loadTakes();
    }
    if (act === 'del') {
      if (await confirmModal({
        title: 'Delete take',
        message: 'Delete this take and its audio?',
        confirmText: 'Delete',
        danger: true
      })) {
        await api('/api/takes/' + id, { method: 'DELETE' });
        delete State.picked[id];
        loadTakes();
      }
    }
    if (act === 'open') {
      var opened = takeById(id);
      if (!opened) { return; }
      selectTake(opened);
      statusLine('Showing the score for ' + opened.title + '.', 'good');
      if ($('editor-modal')) { openEditor('score'); } else { $('score-box').scrollIntoView({ behavior: 'smooth', block: 'center' }); }
    }
    if (act === 'save') {
      var saveTake = takeById(id);
      if (saveTake) {
        selectTake(saveTake);
        openSaveModal(saveTake);
      }
    }
    if (act === 'stems') {
      var stemTake = takeById(id);
      if (stemTake) {
        selectTake(stemTake);
        openStemsModal({ kind: 'take', id: stemTake.id, title: stemTake.title });
      }
    }
    if (act === 'stem-play') {
      playStem(button.dataset.set, button.dataset.file);
    }
    if (act === 'stem-del') {
      await api('/api/stem-sets/' + button.dataset.set, { method: 'DELETE' });
      loadTakes();
    }
    if (act === 'dismiss-note') {
      var noted = takeById(id);
      if (noted) { noted.note_dismissed = 1; paintTakes(); }
      try {
        await api('/api/takes/' + id + '/note/dismiss', { method: 'POST' });
      } catch (err) {
        statusLine('Could not dismiss the note: ' + err.message, 'bad');
      }
      loadTakes();
      return;
    }
    if (act === 'dismiss-weak') {
      var heard = takeById(id);
      if (heard) { heard.weak_dismissed = 1; paintTakes(); }
      try {
        await api('/api/takes/' + id + '/weak/dismiss', { method: 'POST' });
      } catch (err) {
        statusLine('Could not dismiss the note: ' + err.message, 'bad');
      }
      loadTakes();
      return;
    }
    if (act === 'normalise' || act === 'unnormalise') {
      var undo = act === 'unnormalise';
      if (State.normalising[id]) { return; }
      State.normalising[id] = true;
      // The player streams the take a piece at a time and keeps it open, and Windows
      // will not replace a file that is open.  Let go of it first.
      if (State.loadedId === id) {
        var player = $('audio');
        player.pause();
        player.removeAttribute('src');
        player.load();
        State.loadedId = null;
      }
      paintTakes();
      statusLine(undo ? 'Undoing the normalise\u2026' : 'Normalising\u2026');
      try {
        await api('/api/takes/' + id + '/normalise' + (undo ? '?undo=true' : ''), { method: 'POST' });
        // The same take loaded in the player would carry on with the old file.
        if (State.loadedId === id) { State.loadedId = null; }
        statusLine(undo ? 'Back to the level it was rendered at.' : 'Normalised.', 'good');
      } catch (err) {
        statusLine((undo ? 'Could not undo the normalise: ' : 'Could not normalise the take: ') + err.message, 'bad');
      }
      delete State.normalising[id];
      await loadTakes();
      paintTakes();   // an unchanged list is not redrawn, and the card must drop Normalising
      return;
    }
    if (act === 'render') {
      var planned = takeById(id);
      // An instrumental whose plan holds a vocal line: say so before the render
      // is paid for, and let the choice be made with the facts in hand.
      if (planned && planned.kind === 'instrumental' && planned.status === 'planned' && planned.error) {
        openSungWarning(planned);
        return;
      }
      selectTake(takeById(id));
      var payload = {
        interpretation: $('interpretation').value,
        realaudio: $('realaudio').checked, normalise: normaliseWanted(),
        style_lora: $('style-lora') ? $('style-lora').value : '',
        style_lora_model: $('style-lora-model') && !$('style-lora-model').disabled ? parseFloat($('style-lora-model').value) : 0,
        style_lora_clip: $('style-lora-clip') && !$('style-lora-clip').disabled ? parseFloat($('style-lora-clip').value) : 0
      };
      if ($('seed-fixed').checked && !isNaN(parseInt($('seed').value, 10))) {
        payload.seed = parseInt($('seed').value, 10);
      }
      await api('/api/takes/' + id + '/render', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      loadTakes();
    }
    if (act === 'clear') {
      try {
        var cleared = await api('/api/takes/' + id + '/clear', { method: 'POST' });
        statusLine('Cleared. The take is back to ' + (cleared.status === 'done' ? 'its audio.' : 'its score.'), 'good');
      } catch (err) {
        statusLine(err.message, 'bad');
      }
      loadTakes();
    }
    if (act === 'details' || act === 'mastering') {
      if (act === 'mastering') {
        var targetTake = takeById(id);
        if (targetTake && window.Rack) {
          var audio = $('audio');
          if (audio && !audio.paused && !audio.ended && State.playing !== targetTake.id) {
            audio.pause();
            State.playing = null;
            paintTakes();
            paintTransport();
          }
          selectTake(targetTake);
          window.Rack.openForTake(targetTake);
          return;
        }
      }
      openDetails(takeById(id));
      return;
    }
    if (act === 'replan') {
      selectTake(takeById(id));
      await api('/api/takes/' + id + '/replan', { method: 'POST' });
      awaitNewPlan(id);
      statusLine('Writing a new plan for the same words\u2026');
      loadTakes();
    }
    if (act === 'revoice') {
      var voiced = takeById(id);
      await api('/api/takes/' + id + '/revoice', { method: 'POST' });
      statusLine('Singing ' + (voiced ? voiced.title : 'this take') + ' again with a new seed\u2026', 'good');
      loadTakes();
    }
    if (act === 'variations') {
      var source = takeById(id);
      if (source) { openVariations(source); }
    }
    if (act === 'tries') {
      var origin = takeById(id);
      if (origin) { openTries(origin); }
    }
    if (act === 'move') {
      var moving = takeById(id);
      if (moving) { openMoveModal(moving); }
    }
    if (act === 'rename') {
      var targetTake = takeById(id);
      if (!targetTake) { return; }
      var newTitle = await confirmModal({
        title: 'Rename take',
        message: 'Rename take:',
        input: true,
        defaultValue: targetTake.title,
        confirmText: 'Rename'
      });
      if (newTitle && newTitle.trim() && newTitle.trim() !== targetTake.title) {
        try {
          var updated = await api('/api/takes/' + id + '/rename', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle.trim() })
          });
          targetTake.title = updated.title;
          if (selectedTakeId() === id) { $('title').value = updated.title; }
          paintTakes();
        } catch (err) {
          statusLine('Could not rename take: ' + err.message, 'bad');
        }
      }
    }
    if (act === 'again') {
      var previous = takeById(id);
      if (!previous) { return; }
      selectTake(previous);
      if (previous.seed != null) {
        $('seed').value = previous.seed;
      }
      $('seed-fixed').checked = true;
      var adv = $('seed') ? $('seed').closest('details') : null;
      if (adv) { adv.open = true; }
      $('seed').dispatchEvent(new Event('input', { bubbles: true }));
      $('seed').dispatchEvent(new Event('change', { bubbles: true }));
      $('seed-fixed').dispatchEvent(new Event('change', { bubbles: true }));
      saveForm();
      statusLine('Loaded settings and seed ' + previous.seed + ' (fixed) from ' + (previous.title || 'take') + '.', 'good');
      if ($('editor-modal')) {
        openEditor('sound');
      } else {
        var createButton = $({ song: 'create-song', instrumental: 'create-inst' }[previous.kind] || 'create-cover');
        if (createButton) { createButton.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
      }
    }
  }

  $('job-queue').addEventListener('click', function (event) {
    var button = event.target.closest('.q-cancel');
    if (!button) { return; }
    button.disabled = true;
    api('/api/queue/' + encodeURIComponent(button.dataset.kind) + '/' + encodeURIComponent(button.dataset.id) + '/cancel', { method: 'POST' })
      .then(function () { loadTakes(); pollState(); })
      .catch(function (err) {
        button.disabled = false;
        statusLine('Could not cancel the job: ' + err.message, 'bad');
      });
  });

  $('job-stop').addEventListener('click', function () {
    api('/api/jobs/current/cancel', { method: 'POST' }).then(loadTakes).catch(function (err) {
      statusLine('Could not stop the job: ' + err.message, 'bad');
    });
  });

  wireWave();
  wireTransport();
  if (window.Rack) { window.Rack.init(); }
  paintVocals();
  loadVocalIdentities();

  wireStyleBox();
  FORM_FIELDS.forEach(function (id) {
    $(id).addEventListener('input', function () {
      if (id === 'style') { $('style').dataset.touched = '1'; }
      saveForm();
    });
    $(id).addEventListener('change', saveForm);
  });
  $('auto-render').addEventListener('change', saveForm);
  $('seed-fixed').addEventListener('change', saveForm);
  $('realaudio').addEventListener('change', saveForm);
  if ($('normalise')) { $('normalise').addEventListener('change', saveForm); }
  $('style-lora-field').addEventListener('click', function (event) {
    if (event.target.closest('#lora-reload')) { reloadLoras(); }
    if (event.target.closest('#lora-use-saved')) {
      wakeStyleLoraStrengths();
      paintStyleLoraStrengths();
      saveForm();
    }
  });
  $('style-lora').addEventListener('change', function () {
    var item = loraChosen();
    applyLoraTrigger(item && item.trigger);
    fillCorpusSongStyle();
    wakeStyleLoraStrengths();
    paintStyleLoraStrengths();
    saveForm();
  });
  ['style-lora-model', 'style-lora-clip'].forEach(function (id) {
    $(id).addEventListener('input', function () {
      paintStrengthValue(id, !$(id).disabled, true);
      saveForm();
      paintStyleLoraNote();
    });
    // The number beside the slider, so an exact strength can be typed rather than
    // hunted for with the mouse.
    var box = $(id + '-value');
    if (box) {
      box.addEventListener('change', function () { setStrength(id, box.value); });
      box.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') { setStrength(id, box.value); box.blur(); }
      });
    }
  });
  $('lyrics').addEventListener('input', function () {
    State.formEdited = true;
    refreshTitleHint();
  });
  ['title', 'style'].forEach(function (id) {
    $(id).addEventListener('input', function () { State.formEdited = true; });
  });
  $('abc').addEventListener('input', function () {
    if (State.mode === 'inst') { paintInstSource(); }
    if (State.mode === 'cover') { paintStructure(); }
    saveWorkingScore();
    pushScoreHistory($('abc').value);
    paintScoreDirty();
  });

  $('brand').addEventListener('click', function (event) {
    event.stopPropagation();
    toggleBrandMenu();
  });
  var menuIdentities = $('menu-identities');
  if (menuIdentities) {
    menuIdentities.addEventListener('click', function (event) {
      event.stopPropagation();
      openIdentities();
    });
  }
  wireAbout();
  wireDetails();
  var menuSettings = $('menu-settings');
  if (menuSettings) {
    menuSettings.addEventListener('click', function (event) {
      event.stopPropagation();
      openSettings();
    });
  }
  document.addEventListener('click', function (event) {
    if (!event.target.closest('.brand-wrap')) {
      closeBrandMenu();
    }
  });
  $('settings-close').addEventListener('click', closeSettings);
  wireStorage();
  $('settings-modal').addEventListener('click', function (event) {
    if (backdropClick(event, $('settings-modal'))) { closeSettings(); }
  });
  $('settings-list').addEventListener('change', function (event) {
    if (event.target && event.target.id === 'select-llm-model') {
      var val = event.target.value;
      if (val) {
        var inp = $('input-llm-model');
        if (inp) {
          inp.value = val;
          saveSetting(inp);
        }
      }
      return;
    }
    if (event.target.dataset && event.target.dataset.key) { saveSetting(event.target); }
  });
  $('settings-list').addEventListener('click', async function (event) {
    if (event.target && event.target.id === 'btn-fetch-models') {
      event.preventDefault();
      fetchLLMModels(false);
      return;
    }
    if (event.target && event.target.dataset && event.target.dataset.remove) {
      event.preventDefault();
      if (!await confirmModal({
        title: 'Remove API key',
        message: 'Remove the saved key?',
        confirmText: 'Remove',
        danger: true
      })) { return; }
      var removeKey = event.target.dataset.remove;
      api('/api/settings', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: removeKey, value: '' })
      }).then(function (data) {
        adoptSettings(data.settings);
        paintSettings();
        paintSettingRequirements();
      }).catch(function (err) {
        var mark = $('settings-list').querySelector('[data-saved="' + removeKey + '"]');
        if (mark) { mark.textContent = err.message; mark.style.color = 'var(--bad)'; }
      });
      return;
    }
    if (event.target && event.target.classList.contains('btn-toggle-mask')) {
      event.preventDefault();
      var wrap = event.target.closest('.api-key-control');
      if (wrap) {
        var inp = wrap.querySelector('input');
        if (inp) {
          var isMasked = inp.classList.toggle('setting-masked-input');
          event.target.textContent = isMasked ? 'Show' : 'Hide';
        }
      }
      return;
    }
  });
  $('settings-list').addEventListener('blur', function (event) {
    if (event.target.dataset && event.target.dataset.key && event.target.tagName === 'INPUT') { saveSetting(event.target); }
  }, true);
  $('lora-install').addEventListener('click', function () { $('lora-install-file').click(); });
  $('lora-delete').addEventListener('click', deleteLora);
  $('lora-strengths').addEventListener('click', saveLoraStrengths);
  $('lora-install-file').addEventListener('change', installSharedLora);
  var btnTestLLM = $('btn-test-llm');
  if (btnTestLLM) { btnTestLLM.addEventListener('click', testLLMConnection); }
  $('save-close').addEventListener('click', closeSaveModal);
  $('save-run').addEventListener('click', runSave);
  $('save-format').addEventListener('click', function (event) {
    var b = event.target.closest('button[data-format]');
    if (b) { pickSaveFormat(b.dataset.format); }
  });
  $('save-modal').addEventListener('click', function (event) {
    if (backdropClick(event, $('save-modal'))) { closeSaveModal(); }
  });
  $('stems-close').addEventListener('click', closeStemsModal);
  $('stems-run').addEventListener('click', runStems);
  $('stems-model').addEventListener('change', paintStemChoices);
  $('stems-modal').addEventListener('click', function (event) {
    if (backdropClick(event, $('stems-modal'))) { closeStemsModal(); }
  });
  $('lyrics-expand').addEventListener('click', openLyricsEditor);
  $('score-expand').addEventListener('click', function (event) {
    event.preventDefault();   // the Expand sits inside a summary, which toggles the box
    openScoreEditor();
  });
  var scoreRoll = $('score-roll');
  if (scoreRoll) {
    scoreRoll.addEventListener('click', function (event) {
      event.preventDefault();
      openScoreEditor('roll');
    });
  }
  if (window.PianoRoll) {
    window.PianoRoll.onUpdate(function (newAbc) {
      scoreStack.at = 0;
      pushScoreHistory(newAbc);
      $('score-big').value = newAbc;
      $('abc').value = newAbc;
      $('abc').dispatchEvent(new Event('input'));
      paintScoreTempo();
      paintScoreDirty();
      updateScoreCount();
      paintScoreHistory();
      scheduleScoreAutoSave();
    });
  }
  try {
    var savedView = localStorage.getItem(SCORE_VIEW_KEY);
    if (savedView) { State.scoreView = savedView; }
  } catch (err) { /* private mode */ }
  $('score-close').addEventListener('click', closeScoreEditor);
  var sf2Btn = $('score-render-sf2');
  if (sf2Btn) { sf2Btn.addEventListener('click', renderScoreSf2); }
  if ($('audio')) {
    ['play', 'pause', 'ended', 'emptied'].forEach(function (name) { $('audio').addEventListener(name, paintRollStudio); });
  }
  $('score-big').addEventListener('input', syncScoreFromBig);
  $('do-replace-big').addEventListener('click', function () {
    var find = $('find-chord-big').value.trim();
    var replace = $('replace-chord-big').value.trim();
    if (!find) { return; }
    var text = $('score-big').value;
    if (text.indexOf('"' + find + '"') === -1) { return; }
    scoreStack.at = 0;   // a replace is always its own step
    $('score-big').value = text.split('"' + find + '"').join('"' + replace + '"');
    syncScoreFromBig();
  });
  $('score-views').addEventListener('click', function (event) {
    var chip = event.target.closest('[data-view]');
    if (chip) { setScoreView(chip.dataset.view); }
  });
  paintScoreDirty();
  $('score-tempo').addEventListener('change', function () {
    var box = $('score-big');
    scoreStack.at = 0;                     // a tempo change is its own undo step
    setScoreTempo(parseInt($('score-tempo').value, 10));
    paintScoreTempo();
    if (box.value) { showPlanLength(box.value); }
  });
  $('score-undo').addEventListener('click', undoScore);
  $('score-redo').addEventListener('click', redoScore);
  var rollUndo = $('roll-undo-btn');
  var rollRedo = $('roll-redo-btn');
  if (rollUndo) { rollUndo.addEventListener('click', undoScore); }
  if (rollRedo) { rollRedo.addEventListener('click', redoScore); }
  var scoreMaxBtn = $('score-maximize');
  if (scoreMaxBtn) { scoreMaxBtn.addEventListener('click', toggleScoreMaximized); }
  var rollMaxBtn = $('roll-maximize');
  if (rollMaxBtn) { rollMaxBtn.addEventListener('click', toggleScoreMaximized); }
  loadScoreMaximized();
  paintScoreHistory();
  // The Lyrics and Score editors are for working in, so a click beside them does not
  // close them: only Done does (or Esc).
  $('lyrics-close').addEventListener('click', closeLyricsEditor);
  $('lyrics-big').addEventListener('input', syncLyricsFromBig);
  document.querySelector('.modal-tools').addEventListener('click', function (event) {
    var button = event.target.closest('[data-tag]');
    if (button) { insertTag(button.dataset.tag); }
  });
  if ($('confirm-modal')) {
    $('confirm-ok').addEventListener('click', function () { closeConfirmModal(true); });
    $('confirm-cancel').addEventListener('click', function () { closeConfirmModal(false); });
    if ($('confirm-close')) {
      $('confirm-close').addEventListener('click', function () { closeConfirmModal(false); });
    }
    if ($('confirm-input')) {
      $('confirm-input').addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          closeConfirmModal(true);
        }
      });
    }
    $('confirm-modal').addEventListener('click', function (event) {
      if (backdropClick(event, $('confirm-modal'))) { closeConfirmModal(false); }
    });
  }
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && $('confirm-modal') && !$('confirm-modal').classList.contains('hidden')) { closeConfirmModal(false); return; }
    if (event.key === 'Tab' && $('confirm-modal') && !$('confirm-modal').classList.contains('hidden')) {
      var focusable = $('confirm-modal').querySelectorAll('button:not([disabled]), input:not([disabled]):not(.hidden)');
      if (focusable.length) {
        var first = focusable[0];
        var last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
          return;
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
          return;
        }
      }
    }
    if (event.key === 'Escape' && $('source-picker-menu') && !$('source-picker-menu').classList.contains('hidden')) { closeSourcePicker(); return; }
    if (event.key === 'Escape' && $('lora-picker-menu') && !$('lora-picker-menu').classList.contains('hidden')) { closeLoraPicker(); return; }
    if (event.key === 'Escape' && $('style-picker-menu') && !$('style-picker-menu').classList.contains('hidden')) { closeStylePicker(); return; }
    if (event.key === 'Escape' && $('brand-menu') && !$('brand-menu').classList.contains('hidden')) { closeBrandMenu(); return; }
    if (event.key === 'Escape' && $('details-modal') && !$('details-modal').classList.contains('hidden')) { closeDetails(); return; }
    if (event.key === 'Escape' && $('about-modal') && !$('about-modal').classList.contains('hidden')) { closeAbout(); return; }
    if (event.key === 'Escape' && !$('sung-modal').classList.contains('hidden')) { closeSungWarning(); return; }
    if (event.key === 'Escape' && !$('move-modal').classList.contains('hidden')) { closeMoveModal(); return; }
    var idModal = $('identities-modal') || $('personas-modal');
    if (event.key === 'Escape' && $('train-modal') && !$('train-modal').classList.contains('hidden')) { closeTrain(); return; }
    if (event.key === 'Escape' && idModal && !idModal.classList.contains('hidden')) { closeIdentities(); return; }
    if (event.key === 'Escape' && !$('write-modal').classList.contains('hidden')) { closeWrite(); return; }
    if (event.key === 'Escape' && !$('variations-modal').classList.contains('hidden')) { closeVariations(); return; }
    if (event.key === 'Escape' && $('tries-modal') && !$('tries-modal').classList.contains('hidden')) { closeTries(); return; }
    if (event.key === 'Escape' && !$('steps-modal').classList.contains('hidden')) { closeLoraSteps(); return; }
    if (event.key === 'Escape' && !$('lyrics-modal').classList.contains('hidden')) { closeLyricsEditor(); return; }
    if (event.key === 'Escape' && !$('stems-modal').classList.contains('hidden')) { closeStemsModal(); return; }
    if (event.key === 'Escape' && !$('save-modal').classList.contains('hidden')) { closeSaveModal(); return; }
    if (event.key === 'Escape' && $('storage-modal') && !$('storage-modal').classList.contains('hidden')) { closeStorage(); return; }
    if (event.key === 'Escape' && !$('settings-modal').classList.contains('hidden')) { closeSettings(); return; }
    if (event.key === 'Escape' && !$('score-modal').classList.contains('hidden')) {
      if (scoreView() === 'roll' && window.PianoRoll && window.PianoRoll.hasSelection && window.PianoRoll.hasSelection()) {
        event.preventDefault();
        window.PianoRoll.clearSelection();
        return;
      }
      closeScoreEditor();
      return;
    }
    if (event.key === 'Escape' && $('advanced-take-modal') && !$('advanced-take-modal').classList.contains('hidden')) { closeAdvancedModal(); return; }
    if (event.key === 'Escape' && typeof editorOpen === 'function' && editorOpen()) { closeEditor(); return; }

    if (compareOpen()) { if (compareKey(event)) { event.preventDefault(); } return; }

    // Undo and redo of the score, from either box or score editor modal.
    var focus = document.activeElement;
    var inScoreModal = $('score-modal') && !$('score-modal').classList.contains('hidden');
    var inScore = focus === $('abc') || focus === $('score-big') || inScoreModal;
    if (inScore && (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'z') {
      event.preventDefault();
      if (event.shiftKey) { redoScore(); } else { undoScore(); }
      return;
    }
    if (inScore && (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'y') {
      event.preventDefault();
      redoScore();
      return;
    }
    if (inScore && (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's') {
      event.preventDefault();
      saveScore(false);
      return;
    }

    if (inScoreModal && scoreView() === 'roll') {
      var rollTag = (focus && focus.tagName) || '';
      if (rollTag !== 'INPUT' && rollTag !== 'TEXTAREA' && rollTag !== 'SELECT') {
        if (event.code === 'Space') {
          event.preventDefault();
          if (window.PianoRoll) { window.PianoRoll.togglePlay(); }
          return;
        }
        if (event.key === 'ArrowLeft') {
          event.preventDefault();
          if (window.PianoRoll) { window.PianoRoll.stepPrev(); }
          return;
        }
        if (event.key === 'ArrowRight') {
          event.preventDefault();
          if (window.PianoRoll) { window.PianoRoll.stepNext(); }
          return;
        }
        if (event.key === 'Home') {
          event.preventDefault();
          if (window.PianoRoll) { window.PianoRoll.rewindToStart(); }
          return;
        }
        if (event.key === 'Delete' || event.key === 'Backspace') {
          if (window.PianoRoll && (window.PianoRoll.hasSelection ? window.PianoRoll.hasSelection() : window.PianoRoll.selectedNoteId)) {
            event.preventDefault();
            window.PianoRoll.deleteSelectedNotes();
            return;
          }
        }
        if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'a') {
          event.preventDefault();
          if (window.PianoRoll) {
            if (event.shiftKey) {
              window.PianoRoll.selectRightOfPlayhead();
            } else {
              window.PianoRoll.selectAll();
            }
          }
          return;
        }
        if (event.altKey && event.key.toLowerCase() === 'a') {
          event.preventDefault();
          if (window.PianoRoll) { window.PianoRoll.selectRightOfPlayhead(); }
          return;
        }
        if (event.key.toLowerCase() === 'l' && !event.ctrlKey && !event.metaKey && !event.altKey) {
          if (window.PianoRoll && (window.PianoRoll.hasSelection ? window.PianoRoll.hasSelection() : window.PianoRoll.selectedNoteId)) {
            event.preventDefault();
            window.PianoRoll.editSelectedNoteLyric();
            return;
          }
        }
        if (event.key.toLowerCase() === 'v' && !event.ctrlKey && !event.metaKey && !event.altKey) {
          event.preventDefault();
          if (window.PianoRoll && window.PianoRoll.toggleVoice) {
            window.PianoRoll.toggleVoice();
          }
          return;
        }
        if ((event.key.toLowerCase() === 'c' || event.key.toLowerCase() === 'm') && !event.ctrlKey && !event.metaKey && !event.altKey) {
          event.preventDefault();
          if (window.PianoRoll) { window.PianoRoll.toggleMetronome(); }
          return;
        }
        if (event.key.toLowerCase() === 'h' && !event.ctrlKey && !event.metaKey && !event.altKey) {
          event.preventDefault();
          if (window.PianoRoll) { window.PianoRoll.toggleChords(); }
          return;
        }
        if (event.key === '+' || event.key === '=' || event.code === 'NumpadAdd' || (event.code === 'Equal' && !event.altKey)) {
          event.preventDefault();
          if (window.PianoRoll) { window.PianoRoll.zoomIn(); }
          return;
        }
        if (event.key === '-' || event.key === '_' || event.code === 'NumpadSubtract' || (event.code === 'Minus' && !event.altKey)) {
          event.preventDefault();
          if (window.PianoRoll) { window.PianoRoll.zoomOut(); }
          return;
        }
        if (event.key.toLowerCase() === 'f' && event.shiftKey && !event.ctrlKey && !event.metaKey && !event.altKey) {
          event.preventDefault();
          if (window.PianoRoll && window.PianoRoll.toggleFollow) { window.PianoRoll.toggleFollow(); }
          return;
        }
        if ((event.key.toLowerCase() === 'f' || event.key === '0') && !event.shiftKey && !event.ctrlKey && !event.metaKey && !event.altKey) {
          event.preventDefault();
          if (window.PianoRoll) { window.PianoRoll.scrollToNotes(); }
          return;
        }
      }
    }

    // Playback shortcuts, but never while typing, and never through a window
    // that is open in front: space belongs to whatever the eye is on.
    var tag = (focus && focus.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') { return; }
    if (document.querySelector('.modal:not(.hidden)')) { return; }
    if (event.code === 'Space') { event.preventDefault(); $('btn-play').click(); }
    else if (event.key === 'ArrowLeft') { nudge(-5); }
    else if (event.key === 'ArrowRight') { nudge(5); }
    else if (event.key === 'ArrowUp') { event.preventDefault(); $('volume').value = Math.min(100, Number($('volume').value) + 5); $('volume').dispatchEvent(new Event('input')); }
    else if (event.key === 'ArrowDown') { event.preventDefault(); $('volume').value = Math.max(0, Number($('volume').value) - 5); $('volume').dispatchEvent(new Event('input')); }
  });
}

wire();
loadLayout();
loadWidth();
loadSpaceChoice();
loadForm();
paintHarmony();
loadWorkingScore();
setScoreActions();
refreshTitleHint();
setMode(savedMode());
pollState();
loadSources();
loadSpaces().catch(function () { /* the takes poll retries */ });
loadTakes();

/* Polls never overlap, and stop while the tab is hidden. */
function every(ms, fn) {
  var running = false;
  setInterval(function () {
    if (running || document.hidden) { return; }
    running = true;
    Promise.resolve().then(fn).catch(function () { /* the next tick retries */ })
      .then(function () { running = false; });
  }, ms);
}
every(2000, pollState);
// Every 3 seconds while something is running, so progress on the cards moves;
// every 6 when idle.
every(3000, function () {
  var working = State.busy || State.takes.some(function (take) {
    return take.status === 'queued' || take.status === 'running' ||
      (take.stem_sets || []).some(function (set) { return set.status === 'queued' || set.status === 'running'; });
  });
  if (!working && Date.now() - State.takesAt < 6000) { return; }
  return loadTakes();
});
document.addEventListener('visibilitychange', function () {
  if (!document.hidden) { pollState(); loadTakes(); }
});

/* ============================================================ the take sheet
   The left panel shows the take the form describes, read-only: how it was made, in
   short. Making and changing takes happens in the editor window below. */

function sheetTake() {
  return takeById(selectedTakeId()) || takeById(awaitingPlanId()) || null;
}

function sheetAgo(when) {
  var gone = Date.now() / 1000 - when;
  if (gone < 3600) { return Math.max(1, Math.round(gone / 60)) + ' min ago'; }
  if (gone < 86400) { return Math.round(gone / 3600) + ' h ago'; }
  return Math.round(gone / 86400) + ' d ago';
}

/* The score's key facts and each section's chords, in the order they come. */
function sheetScore(abc) {
  var pick = function (key) { var m = abc.match(new RegExp('^' + key + ':\\s*(.*)$', 'm')); return m ? m[1].trim() : ''; };
  var tempo = (pick('Q').match(/=(\d+)/) || [])[1] || '';
  var sections = [], current = null, voice = null, bars = 0;
  abc.split('\n').forEach(function (raw) {
    var line = raw.trim();
    if (line.charAt(0) === '%') { current = { name: line.replace(/^%\s*/, '') || 'section', chords: [] }; sections.push(current); return; }
    if (line.indexOf('V:') === 0) { voice = line.slice(2).trim().split(/\s+/)[0]; return; }
    if (!line || voice !== 'Vocal' || /^[XTMLQK]:/.test(line)) { return; }
    if (!current) { current = { name: 'song', chords: [] }; sections.push(current); }
    line.split('|').forEach(function (bar) {
      if (!bar.trim()) { return; }
      bars += 1;
      (bar.match(/"([A-G][#b]?[^"\s]*)"/g) || []).forEach(function (chord) {
        chord = chord.replace(/"/g, '');
        if (current.chords[current.chords.length - 1] !== chord) { current.chords.push(chord); }
      });
    });
  });
  return { key: pick('K'), tempo: tempo, bars: bars, sections: sections.filter(function (s) { return s.chords.length; }) };
}

function sheetHTML(take) {
  if (!take) {
    return '<p class="sub">Choose a take to see how it was made, or start something new above.</p>';
  }
  var kind = take.kind || 'cover';
  var busy = take.status === 'queued' || take.status === 'running';
  var hasScore = Boolean(take.abc && take.abc.length > 50);
  var html = '<div class="kind kind-' + kind + '">' + (SHEET_KIND[kind] || kind) + '</div>' +
    '<h2>' + esc(take.title) + '</h2>' +
    '<div class="meta">' + [take.duration ? secs(take.duration) : '', take.created_at ? sheetAgo(take.created_at) : '']
      .filter(Boolean).join(' · ') + '</div>';
  if (busy) {
    html += '<div class="note">' + (take.status === 'running' ? 'Being made now.' : 'Waiting in the queue.') + '</div>';
  } else if (take.status === 'failed') {
    html += '<div class="note bad">It did not finish' + (take.error ? ': ' + esc(take.error) : '.') + '</div>';
  }
  var main = busy ? 'Open' : (take.status === 'planned' || (hasScore && !take.has_audio) ? 'Review the plan and render' : 'Edit and render again');
  html += '<div class="acts"><button type="button" class="primary tone-' + kind + '" data-sheet="' +
    (take.status === 'planned' ? 'score' : 'edit') + '">' + main + '</button>' +
    (take.has_audio ? '<button type="button" class="ghost" data-sheet="play">' + (State.playing === take.id ? 'Pause' : 'Play') + '</button>' : '') +
    '</div>';

  if (kind === 'cover') {
    var source = take.source_id ? sourceById(take.source_id) : null;
    html += '<div class="sheet-blk"><h3>Recording</h3><div class="sheet-facts">' +
      (source ? esc(source.title || source.filename || 'a recording') : '<span class="muted">not in this library any more</span>') + '</div></div>';
  }
  var tags = (take.style || '').split(',').map(function (s) { return s.trim(); }).filter(Boolean);
  if (tags.length) {
    html += '<div class="sheet-blk"><h3>Style</h3><div class="sheet-tags">' +
      tags.map(function (tag) { return '<span class="sheet-tag">' + esc(tag) + '</span>'; }).join('') + '</div></div>';
  }

  var sound = [];
  if (kind !== 'cover') {
    sound.push(['Harmony', HARMONY_WORDS[take.harmony || 0] || 'Familiar']);
    sound.push(['Plan variety', take.variety || 'normal']);
  }
  sound.push(['Interpretation', (INTERPRETATIONS[take.interpretation] || INTERPRETATIONS.standard).name]);
  if (take.style_lora) {
    sound.push(['Style LoRA', esc(take.style_lora.replace(/\.safetensors$/, '')) + ' <span class="muted">(planner ' +
      Number(take.style_lora_clip || 0).toFixed(2) + ', sound ' + Number(take.style_lora_model || 0).toFixed(2) + ')</span>']);
  }
  sound.push(['Production polish', take.realaudio ? 'on' : 'off']);
  if (take.normalised) {
    var level = take.normalised_to == null ? -14 : take.normalised_to;
    sound.push(['Normalised', (level < 0 ? '−' : '') + Math.abs(level) + ' LUFS']);
  }
  if (take.max_duration) { sound.push(['Length cap', secs(take.max_duration)]); }
  if (take.seed != null) { sound.push(['Seed', take.seed]); }
  html += '<div class="sheet-blk"><h3>Sound</h3><dl class="sheet-pairs">' +
    sound.map(function (pair) { return '<dt>' + pair[0] + '</dt><dd>' + pair[1] + '</dd>'; }).join('') + '</dl></div>';

  var lines = (take.lyrics || '').split('\n').map(function (l) { return l.trim(); }).filter(Boolean);
  var isTag = function (line) { return /^\[.*\]$/.test(line); };
  if (kind === 'instrumental') {
    var parts = lines.filter(isTag).map(function (l) { return l.slice(1, -1); });
    html += '<div class="sheet-blk"><h3>Structure</h3><div class="sheet-tags">' + (parts.length
      ? parts.map(function (p) { return '<span class="sheet-tag">' + esc(p) + '</span>'; }).join('')
      : '<span class="muted">YuE2 decides</span>') + '</div></div>';
  } else if (lines.length) {
    var shown = [], sung = 0;
    for (var i = 0; i < lines.length && sung < 5; i++) {
      if (isTag(lines[i])) { shown.push('<div class="sec">' + esc(lines[i].slice(1, -1)) + '</div>'); }
      else { shown.push('<div>' + esc(lines[i]) + '</div>'); sung += 1; }
    }
    var rest = lines.filter(function (l) { return !isTag(l); }).length - sung;
    html += '<div class="sheet-blk"><h3>Words <button type="button" class="link" data-sheet="words">Open</button></h3>' +
      '<div class="sheet-words">' + shown.join('') + (rest > 0 ? '<div class="more">and ' + rest + ' more lines</div>' : '') + '</div></div>';
  }

  if (hasScore) {
    var facts = sheetScore(take.abc);
    html += '<div class="sheet-blk"><h3>Score <button type="button" class="link" data-sheet="score">Open</button></h3>' +
      '<div class="sheet-facts">' + [facts.key && ('Key ' + esc(facts.key)), facts.tempo && (facts.tempo + ' BPM'),
        facts.bars && (facts.bars + ' bars')].filter(Boolean).join(' · ') + '</div>' +
      '<div class="sheet-chart">' + facts.sections.slice(0, 10).map(function (s) {
        return '<span class="s">' + esc(s.name) + '</span><span class="c">' + esc(s.chords.slice(0, 8).join(' ')) +
          (s.chords.length > 8 ? ' …' : '') + '</span>';
      }).join('') + (facts.sections.length > 10 ? '<span class="s">…</span><span></span>' : '') + '</div></div>';
  } else {
    html += '<div class="sheet-blk"><h3>Score</h3><div class="muted small">' + (busy && kind !== 'cover'
      ? 'The plan is being written.' : 'No score yet.') + '</div></div>';
  }
  return html;
}

function paintSheet() {
  var host = $('take-sheet');
  if (!host) { return; }
  var take = sheetTake();
  // The new button of the take's own kind stays bright; the other two step back.
  var current = take ? ({ song: 'song', cover: 'cover', instrumental: 'inst' }[take.kind] || '') : '';
  var row = document.querySelector('.sheet-new');
  if (row) {
    row.classList.toggle('has-current', Boolean(current));
    Array.prototype.forEach.call(row.querySelectorAll('[data-new]'), function (button) {
      button.classList.toggle('current', button.dataset.new === current);
    });
  }
  var html = sheetHTML(take);
  if (host.dataset.html !== html) {
    host.innerHTML = html;
    host.dataset.html = html;
  }
}

/* ========================================================== the editor window
   Every control for making or changing a take, in one window: three columns with the
   score on a tab of its own, or steps, as Settings chooses. The controls are the ones
   the left panel used to hold, so everything they do works as it did. */

function editorLayout() { return setting('editor.layout', 'columns') === 'steps' ? 'steps' : 'columns'; }
function editorOpen() { return Boolean($('editor-modal')) && !$('editor-modal').classList.contains('hidden'); }

function openEditor(where) {
  if (!$('editor-modal')) { return; }
  Editor.page = where === 'score' ? 'score' : 'song';
  Editor.step = { words: 1, sound: 2, score: 3 }[where] || 0;
  $('editor-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
  paintEditor();
  if (where === 'words' && $('lyrics') && $('lyrics').offsetParent) { $('lyrics').focus(); }
}

function closeEditor() {
  if (!editorOpen()) { return; }
  notationStop();
  if (window.PianoRoll) { window.PianoRoll.stop(); }
  if (scoreIsDirty() && (takeIdInEditor() || (State.mode === 'cover' && currentSource()))) {
    saveScore(true);
  }
  $('editor-modal').classList.add('hidden');
  document.body.style.overflow = '';
  paintSheet();
}

function paintEditor() {
  var ed = $('editor');
  if (!ed) { return; }
  setScoreActions();   // the main button's words follow the mode and the words
  var steps = editorLayout() === 'steps';
  ed.classList.toggle('layout-steps', steps);
  ed.classList.toggle('layout-columns', !steps);
  var page = steps ? (Editor.step === 3 ? 'score' : (Editor.step === 4 ? 'review' : 'song')) : Editor.page;
  Array.prototype.forEach.call(ed.querySelectorAll('[data-edpage]'), function (el) {
    el.classList.toggle('hidden', el.dataset.edpage !== page);
  });
  Array.prototype.forEach.call(ed.querySelectorAll('.ed-col'), function (el) {
    el.classList.toggle('on', Number(el.dataset.edstep) === Editor.step);
  });
  Array.prototype.forEach.call(ed.querySelectorAll('#ed-tabs [data-edtab]'), function (b) {
    b.classList.toggle('on', b.dataset.edtab === Editor.page);
  });
  Array.prototype.forEach.call(ed.querySelectorAll('#ed-steps [data-edstep]'), function (b) {
    b.classList.toggle('on', Number(b.dataset.edstep) === Editor.step);
  });
  var names = [State.mode === 'cover' ? 'Recording and style' : 'Idea', State.mode === 'inst' ? 'Structure' : 'Words', 'Sound', 'Score', 'Make it'];
  Array.prototype.forEach.call(ed.querySelectorAll('#ed-steps .ed-step-name'), function (el, i) { el.textContent = names[i]; });
  if ($('ed-words-head')) { $('ed-words-head').textContent = State.mode === 'inst' ? 'The structure' : 'The words'; }
  if ($('ed-bar')) { $('ed-bar').className = 'ed-bar ' + ({ song: 'song', inst: 'inst' }[State.mode] || 'cover'); }
  $('ed-prev').disabled = Editor.step === 0;
  $('ed-next').disabled = Editor.step === 4;
  if (page === 'score') { $('score-box').open = true; }
  if (page === 'review') { paintEditorReview(); }
  paintWriteJob(State.currentJob, []);
  paintEdTransport();
}

/* Steps: what will be sent, and anything that stops it. */
function paintEditorReview() {
  var mode = State.mode;
  var problem = mode === 'cover' ? coverProblem() : (mode === 'inst' ? instProblem() : songProblem());
  var lines = ($('lyrics').value || '').split('\n').filter(function (l) { return l.trim() && !/^\s*\[.*\]\s*$/.test(l); });
  var lora = $('style-lora') ? $('style-lora').value : '';
  var rows = [['Making', { cover: 'a cover of a recording', song: 'a song from a prompt', inst: 'an instrumental' }[mode]],
              ['Title', esc($('title').value) || '<span class="muted">from the first lyric line</span>']];
  if (mode === 'cover') {
    var source = sourceById($('source-select').value);
    rows.push(['Recording', source ? esc(source.title || source.filename) : '<span class="bad">none chosen</span>']);
  }
  rows.push(['Style', esc($('style').value) || '<span class="muted">none</span>']);
  rows.push(mode === 'inst' ? ['Structure', esc(($('structure-preview') || {}).textContent || '')] : ['Words', lines.length + ' lines']);
  if (mode !== 'cover') {
    rows.push(['Harmony', esc($('harmony-word').textContent)]);
    rows.push(['Plan variety', esc($('variety').value)]);
  }
  rows.push(['Interpretation', (INTERPRETATIONS[$('interpretation').value] || INTERPRETATIONS.standard).name]);
  rows.push(['Style LoRA', lora ? esc(lora.replace(/\.safetensors$/, '')) + ' <span class="muted">(planner ' +
    Number($('style-lora-clip').value).toFixed(2) + ', sound ' + Number($('style-lora-model').value).toFixed(2) + ')</span>' : 'none']);
  rows.push(['Length cap', esc($('max-duration').value) + ' s']);
  rows.push(['Seed', $('seed-fixed').checked ? esc($('seed').value) : 'a new one']);
  rows.push(['Production polish', $('realaudio').checked ? 'on' : 'off']);
  rows.push(['Score', keepTune() ? 'this take\'s, sung with the new words as a new take'
    : ($('abc').value.trim().length > 50 && !wordsChanged() ? 'ready, as it stands on the Score step'
    : (mode === 'cover' ? 'from the recording' : 'written first, then sung'))]);
  if (State.training) {
    rows.push(['GPU status', '<span class="bad">Reserved for training LoRA \u201c' + esc(State.training.lora_name || 'custom') + '\u201d</span>']);
  } else if (problem) {
    rows.push(['Before it can be made', '<span class="bad">' + esc(problem) + '</span>']);
  }
  $('ed-review').innerHTML = rows.map(function (r) { return '<dt>' + r[0] + '</dt><dd>' + r[1] + '</dd>'; }).join('');
}

/* After the main button: a render is queued, so the window closes and the card shows
   its progress. A plan arrives on the Score page to read, unless it renders by itself. */
/* Writing a plan closes the editor, as every other start does: the take's card shows it being written,
   and a window left open looks as if nothing happened and invites a second click. */
function editorAfterPlan() {
  closeEditor();
}

async function newTake(kind) {
  setMode(kind);
  if (!await startFresh()) { return; }
  openEditor('song');
}

function wireEditor() {
  if (!$('editor-modal') || !$('sheet-panel')) { return; }   // a page from before the editor window
  $('sheet-panel').addEventListener('click', function (event) {
    var button = event.target.closest('[data-new],[data-sheet]');
    if (!button) { return; }
    if (button.dataset.new) { newTake(button.dataset.new); return; }
    var take = sheetTake();
    var act = button.dataset.sheet;
    if (act === 'play' && take) { togglePlay(take.id); setTimeout(paintSheet, 300); return; }
    openEditor(act === 'edit' ? 'song' : act);
  });
  $('editor-close').addEventListener('click', closeEditor);
  if ($('editor-cancel')) { $('editor-cancel').addEventListener('click', closeEditor); }
  $('ed-tabs').addEventListener('click', function (event) {
    var button = event.target.closest('[data-edtab]');
    if (!button) { return; }
    Editor.page = button.dataset.edtab;
    paintEditor();
  });
  $('ed-steps').addEventListener('click', function (event) {
    var button = event.target.closest('[data-edstep]');
    if (!button) { return; }
    Editor.step = Number(button.dataset.edstep);
    paintEditor();
  });
  $('ed-prev').addEventListener('click', function () { Editor.step = Math.max(0, Editor.step - 1); paintEditor(); });
  $('ed-next').addEventListener('click', function () { Editor.step = Math.min(4, Editor.step + 1); paintEditor(); });
  // The mode buttons change what the window shows: its colour, its headings, its steps.
  Array.prototype.forEach.call(document.querySelectorAll('.modes .mode'), function (button) {
    button.addEventListener('click', function () { setTimeout(paintEditor, 0); });
  });
  // The score box belongs open in its own page.
  $('score-box').addEventListener('toggle', function () {
    if (editorOpen() && !$('score-box').open) { $('score-box').open = true; }
  });
  wireSheetToggle();
  wireAdvancedSettings();
  paintSheet();
}


/* Fold the take panel away, or bring it back. Clicking takes still updates it, so
   it is current when it opens. Remembered in this browser, like the layout. */
function setSheetCollapsed(collapsed, animate) {
  var main = document.querySelector('main');
  var toggle = $('sheet-toggle');
  if (!main || !toggle) { return; }
  setSheetCollapsed.wanted = collapsed;   // what was asked for, which a fade may not have reached yet
  toggle.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
  toggle.title = collapsed ? 'Show the take panel' : 'Hide the take panel';
  try { localStorage.setItem(SHEET_KEY, collapsed ? 'collapsed' : 'open'); } catch (err) { /* private mode */ }
  var still = !animate || (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  clearTimeout(setSheetCollapsed.timer);
  if (still) {
    main.classList.remove('sheet-fading', 'sheet-settle');
    main.classList.toggle('sheet-collapsed', collapsed);
    return;
  }
  // The takes come back up from a dip once the columns have changed.
  var settle = function () {
    main.classList.add('sheet-settle');
    void main.offsetWidth;   // lay out once at the dip, so the rise animates
    // A timer rather than an animation frame, which a tab in the background would hold back.
    setSheetCollapsed.timer = setTimeout(function () {
      main.classList.remove('sheet-settle');
      if (!collapsed) { main.classList.remove('sheet-fading'); }   // and the panel slides in
    }, 30);
  };
  if (collapsed) {
    // Slide the panel out, then give its column away.
    main.classList.add('sheet-fading');
    setSheetCollapsed.timer = setTimeout(function () {
      // One step, with nothing animating across it: settle first, then the change.
      main.classList.add('sheet-settle');
      main.classList.add('sheet-collapsed');
      main.classList.remove('sheet-fading');
      settle();
    }, 220);
  } else {
    // The column comes back with the panel still out of view, then it slides in.
    main.classList.add('sheet-settle');
    main.classList.add('sheet-fading');
    main.classList.remove('sheet-collapsed');
    settle();
  }
}

function wireSheetToggle() {
  var toggle = $('sheet-toggle');
  if (!toggle) { return; }   // a page from before the fold
  var saved = null;
  try { saved = localStorage.getItem(SHEET_KEY); } catch (err) { saved = null; }
  setSheetCollapsed(saved === 'collapsed');
  toggle.addEventListener('click', function () {
    setSheetCollapsed(!setSheetCollapsed.wanted, true);
  });
}
