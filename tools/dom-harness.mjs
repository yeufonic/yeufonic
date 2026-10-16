// Shared Node VM + stub DOM sandbox for offline/online UI harnesses.
import fs from 'node:fs';
import vm from 'node:vm';

export function createAppSandbox(options = {}) {
  const els = new Map();
  const store = new Map();

  function makeEl(id) {
    const classes = new Set();
    const el = {
      id,
      value: '',
      textContent: '',
      innerHTML: '',
      title: '',
      checked: false,
      disabled: false,
      open: false,
      files: [],
      options: [],
      selectionStart: 0,
      selectionEnd: 0,
      style: { setProperty() {}, removeProperty() {} },
      dataset: {},
      get className() {
        return Array.from(classes).join(' ');
      },
      set className(val) {
        classes.clear();
        (val || '').split(/\s+/).filter(Boolean).forEach((c) => classes.add(c));
      },
      classList: {
        add(c) { classes.add(c); },
        remove(c) { classes.delete(c); },
        toggle(c, force) {
          if (force !== undefined) {
            force ? classes.add(c) : classes.delete(c);
          } else {
            classes.has(c) ? classes.delete(c) : classes.add(c);
          }
        },
        contains(c) { return classes.has(c); }
      },
      addEventListener(t, fn) { (el._h[t] = el._h[t] || []).push(fn); },
      click() { (el._h.click || []).forEach((f) => f({ target: el, preventDefault() {} })); },
      dispatchEvent(t) { (el._h[t.type] || []).forEach((f) => f(t)); return true; },
      focus() { document.activeElement = el; },
      blur() {},
      remove() {},
      closest(selector) {
        if (selector === '[data-tag]' && el.dataset.tag) return el;
        return null;
      },
      scrollIntoView() {},
      setAttribute(k, v) { if (k.startsWith('data-')) el.dataset[k.slice(5)] = v; },
      removeAttribute() {},
      appendChild(child) {
        if (child && child.id) { els.set(child.id, child); }
        return child;
      },
      querySelector() { return null; },
      querySelectorAll() { return []; },
      getContext() { return { clearRect() {}, fillRect() {}, fillStyle: '', measureText: () => ({ width: 10 }) }; },
      getBoundingClientRect() { return { left: 0, width: 600, top: 0, height: 44 }; },
      clientWidth: 600,
      width: 600,
      height: 44,
      _h: {}
    };
    if (id) { els.set(id, el); }
    return el;
  }

  const document = {
    activeElement: null,
    getElementById(id) { if (!els.has(id)) els.set(id, makeEl(id)); return els.get(id); },
    querySelector(s) { if (!els.has(s)) els.set(s, makeEl(s)); return els.get(s); },
    querySelectorAll() { return []; },
    createElement() { return makeEl(''); },
    addEventListener(t, fn) { (this._h[t] = this._h[t] || []).push(fn); },
    dispatchEvent(e) { (this._h[e.type] || []).forEach((f) => f(e)); },
    _h: {},
    body: makeEl('body'),
    documentElement: makeEl('documentElement')
  };

  const defaultFetch = () => Promise.resolve({
    ok: true,
    status: 200,
    headers: { get: () => 'application/json' },
    json: () => Promise.resolve({}),
    text: () => Promise.resolve('{}')
  });

  const ctx = {
    document,
    console,
    setTimeout,
    clearTimeout,
    setInterval: () => 0,
    clearInterval: () => {},
    Promise,
    confirm: () => true,
    requestAnimationFrame: () => 0,
    cancelAnimationFrame: () => 0,
    window: {
      confirm: () => true,
      addEventListener() {},
      devicePixelRatio: 1,
      requestAnimationFrame: () => 0,
      cancelAnimationFrame: () => 0,
      getComputedStyle: () => ({ getPropertyValue: () => '' })
    },
    navigator: { mediaSession: { setActionHandler() {} }, clipboard: { writeText: async () => {} } },
    ABCJS: { renderAbc() {} },
    marked: { parse: (text) => text },
    Path2D: class { moveTo() {} lineTo() {} closePath() {} },
    localStorage: {
      getItem: (k) => (store.has(k) ? store.get(k) : null),
      setItem: (k, v) => store.set(k, String(v))
    },
    fetch: options.fetch || defaultFetch,
    Event: class { constructor(type) { this.type = type; } }
  };
  ctx.globalThis = ctx;
  vm.createContext(ctx);

  const scripts = options.scripts || ['../app/static/sectionedit.js', '../app/static/app.js'];
  for (const rel of scripts) {
    const url = new URL(rel, import.meta.url);
    if (fs.existsSync(url)) {
      const code = fs.readFileSync(url, 'utf8');
      vm.runInContext(code, ctx, { filename: rel.split('/').pop() });
    }
  }

  return { ctx, document, els, makeEl, $: (id) => document.getElementById(id) };
}
