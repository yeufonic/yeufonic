# Third-party notices

Yeufonic's own code is licensed for free personal, non-commercial use (see [LICENSE.md](LICENSE.md)). It runs
models and software made by others, and each of those keeps its own terms. None of the model
weights are part of this repository: `scripts/fetch-models.sh` downloads them from their
publishers, and by using them you accept their terms. Files from a single author's account are fetched from an
unchanged copy first, so an install does not stop if the original is moved or taken down.

This page is a summary for convenience, not legal advice. Where it and a publisher's own terms
differ, the publisher's terms apply.

## Models

### YuE2-3B (plans and renders)

- By HKUST M-A-P. Weights: **CC BY-NC 4.0, with an additional creator permission**.
  Source: [m-a-p/YuE2-3B](https://huggingface.co/m-a-p/YuE2-3B), repackaged for ComfyUI as
  [Comfy-Org/YuE2](https://huggingface.co/Comfy-Org/YuE2).
- The authors' terms, from the [YuE2 repository](https://github.com/multimodal-art-projection/YuE#license):
  - **Personal users, content creators and musicians** may use YuE2 and monetise the music they
    generate, with no fees or royalties payable to the authors.
  - **Academic research and education**: free for non-commercial use.
  - **Commercial companies**: contact the authors for a commercial licence for the weights.
  - The permission excludes illegal, harmful, deceptive or unethical use.
  - Attribution such as "YuE2" or "#YuE2" is encouraged, not required.
  - YuE2 is provided as is, without warranties, and users are responsible for their inputs,
    outputs and use.
- Official licence: [YuE2 MODEL_LICENSE](https://github.com/multimodal-art-projection/YuE/blob/main/MODEL_LICENSE),
  the weights licence with the creator permission. (The repository's `LICENSE` file is Apache 2.0
  and covers YuE2's code, not the weights.)

### YuE2, SheetSage2 and MERT as GGUF (the yue2.cpp engine)

- Converted to GGUF by Serveurperso for yue2.cpp: YuE2-3B, its VAE, SheetSage2 and MERT-v2-FullSong. **CC BY-NC 4.0**,
  with the same authors' terms as the originals above and below. Source:
  [Serveurperso/YuE2-GGUF](https://huggingface.co/Serveurperso/YuE2-GGUF), fetched first from an unchanged copy,
  [pshields/yue2-gguf-copies](https://huggingface.co/pshields/yue2-gguf-copies), at a pinned revision.
- Fetched only when yue2.cpp is chosen at install (or with `fetch-models.sh --cpp`).

### SheetSage2 (transcription)

- By HKUST M-A-P. Weights: **CC BY-NC 4.0**.
  Source: [m-a-p/SheetSage2](https://huggingface.co/m-a-p/SheetSage2), repackaged in
  [Comfy-Org/YuE2](https://huggingface.co/Comfy-Org/YuE2).
- Official licence: [SheetSage2 LICENSE](https://huggingface.co/m-a-p/SheetSage2/blob/main/LICENSE)

### YuE2 instrumental LoRA (Instrumental mode)

- By Mothersuperior. **CC BY-NC 4.0**, inherited from YuE2-3B.
  Source: [Mothersuperior/YuE2-instrumental-cot-full-loras](https://huggingface.co/Mothersuperior/YuE2-instrumental-cot-full-loras).
- Downloaded from an unchanged copy, [pshields/yue2-mothersuperior-copies](https://huggingface.co/pshields/yue2-mothersuperior-copies), with the author's
  repository as the fallback; either must match the same checksum. The copy keeps the licence and credits the author.
- Its model card says nothing about monetising generated music. The YuE2 creator permission above
  comes from the YuE2 authors; check with the LoRA's author before relying on it for music made in
  Instrumental mode.
- Official licence: as declared on its [model card](https://huggingface.co/Mothersuperior/YuE2-instrumental-cot-full-loras).

### YuE2 Realaudio Tokenizer & Production LoRA (Realaudio polish & vocal identity)

- By Mothersuperior. **CC BY-NC 4.0**, inherited from YuE2-3B.
  Source: [Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4](https://huggingface.co/Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4).
- Downloaded from an unchanged copy, [pshields/yue2-mothersuperior-copies](https://huggingface.co/pshields/yue2-mothersuperior-copies), with the author's
  repository as the fallback; either must match the same checksum. The copy keeps the licence and credits the author.
- Production LoRA (`nar_lora_joint_v9_comfyui.safetensors`) enhances rendering fidelity and frequency separation.
- Audio Tokenizer head (`tokenizer_head_joint_v9.safetensors`) enables vocal token extraction in conjunction with MERT-v2.
- User consent: only use audio recordings that are your own voice or with explicit written consent from the performer.

### YuE2 hum-to-song regularizer pack (LoRA training)

- By Mothersuperior. **CC BY-NC 4.0**.
  Source: [Mothersuperior/YuE2-hum-to-song](https://huggingface.co/Mothersuperior/YuE2-hum-to-song)
  (`minted_regularizer_pack_v2.pt`). Training uses it to keep a LoRA close to the base model's
  general musicianship while it learns a corpus.
- Downloaded from an unchanged copy, [pshields/yue2-mothersuperior-copies](https://huggingface.co/pshields/yue2-mothersuperior-copies), with the author's
  repository as the fallback; either must match the same checksum. The copy keeps the licence and credits the author.
- Official licence: as declared on its [model card](https://huggingface.co/Mothersuperior/YuE2-hum-to-song).

### Gemma 4 E4B (lyric drafts)

- By Google. **Apache 2.0**.
  Source: [google/gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it), repackaged for
  ComfyUI as [Comfy-Org/gemma-4](https://huggingface.co/Comfy-Org/gemma-4).
- With yue2.cpp, the same model comes from Ollama's library as
  [`gemma4:e4b-it-qat`](https://ollama.com/library/gemma4), under the same licence.
- Official licence: [Google's Gemma 4 licence page](https://ai.google.dev/gemma/docs/gemma_4_license)

### FLUX.2 klein 4B and Qwen3 4B (take pictures, when chosen)

- FLUX.2 klein 4B by Black Forest Labs. **Apache 2.0**. Source:
  [black-forest-labs/FLUX.2-klein-4b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8).
- Its text encoder, Qwen3 4B by the Qwen team (Alibaba Cloud), and its VAE. **Apache 2.0**. Repackaged for
  ComfyUI as [Comfy-Org/Flux-2-Klein-4B](https://huggingface.co/Comfy-Org/Flux-2-Klein-4B).
- Fetched only when chosen at install (or with `fetch-models.sh --pictures`).
- With yue2.cpp, the text encoder is Qwen3 4B as GGUF, converted by Unsloth: **Apache 2.0**. Source:
  [unsloth/Qwen3-4B-GGUF](https://huggingface.co/unsloth/Qwen3-4B-GGUF), at a pinned revision.
- Official licence: [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0), as declared on each model card.

### Style LoRAs (when chosen)

- 39 style LoRAs, each its author's work, fetched only when chosen at install (or with `fetch-models.sh --loras`)
  from [pshields/yue2-style-loras](https://huggingface.co/pshields/yue2-style-loras), where they are gathered
  byte for byte as published (only the concept sliders' file names are shortened). Its README lists every file
  with its source and checksum.
- By becausereasons: [chanson française](https://huggingface.co/becausereasons/yue2-chnsn-chanson-francaise),
  [canzone italiana](https://huggingface.co/becausereasons/yue2-cnzn-canzone-italiana),
  [Bulgarian voices](https://huggingface.co/becausereasons/yue2-blgr-bulgarian-voices),
  [qawwali, sufi and tabla](https://huggingface.co/becausereasons/yue2-qwwl-qawwali-sufi-tabla),
  [militant reggae](https://huggingface.co/becausereasons/yue2-mltnt-militant-reggae). By storagejuju:
  [J-pop](https://huggingface.co/storagejuju/yue2-jpop-t4-lora). By atomtanstudio: dream pop and old school
  hip-hop, from [lora-library](https://huggingface.co/atomtanstudio/lora-library). By ntc-ai: the concept sliders,
  from [yue2-particle-sliders](https://huggingface.co/ntc-ai/yue2-particle-sliders).
- Official licence: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), as declared on each
  author's model card. Non-commercial use only.

### Whisper large-v3-turbo (hearing lyrics)

- By OpenAI, converted for faster-whisper. **MIT**. Source:
  [dropbox-dash/faster-whisper-large-v3-turbo](https://huggingface.co/dropbox-dash/faster-whisper-large-v3-turbo)
  (formerly published as mobiuslabsgmbh/faster-whisper-large-v3-turbo).
- Official licence: [MIT](https://huggingface.co/dropbox-dash/faster-whisper-large-v3-turbo), as declared on its model card.

### MERT-v2-FullSong (semantic tokens, a command-line script only)

- By HKUST M-A-P. **CC BY-NC 4.0**. Source: [m-a-p/MERT-v2-FullSong](https://huggingface.co/m-a-p/MERT-v2-FullSong).
- Not installed: `scripts/tokenize_identity.py` downloads it when run, at the revision pinned in `app/tokenizer.py`.
- Official licence: [MERT-v2-FullSong LICENSE](https://huggingface.co/m-a-p/MERT-v2-FullSong/blob/main/LICENSE)

### Demucs (stems)

- By Meta. Code and weights: **MIT**. Source: [facebookresearch/demucs](https://github.com/facebookresearch/demucs).
  Installed in the app image; the weights are downloaded on first use.
- Official licence: [Demucs LICENSE](https://github.com/facebookresearch/demucs/blob/main/LICENSE)

## Software

### ComfyUI (the engine)

- **GPL-3.0**. Source: [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI).
- It is not part of this repository. `engine/Dockerfile` builds it from its upstream source, and
  it runs as a separate container that the app talks to over HTTP.
- Official licence: [ComfyUI LICENSE](https://github.com/comfyanonymous/ComfyUI/blob/master/LICENSE)

### yue2.cpp (the other engine)

- By ServeurpersoCom. **MIT**. Source: [ServeurpersoCom/yue2.cpp](https://github.com/ServeurpersoCom/yue2.cpp),
  built on ggml (**MIT**).
- It is not part of this repository. `engine-cpp/Dockerfile` builds its server from a pinned commit with the patches
  in `engine-cpp/patches`; the ready-made image (`ghcr.io/yeufonic/yeufonic-engine-cpp`) and the Windows build are
  made from that by this repository's workflows. Each carries the licences of yue2.cpp and of what is built into it
  (ggml, cpp-httplib, yyjson, minimp3): in `/usr/share/licenses/yue2.cpp/` in the image, and in `licenses\` in the
  Windows build.
- The Windows build includes NVIDIA's CUDA runtime libraries (`cudart64_12.dll`, `cublas64_12.dll`,
  `cublasLt64_12.dll`), redistributed unchanged under the
  [NVIDIA CUDA Toolkit End User License Agreement](https://docs.nvidia.com/cuda/eula/); the images are built on
  NVIDIA's CUDA runtime images, under the same terms.
- Official licence: [yue2.cpp LICENSE](https://github.com/ServeurpersoCom/yue2.cpp/blob/master/LICENSE)

### stable-diffusion.cpp (take pictures beside yue2.cpp)

- By leejet. **MIT**. Source: [leejet/stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp), built
  on ggml (**MIT**).
- It is not part of this repository. `engine-pictures/Dockerfile` builds its server from a pinned commit (the
  ready-made image is `ghcr.io/yeufonic/yeufonic-pictures`, which carries the licences of stable-diffusion.cpp and of
  what is built into it, in `/usr/share/licenses/stable-diffusion.cpp/`); the Windows install downloads its
  published build.
- Official licence: [stable-diffusion.cpp LICENSE](https://github.com/leejet/stable-diffusion.cpp/blob/master/LICENSE)

### Ollama (Gemma beside yue2.cpp)

- **MIT**. Source: [ollama/ollama](https://github.com/ollama/ollama). Its published image (Docker) or Windows build
  is downloaded at a pinned version; it is not part of this repository.
- Official licence: [Ollama LICENSE](https://github.com/ollama/ollama/blob/main/LICENSE)

### ComfyUI-YuE2-Trainer (LoRA training)

- By speedyrulz. **Apache-2.0**.
  Source: [yeufonic/ComfyUI-YuE2-Trainer](https://github.com/yeufonic/ComfyUI-YuE2-Trainer), an
  unchanged copy of its history, kept because the original repository is no longer on GitHub.
- It is not part of this repository. `engine/Dockerfile` installs it into the engine at a pinned
  commit (unless built with `WITH_TRAINER=0`), where it trains the style LoRAs made from a corpus.

### abcjs (staff notation, and hearing a plan)

- By Paul Rosen and Gregory Dyke. **MIT**. Source: [paulrosen/abcjs](https://github.com/paulrosen/abcjs).
- Vendored in `app/static/abcjs-basic-min.js`, with its licence in
  [app/static/abcjs.LICENSE.md](app/static/abcjs.LICENSE.md), and its audio-control stylesheet in
  `app/static/abcjs-audio.css` (same package and licence; the colours in it are set again by the
  app's themes).
- **The note samples the player uses are not bundled.** It fetches them, when asked, from
  [paulrosen/midi-js-soundfonts](https://github.com/paulrosen/midi-js-soundfonts) into
  `data/models/soundfonts`, and the app serves them from there — one set per instrument the
  preview can play, about 7 MB each, and only the ones a score asks for. That repository states
  the licences of its FluidR3_GM (CC BY 3.0) and MusyngKite (CC BY-SA 3.0) sets; the `abcjs` set
  used here is a third one, with no licence stated, so it is fetched from its publisher rather
  than redistributed with this app.

### marked (the guide's renderer)

- By Christopher Jeffrey and contributors. **MIT**. Source: [markedjs/marked](https://github.com/markedjs/marked).
- Vendored in `app/static/marked.min.js` (v15.0.12), with its licence in
  [app/static/marked.LICENSE.md](app/static/marked.LICENSE.md). It renders `app/static/guide.md` in
  the browser, so the guide stays readable markdown and the image gains no dependency.

### FluidSynth (MIDI synthesis)

- **LGPL-2.1-or-later**. Source: [FluidSynth/fluidsynth](https://github.com/FluidSynth/fluidsynth).
- Used for high-fidelity offline audio rendering of MIDI files. Installed via system package manager
  in the Docker image, and fetched as official Windows x64 release binaries during Windows setup.
  On a Mac, Homebrew's is used when it is installed; it is not fetched.

### FFmpeg (decoding, encoding and measuring audio)

- **GPL-3.0** as built (with `--enable-gpl --enable-version3`). Source:
  [FFmpeg](https://ffmpeg.org/download.html).
- Not part of this repository. Installed from the system's packages in the Docker images; fetched
  during setup as the "essentials" build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) on
  Windows, and as the static arm64 `ffmpeg` and `ffprobe` from
  [Martin Riedl's build server](https://ffmpeg.martin-riedl.de/) on a Mac.

### PyObjC (the Mac app's menu-bar icon)

- **MIT**. Source: [ronaldoussoren/pyobjc](https://github.com/ronaldoussoren/pyobjc). Installed
  into the Mac app's Python during setup.

### SoundFonts (.sf2)

The application uses General MIDI SoundFonts (`.sf2`) for rendering and auditioning imported MIDI files.
None of the SoundFont binaries are part of this repository: setup scripts download them into
`data/models/soundfonts/sf2/`.

#### Arachno SoundFont 1.0

- By Maxime Abbey (Arachnosoft).
- Source: [Arachnosoft Arachno SoundFont](http://www.arachnosoft.com/main/soundfont.php) /
  [Internet Archive](https://archive.org/download/free-soundfonts-sf2-2019-04/Arachno_SoundFont_Version_1.0.sf2).
- Terms: Freeware for personal, non-commercial use. Maxime Abbey retains copyright over the SoundFont bank compilation, configuration, and custom sound design. Samples from third-party authors remain their respective property. Any commercial use or commercial redistribution requires authorization from the respective original sample authors.

#### JNS-GM 2.0 (`github_Jnsgm2.sf2`)

- By Jordi Navarro Subirana (JNS).
- Source: [wrightflyer/SF2_SoundFonts](https://github.com/wrightflyer/SF2_SoundFonts/blob/master/Jnsgm2.sf2) /
  Jordi Navarro Subirana.
- Terms: Freely distributed General MIDI soundfont bank for personal, creative, and educational musical playback.

### Python packages

- The app's packages are listed, with pinned versions, in `requirements.txt`. Each is used under
  its own licence, installed from PyPI when the image is built.
