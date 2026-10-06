/**
 * Rearranging the sections of a score.
 *
 * A transcribed score names each of its sections on a "% name" line, and every section is a block of its
 * own: the voices it plays and its bars follow the line, under a header (tempo, key, voices) that they
 * share. So a section can be moved, copied or taken out by moving the block, and the score that results
 * is still the score of a song. This works on the text only; the page shows the result and the render
 * plays it as it plays any score.
 */
(function (global) {
  'use strict';

  var MARK = /^%[ \t]*([A-Za-z][\w -]*?)[ \t]*$/gm;       // the same lines the section list reads

  // The header, and each section's text from its "%" line up to the next one.
  function parse(abc) {
    var text = String(abc || '');
    var at = [];
    var found;
    MARK.lastIndex = 0;
    while ((found = MARK.exec(text))) { at.push(found.index); }
    if (!at.length) { return { head: text, parts: [], endsWithNewline: /\n$/.test(text) }; }
    var parts = at.map(function (start, i) { return text.slice(start, i + 1 < at.length ? at[i + 1] : text.length); });
    return { head: text.slice(0, at[0]), parts: parts, endsWithNewline: /\n$/.test(text) };
  }

  function build(head, parts, endsWithNewline) {
    var out = head + parts.map(function (part) { return /\n$/.test(part) ? part : part + '\n'; }).join('');
    return endsWithNewline ? out : out.replace(/\n$/, '');
  }

  /**
   * op: { act: 'up' | 'down' | 'copy' | 'remove' | 'move', index, to }; 'move' puts section `index` at position `to`
   * (counted after it has been lifted out, so `to` is where it ends up). Returns the new score, or null when the
   * move cannot be made (off either end, no such section, or the last section left).
   */
  function change(abc, op) {
    var score = parse(abc);
    var parts = score.parts.slice();
    var i = Number(op && op.index);
    if (!parts.length || !(i >= 0 && i < parts.length) || Math.floor(i) !== i) { return null; }
    if (op.act === 'up') {
      if (i === 0) { return null; }
      parts.splice(i - 1, 2, parts[i], parts[i - 1]);
    } else if (op.act === 'down') {
      if (i === parts.length - 1) { return null; }
      parts.splice(i, 2, parts[i + 1], parts[i]);
    } else if (op.act === 'copy') {
      parts.splice(i + 1, 0, parts[i]);
    } else if (op.act === 'move') {
      var to = Number(op.to);
      if (!(to >= 0 && to < parts.length) || Math.floor(to) !== to || to === i) { return null; }
      parts.splice(to, 0, parts.splice(i, 1)[0]);
    } else if (op.act === 'remove') {
      if (parts.length < 2) { return null; }
      parts.splice(i, 1);
    } else {
      return null;
    }
    return build(score.head, parts, score.endsWithNewline);
  }

  /**
   * Whether a score of `total` seconds fits under a cap of `cap` seconds. When it does not, by how much it falls short and
   * the cap that would hold it with a little to spare (the same rule the page uses for a recording: ten seconds, rounded up
   * to ten, and never over the 900 the engine allows).
   */
  function capCheck(total, cap) {
    total = Number(total); cap = Number(cap);
    if (!(total > 0) || !(cap > 0) || total <= cap) { return { over: false }; }
    return { over: true, short: Math.round(total - cap), raiseTo: Math.min(900, Math.ceil((total + 10) / 10) * 10) };
  }

  /**
   * What to tell the person about a cover's words after the sections changed: the words are matched to the sections in
   * order, so an added section needs words, a removed one should lose its, and a moved one should have its words moved.
   * `before` and `after` are how many sections there were. Returns null when nothing changed.
   */
  function wordsNote(before, after, reordered) {
    before = Number(before); after = Number(after);
    var plural = function (n, word) { return n + ' ' + word + (n === 1 ? '' : 's'); };
    if (after > before) {
      return 'You added ' + plural(after - before, 'section') + ', and the words are matched to the sections in order, so the Words box needs ' +
        plural(after - before, 'more block') + ' of words. Repeating the words of the section you copied works.';
    }
    if (after < before) {
      return 'You took out ' + plural(before - after, 'section') + ', and the words are matched to the sections in order, so take their words out of the Words box too.';
    }
    return reordered ? 'You rearranged the sections, and the words are matched to the sections in order, so rearrange their words in the Words box to match.' : null;
  }

  global.ScoreSections = { parse: parse, change: change, capCheck: capCheck, wordsNote: wordsNote };
  if (typeof module !== 'undefined' && module.exports) { module.exports = global.ScoreSections; }

})(typeof window !== 'undefined' ? window : this);
