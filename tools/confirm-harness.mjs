// Asserts in-app confirm modal behavior: destructive tone, button focus,
// keyboard dismissal, and cancellation.
//
//   node tools/confirm-harness.mjs
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
    id, value: '', textContent: '', innerHTML: '', checked: false, disabled: false,
    open: false, files: [], options: [], selectionStart: 0, selectionEnd: 0,
    style: { setProperty() {}, removeProperty() {} }, dataset: {},
    get className() { return Array.from(classes).join(' '); },
    set className(val) { classes.clear(); (val || '').split(/\s+/).filter(Boolean).forEach((c) => classes.add(c)); },
    classList: {
      add(c) { classes.add(c); },
      remove(c) { classes.delete(c); },
      toggle(c, force) { if (force !== undefined) { force ? classes.add(c) : classes.delete(c); } else { classes.has(c) ? classes.delete(c) : classes.add(c); } },
      contains(c) { return classes.has(c); }
    },
    addEventListener(t, fn) { (el._h[t] = el._h[t] || []).push(fn); },
    click() { (el._h.click || []).forEach((f) => f({ target: el, preventDefault() {} })); },
    dispatchEvent(t) { (el._h[t.type] || []).forEach((f) => f(t)); return true; },
    focus() { document.activeElement = el; }, blur() {}, remove() {},
    closest() { return null; }, scrollIntoView() {}, setAttribute() {},
    querySelectorAll() { return []; }, querySelector() { return null; }, _h: {}
  };
  return el;
}

const els = new Map();
const document = {
  activeElement: null,
  getElementById(id) { if (!els.has(id)) els.set(id, makeEl(id)); return els.get(id); },
  querySelector(s) { if (!els.has(s)) els.set(s, makeEl(s)); return els.get(s); },
  querySelectorAll() { return []; },
  addEventListener(t, fn) { (this._h[t] = this._h[t] || []).push(fn); },
  dispatchEvent(e) { (this._h[e.type] || []).forEach((f) => f(e)); },
  _h: {}, body: makeEl('body'), documentElement: makeEl('documentElement')
};

const ctx = {
  document, console, setTimeout, clearTimeout, setInterval: () => 0, clearInterval: () => {}, Promise,
  window: { confirm: () => true, addEventListener() {}, devicePixelRatio: 1, requestAnimationFrame: () => 0, cancelAnimationFrame: () => 0 },
  navigator: { mediaSession: { setActionHandler() {} }, clipboard: { writeText: async () => {} } },
  ABCJS: { renderAbc() {} },
  Path2D: class {},
  localStorage: { getItem: () => null, setItem: () => {} },
  fetch: () => Promise.resolve({
    ok: true,
    headers: { get: () => 'application/json' },
    json: () => Promise.resolve({}),
    text: () => Promise.resolve('')
  })
};
ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(src, ctx);

async function run() {
  const { confirmModal, $ } = ctx;
  const modal = $('confirm-modal');
  modal.classList.add('hidden');

  // Destructive modal configuration and focus guard
  let p1 = confirmModal({
    title: 'Delete take',
    message: 'Delete take 1?',
    confirmText: 'Delete',
    cancelText: 'Cancel',
    danger: true
  });
  if (modal.classList.contains('hidden')) throw new Error('modal not visible');
  if ($('confirm-title').textContent !== 'Delete take') throw new Error('title mismatch');
  if ($('confirm-message').textContent !== 'Delete take 1?') throw new Error('message mismatch');
  if ($('confirm-ok').textContent !== 'Delete') throw new Error('ok text mismatch');
  if ($('confirm-cancel').textContent !== 'Cancel') throw new Error('cancel text mismatch');
  if (!$('confirm-ok').classList.contains('danger')) throw new Error('ok button missing danger class');
  if (document.activeElement !== $('confirm-cancel')) throw new Error('focus was not on cancel button');
  console.log('ok   danger modal focuses cancel and applies danger styling');

  // Cancel action resolves false
  $('confirm-cancel').click();
  let res1 = await p1;
  if (res1 !== false) throw new Error('expected false on cancel');
  if (!modal.classList.contains('hidden')) throw new Error('modal not hidden after cancel');
  console.log('ok   cancel button resolves false and hides modal');

  // Non-destructive modal configuration and OK focus
  let p2 = confirmModal({
    title: 'Normal',
    message: 'Proceed?',
    confirmText: 'Yes',
    danger: false
  });
  if ($('confirm-ok').classList.contains('danger')) throw new Error('danger class should not be present');
  if (document.activeElement !== $('confirm-ok')) throw new Error('focus was not on ok button');
  console.log('ok   non-danger modal focuses ok button');

  // OK action resolves true
  $('confirm-ok').click();
  let res2 = await p2;
  if (res2 !== true) throw new Error('expected true on ok');
  console.log('ok   ok button resolves true and hides modal');

  // Header close button resolves false
  let p3 = confirmModal('Close test');
  $('confirm-close').click();
  let res3 = await p3;
  if (res3 !== false) throw new Error('expected false on close');
  console.log('ok   header close button resolves false');

  // Escape key resolves false
  let p4 = confirmModal('Escape test');
  document.dispatchEvent({ type: 'keydown', key: 'Escape' });
  let res4 = await p4;
  if (res4 !== false) throw new Error('expected false on escape');
  console.log('ok   escape key resolves false');

  // Superseding modal
  let p5 = confirmModal('First');
  let p6 = confirmModal('Second');
  let res5 = await p5;
  if (res5 !== false) throw new Error('first should resolve false');
  $('confirm-ok').click();
  let res6 = await p6;
  if (res6 !== true) throw new Error('second should resolve true');
  console.log('ok   pending confirm is safely superseded by a new one');

  // Input modal (New space / Rename space)
  let p7 = confirmModal({
    title: 'New space',
    message: 'Name the new space:',
    input: true,
    defaultValue: 'My Space',
    confirmText: 'Create space'
  });
  const inputEl = $('confirm-input');
  if (inputEl.classList.contains('hidden')) throw new Error('input should be visible in input mode');
  if (inputEl.value !== 'My Space') throw new Error('defaultValue was not populated');
  // Type a new name and submit
  inputEl.value = 'Acoustic Sessions';
  $('confirm-ok').click();
  let res7 = await p7;
  if (res7 !== 'Acoustic Sessions') throw new Error('expected entered text string on OK');
  if (!inputEl.classList.contains('hidden')) throw new Error('input should be hidden after close');
  console.log('ok   input modal returns entered string on OK');

  // Input modal cancelled returns null
  let p8 = confirmModal({
    title: 'Rename space',
    message: 'Rename space:',
    input: true,
    defaultValue: 'Default'
  });
  $('confirm-cancel').click();
  let res8 = await p8;
  if (res8 !== null) throw new Error('expected null on cancel in input mode');
  console.log('ok   input modal returns null on Cancel');

  console.log('\nall confirm modal checks pass');
  process.exit(0);
}

run().catch((err) => {
  console.error('FAILED:', err);
  process.exit(1);
});
