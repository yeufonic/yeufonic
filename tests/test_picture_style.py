"""Make a new picture with a new prompt: custom art styles without Hipgnosis leakage, direct per-take prompts,
and Settings' art.prompt_mode (prefix vs replace)."""
import asyncio
import io
import struct
import zlib

from app import artwork, jobs
from app.db import set_setting
from conftest import make_take


def _tiny_png() -> bytes:
    """Minimal 2x2 non-white RGBA PNG so artwork.cut_out and keep succeed offline."""
    raw = b"".join(b"\x00" + b"\x20\x40\x60\xff" * 2 for _ in range(2))
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6))
            + chunk(b"IEND", b""))


def test_a_style_typed_for_one_picture_replaces_settings_for_that_take_only(client, monkeypatch):
    monkeypatch.setattr(artwork, "words_by_engine", lambda: True)    # waits in the GPU lane: nothing starts here
    set_setting("art.style", "pastel watercolours")
    take, other = make_take(title="Copper Fields"), make_take(title="Glass Harbour")
    jobs.ART_WAITING.clear()
    jobs.start_art(take["id"], "  bold linocut, two colours  ")
    assert artwork.art_style(take["id"]) == "bold linocut, two colours"
    assert artwork.art_style(other["id"]) == "pastel watercolours"
    req_custom = artwork.description_request(take)
    assert "Album art style: bold linocut, two colours" in req_custom
    # Custom styles must NOT leak the hardcoded Hipgnosis everyday-object brief (#81)
    assert artwork.PROMPT_BRIEF not in req_custom
    assert artwork.CUSTOM_STYLE_BRIEF in req_custom
    assert "Hipgnosis" not in req_custom
    assert "in this style: bold linocut, two colours" in artwork.take_description(take, scene="a lighthouse")
    assert "Hipgnosis" in artwork.take_description(other, scene="a lighthouse")
    assert artwork.info(take["id"])["style"] == "bold linocut, two colours"
    # The take's next picture without one goes back to Settings'.
    jobs.start_art(take["id"])
    assert artwork.art_style(take["id"]) == "pastel watercolours"
    assert artwork.info(take["id"])["style"] == "pastel watercolours"
    jobs.ART_WAITING.clear()
    artwork.STATE.clear()


def test_custom_settings_art_style_suppresses_hipgnosis_brief_and_sleeve_wear(client, monkeypatch):
    """Changing Take pictures: art style in Settings removes the hidden Hipgnosis PROMPT_BRIEF and
    ring-wear injection, while leaving the default Hipgnosis behavior unchanged when empty/default."""
    take = make_take(title="Midnight Riff", lyrics="Playing in the fog", seed=1)
    default_req = artwork.description_request(take)
    assert artwork.PROMPT_BRIEF in default_req
    assert artwork.is_default_style(take["id"]) is True

    set_setting("art.style", "Cinematic 35mm film still of a guitarist in twilight fog")
    custom_req = artwork.description_request(take)
    assert artwork.is_default_style(take["id"]) is False
    assert artwork.PROMPT_BRIEF not in custom_req
    assert artwork.CUSTOM_STYLE_BRIEF in custom_req
    assert "Hipgnosis" not in custom_req

    # Even on a well-worn seed, custom art.style skips KLEIN_WORN sleeve wear
    monkeypatch.setattr(artwork, "describer", lambda: "external")
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    monkeypatch.setattr(artwork, "is_well_worn", lambda t=None: True)
    drawn = []

    async def fake_describe(record, *args):
        return "A guitarist under twilight fog."

    async def fake_draw(take_id, description, title="", as_given=False):
        drawn.append((description, as_given))
        return _tiny_png()

    monkeypatch.setattr(artwork, "describe_external", fake_describe)
    monkeypatch.setattr(jobs, "_draw_on_engine", fake_draw)
    asyncio.run(jobs.run_art(take["id"]))
    assert drawn == [("A guitarist under twilight fog.", True)]
    assert artwork.KLEIN_WORN not in drawn[0][0]


def test_direct_prompt_on_take_card_skips_llm_and_settings(client, monkeypatch):
    """Make a new picture with a new prompt (direct=True) sends the prompt verbatim straight to the drawer,
    ignoring the LLM, art.style, art.prompt, and sleeve wear."""
    take = make_take(title="Ghost Sky", lyrics="Old chair by the sea", seed=1)
    set_setting("art.prompt", "unrelated prefix")
    monkeypatch.setattr(artwork, "describer", lambda: "gemma")
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    monkeypatch.setattr(artwork, "is_well_worn", lambda t=None: True)
    llm_called, drawn = [], []

    async def fail_if_llm(*args, **kwargs):
        llm_called.append(args)
        raise AssertionError("LLM must not be called for a direct prompt")

    async def fake_draw(take_id, description, title="", as_given=False):
        drawn.append((description, as_given))
        return _tiny_png()

    monkeypatch.setattr(jobs, "_run_graph", fail_if_llm)
    monkeypatch.setattr(jobs, "_draw_on_engine", fake_draw)
    jobs.start_art(take["id"], "Cinematic medium shot of a guitarist in twilight fog", direct=True)
    jobs.ART_WAITING.clear()
    asyncio.run(jobs.run_art(take["id"], on_gpu=True))
    assert not llm_called
    assert drawn == [("Cinematic medium shot of a guitarist in twilight fog", True)]
    assert "Described by your prompt" in (artwork.info(take["id"])["words"] or "")
    artwork.DIRECT_FOR.pop(take["id"], None)


def test_settings_own_prompt_replace_mode_skips_llm_and_art_style(client, monkeypatch):
    """When art.prompt_mode is 'replace' and art.prompt is set, Settings' own prompt is drawn directly
    without calling the LLM or layering art.style behind it."""
    take = make_take(title="Stage Lights", lyrics="A wooden boat", seed=1)
    set_setting("art.prompt", "Neon rain on a Tokyo alley, 35mm film")
    set_setting("art.prompt_mode", "replace")
    assert artwork.own_prompt_replaces() is True

    monkeypatch.setattr(artwork, "describer", lambda: "external")
    monkeypatch.setattr(artwork, "drawer", lambda: "local")
    monkeypatch.setattr(artwork, "is_well_worn", lambda t=None: True)
    drawn = []

    async def fail_llm(*args, **kwargs):
        raise AssertionError("LLM must not be called when art.prompt_mode is replace")

    async def fake_draw(take_id, description, title="", as_given=False):
        drawn.append((description, as_given))
        return _tiny_png()

    monkeypatch.setattr(artwork, "describe_external", fail_llm)
    monkeypatch.setattr(jobs, "_draw_on_engine", fake_draw)
    asyncio.run(jobs.run_art(take["id"]))
    assert drawn == [("Neon rain on a Tokyo alley, 35mm film", True)]
    assert "Described by your own prompt" in (artwork.info(take["id"])["words"] or "")


def test_the_route_takes_a_style_for_one_picture(client, monkeypatch):
    asked = []
    monkeypatch.setattr(jobs, "start_art", lambda take_id, style=None, direct=False: asked.append((take_id, style, direct)))
    monkeypatch.setattr(artwork, "drawing_problem", lambda: None)
    take = make_take(title="Copper Fields")
    assert client.post(f"/api/takes/{take['id']}/art").status_code == 200
    assert client.post(f"/api/takes/{take['id']}/art", json={"style": "ink and wash"}).status_code == 200
    assert client.post(f"/api/takes/{take['id']}/art", json={"style": "a neon fox", "direct": True}).status_code == 200
    assert asked == [(take["id"], None, False), (take["id"], "ink and wash", False), (take["id"], "a neon fox", True)]
    assert client.post(f"/api/takes/{take['id']}/art", json={"style": "x" * 4001}).status_code == 422


def test_visualizer_picture_button_exposes_full_view_options():
    """Clicking the visualizer's picture button opens a menu with the same three options as full view,
    and mounts both the menu and prompt dialog inside the visualizer/fullscreen host."""
    from pathlib import Path
    static = Path(__file__).resolve().parent.parent / "app" / "static"
    vis_js = (static / "visualizer.js").read_text(encoding="utf-8")
    app_js = (static / "app.js").read_text(encoding="utf-8")
    css = (static / "styles.css").read_text(encoding="utf-8")

    # Visualizer button opens the menu instead of blindly regenerating
    assert "self.togglePictureMenu();" in vis_js
    assert "renderPictureMenu:" in vis_js
    assert "pictureMenuAction:" in vis_js
    assert "clearArtwork:" in vis_js
    for kind, label in (
        ("make", "Make a new picture"),
        ("make-own", "Make a new picture with a new prompt"),
        ("plain", "Use the default background"),
    ):
        assert f"kind: '{kind}'" in vis_js
        assert f"t('{label}')" in vis_js

    # Prompt modal mounts in fullscreen / visualizer host so visualizer-open doesn't hide it
    assert "document.fullscreenElement ||" in app_js
    assert "window.Visualizer && window.Visualizer.isOpen && $('visualizer-modal')" in app_js
    # Escape closes picstyle-modal or vis-picture-menu before closing the visualizer
    esc_picstyle = app_js.index("event.key === 'Escape' && $('picstyle-modal')")
    esc_menu = app_js.index("event.key === 'Escape' && $('vis-picture-menu')")
    esc_vis = app_js.index("event.key === 'Escape' && window.Visualizer && window.Visualizer.isOpen")
    assert esc_picstyle < esc_menu < esc_vis
    # Styles layer menu and prompt dialog cleanly above the visualizer
    assert ".vis-picture-menu {" in css
    assert ".modal.picstyle-modal { z-index: 980; user-select: text; }" in css
