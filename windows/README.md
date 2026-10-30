# The Windows installer

A small installer (under 1 MB) for people who would rather not use Docker. It runs natively
on Windows: no Docker, no WSL and no administrator prompt.

## What it does

1. **Shows the terms** of each part (`terms.txt`) and asks whether to include Gemma, for lyric
   drafts on this PC (8 GB). If you plan on configuring Yeufonic to use your own LLM via its API
   (recommended for richer results), then you can leave this out.
2. **Copies our own files** into `%LOCALAPPDATA%\Programs\Yeufonic`: the app, our engine node,
   `setup.ps1`, `launcher.py` and the notices.
3. **Runs `setup.ps1`** in a window that shows its progress.
   - It checks the PC: Windows 10 22H2 or 11, an NVIDIA card of compute capability 8.0 or
     higher (RTX 30-series or newer, for bf16), video memory, driver, RAM, disk space, ports and
     network.
   - It then fetches the rest from each publisher, pinned, checking each file's sha256 where
     the publisher gives one:
     - ComfyUI's own Windows portable build, for its Python and CUDA torch. It takes the CUDA
       13.0 build with driver 580 or later, and the CUDA 12.6 build otherwise.
     - The ComfyUI commit `engine/Dockerfile` pins, in place of the portable's newer one.
     - ComfyUI-YuE2-Trainer.
     - uv, which installs a Python for the app and its packages (CPU torch and demucs, as in
       the app image).
     - ffmpeg and 7-Zip's `7zr.exe`.
     - The models from Hugging Face.
   - Downloads resume. A second run keeps whatever is already in place, which is also what
     **Repair** in the Start menu does.
4. **Adds shortcuts** to the Start menu and the desktop, and an uninstaller. The uninstaller
   offers to keep the library and the models; a reinstall puts the models back.

**The launcher.** The shortcuts start `Yeufonic.exe`, a small NSIS program
(`yeufonic-exe.nsi`, built by `build.sh`) that runs `launcher.py` with `pythonw` and waits.
Task Manager therefore lists *Yeufonic*, with the engine and the app beneath it.
- **Start:** the engine and the app start together. The page opens as soon as the app answers,
  in a window of its own: the app mode of the default browser when it has one (Chrome, Edge,
  Brave, Vivaldi), and otherwise Edge's, which comes with Windows (Firefox has none). Each
  browser gets a profile of its own in `browsers\`, with no sign-in, sync or extensions. The engine takes longer; the page says it is starting, and a job asked for
  meanwhile waits for it.
- **The icon by the clock:** drawn with the Windows API through `ctypes`, so there is nothing
  to install. Click it to open the window; right-click for *Open*, *Open the logs folder* and
  *Quit*. Quit always asks, and says so when a job or training would stop.
- **Closing the window** leaves Yeufonic running by the clock. The first time, a note says so.
- **The taskbar:** the launcher gives the window Yeufonic's own app ID and relaunch command,
  so it has a taskbar group of its own, and pinning it pins `Yeufonic.exe` with our icon
  rather than Edge.
- **Stopping:** the engine, the app and the window's browser run in a Windows job tied to the
  launcher, so they stop when it does, however it ends.
- **Problems** (a port in use, the engine failing) are shown in a message box, which offers
  to open the logs folder. *Yeufonic (with console)* runs `launcher.py --console`, which also
  reports to a console window.
- **Logs:** `logs\engine.log`, `logs\app.log`, how long each took to start in
  `logs\launcher.log`, and the install's own log in `logs\install.log`.

Ports, the library folder and the window can be changed in `settings.ini`:

```ini
[yue2]
app_port = 8090
engine_port = 8188
data_dir = D:\YuE2 library
; app: a window of its own (the default); browser: a tab in the default browser
window = app
; when the engine frees the graphics card's memory: auto (after a picture), 1 whenever its work runs out, 0 never
unload_when_idle = auto
```

## Building

```bash
sh windows/build.sh
```

The installer lands in `windows/dist/`.
- **On Linux or in CI**, it uses `makensis` (`apt install nsis`).
- **From WSL**, it uses the Windows NSIS zip, unpacked, with nothing installed. Set `NSIS_DIR`
  to its folder; the default is `C:\Users\Public\yue2-build\nsis-3.12`.

## Testing without the 18 GB of models

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1 -InstallDir C:\somewhere -SkipModels
powershell -ExecutionPolicy Bypass -File setup.ps1 -InstallDir C:\somewhere -CheckOnly
```

## The model size

The components page offers two sizes of the YuE2 model, full quality (BF16) and low memory (INT8), as
a choice of one. The choice is passed to `setup.ps1` as `-Int8` for the small one, remembered in the
registry for the next update, and the file that was not chosen is removed once the chosen one is in
place. The app picks whichever the engine reports (BF16 first), so there is no setting to keep in step.

## Trying an update before it is released

A test build of the installer (`TEST_BUILD=1`, which installs as "Yeufonic (test)" in a folder of
its own) can be given `TEST_MANIFEST=<url>`. The installer then writes `update_manifest` into the
install's `settings.ini`, the launcher hands it to the app as `YEUFONIC_UPDATE_MANIFEST`, and the
app asks that address only: not the site's manifest and not GitHub. Build an older and a newer
test installer (`VERSION=0.0.98` and `VERSION=0.0.99`, versions that will never be real), serve a
manifest naming the newer one, install the older one and run the update with the app open. A
release build never sets it. The steps are in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Not done yet

- **Signing.** Until the installer is signed, Windows shows *Windows protected your PC*; choose
  *More info*, then *Run anyway*. SignPath Foundation signs open-source projects for free (see
  IDEAS.md).
- **Tested on one PC only** so far. It has not been tried on a clean machine, on the CUDA 12.6
  build, or with a card below 16 GB.
- **An app already on ports 8090 and 8188** (the Docker version, say) has to be stopped first.
  The installer and the launcher both check for this.
