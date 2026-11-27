"""End-to-end tests for Starter Pack packaging, Docker fetch (--demos), and app import."""
from __future__ import annotations

import functools
import hashlib
import http.server
import importlib.util
import json
import sqlite3
import struct
import threading
import zlib
from pathlib import Path

from app import artwork, config, db, starter_pack
from conftest import make_take

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _tiny_png() -> bytes:
    raw = b"".join(b"\x00" + b"\x10\x20\x30\xff" * 2 for _ in range(2))
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )


def _populate_source_library(src_data: Path, src_models: Path) -> None:
    """Create a mini source Yeufonic library with a 'Starter Pack' space containing:
    - 1 song with style LoRA, artwork, mastering fx_chain, peaks, and voice
    - 1 cover referencing a source recording
    """
    src_data.mkdir(parents=True, exist_ok=True)
    (src_models / "loras").mkdir(parents=True, exist_ok=True)

    # Create a separate SQLite DB using Yeufonic's own schema
    db_path = src_data / "yue2.sqlite"
    con = sqlite3.connect(db_path)
    con.executescript(db.BASE_SCHEMA)
    con.execute("INSERT INTO spaces (id, name, created_at) VALUES ('default', 'Default', 0)")
    con.execute("INSERT INTO spaces (id, name, created_at) VALUES ('sp_src_1', 'Starter Pack', 1000.0)")

    # Style LoRA + description
    (src_models / "loras" / "demo_style_lora.safetensors").write_bytes(b"FAKE_LORA_WEIGHTS_123456")
    (src_models / "loras" / "demo_style_lora.txt").write_text("Demo Style\nTrigger: demostyle\n", encoding="utf-8")

    # Voice + model.pth + model.index
    vdir = src_data / "voices" / "voice0000001"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "model.pth").write_bytes(b"PK\x03\x04FAKE_VOICE_MODEL")
    (vdir / "model.index").write_bytes(b"FAKE_VOICE_INDEX")
    con.execute(
        "INSERT INTO voices (id, name, state, progress, model_path, created_at, octave, level_db, likeness, room, f0_floor) "
        "VALUES ('voice0000001', 'Studio Singer', 'ready', 1.0, '/data/voices/voice0000001/model.pth', 1001.0, 0, 3.0, 0.75, 0.14, 95.0)"
    )

    # Cover source recording
    sdir = src_data / "sources"
    sdir.mkdir(parents=True, exist_ok=True)
    src_bytes = b"fLaC_FAKE_SOURCE_AUDIO_DATA"
    src_sha = hashlib.sha256(src_bytes).hexdigest()
    src_file = sdir / f"{src_sha[:16]}-rough-demo.flac"
    src_file.write_bytes(src_bytes)
    con.execute(
        "INSERT INTO sources (id, title, filename, stored_path, sha256, created_at, abc, transcribe_state, lyrics, lyrics_state, duration) "
        "VALUES ('src000000001', 'Rough Demo', 'Rough Demo.flac', ?, ?, 1002.0, 'X:1\nK:C\nC4|\n', 'done', '[Verse]\nHello', 'done', 120.5)",
        (f"/data/sources/{src_file.name}", src_sha),
    )

    # Take 1: song with LoRA, voice, mastering fx_chain, artwork, peaks
    t1_dir = src_data / "takes" / "first-demo-take00000001"
    t1_dir.mkdir(parents=True, exist_ok=True)
    t1_audio = t1_dir / "first-demo.normalised.flac"
    t1_audio.write_bytes(b"fLaC_FAKE_TAKE1_AUDIO")
    (t1_dir / "first-demo.normalised.peaks.json").write_text(json.dumps({"peaks": [0.1, 0.5, 0.9]}), encoding="utf-8")
    (src_data / "art").mkdir(parents=True, exist_ok=True)
    (src_data / "art" / "take00000001.png").write_bytes(_tiny_png())
    (src_data / "art" / "take00000001.txt").write_text("A glowing vinyl turntable at dusk.", encoding="utf-8")
    fx1 = {"version": 2, "reverb": {"on": True, "mix": 8, "program": "large_hall"}, "limit": {"on": True}}
    vmix1 = {"octave": 0, "level_db": 3.0, "likeness": 0.75}
    con.execute(
        "INSERT INTO takes (id, kind, title, style, lyrics, abc, mode, seed, checkpoint, status, audio_path, duration, "
        "created_at, space_id, style_lora, style_lora_model, style_lora_clip, voice_id, voice_mix, fx_chain, loudness, normalised) "
        "VALUES ('take00000001', 'song', 'First Demo', 'indie rock, bright guitars', '[Verse]\nLa la', 'X:1\nK:G\nG4|\n', "
        "'full', 42, 'yue2_3b_bf16.safetensors', 'done', ?, 182.5, 1010.0, 'sp_src_1', 'demo_style_lora.safetensors', "
        "0.7, 0.6, 'voice0000001', ?, ?, -14.0, 1)",
        (f"/data/takes/{t1_dir.name}/{t1_audio.name}", json.dumps(vmix1), json.dumps(fx1)),
    )

    # Take 2: cover referencing source recording
    t2_dir = src_data / "takes" / "cover-demo-take00000002"
    t2_dir.mkdir(parents=True, exist_ok=True)
    t2_audio = t2_dir / "cover-demo.flac"
    t2_audio.write_bytes(b"fLaC_FAKE_TAKE2_AUDIO")
    (src_data / "art" / "take00000002.png").write_bytes(_tiny_png())
    con.execute(
        "INSERT INTO takes (id, kind, source_id, title, style, lyrics, abc, mode, seed, checkpoint, status, audio_path, duration, "
        "created_at, space_id, fx_chain, loudness, normalised) "
        "VALUES ('take00000002', 'cover', 'src000000001', 'Cover Demo', 'synth pop', '[Verse]\nHello', 'X:1\nK:C\nC4|\n', "
        "'full', 99, 'yue2_3b_bf16.safetensors', 'done', ?, 121.0, 1020.0, 'sp_src_1', ?, -14.2, 0)",
        (f"/data/takes/{t2_dir.name}/{t2_audio.name}", json.dumps({"version": 2, "eq": {"on": True}})),
    )

    con.commit()
    con.close()


def _serve_directory(directory: Path):
    class QuietServer(http.server.ThreadingHTTPServer):
        allow_reuse_address = True

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def log_message(self, format, *args):
            pass

    httpd = QuietServer(("127.0.0.1", 0), QuietHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def test_build_fetch_and_install_starter_pack_end_to_end(client, tmp_path):
    """Full pipeline: build R2 package -> fetch over HTTP into destination -> import via API -> verify play/edit state."""
    builder = _load_module("build_starter_pack", "tools/build_starter_pack.py")
    fetcher = _load_module("fetch_starter_pack", "scripts/_fetch_starter_pack.py")

    src_data = tmp_path / "src_data"
    src_models = tmp_path / "src_models"
    r2_dir = tmp_path / "r2_starter_pack"
    _populate_source_library(src_data, src_models)

    # Force multi-part zip splitting (e.g., to stay under R2's 300 MiB Wrangler upload limit)
    manifest = builder.build_pack(src_data, src_models, r2_dir, max_bundle_bytes=120)
    assert manifest["format"] == "yeufonic-starter-pack-manifest"
    assert manifest["counts"] == {"takes": 2, "voices": 1, "sources": 1, "loras": 1}
    assert len(manifest["bundles"]) >= 2
    assert (r2_dir / "manifest.json").is_file()
    for b in manifest["bundles"]:
        assert (r2_dir / b["path"]).is_file()
    assert (r2_dir / "loras" / "demo_style_lora.safetensors").is_file()
    assert (r2_dir / "loras" / "demo_style_lora.txt").is_file()
    assert (r2_dir / "voices" / "voice0000001" / "model.pth").is_file()
    assert (r2_dir / "voices" / "voice0000001" / "model.index").is_file()

    # Destination root uses the pytest fixture's DATA_DIR via a symlink or direct layout
    dest_root = tmp_path / "dest_root"
    dest_root.mkdir()
    (dest_root / "data").symlink_to(config.DATA_DIR)
    (dest_root / "models" / "loras").mkdir(parents=True)

    # Pre-seed an existing LoRA description file to confirm user files are NOT overwritten
    (dest_root / "models" / "loras" / "demo_style_lora.txt").write_text("My custom notes\n", encoding="utf-8")

    httpd, url = _serve_directory(r2_dir)
    try:
        fetch_res = fetcher.fetch_starter_pack(dest_root, base_url=url, trigger_live=False)
    finally:
        httpd.shutdown()

    assert fetch_res["skipped_bundle"] is False
    assert (dest_root / "models" / "loras" / "demo_style_lora.safetensors").read_bytes() == b"FAKE_LORA_WEIGHTS_123456"
    assert (dest_root / "models" / "loras" / "demo_style_lora.txt").read_text(encoding="utf-8") == "My custom notes\n"
    assert (config.DATA_DIR / "starter-pack" / "pack.json").is_file()

    # Check status endpoint reports pending before install
    st = client.get("/api/starter-pack")
    assert st.status_code == 200
    assert st.json()["pending"] is True

    # Trigger install via API endpoint (the same path fetch-models.sh calls on a running container)
    res = client.post("/api/starter-pack/install")
    assert res.status_code == 200
    body = res.json()
    assert body["installed"] is True
    assert body["space_name"] == "Starter Pack"
    assert body["takes_added"] == 2
    assert body["voices_added"] == 1
    assert body["sources_added"] == 1

    # Stage folder cleaned up after install
    assert not (config.DATA_DIR / "starter-pack").exists()

    # Space exists and lists both takes with mastering settings, artwork, voice, and cover source
    spaces = client.get("/api/spaces").json()
    sp = next(s for s in spaces if s["name"] == "Starter Pack")
    takes = client.get(f"/api/takes?space_id={sp['id']}").json()
    assert len(takes) == 2
    by_id = {t["id"]: t for t in takes}

    t1 = by_id["take00000001"]
    assert t1["title"] == "First Demo"
    assert t1["style_lora"] == "demo_style_lora.safetensors"
    assert t1["voice_id"] == "voice0000001"
    assert json.loads(t1["fx_chain"])["reverb"]["program"] == "large_hall"
    assert json.loads(t1["voice_mix"])["level_db"] == 3.0
    assert artwork.png_path("take00000001").is_file()
    assert "turntable" in (artwork.info("take00000001")["words"] or "")

    # Audio & artwork endpoints serve cleanly
    assert client.get("/api/takes/take00000001/audio").content == b"fLaC_FAKE_TAKE1_AUDIO"
    assert client.get("/api/takes/take00000001/art.png").status_code == 200

    # Cover take is linked to the imported source recording
    t2 = by_id["take00000002"]
    assert t2["kind"] == "cover"
    assert t2["source_id"] == "src000000001"
    assert Path(db.one("SELECT stored_path FROM sources WHERE id = 'src000000001'")["stored_path"]).is_file()

    # Voice is installed with model.pth & model.index pointing into destination DATA_DIR
    voice_row = db.one("SELECT * FROM voices WHERE id = 'voice0000001'")
    assert voice_row["name"] == "Studio Singer"
    assert Path(voice_row["model_path"]).is_file()
    assert (Path(voice_row["model_path"]).parent / "model.index").is_file()

    # Re-running fetcher sees identical pack_id already installed and skips re-downloading bundle
    httpd2, url2 = _serve_directory(r2_dir)
    try:
        fetch_again = fetcher.fetch_starter_pack(dest_root, base_url=url2, trigger_live=False)
    finally:
        httpd2.shutdown()
    assert fetch_again["skipped_bundle"] is True
    assert fetch_again["loras_fetched"] == 0


def test_starter_pack_import_is_idempotent_and_reuses_existing_voice_and_space(client, tmp_path):
    """Existing 'Starter Pack' space, existing voice (by name), and existing takes are preserved without duplication."""
    builder = _load_module("build_starter_pack", "tools/build_starter_pack.py")
    fetcher = _load_module("fetch_starter_pack", "scripts/_fetch_starter_pack.py")

    src_data = tmp_path / "src_data"
    src_models = tmp_path / "src_models"
    r2_dir = tmp_path / "r2_starter_pack"
    _populate_source_library(src_data, src_models)
    builder.build_pack(src_data, src_models, r2_dir)

    # Pre-create a space named "starter pack" (different case) and a voice named "Studio Singer" (different id)
    db.execute("INSERT INTO spaces (id, name, created_at) VALUES ('custom_sp', 'starter pack', 500.0)")
    existing_vdir = config.DATA_DIR / "voices" / "user_voice_99"
    existing_vdir.mkdir(parents=True, exist_ok=True)
    (existing_vdir / "model.pth").write_bytes(b"PK\x03\x04USER_OWN_VOICE")
    db.execute(
        "INSERT INTO voices (id, name, state, progress, model_path, created_at) "
        "VALUES ('user_voice_99', 'studio singer', 'ready', 1.0, ?, 500.0)",
        (str(existing_vdir / "model.pth"),),
    )

    dest_root = tmp_path / "dest_root"
    dest_root.mkdir()
    (dest_root / "data").symlink_to(config.DATA_DIR)
    (dest_root / "models" / "loras").mkdir(parents=True)

    httpd, url = _serve_directory(r2_dir)
    try:
        fetch_res = fetcher.fetch_starter_pack(dest_root, base_url=url, trigger_live=False)
    finally:
        httpd.shutdown()

    # Fetcher detected the existing voice by name in SQLite and skipped downloading it
    assert fetch_res["voices_fetched"] == 0

    first = starter_pack.install_pending(keep_stage=True)
    assert first["installed"] is True
    assert first["space_id"] == "custom_sp"
    assert first["voices_added"] == 0
    assert first["voices_skipped"] == 1
    assert first["takes_added"] == 2

    # Take 1 is linked to the user's existing voice without overwriting user's model.pth
    t1 = db.one("SELECT voice_id, title FROM takes WHERE id = 'take00000001'")
    assert t1["voice_id"] == "user_voice_99"
    assert (existing_vdir / "model.pth").read_bytes() == b"PK\x03\x04USER_OWN_VOICE"

    # Edit take title, then re-run install_pending — must skip existing takes and preserve user edit
    db.execute("UPDATE takes SET title = 'My Edited Demo' WHERE id = 'take00000001'")
    second = starter_pack.install_pending(keep_stage=False)
    assert second["takes_added"] == 0
    assert second["takes_skipped"] == 2
    assert db.one("SELECT title FROM takes WHERE id = 'take00000001'")["title"] == "My Edited Demo"


def test_fetch_models_script_documents_and_parses_demos_flag():
    script = (REPO_ROOT / "scripts" / "fetch-models.sh").read_text(encoding="utf-8")
    assert "--demos)" in script
    assert "DEMOS=yes" in script
    assert "_fetch_starter_pack.py" in script
    assert "STARTER_PACK_URL" in script
    builder = _load_module("build_starter_pack_schema_check", "tools/build_starter_pack.py")
    assert builder.TAKE_COLUMNS == starter_pack.TAKE_COLUMNS
    assert builder.VOICE_COLUMNS == starter_pack.VOICE_COLUMNS
    assert builder.SOURCE_COLUMNS == starter_pack.SOURCE_COLUMNS


def test_native_installers_default_starter_pack_on_for_new_users_and_off_for_existing():
    nsi = (REPO_ROOT / "windows" / "installer.nsi").read_text(encoding="utf-8")
    # Default ticked for new installs (Section without /o), unticked for existing users
    assert 'Section "Starter Pack (demo songs)" SecDemos' in nsi
    assert 'StrCpy $1 "$1 -Demos"' in nsi
    assert '!insertmacro UnselectSection ${SecDemos}' in nsi
    assert 'Starter Pack (installed)' in nsi

    ps1 = (REPO_ROOT / "windows" / "setup.ps1").read_text(encoding="utf-8")
    assert "[switch]$Demos" in ps1
    assert "https://media.yeufonic.com/starter-pack" in ps1
    assert "Done 'starter-pack'" in ps1

    linux_sh = (REPO_ROOT / "linux" / "setup.sh").read_text(encoding="utf-8")
    assert "--demos) DEMOS=yes; shift ;;" in linux_sh
    assert "--no-demos) DEMOS=no; shift ;;" in linux_sh
    assert 'echo "$DEMOS" > "$STATE/demos"' in linux_sh
    assert "https://media.yeufonic.com/starter-pack" in linux_sh

    macos_sh = (REPO_ROOT / "macos" / "setup.sh").read_text(encoding="utf-8")
    assert "--demos) DEMOS=yes; shift ;;" in macos_sh
    assert "--no-demos) DEMOS=no; shift ;;" in macos_sh
    assert "Install the Starter Pack demo songs? [Y/n]" in macos_sh
    assert "https://media.yeufonic.com/starter-pack" in macos_sh

    # Every installer falls back to the Hugging Face mirror when R2 fails
    for text in (ps1, linux_sh, macos_sh):
        assert "pshields/yeufonic-starter-pack/resolve/main" in text


def test_fetch_starter_pack_falls_back_to_mirror_and_sticks_to_it(tmp_path):
    """If primary serves manifest.json (small) but fails on payload downloads (e.g. 16 KB ISP reset),
    the fetcher switches to the fallback mirror and uses it directly for all remaining files."""
    builder = _load_module("build_starter_pack_fb", "tools/build_starter_pack.py")
    fetcher = _load_module("fetch_starter_pack_fb", "scripts/_fetch_starter_pack.py")

    src_data = tmp_path / "src_data"
    src_models = tmp_path / "src_models"
    _populate_source_library(src_data, src_models)
    dist_dir = tmp_path / "dist"
    builder.build_pack(src_data, src_models, dist_dir)

    primary_hits: list[str] = []
    fallback_hits: list[str] = []

    class FlakyPrimaryHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            primary_hits.append(self.path)
            if self.path.endswith("/manifest.json"):
                return super().do_GET()
            self.send_error(502, "Simulated Cloudflare reset")

        def log_message(self, fmt, *args):
            pass

    class MirrorHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            fallback_hits.append(self.path)
            return super().do_GET()

        def log_message(self, fmt, *args):
            pass

    p_srv = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(FlakyPrimaryHandler, directory=str(dist_dir))
    )
    f_srv = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(MirrorHandler, directory=str(dist_dir))
    )
    threading.Thread(target=p_srv.serve_forever, daemon=True).start()
    threading.Thread(target=f_srv.serve_forever, daemon=True).start()
    try:
        dest_root = tmp_path / "dest"
        res = fetcher.fetch_starter_pack(
            dest_root,
            base_url=f"http://127.0.0.1:{p_srv.server_address[1]}",
            fallback_url=f"http://127.0.0.1:{f_srv.server_address[1]}",
            trigger_live=False,
        )
    finally:
        p_srv.shutdown()
        p_srv.server_close()
        f_srv.shutdown()
        f_srv.server_close()

    assert res["loras_fetched"] == 2
    assert res["voices_fetched"] == 2
    assert (dest_root / "models" / "loras" / "demo_style_lora.safetensors").is_file()
    assert (dest_root / "data" / "starter-pack" / "pack.json").is_file()
    # Primary was hit for manifest.json and only the first failing payload (never subsequent files)
    payload_primary = {p for p in primary_hits if not p.endswith("/manifest.json")}
    assert len(payload_primary) == 1, f"expected sticky switch after 1st failed payload, got {payload_primary}"
    assert len(fallback_hits) >= 4
