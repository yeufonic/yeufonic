"""A recorded voice: the render continues from a prefix of that voice's own semantic tokens.

Stands in for YuE2 Generate Music when a take names a voice (app/jobs.py, build_render_graph). The app uploads
the voice's tokens into the input folder before each render and names the file here. yue2.py's
encode_token_weights is reimplemented with one addition - the voice's tokens after [MUSIC_START] - because the
engine pin ships that method without a hook. The design and the listening tests are in VOICE-PERSONA.md 8.6.
"""
from __future__ import annotations

from pathlib import Path

import numpy
import torch

import comfy.model_management
import folder_paths
from comfy.text_encoders.yue2 import (ABC_END, ABC_START, MUSIC_START, YuE2TEModel)

CODEC_OFFSET = 151853
FRAMES_PER_SECOND = 25


def _encode_token_weights_with_persona(self, tokens):
    """comfy.text_encoders.yue2.encode_token_weights, plus the persona ids after MUSIC_START."""
    device = self.execution_device
    dtype = torch.bfloat16 if comfy.model_management.should_use_bf16(device) else torch.float32
    prefix = tokens["prefix"]
    abc_ids = tokens["abc_ids"]
    cot = tokens["cot"]
    if cot == "off":
        abc_ids = []
    persona_ids = list(tokens.get("persona_ids") or [])
    prefix = prefix + abc_ids + [ABC_END, MUSIC_START] + persona_ids
    negative = tokens["negative"] + ([MUSIC_START] if cot == "off" else [ABC_START] + abc_ids + [ABC_END, MUSIC_START])
    context = self.config.max_position_embeddings
    max_tokens = min(tokens["max_tokens"], context - max(len(prefix), len(negative)))
    if max_tokens < 1 or len(prefix) + 5 > context:
        raise ValueError("YuE2 prompt leaves no room for music; shorten the style, lyrics, ABC or persona.")
    semantic, semantic_truncated = self._generate(
        prefix, tokens["seed"], max_tokens, "semantic", dtype,
        negative=negative, cfg_scale=tokens["cfg_scale"], legacy_off=cot == "off",
        temperature=tokens["temperature"], top_p=tokens["top_p"], top_k=tokens["top_k"],
        repetition_penalty=tokens["repetition_penalty"], penalty_window=50,
        min_tokens=min(200, max_tokens),
    )
    conditioning, chunks = self._acoustic_conditioning(prefix, semantic, dtype)
    return conditioning, None, {
        "yue2_chunks": chunks, "yue2_abc_ids": abc_ids, "yue2_frames": len(semantic),
        "yue2_truncated": semantic_truncated,
    }


def install_hook():
    """Only the persona node uses this method set; it is a no-op for every other prompt."""
    if getattr(YuE2TEModel.encode_token_weights, "_persona_hooked", False):
        return
    _encode_token_weights_with_persona._persona_hooked = True
    YuE2TEModel.encode_token_weights = _encode_token_weights_with_persona


def tokens_path(name: str) -> str:
    """A token file named as the app uploads it (into the input folder), or a full path as a script passes it."""
    path = Path(name)
    if path.is_absolute():
        return str(path)
    found = folder_paths.get_annotated_filepath(name)
    if not found or not Path(found).exists():
        raise ValueError(f"no such voice tokens in the input folder: {name!r}")
    return found


class Yue2PersonaGenerate:
    """YuE2 Generate Music with a persona: the AR continues from a voice's own tokens."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "clip": ("CLIP",),
            "style": ("STRING", {"multiline": True, "default": ""}),
            "lyrics": ("STRING", {"multiline": True, "default": ""}),
            "persona_tokens": ("STRING", {"default": "",
                                          "tooltip": "A .semantic.npy of the persona's tokens: a file in the input folder, or a full path."}),
            "persona_seconds": ("FLOAT", {"default": 48.0, "min": 0.0, "max": 120.0, "step": 0.04,
                                          "tooltip": "How much of the persona's stream goes before the new material."}),
            "abc": ("STRING", {"multiline": True, "default": ""}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            "mode": (["full", "melody", "off"], {"default": "full"}),
            "max_duration": ("FLOAT", {"default": 360.0, "min": 0.04, "max": 900.0, "step": 0.04}),
            # The same samplers YuE2 Generate Music takes, so this node can stand in for it unchanged.
            "temperature": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.05}),
            "top_p": ("FLOAT", {"default": 0.95, "min": 0.01, "max": 1.0, "step": 0.01}),
            "top_k": ("INT", {"default": 100, "min": 1, "max": 32768}),
            "repetition_penalty": ("FLOAT", {"default": 1.2, "min": 0.01, "max": 10.0, "step": 0.01}),
            "cfg_scale": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.01}),
        }}

    RETURN_TYPES = ("CONDITIONING", "FLOAT")
    RETURN_NAMES = ("conditioning", "seconds")
    FUNCTION = "generate"
    CATEGORY = "model/conditioning/yue2"

    def generate(self, clip, style, lyrics, persona_tokens, persona_seconds, abc, seed, mode, max_duration,
                 temperature=1.0, top_p=0.95, top_k=100, repetition_penalty=1.2, cfg_scale=None):
        install_hook()
        if not abc.strip():
            mode = "off"
        if cfg_scale is None:
            cfg_scale = 1.01 if mode == "off" else 1.0
        tokens = clip.tokenize(style, lyrics=lyrics, cot=mode, seed=seed, abc=abc,
                               max_tokens=max(1, round(max_duration * FRAMES_PER_SECOND)),
                               temperature=temperature, top_p=top_p, top_k=top_k,
                               repetition_penalty=repetition_penalty, cfg_scale=cfg_scale)
        ids = []
        if persona_tokens.strip() and persona_seconds > 0:
            codes = numpy.load(tokens_path(persona_tokens.strip()))
            ids = [CODEC_OFFSET + int(code) for code in codes[: int(persona_seconds * FRAMES_PER_SECOND)]]
        tokens["persona_ids"] = ids
        conditioning = clip.encode_from_tokens_scheduled(tokens)
        return (conditioning, conditioning[0][1]["yue2_frames"] / FRAMES_PER_SECOND)
