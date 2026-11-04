"""The app in the user's language: the setting, the page it gives, and the string tables against what the
page shows (tools/i18n_catalog.py lists that)."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import i18n_catalog  # noqa: E402
from app import locales  # noqa: E402

TRANSLATED = [code for code in locales.LOCALES if code not in (locales.SOURCE, "en-US")]
PLACEHOLDER = re.compile(r"\{([A-Za-z_]\w*)\}")
TAG = re.compile(r"</?([a-z]+)>")


@pytest.fixture(scope="module")
def catalog():
    return i18n_catalog.catalog()


def boot(html: str) -> dict:
    found = re.search(r"window\.YEUFONIC_LOCALE = (\{.*?\});</script>", html)
    assert found, "the page carries no locale"
    return json.loads(found.group(1).replace("<\\/", "</").replace("<\\!--", "<!--"))


# ------------------------------------------------------------------ the setting
def test_the_language_setting_follows_the_browser_until_one_is_chosen(client):
    spec = next(s for s in client.get("/api/settings").json()["settings"] if s["key"] == "ui.language")
    assert spec["value"] == "auto"
    assert [o["value"] for o in spec["options"]] == ["auto", *locales.LOCALES]
    # each language by its own name, so someone who cannot read the page finds theirs
    names = {o["value"]: o["label"] for o in spec["options"]}
    assert names["de-DE"] == "Deutsch" and names["zh-TW"] == "繁體中文" and names["ru-RU"] == "Русский"


def test_a_language_can_be_chosen_and_nothing_else(client):
    assert client.put("/api/settings", json={"key": "ui.language", "value": "fr-FR"}).status_code == 200
    spec = next(s for s in client.get("/api/settings").json()["settings"] if s["key"] == "ui.language")
    assert spec["value"] == "fr-FR"
    assert client.put("/api/settings", json={"key": "ui.language", "value": "klingon"}).status_code == 400


def test_the_page_is_in_the_browsers_language(client):
    html = client.get("/", headers={"Accept-Language": "de-AT,de;q=0.9,en;q=0.5"}).text
    assert '<html lang="de-DE">' in html
    data = boot(html)
    assert data["code"] == "de-DE"
    assert data["strings"] == locales.table("de-DE")


def test_with_no_language_of_its_own_the_page_is_american_english(client):
    for header in (None, "", "tr-TR,pl;q=0.8", "*"):
        headers = {"Accept-Language": header} if header is not None else {}
        assert boot(client.get("/", headers=headers).text)["code"] == "en-US"


def test_a_chosen_language_wins_over_the_browsers(client):
    client.put("/api/settings", json={"key": "ui.language", "value": "pt-PT"})
    html = client.get("/", headers={"Accept-Language": "de-DE"}).text
    assert boot(html)["code"] == "pt-PT"
    assert '<html lang="pt-PT">' in html
    # the logs window follows it too
    assert boot(client.get("/logs").text)["code"] == "pt-PT"


def test_british_english_is_the_text_as_written(client):
    client.put("/api/settings", json={"key": "ui.language", "value": "en-GB"})
    assert boot(client.get("/").text) == {"code": "en-GB", "strings": {}}


@pytest.mark.parametrize("asked, given", [
    ("de", "de-DE"), ("de-CH", "de-DE"), ("en", "en-US"), ("en-AU", "en-GB"), ("en-GB", "en-GB"),
    ("zh", "zh-CN"), ("zh-SG", "zh-CN"), ("zh-HK", "zh-TW"), ("zh-Hant", "zh-TW"), ("zh-Hant-HK", "zh-TW"),
    ("zh-Hans-CN", "zh-CN"), ("es", "es-ES"), ("es-ES", "es-ES"), ("es-MX", "es-419"), ("es-419", "es-419"),
    ("pt", "pt-BR"), ("pt-BR", "pt-BR"), ("pt-PT", "pt-PT"), ("nl-BE", "nl-NL"), ("fr-CA", "fr-FR"),
    ("it-CH", "it-IT"), ("ru", "ru-RU"), ("ja", "ja-JP"), ("ko", "ko-KR"), ("ko-KP", "ko-KR"), ("tr", None), ("", None), ("*", None),
])
def test_a_browser_language_finds_its_table(asked, given):
    assert locales.match(asked) == given


def test_the_browsers_languages_are_taken_in_the_order_of_their_weights():
    assert locales.pick("tr;q=1, fr;q=0.4, it;q=0.8") == "it-IT"
    assert locales.pick("fr;q=0, nl") == "nl-NL"
    assert locales.pick(None) == "en-US"


def test_nothing_in_a_table_can_close_the_pages_script(tmp_path, monkeypatch):
    (tmp_path / "de-DE.json").write_text(json.dumps({"Bad": "</script><script>alert(1)</script>"}), encoding="utf-8")
    monkeypatch.setattr(locales, "LOCALES_DIR", tmp_path)
    locales._cache.clear()
    try:
        script = locales.boot_script("de-DE")
        assert script.count("</script>") == 1 and script.endswith("</script>")
        assert json.loads(script[len("<script>window.YEUFONIC_LOCALE = "):-len(";</script>")].replace("<\\/", "</"))["strings"]["Bad"]
    finally:
        locales._cache.clear()


# ------------------------------------------------------------------ the tables
def test_every_script_names_its_words(catalog):
    """A table can only hold a string written out where it is used: t(someVariable) would never be found."""
    assert i18n_catalog.dynamic_keys() == {}


@pytest.mark.parametrize("code", TRANSLATED)
def test_a_table_has_every_string_the_app_shows(catalog, code):
    table = i18n_catalog.load_table(code)
    missing = [key for key in catalog if key not in table]
    assert not missing, f"{code} lacks {len(missing)} strings, e.g. {missing[:5]} (tools/i18n_catalog.py --missing {code})"


@pytest.mark.parametrize("code", [c for c in locales.LOCALES if c != locales.SOURCE])
def test_a_table_holds_nothing_the_app_no_longer_shows(catalog, code):
    stale = [key for key in i18n_catalog.load_table(code) if key not in catalog]
    assert not stale, f"{code} has {len(stale)} strings nothing uses, e.g. {stale[:5]} (tools/i18n_catalog.py --prune)"


def test_american_english_has_every_british_spelling(catalog):
    table = i18n_catalog.load_table("en-US")
    wanted = i18n_catalog.us_candidates(catalog)
    assert wanted, "the catalog has no British spellings: the check has stopped finding them"
    missing = [key for key in wanted if key not in table]
    assert not missing, f"en-US lacks {missing[:5]}"
    same = [key for key, value in table.items() if key == value]
    assert not same, f"en-US repeats the English as written: {same[:5]}"


@pytest.mark.parametrize("code", [c for c in locales.LOCALES if c != locales.SOURCE])
def test_a_translation_keeps_its_values_and_markup(code):
    """Every {value} and every tag of the English, so nothing the app puts in is lost and no markup breaks;
    no quote or angle bracket the English did not have, since some strings sit inside an attribute."""
    problems = []
    for key, said in i18n_catalog.load_table(code).items():
        forms = said.split(" | ") if " | " in said else [said]
        for form in forms:
            if set(PLACEHOLDER.findall(form)) - set(PLACEHOLDER.findall(key)):
                problems.append(f"new value in {key!r}: {form!r}")
            if len(forms) == 1 and set(PLACEHOLDER.findall(form)) != set(PLACEHOLDER.findall(key)):
                problems.append(f"values differ in {key!r}: {form!r}")
            if Counter(TAG.findall(form)) != Counter(TAG.findall(key)):
                problems.append(f"markup differs in {key!r}: {form!r}")
            for mark in '"<>':
                if form.count(mark) > key.count(mark):
                    problems.append(f"{mark} added in {key!r}: {form!r}")
            if not form.strip():
                problems.append(f"empty: {key!r}")
    assert not problems, "\n".join(problems[:20])


PLURAL_FORMS = {"ru-RU": 4}   # one | few | many | other, as Intl.PluralRules gives them for Russian


@pytest.mark.parametrize("code", TRANSLATED)
def test_plural_forms_are_the_ones_the_language_has(code):
    """A ' | ' list of forms is only for a language with more than English's two, and has all of them."""
    for key, said in i18n_catalog.load_table(code).items():
        if " | " in said:
            assert code in PLURAL_FORMS, f"{code}: forms in {key!r}"
            assert len(said.split(" | ")) == PLURAL_FORMS[code], f"{code}: {key!r}"


def test_the_page_reads_its_text_as_the_catalog_does():
    """A block with only inline markup is one string, with its markup as bare tags; the attributes too."""
    found = i18n_catalog.page_strings(
        '<body><p class="x">Press <b class="k">Render</b> to begin.</p>'
        '<div title="A tip"><span id="n">3</span> takes <svg><text>No</text></svg></div>'
        '<textarea>Not this</textarea><span translate="no">Brand</span>'
        '<label><input type="checkbox"> Keep this tune</label></body>')
    assert found == ["Press <b>Render</b> to begin.", "A tip", "takes", "Keep this tune"]


def test_server_messages_are_patterns_of_their_values():
    keys = i18n_catalog.server_strings()
    # an f-string's values are named, so tr() can match the whole message and look its values up
    assert "Where stems are written. It must sit inside {DATA_DIR}." in keys
    assert "Output audio format" in keys
