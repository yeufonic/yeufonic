# <img src="app/static/icon.svg" alt="" width="40" align="top"> Yeufonic

A web interface for [YuE2](https://github.com/multimodal-art-projection/YuE), the open music
model. Write a song from a prompt, or cover your own recording. Create a local LoRA trained on 
a corpus of music. Edit the score either way, then pull the stems out of the result.

- **Song from a prompt:** write a score plan from a style and lyrics, edit it, render it.
- **Choose your engine:** ComfyUI with the YuE2 nodes, or yue2.cpp (GGUF) for smaller GPUs.
- **Cover a recording:** transcribe your song, change its melody and chords, render a new version.
- **Instrumentals:** build the structure section by section, or play a recording's score.
- **Record a tune:** sing, hum or play one on an instrument, and expand a few bars into a whole song.
- **MIDI import for covers and instrumentals:** MIDI editing with piano roll and sf2.
- **Style LoRAs:** use published ones, or, with the ComfyUI engine, train your own from a folder of songs.
- **Recorded voices:** train a voice from your own singing or a corpus's singer, and have any take sung in it (Docker and Windows); see [Recorded voices](#recorded-voices).
- **Lyrics:** draft them from a sentence, or extract them from a recording.
- **Duets:** cue a man, a woman or both for any lines of the lyrics, and the melody is set where that voice sings.
- **Languages:** the app and its user guide in fifteen languages, machine-translated: English (US and UK), Simplified and Traditional Chinese, Japanese, Korean, German, Dutch, French, Italian, Russian, Spanish (Spain and Latin America) and Portuguese (Brazil and Portugal).
- **Vintage mastering rack:** a skeuomorphic channel strip with a 1073-style EQ, a seven-band parametric equalizer you shape by dragging its bands on a graph over the live spectrum, vintage compressor, stereo imager, and master limiter with tube warmth to polish and master any take in real time.
- **An MCP server (off by default):** let an AI agent such as Claude Code make songs, covers and instrumentals, try them other ways, give them pictures, gather them into playlists and tidy the library, in your own words. See [Using Yeufonic from an AI agent](app/static/guide.md#using-yeufonic-from-an-ai-agent-mcp).
- **Stems:** split any take into vocals, drums, bass and more, or into vocals and a backing track.
- **A library:** spaces, stars, and every take's settings kept so it can be made again.
- **A take panel and an editor:** the left panel shows how the selected take was made, and a large
  window, in three columns or as steps, is where takes are made and changed.
- **Song art:** Create song/album art using local models (Flux.2, Gemma), or for better quality plug in your own external LLM API
- **Windows without Docker:** an installer that sets it all up natively, for people who would
  rather not use Docker.
- **macOS (Experimental):** a disk image for Macs with Apple silicon that sets it all up natively,
  running on the Mac's GPU through Metal. It is much slower than an NVIDIA card and LoRA training
  does not work on it yet: see **[yeufonic.com/macos](https://yeufonic.com/macos/)**.
- **Example LoRAs and songs generated with Yeufonic:**  **[examples](https://yeufonic.com/examples/)**

Everything runs on one machine, in two parts: the app and the engine. With Docker they are two
containers; the Windows installer runs the same two natively. No cloud and no accounts; an
external LLM for lyrics is optional.

    browser  ->  app  (this project)                 http://localhost:8090
                   |
                   v
                 engine  (ComfyUI + the YuE2 nodes, or yue2.cpp)  owns the GPU

If you enjoy using this app, then please give it a ⭐️, and if you want to buy me a coffee, then please use [Buy Me a Coffee](https://buymeacoffee.com/dynamohum).

## What it looks like

Covering a recording: the editor window on its Score page, with the transcribed score and its chord
chart:

[![Cover a recording](docs/screenshots/cover-a-recording.png)](https://raw.githubusercontent.com/yeufonic/yeufonic/main/docs/screenshots/full/cover-a-recording.png)

The library at the window's full width with comfy cards, and the take panel on the left showing how the selected
take was made. The cards are wider, with room for more of the title and prompt; hover over a card's title, settings or
prompt to read all of it. Compact cards are what you start with, and the chevron beside the panel
folds it away:

[![Comfy layout](docs/screenshots/comfy-layout.png)](https://raw.githubusercontent.com/yeufonic/yeufonic/main/docs/screenshots/full/comfy-layout.png)

The same in the **Light** theme, one of five in Settings → Theme:

[![Light theme](docs/screenshots/light-theme.png)](https://raw.githubusercontent.com/yeufonic/yeufonic/main/docs/screenshots/full/light-theme.png)

Writing a song from a prompt, in the editor's three columns:

[![Write a song](docs/screenshots/write-a-song.png)](https://raw.githubusercontent.com/yeufonic/yeufonic/main/docs/screenshots/full/write-a-song.png)

Writing an instrumental, with the structure built section by section:

[![Instrumental](docs/screenshots/instrumental.png)](https://raw.githubusercontent.com/yeufonic/yeufonic/main/docs/screenshots/full/instrumental.png)

Mastering a take:

[![Mastering a take](docs/screenshots/mastering-take.png)](https://raw.githubusercontent.com/yeufonic/yeufonic/main/docs/screenshots/full/mastering-take.png)

Organising playlists and liked songs: gather favourite takes into custom collections, browse starred tracks, sort columns by clicking their headers, and jump directly to any track's space in the library:

[![Playlists](docs/screenshots/playlists.png)](https://raw.githubusercontent.com/yeufonic/yeufonic/main/docs/screenshots/full/playlists.png)

To hear what it makes, there are example songs in **[examples](examples/)**, made with style LoRAs
trained in the app. They play on that page, and the MP3s can be downloaded.

## What it does

- **Cover a recording.** Upload a song, transcribe it once, edit the melody and chords, render.
  Or pick a song from one of your corpora: its analysis already has the score and the words.
  A video file works too: its sound is kept as the recording.
  The transcription is cached per recording, so re-rendering skips straight to the music.
- **Hear what the recording sings.** A cover needs lyrics. **Extract lyrics** separates the vocal,
  listens to it and lays the lines under the sections of the score. It is asked for rather than
  done every time. The vocal is separated, and its words heard, on the GPU when the engine has Demucs and Whisper, otherwise on the CPU.
  Configure Yeufonic to use an external LLM for even greater accuracy.
- **Song from a prompt.** Write a score plan from style and lyrics, read it, repair it, render it.
  A new plan costs seconds, so a bad melody is cheap to discard.
- **Same tune, new words.** Change the words of a take you like, keep **Keep this tune** ticked,
  and its score is sung with them as a new take with the same seed. A new plan would be a new tune.
- **Or no score at all.** Mode's *No score* sings the words with no plan: YuE2 writes the tune and the chords as
  it sings, as the original YuE did, for a song that moves differently from a planned one.
- **Choose how adventurous the chords are.** YuE2 tends to write one four-chord loop for a whole
  song. The Harmony slider, from Familiar to Outside, pushes the planner towards chords it has not
  just used, without breaking the song's structure.
- **Instrumentals.** A third mode: style and structure in, a song with no vocal out. Build the
  structure section by section, time each section, or let YuE2 decide. Used in combination with 
  LoRA ar_lora_inst_v3abc_comfyui.safetensors by Mothersuperior. Or choose a recording, and its
  score is played, sections and all, with any sung melody played by an instrument.
- **Draft lyrics from a sentence.** Say what the song is about and pick a structure. Gemma 4
  writes a first draft in YuE2's section layout, or you can call an external LLM if you
  set one up in Settings.
- **Choose the interpretation.** Six ways to render the same score, from Tight to Wide, and
  **Variations** renders one take in the others, so you can compare them by ear.
- **Choose the voice.** Chips set female, male or duet and a voice character. YuE2 has no vocal
  parameter, so the chips write into the style text, and the take keeps the choice.
- **Fine-tune a take.** An **Advanced** panel in the editor sets, per take, the key and tempo the
  plan is moved to, the render's diffusion steps, the planner's chord habits, and the loudness and
  fade of the finished file. **Reset to defaults** puts them back.
- **Train a LoRA from your own songs.** Prepare a corpus from a folder of songs, by one artist,
  in one genre or by a few similar artists, and train a style LoRA from it. It works best in a
  song from a prompt, where the LoRA writes the tune. See Training a LoRA below.
- **Sing a take in a recorded voice.** Train a voice from recordings of someone singing — yours, sung into the
  built-in recorder, or a corpus's singer — and a take that uses it is rendered as usual, then its vocal is
  separated and sung again in that voice over the rest. Optional: it runs in its own container (see Recorded
  voices below).
- **Hear every step of a LoRA's training.** A training run keeps a checkpoint every 50 steps.
  **Checkpoints** renders the same song once on each of them, with one seed, as takes named after
  their step. Each has its own taste in melody and structure, while keeping the style and sound
  the LoRA was trained on.
- **Lean on a style LoRA.** Drop other people's trained files into `models/loras/` and pick one
  from a list, with separate strengths for the score and the sound. See Style LoRAs below.
- **Read the score three ways.** Expand opens a full size editor, with the chord find and replace
  beside it, and three views below: a chord chart, real staff notation, and the lyrics with each
  section's chords. Chord symbols sit in double quotes. Fix one everywhere with find and
  replace, or edit any single chord by hand in the score.
- **Hear a plan, and export it.** The Score window's **Notation** tab plays the plan as you have
  edited it, with the note it is on picked out and each line played with an instrument the style
  names — a guitar, a piano, strings, a synth — and drums when the style asks for them. **Download
  MIDI** saves the score for a DAW, one track for each part: the vocal and instrument lines, the
  chords with their bass, and drums when the style asks for them, each with its General MIDI instrument.
- **Record a tune of your own.** Sing or hum into a microphone (with optional autotune), or play a
  melody on an instrument such as a guitar into an audio interface, with a metronome, count-in and
  headphone monitoring (for the least delay, use your audio interface's own zero-latency monitoring
  instead). **Expand to full song** has YuE2 write a whole song around those few bars,
  your tune in every chorus, sung by the voice you choose, with words you write or draft.
- **MIDI import and audition.** Drop a Standard MIDI file (`.mid`, `.midi`) into Cover
  mode to generate different, often off-the-wall takes of original tunes. The app parses tracks into
  vocal melody, accompaniment, and chords, extracts embedded lyrics, and provides high-fidelity audio
  audition via FluidSynth and bundled General MIDI SoundFonts (`.sf2`).
- **Stems.** Extract vocals, drums, bass, other, and optionally guitar and piano, on the GPU in the
  engine's queue when it has Demucs, otherwise on the CPU. Or split into just the vocals and the
  instruments, for a backing track.
  Download them singly or as a zip.
- **Spaces.** Keep takes apart by project: a space per song, per album, or for sketches. Create,
  rename and delete spaces, and move a take from one to another.
- **A take's recipe as a file.** Save a take's words, score, seeds and settings (not its audio) as a small
  file, alone or beside the audio, and import one as a new take ready to render, on either engine: to keep a
  recipe, or to share it with another Yeufonic user.
- **Save a take as a video.** A take with a picture can be saved as an MP4 that shows the picture for the length
  of the song, which messaging apps such as WhatsApp send and play as a video rather than as a file.
- **Try more, and Compare.** Render a take again as a set of new seeds, or at other LoRA planner
  strengths, then play the ones you tick against each other from the same point in the song, with
  matched loudness and an optional blind listen.
- **Takes kept inside the take they came from.** The takes that Variations, Try more and Checkpoints
  make are kept inside the take they were made from, so a space lists songs rather than every
  render of each. A button that appears on the card once the take holds any opens them in a
  panel under it, where each is a take like any other and can be taken out to stand on its own.
- **A picture for each take.** Each new take gets a picture of the song, shown behind the take's card,
  atop the take panel and behind the editor (drawn on this PC, it waits until the song is made, so it never
  holds it up): a description is made from the title, style and opening words, with no LLM, then
  FLUX.2 klein draws it on this PC in a few seconds (an install option, and all a
  picture drawn here needs; the 9B, FLUX 3 klein and FIBO 2.0 can be added by hand) or the external LLM's image model does, and its background is taken out. The editor's **Picture** button makes a new one or goes back
  to the plain background. Without either way to draw, there are no pictures.
- **A library.** Every take keeps its score, style, lyrics, seed and settings, so it can be
  reproduced, reworked, starred or deleted. Search by title, style, lyrics or LoRA, in one space or
  all of them. Tick several cards and one button clears them all. Single keys act on the chosen take:
  mastering, edit, details, normalise, Variations, Try more, star and delete.
- **A player for reviewing takes.** A real waveform you can click to seek, previous and next through
  the library, ten second skips, repeat, speed and volume, with keyboard shortcuts.
- **Playlists and Liked songs.** Group takes into custom playlists and browse your starred songs in a
  dedicated view. Sort by title, duration, or date added, click any song title to jump straight to its
  space in the library, and play tracks directly with inline art-hover controls.
- **Audio visualizer and lyrics display.** An expandable visualizer displays real-time frequency
  bars, waveform scope, or circular frequency displays alongside a scrollable lyrics sheet view,
  with configurable colour themes — or the Yeufonic mark itself, breathing with the music.
- **Told when a newer version is out.** Every four hours the app asks its own site whether a later release
  exists — one request, nothing else leaves the computer. When there is one, a quiet pill beside the
  version and **Check for updates** in the menu offer the installer (Windows) or the two commands
  that update a Docker copy. Either can be switched off in Settings.

## Style LoRAs

A LoRA is a small file that leans YuE2 towards a sound: a genre, a tradition, a production style.
Put one in `models/loras/` and press **Rescan**, or use **Install**, and it appears in the **Style
LoRA** list in the editor's sound settings, in all three modes. **Download** hands one to someone
else. Here it is in the editor, chosen, with its strengths and its trigger word in the style:

[![Style LoRA](docs/screenshots/style-lora.png)](https://raw.githubusercontent.com/yeufonic/yeufonic/main/docs/screenshots/full/style-lora.png)

These are usually files other people have published, e.g. on Hugging Face, and
the app's job is to make them usable without knowing how they are put together:

- **Two strengths, because a LoRA has two halves.** *Planner* shapes what is played: the score
  plan — form, harmony, phrasing — and then the music a render writes from it. *Sound* shapes the audio. A file that
  holds only one half has the other strength greyed out, and a file this engine cannot load is
  named as such in the list rather than failing quietly inside a render.
- **The trigger word is handled for you.** Most of these files do very little unless the style text
  starts with the word they were trained on. Choosing a LoRA puts its trigger at the front of the
  Style, switching swaps it, and None takes it away.
- **Each one says what it is.** The list is grouped by publisher, and every entry carries its
  author's own description and suggested strengths, on the option and in a tooltip. A LoRA of your
  own gets the same by writing a `.txt` beside it: first line the name, a `Trigger:` line, then the
  description.

The [user guide](app/static/guide.md#style-loras) has the detail, including links to third-party LoRAs
that you can import to Yeufonic.

## Recorded voices

A recorded voice is a singer's voice, trained from recordings of them singing: yours, or a corpus's singer. Open
**Voices** from the menu to make one, then choose it in the editor's **Recorded voice** field, in all three modes. A
take that uses it is rendered as usual; then its vocal is separated from the backing, sung again in the voice, and
mixed back in. Here is a voice of someone's own recordings, trained, with its settings and what it learned from:

[![Recorded voices](docs/screenshots/voices.png)](https://raw.githubusercontent.com/yeufonic/yeufonic/main/docs/screenshots/full/voices.png)

It is optional. With Docker it runs in a container of its own beside the engine:

```sh
sh scripts/fetch-models.sh --voice      # about 1.1 GB into models/voice/
echo COMPOSE_PROFILES=voice >> .env
docker compose up --build
```

- **Your own voice, or a corpus's singer.** **New voice** makes either a voice of recordings or one trained on a
  corpus's songs. A voice of recordings gathers them on its page: **Record…** opens the built-in recorder and adds
  each take as it is sung, never autotuned; **Upload…** takes audio files; **From the library…** adds recordings
  you already have, such as a vocal you recorded for a cover, without copying them. About ten minutes of singing
  across your range is plenty, and the page counts it up.
- **Only what needs separating is separated.** Each recording says whether it is a voice alone or a song with a
  backing. A voice alone, such as one sung into the recorder, is used as it is, which is quicker and gives a
  cleaner voice; a song is separated with BS-Roformer first.
- **Settings that belong to the voice, and to the take.** **Octave** moves the voice up or down for a singer whose
  range is far from the take's, **Vocal level** and **Instrument level** set the balance of the remix, and
  **Likeness** how closely it keeps to the singer's own sounds (higher sounds more like them, and can sound more
  processed). They are the voice's defaults on its page; the editor shows them under the voice, to change for one
  take, and a take file carries them.
- **Training waits its turn on the GPU**, as a LoRA's does, and shows its progress in the job pill. Settings →
  *Voice Training* sets how much singing a voice learns from and for how many passes; the batch follows the GPU's
  memory. **Download voice** saves a trained voice to give to someone, and **Import a voice…** adds one, or an RVC
  model from elsewhere (a `.pth`, or a zip with its index).

The result is a converted vocal over a separated backing, so it does not sound as seamless as a vocal YuE2 sang
itself; clean, dry recordings give the cleanest voice. In the Windows install it is a component of the installer,
**Recorded voices**, rather than a container. It is not on macOS yet.

## Training a LoRA

Open **Corpora** from the menu. The app prepares a **corpus**: a folder of songs. Typically this
would be of an artist or genre to use when training your LoRA. Each track gets its vocal
separated, its key, tempo and sections found and its lyrics drafted. You then export it as a
training set, and train a style LoRA from it. **Run all** does the three one after the other, for
a big corpus you would rather not wait on. Training holds the GPU until it finishes, and the
LoRA appears in the Style LoRA list, with a style chip for each song it learned from. Training
also saves a checkpoint every 50 steps, folded under its LoRA in the list, and a corpus's **Edit**
form lists them run by run, with their sizes, to delete the ones you don't need. Each gives its own
take on the style. With the LoRA chosen, **Checkpoints** beside **Delete LoRA** makes what the
panel would make once on each of them, with one seed, so you can compare them by ear. To save the
space, **Training checkpoints** in Settings can delete them when training ends. To share a LoRA, press **Download** under the picker: the zip carries
its chips, and the other person adds it with **Install**.

Your corpora, one corpus per artist or genre:

[![Corpora](docs/screenshots/corpora.png)](https://raw.githubusercontent.com/yeufonic/yeufonic/main/docs/screenshots/full/corpora.png)

One corpus, analysed, exported and trained, with each song's key and tempo:

[![A corpus](docs/screenshots/corpus.png)](https://raw.githubusercontent.com/yeufonic/yeufonic/main/docs/screenshots/full/corpus.png)

It does most in a song from a prompt, where the LoRA writes the tune. It usually works best with Planner and Sound up to
about 0.70 but experiment to find the sweet spot and save them as a default for the LoRA. In a cover your recording sets the melody, so
you may keep Sound nearer to 0.50. The [user guide](app/static/guide.md#corpora-and-training-a-lora) walks
through it.

Every analysed song in your corpora is ready to cover: pick it from the recording list, choose a
LoRA, and render, with no transcribing or lyric extraction to wait for. The style fills in with
the one the song was learned with. See
[Covering a song from a corpus](app/static/guide.md#covering-a-song-from-a-corpus).

Training on the recommended full-quality (BF16) model needs about 12.5 GB of GPU memory, most of
it while it prepares the songs (the low-memory INT8 model trains in about 6 GB), and the Train window
warns when less is free.

How many steps a run trains for, and how much it can learn, can be changed: see
[Environment variables](#training).

It is on by default. `TRAINING_ENABLED: "0"` on the app takes it out, and `WITH_TRAINER=0` leaves
the trainer out of the engine image.

## On Windows, without Docker

A small installer sets Yeufonic up natively on Windows.
It needs no Docker, no WSL and no administrator rights. Running a newer installer will automatically update an existing
installation, and running it again is also how you change the model size (below).

**You need:**

- Windows 10 22H2 or Windows 11, 64-bit.
- An NVIDIA graphics card, RTX 30-series or newer, with a recent driver. 12 GB of video memory is
  recommended, and 8 GB works for making songs (with 6 GB or less, choose the low-memory model: see
  [Choosing a model size](https://github.com/yeufonic/yeufonic#choosing-a-model-size)). Training a LoRA can
  need more VRAM: about 12.5 GB free while it prepares the songs, so 16 GB is the practical minimum
  when using the recommended BF16 model. An 8 GB card can be used for training if the INT8 model is
  chosen at installation time. AMD and Intel graphics are not supported.
- 16 GB of RAM and about 30 GB of free disk, more as your library grows.
- An internet connection for about 27 GB of downloads (23 GB with the smaller low-memory model, see
  [Choosing a model size](#choosing-a-model-size)), most of it the models. The score preview
  fetches its own note samples as they are played, about 7 MB for each instrument.

The installer checks all of this before it downloads anything.

**Installing:**

1. **Download** `Yeufonic-Setup-<version>.exe` from the
   [latest release](https://github.com/yeufonic/yeufonic/releases/latest).
2. **Run it.** The installer is not signed yet, so Windows may say *Windows protected your PC*.
   Choose *More info*, then *Run anyway*.
3. **Choose your options:**
   - Accept the terms.
   - Choose the **engine**: *ComfyUI* (the default) does everything, LoRA training included; *yue2.cpp*
     is smaller, for graphics cards with less memory, and does not train LoRAs.
     [Choosing an engine](#choosing-an-engine) says how to decide. To switch later, run the installer
     again and choose the other: your library, settings and LoRAs are kept.
   - Choose the **YuE2 model size**: *Full quality* (the default, and what we recommend) or *Low
     memory*, a smaller model for graphics cards with little video memory. To change your mind later,
     run the installer again and pick the other on this page; it downloads the new one and keeps the
     old, so changing back downloads nothing. These are ComfyUI's sizes: with yue2.cpp they are greyed
     out. [Choosing a model size](#choosing-a-model-size) says how to decide.
   - Choose whether to include **Lyric drafts (Gemma 4)**. Leave it out if you will set up an
     external LLM; that saves a download of 8 GB (6 GB with yue2.cpp).
   - Choose whether to include **FLUX.2 [klein]**, unticked to begin with. It draws a
     picture of each take on this PC, about 8 GB to download. Leave it out if your external LLM can
     draw them (Gemini can), or if you do not want pictures.
   - Choose whether to include **Style LoRAs**, unticked to begin with: 39 style LoRAs by their
     authors (chanson, canzone, Bulgarian voices, qawwali, militant reggae, J-pop, dream pop, old school
     hip-hop and 16 concept sliders), each with its trigger word and suggested strengths, 3.8 GB to
     download. They are CC BY-NC 4.0; [their repository](https://huggingface.co/pshields/yue2-style-loras)
     credits each author.
   - Choose whether to include **Recorded voices**, ticked to begin with: train a singer's voice from
     recordings, your own or a corpus's songs, and have a take sung in it (see [Recorded voices](#recorded-voices)).
     About 4 GB to download; untick it if you will not use it.
   - Keep or change the folder. The default is `%LOCALAPPDATA%\Programs\Yeufonic`.
4. **Wait for setup.** A setup window checks the PC, then downloads each part from its own
   publisher and checks it against its published checksum. The window may open behind the
   installer. If a download breaks off, run the installer again: it carries on from where it
   stopped.
5. **Start Yeufonic** from the Start menu or the desktop. It opens in a window of its own within a
   few seconds, while the engine finishes starting. Its icon sits by the clock: click it to open
   the window, and right-click it to quit. Closing the window leaves Yeufonic running there, so
   a render or training carries on. *Yeufonic (with console)* in the Start menu starts it with a
   window that reports as it goes, for when something needs diagnosing.

**Ports and folders:** a `settings.ini` in the install folder changes them. Create it with a
`[yue2]` section and only the lines you need, then start Yeufonic again:

```ini
[yue2]
app_port = 8090
engine_port = 8188
data_dir = D:\YuE2 library
import_roots = D:\Music
open_browser = yes
window = app
engine_args = --disable-dynamic-vram
unload_when_idle = auto
```

`engine_args` adds switches to the command that starts the engine (ComfyUI), for when it misbehaves on a particular PC;
its own `--help` lists them. Leave it out unless you need it. `cpp_engine_args` does the same for yue2.cpp, whose
switches are different: an install switched from ComfyUI keeps its `engine_args` for switching back, and yue2.cpp
does not see them.

`unload_when_idle` says when the engine is asked to free the graphics card's memory. `auto` (the default)
frees it after a take's picture, so FLUX.2 klein does not stay loaded under your songs and other programs;
`1` also frees it whenever the engine's work runs out, at the cost of loading the song model again for the
next take; `0` never frees it.

`data_dir` is where the library lives (by default, `data` in the install folder). `import_roots`
is the folders a corpus may be built from, separated by commas (by default, your user folder).
The window is your default browser's app mode when it has one (Chrome, Edge, Brave or Vivaldi),
and otherwise Microsoft Edge's, which comes with Windows. Either way it uses a profile of its own,
so none of your browsing comes into it. `window = browser` opens Yeufonic as an ordinary tab in
your default browser instead.
Other settings are environment variables: see [Environment variables](#environment-variables).

**Updating:** run a newer installer over the top. It says it is an update, keeps the models and
your library, and fetches only what has changed. The app tells you when there is a newer release:
the pill beside the version hands you the installer for it.

**Uninstalling:** use *Settings → Apps*. It asks two things:
- **Keep your library?** Your songs, takes, corpora and LoRAs. Yes unless you say otherwise.
- **Also keep the downloaded models?** It shows their size. No unless you say otherwise, so the
  space is freed.

Anything kept stays in the install folder, and installing again finds it there, so kept models
are not downloaded again. Deleting that folder removes it.

**If something goes wrong:**
- **Logs:** the `logs` folder inside the install folder holds `install.log`, `engine.log` and
  `app.log`, and with yue2.cpp `gemma.log` and `pictures.log` for its add-ons.
- **Repair:** *Repair Yeufonic* in the Start menu runs the setup again.
- **Docker at the same time:** a Docker copy of Yeufonic uses the same ports and the same GPU,
  so stop one before starting the other.

## Requirements

- On Windows or Linux, an NVIDIA GPU with 12 GB of VRAM or more is recommended, with 16 GB of system RAM. An 8 GB card
  is worth trying: ComfyUI moves what does not fit into system RAM, so it still works, though
  smaller cards are usually slower chips and renders take longer. Training a LoRA locally needs
  more: If using BF16 then about 12.5 GB of VRAM free while it prepares the songs, so 16 GB of GPU
  VRAM and 32 GB of system RAM is the practical minimum (the engine stages the 11.5 GB YuE2 weights
  and dataset caches in host memory; on WSL2, set `memory=32GB` in `.wslconfig`). An 8 GB card
  can be used to train LoRAs if you are using the INT8 model. Regardless, you can always use
  LoRAs that have been trained elsewhere. These figures are ComfyUI's: for a card with less memory,
  the yue2.cpp engine is the one to choose (see [Choosing an engine](#choosing-an-engine)).
- Docker with the NVIDIA container toolkit, so containers can see the GPU.
- An NVIDIA driver that supports CUDA 13.0: the top line of `nvidia-smi` says `CUDA Version: 13.0` or higher.
  With an older driver, put `TORCH_CUDA=cu128` in `.env` before building the engine. Everything works on it,
  but the low-memory model is much slower (see [Choosing a model size](#choosing-a-model-size)). That is
  ComfyUI's: yue2.cpp's ready-made images need CUDA 13.0.
- About 30 GB of disk with ComfyUI (less with yue2.cpp), more as your library grows.
- Linux, or Windows with WSL2 or Docker Desktop. WSL2 is what this was built on; Windows with
  Docker Desktop needs a few settings, below.  Alternatively, on Windows, [the installer](#on-windows-without-docker) needs none of this.
- Display resolution minimum 1920x1080, though Yeufonic works best with higher resolution displays
- The macOS build has been tested on a Mac mini with an M4 and 24 GB of RAM, and found usable; a Pro or Max chip should give better results.

## Choosing a model size

YuE2 comes in two sizes for ComfyUI (yue2.cpp has its own, described in
[docs/ENGINES.md](docs/ENGINES.md)). An install has one of them: **full quality** (BF16, 7.8 GB), which is what
we recommend, or **low memory** (INT8, 4.0 GB), a smaller copy for graphics cards with little video
memory. The Windows installer asks which on its components page; with Docker, `sh scripts/fetch-models.sh`
fetches full quality and `sh scripts/fetch-models.sh --int8` the low-memory one; the app uses whichever
is in `models/checkpoints`, so that is all the choosing there is. With both files there it uses full quality,
and `YUE2_CHECKPOINT=int8` in `.env` picks the other, so a Docker install can keep both and switch (restart
with `docker compose up -d`). On Windows, to change later, run the installer again and choose differently
(the one you leave is kept, so changing back downloads nothing). The Settings page doesn't switch it, and **About** says which is in use.

| | Full quality (BF16) | Low memory (INT8) |
|---|---|---|
| Download | 7.8 GB | 4.0 GB |
| Video memory a render adds | about 8 GB | about 5 GB |
| LoRA training | yes (recommended) | yes (with the INT8 model) |
| Sound | the model as released | a compressed copy; in our listening it sounded fine, with and without the production polish decoder |

**What to expect.** We timed one short song on one PC: an RTX 4070 Ti SUPER (16 GB) on a PCIe 3.0 x16
link with 64 GB of RAM, using the Windows install's engine (CUDA 13.0). To see what smaller cards would
do, the rest of the card's memory was held back so that only the amount below was free. These are single
runs, so read them as a comparison between the two columns, not as figures for your PC.

| Video memory free to the engine | Full quality: write the plan, then render | Low memory: write the plan, then render |
|---|---|---|
| plenty (about 13 GB) | 10 s, then 32 s | 10 s, then 27 s |
| about 6 GB, an 8 GB card with Windows running | 10 s, then 32 s | 10 s, then 28 s |
| about 5 GB, a 6 GB card | 182 s, then 305 s | 10 s, then 29 s |

- **A card with 8 GB or more** ran the full-quality model at full speed here. The engine moves what
  does not fit into system RAM, and a PC with plenty of RAM does that cheaply. A PC with less RAM, or
  slower RAM, may slow down sooner.
- **Around 5 to 6 GB free** the full-quality model slowed ten-fold or more, and the low-memory model
  did not. That is what it is for.
- **Speed depends on the software around the model.** The low-memory model needs PyTorch built for
  CUDA 13.0, which both the Windows install and the Docker engine use. On an engine built for CUDA 12.8
  (`TORCH_CUDA=cu128`, for an older driver) it rendered about four times slower than full quality in an
  earlier test on the same card, and **About** says so.
- **The LoRAs** (the instrumental one, the production polish decoder, and style LoRAs) are applied on
  top of either model. A style LoRA and the polish decoder ran without error on the low-memory model;
  we have not compared how they sound.

Our advice: use full quality if your card has the room, and try low memory if renders are slow or
run out of memory.

## Choosing an engine

YuE2 runs on one of two engines, chosen when you set up. **ComfyUI** is the default and does everything on
this page. **yue2.cpp**, a smaller native engine, is for graphics cards with less memory: it makes songs,
covers and instrumentals, and with its add-ons drafts lyrics and draws take pictures on your PC, but it does
not train LoRAs. [docs/ENGINES.md](docs/ENGINES.md) has a table of what each one
does, how to choose, and how to switch: on the Windows installer's components page, or with Docker
(`sh scripts/fetch-models.sh --cpp`).

## Quick start

```sh
git clone https://github.com/yeufonic/yeufonic.git
cd yeufonic
sh scripts/fetch-models.sh          # about 19 GB, and creates the folders below
# sh scripts/fetch-models.sh --int8   # the smaller low-memory model instead: see Choosing a model size
# sh scripts/fetch-models.sh --cpp    # the yue2.cpp engine instead (5.4 GB): see Choosing an engine
# sh scripts/fetch-models.sh --pictures   # also FLUX.2 klein (8.3 GB), to draw take pictures here
# sh scripts/fetch-models.sh --loras      # also 39 style LoRAs by their authors (3.8 GB, CC BY-NC 4.0)
docker compose up -d --build
```

Then open <http://localhost:8090>.

With ComfyUI, the engine's own ComfyUI page is at <http://localhost:8189> (on Windows, <http://localhost:8188>),
on this machine only and with no login. It's the same engine and GPU the app uses: a job run there
shows in the app's queue as coming from outside and holds up the app's own, and its History shows
every graph the app sent. The guide says more. With yue2.cpp, the same address is yue2.cpp's own test page.

### Build options

These need a rebuild rather than a setting.

| Build arg | Default | What it does |
|---|---|---|
| `WITH_TRAINER` | `1` | on the **engine** service. Builds in the LoRA trainer; `0` leaves it out, and Corpora is hidden. See Training a LoRA above |
| `YUE2_TRAINER_REF` | pinned commit | which commit of ComfyUI-YuE2-Trainer to use, if it is included |
| `COMFYUI_REF` | pinned commit | which commit of ComfyUI the engine is built from. See Contributing for how far it has drifted |
| `TORCH_CUDA` | `cu130` | on the **engine** service: PyTorch's CUDA build. `cu130` needs a driver that supports CUDA 13.0; `cu128` runs on older drivers, with the low-memory model and Gemma much slower. Read from `.env` (`TORCH_CUDA=cu128`), so an update never changes it |
| `CUDA_ARCHITECTURES` | every recent card | only when yue2.cpp's two servers are built here rather than downloaded ready-made (`YUE2CPP_BUILD=1 sh scripts/fetch-models.sh --cpp`): which NVIDIA GPU generations to build for. The script sets `YUE2CPP_CUDA_ARCH` in `.env` to this PC's card (`89` for an RTX 40), which builds much faster than every card |
| `YUE2CPP_REF` | pinned commit | on the **engine-cpp** image, built here: which commit of yue2.cpp to build, with the patches in `engine-cpp/patches` |

They are set under `build: args:` in `compose.yml`, or passed on the command line:

```sh
docker compose build --build-arg WITH_TRAINER=0 engine
```

The fetch script also creates `data/` and `engine-state/output/`. Let it, rather than leaving them
to Docker: a folder Docker creates for a mount belongs to root, and the app then cannot write its
library there. On Linux it also writes your user and group ids to `.env`, as `APP_UID` and
`APP_GID`, and the app runs as them, so what it writes belongs to you. Without them it runs as
1000:1000. To set them by hand, put your `id -u` and `id -g` in `.env`:

```sh
APP_UID=1000
APP_GID=1000
```

The app is published on port 8090. To use another, set `APP_PORT` in the same `.env`, say
`APP_PORT=8095`; the address the engine prints at start-up follows it.

An install from before these settings wrote its files as 1000:1000. After setting them, give those
files to your user and group, then run `docker compose up -d`:

```sh
sudo chown -R "$(id -u):$(id -g)" data engine-state/output
```

The models are YuE2 (plans and renders), SheetSage2 (transcription), Gemma 4 E4B (lyric drafts),
the YuE2 instrumental LoRA, and the Realaudio decoder LoRA and tokenizer head; with `--pictures`,
FLUX.2 klein 4B with its text encoder and VAE as well; with `--loras`, the style LoRAs. Fetched later, the engine sees them at once:
no restart.

Only localhost is published, and **there is no login**: anyone who can reach the port can use the
app. To reach it from other machines, put it behind something that authenticates, and add the
name or address you use to `ALLOWED_HOSTS` in compose.yml, or the app refuses the request. See
Other ways to run it below.

### Windows with Docker Desktop

Docker Desktop runs the containers in the same WSL2 Linux system as WSL itself, so the app runs
the same way. The setup around it needs care:

1. **Use the WSL 2 engine.** In Docker Desktop, *Settings → General → Use the WSL 2 based engine*
   must be on. The older Hyper-V engine cannot reach the GPU.
2. **Turn on WSL integration** for your distribution, in *Settings → Resources → WSL
   Integration*, then open a new terminal. Without it, `docker` in a WSL terminal cannot see
   Desktop's daemon. If Docker is also installed inside WSL, `docker info --format
   '{{.OperatingSystem}}'` says which one you are talking to: Docker Desktop names itself, the
   other names the distribution.
3. **Install a current NVIDIA driver** for Windows. It includes WSL support; nothing is installed
   inside Linux. Check with `docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi`,
   which should print the card, with `CUDA Version: 13.0` or higher at the top (see Requirements if not).
4. **Give WSL enough memory.** It is capped at part of the PC's RAM: a render needs about
   14 GB, and **LoRA training needs 32 GB** (so the engine can stage the 11.5 GB YuE2 weights
   and training caches in host RAM without the Linux kernel OOM-killing the container). Create
   `%UserProfile%\.wslconfig` with:

   ```ini
   [wsl2]
   memory=32GB
   ```

   Set it to at least 14 GB for rendering or 32 GB for LoRA training (up to your RAM less 2 GB),
   then run `wsl --shutdown` and start Docker Desktop again.
5. **Clone inside WSL, not on C:.** Open a WSL terminal (Ubuntu from the Store is the usual one)
   and run the quick start there. A clone on `C:\` works, but the 19 GB of models and the library
   then cross a slow bridge into Linux, and SQLite's locking is less dependable across it.
6. **Run the fetch script in that WSL terminal**, or in Git Bash. PowerShell and Command Prompt
   cannot run `sh`.

The repository forces Unix line endings, so a clone on Windows keeps its scripts runnable. If
`sh scripts/fetch-models.sh` still reports `$'\r': command not found`, the clone was made with a
setting that overrides it: clone again from the WSL terminal.

## Updating

```sh
git pull
docker compose up -d --build
```

On Docker Desktop (Windows), run it in your WSL terminal, inside the Yeufonic folder. First check that
`docker info --format '{{.OperatingSystem}}'` says *Docker Desktop*. If it names your Linux distribution,
`docker` is talking to a different engine, and the update would rebuild there.

The database migrates itself on the first start. Read the release notes for anything to do by
hand, such as a new setting in `compose.yml`.

If you have installed the standalone Windows app then running a newer release will update the existing
installation and not require any downloading of existing models.

## Moving from YuE2 Studio

Yeufonic is YuE2 Studio renamed, so your library, settings, LoRAs and models come across as
they are.

**On Windows,** run the Yeufonic installer. It finds YuE2 Studio and updates it where it is,
in its own folder, and replaces its shortcuts and Apps list entry with Yeufonic ones. Nothing is
downloaded again except what has changed.

**With Docker,** clone Yeufonic beside your YuE2 Studio folder and move your things across:

```sh
cd YuE2gen-studio && docker compose down && cd ..
git clone https://github.com/yeufonic/yeufonic.git
cd yeufonic
sh scripts/migrate-from-yue2studio.sh ../YuE2gen-studio
docker compose up
```

The script moves `data/`, `models/`, `engine-state/` and your `compose.override.yml`. It reuses
the engine image rather than building it again. Once Yeufonic has started with your library,
the YuE2 Studio folder can be deleted.

## Using it

The **[user guide](app/static/guide.md)** covers everything the app does, organised by what you are
trying to do: writing a song, covering a recording, instrumentals, voices, style
LoRAs, stems, the library and what to do when something is wrong.

It is also in the app itself, under the menu in the top left, or at
<http://localhost:8090/guide> — which is where it is most useful, since trigger words and LoRA
strengths are things you need while working in the editor.

How it is built — the two containers, how the app drives ComfyUI, what YuE2 does inside it, the
LLMs and the API, with diagrams — is in **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## Settings

Press **Yeufonic** in the top left. The settings are stored on the server, so they follow you to
any browser and survive a rebuild.

| Setting | What it does |
|---|---|
| Output audio format | FLAC (the default), WAV, or MP3 at 320 kbps. The format stems start with; they can choose another at the time. A take's **Save** starts with what it saved last |
| Language | The language of the app's words: the browser's language (the default, the nearest of the fifteen), or one of English (US), English (UK), 简体中文, 繁體中文, 日本語, 한국어, Deutsch, Nederlands, Français, Italiano, Русский, Español (España), Español (Latinoamérica), Português (Brasil) or Português (Portugal). The translations are machine-made. Your titles, styles and lyrics stay as you wrote them. The guide follows the language where it has been translated, also by machine. The page reloads to change it |
| Theme | Dark (the default), Light, Match the computer (dark or light, as the system is), Studio (warm and dark) or High contrast |
| Normalise to | How loud a normalised take is made: −16, −14 (the default) or −11 LUFS |
| MCP server | Off by default. Turn it on to let an AI agent on this computer use Yeufonic: see [Using Yeufonic from an AI agent](app/static/guide.md#using-yeufonic-from-an-ai-agent-mcp) |
| Stem separation model | Which model a run starts with |
| Use the GPU for stems and lyrics | On by default. Separating a vocal and hearing its words run on the engine's GPU when it has Demucs and Whisper, in its queue beside renders; off, or while a LoRA trains, the CPU does them. With yue2.cpp the CPU always does them |
| Stem save folder | Where stems are written. It must sit inside the data folder |
| Take pictures | On by default, where something can draw them: FLUX.2 klein, chosen at install, or an external LLM whose provider lists an image model. **Drawn by** chooses between the two (this PC first, as it costs nothing), **Described by** what writes the image prompt, from the take's title, style and words an **Art style** and, if you like, **Your own prompt** to lead it (Gemma on this PC by default where it is installed, else the take itself with no LLM; or the external LLM), and **Image model** which of the provider's models draws, when it draws. **Only when asked** makes none by itself, and one can still be made for any take; **No pictures** where nothing can draw, saying how to have them |
| External LLM & Lyrics | Choose between Local Gemma on GPU or an external OpenAI-compatible API for lyric drafting, corpus analysis, and audio transcription. Avoids GPU VRAM overhead. An API without billing applied (such as Google Gemini's free tier) is recommended if available to avoid usage charges |
| Storage | Opens the Storage window (below). It also holds three settings: **Training checkpoints**, kept by default or deleted when training ends; **Working copies of corpus songs**, removed when a song's analysis ends by default; and **Training sets**, kept by default or removed when training ends |

A settings sheet is generated from a specification on the server, so a new setting is a
server-side change only.

### Storage

A corpus takes a lot of room, and some of it is not needed again. **Settings → Storage** shows where the
space is (takes, corpora, recordings, stems, voices, LoRAs, the models, the engine's folders) and, for each corpus,
what it holds. Above that it lists what can be **given back**: files Yeufonic made along the way and can make
again. Each item says what it is and what removing it costs, and nothing is removed until you tick it and
confirm. What it can list:

- **Working copies made while analysing songs.** Copies for the engine to read (the song with its tags
  stripped, a padded copy for the transcriber, a short clip for its style). Removing them costs nothing;
  they are made again if the song is analysed again.
- **Copies already uploaded to the engine**, and the engine's copies of finished training sets. Also
  nothing you would notice.
- **A corpus's training set.** Its songs written again as lossless FLAC, larger than the originals.
  The LoRA trained from it is unaffected and stays in the Style LoRA list; only training that corpus again
  needs the set, so you press **Export** to write it again first, which takes a few minutes.
- **A corpus's training checkpoints.** The stages a training run saved along the way. Each is an entry in the
  Style LoRA list that you can pick for new takes. Removed, those entries disappear from the list and can no
  longer be chosen; the finished LoRA stays and keeps working.
- **Separated vocals saved as WAV.** Songs analysed now keep their separated vocal as FLAC, which is the same
  audio in about half the room. A **Convert to FLAC** button does the same for the WAVs you already have: it
  converts each one, checks that the FLAC decodes to exactly the same audio, and only then removes the WAV
  (one that does not check out is left as it was). It runs in the background and can be stopped.
- **What a voice learned from.** Each song's separated vocal and the excerpts a recorded voice trained on, kept
  to listen to on its page. The voice does not need them; its own recordings are not touched.

Your takes, your songs, your recordings, the finished LoRAs and the models are never listed for removal. A corpus that is training, being exported or being analysed is shown but cannot be
touched until it has finished. The window also lets you choose what is tidied **automatically**: working
copies are removed as each song's analysis ends (on by default, since nothing reads them again), and you can
have the training set removed when training ends, the checkpoints deleted when training ends, and what a voice
learned from removed when it has trained (all off by default). A voice that uses a library recording points at it
rather than keeping a copy.

Docker keeps its own images and build cache outside the project, so the Storage window does not cover them;
`docker system df` shows what they take.

## Things worth knowing about YuE2

- **Both nodes must be on `full` mode to keep a chord progression.** SheetSage2's `melody` mode
  strips chord symbols, and YuE2 then invents its own harmony. `melody` is only better when you
  want the accompaniment to follow a new style freely.
- **Bracket tags in the lyrics box steer the model and are not sung.** `[Genre: ...]` and
  `[Chorus: bigger]` go into the conditioning. Measured: adding `[Genre: Indie Folk, Chamber
  Pop]` moved a plan from E minor to E flat and changed the chords, while the melody gained no
  notes for the tag's syllables.
- **Changing one word changes the tune.** The planner reads all the lyrics before it writes a note,
  so a seed gives the same plan only for the same words. To keep a tune, sing its score with the
  new words instead of writing a new plan.
- **Duration is a cap, not a target.** `max_duration` truncates; it never stretches. The real
  length comes from the score: bars x beats per bar x 60 / tempo predicted the finished render
  within about 5 per cent across six takes. The app shows that estimate under the score.
- **A score writer will happily loop four bars for a whole song.** Use *Harmony* for the chords
  and *Plan variety* for the melody and structure, or fix the harmony by hand.
- **Plan variety is mostly the repetition penalty.** It pushes against every recently used token,
  chords and melody notes alike. Temperature matters little between 0.55 and 1.0. Measured on
  plans alone (8 per step, two invented songs):
  - **Calm to bold:** the chord vocabulary grows about threefold while the melody stays within two
    octaves.
  - **At a penalty of 1.08** (*quirky* and *wild*): the melody spans up to five octaves and jumps
    register between sections. *Wild* changes key about twice a song.
  - **Too much breaks the score:** the voice headers are tokens too. An older *wild* (temperature
    1.25, penalty 1.18) broke 6 of 6 test plans.

  A plan that does come out unreadable (no vocal part, a line spanning several octaves, a
  metre that keeps changing, a song with nothing sung, or a plan that runs on for minutes) is written once more with a new seed. If that fails too, it is marked
  failed, with a reason, instead of being stored and rendered.
- **The models have their own licences**, separate from this code. See License below.

## Layout

```
compose.yml            engine + app, the one machine setup
compose.cpp.yml        yue2.cpp in place of ComfyUI, with Gemma and pictures beside it
compose.cpp-build.yml  yue2.cpp's servers built here rather than downloaded
compose.override.yml.example
                       your own settings and music mounts: copy it to
                       compose.override.yml, which is git-ignored
engine/Dockerfile      ComfyUI pinned to the commit this was built against, and the
                       WITH_TRAINER build arg, on, that builds the trainer in
engine/custom_nodes/   yue2_harmony, the node behind the Harmony slider
engine-cpp/            yue2.cpp's server, pinned, with our patches
engine-pictures/       stable-diffusion.cpp's server, for take pictures beside yue2.cpp
Dockerfile             the app: FastAPI, one static page, demucs
app/                   the application
  main.py              the HTTP API
  jobs.py              the GPU and stem job lanes: submit, wait, cancel, collect
  lyrics.py            the lyric prompt, and tidying what the model writes
  engine.py            the ComfyUI client, progress relay, template validation
  engine_cpp.py        the yue2.cpp client: reads the same graphs, answers as ComfyUI would
  db.py                SQLite: connection per thread, numbered migrations, settings
  library.py           the data folder: names, take.json, durations, waveform peaks
  stems.py             demucs
  config.py            settings read from the environment
  templates/           API-format graphs: transcribe, song_plan, render
  static/              the page. No build step
tests/                 pytest: the API, the job lanes against a fake engine, migrations
browser-tests/         the page in Chromium against a stand-in engine (Playwright)
scripts/fetch-models.sh
scripts/check-upstream.sh   how far ComfyUI, the trainer and the model repositories have moved,
                            and whether every download address still answers as pinned
models/                bind mounted into the engine (git ignored)
data/                  your library: sources, takes, stems, SQLite (git ignored)
engine-state/          ComfyUI's input, output and user folders (git ignored)
tools/ui-harness.mjs   drives the real app.js against a running instance, with a stub DOM
tools/git-hooks/       the pre-push hook that keeps top-level PDFs off GitHub
requirements-dev.txt   the app's packages plus pytest
eslint.config.mjs      lint rules for app.js
```

## Where files live

The data folder names things after what they hold, so it reads without the database.

```
data/
  yue2.sqlite                                    everything the app knows
  sources/f72ac22518a9ea05-modern-girl.wav       your upload, hash first, then its name
  sources/f72ac22518a9ea05-modern-girl.vocals.flac  its vocal, kept once lyrics are extracted
  takes/modern-girl-take1-329e420d5990/
    modern-girl-take1.flac                       the rendered audio
    modern-girl-take1.peaks.json                 the waveform the player draws, cached
    take.json                                    title, style, lyrics, seed, score, date
  stems/hippie-doodling2-3f35c4d3c286/
    vocals.wav  drums.wav  bass.wav  other.wav
  models/torch/                                  demucs weights, downloaded on first use
  tmp/                                           work in progress, emptied on every start
```

A folder name ends with the take's id, which keeps two takes of the same name apart.
`take.json` holds the seed and the date the card shows, so a folder copied out of the library
still says where it came from.

## Backups

Everything that matters is under `data/`: the uploaded sources, the rendered takes, the stems
and the database. Copy that folder and you have the library. Scores and settings live in the
database, so a take is reproducible from it.

`data/tmp/` and `data/models/` can be left out: one is emptied on start and the other downloads
again. So can the `*.peaks.json` files, which are rebuilt when a take is played, and the
`*.vocals.flac` beside recordings, which are separated again the next time lyrics are extracted. Copy the database
while the app is stopped, or with `sqlite3 data/yue2.sqlite ".backup backup.sqlite"`, so the copy
is consistent.

## Other ways to run it

The app and the engine are separate services that talk over HTTP and WebSocket, so they do not
have to sit on the same machine. `ENGINE_URL` is the only setting that matters (with `ENGINE_KIND=yue2cpp`
for yue2.cpp).

- **One machine** (this file): simplest, and what the quick start does.
- **App on a NAS, engine on the GPU box**: keeps the library and the UI always on, even when the
  rendering machine sleeps. Use `compose.split.yml` for the app. On the GPU box, publish the
  engine's port on the LAN rather than on 127.0.0.1, and set `ENGINE_URL` to it. Set
  `ALLOWED_HOSTS` to the names you reach the NAS by.
- **Docker Desktop on Windows**: works, with the settings in *Windows with Docker Desktop*
  above. It publishes ports onto the Windows host, so other devices can reach the UI once
  `ALLOWED_HOSTS` names them.
- **Native Linux, no containers**: install ComfyUI with the YuE2 nodes, or build yue2.cpp's server
  with the patches in `engine-cpp/patches` and set `ENGINE_KIND=yue2cpp`, and point `ENGINE_URL` at
  it. Install `requirements.txt`, ffmpeg and demucs, then run the app from the repository with
  `DATA_DIR=./data VERSION_FILE=./VERSION uvicorn app.main:app --port 8090`. Without those two
  variables the app looks for `/data` and shows its version as unknown.

Whichever you choose, the app checks the engine every two seconds, and starts without it. A
missing node or model shows in the header instead of failing a render.

## Environment variables

Settings that are not in the app's Settings panel. With Docker, add them under the **app**
service's `environment:` in `compose.override.yml`, which updates never overwrite, and restart.
The easiest start is the example, which has every setting below commented out, with a line on
each, and examples of mounting your music:

```sh
cp compose.override.yml.example compose.override.yml
```

Then uncomment what you need. A setting on its own looks like this:

```yaml
services:
  app:
    environment:
      TRAIN_MIN_STEPS: "600"
```

Values are read once, at start.

**On Windows, without Docker,** they are ordinary Windows environment variables:

1. Quit Yeufonic: right-click its icon by the clock and choose **Quit**. Closing the window leaves it running.
2. Open Start, type *environment*, and choose **Edit environment variables for your account**.
3. Under *User variables*, press **New**. Enter the name, say `TRAIN_MIN_STEPS`, and the
   value, say `600`, then **OK** twice.
4. Start Yeufonic again from the Start menu or the desktop.

Or in PowerShell, `setx TRAIN_MIN_STEPS 600`, then start Yeufonic. To go back to the default,
delete the variable. The Windows install sets the library folder, the folders a corpus may be
built from, and the ports itself: change those in its `settings.ini` instead (see
[On Windows, without Docker](#on-windows-without-docker)). `ENGINE_URL`, `ENGINE_OUTPUT_DIR` and
`TRAINING_ENABLED` are fixed there.

### The app

| Variable | Default | What it does |
|---|---|---|
| `IMPORT_ROOTS` | `/import` | folders a corpus may be built from, comma-separated, as paths inside the container. Each needs a read-only volume mount; `compose.override.yml.example` has examples. `./data/corpus` is always offered |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,::1` | host names the page may be reached by. Add a LAN name or address when you publish the port; `*` turns the check off |
| `ENGINE_URL` | `http://127.0.0.1:8188` | where the engine answers. Change it when the engine runs on another machine |
| `ENGINE_KIND` | `comfyui` | which engine that is: `comfyui`, or `yue2cpp` for yue2.cpp's server (`compose.cpp.yml` sets it). See Choosing an engine |
| `PICTURES_URL` | unset | with yue2.cpp, where stable-diffusion.cpp's server answers (`compose.cpp.yml` sets it). Unset, pictures are not drawn on this PC |
| `GEMMA_URL`, `GEMMA_MODEL` | unset, `gemma4:e4b-it-qat` | with yue2.cpp, where Ollama answers with Gemma, and which model (`compose.cpp.yml` sets the address). Unset, Gemma's features are off |
| `ENGINE_OUTPUT_DIR` | unset | the engine's output folder, mounted into the app. Renders are removed from it once the app has its copy |
| `MAX_UPLOAD_MB` | `2048` | the largest recording you can upload, in megabytes. The engine has its own ceiling, `ENGINE_MAX_UPLOAD_MB` on the engine service, set to the same figure: raise both together |
| `STEMS_ON_GPU` | `1` | `0` keeps stems, vocal separation and lyric hearing on the CPU whatever Settings says |
| `STEMS_THREADS` | half the CPUs | torch threads for the separation on the CPU |
| `STEMS_JOBS` | 4, or a quarter of the CPUs | demucs segments applied at once. One uses about 1.8 GB and 2.5x realtime, four uses 3.7 GB and 3.6x. The split setup's 2 GB cap needs this at 1, or the cap raised |
| `WEAK_RENDER_DB` | `-24` | the average level, in dB, below which a take is marked *Weak render* |
| `DEFAULT_CAP` | `360` | the length cap, in seconds (10 to 900), that a new take starts with until **Length cap for a new take** in Settings is changed. A planned take's cap still rises to fit a longer plan |
| `PEAK_GUARD` | `1` | with an engine that has the peak guard, a render whose peaks would clip is turned down around them before it is saved. `0` leaves it out |
| `PEAK_CEILING_DB` | `-0.5` | the highest a peak may reach with the guard on, in dB below full scale |
| `YUE2_CHECKPOINT` | unset | which YuE2 model the app asks the engine for: `bf16`, `int8`, or a file name. Unset, it uses the full-quality model if it is installed, else the low-memory one. Put it in `.env` (`YUE2_CHECKPOINT=int8`) or in `compose.override.yml`. See Choosing a model size |
| `UNLOAD_WHEN_IDLE` | `auto` | whether the engine is asked to unload its models whenever no more GPU work is waiting. `auto` does it after a take's picture on any GPU (unless another picture is next), so FLUX.2 klein does not sit in video memory under the songs, the app's stems and other programs; and on a Mac, where the GPU shares the computer's memory, whenever the GPU's work runs out. `1` whenever it runs out, `0` never, not even after a picture. The next job loads its models again. Put it in `.env` (`UNLOAD_WHEN_IDLE=1`) |
| `VOICE_URL` | `http://voice:8190` in `compose.yml` | where the voice service answers, for recorded voices. It runs only with `COMPOSE_PROFILES=voice` in `.env`; while it is not answering, the app hides recorded voices. See Recorded voices |
| `TRAINING_ENABLED` | `1` | corpora and LoRA training; `0` takes them out of the app. Training also needs `WITH_TRAINER` on the engine. See Training a LoRA |
| `DATA_DIR` | `/data` | the library. Only needed when running without the containers |

### Training

How long a run trains and how much it can learn. A **step** trains on two songs; a **pass** has
seen every song in the corpus once. Longer runs fit the corpus more closely, and past a point
copy it rather than its style. The checkpoints are kept, so a run that went too far can be
heard back to an earlier step with **Checkpoints**.

| Variable | Default | What it does |
|---|---|---|
| `TRAIN_MIN_STEPS` | `500` | the fewest steps a run gets. Small corpora need the floor: ten passes over 14 songs is only 150 steps |
| `TRAIN_PASSES` | `10` | passes over each song. A corpus big enough for more steps than the floor gets these: 60 songs gives 600 |
| `TRAIN_STEPS` | unset | a fixed step count for every run, in place of the two above |
| `TRAIN_CHECKPOINT_EVERY` | `50` | steps between the checkpoints a run saves |
| `TRAIN_MAX_MINUTES` | `auto` | how much of each song is trained on, from its start, in minutes. `auto` works it out from the graphics card's free memory when a corpus is exported and when training starts, and never goes below 3.5, above 6, or past the longest song: about 5.5 on a 16 GB card. Preparing a song for training holds it whole on the GPU, so if that runs out of memory, set a lower number (`3.5`, say). The Logs window shows what was chosen |
| `TRAIN_MAX_TOKENS` | `auto` | the Planner's context: it learns each song whole, as one sequence, and leaves out any song too long for it. `auto` sizes it to the longest song after the cut (at least 8192, at most 16384); a number fixes it. It costs little in itself: time and memory follow the songs' real length |
| `TRAIN_RANK_PLANNER` | `64` | how much the Planner half, which shapes the melody and structure, can hold. Higher can capture more, and makes a bigger file that overfits more easily |
| `TRAIN_RANK_DECODER` | `32` | the same for the Sound half |
| `TRAIN_DECODER_STEPS` | `1000` | steps for the Sound half, whatever the corpus size |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Header says *Engine offline* | the engine container is not running | `docker compose up -d engine`, then read `docker compose logs engine` (with yue2.cpp the service is `engine-cpp`) |
| Header says *Engine can't start: driver too old* | the NVIDIA driver does not support CUDA 13.0, which the engine is built for | update the driver, or put `TORCH_CUDA=cu128` in `.env` and run `docker compose up -d --build` |
| Header names a missing node | ComfyUI was updated and a node was renamed (ComfyUI only) | check `app/templates/*.json` against `/object_info` |
| torchaudio fails to load its extension | torch, torchvision and torchaudio drifted apart | they are pinned together in both Dockerfiles; keep it that way |
| `docker compose build` hangs with no output | the buildx plugin is missing | install `docker-buildx` for your Docker |
| Engine runs but sees no GPU | the container has no GPU access | `docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi` should print the card |
| A job fails with *the GPU ran out of memory* | another program is using the GPU, the card is small, or the song is long | close other GPU work, lower the length cap, or for training leave the longest songs out; see Requirements |
| A job fails with *the engine stopped during this job* | the engine crashed and restarted | `docker compose logs engine` says why |
| **Write score plan** is greyed out in Instrumental | the LoRA is not in `models/loras` | `sh scripts/fetch-models.sh`, then `docker compose restart engine` (yue2.cpp sees it without a restart) |
| **Write lyrics** is greyed out | Gemma is not in `models/text_encoders`; with yue2.cpp, its Gemma add-on is not set up | `sh scripts/fetch-models.sh`, then `docker compose restart engine`; with yue2.cpp, `sh scripts/fetch-models.sh --cpp --gemma`, then `docker compose up -d` |
| **Corpora** is not in the menu | `TRAINING_ENABLED` is `0`, or the engine was built with `WITH_TRAINER=0`, or the engine is yue2.cpp, which does not train | set both back to `1`, rebuild the engine if it was the second; see Training a LoRA above. To train, switch to ComfyUI |
| Header says the checkpoint is missing | neither `yue2_3b_bf16.safetensors` nor `yue2_3b_int8_convrot.safetensors` is in `models/checkpoints` (ComfyUI; yue2.cpp without its model does not start, and its log says so) | `sh scripts/fetch-models.sh` (with yue2.cpp, `--cpp`), then `docker compose restart engine` |
| **Render this score** and **Write a new plan** are greyed out | no take's score is in the editor | press **Score** on a take in the library, or write a plan |
| The app restarts, and its log says it cannot open the database | `data/` belongs to root, because Docker created it | `sudo chown -R "$(id -u):$(id -g)" data engine-state/output`, with your ids as `APP_UID` and `APP_GID` in `.env` |
| The page says *This host name is not allowed* | you reached it by a name not in `ALLOWED_HOSTS` | add that name or address to `ALLOWED_HOSTS` in compose.yml |
| The Harmony slider is greyed out | the engine image is older than the app and has no `yue2_harmony` node (with yue2.cpp, no harmony patch) | `docker compose up -d --build` |
| Chinese, Japanese or Korean words show as empty boxes | the browser has no font for them: common on a Linux desktop | install the Noto CJK fonts (`fonts-noto-cjk` on Debian and Ubuntu, `google-noto-sans-cjk-fonts` on Fedora), then reload the page |

## Contributing

Working on the code, rather than running it? [CONTRIBUTING.md](CONTRIBUTING.md) has the
branch and test-instance workflow, the checks to run, the engine pin and how a release is
cut.

## Credits

- YuE2 by HKUST M-A-P. Weights CC BY-NC 4.0.
- SheetSage2 and MERT2 by the same team, for transcription.
- [YuE2 instrumental LoRA](https://huggingface.co/Mothersuperior/YuE2-instrumental-cot-full-loras), the realaudio
  LoRA and tokenizer head, and the training regularizer pack, by Mothersuperior. CC BY-NC 4.0. The installers fetch
  them from an unchanged copy, [pshields/yue2-mothersuperior-copies](https://huggingface.co/pshields/yue2-mothersuperior-copies),
  with the author's repositories as the fallback.
- [Gemma 4](https://huggingface.co/Comfy-Org/gemma-4) by Google, for lyric drafts (with yue2.cpp, from
  [Ollama's library](https://ollama.com/library/gemma4)). Apache 2.0.
- [FLUX.2 klein 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8) by Black Forest Labs, with
  Qwen3 4B as its text encoder, for take pictures, when chosen. Apache 2.0.
- The style LoRAs offered at install, by becausereasons, storagejuju, atomtanstudio and ntc-ai, gathered unchanged
  in [pshields/yue2-style-loras](https://huggingface.co/pshields/yue2-style-loras), whose README credits each one.
  CC BY-NC 4.0.
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) as the engine. GPL-3.0.
- [yue2.cpp](https://github.com/ServeurpersoCom/yue2.cpp) by ServeurpersoCom as the other engine, with our patches.
  MIT. Its [YuE2 GGUF models](https://huggingface.co/Serveurperso/YuE2-GGUF) by Serveurperso, CC BY-NC 4.0, fetched
  from an unchanged copy, [pshields/yue2-gguf-copies](https://huggingface.co/pshields/yue2-gguf-copies), first.
- [Ollama](https://github.com/ollama/ollama), to run Gemma beside yue2.cpp. MIT.
- [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) by leejet, to draw take pictures beside
  yue2.cpp, with [Qwen3 4B as GGUF](https://huggingface.co/unsloth/Qwen3-4B-GGUF) by Unsloth as its text encoder.
  MIT; the encoder Apache 2.0.
- [Demucs](https://github.com/facebookresearch/demucs) by Meta for stems. MIT.
- [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) by the RVC Project, with its
  content encoder, pitch tracker (RMVPE) and base weights, for recorded voices. MIT.
- [pymss](https://github.com/KitsuneX07/pymss) by KitsuneX07, bundled with RVC, and the BS-Roformer vocal model
  by viperx it runs, to separate a vocal for a recorded voice. MIT.
- [abcjs](https://github.com/paulrosen/abcjs) by Paul Rosen and Gregory Dyke, for staff notation.
  MIT, vendored in `app/static/` so it works offline.

## License & Copyright

Copyright (c) 2026 Paul Shields. All rights reserved.

The code in this repository is licensed for free personal, non-commercial use under the [Yeufonic Software License Agreement](LICENSE.md). For commercial licensing, contact yeufonic@paulshields.com.

The AI models run by this software are not part of this repository; they are downloaded directly from their respective creators and are governed by their own individual licenses and terms of use (summarized in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)). You are responsible for reviewing the upstream model terms and ensuring that their use and any distribution or monetization of generated audio complies with those licenses.
