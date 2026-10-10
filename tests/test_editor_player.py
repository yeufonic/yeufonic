"""The editor's player belongs to every take, so it must not sit inside a field that one mode hides.

The lyrics field is hidden for an instrumental (it shows the structure instead), and the structure field is hidden for
a song or a cover. The player used to live inside the lyrics field, so an instrumental's editor had no playback controls."""
from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "app" / "static" / "index.html"


class Ancestors(HTMLParser):
    def __init__(self, target):
        super().__init__()
        self.target, self.stack, self.found = target, [], None

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "img", "input", "meta", "link", "hr", "path"):
            return
        attrs = dict(attrs)
        if attrs.get("id") == self.target:
            self.found = [i for i in self.stack if i]
        self.stack.append(attrs.get("id"))

    def handle_endtag(self, tag):
        if tag not in ("br", "img", "input", "meta", "link", "hr", "path") and self.stack:
            self.stack.pop()


def test_the_editors_player_is_not_inside_a_field_that_a_mode_hides():
    parser = Ancestors("ed-transport")
    parser.feed(PAGE.read_text(encoding="utf-8"))
    assert parser.found is not None, "the editor's player is missing from the page"
    assert "lyrics-field" not in parser.found and "structure-field" not in parser.found


def test_editor_does_not_close_on_backdrop_click():
    app_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "app.js").read_text(encoding="utf-8")
    assert "backdropClick(event, $('editor-modal'))" not in app_js
