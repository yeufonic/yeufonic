"""The guide is a page in the app, so it has to be there when the app is."""
import re
from pathlib import Path

import pytest

GUIDE = Path(__file__).resolve().parent.parent / "app" / "static" / "guide.md"


def test_the_guide_is_served(client):
    r = client.get("/guide", headers={"Accept-Language": "en-GB"})
    assert r.status_code == 200
    assert "/static/guide.md" in r.text, "the page has to fetch the markdown it renders"
    assert "{{VERSION}}" not in r.text, "the version has to be stamped, or caching lies"


def test_the_markdown_ships_with_the_app(client):
    """It lives under app/, not docs/, because only app/ is copied into the image."""
    r = client.get("/static/guide.md")
    assert r.status_code == 200
    assert r.text.startswith("# Yeufonic")


def test_the_renderer_is_vendored(client):
    assert client.get("/static/marked.min.js").status_code == 200


def test_every_feature_has_a_section():
    """A guide that quietly stops covering things is worse than no guide, so the
    headings are pinned to the features they describe."""
    text = GUIDE.read_text(encoding="utf-8")
    headings = set(re.findall(r"^#{2,3} (.+)$", text, re.M))
    for wanted in ("Your first song", "The Piano Roll", "Harmony", "Rendering", "Covering a recording",
                   "Instrumentals", "Voices", "Corpora", "Style LoRAs", "Stems",
                   "The library", "Settings", "When something is wrong"):
        assert any(wanted in head for head in headings), f"the guide says nothing about {wanted}"


def test_the_guide_does_not_promise_what_is_not_built():
    text = GUIDE.read_text(encoding="utf-8").lower()
    for unbuilt in ("mixing desk", "timeline editor"):
        assert unbuilt not in text, f"the guide describes {unbuilt}, which is not in the app"


def test_the_guide_says_how_to_switch_training_off():
    """On by default, so the guide says how to take it out rather than how to put it in."""
    text = GUIDE.read_text(encoding="utf-8")
    assert "TRAINING_ENABLED=0" in text, "the app half"
    assert "WITH_TRAINER=0" in text, "and the engine half"
    training_section = re.search(r"## Corpora and training a LoRA.*?(?=## |\Z)", text, re.S)
    assert training_section and "experimental" not in training_section.group(0).lower()


def test_the_guide_names_the_corpus_buttons():
    """The walkthrough follows the buttons, so it has to use their names."""
    text = GUIDE.read_text(encoding="utf-8")
    for button in ("Scan the folder", "Analyse", "Export training set", "Train a LoRA", "Install a LoRA"):
        assert button in text, f"the guide does not name {button}"


# ---- The guide in other languages: app/static/guides/<code>.md, one file per locale.

GUIDES = GUIDE.parent / "guides"
TRANSLATIONS = sorted(GUIDES.glob("*.md")) if GUIDES.is_dir() else []
HEADING = re.compile(r"^(#{2,4}) (.+?)\s*$", re.M)
ANCHOR = re.compile(r"\s*\{#([A-Za-z0-9_-]+)\}\s*$")
FENCE = re.compile(r"^```", re.M)


def slug(text):
    """As guide.html makes an anchor from a heading."""
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", text.lower()))


def anchors(text):
    """Each h2, h3 and h4 as (level, anchor), the given {#anchor} where there is one."""
    found = []
    for level, head in HEADING.findall(text):
        given = ANCHOR.search(head)
        found.append((level, given.group(1) if given else slug(head)))
    return found


def test_a_language_with_a_guide_of_its_own_gets_it(client):
    for path in TRANSLATIONS:
        r = client.get("/guide", headers={"Accept-Language": path.stem})
        assert f"/static/guides/{path.stem}.md" in r.text, path.stem
        assert client.get(f"/static/guides/{path.stem}.md").status_code == 200


def test_the_english_links_only_to_sections_it_has():
    text = GUIDE.read_text(encoding="utf-8")
    have = {anchor for _, anchor in anchors(text)}
    dead = [target for target in re.findall(r"\]\(#([^)]+)\)", text) if target not in have]
    assert not dead, f"the guide links to {dead}"


def test_british_english_reads_the_guide_as_written(client):
    """en-GB has no translated guide: it is guide.md itself (en-AU resolves to en-GB)."""
    r = client.get("/guide", headers={"Accept-Language": "en-AU"})
    assert "/static/guide.md" in r.text and "/static/guides/" not in r.text


def test_an_unsupported_language_gets_the_default_guide(client):
    """Turkish has no table, so the page and the guide are the default language's (en-US)."""
    r = client.get("/guide", headers={"Accept-Language": "tr-TR"})
    assert "/static/guides/en-US.md" in r.text


@pytest.mark.parametrize("path", TRANSLATIONS, ids=[p.stem for p in TRANSLATIONS])
def test_a_translation_has_the_english_sections_and_anchors(path):
    """The same chapters in the same order, each under the English heading's anchor, so a link into the guide
    (its own, or the README's) lands on the same section in every language."""
    english = anchors(GUIDE.read_text(encoding="utf-8"))
    assert anchors(path.read_text(encoding="utf-8")) == english


@pytest.mark.parametrize("path", TRANSLATIONS, ids=[p.stem for p in TRANSLATIONS])
def test_a_translation_links_only_to_sections_it_has(path):
    text = path.read_text(encoding="utf-8")
    have = {anchor for _, anchor in anchors(text)}
    dead = [target for target in re.findall(r"\]\(#([^)]+)\)", text) if target not in have]
    assert not dead, f"{path.stem} links to {dead}"


@pytest.mark.parametrize("path", TRANSLATIONS, ids=[p.stem for p in TRANSLATIONS])
def test_a_translation_keeps_the_code_blocks(path):
    """Commands and settings are typed as written: a translation has every fenced block of the English."""
    english = re.findall(r"^```.*?^```", GUIDE.read_text(encoding="utf-8"), re.M | re.S)
    theirs = re.findall(r"^```.*?^```", path.read_text(encoding="utf-8"), re.M | re.S)
    assert theirs == english
