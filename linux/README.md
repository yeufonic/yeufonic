# The native Linux installer

Yeufonic natively on Linux (`x86_64`), with no Docker, no `sudo`, and no GUI installer — everything
runs cleanly from the command line. It sits beside the Windows installer (`windows/`) and the Mac
app (`macos/`), targeting common Linux distributions (Ubuntu/Debian, Red Hat/Fedora/Rocky/AlmaLinux,
Arch, openSUSE, and native WSL2).

## What it does

1. **One self-extracting command-line installer:** `yeufonic-<version>-linux-x86_64.run` (built by `linux/build.sh`).
   It carries only Yeufonic's own files (under 5 MB), verifies its embedded payload SHA-256 before
   unpacking, and accepts optional flags:

   ```bash
   ./yeufonic-<version>-linux-x86_64.run --help
   ./yeufonic-<version>-linux-x86_64.run --install-dir ~/yeufonic-custom
   ./yeufonic-<version>-linux-x86_64.run --extract-only ./unpacked
   ./yeufonic-<version>-linux-x86_64.run --demos            # include the Starter Pack demo library (~1.7 GB; default on fresh installs)
   ./yeufonic-<version>-linux-x86_64.run --no-demos         # skip the Starter Pack on a fresh install
   ./yeufonic-<version>-linux-x86_64.run --force-downloads
   ./yeufonic-<version>-linux-x86_64.run --check-only
   ./yeufonic-<version>-linux-x86_64.run --skip-models --no-desktop
   ```

   Models, LoRAs, SoundFonts and voice files already present on disk are verified once and skipped
   on subsequent runs (just like the Windows installer), unless `--force-downloads` is passed.
   All downloads and large checksum checks show a live CLI progress bar with size, speed, and ETA.

2. **Pre-flight checks (`setup.sh`)** before anything is downloaded:
   - Linux `x86_64`, `glibc >= 2.28`, core shell utilities (`bash`, `curl`/`wget`, `tar`, `gzip`, `sha256sum`)
   - NVIDIA GPU via `nvidia-smi` (including `/usr/lib/wsl/lib/nvidia-smi` on WSL2) and `libcuda.so.1`:
     - Driver `>= 580` selects PyTorch `cu130` (with isolated CUDA 12 libraries in `engine/cuda12` for GPU Whisper)
     - Driver `525–579` selects PyTorch `cu128`
   - VRAM, system RAM, `/dev/shm` (for recorded voices), free disk space, ports (reading `settings.ini`), and network reachability
   - Optional shared library hints (`libgomp.so.1`, `libGL.so.1`, `libglib-2.0.so.0`) with distro-specific `apt`/`dnf`/`pacman`/`zypper` commands if missing

3. **Self-contained user install** (default `~/.local/share/yeufonic`, overridable via `--install-dir` or `YEUFONIC_HOME`):
   - Static musl `uv` + isolated Python 3.13 (and 3.12 when `--voices` is chosen) — system Python and PEP 668 are never touched
   - Static Linux `amd64` `ffmpeg` and `ffprobe`
   - Pinned ComfyUI + `ComfyUI-YuE2-Trainer` + `yue2_harmony` + GPU Demucs + GPU Whisper (`Yue2Hear`), or `yue2.cpp` + Ollama + `sd-server` (Phase 1)
   - App virtual environment (`requirements.txt`, CPU PyTorch, Demucs)
   - SHA-256 verified models and SoundFonts (resumable; re-running keeps everything already in place)
   - CLI entrypoint (`~/.local/bin/yeufonic`) and FreeDesktop menu entry (`~/.local/share/applications/yeufonic.desktop`) unless `--no-desktop`

## Managing an install

```bash
yeufonic                         # start Yeufonic in foreground (Ctrl+C stops it)
yeufonic start -d                # start detached in the background (also --detach / --background)
yeufonic status                  # check app and engine state
yeufonic stop                    # stop cleanly (including detached instances)
yeufonic logs app                # tail app.log (or engine, launcher, voice, setup)
yeufonic setup                   # interactively reconfigure engine, model size, or add-ons
yeufonic setup --engine yue2cpp  # switch engines directly (keeps ComfyUI's files on disk)
yeufonic setup --pictures        # add optional components directly
yeufonic setup --demos           # download and install the Starter Pack demo takes (~1.7 GB)
yeufonic uninstall               # remove Yeufonic (offers to keep data/ and models/)
```

On an existing install, the **Starter Pack** is skipped by default during updates; run `yeufonic setup --demos` (or pass `--demos` to the `.run` installer) to add it at any time. Any style LoRAs or voices already installed are skipped, and existing takes are never overwritten — the demo takes appear in a **Starter Pack** space the next time Yeufonic starts.

`settings.ini` inside the install folder overrides ports, library path, model size, and browser mode:

```ini
[yue2]
app_port = 8090
engine_port = 8188
data_dir = ~/.local/share/yeufonic/data
import_roots = ~
open_browser = yes
window = browser
unload_when_idle = auto
training = yes
model = bf16
```

## Building

```bash
bash linux/build.sh
```

The installer lands at `linux/dist/yeufonic-<version>-linux-x86_64.run` with its `.sha256` file beside it.

## Testing in an isolated folder (without touching Docker)

```bash
mkdir -p ~/scratch/yeufonic-linux-test
printf '[yue2]\napp_port = 8095\nengine_port = 8195\nopen_browser = no\n' > ~/scratch/yeufonic-linux-test/settings.ini
./linux/dist/yeufonic-*-linux-x86_64.run --install-dir ~/scratch/yeufonic-linux-test --no-desktop --skip-models
~/scratch/yeufonic-linux-test/bin/yeufonic start --no-browser
```
