"""A new instrumental starts from the usual sections, not the last one's long list; the way its structure is given
(YuE2 decides, sections, timed) is kept like a setting."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import open_new  # noqa: E402


def test_a_new_instrumental_starts_from_the_usual_sections(page, app_server):
    open_new(page, "Instrumental")
    page.evaluate("""() => {
      STRUCTURE.kind = 'timed';
      STRUCTURE.sections = Array.from({ length: 23 }, () => ({ name: 'chorus', seconds: 25 }));
      paintStructure(); saveForm();
    }""")
    page.click("#editor-close")
    page.reload()
    open_new(page, "Instrumental")
    shape = page.evaluate("() => [STRUCTURE.kind, STRUCTURE.sections.map(s => s.name).join(',')]")
    assert shape == ["timed", "intro,verse,chorus,verse,chorus,bridge,chorus,outro"]
