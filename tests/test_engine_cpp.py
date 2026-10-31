"""The yue2.cpp engine: the app's ComfyUI graphs read as yue2.cpp requests, and yue2.cpp's
answers handed back shaped like ComfyUI's history, against a fake server."""
import asyncio
import json
import math
import shutil
import struct
import subprocess

import httpx
import pytest

from app import config, engine_cpp
from app.engine_cpp import CppEngine, adapters_for, split_tracks, translate
from app.jobs import build_plan_graph, build_render_graph, build_transcribe_graph, extract_audio_item, extract_text_output

TAKE = {"id": "t1", "style": "indie pop", "lyrics": "[verse]\nla la", "abc": "X:1\nK:C\n", "seed": 42,
        "sound_seed": 7, "mode": "full", "max_duration": 120, "sampler_steps": 24, "interpretation": "loose"}


def test_a_render_becomes_a_synth_request():
    job = translate(build_render_graph(TAKE))
    body = job["body"]
    assert job["kind"] == "render" and job["path"] == "/synth"
    assert body["abc"] == "X:1\nK:C" and body["lyrics"] == "[verse]\nla la" and body["cot"] == "full"
    # The notes come from the take's seed, the sound from its sound seed, as on ComfyUI.
    assert body["lm_seed"] == 42 and body["seed"] == 7 and body["steps"] == 24
    assert body["duration"] == 120.0
    assert body["semantic_sampling"]["temperature"] == 1.2          # Loose
    assert body["semantic_sampling"]["max_tokens"] >= 120 * 25
    assert body["output_format"] == "wav32" and body["adapters"] == []
    assert job["output"] == "16"


def test_a_long_cap_raises_the_music_stage_budget_within_the_context():
    body = translate(build_render_graph({**TAKE, "max_duration": 600}))["body"]
    assert body["semantic_sampling"]["max_tokens"] == 600 * 25
    body = translate(build_render_graph({**TAKE, "max_duration": 900}))["body"]
    assert body["semantic_sampling"]["max_tokens"] == engine_cpp.SEMANTIC_CEILING


def test_each_lora_half_keeps_its_own_strength():
    take = {**TAKE, "style_lora": "style.safetensors", "style_lora_model": 0.7, "style_lora_clip": 0.5,
            "voice_lora": "voice.safetensors", "voice_lora_strength": 0.9}
    adapters = {a["name"]: a for a in translate(build_render_graph(take))["body"]["adapters"]}
    assert adapters["style.safetensors"]["scale_ar"] == 0.5 and adapters["style.safetensors"]["scale_nar"] == 0.7
    # A voice is the sound half alone.
    assert adapters["voice.safetensors"]["scale_ar"] == 0.0 and adapters["voice.safetensors"]["scale_nar"] == 0.9
    assert all(a["scale"] == 0.0 for a in adapters.values())


def test_an_instrumental_brings_its_planner_lora():
    take = {**TAKE, "kind": "instrumental", "feel": "steady"}
    adapters = translate(build_render_graph(take))["body"]["adapters"]
    inst = next(a for a in adapters if a["name"] == config.INSTRUMENTAL_LORA)
    assert inst["scale_ar"] > 0 and inst["scale_nar"] == 0.0


def test_a_lora_at_zero_on_both_halves_is_left_out():
    graph = build_render_graph({**TAKE, "style_lora": "off.safetensors", "style_lora_model": 0.0, "style_lora_clip": 0.0})
    assert translate(graph)["body"]["adapters"] == []


def test_a_plan_becomes_a_plan_request_with_its_variety_and_planner_lora():
    take = {**TAKE, "variety": "bold", "style_lora": "style.safetensors", "style_lora_clip": 0.6}
    job = translate(build_plan_graph(take))
    body = job["body"]
    assert job["kind"] == "plan" and job["path"] == "/plan"
    assert body["lm_seed"] == 42 and body["cot"] == "full"
    assert body["abc_sampling"]["temperature"] == 1.0 and body["abc_sampling"]["repetition_penalty"] == 1.03
    assert body["abc_sampling"]["max_tokens"] == 8192
    assert body["adapters"] == [{"name": "style.safetensors", "scale": 0.0, "scale_ar": 0.6, "scale_nar": 0.0}]
    assert job["output"] == "3"


def test_a_harmony_plan_is_written_by_the_stock_planner():
    job = translate(build_plan_graph({**TAKE, "harmony": 2}))
    assert job["kind"] == "plan" and "chord_strength" not in job["body"]


def test_a_transcription_sends_the_uploaded_recording():
    job = translate(build_transcribe_graph("song.flac", "melody"))
    assert job == {"kind": "transcribe", "path": "/transcribe", "audio": "song.flac", "melody_only": True, "output": "4"}


def test_a_job_only_comfyui_can_run_is_refused_with_why():
    graph = {"1": {"class_type": "CLIPLoader", "inputs": {}}, "2": {"class_type": "TextGenerate", "inputs": {}}}
    with pytest.raises(RuntimeError, match="ComfyUI engine"):
        translate(graph)


def test_adapters_follow_only_the_chains_that_reach_the_two_halves():
    graph = {"10": {"class_type": "CheckpointLoaderSimple", "inputs": {}},
             "20": {"class_type": "LoraLoader", "inputs": {"model": ["10", 0], "clip": ["10", 1], "lora_name": "a",
                                                           "strength_model": 0.3, "strength_clip": 0.4}},
             "21": {"class_type": "LoraLoader", "inputs": {"model": ["20", 0], "clip": ["10", 1], "lora_name": "b",
                                                           "strength_model": 0.8, "strength_clip": 0.9}}}
    # The text side reads a; the sampler reads b and, through it, a.
    got = {a["name"]: (a["scale_ar"], a["scale_nar"]) for a in adapters_for(graph, ["20", 1], ["21", 0])}
    assert got == {"a": (0.4, 0.3), "b": (0.0, 0.8)}


def _wav_f32(seconds=0.5, rate=48000, peak=1.4):
    n = int(seconds * rate)
    frames = b"".join(struct.pack("<ff", peak * math.sin(i / 20), peak * math.sin(i / 20)) for i in range(n))
    fmt = struct.pack("<HHIIHH", 3, 2, rate, rate * 8, 8, 32)
    return (b"RIFF" + struct.pack("<I", 4 + 8 + len(fmt) + 8 + len(frames)) + b"WAVE" + b"fmt " + struct.pack("<I", len(fmt))
            + fmt + b"data" + struct.pack("<I", len(frames)) + frames)


def _multipart(parts, boundary="yue2-batch-boundary"):
    out = b""
    for kind, data in parts:
        out += f"--{boundary}\r\nContent-Type: {kind}\r\n\r\n".encode() + data + b"\r\n"
    return out + f"--{boundary}--\r\n".encode()


def test_split_tracks_reads_the_replay_the_audio_and_the_latents():
    body = _multipart([("application/json", b'{"seed": 1}'), ("audio/wav", b"RIFFxx\r\n--not"), ("application/octet-stream", b"\x00\x01")])
    parts = split_tracks(body, 'multipart/mixed; boundary=yue2-batch-boundary')
    assert [p["type"] for p in parts] == ["application/json", "audio/wav", "application/octet-stream"]
    assert parts[1]["data"] == b"RIFFxx\r\n--not"


class FakeServer:
    """yue2.cpp's routes, enough for one job of each kind."""

    def __init__(self):
        self.requests = []
        self.jobs = {}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/props":
            return httpx.Response(200, json={
                "version": "test", "model": "/models/YuE2-3B-Q8_0.gguf",
                "device": {"name": "CUDA0", "description": "Test GPU", "memory_free": 8 << 30, "memory_total": 12 << 30},
                "adapters": [{"name": config.INSTRUMENTAL_LORA, "ar": True, "nar": False},
                             {"name": "style.safetensors", "ar": True, "nar": True}]})
        if path == "/adapters/rescan":
            return httpx.Response(200, json={"status": "queued"})
        if path in ("/synth", "/plan", "/transcribe"):
            self.requests.append((path, request.content))
            job_id = f"{len(self.jobs):016x}"
            self.jobs[job_id] = path
            return httpx.Response(200, json={"id": job_id})
        if path == "/job":
            job_id = request.url.params["id"]
            kind = self.jobs.get(job_id)
            if not kind:
                return httpx.Response(404, json={"error": "job not found"})
            if request.url.params.get("cancel"):
                return httpx.Response(200, json={"status": "cancelled"})
            if not request.url.params.get("result"):
                return httpx.Response(200, json={"status": "done"})
            if kind == "/plan":
                return httpx.Response(200, json={"abc": "X:1\nK:D\n|abc|", "truncated": False, "lm_seed": 42})
            if kind == "/transcribe":
                return httpx.Response(200, json={"abc": "X:1\nK:G\n|GAB|"})
            body = _multipart([("application/json", b"{}"), ("audio/wav", _wav_f32()), ("application/octet-stream", b"")])
            return httpx.Response(200, content=body, headers={"content-type": "multipart/mixed; boundary=yue2-batch-boundary"})
        return httpx.Response(404)


def _engine(server):
    engine = CppEngine("http://cpp")
    engine.POLL = 0.01
    engine.client = httpx.AsyncClient(base_url="http://cpp", transport=httpx.MockTransport(server))
    return engine


async def _finish(engine, pid):
    for _ in range(500):
        job = await engine.history(pid)
        if job:
            return job
        await asyncio.sleep(0.01)
    raise AssertionError("the job did not finish")


def test_options_say_what_this_engine_has(monkeypatch):
    monkeypatch.setattr(config, "CHECKPOINT", config.CHECKPOINT)
    engine = _engine(FakeServer())

    async def go():
        await engine.refresh_status()
        await engine.refresh_options()
    asyncio.run(go())
    options = engine.options
    assert engine.online and options["engine"] == "yue2cpp"
    for absent in ("harmony", "hook", "lyrics", "trainer", "pictures", "separate", "hear"):
        assert options[absent] is False
    assert options["instrumental"] is True and "style.safetensors" in options["loras"]
    assert config.CHECKPOINT == "YuE2-3B-Q8_0.gguf" and options["checkpoints"] == [config.CHECKPOINT]
    assert "yue2.cpp" in config.CHECKPOINT_LABELS[config.CHECKPOINT]
    gpu = engine.gpu()
    assert gpu["name"] == "Test GPU" and gpu["vram_total"] == 12 << 30


def test_a_plan_comes_back_as_comfyuis_history_would_have_it():
    server = FakeServer()
    engine = _engine(server)

    async def go():
        pid = await engine.submit(build_plan_graph(TAKE))
        return await _finish(engine, pid)
    job = asyncio.run(go())
    assert job["status"]["status_str"] == "success"
    assert extract_text_output(job, "YuE2GenerateABC", "PreviewAny") == "X:1\nK:D\n|abc|"
    path, sent = server.requests[0]
    assert path == "/plan" and json.loads(sent)["lm_seed"] == 42


def test_a_transcription_takes_its_upload_with_it():
    server = FakeServer()
    engine = _engine(server)

    async def go():
        name = (await engine.upload("tune.wav", b"audio-bytes"))["name"]
        pid = await engine.submit(build_transcribe_graph(name, "melody"))
        return await _finish(engine, pid)
    job = asyncio.run(go())
    assert extract_text_output(job, "SheetSage2AudioToABC", "PreviewAny") == "X:1\nK:G\n|GAB|"
    path, sent = server.requests[0]
    assert path == "/transcribe" and b"audio-bytes" in sent and b"melody_only" in sent


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_a_recording_it_cannot_read_is_made_a_wav_first():
    engine = _engine(FakeServer())
    flac = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.3",
                           "-c:a", "flac", "-f", "flac", "pipe:1"], capture_output=True, check=True).stdout
    asyncio.run(engine.upload("tune.flac", flac))
    assert engine.uploads["tune.flac"][:4] == b"RIFF"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_a_render_comes_down_as_levelled_flac(tmp_path):
    engine = _engine(FakeServer())
    dest = tmp_path / "take.flac"

    async def go():
        pid = await engine.submit(build_render_graph(TAKE))
        job = await _finish(engine, pid)
        item = extract_audio_item(job, "SaveAudioAdvanced")
        await engine.download(item, dest)
        return job, item
    job, item = asyncio.run(go())
    assert item["type"] == "yue2cpp"
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,sample_fmt,sample_rate",
                            "-of", "json", str(dest)], capture_output=True, text=True, check=True)
    stream = json.loads(probe.stdout)["streams"][0]
    assert stream["codec_name"] == "flac" and stream["sample_fmt"] == "s16" and stream["sample_rate"] == "48000"
    # The fake's audio peaks at +3 dB over full scale; the guard brought it under the ceiling.
    peak = subprocess.run(["ffmpeg", "-v", "info", "-i", str(dest), "-af", "astats=measure_overall=Peak_level",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    level = float([l for l in peak.splitlines() if "Peak level dB" in l][-1].split(":")[-1])
    assert level <= config.PEAK_CEILING_DB + 0.3


def test_a_failed_job_reports_the_engines_own_words():
    class Failing(FakeServer):
        def __call__(self, request):
            if request.url.path == "/job" and not request.url.params.get("result"):
                return httpx.Response(200, json={"status": "failed"})
            return super().__call__(request)
    engine = _engine(Failing())

    async def go():
        pid = await engine.submit(build_plan_graph(TAKE))
        await asyncio.sleep(0)
        engine._handle_log("[Server] Plan job 0000000000000000: {")
        engine._handle_log("[Plan] FATAL: cot must be full or melody to write a score")
        return await _finish(engine, pid)
    job = asyncio.run(go())
    assert job["status"]["status_str"] == "error"
    assert "cot must be full" in json.dumps(job["status"]["messages"])


def test_the_log_moves_the_progress_of_the_job_it_is_on():
    engine = _engine(FakeServer())
    pid = "p1"
    engine.progress[pid] = {"stage": None, "frac": 0.0, "value": None, "max": None, "kind": "render",
                            "started": 0, "executing": False, "stages": list(engine_cpp.STAGES["render"])}
    engine.server_ids[pid] = "abc123"
    engine._tasks[pid] = None
    engine._handle_log("[NAR] Step 3/32, 70 ms")               # before its job opened: someone else's
    assert engine.progress[pid]["stage"] is None
    engine._handle_log("[Server] Job abc123: {")
    assert engine.has_started(pid)
    engine._handle_log("[AR] Semantic 300/750")
    assert engine.progress[pid]["stage"] == "YuE2GenerateMusic" and engine.progress[pid]["frac"] == 0.4
    engine._handle_log("[NAR] Step 16/32, 73 ms")
    snap = engine.snapshot(pid)
    assert snap["label"] == "Rendering audio" and 0 < snap["progress"] < 1
    engine._handle_log("CUDA error: out of memory")
    assert engine.oom_at > 0


def test_the_engine_is_chosen_by_its_kind():
    assert isinstance(engine_cpp.make_engine("http://x", "yue2cpp"), CppEngine)
    assert not isinstance(engine_cpp.make_engine("http://x", "comfyui"), CppEngine)
