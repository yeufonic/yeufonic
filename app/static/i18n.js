/* The app's words in the user's language (app/locales.py has the why).

   t('Some words')                     the words in the page's language
   t('{n} takes found', {n: count})    with values put in; a table may move {n} wherever its language wants it
   tn(n, '{n} take', '{n} takes')      a count, in the plural forms of the page's language
   tr(message)                         a message from the server, matched whole or against a table's
                                       patterns ("Take {id} not found"), its values looked up in turn
   I18N.translateDom(root)             the page's own text and its titles, placeholders and labels

   The table comes in the page's head (window.YEUFONIC_LOCALE), keyed by the English as written; a string
   it lacks stays English.  Nothing here changes what the user wrote: only the app's own words go through. */
(function (root) {
  'use strict';
  var boot = root.YEUFONIC_LOCALE || {};
  var LOCALE = boot.code || 'en-GB';
  var STRINGS = boot.strings || {};
  var has = Object.prototype.hasOwnProperty;

  function fill(text, vars) {
    return text.replace(/\{([A-Za-z_][A-Za-z0-9_]*)\}/g, function (whole, name) {
      return has.call(vars, name) && vars[name] !== undefined && vars[name] !== null ? String(vars[name]) : whole;
    });
  }

  function t(text, vars) {
    var said = has.call(STRINGS, text) ? STRINGS[text] : text;
    return vars ? fill(said, vars) : said;
  }

  /* A count: tn(n, '{n} take', '{n} takes').  A table may give the plural key every form its language has,
     ' | ' between them, in the order zero, one, two, few, many, other of those the language uses (Russian:
     one | few | many | other); otherwise the English rule picks the singular or the plural key. */
  var ORDER = ['zero', 'one', 'two', 'few', 'many', 'other'];
  var RULES = null;
  function forms() {
    if (RULES) { return RULES; }
    try {
      var rules = new Intl.PluralRules(LOCALE);
      var cats = rules.resolvedOptions().pluralCategories;
      RULES = { rules: rules, cats: ORDER.filter(function (c) { return cats.indexOf(c) >= 0; }) };
    } catch (err) { RULES = { rules: null, cats: ['one', 'other'] }; }
    return RULES;
  }
  function tn(n, one, other, vars) {
    var all = { n: n };
    if (vars) { Object.keys(vars).forEach(function (k) { all[k] = vars[k]; }); }
    var said = has.call(STRINGS, other) ? STRINGS[other] : null;
    if (said && said.indexOf(' | ') >= 0 && forms().rules) {
      var list = said.split(' | ');
      var at = forms().cats.indexOf(forms().rules.select(n));
      return fill(list[Math.max(0, Math.min(at, list.length - 1))], all);
    }
    return t(n === 1 ? one : other, all);
  }

  /* Patterns: every key with a {value} in it, made into an expression once, with its longest fixed piece
     to look for first so a message is tried against only the few that could fit. */
  var PATTERNS = null;
  function patterns() {
    if (PATTERNS) { return PATTERNS; }
    PATTERNS = [];
    Object.keys(STRINGS).forEach(function (key) {
      if (key.indexOf('{') < 0) { return; }
      var names = [];
      var pieces = key.split(/\{([A-Za-z_][A-Za-z0-9_]*)\}/);
      var source = '';
      var longest = '';
      pieces.forEach(function (piece, i) {
        if (i % 2) { names.push(piece); source += '([\\s\\S]+?)'; return; }
        source += piece.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        if (piece.length > longest.length) { longest = piece; }
      });
      if (!/[A-Za-z]{2}/.test(longest)) { return; }   // "{a}: {b}" alone would claim anything
      PATTERNS.push({ re: new RegExp('^' + source + '$'), names: names, key: key, clue: longest });
    });
    PATTERNS.sort(function (a, b) { return b.clue.length - a.clue.length; });
    return PATTERNS;
  }

  function tr(message, depth) {
    if (typeof message !== 'string' || !message) { return message; }
    if (has.call(STRINGS, message)) { return STRINGS[message]; }
    depth = depth || 0;
    if (depth > 3) { return message; }
    var list = patterns();
    for (var i = 0; i < list.length; i++) {
      var p = list[i];
      if (message.indexOf(p.clue) < 0) { continue; }
      var found = p.re.exec(message);
      if (!found) { continue; }
      var vars = {};
      p.names.forEach(function (name, j) { vars[name] = tr(found[j + 1], depth + 1); });
      return fill(STRINGS[p.key], vars);
    }
    // "Could not save: <a reason from the server>": the two halves each have a chance on their own.
    var colon = message.indexOf(': ');
    if (colon > 0 && has.call(STRINGS, message.slice(0, colon))) {
      return STRINGS[message.slice(0, colon)] + ': ' + tr(message.slice(colon + 2), depth + 1);
    }
    return message;
  }

  /* ------------------------------------------------------------ the page's own text
     A block of text with only inline markup in it (bold, code, a link, a line break) is one string, its
     markup written as bare tags ("Press <b>Render</b> to begin"), so a sentence is translated whole and
     its words can move around the markup.  Any other element's own text pieces are a string each.
     tools/i18n_catalog.py reads index.html the same way to list them; keep the two alike. */
  var INLINE = { B: 1, STRONG: 1, I: 1, EM: 1, CODE: 1, KBD: 1, BR: 1, A: 1, SMALL: 1, SUP: 1, SUB: 1, U: 1, S: 1, MARK: 1, ABBR: 1 };
  var SKIP = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1, PRE: 1, NOSCRIPT: 1, TEMPLATE: 1, svg: 1, SVG: 1 };
  var ATTRS = ['title', 'placeholder', 'aria-label', 'alt', 'label', 'data-tip'];

  function squash(text) { return text.replace(/[ \t\n\r\f]+/g, ' ').replace(/^ | $/g, ''); }
  function wordy(text) { return /[A-Za-z]{2}/.test(text); }
  function escText(text) { return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function unescText(text) { return text.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&'); }
  function skipped(el) { return SKIP[el.nodeName] || el.getAttribute('translate') === 'no'; }

  function inlineOnly(el) {
    for (var node = el.firstChild; node; node = node.nextSibling) {
      if (node.nodeType === 1 && (!INLINE[node.nodeName] || skipped(node) || !inlineOnly(node))) { return false; }
    }
    return true;
  }

  function serial(el) {
    var out = '';
    for (var node = el.firstChild; node; node = node.nextSibling) {
      if (node.nodeType === 3) { out += escText(node.nodeValue); }
      else if (node.nodeType === 1) {
        var tag = node.nodeName.toLowerCase();
        out += tag === 'br' ? '<br>' : '<' + tag + '>' + serial(node) + '</' + tag + '>';
      }
    }
    return out;
  }

  /* The translation's bare tags take back the block's own elements, in order, attributes and all. */
  function rebuild(el, translated) {
    var own = {};
    el.querySelectorAll('*').forEach(function (node) {
      var tag = node.nodeName.toLowerCase();
      (own[tag] = own[tag] || []).push(node);
    });
    var stack = [el];
    var re = /<(\/?)([a-z]+)>/g;
    var last = 0;
    var found;
    function text(s) { if (s) { stack[stack.length - 1].appendChild(document.createTextNode(unescText(s))); } }
    while (el.firstChild) { el.removeChild(el.firstChild); }
    while ((found = re.exec(translated))) {
      text(translated.slice(last, found.index));
      last = re.lastIndex;
      var tag = found[2];
      if (found[1]) {
        if (stack.length > 1) { stack.pop(); }
        continue;
      }
      var node = own[tag] && own[tag].length ? own[tag].shift() : document.createElement(tag);
      while (node.firstChild) { node.removeChild(node.firstChild); }
      stack[stack.length - 1].appendChild(node);
      if (tag !== 'br') { stack.push(node); }
    }
    text(translated.slice(last));
  }

  function translateAttrs(el) {
    for (var i = 0; i < ATTRS.length; i++) {
      var value = el.getAttribute(ATTRS[i]);
      if (value && wordy(value)) {
        var key = squash(value);
        if (has.call(STRINGS, key)) { el.setAttribute(ATTRS[i], STRINGS[key]); }
      }
    }
  }

  function translateDom(root) {
    root = root || document.body;
    if (!root) { return; }
    (function visit(el) {
      if (skipped(el)) { return; }
      translateAttrs(el);
      var hasText = false;
      for (var node = el.firstChild; node; node = node.nextSibling) {
        if (node.nodeType === 3 && wordy(node.nodeValue)) { hasText = true; break; }
      }
      if (hasText && el.firstElementChild && inlineOnly(el)) {
        var key = squash(serial(el));
        el.querySelectorAll('*').forEach(translateAttrs);
        if (has.call(STRINGS, key)) { rebuild(el, STRINGS[key]); }
        return;
      }
      for (var child = el.firstChild; child; child = child.nextSibling) {
        if (child.nodeType === 3) {
          var raw = child.nodeValue;
          if (!wordy(raw)) { continue; }
          var k = squash(raw);
          if (has.call(STRINGS, k)) {
            var lead = raw.match(/^[ \t\n\r\f]*/)[0] ? ' ' : '';
            var trail = raw.match(/[ \t\n\r\f]*$/)[0] ? ' ' : '';
            child.nodeValue = lead + STRINGS[k] + trail;
          }
        } else if (child.nodeType === 1) {
          visit(child);
        }
      }
    })(root);
  }

  /* A number or a date the way the page's language writes it. */
  function number(value, options) {
    try { return new Intl.NumberFormat(LOCALE, options).format(value); } catch (err) { return String(value); }
  }

  root.t = t;
  root.tn = tn;
  root.tr = tr;
  root.I18N = {
    locale: LOCALE,
    language: LOCALE.split('-')[0],
    strings: STRINGS,
    t: t,
    tn: tn,
    tr: tr,
    pluralForms: function () { return forms().cats.slice(); },
    translateDom: translateDom,
    number: number,
    key: function (el) { return squash(serial(el)); }
  };
  if (typeof document !== 'undefined' && document.documentElement) {
    document.documentElement.setAttribute('lang', LOCALE);
    document.documentElement.setAttribute('data-script', /^(zh|ja|ko)/.test(LOCALE) ? 'cjk' : 'latin');
  }
  // Loaded by node (the tests do, before the scripts they run), it gives the same functions, in English.
  if (typeof module !== 'undefined' && module.exports) { module.exports = root.I18N; }
})(typeof window !== 'undefined' ? window : globalThis);
