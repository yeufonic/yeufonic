"""The app's words in the user's language.

The page's text is English as written (British: ``en-GB``).  Each other locale has a string table,
``app/static/locales/<code>.json``, keyed by that English: the scripts look their words up with ``t()``,
the page's own text is looked up once as it loads, and a message from the server is looked up where the
page shows it (``tr()`` in ``i18n.js``), so the server goes on writing English.  ``en-US`` is the default
and holds only the words spelt differently there.

The page needs its words before it paints, so the table goes into the page itself (``localise_page``):
the language comes from the ``ui.language`` setting or, left to follow the browser, from the languages
the browser asks for, which are the ones ``navigator.languages`` lists.
"""

from __future__ import annotations

import json
from pathlib import Path

LOCALES_DIR = Path(__file__).parent / "static" / "locales"

# The language the page's words are written in: it has no table.
SOURCE = "en-GB"
DEFAULT = "en-US"

# Each language by its own name, never translated: someone who cannot read the page finds theirs.
LOCALES: dict[str, str] = {
    "en-US": "English (US)",
    "en-GB": "English (UK)",
    "zh-CN": "简体中文",
    "zh-TW": "繁體中文",
    "de-DE": "Deutsch",
    "nl-NL": "Nederlands",
    "fr-FR": "Français",
    "it-IT": "Italiano",
    "ru-RU": "Русский",
    "es-ES": "Español (España)",
    "es-419": "Español (Latinoamérica)",
    "pt-BR": "Português (Brasil)",
    "pt-PT": "Português (Portugal)",
}

# A browser language with no exact match, by its language alone.  Chinese goes by script: Hong Kong
# and Macau read Traditional, as Taiwan does.  Spanish of any country but Spain is the Latin American table;
# Portuguese of any country but Portugal is the Brazilian.
_BY_LANGUAGE = {"en": "en-US", "zh": "zh-CN", "de": "de-DE", "nl": "nl-NL", "fr": "fr-FR", "it": "it-IT",
                "ru": "ru-RU", "es": "es-ES", "pt": "pt-BR"}
_ALIASES = {"zh-hk": "zh-TW", "zh-mo": "zh-TW", "zh-hant": "zh-TW", "zh-hans": "zh-CN", "zh-sg": "zh-CN",
            "en-au": "en-GB", "en-nz": "en-GB", "en-ie": "en-GB", "en-za": "en-GB", "en-in": "en-GB"}

_cache: dict[str, tuple[float, dict]] = {}


def match(tag: str) -> str | None:
    """The locale for one language tag ("de-AT", "zh-Hant-HK", "pt"), or None."""
    tag = (tag or "").strip().replace("_", "-")
    if not tag or tag == "*":
        return None
    lower = tag.lower()
    for code in LOCALES:
        if code.lower() == lower:
            return code
    parts = lower.split("-")
    if parts[0] == "zh":
        if "hant" in parts or any(p in ("tw", "hk", "mo") for p in parts[1:]):
            return "zh-TW"
        return "zh-CN"
    if len(parts) > 1 and f"{parts[0]}-{parts[-1]}" in _ALIASES:
        return _ALIASES[f"{parts[0]}-{parts[-1]}"]
    if parts[0] == "es" and len(parts) > 1 and parts[-1] != "es":
        return "es-419"
    if parts[0] == "pt" and len(parts) > 1 and parts[-1] == "pt":
        return "pt-PT"
    return _BY_LANGUAGE.get(parts[0])


def pick(accept_language: str | None) -> str:
    """The best locale for a browser's Accept-Language, taking its languages in the order of their weights."""
    ranked = []
    for index, item in enumerate((accept_language or "").split(",")):
        tag, _, params = item.strip().partition(";")
        weight = 1.0
        for param in params.split(";"):
            name, _, value = param.strip().partition("=")
            if name == "q":
                try:
                    weight = float(value)
                except ValueError:
                    weight = 0.0
        if tag and weight > 0:
            ranked.append((-weight, index, tag))
    for _, _, tag in sorted(ranked):
        found = match(tag)
        if found:
            return found
    return DEFAULT


def resolve(setting: str | None, accept_language: str | None) -> str:
    """The locale a page is shown in: the one chosen in Settings, or the browser's."""
    if setting in LOCALES:
        return setting
    return pick(accept_language)


def table(code: str) -> dict[str, str]:
    """A locale's strings, English to its own; empty for the English the page is written in."""
    if code == SOURCE or code not in LOCALES:
        return {}
    path = LOCALES_DIR / f"{code}.json"
    try:
        stamp = path.stat().st_mtime
    except OSError:
        return {}
    held = _cache.get(code)
    if held and held[0] == stamp:
        return held[1]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    strings = {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str) and not k.startswith("@")}
    _cache[code] = (stamp, strings)
    return strings


def boot_script(code: str) -> str:
    """The locale and its table as a script for the page's head, before any of its own scripts run."""
    payload = json.dumps({"code": code, "strings": table(code)}, ensure_ascii=False, separators=(",", ":"))
    # Nothing in a string may close the script early.
    payload = payload.replace("</", "<\\/").replace("<!--", "<\\!--")
    return f"<script>window.YEUFONIC_LOCALE = {payload};</script>"


def localise_page(html: str, code: str) -> str:
    """A page with its language set and the locale's table in its head.  ``<html lang>`` lets the browser
    pick the right forms of Chinese characters, and its hyphenation."""
    html = html.replace('<html lang="en">', f'<html lang="{code}">', 1)
    return html.replace("<!--{{LOCALE}}-->", boot_script(code), 1)
