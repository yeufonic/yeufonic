# Handover Document: YuE2-Trainer LoRA Architecture Migration

## 1. Overview & Objectives

This document tracks the migration of Yeufonic's corpus LoRA training backend from `ComfyUI-FS_Audio_Suite` (`FSAudioArtistTrainer`) to `speedyrulz/ComfyUI-YuE2-Trainer` on branch `feature/yue2-trainer` (GitHub enhancement issue [#49](https://github.com/yeufonic/yeufonic/issues/49)).

### Primary Objectives:
- **Direct Replacement**: Seamlessly replace the `FS_Audio` training stack with `ComfyUI-YuE2-Trainer` across Docker and native Windows environments.
- **Eliminate Memory Bottlenecks**: Solve the quadratic attention memory explosion and multi-gigabyte VRAM spikes caused by full-song attention on Windows/Docker without FlashAttention.
- **Preserve Song Endings**: Eliminate the issue where long training songs lose their endings and structure, using structured token cropping (1/3 head, 1/3 middle, 1/3 tail) and prior preservation.
- **Maintain Full Backward Compatibility**: Produce merged `{identity_lora}.safetensors` files containing disjoint `diffusion_model.` (acoustic) and `text_encoders.` (planner) weights compatible with Yeufonic's existing `LoraLoader` workflows.
- **Permissive Licensing**: Replace the CC BY-NC 4.0 dependency (`ComfyUI-FS_Audio_Suite`) with Apache-2.0 (`ComfyUI-YuE2-Trainer`).

---

## 2. Upstream Architecture Comparison

| Feature | Legacy: `ComfyUI-FS_Audio_Suite` | Target: `ComfyUI-YuE2-Trainer` | Impact / Advantage |
| :--- | :--- | :--- | :--- |
| **VRAM Consumption** | ~14 GB VRAM for 4-5 min songs; full-song latent encoding | < 6 GB VRAM (< 4 GB in int8); 30s random crops | Enables training on 8 GB-12 GB cards without OOM |
| **Latent Encoding** | Full song loaded into VRAM simultaneously | 60s sliding window encoding cached to disk | Eliminates memory spikes during dataset prep |
| **Song Length Support** | Hard-capped at 3.5 minutes on 16 GB GPUs | Supports full songs (6+ minutes) via segmentation | No need to cut songs short or fade them out prematurely |
| **Attention Mechanism** | Grouped-Query Attention (GQA) with quadratic scaling on Windows | Standard segmented linear/SDPA crops with gradient checkpointing | Eliminates Windows PyTorch `enable_gqa` source monkey-patch |
| **End Token Learning** | Uniform random cropping rarely samples `</abc>` | Structured crop: 1/3 head, 1/3 middle, 1/3 tail | Guaranteed preservation of `</abc>` and song endings |
| **Prior Preservation** | Required external `minted_regularizer_pack_v2.pt` | `YuE2TrainerRegularizationScores` generates fresh scores | Self-contained; anchors style and phrasing without drift |
| **LoRA Key Naming** | Custom namespace or dual output | `diffusion_model.*` (MODEL) & `text_encoders.*` (CLIP) | 100% native ComfyUI `LoraLoader` compatibility |
| **Progress Reporting** | Custom WebSocket messages (`fsaudio.train`) | Standard `comfy.utils.ProgressBar` | Native websocket event handling |
| **Quantization Support** | Limited / bf16-only | Native int8 LoRA training on `yue2_3b_int8_convrot` | Lowers hardware bar significantly |
| **License** | CC BY-NC 4.0 | Apache-2.0 | Clean permissive open-source licensing |

---

## 3. Key Technical Findings

1. **Dual-Branch LoRA Key Compatibility & Automatic Merging**:
   - `YuE2TrainerAcousticLoRA` prefixes weights with `diffusion_model.`.
   - `YuE2TrainerPlannerLoRA` prefixes weights with `text_encoders.`.
   - In `app/jobs.py`, `train_graph()` saves `{lora_name}_planner.safetensors` (Node 8) and `{lora_name}_acoustic.safetensors` (Node 9).
   - `finish_training()` via `_merge_lora_files()` automatically merges both files into the single canonical `{lora_name}.safetensors` (and merges matching step checkpoints `{lora_name}_planner_stepN.safetensors` + `{lora_name}_acoustic_stepN.safetensors` into `{lora_name}_stepN.safetensors`), deleting the intermediate `_planner` and `_acoustic` files once merged.
   - ComfyUI's native `LoraLoader` loads the merged file simultaneously (routing `diffusion_model.*` to MODEL and `text_encoders.*` to CLIP via `strength_model` and `strength_clip`).

2. **Dataset Sidecar Structure**:
   - `YuE2TrainerDatasetFolder` scans for:
     - Audio: `.flac`, `.wav`, `.mp3`, `.ogg`, `.m4a`, `.opus`
     - Captions/Tags: `{name}.style.txt` (or `.tags.txt` or `{name}.json`)
     - Lyrics: `{name}.lyrics.txt` (or `.txt`)
     - ABC Scores: `{name}.abc`
   - `_export()` in `app/main.py` now writes `{name}.style.txt`, `{name}.json` (`style`, `lyrics`, `title`), `{name}.lyrics.txt`, `{name}.txt` (for legacy compatibility), and copies `score.abc` to `{name}.abc` when present on the corpus song.

3. **Progress Tracking & Stage Weights**:
   - Every node in `ComfyUI-YuE2-Trainer` uses `comfy.utils.ProgressBar(total)`, emitting standard `"progress"` websocket events with `value` and `max`.
   - `app/engine.py` registers `YuE2TrainerDatasetFolder`, `YuE2TrainerEncodeDataset`, `YuE2TrainerRegularizationScores`, `YuE2TrainerPlannerLoRA`, `YuE2TrainerAcousticLoRA`, `YuE2TrainerSaveLoRA`, and `YuE2TrainerMergeLoRA` in `STAGE_LABELS` and `STAGE_WEIGHT`.
   - Backward compatibility with legacy `fsaudio.train` websocket messages and `FSAudioArtistTrainer` node detection is retained so existing environments or historical test cases continue to work.

4. **Song Duration Sizing**:
   - In `app/config.py`, the auto default for `TRAIN_MAX_MINUTES` was raised from `3.5` minutes to `6.0` minutes because 60-second sliding-window VAE encoding (`window_seconds=60`) and 30-second training crops (`segment_seconds=30.0`) bound VRAM usage independently of full song length.

5. **Test Suite Event-Loop Hang Resolution (`tests/test_run_all.py`)**:
   - During full-suite verification, `tests/test_run_all.py` hung when crossing the 2-second boundary (`OPTIONS_EVERY = 2.0` / `jobs.keeper()` 2.0s sleep).
   - Root cause: `chain` fixture in `tests/test_run_all.py` patched `main.asyncio.sleep` globally (`lambda _s: REAL_SLEEP(0)`), which also affected `TestClient`'s background portal thread where `ENGINE._options_loop()` runs `while True: await asyncio.sleep(OPTIONS_EVERY); if not self.online: continue`. A 0ms sleep turned `_options_loop` into an infinite tight spin loop that starved `TestClient.__exit__()`.
   - Fix: Scoped the `REAL_SLEEP(0)` fast-forward in `tests/test_run_all.py` to `threading.current_thread() is test_thread` so `main._run_all_chain` sleeps are instant while background daemon loops keep real sleep timing.

---

## 4. Implementation Steps (All Completed)

- [x] **Step 1: Dual-Branch Save & Merge Pipeline (`app/jobs.py`)**
  - Implemented `_merge_lora_files(lora_dir, stem)` in `app/jobs.py` using `safetensors.torch` to combine `{stem}_planner.safetensors` (`text_encoders.*`) and `{stem}_acoustic.safetensors` (`diffusion_model.*`) into `{stem}.safetensors`, plus per-step checkpoints (`{stem}_stepN.safetensors`).
  - Preserved fallback promotion of `{stem}_best.safetensors` and single-branch outputs.
- [x] **Step 2: Training Graph Pipeline in `app/jobs.py`**
  - Replaced `train_graph()` with the 9-node `ComfyUI-YuE2-Trainer` workflow:
    - Node `"1"`: `CheckpointLoaderSimple` (`config.CHECKPOINT`)
    - Node `"2"`: `AudioEncoderLoader` (`sheetsage2_bf16.safetensors`)
    - Node `"3"`: `YuE2TrainerDatasetFolder` (staged input directory, `caption_prefix=trigger`, `cache_in_folder=True`)
    - Node `"4"`: `YuE2TrainerEncodeDataset` (`window_seconds=60`, `transcribe="full"`, `max_seconds=max_minutes * 60`)
    - Node `"5"`: `YuE2TrainerRegularizationScores` (`scores_per_prompt=1`, `mode="full"`)
    - Node `"6"`: `YuE2TrainerPlannerLoRA` (CLIP AR next-token on ABC scores, `rank`, `alpha=rank*2`, `lr=lr*2`, `prior_loss_weight=0.3`, `save_every`)
    - Node `"7"`: `YuE2TrainerAcousticLoRA` (MODEL flow matching on 30s latents, `rank`, `alpha=rank*2`, `lr`, `keep="best_eval"`, `ema_decay=0.99`, `save_every`)
    - Node `"8"`: `YuE2TrainerSaveLoRA` (`{lora_name}_planner`)
    - Node `"9"`: `YuE2TrainerSaveLoRA` (`{lora_name}_acoustic`)
- [x] **Step 3: Engine Node Registration & Progress Tracking (`app/engine.py`)**
  - Added `YuE2Trainer*` nodes to `STAGE_LABELS`, `STAGE_WEIGHT`, `JOB_KINDS`, and `_handle_ws`.
  - Updated `self.options["trainer"]` to detect `YuE2TrainerAcousticLoRA`, `YuE2TrainerPlannerLoRA`, or `FSAudioArtistTrainer`.
- [x] **Step 4: Dataset Export Updates (`app/main.py`)**
  - Updated `_export()` to write `{name}.style.txt`, `{name}.json`, `{name}.lyrics.txt`, `{name}.txt`, and `{name}.abc` (when `score.abc` exists on the song).
- [x] **Step 5: Relax Memory & Sizing Constraints (`app/config.py`)**
  - Raised default auto `TRAIN_MAX_MINUTES` from `3.5` to `6.0` minutes and updated documentation comments.
- [x] **Step 6: Packaging, Licensing & Installation Scripts**
  - Updated `engine/Dockerfile` to install `speedyrulz/ComfyUI-YuE2-Trainer` pinned to commit `6a9355efff60589d93b41b569676f09d5db85d09`.
  - Updated `windows/setup.ps1` (`$Yue2TrainerCommit = '6a9355efff60589d93b41b569676f09d5db85d09'`), removed the `enable_gqa` source patch and obsolete `models\fs_audio` copy.
  - Updated `scripts/fetch-models.sh` and `scripts/check-upstream.sh`.
  - Updated `THIRD_PARTY_NOTICES.md`, `windows/terms.txt`, and `windows/README.md` to reflect `ComfyUI-YuE2-Trainer` (Apache-2.0).
- [x] **Step 7: Test Suite Updates & Verification**
  - Updated `tests/test_graphs.py`, `tests/test_lora_training.py`, and `tests/test_installer_script.py`.
  - Fixed thread-unsafe `asyncio.sleep` monkeypatch in `tests/test_run_all.py`.
- [x] **Step 8: Grouped Settings Sub-Folders & Material LoRA Training Options (`app/main.py`, `app/jobs.py`, `app/static/app.js`, `app/static/index.html`, `app/static/styles.css`)**
  - Organised the Settings panel into 5 collapsible sub-folder sections (`<details class="settings-group">`):
    1. **Audio, Takes & Stems** (`audio` — open by default)
    2. **LoRA Training** (`training` — dedicated section for `ComfyUI-YuE2-Trainer` options)
    3. **External LLM & Lyrics** (`llm` — includes the `Test LLM Connection` button inside the section)
    4. **Take Pictures** (`art`)
    5. **Appearance & System** (`system`)
  - Added and wired 7 material LoRA training settings:
    - `training.branches` (`both`, `acoustic`, `planner`): controls whether both Planner + Acoustic, Acoustic-only, or Planner-only nodes are built and executed.
    - `training.regularization` (`on`, `75%`, `50%`, `25%`, `10%`, `off`): enables `YuE2TrainerRegularizationScores` for 100% of corpus songs (`on`, default), samples an evenly spaced percentage of corpus songs (`75%`, `50%`, `25%`, `10%`), or skips prior-preservation (`off`) and sets `regularization_fraction` (`0.5` vs `0.0`).
    - `training.semantic_tokens` (`off`, `on`): toggles SheetSage semantic token training (`train_semantic` on Planner, `use_semantic_tokens` + `train_acoustic_head` on Acoustic).
    - `training.keep_strategy` (`best_eval`, `final`): toggles validation holdout + EMA smoothing (`keep="best_eval"`, `ema_decay=0.99`, `eval_holdout=1`) vs exact final step weights (`keep="final"`, `ema_decay=0.0`, `eval_holdout=0`).
    - `training.targets` (`attention+mlp`, `attention`): selects full attention + MLP projections vs attention-only projections.
    - `training.max_minutes` (`auto`, `4`, `6`, `8`, `0`): overrides per-song training cut duration across `_train_sizing()`, `_export()`, and `YuE2TrainerEncodeDataset` (`0` = full song with no length cut).
    - `training.allow_int8` (`off`, `on`): allows training on the quantized `yue2_3b_int8_convrot.safetensors` low-memory checkpoint when enabled.
- [x] **Step 9: Automated Dataset Tagging & Corpus Analysis Enhancements (`app/identities.py`, `app/jobs.py`, `app/main.py`)**
  - **LRCLIB Studio Lyrics Lookup (`fetch_lrclib`, `parse_lrc`, `lyrics_match_transcript`, `file_metadata`, `parse_stem`)**:
    - Extracts artist, title, and duration from audio file tags or `Artist - Title` filenames (`parse_stem`).
    - Queries `lrclib.net` (`/api/get` and `/api/search` within an 8-second duration tolerance) for synced LRC (`[mm:ss.xx]`) or plain studio lyrics, logging every lookup attempt and outcome (`querying LRCLIB`, `LRCLIB matched transcript`, `rejected`, or `no match on LRCLIB`).
    - Verifies LRCLIB matches against Whisper's transcript (`lyrics_match_transcript >= 0.35`) so wrong-song matches are rejected automatically.
    - Stores verified LRCLIB lyrics in `lyrics-llm.json` / `lyrics-lrclib.txt` (`model: "LRCLIB"`) alongside `lyrics-whisper.json` so users can toggle between LRCLIB and Whisper in the Corpus UI.
    - Controlled via the new `lyrics.lrclib` setting in **External LLM & Lyrics** (`on` by default).
  - **Stanza-Repetition Section Tag Heuristic (`heuristic_sections`, `plain_to_sections`, `tag_lyrics`)**:
    - Groups timed lines by vocal pauses (`gap_seconds=2.5`) and stanza length (`max_lines=6`), fuzzy-matches lines (`_block_overlap >= 0.6`), and promotes repeated stanzas to `[Chorus]` while marking `[Intro]` when vocals start after 8 seconds.
    - Formats stanza-separated plain lyrics from LRCLIB into `[Verse]` and `[Chorus]` blocks (`plain_to_sections`).
    - Automatically promotes repeated stanzas to `[Chorus]` in `tag_lyrics()` when SheetSage sections are absent or only contain `[Verse]` markers.
  - **Krumhansl-Schmuckler Key & BPM Detection (`audio_key_and_tempo`, `key_and_tempo`)**:
    - Computes 12-bin pitch-class chroma profiles correlated against Krumhansl-Schmuckler `MAJOR_PROFILE` / `MINOR_PROFILE` (`KEYS = ["C", ..., "B"]`) and measures BPM via `librosa.beat.beat_track` + `librosa.feature.chroma_cqt` (with a pure-`numpy` STFT chroma + onset-autocorrelation fallback when `librosa` is not installed in the app container).
    - Used by `key_and_tempo(abc, audio)` and `run_identity_job("identity_score")` whenever `score.abc` omits `K:` / `Q:` or when score transcription fails.
- [x] **Step 10: External LLM Error Pop-up & Session-Local Fallback (`app/llm.py`, `app/main.py`, `app/jobs.py`, `app/artwork.py`, `app/static/index.html`, `app/static/app.js`, `app/static/styles.css`)**
  - Added session-scoped fallback and alert tracking (`record_alert`, `record_alert_from_exception`, `set_session_local_only`, `dismiss_alert`, `alert_state`) in `app/llm.py`.
  - Exposed `llm_status` in `/api/state` and added `POST /api/llm/session-fallback` (`local_session`, `resume_external`, `dismiss`) in `app/main.py`.
  - Added `#llm-alert-modal` pop-up in the UI when an external LLM error (such as HTTP 429 quota/spending cap) occurs, explaining the failure and letting the user choose between:
    - **Switch to Local for This Session**: Uses local models for all remaining tasks until Yeufonic restarts (without modifying the saved `llm.provider` setting on disk).
    - **Keep Trying External LLM**: Dismisses the pop-up and continues using the external LLM (e.g. after increasing an API spending cap).
  - Added `#llm-session-pill` in the topbar and a session banner with a **Resume External LLM** button in **Settings → External LLM & Lyrics** so the user always sees when session-local mode is active and can resume external LLM at any time without restarting.
- [x] **Step 11: GitHub Enhancement Issue**
  - Created enhancement issue [#49](https://github.com/yeufonic/yeufonic/issues/49) (`Migrate corpus LoRA training backend to ComfyUI-YuE2-Trainer`) with the feature objectives and the comparison table from Section 2.
- [x] **Step 12: Cross-Platform VRAM & Host RAM Cleanup, 32 GB System RAM Checks, and Percentage-Based Regularization Prompt Sampling (`app/engine.py`, `app/trainsize.py`, `app/jobs.py`, `app/main.py`, `app/static/app.js`, `engine/custom_nodes/yue2_harmony/*.py`, `README.md`, `app/static/guide.md`)**
  - Unloaded `faster-whisper` (`CTranslate2`) CUDA weights and ran `gc.collect()` immediately in `engine/custom_nodes/yue2_harmony/hear.py` so Whisper's ~1.6 GB of GPU VRAM is freed after corpus transcription instead of lingering outside PyTorch's allocator.
  - Added `separate.clear_cache()` and `POST /yeufonic/free` in `engine/custom_nodes/yue2_harmony/watch.py` (called from `ENGINE.free()`, followed by `refresh_status()`) to unload custom-node caches, ComfyUI staged models, CUDA caches (`empty_cache` + `ipc_collect`), and OS heap/working-set memory across both Linux (`malloc_trim(0)`) and Windows (`SetProcessWorkingSetSize`).
  - Added system RAM tracking (`ram_total`, `ram_free`) to `ENGINE.gpu()` and `trainsize.py` (`MIN_RAM_GB = 28.0`, corresponding to 32 GB physical / WSL2 RAM), surfacing a clear pre-flight warning in `#train-memory` (`paintTrainMemory()`), `run_lora_train()`, `_lost()`, `README.md`, and `app/static/guide.md` (including `.wslconfig` `memory=32GB` guidance on WSL2).
  - Expanded `training.regularization` in Settings to support `off` (default), percentage-based sampling (`75%`, `50%`, `25%`, `10%` evenly spaced corpus prompts via `_sample_regularization_prompts()`), and `on`.
- [x] **Step 13: Live VRAM Display on Training LoRA Button & Pinned Memory Fix (`app/static/app.js`, `compose.yml`, `windows/launcher.py`, `app/jobs.py`, `app/main.py`)**
  - Updated `#engine-pill` in `app/static/app.js` during training to display live VRAM utilisation matching the idle engine pill format: `Training LoRA · <used> / <total> GB` (e.g. `Training LoRA · 11.2 / 16 GB`, with tooltip `LoRA “...” is training and holds the GPU (11.2 GB used · 4.8 GB free of 16 GB VRAM). Click to view in Corpora.`).
  - Added `--disable-pinned-memory` to `engine` startup in both `compose.yml` (Docker) and `windows/launcher.py` (native Windows) to prevent ComfyUI from pre-locking 40–90% of host RAM in pinned memory DMA buffers.
  - Reduced `max_abc_tokens` in `YuE2TrainerRegularizationScores` (`train_graph()` in `app/jobs.py`) from 8,192 to 2,048 tokens to keep reference scores within normal song length and eliminate multi-minute LLM generation loops.
  - Set default and fallback for `training.regularization` in `app/main.py` and `app/jobs.py` (`run_lora_train()`) to `off` so training defaults to pure corpus fitting without heavy pre-training LM generation, while wiring `kl_weight: 0.5` into `YuE2TrainerPlannerLoRA` when regularization is off (giving prior preservation mathematically on existing corpus positions with zero synthetic generation or extra memory).
- [x] **Step 14: Acoustic Conditioning Mode & Kernel OOM Elimination (`app/jobs.py`, `app/main.py`, `tests/test_graphs.py`, `tests/test_lora_training.py`)**
  - **Root Cause of Engine Restarts (Linux OOM-Kill)**:
    - Kernel logs (`dmesg` / `journalctl`) revealed process `14103` (`python main.py`) was killed by the Linux kernel OOM-killer at `31,550,356 kB` anon-RSS (~31.55 GB) exceeding WSL2's 32 GB memory allocation.
    - Deep analysis revealed the bottleneck in `YuE2TrainerAcousticLoRA`'s `prepare_samples()`: previously hardcoded to `"conditioning": "inference_like"`, the trainer eager-precomputed the full 32-layer rotary-encoded key/value attention cache (`compute_prefix_kv()`) for every song's style + lyrics + full ABC notation (~3,000 tokens) using the 4B language model. Storing these uncompressed 32-layer KV tensors simultaneously in host RAM for 71 songs allocated ~35 GB of system RAM.
  - **Compact Conditioning Resolution**:
    - Switched `YuE2TrainerAcousticLoRA`'s conditioning default in `train_graph()` from `"inference_like"` to upstream's recommended `"compact"` mode. In `"compact"` mode, the acoustic diffusion model conditions on the style prompt prefix (~30 tokens) with latent positions restarting per 30-second segment (tested by upstream to be identical in audio quality and timbre).
    - Reduced host RAM footprint for all 71 songs from **~35 GB** down to **1.04 GB** (total process RSS during training measured live inside `yeufonic-engine` at only **7.36 GB**, with GPU VRAM at only **2.95 GB**).
    - Exposed `training.conditioning` in **Settings → LoRA Training** (`compact` [Recommended, < 8 GB RAM] vs `inference_like` [high RAM, 64 GB+ needed]) and wired it into `run_lora_train()` and `train_graph()`.
    - Added comprehensive regression tests in `tests/test_graphs.py` and `tests/test_lora_training.py`.
- [x] **Step 15: Dual-Branch LoRA Checkpoint Merging ("Score and Sound") & Post-Lyrics VRAM Cleanup (`app/jobs.py`, `engine/Dockerfile`, `docs/HANDOVER_YUE2_TRAINER.md`)**
  - **LoRA Branch Merging**:
    - Identified that when both branches (acoustic decoder + planner) are trained, `safetensors.torch.load_file` on unprivileged `0600` files raised `FileNotFoundError` (standard Rust error mapping for open failures), causing `_merge_lora_files` to merge only the acoustic half into `fountain_lora.safetensors` ("sound only").
    - Merged the trained planner weights (`text_encoders.*`, 336 tensors) and acoustic weights (`diffusion_model.*`, 348 tensors) into `fountain_lora.safetensors` (684 tensors total), converting it to `'both'` ("score and sound").
    - Hardened `finish_training()` in `app/jobs.py` to only unlink source branch files if both branches successfully merged (`len(merged_meta.get("parts", [])) == 2`).
    - Extended intermediate checkpoint discovery to support both `_step50` and `_000050` patterns and automatically clean up intermediate `.resume` files (~16 GB disk savings).
  - **Local LLM VRAM Release**:
    - Identified that when the external LLM is rate-limited or hits its spending cap, local Gemma (`Gemma4TEModel_`, ~7.65 GB) runs in ComfyUI and stays cached in GPU VRAM (consuming ~12.2 GB total VRAM).
    - Wired `await ENGINE.free()` directly into `_finish()` in `app/jobs.py` for `kind == "lyrics"`, automatically unloading Gemma and flushing CUDA cache back to idle VRAM levels (~5.2 GB total, >11 GB free) immediately after lyric drafting finishes.

- [x] **Step 16: Automated Dual-Branch Step Merging & Optimizer Resume File Cleanup (`app/jobs.py`, `tests/test_lora_training.py`, `docs/HANDOVER_YUE2_TRAINER.md`)**
  - **Intermediate File Anatomy & Disk Overhead**:
    - Dual-branch training with `ComfyUI-YuE2-Trainer` saves two sets of intermediate snapshots every `save_every` steps (default 50 steps): acoustic (`diffusion_model.*`, ~57 MB) and planner (`text_encoders.*`, ~113 MB).
    - Additionally, upstream saves the complete PyTorch optimizer state dict (AdamW moments, momentum tensors, and RNG states) as a sibling `<name>.resume` file (~450 MB each) alongside every checkpoint and the final LoRAs. Across a 1,000-step acoustic run and 700-step planner run, `.resume` files alone consumed **~15.5 GB** of disk space.
    - Upstream also writes un-averaged weights as `<name>_raw.safetensors`.
  - **Automated Merging & Purge in `finish_training()`**:
    - Updated `finish_training()` in `app/jobs.py` to group all branch step checkpoints (`planner_steps` and `acoustic_steps`), merge corresponding acoustic + planner pairs into unified canonical `{name}_step{N}.safetensors` (169 MB) with mode `0644`, and unlink all branch parts.
    - After canonical LoRA finalization, `finish_training()` automatically deletes all remaining `f"{name}_acoustic*"`, `f"{name}_planner*"`, `f"{name}*.resume"`, and `f"{name}*.tmp"` files.
    - When `training.checkpoints` is set to `"keep"`, only the unified listening checkpoints (`{name}_stepN.safetensors`) and notes are retained (as in the legacy trainer); when set to `"delete"`, even the step checkpoints are removed, keeping only the final merged `{name}.safetensors`.
    - Manually purged the leftover intermediate files from the `fountain` run, reducing disk usage from **21 GB** to **2.8 GB** (over 18 GB reclaimed).
    - Added comprehensive regression test `test_finish_training_cleans_up_dual_branch_and_resume_files` in `tests/test_lora_training.py`.

---

## 5. Modified Files Summary

- `app/config.py`: Raised default auto `TRAIN_MAX_MINUTES` from `3.5` to `6.0` and updated comments for `ComfyUI-YuE2-Trainer`.
- `app/engine.py`: Registered `YuE2Trainer*` stage labels, progress weights, job kinds, and trainer node detection; included `ram_total` and `ram_free` in `ENGINE.gpu()`; updated `ENGINE.free()` to trim memory cross-platform, call `/yeufonic/free`, and refresh engine status immediately.
- `app/trainsize.py`: Added `MIN_RAM_GB = 28.0`, `ram_gb()`, and `ram_tight` in `card_limit()`, `choose()`, and `for_corpus()`.
- `app/identities.py`: Added `parse_stem()`, `file_metadata()`, `parse_lrc()`, `fetch_lrclib()`, `lyrics_match_transcript()`, `heuristic_sections()`, `plain_to_sections()`, `audio_key_and_tempo()`, and Krumhansl-Schmuckler chroma correlation (`MAJOR_PROFILE`, `MINOR_PROFILE`).
- `app/llm.py`: Added session-local fallback state and external LLM failure alert tracking (`record_alert`, `set_session_local_only`, `dismiss_alert`, `alert_state`).
- `app/artwork.py`: Updated `external_ready()` to respect `llm.is_session_local_only()`.
- `app/jobs.py`: Replaced `train_graph()` with the configurable `YuE2Trainer` pipeline supporting branch selection, regularization toggle/sampling (`_sample_regularization_prompts`), semantic tokens, keep strategy, target modules, and compact acoustic conditioning; reduced `max_abc_tokens` in `YuE2TrainerRegularizationScores` from 8192 to 2048; added `_merge_lora_files()` in `finish_training()`; automated dual-branch step checkpoint merging and `.resume` / `_raw` file cleanup; wired `ENGINE.free()` after lyrics generation to instantly unload local Gemma from VRAM; integrated LRCLIB lookup and audio key/tempo fallback into `prepare_song()`, `hear_all()`, `maybe_draft()`, and `run_identity_job()`; wired `llm.record_alert_from_exception()` into external LLM fallback paths; added system RAM warnings in `run_lora_train()` and `_lost()`.
- `app/main.py`: Added `group` metadata to `SETTINGS_SPEC`, added the 8 `training.*` settings (defaulting `training.regularization` to `off` and `training.conditioning` to `compact`) and `lyrics.lrclib`, wired `training.max_minutes` into `_train_sizing()` and `training.allow_int8` into `train_identity()`, extended `_export()` to write `.style.txt`, `.json`, and `.abc` sidecars, exposed `llm_status` in `/api/state`, and added `POST /api/llm/session-fallback`.
- `app/static/app.js`, `app/static/index.html`, `app/static/styles.css`, `app/static/guide.md`, `README.md`: Grouped Settings into collapsible `<details class="settings-group">` sub-folders, added array support to `paintSettingRequirements()`, added live VRAM utilisation to the Training LoRA pill (`Training LoRA · <used> / <total> GB`), added the `#llm-alert-modal` pop-up, `#llm-session-pill` topbar indicator, and Settings session banner, and added 32 GB system RAM / WSL2 `.wslconfig` checks and documentation.
- `compose.yml`: Added `--disable-pinned-memory` to ComfyUI startup command.
- `windows/launcher.py`: Added `--disable-pinned-memory` to ComfyUI startup command.
- `engine/custom_nodes/yue2_harmony/hear.py`, `separate.py`, `watch.py`: Unloaded CTranslate2 Whisper CUDA model after transcription, added `separate.clear_cache()`, and added `/yeufonic/free` for cross-platform VRAM and host RAM release.
- `engine/Dockerfile`: Switched custom node clone from `ComfyUI-FS_Audio_Suite` to `ComfyUI-YuE2-Trainer` (`6a9355efff60589d93b41b569676f09d5db85d09`), with post-save `0o644` permissions patch on `save_lora_file`.
- `windows/setup.ps1`: Switched Windows installer to `ComfyUI-YuE2-Trainer`, removed `enable_gqa` monkey-patch and obsolete `models\fs_audio` copy.
- `scripts/fetch-models.sh`: Removed obsolete `models/fs_audio` copy step.
- `scripts/check-upstream.sh`: Switched upstream tracking entry to `speedyrulz/ComfyUI-YuE2-Trainer`.
- `THIRD_PARTY_NOTICES.md`, `windows/terms.txt`, `windows/README.md`: Updated third-party notices and license attribution to `ComfyUI-YuE2-Trainer` (Apache-2.0).
- `tests/test_identities.py`, `tests/test_llm.py`, `tests/test_graphs.py`, `tests/test_lora_training.py`, `tests/test_trainsize.py`, `tests/test_installer_script.py`, `tests/test_run_all.py`: Updated assertions for the new training pipeline, added tests for the 8 training settings, regularization prompt sampling, system RAM threshold checks, Settings sub-folders, LRCLIB lookup, heuristic section tagging, Krumhansl-Schmuckler key/BPM detection, External LLM error alert & session-local fallback, and dual-branch checkpoint merging + intermediate file purge.





