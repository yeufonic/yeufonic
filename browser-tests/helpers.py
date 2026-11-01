"""Steps the tests share: what a person does to make a take, and waiting for the app to finish it."""
import json
import time
import urllib.request

WORDS = ("[verse]\nLights along the harbour wall\nA ship goes out into the fog\n\n"
         "[chorus]\nHold on, hold on\nThe tide will bring it home\n")


def api(app_server, path):
    with urllib.request.urlopen(app_server["url"] + path, timeout=10) as r:
        return json.loads(r.read())


def take(app_server, take_id):
    return api(app_server, f"/api/takes/{take_id}")


def wait_take(app_server, take_id, status="done", seconds=60):
    """Until the take reaches the status; fails with the take as it stands if it fails or never does."""
    deadline = time.time() + seconds
    last = None
    while time.time() < deadline:
        last = take(app_server, take_id)
        if last.get("status") == status:
            return last
        if last.get("status") == "failed" and status != "failed":
            raise AssertionError(f"the take failed: {last.get('error')}")
        time.sleep(0.5)
    raise AssertionError(f"the take did not become {status}: {last}")


def card(page, take_id):
    return page.locator(f'#takes article.take[data-id="{take_id}"]')


def new_take_id(page, before):
    """The id of the take that appears in the library, beside the ones there before."""
    page.wait_for_function("(before) => [...document.querySelectorAll('#takes article.take')]"
                           ".some(a => !before.includes(a.dataset.id))", arg=before, timeout=20000)
    return page.evaluate("(before) => [...document.querySelectorAll('#takes article.take')]"
                         ".map(a => a.dataset.id).find(id => !before.includes(id))", before)


def take_ids(page):
    return page.evaluate("() => [...document.querySelectorAll('#takes article.take')].map(a => a.dataset.id)")


def open_new(page, kind):
    """The + Song, + Cover or + Instrumental button at the top of the panel."""
    page.get_by_role("button", name=f"+ {kind}").first.click()
    page.wait_for_selector("#style", state="visible")


def make_song(page, app_server, style="bright indie pop, female vocal", words=WORDS):
    """A song from a style and words, as a person makes one: the plan is written and rendered in one go."""
    before = take_ids(page)
    open_new(page, "Song")
    page.fill("#style", style)
    page.fill("#lyrics", words)
    page.click("#create-song")
    take_id = new_take_id(page, before)
    return wait_take(app_server, take_id)


def confirm(page, text=None):
    """Answer the app's own confirm window, typing into it first when it asks for a name."""
    page.wait_for_selector("#confirm-modal:not(.hidden)")
    if text is not None:
        page.fill("#confirm-input", text)
    page.click("#confirm-ok")
    page.wait_for_selector("#confirm-modal", state="hidden")
