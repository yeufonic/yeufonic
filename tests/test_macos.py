import ast
import plistlib
import subprocess
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
MACOS_DIR = ROOT / "macos"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "macos.yml"


def test_macos_files_exist():
    assert (MACOS_DIR / "Info.plist").is_file()
    assert (MACOS_DIR / "launcher.py").is_file()
    assert (MACOS_DIR / "setup.sh").is_file()
    assert (MACOS_DIR / "build.sh").is_file()
    assert WORKFLOW_PATH.is_file()


def test_macos_info_plist():
    plist_path = MACOS_DIR / "Info.plist"
    with plist_path.open("rb") as f:
        data = plistlib.load(f)
    assert data["CFBundleName"] == "Yeufonic"
    assert data["CFBundleDisplayName"] == "Yeufonic"
    assert data["CFBundleIdentifier"] == "com.yeufonic.app"
    assert data["CFBundleExecutable"] == "Yeufonic"
    assert "LSMinimumSystemVersion" in data
    assert data["NSHighResolutionCapable"] is True


def test_macos_launcher_syntax_and_features():
    launcher_path = MACOS_DIR / "launcher.py"
    content = launcher_path.read_text(encoding="utf-8")
    ast.parse(content)
    assert "MacOSLauncher" in content
    assert "PYTORCH_ENABLE_MPS_FALLBACK" in content
    assert "PYTORCH_MPS_HIGH_WATERMARK_RATIO" in content
    assert "uvicorn" in content
    assert "api/health" in content


def test_macos_shell_scripts_syntax():
    for script in ("setup.sh", "build.sh"):
        p = MACOS_DIR / script
        res = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
        assert res.returncode == 0, f"Syntax error in {script}: {res.stderr}"


def test_macos_setup_script_checks():
    content = (MACOS_DIR / "setup.sh").read_text(encoding="utf-8")
    assert "arm64" in content, "Must verify Apple Silicon architecture"
    assert "hw.memsize" in content, "Must check memory size"
    assert "--check-only" in content
    assert "--skip-models" in content
    assert "UV_URL" in content


def test_macos_github_actions_workflow():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert data["name"]
    # Check trigger
    triggers = data.get("on") or data.get(True)
    assert "workflow_dispatch" in triggers or "workflow_dispatch" in str(triggers)
    # Check jobs
    assert "build-macos" in data["jobs"]
    job = data["jobs"]["build-macos"]
    assert job["runs-on"] == "macos-14", "Must use Apple Silicon runner"
    step_names = [s.get("name", "") for s in job["steps"]]
    assert any("Build macOS" in s for s in step_names)
    assert any("Upload DMG" in s for s in step_names)


def test_update_module_macos_support():
    from app import update
    # Test _installer_from with .dmg on darwin
    assets = [
        {"name": "Yeufonic-Setup-0.0.47.exe", "browser_download_url": "https://example.com/setup.exe"},
        {"name": "Yeufonic-Setup-0.0.47.dmg", "browser_download_url": "https://example.com/setup.dmg"},
    ]
    import sys
    orig_platform = sys.platform
    try:
        sys.platform = "darwin"
        url, _ = update._installer_from(assets)
        assert url == "https://example.com/setup.dmg"

        sys.platform = "win32"
        url, _ = update._installer_from(assets)
        assert url == "https://example.com/setup.exe"
    finally:
        sys.platform = orig_platform
