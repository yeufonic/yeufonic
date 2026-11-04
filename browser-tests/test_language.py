"""The app's words in another language: the page comes up in the browser's language with no script error, the
library's row and the editor in that language, and the user's own words left as they are."""
import json
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

LOCALES = Path(__file__).resolve().parents[1] / "app" / "static" / "locales"


def said(code, text):
    """What the table for the language gives for the English."""
    return json.loads((LOCALES / f"{code}.json").read_text(encoding="utf-8"))[text]


def open_in(browser, app_server, locale):
    context = browser.new_context(viewport={"width": 1400, "height": 900}, locale=locale)
    page = context.new_page()
    page.set_default_timeout(15000)
    errors = []
    page.on("pageerror", lambda exc: errors.append(f"page error: {exc}"))
    page.on("console", lambda msg: errors.append(f"console error: {msg.text}") if msg.type == "error" else None)
    page.on("dialog", lambda d: (errors.append(f"dialog: {d.message}"), d.dismiss()))
    page.goto(app_server["url"] + "/")
    page.wait_for_function("() => window.State && State.options && Object.keys(State.options).length > 0")
    return context, page, errors


@pytest.mark.parametrize("locale, lang", [("de-DE", "de-DE"), ("ru", "ru-RU"), ("zh-CN", "zh-CN"), ("zh-HK", "zh-TW"),
                                          ("ja", "ja-JP"), ("ko-KR", "ko-KR")])
def test_the_page_comes_up_in_the_browsers_language(browser, app_server, locale, lang):
    search, song = said(lang, "Search takes"), said(lang, "Song")
    context, page, errors = open_in(browser, app_server, locale)
    try:
        assert page.get_attribute("html", "lang") == lang
        assert page.get_attribute("#take-search", "placeholder") == search
        assert page.inner_text('.filters .kinds button[data-takekind="song"]').strip() == song
        # The wordmark is a name, not a word to translate.
        assert "eufonic" in page.inner_text("header")   # its Y is drawn
        # The editor opens and is in the language too, with nothing left unset by a script error.
        page.click('[data-new="song"]')
        page.wait_for_selector("#editor-modal:not(.hidden)", timeout=5000)
        assert page.inner_text('.modes .mode[data-mode="song"]').strip() == song
        assert not errors, "\n".join(errors)
    finally:
        context.close()


@pytest.mark.parametrize("locale", ["zh-CN", "ja-JP", "ko-KR"])
def test_a_cjk_label_stays_on_one_line(browser, app_server, locale):
    """Chinese and Japanese may break between any two characters: the row's labels keep to one line instead."""
    context, page, errors = open_in(browser, app_server, locale)
    try:
        for selector in ['.filters .kinds button[data-takekind="instrumental"]', ".filters .star-filter"]:
            box = page.locator(selector).bounding_box()
            assert box and box["height"] < 40, f"{selector} wrapped: {box}"
        assert not errors, "\n".join(errors)
    finally:
        context.close()
