"""How much of each song a LoRA trains on, worked out from the card.

The Planner learns each song whole, as one sequence of audio codes (25 a second) after
its style and lyrics, and leaves out a song whose sequence is longer than `max_tokens`.
So songs are cut at some number of minutes.  What limits that number is not the
context, which costs nothing in itself, but preparing the set: the dataset builder
encodes each song whole on the GPU, and the memory it needs grows with the song.

    tokens  = 25 x seconds + the style and lyrics, rounded up to whole 512s
    minutes = (memory the engine could have - the builder's base - a margin) / per minute

The card is read when a corpus is exported and again when its training starts, counting
what the engine holds as available, since it lets go of that first.  TRAIN_MAX_MINUTES and
TRAIN_MAX_TOKENS win when set to numbers, so a card that runs out of memory can be given less.

`BUILDER_*` are provisional: one measurement (a build of songs up to 5:54 used about
13.9 GB of a 16 GB card, the engine at rest holding 8.6 GB) fitted to a straight line.
Two builds at different cuts would replace them.
"""
from __future__ import annotations

import math

from . import config

TOKENS_PER_SECOND = 25
PREFIX_TOKENS = 1536         # style and lyrics: at most 3,840 characters in the sets seen
TOKEN_STEP = 512
MIN_TOKENS = 8192            # never less than the default: the context costs nothing itself
MAX_TOKENS = 16384           # what the trainer's node allows

FLOOR_MINUTES = 3.5          # never less than the default, which is what ships today
CEILING_MINUTES = 6.0        # the builder encodes a song whole: past this it needs chunked encoding
BUILDER_BASE_GB = 8.6        # provisional: the engine's weights at rest
BUILDER_GB_PER_MINUTE = 0.9  # provisional: (13.9 - 8.6) / 5.9
MARGIN_GB = 1.0              # kept spare: a build that runs out of memory wedges the engine
MIN_RAM_GB = 28.0            # 32 GB physical / WSL2 RAM reports ~30-31.5 GB to the OS; <28 GB risks OS OOM kill

GB = 1024 ** 3


def _half_minutes_down(minutes: float) -> float:
    return math.floor(minutes * 2 + 1e-9) / 2


def _half_minutes_up(minutes: float) -> float:
    return math.ceil(minutes * 2 - 1e-9) / 2


def clock(minutes: float) -> str:
    whole, seconds = divmod(round(minutes * 60), 60)
    return f"{whole}:{seconds:02d}"


def tokens_for(seconds: float) -> int:
    """The context a sequence of this many seconds needs, in whole steps of 512."""
    return math.ceil((TOKENS_PER_SECOND * seconds + PREFIX_TOKENS) / TOKEN_STEP) * TOKEN_STEP


def minutes_from_memory(available_gb: float) -> float:
    """How many minutes of a song the builder can hold, with the margin spare."""
    return (available_gb - BUILDER_BASE_GB - MARGIN_GB) / BUILDER_GB_PER_MINUTE


def shared(gpu: dict | None) -> bool:
    """The GPU is the computer's own memory (Apple silicon, through Metal)."""
    return ((gpu or {}).get("name") or "").lower() == "mps"


def available_gb(gpu: dict | None) -> float | None:
    """What the engine could have once it lets go of what it holds: the free memory
    plus its own.  Memory that other programs hold is not counted.  Where the GPU is the
    computer's memory the engine reports the whole of it as its own, so only the free
    memory counts there (adding the two said 43 GB on a 24 GB Mac)."""
    if not gpu or gpu.get("vram_free") is None:
        return None
    if shared(gpu):
        return (gpu.get("vram_free") or 0) / GB
    return ((gpu.get("vram_free") or 0) + (gpu.get("engine_vram") or 0)) / GB


def ram_gb(gpu: dict | None) -> float | None:
    """Total system RAM visible to the engine (physical RAM on Windows/Linux, or WSL2's memory cap)."""
    if not gpu or not gpu.get("ram_total"):
        return None
    return float(gpu["ram_total"]) / GB


def card_limit(gpu: dict | None) -> dict:
    """What the card allows: minutes of a song, and how it got there."""
    free = available_gb(gpu)
    ram = ram_gb(gpu)
    ram_tight = ram is not None and ram < MIN_RAM_GB
    if free is None:
        return {"minutes": FLOOR_MINUTES, "tight": False, "free_gb": None,
                "ram_gb": ram, "ram_tight": ram_tight,
                "note": "the card's memory could not be read"}
    raw = minutes_from_memory(free)
    return {"minutes": max(FLOOR_MINUTES, _half_minutes_down(min(raw, CEILING_MINUTES))),
            "tight": raw < FLOOR_MINUTES, "free_gb": free,
            "ram_gb": ram, "ram_tight": ram_tight,
            "note": f"{free:.1f} GB available; the builder needs about {BUILDER_BASE_GB:g} GB "
                    f"and {BUILDER_GB_PER_MINUTE:g} GB a minute, with {MARGIN_GB:g} GB spare"}


def size(limit: float, durations: list[float]) -> dict:
    """The cut and the context for songs of these lengths (seconds), given the most the
    card allows.  Never below the default cut, never above the longest song, and a
    context that holds the longest sequence that results."""
    longest = max((d for d in durations if d), default=0.0) / 60
    # Not more than the songs have; and with none yet, the default.
    minutes = min(limit, max(FLOOR_MINUTES, _half_minutes_up(longest))) if longest else FLOOR_MINUTES
    tokens = min(MAX_TOKENS, max(MIN_TOKENS, tokens_for(min(longest, minutes) * 60)))
    return {"minutes": minutes, "tokens": tokens,
            "whole": sum(1 for d in durations if d and d <= minutes * 60 + 1),
            "songs": len([d for d in durations if d])}


def choose(gpu: dict | None, durations: list[float]) -> dict:
    """`size` for a card as it is now, with the reason in words."""
    card = card_limit(gpu)
    result = {**size(card["minutes"], durations), "tight": card["tight"],
              "ram_gb": card["ram_gb"], "ram_tight": card["ram_tight"]}
    result["reason"] = f"up to {clock(result['minutes'])} of each song, {result['tokens']:,} tokens: {card['note']}"
    return result


def for_corpus(durations: list[float], gpu: dict | None) -> dict:
    """What a corpus's export and training use: the settings when they are numbers, the
    card's answer, read as it is now, when they are auto.  Read when the export or the
    training runs, so it is what the card has then; a card that cannot be read gets the
    default."""
    card = card_limit(gpu)
    if config.TRAIN_MINUTES_AUTO:
        result = {**size(card["minutes"], durations), "tight": card["tight"],
                  "ram_gb": card["ram_gb"], "ram_tight": card["ram_tight"], "note": card["note"]}
    else:
        result = {**size(config.TRAIN_MAX_MINUTES, durations), "tight": False,
                  "ram_gb": card["ram_gb"], "ram_tight": card["ram_tight"], "note": "set by TRAIN_MAX_MINUTES"}
        result["minutes"] = config.TRAIN_MAX_MINUTES
    if not config.TRAIN_TOKENS_AUTO:
        result["tokens"] = config.TRAIN_MAX_TOKENS
    result["reason"] = f"up to {clock(result['minutes'])} of each song, {result['tokens']:,} tokens: {result['note']}"
    return result
