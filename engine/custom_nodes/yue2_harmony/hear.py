"""Whisper on the GPU, as a node: the words of a separated vocal, with their times.

The app hears a corpus song's or a cover's words with faster-whisper on the CPU.  The engine
has CUDA PyTorch, and a queue that runs one job at a time, so a node here runs the same
model with the same options on the GPU, next to plans and renders instead of in their way.

What comes back is what Whisper wrote, segment by segment, as JSON: the app turns it into
lines (splitting at sentence ends, dropping Whisper's stock inventions, cutting runs of one
word) exactly as it does for the CPU, so the two differ only in where the model ran.  The
model is loaded for the job and released after it, since a render needs the card's memory.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import torch

MODELS = ("large-v3-turbo",)
_RATE = 16000


def add_cuda_libraries() -> None:
    """CTranslate2 loads cuBLAS and cuDNN itself, by name, from native code.  Where PyTorch carries them (Linux),
    importing torch first is enough.  On Windows they are the CUDA 12 DLLs of the nvidia packages (PyTorch there
    carries CUDA 13's), and native code looks only along PATH, so their folders go on PATH, as well as on Python's
    own list for the extension itself."""
    if sys.platform != "win32":
        return
    for root in sys.path:
        base = Path(root) / "nvidia"
        if base.is_dir():
            for lib in base.glob("*/bin"):
                try:
                    os.add_dll_directory(str(lib))
                except OSError:
                    pass
                if str(lib) not in os.environ.get("PATH", "").split(os.pathsep):
                    os.environ["PATH"] = str(lib) + os.pathsep + os.environ.get("PATH", "")


def usable() -> bool:
    """CTranslate2 is there and sees a CUDA device."""
    add_cuda_libraries()
    try:
        import ctranslate2
        import faster_whisper  # noqa: F401

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:  # noqa: BLE001
        return False


def _weights_dir() -> str:
    import folder_paths

    return str(Path(folder_paths.models_dir) / "whisper")


def load(name: str):
    """A folder of the model's files under the engine's models (what scripts/fetch-models.sh writes) is used as it
    stands; otherwise the Hugging Face cache there, fetching the model the first time it is needed."""
    from faster_whisper import WhisperModel

    root = _weights_dir()
    os.makedirs(root, exist_ok=True)
    plain = Path(root) / name
    target = str(plain) if (plain / "model.bin").is_file() else name
    try:
        return WhisperModel(target, device="cuda", compute_type="float16", download_root=root, local_files_only=True)
    except Exception:  # noqa: BLE001
        model = WhisperModel(target, device="cuda", compute_type="float16", download_root=root, local_files_only=False)
        from .perms import open_up

        open_up(root)    # fetched here, as root: leave it deletable by whoever owns the models folder
        return model


def mono_16k(wave: torch.Tensor, rate: int):
    """`wave` is (channels, samples): Whisper's input, mono at 16 kHz."""
    import torchaudio

    mono = wave.float().mean(0, keepdim=True)
    if rate != _RATE:
        mono = torchaudio.functional.resample(mono, rate, _RATE)
    return mono[0].cpu().numpy()


def hear(wave: torch.Tensor, rate: int, name: str, language: str, on_progress=None, check=None, model=None) -> list[dict]:
    """The segments Whisper wrote, as {"start", "end", "text"}.  The options are the ones the app uses on the CPU."""
    audio = mono_16k(wave, rate)
    seconds = len(audio) / _RATE
    own = model is None
    model = model or load(name)
    try:
        segments, _ = model.transcribe(audio, language=language or None, vad_filter=False, beam_size=5,
                                       condition_on_previous_text=False, word_timestamps=True,
                                       hallucination_silence_threshold=2.0)
        out = []
        for seg in segments:
            if check:
                check()
            out.append({"start": round(float(seg.start), 2), "end": round(float(seg.end), 2), "text": seg.text})
            if on_progress and seconds > 0:
                on_progress(max(0.0, min(1.0, float(seg.end) / seconds)))
        return out
    finally:
        if own:
            del model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


class Yue2Hear:
    """Writes down the words of a separated vocal, with their times, on the GPU."""

    CATEGORY = "audio"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("segments",)
    FUNCTION = "execute"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "audio": ("AUDIO",),
            "model": (list(MODELS), {"default": MODELS[0]}),
            "language": ("STRING", {"default": "en", "tooltip": "The language sung; empty lets Whisper decide."}),
        }}

    def execute(self, audio, model, language):
        import comfy.model_management
        import comfy.utils

        bar = comfy.utils.ProgressBar(100)
        segments = hear(audio["waveform"][0], audio["sample_rate"], model, language.strip(),
                        on_progress=lambda frac: bar.update_absolute(int(frac * 100), 100),
                        check=comfy.model_management.throw_exception_if_processing_interrupted)
        bar.update_absolute(100, 100)
        return (json.dumps(segments),)
