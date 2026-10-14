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


def test_both_installers_put_the_tokenizer_head_where_the_trainer_looks():
    """The trainer lists the head from models/fs_audio, the rest of the app reads it from audio_encoders. Without a
    copy in both, a fresh install refuses to train ("not in ['(run FS_Audio Training Assets first)']")."""
    root = Path(__file__).resolve().parent.parent
    windows = (root / "windows" / "setup.ps1").read_text(encoding="utf-8")
    docker = (root / "scripts" / "fetch-models.sh").read_text(encoding="utf-8")
    assert "tokenizer_head_joint_v9.safetensors" in windows and "'fs_audio'" in windows and "Copy-Item $headFrom $headTo" in windows
    assert "models/fs_audio/tokenizer_head_joint_v9.safetensors" in docker


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


def test_the_windows_trainer_is_given_the_attention_that_runs_fast_on_windows():
    """PyTorch's Windows builds have no FlashAttention, and the trainer's enable_gqa call then runs a kernel that needs
    memory in proportion to the square of the song's length. The installer rewrites the two calls (so each query head has
    its own key/value heads), on every run, and refuses to continue if the trainer's source is not what it expects."""
    setup = (Path(__file__).resolve().parent.parent / "windows" / "setup.ps1").read_text(encoding="utf-8")
    block = setup[setup.index("$trainDir = "):setup.index("# Our own node, carried by the installer.")]
    olds = [line.split("Old = ", 1)[1] for line in block.splitlines() if "Old = " in line]
    news = [line.split("New = ", 1)[1] for line in block.splitlines() if "New = " in line]
    assert len(olds) == len(news) == 2
    assert all("enable_gqa=True" in o for o in olds)                  # the two calls that need it, matched exactly...
    assert not any("enable_gqa" in n for n in news)                   # ...and rewritten without it
    assert all(n.count("repeat_interleave(self.NH // self.NKV, 1)") == 2 for n in news)
    assert "throw" in block and ".Contains($edit.New)" in block       # a changed trainer stops setup; a patched one is left alone
    fetch = setup[setup.index('if (-not (IsDone "fs_audio-'):setup.index("$trainDir = ")]
    assert "$trainDir" not in fetch and "$edit" not in fetch          # outside the fetch's own check, so an existing install is repaired


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
    assert 'Section /o "Take pictures (FLUX.2 klein)" SecPictures' in nsi
    assert 'StrCpy $1 "$1 -Pictures"' in nsi and '"Pictures" 1' in nsi and 'ReadRegDWORD $2 HKCU "Software\\$R9" "Pictures"' in nsi
    assert "[switch]$Pictures," in setup and "if ($Pictures) { $ModelFiles = @($ModelFiles) + $PictureFiles }" in setup
    assert "'Pictures', 'CheckOnly'" in setup                # carried across the 64-bit restart
    for name, sha in (("flux-2-klein-4b-fp8.safetensors", "97ed34fe0567e436200f2faee3939b88f2b5d99f8af2a4dc16532c4245c0ccb6"),
                      ("qwen_3_4b_fp4_flux2.safetensors", "3eab03a77adb0ee5304a4e677d5c10ac22f9049c1d7c894adca4f8bb39206ca8"),
                      ("flux2-vae.safetensors", "868fe7b343cc8f3a19dbcfcafbc3d5f888802be3f89bd81b65b3621a066ce8f3")):
        assert name in setup and sha in setup and name in fetch
    assert "--pictures) PICTURES=yes ;;" in fetch
