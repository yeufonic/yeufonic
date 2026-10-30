"""The engine is asked to unload its models when the GPU's line runs dry: on its own where the
GPU shares the computer's memory (a Mac), and as UNLOAD_WHEN_IDLE says."""
import asyncio

import pytest

from app import config, jobs


@pytest.fixture
def idle(monkeypatch):
    while not jobs.QUEUE.empty():
        jobs.QUEUE.get_nowait()
    monkeypatch.setattr(jobs, "ART_WAITING", jobs.collections.deque())


def gpu_named(monkeypatch, name):
    monkeypatch.setattr(jobs.ENGINE, "gpu", lambda: {"name": name})


@pytest.mark.parametrize("setting, gpu, wanted", [
    ("auto", "mps", True),                                # a Mac
    ("auto", "cuda:0 NVIDIA GeForce RTX 4070", False),    # a card with memory of its own
    ("auto", None, False),                                # the engine not read yet
    ("1", "cuda:0 NVIDIA GeForce RTX 4070", True),
    ("0", "mps", False),
])
def test_when_the_line_is_empty_it_follows_the_setting(monkeypatch, idle, setting, gpu, wanted):
    monkeypatch.setattr(config, "UNLOAD_WHEN_IDLE", setting)
    gpu_named(monkeypatch, gpu)
    assert jobs.unload_when_idle() is wanted


def test_not_while_work_is_waiting(monkeypatch, idle):
    # A plan's render is queued before the plan's job ends: the two keep their models.
    monkeypatch.setattr(config, "UNLOAD_WHEN_IDLE", "1")
    gpu_named(monkeypatch, "mps")
    jobs.QUEUE.put_nowait({"kind": "render", "id": "x"})
    try:
        assert jobs.unload_when_idle() is False
    finally:
        jobs.QUEUE.get_nowait()
    jobs.ART_WAITING.append("take")
    try:
        assert jobs.unload_when_idle() is False
    finally:
        jobs.ART_WAITING.clear()


def test_the_worker_unloads_after_the_last_job(monkeypatch, idle):
    monkeypatch.setattr(config, "UNLOAD_WHEN_IDLE", "auto")
    gpu_named(monkeypatch, "mps")
    freed, ran = [], []

    async def free():
        freed.append(True)

    async def run_job(kind, take_id):
        ran.append(take_id)

    async def no_wait():
        return None

    async def go():
        monkeypatch.setattr(jobs.ENGINE, "free", free)
        monkeypatch.setattr(jobs, "run_job", run_job)
        monkeypatch.setattr(jobs, "wait_for_engine", no_wait)
        jobs.QUEUE.put_nowait({"kind": "render", "id": "a"})
        jobs.QUEUE.put_nowait({"kind": "render", "id": "b"})
        task = asyncio.create_task(jobs.worker())
        for _ in range(100):
            await asyncio.sleep(0.01)
            if freed:
                break
        task.cancel()
    asyncio.run(go())
    assert ran == ["a", "b"] and freed == [True]       # once, after b, not between a and b


def test_after_a_picture_even_with_songs_waiting(monkeypatch, idle):
    # A picture steps aside for song work; its models are no use to the song and would sit under it,
    # on a card with memory of its own as on a Mac.
    monkeypatch.setattr(config, "UNLOAD_WHEN_IDLE", "auto")
    gpu_named(monkeypatch, "mps")
    jobs.QUEUE.put_nowait({"kind": "render", "id": "x"})
    try:
        assert jobs.unload_when_idle("art") is True
        assert jobs.unload_when_idle("render") is False
        gpu_named(monkeypatch, "cuda:0 NVIDIA GeForce RTX 4070")
        assert jobs.unload_when_idle("art") is True
        assert jobs.unload_when_idle("render") is False
    finally:
        jobs.QUEUE.get_nowait()


def test_after_a_picture_not_when_another_picture_is_next_nor_when_told_never(monkeypatch, idle):
    monkeypatch.setattr(config, "UNLOAD_WHEN_IDLE", "auto")
    gpu_named(monkeypatch, "cuda:0 NVIDIA GeForce RTX 4070")
    assert jobs.unload_when_idle("art") is True
    jobs.ART_WAITING.append("take")
    try:
        assert jobs.unload_when_idle("art") is False          # the next picture would only load them again
        jobs.QUEUE.put_nowait({"kind": "render", "id": "x"})
        try:
            assert jobs.unload_when_idle("art") is True       # a song goes first: they would sit under it
        finally:
            jobs.QUEUE.get_nowait()
    finally:
        jobs.ART_WAITING.clear()
    monkeypatch.setattr(config, "UNLOAD_WHEN_IDLE", "0")
    assert jobs.unload_when_idle("art") is False
