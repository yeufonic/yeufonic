"""The note samples the score preview plays with.

abcjs plays a score by loading one small MP3 per note it needs, from
`<url>/<instrument>-mp3/<note>.mp3`.  The samples are not in the repository: they are
fetched from their upstream home when the person asks for them, and kept in
`data/models/soundfonts`, from where the app serves them to its own page.

The sets are not all the same size, and that is not an error: a piano runs A0 to C8
(88 notes), a clean guitar reaches G7 (89), a voice stops at Gb6 (76) and a bass at
Gb5 (64), because a bass cannot play higher than that.  So a download keeps whatever
the publisher has, a note the set never had is skipped rather than failing the whole
set, and what arrived is written to a small JSON beside it.  That record is what says
the set is here, and how far it can play — the preview shifts a score by whole octaves
to fit inside it, since one missing sample stops a whole playback."""
from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import httpx

from . import config, db, library

log = logging.getLogger("yue2.soundfonts")

# paulrosen/midi-js-soundfonts, the set abcjs uses by default.
UPSTREAM = "https://raw.githubusercontent.com/paulrosen/midi-js-soundfonts/gh-pages/abcjs/"
# The sets the score preview can play.  A score names no instruments, so the preview
# reads the style and picks one per voice; these are the ones it can choose between.
# Each is fetched from upstream only when a preview asks for it, so a library with a
# few styles on disk holds a few of them.  The keys are the upstream folder names and
# the numbers are General MIDI programs (see PREVIEW_INSTRUMENTS in app.js).
SETS = {
    "acoustic_grand_piano": "Piano",
    "electric_piano_1": "Electric piano",
    "drawbar_organ": "Organ",
    "marimba": "Marimba",
    "vibraphone": "Vibraphone",
    "acoustic_guitar_nylon": "Nylon guitar",
    "acoustic_guitar_steel": "Steel guitar",
    "electric_guitar_clean": "Clean guitar",
    "overdriven_guitar": "Overdriven guitar",
    "distortion_guitar": "Distorted guitar",
    "banjo": "Banjo",
    "acoustic_bass": "Upright bass",
    "electric_bass_finger": "Finger bass",
    "electric_bass_pick": "Pick bass",
    "slap_bass_1": "Slap bass",
    "synth_bass_1": "Synth bass",
    "violin": "Violin",
    "cello": "Cello",
    "string_ensemble_1": "Strings",
    "choir_aahs": "Choir",
    "voice_oohs": "Voice",
    "brass_section": "Brass",
    "alto_sax": "Saxophone",
    "flute": "Flute",
    "lead_2_sawtooth": "Sawtooth lead",
    "pad_2_warm": "Warm pad",
    # The drum track abcjs writes from a pattern, on the percussion channel.  Named by
    # pitch, as the others are: C2 is a kick, D2 a snare, Gb2 a closed hi-hat.
    "percussion": "Drums",
}

_FLATS = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
# The 88 keys of a piano, A0 to C8, as the files are named (flats, never sharps).
NOTES = [f"{_FLATS[m % 12]}{m // 12 - 1}" for m in range(21, 109)]
NOTE = re.compile(r"[A-G]b?[0-8]")
INSTRUMENT = re.compile(r"[a-z0-9_]+")


def folder() -> Path:
    return config.DATA_DIR / "models" / "soundfonts"


def sample(instrument: str, note: str) -> Path | None:
    """The file for one note, or None when the names are not ones we serve or it is not there."""
    if instrument not in SETS or not NOTE.fullmatch(note):
        return None
    path = folder() / f"{instrument}-mp3" / f"{note}.mp3"
    return path if path.is_file() else None


# The semitones of each note letter, and the note a MIDI number's name is built from.
_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi_of(note: str) -> int:
    """Middle C is 60: A0 is 21 and C8 is 108, the ends of a piano."""
    letter, rest = note[0], note[1:]
    shift = -1 if rest[:1] == "b" else 1 if rest[:1] == "#" else 0
    octave = rest[1:] if shift else rest
    return 12 * (int(octave) + 1) + _SEMITONES[letter] + shift


def _marker(instrument: str) -> Path:
    return folder() / f"{instrument}.json"


def notes_of(instrument: str) -> list[str]:
    """The notes this set has.  A set fetched before this record existed is recognised
    by holding the whole piano, which is what the first version of this fetched."""
    path = _marker(instrument)
    if path.is_file():
        try:
            return list(json.loads(path.read_text(encoding="utf-8")).get("notes") or [])
        except (OSError, ValueError):
            return []
    directory = folder() / f"{instrument}-mp3"
    return NOTES if all((directory / f"{note}.mp3").is_file() for note in NOTES) else []


def installed() -> list[str]:
    return [name for name in SETS if notes_of(name)]


def range_of(instrument: str) -> list[int] | None:
    """The lowest and highest note this set can play, as MIDI numbers."""
    notes = notes_of(instrument)
    if not notes:
        return None
    pitches = sorted(midi_of(note) for note in notes)
    return [pitches[0], pitches[-1]]


_orig_get = httpx.get


def download(instrument: str) -> int:
    """Fetch every note of an instrument that is not here yet, and record what arrived.
    Returns how many were fetched.  Each file is written whole or not at all; a note the
    publisher does not have is left out rather than failing the set."""
    if instrument not in SETS:
        raise ValueError(f"no such instrument: {instrument}")
    target = folder() / f"{instrument}-mp3"
    target.mkdir(parents=True, exist_ok=True)
    known = set(notes_of(instrument))
    missing = [n for n in NOTES if n not in known and not (target / f"{n}.mp3").is_file()]
    absent: list[str] = []

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        def fetch(note: str) -> None:
            url = f"{UPSTREAM}{instrument}-mp3/{note}.mp3"
            try:
                if httpx.get is not _orig_get:
                    response = httpx.get(url)
                else:
                    response = client.get(url)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response is not None and exc.response.status_code == 404:
                    absent.append(note)          # this set never had this note
                    return
                raise
            with tempfile.NamedTemporaryFile(dir=target, delete=False, suffix=".part") as handle:
                handle.write(response.content)
            Path(handle.name).replace(target / f"{note}.mp3")

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(fetch, missing))
    here = [note for note in NOTES if (target / f"{note}.mp3").is_file()]
    _marker(instrument).write_text(json.dumps({"notes": here}), encoding="utf-8")
    log.info("Fetched %d note samples for %s: %d notes from %s to %s, %d the set does not have",
             len(missing) - len(absent), instrument, len(here),
             here[0] if here else "-", here[-1] if here else "-", len(absent))
    return len(missing) - len(absent)


# ---------------------------------------------------------------- SF2 SoundFonts
def sf2_folder() -> Path:
    """The directory where .sf2 SoundFont files are stored."""
    p = folder() / "sf2"
    p.mkdir(parents=True, exist_ok=True)
    return p


_SF2_CACHE: tuple[int, list[dict[str, Any]]] = (-1, [])


def available_sf2() -> list[dict[str, Any]]:
    """List all available .sf2 SoundFont files in data/models/soundfonts/sf2."""
    global _SF2_CACHE
    sf2_dir = sf2_folder()
    try:
        dir_mtime = sf2_dir.stat().st_mtime_ns
    except OSError:
        dir_mtime = 0
    if _SF2_CACHE[0] == dir_mtime and _SF2_CACHE[0] != -1:
        return [dict(x) for x in _SF2_CACHE[1]]

    results = []
    for f in sorted(sf2_dir.glob("*.sf2")):
        size_bytes = f.stat().st_size
        size_mb = round(size_bytes / (1024 * 1024), 1)
        stem = f.stem
        if "Arachno" in stem:
            name = "Arachno SoundFont 1.0"
        elif "DSoundFont" in stem:
            name = "DSoundFont V4"
        elif "Musyng" in stem:
            name = "Musyng Kite"
        elif "Jnsgm2" in stem or "github" in stem:
            name = "Jnsgm2 GM"
        else:
            name = stem.replace("_", " ")

        results.append({
            "id": f.name,
            "filename": f.name,
            "name": name,
            "size_bytes": size_bytes,
            "size_mb": size_mb,
        })
    _SF2_CACHE = (dir_mtime, results)
    return results


def get_active_sf2() -> str | None:
    """The filename of the SoundFont currently chosen for MIDI synthesis."""
    saved = db.get_setting("midi.soundfont")
    sf2_dir = sf2_folder()
    if saved and (sf2_dir / saved).is_file():
        return saved
    # Default priority
    candidates = ["Arachno_SoundFont_Version_1.0.sf2", "Musyng_Kite.sf2", "DSoundFontV4.sf2", "github_Jnsgm2.sf2"]
    for c in candidates:
        if (sf2_dir / c).is_file():
            return c
    found = list(sf2_dir.glob("*.sf2"))
    return found[0].name if found else None


def set_active_sf2(filename: str) -> None:
    sf2_dir = sf2_folder()
    target = sf2_dir / filename
    if not target.is_file():
        raise ValueError(f"SoundFont not found: {filename}")
    db.set_setting("midi.soundfont", filename)


def render_midi_to_audio(
    midi_path: Path,
    output_path: Path,
    sf2_filename: str | None = None,
    gain: float = 0.5,
) -> Path:
    """Render a MIDI file to high-quality audio using fluidsynth and ffmpeg."""
    sf2_name = sf2_filename or get_active_sf2()
    if not sf2_name:
        raise RuntimeError("No .sf2 SoundFont available to render MIDI")
    sf2_path = sf2_folder() / sf2_name
    if not sf2_path.is_file():
        raise FileNotFoundError(f"SoundFont file not found: {sf2_path}")

    fluidsynth_bin = shutil.which("fluidsynth")
    if not fluidsynth_bin:
        raise RuntimeError("fluidsynth executable not found on system")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        wav_path = Path(tmp_wav.name)

    try:
        cmd_synth = [
            fluidsynth_bin,
            "-ni",
            "-o", "audio.file.format=float",
            "-g", str(gain),
            "-F", str(wav_path),
            str(sf2_path),
            str(midi_path),
        ]
        res = subprocess.run(cmd_synth, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            log.warning("fluidsynth non-zero return code %d: %s", res.returncode, res.stderr)
        if not wav_path.is_file() or wav_path.stat().st_size == 0:
            raise RuntimeError(f"fluidsynth produced empty audio: {res.stderr}")

        # Detect peak level to normalize quiet or loud MIDIs to standard listening level
        audio_filter = "alimiter=limit=0.95"
        try:
            res_vol = subprocess.run(
                ["ffmpeg", "-nostats", "-i", str(wav_path), "-af", "volumedetect", "-f", "null", "-"],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            max_vol_match = re.search(r"max_volume:\s*(-?[\d.]+)\s*dB", res_vol.stderr)
            if max_vol_match:
                max_vol = float(max_vol_match.group(1))
                target_peak = -1.0
                boost_db = min(30.0, max(-24.0, target_peak - max_vol))
                audio_filter = f"volume={boost_db:.2f}dB,alimiter=limit=0.95"
        except Exception as exc:
            log.warning("volumedetect failed on rendered MIDI: %s", exc)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd_enc = [
            "ffmpeg", "-y",
            "-i", str(wav_path),
            "-af", audio_filter,
            "-c:a", "flac" if output_path.suffix == ".flac" else "libopus",
            str(output_path),
        ]
        subprocess.run(cmd_enc, capture_output=True, text=True, check=True, timeout=120)
    finally:
        if wav_path.exists():
            wav_path.unlink()

    # Pre-generate waveform peaks
    try:
        library.ensure_peaks(output_path)
    except Exception as exc:
        log.warning("peaks generation failed for rendered audio %s: %s", output_path, exc)

    return output_path

