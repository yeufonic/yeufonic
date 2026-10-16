"""Standard MIDI File (SMF) parser and ABC score converter.

Pure-Python implementation with zero external dependencies. Parses SMF format 0 and 1,
extracts duration, tempo, meter, key, markers/sections, and lyrics, and converts
tracks/channels into clean, valid ABC score notation with Vocal and Ins voices.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

# Pitch spelling mappings
PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
SHARP_NAMES = ["C", "^C", "D", "^D", "E", "F", "^F", "G", "^G", "A", "^A", "B"]
FLAT_NAMES = ["C", "_D", "D", "_E", "E", "F", "_G", "G", "_A", "A", "_B", "B"]
CHORD_ROOTS_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
CHORD_ROOTS_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

FLAT_KEYS = {"F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb", "Dm", "Gm", "Cm", "Fm", "Bbm", "Ebm", "Abm"}

MAJOR_KEYS_BY_SF = {
    0: "C", 1: "G", 2: "D", 3: "A", 4: "E", 5: "B", 6: "F#", 7: "C#",
    -1: "F", -2: "Bb", -3: "Eb", -4: "Ab", -5: "Db", -6: "Gb", -7: "Cb",
}
MINOR_KEYS_BY_SF = {
    0: "Am", 1: "Em", 2: "Bm", 3: "F#m", 4: "C#m", 5: "G#m", 6: "D#m", 7: "A#m",
    -1: "Dm", -2: "Gm", -3: "Cm", -4: "Fm", -5: "Bbm", -6: "Ebm", -7: "Abm",
}

# Krumhansl-Schmuckler key profiles for key estimation fallback
MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

CHORD_TEMPLATES = [
    # (name_suffix, intervals_mod_12, required_interval_if_any)
    ("", (0, 4, 7), None),             # Major
    ("m", (0, 3, 7), None),            # Minor
    ("7", (0, 4, 7, 10), 10),          # Dominant 7: must have minor 7th
    ("maj7", (0, 4, 7, 11), 11),       # Major 7: must have major 7th
    ("m7", (0, 3, 7, 10), 10),         # Minor 7: must have minor 7th
    ("dim", (0, 3, 6), 6),             # Diminished: must have diminished 5th
    ("sus4", (0, 5, 7), 5),            # Sus4: must have 4th
]


def _read_vlq(data: bytes, pos: int) -> tuple[int, int]:
    """Read a variable-length quantity from data starting at pos."""
    val = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        val = (val << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    return val, pos


def midi_to_abc_pitch(pitch: int, key: str = "C") -> str:
    """Convert MIDI pitch number (0-127) to ABC note string."""
    is_flat = key in FLAT_KEYS
    names = FLAT_NAMES if is_flat else SHARP_NAMES

    octave = (pitch // 12) - 1
    semitone = pitch % 12
    raw = names[semitone]

    acc = ""
    letter = raw
    if raw.startswith(("^", "_")):
        acc = raw[0]
        letter = raw[1:]

    if octave < 4:
        note_body = letter + ("," * (4 - octave))
    elif octave == 4:
        note_body = letter
    elif octave == 5:
        note_body = letter.lower()
    else:
        note_body = letter.lower() + ("'" * (octave - 5))

    return acc + note_body


class MidiParser:
    """Parses binary Standard MIDI Files into events and notes."""

    def __init__(self, data: bytes):
        self.data = data
        self.division = 480
        self.format = 0
        self.ntrks = 0
        self.tempo_events: list[tuple[int, int]] = []  # (tick, us_per_beat)
        self.time_sigs: list[tuple[int, int, int]] = []  # (tick, num, den)
        self.key_sigs: list[tuple[int, int, int]] = []  # (tick, sf, mi)
        self.markers: list[tuple[int, str]] = []  # (tick, marker_text)
        self.lyrics: list[tuple[int, str]] = []  # (tick, lyric_text)
        self.track_names: dict[int, str] = {}
        self.notes: list[dict[str, Any]] = []
        self._parse()

    def _parse(self) -> None:
        if len(self.data) < 14 or self.data[:4] != b"MThd":
            raise ValueError("Invalid MIDI file: missing MThd header")

        header_len = int.from_bytes(self.data[4:8], "big")
        self.format = int.from_bytes(self.data[8:10], "big")
        self.ntrks = int.from_bytes(self.data[10:12], "big")
        raw_div = int.from_bytes(self.data[12:14], "big")

        if raw_div & 0x8000:
            # SMPTE timecode: frames per sec, ticks per frame
            fps = (-(raw_div >> 8) & 0x7F) or 25
            tpf = raw_div & 0xFF
            self.division = int(fps * tpf * 0.5) or 480
        else:
            self.division = raw_div or 480

        pos = 8 + header_len
        track_idx = 0

        while pos + 8 <= len(self.data):
            chunk_type = self.data[pos:pos + 4]
            chunk_len = int.from_bytes(self.data[pos + 4:pos + 8], "big")
            pos += 8
            chunk_data = self.data[pos:pos + chunk_len]
            pos += chunk_len

            if chunk_type == b"MTrk":
                self._parse_track(track_idx, chunk_data)
                track_idx += 1

    def _parse_track(self, track_idx: int, chunk: bytes) -> None:
        pos = 0
        curr_tick = 0
        running_status = None
        open_notes: dict[tuple[int, int], list[tuple[int, int]]] = {}  # (ch, pitch) -> list of (start_tick, vel)

        while pos < len(chunk):
            delta, pos = _read_vlq(chunk, pos)
            curr_tick += delta
            if pos >= len(chunk):
                break

            b = chunk[pos]
            if b & 0x80:
                status = b
                pos += 1
                if status < 0xF0:
                    running_status = status
                else:
                    running_status = None
            else:
                status = running_status
                if status is None:
                    pos += 1
                    continue

            msg_type = status & 0xF0
            channel = status & 0x0F

            if msg_type == 0x80:  # Note Off
                if pos + 2 > len(chunk):
                    break
                pitch = chunk[pos]
                pos += 2
                key = (channel, pitch)
                if key in open_notes and open_notes[key]:
                    start_tick, vel = open_notes[key].pop(0)
                    dur = max(1, curr_tick - start_tick)
                    self.notes.append({
                        "track": track_idx, "channel": channel, "pitch": pitch,
                        "start_tick": start_tick, "end_tick": curr_tick,
                        "duration_ticks": dur, "velocity": vel,
                    })

            elif msg_type == 0x90:  # Note On
                if pos + 2 > len(chunk):
                    break
                pitch = chunk[pos]
                vel = chunk[pos + 1]
                pos += 2
                key = (channel, pitch)
                if vel == 0:
                    # Note On with velocity 0 is Note Off
                    if key in open_notes and open_notes[key]:
                        start_tick, o_vel = open_notes[key].pop(0)
                        dur = max(1, curr_tick - start_tick)
                        self.notes.append({
                            "track": track_idx, "channel": channel, "pitch": pitch,
                            "start_tick": start_tick, "end_tick": curr_tick,
                            "duration_ticks": dur, "velocity": o_vel,
                        })
                else:
                    open_notes.setdefault(key, []).append((curr_tick, vel))

            elif msg_type in (0xA0, 0xB0, 0xE0):
                pos += 2
            elif msg_type in (0xC0, 0xD0):
                pos += 1
            elif status == 0xFF:  # Meta event
                if pos >= len(chunk):
                    break
                meta_type = chunk[pos]
                pos += 1
                meta_len, pos = _read_vlq(chunk, pos)
                meta_bytes = chunk[pos:pos + meta_len]
                pos += meta_len

                if meta_type == 0x51 and len(meta_bytes) == 3:  # Set Tempo
                    tempo_us = int.from_bytes(meta_bytes, "big")
                    self.tempo_events.append((curr_tick, tempo_us))
                elif meta_type == 0x58 and len(meta_bytes) >= 2:  # Time Signature
                    num = meta_bytes[0]
                    den = 2 ** meta_bytes[1]
                    self.time_sigs.append((curr_tick, num, den))
                elif meta_type == 0x59 and len(meta_bytes) >= 2:  # Key Signature
                    sf = int.from_bytes(meta_bytes[:1], "big", signed=True)
                    mi = meta_bytes[1]
                    self.key_sigs.append((curr_tick, sf, mi))
                elif meta_type == 0x03 and len(meta_bytes) > 0:  # Sequence / Track Name
                    name = meta_bytes.decode("utf-8", errors="replace").strip()
                    if name:
                        self.track_names[track_idx] = name
                elif meta_type == 0x04 and len(meta_bytes) > 0:  # Instrument Name
                    name = meta_bytes.decode("utf-8", errors="replace").strip()
                    if name and track_idx not in self.track_names:
                        self.track_names[track_idx] = name
                elif meta_type == 0x01 and len(meta_bytes) > 0:  # Text Event
                    text = meta_bytes.decode("utf-8", errors="replace").strip()
                    if text:
                        # Many sequencers use text event at tick 0 to name tracks
                        if track_idx not in self.track_names and curr_tick < 100:
                            self.track_names[track_idx] = text
                        else:
                            self.lyrics.append((curr_tick, text))
                elif meta_type == 0x05 and len(meta_bytes) > 0:  # Lyric Event
                    text = meta_bytes.decode("utf-8", errors="replace").strip()
                    if text:
                        self.lyrics.append((curr_tick, text))
                elif meta_type == 0x06:  # Marker
                    marker = meta_bytes.decode("utf-8", errors="replace").strip()
                    if marker:
                        self.markers.append((curr_tick, marker))

            elif status in (0xF0, 0xF7):  # SysEx
                sysex_len, pos = _read_vlq(chunk, pos)
                pos += sysex_len

        # Close any lingering notes
        for (channel, pitch), starts in open_notes.items():
            for start_tick, vel in starts:
                dur = max(1, curr_tick - start_tick)
                self.notes.append({
                    "track": track_idx, "channel": channel, "pitch": pitch,
                    "start_tick": start_tick, "end_tick": curr_tick,
                    "duration_ticks": dur, "velocity": vel,
                })


def detect_bar_phase(parser: MidiParser, num: int, den: int) -> int:
    """How many beats into the file the first real bar line falls, 0 when the file starts on
    a downbeat or the answer is unclear.

    Many sequences start with the melody's first word on the beat before the downbeat (a
    lead-in), and the file has no bar line to say so.  The rhythm section does: a kick lands on
    the downbeat and the third beat, a snare on the second and fourth, and the bass changes
    note at the bar line.  Each beat of the bar is scored by those, and a shift is only
    reported when one beat clearly beats the file's own start."""
    if den != 4 or num not in (3, 4):
        return 0
    scores = [0.0] * num
    division = parser.division
    for n in parser.notes:
        beat = n["start_tick"] / division
        if abs(beat - round(beat)) > 0.1 or n["channel"] != 9:
            continue
        k = int(round(beat)) % num
        if n["pitch"] in (35, 36):
            scores[k] += 1
        elif n["pitch"] in (38, 40, 37) and num == 4:
            scores[(k - 1) % num] += 1
    by_start: dict[int, int] = {}
    for n in parser.notes:
        if n["channel"] != 9 and n["pitch"] < 52:
            by_start[n["start_tick"]] = min(by_start.get(n["start_tick"], 127), n["pitch"])
    last = None
    for tick in sorted(by_start):
        low = by_start[tick]
        beat = tick / division
        if last is not None and low % 12 != last % 12 and abs(beat - round(beat)) <= 0.1:
            scores[int(round(beat)) % num] += 1
        last = low
    best = max(range(num), key=lambda k: scores[k])
    rivals = [scores[k] for k in range(num) if k != best]
    # Kicks and snares repeat every two beats, so a drum pattern alone cannot tell the downbeat
    # from the third beat; it is the bass changing note that settles it.  A tie is not guessed.
    if best == 0 or scores[best] < 20 or scores[best] < 1.3 * scores[0] or scores[best] < 1.15 * max(rivals):
        return 0
    return best


def calculate_duration(parser: MidiParser) -> float:
    """Calculate exact duration in seconds from tempo map and note/track ticks."""
    tempo_map = sorted(parser.tempo_events, key=lambda x: x[0])
    if not tempo_map or tempo_map[0][0] > 0:
        tempo_map.insert(0, (0, 500000))  # Default 120 BPM

    max_tick = 0
    for note in parser.notes:
        if note["end_tick"] > max_tick:
            max_tick = note["end_tick"]

    if max_tick == 0:
        return 0.0

    seconds = 0.0
    div = parser.division

    for i, (t_start, us_beat) in enumerate(tempo_map):
        t_next = tempo_map[i + 1][0] if i + 1 < len(tempo_map) else max_tick
        t_end = min(max_tick, t_next)
        if t_end > t_start:
            dt = t_end - t_start
            seconds += (dt / div) * (us_beat / 1_000_000.0)
        if t_next >= max_tick:
            break

    return round(seconds, 2)


def estimate_key(parser: MidiParser) -> str:
    """Estimate musical key from key signature events or note pitch classes."""
    # Check for explicit non-zero key signature first
    if parser.key_sigs:
        non_zero = [ks for ks in parser.key_sigs if ks[1] != 0 or ks[2] != 0]
        if non_zero:
            sf, mi = non_zero[0][1], non_zero[0][2]
            return MINOR_KEYS_BY_SF.get(sf, "Am") if mi == 1 else MAJOR_KEYS_BY_SF.get(sf, "C")

    # Note pitch correlation using Krumhansl-Schmuckler
    pitch_counts = [0.0] * 12
    for n in parser.notes:
        pitch_counts[n["pitch"] % 12] += n["duration_ticks"]

    total = sum(pitch_counts)
    if total == 0:
        if parser.key_sigs:
            sf, mi = parser.key_sigs[0][1], parser.key_sigs[0][2]
            return MINOR_KEYS_BY_SF.get(sf, "Am") if mi == 1 else MAJOR_KEYS_BY_SF.get(sf, "C")
        return "C"

    best_key = "C"
    best_corr = -999.0

    for root in range(12):
        maj_prof = [MAJOR_PROFILE[(i - root) % 12] for i in range(12)]
        min_prof = [MINOR_PROFILE[(i - root) % 12] for i in range(12)]

        def corr(p1, p2):
            mean1 = sum(p1) / 12.0
            mean2 = sum(p2) / 12.0
            num = sum((a - mean1) * (b - mean2) for a, b in zip(p1, p2))
            den = math.sqrt(sum((a - mean1) ** 2 for a in p1) * sum((b - mean2) ** 2 for b in p2))
            return num / den if den != 0 else 0.0

        c_maj = corr(pitch_counts, maj_prof)
        if c_maj > best_corr:
            best_corr = c_maj
            best_key = PITCH_NAMES[root]

        c_min = corr(pitch_counts, min_prof)
        if c_min > best_corr:
            best_corr = c_min
            best_key = PITCH_NAMES[root] + "m"

    if parser.key_sigs and best_corr < 0.6:
        sf, mi = parser.key_sigs[0][1], parser.key_sigs[0][2]
        return MINOR_KEYS_BY_SF.get(sf, "Am") if mi == 1 else MAJOR_KEYS_BY_SF.get(sf, "C")

    return best_key


def detect_bar_chord(
    events_or_pitches: list[Any],
    arg2: Any = "C",
    arg3: Any = "",
    arg4: Any = None,
    arg5: Any = None,
) -> str:
    """Determine the most fitting chord symbol for a bar given sounding events or pitches."""
    if not events_or_pitches:
        key = arg4 if isinstance(arg2, int) and arg4 is not None else (arg2 if isinstance(arg2, str) else "C")
        last = arg5 if isinstance(arg2, int) and arg5 is not None else (arg3 if isinstance(arg3, str) else "")
        return last or key

    if isinstance(arg2, int) and arg4 is not None:
        # Called as detect_bar_chord(bar_events, b, ticks_per_bar, key, last_chord)
        b = arg2
        ticks_per_bar = arg3
        key = str(arg4)
        last_chord = str(arg5 or "")
    else:
        # Called as detect_bar_chord(pitches_or_events, key, last_chord)
        key = str(arg2 or "C")
        last_chord = str(arg3 or "")
        b = 0
        ticks_per_bar = 16

    # Convert simple pitch list to synthetic event if needed
    if events_or_pitches and isinstance(events_or_pitches[0], int):
        bar_events = [{"start_tick": b * ticks_per_bar, "end_tick": (b + 1) * ticks_per_bar, "pitches": events_or_pitches}]
    else:
        bar_events = events_or_pitches

    pitch_dur = [0.0] * 12
    downbeat_bass = None
    min_bass_pitch = 999
    bass_dur = [0.0] * 12

    b_start = b * ticks_per_bar
    b_end = (b + 1) * ticks_per_bar

    for e in bar_events:
        ts = max(b_start, e["start_tick"])
        te = min(b_end, e["end_tick"])
        dur = max(1, te - ts)
        for p in e["pitches"]:
            pitch_dur[p % 12] += dur
            if p < 60:
                bass_dur[p % 12] += dur
                if p < min_bass_pitch:
                    min_bass_pitch = p
                if ts == b_start and (downbeat_bass is None or p < downbeat_bass[0]):
                    downbeat_bass = (p, p % 12)

    total_dur = sum(pitch_dur)
    if total_dur == 0:
        return last_chord or key

    primary_bass = (
        downbeat_bass[1]
        if downbeat_bass
        else (max(range(12), key=lambda x: bass_dur[x]) if max(bass_dur) > 0 else min(bar_events[0]["pitches"]) % 12)
    )
    pitch_classes = set(i for i in range(12) if pitch_dur[i] > 0)

    names = CHORD_ROOTS_FLAT if key in FLAT_KEYS else CHORD_ROOTS_SHARP

    best_chord = None
    best_score = -999.0

    for root in range(12):
        root_name = names[root]
        for suffix, intervals, req in CHORD_TEMPLATES:
            if req is not None and ((root + req) % 12) not in pitch_classes:
                continue
            target_pcs = set((root + iv) % 12 for iv in intervals)
            chord_dur_ratio = sum(pitch_dur[pc] for pc in target_pcs) / total_dur
            non_chord_ratio = sum(pitch_dur[pc] for pc in (pitch_classes - target_pcs)) / total_dur

            score = (chord_dur_ratio * 4.0 - non_chord_ratio * 1.5)
            if root in pitch_classes:
                score += 1.0
            if root == primary_bass:
                score += 3.5  # Strong bass alignment
            if suffix in ("", "m"):
                score += 0.8  # Prefer standard triads
            elif suffix == "sus4":
                score -= 1.2  # Sus4 penalty unless explicitly dominant
            elif suffix in ("7", "m7", "maj7"):
                score += 0.3

            if score > best_score:
                best_score = score
                best_chord = root_name + suffix

    if best_chord and best_score >= 1.5:
        return best_chord
    return last_chord or key


def midi_to_abc(
    data: bytes,
    title: str = "",
    vocal_track: int | None = None,
    ins_track: int | None = None,
) -> str:
    """Convert MIDI binary data into an ABC score with Vocal and Ins staves."""
    return parse_midi(data, title=title, vocal_track=vocal_track, ins_track=ins_track)["abc"]


def midi_duration(data: bytes) -> float:
    """Return total playback duration in seconds of a MIDI file."""
    parser = MidiParser(data)
    return calculate_duration(parser)


def extract_midi_tracks(data: bytes) -> list[dict[str, Any]]:
    """Inspect and return metadata for all tracks in a MIDI file."""
    parser = MidiParser(data)
    dur = calculate_duration(parser)
    _, _, tracks = classify_midi_tracks(parser, dur)
    return tracks


def classify_midi_tracks(
    parser: MidiParser,
    total_duration_sec: float,
    vocal_track: int | None = None,
    ins_track: int | None = None,
) -> tuple[set[int], set[int], list[dict[str, Any]]]:
    """Score and classify all MIDI tracks to detect vocal melody and accompaniment.

    Uses monophonicity, pitch range, singing note density, stepwise interval motion,
    and semantic name priors.
    """
    melodic_notes = [n for n in parser.notes if n["channel"] != 9]
    if not melodic_notes:
        melodic_notes = parser.notes

    all_tracks = sorted(set(n["track"] for n in parser.notes))
    track_info: list[dict[str, Any]] = []

    VOCAL_STRONG = ("vocal", "vox", "melody", "lead vox", "voice", "sing")
    VOCAL_MOD = ("lead", "solo", "sax", "flute", "oboe", "clarinet", "harmonica", "synth")
    ACCOMP_EXCL = (
        "bass", "fretless", "bas", "drum", "perc", "click", "rhythm", "rythm",
        "strum", "chord", "chords", "hihat", "cymbal", "snare", "kick",
    )

    scores_by_track: dict[int, float] = {}
    strong_vocal_tracks: set[int] = set()

    for t in all_tracks:
        t_notes = [n for n in parser.notes if n["track"] == t]
        name = parser.track_names.get(t, "")
        name_lower = name.lower()
        n_count = len(t_notes)
        is_drum_channel = any(n["channel"] == 9 for n in t_notes)

        if not t_notes or is_drum_channel or any(k in name_lower for k in ("drum", "perc", "click", "cymbal")):
            track_info.append({
                "track": t,
                "name": name,
                "note_count": n_count,
                "mono_ratio": 0.0,
                "avg_pitch": 0.0,
                "vocal_score": 0.0,
                "role": "drums",
            })
            continue

        sorted_t = sorted(t_notes, key=lambda x: x["start_tick"])
        overlaps = sum(1 for i in range(len(sorted_t) - 1) if sorted_t[i]["end_tick"] > sorted_t[i + 1]["start_tick"])
        mono_ratio = 1.0 - (overlaps / max(1, len(sorted_t) - 1))

        pitches = [n["pitch"] for n in t_notes]
        avg_p = sum(pitches) / n_count
        in_range = sum(1 for p in pitches if 48 <= p <= 84) / n_count
        pitch_penalty = max(0.0, 1.0 - abs(avg_p - 63) / 24.0)

        rate = n_count / max(1.0, total_duration_sec)
        if rate < 0.4:
            rate_score = max(0.1, rate / 0.4)
        elif rate > 5.5:
            rate_score = max(0.01, 1.0 - (rate - 5.5) / 10.0)
        else:
            rate_score = 1.0

        if n_count > 1800:
            count_penalty = max(0.05, 1.0 - (n_count - 1800) / 2000.0)
        elif n_count < 60:
            count_penalty = n_count / 60.0
        else:
            count_penalty = 1.0

        intervals = [abs(sorted_t[i + 1]["pitch"] - sorted_t[i]["pitch"]) for i in range(min(100, len(sorted_t) - 1))]
        stepwise_ratio = sum(1 for iv in intervals if iv <= 4) / max(1, len(intervals)) if intervals else 0.5

        name_factor = 1.0
        is_strong_vocal = any(k in name_lower for k in VOCAL_STRONG)
        if is_strong_vocal:
            name_factor = 3.0
            strong_vocal_tracks.add(t)
        elif any(k in name_lower for k in VOCAL_MOD):
            name_factor = 1.3
        if any(k in name_lower for k in ACCOMP_EXCL):
            name_factor = 0.02
        if any(k in name_lower for k in ("string", "slowstring", "pad")):
            name_factor = 0.4

        score = (
            100.0
            * (mono_ratio ** 4)
            * (in_range ** 2)
            * pitch_penalty
            * rate_score
            * count_penalty
            * (0.5 + 0.5 * stepwise_ratio)
            * name_factor
        )

        if avg_p < 44 or any(k in name_lower for k in ("bass", "fretless", "bas")):
            role = "bass"
        elif score >= 20.0 or is_strong_vocal:
            role = "vocal"
        elif mono_ratio < 0.60 or any(k in name_lower for k in ("chord", "strum", "rhythm", "rythm", "piano", "gtr", "guitar")):
            role = "accompaniment"
        else:
            role = "lead"

        scores_by_track[t] = score
        track_info.append({
            "track": t,
            "name": name,
            "note_count": n_count,
            "mono_ratio": round(mono_ratio, 2),
            "avg_pitch": round(avg_p, 1),
            "vocal_score": round(score, 2),
            "role": role,
        })

    vocal_tracks: set[int] = set()
    accomp_tracks: set[int] = set()

    if vocal_track is not None:
        vocal_tracks = {vocal_track}
        if ins_track is not None:
            accomp_tracks = {ins_track}
        else:
            accomp_tracks = set(t for t in scores_by_track if t != vocal_track)
    else:
        if strong_vocal_tracks:
            vocal_tracks = strong_vocal_tracks
        elif scores_by_track:
            best_t = max(scores_by_track.keys(), key=lambda k: scores_by_track[k])
            if scores_by_track[best_t] > 0.5:
                vocal_tracks.add(best_t)

        if ins_track is not None:
            accomp_tracks = {ins_track}
        else:
            accomp_tracks = set(t for t in scores_by_track if t not in vocal_tracks)

    return vocal_tracks, accomp_tracks, track_info


def parse_midi(
    data: bytes,
    title: str = "",
    vocal_track: int | None = None,
    ins_track: int | None = None,
    octave_shift: int | None = None,
    bar_offset: int | None = None,
) -> dict[str, Any]:
    """Parse MIDI data into ABC score, duration, tempo, meter, key, and lyrics."""
    parser = MidiParser(data)
    duration_sec = calculate_duration(parser)

    # Meter
    if parser.time_sigs:
        num, den = parser.time_sigs[0][1], parser.time_sigs[0][2]
    else:
        num, den = 4, 4
    meter_str = f"{num}/{den}"

    # Tempo (BPM)
    if parser.tempo_events:
        us_per_beat = parser.tempo_events[0][1]
        bpm = round(60_000_000 / us_per_beat)
    else:
        bpm = 120

    # Key
    key = estimate_key(parser)

    # Clean Title
    if not title:
        for t_idx, name in parser.track_names.items():
            if name and not any(kw in name.lower() for kw in ("vocal", "piano", "guitar", "bass", "drum")):
                title = name
                break
    title = title or "Imported MIDI"

    # Quantization settings: grid is L: 1/16
    ticks_per_quarter = parser.division
    ticks_per_16th = ticks_per_quarter / 4.0
    ticks_per_bar = num * (16 // den) if den in (1, 2, 4, 8, 16) else 16

    # A lead-in: when the first real bar line falls `phase` beats into the file, the music is
    # moved later by the rest of that bar, so "Hey" is the last beat of a bar of its own and
    # "Jude" lands on the downbeat.  `bar_offset` overrides the detection (0 turns it off).
    phase = detect_bar_phase(parser, num, den) if bar_offset is None else max(0, int(bar_offset))
    lead_in = ((num - phase) % num) * (16 // den) if phase and den == 4 else 0

    # Filter melodic notes (skip channel 9 General MIDI percussion)
    melodic_notes = [n for n in parser.notes if n["channel"] != 9]
    if not melodic_notes:
        melodic_notes = parser.notes  # Fall back if only drum channel exists

    vocal_tracks, accomp_tracks, track_info = classify_midi_tracks(
        parser, duration_sec, vocal_track=vocal_track, ins_track=ins_track
    )

    if vocal_tracks:
        vocal_source = [dict(n) for n in melodic_notes if n["track"] in vocal_tracks]
        if accomp_tracks:
            ins_source = [dict(n) for n in melodic_notes if n["track"] in accomp_tracks]
        else:
            ins_source = [dict(n) for n in melodic_notes if n["track"] not in vocal_tracks]
    else:
        # Single track: split polyphony
        by_start: dict[int, list[dict[str, Any]]] = {}
        for n in melodic_notes:
            by_start.setdefault(n["start_tick"], []).append(dict(n))
        vocal_source = []
        ins_source = []
        for start_t in sorted(by_start.keys()):
            group = sorted(by_start[start_t], key=lambda x: x["pitch"], reverse=True)
            vocal_source.append(group[0])
            for lower_note in group[1:]:
                ins_source.append(lower_note)

    # Intelligent vocal register normalization:
    # Standard lead pop singing register is centered around C4-D5 (MIDI 65-76).
    # When sequenced an octave lower (e.g. synth or guitar lead in low 50s/60s),
    # average pitch is < 65 and max <= 78.
    applied_octave_shift = 0
    if vocal_source:
        vp = [n["pitch"] for n in vocal_source]
        avg_vocal_pitch = sum(vp) / len(vp)
        max_vocal_pitch = max(vp)
        min_vocal_pitch = min(vp)

        if octave_shift is not None:
            applied_octave_shift = octave_shift
        else:
            if avg_vocal_pitch < 64 and min_vocal_pitch < 58 and max_vocal_pitch <= 78:
                applied_octave_shift = 1
            elif avg_vocal_pitch > 80 and min_vocal_pitch >= 65:
                applied_octave_shift = -1
            else:
                applied_octave_shift = 0

        if applied_octave_shift != 0:
            shift_semitones = applied_octave_shift * 12
            for n in vocal_source:
                n["pitch"] = max(12, min(108, n["pitch"] + shift_semitones))

    # Reduction helpers
    def make_monophonic(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not notes:
            return []
        sorted_notes = sorted(notes, key=lambda x: (x["start_tick"], -x["pitch"]))
        mono: list[dict[str, Any]] = []
        for n in sorted_notes:
            if not mono:
                mono.append({"start_tick": n["start_tick"], "end_tick": n["end_tick"], "pitches": [n["pitch"]]})
                continue
            prev = mono[-1]
            if n["start_tick"] == prev["start_tick"]:
                continue
            if n["start_tick"] < prev["end_tick"]:
                prev["end_tick"] = n["start_tick"]
            mono.append({"start_tick": n["start_tick"], "end_tick": n["end_tick"], "pitches": [n["pitch"]]})
        return mono

    def reduce_polyphony(notes: list[dict[str, Any]], max_polyphony: int = 3) -> list[dict[str, Any]]:
        if not notes:
            return []
        by_start: dict[int, list[dict[str, Any]]] = {}
        for n in sorted(notes, key=lambda x: (x["start_tick"], x["pitch"])):
            by_start.setdefault(n["start_tick"], []).append(n)
        start_ticks = sorted(by_start.keys())
        events: list[dict[str, Any]] = []
        for i, t in enumerate(start_ticks):
            group = by_start[t]
            pitches = sorted(set(n["pitch"] for n in group))
            if len(pitches) > max_polyphony:
                pitches = [pitches[0]] + pitches[-(max_polyphony - 1):]
            min_dur = min(n["duration_ticks"] for n in group)
            if i + 1 < len(start_ticks):
                max_allowed = start_ticks[i + 1] - t
                dur = min(min_dur, max_allowed)
            else:
                dur = min_dur
            dur = max(1, dur)
            events.append({"start_tick": t, "end_tick": t + dur, "pitches": pitches})
        return events

    vocal_events = make_monophonic(vocal_source)
    ins_events = reduce_polyphony(ins_source, max_polyphony=3)

    def quantize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        q = []
        for e in events:
            qs = round(e["start_tick"] / ticks_per_16th) + lead_in
            qe = max(qs + 1, round(e["end_tick"] / ticks_per_16th) + lead_in)
            q.append({"start_tick": qs, "end_tick": qe, "pitches": e["pitches"]})
        return q

    qv = quantize_events(vocal_events)
    qi = quantize_events(ins_events)

    def clean_vocal_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not events:
            return []
        cleaned: list[dict[str, Any]] = []
        for e in events:
            if not cleaned:
                cleaned.append(dict(e))
                continue
            prev = cleaned[-1]
            if e["start_tick"] == prev["start_tick"]:
                if max(e["pitches"]) > max(prev["pitches"]):
                    cleaned[-1] = dict(e)
                continue
            if prev["end_tick"] > e["start_tick"]:
                prev["end_tick"] = e["start_tick"]
            elif e["start_tick"] - prev["end_tick"] <= 1:
                prev["end_tick"] = e["start_tick"]
            cleaned.append(dict(e))
        return cleaned

    qv = clean_vocal_events(qv)

    # Ensure accompaniment does not have overlapping events from quantization rounding
    for i in range(len(qi) - 1):
        if qi[i]["end_tick"] > qi[i + 1]["start_tick"]:
            qi[i]["end_tick"] = max(qi[i]["start_tick"] + 1, qi[i + 1]["start_tick"])

    max_tick = 0
    for e in qv + qi:
        if e["end_tick"] > max_tick:
            max_tick = e["end_tick"]

    total_bars = max(4, math.ceil(max_tick / ticks_per_bar)) if ticks_per_bar > 0 else 4

    bar_chords: list[str] = []
    last_chord = key
    for b in range(total_bars):
        b_start = b * ticks_per_bar
        b_end = (b + 1) * ticks_per_bar
        bar_events = [
            e for e in qv + qi
            if e["end_tick"] > b_start and e["start_tick"] < b_end
        ]
        ch = detect_bar_chord(bar_events, b, ticks_per_bar, key, last_chord)
        bar_chords.append(ch)
        last_chord = ch

    # Generate sections (intro, verse, chorus, outro)
    sections: list[tuple[int, str]] = []
    if parser.markers:
        for m_tick, m_text in parser.markers:
            q_tick = round(m_tick / ticks_per_16th) + lead_in
            b_idx = min(total_bars - 1, q_tick // ticks_per_bar)
            name = m_text.strip().lower()
            if any(s in name for s in ("intro", "verse", "chorus", "bridge", "outro")):
                clean_sec = next(s for s in ("intro", "verse", "chorus", "bridge", "outro") if s in name)
                sections.append((b_idx, clean_sec))

    first_vocal_bar = (min((e["start_tick"] for e in qv), default=0) // ticks_per_bar) if qv else 0

    if not sections:
        outro_threshold = max(total_bars - 8, total_bars - 4) if total_bars > 16 else total_bars
        sec_bars = [first_vocal_bar]
        last_b = first_vocal_bar

        for i in range(len(qv) - 1):
            e1 = qv[i]["end_tick"]
            s2 = qv[i + 1]["start_tick"]
            gap = s2 - e1
            b_next = s2 // ticks_per_bar
            # Break into musical section if vocal rests for >= 6 sixteenths (1.5 beats) or after 16 bars
            if (gap >= 6 or (b_next - last_b) >= 16) and (b_next - last_b) >= 6 and b_next < outro_threshold:
                sec_bars.append(b_next)
                last_b = b_next

        # Musical section naming:
        # Alternating verse / chorus / bridge based on section position and harmonic progression
        vocal_sec_names = []
        v1_chords = None
        for s_i, sb in enumerate(sec_bars):
            eb = sec_bars[s_i + 1] if s_i + 1 < len(sec_bars) else total_bars
            chords_in_sec = set(bar_chords[sb:eb])
            if s_i == 0:
                vocal_sec_names.append("verse")
                v1_chords = chords_in_sec
            elif s_i == 1:
                # If section 2 has very similar chords to section 1, it's verse 2
                overlap = len(v1_chords.intersection(chords_in_sec)) / max(1, len(v1_chords.union(chords_in_sec))) if v1_chords else 1.0
                if overlap >= 0.4:
                    vocal_sec_names.append("verse")
                else:
                    vocal_sec_names.append("chorus")
            elif s_i == 2:
                if vocal_sec_names[-1] == "verse":
                    vocal_sec_names.append("chorus")
                else:
                    vocal_sec_names.append("verse")
            elif s_i == 3:
                if vocal_sec_names[-1] == "chorus":
                    vocal_sec_names.append("verse")
                else:
                    vocal_sec_names.append("chorus")
            elif s_i == 4:
                vocal_sec_names.append("bridge")
            elif s_i == 5:
                vocal_sec_names.append("verse")
            else:
                vocal_sec_names.append("chorus" if s_i % 2 == 0 else "outro")

        if first_vocal_bar > 0:
            sections = [(0, "intro")]
        else:
            sections = []

        for sb, sname in zip(sec_bars, vocal_sec_names):
            sections.append((sb, sname))

        if total_bars > 24 and total_bars - 4 > last_b:
            sections.append((total_bars - 4, "outro"))
    else:
        if sections[0][0] > 0:
            if 0 < first_vocal_bar < sections[0][0]:
                sections.insert(0, (first_vocal_bar, "verse"))
                sections.insert(0, (0, "intro"))
            else:
                sections.insert(0, (0, "intro" if first_vocal_bar > 0 else "verse"))

    sections = sorted(dict(sections).items(), key=lambda x: x[0])

    lines: list[str] = [
        "X:1",
        f"T:{title}",
        f"M:{meter_str}",
        "L:1/16",
        f"Q:1/4={bpm}",
        'V: Vocal clef=treble name="Vocal Melody" snm="Vocal"',
        'V: Ins clef=treble name="Ins Melody" snm="Inst."',
        f"K:{key}",
    ]

    def render_bar(events: list[dict[str, Any]], b_idx: int, chord_name: str | None) -> str:
        b_start = b_idx * ticks_per_bar
        b_end = (b_idx + 1) * ticks_per_bar
        segs = []
        for e in events:
            if e["end_tick"] <= b_start or e["start_tick"] >= b_end:
                continue
            ts = max(b_start, e["start_tick"]) - b_start
            te = min(b_end, e["end_tick"]) - b_start
            tied = e["end_tick"] > b_end
            segs.append({"start": ts, "dur": te - ts, "pitches": e["pitches"], "tied": tied})

        if not segs:
            prefix = f'"{chord_name}"' if chord_name else ""
            return f"{prefix}z{ticks_per_bar}"

        cur_t = 0
        tokens = []
        for idx, s in enumerate(segs):
            if s["start"] > cur_t:
                gap = s["start"] - cur_t
                prefix = f'"{chord_name}"' if (chord_name and idx == 0 and cur_t == 0) else ""
                gap_str = str(gap) if gap > 1 else ""
                tokens.append(f"{prefix}z{gap_str}")
                cur_t = s["start"]

            prefix = f'"{chord_name}"' if (chord_name and idx == 0 and cur_t == 0) else ""
            if len(s["pitches"]) == 1:
                n_str = midi_to_abc_pitch(s["pitches"][0], key)
            else:
                n_str = "[" + "".join(midi_to_abc_pitch(p, key) for p in s["pitches"]) + "]"
            dur = s["dur"]
            dur_str = str(dur) if dur > 1 else ""
            tie_str = "-" if s["tied"] else ""
            tokens.append(f"{prefix}{n_str}{dur_str}{tie_str}")
            cur_t += dur

        if cur_t < ticks_per_bar:
            gap = ticks_per_bar - cur_t
            gap_str = str(gap) if gap > 1 else ""
            tokens.append(f"z{gap_str}")

        return "".join(tokens)

    for s_idx, (s_bar, s_name) in enumerate(sections):
        next_s_bar = sections[s_idx + 1][0] if s_idx + 1 < len(sections) else total_bars
        end_bar = min(total_bars, next_s_bar)
        if s_bar >= end_bar:
            continue

        lines.append(f"% {s_name}")

        for voice in ("Vocal", "Ins"):
            lines.append(f"V: {voice}")
            bar_strs = []
            evs = qv if voice == "Vocal" else qi
            for b in range(s_bar, end_bar):
                chord_to_emit = bar_chords[b] if voice == "Vocal" else None
                bar_str = render_bar(evs, b, chord_to_emit)
                bar_strs.append(bar_str)

            for chunk_start in range(0, len(bar_strs), 4):
                chunk = bar_strs[chunk_start:chunk_start + 4]
                lines.append("|".join(chunk) + "|")

    abc_text = "\n".join(lines) + "\n"

    # Extract lyrics if present
    extracted_lyrics = None
    if parser.lyrics:
        valid_lyrics = [
            (t, txt) for t, txt in parser.lyrics
            if not any(noise in txt.lower() for noise in (
                "sequenced", "bbs", "http", "www.", "copyright", "roland",
                "all rights", "email", "e-mail", "sound canvas", "general midi",
            ))
        ]
        if len(valid_lyrics) >= 5 or (valid_lyrics and any(t > 0 for t, _ in valid_lyrics)):
            words = [txt for _, txt in sorted(valid_lyrics, key=lambda x: x[0])]
            raw_text = " ".join(words)
            # Clean up syllable hyphens if any
            raw_text = raw_text.replace(" - ", " ").replace(" -", "").strip()
            if raw_text:
                extracted_lyrics = raw_text

    if extracted_lyrics:
        from . import aligner
        abc_text = aligner.align_lyrics_to_abc(abc_text, extracted_lyrics)

    min_score_dur = round(total_bars * (num * (4.0 / den)) * (60.0 / bpm), 2)
    if duration_sec < min_score_dur and total_bars == 4:
        duration_sec = min_score_dur

    return {
        "duration": duration_sec,
        "abc": abc_text,
        "tempo": bpm,
        "key": key,
        "meter": meter_str,
        "title": title,
        "lyrics": extracted_lyrics,
        "sections": [s_name for _, s_name in sections],
        "tracks": track_info,
        "octave_shift": applied_octave_shift,
        "bar_offset": phase,
    }

