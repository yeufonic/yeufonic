#!/usr/bin/env python3
"""Build a publishable Starter Pack package from a Yeufonic space.

Reads a Yeufonic library (read-only) and produces a self-contained directory
ready to upload to R2 (for example ``https://yeufonic.com/starter-pack/``):

    <out>/
      manifest.json               # file list, byte sizes, SHA-256 checksums
      starter-pack.zip            # pack.json + takes audio/peaks + artwork + cover sources
      voices/<id>/model.pth       # downloaded only if that voice is not already installed
      voices/<id>/model.index
      loras/<name>.safetensors    # downloaded directly into models/loras/ if not present
      loras/<name>.txt

Usage:
    python3 tools/build_starter_pack.py --out dist/starter-pack
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

# Allow importing app.starter_pack constants when run from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.starter_pack import (  # noqa: E402
    FORMAT,
    SOURCE_COLUMNS,
    SPACE_NAME,
    TAKE_COLUMNS,
    VERSION,
    VOICE_COLUMNS,
)

MANIFEST_FORMAT = "yeufonic-starter-pack-manifest"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_data_path(raw: str | None, data_dir: Path) -> Path | None:
    if not raw:
        return None
    p = Path(raw)
    if p.is_file():
        return p
    # Docker libraries record paths under /data/...
    norm = raw.replace("\\", "/")
    if norm.startswith("/data/"):
        candidate = data_dir / norm[len("/data/"):]
        if candidate.is_file():
            return candidate
    for marker in ("/takes/", "/sources/", "/voices/", "/art/"):
        idx = norm.find(marker)
        if idx >= 0:
            candidate = data_dir / norm[idx + 1:]
            if candidate.is_file():
                return candidate
    return None


def find_peaks_file(audio_path: Path) -> Path | None:
    direct = audio_path.with_suffix(".peaks.json")
    if direct.is_file():
        return direct
    return None


def build_pack(
    data_dir: Path,
    models_dir: Path,
    out_dir: Path,
    space_name: str = SPACE_NAME,
    include_voice_stems: bool = False,
) -> dict[str, Any]:
    db_path = data_dir / "yue2.sqlite"
    if not db_path.is_file():
        raise SystemExit(f"Database not found: {db_path}")

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        space = con.execute(
            "SELECT * FROM spaces WHERE LOWER(name) = LOWER(?)", (space_name,)
        ).fetchone()
        if not space:
            raise SystemExit(f"Space {space_name!r} not found in {db_path}")

        take_rows = [
            dict(r)
            for r in con.execute(
                "SELECT * FROM takes WHERE space_id = ? AND status = 'done' ORDER BY created_at",
                (space["id"],),
            )
        ]
        if not take_rows:
            raise SystemExit(f"No completed takes found in space {space_name!r}")

        voice_ids = sorted({t["voice_id"] for t in take_rows if t.get("voice_id")})
        source_ids = sorted({t["source_id"] for t in take_rows if t.get("source_id")})
        lora_names = sorted(
            {
                t[k]
                for t in take_rows
                for k in ("style_lora", "voice_lora")
                if t.get(k)
            }
        )

        voice_rows = [
            dict(r)
            for vid in voice_ids
            if (r := con.execute("SELECT * FROM voices WHERE id = ?", (vid,)).fetchone())
        ]
        source_rows = [
            dict(r)
            for sid in source_ids
            if (r := con.execute("SELECT * FROM sources WHERE id = ?", (sid,)).fetchone())
        ]
    finally:
        con.close()

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "loras").mkdir(exist_ok=True)
    (out_dir / "voices").mkdir(exist_ok=True)

    # 1. Copy LoRAs (.safetensors + optional .txt) into out_dir/loras/
    manifest_loras: list[dict[str, Any]] = []
    loras_dir = models_dir / "loras"
    for lora_file in lora_names:
        src = loras_dir / lora_file
        if not src.is_file():
            raise SystemExit(f"Referenced LoRA missing: {src}")
        dst = out_dir / "loras" / lora_file
        shutil.copy2(src, dst)
        manifest_loras.append({
            "file": lora_file,
            "path": f"loras/{lora_file}",
            "bytes": dst.stat().st_size,
            "sha256": sha256_file(dst),
        })
        txt_name = Path(lora_file).stem + ".txt"
        src_txt = loras_dir / txt_name
        if src_txt.is_file():
            dst_txt = out_dir / "loras" / txt_name
            shutil.copy2(src_txt, dst_txt)
            manifest_loras.append({
                "file": txt_name,
                "path": f"loras/{txt_name}",
                "bytes": dst_txt.stat().st_size,
                "sha256": sha256_file(dst_txt),
            })

    # 2. Copy voices into out_dir/voices/<id>/ and build pack voice metadata
    pack_voices: list[dict[str, Any]] = []
    manifest_voices: list[dict[str, Any]] = []
    for v in voice_rows:
        vid = v["id"]
        v_src_dir = data_dir / "voices" / vid
        src_model = resolve_data_path(v.get("model_path"), data_dir) or (v_src_dir / "model.pth")
        if not src_model.is_file():
            raise SystemExit(f"Referenced voice model missing for {v['name']} ({vid}): {src_model}")
        v_out_dir = out_dir / "voices" / vid
        v_out_dir.mkdir(parents=True, exist_ok=True)
        dst_model = v_out_dir / "model.pth"
        shutil.copy2(src_model, dst_model)

        voice_manifest_files = [{
            "path": f"voices/{vid}/model.pth",
            "dest": "model.pth",
            "bytes": dst_model.stat().st_size,
            "sha256": sha256_file(dst_model),
        }]
        pack_files = {"model": f"voices/{vid}/model.pth"}

        src_index = v_src_dir / "model.index"
        if src_index.is_file():
            dst_index = v_out_dir / "model.index"
            shutil.copy2(src_index, dst_index)
            voice_manifest_files.append({
                "path": f"voices/{vid}/model.index",
                "dest": "model.index",
                "bytes": dst_index.stat().st_size,
                "sha256": sha256_file(dst_index),
            })
            pack_files["index"] = f"voices/{vid}/model.index"

        v_entry: dict[str, Any] = {"id": vid, "files": pack_files}
        for col in VOICE_COLUMNS:
            if col in v and v[col] is not None:
                v_entry[col] = v[col]
        pack_voices.append(v_entry)
        manifest_voices.append({
            "id": vid,
            "name": v["name"],
            "files": voice_manifest_files,
        })

    # 3. Build starter-pack.zip containing pack.json + sources + takes + artwork
    zip_path = out_dir / "starter-pack.zip"
    pack_sources: list[dict[str, Any]] = []
    pack_takes: list[dict[str, Any]] = []
    zip_members: list[tuple[Path, str]] = []

    for s in source_rows:
        sid = s["id"]
        src_audio = resolve_data_path(s.get("stored_path"), data_dir)
        if not src_audio or not src_audio.is_file():
            raise SystemExit(f"Referenced source audio missing for {s['title']} ({sid})")
        ext = src_audio.suffix.lower() or ".flac"
        arc_audio = f"sources/{sid}{ext}"
        zip_members.append((src_audio, arc_audio))
        s_entry: dict[str, Any] = {"id": sid, "file": arc_audio}
        for col in SOURCE_COLUMNS:
            if col in s and s[col] is not None:
                s_entry[col] = s[col]
        pack_sources.append(s_entry)

    art_dir = data_dir / "art"
    for t in take_rows:
        tid = t["id"]
        src_audio = resolve_data_path(t.get("audio_path"), data_dir)
        if not src_audio or not src_audio.is_file():
            raise SystemExit(f"Take audio missing for {t['title']} ({tid}): {t.get('audio_path')}")
        ext = src_audio.suffix.lower() or ".flac"
        arc_audio = f"takes/{tid}/audio{ext}"
        zip_members.append((src_audio, arc_audio))
        t_files: dict[str, str] = {"audio": arc_audio}

        peaks = find_peaks_file(src_audio)
        if peaks:
            arc_peaks = f"takes/{tid}/audio.peaks.json"
            zip_members.append((peaks, arc_peaks))
            t_files["peaks"] = arc_peaks

        if include_voice_stems:
            v_backing = src_audio.parent / "voice" / "backing.flac"
            v_vocal = src_audio.parent / "voice" / "vocal.flac"
            if v_backing.is_file():
                arc_b = f"takes/{tid}/voice/backing.flac"
                zip_members.append((v_backing, arc_b))
                t_files["voice_backing"] = arc_b
            if v_vocal.is_file():
                arc_v = f"takes/{tid}/voice/vocal.flac"
                zip_members.append((v_vocal, arc_v))
                t_files["voice_vocal"] = arc_v

        art_png = art_dir / f"{tid}.png"
        if art_png.is_file():
            arc_art = f"art/{tid}.png"
            zip_members.append((art_png, arc_art))
            t_files["art"] = arc_art
        art_txt = art_dir / f"{tid}.txt"
        if art_txt.is_file():
            arc_words = f"art/{tid}.txt"
            zip_members.append((art_txt, arc_words))
            t_files["art_words"] = arc_words

        t_entry: dict[str, Any] = {"id": tid, "files": t_files}
        for col in TAKE_COLUMNS:
            if col in t and t[col] is not None:
                val = t[col]
                if col == "normalised":
                    val = 0
                elif col in ("fx_chain", "voice_mix", "sampling", "recording_ref") and isinstance(val, str):
                    try:
                        val = json.loads(val)
                    except ValueError:
                        pass
                t_entry[col] = val
        if t.get("source_id"):
            t_entry["source_id"] = t["source_id"]
        if t.get("voice_id"):
            t_entry["voice_id"] = t["voice_id"]
        pack_takes.append(t_entry)

    pack_id_hash = hashlib.sha256()
    pack_id_hash.update(space_name.encode("utf-8"))
    for src_file, arc_name in zip_members:
        pack_id_hash.update(arc_name.encode("utf-8"))
        pack_id_hash.update(sha256_file(src_file).encode("ascii"))
    for v in manifest_voices:
        for f in v["files"]:
            pack_id_hash.update(f["sha256"].encode("ascii"))
    for item in manifest_loras:
        pack_id_hash.update(item["sha256"].encode("ascii"))
    pack_id_hash.update(
        json.dumps(
            {"takes": pack_takes, "sources": pack_sources, "voices": pack_voices},
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    )
    pack_id = pack_id_hash.hexdigest()[:16]

    pack_doc: dict[str, Any] = {
        "format": FORMAT,
        "version": VERSION,
        "pack_id": pack_id,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "space_name": space_name,
        "takes": pack_takes,
        "sources": pack_sources,
        "voices": pack_voices,
        "loras": [item["file"] for item in manifest_loras],
    }

    # FLAC and PNG are already compressed, so ZIP_STORED for media keeps packing fast;
    # compress JSON/text with ZIP_DEFLATED.
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(
            "pack.json",
            json.dumps(pack_doc, indent=2, ensure_ascii=False) + "\n",
            compress_type=zipfile.ZIP_DEFLATED,
        )
        for src_file, arc_name in zip_members:
            ctype = zipfile.ZIP_DEFLATED if src_file.suffix.lower() in (".json", ".txt") else zipfile.ZIP_STORED
            zf.write(src_file, arc_name, compress_type=ctype)

    bundle_sha = sha256_file(zip_path)
    bundle_bytes = zip_path.stat().st_size
    voice_bytes = sum(f["bytes"] for v in manifest_voices for f in v["files"])
    lora_bytes = sum(item["bytes"] for item in manifest_loras)

    manifest = {
        "format": MANIFEST_FORMAT,
        "version": VERSION,
        "pack_id": pack_id,
        "built_at": pack_doc["built_at"],
        "space_name": space_name,
        "counts": {
            "takes": len(pack_takes),
            "voices": len(manifest_voices),
            "sources": len(pack_sources),
            "loras": len(lora_names),
        },
        "total_bytes": bundle_bytes + voice_bytes + lora_bytes,
        "bundle": {
            "path": "starter-pack.zip",
            "bytes": bundle_bytes,
            "sha256": bundle_sha,
        },
        "voices": manifest_voices,
        "loras": manifest_loras,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build a Starter Pack R2 bundle from a Yeufonic space.")
    ap.add_argument("--data", type=Path, default=Path("data"), help="Source Yeufonic data folder (default: data)")
    ap.add_argument("--models", type=Path, default=Path("models"), help="Source models folder (default: models)")
    ap.add_argument("--space", default=SPACE_NAME, help=f"Space name to export (default: {SPACE_NAME!r})")
    ap.add_argument("--out", type=Path, required=True, help="Output directory to write the R2 package into")
    ap.add_argument(
        "--include-voice-stems",
        action="store_true",
        help="Also bundle cached vocal/backing split stems for voiced takes (~118 MB larger)",
    )
    args = ap.parse_args(argv)

    manifest = build_pack(
        data_dir=args.data.resolve(),
        models_dir=args.models.resolve(),
        out_dir=args.out.resolve(),
        space_name=args.space,
        include_voice_stems=args.include_voice_stems,
    )
    c = manifest["counts"]
    mb = manifest["total_bytes"] / 1_000_000
    bundle_mb = manifest["bundle"]["bytes"] / 1_000_000
    print(f"Starter Pack built in {args.out}")
    print(f"  space:   {manifest['space_name']} (pack_id={manifest['pack_id']})")
    print(f"  takes:   {c['takes']}  sources: {c['sources']}  voices: {c['voices']}  loras: {c['loras']}")
    print(f"  bundle:  starter-pack.zip ({bundle_mb:.1f} MB)")
    print(f"  total:   {mb:.1f} MB (including LoRAs and voices)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
