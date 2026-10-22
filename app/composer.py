"""Symbolic and neural thematic composer for expanding melody motifs into full songs.

Enables home-produced 'Hum-to-Song' thematic continuation: takes a short hummed,
sung, or played motif (e.g. 4 to 8 bars) and musically develops it into a complete,
multi-section song (Intro, Verses, Pre-Chorus, Chorus, Bridge, Outro) with
diatonic voice leading, register management, and coherent harmonic palettes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from . import music, score

# Musical Scale step definitions (semitones from tonic)
MAJOR_STEPS = [0, 2, 4, 5, 7, 9, 11]
NATURAL_MINOR_STEPS = [0, 2, 3, 5, 7, 8, 10]

# Standard harmonic chord palettes (Roman numerals mapped per section)
PALETTES: dict[str, dict[str, list[str]]] = {
    "pop": {
        "intro": ["I", "V", "vi", "IV"],
        "verse": ["vi", "IV", "I", "V"],
        "prechorus": ["ii", "IV", "vi", "V"],
        "chorus": ["I", "V", "vi", "IV"],
        "bridge": ["IV", "I", "V", "vi"],
        "outro": ["I", "V", "IV", "I"],
    },
    "ballad": {
        "intro": ["vi", "IV", "I", "V"],
        "verse": ["I", "vi", "IV", "V"],
        "prechorus": ["IV", "V", "vi", "V"],
        "chorus": ["vi", "IV", "I", "V"],
        "bridge": ["ii", "vi", "IV", "V"],
        "outro": ["IV", "V", "I", "I"],
    },
    "uplifting": {
        "intro": ["I", "IV", "vi", "V"],
        "verse": ["I", "V", "vi", "IV"],
        "prechorus": ["IV", "V", "IV", "V"],
        "chorus": ["I", "IV", "vi", "V"],
        "bridge": ["vi", "V", "IV", "V"],
        "outro": ["I", "IV", "I", "I"],
    },
    "rock": {
        "intro": ["I", "IV", "V", "IV"],
        "verse": ["I", "I", "IV", "I"],
        "prechorus": ["ii", "IV", "V", "V"],
        "chorus": ["I", "IV", "V", "IV"],
        "bridge": ["IV", "IV", "I", "V"],
        "outro": ["IV", "V", "I", "I"],
    },
    "rnb": {
        "intro": ["ii", "V", "I", "vi"],
        "verse": ["ii", "V", "I", "vi"],
        "prechorus": ["IV", "iii", "ii", "V"],
        "chorus": ["ii", "V", "I", "vi"],
        "bridge": ["IV", "V", "iii", "vi"],
        "outro": ["ii", "V", "I", "I"],
    },
}

# Song structure presets
PRESETS: dict[str, list[str]] = {
    "standard": [
        "Intro",
        "Verse 1",
        "Pre-Chorus",
        "Chorus",
        "Verse 2",
        "Pre-Chorus",
        "Chorus",
        "Bridge",
        "Chorus",
        "Outro",
    ],
    "short": [
        "Verse 1",
        "Chorus",
        "Verse 2",
        "Chorus",
        "Outro",
    ],
    "aaba": [
        "Verse 1",
        "Verse 2",
        "Bridge",
        "Verse 3",
        "Outro",
    ],
}

# Regex for tokenizing an ABC bar into notes, chords, rests, and spacing
TOKEN_RE = re.compile(
    r'(?P<chord>"[^"]*")|'
    r'(?P<grace>\{[^}]+\})|'
    r'(?P<rest>[zZ]\d*(?:/\d*)*)|'
    r'(?P<note>(?P<acc>[_^=]*)(?P<letter>[A-Ga-g])(?P<oct>[,\']*)(?P<dur>\d*(?:/\d*)*))|'
    r'(?P<other>\s+|[|\-\(\)\\\/])'
)


@dataclass
class MotifAnalysis:
    key_root: str = "C"
    mode: str = "major"
    bpm: int = 120
    meter: tuple[int, int] = (4, 4)
    unit_length: str = "1/8"
    bars: list[str] = field(default_factory=list)
    raw_header: list[str] = field(default_factory=list)
    pitches: list[int] = field(default_factory=list)
    scale_pcs: set[int] = field(default_factory=set)
    root_pc: int = 0
    tonic_midi: int = 60
    pitch_min: int = 60
    pitch_max: int = 72


def parse_key_header(key_str: str) -> tuple[str, str, int]:
    """Parse K: line (e.g. 'C', 'Am', 'F#m', 'Bb', 'G maj').

    Returns (root_name, mode, root_pitch_class).
    """
    clean = key_str.strip()
    match = re.match(r"^([A-G][#b]?)\s*(m(?:in(?:or)?)?|maj(?:or)?)?", clean, re.I)
    if not match:
        return "C", "major", 0
    root = match.group(1).capitalize()
    mode_raw = (match.group(2) or "").lower()
    mode = "minor" if mode_raw.startswith("m") and not mode_raw.startswith("maj") else "major"
    # Root pitch class
    base_pc = music.PITCH_CLASS[root[0]]
    if len(root) > 1:
        if root[1] == "#":
            base_pc = (base_pc + 1) % 12
        elif root[1] == "b":
            base_pc = (base_pc - 1) % 12
    return root, mode, base_pc


def analyze_motif(abc: str) -> MotifAnalysis:
    """Analyze an input ABC motif to extract key, tempo, meter, notes, and bars."""
    analysis = MotifAnalysis()
    headers: list[str] = []
    lines = (abc or "").splitlines()
    in_header = True

    for line in lines:
        stripped = line.strip()
        if in_header:
            if stripped.startswith("K:"):
                analysis.key_root, analysis.mode, analysis.root_pc = parse_key_header(stripped[2:])
                headers.append(stripped)
                in_header = False
                continue
            if stripped.startswith("M:"):
                m_match = re.search(r"(\d+)/(\d+)", stripped)
                if m_match:
                    analysis.meter = (int(m_match.group(1)), int(m_match.group(2)))
            elif stripped.startswith("L:"):
                l_match = re.search(r"(\d+/\d+)", stripped)
                if l_match:
                    analysis.unit_length = l_match.group(1)
            elif stripped.startswith("Q:"):
                q_match = re.search(r"1/4=(\d+)", stripped)
                if q_match:
                    analysis.bpm = int(q_match.group(1))
            if stripped and not stripped.startswith("%") and score.HEADER.match(stripped):
                headers.append(stripped)
        elif stripped and score.HEADER.match(stripped) and not stripped.startswith("V:"):
            # Header inside body
            headers.append(stripped)

    analysis.raw_header = headers

    # Scale pitch classes
    steps = NATURAL_MINOR_STEPS if analysis.mode == "minor" else MAJOR_STEPS
    analysis.scale_pcs = {(analysis.root_pc + s) % 12 for s in steps}

    # Extract vocal bars
    bars = score.vocal_bars(abc)
    # If no voice header was present, parse bars from non-header lines
    if not bars:
        for line in lines:
            s = line.strip()
            if not s or s.startswith("%") or score.HEADER.match(s) or s.startswith("V:"):
                continue
            for b in s.split("|"):
                if b.strip() and not score.BARLINE_ONLY.fullmatch(b):
                    bars.append(b.strip())

    analysis.bars = bars

    # Extract all note pitches
    pitches: list[int] = []
    for bar in bars:
        for m in TOKEN_RE.finditer(bar):
            if m.group("note"):
                letter = m.group("letter")
                oct_marks = m.group("oct") or ""
                acc_marks = m.group("acc") or ""
                octave = music.abc_note_octave(letter, oct_marks)
                acc = music.ACCIDENTAL_DELTA.get(acc_marks, 0)
                midi = music.abc_to_midi(letter, octave, acc)
                pitches.append(midi)

    if pitches:
        analysis.pitches = pitches
        analysis.pitch_min = min(pitches)
        analysis.pitch_max = max(pitches)
        # Find tonic near pitch center
        center = sum(pitches) // len(pitches)
        # Find nearest octave of tonic
        candidates = [analysis.root_pc + 12 * oct_idx for oct_idx in range(2, 8)]
        analysis.tonic_midi = min(candidates, key=lambda c: abs(c - center))
    else:
        analysis.tonic_midi = 60 + analysis.root_pc

    return analysis


def snap_to_scale(midi_pitch: int, scale_pcs: set[int]) -> int:
    """Snap a MIDI pitch to the nearest diatonic scale pitch class."""
    pc = midi_pitch % 12
    if pc in scale_pcs:
        return midi_pitch
    # Test +1, -1, +2, -2
    for delta in (1, -1, 2, -2):
        if (pc + delta) % 12 in scale_pcs:
            return midi_pitch + delta
    return midi_pitch


def midi_to_abc_token(midi_pitch: int, duration_str: str, use_flats: bool = False) -> str:
    """Format a MIDI pitch number and duration into valid ABC note token."""
    pc = midi_pitch % 12
    octave = (midi_pitch // 12) - 1

    names = music.STANDARD_FLAT_NAMES if use_flats else music.STANDARD_SHARP_NAMES
    note_name = names[pc]

    # Handle accidentals
    accidental = ""
    if "#" in note_name:
        accidental = "^"
        base_letter = note_name[0]
    elif "b" in note_name:
        accidental = "_"
        base_letter = note_name[0]
    else:
        base_letter = note_name

    spelling = music.midi_to_abc_spelling(base_letter, octave)
    return f"{accidental}{spelling}{duration_str}"


def roman_to_chord(numeral: str, root_pc: int, mode: str = "major", use_flats: bool = False) -> str:
    """Convert a Roman numeral (e.g. 'I', 'V', 'vi', 'ii') to a chord symbol in key."""
    num_clean = numeral.strip()
    is_lower = num_clean.islower()
    num_upper = num_clean.upper()

    # Major key degree semitones: I:0, ii:2, iii:4, IV:5, V:7, vi:9, vii:11
    # Minor key degree semitones: i:0, ii:2, III:3, iv:5, v:7, VI:8, VII:10
    degree_semitones_maj = {"I": 0, "II": 2, "III": 4, "IV": 5, "V": 7, "VI": 9, "VII": 11}
    degree_semitones_min = {"I": 0, "II": 2, "III": 3, "IV": 5, "V": 7, "VI": 8, "VII": 10}

    table = degree_semitones_min if mode == "minor" else degree_semitones_maj
    offset = table.get(num_upper, 0)
    chord_pc = (root_pc + offset) % 12

    names = music.STANDARD_FLAT_NAMES if use_flats else music.STANDARD_SHARP_NAMES
    root_name = names[chord_pc]

    # Chord quality
    quality = "m" if is_lower else ""
    return f"{root_name}{quality}"


def transform_bar_notes(
    bar: str,
    analysis: MotifAnalysis,
    semitone_shift: int = 0,
    invert: bool = False,
    pivot_midi: int = 60,
    smooth_leaps: bool = False,
    use_flats: bool = False,
) -> str:
    """Transform the musical notes in an ABC bar while preserving rhythm and structure."""
    parts: list[str] = []
    last_midi: int | None = None

    for m in TOKEN_RE.finditer(bar):
        if m.group("chord"):
            # Chords will be replaced by section harmony
            continue
        elif m.group("note"):
            letter = m.group("letter")
            oct_marks = m.group("oct") or ""
            acc_marks = m.group("acc") or ""
            dur = m.group("dur") or ""
            octave = music.abc_note_octave(letter, oct_marks)
            acc = music.ACCIDENTAL_DELTA.get(acc_marks, 0)
            orig_midi = music.abc_to_midi(letter, octave, acc)

            # Transformation
            new_midi = orig_midi
            if invert:
                new_midi = 2 * pivot_midi - orig_midi
            new_midi += semitone_shift

            # Snap to key scale
            new_midi = snap_to_scale(new_midi, analysis.scale_pcs)

            # Stepwise smoothing for verses
            if smooth_leaps and last_midi is not None:
                diff = new_midi - last_midi
                if abs(diff) > 4:
                    direction = 1 if diff > 0 else -1
                    new_midi = last_midi + direction * 2
                    new_midi = snap_to_scale(new_midi, analysis.scale_pcs)

            last_midi = new_midi
            parts.append(midi_to_abc_token(new_midi, dur, use_flats=use_flats))
        elif m.group("rest"):
            parts.append(m.group("rest"))
        elif m.group("grace"):
            parts.append(m.group("grace"))
        elif m.group("other"):
            parts.append(m.group("other"))

    return "".join(parts).strip()


def expand_motif_to_song(
    abc: str,
    structure: list[str] | None = None,
    palette_name: str = "pop",
    role: str = "chorus",
) -> str:
    """Expand a short ABC motif into a complete, balanced multi-section song.

    Applies musical theory transformations:
    - Chorus: exact pristine hook motif fully harmonized
    - Verse: register lowered by 4th/octave, smoothed intervals, verse progression
    - Pre-Chorus: ascending sequence building anticipation into dominant
    - Bridge: melodic inversion around tonic into relative minor
    - Intro: instrumental motif fragment with tonic pedal
    - Outro: cadential resolution tag

    Returns complete, valid ABC score text.
    """
    analysis = analyze_motif(abc)
    use_flats = "b" in analysis.key_root or analysis.key_root in ("F", "Bb", "Eb", "Ab", "Db", "Gb", "Dm", "Gm", "Cm", "Fm")
    palette = PALETTES.get(palette_name, PALETTES["pop"])
    sections = structure or PRESETS["standard"]

    # Ensure we have at least 1 usable bar
    motif_bars = [b for b in analysis.bars if b.strip()]
    if not motif_bars:
        # Fallback default motif if empty
        motif_bars = ['"C"c4 d4 | "G"e4 d4 | "Am"c4 A4 | "F"G8 |']
        analysis.bars = motif_bars

    num_motif_bars = len(motif_bars)
    pivot = analysis.tonic_midi

    # Generate section blocks
    output_sections: list[str] = []

    for sec_idx, section_name in enumerate(sections):
        sec_key = section_name.lower()
        sec_type = "chorus"
        if "intro" in sec_key:
            sec_type = "intro"
        elif "verse" in sec_key:
            sec_type = "verse"
        elif "pre" in sec_key:
            sec_type = "prechorus"
        elif "bridge" in sec_key:
            sec_type = "bridge"
        elif "outro" in sec_key:
            sec_type = "outro"

        chord_prog = palette.get(sec_type, palette["chorus"])

        section_lines = [f"% {section_name}", "V: Vocal"]
        section_bars: list[str] = []

        if sec_type == "intro":
            # 4-bar instrumental intro derived from motif opening bars
            intro_bars_count = min(4, max(2, num_motif_bars))
            for b_idx in range(intro_bars_count):
                source_bar = motif_bars[b_idx % num_motif_bars]
                c_num = chord_prog[b_idx % len(chord_prog)]
                chord_sym = roman_to_chord(c_num, analysis.root_pc, analysis.mode, use_flats)
                # Rest or quiet accompaniment
                notes = transform_bar_notes(
                    source_bar, analysis, semitone_shift=0, use_flats=use_flats
                )
                section_bars.append(f'"{chord_sym}"{notes}')

        elif sec_type == "chorus":
            if role == "chorus":
                # Pristine motif
                for b_idx, bar in enumerate(motif_bars):
                    c_num = chord_prog[b_idx % len(chord_prog)]
                    chord_sym = roman_to_chord(c_num, analysis.root_pc, analysis.mode, use_flats)
                    clean_notes = transform_bar_notes(bar, analysis, semitone_shift=0, use_flats=use_flats)
                    section_bars.append(f'"{chord_sym}"{clean_notes}')
            else:
                # Role was verse: chorus is transposed up a 4th (+5 semitones)
                for b_idx, bar in enumerate(motif_bars):
                    c_num = chord_prog[b_idx % len(chord_prog)]
                    chord_sym = roman_to_chord(c_num, analysis.root_pc, analysis.mode, use_flats)
                    chorus_notes = transform_bar_notes(
                        bar, analysis, semitone_shift=5, use_flats=use_flats
                    )
                    section_bars.append(f'"{chord_sym}"{chorus_notes}')

        elif sec_type == "verse":
            # Vocal intimacy: lower register by 4th (-5 semitones) or 5th (-7) with smoothed leaps
            shift = -5 if role == "chorus" else 0
            for b_idx, bar in enumerate(motif_bars):
                c_num = chord_prog[b_idx % len(chord_prog)]
                chord_sym = roman_to_chord(c_num, analysis.root_pc, analysis.mode, use_flats)
                verse_notes = transform_bar_notes(
                    bar, analysis, semitone_shift=shift, smooth_leaps=True, use_flats=use_flats
                )
                section_bars.append(f'"{chord_sym}"{verse_notes}')

        elif sec_type == "prechorus":
            # Rhythmic build & ascending tension into dominant
            half_bars = motif_bars[len(motif_bars) // 2:] or motif_bars
            target_bars = max(2, min(4, len(half_bars) * 2))
            for b_idx in range(target_bars):
                source_bar = half_bars[b_idx % len(half_bars)]
                c_num = chord_prog[b_idx % len(chord_prog)]
                chord_sym = roman_to_chord(c_num, analysis.root_pc, analysis.mode, use_flats)
                # Ascending step (+2 semitones per iteration)
                asc_shift = (b_idx // 2) * 2
                pre_notes = transform_bar_notes(
                    source_bar, analysis, semitone_shift=asc_shift, use_flats=use_flats
                )
                section_bars.append(f'"{chord_sym}"{pre_notes}')

        elif sec_type == "bridge":
            # Melodic inversion around pivot into relative minor
            for b_idx, bar in enumerate(motif_bars):
                c_num = chord_prog[b_idx % len(chord_prog)]
                chord_sym = roman_to_chord(c_num, analysis.root_pc, analysis.mode, use_flats)
                bridge_notes = transform_bar_notes(
                    bar, analysis, invert=True, pivot_midi=pivot, use_flats=use_flats
                )
                section_bars.append(f'"{chord_sym}"{bridge_notes}')

        elif sec_type == "outro":
            # 4-bar cadential resolution tag
            outro_bars_count = min(4, max(2, num_motif_bars))
            for b_idx in range(outro_bars_count):
                source_bar = motif_bars[b_idx % num_motif_bars]
                c_num = chord_prog[b_idx % len(chord_prog)]
                chord_sym = roman_to_chord(c_num, analysis.root_pc, analysis.mode, use_flats)
                outro_notes = transform_bar_notes(
                    source_bar, analysis, semitone_shift=-12 if b_idx == outro_bars_count - 1 else 0, use_flats=use_flats
                )
                section_bars.append(f'"{chord_sym}"{outro_notes}')

        # Format bars into lines of 4 bars
        bar_lines: list[str] = []
        for i in range(0, len(section_bars), 4):
            chunk = section_bars[i:i + 4]
            bar_lines.append("| " + " | ".join(chunk) + " |")

        section_lines.extend(bar_lines)
        output_sections.append("\n".join(section_lines))

    # Construct the full score header
    header_lines: list[str] = []
    # If original header exists, preserve it; otherwise construct canonical header
    if analysis.raw_header:
        for h in analysis.raw_header:
            if not h.startswith("V:"):
                header_lines.append(h)
    else:
        header_lines = [
            "X:1",
            "T:Expanded Song",
            f"M:{analysis.meter[0]}/{analysis.meter[1]}",
            f"L:{analysis.unit_length}",
            f"Q:1/4={analysis.bpm}",
            f"K:{analysis.key_root}{'m' if analysis.mode == 'minor' else ''}",
        ]

    # Ensure Voice declaration is present
    header_lines.append('V: Vocal clef=treble name="Vocal Melody" snm="Vocal"')

    full_abc = "\n".join(header_lines) + "\n\n" + "\n\n".join(output_sections) + "\n"
    return full_abc


def stitch_motif_into_plan(plan_abc: str, motif_abc: str, role: str = "chorus") -> str:
    """Stitch the pristine hummed motif into the matching sections of a neural score plan.

    Ensures that when the AI planner extrapolates the rest of the song, the user's
    exact hummed melody and chords remain 100% faithful in the hook section.
    """
    motif_analysis = analyze_motif(motif_abc)
    motif_bars = [b for b in motif_analysis.bars if b.strip()]
    if not motif_bars:
        return plan_abc

    lines = plan_abc.splitlines()
    output_lines: list[str] = []
    current_sec: str = ""
    in_target_sec: bool = False
    in_voice_vocal: bool = False
    target_role = role.lower()

    for line in lines:
        stripped = line.strip()
        sec_match = score.SECTION_MARK.match(stripped)
        if sec_match:
            current_sec = stripped[1:].strip().lower()
            in_target_sec = (target_role in current_sec)
            in_voice_vocal = False
            output_lines.append(line)
            continue

        if stripped.startswith("V:"):
            v_name = stripped[2:].strip().split()[0] if stripped[2:].strip() else ""
            in_voice_vocal = (v_name.lower() == "vocal")
            output_lines.append(line)
            if in_target_sec and in_voice_vocal:
                # Insert the motif bars
                bar_chunks: list[str] = []
                for i in range(0, len(motif_bars), 4):
                    chunk = [b.strip() for b in motif_bars[i:i + 4]]
                    bar_chunks.append("| " + " | ".join(chunk) + " |")
                output_lines.extend(bar_chunks)
            continue

        if in_target_sec and in_voice_vocal:
            # Skip the planner's generated bars for this target section since we replaced them
            if "|" in stripped:
                continue

        output_lines.append(line)

    return "\n".join(output_lines)

