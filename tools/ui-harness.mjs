// Drives the real app.js against a running deployment, with a stub DOM.
//
// Written to find a bug where a finished job reloaded the source list and
// overwrote the score plan that had just landed, leaving "Render this score"
// with nothing to act on.  It reproduced that in one run, which reading the
// code had failed to do three times.
//
//   APP=http://127.0.0.1:8090 node tools/ui-harness.mjs
//
// It creates real takes.  Delete them afterwards.

import { createAppSandbox } from './dom-harness.mjs';
const APP = process.env.APP || 'http://127.0.0.1:8090';
const { ctx, $ } = createAppSandbox({
  fetch: (u, o) => fetch(u.startsWith('http') ? u : APP + u, o)
});
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

ctx.setMode('song');
// The controls the page reads when it builds the request. A real browser has a
// default in each; these stubs start empty, and an empty interpretation is
// refused by the server.
$('title').value = 'Harness click-through';
$('style').value = 'late 1960s psychedelic';
$('lyrics').value = '[Verse]\nOne pill makes you larger\nAnd one pill makes you small\n[Chorus]\nGo ask Alice';
$('interpretation').value = 'standard';
$('variety').value = 'normal';
$('harmony').value = '0';
$('max-duration').value = '60';
$('mode').value = 'full';
await ctx.doPlan();
console.log('STEP doPlan said  :', JSON.stringify($('render-status').textContent).slice(0, 120));
const id = ctx.Selection.awaiting;
for (let i = 0; i < 15; i++) {
  await sleep(4000);
  await ctx.watchPlan();
  if (String($('abc').value).length > 50) break;
}
console.log('STEP plan landed   : abc=' + String($('abc').value).length, 'editorTake=' + ctx.takeIdInEditor(), 'render disabled=' + $('render-take').disabled);

await ctx.doRenderTake();
console.log('STEP render clicked: status text =', JSON.stringify($('render-status').textContent));
let status = '?';
for (let i = 0; i < 40; i++) {
  await sleep(5000);
  const t = await (await fetch(APP + '/api/takes/' + id)).json();
  status = t.status;
  if (status === 'done' || status === 'failed') { console.log('STEP render:', status, 'duration=', t.duration, 'audio=', t.has_audio, (t.error || '')); break; }
}
console.log('TAKE_ID', id);
