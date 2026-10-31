# Choosing an engine

Yeufonic makes its songs with YuE2, and runs YuE2 on one of two engines. You choose one when you set
Yeufonic up, only that one runs, and you can switch later. Your library, your settings and your LoRAs
are the same whichever runs.

- **ComfyUI** does everything Yeufonic can do, LoRA training included. It works best with a graphics
  card with 12 GB of video memory or more.
- **yue2.cpp** is a smaller native engine, for graphics cards with less memory. It makes songs, covers
  and instrumentals, and with its two optional add-ons it drafts lyrics and draws take pictures on your
  PC too. It does not train LoRAs, and it has no Harmony control.

## What each one does

| | ComfyUI | yue2.cpp |
|---|---|---|
| Songs, covers and instrumentals | Yes | Yes |
| Score plans, and editing them before the render | Yes | Yes |
| Transcribing a recording into a score | Yes | Yes |
| Style LoRAs, the instrumental LoRA, production polish | Yes | Yes |
| Harmony above Familiar, **Follow this structure exactly**, **Expand to full song** | Yes | No: plans come from YuE2's own planner |
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

- **A graphics card with 12 GB or more**, and you want to train LoRAs or use the Harmony control:
  **ComfyUI**.
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

With `--cpp` the script writes `COMPOSE_FILE=compose.yml:compose.cpp.yml` to `.env`, and with an add-on
`COMPOSE_PROFILES=gemma,pictures` (the ones you chose). It fetches Gemma with Docker, so Docker must be
running.

### Switching

Stop Yeufonic first, while the engine it runs is still the one `.env` names, so that engine is stopped
too and does not keep the graphics card:

```sh
docker compose down
```

Then, **from ComfyUI to yue2.cpp:**

```sh
sh scripts/fetch-models.sh --cpp --gemma --pictures   # or without the add-ons you do not want
docker compose up -d --build
```

**From yue2.cpp to ComfyUI:** take the `COMPOSE_FILE=` and `COMPOSE_PROFILES=` lines out of `.env`, then

```sh
sh scripts/fetch-models.sh                # add --pictures for take pictures
docker compose up -d --build
```

The first build of an engine takes a while; switching back to one you have used before does not.
Each engine's models stay in `models/` when you switch away, so switching back downloads nothing. To
free the space, remove them: `models/yue2cpp/`, `models/ollama/` and `models/text_encoders/Qwen3-*.gguf`
are yue2.cpp's, Gemma's and its picture encoder's; `models/checkpoints/` and
`models/text_encoders/gemma4_*` are ComfyUI's. The engine you left also keeps its Docker image
(`docker image rm yeufonic-engine` removes ComfyUI's, `docker image rm yeufonic-engine-cpp` yue2.cpp's).

### Settings

| In `.env` | What it does |
|---|---|
| `YUE2CPP_MODEL` | Which size of YuE2 yue2.cpp uses: `YuE2-3B-Q8_0.gguf` (the default), `YuE2-3B-BF16.gguf` (full precision, 7.2 GB), `YuE2-3B-Q6_K.gguf` or `YuE2-3B-Q5_K_M.gguf` (smaller). Set it before `fetch-models.sh --cpp`, which fetches that one |
| `YUE2CPP_CUDA_ARCH` | Builds yue2.cpp and the picture server for one generation of NVIDIA card, which builds much faster: `89-real` for an RTX 40, `86-real` for an RTX 30 |
| `GEMMA_MODEL` | The Gemma model, `gemma4:e4b-it-qat` unless set |

The FLUX.2 klein 9B is never downloaded for you (it is under a non-commercial licence): the guide's
take pictures section says where to put it, and which text encoder yue2.cpp needs for it.

## On Windows, with the installer

> **Coming with the next Windows installer.** Until then the Windows install runs ComfyUI.

The installer's components page asks which engine to install, beside the model size and the optional
parts. Lyric drafts and take pictures are offered for either engine.

To switch, quit Yeufonic (right-click its icon by the clock and choose **Quit**), run the installer
again and choose the other engine. Your library, settings and LoRAs are kept.
