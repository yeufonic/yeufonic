"""What is in a LoRA file, so the app can say what a LoRA will do.

A YuE2 LoRA holds one half of the model, or both.  The planner half sits under
`text_encoders.` and decides what is written: form, harmony, phrasing.  The
decoder half sits under `diffusion_model.` and decides how it sounds: timbre,
production.  ComfyUI's LoraLoader applies them through two separate strengths,
and a strength for a half the file does not contain does nothing at all.

The app's own two LoRAs are one half each, which is why each is applied with the
other strength at zero.  A style LoRA from elsewhere is usually both, and wants
both strengths, so the picker has to know which it is holding.

Reading that costs almost nothing: a safetensors file starts with the length of
its header, then the header itself as JSON, and the tensor names are in there.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import stat
import struct
import time
import zipfile
from pathlib import Path

import numpy as np

from . import config

log = logging.getLogger("yue2.loras")

PLANNER = "text_encoders"
DECODER = "diffusion_model"

# The two the app applies itself.  They are listed by the engine like any other,
# but choosing one as a style LoRA would fight the setting that already applies it.
RESERVED = {config.INSTRUMENTAL_LORA, config.REAL_AUDIO_LORA}

# A header longer than this is not a LoRA we can make sense of, and reading it
# would be a way to spend memory on a malformed file.
MAX_HEADER = 32 * 1024 * 1024


def _read_header(path: Path) -> tuple[dict, int]:
    """Read a safetensors JSON header and return (header_dict, data_start_offset)."""
    with path.open("rb") as handle:
        raw = handle.read(8)
        if len(raw) < 8:
            raise ValueError("too short to be a safetensors file")
        length = struct.unpack("<Q", raw)[0]
        if not 0 < length <= MAX_HEADER:
            raise ValueError("header length out of range")
        header = json.loads(handle.read(length).decode("utf-8"))
    if not isinstance(header, dict):
        raise ValueError("invalid safetensors header")
    return header, 8 + length


def names_in(path: Path) -> list[str]:
    """The tensor names in a safetensors file, read without loading a tensor."""
    header, _ = _read_header(path)
    return [key for key in header if key != "__metadata__"]


# ------------------------------------------- converting upstream YuE2 LoRAs
# Standalone YuE2 LoRAs (such as PEFT / upstream NAR acoustic checkpoints) use
# unprefixed, unfused keys (model.layers.N.nar_mlp.{gate,up,down}_proj.lora_{A,B},
# llm2vae.lora_{A,B}, etc.), while ComfyUI's YuE2 loader expects fused keys under
# diffusion_model. or text_encoders. with .lora_down.weight / .lora_up.weight.
_YUE2_LAYERS = 28
_YUE2_HIDDEN = 2048
_YUE2_INTER = 6144
_YUE2_KV = 1024
_YUE2_VAE = 64

_DIRECT_DECODER_SHAPES: dict[str, tuple[int, int]] = {
    "llm2vae": (_YUE2_VAE, _YUE2_HIDDEN),
    "vae2llm": (_YUE2_HIDDEN, _YUE2_VAE),
    "time_embedder.mlp.0": (_YUE2_HIDDEN, 256),
    "time_embedder.mlp.2": (_YUE2_HIDDEN, _YUE2_HIDDEN),
}

_LAYER_PROJ_RE = re.compile(
    r"^model\.layers\.(\d+)\.(nar_mlp|ar_mlp|mlp|nar_self_attn|ar_self_attn|self_attn)\."
    r"(down_proj|gate_proj|up_proj|gate_up_proj|o_proj|q_proj|k_proj|v_proj|qkv_proj)$"
)

_FUSED_SLOTS: dict[str, list[tuple[str, int]]] = {
    "gate_up_proj": [("gate", _YUE2_INTER), ("up", _YUE2_INTER)],
    "qkv_proj": [("q", _YUE2_HIDDEN), ("k", _YUE2_KV), ("v", _YUE2_KV)],
}


def _parse_upstream_key(key: str) -> tuple[str, str, str | None, str, tuple[int, int]] | None:
    """Parse an upstream YuE2 LoRA tensor key into (prefix, target_module, slot, role, expected_shape)."""
    clean = key
    if clean.startswith("base_model.model."):
        clean = clean[len("base_model.model."):]
    if clean.endswith(".lora_A.weight"):
        base, role = clean[:-len(".lora_A.weight")], "down"
    elif clean.endswith(".lora_B.weight"):
        base, role = clean[:-len(".lora_B.weight")], "up"
    elif clean.endswith(".lora_A"):
        base, role = clean[:-len(".lora_A")], "down"
    elif clean.endswith(".lora_B"):
        base, role = clean[:-len(".lora_B")], "up"
    elif clean.endswith(".lora_down.weight"):
        base, role = clean[:-len(".lora_down.weight")], "down"
    elif clean.endswith(".lora_up.weight"):
        base, role = clean[:-len(".lora_up.weight")], "up"
    elif clean.endswith(".alpha"):
        base, role = clean[:-len(".alpha")], "alpha"
    else:
        return None

    if base in _DIRECT_DECODER_SHAPES:
        return ("diffusion_model", base, None, role, _DIRECT_DECODER_SHAPES[base])

    match = _LAYER_PROJ_RE.match(base)
    if not match:
        return None
    layer = int(match.group(1))
    if not 0 <= layer < _YUE2_LAYERS:
        return None
    block, proj = match.group(2), match.group(3)
    if block.startswith("nar_"):
        prefix = "diffusion_model"
        norm_block = block[4:]
    elif block.startswith("ar_"):
        prefix = "text_encoders"
        norm_block = block[3:]
    else:
        prefix = "text_encoders"
        norm_block = block

    if norm_block == "mlp":
        if proj == "down_proj":
            return (prefix, f"model.layers.{layer}.mlp.down_proj", None, role, (_YUE2_HIDDEN, _YUE2_INTER))
        if proj == "gate_proj":
            return (prefix, f"model.layers.{layer}.mlp.gate_up_proj", "gate", role, (_YUE2_INTER, _YUE2_HIDDEN))
        if proj == "up_proj":
            return (prefix, f"model.layers.{layer}.mlp.gate_up_proj", "up", role, (_YUE2_INTER, _YUE2_HIDDEN))
        if proj == "gate_up_proj":
            return (prefix, f"model.layers.{layer}.mlp.gate_up_proj", None, role, (_YUE2_INTER * 2, _YUE2_HIDDEN))
        return None

    if norm_block == "self_attn":
        if proj == "o_proj":
            return (prefix, f"model.layers.{layer}.self_attn.o_proj", None, role, (_YUE2_HIDDEN, _YUE2_HIDDEN))
        if proj == "q_proj":
            return (prefix, f"model.layers.{layer}.self_attn.qkv_proj", "q", role, (_YUE2_HIDDEN, _YUE2_HIDDEN))
        if proj == "k_proj":
            return (prefix, f"model.layers.{layer}.self_attn.qkv_proj", "k", role, (_YUE2_KV, _YUE2_HIDDEN))
        if proj == "v_proj":
            return (prefix, f"model.layers.{layer}.self_attn.qkv_proj", "v", role, (_YUE2_KV, _YUE2_HIDDEN))
        if proj == "qkv_proj":
            return (prefix, f"model.layers.{layer}.self_attn.qkv_proj", None, role, (_YUE2_HIDDEN + _YUE2_KV * 2, _YUE2_HIDDEN))
        return None
    return None


def _plan_upstream_conversion(header: dict) -> dict[tuple[str, str], dict] | None:
    """Validate that a safetensors header is a convertible upstream YuE2 LoRA and return its grouping plan."""
    groups: dict[tuple[str, str], dict] = {}
    tensor_keys = [k for k in header if k != "__metadata__"]
    if not tensor_keys:
        return None
    for key in tensor_keys:
        parsed = _parse_upstream_key(key)
        if not parsed:
            return None
        prefix, target, slot, role, expected = parsed
        info = header[key]
        if not isinstance(info, dict) or info.get("dtype") not in ("F32", "F16", "BF16"):
            return None
        shape = info.get("shape")
        if role == "alpha":
            if shape not in ([], [1]):
                return None
        else:
            if not isinstance(shape, list) or len(shape) != 2:
                return None
        slot_key = slot or ""
        group = groups.setdefault((prefix, target), {})
        slot_entry = group.setdefault(slot_key, {"expected": expected})
        if role in slot_entry:
            return None
        slot_entry[role] = key

    if not groups:
        return None

    # Validate shapes and that every slot has both down and up tensors of matching rank.
    for (_, target), slots in groups.items():
        if "" in slots and len(slots) > 1:
            return None
        for slot_key, entry in slots.items():
            if "down" not in entry or "up" not in entry:
                return None
            out_dim, in_dim = entry["expected"]
            down_shape = header[entry["down"]]["shape"]
            up_shape = header[entry["up"]]["shape"]
            rank = down_shape[0]
            if rank <= 0 or down_shape[1] != in_dim or up_shape[0] != out_dim or up_shape[1] != rank:
                return None
    return groups


def _read_f32_tensor(handle, data_start: int, info: dict) -> np.ndarray:
    start, end = info["data_offsets"]
    handle.seek(data_start + start)
    raw = handle.read(end - start)
    dtype = info["dtype"]
    if dtype == "F32":
        arr = np.frombuffer(raw, dtype="<f4").copy()
    elif dtype == "F16":
        arr = np.frombuffer(raw, dtype="<f2").astype(np.float32)
    elif dtype == "BF16":
        u32 = np.frombuffer(raw, dtype="<u2").astype(np.uint32) << np.uint32(16)
        arr = u32.view(np.float32).copy()
    else:
        raise ValueError(f"unsupported tensor dtype {dtype}")
    shape = info["shape"]
    return arr.reshape(shape) if shape else arr.reshape(())


def _f32_to_bf16_bytes(arr: np.ndarray) -> bytes:
    f32 = np.ascontiguousarray(arr, dtype="<f4")
    u32 = f32.view(np.uint32)
    lsb = (u32 >> np.uint32(16)) & np.uint32(1)
    rounded = u32 + np.uint32(0x7FFF) + lsb
    return (rounded >> np.uint32(16)).astype("<u2").tobytes()


def _write_safetensors(dest: Path, tensors: dict[str, tuple[str, list[int], bytes]], metadata: dict | None = None) -> None:
    header: dict = {}
    if metadata:
        header["__metadata__"] = {str(k): str(v) for k, v in metadata.items()}
    offset = 0
    chunks: list[bytes] = []
    for name in sorted(tensors):
        dtype, shape, raw = tensors[name]
        end = offset + len(raw)
        header[name] = {"dtype": dtype, "shape": shape, "data_offsets": [offset, end]}
        chunks.append(raw)
        offset = end
    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    tmp = dest.with_name(dest.name + ".converting")
    try:
        with tmp.open("wb") as out:
            out.write(struct.pack("<Q", len(header_bytes)))
            out.write(header_bytes)
            for chunk in chunks:
                out.write(chunk)
        tmp.replace(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def convert_upstream_yue2_lora(source: Path, dest: Path) -> str | None:
    """Convert an unprefixed/unfused upstream YuE2 LoRA to ComfyUI format.

    Returns the converted kind ("planner", "decoder", or "both") on success, or None if
    source is not a convertible upstream YuE2 LoRA.
    """
    header, data_start = _read_header(source)
    plan = _plan_upstream_conversion(header)
    if not plan:
        return None

    out_tensors: dict[str, tuple[str, list[int], bytes]] = {}
    prefixes_written: set[str] = set()

    with source.open("rb") as handle:
        for (prefix, target), slots in plan.items():
            prefixes_written.add(prefix)
            full_base = f"{prefix}.{target}"
            if "" in slots:
                entry = slots[""]
                down = _read_f32_tensor(handle, data_start, header[entry["down"]])
                up = _read_f32_tensor(handle, data_start, header[entry["up"]])
                rank = int(down.shape[0])
                if "alpha" in entry:
                    alpha = float(_read_f32_tensor(handle, data_start, header[entry["alpha"]]).reshape(-1)[0])
                    up = up * (alpha / rank)
                out_tensors[f"{full_base}.lora_down.weight"] = ("BF16", list(down.shape), _f32_to_bf16_bytes(down))
                out_tensors[f"{full_base}.lora_up.weight"] = ("BF16", list(up.shape), _f32_to_bf16_bytes(up))
                out_tensors[f"{full_base}.alpha"] = ("F32", [], struct.pack("<f", float(rank)))
            else:
                fused_name = target.rsplit(".", 1)[-1]
                slot_layout = _FUSED_SLOTS[fused_name]
                downs: list[np.ndarray] = []
                ups: list[tuple[int, int, np.ndarray]] = []
                row_offset = 0
                total_out = sum(size for _, size in slot_layout)
                in_dim = 0
                for slot_name, slot_out in slot_layout:
                    if slot_name in slots:
                        entry = slots[slot_name]
                        down = _read_f32_tensor(handle, data_start, header[entry["down"]])
                        up = _read_f32_tensor(handle, data_start, header[entry["up"]])
                        rank = int(down.shape[0])
                        in_dim = int(down.shape[1])
                        if "alpha" in entry:
                            alpha = float(_read_f32_tensor(handle, data_start, header[entry["alpha"]]).reshape(-1)[0])
                            up = up * (alpha / rank)
                        downs.append(down)
                        ups.append((row_offset, slot_out, up))
                    row_offset += slot_out
                fused_down = np.concatenate(downs, axis=0)
                total_rank = int(fused_down.shape[0])
                fused_up = np.zeros((total_out, total_rank), dtype=np.float32)
                col_offset = 0
                for r_off, s_out, up in ups:
                    r = int(up.shape[1])
                    fused_up[r_off:r_off + s_out, col_offset:col_offset + r] = up
                    col_offset += r
                out_tensors[f"{full_base}.lora_down.weight"] = ("BF16", [total_rank, in_dim], _f32_to_bf16_bytes(fused_down))
                out_tensors[f"{full_base}.lora_up.weight"] = ("BF16", [total_out, total_rank], _f32_to_bf16_bytes(fused_up))
                out_tensors[f"{full_base}.alpha"] = ("F32", [], struct.pack("<f", float(total_rank)))

    meta = dict(header.get("__metadata__") or {}) if isinstance(header.get("__metadata__"), dict) else {}
    meta["yeufonic_converted"] = "upstream_yue2"
    _write_safetensors(dest, out_tensors, metadata=meta)
    has_planner = PLANNER in prefixes_written
    has_decoder = DECODER in prefixes_written
    if has_planner and has_decoder:
        return "both"
    return "planner" if has_planner else "decoder"


def kind_of(names: list[str]) -> str:
    """planner, decoder, both, or other for a file this engine cannot chain."""
    planner = any(name.startswith(PLANNER + ".") for name in names)
    decoder = any(name.startswith(DECODER + ".") for name in names)
    if planner and decoder:
        return "both"
    if planner:
        return "planner"
    if decoder:
        return "decoder"
    return "other"


def folder() -> Path | None:
    """Where the LoRA files are, when this machine can see them.  With the app
    and the engine on different machines it cannot, and the catalogue then says
    only what the engine reported."""
    path = Path(config.MODELS_DIR) / "loras"
    return path if path.is_dir() else None


def note_for(path: Path) -> dict:
    """A LoRA's own notes, from a text file beside it.

    A file name is not a description. `mltnt_roots.safetensors` says nothing
    about what it does, and the people who publish these write a paragraph that
    is left behind on a web page. So a `.txt` of the same name is read if it is
    there: the first line names it, the rest describes it.

    Nothing has to have one, and anything can: a LoRA of your own gets a note by
    writing one beside it."""
    sidecar = path.with_suffix(".txt")
    if not sidecar.is_file():
        return {}
    try:
        lines = sidecar.read_text(encoding="utf-8").strip().split("\n")
    except (OSError, UnicodeDecodeError) as err:
        log.warning("could not read %s: %s", sidecar.name, err)
        return {}
    title = lines[0].strip()
    rest, trigger, styles, strengths = [], None, [], None
    for line in lines[1:]:
        # A trigger word has to be typed into the style, or the LoRA barely
        # shows, so it is pulled out of the prose and shown on its own.
        if line.lower().startswith("trigger:"):
            trigger = line.split(":", 1)[1].strip()
            continue
        style = parse_style(line)
        if style:
            styles.append(style)
            continue
        found = parse_strengths(line)
        if found:
            strengths = found
            continue
        rest.append(line)
    body = "\n".join(rest).strip()
    return {k: v for k, v in (("title", title), ("note", body), ("trigger", trigger), ("styles", styles),
                              ("strengths", strengths)) if v}


# The strengths a LoRA starts at when it is chosen, kept in its note so they travel with
# it when it is shared:  Strengths: Planner 0.80, Sound 0.60
STRENGTHS = re.compile(r"^strengths:\s*planner\s+([\d.]+)\s*,\s*sound\s+([\d.]+)\s*$", re.I)


def parse_strengths(line: str) -> dict | None:
    match = STRENGTHS.match(line.strip())
    if not match:
        return None
    try:
        return {"planner": float(match.group(1)), "sound": float(match.group(2))}
    except ValueError:
        return None


def set_strengths(path: Path, planner: float | None, sound: float | None) -> None:
    """Write, replace or (with both None) remove the Strengths line in a LoRA's note,
    just under its trigger word.  A LoRA with no note gets one named after its file."""
    sidecar = path.with_suffix(".txt")
    try:
        lines = sidecar.read_text(encoding="utf-8").rstrip("\n").split("\n") if sidecar.is_file() else [path.stem]
    except (OSError, UnicodeDecodeError):
        lines = [path.stem]
    lines = [line for line in lines if not parse_strengths(line)]
    if planner is not None and sound is not None:
        at = next((i + 1 for i, line in enumerate(lines) if line.lower().startswith("trigger:")), 1)
        lines.insert(at, f"Strengths: Planner {planner:.2f}, Sound {sound:.2f}")
    sidecar.write_text("\n".join(lines) + "\n", encoding="utf-8")


# A learned style travels in the note as one line, so a LoRA shared as its file and
# note still offers its chips:  Style: Jet | pop, synth, male vocal, key of A major | 136
STYLE_PREFIX = "style:"


def parse_style(line: str) -> dict | None:
    if not line.lower().startswith(STYLE_PREFIX):
        return None
    parts = [part.strip() for part in line.split(":", 1)[1].split("|")]
    if len(parts) < 2 or not parts[1]:
        return None
    tempo = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
    return {"title": parts[0], "prompt": parts[1], "hint": parts[1], "tempo": tempo, "key": None}


def style_line(style: dict) -> str:
    clean = lambda text: str(text or "").replace("|", "/").replace("\n", " ").strip()
    tempo = f" | {style['tempo']}" if style.get("tempo") else ""
    return f"Style: {clean(style.get('title'))} | {clean(style.get('prompt'))}{tempo}"


def note_with_styles(path: Path, styles: list[dict]) -> str:
    """The note beside a LoRA, with its learned styles written in, replacing any it
    already carries.  A LoRA with no note gets one named after its file."""
    sidecar = path.with_suffix(".txt")
    try:
        lines = sidecar.read_text(encoding="utf-8").rstrip().split("\n") if sidecar.is_file() else [path.stem]
    except (OSError, UnicodeDecodeError):
        lines = [path.stem]
    lines = [line for line in lines if not parse_style(line)]
    while lines and not lines[-1].strip():
        lines.pop()
    if styles:
        lines += [""] + [style_line(style) for style in styles]
    return "\n".join(lines) + "\n"


def bundle(path: Path, styles: list[dict], dest: Path) -> Path:
    """One file to hand to someone else: the LoRA and its note, styles included.
    Stored rather than compressed, since a safetensors file does not compress."""
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.write(path, path.name)
        archive.writestr(path.with_suffix(".txt").name, note_with_styles(path, styles))
    return dest


def remove(name: str, root: Path | None = None) -> list[str]:
    """Delete a LoRA and what belongs to it alone: its note, its training log, and
    its line in families.txt.  A line naming a whole set by its prefix is left, since
    other files share it."""
    root = root or folder()
    if not root:
        raise ValueError("the app cannot see the engine's model folder")
    path = root / name
    stem = path.stem
    gone = []
    for item in (path, root / f"{stem}.txt", root / f"{stem}_log.json"):
        if item.is_file():
            item.unlink()
            gone.append(item.name)
    listing = root / "families.txt"
    if listing.is_file():
        lines = listing.read_text(encoding="utf-8").split("\n")
        kept = [line for line in lines
                if line.strip().startswith("#") or line.partition("=")[0].strip().lower() != stem.lower()]
        if len(kept) != len(lines):
            text = "\n".join(kept)
            while "\n\n\n" in text:
                text = text.replace("\n\n\n", "\n\n")
            listing.write_text(text, encoding="utf-8")
            gone.append("its line in families.txt")
    log.info("removed LoRA %s: %s", name, ", ".join(gone))
    return gone


# ------------------------------------------------------------ a previous run
# Training again under a name that already has a LoRA would replace it, and leave
# behind any checkpoints past the new run's last step, looking like its own.  So
# before a run starts, the last one's files are set aside under a dated name, or
# deleted, as the user chooses.
PREVIOUS_FAMILY = "Previous runs"


def run_files(base: str, root: Path) -> list[Path]:
    """The LoRA files a training run left under this name: the LoRA, its trainer's
    best copy and its checkpoints.  Notes and the log travel with them."""
    found = [root / f"{base}.safetensors", root / f"{base}_best.safetensors",
             *sorted(root.glob(f"{base}_step*.safetensors"))]
    return [path for path in found if path.is_file() and re.fullmatch(rf"{re.escape(base)}(_best|_step\d+)?", path.stem)]


def previous_run(base: str, root: Path | None) -> dict | None:
    """What is already there under this run name, if anything: how many files, and
    the day it was trained."""
    files = run_files(base, root) if root else []
    if not files:
        return None
    trained = max(path.stat().st_mtime for path in files)
    when = time.localtime(trained)          # "%-d" is not on Windows, where this also runs
    return {"files": len(files), "trained": trained, "day": f"{when.tm_mday} {time.strftime('%b', when)}"}


def _drop_family(stem: str, root: Path) -> None:
    listing = root / "families.txt"
    if not listing.is_file():
        return
    lines = listing.read_text(encoding="utf-8").split("\n")
    kept = [line for line in lines if line.strip().startswith("#") or line.partition("=")[0].strip().lower() != stem.lower()]
    if len(kept) != len(lines):
        listing.write_text("\n".join(kept), encoding="utf-8")


def _add_family(stem: str, family: str, root: Path) -> None:
    listing = root / "families.txt"
    existing = listing.read_text(encoding="utf-8") if listing.is_file() else ""
    joiner = "" if not existing or existing.endswith("\n") else "\n"
    listing.write_text(existing + joiner + f"{stem.lower()} = {family}\n", encoding="utf-8")


def set_aside(base: str, root: Path, title: str) -> str:
    """Rename a previous run's files to a dated name, retitled "<title> · <day>
    (previous)", in a group of their own.  Returns the new name."""
    info = previous_run(base, root)
    if not info:
        return base
    stamp = time.strftime("%Y%m%d", time.localtime(info["trained"]))
    new = f"{base}_{stamp}"
    if any(root.glob(f"{new}*.safetensors")):
        new = f"{base}_{time.strftime('%Y%m%d_%H%M', time.localtime(info['trained']))}"
    label = f"{title} · {info['day']} (previous)"
    for path in run_files(base, root):
        old_stem = path.stem
        if old_stem.endswith("_best"):
            path.unlink()              # the trainer's copy of the LoRA itself
            continue
        suffix = old_stem[len(base):]
        new_stem = new + suffix
        path.rename(root / f"{new_stem}.safetensors")
        note = root / f"{old_stem}.txt"
        lines = note.read_text(encoding="utf-8").split("\n") if note.is_file() else [""]
        lines[0] = label + (f" · step {suffix[5:].lstrip('0') or '0'}" if suffix.startswith("_step") else "")
        (root / f"{new_stem}.txt").write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
        note.unlink(missing_ok=True)
        _drop_family(old_stem, root)
        _add_family(new_stem, PREVIOUS_FAMILY, root)
    log_file = root / f"{base}_log.json"
    if log_file.is_file():
        log_file.rename(root / f"{new}_log.json")
    log.info("set the previous %s aside as %s", base, new)
    return new


def run_lora(name: str) -> str:
    """The LoRA a training run's other files belong to: its checkpoints (base_stepN),
    the trainer's best copy, and a previous run set aside (base_20260920_stepN).
    Anything else is its own."""
    stem = name.removesuffix(".safetensors")
    found = re.fullmatch(r"(.+?)(?:_\d{8}(?:_\d{4})?)?(?:_step\d+|_best)?", stem)
    return f"{found.group(1)}.safetensors" if found else name


def checkpoints(base: str, root: Path | None) -> list[dict]:
    """The checkpoints a corpus's training runs kept: this run's (base_stepN) and any
    previous run's, set aside under a dated name (base_20260920_stepN).  Each with its
    run, its step and its size, this run first, then the newest previous one."""
    if not root:
        return []
    pattern = re.compile(rf"{re.escape(base)}(?:_(\d{{8}}(?:_\d{{4}})?))?_step(\d+)")
    found = []
    for path in root.glob(f"{base}*_step*.safetensors"):
        match = pattern.fullmatch(path.stem)
        if match and path.is_file():
            found.append({"name": path.name, "run": match.group(1) or "", "step": int(match.group(2)),
                          "bytes": path.stat().st_size})
    found.sort(key=lambda item: (item["run"] != "", _reverse(item["run"]), item["step"]))
    return found


def _reverse(text: str) -> str:
    """Sorts dated run names newest first."""
    return "".join(chr(0x10FFFF - ord(ch)) for ch in text)


def delete_run(base: str, root: Path) -> int:
    """Delete a previous run's LoRA, its checkpoints, their notes and its log."""
    files = run_files(base, root)
    for path in files:
        remove(path.name, root)
    (root / f"{base}_log.json").unlink(missing_ok=True)
    log.info("deleted the previous %s: %d files", base, len(files))
    return len(files)


# The group a LoRA installed from someone else's bundle goes in.
INSTALLED_FAMILY = "Installed"


def install_shared(source: Path, filename: str, root: Path | None = None) -> dict:
    """Put a LoRA someone shared where the engine looks: a bundle from Download (the
    file and its note), or a bare safetensors file.  The note is kept as it came, so
    the LoRA arrives with its name, trigger word and chips."""
    root = root or folder()
    if not root:
        raise ValueError("the app cannot see the engine's model folder")
    note = None
    if zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            members = [m for m in archive.infolist() if not m.is_dir()]
            weights = [m for m in members if m.filename.lower().endswith(".safetensors")]
            if len(weights) != 1:
                raise ValueError("that zip should hold one .safetensors file")
            stem = Path(weights[0].filename).stem
            texts = [m for m in members if Path(m.filename).name.lower() == f"{stem.lower()}.txt"]
            staged = source.with_name(source.name + ".lora")
            with archive.open(weights[0]) as src, staged.open("wb") as out:
                shutil.copyfileobj(src, out)
            if texts:
                note = archive.read(texts[0]).decode("utf-8", errors="replace")
        weights_path = staged
    else:
        stem = Path(filename or "lora").stem
        weights_path = source
    converted = False
    try:
        names = names_in(weights_path)          # raises if it is not a safetensors file
        if not names:
            raise ValueError("that file holds no tensors")
        kind = kind_of(names)
        stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._") or "lora"
        target = root / f"{stem}.safetensors"
        if target.exists():
            raise ValueError(f"{target.name} is already in the LoRA folder")
        if kind == "other":
            converted_kind = convert_upstream_yue2_lora(weights_path, target)
            if not converted_kind:
                raise ValueError("This file is not a YuE2 LoRA that Yeufonic can use (no YuE2 planner or acoustic layers were found).")
            kind = converted_kind
            converted = True
        else:
            shutil.copyfile(weights_path, target)
    finally:
        if weights_path != source:
            weights_path.unlink(missing_ok=True)
    (root / f"{stem}.txt").write_text(note if note is not None else stem + "\n", encoding="utf-8")
    if stem.lower() not in families(root):
        with (root / "families.txt").open("a", encoding="utf-8") as handle:
            handle.write(f"\n{stem.lower()} = {INSTALLED_FAMILY}\n")
    log.info("installed shared LoRA %s (%s%s)", target.name, kind, ", converted from upstream format" if converted else "")
    result = {"name": target.name, "kind": kind, "styles": len(note_for(target).get("styles", []))}
    if converted:
        result["converted"] = True
    return result


def install(source: Path, name: str, trigger: str, corpus: str, root: Path | None = None) -> dict:
    """Put a trained LoRA where the engine looks, with a note beside it.

    The app cannot train, so the file arrives from a trainer elsewhere.  It goes into
    the LoRA folder with a .txt naming it and giving its trigger word — the same note
    the downloaded ones carry — and the family file gains a line, so the picker groups
    it under the corpus it came from instead of leaving it under Other."""
    root = root or folder()
    if not root:
        raise ValueError("the app cannot see the engine's model folder")
    names = names_in(source)             # raises if it is not a safetensors file
    if not names:
        raise ValueError("that file holds no tensors")
    kind = kind_of(names)

    stem = re.sub(r"[^a-z0-9]+", "_", (name or source.stem).lower()).strip("_") or "lora"
    target = root / f"{stem}.safetensors"
    if target.exists():
        raise ValueError(f"{target.name} is already in the LoRA folder")

    converted = False
    if kind == "other":
        converted_kind = convert_upstream_yue2_lora(source, target)
        if not converted_kind:
            raise ValueError("This file is not a YuE2 LoRA that Yeufonic can use (no YuE2 planner or acoustic layers were found).")
        kind = converted_kind
        converted = True
        names = names_in(target)
    else:
        shutil.copyfile(source, target)
    write_note(target, trigger, corpus, title=name)
    log.info("installed %s (%s%s)", target.name, kind, ", converted from upstream format" if converted else "")
    result = {"name": target.name, "kind": kind, "trigger": trigger.lower(), "tensors": len(names)}
    if converted:
        result["converted"] = True
    return result


# The group every LoRA made from one of your corpora shares.  Its own note names it,
# so a group per corpus would only repeat that name above it.
CORPUS_FAMILY = "Your corpora"
# The checkpoints a training run writes along the way.  Kept, since an earlier one can
# suit a voice better than the last, but in a group of their own below the finished LoRAs.
CHECKPOINT_FAMILY = "Training checkpoints"


def write_note(path: Path, trigger: str, corpus: str, title: str = "", root: Path | None = None,
               family: str = CORPUS_FAMILY) -> Path:
    """The text file the picker reads: what the file is called, its trigger word, and
    where it came from.  Used for a LoRA installed by hand and for one trained here."""
    root = root or path.parent
    stem = path.stem
    note = [title or stem]
    if trigger:
        note.append(f"Trigger: {trigger.lower()}")
    note.append("")
    note.append(f"Trained from the corpus {corpus} on {time.strftime('%Y-%m-%d')}.")
    # Which halves the file holds is what the picker says, with the strength each one
    # needs, so the note does not repeat it.
    note_path = root / f"{stem}.txt"
    note_path.write_text("\n".join(note) + "\n", encoding="utf-8")

    # Grouped by the whole file name, not the word in front of it: that word is often a
    # first name, and jane_doe would take in jane_smith.
    if stem.lower() not in families(root):
        path_families = root / "families.txt"
        existing = path_families.read_text(encoding="utf-8") if path_families.exists() else None
        header = ("# The picker groups LoRAs by the word in front of the file name.\n" if existing is None
                  else "" if existing.endswith("\n") or not existing else "\n")
        with path_families.open("a", encoding="utf-8") as handle:
            handle.write(header + f"{stem.lower()} = {family}\n")
    return note_path


def families(root: Path | None) -> dict[str, str]:
    """Readable names for the groups the picker makes, from `families.txt`.

    Authors name a set with a code — chnsn, mltnt — and the picker groups on it
    because that is what the file names carry. `chnsn = Chanson francaise` in
    that file turns the heading into something a person can read."""
    if not root:
        return {}
    path = root / "families.txt"
    out = {}
    try:
        if not path.is_file():
            return {}
        for line in path.read_text(encoding="utf-8").split("\n"):
            if "=" in line and not line.strip().startswith("#"):
                key, _, label = line.partition("=")
                out[key.strip().lower()] = label.strip()
    except (OSError, UnicodeDecodeError) as err:
        log.warning("could not read families.txt: %s", err)
    return out


_DESCRIBE_CACHE: dict[tuple[str, int, int], dict] = {}


def describe(name: str, root: Path | None) -> dict:
    """One entry for the picker: what the file is, what it is for, and whether
    it can be read at all."""
    entry = {"name": name, "kind": "unknown", "reserved": name in RESERVED}
    if not root:
        return entry
    path = root / name
    # One look at the file and one at its notes: the state poll asks this of every LoRA every two seconds, and
    # is_file, stat and is_file again on each was four or five calls to the disk apiece.
    try:
        found = os.stat(path)
    except OSError:
        return entry
    if not stat.S_ISREG(found.st_mode):
        return entry
    try:
        sidecar_mtime = os.stat(os.path.splitext(path)[0] + ".txt").st_mtime_ns
    except OSError:
        sidecar_mtime = 0
    cache_key = (str(path), found.st_mtime_ns, sidecar_mtime)
    cached = _DESCRIBE_CACHE.get(cache_key)
    if cached is not None:
        return dict(cached)

    try:
        entry["kind"] = kind_of(names_in(path))
    except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as err:
        # A file the engine lists but this side cannot parse is still offered:
        # the engine is the one that has to load it.
        log.warning("could not read %s: %s", name, err)
    entry.update(note_for(path))
    if cache_key is not None:
        if len(_DESCRIBE_CACHE) > 500:
            _DESCRIBE_CACHE.clear()
        _DESCRIBE_CACHE[cache_key] = dict(entry)
    return entry


def catalogue(listed: list[str]) -> list[dict]:
    """Everything the engine can load, with what each one holds.  The engine's
    list is the authority on what exists; the files only add detail."""
    root = folder()
    named = families(root)
    entries = []
    for name in listed:
        entry = describe(name, root)
        stem = name.replace(".safetensors", "").lower()
        family = stem.split("-")[0].split("_")[0]
        if stem in named or family in named:
            entry["family"] = named.get(stem) or named[family]
        entries.append(entry)
    return entries


def usable(entry: dict) -> bool:
    """A style LoRA has to hold a half this app knows how to chain, and must not
    be one the app already applies for another reason."""
    return not entry["reserved"] and entry["kind"] in ("planner", "decoder", "both", "unknown")
