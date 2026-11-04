"""Every string the app shows that a locale's table should hold, and the tables' state against it.

The page's words come from three places, each read here the way the page reads it (app/locales.py has the
design):

* the pages' own text (index.html, logs.html): a block of text with only inline markup is one string,
  its markup as bare tags; otherwise each text piece; and the title, placeholder and label attributes.
  ``I18N.translateDom`` in app/static/i18n.js does the same in the browser: keep the two alike.
* the scripts: the literal English in every ``t('...')``, ``I18N.t('...')`` and ``tn(n, '...', '...')``.
* the server: the messages the page shows, from the Python source: HTTP errors, job errors and stages,
  settings' labels and help, and the like.  An f-string is a pattern, its values named in braces, which
  ``tr()`` matches whole messages against.

    python3 tools/i18n_catalog.py                  how complete each table is
    python3 tools/i18n_catalog.py --missing de-DE  the strings de-DE lacks, as JSON, to translate
    python3 tools/i18n_catalog.py --stale de-DE    the strings de-DE has that nothing uses
    python3 tools/i18n_catalog.py --prune          take every table's unused strings out
"""

from __future__ import annotations

import ast
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "app" / "static"
LOCALES_DIR = STATIC / "locales"
PAGES = ["index.html", "logs.html"]
SCRIPTS = ["app.js", "rack.js", "pianoroll.js", "visualizer.js", "recorder.js", "sectionedit.js", "logs.html"]

# ------------------------------------------------------------------ the pages
INLINE = {"b", "strong", "i", "em", "code", "kbd", "br", "a", "small", "sup", "sub", "u", "s", "mark", "abbr"}
SKIP = {"script", "style", "textarea", "pre", "noscript", "template", "svg"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
ATTRS = ["title", "placeholder", "aria-label", "alt", "label", "data-tip"]
SPACE = re.compile(r"[ \t\n\r\f]+")


def squash(text: str) -> str:
    return SPACE.sub(" ", text).strip(" ")


def wordy(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]{2}", text))


def esc_text(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Node:
    def __init__(self, tag: str, attrs: dict, parent: "Node | None"):
        self.tag, self.attrs, self.parent, self.children = tag, attrs, parent, []


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.at = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs}, self.at)
        self.at.children.append(node)
        if tag not in VOID:
            self.at = node

    def handle_startendtag(self, tag, attrs):
        self.at.children.append(Node(tag, {k: (v or "") for k, v in attrs}, self.at))

    def handle_endtag(self, tag):
        node = self.at
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self.at = node.parent

    def handle_data(self, data):
        self.at.children.append(data)


def _skipped(node: Node) -> bool:
    return node.tag in SKIP or node.attrs.get("translate") == "no"


def _inline_only(node: Node) -> bool:
    return all(isinstance(c, str) or (c.tag in INLINE and not _skipped(c) and _inline_only(c)) for c in node.children)


def _serial(node: Node) -> str:
    out = ""
    for c in node.children:
        if isinstance(c, str):
            out += esc_text(c)
        elif c.tag == "br":
            out += "<br>"
        else:
            out += f"<{c.tag}>{_serial(c)}</{c.tag}>"
    return out


def page_strings(html: str) -> list[str]:
    tree = Tree()
    tree.feed(html)
    found: list[str] = []
    body = next((c for c in _walk(tree.root) if isinstance(c, Node) and c.tag == "body"), tree.root)

    def attrs(node: Node):
        for name in ATTRS:
            value = node.attrs.get(name)
            if value and wordy(value):
                found.append(squash(value))

    def visit(node: Node):
        if _skipped(node):
            return
        attrs(node)
        has_text = any(isinstance(c, str) and wordy(c) for c in node.children)
        has_element = any(isinstance(c, Node) for c in node.children)
        if has_text and has_element and _inline_only(node):
            found.append(squash(_serial(node)))
            for c in _walk(node):
                if isinstance(c, Node) and c is not node:
                    attrs(c)
            return
        for c in node.children:
            if isinstance(c, str):
                if wordy(c):
                    found.append(squash(c))
            else:
                visit(c)

    visit(body)
    return found


def _walk(node: Node):
    yield node
    for c in node.children:
        if isinstance(c, Node):
            yield from _walk(c)
        else:
            yield c


# ------------------------------------------------------------------ the scripts
def _js_string(src: str, at: int) -> tuple[str, int] | None:
    """The JavaScript string literal starting at src[at] (' or "), decoded, and where it ends."""
    quote = src[at]
    if quote not in "'\"":
        return None
    out, i = [], at + 1
    escapes = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}
    while i < len(src):
        ch = src[i]
        if ch == quote:
            return "".join(out), i + 1
        if ch == "\\":
            nxt = src[i + 1]
            if nxt == "u":
                if src[i + 2] == "{":
                    end = src.index("}", i)
                    out.append(chr(int(src[i + 3:end], 16)))
                    i = end + 1
                else:
                    out.append(chr(int(src[i + 2:i + 6], 16)))
                    i += 6
                continue
            if nxt == "x":
                out.append(chr(int(src[i + 2:i + 4], 16)))
                i += 4
                continue
            if nxt == "\n":
                i += 2
                continue
            out.append(escapes.get(nxt, nxt))
            i += 2
            continue
        if ch == "\n":
            return None
        out.append(ch)
        i += 1
    return None


def _skip_ws(src: str, i: int) -> int:
    while i < len(src) and src[i] in " \t\r\n":
        i += 1
    return i


def _after_first_arg(src: str, i: int) -> int | None:
    """From inside a call's parentheses, the index just past the comma that ends the first argument."""
    depth = 0
    while i < len(src):
        ch = src[i]
        if ch in "'\"":
            lit = _js_string(src, i)
            if not lit:
                return None
            i = lit[1]
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            if depth == 0:
                return None
            depth -= 1
        elif ch == "," and depth == 0:
            return i + 1
        i += 1
    return None


CALL = re.compile(r"(?<![\w.$])(?:I18N\.)?(t|tn)\(")


def plural_keys() -> set[str]:
    """The plural keys of tn(n, one, other): those whose translation may list a language's plural forms."""
    out = set()
    for name in SCRIPTS:
        found = script_strings((STATIC / name).read_text(encoding="utf-8"), plurals=True)[0]
        out.update(found)
    return out


def script_strings(src: str, plurals: bool = False) -> tuple[list[str], list[int]]:
    """The keys a script looks up, and the lines of any t() whose key is not written out.  With plurals,
    only tn()'s plural keys."""
    found, dynamic = [], []
    for m in CALL.finditer(src):
        i = _skip_ws(src, m.end())
        if m.group(1) == "t":
            lit = _js_string(src, i) if i < len(src) else None
            if lit and not plurals:
                found.append(lit[0])
            elif not lit:
                dynamic.append(src.count("\n", 0, m.start()) + 1)
            continue
        i = _after_first_arg(src, i)
        for form in range(2):
            i = _skip_ws(src, i or 0)
            lit = _js_string(src, i) if i else None
            if not lit:
                dynamic.append(src.count("\n", 0, m.start()) + 1)
                break
            if not plurals or form == 1:
                found.append(lit[0])
            i = _skip_ws(src, lit[1])
            if src[i] == ",":
                i += 1
    return found, dynamic


# ------------------------------------------------------------------ the server
MSG_KEYS = {"error", "message", "detail", "stage", "label", "note", "hint", "reason", "warning", "what",
            "consequence", "blocked", "help", "requires_note", "problem", "caveat", "summary"}
# Keys that hold words only in some modules: a storage area's name, a storage item's title.
MSG_KEYS_IN = {"storage.py": {"title", "name"}}
STAGE_CALLS = {"stage", "on_stage", "set_stage"}
# The language names stay as they are, each in its own language; the MCP server's text is read by an agent.
NOT_MESSAGES = {"locales.py", "mcp.py"}


def _name_of(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _name_of(node.func)
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        return re.sub(r"\W", "_", node.slice.value)
    return "value"


def _template(node: ast.AST) -> str | None:
    """A string, f-string or + of them as a key: values become {name}."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out, used = "", {}
        for part in node.values:
            if isinstance(part, ast.Constant):
                out += str(part.value)
            elif isinstance(part, ast.FormattedValue):
                name = _name_of(part.value) or "value"
                name = name if re.fullmatch(r"[A-Za-z_]\w*", name) else "value"
                base, k = name, 2
                while name in used and used[name] != ast.dump(part.value):
                    name = f"{base}{k}"
                    k += 1
                used[name] = ast.dump(part.value)
                out += "{" + name + "}"
        return out
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _template(node.left), _template(node.right)
        if left is None and right is None:
            return None
        return (left if left is not None else "{" + _name_of(node.left) + "}") + \
               (right if right is not None else "{" + _name_of(node.right) + "}")
    return None


def _message_like(text: str) -> bool:
    plain = re.sub(r"\{\w+\}", "", text).strip()
    if not re.search(r"[A-Za-z]{2}", plain):
        return False
    if re.fullmatch(r"\w*[a-z][A-Z]\w*|[A-Z]{2,}[a-z]\w*", plain) or len(plain) <= 2:   # a node's class, a note
        return False
    if re.fullmatch(r"[\w.\-/:]+", plain) and (re.search(r"[._/:\-\d]", plain) or re.fullmatch(r"[A-Z_]+", plain)):
        return False                                         # a path, a key, an id, a CONSTANT
    if plain.startswith(("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE ", "ALTER ", "PRAGMA ")):
        return False
    return True


def server_strings(app_dir: Path = ROOT / "app") -> list[str]:
    found: list[str] = []

    def add(node):
        text = _template(node) if node is not None else None
        if text is None and isinstance(node, ast.IfExp):
            add(node.body)
            add(node.orelse)
            return
        if text and _message_like(text):
            found.append(text)

    for path in sorted(app_dir.glob("*.py")):
        if path.name in NOT_MESSAGES:
            continue
        keys = MSG_KEYS | MSG_KEYS_IN.get(path.name, set())
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _name_of(node.func)
                if name == "HTTPException":
                    for arg in node.args[1:2]:
                        add(arg)
                    for kw in node.keywords:
                        if kw.arg == "detail":
                            add(kw.value)
                if name in STAGE_CALLS and node.args:
                    add(node.args[0])
                for kw in node.keywords:
                    if kw.arg in keys:
                        add(kw.value)
            elif isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    if isinstance(k, ast.Constant) and k.value in keys:
                        add(v)
                # a choice's words by its number, as the length cap's {240: "4 minutes", ...}
                numbered = [k for k in node.keys if k is not None]
                if numbered and all(isinstance(k, ast.Constant) and isinstance(k.value, int) for k in numbered):
                    for v in node.values:
                        add(v)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant) \
                            and target.slice.value in keys:
                        add(node.value)
                    if isinstance(target, ast.Name) and target.id.endswith("_LABELS") and isinstance(node.value, ast.Dict):
                        for v in node.value.values:
                            add(v)
            elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and node.exc.args:
                add(node.exc.args[0])
    return found


# ------------------------------------------------------------------ the whole
def catalog() -> dict[str, list[str]]:
    """Each string, in the order it is first met, with where it is used."""
    out: dict[str, list[str]] = {}

    def put(text: str, where: str):
        if text and wordy(text):
            out.setdefault(text, [])
            if where not in out[text]:
                out[text].append(where)

    for name in PAGES:
        for text in page_strings((STATIC / name).read_text(encoding="utf-8")):
            put(text, name)
    for name in SCRIPTS:
        for text in script_strings((STATIC / name).read_text(encoding="utf-8"))[0]:
            put(text, name)
    for text in server_strings():
        put(text, "server")
    return out


def dynamic_keys() -> dict[str, list[int]]:
    """Scripts' t() calls whose key is not a literal: a table cannot know them."""
    out = {}
    for name in SCRIPTS:
        lines = script_strings((STATIC / name).read_text(encoding="utf-8"))[1]
        if lines:
            out[name] = lines
    return out


def table_path(code: str) -> Path:
    return LOCALES_DIR / f"{code}.json"


def load_table(code: str) -> dict[str, str]:
    path = table_path(code)
    if not path.exists():
        return {}
    return {k: v for k, v in json.loads(path.read_text(encoding="utf-8")).items() if not k.startswith("@")}


def save_table(code: str, strings: dict[str, str], order: list[str] | None = None) -> None:
    """A table in the catalog's order, so its strings sit near their neighbours on the page."""
    order = order or list(catalog())
    rank = {k: i for i, k in enumerate(order)}
    keys = sorted(strings, key=lambda k: (rank.get(k, len(rank)), k))
    data = {"@locale": code}
    data.update({k: strings[k] for k in keys})
    table_path(code).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# en-US holds only what is spelt differently; the rest is the English as written.  A string with one of these
# British spellings needs an en-US entry.
US_SPELLINGS = re.compile(
    r"colour|behaviour|favourit|neighbour|flavour|honour|humour|centre|\bgrey|cancell|travell|modell|labell|levell|"
    r"catalogue|whilst|amongst|analys(e|ed|es|ing)\b|normalis|organis|recognis|summaris|optimis|customis|"
    r"visualis|synchronis|harmonis|quantis|initialis|finalis|prioritis|minimis|maximis|categoris|memoris|"
    r"authoris|realis|specialis|stabilis|randomis|tokenis|equalis|serialis|licence|\bmetre|programme\b|"
    r"judgement|artefact|ageing|utilis|sanitis|personalis|capitalis|emphasis(e|ed|es|ing)\b|apologis",
    re.IGNORECASE)


def us_candidates(keys) -> list[str]:
    return [k for k in keys if US_SPELLINGS.search(re.sub(r"<[^>]*>|\{\w+\}", "", k))]


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(ROOT))
    from app.locales import LOCALES, SOURCE
    keys = list(catalog())
    if len(argv) > 2 and argv[1] == "--missing":
        table = load_table(argv[2])
        wanted = us_candidates(keys) if argv[2] == "en-US" else keys
        print(json.dumps([k for k in wanted if k not in table], ensure_ascii=False, indent=1))
        return 0
    if len(argv) > 2 and argv[1] == "--stale":
        print(json.dumps([k for k in load_table(argv[2]) if k not in set(keys)], ensure_ascii=False, indent=1))
        return 0
    if len(argv) > 1 and argv[1] == "--prune":
        known = set(keys)
        for code in LOCALES:
            if code == SOURCE or not table_path(code).exists():
                continue
            table = load_table(code)
            save_table(code, {k: v for k, v in table.items() if k in known}, keys)
        return 0
    print(f"{len(keys)} strings")
    for code in LOCALES:
        if code == SOURCE:
            continue
        table = load_table(code)
        wanted = us_candidates(keys) if code == "en-US" else keys
        missing = sum(1 for k in wanted if k not in table)
        print(f"{code:7} {len(wanted) - missing:5} of {len(wanted)}")
    dyn = dynamic_keys()
    if dyn:
        print("t() without a written key:", dyn)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
