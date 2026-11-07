"""The voice service: train a recorded voice, and sing a take's vocal in it.

A small HTTP server in front of RVC (MIT) and a BS-Roformer separator, run one job at a time.  The app owns the
GPU schedule: it frees the engine before it asks for anything here, so this never shares the card with a render.

    GET  /health                    {"ok": true, "models": {...}}
    POST /train    {"id", "sources": [paths], "separate": bool, "epochs": int}    -> {"job": id}
    GET  /jobs/<id>                 {"state": queued|running|done|failed, "progress": 0..1, "stage", "error"}
    POST /jobs/<id>/stop            ends a training run: the step under way is terminated, its files removed
    POST /convert  {"id", "input", "output", "octave": int}                        -> {"ok": true} when written

Paths are the app's own (/data/...): this container mounts the same data folder.  A voice's files go to
/data/voices/<id>/: model.pth and model.index, and a work folder that is removed once training succeeds.
"""
from __future__ import annotations

import glob
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RVC = Path("/opt/rvc")
ASSETS = RVC / "assets"                  # mounted from models/voice/assets
LOGS = RVC / "logs"                      # mounted from models/voice/logs (holds RVC's "mute" samples)
VOICES = Path(os.environ.get("VOICES_DIR", "/data/voices"))
SEPARATOR = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
SR, HZ = "48k", "48000"
PY = "python"

JOBS: dict[str, dict] = {}
LOCK = threading.Lock()                  # one GPU job at a time: a training run or a conversion
RUNNING: dict = {}                       # the step under way, so a stop can end it: {"job": id, "proc": Popen}


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


def train(job: dict, voice: str, sources: list[str], split: bool, epochs: int) -> None:
    folder = VOICES / voice
    work = folder / "work"
    shutil.rmtree(work, ignore_errors=True)
    trainset = work / "trainset"
    trainset.mkdir(parents=True)
    log = work / "train.log"
    for index, name in enumerate(sources):
        job.update(stage="separating" if split else "preparing", progress=0.1 * index / max(1, len(sources)))
        source = Path(name)
        print(f"[{voice}] {job['stage']} {index + 1}/{len(sources)}: {source.name}", flush=True)
        if job.get("stop"):
            raise Stopped()
        vocal = separate(source, work / "sep")[0] if split else source
        mono(vocal, trainset / f"{index:03d}.wav")
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
    # Batch 4 rather than RVC's usual 8: the engine is freed first, but a smaller batch leaves room on a 12 GB card.
    run(["train/train.py", "-e", exp, "-sr", SR, "-f0", "1", "-bs", "4", "-g", "0", "-te", str(epochs),
         "-se", str(epochs), "-pg", f"assets/pretrained_v2/f0G{SR}.pth", "-pd", f"assets/pretrained_v2/f0D{SR}.pth",
         "-l", "1", "-c", "0", "-sw", "0", "-v", "v2"], job=job, log=log)
    job["epochs_done"] = epochs
    small = ASSETS / "weights" / f"{exp}.pth"
    if not small.exists():   # RVC's final save can fail on its own; the last checkpoint holds the same weights
        run(["-c", "from train.process_ckpt import extract_small_model as x; import sys; "
                   f"print(x('{logs}/G_2333333.pth', '{exp}', '{SR}', 1, 'Yeufonic voice', 'v2'))"], log=log)
    job.update(stage="indexing", progress=0.97)
    print(f"[{voice}] building the index", flush=True)
    run(["train/train_index.py", exp, "v2", str(ASSETS / "indices"), str(max(1, (os.cpu_count() or 4) // 2)), "single"],
        log=log)
    index = next(iter(sorted(logs.glob("added_*.index"))), None)
    if not small.exists() or index is None:
        raise RuntimeError("training finished without a model")
    shutil.move(str(small), folder / "model.pth")
    shutil.copy(index, folder / "model.index")
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


def convert(voice: str, source: Path, output: Path, octave: int) -> None:
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
             "--index-rate", "0.75", "--protect", "0.33", "--rms-mix-rate", "0.25", "--overwrite"])
        if not sung.exists():
            raise RuntimeError("the conversion wrote nothing")
        mixed = work / f"mixed{output.suffix or '.flac'}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(rest), "-i", str(sung), "-filter_complex",
                        "[1:a]aresample=44100,aformat=channel_layouts=stereo[v];[0:a]aresample=44100[i];"
                        "[i][v]amix=inputs=2:normalize=0[m]", "-map", "[m]", str(mixed)], check=True)
        shutil.move(str(mixed), output)
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
                  int(body.get("epochs") or 100))
            job.update(state="done", progress=1.0, stage=None)
            print(f"[{body['id']}] trained", flush=True)
        except Stopped:
            job.update(state="stopped", stage=None)
            shutil.rmtree(VOICES / body["id"] / "work", ignore_errors=True)
            shutil.rmtree(LOGS / f"v-{body['id']}", ignore_errors=True)
        except Exception as err:  # noqa: BLE001 - every failure is reported to the app
            traceback.print_exc()
            job.update(state="failed", error=str(err)[-800:])


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
            return self._send(200, {"ok": all(models.values()), "models": models})
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
                    convert(body["id"], Path(body["input"]), Path(body["output"]), int(body.get("octave") or 0))
                except Exception as err:  # noqa: BLE001
                    traceback.print_exc()
                    return self._send(500, {"error": str(err)[-800:]})
            return self._send(200, {"ok": True})
        self._send(404, {"error": "not found"})


if __name__ == "__main__":
    VOICES.mkdir(parents=True, exist_ok=True)
    print("voice service on :8190; models:", needed(), flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8190), Handler).serve_forever()
