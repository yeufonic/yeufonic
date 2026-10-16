// Asserts corpora badge behavior: failure count and busy state are scoped
// to the displayed corpus, clearing error styling and tooltips when switching
// to a clean corpus.
//
//   node tools/badge-harness.mjs
//
// It runs offline: the DOM is stubbed, so it needs no server, no engine
// and no library.

import { createAppSandbox } from './dom-harness.mjs';

const { ctx, els } = createAppSandbox({
  fetch: () => Promise.resolve({
    ok: true,
    headers: { get: () => 'application/json' },
    json: () => Promise.resolve([]),
    text: () => Promise.resolve('[]')
  })
});

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
