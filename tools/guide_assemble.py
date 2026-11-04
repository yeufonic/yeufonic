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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADING = re.compile(r'^(#{2,4}) (.+?)\s*$', re.M)


def slug(text):
    return re.sub(r'^-|-$', '', re.sub(r'[^a-z0-9]+', '-', text.lower()))


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
    return ''.join(out), sorted(set(missing)), problems, len(found)


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
