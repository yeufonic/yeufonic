"""The voice service: train a recorded voice, and sing a take's vocal in it.

A small HTTP server in front of RVC (MIT) and a BS-Roformer separator, run one job at a time.  The app owns the
GPU schedule: it frees the engine before it asks for anything here, so this never shares the card with a render.

    GET  /health                    {"ok": true, "models": {...}}
    POST /train    {"id", "sources": [paths], "separate": bool, "epochs": int}    -> {"job": id}
    GET  /jobs/<id>                 {"state": queued|running|done|failed, "progress": 0..1, "stage", "error"}
    POST /jobs/<id>/stop            ends a training run: the step under way is terminated, its files removed
    POST /convert  {"id", "input", "output", "octave": int}                        -> {"ok": true} when written
    POST /audition {"id", "loop", "output", "octave", "likeness", ...}             -> {"ok": true, "seconds"}
    POST /audition/free             lets go of the voice an audition holds on the card

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


def remove_tree(path: Path) -> None:
    """A folder and what is in it.  On Windows a file a step has just closed can stay locked for a moment (a child
    process still exiting, a virus scanner reading it), so a refusal is tried again before it is left for the next run."""
    for attempt in range(6):
        shutil.rmtree(path, ignore_errors=True)
        if not path.exists():
            return
        time.sleep(1 + attempt)


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
    remove_tree(logs)                                # the checkpoints are half a gigabyte; the model is all that is used
    for linked in (ASSETS / "indices").glob(f"*{exp}*"):
        linked.unlink(missing_ok=True)
    remove_tree(work)


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


def settle(original: Path, sung: Path, voice: str = "", level_db: float = 0.0, room: float = ROOM_WET,
           brightness: bool = True) -> None:
    """Put the converted vocal where the rendered one sat: its presence, its loudness, and a little room.

    RVC returns a vocal with less presence than the one it was given, and dry, so it sounded low and apart from the
    backing even at the same level. Its 2 kHz-and-up is lifted towards the original's balance (up to 6 dB, never
    cut), its loudness over the singing matched to the original's as the ear weighs it, and a short decaying room
    mixed under it so it shares a space with the mix rather than lying on top of it.  The voice's Room sets how much
    of that room (none at 0), and Brightness off leaves its upper range as converted.
    """
    import numpy as np  # noqa: PLC0415
    import soundfile  # noqa: PLC0415
    from scipy.signal import fftconvolve, lfilter  # noqa: PLC0415

    before, before_rate = soundfile.read(str(original), dtype="float32")
    after, rate = soundfile.read(str(sung), dtype="float32")
    dry = _mono(after).astype("float64")
    lift = float(np.clip(_presence(before, before_rate) - _presence(dry, rate), 0.0, MAX_PRESENCE_DB)) if brightness else 0.0
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
    mixed = dry + max(0.0, float(room)) * fftconvolve(dry, tail)[: len(dry)] if room else dry
    # Kept in float, peaks and all: scaling the vocal alone to stop it clipping undid the level set above.  The
    # finished mix is brought under full scale as a whole instead (convert), which keeps the balance.
    soundfile.write(str(sung), mixed.astype("float32"), rate, subtype="FLOAT")
    print(f"[{voice}] converted vocal: presence {lift:+.1f} dB" + ("" if brightness else " (brightness off)")
          + f", level {gain_db:+.1f} dB to the rendered vocal's, room {float(room):.2f}", flush=True)


FORMANT_FLOOR, FORMANT_CEILING = 75.0, 600.0    # the pitch range Praat looks for the voice in


def shift_formants(sung: Path, ratio: float) -> None:
    """The converted vocal with its formants moved by `ratio`, its pitch and timing kept: below 1 a larger, deeper
    voice, above 1 a smaller, brighter one.  Praat's Change gender, through parselmouth (installed with RVC)."""
    if not ratio or abs(ratio - 1.0) < 0.005:
        return
    import parselmouth  # noqa: PLC0415
    import soundfile  # noqa: PLC0415
    from parselmouth.praat import call  # noqa: PLC0415

    samples, rate = soundfile.read(str(sung), dtype="float64")
    sound = parselmouth.Sound(_mono(samples), sampling_frequency=rate)
    moved = call(sound, "Change gender", FORMANT_FLOOR, FORMANT_CEILING, float(ratio), 0.0, 1.0, 1.0)
    out = moved.values[0][: len(samples)]
    soundfile.write(str(sung), out.astype("float32"), rate, subtype="FLOAT")


def blend(original: Path, sung: Path, wet: float) -> None:
    """The converted vocal mixed with the rendered vocal it was made from: `wet` of the one, the rest of the other.
    The two are at the same level by now (settle matched them), so the blend keeps the vocal's level."""
    if wet >= 0.995:
        return
    import numpy as np  # noqa: PLC0415
    import soundfile  # noqa: PLC0415
    from scipy.signal import resample_poly  # noqa: PLC0415

    dry, dry_rate = soundfile.read(str(original), dtype="float64")
    wet_part, rate = soundfile.read(str(sung), dtype="float64")
    dry = _mono(dry)
    if dry_rate != rate:
        g = math.gcd(int(rate), int(dry_rate))
        dry = resample_poly(dry, int(rate) // g, int(dry_rate) // g)
    dry = np.pad(dry, (0, max(0, len(wet_part) - len(dry))))[: len(wet_part)]
    mixed = max(0.0, float(wet)) * _mono(wet_part) + (1 - max(0.0, float(wet))) * dry
    soundfile.write(str(sung), mixed.astype("float32"), rate, subtype="FLOAT")


# ---------------------------------------------------------------- auditions
# A voice heard on a short loop while its settings change.  A conversion run as a script loads RVC and its models
# every time (seconds); an audition keeps them loaded here, and keeps what does not depend on the settings: the
# loop's pitch (RMVPE) and its sound features (HuBERT) are worked out once and reused, so a change of octave,
# likeness or protect runs only the index blend and the synthesis.  It holds about a gigabyte of the card, so it
# is let go when the app starts other GPU work (/audition/free), when this service trains or converts, and after
# AUDITION_IDLE seconds unused.
AUDITION_IDLE = 120
AUDITION: dict = {}          # "vc": RVC's VC, "voice": its id, "used": time
_CACHE: dict = {}            # input digest -> result, for the two analyses (a few loops' worth)


def _digest(array) -> str:
    import hashlib  # noqa: PLC0415

    data = array.detach().float().cpu().numpy().tobytes() if hasattr(array, "detach") else array.tobytes()
    return hashlib.blake2b(data, digest_size=16).hexdigest() + str(len(data))


def _cached(kind: str, key: str, make):
    found = _CACHE.get((kind, key))
    if found is None:
        found = make()
        if len(_CACHE) > 8:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[(kind, key)] = found
    return found


def _audition_setup() -> None:
    """RVC importable in this process, as its scripts find it, with the two analyses remembered by their input."""
    if AUDITION.get("ready"):
        return
    if str(RVC) not in sys.path:
        sys.path.insert(0, str(RVC))
    os.chdir(RVC)                      # RVC reads its assets by relative path; the service already runs here
    for key, value in (("weight_root", str(ASSETS / "weights")), ("index_root", str(LOGS)),
                       ("outside_index_root", str(ASSETS / "indices")), ("rmvpe_root", str(ASSETS / "rmvpe"))):
        os.environ.setdefault(key, value)
    import infer.rmvpe as rmvpe  # noqa: PLC0415
    import infer.vc.pipeline as pipeline  # noqa: PLC0415

    infer_f0 = rmvpe.RMVPE.infer_from_audio
    rmvpe.RMVPE.infer_from_audio = lambda self, audio, thred=0.03: _cached(
        "f0", _digest(audio) + str(thred), lambda: infer_f0(self, audio, thred=thred)).copy()
    features = pipeline.extract_hubert_features
    pipeline.extract_hubert_features = lambda model, feats, version, padding_mask=None: _cached(
        "hubert", _digest(feats) + version, lambda: features(model, feats, version, padding_mask=padding_mask)).clone()
    AUDITION["ready"] = True


def audition_free() -> None:
    """Let go of the auditioned voice and RVC's models, and the card's memory with them."""
    vc = AUDITION.pop("vc", None)
    AUDITION.pop("voice", None)
    _CACHE.clear()
    if vc is not None:
        del vc
        import gc  # noqa: PLC0415

        gc.collect()
        try:
            import torch  # noqa: PLC0415

            torch.cuda.empty_cache()
        except Exception:  # noqa: BLE001 - nothing to free without a card
            pass
        print("audition: let go of the voice", flush=True)


def _audition_idle() -> None:
    while True:
        time.sleep(15)
        if AUDITION.get("vc") is not None and time.time() - AUDITION.get("used", 0) > AUDITION_IDLE and LOCK.acquire(False):
            try:
                audition_free()
            finally:
                LOCK.release()


def audition(voice: str, loop: Path, output: Path, octave: int = 0, likeness: float = 0.75, protect: float = 0.33,
             dynamics: float = 0.25, room: float = ROOM_WET, brightness: bool = True, formant: float = 1.0) -> float:
    """`loop` sung in `voice` with these settings, finished as a take's vocal is (formants, presence, level, room)
    and written to `output` as WAV; the seconds it took.  The blend with the dry loop is left to the page, which
    plays both."""
    started = time.time()
    folder = VOICES / voice
    model, index = folder / "model.pth", folder / "model.index"
    if not model.exists():
        raise RuntimeError("this voice has no trained model")
    _audition_setup()
    if AUDITION.get("voice") != voice:
        audition_free()
        import sys as _sys  # noqa: PLC0415
        from configs.config import Config  # noqa: PLC0415
        from infer.vc.modules import VC  # noqa: PLC0415

        argv, _sys.argv = _sys.argv, [_sys.argv[0]]     # RVC's Config reads the command line
        try:
            vc = VC(Config())
        finally:
            _sys.argv = argv
        os.environ["weight_root"] = str(folder)
        vc.get_vc(model.name)
        AUDITION.update(vc=vc, voice=voice)
        print(f"[{voice}] audition: voice loaded in {time.time() - started:.1f} s", flush=True)
    vc = AUDITION["vc"]
    status, result = vc.vc_single(0, str(loop), 12 * int(octave), "rmvpe", str(index) if index.exists() else "",
                                  min(1.0, max(0.0, likeness)), 0, min(1.0, max(0.0, dynamics)),
                                  min(0.5, max(0.0, protect)))
    if not result or result[1] is None:
        raise RuntimeError(f"the audition failed: {status[-300:]}")
    import soundfile  # noqa: PLC0415

    rate, samples = result
    converted = time.time()
    work = Path(tempfile.mkdtemp(prefix="audition-", dir=str(VOICES)))
    try:
        sung = work / "sung.wav"
        soundfile.write(str(sung), samples, rate)
        shift_formants(sung, formant)
        shifted = time.time()
        settle(loop, sung, voice, 0.0, room, brightness)
        shutil.move(str(sung), output)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    AUDITION["used"] = time.time()
    times = re.findall(r"(\d+\.\d+)s", status)
    print(f"[{voice}] audition: converted in {converted - started:.2f} s (" + "/".join(times) + "), formants "
          f"{shifted - converted:.2f} s, finished {time.time() - shifted:.2f} s", flush=True)
    return time.time() - started


def convert(voice: str, source: Path, output: Path, octave: int, level_db: float = 0.0, likeness: float = 0.75,
            backing_db: float = 0.0, parts: Path | None = None, room: float = ROOM_WET, brightness: bool = True,
            protect: float = 0.33, dynamics: float = 0.25, formant: float = 1.0, wet: float = 1.0) -> None:
    """The take at `source` with its vocal sung in `voice`, written to `output`.  With `parts`, the two halves as they
    were mixed are kept there too: vocal.flac (the sung vocal at its level) and backing.flac (the rest at its level),
    both brought down with the mix where it would clip, so together they are the finished take."""
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
             "--index-rate", f"{min(1.0, max(0.0, likeness)):.2f}", "--protect", f"{min(0.5, max(0.0, protect)):.2f}",
             "--rms-mix-rate", f"{min(1.0, max(0.0, dynamics)):.2f}", "--overwrite"])
        if not sung.exists():
            raise RuntimeError("the conversion wrote nothing")
        shift_formants(sung, formant)
        settle(vocals, sung, voice, level_db, room, brightness)
        blend(vocals, sung, wet)
        mixed = work / "mixed.wav"
        halves = [work / "vocal.wav", work / "backing.wav"]
        # The same two streams the mix sums, written out as they go into it when the halves are to be kept.
        split = parts is not None
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(rest), "-i", str(sung), "-filter_complex",
                        "[1:a]aresample=44100,aformat=sample_fmts=flt:channel_layouts=stereo" + (",asplit=2[v][vk];" if split else "[v];")
                        + f"[0:a]aresample=44100,aformat=sample_fmts=flt,volume={float(backing_db):.1f}dB"
                        + (",asplit=2[i][ik];" if split else "[i];")
                        + "[i][v]amix=inputs=2:normalize=0[m]", "-map", "[m]", "-c:a", "pcm_f32le", str(mixed),
                        *(["-map", "[vk]", "-c:a", "pcm_f32le", str(halves[0]),
                           "-map", "[ik]", "-c:a", "pcm_f32le", str(halves[1])] if split else [])], check=True)
        import soundfile  # noqa: PLC0415

        samples, rate = soundfile.read(str(mixed), dtype="float32")
        peak = float(abs(samples).max()) if samples.size else 0.0
        scale = 0.98 / peak if peak > 0.98 else 1.0
        if peak > 0.98:     # the whole mix down, vocal and backing together, so the balance set holds
            samples *= scale
        final = work / f"final{output.suffix or '.flac'}"
        soundfile.write(str(final), samples, rate)
        print(f"[{voice}] mixed: vocal {level_db:+.0f} dB, backing {backing_db:+.0f} dB"
              + (f", whole mix {20 * math.log10(0.98 / peak):+.1f} dB to stay under full scale" if peak > 0.98 else ""),
              flush=True)
        if split:
            parts.mkdir(parents=True, exist_ok=True)
            for half, name in zip(halves, ("vocal.flac", "backing.flac")):
                part, part_rate = soundfile.read(str(half), dtype="float32")
                soundfile.write(str(parts / name), part * scale, part_rate, subtype="PCM_24")
            print(f"[{voice}] kept the vocal and the backing as mixed in {parts}", flush=True)
        shutil.move(str(final), output)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _train_job(job_id: str, body: dict) -> None:
    job = JOBS[job_id]
    with LOCK:
        audition_free()
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
        if self.path == "/audition/free":
            with LOCK:
                audition_free()
            return self._send(200, {"ok": True})
        if self.path == "/audition":
            if not LOCK.acquire(timeout=1.0):        # training or a take's conversion has the card
                return self._send(409, {"error": "the voice service is busy"})
            try:
                seconds = audition(body["id"], Path(body["loop"]), Path(body["output"]), int(body.get("octave") or 0),
                                   float(body.get("likeness", 0.75)), float(body.get("protect", 0.33)),
                                   float(body.get("dynamics", 0.25)),
                                   float(body["room"]) if body.get("room") is not None else ROOM_WET,
                                   bool(int(body.get("brightness", 1))), float(body.get("formant", 1.0)))
            except Exception as err:  # noqa: BLE001
                traceback.print_exc()
                return self._send(500, {"error": str(err)[-800:]})
            finally:
                LOCK.release()
            return self._send(200, {"ok": True, "seconds": round(seconds, 3)})
        if self.path == "/convert":
            with LOCK:
                audition_free()
                try:
                    convert(body["id"], Path(body["input"]), Path(body["output"]), int(body.get("octave") or 0),
                            float(body.get("level_db") or 0), float(body.get("likeness", 0.75)),
                            float(body.get("backing_db") or 0), Path(body["parts"]) if body.get("parts") else None,
                            float(body["room"]) if body.get("room") is not None else ROOM_WET,
                            bool(int(body.get("brightness", 1))),
                            float(body.get("protect", 0.33)), float(body.get("dynamics", 0.25)),
                            float(body.get("formant", 1.0)), float(body.get("wet", 1.0)))
                except Exception as err:  # noqa: BLE001
                    traceback.print_exc()
                    return self._send(500, {"error": str(err)[-800:]})
            return self._send(200, {"ok": True})
        self._send(404, {"error": "not found"})


if __name__ == "__main__":
    VOICES.mkdir(parents=True, exist_ok=True)
    BATCH = batch_size()
    threading.Thread(target=_audition_idle, daemon=True).start()
    print(f"voice service on {HOST}:{PORT}; batch {BATCH}; models:", needed(), flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
