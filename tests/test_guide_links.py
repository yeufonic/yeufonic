"""Every link inside the guide to one of its own headings should land on one."""
import re
from pathlib import Path

GUIDE = Path(__file__).resolve().parent.parent / "app" / "static" / "guide.md"


def slug(text: str) -> str:
    """The same rule the guide page uses to give a heading its id."""
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", text.lower()))


def test_the_guides_own_links_all_land_on_a_heading():
    text = GUIDE.read_text(encoding="utf-8")
    headings = {slug(re.sub(r"[*`_]", "", m.group(1))) for m in re.finditer(r"^#{1,4}\s+(.+?)\s*$", text, re.M)}
    links = set(re.findall(r"\]\(#([a-z0-9-]+)\)", text))
    assert links, "the guide has links to its own sections"
    assert links <= headings, sorted(links - headings)


def test_the_chapter_on_writing_a_song_is_there_to_be_linked_to():
    text = GUIDE.read_text(encoding="utf-8")
    assert re.search(r"^## Writing a song from a prompt: every option$", text, re.M)
    assert slug("Writing a song from a prompt: every option") == "writing-a-song-from-a-prompt-every-option"
