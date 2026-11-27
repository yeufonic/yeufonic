import json

from app import config
from app.library import audio_duration, compute_peaks, ensure_peaks, inside, peaks_path, slugify, source_path

from conftest import tone


def test_slugify():
    assert slugify("Paper Boat (demo)!") == "paper-boat-demo"
    assert slugify("") == "untitled"
    assert len(slugify("x" * 100)) == 40


def test_source_path_keeps_the_name_after_the_hash():
    path = source_path("f72ac22518a9ea05ffff", "Paper Boat.wav", "fallback", ".wav")
    assert path == config.SOURCES_DIR / "f72ac22518a9ea05-paper-boat.wav"


def test_inside():
    assert inside(config.DATA_DIR / "stems" / "a", config.DATA_DIR)
    assert not inside(config.DATA_DIR / ".." / "elsewhere", config.DATA_DIR)


def test_duration_of_flac_from_the_header_and_mp3_from_ffprobe(data_dir):
    assert abs(audio_duration(tone(data_dir / "a.flac", 2.0)) - 2.0) < 0.05
    assert abs(audio_duration(tone(data_dir / "a.mp3", 3.0)) - 3.0) < 0.1


def test_peaks_are_normalised_and_cached(data_dir):
    audio = tone(data_dir / "a.flac", 1.5)
    result = compute_peaks(audio)
    assert result["columns"] == len(result["peaks"]) == len(result["rms"]) == 1024
    assert max(result["peaks"]) == 1.0 and min(result["peaks"]) >= 0
    cached = ensure_peaks(audio)
    assert json.loads(peaks_path(audio).read_text()) == cached


def test_peaks_of_a_very_short_file(data_dir):
    result = compute_peaks(tone(data_dir / "short.wav", 0.05))
    assert len(result["peaks"]) == 1024


def test_ensure_peaks_recovers_from_empty_cache_and_writes_atomically(data_dir):
    from concurrent.futures import ThreadPoolExecutor

    audio = tone(data_dir / "race.flac", 1.0)
    cache = peaks_path(audio)
    # Simulate a truncated/empty cache file newer than the audio.
    cache.write_text("", encoding="utf-8")
    recovered = ensure_peaks(audio)
    assert recovered is not None and len(recovered["peaks"]) == 1024
    assert json.loads(cache.read_text(encoding="utf-8")) == recovered

    # Concurrent readers/writers never observe a partial cache or leave temp files behind.
    cache.unlink()
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: ensure_peaks(audio), range(12)))
    assert all(r is not None and len(r["peaks"]) == 1024 for r in results)
    assert not list(data_dir.glob("*.tmp"))
