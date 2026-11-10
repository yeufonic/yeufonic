"""An RVC model's loose files, chosen together, import as one voice with its index; one imported without its index
says so, and takes the index later."""
import pytest

pytest.importorskip("playwright.sync_api")

MODEL = b"PK\x03\x04" + b"weights" * 10        # torch.save writes a zip; the app checks no further
INDEX = b"IwFl" + b"\x00" * 40                # a faiss IVF-Flat index's tag


def _file(name, data):
    return {"name": name, "mimeType": "application/octet-stream", "buffer": data}


def _import(page, *files):
    with page.expect_file_chooser() as chooser:
        page.click("#voice-import")
    assert chooser.value.is_multiple()
    chooser.value.set_files(list(files))


def test_loose_rvc_files_import_and_an_index_comes_later(page):
    page.evaluate("() => openVoices()")
    page.wait_for_selector("#voice-import")
    assert page.get_attribute(".voice-sources a", "href") == "https://voice-models.com/"

    _import(page, _file("Paired.pth", MODEL), _file("Paired.index", INDEX))
    page.wait_for_selector("#voice-state[data-state='ready']")
    assert "Paired" in page.inner_text("#voices-modal")
    assert page.query_selector("#voice-add-index") is None

    page.evaluate("() => showVoiceList()")
    _import(page, _file("Alone.pth", MODEL))
    page.wait_for_selector("#voice-add-index")
    assert "no index" in page.inner_text(".voice-no-index")

    with page.expect_file_chooser() as chooser:
        page.click("#voice-add-index")
    chooser.value.set_files([_file("Alone.index", INDEX)])
    page.wait_for_selector("#voice-add-index", state="detached")
    page.wait_for_selector("#voice-state[data-state='ready']")
