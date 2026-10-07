"""Stem separation on the GPU, with Demucs, as a node.

The app separates a song's vocal (for stems, and for each song of a corpus) with the demucs
command, on the CPU, because the app's own PyTorch is the CPU build.  The engine already has
CUDA PyTorch and a queue that runs one job at a time, so a separation here waits for a render
instead of competing with it, and shows in the queue like any other job.

This follows what the demucs command does, step by step, so the stems match it: the track is
brought to the model's sample rate and channels, normalised by its own mean and spread, run
through the model in overlapping segments, scaled back, and each stem is pulled back under full
scale the way the command's default does.  The two-stem split is the vocal and the sum of
everything else.
"""
from __future__ import annotations

import contextlib
from pathlib import Path

import torch

# What the node can run, and the stems each model has.  htdemucs_ft is a bag of four models.
MODELS = ("htdemucs", "htdemucs_ft", "htdemucs_6s")
STEMS = ("vocals", "drums", "bass", "other", "guitar", "piano")
OUTPUTS = STEMS + ("instruments",)

_CACHE: dict = {}


def _weights_dir() -> str:
    import folder_paths

    return str(Path(folder_paths.models_dir) / "demucs")


@contextlib.contextmanager
def _hub_in(directory: str):
    """demucs 4.1 looks a model up on the Hugging Face hub first and falls back to torch.hub; keep what
    either fetches with the engine's models, so it is found again after the engine is rebuilt."""
    before = torch.hub.get_dir()
    torch.hub.set_dir(directory)
    constants = None
    cache = None
    try:
        from huggingface_hub import constants

        cache = constants.HF_HUB_CACHE
        constants.HF_HUB_CACHE = str(Path(directory) / "hub")
    except Exception:  # noqa: BLE001
        constants = None
    try:
        yield
    finally:
        torch.hub.set_dir(before)
        if constants is not None:
            constants.HF_HUB_CACHE = cache


def load(name: str):
    """The model, on the CPU, kept between jobs: it is small and loading it is the slow part."""
    if name not in _CACHE:
        from demucs.pretrained import get_model

        with _hub_in(_weights_dir()):
            model = get_model(name)
        model.eval()
        _CACHE.clear()
        _CACHE[name] = model
    return _CACHE[name]


def silence(rate: int, channels: int = 2) -> dict:
    """What an output the model has no stem for carries, so nothing downstream gets a None."""
    return {"waveform": torch.zeros(1, channels, 1), "sample_rate": rate}


def separate(wave: torch.Tensor, rate: int, name: str, shifts: int, overlap: float, device, on_progress=None) -> tuple[dict, int]:
    """`wave` is (channels, samples).  Returns {stem: (channels, samples)} at the model's rate,
    with an "instruments" stem that is everything but the vocal."""
    from demucs.apply import apply_model
    from demucs.audio import convert_audio, prevent_clip

    model = load(name)
    wav = convert_audio(wave.float(), rate, model.samplerate, model.audio_channels)
    ref = wav.mean(0)
    wav = wav - ref.mean()
    spread = ref.std().clamp_min(1e-8)
    wav = wav / spread

    models = len(model.models) if hasattr(model, "models") else 1
    steps = max(1, models * max(1, shifts))
    length = wav.shape[-1]

    def callback(info: dict) -> None:
        import comfy.model_management

        comfy.model_management.throw_exception_if_processing_interrupted()
        if on_progress and info.get("state") == "end":
            done = (info["model_idx_in_bag"] * max(1, shifts) + info["shift_idx"]) * length + info["segment_offset"]
            on_progress(min(1.0, done / (steps * length)))

    model.to(device)
    try:
        with torch.no_grad():
            sources = apply_model(model, wav[None].to(device), device=device, shifts=shifts, split=True,
                                  overlap=overlap, progress=False, num_workers=0, callback=callback)[0]
    finally:
        model.to("cpu")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    sources = (sources.cpu() * spread + ref.mean()).float()

    out = {stem: sources[i] for i, stem in enumerate(model.sources)}
    out["instruments"] = sum(t for stem, t in out.items() if stem != "vocals")
    return {stem: prevent_clip(t, mode="rescale") for stem, t in out.items()}, model.samplerate


class Yue2Separate:
    """Splits a recording into its vocal and instruments, or into drums, bass and the rest,
    on the GPU.  Outputs a stem the model does not have as a moment of silence."""

    CATEGORY = "audio"
    RETURN_TYPES = ("AUDIO",) * len(OUTPUTS)
    RETURN_NAMES = OUTPUTS
    FUNCTION = "execute"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "audio": ("AUDIO",),
            "model": (list(MODELS), {"default": "htdemucs",
                                     "tooltip": "htdemucs is fast; htdemucs_ft is four models, slower; htdemucs_6s adds guitar and piano."}),
            "shifts": ("INT", {"default": 1, "min": 0, "max": 5, "tooltip": "Random shifts averaged: more is slower and a little cleaner; 0 gives the same result every time."}),
            "overlap": ("FLOAT", {"default": 0.25, "min": 0.05, "max": 0.5, "step": 0.05,
                                  "tooltip": "How much neighbouring segments overlap."}),
        }}

    def execute(self, audio, model, shifts, overlap):
        import comfy.model_management
        import comfy.utils

        wave = audio["waveform"][0]
        bar = comfy.utils.ProgressBar(100)
        stems, rate = separate(wave, audio["sample_rate"], model, int(shifts), float(overlap),
                               comfy.model_management.get_torch_device(),
                               on_progress=lambda frac: bar.update_absolute(int(frac * 100), 100))
        bar.update_absolute(100, 100)
        return tuple({"waveform": stems[name][None], "sample_rate": rate} if name in stems else silence(rate)
                     for name in OUTPUTS)
