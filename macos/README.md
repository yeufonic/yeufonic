# The Mac app (experimental)

Yeufonic as a Mac app, for a Mac with Apple silicon (M1 or later) and macOS 14 or later. Like the
Windows installer it runs natively: no Docker, which on a Mac cannot reach the GPU, and no
administrator prompt. The engine runs on the GPU through Metal (PyTorch's MPS backend).

**It is experimental**, offered as a pre-release on GitHub and through
[yeufonic.com/macos](https://yeufonic.com/macos/). It installs and makes songs, covers and pictures on a
Mac with Apple silicon, but it is slower than on an NVIDIA card, and training does not yet work on Metal.

## What it does

1. **The disk image** holds `Yeufonic.app` and a link to Applications. Drag one onto the other.
2. **The first time it is opened**, the app opens a Terminal window and runs `setup.sh`, which
   shows its progress and opens the app again when it has finished.
   - It checks the Mac: Apple silicon, macOS 14 or later, memory (16 GB at the least; 32 GB
     recommended, since the GPU and the system share it), disk space, ports and network.
   - It then fetches the rest from each publisher, pinned, checking each file's sha256 where the
     publisher gives one:
     - uv, which installs Python 3.13 and two environments: one for the engine (ComfyUI's
       packages and torch with Metal) and one for the app (as in the app image, with the CPU
       torch and demucs for stems).
     - The ComfyUI commit `engine/Dockerfile` pins, and ComfyUI-YuE2-Trainer.
     - ffmpeg and ffprobe, static arm64 builds.
     - The models from Hugging Face: the ones the Windows installer fetches, with the same
       checksums (a test holds the two lists together), but for the low-memory YuE2, whose
       int8 kernels are CUDA's.
   - **Take pictures drawn on the Mac are an option**, asked once in that window and remembered
     for every later run: FLUX.2 [klein], about 16 GB more. A Mac takes the model and its text
     encoder at full precision, because the FP8 and FP4 files Windows uses need an NVIDIA card. The
     question says it is slow on a Mac (minutes a picture), needs 24 GB of memory at the least
     (32 GB recommended), and is experimental. To change the answer later, quit Yeufonic and run
     `bash /Applications/Yeufonic.app/Contents/Resources/setup.sh --pictures` (or
     `--no-pictures`, which fetches nothing and leaves files already there).
   - **Style LoRAs are an option too**, asked and remembered the same way: the 39 style LoRAs by their
     authors that the Windows installer and `fetch-models.sh --loras` fetch (about 3.8 GB), each with its
     description. A file already in the LoRA folder is left as it is. `setup.sh --loras` fetches them later.
   - **The engine can be yue2.cpp instead** (`setup.sh --engine yue2cpp`, kept for every later run):
     yue2.cpp's server and stable-diffusion.cpp's, built for macOS 14 on Apple silicon by
     `macos/build-cpp.sh` (published as a pre-release by `.github/workflows/engine-cpp-macos.yml`), Ollama
     for Gemma, and the GGUF files the Windows installer fetches, with the same checksums. On a Mac it
     drafts lyrics in seconds rather than minutes and draws pictures with a third of the memory, and
     renders at about ComfyUI's speed; it does not train LoRAs. The launcher starts its server, with
     Ollama and the picture server beside it where they are set up (`engine = yue2cpp` in settings.ini,
     with `gemma_port`, `pictures_port`, `yue2cpp_model` and `cpp_engine_args` as on Windows). The other
     engine's files stay, so changing back downloads nothing. Its YuE2 is Q8 (3.8 GB) unless
     `--cpp-model bf16` asks for full quality (7.2 GB, about twice the memory), kept for later runs.
   - **Recorded voices are an option as well**, asked and remembered the same way: the voice service
     (RVC and its separator) in a Python 3.12 of its own, with the torch the Windows voice service
     runs, and its models from the same places with the same checksums (about 1.1 GB, and 1.5 GB of
     packages). RVC is the commit Docker and Windows pin, with `voice/rvc-mps.patch` applied, so it
     trains and sings on the GPU; the launcher starts the service beside the app (`voice_port` in
     settings.ini, 8190) and the app shows recorded voices while it answers. `setup.sh --voices`
     adds it later.
   - Downloads resume, and a second run keeps whatever is already in place.
   - A Terminal window is used because it needs no permission: the app writes a `.command` file
     and opens it, where telling Terminal what to do would ask to control it.
3. **After an update** (a newer app dragged over this one) the app sees it is not the one that
   was set up, and runs `setup.sh` again, which adds whatever the new version needs and copies
   its engine node; everything already there is kept.

Where things are:

- The app: `/Applications/Yeufonic.app`. It holds our own files only, and nothing is written in
  it (Python's byte-compiled files go to the install's `cache/`).
- The install: `~/Library/Application Support/Yeufonic`: Python, the engine and its models,
  the tools, the library (`data/`) and `settings.ini`.
- The logs: `~/Library/Logs/Yeufonic`: `setup.log`, `launcher.log`, `engine.log`, `app.log`.

**The launcher.** The app's own program (`Yeufonic.swift`, compiled by `build.sh`) owns the icon in
the menu bar and runs `start.sh`, which sets the install up when it needs it and otherwise runs
`launcher.py --child` with the app's Python. (macOS 26 shows no icon from a program the app hands
over to, so the icon cannot be Python's.)

- **Start:** the engine and the app start together, and the page opens in the default browser as
  soon as the app answers.
- **The icon in the menu bar:** *Open Yeufonic*,
  *Show the logs*, *Restart the engine* and *Quit Yeufonic*. Quit asks only when it would stop a
  job or a training run, as on Windows. There is no Dock icon and no window of its own: the page is
  the app. Opening Yeufonic again while it runs opens the page.
- **Stopping:** quitting, logging out or shutting down stops the app and then the engine. A
  launcher that was killed outright leaves them running; the next start finds the ones it
  recorded and stops them first.
- **Problems** (a port in use, the engine stopping) are shown in an alert. `launcher.py` run from a
  terminal runs it without the menu bar, reporting there.

`settings.ini` in the install folder can change:

```ini
[yue2]
app_port = 8090
engine_port = 8188
data_dir = ~/Music/Yeufonic
; added to ComfyUI's command line after --gpu-only --use-pytorch-cross-attention
; (always given on a Mac), e.g. --cpu or --lowvram
engine_args =
; off: the trainer is written for CUDA and does not yet finish a run on Metal
training = no
; when the engine frees the GPU's memory: auto (after a picture, and whenever its work runs out), 0 never
unload_when_idle = auto
```

## Building

```bash
bash macos/build.sh
```

On a Mac this makes `macos/dist/Yeufonic-<version>.dmg`, with the app signed ad hoc (not with a
Developer ID). Anywhere else it puts the app together in `macos/dist/Yeufonic.app` and packs it
as a `.tar.gz`, to look inside; that is not something to ship.

The workflow `.github/workflows/macos.yml` does it on GitHub's Apple silicon runners, runs
`tests/test_macos.py` there, sets the install up without the models from inside the built app,
starts it, and checks that the app answers and the engine loads ComfyUI's YuE2 nodes and ours.
Those runners have Metal but too little memory for the models, so it cannot make a song. Each disk
image it builds carries a build-provenance attestation (`gh attestation verify <file> --repo
yeufonic/yeufonic`).

## Testing without the 18 GB of models

```bash
bash setup.sh --check-only
bash setup.sh --skip-models --install-dir /tmp/yeufonic-test
```

## Test plan for a Mac

Wanted: Apple silicon with 32 GB, macOS 14 or later. Each step's answer decides whether the next
is worth doing.

1. **Install from the disk image** as a user would: download it in Safari, drag it into
   Applications, open it (Gatekeeper asks, see below), let setup run. Note anything that is
   unclear on the way.
2. **A song, the default settings.** Does the plan come out, does the render finish, does it
   sound right? How long do the plan and the render take? Watch *Memory pressure* in Activity
   Monitor; save `engine.log`.
3. **If a render fails on Metal:** what the engine log says. `engine_args = --cpu` in
   `settings.ini` tells whether it is Metal or the model.
4. **The rest, in order:** the production polish (Realaudio); a style LoRA; a cover (SheetSage2
   transcription, Whisper on the CPU, stems in the engine); an instrumental; lyric drafts with
   Gemma on the Mac; Quit with a job running; an update (drag a newer build over it).
5. **Training**, only if all of that works: set `training = yes` and try a small corpus.

## Not done yet

- **Signing and notarisation.** Without a Developer ID (Apple's developer program, a yearly fee)
  macOS will not open the app at first. Choose *Done*, then *System Settings → Privacy &
  Security → Open Anyway*, and open it again.
- **FluidSynth**, which plays an imported MIDI file, has no macOS build of its own, so the setup
  fetches ours: `macos/build-fluidsynth.sh`, published by `.github/workflows/fluidsynth-macos.yml`,
  one program that needs nothing but macOS, into the tools folder.
- **The update notice** sends a Mac to the disk image named under `macos` in the site's manifest
  (`updates.json`), or to the release notes when there is none. Nothing publishes one yet.
- **No uninstaller.** Delete the app, and `~/Library/Application Support/Yeufonic` and
  `~/Library/Logs/Yeufonic` with it.
- **The GPU meter** in the header shows nothing on a Mac.
- **Intel Macs** are not supported: PyTorch no longer publishes builds for them, and they have no
  GPU it can use.
