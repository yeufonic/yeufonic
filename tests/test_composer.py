"""Unit and integration tests for Hum-to-Song Thematic Composer."""
import pytest
from app import composer, score


def test_analyze_motif():
    abc = """X:1
T:Test Motif
M:4/4
L:1/8
Q:1/4=130
K:G
V: Vocal
"G"g4 d4 | "C"e4 c4 | "D"d4 A4 | "G"B8 |
"""
    analysis = composer.analyze_motif(abc)
    assert analysis.key_root == "G"
    assert analysis.mode == "major"
    assert analysis.bpm == 130
    assert analysis.meter == (4, 4)
    assert len(analysis.bars) == 4
    assert len(analysis.pitches) == 7


def test_analyze_minor_key_and_accidentals():
    abc = """X:1
M:3/4
L:1/16
Q:1/4=90
K:Am
V: Vocal
"Am"A4 c4 e4 | "Dm"d4 f4 a4 | "E7"^g4 e4 B4 | "Am"A12 |
"""
    analysis = composer.analyze_motif(abc)
    assert analysis.key_root == "A"
    assert analysis.mode == "minor"
    assert analysis.bpm == 90
    assert analysis.meter == (3, 4)
    assert 9 in analysis.scale_pcs  # A is pc 9


def test_expand_motif_symbolic_standard_pop():
    abc = """X:1
T:Vocal Hook
M:4/4
L:1/8
Q:1/4=120
K:C
V: Vocal
"C"c4 d4 | "G"e4 d4 | "Am"c4 A4 | "F"G8 |
"""
    expanded = composer.expand_motif_to_song(abc, palette_name="pop", role="chorus")
    assert "% Intro" in expanded
    assert "% Verse 1" in expanded
    assert "% Pre-Chorus" in expanded
    assert "% Chorus" in expanded
    assert "% Bridge" in expanded
    assert "% Outro" in expanded

    # Score must be valid with zero problems
    problems = score.problems(expanded)
    assert not problems, f"Score has problems: {problems}"

    est = score.estimate(expanded)
    assert est is not None
    assert est["bars"] >= 30
    assert est["bpm"] == 120


def test_expand_motif_verse_role_and_short_preset():
    abc = """X:1
M:4/4
L:1/8
Q:1/4=110
K:F
V: Vocal
"F"F4 A4 | "Bb"B4 d4 | "C"c4 G4 | "F"F8 |
"""
    sections = composer.PRESETS["short"]
    expanded = composer.expand_motif_to_song(abc, structure=sections, palette_name="rock", role="verse")
    assert "% Verse 1" in expanded
    assert "% Chorus" in expanded
    assert "% Bridge" not in expanded

    problems = score.problems(expanded)
    assert not problems, f"Score has problems: {problems}"


def test_stitch_motif_into_plan():
    plan = """X:1
T:Plan
M:4/4
L:1/8
K:C
V: Vocal clef=treble name="Vocal Melody" snm="Vocal"

% Verse 1
V: Vocal
| "C"c4 c4 | "G"d4 d4 |

% Chorus
V: Vocal
| "Am"a4 a4 | "F"f4 f4 |

% Outro
V: Vocal
| "C"c8 |
"""
    motif = """X:1
M:4/4
L:1/8
K:C
V: Vocal
| "C"e4 g4 | "Am"a4 e4 |
"""
    stitched = composer.stitch_motif_into_plan(plan, motif, role="chorus")
    assert "e4 g4" in stitched
    assert "a4 a4" not in stitched
    assert "% Verse 1" in stitched
    assert "% Outro" in stitched


def test_api_composer_options(client):
    res = client.get("/api/composer/options")
    assert res.status_code == 200
    data = res.json()
    assert "presets" in data
    assert "palettes" in data
    assert any(p["id"] == "standard" for p in data["presets"])
    assert any(p["id"] == "pop" for p in data["palettes"])


def test_api_composer_expand_symbolic(client):
    abc = """X:1
M:4/4
L:1/8
Q:1/4=120
K:D
V: Vocal
"D"d4 f4 | "G"g4 b4 | "A"a4 e4 | "D"d8 |
"""
    payload = {
        "abc": abc,
        "method": "symbolic",
        "preset": "standard",
        "palette": "pop",
        "role": "chorus",
    }
    res = client.post("/api/composer/expand", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["method"] == "symbolic"
    assert "abc" in data
    assert data["estimate"]["bpm"] == 120
    assert not data["problems"]


def test_api_composer_expand_neural(client):
    abc = """X:1
M:4/4
L:1/8
Q:1/4=128
K:C
V: Vocal
"C"c4 d4 | "G"e4 d4 | "Am"c4 A4 | "F"G8 |
"""
    payload = {
        "abc": abc,
        "method": "neural",
        "preset": "short",
        "title": "My Neural Song",
        "style": "Synthwave, 128 BPM",
    }
    res = client.post("/api/composer/expand", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["method"] == "neural"
    assert "take_id" in data
    assert data["status"] == "queued"


def test_api_composer_expand_missing_input_errors(client):
    res = client.post("/api/composer/expand", json={"method": "symbolic"})
    assert res.status_code == 400

    res_missing_src = client.post("/api/composer/expand", json={"source_id": "nonexistent", "method": "symbolic"})
    assert res_missing_src.status_code == 404
