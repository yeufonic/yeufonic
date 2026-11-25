"""Custom user themes stored in the app's settings table.

Each custom theme builds on one of the four built-in themes (studio, dark, light,
contrast) and overrides any subset of the colour tokens that the built-in themes
manage.  The browser derives companion RGB and alpha tokens (bars, glows,
waveforms, borders) automatically from these hex colours so every surface stays
coherent.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from typing import Any

from . import db

STORAGE_KEY = "appearance.custom_themes"

VALID_BASES = ("studio", "dark", "light", "contrast")
RESERVED_NAMES = {"studio", "dark", "light", "high contrast", "contrast", "system"}

MAX_THEMES = 50
MAX_NAME_LEN = 48

# Every editable hex colour token managed by the fixed themes in styles.css.
COLOR_TOKENS = (
    # Surfaces
    "--bg",
    "--bg-2",
    "--panel",
    "--card",
    "--card-2",
    "--card-3",
    # Text
    "--text",
    "--muted",
    "--text-strong",
    # Accents & transport
    "--accent-a",
    "--accent-b",
    "--play-bg",
    "--play-fg",
    # Origin colours (Song, Cover, Instrumental)
    "--song-a",
    "--song-b",
    "--cover-a",
    "--cover-b",
    "--inst-a",
    "--inst-b",
    # Status & highlights
    "--good",
    "--warn",
    "--bad",
    "--danger-text",
    "--info",
    "--lit-take",
    # Inputs & menus
    "--input-bg",
    "--input-border",
    "--menu-bg",
    "--menu-head-bg",
    "--menu-border",
    # Waveforms (body/outline alphas are derived from these base colours)
    "--wave-song",
    "--wave-cover",
    "--wave-inst",
    "--wave-default",
)
COLOR_TOKEN_SET = frozenset(COLOR_TOKENS)

# Surface & fill tokens that also support an optional 2-colour gradient.
GRADIENT_TOKENS = (
    "--bg",
    "--bg-2",
    "--panel",
    "--card",
    "--card-2",
    "--card-3",
    "--play-bg",
    "--input-bg",
    "--menu-bg",
    "--menu-head-bg",
)
GRADIENT_TOKEN_SET = frozenset(GRADIENT_TOKENS)
VALID_GRADIENT_DIRS = ("135deg", "180deg", "90deg", "radial")

_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def normalize_hex(value: Any) -> str:
    """Validate and normalise a hex colour string to lowercase #rrggbb."""
    if not isinstance(value, str):
        raise ValueError("Colour value must be a hex string like #7b5cff")
    s = value.strip()
    m = _HEX_RE.match(s)
    if not m:
        raise ValueError(f"Invalid hex colour: {value!r}")
    digits = m.group(1).lower()
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    return "#" + digits


def validate_colors(colors: Any) -> dict[str, str]:
    """Return a clean dict of valid {token: '#rrggbb'} overrides."""
    if colors is None:
        return {}
    if not isinstance(colors, dict):
        raise ValueError("colors must be an object mapping token names to hex values")
    out: dict[str, str] = {}
    for key, val in colors.items():
        if key not in COLOR_TOKEN_SET:
            continue
        if val is None or val == "":
            continue
        out[key] = normalize_hex(val)
    return out


def validate_gradients(gradients: Any) -> dict[str, dict[str, str]]:
    """Return a clean dict of valid {token: {'to': '#rrggbb', 'dir': '...'}} overrides."""
    if gradients is None:
        return {}
    if not isinstance(gradients, dict):
        raise ValueError("gradients must be an object mapping token names to gradient settings")
    out: dict[str, dict[str, str]] = {}
    for key, val in gradients.items():
        if key not in GRADIENT_TOKEN_SET or val is None:
            continue
        if not isinstance(val, dict):
            raise ValueError(f"Gradient for {key} must be an object with 'to' and 'dir'")
        to_raw = val.get("to")
        if not to_raw:
            continue
        to_hex = normalize_hex(to_raw)
        direction = str(val.get("dir") or "135deg").strip().lower()
        if direction not in VALID_GRADIENT_DIRS:
            raise ValueError(f"Gradient direction must be one of {', '.join(VALID_GRADIENT_DIRS)}")
        out[key] = {"to": to_hex, "dir": direction}
    return out


def validate_name(name: Any, existing: list[dict], exclude_id: str | None = None) -> str:
    if not isinstance(name, str):
        raise ValueError("Theme name is required")
    clean = " ".join(name.strip().split())
    if not clean:
        raise ValueError("Theme name is required")
    if len(clean) > MAX_NAME_LEN:
        raise ValueError(f"Theme name must be at most {MAX_NAME_LEN} characters")
    low = clean.lower()
    if low in RESERVED_NAMES:
        raise ValueError(f"'{clean}' is reserved for a built-in theme")
    for item in existing:
        if exclude_id and item.get("id") == exclude_id:
            continue
        if (item.get("name") or "").strip().lower() == low:
            raise ValueError(f"A custom theme named '{clean}' already exists")
    return clean


def validate_base(base: Any) -> str:
    b = (str(base or "studio")).strip().lower()
    if b not in VALID_BASES:
        raise ValueError(f"Base theme must be one of {', '.join(VALID_BASES)}")
    return b


def list_themes() -> list[dict[str, Any]]:
    raw = db.get_setting(STORAGE_KEY, None)
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    out: list[dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict) or not item.get("id") or not item.get("name"):
            continue
        base = item.get("base") if item.get("base") in VALID_BASES else "studio"
        try:
            colors = validate_colors(item.get("colors") or {})
        except ValueError:
            colors = {}
        try:
            gradients = validate_gradients(item.get("gradients") or {})
        except ValueError:
            gradients = {}
        out.append({
            "id": str(item["id"]),
            "name": str(item["name"]),
            "base": base,
            "colors": colors,
            "gradients": gradients,
            "updated_at": float(item.get("updated_at") or item.get("created_at") or 0),
        })
    return out


def _save_all(items: list[dict[str, Any]]) -> None:
    db.set_setting(STORAGE_KEY, json.dumps(items, ensure_ascii=False))


def get_theme(theme_id: str) -> dict[str, Any] | None:
    for item in list_themes():
        if item["id"] == theme_id:
            return item
    return None


def create_theme(
    name: str,
    base: str = "studio",
    colors: dict[str, str] | None = None,
    gradients: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    items = list_themes()
    if len(items) >= MAX_THEMES:
        raise ValueError(f"At most {MAX_THEMES} custom themes can be saved")
    clean_name = validate_name(name, items)
    clean_base = validate_base(base)
    clean_colors = validate_colors(colors or {})
    clean_gradients = validate_gradients(gradients or {})
    now = time.time()
    created = {
        "id": uuid.uuid4().hex[:10],
        "name": clean_name,
        "base": clean_base,
        "colors": clean_colors,
        "gradients": clean_gradients,
        "updated_at": now,
    }
    items.append(created)
    _save_all(items)
    return created


def update_theme(
    theme_id: str,
    name: str | None = None,
    base: str | None = None,
    colors: dict[str, str] | None = None,
    gradients: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    items = list_themes()
    target = next((item for item in items if item["id"] == theme_id), None)
    if not target:
        raise KeyError(theme_id)
    if name is not None:
        target["name"] = validate_name(name, items, exclude_id=theme_id)
    if base is not None:
        target["base"] = validate_base(base)
    if colors is not None:
        target["colors"] = validate_colors(colors)
    if gradients is not None:
        target["gradients"] = validate_gradients(gradients)
    target["updated_at"] = time.time()
    _save_all(items)
    return target


def delete_theme(theme_id: str) -> bool:
    items = list_themes()
    kept = [item for item in items if item["id"] != theme_id]
    if len(kept) == len(items):
        return False
    _save_all(kept)
    return True
