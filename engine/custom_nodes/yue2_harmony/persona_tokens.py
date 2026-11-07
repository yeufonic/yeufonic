"""Tokenise one recording into YuE2 semantic tokens, for a vocal persona.

A persona is a recording of a voice, tokenised once and passed to the render as a prefix (VOICE-PERSONA.md
8.6).  This is the tokenise half: it takes an audio file from ComfyUI's input folder, runs the
Mothersuperior tokenizer head the trainer ships with, and writes the stream where the app can read it.
"""
from __future__ import annotations

from pathlib import Path

import comfy.model_management
import folder_paths
import numpy
import torch

DEFAULT_MERT = "m-a-p/MERT-v2-FullSong"
DEFAULT_HEAD = "tokenizer_head_joint_v9.safetensors"


def _tokenizer():
    """The trainer's own tokeniser, which is a sibling custom node."""
    from yue2_trainer.semantic import SemanticTokenizer  # noqa: PLC0415 - loaded at call time

    return SemanticTokenizer


class Yue2PersonaTokens:
    """Writes <audio name>.semantic.npy for one recording."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "audio": ("STRING", {"default": "", "tooltip": "A file in ComfyUI's input folder."}),
            "out": ("STRING", {"default": "",
                               "tooltip": "Where to write the .npy. Blank: beside the audio."}),
            "head": ("STRING", {"default": DEFAULT_HEAD,
                                "tooltip": "A tokenizer_head_*.safetensors from models/audio_encoders."}),
            "mert": ("STRING", {"default": DEFAULT_MERT}),
            "device": (["auto", "cuda", "cpu"], {"default": "auto"}),
        }}

    RETURN_TYPES = ("STRING", "INT", "STRING")
    RETURN_NAMES = ("tokens", "seconds", "report")
    FUNCTION = "tokenise"
    CATEGORY = "model/conditioning/yue2"

    def tokenise(self, audio, out, head, mert, device):
        SemanticTokenizer = _tokenizer()
        source = folder_paths.get_annotated_filepath(audio) if audio.strip() else ""
        if not source or not Path(source).exists():
            raise ValueError(f"no such audio in the input folder: {audio!r}")
        head_path = folder_paths.get_full_path_or_raise("audio_encoders", head)
        target = Path(out.strip()) if out.strip() else Path(source).with_suffix(".semantic.npy")
        target.parent.mkdir(parents=True, exist_ok=True)
        wanted = device
        if wanted == "auto":
            wanted = "cuda" if comfy.model_management.should_use_gpu() else "cpu"
        comfy.model_management.unload_all_models()
        comfy.model_management.soft_empty_cache()
        with torch.inference_mode(), SemanticTokenizer(head_path, mert, wanted) as tokenizer:
            ids = numpy.asarray(tokenizer.tokenize_file(source))
        numpy.save(target, ids)
        seconds = float(len(ids)) / 25.0
        report = f"{target} · {len(ids)} tokens · {seconds:.1f} s · head {Path(head_path).name}"
        print("[persona] " + report)
        return (str(target), int(seconds), report)
