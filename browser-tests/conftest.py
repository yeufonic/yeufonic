"""The app in a real browser, against a stand-in engine (fake_engine.py), with a library of its own.

One app and one engine serve the whole run, each test in a fresh browser context.  Every test fails if the page
logs a script error, or the app's log has a traceback.  Run them with browser-tests/run.sh.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
APP_PORT = int(os.environ.get("BROWSER_TESTS_APP_PORT", "8093"))
ENGINE_PORT = int(os.environ.get("BROWSER_TESTS_ENGINE_PORT", "8199"))
APP = f"http://127.0.0.1:{APP_PORT}"
ARTIFACTS = Path(os.environ.get("BROWSER_TESTS_ARTIFACTS", ROOT / "browser-tests" / "artifacts"))


def _wait(url: str, seconds: float = 60) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2).read()
            return
        except Exception:  # noqa: BLE001
            time.sleep(0.3)
    raise RuntimeError(f"{url} did not answer")


def _free(port: int) -> None:
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            raise RuntimeError(f"port {port} is in use: set BROWSER_TESTS_APP_PORT / BROWSER_TESTS_ENGINE_PORT")


@pytest.fixture(scope="session")
def app_server():
    """The engine stand-in and the app, from this checkout, with an empty data folder."""
    _free(APP_PORT)
    _free(ENGINE_PORT)
    data = Path(tempfile.mkdtemp(prefix="yeufonic-browser-"))
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    log = (ARTIFACTS / "app.log").open("w")
    engine = subprocess.Popen([sys.executable, str(ROOT / "browser-tests" / "fake_engine.py"), "--port", str(ENGINE_PORT)],
                              stdout=log, stderr=subprocess.STDOUT)
    env = dict(os.environ, DATA_DIR=str(data), ENGINE_URL=f"http://127.0.0.1:{ENGINE_PORT}",
               VERSION_FILE=str(ROOT / "VERSION"), ALLOWED_HOSTS="localhost,127.0.0.1",
               # Asked instead of yeufonic.com, and closed: the tests never talk to the internet.
               YEUFONIC_UPDATE_MANIFEST="http://127.0.0.1:9/updates.json",
               ENGINE_INPUT_DIR=str(data / "engine-input"), ENGINE_OUTPUT_DIR=str(data / "engine-output"),
               MODELS_DIR=str(data / "models"), TZ="UTC")
    for folder in ("engine-input", "engine-output", "models/loras"):
        (data / folder).mkdir(parents=True, exist_ok=True)
    app = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                            "--port", str(APP_PORT), "--no-access-log"], cwd=ROOT, env=env,
                           stdout=log, stderr=subprocess.STDOUT)
    try:
        _wait(f"http://127.0.0.1:{ENGINE_PORT}/system_stats")
        _wait(f"{APP}/api/health")
        # Online, with the engine's options read, before any test looks at the page.
        deadline = time.time() + 30
        while time.time() < deadline:
            state = json.loads(urllib.request.urlopen(f"{APP}/api/state", timeout=4).read())
            if state["engine"]["online"] and (state["engine"].get("compat") or {}).get("ok"):
                break
            time.sleep(0.5)
        yield {"url": APP, "data": data, "log": ARTIFACTS / "app.log", "engine": f"http://127.0.0.1:{ENGINE_PORT}"}
    finally:
        app.terminate()
        engine.terminate()
        for p in (app, engine):
            try:
                p.wait(10)
            except subprocess.TimeoutExpired:
                p.kill()
        log.close()
        shutil.rmtree(data, ignore_errors=True)


@pytest.fixture(scope="session")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        yield b
        b.close()


@pytest.fixture
def page(browser, app_server, request):
    """A fresh browser context on the app, failing the test on any script error the page logs."""
    # In UK English, the text as written in the page and the scripts, which the tests look for; a browser's own
    # language would otherwise choose the app's (US English, where the tests' browser says nothing else).
    context = browser.new_context(viewport={"width": 1600, "height": 1000}, locale="en-GB")
    page = context.new_page()
    page.set_default_timeout(15000)
    errors = []
    page.on("pageerror", lambda exc: errors.append(f"page error: {exc}"))
    page.on("console", lambda msg: errors.append(f"console error: {msg.text}") if msg.type == "error" else None)
    # A dialog would hang the page: none should come up, and one that does fails the test.
    page.on("dialog", lambda d: (errors.append(f"dialog: {d.message}"), d.dismiss()))
    log_from = app_server["log"].stat().st_size
    page.goto(app_server["url"] + "/")
    # The first state from the app has arrived, with the engine's options: the page is set up.
    page.wait_for_function("() => window.State && State.options && Object.keys(State.options).length > 0")
    yield page
    failed = getattr(request.node, "rep_call", None)
    if failed is not None and failed.failed:
        page.screenshot(path=str(ARTIFACTS / f"{request.node.name}.png"), full_page=True)
    context.close()
    with app_server["log"].open() as f:
        f.seek(log_from)
        app_log = f.read()
    problems = [line for line in app_log.splitlines() if "Traceback" in line or " ERROR " in line]
    allowed = [m.args[0] for m in request.node.iter_markers("console_allows")]
    errors = [e for e in errors if not any(a in e for a in allowed)]
    assert not errors, "\n".join(errors)
    assert not problems, "the app logged errors:\n" + app_log[-4000:]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        item.rep_call = report


def pytest_configure(config):
    config.addinivalue_line("markers", "console_allows(text): a console error the test causes on purpose")
