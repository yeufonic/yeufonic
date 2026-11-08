"""The voice service: train a recorded voice, and sing a take's vocal in it.

A small HTTP server in front of RVC (MIT) and a BS-Roformer separator, run one job at a time.  The app owns the
GPU schedule: it frees the engine before it asks for anything here, so this never shares the card with a render.

    GET  /health                    {"ok": true, "models": {...}}
    POST /train    {"id", "sources": [paths], "separate": bool, "epochs": int}    -> {"job": id}
    GET  /jobs/<id>                 {"state": queued|running|done|failed, "progress": 0..1, "stage", "error"}
    POST /jobs/<id>/stop            ends a training run: the step under way is terminated, its files removed
    POST /convert  {"id", "input", "output", "octave": int}                        -> {"ok": true} when written

Paths are the app's own (/data/...): this container mounts the same data folder.  A voice's files go to
/data/voices/<id>/: model.pth and model.index, vocals/ (each song separated) and excerpts/ (what was trained on), and a
work folder that is removed once training succeeds.
"""
from __future__ import annotations

import glob
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Where RVC is: /opt/rvc in the container; the Windows install sets RVC_DIR to its own copy.  Its scripts read their
# models from assets/ and write to logs/ beside them, relative to where they run.
RVC = Path(os.environ.get("RVC_DIR", "/opt/rvc"))
ASSETS = RVC / "assets"                  # in the container, mounted from models/voice/assets
LOGS = RVC / "logs"                      # in the container, mounted from models/voice/logs (holds RVC's "mute" samples)
VOICES = Path(os.environ.get("VOICES_DIR", "/data/voices"))
SEPARATOR = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
SR, HZ = "48k", "48000"
PY = sys.executable                      # RVC's steps run in this service's own Python
HOST = os.environ.get("VOICE_HOST", "0.0.0.0")
PORT = int(os.environ.get("VOICE_PORT", "8190"))
# What RVC's scripts need wherever they run: their imports from the repository root, without this file's folder
# shadowing RVC's own "train" package, and no CUDA graphs (they failed in the container's first runs).
for key, value in (("PYTHONPATH", str(RVC)), ("PYTHONSAFEPATH", "1"), ("RVC_CUDA_GRAPH", "0"), ("PYTHONUNBUFFERED", "1"),
                   ("PYTHONUTF8", "1")):
    os.environ.setdefault(key, value)

JOBS: dict[str, dict] = {}
LOCK = threading.Lock()                  # one GPU job at a time: a training run or a conversion
RUNNING: dict = {}                       # the step under way, so a stop can end it: {"job": id, "proc": Popen}


def batch_size() -> int:
    """Clips trained on at once, by the card's memory (the engine is unloaded while a voice trains)."""
    try:
        got = subprocess.run([PY, "-c", "import torch; print(torch.cuda.get_device_properties(0).total_memory)"],
                             capture_output=True, text=True, timeout=60)
        gib = int(got.stdout.strip()) / 2**30
    except Exception:  # noqa: BLE001 - no card to ask: the cautious size
        return 4
    return 2 if gib < 7 else 4 if gib < 11 else 8 if gib < 20 else 12


BATCH = 4


class Stopped(Exception):
    pass


def needed() -> dict:
    """The model files this service cannot work without, and whether each is there."""
    files = {
        "content encoder": ASSETS / "hubert_base" / "pytorch_model.bin",
        "pitch tracker": ASSETS / "rmvpe" / "rmvpe.pt",
        "base generator": ASSETS / "pretrained_v2" / f"f0G{SR}.pth",
        "base discriminator": ASSETS / "pretrained_v2" / f"f0D{SR}.pth",
        "separator": ASSETS / "pymss" / "vocal" / "vocal_extraction" / SEPARATOR,
        "silence samples": LOGS / "mute" / "0_gt_wavs" / f"mute{SR}.wav",
    }
    return {name: path.exists() for name, path in files.items()}


def run(args: list[str], job: dict | None = None, log: Path | None = None) -> None:
    """One RVC step.  Its output goes to the job's log, which training reads its epoch from."""
    if job is not None and job.get("stop"):
        raise Stopped()
    out = open(log, "a", encoding="utf-8") if log else subprocess.DEVNULL
    try:
        proc = subprocess.Popen([PY, *args], cwd=RVC, stdout=out, stderr=subprocess.STDOUT)
        RUNNING.update(job=job, proc=proc)
        proc.wait()
    finally:
        RUNNING.clear()
        if log:
            out.close()
    if job is not None and job.get("stop"):
        raise Stopped()
    if proc.returncode != 0:
        raise RuntimeError(f"{Path(args[0]).name} failed: {_reason(log)}")


def _reason(log: Path | None) -> str:
    """The last error line of a step's log, rather than a traceback's tail: what the app shows and logs."""
    if not log or not log.exists():
        return "no log"
    lines = [line.strip() for line in log.read_text(encoding="utf-8", errors="replace").splitlines()]
    errors = [line for line in lines if re.match(r"^[\w.]*(Error|Exception)\b", line) and "Warning" not in line]
    return (errors[-1] if errors else next((line for line in reversed(lines) if line), "no output"))[:300]


def separate(source: Path, out_dir: Path) -> tuple[Path, Path]:
    """A recording split into its vocal and the rest, with BS-Roformer."""
    out_dir.mkdir(parents=True, exist_ok=True)
    run(["-m", "tools.pymss.cli", "infer", "--model-dir", str(ASSETS / "pymss"), "-i", str(source), "-o", str(out_dir),
         "--device", "cuda", "--format", "flac", "--flac-bit-depth", "PCM_24", SEPARATOR])
    stem = source.stem
    vocals = next(iter(glob.glob(str(out_dir / f"{glob.escape(stem)}_Vocals.flac"))), None)
    rest = next(iter(glob.glob(str(out_dir / f"{glob.escape(stem)}_Instrumental.flac"))), None)
    if not vocals or not rest:
        raise RuntimeError(f"the separator wrote nothing for {source.name}")
    return Path(vocals), Path(rest)


def mono(source: Path, dest: Path) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-ac", "1", "-ar", "44100", str(dest)], check=True)


FRAME_SECONDS = 0.05
SINGING_BELOW_LOUD_DB = 25.0      # a frame counts as singing within this many dB of the vocal's loud passages


def singing_frames(samples, rate: int):
    """Which 50 ms frames of a separated vocal hold singing: within 25 dB of its loud passages (95th percentile)."""
    import numpy as np  # noqa: PLC0415 - only the training path needs it

    hop = max(1, int(rate * FRAME_SECONDS))
    count = len(samples) // hop
    if count == 0:
        return np.zeros(0, dtype=bool)
    frames = samples[: count * hop].reshape(count, hop)
    rms = np.sqrt((frames.astype("float64") ** 2).mean(axis=1)) + 1e-9
    loud = np.percentile(rms, 95)
    return rms > loud * 10 ** (-SINGING_BELOW_LOUD_DB / 20)


def share_out(singing: list[float], total: float) -> list[float]:
    """How many seconds of singing to take from each song: an equal share of the total, and what a song lacks of its
    share goes to the others."""
    shares = [0.0] * len(singing)
    open_ = [i for i, have in enumerate(singing) if have > 0]
    left = total
    while open_ and left > 1e-6:
        each = left / len(open_)
        short = [i for i in open_ if singing[i] - shares[i] <= each]
        if not short:
            for i in open_:
                shares[i] += each
            break
        for i in short:
            left -= singing[i] - shares[i]
            shares[i] = singing[i]
        open_ = [i for i in open_ if i not in short]
    return shares


def excerpt_with(mask, need_frames: int) -> tuple[int, int]:
    """The frames [a, b) around the middle of a vocal that hold `need_frames` of singing (all of it if it has less)."""
    a = b = len(mask) // 2
    have = 0
    while have < need_frames and (a > 0 or b < len(mask)):
        if b < len(mask):
            have += int(mask[b])
            b += 1
        if have < need_frames and a > 0:
            a -= 1
            have += int(mask[a])
    return a, b


def train(job: dict, voice: str, sources: list, default_split: bool, epochs: int, minutes: float = 0.0) -> None:
    folder = VOICES / voice
    work = folder / "work"
    shutil.rmtree(work, ignore_errors=True)
    trainset = work / "trainset"
    trainset.mkdir(parents=True)
    log = work / "train.log"
    kept = work / "vocals"   # each song's separated vocal, kept with the voice once it has trained
    kept.mkdir()
    vocals = []
    for index, item in enumerate(sources):
        # Each source says whether it is separated first (a full song) or used as it is (vocals alone); a plain path
        # follows the request's own "separate".
        name, split = (item["path"], bool(item.get("separate", True))) if isinstance(item, dict) else (item, default_split)
        job.update(stage="separating" if split else "preparing", progress=0.1 * index / max(1, len(sources)))
        source = Path(name)
        print(f"[{voice}] {job['stage']} {index + 1}/{len(sources)}: {source.name}", flush=True)
        if job.get("stop"):
            raise Stopped()
        vocal = separate(source, work / "sep")[0] if split else source
        if split:   # corpus songs are all "original.*", so the song's folder names it
            label = source.parent.name if source.stem == "original" else source.stem
            shutil.move(str(vocal), kept / f"{index:03d} {label}.flac")
            vocal = kept / f"{index:03d} {label}.flac"
        staged = work / "mono" / f"{index:03d}.wav"
        staged.parent.mkdir(parents=True, exist_ok=True)
        mono(vocal, staged)
        vocals.append(staged)
    # The singing asked for, shared across the songs: each gives the stretch around its middle that holds its share.
    import soundfile  # noqa: PLC0415 - only training needs it, and only from here on

    loaded = [soundfile.read(str(path), dtype="float32") for path in vocals]
    masks = [singing_frames(samples, rate) for samples, rate in loaded]
    singing = [float(mask.sum()) * FRAME_SECONDS for mask in masks]
    shares = share_out(singing, minutes * 60) if minutes > 0 else singing
    for index, ((samples, rate), mask, share) in enumerate(zip(loaded, masks, shares)):
        if share <= 0:
            continue
        a, b = excerpt_with(mask, int(round(share / FRAME_SECONDS)))
        hop = max(1, int(rate * FRAME_SECONDS))
        soundfile.write(str(trainset / f"{index:03d}.wav"), samples[a * hop: b * hop], rate)
    job.update(singing_seconds=round(sum(shares)), available_seconds=round(sum(singing)))
    print(f"[{voice}] {sum(shares) / 60:.1f} of {sum(singing) / 60:.1f} minutes of singing, from {len(vocals)} "
          f"recording(s)", flush=True)
    shutil.rmtree(work / "mono", ignore_errors=True)
    if not any(trainset.iterdir()):
        raise RuntimeError("no singing was found in these recordings")
    exp = f"v-{voice}"
    logs = LOGS / exp
    shutil.rmtree(logs, ignore_errors=True)
    logs.mkdir(parents=True)
    job.update(stage="analysing", progress=0.1)
    run(["train/preprocess.py", str(trainset), HZ, str(max(1, (os.cpu_count() or 4) // 2)), str(logs), "False", "3.7"],
        job=job, log=log)
    run(["train/dataset/extract_f0.py", "cuda", "1", "0", "0", str(logs), "True"], job=job, log=log)
    run(["train/dataset/extract_hubert_feature.py", "cuda:0", "1", "0", "0", str(logs), "v2", "True"], job=job, log=log)
    gt, fea, f0, f0n = (logs / d for d in ("0_gt_wavs", "3_feature768", "2a_f0", "2b-f0nsf"))
    stems = lambda d: {n.split(".")[0] for n in os.listdir(d)}  # noqa: E731
    names = stems(gt) & stems(fea) & stems(f0) & stems(f0n)
    if not names:
        raise RuntimeError("no singing was found in these recordings")
    lines = [f"{gt}/{n}.wav|{fea}/{n}.npy|{f0}/{n}.wav.npy|{f0n}/{n}.wav.npy|0" for n in sorted(names)]
    m = LOGS / "mute"
    lines += [f"{m}/0_gt_wavs/mute{SR}.wav|{m}/3_feature768/mute.npy|{m}/2a_f0/mute.wav.npy|{m}/2b-f0nsf/mute.wav.npy|0"] * 2
    random.shuffle(lines)
    (logs / "filelist.txt").write_text("\n".join(lines), encoding="utf-8")
    shutil.copy(RVC / "configs" / "v2" / f"{SR}.json", logs / "config.json")
    (ASSETS / "weights").mkdir(parents=True, exist_ok=True)
    job.update(stage="training", progress=0.15, clips=len(names))
    print(f"[{voice}] training on {len(names)} clips, {epochs} passes", flush=True)
    watcher = threading.Thread(target=_follow_epochs, args=(job, log, epochs), daemon=True)
    watcher.start()
    # The batch follows the card's memory (batch_size): the engine is freed first, so the card is the voice's.
    run(["train/train.py", "-e", exp, "-sr", SR, "-f0", "1", "-bs", str(BATCH), "-g", "0", "-te", str(epochs),
         "-se", str(epochs), "-pg", f"assets/pretrained_v2/f0G{SR}.pth", "-pd", f"assets/pretrained_v2/f0D{SR}.pth",
         "-l", "1", "-c", "0", "-sw", "0", "-v", "v2"], job=job, log=log)
    job["epochs_done"] = epochs
    small = ASSETS / "weights" / f"{exp}.pth"
    if not small.exists():   # RVC's final save can fail on its own; the last checkpoint holds the same weights
        # Paths as Python literals (repr): a Windows path's backslashes would be read as escapes.
        run(["-c", "from train.process_ckpt import extract_small_model as x; import sys; "
                   f"print(x({str(logs / 'G_2333333.pth')!r}, {exp!r}, {SR!r}, 1, 'Yeufonic voice', 'v2'))"], log=log)
    job.update(stage="indexing", progress=0.97)
    print(f"[{voice}] building the index", flush=True)
    run(["train/train_index.py", exp, "v2", str(ASSETS / "indices"), str(max(1, (os.cpu_count() or 4) // 2)), "single"],
        log=log)
    index = next(iter(sorted(logs.glob("added_*.index"))), None)
    if not small.exists() or index is None:
        raise RuntimeError("training finished without a model")
    shutil.move(str(small), folder / "model.pth")
    shutil.copy(index, folder / "model.index")
    for name, made in (("vocals", kept), ("excerpts", trainset)):   # what it learned from: whole, and as trained
        shutil.rmtree(folder / name, ignore_errors=True)
        if any(made.iterdir()):
            shutil.move(str(made), folder / name)
    shutil.rmtree(logs, ignore_errors=True)          # the checkpoints are half a gigabyte; the model is all that is used
    for linked in (ASSETS / "indices").glob(f"*{exp}*"):
        linked.unlink(missing_ok=True)
    shutil.rmtree(work, ignore_errors=True)


def _follow_epochs(job: dict, log: Path, epochs: int) -> None:
    while job.get("state") == "running" and not job.get("epochs_done"):
        try:
            text = log.read_text(encoding="utf-8", errors="replace")
            found = [int(x) for x in __import__("re").findall(r"Epoch: ?(\d+)", text)]
            if found:
                job["progress"] = 0.15 + 0.8 * min(1.0, max(found) / epochs)
        except OSError:
            pass
        time.sleep(5)


MAX_LEVEL_DB = 12.0       # the most the converted vocal is moved to meet the original's level
MAX_PRESENCE_DB = 6.0     # the most its presence (2 kHz and up) is lifted to meet the original's
ROOM_WET = 0.14           # how much of a short synthetic room goes under the converted vocal
ROOM_SECONDS = 1.2


def _biquad(kind: str, f0: float, rate: int, q: float, gain_db: float = 0.0):
    """RBJ cookbook coefficients (b, a) for a high shelf or a high pass."""
    import numpy as np  # noqa: PLC0415

    amp = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / rate
    alpha = np.sin(w0) / (2 * q)
    cos = np.cos(w0)
    if kind == "highshelf":
        sq = 2 * np.sqrt(amp) * alpha
        b = [amp * ((amp + 1) + (amp - 1) * cos + sq), -2 * amp * ((amp - 1) + (amp + 1) * cos),
             amp * ((amp + 1) + (amp - 1) * cos - sq)]
        a = [(amp + 1) - (amp - 1) * cos + sq, 2 * ((amp - 1) - (amp + 1) * cos), (amp + 1) - (amp - 1) * cos - sq]
    else:
        b = [(1 + cos) / 2, -(1 + cos), (1 + cos) / 2]
        a = [1 + alpha, -2 * cos, 1 - alpha]
    return np.array(b) / a[0], np.array(a) / a[0]


def _mono(samples):
    return samples.mean(axis=1) if samples.ndim > 1 else samples


def _loudness(samples, rate: int) -> float:
    """The vocal's loudness over its singing as the ear weighs it (BS.1770's K-weighting), not its plain RMS: a
    converted vocal with less presence sounds quieter at the same RMS."""
    from scipy.signal import lfilter  # noqa: PLC0415

    x = _mono(samples).astype("float64")
    x = lfilter(*_biquad("highshelf", 1681.97, rate, 0.7072, 4.0), x)
    x = lfilter(*_biquad("highpass", 38.135, rate, 0.5003), x)
    return _singing_rms(x, rate, _mono(samples))


def _singing_rms(samples, rate: int, gate=None) -> float:
    import numpy as np  # noqa: PLC0415

    mono = _mono(samples)
    mask = singing_frames(_mono(gate) if gate is not None else mono, rate)
    hop = max(1, int(rate * FRAME_SECONDS))
    count = min(len(mask), len(mono) // hop)
    frames = mono[: count * hop].reshape(count, hop)[mask[:count]] if mask[:count].any() else mono[None, :]
    return float(np.sqrt((frames.astype("float64") ** 2).mean()) + 1e-9)


def _presence(samples, rate: int) -> float:
    """How much of the vocal's energy lies at 2-8 kHz against 300 Hz-2 kHz, in dB: where its words and edge are."""
    import numpy as np  # noqa: PLC0415

    x = _mono(samples)[: rate * 90]
    spectrum = np.abs(np.fft.rfft(x)) ** 2
    freqs = np.fft.rfftfreq(len(x), 1 / rate)
    high = spectrum[(freqs >= 2000) & (freqs < 8000)].sum()
    body = spectrum[(freqs >= 300) & (freqs < 2000)].sum()
    return float(10 * np.log10((high + 1e-12) / (body + 1e-12)))


def settle(original: Path, sung: Path, voice: str = "", level_db: float = 0.0) -> None:
    """Put the converted vocal where the rendered one sat: its presence, its loudness, and a little room.

    RVC returns a vocal with less presence than the one it was given, and dry, so it sounded low and apart from the
    backing even at the same level. Its 2 kHz-and-up is lifted towards the original's balance (up to 6 dB, never
    cut), its loudness over the singing matched to the original's as the ear weighs it, and a short decaying room
    mixed under it so it shares a space with the mix rather than lying on top of it.
    """
    import numpy as np  # noqa: PLC0415
    import soundfile  # noqa: PLC0415
    from scipy.signal import fftconvolve, lfilter  # noqa: PLC0415

    before, before_rate = soundfile.read(str(original), dtype="float32")
    after, rate = soundfile.read(str(sung), dtype="float32")
    dry = _mono(after).astype("float64")
    lift = float(np.clip(_presence(before, before_rate) - _presence(dry, rate), 0.0, MAX_PRESENCE_DB))
    if lift > 0.5:
        dry = lfilter(*_biquad("highshelf", 2500.0, rate, 0.7, lift), dry)
    gain_db = 20 * np.log10(_loudness(before, before_rate) / _loudness(dry, rate))
    gain_db = float(np.clip(gain_db, -MAX_LEVEL_DB, MAX_LEVEL_DB)) + float(level_db)   # then the voice's own setting
    dry = dry * 10 ** (gain_db / 20)
    rng = np.random.default_rng(7)                       # the same room every time
    length = int(rate * ROOM_SECONDS)
    tail = rng.standard_normal(length) * np.exp(-np.arange(length) / (rate * ROOM_SECONDS / 6))
    tail[: int(rate * 0.012)] = 0                        # a short gap before the room answers
    tail /= np.sqrt((tail ** 2).sum())
    mixed = dry + ROOM_WET * fftconvolve(dry, tail)[: len(dry)]
    # Kept in float, peaks and all: scaling the vocal alone to stop it clipping undid the level set above.  The
    # finished mix is brought under full scale as a whole instead (convert), which keeps the balance.
    soundfile.write(str(sung), mixed.astype("float32"), rate, subtype="FLOAT")
    print(f"[{voice}] converted vocal: presence {lift:+.1f} dB, level {gain_db:+.1f} dB to the rendered vocal's",
          flush=True)


def convert(voice: str, source: Path, output: Path, octave: int, level_db: float = 0.0, likeness: float = 0.75,
            backing_db: float = 0.0) -> None:
    folder = VOICES / voice
    model, index = folder / "model.pth", folder / "model.index"
    if not model.exists():
        raise RuntimeError("this voice has no trained model")
    work = Path(tempfile.mkdtemp(prefix="convert-", dir=str(VOICES)))
    try:
        vocals, rest = separate(source, work / "sep")
        sung = work / "sung.wav"
        run(["infer/cli.py", "--model", str(model), "--input", str(vocals), "--output", str(sung), "--format", "wav",
             "--f0-method", "rmvpe", "--pitch", str(12 * int(octave)), *(["--index", str(index)] if index.exists() else []),
             "--index-rate", f"{min(1.0, max(0.0, likeness)):.2f}", "--protect", "0.33", "--rms-mix-rate", "0.25", "--overwrite"])
        if not sung.exists():
            raise RuntimeError("the conversion wrote nothing")
        settle(vocals, sung, voice, level_db)
        mixed = work / "mixed.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(rest), "-i", str(sung), "-filter_complex",
                        "[1:a]aresample=44100,aformat=sample_fmts=flt:channel_layouts=stereo[v];"
                        f"[0:a]aresample=44100,aformat=sample_fmts=flt,volume={float(backing_db):.1f}dB[i];"
                        "[i][v]amix=inputs=2:normalize=0[m]", "-map", "[m]", "-c:a", "pcm_f32le", str(mixed)], check=True)
        import soundfile  # noqa: PLC0415

        samples, rate = soundfile.read(str(mixed), dtype="float32")
        peak = float(abs(samples).max()) if samples.size else 0.0
        if peak > 0.98:     # the whole mix down, vocal and backing together, so the balance set holds
            samples *= 0.98 / peak
        final = work / f"final{output.suffix or '.flac'}"
        soundfile.write(str(final), samples, rate)
        print(f"[{voice}] mixed: vocal {level_db:+.0f} dB, backing {backing_db:+.0f} dB"
              + (f", whole mix {20 * math.log10(0.98 / peak):+.1f} dB to stay under full scale" if peak > 0.98 else ""),
              flush=True)
        shutil.move(str(final), output)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _train_job(job_id: str, body: dict) -> None:
    job = JOBS[job_id]
    with LOCK:
        if job.get("stop"):
            job["state"] = "stopped"
            return
        job["state"] = "running"
        try:
            train(job, body["id"], list(body.get("sources") or []), bool(body.get("separate", True)),
                  int(body.get("epochs") or 100), float(body.get("minutes") or 0))
            job.update(state="done", progress=1.0, stage=None)
            print(f"[{body['id']}] trained", flush=True)
        except Stopped:
            job.update(state="stopped", stage=None)
            shutil.rmtree(VOICES / body["id"] / "work", ignore_errors=True)
            shutil.rmtree(LOGS / f"v-{body['id']}", ignore_errors=True)
        except Exception as err:  # noqa: BLE001 - every failure is reported to the app
            traceback.print_exc()
            job.update(state="failed", error=str(err)[-800:])
            # The reason is in the job; what a failed run left (half a gigabyte of checkpoints) is not kept.
            shutil.rmtree(VOICES / body["id"] / "work", ignore_errors=True)
            shutil.rmtree(LOGS / f"v-{body['id']}", ignore_errors=True)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, data: dict) -> None:
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # noqa: D102 - quiet: the app logs what matters
        pass

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            models = needed()
            return self._send(200, {"ok": all(models.values()), "models": models, "batch": BATCH})
        if self.path.startswith("/jobs/"):
            job = JOBS.get(self.path.split("/", 2)[2])
            return self._send(200, job) if job else self._send(404, {"error": "no such job"})
        self._send(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except ValueError:
            return self._send(400, {"error": "not JSON"})
        if self.path == "/train":
            job_id = f"train-{body.get('id')}-{int(time.time())}"
            JOBS[job_id] = {"state": "queued", "progress": 0.0, "stage": None, "error": None}
            threading.Thread(target=_train_job, args=(job_id, body), daemon=True).start()
            return self._send(200, {"job": job_id})
        if self.path.startswith("/jobs/") and self.path.endswith("/stop"):
            job = JOBS.get(self.path.split("/")[2])
            if not job:
                return self._send(404, {"error": "no such job"})
            job["stop"] = True
            if job.get("state") == "queued":
                job["state"] = "stopped"
            proc = RUNNING.get("proc") if RUNNING.get("job") is job else None
            if proc is not None:
                proc.terminate()
            return self._send(200, {"stopping": True})
        if self.path == "/convert":
            with LOCK:
                try:
                    convert(body["id"], Path(body["input"]), Path(body["output"]), int(body.get("octave") or 0),
                            float(body.get("level_db") or 0), float(body.get("likeness", 0.75)),
                            float(body.get("backing_db") or 0))
                except Exception as err:  # noqa: BLE001
                    traceback.print_exc()
                    return self._send(500, {"error": str(err)[-800:]})
            return self._send(200, {"ok": True})
        self._send(404, {"error": "not found"})


if __name__ == "__main__":
    VOICES.mkdir(parents=True, exist_ok=True)
    BATCH = batch_size()
    print(f"voice service on {HOST}:{PORT}; batch {BATCH}; models:", needed(), flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
