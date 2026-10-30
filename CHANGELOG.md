# Changelog

Versions are git tags on `main`. The number lives in `VERSION`, which is copied into the
app image and shown in the header, so a running container can be identified at a glance.

**`VERSION` moves for a change worth a number: a capability, or a change to how the app works.
A fix, a layout change or a colour does not move it; only a release gets a tag.** The number in the
header says which build is running, so it is worth keeping meaningful rather than counting deploys.
A tag, an entry here and a push are for a milestone worth naming, and are cut only when asked for —
not for every update.

To deploy a change:

1. Merge to `main` and redeploy. Bump `VERSION` only when the change is one of the above: a
   deploy that does not move it may leave a browser holding the old scripts, so hard-refresh to
   check one.

To cut a release:

0. **If the installer or the updater changed, try the update before tagging.** A test build of the
   installer can be pointed at a manifest of its own, so an update runs end to end with no tag and no
   GitHub release: see "Trying an update before it is released" in [CONTRIBUTING.md](CONTRIBUTING.md).
1. Add an entry here, newest first.
2. `git tag -a vX.Y.Z -m "..."`
3. `git push origin main --tags`   (homer only, unless GitHub is wanted)
4. For a public release: `git push github main --tags` and
   `gh release create vX.Y.Z --title vX.Y.Z --notes "..."`
5. **Announce it.** In the website repository, `python3 scripts/updates.py 0.0.13 <the
   installer>` writes `public/updates.json` — the version, the release's page, and the installer's
   URL, SHA-256 and size, computed from the file rather than copied by hand. Commit and push:
   Cloudflare deploys in about a minute. Every app asks it every four hours, so within that they
   show a newer version in the header, with the installer or the two commands to update. The script
   refuses an older version than the one on file or an installer whose name disagrees, and
   `--verify` downloads the published asset to check it is the one that was hashed.

Release notes live in two places and neither is a file in this repository: this changelog holds the
history, and each GitHub release holds its published notes. `RELEASE-NOTES-*.md` is ignored so it
cannot creep back in.

## Unreleased

- **The job card and the player take you to the take.** Click the title of the job running, a take in **Up next**, or
  the title of the take playing in the player, and the library goes to that take in whichever space it is in, clearing a
  search or filter that would hide it; a take being made inside another opens on that take's card. A picture's job is
  named as one, not as an engine job.
- **An Artwork visualizer.** The take's picture, large, with its title under it, over a soft copy of itself that
  moves with the music; the Yeufonic scene has the same backdrop behind its mark. A picture button at the
  visualizer's top right, in every scene, makes a new picture for the take playing. The waveform under the Yeufonic
  scene is fainter, the lyrics panel can be dragged out of the way, and a scene chosen in the visualizer no longer
  switches back to the saved one a moment later.
- **Pictures drawn on this PC seldom have people in them.** Gemma, describing a picture for FLUX.2 [klein], is asked to
  leave people out and let objects, the place and the light carry it; a person appears only where the idea needs one,
  small and far off. Asked before only to keep people far off, it put a distant figure in many pictures. Pictures
  already made are not changed.
- **A take with no picture offers to make one from its card.** Pointing at the square at the top left of a card with no
  picture shows **Make a new picture**, as the enlarged picture does, where this PC can make pictures.

## 0.0.52 (2026-10-30)

- **Yeufonic for Mac, experimental.** A disk image for Macs with Apple silicon (M1 or later, macOS 14 or later) that sets
  it all up natively, with no Docker: the first time it is opened, a Terminal window installs Python, the engine and the
  models, and asks once whether to draw take pictures on the Mac. The engine runs on the Mac's GPU through Metal; a Mac is
  much slower than an NVIDIA card, and LoRA training does not work on it yet. Its icon sits in the menu bar. The disk
  image is built on GitHub's own Mac runners, which keep a signed record of the build to check it against. The update
  notice tells a Mac to drag in the new app, and the CPU meter reads a Mac's own figures. See yeufonic.com/macos.
- **Take pictures drawn on this PC are better, and less alike.** FLUX.2 [klein] is run as it was made to be run again,
  so pictures are no longer burnt (hard contrast, oversaturated colour). Gemma's scene leads what klein is asked for,
  and a cover keeps its visual pun on the song's title, where the title's words were cut out of it before. Gemma is asked
  for a setting and light that suit the song rather than a bleak landscape each time, with concrete detail, and for any
  people to stand far off, where klein draws them well (it draws hands badly up close). Without an LLM, a picture's scene
  is made from the song's words and title, so it is no longer the same wide landscape every time. Signs and quoted words
  are still kept out, so klein does not letter the sleeve. An external image model's prompt is unchanged.
- **FLUX.2 klein 9B, for graphics cards with more video memory.** A larger klein that draws more detail and better hands.
  Yeufonic never downloads it (it is gated on Hugging Face and under a non-commercial licence), but put its model and text
  encoder in the models folder and it draws your pictures. **Take pictures: FLUX.2 klein model** in Settings chooses
  between it and the 4B, which draws until the 9B is chosen. The guide says where to get the files and where they go. A picture's note says which drew it.
- **The graphics card's memory is freed after a take's picture**, on every PC. klein stayed loaded after drawing, holding
  most of a 16 GB card with the 9B, out of reach of the app's stems and of other programs; the next picture loads it again.
  The log also says why a picture was not described or drawn by the external LLM when that was chosen.
- **A new take renders as soon as its plan is ready, unless you say otherwise.** *Render as soon as the plan is ready* is
  ticked to begin with, and sits beside **Write score plan**, where it is seen, rather than at the other end of the
  window. Without it a new take stopped at its plan, which looked as if nothing had been made. A browser that has saved
  a choice keeps it.
- **An engine too busy to answer is no longer called offline.** Loading several gigabytes of models can keep the engine from
  answering the app's status check for a while; that read as "offline" in the log and on the page, and could make a later
  failure say the engine had stopped. A slow answer now leaves it online for up to 90 seconds; a refused connection is still
  offline at once.
- **Running out of GPU memory on a Mac is said plainly**, with what to try, instead of the engine's whole raw report.
- **`UNLOAD_WHEN_IDLE`:** when the engine is asked to unload its models. `auto` (the default) unloads after a take's
  picture on any GPU, unless another picture is next, and, where the GPU shares the computer's memory as on a Mac, whenever
  no more GPU work is waiting; `1` whenever no more work is waiting, `0` never. Docker reads it from `.env`; the Windows and
  Mac apps read `unload_when_idle` from `settings.ini`.
- **Pictures from FLUX.2 [klein]'s full-precision files.** The app draws with whichever of its two sets of files is installed:
  the FP8 model and FP4 encoder that Windows and Docker install, or the full-precision pair, which a GPU without FP8 and
  FP4 (a Mac's) can run.

## 0.0.51 (2026-10-27)

- **More for the MCP server.** An agent can now name a new take's settings as the page shows them (Harmony, Plan variety, the
  interpretation, the key and tempo locks, and for a song Follow this structure exactly and Voices follow the cues), and a take it
  makes starts where the page's does, at Varied and Wide. It can also sing a take again, make its variations, sing its score with new
  words, make an instrumental of it, write a new plan for a take with no audio yet, and take a take out of the one it is kept in; make
  a take's picture and open it; make playlists and put takes in them or take them out; look through the saved and built-in styles and
  save one; make a space; and have the app write lyrics in its own song shapes and feels. The guide's MCP chapter has an example
  conversation from an idea to a playlist.
- **The Docker engine is built for CUDA 13.0, as the Windows install's is.** The low-memory (INT8) model now renders at full
  speed on Docker, where it was several times slower than full quality; a LoRA trained on it trains faster and with less video
  memory; and Gemma's lyric drafts and picture descriptions run faster too. It needs an NVIDIA driver that supports CUDA 13.0;
  with an older one the engine waits rather than starting, and the header says the driver is too old. `TORCH_CUDA=cu128` in
  `.env` keeps the previous build. **About** shows the engine's PyTorch and CUDA. The same seed gives a different take on the
  new build. **A Docker install has to rebuild the engine to get it:** check that `nvidia-smi` says `CUDA Version: 13.0` or
  higher, then `git pull && docker compose up -d --build` (with a foreground compose, Ctrl+C and `docker compose up --build`).
  A plain `docker compose up` can keep running the old engine. The first build downloads a new PyTorch, so it takes a while.
- **Low-memory model training does what it says with both models installed.** With full quality and the low-memory model both
  installed and the low-memory one chosen, a LoRA trained on the low-memory model even with **Low-memory (int8) model training**
  off. Off now trains on full quality, and on trains on the model in use. The Train window's memory note follows the model it will
  train on.

## 0.0.50 (2026-10-26)

- **Take pictures are described by Gemma when the external LLM is unavailable** (if Gemma is installed), instead of from the take's title and style alone, which gave much the same landscape each time.
- **Comfy layout: a take card's details are readable again.** A folded card's short line was drawn over them.

## 0.0.49 (2026-10-25)

- A **Yeufonic** visualizer style.
- **The player's play and pause button stays with the song it is playing.** Pausing a song played from a
  playlist and pressing play again resumed the take left in focus in the library instead; now it carries on
  with the song the player shows, from where it stopped. Another take is played from its own card.
- **Pictures drawn on this PC by FLUX.2 [klein] have no lettering.** It wrote garbled words on the sleeve,
  often the song's title; the picture is now described without the title and drawn with a negative prompt
  against text. A picture from an external image model still carries the title, as before. As always,
  configuring Yeufonic to use an external LLM will generate much better results.
- Enlarging a take's picture offers the picture menu's two actions under it: make a new picture, or put the
  default background back.
- **New words that do not fit the tune write a new plan.** Words with far more syllables than the tune has notes
  are crammed onto them and come out garbled, so **Keep this tune** is unticked from about 1.3 syllables a note
  (it was 1.8), and a note held over a bar is counted once, not as two. It can be ticked again for a style that
  packs words in.
- Settings' **Resume External LLM** notice goes away once the external LLM is resumed. It stayed on screen whatever
  the state, so Resume looked as if it did nothing.
- A new cover or instrumental no longer shows the last recording's tempo warning, and a switch of the
  editor's mode tabs that lets go of the open take starts the Advanced settings from their defaults.
- **Files every install needs are fetched from our own copy first.** The instrumental and
  production polish LoRAs, the tokenizer head and the training regularizer pack are fetched from an unchanged copy
  first, with their author's repository as the fallback; either must match the same checksum, on Windows and Docker.
- Two model repositories that were renamed upstream (the Whisper model, and FLUX.2 klein's text encoder and VAE)
  are fetched under their new names, rather than through a redirect from the old ones.
- MERT, which `scripts/tokenize_identity.py` downloads, is loaded at a pinned revision rather than the latest.
- `scripts/check-upstream.sh` also asks every address the installers download from whether it still answers with
  the size and checksum pinned, and says when a repository has been renamed.

### UI enhancements

- A **Collapse** chip beside Comfy and Fit folds every take card down to its title line and buttons, so more
  takes fit on screen; **Expand** opens them again. It is a view, kept on this browser: the takes inside a take,
  new takes and other spaces' takes come folded too, and a folded take's **Inside** button still opens the takes
  inside it.
- Settings opens with every section folded, and each section has a colour of its own, so the five are easier to
  tell apart.

## 0.0.48 (2026-10-22)

- **A fresh install could not fetch the LoRA trainer.** Its repository is no longer on GitHub, so the
  Windows installer stopped at the engine step and an engine image could not be built. Both now fetch
  the same pinned commit from a copy kept under the project's own account.
- **Record a tune (Experimental).** Cover mode has a recorder: sing or hum into a microphone, or play
  a melody on an instrument such as a guitar into an audio interface (choose the device, the input's
  side and its gain). A metronome with time signatures and a count-in, headphone monitoring, a level
  meter and a live pitch readout; for a voice, optional autotune to a key and scale with an A/B
  switch. A take is kept as a recording, marked MIC or INST, and transcribed as melody only, so no
  guessed chords are held in a song made from it; its tune is put in the vocal line even where the
  transcriber heard it as an instrument.
- **Expand to full song (Experimental).** A recorded tune becomes the hook of a whole song: YuE2 plans
  the song in the tune's key, metre and tempo with the tune in every chorus (or verse) and writes the
  rest around it, then renders it as a cover of the recording. Choose who sings it: the tune is moved
  by octaves to that voice's register. A tune transcribed with no chords is given chords from its own
  notes, so the plan has a harmony to follow. With lyrics in the box their sections are the
  structure; a tune played on an instrument needs words first (Write lyrics). Docker needs
  `docker compose build engine` for it.
- **Write lyrics in a cover** of a recorded tune or a MIDI file.
- **F toggles fullscreen** on every page: the main page, the guide and the logs.
- Saving a take mastered earlier could download it without its mastering when the rack had not yet
  read the take's settings; Save now waits for them.
- The visualizer's artwork moves more smoothly and wanders further.
- A cover whose score opens with a bar of rest kept its first section unnamed when its words had
  more sections than the score, and could leave those words unsung.

## 0.0.47 (2026-10-20)

- **Playlists and Liked Songs.** Organise takes into custom playlists and access all your starred favourites in a dedicated two-column view:
  - **Dedicated Playlists view:** Switch seamlessly between the generation Library and Playlists via the topbar segmented control. The playlist sidebar occupies the left column (matching the sheet panel dimensions), and the playlist tracks table occupies the main view with complete view isolation from library panels.
  - **Suno-style track list:** Features high-resolution cover artwork, playlist title, description, aggregate song count, and total duration. Each track row displays a prominent 56px album art thumbnail with a superimposed circular play/pause button on hover, title, badge, style tags, duration, added date, favourite star button, and quick actions.
  - **Automatic Liked songs synchronisation:** Starring any take across any space immediately adds it to the system "Liked" playlist, and unstarring removes it.
  - **Quick Add to Playlist:** Press **P** or click the Playlist button on any take card to toggle membership across existing playlists or create and populate a new playlist on the fly. Pressing Escape closes the picker pane.
  - **Interactive column sorting & in-playlist search:** Click table column headers (**Title**, **Duration**, or **Added**) to sort with directional indicators and reverse the order on a second click, with instant text filtering across titles, styles, and lyrics.
  - **Instant space navigation:** Clicking any song title in the playlist table immediately flips to the Library view, switches to the space where that take lives, selects the take in the left Sheet panel, and scrolls its card into view with a focus pulse.
  - **Contextual hotkey handling:** Take-specific hotkeys are ignored in the Playlists view to prevent unintentional library edits, while **M** continues to open and close the vintage mastering rack for the currently playing or loaded track alongside full transport keyboard controls.
  - **Continuous playback & shuffle:** Start listening from the beginning or click **Shuffle** to randomise the playback order. The transport player bar automatically steps through the playlist tracks.
- **Real-time audio visualizer & lyrics display.** A dedicated hardware-accelerated audio visualizer stage is integrated directly into playback, offering full-screen immersion, interactive Hipgnosis-style album cover dynamics, lyrics display, and an ambient player bar backdrop:
  - **Full-screen visualizer stage & modes:** Toggle the visualizer with **V** or the transport button whenever audio is playing. Features eight real-time visualizer rendering modes:
    - *Waveform Ribbon:* Dual floating harmonic wave ribbons reacting smoothly to audio amplitude and frequency contours.
    - *Aurora Borealis:* Undulating, ethereal northern lights shifting with musical tone and mid/high frequencies.
    - *Cosmic Nebula:* Deep space starfield with glowing galaxy dust particles that pulse and drift with bass energy.
    - *Kaleidoscope:* Radial geometric symmetries pulsing and folding in time with musical tempo.
    - *Neon Grid:* Retro-futuristic synthwave perspective wireframe terrain undulating to low frequencies.
    - *Liquid Warp:* Fluid reactive displacement surface warping and flowing with harmonic layers.
    - *Particle Swarm:* Gravitational particle clusters that scatter on transient percussive hits and coalesce into orbital nodes.
    - *Hi-Fi Spectrum Bars:* Classic multi-band equalizer spectrum analyzer with physical floating peak decay caps.
  - **Hipgnosis-style album artwork & vinyl dynamics:**
    - Large album cover sleeve presentation with interactive 3D pointer-tracking orbit and subtle tilt.
    - Realistic vinyl record complete with light-sheen reflections, concentric groove rings, and accurate 33⅓ RPM rotation that slides dynamically out from the sleeve on bass hits.
    - Holographic glare overlay and expanding beat-synchronized shockwave pulse rings.
    - Three selectable artwork modes (**Sleeve**, **Aura** blurred ambient backdrop, or **Off**).
  - **Lyrics display:**
    - High-legibility typography sheet view scrollable independently of the visual stage.
    - Toggle with **L** or the **Lyrics** toolbar button.
  - **Ambient mini player ribbon:**
    - Real-time reactive dual-wave audio visualizer ribbon integrated across the bottom transport player bar behind playback controls.
    - Configurable under **Settings → Appearance → Mini player visualizer backdrop**.
  - **Visualizer controls & hot keys:**
    - **V** or **Escape**: Close the visualizer.
    - **F**: Toggle fullscreen.
    - **L**: Toggle lyrics sheet view.
    - **Space**: Play / pause.
    - **Left / Right arrow**: Seek backward / forward 5 seconds.
- **Parallel artwork generation for external image providers.**
  - When using external providers (such as Google Gemini via `gemini-3.1-flash-image`) with take or external descriptions, artwork generation requires zero local GPU compute. Image generation now starts in parallel as soon as the audio render is submitted, reducing total take waiting time by 15–30 seconds.
  - Local GPU models (FLUX.2 klein drawing, Gemma descriptions) remain strictly sequential, waiting until the GPU has finished all audio work to prevent CUDA memory exhaustion.
  - Resilient fallback: if an external image provider encounters an API quota or network error, it automatically yields and queues into local FLUX.2 drawing once the audio render completes.
- **Dynamic artwork polling & live updates.**
  - The visualizer, player bar cover, and OS system media session metadata dynamically poll for artwork while playing, immediately revealing the album sleeve, spinning vinyl, and lockscreen artwork as soon as background generation completes without requiring playback to be paused or restarted.
- **Auto-saving song titles in editor.**
  - Editing a take's title in the score editor now auto-saves automatically with a 1.2s debounce and immediate flush on Enter, blur, or closing the editor.
  - A gentle pulsing indicator displays "Saving…" followed by "Saved".
- **Prompt refinement for album covers.**
  - Album cover prompts ensure the literal name "Hipgnosis" and unrequested decades or years are not injected into prompts unless explicitly requested in the song's style description.

## 0.0.46 (2026-10-19)

- **ComfyUI-YuE2-Trainer migration: faster LoRA training, lower memory overhead and configurable pipelines.** The corpus trainer replaces the legacy FS_Audio Suite with ComfyUI-YuE2-Trainer, delivering substantial performance improvements and eight configurable settings under **Settings → YuE2 LoRA Training**:
  - **Training performance & VRAM efficiency:** Audio is processed in fixed 30-second crops with chunked 60-second encoding using native PyTorch scaled dot-product attention, eliminating the quadratic VRAM growth and severe training slowdowns that afflicted longer songs in the legacy trainer.
  - **Drastically lower host RAM consumption:** Default *Compact* acoustic conditioning mode keeps system memory usage under 8 GB (compared to 64 GB+ RAM previously needed for corpora over 30 songs) while accelerating batch preparation and step execution with identical acoustic fidelity.
  - **Single-branch & layer acceleration:** Training a single branch (*Voice & sound only* for vocal timbre/instruments, or *Songwriting & structure only* for composition and melody) cuts total training time roughly in half. Choosing *Attention only* target layers reduces step latency, halves file size (~88 MB vs ~177 MB), and resists overfitting on small corpora.
  - **Faster prior-preservation startup:** Prior regularization mixes base-model reference scores into training to preserve natural musical structures, phrasing and endings. Prompt sampling (10%, 25%, 50%, 75% or 100%) and persistent disk caching cut pre-generation startup time from hours to minutes on large corpora.
  - **Semantic audio tokens:** Optionally trains on SheetSage continuous acoustic tokens alongside ABC notation to capture micro-timing, vocal inflection and performance nuances beyond standard sheet notation.
  - **Final weights & overfitting guard:** Choose between keeping the snapshot with the lowest validation loss (using Exponential Moving Average weights) to guard against late-step overfitting on small corpora, or saving the final step without holdout.
  - **Song length limits:** Configurable per-song audio limits for training exports (*Auto*, 4, 6, or 8 minutes, or *Full song*). Long songs are safely trained without memory exhaustion.
  - **Low-memory (int8) training:** Optionally allows training on the quantized int8 checkpoint in under 6 GB VRAM when the full 40 GB bf16 model is not installed.
  - **Dual-branch merging & cleanup:** When training both branches, the planner and acoustic adapters are automatically merged into a single `.safetensors` LoRA, and temporary `.resume` state and raw single-branch weights are purged automatically.
- **Corpora: 25-minute song duration limit & full re-analysis.**
  - **Extended duration limit:** The maximum song length for corpus audio is raised from 10 minutes to 25 minutes (1,500 seconds), supporting long studio and progressive rock tracks. Stale duration warnings on existing songs under 25 minutes are cleared automatically on startup.
  - **Style re-analysis:** Clicking **Analysed ✓** on a completed corpus prompts to re-analyse style tags across all songs with current prompt templates and LLMs (useful after renaming a corpus or switching providers). Shift-clicking runs a complete re-analysis from scratch.
  - **Stored audio preservation:** Analysis and training re-use the preserved lossless copy stored in Yeufonic's identity storage, so moving or deleting the original import folder never breaks re-analysis or exports.
  - **Queue visibility & control:** Corpus analysis jobs now display in the main page active job card and queue list, with buttons to cancel upcoming jobs or stop the running step.
  - **Enriched style tagging:** Song titles, artist tags and lyrics snippets are now provided to local Gemma and external LLMs for structured subgenre, instrumentation and mood tagging.
- **Hipgnosis album cover artwork & non-blocking generation.**
  - Take pictures are drawn as 1:1 square album covers in the style of Hipgnosis, explicitly including the song title and style prompt with ~30% randomised probability of well-worn sleeve wear.
  - Picture creation waits until audio rendering is complete before queueing, ensuring external image requests never block or delay audio rendering.
  - Corpus trigger words and well-known artist names are automatically stripped from image prompts to prevent external model refusals.
  - Consolidated logging outputs a single full prompt log entry under `[yue2.jobs]`.
- **Album cover pop-up preview.** On the main page takes grid, hovering or clicking the cover initial square in the top-left of any take card with artwork opens a floating pop-up preview of the album cover. Clicking the preview opens the full-screen lightbox view.
- **Resilient external LLM error handling & session fallback.**
  - When an external LLM returns an HTTP 429 quota or spending limit error, Yeufonic presents an error alert dialog with the option to switch to local models for the remainder of the session or keep trying after increasing an API budget.
  - A topbar pill and Settings banner indicate when session-local mode is active, with a single click to resume using the external LLM at any time.
- **Proactive engine memory management.** The engine ComfyUI node unloads local Gemma from GPU memory (`/free`) immediately after lyrics generation and before initiating LoRA training, returning ~8 GB of VRAM to the pool for YuE2 audio generation.
- **Studio lyrics lookup (LRCLIB).** Automatic studio lyrics search on lrclib.net before transcription, matching title, artist and duration tags before falling back to Whisper.
- **External LLM guide & unbilled recommendations.** Added a dedicated External LLM section to the user guide under Settings, explaining GPU memory benefits and recommending unbilled API tiers (such as Google Gemini via Google AI Studio) to prevent unintended token charges during bulk corpus analysis.

### UI enhancements

- **Grouped settings.** Settings are now organised into distinct categories (General, Stems & Demucs, External LLM & Lyrics, Take Pictures, YuE2 LoRA Training, and Appearance).
- **Style LoRA suggestion cleanup.** Removed the redundant static strength recommendation line under the Style LoRA picker in the editor.
- **Log hot key.** Pressing **L** toggles the system log window from anywhere on the page.

## 0.0.45 (2026-10-16)

- **Hot keys help overlay.** Pressing **?** (or **Shift + /**) opens an overlay dialog displaying all application keyboard shortcuts grouped by section: main page playback and chosen take actions, the score editor and piano roll, and take comparison. The dialog closes on Escape, on clicking Close or the backdrop, or on pressing **?** again. Typing in text fields is left alone so question marks in lyrics, styles and titles are unaffected.
- **Resilient fallback on external LLM and image model limits.**
  - **Take picture drawing:** When set to *The external LLM's image model*, if an external draw request fails (HTTP 429 rate limits, quota/credit exhaustion, timeout), picture generation gracefully falls back to FLUX.2 [klein] on this PC if installed. If a song render is active on the GPU, drawing steps aside to the waiting queue so song renders are never interrupted.
  - **Take picture description:** When set to *External LLM*, if the description request fails, it seamlessly falls back to describing from the take itself (title, style tags and lyrics imagery) without failing the picture.
  - **Lyric drafts from prompts:** When *LLM for writing lyrics & style tags* is set to *External LLM*, if drafting fails or hits rate limits, Yeufonic falls back to drafting with local Gemma on the engine (if installed) and displays a clear warning in the status bar alerting you that external limits were hit.
  - **Lyrics from recordings & style tags:** If hearing lyrics with the external LLM fails, Yeufonic falls back to Whisper and flags the warning in the status bar. Corpus style tagging similarly falls back to local Gemma on the engine.
- **Performance, deduplication and code maintainability.**
  - **Database transactions & query performance:** wrapped startup initialization in atomic database transactions, optimized single-record lookups to `.fetchone()`, added thread-safe settings locking, and batched N+1 style resolution queries.
  - **Canonical music theory & lyrics:** centralized pitch, interval and ABC notation conversion in a shared `app/music.py` module, unified section tag synonyms in `app/lyrics.py`, and eliminated circular dependencies.
  - **Audio & storage speedups:** unified FLAC header parsing to read streaminfo directly across normalization, audio duration and tagging routines without spawning external `ffprobe` processes; cached LoRA metadata by file modification time.
  - **Engine & frontend rendering:** precalculated harmony bias penalties, cached NVML library handles to avoid reopening the shared library, recycled piano roll key DOM elements to eliminate layout rebuilds, paused mastering rack meter animations when closed, and throttled waveform playback updates.

### UI enhancements

- **The editor can fill the window.** A button in its top right corner, after Close, makes the editor fill the whole browser window, and a second click puts it back to its usual size. The editor opens the way you last left it. Filling the window, the words column takes its full height: the lyrics box (once there are words in it) and the structure grow into the room, and the player stays at the foot of the column.
- **The whole picture.** Clicking the picture in the editor's Picture menu shows the whole of it, as large as the window allows; a click anywhere or Escape puts it away and leaves the editor open.
- **Voice cues in the expanded lyrics editor.** Buttons for **+ Male**, **+ Female** and **+ Both** in the expanded lyrics window add `[male voice]`, `[female voice]` or `[both voices]` on the line where the cursor is, and **Done** moves to the bottom status line beside the word count so the buttons fit on one line.

## 0.0.44 (2026-10-14)

- **A picture for each take.** Each new take gets a picture of the song, made once no song is being made when it is drawn on this PC (so it never holds up a plan or a render) and while the take renders when an external LLM draws it, and shown faintly behind the take's card, across the top of the take panel when it is chosen, and behind the editor when the take is open there; a take made inside another shows that one's. It is described from the take's title, style and opening words with no LLM, drawn on white, and the app takes the white out: drawn on this PC a picture takes a few seconds and needs nothing but FLUX.2 [klein]. It is drawn on this PC by FLUX.2 klein 4B, a new install option (**FLUX.2 [klein]**, unticked, about 8 GB; `fetch-models.sh --pictures` for Docker), or by the external LLM's image model where the provider lists one; with neither, Settings says **No pictures**, the default background, and how to have them, until something that can draw is there. The editor's **Picture** button makes a new one or goes back to the default background, for good. Settings turn pictures off, choose who draws (this PC first), who describes (the take itself by default, or Local Gemma or the external LLM, slower) and which image model. The description leaves out real names, which an image model will not draw, and asks for soft lettering.
- **Hot keys.** On the main page single keys act on the chosen take, the one in the left panel: **M** opens the mastering rack (again to close it), **E** opens the take in the editor, **I** shows its details, **N** normalises it or undoes it, **V** opens Variations, **T** Try more, **S** stars or unstars it, **D** deletes it after asking, and **L** opens or closes the logs. They do what the buttons do, they say in the status bar why when a take cannot, and they keep out of the way while you type, while a window is open, or with Ctrl, Alt or the system key held. A button's tip names its key, and the guide has a Hot keys section.
- **Style LoRAs at install.** A new, unticked install option, **Style LoRAs** (`fetch-models.sh --loras` for Docker), fetches 39 style LoRAs by their authors, 3.8 GB, each with a description giving its trigger word and suggested strengths: chanson, canzone, Bulgarian voices, qawwali, militant reggae, J-pop, dream pop, old school hip-hop and sixteen concept sliders. They are CC BY-NC 4.0, gathered unchanged in one Hugging Face repository whose README credits every author, and each is checked against its checksum. A LoRA already in the folder under the same name is left as it is.
- **Mastering rack: a Boost preset.** A sixth factory preset, made by ear: a strong lift of the lows and highs, a touch of the parametric equalizer, the compressor catching only what passes full scale, and no limiter. Unlike the others it comes out a good deal louder than the take it is given, and its loudest peaks clip, which is part of its sound.

### UI enhancements

- **The take that is playing pulses on its beat.** Its edge widens and flashes the Play button's green on every other beat of its score's tempo (following the speed control, and back in step after a seek), with a slow breath for a take with no tempo, and the card sits a little larger than the takes at rest, so the take you are hearing is found at a glance. Reduced motion holds it still.
- **The editor has the take's own buttons.** Sing again, Variations, Try more, Inside, Take out, Normalise and Move sit in the window's top row, larger than on the card, lit as on the card and with tips that follow. The Picture button is an icon among them.
- **The take panel shows the take's picture,** as a banner across its top, behind the buttons and the title, fading out before the details. The title and details over it are bolder, the style chips sit on a soft backing, and the section headings (Style, Sound, Words, Score) on a strip of their own, so they read over any picture.
- **Clearer, larger lettering.** The text on every take card, and the small text in the editor, is a point larger, with a little more weight and a fine edge that keeps it sharp over a picture. A take's picture behind its card is less saturated, so it no longer competes with the card.
- **Mastering rack: delete a preset from its bin.** The preset box is a menu with a bin beside each of your own presets; deleting one leaves the rack sounding as it does. The old Delete button only showed while a preset was unchanged, and put the rack back to flat.
- **The mastering rack follows the theme.** In the light theme it was still black. Its panels are now brushed silver with dark lettering there, each unit keeping its own tint and coloured top edge; the knobs, the meter windows and the readouts keep the dark look of the hardware. The parametric equalizer's graph is drawn in light colours to match. The dark themes keep the rack as it was.
- **Equalizer band tips.** Each band of the parametric equalizer says what it is and how it is set when the pointer rests on it.
- **Backdrop colour.** A setting under Theme tints the page behind the takes with a hue you choose, at a strength from a faint wash to a rich colour, and the page changes as you drag. The take cards, the panels and the windows keep their own colours, and the high contrast theme stays black. Like every setting it is kept by the app, so every window onto it shows the same.
- **The editor's player has its keys.** Space and the arrows work the player for the take open in the editor, as they do the page's player; typing in a box is left alone.
- **The editor is always three columns.** The Editor layout setting, which offered the editor as steps one part at a time, is gone: the editor is three columns with everything in view, and the score on a tab of its own.
- **The layout buttons say what they do.** The buttons beside Starred read Comfy or Compact, and Fit or Wide, for the layout a click gives, rather than the one on show.
- **Escape closes the logs** before anything under them, and closes the popped-out log window.
- **Reload to update** now appears for a change to the page's look, as it did for a change to its scripts.

## 0.0.43 (2026-10-13)

- **Mastering rack: a parametric equalizer.** A new unit between the 1073 EQ and the compressor, with seven bands on a graph. Each band is a dot: drag it across for its frequency and up or down for its gain, turn the mouse wheel over it for its width, double-click it to reset it. A band can be a low cut, a low shelf, a bell, a notch, a high shelf or a high cut, and can be switched off; a cut waits, switched off, at each end. The graph shows each band's own curve in its colour, the curve of all of them together, and, while a take plays, the spectrum of what is heard behind them. **Flat**, beside the kinds, puts every band back to 0 dB and switches the cuts and notches off, leaving each band where it is. A button in the graph's corner sets how many decibels it shows (6, 12 or 18 either side), for fine moves or broad ones. The equalizer is part of the rack's settings: it is kept with the take, and a preset you save holds it. The factory presets leave it out and flat.
- **Mastering rack: all of it in the window.** With five units the rack is taller than most windows. It now takes all the height the window has and is drawn smaller, by as much as it needs for every unit to be seen at once, so there is nothing to scroll. Its lettering is set larger as the rack is drawn smaller, so labels and readouts stay close to their own size and stay readable. **Full size** in its header shows the rack at its own size instead, and scrolls; **Fit** goes back. In a very short window it stops shrinking at a little over half its size and scrolls the rest.
- **Mastering rack: three presets have a ratio the rack has a button for.** Vintage Tube Warmth, Vocal Air & Glue and Acoustic Clarity used compressor ratios between the rack's buttons, so none was lit when one of them was chosen. They are now 2:1, with threshold and output moved so that they come out as loud as before.
- **Mastering rack: a double-click on the compressor's OUTPUT goes to +6 dB.** That is where Reset leaves it; the double-click went to 0 dB, so the two disagreed.
- **Windows: Quit quits.** Choosing Quit from the icon by the clock asked "Quit Yeufonic?" every time. It now quits at once, and asks only when a render or a training run is going, which quitting would stop.
- **Sing again asks first.** One click on the card's Sing again button started a render at once. It now asks, saying what it will do, and does nothing if you cancel.

## 0.0.42 (2026-10-12)

- **Saved styles.** A **Save** button beside the style menu keeps the style in the Style box under a name you give it. The menu's first entry is **Saved styles**, which opens onto the ones you kept, each with a bin to delete it, and the menu's search finds them with the canned styles. Saving under a name already used replaces that style, after asking. A style is kept without a style LoRA's trigger word, which is put back for the LoRA in use when the style is chosen. They are kept by the app, so the Windows window and any browser see the same ones.
- **The mastering rack opens from the editor window.** A **Mastering** button in the window's header, to the left of Advanced, is there when the take has sound, and is green while the rack changes how the take sounds. The rack opens over the window; Escape closes the rack first, and the window after. With the rack open there, the keys are the page's: space plays and pauses the take, the left and right arrows move through it, up and down set the volume.
- **Mastering rack: the five presets are remade.** The old ones made a take much louder than it came in and pushed it past full scale inside the rack, where it was cut off flat: that was the distortion. Each preset now turns the input down before it adds anything, comes out at about the loudness it was given (Radio Ready a little more), and leaves the peaks under full scale. A take already saved with one of the old presets keeps those settings, and the preset box shows it as Custom.
- **Mastering rack: the limiter limits, and MIX blends.** A peak over full scale used to be cut off flat by the stage before the limiter, so the limiter never saw it and Drive was a hard clip. An over now reaches the limiter whole, the tube stages bend it without a corner, and the ceiling is the most the rack puts out. The compressor's MIX used to thin the sound, because the compressed signal comes out a few milliseconds late and was blended with a dry signal that was not; the dry signal now waits for it. A take mastered with Drive up, or with MIX below 100%, will sound cleaner than it did.
- **Mastering rack: the compressor's OUTPUT is all the gain it adds.** The browser's compressor raises what it puts out by an amount of its own, more the lower the threshold and the higher the ratio, so a compressor with OUTPUT at 0 still made a take louder. The rack now takes that amount off, and OUTPUT at 0 leaves the quiet parts as loud as they were. Settings already kept with a take, and presets of your own, are read with that amount added to their OUTPUT, so they sound as they did and the knob shows the whole of it. The flat preset's compressor waits at +6 dB for the same reason: switched in, it compresses without a drop in level. The knob now goes up to +30 dB.
- **Mastering rack: saving a preset under a name already used replaces it.** It used to add a second preset with the same name. The rack now asks, then writes the preset over; presets left sharing that name by earlier saves become one.
- **Mastering rack: opened for another take while one is playing, it plays that take.** The take that was playing used to stop and leave silence; now the take the rack is set for is heard in its place. With nothing playing, opening the rack starts nothing.
- **Mastering rack: Dock and Float mean what they say.** A docked rack stays at the foot of the window and is no longer moved by dragging its header; Float lets it be dragged, and puts it back where it last floated. The first Float is centred by the rack's real height, where it used to land almost where the docked rack was.
- **A take's title has the top of its card to itself.** The small buttons that sat beside the title (Sing again, Variations, Try more, Inside, Normalise, the mastering rack, Move) are now on the status line, to the right, so a narrow card shows its title and not its first letter. A status too long to share the line takes it, and the buttons go under.
- **The takes inside a take look like they belong to it.** The cards in an open panel have the lighter shade of the take that holds them, where they used to look like more of the list.

## 0.0.41 (2026-10-12)

- **Piano roll:** saving a score no longer drops a chord that changes at a tie or part-way through a rest, and no longer moves a note by a semitone where a plain note follows a sharp or flat in the same bar.
- **Takes inside a take:** when one is playing and its panel is shut, the Play button on the take that holds it glows gold.
- **Windows:** the picture down the side of the installer says Yeufonic, where it still carried the app's earlier name. The installer on the release page was replaced for this.

## 0.0.40 (2026-10-12)

- **Takes made from a take are kept inside it (#48).** Variations, Try more and Checkpoints each make several takes of one song, and they used to sit in the list beside the take they came from, told apart by the end of their titles. They are now kept inside that take, so a space lists songs rather than every render of each. A take that holds any, finished or still being made, has an **Inside** button on its card, lit orange, and its card is plainly lighter than the others (a warm tint in the light theme). It opens a panel under the card with the takes inside as cards of their own, each one a take like any other: play it, star it, save it, double-click it to open its song and score. A take shows there once it is finished. There is one level: a take inside another holds none of its own, and **Take out** on its card makes it a take of its own again. While a panel is open, Select all, Starred, the kind buttons, Compare, Delete and the player's previous and next work on the takes in it. A search finds takes wherever they are. **Deleting a take deletes the takes inside it**, after a warning that says how many, and moving a take to another space takes them along. Checkpoints, pressed with a take open in the editor, puts its takes inside that take; for a new song the take on the last checkpoint ticked holds the others, and it is not offered from a take that is itself inside another. Try more no longer ticks the takes it makes: with the panel open, Select all and Compare do that. Takes made before this stay as they are. An agent using the MCP server sees how many takes a take holds and can list them.
- **Checkpoints closes the editor.** Pressing Render in the Checkpoints window left the editor open over the library, which looked as if nothing had happened. It now closes, as it does when a plan is written, and the library shows the take being made.
- **Take cards stand out from the page.** A card had a faint outline on a page almost its own colour. In the dark and Studio themes it now has a clearer outline and a lit top edge; in the light theme a soft shadow lifts it; the high contrast theme, whose outline was already strong, is unchanged.
- **A mastered take's card says so.** The mastering rack's button on a card is lit green when the rack changes how that take sounds.
- **Lyrics in the piano roll follow the tune of a song from a prompt.** The roll shared the lyrics out section by section, and a plan's sections are seldom the lyrics' sections. A heading followed at once by a voice cue such as `[male voice]` counted as a section with no words, so the first sung phrase had none, and each block of the lyrics was squeezed into whichever section of the plan came next. Where the two do not count the same, every line is now fitted to the whole melody at once, as a cover's words already were, and a line that only says who sings is no longer a section. A score matched before this keeps the words it was given: **Match Lyrics** sets them again.
- **Words matched to a score counted in thirty-seconds are in order.** Matching a cover's or an import's words to its score read every length as a sixteenth. In a score that counts in thirty-seconds a bar then ran on into the next, the notes of neighbouring bars were taken out of order, and the words came out shuffled. Lengths are read in the score's own unit, fractions and whole bars of rest included.
- **Match Lyrics leaves the score's sections alone.** When the lyrics had more headings than the score had sung sections, the piano roll divided a long section at its pauses to share the words out, and wrote that division into the score as new `% verse` lines. The division is now only its own working.

## 0.0.39 (2026-10-11)

- **Voices follow the cues: a man, a woman or both, line by line.** A line in the lyrics such as `[male voice]`, `[female voice]` or `[both voices]` says who sings the lines under it, until the next cue or the next section. A cue alone did not decide the voice: the render takes the singer mostly from how high the melody is written, and the planner tends to write a verse in two octaves, changing every four lines or so whoever was cued, so a block of eight lines for one singer could come out shared between two. With **Voices follow the cues** ticked (under the lyrics box, shown once the lyrics have a cue; on for a new take), each cued stretch of the plan's melody is moved by whole octaves to where that voice sings, low for a man and high for a woman; for both, the line is put where a woman sings and the second voice is left to the render. The lyric lines are matched to the phrases of the melody over the whole song; phrases that sit together move together, so a tune is not broken in the middle; a plan that is already as cued is left exactly as it is. Nothing else in the plan changes. It is done when the plan is written and again before each render, so it follows a change to the words or the score, and it works for a cover's words too. The Score page has **Voices to cues**, which does the same once to the score in the box, for a take made before the tick existed or with it off. Who sings a line is still partly chance: with the melody in the right place most lines go to the voice cued, and another seed can put right one that did not. Details shows the setting. The guide's chapter on writing a song from a prompt explains the cues.
- **A long song is no longer cut short by its cap.** The length cap of a song or an instrumental from a prompt now rises to fit its plan when the plan is written: to the plan's length with about ten seconds to spare, rounded up to ten, as a recording's score has always set a cover's. It is only raised, never brought down, and never past the 900 seconds the engine allows. A cap you typed yourself stays as you set it, and what is made from that take keeps it. A plan more than a third longer than its cap, and over eight minutes, is still written again rather than taken for a song.
- **The cap a new take starts with is a setting.** Settings has **Length cap for a new take** (4, 6, 8, 10 or 15 minutes; 6 as before), and `DEFAULT_CAP` in the environment sets what it starts at. A take made through the API or by an agent without a cap gets it too.
- **The mastering rack's preset box says what the rack holds.** When the rack takes up another take's settings, as it does when the take playing changes, the box names the preset those settings are, a factory one or one of your own, where it used to go on showing the last preset chosen. It shows **Custom** once a control has been moved away from a preset.

## 0.0.38 (2026-10-10)

- **Vintage Stereo Imager & Spatial Processor.** Added a skeuomorphic stereo imaging module to the Vintage Mastering Rack, positioned immediately before the master limiter:
  - **Bigness width control:** Seamless stereo soundstage width management from mono fold-down (0), transparent stereo (1), up to expansive spatial stereophony (9).
  - **Bass punch filter:** Dedicated 85 Hz mono-summed low-end punch filter keeping sub frequencies centred and punchy without stereo smear.
  - **Analogue tube harmonics:** Tube saturation circuit introducing gentle musical warmth across the stereo bus.
  - **Range & Stage spatial network:** Band-focusing filter network and all-pass phase rotation to shape stereo spread and depth.
- **A saved take sounds as it plays.** Saving a take the mastering rack changes renders the file in the page, through the chain that plays it: the same nodes and the same settings code, on an offline context at the file's own sample rate. The server converts and tags that file and no longer processes the sound itself, so there is no second version of the chain to drift from the first. If the render fails, nothing is saved and the status line says so. The take itself is left untouched.
- **A rack nobody has touched does nothing.** The compressor, the stereo imager and the limiter start switched out, and the rack is in the path only when something in it changes the sound, so a take plays and saves exactly as it was made until a control is used. Turning a control of a module that is out switches it in. Settings kept by earlier builds, which had all three in at their starting values, are read as out where they were never adjusted, and a take that was only played or saved no longer has settings written to it.
- **A page left open across an update says so.** A page loads its scripts once, and after the app behind it is updated and restarted it goes on running the old ones. The header now shows **Reload to update** when the page's scripts are not the ones the app would serve, and a save that an older page asks the server to master is refused with that advice rather than handed over unmastered.
- **The limiter's Out is a true bypass,** like the other modules', and a render keeps the take's sample rate rather than the sound card's.
- **Windows: Save asks where to put the file.** The app's window is told to ask on every start, so an install whose window was first opened by an earlier version asks too, where it used to save straight to Downloads.
- **Mastered audio export cache prevention:** Enforced `Cache-Control: no-cache, no-store, must-revalidate` headers across audio download and export endpoints so browsers never serve stale or unmastered cached audio.
- **AudioContext autoplay reliability:** Global user gesture listeners unlock and auto-resume the Web Audio context immediately on playback and transport actions, ensuring audio begins without first having to open the mastering rack.

## 0.0.37 (2026-10-10)

- **Vintage Mastering Rack & Channel Strip.** A skeuomorphic studio mastering rack with ultra-low latency real-time Web Audio DSP and matching export rendering:
  - **1073 Equalizer:** Preamp drive gain (-15 to +20 dB), high-pass low cut (20 to 300 Hz), low shelf (35 to 220 Hz, ±16 dB), mid peaking bell (360 Hz to 7.2 kHz, ±18 dB), 12 kHz high shelf (analog 6.8 kHz corner slope, ±16 dB), phase invert, and output trim.
  - **Vintage Compressor:** Fast FET-style compressor with stepped ratios (2:1, 4:1, 8:1, 12:1, 20:1, and "All Buttons In" mode), threshold, attack (1 to 80 ms), release (50 to 1200 ms), makeup gain, parallel mix blend, and an analog gain reduction VU meter.
  - **670 Variable-Mu Master Limiter & Tube Warmth:** Clean input drive, tube warmth harmonic saturation curve, true peak ceiling control, and release timing.
  - **Chassis & Workflow:** Draggable floating or bottom-docked chassis, take header selector with quick-access M icon on each take card, factory and user preset manager, and master bypass A/B auditioning.
  - **Export Rendering:** All mastering rack settings are non-destructively saved per take and baked into exported FLAC, WAV, and MP3 renditions.
- **Piano Roll improvements:**
  - **Follow playback auto-scroll:** The piano roll view smoothly scrolls to follow the active bar as audio plays, keeping the playback position in view.
  - **Voice toggle:** Switch quickly between Vocal and Instrumental voice parts in the Piano Roll (with dedicated button and keyboard shortcut).
  - **Key signatures and accidentals:** Corrected note pitch resolution and accidental tracking in flat keys (such as F, B♭, and E♭), respecting measure barlines and key signatures.
  - **Score saving:** Score edits now auto-save on modal exit and editing, and the score modal has an explicit Save button.
- **Transport bar & take selection:**
  - Selecting or highlighting a take now links its recording to the transport bar, so pressing Spacebar immediately plays the selected take.
  - Selecting another take does not abruptly stop active playback; playback continues undisturbed until Spacebar or Play is clicked.
  - Double-clicking any take card immediately opens the Take Editor.
- **Modal and editor ergonomics:**
  - The song and score editor modals remain open when clicking outside on the backdrop, preventing accidental lost state.
  - Relocated the Take Editor Close button to the top-right header.

## 0.0.36 (2026-10-09)

- **CPU and GPU usage in the header.** Next to the version number, two subtle indicators show current GPU and CPU utilisation in percent, updating live with the app's state polling.
- **Refreshed UI.** Take cards, action buttons and waveforms have a refreshed look across all themes, and the README screenshots have been updated to match.
- **The end-of-render notes can be dismissed.** "Ran to the length cap" and "Stopped before the last section" have a × at their end, as the
  weak-render note has, for when the end sounds fine. A new take made from one starts with the note again.
- **The section list says when a take ended short of its score.** A render that is more than about 5 percent shorter than
  its score (and at least 6 s) now gets a line under the section list saying by how much, and that the list can be out of
  step with the audio, more so later in the song. The score's section times are right for the first part of every take and
  for takes that render in full; they drift after a render has compressed or skipped something.

## 0.0.35 (2026-10-08)

This release changes the engine image (the Harmony node), so a Docker install needs `docker compose build engine`
and a recreate as well as a pull.

- **Build a song's structure, then write the words.** Song from a prompt has a structure builder above the lyrics, as an
  instrumental does: add, remove and reorder sections, or start from one of eleven common shapes. It includes an
  **interlude**, an instrumental passage the planner plays on its own. Write lyrics follows the structure and asks how
  many lines a verse or chorus has (more lines make a longer song), **Put sections in the lyrics box** lays the
  sections out to write under by hand, and the lyrics editor has buttons for intro, pre-chorus, interlude and outro.
  The old Structure dropdown in the Write lyrics window is gone, replaced by the builder.
- **How the lines sound.** The lyric writer no longer defaults to eight-syllable rhymed couplets, which is what its old
  instruction ("6 to 10 syllables, with rhymes") produced almost every time. Write lyrics has a **How the lines
  sound** choice that shows the syllables each line aims for: Natural (the default, a mix of short and long lines
  with some rhymes), Regular rhyme (the old shape), Spoken rhythm, Loose rhyme, Short and punchy, and Long and
  flowing. The last pick is remembered.
- **Follow this structure exactly.** A tick under a song's lyrics box makes the plan write exactly the sections the
  lyrics name, in order, and no others (so no intro or outro of its own). It steers only the name the planner writes
  after a section comment and holds the plan's end back until the last section has begun; the planner still decides
  what the music is. An instrumental is not affected.
- **A chorus no longer opens the way the verse did.** From Colourful up, the Harmony step also takes logits from a
  chord that would repeat how the previous section opened (its first four chords, position for position). It chooses no
  chord and forbids none, and the chords inside a section can still loop. **Sections open differently** in the Advanced
  settings follows the Harmony step by default, or can be set to Always or Never for a take.
- **Details shows the structure.** A take's Details lists the structure it was asked for (the lyrics' sections, with
  their line counts) and the sections the plan wrote, with where each starts. The builder says when a list is longer
  than the planner usually writes (8 to 10 sections), and when edited words have more sections than a take's tune,
  or far more syllables than it has notes (long lines on a tune made for short ones come out repeated or dropped),
  **Keep this tune** is unticked, with a line saying why, so a new plan is written for them.
- **New songs start at Harmony Varied and interpretation Wide,** where they used to start at Familiar and Standard: our
  own testing found that pair gave the most musically interesting renditions. Both can be changed, existing takes keep
  their own, and the API's defaults are unchanged.
- **Write lyrics remembers the brief.** What a song was said to be about is kept with the take, and opening a take and
  pressing Write lyrics shows it again. A take made with new words keeps it, or takes the one you changed it to.
- **Render this score makes a new take.** A take that already has audio is rendered as a new take beside it, so a render
  never overwrites one that may be worth keeping: for songs and instrumentals, from the Score page and from a planned
  instrumental's main button, whatever was changed. The new take keeps the title of the one it came from. A take with
  no audio yet is filled in, and the card's own Render action is unchanged.
- **More styles to start from.** The Style dropdown has 200 styles. About 125 are new and cover mainstream genres (pop,
  rock, country, R&B, gospel, Latin, metal and more), with more rap, hip-hop, trap and EDM; some of the most niche
  of the old ones were dropped to make room. Songs and covers have five more one-click presets.
- **Filter takes by kind.** Song, Cover and Instrumental toggles beside the library's filters show only those kinds in
  whichever space is open. Pick more than one, or none for every kind; the choice is kept across a reload.
- **Write lyrics closes when the draft starts.** The window used to stay open and tell you to close it; the progress
  already shows beside the lyrics box.
- **The mode buttons keep one order.** Song, Cover and Instrumental are in the same order in the editor as on the
  library's buttons.
- **The guide has a chapter on writing a song from a prompt,** going through every option in the order the editor
  shows them, with what to change to make a song longer.

## 0.0.34 (2026-10-08)

- **A corpus without vocals.** The corpus **Voice** menu has a **none** entry for instrumental songs (#40): the
  vocal is not separated and Whisper does not run, a song's lyrics are the section tags from its score
  (`[instrumental]` without one), the caption leaves out the vocal clause, and the lyrics review and its tick
  do not apply. Style descriptions use the local model when it is installed, as the external one would have only a
  title. Changing a corpus's Voice to or from **none** updates the songs already analysed.
- **Render this score makes a new take.** A take that already has audio is rendered as a new take beside it, so a
  render never overwrites one that may be worth keeping: for songs and instrumentals, from the Score page and from a
  planned instrumental's main button, whatever was changed. The new take keeps the title of the one it came from.
  A take with no audio yet is filled in, and the card's own Render action is unchanged.
- **Play after switching spaces.** A take paused in one space can be resumed after switching to another; Play
  did nothing because the player had lost the take.

## 0.0.33 (2026-10-07)

### Changed
- **Make an instrumental is now available for covers as well as for songs from a prompt.** It was only on a song's Score page, and on a cover it showed or not depending on what the editor had held before. A cover's page now always
  shows it (a cover has no plan to render again or write anew, so it is the only button there), with a line saying what it does.

## 0.0.32 (2026-10-07)

### Added
- **A Details button on a take** lists what it was made with, in words (model, mode, seed, interpretation, production polish, whether the volume was normalised, style LoRA and strengths, length cap, the Advanced
  settings and the style), with a button to copy it as text.
- **Make an instrumental from a song's or cover's score.** A button beside **Render this score** makes the same score as an instrumental in a new take, leaving the original as it was: the sung melody is
  given to an instrument, only the score's section tags are sent in place of the words, and the style loses its vocal descriptions. Emptying a song's Vocal part by hand did not stop it singing,
  since the render sings the words it is given.

### Changed
- **Switching a corpus song's words between versions no longer drafts them again.** Each version keeps its own finished words, edits and checked tick: the first choice of a version drafts it (and calls the
  external model to mark its sections), and every switch after that puts its words back at once. Before, each switch drafted again and threw away what was in the box, even for a version drafted before.
- **Each interpretation shows what it does as a tooltip in the menu**, so it can be read before choosing it, not only for the one already chosen.
- **Stems, vocal separation and lyric hearing run on the GPU.** The engine has a Demucs node and a Whisper node, and the app separates a recording's vocal, a take's stems and each corpus
  song's vocal, and hears the words of a separated vocal, there, as jobs in the engine's queue beside plans and renders, instead of on the CPU. **Use the GPU for stems and lyrics** in Settings
  (on by default) turns it off; an engine without the nodes, a LoRA being trained, or `STEMS_ON_GPU=0` keeps the CPU, and a job the engine fails falls back to the CPU. The Docker engine image
  adds both, so an existing Docker install needs the engine rebuilt (`docker compose build engine`); `scripts/fetch-models.sh` now fetches the Whisper model for the engine (about 1.6 GB, into `models/whisper`), so run it again before the first lyric hearing; if it has not been, the first hearing
  fetches it and the song's line says so. The Windows installer adds Demucs and Whisper (with the CUDA 12 libraries Whisper needs, a little over a gigabyte more) and fetches the Whisper model for the engine.
  **Updating to this takes longer than usual**: a Docker install rebuilds the engine, and a Windows install downloads about 3 GB more (the libraries and the model).

### Fixed
- **The take card's Sing again, Variations and Try more icons have their tooltips back.** While no LoRA was training, the check that disables GPU buttons during training replaced
  each button's tooltip with an empty one. It now puts the button's own tooltip back when training ends, and leaves it alone otherwise.
- The guide no longer says a finished instrumental is checked for singing; that check was removed.

## 0.0.31 (2026-10-06)

### Changed
- **The guide says where to find style LoRAs.** It links published sets that load here, with their licence, and says how to add one; the README points to it.
- **The Corpora pages share LoRAs.** A trained corpus's page has **Download LoRA**, the zip the Style LoRA picker's **Download** gives, and the list of corpora has **Import LoRA** beside **New corpus**, which installs such a zip (or a `.safetensors` file) as the picker's **Install** does.
- **New cover starts with no recording.** It kept the last cover's recording selected, with its score, words and sections still showing. Choosing a recording fills them in again.
- **Writing a plan closes the editor.** It used to stay open on the Score page, which looked as if nothing had happened and invited a second click. The take's card shows the plan being written.
- **A planned instrumental lists its sections to rearrange, as one from a recording does.** The list used to appear only with a source recording, though
  an instrumental written from a structure has a score with sections once it is planned. Rearranging them and pressing **Render this score** renders
  with section tags that follow the edited score, as a new take beside the original when that has audio; an untouched plan keeps the structure it was written with, times included.
- **A take that ends before its score's last section is flagged, and retried once.** The card used to say "stopped early" only when a render fell under 60% of its score,
  which missed most renders that stopped partway through a long score. It now says "Stopped before the last section" whenever the render ends before the last section of
  its score begins (a cap set below the score still counts as the end). A score of a single section keeps the share rule.
- **The section list shows the length cap and warns when the score outgrows it.** Copying a section can make a song longer than its cap, and the render
  then stops before the end. The list now shows the total against the cap, says by how much the render would fall short, and offers to raise the cap. For a
  recording being covered, the cap follows the edited score as it did when the recording was chosen.
- **A cover's section list says what its words need.** The words are matched to the sections in order, so after you add, remove or rearrange sections it says
  whether the Words box needs more blocks, fewer, or a different order.

## 0.0.30 (2026-10-06)

### Added
- **An MCP server, off by default.** With **MCP server** switched on in Settings, an AI agent on the same computer (Claude Code, Cursor and
  others) can make songs, covers and instrumentals and read the library, at `/mcp`. A tool calls the app's own routes, so it has the page's
  checks and effects. It can list and read takes, wait for one to finish, play it (it opens a link in your browser), make a song, a cover from a
  recording in the library or an instrumental (with a length, in a named space, with a style LoRA by name), render again, cancel, star, rename, move
  and delete takes. Takes can share a title, so it works by id and shows a short one; deleting asks twice, and a starred take needs asking for
  again. An instrumental is always given a structure with times, since without times the planner writes plans too long to use. See the guide.
- **More for the MCP server:** try more takes from one, transcribe a recording, split a take into stems (with links to each file and a zip), and
  ask how busy it is.
- A link to a take's audio now plays in a browser instead of saving the file (saving is as before).

### Fixed
- **The Windows installer checked the default ports, not the ones the install uses.** Its check that the app's and the engine's ports
  are free now reads them from `settings.ini`, so an install moved off 8090 beside a Docker copy is checked on its own ports and not
  warned about Docker's. The guide's MCP chapter also says which address to use, and that an agent in WSL cannot reach the Windows app.
- **A failed instrumental plan no longer tells you to lower a style LoRA's strength when none was used.** Every take stores a strength,
  1.00 unless changed, whether or not a LoRA was chosen, and the advice read it as if one had been. It now appears only for a take with a LoRA.

## 0.0.29 (2026-10-06)

### Changed
- **Finished instrumentals are no longer checked for singing.** The check separated a few spans of the audio and
  flagged a take when anything loud enough landed in the vocal stem, which synths and effects could do, and plenty of
  instrumentals have a spoken line or a refrain in them anyway. Renders finish sooner without it, and the engine no
  longer loads the separator while an instrumental renders. The **Vocal check on instrumentals** setting is gone.
  The warning on a *plan* that has a melody in its vocal part ("This plan may sing") stays, as it reads the score.

### Added
- **Rearranging a song's sections.** For an instrumental made from a recording and for a cover, each section in the list can be
  dragged to a new place or moved with the arrows, copied or taken out, and the score is rewritten to match, so a verse, chorus, verse, verse can become verse,
  chorus, verse, chorus. The original sections can be restored until another score is loaded. A cover's words are matched to the
  sections in order, so they need to suit the new order. While the take plays in the editor, the section it is at is lit in
  the list, and double-clicking a section jumps the take to it. Once a take has played after its sections were rearranged, the status
  line says the structure has changed and what to press to render it, until they are put back. (First pass; issue #37.)

### Fixed
- **A cover keeps its score's section names when its lyrics have cue lines.** A bracketed line such as `[strings]` or `[full orchestra]`
  is not a section heading, but a section it stood over was relabelled "verse", so a transcription's intro, interlude and outro all
  read as verses once words were fitted. Such a section now keeps the name the score gave it. Takes made before this keep the names
  they were made with.
- **A recording brings its words back.** Choosing a recording fills the lyrics box with the words heard in it, and now, when none were
  heard, with the words last used for a cover of it. Starting a new cover does the same, where it used to leave the box empty because
  the recording stays chosen. Words already in the box are only replaced after asking.
- **A new take starts clean.** Starting a new song, cover or instrumental no longer leaves the last take's playback controls in the
  editor, and it clears the style LoRA (and with it the trigger word in the style) along with the title, style and score.
- **An instrumental's editor now has the playback controls** a song's and a cover's have.

## 0.0.28 (2026-10-06)

### Fixed
- **Training a LoRA on native Windows.** PyTorch's Windows builds have no FlashAttention, so the trainer's
  grouped-query attention fell back to a kernel whose memory grows with the square of a song's length: a long song
  filled the card, and training slowed to a crawl or stopped the engine. The installer now gives the trainer's two
  attention calls the key/value heads they need (the result is the same, and the fast kernel is used). It is applied
  on every run, so an install updated from an earlier version is repaired, and it stops setup if the trainer's code is
  not what it expects. Docker is unchanged: Linux already had the fast path.

## 0.0.27 (2026-10-06)

### Fixed
- **The MIDI file saved from the Score window now carries its instruments and drums properly.** The file came from abcjs's
  own writer, which put every instrument change on channel 1, left the bass without an instrument of its own, and wrote a score
  with drums as an invalid file: the drum pitches were wrong (a kick and snare came out as a tambourine and a cowbell) and one
  velocity was 128, which a strict MIDI reader rejects. It is now written from the same sequence that plays the preview: a track
  for each part (the vocal and instrument lines, the chords, the bass, the drums), each on its own channel with its instrument,
  the drums on channel 10 at General MIDI pitches, and the tempo and metre in the file. The notes, their timing and the tempo
  are unchanged. Fixes #36.

## 0.0.26 (2026-10-05)

### Fixed
- **The low-memory model was several times slower than full quality on Windows in 0.0.25.** That release put the engine on
  PyTorch with CUDA 12.8, and on that build the low-memory (INT8) model renders far slower; on CUDA 13, which the Windows
  engine ships and which the model was tested on, it is no slower than full quality. The installer no longer installs the
  CUDA 12.8 build, and an install that has it is put back on CUDA 13 when the installer is run over it (only PyTorch is
  downloaded again). Full-quality installs were not affected. Fixes #35.

## 0.0.25 (2026-10-04)

### Known limits
- **Training a LoRA on native Windows.** In our own testing this workflow performs poorly in a native Windows
  environment (it is slow, and on a 16 GB card the engine sometimes stopped). The README and the guide now say so and
  point to the Docker and WSL2 route for anyone who needs to train. Making songs is not affected.

### Fixed
- **The installer says how to quit Yeufonic.** Its prompt, the welcome pages, the update window and the README told people
  to close the window, but that leaves the app running by the clock, so the installer kept waiting. They now say to
  right-click the icon there and choose Quit.
- **A stopped engine showed dozens of error boxes on Windows.** The launcher raised its "engine stopped unexpectedly"
  box from a half-second timer, and the box let the timer fire again beneath it, stacking another every tick until
  the screen was covered. It now stops the timer and shows the box once.
- **Training on a fresh install.** The trainer reads the tokenizer head from its own `fs_audio` folder, and neither
  the Windows installer nor `fetch-models.sh` put it there (only in `audio_encoders`), so a new install refused to
  train with "tokenizer_head … not in ['(run FS_Audio Training Assets first)']". Both now place it in both folders,
  and an install updated afterwards is repaired.
- **The Windows engine used the same PyTorch as the Docker engine.** The installer put torch 2.9.1 on CUDA 12.8 into the
  engine, in place of the CUDA 13 build ComfyUI ships. It did not help training, and it slowed the low-memory model:
  reverted in 0.0.26.
- **Lyric extraction on a fresh install.** A newer release of the audio library PyAV (19) removed an option
  faster-whisper uses to read audio, so on an install set up after it came out, hearing a song's lyrics failed
  with "open() got an unexpected keyword argument 'metadata_errors'". PyAV is now held at the version the app
  was tested with, and an install updated afterwards is repaired.
- **The Windows installer no longer puts a `python3.13.exe` in your own `.local\bin` folder.** Setting up Python for
  the app also left a copy of its launcher there, outside the install folder, where the uninstaller never looked.

### Added
- **An About window,** in the menu: the version, the build it was made from and the model in use.
- **A clearer message when a plan can't be read and a style LoRA is set.** It now suggests writing a new plan or trying a
  different checkpoint, and nothing is changed for you.
- **A line in the Train window on native Windows,** saying training performs poorly there and that Docker with WSL2 is
  recommended. Training is not refused.
- **`engine_args` in the Windows `settings.ini`.** Extra switches for the command that starts the engine, for a PC where it
  misbehaves (for example `engine_args = --disable-dynamic-vram`).
- **A Storage window, in Settings.** It shows where the disk space is going, per area and per corpus, and
  lists what can be given back: the copies made for the engine while songs are analysed, the engine's
  copies of uploads and finished training sets, each corpus's training set (each song written again as
  lossless FLAC) and its training checkpoints. Every item says what it is and what removing it costs, and
  nothing goes until it is ticked and confirmed. A corpus that is training, being exported or analysed is
  refused. The window also holds the settings for tidying automatically: the working copies of a song are
  now removed when its analysis ends (they were never read again), the training set can be removed when
  training ends, and the existing choice about checkpoints moved here.
- **Separated vocals are saved as FLAC.** A corpus song's separated vocal was an uncompressed WAV; it is now
  FLAC, the same audio in about half the room. The Storage window has a **Convert to FLAC** button for the
  vocals already saved as WAV: it converts each, checks the FLAC decodes to exactly the same audio, then
  removes the WAV, in the background and stoppable.
- **A smaller YuE2 model for graphics cards with little memory.** The Windows installer offers
  two sizes on its components page, full quality (BF16, recommended) or low memory (INT8, 4.0 GB),
  and the Docker script takes `--int8`. An install has one: running the installer again changes it,
  and `YUE2_CHECKPOINT` forces one. The app uses whichever is installed, **About** says which.
  Training a LoRA needs the full-quality model, so it is not available on a low-memory install.
  The README has a section on choosing between them.
  Fixes #31.

## 0.0.24 (2026-10-03)

### Fixed
- **Updating from inside the app on Windows.** The installer was started inside the app's own
  process group, so closing Yeufonic, which it needs, ended the installer with it. It is now
  started outside it, and it checks first whether Yeufonic is running: if so it asks you to close
  it and waits (Retry, or Cancel to leave everything as it is), instead of carrying on or
  stopping it for you. A silent install is unchanged.

## 0.0.23 (2026-10-03)

### Added
- **Advanced take settings.** An *Advanced* button in the song editor opens a panel of per-take
  settings: diffusion steps, an *Avoid* hint, key lock, tempo lock, the planner's score length,
  the chord hold limit and outside-chord bonus, the loudness target and the fade-out. They are
  saved with the take, the button lights up when any differs from its default, and *Reset to
  defaults* puts them all back.
- **Key lock moves the plan.** The planner does not follow a key named in the style, so the
  finished plan is moved to the key asked for: every note and chord symbol shifts by the same
  interval and the key signature is rewritten. The plan keeps its mode (a minor plan stays minor,
  with only the tonic moving). A plan it cannot read with certainty (a modal key, or a key change
  part way) is left in the planner's own key, and the log says so.

### Changed
- **MIDI imports find the real bar line.** Some MIDI files start with the first word on the beat
  before the downbeat, which put every bar marker, chord change and phrase a beat out. The drums
  and bass now decide where the first bar line is, and a lead-in gets a short bar of its own. A
  file whose rhythm section does not say is left as it was. `bar_offset` on retrack overrides it.
- **Pasted lyrics are fitted to the whole melody.** The words were shared out section by section
  by count, so one misplaced line shifted every later one, and a text longer than the melody
  squeezed everything early. They are now placed a syllable to a note over the whole song, with
  line ends pulled towards the melody's rests, line starts towards phrase starts, and the notes
  left over held after the word they belong to. Lines that cannot fit are left out from the end.

- **Studio Audio in the piano roll is a mode.** Its button stays lit while it is on, and the
  roll's Play, Pause, Rewind and bar-step controls act on the studio audio, with the cursor
  following it. Only one thing plays at a time: the roll, the notation preview and the main
  player give way to each other, and Roll Sound is greyed out while the studio audio is on.
  Pressed again, the button returns to the ordinary preview. The duplicate button beside Match
  Lyrics is gone.

### Fixed
- **MIDI Tracks window in light themes.** The track rows kept a dark background with dark text.
- **Tempo lock now sets the plan's tempo.** A style that named two tempos, or a planner that wrote
  its own, could leave the plan at a different tempo from the one asked for. The tempo lock now
  replaces the tempo in the style and in the stored plan, and the plan that is shown is the one
  that renders.
- **Tempo and key locks apply to covers.** A cover from a MIDI file or a recording's score kept
  the source's tempo in the score you read, and ignored a key lock. Both now apply to the stored
  score as well as the render.
- **Reset to defaults reaches the server.** After a reset, a plan, render or new-words request
  now puts every setting back to its default instead of keeping the take's earlier values; a
  request that says nothing about a setting still keeps the take's.

### Notes
- *Avoid* is added to the style as a hint; the renderer runs without negative conditioning, so it
  is not a guarantee.

## 0.0.22 (2026-10-03)

### Removed

- **Removed "What is new" menu item.** Removed the menu item to keep the brand menu focused and prevent external browser windows from opening behind full-screen app windows.

## 0.0.21 (2026-10-03)

### Added

- **In-app update download with live progress.** The Windows update flow now streams the installer directly into the user's Downloads folder within the app, displaying real-time download progress, byte counters, and checksum verification. This completely avoids background browser windows opening behind maximized app windows or being intercepted by browser SmartScreen prompts.
- **Direct installer launch and folder reveal.** Once downloaded and verified, the update modal offers direct "Run installer" and "Show in folder" actions.

## 0.0.20 (2026-10-03)

### Added

- **Canned styles dropdown.** A searchable dropdown directly under the Style box with 100 curated styles alphabetized for quick selection, prepending active LoRA triggers automatically.
- **Editor transport for active takes.** The transport controls now display in the editor for playable takes so songs can be auditioned directly.

### Changed & Fixed

- **Cleaner status bar.** Unified status reporting in the bottom status bar and eliminated transient status boxes across views.
- **Empty style default on new take.** Creating a new song, cover, or instrumental starts with a clean, empty style box.

## 0.0.19 (2026-10-02)

### Fixed

- **Windows installer update reliability.** Fixed an issue where updating an existing installation from within the application window was terminated prematurely by Windows Job Object cleanup when closing the previous version. You will be instructed to close any open Yeufonic window prior to running the updater.

## 0.0.18 (2026-10-02)

### Added

- **MIDI import and audition (Experimental).** Drop Standard MIDI files (`.mid`, `.midi`) into Cover mode to generate different, often off-the-wall takes of original tunes. Auto-transcription separates lead vocal melody, accompaniment, and chord progressions into ABC notation and the interactive Piano Roll.
- **Embedded MIDI lyrics extraction & phrase alignment.** Lyrics and text events inside MIDI files are extracted and aligned to the vocal melody across breath pauses and rests.
- **Large piano roll to edit MIDI notes and see how your lyrics match the vocal melody.**
- **Automatic vocal octave normalization.** MIDI lead melody tracks sequenced in lower registers (such as synth leads or guitar tracks) are automatically transposed to a natural singing register.
- **High-fidelity SoundFont audition.** MIDI files can be auditioned in-browser using FluidSynth and General MIDI SoundFonts (`.sf2`). Audio rendering includes automatic peak volume detection and normalisation with true-peak limiting, ensuring multi-track MIDI recordings audition loudly and clearly without clipping.
- **Default SoundFonts installation.** Setup scripts on both Linux/Docker (`scripts/fetch-models.sh`) and Windows (`windows/setup.ps1`) automatically download `Arachno_SoundFont_Version_1.0.sf2` and `github_Jnsgm2.sf2` into `data/models/soundfonts/sf2/`. Active SoundFont can be selected in Settings.
- **FluidSynth on Windows.** The Windows setup and launcher now automatically download and configure official FluidSynth binaries in `tools/fluidsynth/bin`.
- **Themed confirmation and input dialogs.** Destructive actions (deleting takes, stems, recordings, corpora, LoRAs, spaces, or checkpoints, and discarding unsaved score changes) use an in-app modal styled to match the application theme, with focus initially on Cancel for safety, replacing browser popups. Creating and renaming spaces and takes use in-app text prompts with Enter submission, Escape dismissal, and focus trapping.

### Changed

- **Prompt token sanitization.** Section structure markers and prompts sent to YuE2 are cleaned of embedded `w:` lyric headers, ensuring the causal language model does not suffer token collisions or skip subsequent verses.
- **The external model's words win.** With an external LLM set to hear a recording's lyrics, a reply that looks like lyrics is now always used, even where it differs a good deal from what Whisper heard, which had been refused when it had fewer than 60% of Whisper's words or when under 30% of its words matched. Whisper can miss a vocal buried in a mix, and a held syllable it loops on inflated its word count. A reply that refuses, cuts lines short, writes a notice, or is almost nothing, or an error, still falls back to Whisper. When the words cannot be matched to Whisper's times, the lines are spread over the song instead. Obviously this only really works when the lyrics are on the public Internet and can be found via LLM searches.
- **Both versions of a corpus song's words are kept,** and its Review panel has a **Words from** switch to put either in use, the external model's by default. Songs analysed before this have Whisper's or the model's lines only; analyse again to get both.
- Whisper's lines no longer hold a word repeated more than eight times in a row: a vocalise it looped on ("la" written 237 times) is cut back.

### Fixed

- **Corpora badge status scoped to the active corpus.** The top bar badge previously accumulated failed tracks across all corpora in the library, causing it to remain red and report errors in its tooltip even after switching to a corpus whose tracks had all succeeded. The badge now reflects the failure count and working state of the shown corpus.
- A plan that looped could run for ten minutes or more, mostly rests, and the render then ran to the length cap with long repeated intros and sometimes no vocal. It happened with a style LoRA, a short style and Calm plan variety together. A written plan far longer than a song (over 8 minutes, or well past a longer cap), or a song whose vocal line has no notes at all, is now written once more with a new seed, like any unreadable plan, and the take fails with advice if the second comes out the same: describe the style in more detail, or use Normal plan variety with a LoRA.

## 0.0.13 (2026-09-30)

### Added

- **The app says when a newer version is out.** Every four hours it asks its own site for the current
  release — one request, to a file on yeufonic.com, with GitHub's release as a fallback, and nothing
  else leaves the computer. A newer version shows as a quiet pill beside the version in the top bar,
  and the menu offers **Get x.y.z** — the installer on a Windows install, the two commands on the
  clipboard for a Docker copy — beside **What is new**, which opens the release notes. **Check for
  updates** asks on demand and answers in place, which is also where you can see which version you
  are running. It can be switched off in Settings; the menu works either way.
- **Hear a score plan, and take it to a DAW.** The Score window's **Notation** tab plays the plan
  with abcjs, as the box has it: **Play**, the progress, restart and a tempo control sit above the
  staves, the note being played is picked out, and clicking a note puts the cursor on the ABC it
  came from. A plan is heard as it is edited, saved or not, none of it uses the engine, and closing
  the window or moving to another tab stops it. **Download MIDI** saves the score for a DAW, the
  chord symbols written out as a part of their own — the only place the harmony is written as notes
  — and a plan that changes its metre part way is written in the metre it starts in, while the notes
  keep their own lengths.
- **A corpus being prepared says so on its own card.** The badge in the top bar has said it since
  0.0.8; the Corpora screen says it on the corpus itself now — a dot pulsing beside its name and the
  word "preparing…" — kept current while the screen is open, so a corpus working through its songs
  is not one that merely looks unfinished.
- **Every voice plays the instrument the style names.** A score names none: YuE2 writes a melody, a
  second line and chord symbols. With **Instruments** ticked the preview reads the Style the take
  was made with and plays those lines with something that fits — a guitar, a piano, strings, a
  synth, whichever the words point at — stands in for a sung line with a voice, gives the chord
  symbols a part and a bass of their own, and adds drums when the style asks for them, written
  against the score's metre: a backbeat for rock, four to the floor for dance, a ride for jazz,
  something sparser for a ballad. The line beside the player says what it chose, and unticking it
  plays a piano throughout as before. It is a reading of the style, not of the render. Each
  instrument is fetched from its upstream publisher the first time it is used — about 7 MB each,
  kept in the library, offline afterwards — and a score that runs past what its instruments can
  play is shifted by whole octaves into range, with a line saying how far.

### Changed

- **The score preview's controls stay where they can be seen.** The editor's score box takes three
  quarters of the panel it sits in rather than a share of the window, so its heading, its hint and
  the buttons under it are in view on any screen. The chevron beside it has gone: the app holds the
  block open, so it invited a click that could do nothing. The tempo reads as one control instead
  of a dark box wedged against the "%", and the notation tab's caption — "Drawn from the ABC with
  abcjs. It follows your edits." — has gone, because the view showed what it described.
- **Play says when it is preparing.** A score is played from one buffer, prepared in advance, which
  takes a moment on a long one. The line beside the player says "Getting the preview ready…" until
  the first sound, rather than the control looking like it does not work.

### Fixed

- **Changing what a preview plays no longer stops it.** Unticking Instruments or Chords mid-song
  handed the score over again — that is how abcjs changes a tune, and handing it over stops
  playback — so the place in the song is taken before the hand-over and given back after it: still
  playing, still in the same place, and a preview that was paused keeps its place.
- **The line beside the player follows the score.** It was written once from an empty box and kept
  saying "This score has no notes in it yet." while a score played.

## 0.0.8 (2026-09-29)

### Added

- **Try more.** The dice button on a take card renders the same score and words again as several
  new takes: with new seeds, or, for a take with a style LoRA that has a planner half, the same seed
  at other Planner strengths. With a LoRA the result depends on the roll as much as on the
  strengths, and this makes a set to choose from in one go. The new takes are ticked with the
  original. Fixes #27.
- **Compare.** Tick two to six takes and press Compare to play them against each other on one
  shared position: switching keeps the place in the song. Levels can be matched, the names hidden
  for a blind listen, and the one you prefer starred. Fixes #28.

### Fixed

- **Some renders clipped.** A loud render could overshoot full scale by a few dB, and saving it as
  16-bit flattened every peak past it: about one take in six had flat tops, a few of them many.
  The engine now has a peak guard between the decode and the save: it turns the audio down around
  a peak that would clip, in floating point, for a few milliseconds either side, and leaves the
  rest alone, so a render's level changes by hundredths of a dB and no sample is flat-topped. The
  app uses it when the engine has it, so rebuild the engine (`docker compose build engine`) to get
  it; an older engine keeps saving renders as before. `PEAK_GUARD=0` turns it off. Fixes #4.

### Changed

- A take's title stays on one line, ending in an ellipsis when it is long, in the wide layout as
  in the compact one; the tooltip shows the whole title. In the wide layout the details and the
  prompt each keep two lines, and the status line keeps a place of its own, so the parts of a card
  sit at the same height on every card in a row.
- The Try more button has its own icon, a die drawn in three dimensions.
- The guide's advice on LoRA strengths says how to find a good take: the Sound strength changes the
  voice little between 0.3 and 0.6, and the Planner strength works like another seed.

## 0.0.7 (2026-09-29)

### Added

- **Search the takes.** A search box beside the library's filters finds takes with every word typed
  in the title, style, lyrics or LoRA name. It looks through the space on show, or every space with
  the All spaces chip, where a card from another space names it. The last few searches that found
  something are offered under the box. Fixes #26.

### Changed

- **Training takes as much of each song as the card allows.** The cut was a fixed 3½ minutes, so
  most songs in a corpus were cut short. `TRAIN_MAX_MINUTES` and `TRAIN_MAX_TOKENS` now default
  to `auto`: when a corpus is exported and when training starts, the app reads the graphics
  card's free memory and works out how much of each song the dataset builder can hold, and a
  context to fit (about 5½ minutes on a 16 GB card, never below 3½ nor above 6, nor past the
  longest song). The Logs window says what was chosen. Setting either to a number, such as
  `3.5`, overrides it, and a training run that runs out of memory now says so.
- **Training cuts a long song at a section end.** A song longer than the training limit was cut
  where the limit fell, mid-bar, with the whole song's words, so the planner learned that songs
  stop abruptly and were sung words they never reached. The export now cuts it at the end of the
  last section within the limit, fades it out, and keeps only the words of the sections that are
  still heard; with no section end near enough it cuts at the limit as before. The corpus window
  says how much of each long song is trained. Fixes #7.
- **Progress in the editor.** Transcribing a recording shows its progress under the recording's
  buttons, writing a score plan shows it on the Score page, and a take opened while it renders
  shows its render in the editor's bottom bar, as the job card behind the editor does. Each says
  when the job is queued behind another.

### Fixed

- The plan check let through plans that read as scores but couldn't be sung: a vocal line
  spanning more than three octaves, the metre changing more than four times, or a dozen chords
  with double sharps or flats. These are now caught, and, like any unreadable plan, written once
  more with a new seed before the take is marked failed. Fixes #5.
- A render that doesn't stop at the end of its score plays on to the length cap, and was cut off
  there mid-flow. A take stopped by its cap is now faded out over its last few seconds, and with a
  recording the cap allows about ten seconds past the score rather than thirty, so an overrun is
  short. Fixes #24.
- Now and then a render ended long before its score, and the take looked like a short song. A
  render that ends before 60% of its score is now tried once more with a new seed before it's
  called finished; if that ends early too, it's kept, and its card says it stopped early. Fixes #25.

## 0.0.6 (2026-09-28)

### Added

- **An instrumental from a recording.** Instrumental mode can take a recording, as a cover does,
  and render its transcription with the instrumental LoRA, with no plan to write. The structure is
  the score's own sections, so the whole score is played. A sung melody is given to an
  instrument wherever none plays, since a vocal part with notes makes the render sing, and an
  emptied one leaves gaps the model fills with humming. #21.
- **Ten more instrumental styles** under the Style box: acoustic pop, piano ballad, rock band,
  worship ballad, country, funk, blues, reggae, dance and orchestral, beside the first five.
- **Vocals and instruments.** Two more stem models, fast and fine tuned, split a take or a recording
  into the vocal and one **instruments** stem holding everything else, a backing track. Untick
  vocals to keep only the instruments. #20.
- **A corpus song's own style.** Picking a corpus song as the recording fills the Style box with
  the style it was learned with, as its chip has it, with the chosen LoRA's trigger word in front.
  Choosing a LoRA afterwards leaves a style typed by hand alone.

### Changed

- **The log window follows the theme,** the one in the app and the one popped out, where it
  stayed dark whatever the rest of the app wore, and in a light theme its buttons turned white on
  white.
- **The engine's own ComfyUI page is documented,** in the README and the guide: where it is, and
  that its jobs share the app's engine and GPU. Fixes #8.
- **The length cap follows a recording's score.** Choosing a recording, for a cover or an
  instrumental, sets the cap to its score's length with half a minute to spare, where 360 seconds
  would cut a longer song short. A cap typed by hand, or a take's own, is left alone.

### Fixed

- A training checkpoint, or a previous run's LoRA, showed none of its LoRA's learned styles. It now
  offers the same chips, and its **Download** carries them in the note. Fixes #17.
- A score in 6/8 was said to describe about twice the music its recording held, with a warning that
  its tempo was probably wrong when it was right. A score's length now counts each bar in quarter
  notes, a multi-bar rest as all its bars, and a change of meter part way. The same miscount could
  mark a corpus song *score: first N min* when the whole song was there. Fixes #18.
- Choosing a second recording left the first one's words in the Lyrics box, so a cover could be sung
  with another song's words. Words the app put in from a recording now follow the recording chosen,
  and go when it has none; words typed or edited in the box are replaced only after asking. Fixes #19.
- The vocal check on an instrumental listened to only three short spans, at a quarter, a half
  and three quarters, and missed a voice that came and went between them. It now hears a span from
  every fifteen seconds, so a voice lasting that long cannot fall between two. Fixes #22.
- Deleting a corpus could fail to mention its LoRA, found by a name search that missed a
  two-word name such as "First Second" in first_second_lora. It now uses the LoRA the corpus
  recorded, with its checkpoints and previous runs. Fixes #3.
- Renaming a normalised take moved its louder copy to a folder named after the new title and left
  the file as rendered in the old one, so Normalise could not be undone; the old folder stayed
  too. A rename now brings the file as rendered along and clears the old folder, and at start the
  app puts back any file as rendered an earlier rename left behind. Fixes #2.

## 0.0.5 (2026-09-28)

### Added

- **Themes.** Settings → Theme: Dark, as before; Light; Match the computer, following the
  system's light or dark; Studio, a warm dark with amber; and High contrast. It changes at once,
  and the browser remembers it so a page opens in it without a flash of the dark one. The log
  window stays dark in every theme.

### Fixed

- **+ Song** or **+ Instrumental** after a cover asked whether to discard score changes nobody had
  made. Fixes #16.
- **+ Song**, **+ Cover** and **+ Instrumental** kept the last take's style and settings. They now
  start from the defaults: an empty style (with a chosen LoRA's trigger word), a 360-second cap,
  Harmony Familiar, Plan variety normal, Interpretation Standard, Production polish on,
  Normalise off, and a new seed that is not held. A chosen LoRA stays chosen.

## 0.0.4 (2026-09-28)

### Added

- **Cover a song from a corpus.** The recording list offers every analysed corpus song, folded by
  corpus, with a filter. Picking one makes it a recording at once, with the score and words its
  analysis found, laid under the score's sections, and its separated vocal kept for Extract
  lyrics. The file is linked, not copied, where the disk allows. #14.
- **Filter a big LoRA's learned styles.** Past a dozen songs, a filter box and a row of the tags
  that recur across the corpus narrow the style chips, tags combining; the list shows its first
  dozen until Show all.
- **Finish a training run that ended early** from what it saved. The corpus window says when and
  why a run ended, and after which step; **Finish with what it saved** makes the trainer's best
  copy, or its last checkpoint, the LoRA, as a finished run does, with its checkpoints under it
  and no GPU time.
- **Run all** in the corpus window analyses, exports and trains one after the other, on the server,
  so a big corpus needs no one to wait for each step. It asks about an earlier LoRA first, analyses
  only what still needs it, leaves out and names any song whose analysis fails, and waits for
  anything already using the engine before it trains. #15.

### Fixed

- **Training no longer has a time limit.** A run was stopped at 2.5 hours, by a clock that did not
  look at progress, at step 1325 of 1400 while it was reporting a step every few seconds. The
  app told the engine to stop it. Training shows its progress and has Stop, and an engine that
  goes away, loses the job or dies is caught without a clock.
- The corpora badge could freeze on its last count, still pulsing, after one failed update during
  a restart. It now tries again.
- The New corpus window's folder picker had no way back from one of its starting folders to the
  list of them, and on Windows listed each subfolder by its whole path. It now has *all folders*
  there, and shows subfolders by name. Fixes #13.

## 0.0.3 (2026-09-27)

### Changed

- **A training run's checkpoints fold under their LoRA** in the Style LoRA list, behind a
  "▸ 9 steps" toggle beside its name, in step order, instead of sharing one Training checkpoints
  group with every other run's. A previous run's fold under its dated LoRA the same way. A
  checkpoint whose LoRA has been deleted stays in that group.

### Added

- **Same tune, new words.** The planner reads all the lyrics before it writes a note, so changed
  words get a new tune even with the same seed. When a take's words are changed in the editor,
  **Keep this tune** appears, ticked, and the main button sings the take's score with them instead:
  a new take with the same seed and whatever else the editor shows, leaving the original as it
  was. Untick it to write a new plan for the words. Before, rendering a take's score sang its saved
  words, whatever the editor held.
- **Delete a corpus's checkpoints from its Edit form.** **Training checkpoints** there lists each
  run's, this run's and any previous run's, with their sizes, to tick and delete in one go. Only
  step files: the finished LoRA keeps its own Delete LoRA, and a corpus that is training keeps its
  checkpoints until it finishes.

### Fixed

- Running out of GPU memory now says so. A job the engine failed that way said only the engine's
  CUDA error, and one lost when the engine crashed and restarted said "the engine lost the job".
  Both now say the GPU ran out of memory, with what to try, and a job lost to a restart for
  another reason says the engine stopped during it. The engine notes the error that kills its job
  thread for the app before it goes, and the app also keeps the error the engine sends for each
  job, so this does not rely on reading the engine's log, which is kept only as a fallback for an
  engine built before this. Rebuild the engine to get it. When the engine stays up without its
  job thread, still listing the dead job as running, the job fails at once instead of waiting out
  its time limit, the header says **Engine needs a restart**, and new jobs wait for the restart
  instead of queueing behind the dead one. The Train window warns before a run when less GPU
  memory is free than training needs. Fixes #12.
- The engine's start-up message, "To see the GUI go to", gave the engine's own address, and on
  Docker as 0.0.0.0, which a browser cannot open. It now gives the app's. On Docker the app's port
  can be moved with `APP_PORT` in `.env`, and the message follows it. Rebuild the engine to get
  it.
- On Docker, the app ran as user and group 1000 whatever the host's ids were, so on a host where
  yours differ its files belonged to a group, and perhaps a user, that does not exist there.
  `compose.yml` now reads `APP_UID` and `APP_GID` from `.env`, and `scripts/fetch-models.sh`
  writes yours there. An existing install can run the script again, or set them by hand; the
  README says how, and how to hand over the files written before. Fixes #11.
- Rendering a take's score again now uses the editor's style, style LoRA and strengths, length cap
  and mode. It kept the take's own, so choosing another LoRA and rendering changed nothing. With
  **keep this seed** unticked it now rolls a new seed, as the guide says, instead of reusing the
  take's.

## 0.0.2 (2026-09-27)

### Changed

- **The left panel is now a read-only sheet for the selected take,** and making and changing takes
  happens in an **editor window**: three columns with the score on a tab of its own, or steps, as
  **Settings → Editor layout** chooses. The panel's **+ Song**, **+ Cover** and **+ Instrumental**
  start something new; a card's Score and Again buttons, or a double-click on a card, open the
  editor. The panel folds away, from a chevron beside it, to give the takes the width.

### Fixed

- Opening a take in the editor now brings back its length cap, which kept whatever the last take
  had. The take panel shows the cap too.

## 0.0.1 (2026-09-27)

**Yeufonic 0.0.1: YuE2 Studio, renamed.** It carries on from YuE2 Studio 0.0.37, whose history and
changelog are in the archived repository, [dynamohum/YuE2gen-studio](https://github.com/dynamohum/YuE2gen-studio).
Everything YuE2 Studio did, Yeufonic does. The version numbers start again.

### Changed

- **The name.** The app, its Docker project, containers and images, the Windows installer and its
  install folder are now Yeufonic. "YuE2" still names the model the app runs.
- **On Windows, the page opens as soon as the app is up,** rather than after the engine. The engine
  starts alongside it, the header says *Engine starting…*, and anything asked for meanwhile waits.
  How long each took to start is kept in `logs\launcher.log`.
- **On Windows, Yeufonic runs like an app,** with no console window. It opens in a window of its
  own, in your default browser when that is Chrome, Edge, Brave or Vivaldi and otherwise in Edge,
  has an icon by the clock to reopen it or quit, and shows as *Yeufonic* in Task Manager.
  Closing the window leaves it running, and Quit asks first. *Yeufonic (with console)* in the
  Start menu keeps the old console for diagnosing.

### Added

- **Moving from YuE2 Studio:**
  - **Windows:** the installer finds a YuE2 Studio installation and updates it where it is, in
    its own folder. Your library, settings, LoRAs and models stay, so nothing is downloaded again.
  - **Docker:** a script moves them from an old clone into a new one.
- A saved take is tagged with its title, its lyrics and "Made with Yeufonic".
- Clicking a take's *Normalised* label undoes the normalise.
- **Normalise to** in Settings: how loud a normalised take is made, −16, −14 or −11 LUFS.

### Fixed

- Normalising a take whose peaks were already high could make its volume dip and swell. It now
  applies one gain to the whole take, and limits only the peaks that would clip.
