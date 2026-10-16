// Asserts expanded lyrics editor tag insertion:
// - + Male inserts [male voice]
// - + Female inserts [female voice]
// - + Both inserts [both voices]
// - Cursor handling and synchronization with lyrics textarea

import fs from 'node:fs';
import assert from 'node:assert/strict';

// 1. Verify index.html contains the buttons
const html = fs.readFileSync(new URL('../app/static/index.html', import.meta.url), 'utf8');
assert.match(html, /<button class="chip" data-tag="\[male voice\]"[^>]*>\+ Male<\/button>/);
assert.match(html, /<button class="chip" data-tag="\[female voice\]"[^>]*>\+ Female<\/button>/);
assert.match(html, /<button class="chip" data-tag="\[both voices\]"[^>]*>\+ Both<\/button>/);

// 2. Test insertion logic in app.js
import { createAppSandbox } from './dom-harness.mjs';

const { document, makeEl } = createAppSandbox();

const lyricsBig = document.getElementById('lyrics-big');
const lyricsSmall = document.getElementById('lyrics');
const modalTools = document.querySelector('.modal-tools');

// Helper to simulate clicking a tag button in modal-tools
function clickTag(tagName, tagText) {
  const btn = makeEl('');
  btn.dataset.tag = tagText;
  const listeners = modalTools._h['click'] || [];
  listeners.forEach(fn => fn({
    target: btn,
    preventDefault() {}
  }));
}

// Test 1: Insert [male voice] at beginning of line
lyricsBig.value = '[Verse]\nI still dream\nof Orgonon';
// Place cursor at the start of line 2 ("I still dream")
const line2Pos = lyricsBig.value.indexOf('I still dream');
lyricsBig.selectionStart = lyricsBig.selectionEnd = line2Pos;

clickTag('+ Male', '[male voice]');

assert.equal(lyricsBig.value, '[Verse]\n[male voice]\nI still dream\nof Orgonon');
assert.equal(lyricsSmall.value, lyricsBig.value, 'small lyrics box synced');
assert.equal(document.activeElement, lyricsBig, 'lyricsBig focused after insertion');
console.log('ok   + Male inserts [male voice] on the line where the cursor is');

// Test 2: Insert [female voice] at end of text / on a new line
lyricsBig.value = '[Verse]\nI still dream\n';
lyricsBig.selectionStart = lyricsBig.selectionEnd = lyricsBig.value.length;

clickTag('+ Female', '[female voice]');

assert.equal(lyricsBig.value, '[Verse]\nI still dream\n[female voice]\n');
assert.equal(lyricsSmall.value, lyricsBig.value, 'small lyrics box synced');
console.log('ok   + Female inserts [female voice] on new line');

// Test 3: Insert [both voices]
lyricsBig.value = '[Chorus]\n';
lyricsBig.selectionStart = lyricsBig.selectionEnd = lyricsBig.value.length;

clickTag('+ Both', '[both voices]');

assert.equal(lyricsBig.value, '[Chorus]\n[both voices]\n');
assert.equal(lyricsSmall.value, lyricsBig.value, 'small lyrics box synced');
console.log('ok   + Both inserts [both voices] on new line');

// Test 4: Replace selected text
lyricsBig.value = '[Verse]\n[placeholder]\nLine 1';
const selStart = lyricsBig.value.indexOf('[placeholder]');
lyricsBig.selectionStart = selStart;
lyricsBig.selectionEnd = selStart + '[placeholder]'.length;

clickTag('+ Male', '[male voice]');

assert.equal(lyricsBig.value, '[Verse]\n[male voice]\nLine 1');
console.log('ok   + Male replaces selected text with [male voice]');

console.log('\nall lyrics tag checks pass');
process.exit(0);
