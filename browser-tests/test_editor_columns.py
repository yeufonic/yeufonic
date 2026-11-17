"""The editor's three columns: the bars between them widen one and narrow its neighbour, no column goes below its
least width, the widths are kept for the next time, a double-click puts the usual ones back, and in a narrow window,
where the columns stack, the bars are hidden."""
import pytest

pytest.importorskip("playwright.sync_api")

from helpers import open_new  # noqa: E402

WIDTHS = "() => Array.from(document.querySelectorAll('.ed-cols > .ed-col')).map(c => c.offsetWidth)"


def drag(page, index, dx):
    handle = page.locator(".ed-cols > .ed-col-handle").nth(index)
    box = handle.bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + 40
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + dx / 2, y)
    page.mouse.move(x + dx, y)
    page.mouse.up()
    page.wait_for_timeout(100)


def test_the_columns_can_be_widened_kept_and_put_back(page, app_server):
    page.evaluate("() => localStorage.removeItem('yue2.editorColumns')")
    open_new(page, "Song")
    page.click("#editor-max")
    usual = page.evaluate(WIDTHS)
    assert page.locator(".ed-cols > .ed-col-handle").count() == 2

    drag(page, 0, 150)                                   # the first column wider, the words column narrower
    wider = page.evaluate(WIDTHS)
    assert wider[0] > usual[0] + 100 and wider[1] < usual[1] - 100
    assert abs(wider[2] - usual[2]) < 3                 # the third is left alone
    assert page.evaluate("() => localStorage.getItem('yue2.editorColumns')")

    drag(page, 1, -2000)                                 # far past the end: the words column stops at its least width
    assert min(page.evaluate(WIDTHS)) >= 259

    page.reload()                                        # kept for the next time the editor opens
    open_new(page, "Song")
    kept = page.evaluate(WIDTHS)
    assert kept[1] < usual[1] - 100

    page.locator(".ed-cols > .ed-col-handle").nth(0).dblclick()
    back = page.evaluate(WIDTHS)
    assert all(abs(a - b) < 3 for a, b in zip(back, usual))
    assert page.evaluate("() => localStorage.getItem('yue2.editorColumns')") is None


def test_in_a_narrow_window_the_columns_stack_and_the_bars_hide(page, app_server):
    page.set_viewport_size({"width": 1000, "height": 900})
    open_new(page, "Song")
    page.wait_for_timeout(150)
    assert page.locator(".ed-cols > .ed-col-handle:visible").count() == 0
    page.set_viewport_size({"width": 1600, "height": 1000})
    page.wait_for_timeout(250)
    assert page.locator(".ed-cols > .ed-col-handle:visible").count() == 2
