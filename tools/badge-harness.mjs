// Asserts corpora badge behavior: failure count and busy state are scoped
// to the displayed corpus, clearing error styling and tooltips when switching
// to a clean corpus.
//
//   node tools/badge-harness.mjs
//
// It runs offline: the DOM is stubbed, so it needs no server, no engine
// and no library.

import fs from 'node:fs';
import vm from 'node:vm';

const here = new URL('../app/static/app.js', import.meta.url);
const src = fs.readFileSync(here, 'utf8');

function makeEl(id) {
  const classes = new Set();
  const el = {
    id, value: '', textContent: '', innerHTML: '', title: '', dataset: {},
    options: [], selectionStart: 0, selectionEnd: 0,
    style: { setProperty() {}, removeProperty() {} },
    get className() { return Array.from(classes).join(' '); },
    set className(val) { classes.clear(); (val || '').split(/\s+/).filter(Boolean).forEach((c) => classes.add(c)); },
    classList: {
      add(c) { classes.add(c); },
      remove(c) { classes.delete(c); },
      toggle(c, force) { if (force !== undefined) { force ? classes.add(c) : classes.delete(c); } else { classes.has(c) ? classes.delete(c) : classes.add(c); } },
      contains(c) { return classes.has(c); }
    },
    addEventListener(t, fn) { (el._h[t] = el._h[t] || []).push(fn); },
    dispatchEvent(t) { (el._h[t.type] || []).forEach((f) => f(t)); return true; },
    focus() {}, blur() {}, remove() {},
    closest() { return null; }, querySelector() { return null; }, querySelectorAll() { return []; },
    appendChild(child) { if (child && child.id) { els.set(child.id, child); } return child; },
    setAttribute() {}, removeAttribute() {}, _h: {}
  };
  if (id) { els.set(id, el); }
  return el;
}

const els = new Map();
const document = {
  getElementById(id) { if (!els.has(id)) els.set(id, makeEl(id)); return els.get(id); },
  querySelector(s) { if (!els.has(s)) els.set(s, makeEl(s)); return els.get(s); },
  querySelectorAll() { return []; },
  createElement(tag) { return makeEl(''); },
  body: makeEl('body'),
  documentElement: makeEl('documentElement'),
  addEventListener() {}
};

const store = new Map();
const ctx = {
  document, console, setTimeout, clearTimeout, setInterval: () => 0, clearInterval: () => {}, Promise,
  window: { confirm: () => true, addEventListener() {}, devicePixelRatio: 1, requestAnimationFrame: () => 0, cancelAnimationFrame: () => 0 },
  navigator: { mediaSession: { setActionHandler() {} }, clipboard: { writeText: async () => {} } },
  ABCJS: { renderAbc() {} },
  Path2D: class {},
  localStorage: { getItem: (k) => store.get(k) || null, setItem: (k, v) => store.set(k, String(v)) },
  fetch: () => Promise.resolve({
    ok: true,
    headers: { get: () => 'application/json' },
    json: () => Promise.resolve([]),
    text: () => Promise.resolve('[]')
  })
};
ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(src, ctx, { filename: 'app.js' });

ctx.State.options = { training_available: true };
const badge = ctx.corporaBadge();

ctx.State.corpusProgress = {
  c1: { id: 'c1', name: 'Corpus With Errors', done: 10, total: 10, failed: 2, busy: false, started: true },
  c2: { id: 'c2', name: 'Clean Corpus', done: 10, total: 10, failed: 0, busy: false, started: true },
  c3: { id: 'c3', name: 'Busy Corpus', done: 4, total: 10, failed: 0, busy: true, started: true }
};

// 1. Viewing a corpus with settled failures applies trouble class and mentions failed songs in tooltip
ctx.IDENTITY.id = 'c1';
ctx.paintCorporaBadge();
if (!badge.classList.contains('trouble')) throw new Error('c1 badge must have trouble class');
if (!badge.title.includes('2 songs did not analyse')) throw new Error('c1 title must mention 2 songs did not analyse: ' + badge.title);
if (!els.get('corpora-text').innerHTML.includes('Corpus With Errors')) throw new Error('c1 text must show name');
console.log('ok   corpus with errors shows trouble class and failed songs in tooltip');

// 2. Switching to a clean corpus clears trouble class and omits error text from tooltip
ctx.IDENTITY.id = 'c2';
ctx.paintCorporaBadge();
if (badge.classList.contains('trouble')) throw new Error('c2 badge must NOT have trouble class');
if (badge.title.includes('did not analyse')) throw new Error('c2 title must NOT mention did not analyse: ' + badge.title);
if (!els.get('corpora-text').innerHTML.includes('Clean Corpus')) throw new Error('c2 text must show name');
console.log('ok   clean corpus clears trouble class and tooltip error text');

// 3. Switching back to the corpus with errors restores trouble class and error tooltip
ctx.IDENTITY.id = 'c1';
ctx.paintCorporaBadge();
if (!badge.classList.contains('trouble')) throw new Error('c1 badge must have trouble class again');
if (!badge.title.includes('2 songs did not analyse')) throw new Error('c1 title must mention 2 songs did not analyse again: ' + badge.title);
console.log('ok   switching back restores trouble styling and error tooltip');

// 4. Viewing a busy corpus pulses busy without showing trouble
ctx.IDENTITY.id = 'c3';
ctx.paintCorporaBadge();
if (!badge.classList.contains('busy')) throw new Error('c3 badge must have busy class');
if (badge.classList.contains('trouble')) throw new Error('c3 badge must NOT have trouble class');
if (!badge.title.includes('still working')) throw new Error('c3 title must indicate working: ' + badge.title);
console.log('ok   busy corpus shows busy class and working tooltip');

console.log('\nall badge checks pass');
process.exit(0);
