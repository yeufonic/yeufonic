"""Assemble a translated guide, app/static/guides/<code>.md, from parts written by hand or by a model.

    python3 tools/guide_assemble.py <code> <parts-folder> [--dry]

The parts are <code>.1.md, <code>.2.md, ... in the folder, joined in order. They follow app/static/guide.md
heading for heading (h2-h4), and name every button or setting as ⟦English text⟧, the en-GB string the app shows:
each is swapped for the locale table's wording, so the guide names things exactly as the translated app does (a
name missing from the table is reported and left in English). Each translated h2-h4 heading then gets the English
heading's anchor, `{#slug}`, by position, so links into the guide (#hot-keys, #style-loras...) land in the same place
in every language; guide.html strips the suffix and uses it as the heading's id. tests/test_guide.py checks the
result: the same anchors in the same order, no dead links, code blocks unchanged.
"""
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADING = re.compile(r'^(#{2,4}) (.+?)[ \t]*$', re.M)


def slug(text):
    return re.sub(r'^-|-$', '', re.sub(r'[^a-z0-9]+', '-', text.lower()))


def _punct(ch):
    return ch == '\x00' or unicodedata.category(ch)[0] in 'PS'


def _fix_emphasis(text):
    """CommonMark (and marked) only opens `**` when the run is followed by a letter or comes after a space or
    punctuation, and only closes it in the mirror case. Chinese and Japanese put no spaces between words, so
    `**+ 歌曲**` or `**无乐谱（仅限歌曲）**` sits straight against other letters and the asterisks show instead of bold.
    Such spans become <strong> or <em>, which marked passes through. Code is kept out of it: each code span stands
    in as one punctuation mark (a backtick is one to marked), and fenced blocks are not touched."""
    codes = []
    def keep(m):
        codes.append(m.group(0))
        return '\x00'
    text = re.sub(r'```.*?```|`[^`\n]*`', keep, text, flags=re.S)
    text = text.replace('****', '** **')  # two bold spans meeting: `**a：****b**` would read as one run
    def one(m, tag):
        before, inner, after = m.string[m.start() - 1:m.start()], m.group(1), m.string[m.end():m.end() + 1]
        if (before and not before.isspace() and not _punct(before) and _punct(inner[0])) or \
           (after and not after.isspace() and not _punct(after) and _punct(inner[-1])):
            return f'<{tag}>{inner}</{tag}>'
        return m.group(0)
    span = r'((?:(?!\*)[^\n]|\n(?!\n))+?)'
    text = re.sub(r'\*\*' + span + r'\*\*', lambda m: one(m, 'strong'), text)
    text = re.sub(r'(?<!\*)\*(?=\S)' + span + r'(?<=\S)\*(?!\*)', lambda m: one(m, 'em'), text)
    return re.sub('\x00', lambda m: codes.pop(0), text)


_WIDE = re.compile(r'[\u2014\u2026\u3000-\u30ff\u3400-\u9fff\uf900-\ufaff\uff00-\uffef]')
_BLOCK = re.compile(r'\s*(#|\||[-*+] |\d+\. |>|```|$)')


def _join_wide_lines(text):
    """Chinese and Japanese put no spaces between words, but a browser turns the line break inside a paragraph into
    a space (Chromium does not drop it between wide characters, as CSS allows), so a sentence wrapped in the source
    showed a gap. A line that carries on a paragraph is joined to the one before when both sides of the break are
    wide characters; headings, tables, list items and code are left alone."""
    out, fenced = [], False
    for line in text.split('\n'):
        if line.lstrip().startswith('```'):
            fenced = not fenced
            out.append(line)
            continue
        prev = out[-1] if out else ''
        if (not fenced and out and prev.strip() and not _BLOCK.match(line) and not re.match(r'\s*(#|\|)', prev)
                and _WIDE.match(prev.rstrip().rstrip('*')[-1:] or ' ') and _WIDE.match(line.lstrip().lstrip('*')[:1] or ' ')):
            out[-1] = prev.rstrip() + line.lstrip()
        else:
            out.append(line)
    return '\n'.join(out)


def assemble(code, folder):
    names = [n for n in os.listdir(folder) if re.fullmatch(re.escape(code) + r'\.\d+\.md', n)]
    names.sort(key=lambda n: int(n.rsplit('.', 2)[-2]))
    text = '\n'.join(open(os.path.join(folder, n), encoding='utf-8').read().rstrip('\n') + '\n' for n in names)
    path = os.path.join(ROOT, 'app', 'static', 'locales', f'{code}.json')
    table = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    missing = []

    def swap(m):
        if m.group(1) in table:
            return table[m.group(1)]
        missing.append(m.group(1))
        return m.group(1)

    text = re.sub(r'⟦([^⟧]+)⟧', swap, text)
    english = HEADING.findall(open(os.path.join(ROOT, 'app', 'static', 'guide.md'), encoding='utf-8').read())
    found = list(HEADING.finditer(text))
    problems = [f'{len(found)} headings, English has {len(english)}'] if len(found) != len(english) else []
    out, last = [], 0
    for (level, head), m in zip(english, found):
        if m.group(1) != level:
            problems.append(f'level differs: {head} | {m.group(2)}')
        out += [text[last:m.start()], f'{m.group(1)} {re.sub(r"\s*\{#[^}]*\}$", "", m.group(2))} {{#{slug(head)}}}']
        last = m.end()
    out.append(text[last:])
    text = ''.join(out)
    if code[:2] in ('zh', 'ja'):
        text = _join_wide_lines(text)
    if code[:2] in ('zh', 'ja', 'ko'):
        text = _fix_emphasis(text)
    return text, sorted(set(missing)), problems, len(found)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    code, folder = sys.argv[1], sys.argv[2]
    text, missing, problems, count = assemble(code, folder)
    for p in problems:
        print(p)
    if missing:
        print('NOT IN TABLE', missing)
    if '--dry' not in sys.argv:
        os.makedirs(os.path.join(ROOT, 'app', 'static', 'guides'), exist_ok=True)
        open(os.path.join(ROOT, 'app', 'static', 'guides', f'{code}.md'), 'w', encoding='utf-8').write(text)
    print(code, count, 'headings', len(text), 'chars')
