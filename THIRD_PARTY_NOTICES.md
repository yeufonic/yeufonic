# Third-party notices

Yeufonic's own code is licensed for free personal, non-commercial use (see [LICENSE.md](LICENSE.md)). It runs
models and software made by others, and each of those keeps its own terms. None of the model
weights are part of this repository: `scripts/fetch-models.sh` downloads them from their
publishers, and by using them you accept their terms.

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

### SheetSage2 (transcription)

- By HKUST M-A-P. Weights: **CC BY-NC 4.0**.
  Source: [m-a-p/SheetSage2](https://huggingface.co/m-a-p/SheetSage2), repackaged in
  [Comfy-Org/YuE2](https://huggingface.co/Comfy-Org/YuE2).
- Official licence: [SheetSage2 LICENSE](https://huggingface.co/m-a-p/SheetSage2/blob/main/LICENSE)

### YuE2 instrumental LoRA (Instrumental mode)

- By Mothersuperior. **CC BY-NC 4.0**, inherited from YuE2-3B.
  Source: [Mothersuperior/YuE2-instrumental-cot-full-loras](https://huggingface.co/Mothersuperior/YuE2-instrumental-cot-full-loras).
- Its model card says nothing about monetising generated music. The YuE2 creator permission above
  comes from the YuE2 authors; check with the LoRA's author before relying on it for music made in
  Instrumental mode.
- Official licence: as declared on its [model card](https://huggingface.co/Mothersuperior/YuE2-instrumental-cot-full-loras).

### YuE2 Realaudio Tokenizer & Production LoRA (Realaudio polish & vocal identity)

- By Mothersuperior. **CC BY-NC 4.0**, inherited from YuE2-3B.
  Source: [Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4](https://huggingface.co/Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4).
- Production LoRA (`nar_lora_joint_v9_comfyui.safetensors`) enhances rendering fidelity and frequency separation.
- Audio Tokenizer head (`tokenizer_head_joint_v9.safetensors`) enables vocal token extraction in conjunction with MERT-v2.
- User consent: only use audio recordings that are your own voice or with explicit written consent from the performer.

### YuE2 hum-to-song regularizer pack (LoRA training)

- By Mothersuperior. **CC BY-NC 4.0**.
  Source: [Mothersuperior/YuE2-hum-to-song](https://huggingface.co/Mothersuperior/YuE2-hum-to-song)
  (`minted_regularizer_pack_v2.pt`). Training uses it to keep a LoRA close to the base model's
  general musicianship while it learns a corpus.
- Official licence: as declared on its [model card](https://huggingface.co/Mothersuperior/YuE2-hum-to-song).

### Gemma 4 E4B (lyric drafts)

- By Google. **Apache 2.0**.
  Source: [google/gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it), repackaged for
  ComfyUI as [Comfy-Org/gemma-4](https://huggingface.co/Comfy-Org/gemma-4).
- Official licence: [Google's Gemma 4 licence page](https://ai.google.dev/gemma/docs/gemma_4_license)

### FLUX.2 klein 4B and Qwen3 4B (take pictures, when chosen)

- FLUX.2 klein 4B by Black Forest Labs. **Apache 2.0**. Source:
  [black-forest-labs/FLUX.2-klein-4b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8).
- Its text encoder, Qwen3 4B by the Qwen team (Alibaba Cloud), and its VAE. **Apache 2.0**. Repackaged for
  ComfyUI as [Comfy-Org/vae-text-encorder-for-flux-klein-4b](https://huggingface.co/Comfy-Org/vae-text-encorder-for-flux-klein-4b).
- Fetched only when chosen at install (or with `fetch-models.sh --pictures`).
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
