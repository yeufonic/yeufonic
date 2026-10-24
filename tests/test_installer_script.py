"""Things in the Windows installer script that went wrong once and are cheap to keep from coming back."""
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parent.parent / "windows" / "installer.nsi").read_text(encoding="utf-8")


def test_the_model_size_choice_does_not_use_the_radio_button_macros():
    """NSIS's StartRadioButtons takes a variable holding the previously chosen section and unticks that
    section first. With it unset it unticked the core section on the first click anywhere on the
    components page, so nothing was installed and setup failed. The two sizes are handled in
    .onSelChange by hand, touching only those two sections."""
    assert "StartRadioButtons" not in SCRIPT
    assert "Function .onSelChange" in SCRIPT
    assert "Var ModelRadio" in SCRIPT


def test_the_component_choice_is_set_up_before_the_page_is_shown():
    start = SCRIPT.index("Function .onInit")
    init = SCRIPT[start:SCRIPT.index("\nFunctionEnd", start)]
    assert "StrCpy $ModelRadio" in init


def test_both_installers_pin_the_trainer_commit():
    """Both Docker and Windows install ComfyUI-YuE2-Trainer pinned to the same tested commit."""
    root = Path(__file__).resolve().parent.parent
    windows = (root / "windows" / "setup.ps1").read_text(encoding="utf-8")
    docker = (root / "engine" / "Dockerfile").read_text(encoding="utf-8")
    assert "Yue2TrainerCommit = '6a9355efff60589d93b41b569676f09d5db85d09'" in windows
    assert "ARG YUE2_TRAINER_REF=6a9355efff60589d93b41b569676f09d5db85d09" in docker


def test_the_launcher_shows_a_dead_engine_once_not_on_every_tick():
    """fail() shows a message box from inside the half-second timer; the box runs its own message loop, so the
    timer fired again beneath it and stacked another box each time (126 in one failure)."""
    launcher = (Path(__file__).resolve().parent.parent / "windows" / "launcher.py").read_text(encoding="utf-8")
    body = launcher[launcher.index("    def stop_with("):launcher.index("    # ---------- the loop")]
    assert "self.quitting = True" in body and "KillTimer" in body
    assert body.index("self.quitting = True") < body.index("fail(text, log)")
    assert "if self.quitting:\n            return" in launcher[launcher.index("    def tick("):]


def test_extra_engine_switches_can_be_set_in_settings_ini():
    launcher = (Path(__file__).resolve().parent.parent / "windows" / "launcher.py").read_text(encoding="utf-8")
    assert '"engine_args": ""' in launcher and 'shlex.split(self.cfg.get("engine_args", ""))' in launcher


def test_the_windows_engine_keeps_the_portable_torch_and_undoes_the_0_0_25_pin():
    """0.0.25 put torch 2.9.1 on CUDA 12.8 into the Windows engine, where the low-memory model renders several
    times slower than on the CUDA 13 build the portable ships. The installer must not install CUDA 12.8 torch,
    and must put an install that has the pair back on the portable's own (a step of its own, so an update does it)."""
    setup = (Path(__file__).resolve().parent.parent / "windows" / "setup.ps1").read_text(encoding="utf-8")
    block = setup[setup.index("if ($variant -eq 'cu130') {\n    $torchHave"):setup.index("$nodes = Join-Path")]
    assert "whl/cu128" not in setup
    assert "'2.9.1+cu128'" in block
    assert "'torch==2.13.0', 'torchvision==0.28.0', 'torchaudio==2.11.0'" in block
    assert "https://download.pytorch.org/whl/cu130" in block
    assert "torch-2.9.1-cu128-*.done" in block


def test_the_windows_engine_gets_the_yue2_trainer():
    """Windows installs ComfyUI-YuE2-Trainer with soundfile, librosa, scipy, mutagen and einops."""
    setup = (Path(__file__).resolve().parent.parent / "windows" / "setup.ps1").read_text(encoding="utf-8")
    assert "yeufonic/ComfyUI-YuE2-Trainer" in setup and "speedyrulz/" not in setup
    assert "ComfyUI-YuE2-Trainer" in setup
    assert "soundfile>=0.12" in setup and "librosa>=0.10" in setup and "mutagen" in setup


def test_the_installers_port_check_uses_the_ports_in_settings_ini():
    """An install moved off 8090 (beside a Docker copy, which holds it) was still checked on 8090, and its own port never was."""
    setup = (Path(__file__).resolve().parent.parent / "windows" / "setup.ps1").read_text(encoding="utf-8")
    block = setup[setup.index("$ports = @(8090, 8188)"):setup.index("foreach ($site in")]
    assert "app_port" in block and "engine_port" in block and "settings.ini" in block
    assert "foreach ($port in $ports)" in block and "foreach ($port in @(8090, 8188))" not in setup


def test_the_windows_engine_gets_demucs_so_stems_can_run_on_the_gpu():
    """Installed with the engine's own Python, before our node is copied in, and its weights kept with the engine's models."""
    setup = (Path(__file__).resolve().parent.parent / "windows" / "setup.ps1").read_text(encoding="utf-8")
    block = setup.split("IsDone 'engine-demucs')")[1].split("Done 'engine-demucs'")[0]
    assert "$py @('-s', '-m', 'pip', 'install'" in block and "demucs==4.1.0" in block
    assert setup.index("Done 'engine-demucs'") < setup.index("# Our own node, carried by the installer.") + len("# Our own node, carried by the installer.")
    assert "Join-Path $Models 'demucs'" in setup and "HF_HUB_CACHE" in setup


def test_the_windows_engine_gets_whisper_with_the_cuda_12_libraries_ctranslate2_wants():
    """PyTorch there carries CUDA 13, CTranslate2 wants 12: the cuBLAS and cuDNN packages come with it, and faster-whisper
    goes in without its dependencies so PyAV is left alone."""
    setup = (Path(__file__).resolve().parent.parent / "windows" / "setup.ps1").read_text(encoding="utf-8")
    block = setup.split("IsDone 'engine-whisper')")[1].split("Done 'engine-whisper'")[0]
    assert "'--no-deps', 'faster-whisper==1.2.1'" in block and block.count("--no-warn-conflicts") >= 2   # pip's red note about onnxruntime is not a failure
    assert "nvidia-cublas-cu12" in block and "nvidia-cudnn-cu12" in block and "ctranslate2>=4.5,<5" in block
    # the model comes down with the installer's own download, so it shows progress, resumes and is checked
    block = setup.split("IsDone 'engine-whisper-model')")[1].split("Done 'engine-whisper-model'")[0]
    assert "Get-Verified" in block and "whisper\\large-v3-turbo" in block and "model.bin" in block
    assert "e76620f83d5f5b69efd3d87e3dc180c1bd21df9fbebacfd4335e5e1efcc018da" in block and "download_model" not in block


def test_quit_from_the_tray_quits_at_once_and_asks_only_when_it_would_stop_work():
    """Quit is chosen from a menu, on purpose, so it is not asked about; a render or a training run that quitting
    would stop is the one thing it still asks for."""
    launcher = (Path(__file__).resolve().parent.parent / "windows" / "launcher.py").read_text(encoding="utf-8")
    body = launcher[launcher.index("    def ask_to_quit(self)"):launcher.index("    def stop_with(")]
    assert "if warning and message(" in body                 # no question unless there is something to lose
    assert body.count("message(") == 1 and "MB_DEFBUTTON2" in body
    assert body.index("warning = self.busy()") < body.index("self.quitting = True")
    assert 'f"Quit {APP}?" + ' not in body


def test_take_pictures_are_chosen_at_install():
    """FLUX.2 klein, about 8 GB, comes only when ticked (unticked to begin with) and is remembered for updates;
    setup.ps1 fetches its three files, each against its published checksum, only with -Pictures."""
    ROOT = Path(__file__).resolve().parent.parent
    nsi = (ROOT / "windows" / "installer.nsi").read_text(encoding="utf-8")
    setup = (ROOT / "windows" / "setup.ps1").read_text(encoding="utf-8")
    fetch = (ROOT / "scripts" / "fetch-models.sh").read_text(encoding="utf-8")
    assert 'Section /o "FLUX.2 [klein]" SecPictures' in nsi
    assert 'StrCpy $1 "$1 -Pictures"' in nsi and '"Pictures" 1' in nsi and 'ReadRegDWORD $2 HKCU "Software\\$R9" "Pictures"' in nsi
    assert "[switch]$Pictures," in setup and "if ($Pictures) { $ModelFiles = @($ModelFiles) + $PictureFiles }" in setup
    assert "'Pictures', 'Loras', 'CheckOnly'" in setup       # carried across the 64-bit restart
    for name, sha in (("flux-2-klein-4b-fp8.safetensors", "97ed34fe0567e436200f2faee3939b88f2b5d99f8af2a4dc16532c4245c0ccb6"),
                      ("qwen_3_4b_fp4_flux2.safetensors", "3eab03a77adb0ee5304a4e677d5c10ac22f9049c1d7c894adca4f8bb39206ca8"),
                      ("flux2-vae.safetensors", "868fe7b343cc8f3a19dbcfcafbc3d5f888802be3f89bd81b65b3621a066ce8f3")):
        assert name in setup and sha in setup and name in fetch
    assert "--pictures) PICTURES=yes ;;" in fetch


def test_style_loras_are_chosen_at_install_and_never_replace_a_users_file():
    """The style LoRAs (by their authors, CC BY-NC 4.0, gathered in one Hugging Face repository) come only when ticked
    and are remembered for updates; Windows and Docker fetch the same files against the same checksums, a description
    with each, and a file already in the folder is left as it is, never checked or replaced."""
    import re
    ROOT = Path(__file__).resolve().parent.parent
    nsi = (ROOT / "windows" / "installer.nsi").read_text(encoding="utf-8")
    setup = (ROOT / "windows" / "setup.ps1").read_text(encoding="utf-8")
    fetch = (ROOT / "scripts" / "fetch-models.sh").read_text(encoding="utf-8")
    assert 'Section /o "Style LoRAs" SecLoras' in nsi
    assert 'StrCpy $1 "$1 -Loras"' in nsi and '"Loras" 1' in nsi and 'ReadRegDWORD $2 HKCU "Software\\$R9" "Loras"' in nsi
    assert "Download size: 3.8 GB." in nsi and "CC BY-NC 4.0" in nsi
    assert "[switch]$Loras," in setup and "if ($Loras) { $ModelFiles = @($ModelFiles) + $LoraFiles }" in setup
    assert "if ($spec.KeepIfPresent -and (Test-Path $dest)) { return }" in setup
    assert '$StyleLoras = "$HF/pshields/yue2-style-loras/resolve/main"' in setup
    windows = dict(re.findall(r"File = '([^']+)'; KeepIfPresent = \$true\n\s+Url = \"\$StyleLoras/\1\"\n\s+Sha = '([0-9a-f]{64})'", setup))
    listed = fetch.split("<<'LIST'\n", 1)[1].split("\nLIST\n", 1)[0]
    docker = dict(line.split() for line in listed.splitlines() if line.strip())
    assert windows == docker and len(windows) == 78
    loras = [name for name in windows if name.endswith(".safetensors")]
    assert len(loras) == 39 and all(name[:-len(".safetensors")] + ".txt" in windows for name in loras)
    assert not any(name.startswith(("samjac", "earthdrone")) for name in windows)   # no licence: never passed on
    assert '--loras) LORAS=yes ;;' in fetch and 'if [ -s "$dest" ]; then echo "have  $file"; continue; fi' in fetch



MOTHERSUPERIOR = {
    "ar_lora_inst_v3abc_comfyui.safetensors": "de6a11d5701df103a191c87dc73115266e2420f3834739319dec5c24d2119f31",
    "nar_lora_joint_v9_comfyui.safetensors": "cd2bf0d3ce4bf68697daa016671da7d70e34e2f5545617ab9094c96b14a581db",
    "tokenizer_head_joint_v9.safetensors": "06440f25605c6c12c4e517ef033d7b70b8d9e961b3b06aa3848b1f8028fd7eb8",
    "minted_regularizer_pack_v2.pt": "587631eec5946f9f87d4b422abcda7e35dee43299efb7b7d2fcba4cd8752c475",
}


def test_files_from_a_single_authors_account_are_fetched_from_our_copy_first():
    """The trainer's repository vanished and every fresh install stopped. The files by Mothersuperior (one person's
    account, every install needs them) are fetched from an unchanged copy first and from the author's repository if the
    copy cannot be had, on Windows and Docker alike, and either must match the same checksum."""
    import re
    ROOT = Path(__file__).resolve().parent.parent
    setup = (ROOT / "windows" / "setup.ps1").read_text(encoding="utf-8")
    fetch = (ROOT / "scripts" / "fetch-models.sh").read_text(encoding="utf-8")
    assert '$Copies = "$HF/pshields/yue2-mothersuperior-copies/resolve/main"' in setup
    assert "COPIES=https://huggingface.co/pshields/yue2-mothersuperior-copies/resolve/main" in fetch
    for name, sha in MOTHERSUPERIOR.items():
        block = re.search(r"@\{[^{}]*File = '" + re.escape(name) + r"'[^{}]*\}", setup).group(0)
        assert f'Copy = "$Copies/{name}"' in block and "Url = \"$HF/Mothersuperior/" in block and sha in block
        assert re.search(r'fetch "\$COPIES/' + re.escape(name) + r'" \\\n[^\n]+\\\n\s+"\$\w+/' + re.escape(name) + '"', fetch)
    helper = setup[setup.index("function Get-Verified("):setup.index("function Expand-Zip(")]
    assert "@(@($spec.Copy, $spec.Url) | Where-Object { $_ })" in helper   # the copy first, then the publisher
    assert "$LASTEXITCODE -eq 22" in helper                                # a refusal moves on at once
    assert helper.index("if (-not $got)") < helper.index("Move-Item -Force $part $dest")


def test_mert_is_loaded_at_a_pinned_revision():
    """MERT comes with trust_remote_code, so its Python runs in the app: loaded from main, a change on Hugging Face would
    change the tokens and run code nobody had read."""
    import re
    text = (Path(__file__).resolve().parent.parent / "app" / "tokenizer.py").read_text(encoding="utf-8")
    assert re.search(r'^MERT_REVISION = "[0-9a-f]{40}"$', text, re.M)
    calls = re.findall(r"from_pretrained\(([^)]*)\)", text)
    mert = [c for c in calls if "MERT" in c]
    assert len(mert) == 2 and all("revision=MERT_REVISION" in c for c in mert)
    assert text.count('"m-a-p/MERT-v2-FullSong"') == 1   # only in MERT_REPO: nothing loads it another way


def test_the_sources_check_reads_every_kind_of_address():
    """scripts/check-upstream.sh asks every download address whether it still answers; this checks it finds them all
    without the network: files with a checksum, our copies, the Whisper files, pinned commits and the score samples."""
    import importlib.util
    ROOT = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location("sources_report", ROOT / "scripts" / "_sources_report.py")
    report = importlib.util.module_from_spec(spec)
    import sys
    sys.modules["sources_report"] = report   # its dataclass looks itself up there
    spec.loader.exec_module(report)
    found = {s.url: s for s in report.sources()}
    assert all("$" not in url for url in found)
    copies = [u for u in found if "/pshields/yue2-mothersuperior-copies/" in u]
    assert sorted(u.rsplit("/", 1)[1] for u in copies) == sorted(MOTHERSUPERIOR)
    assert all(found[u].sha == MOTHERSUPERIOR[u.rsplit("/", 1)[1]] for u in copies)
    assert any(u.endswith("/faster-whisper-large-v3-turbo/resolve/main/model.bin") for u in found)
    assert "https://github.com/yeufonic/ComfyUI-YuE2-Trainer/commit/6a9355efff60589d93b41b569676f09d5db85d09" in found
    assert any(u.startswith("https://github.com/Comfy-Org/ComfyUI/commit/") for u in found)       # setup.ps1
    assert any(u.startswith("https://github.com/comfyanonymous/ComfyUI/commit/") for u in found)  # the Dockerfile
    assert sum("/pshields/yue2-style-loras/" in u for u in found) == 78
    assert any(u.endswith("acoustic_grand_piano-mp3/A4.mp3") for u in found)
    assert all(found[u].sha for u in found if u.endswith(".safetensors"))
