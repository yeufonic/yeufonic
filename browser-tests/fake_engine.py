"""A stand-in for ComfyUI, for the browser tests: the HTTP API the app uses, answering every graph quickly.

It lists every node the app's graphs use, with the models a full install has, so every feature is offered.  A graph
"runs" for a moment, then its history holds what the app reads: a score for a plan or a transcription, words for a
lyric draft or a picture description, segments for hearing a recording, audio for a render or a stem, a picture for
klein.  Nothing is computed; the audio is a few seconds of tones, so a take plays.

    python browser-tests/fake_engine.py --port 8199

GET /calls lists what was asked of it, for a test to check what the app sent.
"""
import argparse
import io
import json
import re
import struct
import sys
import threading
import time
import uuid
import wave
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config  # noqa: E402  the model names the app looks for

RUN_SECONDS = 1.0
LOCK = threading.Lock()
JOBS: dict[str, dict] = {}      # prompt id -> {"graph", "started", "outputs", "number", "extra"}
FILES: dict[str, bytes] = {}    # file name -> bytes, for /view
UPLOADS: dict[str, bytes] = {}  # what the app uploaded, by the name it was given
CALLS: list[dict] = []
COUNTER = [0]


def object_info() -> dict:
    """Every node type the app's graphs name, each with the choices the app reads."""
    nodes = {n: {"input": {"required": {}, "optional": {}}} for n in (
        "AudioEncoderLoader", "CFGGuider", "CLIPLoader", "CLIPTextEncode", "CheckpointLoaderSimple",
        "ConditioningZeroOut", "EmptyFlux2LatentImage", "EmptyYuE2LatentAudio", "Flux2Scheduler", "KSampler",
        "KSamplerSelect", "LoadAudio", "LoraLoader", "PreviewAny", "RandomNoise", "SamplerCustomAdvanced", "SaveAudio",
        "SaveAudioAdvanced", "SaveImage", "SheetSage2AudioToABC", "TextGenerate", "UNETLoader", "VAEDecode",
        "VAEDecodeAudioTiled", "VAELoader", "YuE2GenerateABC", "YuE2GenerateABCHarmony", "YuE2GenerateMusic",
        "YuE2TrainerAcousticLoRA", "YuE2TrainerDatasetFolder", "YuE2TrainerEncodeDataset", "YuE2TrainerPlannerLoRA",
        "YuE2TrainerRegularizationScores", "YuE2TrainerSaveLoRA", "Yue2Hear", "Yue2PeakGuard", "Yue2Separate")}
    four, nine = config.PICTURE_PAIRS[0], config.PICTURE_PAIRS_9B[0]
    nodes["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"] = [[config.CHECKPOINT_BF16]]
    nodes["AudioEncoderLoader"]["input"]["required"]["audio_encoder_name"] = [["sheetsage2_bf16.safetensors"]]
    nodes["CLIPLoader"]["input"]["required"]["clip_name"] = [[config.LYRICS_MODEL, four[1], nine[1]]]
    nodes["UNETLoader"]["input"]["required"]["unet_name"] = [[four[0], nine[0]]]
    nodes["VAELoader"]["input"]["required"]["vae_name"] = [[config.PICTURE_VAE]]
    nodes["LoraLoader"]["input"]["required"]["lora_name"] = [[config.INSTRUMENTAL_LORA, config.REAL_AUDIO_LORA,
                                                              "bright-pop.safetensors"]]
    nodes["YuE2GenerateABCHarmony"]["input"]["optional"]["hook_body"] = ["STRING", {}]
    return nodes


def tones(seconds: float = 8.0, rate: int = 22050) -> bytes:
    """A stereo WAV of changing chords, loud enough not to read as a weak render."""
    import numpy as np
    t = np.arange(int(seconds * rate)) / rate
    chords = np.array(((261.6, 329.6, 392.0), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7)))
    freqs = chords[(t // 2).astype(int) % len(chords)]
    v = np.sin(2 * np.pi * freqs * t[:, None]).mean(axis=1) * 0.4
    pcm = (np.clip(v, -1, 1) * 32767).astype("<i2")
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(np.repeat(pcm, 2).tobytes())
    return out.getvalue()


def render_seconds(graph: dict) -> float:
    """As long as the score the render was given, as the model would play it, so it does not read as cut short."""
    from app.score import estimate
    for node in graph.values():
        for value in (node.get("inputs") or {}).values():
            if isinstance(value, str) and value.lstrip().startswith("X:"):
                planned = estimate(value) or {}
                return max(4.0, min(120.0, float(planned.get("seconds") or 8.0)))
    return 8.0


def png(width: int = 64, height: int = 64) -> bytes:
    """A small colourful PNG, as klein would hand back a picture."""
    rows = b"".join(b"\x00" + bytes(((x * 4) % 256, (y * 4) % 256, ((x + y) * 2) % 256)[c]
                                    for x in range(width) for c in range(3)) for y in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def score(sections: list[str], bars: int = 8) -> str:
    """A score that passes the app's check: a key, a Vocal part with chords, enough bars, a section per tag.  An
    instrumental's, as the instrumental LoRA writes it: the Vocal voice rests under the chords, the tune is in Ins."""
    if all(name == "instrumental" for name in sections):
        body = "".join(f"% {name}\nV: Vocal\n" + "".join(('"C"z8|', '"Am"z8|', '"F"z8|', '"G"z8|')[i % 4] for i in range(bars))
                       + "\nV: Ins\n" + "".join(("c8|", "A8|", "F8|", "G8|")[i % 4] for i in range(bars)) + "\n"
                       for name in sections)
    else:
        body = "".join(f"% {name}\nV: Vocal\n" + "".join(('"C"c8|', '"Am"A8|', '"F"F8|', '"G"G8|')[i % 4] for i in range(bars))
                       + "\n" for name in sections)
    return ('X:1\nM:4/4\nL:1/8\nQ:1/4=100\nV: Vocal clef=treble name="Vocal Melody" snm="Vocal"\nK:C\n' + body)


def uploaded_seconds(graph: dict) -> float:
    """How long the recording a graph loads is, from the copy the app uploaded."""
    for node in graph.values():
        if node.get("class_type") == "LoadAudio":
            data = UPLOADS.get(str((node.get("inputs") or {}).get("audio")))
            if data:
                try:
                    with wave.open(io.BytesIO(data)) as w:
                        return w.getnframes() / w.getframerate()
                except (wave.Error, EOFError):
                    pass
    return 12.0


def sections_of(graph: dict) -> list[str]:
    words = " ".join(str(v) for node in graph.values() for v in (node.get("inputs") or {}).values() if isinstance(v, str))
    found = re.findall(r"\[(verse|chorus|bridge|intro|outro|pre-chorus|instrumental)[^\]]*\]", words, re.I)
    return [s.lower() for s in found] or ["verse", "chorus"]


LYRICS = ("[verse]\nLights along the harbour wall\nA ship goes out into the fog\n"
          "[chorus]\nHold on, hold on\nThe tide will bring it home\n")
DESCRIPTION = "A lighthouse on a rocky shore at dusk, warm light across a calm sea, painted in bold colours."
HEARD = [{"start": 0.5, "end": 3.0, "text": "Lights along the harbour wall"},
         {"start": 3.5, "end": 6.5, "text": "A ship goes out into the fog"}]


def finish(prompt_id: str, graph: dict) -> dict:
    """What the graph's output nodes hold when it is done."""
    outputs = {}
    for nid, node in graph.items():
        kind = node.get("class_type")
        if kind == "PreviewAny":
            source = (node.get("inputs") or {}).get("source") or [None]
            upstream = (graph.get(str(source[0])) or {}).get("class_type", "")
            if upstream == "SheetSage2AudioToABC":
                # A transcription as long as the recording: a bar of 4/4 at 100 BPM is 2.4 s.
                text = score(["verse"], bars=max(2, round(uploaded_seconds(graph) / 2.4)))
            elif upstream in ("YuE2GenerateABC", "YuE2GenerateABCHarmony"):
                text = score(sections_of(graph), bars=4)
            elif upstream == "Yue2Hear":
                text = json.dumps(HEARD)
            elif upstream == "TextGenerate":
                # Asked for a picture's scene (artwork.describe_graph) or for lyrics (llm's draft): only the first
                # names Hipgnosis.
                prompt = json.dumps(graph).lower()
                text = DESCRIPTION if "hipgnosis" in prompt else LYRICS
            else:
                text = ""
            outputs[nid] = {"text": [text]}
        elif kind in ("SaveAudio", "SaveAudioAdvanced"):
            name = f"fake-{prompt_id[:8]}-{nid}.wav"
            FILES[name] = tones(render_seconds(graph))
            outputs[nid] = {"audio": [{"filename": name, "subfolder": "", "type": "output"}]}
        elif kind == "SaveImage":
            name = f"fake-{prompt_id[:8]}-{nid}.png"
            FILES[name] = png()
            outputs[nid] = {"images": [{"filename": name, "subfolder": "", "type": "output"}]}
    return outputs


def queue() -> dict:
    now = time.time()
    running, pending = [], []
    with LOCK:
        live = [(pid, job) for pid, job in JOBS.items() if job.get("outputs") is None]
        live.sort(key=lambda item: item[1]["number"])
        for i, (pid, job) in enumerate(live):
            entry = [job["number"], pid, job["graph"], job["extra"], []]
            (running if i == 0 else pending).append(entry)
            if i == 0 and job.get("running_from") is None:
                job["running_from"] = now
            if i == 0 and now - job["running_from"] >= RUN_SECONDS:
                job["outputs"] = finish(pid, job["graph"])
                job["finished"] = now
    return {"queue_running": running, "queue_pending": pending}


def ticker() -> None:
    while True:
        queue()
        time.sleep(0.2)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, body, status=200, kind="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self) -> bytes:
        return self.rfile.read(int(self.headers.get("Content-Length") or 0))

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/object_info":
            return self.reply(object_info())
        if url.path == "/system_stats":
            return self.reply({"system": {"os": "posix", "pytorch_version": "2.9.1+cu130", "comfyui_version": "fake",
                                          "ram_total": 32 * 2**30, "ram_free": 16 * 2**30},
                               "devices": [{"name": "cuda:0 Fake GPU", "type": "cuda", "index": 0,
                                            "vram_total": 16 * 2**30, "vram_free": 15 * 2**30,
                                            "torch_vram_total": 0, "torch_vram_free": 0}]})
        if url.path == "/queue":
            return self.reply(queue())
        if url.path.startswith("/history/"):
            pid = url.path.rsplit("/", 1)[1]
            with LOCK:
                job = JOBS.get(pid)
                if not job or job.get("outputs") is None:
                    return self.reply({})
                return self.reply({pid: {
                    "prompt": [job["number"], pid, job["graph"], job["extra"], list(job["outputs"])],
                    "outputs": job["outputs"],
                    "status": {"status_str": "success", "completed": True, "messages": []}}})
        if url.path == "/view":
            name = (parse_qs(url.query).get("filename") or [""])[0]
            if name not in FILES:
                return self.reply({"error": "no such file"}, 404)
            return self.reply(FILES[name], kind="audio/wav" if name.endswith(".wav") else "image/png")
        if url.path == "/calls":
            return self.reply(CALLS)
        return self.reply({"error": "not here"}, 404)

    def do_POST(self):
        url = urlparse(self.path)
        raw = self.body()
        if url.path == "/prompt":
            payload = json.loads(raw or b"{}")
            pid = str(uuid.uuid4())
            with LOCK:
                COUNTER[0] += 1
                JOBS[pid] = {"graph": payload.get("prompt") or {}, "number": COUNTER[0], "outputs": None,
                             "extra": {"client_id": payload.get("client_id", ""), "create_time": int(time.time() * 1000)}}
                CALLS.append({"path": "/prompt", "classes": sorted({n.get("class_type") for n in JOBS[pid]["graph"].values()})})
            return self.reply({"prompt_id": pid, "number": COUNTER[0], "node_errors": {}})
        if url.path == "/upload/image":
            # A multipart form: the file's name is all the app reads back.
            match = re.search(rb'filename="([^"]+)"\r\n(?:[^\r\n]+\r\n)*\r\n', raw)
            name = match.group(1).decode() if match else f"upload-{uuid.uuid4().hex[:8]}"
            if match:
                boundary = raw.split(b"\r\n", 1)[0]
                UPLOADS[name] = raw[match.end():raw.index(b"\r\n" + boundary, match.end())]
            CALLS.append({"path": "/upload/image", "name": name})
            return self.reply({"name": name, "subfolder": "", "type": "input"})
        if url.path == "/queue":
            payload = json.loads(raw or b"{}")
            with LOCK:
                for pid in payload.get("delete") or []:
                    JOBS.pop(pid, None)
            return self.reply({})
        if url.path in ("/interrupt", "/free"):
            CALLS.append({"path": url.path})
            return self.reply({})
        return self.reply({"error": "not here"}, 404)

    def do_PATCH(self):
        self.body()
        return self.reply({})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8199)
    args = parser.parse_args()
    threading.Thread(target=ticker, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
