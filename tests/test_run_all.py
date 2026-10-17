"""Run all: analyse, export and train a corpus one after the other, on the server,
so nobody has to wait for each step.  Songs whose analysis fails are left out and
named; a busy engine is waited for; a stop during the export lets it finish."""
import asyncio
import time

import pytest
from fastapi import HTTPException

from app import loras, main
from app.db import execute, one

REAL_SLEEP = asyncio.sleep


def a_corpus(failed=()):
    execute("""INSERT INTO identities(id, name, trigger_word, folder, consent, created_at)
               VALUES('c1', 'Tidewater', 'tide', '/x', 1, 0)""")
    for n, title in enumerate(("One", "Two", "Three")):
        state = "failed" if title in failed else "done"
        execute("""INSERT INTO identity_songs(id, identity_id, file, title, sha256, duration, include, position,
                                              vocals_state, score_state, lyrics_state, style_state)
                   VALUES(?, 'c1', ?, ?, ?, 100, 1, ?, 'done', 'done', ?, 'done')""",
                (f"s{n}", f"{title}.flac", title, f"h{n}", n, state))


@pytest.fixture
def chain(monkeypatch):
    calls = {"analyse": 0, "export": None, "train": []}

    async def analyse(identity_id):
        calls["analyse"] += 1
        return {"queued": 0}

    async def export(identity, view, chosen):
        calls["export"] = [song["title"] for song in chosen]
        return {}

    async def train(identity_id, body=None):
        calls["train"].append(body.previous)
        return {}
    import threading
    test_thread = threading.current_thread()
    monkeypatch.setattr(main, "analyse_identity", analyse)
    monkeypatch.setattr(main, "_export", export)
    monkeypatch.setattr(main, "train_identity", train)
    monkeypatch.setattr(main.asyncio, "sleep",
                        lambda s: REAL_SLEEP(0) if threading.current_thread() is test_thread else REAL_SLEEP(s))
    main.RUN_ALL.clear()
    return calls


def go(previous=None):
    identity = one("SELECT * FROM identities WHERE id = 'c1'")
    main.RUN_ALL["c1"] = {"stage": "analysing", "since": time.time(), "left_out": [], "error": None}
    asyncio.run(main._run_all(identity, previous))
    return main.RUN_ALL["c1"]


def test_it_analyses_exports_and_trains_in_turn(client, chain):
    a_corpus()
    run = go("keep")
    assert chain["analyse"] == 1 and chain["export"] == ["One", "Two", "Three"] and chain["train"] == ["keep"]
    assert run["stage"] == "training" and run["left_out"] == []


def test_a_song_whose_analysis_failed_is_left_out_and_named(client, chain):
    a_corpus(failed=("Two",))
    run = go()
    assert chain["export"] == ["One", "Three"] and run["left_out"] == ["Two"] and run["stage"] == "training"


def test_nothing_analysed_is_nothing_to_train_on(client, chain):
    a_corpus(failed=("One", "Two", "Three"))
    run = go()
    assert run["stage"] == "failed" and "nothing to train on" in run["error"]
    assert chain["export"] is None and not chain["train"]


def test_a_busy_engine_is_waited_for(client, chain, monkeypatch):
    a_corpus()
    answers = [HTTPException(409, "The engine is busy with a render. Wait for it to finish."),
               HTTPException(409, "Something is already queued for the engine. Wait for it, or stop it."), None]

    async def train(identity_id, body=None):
        answer = answers.pop(0)
        if answer:
            raise answer
        chain["train"].append(body.previous)
    monkeypatch.setattr(main, "train_identity", train)
    assert go()["stage"] == "training" and chain["train"] == [None] and not answers


def test_a_refusal_that_waiting_will_not_mend_fails_the_run(client, chain, monkeypatch):
    a_corpus()

    async def train(identity_id, body=None):
        raise HTTPException(400, "Export the training set first: there is nothing to train on.")
    monkeypatch.setattr(main, "train_identity", train)
    run = go()
    assert run["stage"] == "failed" and run["error"].startswith("Export the training set first")


def test_a_stop_during_the_export_lets_it_finish_then_stops(client, chain, monkeypatch):
    a_corpus()

    async def export(identity, view, chosen):
        await main._end_run_all("c1", "stopped")
        assert main.RUN_ALL["c1"]["stage"] == "exporting", "still writing the set"
        chain["export"] = [song["title"] for song in chosen]
    monkeypatch.setattr(main, "_export", export)
    run = go()
    assert chain["export"] and not chain["train"] and run["stage"] == "stopped"


def test_starting_asks_about_an_earlier_lora_first(client, chain, monkeypatch, tmp_path):
    a_corpus()
    (tmp_path / "tidewater_lora.safetensors").write_bytes(b"x")
    monkeypatch.setattr(loras, "folder", lambda: tmp_path)
    monkeypatch.setattr(main.config, "ENGINE_INPUT_DIR", tmp_path)
    got = client.post("/api/identities/c1/run-all", json={})
    assert got.status_code == 409 and "keep it or delete it" in got.json()["detail"]
    assert "c1" not in main.RUN_ALL


def test_it_does_not_start_while_a_lora_trains(client, chain, monkeypatch, tmp_path):
    a_corpus()
    monkeypatch.setattr(main.config, "ENGINE_INPUT_DIR", tmp_path)
    execute("""INSERT INTO lora_runs(id, identity_id, lora_name, steps, rank, state, started_at)
               VALUES('r1', 'c9', 'other_lora', 500, 64, 'running', ?)""", (time.time(),))
    assert client.post("/api/identities/c1/run-all", json={}).status_code == 409
