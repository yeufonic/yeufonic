"""The yue2.cpp engine: yue2.cpp's server in place of ComfyUI, for smaller GPUs and Macs.

The app builds the same ComfyUI graphs whichever engine runs, and this client reads them:
a render, a plan or a transcription becomes the yue2.cpp request that does the same, and
its answer comes back shaped like ComfyUI's history, so the job code above it does not
know which engine it talks to.  What yue2.cpp cannot do (training, Gemma, pictures, the
harmony control, stems and hearing on the GPU) is reported as absent in `options`, the
same way a ComfyUI engine built without a node pack reports it, and the page offers
those features only where they are there.

yue2.cpp runs one job at a time and holds nothing on the GPU between jobs.  It reports
progress only in its log, so the log stream is read for the lines of the job it is on.
"""
from __future__ import annotations

import asyncio
import logging
import math
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

from . import config, logging_setup
from .engine import OUT_OF_MEMORY, Engine

log = logging.getLogger("yue2.engine")

KIND = "yue2cpp"
NAME = "yue2.cpp"

# The nodes of the app's graphs this engine can run, by what they do.
RENDER_NODE = "YuE2GenerateMusic"
PLAN_NODES = ("YuE2GenerateABC", "YuE2GenerateABCHarmony")
TRANSCRIBE_NODE = "SheetSage2AudioToABC"
SAMPLER_NODE = "KSampler"
LORA_NODE = "LoraLoader"

# The music stage writes 25 tokens a second of song; its own cap is 9000 (six minutes), and
# the context of the model is 24576 with the prompt and the score in it too.
FRAME_RATE = 25
SEMANTIC_MAX = 9000
SEMANTIC_CEILING = 22000

# The stages of each kind of job as the progress bar has them: the names are the ComfyUI
# nodes they stand for, so the labels and weights in engine.py serve both engines.
STAGES = {
    "render": ["CheckpointLoaderSimple", "YuE2GenerateMusic", "KSampler", "VAEDecodeAudioTiled", "SaveAudioAdvanced"],
    "plan": ["CheckpointLoaderSimple", "YuE2GenerateABC"],
    "transcribe": ["AudioEncoderLoader", "SheetSage2AudioToABC"],
}

# The log lines that say where a job is.  "[Server] Job <id>", "[Server] Plan job <id>" and
# "[Server] Transcribe job <id>" open a job; the rest are its steps.
JOB_START = re.compile(r"^\[Server\] (?:Plan |Transcribe |Tokenize |VAE \w+ )?[Jj]ob ([0-9a-f]+)")
STEP_LINES = [
    (re.compile(r"^\[AR\] Score (\d+)/(\d+)"), "YuE2GenerateABC"),
    (re.compile(r"^\[AR\] Semantic (\d+)/(\d+)"), "YuE2GenerateMusic"),
    (re.compile(r"^\[NAR\] Step (\d+)/(\d+)"), "KSampler"),
    (re.compile(r"^\[VAE\] Track (\d+)/(\d+)"), "VAEDecodeAudioTiled"),
]
FATAL = re.compile(r"FATAL: (.+)$")
# Lines worth leaving out of the app's log: one per hundred tokens, one per solver step.
NOISY = re.compile(r"^\[(?:AR\] (?:Score|Semantic) \d+/|NAR\] Step \d+/|Adapter\] Skip )")


def _input(graph: dict, link: Any) -> dict | None:
    """The node a link [node id, output] points at."""
    if isinstance(link, list) and link and str(link[0]) in graph:
        return graph[str(link[0])]
    return None


def _chain(graph: dict, link: Any, strength_field: str) -> list[tuple[str, float]]:
    """The LoRAs a link passes through on its way back to the checkpoint, with the strength
    each one gives that half: a model link carries the acoustic half, a clip link the planner's."""
    out = []
    output = 0 if strength_field == "strength_model" else 1
    node = _input(graph, link)
    seen = 0
    while node and node.get("class_type") == LORA_NODE and seen < 32:
        inputs = node.get("inputs") or {}
        out.append((str(inputs.get("lora_name") or ""), float(inputs.get(strength_field) or 0.0)))
        node = _input(graph, inputs.get("model" if output == 0 else "clip"))
        seen += 1
    return out


def adapters_for(graph: dict, clip_link: Any, model_link: Any) -> list[dict]:
    """The request's adapters: every LoRA on the text side's chain and the sampler's chain, with
    each half's strength as the graph gives it (a half the graph does not reach is 0)."""
    halves: dict[str, dict[str, float]] = {}
    for name, strength in _chain(graph, clip_link, "strength_clip"):
        halves.setdefault(name, {"ar": 0.0, "nar": 0.0})["ar"] += strength
    for name, strength in _chain(graph, model_link, "strength_model"):
        halves.setdefault(name, {"ar": 0.0, "nar": 0.0})["nar"] += strength
    return [{"name": name, "scale": 0.0, "scale_ar": h["ar"], "scale_nar": h["nar"]}
            for name, h in halves.items() if name and (h["ar"] or h["nar"])]


def _find(graph: dict, class_types: tuple[str, ...] | str) -> tuple[str, dict] | tuple[None, None]:
    wanted = (class_types,) if isinstance(class_types, str) else class_types
    for nid, node in graph.items():
        if node.get("class_type") in wanted:
            return nid, node
    return None, None


def _output_node(graph: dict, *class_types: str) -> str | None:
    nid, _ = _find(graph, class_types)
    return nid


def translate(graph: dict) -> dict:
    """What a graph asks for, as a yue2.cpp request: {"kind", "path", "body"} plus, for the
    answer, the id of the node ComfyUI would have put it on.  Raises for a graph this engine
    cannot run."""
    nid, render = _find(graph, RENDER_NODE)
    if render:
        inputs = render["inputs"]
        _, sampler = _find(graph, SAMPLER_NODE)
        sampler_inputs = (sampler or {}).get("inputs") or {}
        duration = float(inputs.get("max_duration") or 360)
        body = {
            "style": inputs.get("style") or "",
            "lyrics": inputs.get("lyrics") or "",
            "abc": inputs.get("abc") or "",
            "cot": inputs.get("mode") if inputs.get("mode") in ("full", "melody") else "full",
            "duration": duration,
            "lm_seed": int(inputs.get("seed") or 0),
            "seed": int(sampler_inputs.get("seed") if sampler_inputs.get("seed") is not None else inputs.get("seed") or 0),
            "steps": int(sampler_inputs.get("steps") or 32),
            # Float audio, as ComfyUI's decoder hands it on: the app levels and saves it.
            "output_format": "wav32",
            "semantic_sampling": {
                "temperature": float(inputs.get("temperature", 1.0)),
                "top_p": float(inputs.get("top_p", 0.95)),
                "top_k": int(inputs.get("top_k", 100)),
                "repetition_penalty": float(inputs.get("repetition_penalty", 1.2)),
                "penalty_window": 50,
                "min_tokens": 200,
                "max_tokens": min(SEMANTIC_CEILING, max(SEMANTIC_MAX, int(math.ceil(duration * FRAME_RATE)))),
            },
            "adapters": adapters_for(graph, inputs.get("clip"), sampler_inputs.get("model")),
        }
        guard = next((n for n in graph.values() if n.get("class_type") == "Yue2PeakGuard"), None)
        return {"kind": "render", "path": "/synth", "body": body,
                "output": _output_node(graph, "SaveAudioAdvanced", "SaveAudio") or "16",
                "ceiling_db": float((guard or {}).get("inputs", {}).get("ceiling_db", config.PEAK_CEILING_DB))}
    nid, plan = _find(graph, PLAN_NODES)
    if plan:
        inputs = plan["inputs"]
        if plan.get("class_type") != "YuE2GenerateABC":
            log.info("yue2.cpp has no harmony control: this plan is written by the stock planner")
        body = {
            "style": inputs.get("style") or "",
            "lyrics": inputs.get("lyrics") or "",
            "cot": inputs.get("mode") if inputs.get("mode") in ("full", "melody") else "full",
            "lm_seed": int(inputs.get("seed") or 0),
            "abc_sampling": {
                "temperature": float(inputs.get("temperature", 0.7)),
                "top_p": float(inputs.get("top_p", 0.9)),
                "top_k": int(inputs.get("top_k", 30)),
                "repetition_penalty": float(inputs.get("repetition_penalty", 1.005)),
                "penalty_window": max(1, min(100, int(inputs.get("penalty_window", 100)))),
                "min_tokens": 32,
                "max_tokens": int(inputs.get("max_abc_tokens") or 8192),
            },
            "adapters": adapters_for(graph, inputs.get("clip"), None),
        }
        return {"kind": "plan", "path": "/plan", "body": body,
                "output": _output_node(graph, "PreviewAny") or nid}
    nid, transcribe = _find(graph, TRANSCRIBE_NODE)
    if transcribe:
        audio = _input(graph, transcribe["inputs"].get("audio")) or {}
        return {"kind": "transcribe", "path": "/transcribe",
                "audio": (audio.get("inputs") or {}).get("audio"),
                "melody_only": transcribe["inputs"].get("mode") == "melody",
                "output": _output_node(graph, "PreviewAny") or nid}
    names = sorted({node.get("class_type", "?") for node in graph.values()})
    raise RuntimeError("the yue2.cpp engine cannot run this job (" + ", ".join(names[:4]) + "): it needs the ComfyUI engine")


def level_to_flac(src: Path, dest: Path, ceiling_db: float) -> None:
    """The float audio yue2.cpp wrote, saved the way the app keeps a render: peaks above the
    ceiling turned down where they happen (a limiter, as the ComfyUI engine's peak guard
    does), the rest left as it is, then 16-bit FLAC at the song's own rate."""
    limit = max(0.0625, min(1.0, 10 ** (ceiling_db / 20)))
    filters = [] if not config.PEAK_GUARD else [f"alimiter=limit={limit:.4f}:attack=5:release=50:level=disabled"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src)]
    if filters:
        cmd += ["-af", ",".join(filters)]
    if dest.suffix.lower() == ".flac":
        cmd += ["-c:a", "flac", "-sample_fmt", "s16"]
    cmd.append(str(dest))
    subprocess.run(cmd, check=True, capture_output=True, timeout=600)


def as_wav(data: bytes) -> bytes:
    """Audio in any format ffmpeg reads, as a 16-bit WAV at its own rate and channels."""
    done = subprocess.run(["ffmpeg", "-v", "error", "-i", "pipe:0", "-map", "0:a:0", "-map_metadata", "-1",
                           "-c:a", "pcm_s16le", "-f", "wav", "pipe:1"],
                          input=data, capture_output=True, timeout=600)
    if done.returncode or not done.stdout:
        raise RuntimeError("the recording could not be read: " + done.stderr.decode(errors="replace")[:200])
    return done.stdout


def split_tracks(body: bytes, content_type: str) -> list[dict[str, Any]]:
    """The parts of a /synth result (multipart/mixed, per track: the replay request, the
    audio, the latents), as dicts of content type and bytes, in order."""
    found = re.search(r'boundary="?([^";]+)"?', content_type or "")
    if not found:
        raise RuntimeError("the engine's answer had no parts")
    boundary = b"--" + found.group(1).encode()
    parts = []
    for chunk in body.split(boundary)[1:]:
        if chunk.startswith(b"--"):
            break
        head, _, data = chunk.lstrip(b"\r\n").partition(b"\r\n\r\n")
        if data.endswith(b"\r\n"):
            data = data[:-2]
        kind = ""
        for line in head.decode("latin-1").split("\r\n"):
            if line.lower().startswith("content-type:"):
                kind = line.split(":", 1)[1].strip().lower()
        parts.append({"type": kind, "data": data})
    return parts


class CppEngine(Engine):
    """The Engine interface, spoken to yue2.cpp's server."""

    kind = KIND
    name = NAME
    POLL = 0.75

    def __init__(self, url: str) -> None:
        super().__init__(url)
        self.client_id = f"yeufonic-{uuid.uuid4().hex[:8]}"
        self.uploads: dict[str, bytes] = {}
        self.results: dict[str, dict[str, Any]] = {}
        self.files: dict[str, Path] = {}
        self.server_ids: dict[str, str] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._order: list[str] = []
        self._log_task: asyncio.Task | None = None
        self._current_server_job: str | None = None
        self._lock = asyncio.Lock()
        self.props: dict[str, Any] = {}
        self._scratch = Path(tempfile.mkdtemp(prefix="yeufonic-cpp-"))

    # ---------- lifecycle ----------
    async def start(self) -> None:
        self.client = httpx.AsyncClient(base_url=self.url, timeout=httpx.Timeout(60.0, connect=4.0))
        self._log_task = asyncio.create_task(self._log_loop())
        self._options_task = asyncio.create_task(self._options_loop())
        await self.refresh_status()
        if self.online:
            try:
                await self.refresh_options()
            except Exception as exc:  # noqa: BLE001
                log.warning("engine options not read at startup: %s", exc)

    async def close(self) -> None:
        for task in (self._log_task, self._options_task, *self._tasks.values()):
            if task:
                task.cancel()
        if self.client:
            await self.client.aclose()
        shutil.rmtree(self._scratch, ignore_errors=True)

    # ---------- status ----------
    async def refresh_status(self) -> None:
        assert self.client
        try:
            r = await self.client.get("/props", timeout=4.0)
            r.raise_for_status()
            props = r.json()
        except Exception as exc:  # noqa: BLE001
            if (isinstance(exc, httpx.ReadTimeout) and self.online
                    and time.time() - self.last_contact < self.SLOW_GRACE):
                return
            if self.online:
                self.offline_at = time.time()
            self.online = False
            self.last_error = str(exc) or exc.__class__.__name__
            self.stats = None
            self.queue = []
            return
        self._contact()
        self.props = props
        device = props.get("device") or {}
        total = int(device.get("memory_total") or 0)
        free = int(device.get("memory_free") or 0)
        # Shaped like ComfyUI's /system_stats, which the GPU panel reads.  yue2.cpp holds
        # nothing between jobs, so what it holds is only known to be the card's use during one.
        name = device.get("description") or device.get("name") or "GPU"
        if str(device.get("name") or "").upper().startswith("MTL"):
            name = "mps"
        self.stats = {"devices": [{"name": name, "vram_total": total, "vram_free": free,
                                   "torch_vram_total": 0}], "system": {}}
        running = [pid for pid in self._order if pid in self._tasks and self.progress.get(pid, {}).get("executing")]
        pending = [pid for pid in self._order if pid in self._tasks and pid not in running]
        self.queue_counts = {"running": len(running), "pending": len(pending)}
        now = time.time()
        self.queue = [{"prompt_id": pid, "state": "running" if pid in running else "pending",
                       "kind": (self.progress.get(pid) or {}).get("kind", "other"), "client": self.client_id,
                       "mine": True, "queued_at": (self.progress.get(pid) or {}).get("queued"),
                       "running_since": (self.progress.get(pid) or {}).get("started") if pid in running else None}
                      for pid in running + pending]
        for pid in list(self._running_since):
            if pid not in running:
                del self._running_since[pid]
        for pid in running:
            self._running_since.setdefault(pid, now)

    @property
    def shares_memory(self) -> bool:
        return str((self.props.get("device") or {}).get("name") or "").upper().startswith("MTL")

    async def refresh_options(self) -> None:
        assert self.client
        # A LoRA put into the folder since the start is read once the jobs ahead have run.
        try:
            await self.client.post("/adapters/rescan", timeout=4.0)
            await asyncio.sleep(0.3)
        except Exception:  # noqa: BLE001  an older build has no rescan; the start-up list stands
            pass
        r = await self.client.get("/props", timeout=10.0)
        r.raise_for_status()
        props = r.json()
        self.props = props
        loras = [a["name"] for a in props.get("adapters") or [] if a.get("name")]
        model = Path(str(props.get("model") or "")).name or "yue2.cpp"
        config.CHECKPOINT = model
        config.CHECKPOINT_LABELS.setdefault(model, cpp_model_label(model))
        self.options = {
            "engine": KIND,
            "checkpoints": [model],
            "audio_encoders": [],
            # Not on this engine: the harmony control, the recorded tune held in a plan, the GPU's
            # stems and hearing (the app's CPU does them), Gemma, pictures, training.
            "harmony": False,
            "hook": False,
            "peak_guard": True,       # done by the app as the audio comes down (level_to_flac)
            "separate": False,
            "hear": False,
            "lyrics": False,
            "instrumental": config.INSTRUMENTAL_LORA in loras,
            "realaudio": config.REAL_AUDIO_LORA in loras,
            "trainer": False,
            "pictures": False,
            "klein": {},
            "loras": loras,
        }
        self.compat = {"ok": True, "missing": [], "notes": []}
        self.options_loaded = True

    # ---------- jobs ----------
    async def upload(self, filename: str, data: bytes) -> dict[str, Any]:
        """Kept here until the job that reads it is sent: yue2.cpp takes the audio with the job.
        It reads WAV and MP3 only, so anything else (FLAC, an m4a) is made a WAV first."""
        if Path(filename).suffix.lower() not in (".wav", ".mp3"):
            data = await asyncio.to_thread(as_wav, data)
        self.uploads[filename] = data
        # Only the latest few: a transcription reads its upload once.
        while len(self.uploads) > 8:
            self.uploads.pop(next(iter(self.uploads)))
        return {"name": filename, "subfolder": "", "type": "input"}

    async def submit(self, graph: dict[str, Any]) -> str:
        assert self.client
        job = translate(graph)
        pid = uuid.uuid4().hex
        self.graphs[pid] = {nid: node["class_type"] for nid, node in graph.items()}
        self.progress[pid] = {"stage": None, "frac": 0.0, "value": None, "max": None, "kind": job["kind"],
                              "started": time.time(), "queued": time.time(), "executing": False,
                              "stages": list(STAGES[job["kind"]])}
        self._order.append(pid)
        self._tasks[pid] = asyncio.create_task(self._run(pid, graph, job))
        return pid

    async def _send(self, job: dict) -> str:
        assert self.client
        if job["kind"] == "transcribe":
            data = self.uploads.pop(job.get("audio") or "", None)
            if data is None:
                raise RuntimeError("the recording was not sent to the engine")
            form = {"melody_only": "1"} if job.get("melody_only") else {}
            r = await self.client.post("/transcribe", files={"audio": (job["audio"], data)}, data=form, timeout=120.0)
        else:
            r = await self.client.post(job["path"], json=job["body"], timeout=30.0)
        if r.status_code >= 400:
            try:
                message = r.json().get("error") or r.text
            except ValueError:
                message = r.text
            raise RuntimeError(f"engine rejected the job: {message[:300]}")
        self._contact()
        return r.json()["id"]

    async def _run(self, pid: str, graph: dict, job: dict) -> None:
        rec = self.progress[pid]
        outputs: dict[str, Any] = {}
        status = "error"
        error = None
        try:
            server_id = await self._send(job)
            self.server_ids[pid] = server_id
            while True:
                await asyncio.sleep(self.POLL)
                r = await self.client.get("/job", params={"id": server_id}, timeout=10.0)
                if r.status_code == 404:
                    raise RuntimeError("the engine lost the job")
                state = r.json().get("status")
                self._contact()
                if state == "running":
                    continue
                if state == "cancelled":
                    error = "cancelled"
                    break
                if state == "failed":
                    error = rec.get("error") or "the engine could not finish the job"
                    break
                if state == "done":
                    res = await self.client.get("/job", params={"id": server_id, "result": "1"}, timeout=120.0)
                    res.raise_for_status()
                    outputs = await self._outputs(pid, job, res)
                    status = "success"
                    break
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            error = str(exc) or exc.__class__.__name__
            log.warning("yue2.cpp job %s failed: %s", pid, error)
        finally:
            self._tasks.pop(pid, None)
            if pid in self._order:
                self._order.remove(pid)
        if error and not rec.get("error"):
            rec["error"] = error[:300]
        rec["stage"] = rec["stages"][-1] if status == "success" else rec.get("stage")
        rec["frac"] = 1.0 if status == "success" else rec.get("frac", 0.0)
        self.results[pid] = {
            "prompt": [0, pid, graph, {}, []],
            "outputs": outputs,
            "status": {"status_str": status, "completed": status == "success",
                       "messages": [] if status == "success" else
                       [["execution_error", {"exception_message": error or "error", "node_type": "yue2.cpp"}]]},
        }

    async def _outputs(self, pid: str, job: dict, res: httpx.Response) -> dict[str, Any]:
        if job["kind"] in ("plan", "transcribe"):
            abc = (res.json() or {}).get("abc") or ""
            if job["kind"] == "plan" and (res.json() or {}).get("truncated"):
                log.info("yue2.cpp: the plan reached its token limit")
            return {str(job["output"]): {"text": [abc]}}
        parts = split_tracks(res.content, res.headers.get("content-type", ""))
        audio = next((p for p in parts if p["type"].startswith("audio/")), None)
        if not audio:
            raise RuntimeError("the engine returned no audio")
        raw = self._scratch / f"{pid}.wav"
        raw.write_bytes(audio["data"])
        name = f"{pid}.wav"
        self.files[name] = raw
        self.progress[pid]["ceiling_db"] = job.get("ceiling_db", config.PEAK_CEILING_DB)
        return {str(job["output"]): {"audio": [{"filename": name, "subfolder": "", "type": KIND}]}}

    async def history(self, prompt_id: str) -> dict[str, Any] | None:
        return self.results.get(prompt_id)

    async def prompt_state(self, prompt_id: str) -> str | None:
        if prompt_id in self._tasks:
            return "running" if self.progress.get(prompt_id, {}).get("executing") else "pending"
        return "gone"

    async def cancel(self, prompt_id: str) -> None:
        server_id = self.server_ids.get(prompt_id)
        if server_id and self.client:
            try:
                await self.client.post("/job", params={"id": server_id, "cancel": "1"}, timeout=4.0)
            except Exception as exc:  # noqa: BLE001
                log.warning("could not cancel %s on the engine: %s", prompt_id, exc)
        task = self._tasks.get(prompt_id)
        if task and not server_id:
            task.cancel()

    async def free(self) -> None:
        """Nothing to do: yue2.cpp lets go of the GPU after every job."""
        return

    async def interrupt(self) -> None:
        for pid in list(self._tasks):
            await self.cancel(pid)

    async def download(self, item: dict[str, Any], dest: Path) -> Path:
        src = self.files.pop(item.get("filename") or "", None)
        if not src or not src.is_file():
            raise RuntimeError("the render is no longer held for the app")
        pid = Path(item["filename"]).stem
        ceiling = float((self.progress.get(pid) or {}).get("ceiling_db", config.PEAK_CEILING_DB))
        dest.parent.mkdir(parents=True, exist_ok=True)
        partial = dest.with_name(dest.name + ".part" + dest.suffix)
        try:
            await asyncio.to_thread(level_to_flac, src, partial, ceiling)
            partial.replace(dest)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
        finally:
            src.unlink(missing_ok=True)
        return dest

    def forget(self, prompt_id: str) -> None:
        super().forget(prompt_id)
        self.results.pop(prompt_id, None)
        self.server_ids.pop(prompt_id, None)

    # ---------- the log ----------
    async def _log_loop(self) -> None:
        """Read the server's log as it is written: progress for the job it is on, its errors,
        out-of-memory, and the lines worth keeping in the app's log."""
        while True:
            try:
                assert self.client
                async with self.client.stream("GET", "/logs", timeout=httpx.Timeout(None, connect=4.0)) as r:
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if line.startswith("data: "):
                            self._handle_log(line[6:])
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.debug("engine log stream unavailable: %s", exc)
            await asyncio.sleep(3)

    def _active(self) -> dict[str, Any] | None:
        """The progress record of the job the server says it is on."""
        if not self._current_server_job:
            return None
        for pid, server_id in self.server_ids.items():
            if server_id == self._current_server_job and pid in self._tasks:
                return self.progress.get(pid)
        return None

    def _handle_log(self, text: str) -> None:
        line = text.strip()
        if not line:
            return
        started = JOB_START.match(line)
        if started:
            self._current_server_job = started.group(1)
            rec = self._active()
            if rec is not None:
                rec["executing"] = True
                rec["started"] = time.time()
                rec["stage"] = rec["stages"][0]
        rec = self._active()
        if rec is not None:
            for pattern, stage in STEP_LINES:
                step = pattern.match(line)
                if step and stage in rec["stages"]:
                    value, total = int(step.group(1)), int(step.group(2))
                    rec.update({"stage": stage, "value": value, "max": total,
                                "frac": value / total if total else 0.0})
                    break
            fatal = FATAL.search(line)
            if fatal:
                rec["error"] = fatal.group(1)[:300]
        if OUT_OF_MEMORY.search(line) or "out of memory" in line.lower():
            self.oom_at = time.time()
        if not NOISY.match(line):
            logging_setup.log_engine_entry(line)


def cpp_model_label(model: str) -> str:
    """How the model file reads in About: its precision."""
    found = re.search(r"-(BF16|F16|Q8_0|Q6_K|Q5_K_M|Q4_K_M)\.gguf$", model, re.I)
    quant = found.group(1).upper() if found else model
    return {"BF16": "Full quality (BF16)", "Q8_0": "Near full quality (Q8)", "Q6_K": "Smaller (Q6)",
            "Q5_K_M": "Smallest (Q5)"}.get(quant, quant) + ", yue2.cpp"


def make_engine(url: str, kind: str) -> Engine:
    """The client for the engine this install runs."""
    return CppEngine(url) if kind == KIND else Engine(url)


def describe(engine: Engine) -> dict[str, Any]:
    """Which engine, for the page: its kind and name, so it can say what needs the other one."""
    kind = getattr(engine, "kind", "comfyui")
    return {"kind": kind, "name": getattr(engine, "name", "ComfyUI")}

