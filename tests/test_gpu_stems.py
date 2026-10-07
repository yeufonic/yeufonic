"""Stems separated on the engine's GPU, and the fall back to the CPU."""
import asyncio
import shutil
import time

import pytest

from app import config, jobs

from conftest import tone

REAL_SLEEP = asyncio.sleep


class GpuEngine:
    """An engine that has the Demucs node and answers a job with the stems asked for."""

    def __init__(self, audio, outcome="success"):
        self.audio, self.outcome = audio, outcome
        self.online = True
        self.options = {"separate": True}
        self.progress = {}
        self.last_contact = time.time()
        self.submitted, self.uploads, self.cancelled = [], [], []

    async def submit(self, graph):
        self.submitted.append(graph)
        return "pid"

    async def history(self, prompt_id):
        self.last_contact = time.time()
        graph = self.submitted[-1]
        outputs = {nid: {"audio": [{"filename": f"{node['inputs']['filename_prefix'].rsplit('/', 1)[-1]}_00001.flac",
                                    "subfolder": "x", "type": "output"}]}
                   for nid, node in graph.items() if node["class_type"] == "SaveAudio"}
        return {"status": {"status_str": self.outcome, "completed": self.outcome == "success",
                           "messages": [["execution_error", {"exception_message": "no good"}]] if self.outcome != "success" else []},
                "outputs": outputs}

    def has_started(self, prompt_id):
        return True

    async def prompt_state(self, prompt_id):
        return "running"

    async def cancel(self, prompt_id):
        self.cancelled.append(prompt_id)

    def forget(self, prompt_id):
        pass

    async def upload(self, name, data):
        self.uploads.append(name)
        return {"name": name}

    async def download(self, item, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.audio, dest)
        return dest


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(jobs.asyncio, "sleep", lambda _s: REAL_SLEEP(0))
    jobs.CURRENT.clear()
    jobs.CANCELLED.clear()
    yield
    jobs.CURRENT.clear()


@pytest.fixture
def cpu(monkeypatch):
    """The CPU separation, recorded and answered without running demucs."""
    calls = []

    async def separate(src, dest_dir, model, wanted, fmt, on_progress=None, work_root=None):
        calls.append((model, tuple(wanted), fmt))
        return {"stems": {}, "model": model, "format": fmt, "seconds": 0, "device": "cpu"}

    monkeypatch.setattr(jobs.stems, "separate", separate)
    return calls


def run(src, dest, model="htdemucs_2s", wanted=("vocals", "instruments"), fmt="flac", progress=None):
    return asyncio.run(jobs.separate_stems(src, dest, model, list(wanted), fmt, progress, work_root=dest.parent / "work"))


def test_a_vocal_is_separated_on_the_engine_and_collected(monkeypatch, tmp_path):
    src, sample = tone(tmp_path / "in.flac", 1.0), tone(tmp_path / "stem.flac", 0.5)
    engine = monkeypatch.setattr(jobs, "ENGINE", GpuEngine(sample)) or jobs.ENGINE
    seen = []
    got = run(src, tmp_path / "out", progress=lambda frac, stage: seen.append((frac, stage)))
    assert got["device"] == "gpu" and set(got["stems"]) == {"vocals", "instruments"}
    assert (tmp_path / "out" / "vocals.flac").exists() and (tmp_path / "out" / "instruments.flac").exists()
    graph = engine.submitted[0]
    assert graph["1"]["class_type"] == "LoadAudio" and graph["1"]["inputs"]["audio"] == engine.uploads[0]
    assert graph["2"]["class_type"] == "Yue2Separate" and graph["2"]["inputs"]["model"] == "htdemucs", "the two-stem model runs the base model"
    saves = {n["inputs"]["filename_prefix"].rsplit("/", 1)[-1]: n["inputs"]["audio"][1] for n in graph.values() if n["class_type"] == "SaveAudio"}
    assert saves == {"vocals": 0, "instruments": 6}, "each stem from its own output of the node"
    assert seen[-1] == (1.0, "Done")
    assert not list((tmp_path / "work").glob("*")), "the working copy is removed"


def test_other_formats_are_made_from_the_engine_flac(monkeypatch, tmp_path):
    src, sample = tone(tmp_path / "in.flac", 1.0), tone(tmp_path / "stem.flac", 0.5)
    monkeypatch.setattr(jobs, "ENGINE", GpuEngine(sample))
    got = run(src, tmp_path / "out", model="htdemucs", wanted=("drums", "bass"), fmt="wav")
    assert (tmp_path / "out" / "drums.wav").exists() and (tmp_path / "out" / "bass.wav").exists()
    assert set(got["stems"]) == {"drums", "bass"}


@pytest.mark.parametrize("why", ["no node", "offline", "training", "switched off", "setting off"])
def test_the_cpu_is_used_when_the_gpu_cannot_be(monkeypatch, tmp_path, cpu, why):
    src, sample = tone(tmp_path / "in.flac", 1.0), tone(tmp_path / "stem.flac", 0.5)
    engine = monkeypatch.setattr(jobs, "ENGINE", GpuEngine(sample)) or jobs.ENGINE
    if why == "no node":
        engine.options = {}
    elif why == "offline":
        engine.online = False
    elif why == "training":
        jobs.CURRENT.update({"kind": "train", "id": "r"})
    elif why == "setting off":
        monkeypatch.setattr(jobs, "get_setting", lambda key, default=None: "off" if key == "processing.gpu" else default)
    else:
        monkeypatch.setattr(config, "STEMS_ON_GPU", False)
    got = run(src, tmp_path / "out")
    assert got["device"] == "cpu" and cpu == [("htdemucs_2s", ("vocals", "instruments"), "flac")]
    assert not engine.submitted


def test_a_failed_engine_job_falls_back_to_the_cpu(monkeypatch, tmp_path, cpu):
    src, sample = tone(tmp_path / "in.flac", 1.0), tone(tmp_path / "stem.flac", 0.5)
    monkeypatch.setattr(jobs, "ENGINE", GpuEngine(sample, outcome="error"))
    assert run(src, tmp_path / "out")["device"] == "cpu" and len(cpu) == 1


def test_progress_follows_the_engines_stages_and_does_not_sit_still():
    step = jobs._gpu_separation_progress
    assert step({}) is None and step({"stage": "PreviewAny"}) is None
    steps = [step({"stage": "LoadAudio"}),
             step({"stage": "Yue2Separate", "value": None}),
             step({"stage": "Yue2Separate", "value": 10, "max": 100, "frac": 0.1}),
             step({"stage": "Yue2Separate", "value": 100, "max": 100, "frac": 1.0}),
             step({"stage": "SaveAudio"})]
    fracs = [s[0] for s in steps]
    assert fracs == sorted(fracs) and len(set(fracs)) == len(fracs), "each stage is further along than the last"
    assert steps[1][1].startswith("Loading the model") and steps[2][1] == "Separating (GPU)" and steps[-1][1].startswith("Saving")
    assert fracs[-1] < 0.92, "collecting the files comes after"


# ------------------------------------------------------------------ hearing the words on the GPU
import json  # noqa: E402

from app import identities  # noqa: E402

SEGMENTS = [{"start": 1.0, "end": 5.0, "text": " Hello there. How are you"},
            {"start": 6.0, "end": 7.0, "text": " Thank you."}]


class HearEngine(GpuEngine):
    async def history(self, prompt_id):
        self.last_contact = time.time()
        graph = self.submitted[-1]
        nid = next(n for n, node in graph.items() if node["class_type"] == "PreviewAny")
        return {"status": {"status_str": self.outcome, "completed": self.outcome == "success", "messages": []},
                "outputs": {nid: {"text": [json.dumps(SEGMENTS)]}}}


@pytest.fixture
def cpu_hear(monkeypatch):
    calls = []

    def transcribe(vocal, on_progress=None, duration=0.0, should_stop=None):
        calls.append(vocal.name)
        return [{"start": 0.0, "end": 1.0, "text": "from the cpu"}]

    monkeypatch.setattr(jobs.identities, "transcribe", transcribe)
    return calls


def hear(vocal, **kwargs):
    return asyncio.run(jobs.hear_lines(vocal, kwargs.get("progress"), 10.0, kwargs.get("should_stop")))


def test_words_are_heard_on_the_engine_and_laid_out_as_the_cpu_does(monkeypatch, tmp_path):
    vocal = tone(tmp_path / "vocals.flac", 1.0)
    engine = monkeypatch.setattr(jobs, "ENGINE", HearEngine(vocal)) or jobs.ENGINE
    engine.options = {"hear": True}
    lines = hear(vocal)
    assert [line["text"] for line in lines] == ["Hello there", "How are you"], "split at the sentence end, the stock phrase dropped"
    graph = engine.submitted[0]
    assert graph["2"]["class_type"] == "Yue2Hear" and graph["2"]["inputs"]["model"] == identities.WHISPER_MODEL
    assert graph["2"]["inputs"]["language"] == "en" and graph["3"]["class_type"] == "PreviewAny"


@pytest.mark.parametrize("why", ["no node", "offline", "training", "setting off", "engine error"])
def test_the_cpu_hears_when_the_gpu_cannot(monkeypatch, tmp_path, cpu_hear, why):
    vocal = tone(tmp_path / "vocals.flac", 1.0)
    engine = HearEngine(vocal, outcome="error" if why == "engine error" else "success")
    engine.options = {"hear": True}
    monkeypatch.setattr(jobs, "ENGINE", engine)
    if why == "no node":
        engine.options = {}
    elif why == "offline":
        engine.online = False
    elif why == "training":
        jobs.CURRENT.update({"kind": "train", "id": "r"})
    elif why == "setting off":
        monkeypatch.setattr(jobs, "get_setting", lambda key, default=None: "off" if key == "processing.gpu" else default)
    assert hear(vocal)[0]["text"] == "from the cpu" and cpu_hear == ["vocals.flac"]


def test_stopping_while_the_engine_listens_stops_the_analysis(monkeypatch, tmp_path):
    vocal = tone(tmp_path / "vocals.flac", 1.0)
    engine = HearEngine(vocal)
    engine.options = {"hear": True}

    async def never(self, prompt_id):
        self.last_contact = time.time()
        return None

    monkeypatch.setattr(HearEngine, "history", never)
    monkeypatch.setattr(jobs, "ENGINE", engine)
    with pytest.raises(identities.Stopped):
        hear(vocal, should_stop=lambda: True)
    assert engine.cancelled == ["pid"]


def test_hearing_progress_waits_for_the_node_to_start():
    step = jobs._gpu_hearing_progress
    assert step({}) is None and step({"stage": "LoadAudio"}) is None
    assert step({"stage": "Yue2Hear", "value": None}) is None, "loading the model says nothing, so a label set for the wait stays"
    assert step({"stage": "Yue2Hear", "value": 5, "frac": 0.4}) == 0.4


def test_the_wait_for_the_whisper_model_is_labelled_the_first_time(monkeypatch, tmp_path):
    vocal = tone(tmp_path / "vocals.flac", 1.0)
    engine = HearEngine(vocal)
    engine.options = {"hear": True}
    monkeypatch.setattr(jobs, "ENGINE", engine)
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    (tmp_path / "models").mkdir()
    said = []
    asyncio.run(jobs.hear_lines(vocal, None, 10.0, None, said.append))
    assert said == ["Downloading the Whisper model, first time only"]
    # with the model there, as a plain folder or in the Hugging Face cache, nothing is said
    for place in ("whisper/large-v3-turbo", "whisper/models--x--faster-whisper-large-v3-turbo/snapshots/abc"):
        folder = tmp_path / "models" / place
        folder.mkdir(parents=True)
        (folder / "model.bin").write_bytes(b"x")
        said.clear()
        asyncio.run(jobs.hear_lines(vocal, None, 10.0, None, said.append))
        assert said == [], place
        shutil.rmtree(tmp_path / "models" / "whisper")
