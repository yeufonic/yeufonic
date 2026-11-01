# Choosing an engine

Yeufonic makes its songs with YuE2, and runs YuE2 on one of two engines. You choose one when you set
Yeufonic up, only that one runs, and you can switch later. Your library, your settings and your LoRAs
are the same whichever runs.

- **ComfyUI** does everything Yeufonic can do, LoRA training included. It works best with a graphics
  card with 12 GB of video memory or more.
- **yue2.cpp** is a smaller native engine, for graphics cards with less memory. It makes songs, covers
  and instrumentals, and with its two optional add-ons it drafts lyrics and draws take pictures on your
  PC too. It does not train LoRAs.

## What each one does

| | ComfyUI | yue2.cpp |
|---|---|---|
| Songs, covers and instrumentals | Yes | Yes |
| Score plans, and editing them before the render | Yes | Yes |
| Transcribing a recording into a score | Yes | Yes |
| Style LoRAs, the instrumental LoRA, production polish | Yes | Yes |
| Harmony, **Follow this structure exactly**, **Expand to full song** | Yes | Yes |
| Corpora and LoRA training | Yes | No: use LoRAs trained elsewhere, or on a ComfyUI install |
| Lyrics drafted on your PC (Gemma) | Yes | With the Gemma add-on |
| Take pictures described and drawn on your PC (Gemma, FLUX.2 klein 4B or 9B) | Yes | With the Gemma and pictures add-ons |
| An external LLM for lyrics, styles and pictures | Yes | Yes |
| Stems, and hearing the words of a recording | On the graphics card | On the processor |
| Models to download | About 19 GB, 27 GB with pictures | About 5.4 GB; 6.1 GB more for Gemma, 6.9 GB for pictures |
| The YuE2 model | Full quality (BF16), or low memory (INT8) | Near full quality (Q8); full precision or smaller sizes can be chosen |
| Video memory between jobs | Keeps its models loaded until the app unloads them | Lets go of everything after each job |

Both run the same YuE2 model and read the same scores, styles and lyrics. They differ in how they
compress and sample it, so the same score and seed make a different take on each, not the same one.
Some songs come out better on one, some on the other.

A control that needs the other engine is greyed out and says so, and **About** says which engine is
running.

## Which one to choose

- **A graphics card with 12 GB or more**, or you want to train LoRAs: **ComfyUI**.
- **A card with less memory**, or you would rather keep the graphics card free between songs:
  **yue2.cpp**. Add Gemma and pictures if you want lyrics and pictures made on your PC; without them an
  external LLM, set up in Settings, can do both.
- **Not sure?** Start with the one that suits your card and try the other later: switching keeps
  everything you have made.

## With Docker (Linux, or Windows with WSL2)

The engine is chosen by `scripts/fetch-models.sh`, which fetches its models and writes the choice to
`.env`, where every `docker compose` command reads it.

### Setting up

ComfyUI is the default:

```sh
sh scripts/fetch-models.sh                # ComfyUI, with Gemma
sh scripts/fetch-models.sh --pictures     # ... and FLUX.2 klein for take pictures
docker compose up -d --build
```

For yue2.cpp, add `--cpp`, and either add-on or both:

```sh
sh scripts/fetch-models.sh --cpp                      # yue2.cpp alone
sh scripts/fetch-models.sh --cpp --gemma --pictures   # with Gemma and take pictures
docker compose up -d --build
```

With `--cpp` the script writes `COMPOSE_FILE=compose.yml:compose.cpp.yml` to `.env`, ending in
`:compose.override.yml` if you have one (once the files are named there, Docker no longer reads the override by
itself: add it to the line if you make one later), and with an add-on
`COMPOSE_PROFILES=gemma,pictures` (the ones you chose). It fetches Gemma with Docker, so Docker must be
running.

yue2.cpp's server and the picture server are ready-made images, which `docker compose up` downloads from
GitHub's container registry (`ghcr.io/yeufonic`) the first time, a few GB that the two share most of.
They are built by this repository's own workflow, `.github/workflows/engine-images.yml`, from the
`engine-cpp/` and `engine-pictures/` folders, for every NVIDIA generation from the RTX 20 on, and each carries a
build attestation saying so, which you can check with GitHub's CLI:

```sh
gh attestation verify oci://ghcr.io/yeufonic/yeufonic-engine-cpp:<tag> --owner yeufonic
```

(the tag is the one `compose.cpp.yml` names). To build them on your PC instead, set `YUE2CPP_BUILD=1` for the
script: `YUE2CPP_BUILD=1 sh scripts/fetch-models.sh --cpp`. It adds `compose.cpp-build.yml`, and the build is
compiled for your card alone; it still takes a while.

### Switching

One command each way, then start Yeufonic again. **From ComfyUI to yue2.cpp:**

```sh
sh scripts/fetch-models.sh --cpp --gemma --pictures   # or without the add-ons you do not want
docker compose up -d --build
```

**From yue2.cpp to ComfyUI:**

```sh
sh scripts/fetch-models.sh --comfyui      # add --pictures for take pictures
docker compose up -d --build
```

The script fetches the models the engine needs, changes `.env`, and stops and removes the engine you are
leaving, so it lets go of the graphics card before the other starts. Without `--cpp` or `--comfyui` it keeps
the engine you have, so adding `--loras` later, say, changes nothing else.

The first start of an engine takes a while (ComfyUI's image is built, yue2.cpp's downloaded); switching back to
one you have used before does not.
Each engine's models stay in `models/` when you switch away, so switching back downloads nothing. To
free the space, remove them: `models/yue2cpp/`, `models/ollama/` and `models/text_encoders/Qwen3-*.gguf`
are yue2.cpp's, Gemma's and its picture encoder's; `models/checkpoints/` and
`models/text_encoders/gemma4_*` are ComfyUI's. The engine you left also keeps its Docker images
(`docker image rm yeufonic-engine` removes ComfyUI's; `docker images ghcr.io/yeufonic/*` lists yue2.cpp's).

### Settings

| In `.env` | What it does |
|---|---|
| `YUE2CPP_MODEL` | Which size of YuE2 yue2.cpp uses: `YuE2-3B-Q8_0.gguf` (the default), `YuE2-3B-BF16.gguf` (full precision, 7.2 GB), `YuE2-3B-Q6_K.gguf` or `YuE2-3B-Q5_K_M.gguf` (smaller). Set it before `fetch-models.sh --cpp`, which fetches that one |
| `YUE2CPP_CUDA_ARCH` | Only when they are built here: which generation of NVIDIA card yue2.cpp and the picture server are built for. `YUE2CPP_BUILD=1 sh scripts/fetch-models.sh --cpp` sets it to this PC's card (`89` for an RTX 40, `86` for an RTX 30), which builds far faster than for every card. A newer card still runs that build, after a slower first start; take the line out (or set it) and build again to have it at full speed |
| `GEMMA_MODEL` | The Gemma model, `gemma4:e4b-it-qat` unless set |

The FLUX.2 klein 9B is never downloaded for you (it is under a non-commercial licence): the guide's
take pictures section says where to put it, and which text encoder yue2.cpp needs for it.

## On Windows, with the installer

The installer's components page asks which engine to install, beside the model size and the optional
parts. Lyric drafts and take pictures are offered for either engine.

To switch, quit Yeufonic (right-click its icon by the clock and choose **Quit**), run the installer
again and choose the other engine. Your library, settings and LoRAs are kept.
