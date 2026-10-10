"""Where files live in the data folder, and what the app reads from them: names,
the take.json sidecar, durations and waveform peaks."""
from __future__ import annotations

import json
import logging
import math
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import config
from .db import execute, get_setting, rows

log = logging.getLogger("yue2.library")


def slugify(text: str, limit: int = 40) -> str:
    """A short name a person can read, for use in a folder or file name."""
    text = re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower())
    return re.sub(r"-{2,}", "-", text).strip("-")[:limit].strip("-") or "untitled"


def take_folder(take_id: str, title: str) -> Path:
    """takes/<title>-<id>/ so the folder says what it holds and stays unique."""
    return config.TAKES_DIR / f"{slugify(title)}-{take_id}"


def take_audio_path(take_id: str, title: str) -> Path:
    return take_folder(take_id, title) / f"{slugify(title)}.flac"


def source_path(digest: str, filename: str, fallback: str, ext: str) -> Path:
    """sources/<hash>-<original name><ext>, so the file still says what it was."""
    name = slugify(Path(filename).stem if filename else fallback, 40)
    return config.SOURCES_DIR / f"{digest[:16]}-{name}{ext}"


def remove_tree(path: Path | None) -> None:
    """Delete a folder and everything in it.  A folder that is already gone is fine."""
    if path is None:
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def write_take_note(take: dict, audio: Path) -> None:
    """A sidecar, so a folder copied out of the library explains itself."""
    note = {
        "id": take["id"],
        "title": take["title"],
        "kind": take["kind"],
        "style": take.get("style"),
        "lyrics": take.get("lyrics"),
        "seed": take.get("seed"),
        "mode": take.get("mode"),
        "variety": take.get("variety"),
        "harmony": take.get("harmony"),
        "interpretation": take.get("interpretation"),
        "feel": take.get("feel") if take.get("kind") == "instrumental" else None,
        "checkpoint": take.get("checkpoint"),
        "duration": take.get("duration"),
        "created_at": take.get("created_at"),
        "source_id": take.get("source_id"),
        "audio": audio.name,
        "score": take.get("abc"),
        "app": "Yeufonic",
        "version": config.VERSION,
    }
    try:
        (audio.parent / "take.json").write_text(json.dumps(note, indent=2), encoding="utf-8")
    except OSError as exc:
        log.warning("could not write the take note: %s", exc)


# What a take's folder holds besides its audio, all made again when missing.
_REMADE = ("take.json", "*.peaks.json")
TAKE_FOLDER = re.compile(r"^(?:.+-)?([0-9a-f]{12})$")


def _clear_remade(folder: Path) -> None:
    """Drop the files a take's old folder can do without, and the folder if that
    empties it.  Audio is never removed here."""
    for pattern in _REMADE:
        for path in folder.glob(pattern):
            path.unlink(missing_ok=True)
    try:
        folder.rmdir()
    except OSError:
        pass


def _bring_along(have: Path, want: Path) -> None:
    """A renamed take's other audio moves with it: the file as rendered, when the take
    plays its normalised copy, the unmastered premaster copy, and the as-rendered copy the first version of
    normalising kept.  Left behind, Normalise or unbaking could not be undone."""
    for old, new in ((rendered_path(have), rendered_path(want)), (original_path(have), original_path(want)), (premaster_path(have), premaster_path(want))):
        if old != have and old.exists() and not new.exists():
            shutil.move(str(old), str(new))
    _clear_remade(have.parent)


def rescue_stranded() -> int:
    """Put back a normalised take's file as rendered where a rename left it behind, in
    the take's old folder, before the rename brought it along.  Then tidy the old
    folders of takes, and of takes deleted, of what is made again when missing.
    Audio with no take to go to is left where it is."""
    takes = {take["id"]: take for take in rows("SELECT id, audio_path, normalised FROM takes")}
    moved = converted = 0
    if not config.TAKES_DIR.is_dir():
        return 0
    for folder in sorted(config.TAKES_DIR.iterdir()):
        found = TAKE_FOLDER.match(folder.name) if folder.is_dir() else None
        if not found:
            continue
        take = takes.get(found.group(1))
        audio = Path(take["audio_path"]) if take and take["audio_path"] else None
        if audio and audio.parent == folder:
            continue
        if audio and audio.exists():
            left = [path for path in folder.glob("*.flac")]
            wanted = None
            if is_normalised_file(audio):
                wanted = rendered_path(audio)
                left = [path for path in left if not is_normalised_file(path) and not path.stem.endswith(".original")]
            elif take["normalised"]:
                wanted = original_path(audio)      # normalised in place: converted below
                left = [path for path in left if path.stem.endswith(".original")]
            if wanted and not wanted.exists() and len(left) == 1:
                try:
                    shutil.move(str(left[0]), str(wanted))
                    moved += 1
                    converted += wanted == original_path(audio)
                    log.info("put back the file as rendered of take %s from %s", take["id"], folder.name)
                except OSError as exc:
                    log.warning("could not put back the file as rendered of take %s: %s", take["id"], exc)
        _clear_remade(folder)
    if converted:
        convert_old_normalised()
    return moved


def relayout() -> None:
    """Rename stored files after the thing they hold.  Runs on every start and does
    nothing once the names are right.  A renamed take moves to a folder named after
    its new title, and its file as rendered goes with it.  A take.json is only
    written when missing."""
    moved = 0

    for take in rows("SELECT * FROM takes"):
        have = Path(take["audio_path"]) if take["audio_path"] else None
        if not have or not have.exists():
            continue
        want = take_audio_path(take["id"], take["title"])
        if is_normalised_file(have):
            want = normalised_path(want)
        if have != want:
            try:
                want.parent.mkdir(parents=True, exist_ok=True)
                if not want.exists():
                    shutil.move(str(have), str(want))
                    moved += 1
                    if have.parent != want.parent:
                        _bring_along(have, want)
                execute("UPDATE takes SET audio_path = ? WHERE id = ?", (str(want), take["id"]))
            except OSError as exc:
                log.warning("could not rename take %s: %s", take["id"], exc)
                continue
        if want.exists() and not (want.parent / "take.json").exists():
            take["audio_path"] = str(want)
            write_take_note(take, want)

    moved += rescue_stranded()

    for source in rows("SELECT * FROM sources"):
        have = Path(source["stored_path"])
        if not have.exists():
            continue
        want = source_path(source["sha256"], source["filename"], source["title"], have.suffix)
        if have == want:
            continue
        try:
            want.parent.mkdir(parents=True, exist_ok=True)
            if not want.exists():
                shutil.move(str(have), str(want))
                moved += 1
            execute("UPDATE sources SET stored_path = ? WHERE id = ?", (str(want), source["id"]))
        except OSError as exc:
            log.warning("could not rename source %s: %s", source["id"], exc)

    for item in rows("SELECT * FROM stem_sets WHERE folder IS NOT NULL"):
        have = Path(item["folder"])
        if not have.exists():
            continue
        want = have.parent / f"{slugify(item['title'])}-{item['id']}"
        if have == want:
            continue
        try:
            if not want.exists():
                shutil.move(str(have), str(want))
                moved += 1
            execute("UPDATE stem_sets SET folder = ? WHERE id = ?", (str(want), item["id"]))
        except OSError as exc:
            log.warning("could not rename stem set %s: %s", item["id"], exc)

    if moved:
        log.info("library relaid out, %d items renamed", moved)


# ------------------------------------------------------------------- audio info
def loudness(path: Path) -> float | None:
    """The average level of a file in dB, from ffmpeg's volumedetect.  A fifth of a
    second for a two minute take."""
    try:
        out = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(path), "-af", "volumedetect",
                              "-f", "null", "-"], capture_output=True, text=True, timeout=120).stderr
    except (subprocess.SubprocessError, OSError) as exc:
        log.warning("could not read the level of %s: %s", path.name, exc)
        return None
    found = re.search(r"mean_volume:\s*(-?[\d.]+|-inf) dB", out)
    if not found:
        return None
    return -120.0 if found.group(1) == "-inf" else round(float(found.group(1)), 1)


def fill_loudness() -> int:
    """Read the level of finished takes made before it was recorded.  It is the level
    as rendered, so a normalised take is read from the file kept from before."""
    done = 0
    for row in rows("SELECT id, audio_path FROM takes WHERE status = 'done' AND loudness IS NULL AND audio_path IS NOT NULL"):
        path = rendered_path(Path(row["audio_path"]))
        level = loudness(path) if path.exists() else None
        if level is not None:
            execute("UPDATE takes SET loudness = ? WHERE id = ?", (level, row["id"]))
            done += 1
    return done


# What a quiet take is brought up to.  Streaming services play at -14 LUFS, and a
# render that has not lost its footing lands about there.  The peak ceiling keeps
# the raised take from clipping.
NORMAL_LUFS = -14.0
NORMAL_PEAK = -1.0
# The levels Settings offers, as the setting stores them.
NORMAL_LEVELS = ("-16", "-14", "-11")


def normal_target() -> float:
    """The loudness Settings asks a normalised take to be, else the usual."""
    value = get_setting("normalise.level", None)
    return float(value) if value in NORMAL_LEVELS else NORMAL_LUFS


def replace_file(src: Path, dest: Path, tries: int = 10) -> None:
    """os.replace, waiting a moment when another program has the file open.  Windows
    refuses to replace an open file; a player or an editor usually lets go soon."""
    for attempt in range(tries):
        try:
            os.replace(src, dest)
            return
        except PermissionError:
            if attempt == tries - 1:
                raise
            time.sleep(0.3)


# A normalised take points at a louder copy beside the file as rendered, which is never
# changed.  Nothing is replaced while it may be open: Windows refuses to replace a file
# that a player, another tab or an editor is reading.
NORMALISED = ".normalised"


CAP_FADE = 4.0   # seconds faded at the end of a render the length cap stopped


def fade_out_end(rendered: Path, seconds: float = CAP_FADE) -> None:
    """Fade out the end of a render the length cap cut off, in place.  The model does
    not always stop at the end of its score, and a take stopped by the cap otherwise
    ends mid-bar at full level."""
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                            "stream=sample_fmt:format=duration", "-of", "json", str(rendered)],
                           capture_output=True, text=True, timeout=60, check=True)
    info = json.loads(probe.stdout)
    duration = float(info["format"]["duration"])
    sample_fmt = (info.get("streams") or [{}])[0].get("sample_fmt", "s16")
    staged = rendered.with_name(f"{rendered.stem}.fading{rendered.suffix}")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(rendered), "-af",
                        f"afade=t=out:st={max(0.0, duration - seconds):.3f}:d={seconds}",
                        "-sample_fmt", "s16" if sample_fmt.startswith("s16") else "s32", "-c:a", "flac", str(staged)],
                       capture_output=True, text=True, timeout=300, check=True)
        replace_file(staged, rendered)
    finally:
        staged.unlink(missing_ok=True)


def normalised_path(rendered: Path) -> Path:
    return rendered.with_name(f"{rendered.stem}{NORMALISED}{rendered.suffix}")


def is_normalised_file(audio: Path) -> bool:
    return audio.stem.endswith(NORMALISED)


def rendered_path(audio: Path) -> Path:
    """The file as rendered, whichever of the two a take points at."""
    return audio.with_name(audio.stem[:-len(NORMALISED)] + audio.suffix) if is_normalised_file(audio) else audio


def original_path(audio: Path) -> Path:
    """Where the first version of normalising kept the file as rendered, when it
    normalised a take in place.  Read only to convert such takes."""
    return audio.with_name(f"{audio.stem}.original{audio.suffix}")


def premaster_path(audio: Path) -> Path:
    """The unmastered file kept when a take has had mastering baked into it."""
    return audio.with_name(f"{audio.stem}.premaster{audio.suffix}")


def convert_old_normalised() -> int:
    """Takes normalised in place (song.flac louder, song.original.flac as rendered) get
    the present layout (song.flac as rendered, song.normalised.flac louder).  Runs at
    start, when nothing has the files open."""
    done = 0
    for take in rows("SELECT id, audio_path FROM takes WHERE normalised = 1 AND audio_path IS NOT NULL"):
        audio = Path(take["audio_path"])
        kept = original_path(audio)
        if is_normalised_file(audio) or not kept.exists() or not audio.exists():
            continue
        try:
            os.replace(audio, normalised_path(audio))
            os.replace(kept, audio)
        except OSError as exc:
            log.warning("could not convert normalised take %s: %s", take["id"], exc)
            continue
        execute("UPDATE takes SET audio_path = ? WHERE id = ?", (str(normalised_path(audio)), take["id"]))
        done += 1
    return done


def normalise(rendered: Path, target: float = NORMAL_LUFS) -> Path:
    """Write a copy of a take at the target loudness beside the file as rendered, and
    return it.  The rendered file is only read, so doing it twice gives the same result.

    One gain for the whole take, so its quiet and loud parts keep their distance, then
    a fast limiter for any peaks that gain would push past the ceiling.  Not loudnorm's
    own second pass: where the gain would clip, it falls back to riding the level as the
    song plays, and on a take whose peaks are already high that swung the gain by 10 dB,
    heard as sudden dips."""
    first = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(rendered), "-af",
                            f"loudnorm=I={target}:TP={NORMAL_PEAK}:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, timeout=300).stderr
    found = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", first)
    if not found:
        raise RuntimeError("ffmpeg could not measure the take's loudness")
    measured = json.loads(found.group(0))
    loudness, peak = float(measured["input_i"]), float(measured["input_tp"])
    if not math.isfinite(loudness):
        raise RuntimeError("the take is silent")
    gain = target - loudness
    chain = f"volume={gain:.2f}dB"
    if peak + gain > NORMAL_PEAK:
        # Four times oversampled, so the peaks between samples are caught too, and a
        # tenth of a dB under the ceiling for what the resampling back adds.
        ceiling = 10 ** ((NORMAL_PEAK - 0.1) / 20)
        chain += f",aresample=192000,alimiter=limit={ceiling:.4f}:attack=5:release=50:level=0"
    rate, bits = 48000, 16
    with rendered.open("rb") as fh:
        head = fh.read(26)
    if head[:4] == b"fLaC" and len(head) >= 26:
        packed = int.from_bytes(head[18:26], "big")
        rate, bits = (packed >> 44) or 48000, ((packed >> 36) & 0x1F) + 1
    audio = normalised_path(rendered)
    staged = rendered.with_name(f"{rendered.stem}.normalising{rendered.suffix}")
    try:
        # Back at the rendered file's rate and depth: the filters work in floating
        # point, which FLAC would otherwise keep at 32 bits, twice the size.
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(rendered), "-af", chain,
                        "-ar", str(rate), "-sample_fmt", "s16" if bits <= 16 else "s32",
                        "-c:a", "flac", str(staged)],
                       capture_output=True, text=True, timeout=300, check=True)
        replace_file(staged, audio)
    finally:
        staged.unlink(missing_ok=True)
    return audio


def audio_duration(path: Path) -> float | None:
    """FLAC carries its length in the header, which is instant.  Anything else, or a
    FLAC that does not say, goes to ffprobe."""
    try:
        with path.open("rb") as fh:
            head = fh.read(26)
        if head[:4] == b"fLaC" and len(head) >= 26:
            packed = int.from_bytes(head[18:26], "big")
            sample_rate = packed >> 44
            total_samples = packed & ((1 << 36) - 1)
            if sample_rate and total_samples:
                return round(total_samples / sample_rate, 2)
    except OSError as exc:
        log.warning("duration read failed for %s: %s", path, exc)
        return None
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout.strip()
        return round(float(out), 2)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        log.warning("ffprobe could not read %s: %s", path, exc)
        return None


# ---------- a saved take's tags ----------
# A take handed over by Save says what it is and what made it.  ComfyUI's own tags
# (the job's graph, as 'prompt') ride along, as they always have.
MADE_WITH = "Made with Yeufonic"


def sung_words(kind: str | None, lyrics: str | None) -> str | None:
    """The lyrics as the take has them, section tags and all.  None when nothing is
    sung: an instrumental, or a structure of section tags alone."""
    text = (lyrics or "").strip()
    if kind == "instrumental":
        return None
    words = [line for line in text.splitlines() if line.strip() and not re.fullmatch(r"\s*\[[^\]]*\]\s*", line)]
    return text if words else None


def file_tags(path: Path) -> dict[str, str]:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags", "-of", "json", str(path)],
                             capture_output=True, text=True, timeout=30, check=True).stdout
        return json.loads(out).get("format", {}).get("tags", {}) or {}
    except (OSError, subprocess.SubprocessError, ValueError):
        return {}


def _id3_frame(frame_id: str, body: bytes) -> bytes:
    return frame_id.encode("ascii") + len(body).to_bytes(4, "big") + b"\0\0" + body


def _utf16(text: str) -> bytes:
    return text.encode("utf-16")   # with its byte order mark, as ID3v2.3 wants


def id3_tag(title: str, lyrics: str | None, extra: dict[str, str]) -> bytes:
    """An ID3v2.3 tag, written here because ffmpeg can only put a comment or lyrics in
    a custom TXXX frame, which players do not show.  v2.3 rather than v2.4 because it
    is the one every player reads.  Lyrics are marked 'XXX', language unknown."""
    software = f"Yeufonic {config.VERSION}"
    frames = [_id3_frame("TIT2", b"\x01" + _utf16(title)),
              _id3_frame("TENC", b"\x01" + _utf16(software)),
              _id3_frame("TSSE", b"\x01" + _utf16(software)),
              _id3_frame("COMM", b"\x01eng" + _utf16("") + b"\0\0" + _utf16(MADE_WITH))]
    if lyrics:
        frames.append(_id3_frame("USLT", b"\x01XXX" + _utf16("") + b"\0\0" + _utf16(lyrics)))
    for key, value in extra.items():
        frames.append(_id3_frame("TXXX", b"\x01" + _utf16(key) + b"\0\0" + _utf16(value)))
    body = b"".join(frames)
    size = bytes((len(body) >> shift) & 0x7F for shift in (21, 14, 7, 0))
    return b"ID3\x03\x00\x00" + size + body


def vorbis_comments(fields: list[tuple[str, str]]) -> bytes:
    """A FLAC's tag block, written here because ffmpeg renames COMMENT to DESCRIPTION,
    a field players rarely show.  The vendor string is what reads as the encoder."""
    vendor = f"Yeufonic {config.VERSION}".encode()
    body = len(vendor).to_bytes(4, "little") + vendor + len(fields).to_bytes(4, "little")
    for key, value in fields:
        entry = f"{key}={value}".encode()
        body += len(entry).to_bytes(4, "little") + entry
    return body


def set_flac_comments(path: Path, fields: list[tuple[str, str]]) -> None:
    """Swap a FLAC's tag block for one holding fields.  The other blocks, and the
    audio after them, are left as they are."""
    data = path.read_bytes()
    if data[:4] != b"fLaC":
        raise OSError(f"{path.name} is not a FLAC")
    blocks, at, last = [], 4, False
    while not last:
        last, kind = bool(data[at] & 0x80), data[at] & 0x7F
        size = int.from_bytes(data[at + 1:at + 4], "big")
        if kind != 4:   # 4 is VORBIS_COMMENT, the tag block
            blocks.append((kind, data[at + 4:at + 4 + size]))
        at += 4 + size
    blocks.insert(1, (4, vorbis_comments(fields)))   # STREAMINFO stays first
    head = b"".join(bytes([kind | (0x80 if i == len(blocks) - 1 else 0)]) + len(body).to_bytes(3, "big") + body
                    for i, (kind, body) in enumerate(blocks))
    path.write_bytes(b"fLaC" + head + data[at:])


def build_fx_filter(fx_chain: str | dict | None) -> str | None:
    """Build an FFmpeg audio filter string (-af) matching Yeufonic's Vintage Mastering Rack.
    Returns None if fx_chain is empty, masterBypass is True, or all rack modules are transparent/bypassed."""
    if not fx_chain:
        return None
    if isinstance(fx_chain, str):
        try:
            fx_chain = json.loads(fx_chain)
        except (ValueError, TypeError):
            return None
    if not isinstance(fx_chain, dict):
        return None

    if fx_chain.get("masterBypass"):
        return None

    filters: list[str] = []

    # 1. 1073 Equalizer Stage
    eq = fx_chain.get("eq")
    if isinstance(eq, dict) and eq.get("enabled", True) is not False:
        pre_gain = float(eq.get("preGain", 0) or 0)
        if abs(pre_gain) > 0.01:
            filters.append(f"volume={pre_gain:.2f}dB")

        hp = float(eq.get("hp", 20) or 20)
        if hp > 20:
            filters.append(f"highpass=f={hp:.1f}")

        low_gain = float(eq.get("lowGain", 0) or 0)
        low_freq = float(eq.get("lowFreq", 60) or 60)
        if abs(low_gain) > 0.01 and low_freq > 0:
            filters.append(f"lowshelf=f={low_freq:.1f}:g={low_gain:.2f}")

        mid_gain = float(eq.get("midGain") if eq.get("midGain") is not None else (eq.get("mid1Gain") or 0))
        mid_freq = float(eq.get("midFreq") or eq.get("mid1Freq") or 1600)
        if abs(mid_gain) > 0.01 and mid_freq > 0:
            filters.append(f"equalizer=f={mid_freq:.1f}:width_type=q:w=1.1:g={mid_gain:.2f}")

        high_gain = float(eq.get("highGain") if eq.get("highGain") is not None else (eq.get("airGain") or 0))
        if abs(high_gain) > 0.01:
            filters.append(f"highshelf=f=6800.0:g={high_gain:.2f}")

        if eq.get("phase"):
            filters.append("volume=-1.0")

        out_level = float(eq.get("outLevel", 0) or 0)
        if abs(out_level) > 0.01:
            filters.append(f"volume={out_level:.2f}dB")

    # 2. Vintage Compressor Stage
    comp = fx_chain.get("comp")
    if isinstance(comp, dict) and comp.get("enabled", True) is not False:
        mix = float(comp.get("mix", 1.0) if comp.get("mix") is not None else 1.0)
        if mix > 0.001:
            thresh = float(comp.get("threshold", -18) if comp.get("threshold") is not None else -18)
            ratio = max(1.0, min(20.0, float(comp.get("ratio", 4) or 4)))
            att = float(comp.get("attack", 0.015) if comp.get("attack") is not None else 0.015)
            att_ms = att * 1000.0 if att < 5.0 else att
            att_ms = max(0.01, min(2000.0, att_ms))
            rel = float(comp.get("release", 0.25) if comp.get("release") is not None else 0.25)
            rel_ms = rel * 1000.0 if rel < 20.0 else rel
            rel_ms = max(0.01, min(9000.0, rel_ms))
            mk = float(comp.get("makeup", 0) or 0)
            knee_raw = float(comp.get("knee", 10) if comp.get("knee") is not None else 10)
            knee_val = max(1.0, min(8.0, 1.0 + (knee_raw / 40.0) * 7.0 if knee_raw > 8.0 else knee_raw))

            comp_opts = [
                f"threshold={thresh:.2f}dB",
                f"ratio={ratio:.2f}",
                f"attack={att_ms:.1f}",
                f"release={rel_ms:.1f}",
                f"knee={knee_val:.2f}",
                f"mix={mix:.2f}"
            ]
            if abs(mk) > 0.01:
                comp_opts.append(f"makeup={mk:.2f}dB")
            filters.append(f"acompressor={':'.join(comp_opts)}")

    # 3. Vintage Stereo Imager Stage (Placed before Master Limiter)
    imager = fx_chain.get("imager")
    if isinstance(imager, dict) and imager.get("enabled", True) is not False:
        bigness_val = float(imager.get("bigness", 1) if imager.get("bigness") is not None else 1)
        if bigness_val <= 1.0:
            slev = 1.0 if bigness_val >= 1.0 else max(0.0, bigness_val)
        else:
            slev = round(1.0 + ((bigness_val - 1.0) / 8.0) * 1.4, 2)

        stage_val = float(imager.get("stage", 5) if imager.get("stage") is not None else 5)
        phase_deg = round((stage_val - 5.0) * 4.0, 1)

        if abs(slev - 1.0) > 0.01 or abs(phase_deg) > 0.1:
            filters.append(f"stereotools=slev={slev:.2f}:mlev=1.00:phase={phase_deg:.1f}")

        if imager.get("bass"):
            filters.append("lowshelf=f=85.0:g=3.00")

        if imager.get("harmonics"):
            tube_h = float(imager.get("tubeHarmonics", 1) if imager.get("tubeHarmonics") is not None else 1)
            if tube_h > 1.0:
                drive_db = round(((tube_h - 1.0) / 8.0) * 1.8, 2)
                if drive_db > 0.01:
                    filters.append(f"volume={drive_db:.2f}dB")
            filters.append("asoftclip=type=tanh")

    # 4. Master Limiter & Tube Warmth Stage
    limit = fx_chain.get("limit")
    if isinstance(limit, dict) and limit.get("enabled", True) is not False:
        drive = float(limit.get("drive", 0) or 0)
        if abs(drive) > 0.01:
            filters.append(f"volume={drive:.2f}dB")

        if limit.get("warmth"):
            filters.append("asoftclip=type=tanh")

        ceiling = float(limit.get("ceiling", -0.1) if limit.get("ceiling") is not None else -0.1)
        limit_lin = min(1.0, max(0.0625, 10.0 ** (ceiling / 20.0)))
        l_rel = float(limit.get("release", 0.08) if limit.get("release") is not None else 0.08)
        l_rel_ms = l_rel * 1000.0 if l_rel < 10.0 else l_rel
        l_rel_ms = max(1.0, min(8000.0, l_rel_ms))
        filters.append(f"alimiter=limit={limit_lin:.4f}:attack=1:release={l_rel_ms:.1f}:level=disabled")

    return ",".join(filters) if filters else None


def tagged_copy(src: Path, dest: Path, fmt: str, codec: list[str] | None, title: str,
                lyrics: str | None, fx_chain: str | dict | None = None) -> None:
    """The take at src as a file to hand over, in fmt, with its tags.  A FLAC is copied
    rather than encoded again unless a mastering chain is active.  WAV has nowhere
    for lyrics, and ffmpeg's own tags suit it."""
    carried = {k: v for k, v in file_tags(src).items() if k.lower() != "encoder"}
    fx_filter = build_fx_filter(fx_chain)
    filter_args = ["-af", fx_filter] if fx_filter else []

    if fmt == "wav":
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), *filter_args, *(codec or []),
                        "-metadata", f"title={title}", "-metadata", f"comment={MADE_WITH}",
                        "-metadata", f"encoded_by=Yeufonic {config.VERSION}", str(dest)],
                       capture_output=True, timeout=300, check=True)
        return

    # No tags from ffmpeg: the app writes them.  For an MP3, -write_id3v2 0 still
    # leaves a v2.4 tag naming ffmpeg; -id3v2_version 0 leaves none.
    untagged = ["-map_metadata", "-1"] + (["-id3v2_version", "0"] if fmt == "mp3" else [])

    if fmt == "flac" and (fx_filter or src.suffix.lower() != ".flac"):
        flac_codec = ["-c:a", "flac"]
        try:
            with src.open("rb") as fh:
                head = fh.read(26)
            if head[:4] == b"fLaC" and len(head) >= 26:
                packed = int.from_bytes(head[18:26], "big")
                bits = ((packed >> 36) & 0x1F) + 1
                flac_codec.extend(["-sample_fmt", "s16" if bits <= 16 else "s32"])
        except Exception:
            pass
        chosen_codec = flac_codec
    else:
        chosen_codec = codec or ["-c", "copy"]

    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), *filter_args, *chosen_codec, *untagged, str(dest)],
                   capture_output=True, timeout=300, check=True)
    if fmt == "mp3":
        dest.write_bytes(id3_tag(title, lyrics, carried) + dest.read_bytes())
        return
    fields = [("TITLE", title), ("COMMENT", MADE_WITH)]
    if lyrics:
        fields.append(("LYRICS", lyrics))
    set_flac_comments(dest, fields + list(carried.items()))


# The waveform the player draws.  Computed once on the server from an 8 kHz mono
# decode, instead of the browser decoding the whole file to float PCM on every play.
PEAK_COLUMNS = 1024
PEAK_RATE = 8000


def peaks_path(audio: Path) -> Path:
    return audio.with_name(audio.stem + ".peaks.json")


def vocal_path(recording: Path) -> Path:
    """A recording's separated vocal, kept beside it once lyrics have been heard.

    The vocal depends only on the recording, which never changes, and the
    separation model, which the lyrics job fixes, so separating it a second time
    gives the same file and costs most of the job's time.  FLAC: lossless, as the
    listening needs, and about half the size of the WAV the separator writes."""
    return recording.with_name(recording.stem + ".vocals.flac")


def kept_beside(recording: Path) -> list[Path]:
    """What the app keeps beside a recording, to go when the recording does."""
    return [peaks_path(recording), vocal_path(recording)]


def compute_peaks(audio: Path) -> dict:
    import numpy as np

    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(audio), "-ac", "1", "-ar", str(PEAK_RATE), "-f", "f32le", "-"],
        capture_output=True, timeout=300, check=True,
    ).stdout
    data = np.abs(np.frombuffer(raw, dtype=np.float32))
    if data.size < PEAK_COLUMNS:
        data = np.pad(data, (0, PEAK_COLUMNS - data.size))
    per = data.size // PEAK_COLUMNS
    frames = data[: per * PEAK_COLUMNS].reshape(PEAK_COLUMNS, per)
    peaks = frames.max(axis=1)
    rms = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1))

    def norm(values):
        top = float(values.max()) or 1.0
        return [round(float(v) / top, 3) for v in values]

    return {"columns": PEAK_COLUMNS, "peaks": norm(peaks), "rms": norm(rms)}


def ensure_peaks(audio: Path) -> dict | None:
    """Read the cached peaks for a file, computing them the first time."""
    cache = peaks_path(audio)
    try:
        if cache.exists() and cache.stat().st_mtime >= audio.stat().st_mtime:
            return json.loads(cache.read_text(encoding="utf-8"))
        result = compute_peaks(audio)
        cache.write_text(json.dumps(result, separators=(",", ":")), encoding="utf-8")
        return result
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        log.warning("peaks failed for %s: %s", audio, exc)
        return None
