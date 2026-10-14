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


STATIC = PAGE.parent


def test_the_editor_has_a_mastering_button_to_the_left_of_advanced():
    page = PAGE.read_text(encoding="utf-8")
    parser = Ancestors("ed-btn-mastering")
    parser.feed(page)
    assert parser.found is not None and parser.found[-1] == "editor"
    assert page.index('id="ed-btn-mastering"') < page.index('id="btn-advanced-toggle"') < page.index('id="ed-tabs"')
    assert "<span>Mastering</span>" in page
    css = (STATIC / "styles.css").read_text(encoding="utf-8")
    # one class is not enough to hide it (the pill's own display wins), and Advanced gives up the push to the right
    assert ".ed-master-btn.hidden { display: none; }" in css
    assert ".ed-master-btn:not(.hidden) + .ed-advanced-btn { margin-left: 0; }" in css


def test_the_button_is_lit_by_the_racks_own_test_and_the_rack_keeps_it_in_step():
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    paint = app_js[app_js.index("function paintEdMastering()"):app_js.index("function toggleEdMastering()")]
    assert "take.has_audio" in paint and "rack.hasActiveMastering(take.id)" in paint
    assert "$('ed-btn-mastering').addEventListener('click', toggleEdMastering)" in app_js
    rack = (STATIC / "rack.js").read_text(encoding="utf-8")
    cards = rack[rack.index("updateTakeCardsUI: function"):rack.index("openForTake: function")]
    assert "paintEdMastering()" in cards


def test_a_rack_opened_from_the_editor_stands_over_it_and_escape_closes_the_rack_first():
    css = (STATIC / "styles.css").read_text(encoding="utf-8")
    assert "body.rack-over-editor .rack-panel { z-index: 61; }" in css
    # windows opened over the editor still cover the rack, and the ones already above keep their own depth
    assert "body.rack-over-editor .modal:where(:not(#editor-modal)) { z-index: 62; }" in css
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    at = app_js.index("if (event.key === 'Escape' && typeof editorOpen === 'function' && editorOpen()) {")
    block = app_js[at:app_js.index("closeEditor();", at)]
    assert "event.rackClosed" in block and "window.Rack.toggle(false)" in block
    rack = (STATIC / "rack.js").read_text(encoding="utf-8")
    assert "e.rackClosed = true" in rack


def test_the_rack_opened_for_another_take_plays_it_only_when_a_take_was_playing():
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    hear = app_js[app_js.index("function hearForRack(take)"):app_js.index("function toggleEdMastering()")]
    # nothing sounding, or this take already: left alone
    assert "if (!audio || audio.paused || audio.ended || State.playing === take.id) { return; }" in hear
    # another take sounding: this one in its place; anything else that was sounding is stopped, as before
    assert "if (State.playing && take.has_audio) { playTake(take.id); }" in hear
    assert hear.index("playTake(take.id)") < hear.index("audio.pause()")
    # a card's button and the editor's both go through it, before the rack is opened
    card = app_js[app_js.index("if (act === 'mastering') {"):app_js.index("openDetails(takeById(id));")]
    assert card.index("hearForRack(targetTake)") < card.index("window.Rack.openForTake(targetTake)")
    editor = app_js[app_js.index("function toggleEdMastering()"):app_js.index("function paintEdTransport()")]
    assert editor.index("hearForRack(take)") < editor.index("rack.openForTake(take)")


def test_the_editor_has_the_pages_playback_keys():
    """The editor window, alone or with the mastering rack over it, has Space and the arrows for its own player
    whenever that player shows; any other window in front keeps them, and the letter keys are the main page's."""
    app_js = (STATIC / "app.js").read_text(encoding="utf-8")
    keys = app_js[app_js.index("var rackOverEditor = "):app_js.index("\nwire();")]
    assert "var inEditor = editorOpen() && document.querySelectorAll('.modal:not(.hidden)').length === 1;" in keys
    assert "if (inEditor && !rackOverEditor && (!$('ed-transport') || $('ed-transport').classList.contains('hidden'))) { return; }" in keys
    assert "if (!inEditor && document.querySelector('.modal:not(.hidden)')) { return; }" in keys
    assert "else if (!inEditor && takeKey(event)) { event.preventDefault(); }" in keys
    # play is the window's own there, for the take in the window, and the button last pressed lets go
    assert "$(inEditor && $('ed-btn-play') ? 'ed-btn-play' : 'btn-play').click();" in keys
    # typing is left alone, whether the focus or the key is aimed at a box
    guard = app_js[app_js.index("var aimed = "):app_js.index("var rackOverEditor = ")]
    assert "/^(INPUT|TEXTAREA|SELECT)$/.test(tag) || /^(INPUT|TEXTAREA|SELECT)$/.test(aimed)" in guard
    assert "if (tag === 'BUTTON') { focus.blur(); }" in keys
    for key in ("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"):
        assert keys.index("rackOverEditor") < keys.index(key)
    # the window's Mastering button does not keep the focus, or space and Enter would press it again
    editor = app_js[app_js.index("function toggleEdMastering()"):app_js.index("function paintEdTransport()")]
    assert "$('ed-btn-mastering').blur()" in editor
