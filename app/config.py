"""Settings that come from the environment, read once at import."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# compose.yml sets this to the engine service name.  The fallback suits running the
# app outside Docker against an engine on the same machine.
ENGINE_URL = os.environ.get("ENGINE_URL", "http://127.0.0.1:8188")

# The version lives in ./VERSION at the repo root, copied into the image by the
# Dockerfile.  It is shown in the header so a running container can be identified.
VERSION_FILE = Path(os.environ.get("VERSION_FILE", "/app/VERSION"))
try:
    VERSION = VERSION_FILE.read_text(encoding="utf-8").strip()
except OSError:
    VERSION = "unknown"

# Which build of this version is running: a short commit id and the date, written beside VERSION
# when an image or an installer is built.  The same version number can be rebuilt, so the number
# alone does not say.  Empty when the copy was not built with one.
BUILD_FILE = Path(os.environ.get("BUILD_FILE", "/app/BUILD"))
try:
    BUILD = BUILD_FILE.read_text(encoding="utf-8").strip()
except OSError:
    BUILD = ""


def get_branch() -> str:
    """Detect which git branch is active, checking environment variables, .git/HEAD
    (in standard checkouts, worktrees, and mounted container paths), and branch marker files."""
    env_branch = os.environ.get("YEUFONIC_BRANCH") or os.environ.get("GIT_BRANCH")
    if env_branch:
        return env_branch.strip()

    # Search for .git directory or worktree reference
    candidates: list[Path] = [
        Path("/app/.git"),
        Path(__file__).resolve().parent.parent / ".git",
        Path.cwd() / ".git",
    ]
    for git_dir in candidates:
        try:
            head_file: Path | None = None
            if git_dir.is_dir():
                head_file = git_dir / "HEAD"
            elif git_dir.is_file():
                txt = git_dir.read_text(encoding="utf-8").strip()
                if txt.startswith("gitdir:"):
                    head_file = Path(txt.split(":", 1)[1].strip()) / "HEAD"
            if head_file and head_file.exists():
                content = head_file.read_text(encoding="utf-8").strip()
                if content.startswith("ref: refs/heads/"):
                    return content.removeprefix("ref: refs/heads/")
                if len(content) >= 7:
                    return content[:8]
        except (OSError, UnicodeDecodeError):
            continue

    # Fallback to marker files in app or repo
    for marker in [
        Path(__file__).resolve().parent / ".branch",
        Path(__file__).resolve().parent / "BRANCH",
        Path("/app/BRANCH"),
    ]:
        try:
            if marker.exists():
                val = marker.read_text(encoding="utf-8").strip()
                if val:
                    return val
        except (OSError, UnicodeDecodeError):
            continue

    return ""


BRANCH = get_branch()

# A test build of the Windows installer sets this (through settings.ini) to a manifest that only
# the tester knows, so an update can be tried before it is released.  When it is set, nothing
# else is asked, GitHub included.  Public builds never set it.
UPDATE_MANIFEST = os.environ.get("YEUFONIC_UPDATE_MANIFEST", "").strip()

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
PORT = int(os.environ.get("PORT", "8090"))
DB_PATH = DATA_DIR / "yue2.sqlite"
# Where DATA_DIR is on the host, when the app runs in a container, so a folder the
# app wrote can be named the way the user will find it.  Optional.
DATA_DIR_HOST = os.environ.get("DATA_DIR_HOST", "").rstrip("/")
# Where to put songs a corpus should be built from.  The app offers this folder to
# whoever is making one, so nothing has to be mounted or browsed for: copy the files
# in, and the corpus screen shows them.
CORPUS_INBOX = Path(os.environ.get("CORPUS_INBOX", str(DATA_DIR / "corpus")))
STEMS_DIR = DATA_DIR / "stems"
TAKES_DIR = DATA_DIR / "takes"
SOURCES_DIR = DATA_DIR / "sources"
# Scratch space on the same filesystem as the library, so finished work is moved
# into place with a rename rather than a copy.  Emptied on every start.
WORK_DIR = DATA_DIR / "tmp"

# The engine's output folder, when the app can see it (compose.yml mounts it).  A
# rendered file is deleted from there once the app has its own copy.  Unset in the
# split setup, where the folder lives on another machine.
ENGINE_OUTPUT_DIR = Path(os.environ["ENGINE_OUTPUT_DIR"]) if os.environ.get("ENGINE_OUTPUT_DIR") else None
# The engine's input folder, so a training set can be put where the engine can read it.
ENGINE_INPUT_DIR = Path(os.environ["ENGINE_INPUT_DIR"]) if os.environ.get("ENGINE_INPUT_DIR") else None

# The largest recording the app will take.  Two gigabytes is a long lossless source:
# an eleven minute 24/96 FLAC is around 260 MB.  The engine has its own ceiling for
# what it will accept, set to the same number in compose.yml; if this is raised, that
# wants raising with it.
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "2048"))

# Folders the app may read songs from for an identity, as paths inside the container.
# compose.yml mounts them read-only.  Nothing under them is ever written.
IMPORT_ROOTS = [p.strip() for p in os.environ.get("IMPORT_ROOTS", "/import").split(",") if p.strip()]

# Host names the app answers to.  Anything else is refused, which stops DNS
# rebinding.  "*" turns the check off.
ALLOWED_HOSTS = [h.strip().lower() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,::1").split(",") if h.strip()]

# The models the app uses.  One YuE2 checkpoint, and Gemma for writing lyrics.
# The YuE2 model comes in two sizes and an install has one of them: the full-quality BF16 file, which
# is the recommendation, or the smaller INT8 file for GPUs with little memory.  CHECKPOINT is the one
# in use: it starts as BF16 and is set from what the engine reports it has (choose_checkpoint), so
# nothing has to be configured.  YUE2_CHECKPOINT ("bf16", "int8" or a file name) forces one.
CHECKPOINT_BF16 = "yue2_3b_bf16.safetensors"
CHECKPOINT_INT8 = "yue2_3b_int8_convrot.safetensors"
CHECKPOINT = CHECKPOINT_BF16
# Training learns from the full-quality model only.
TRAIN_CHECKPOINT = CHECKPOINT_BF16
CHECKPOINT_LABELS = {CHECKPOINT_BF16: "Full quality (BF16)", CHECKPOINT_INT8: "Low memory (INT8)"}


def choose_checkpoint(installed: list[str] | None) -> str:
    """The model to use, given the checkpoints the engine can see: what YUE2_CHECKPOINT names when
    it is set, else BF16 when it is there, else INT8, else BF16 (so the message about the missing
    file names the usual one)."""
    wanted = os.environ.get("YUE2_CHECKPOINT", "").strip()
    wanted = {"bf16": CHECKPOINT_BF16, "int8": CHECKPOINT_INT8}.get(wanted.lower(), wanted)
    if wanted:
        return wanted
    for name in (CHECKPOINT_BF16, CHECKPOINT_INT8):
        if name in (installed or []):
            return name
    return CHECKPOINT_BF16
def installed_picture_pair(pairs: tuple, models: list[str] | None, encoders: list[str] | None) -> tuple[str, str] | None:
    """The first of these klein model and text encoder pairs whose two files are both installed, or None."""
    for model, encoder in pairs:
        if model in (models or []) and encoder in (encoders or []):
            return model, encoder
    return None


def choose_picture_files(models: list[str] | None, encoders: list[str] | None) -> tuple[str, str]:
    """The klein 4B model and text encoder to draw with: the first pair of PICTURE_PAIRS whose two
    files are both installed, else the first pair (so a message about missing files names it)."""
    return installed_picture_pair(PICTURE_PAIRS, models, encoders) or PICTURE_PAIRS[0]


LYRICS_MODEL = "gemma4_e4b_it_int8_convrot.safetensors"
# Take pictures drawn on this PC: FLUX.2 klein 4B, its text encoder and its VAE, chosen at install.
# Two pairs of files, looked for in this order: the FP8 model with the FP4 encoder that Windows and
# Docker install, whose fast kernels are NVIDIA's, and the full-precision pair, the one a Mac's GPU
# can run.  The engine's list says which is installed (choose_picture_files).
PICTURE_PAIRS = (("flux-2-klein-4b-fp8.safetensors", "qwen_3_4b_fp4_flux2.safetensors"),
                 ("flux-2-klein-4b.safetensors", "qwen_3_4b.safetensors"))
PICTURE_MODEL, PICTURE_TEXT = PICTURE_PAIRS[0]
# FLUX.2 klein 9B, which draws better and needs more of everything: never installed by Yeufonic, as its
# weights are gated on Hugging Face and under a non-commercial licence, but used when someone has put its
# files in the models folder (the guide says how).  Looked for in this order, the FP8 model first, with
# whichever of its text encoders is there; it shares the 4B's VAE.
PICTURE_PAIRS_9B = (("flux-2-klein-9b-fp8.safetensors", "qwen_3_8b_fp8mixed.safetensors"),
                    ("flux-2-klein-9b-fp8.safetensors", "qwen_3_8b_fp4mixed.safetensors"),
                    ("flux-2-klein-9b-fp8.safetensors", "qwen_3_8b.safetensors"),
                    ("flux-2-klein-9b.safetensors", "qwen_3_8b.safetensors"),
                    ("flux-2-klein-9b.safetensors", "qwen_3_8b_fp8mixed.safetensors"),
                    ("flux-2-klein-9b.safetensors", "qwen_3_8b_fp4mixed.safetensors"))
PICTURE_VAE = "flux2-vae.safetensors"
# The engine's model folder, when this machine can see it.  The app only reads
# from it, and only to say what a LoRA holds; the engine is what loads them.
MODELS_DIR = Path(os.environ.get("MODELS_DIR", "/app/models"))
INSTRUMENTAL_LORA = "ar_lora_inst_v3abc_comfyui.safetensors"
REAL_AUDIO_LORA = os.environ.get("REAL_AUDIO_LORA", "nar_lora_joint_v9_comfyui.safetensors")
TOKENIZER_HEAD = os.environ.get("TOKENIZER_HEAD", "tokenizer_head_joint_v9.safetensors")

DEFAULT_STYLE = "English, warm indie rock, expressive lead vocal, drums, bass, guitars, memorable melody, 110 BPM"

# How long a job may run once the engine has started it.  Time spent waiting in the
# engine's queue does not count.
TIMEOUTS = {"transcribe": 12 * 60, "plan": 10 * 60, "render": 25 * 60, "lyrics": 15 * 60, "separate": 20 * 60, "hear": 40 * 60,
            "identity_score": 12 * 60, "identity_style": 10 * 60, "art": 10 * 60,
            "persona_score": 12 * 60, "persona_style": 10 * 60,
            # None: no limit.  A clock blind to progress stopped a run at step 1325 of
            # 1400 that was reporting a step every few seconds.  Training shows its
            # progress and has Stop; an engine that goes away, or loses the job, or
            # whose job thread dies, is caught without one.
            "train": None}

# Vocals and stems are separated on the engine's GPU when it has the node for it (an engine built with
# Demucs), as a job in the engine's own queue, and on the CPU here otherwise.  STEMS_ON_GPU=0 keeps it on
# the CPU always.
STEMS_ON_GPU = os.environ.get("STEMS_ON_GPU", "1") != "0"

# ---------------------------------------------------------------- LoRA training
#
# On by default.  TRAINING_ENABLED=0 takes Corpora and training out of the app, and an
# engine built with --build-arg WITH_TRAINER=0 leaves out the trainer node pack; the
# app offers training only when both are in.
#
# Dual-branch training uses ComfyUI-YuE2-Trainer (YuE2TrainerPlannerLoRA & YuE2TrainerAcousticLoRA):
# trains the planner LoRA (what they write) and the acoustic LoRA (how they sound),
# merged into one canonical file that applies to both halves via LoraLoader.
TRAINING_ENABLED = os.environ.get("TRAINING_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")

# Whether the engine is asked to unload its models whenever the GPU's line of work runs dry.
# "auto" does it where the GPU shares the computer's memory (a Mac, whose engine keeps its models
# loaded on the GPU between jobs), so a model left over from one job cannot crowd out the next;
# "1" always, "0" never.  The next job loads its models again.
UNLOAD_WHEN_IDLE = os.environ.get("UNLOAD_WHEN_IDLE", "auto").strip().lower()

# Dual-branch training parameters, following the trainer's guidance:
# The planner trains on ABC scores and style/lyrics with structured cropping and
# prior preservation, while the acoustic model trains on 30s segmented latent crops.
#
# Planner steps come from the corpus size: TRAIN_PASSES over each song, the rule of
# thumb in the trainer (steps x batch_songs x artist_fraction / songs), rounded up to
# a checkpoint, and never fewer than TRAIN_MIN_STEPS. TRAIN_STEPS, when set,
# overrides it for every run.
#
# The checkpoints are kept, so a run can be evaluated at earlier steps.
WEAK_RENDER_DB = float(os.environ.get("WEAK_RENDER_DB", "-24"))

TRAIN_PASSES = float(os.environ.get("TRAIN_PASSES", "10"))
TRAIN_STEPS = int(os.environ["TRAIN_STEPS"]) if os.environ.get("TRAIN_STEPS") else None
TRAIN_BATCH_SONGS = int(os.environ.get("TRAIN_BATCH_SONGS", "2"))
TRAIN_ARTIST_FRACTION = float(os.environ.get("TRAIN_ARTIST_FRACTION", "0.5"))
# Spread across the planner steps; the trainer says it converges in about 1000.
TRAIN_DECODER_STEPS = int(os.environ.get("TRAIN_DECODER_STEPS", "1000"))
# How often the score is put in front of the music.  None of the published files
# did; the planner still learns to write a score either way.
TRAIN_SCORE_FIRST = float(os.environ.get("TRAIN_SCORE_FIRST", "0"))
TRAIN_CHECKPOINT_EVERY = int(os.environ.get("TRAIN_CHECKPOINT_EVERY", "50"))
TRAIN_MIN_STEPS = int(os.environ.get("TRAIN_MIN_STEPS", "500"))


def train_steps(songs: int) -> int:
    """Planner steps for a corpus of this many songs."""
    if TRAIN_STEPS:
        return TRAIN_STEPS
    raw = TRAIN_PASSES * max(1, songs) / (TRAIN_BATCH_SONGS * TRAIN_ARTIST_FRACTION)
    every = TRAIN_CHECKPOINT_EVERY
    return max(TRAIN_MIN_STEPS, 2 * every, int(-(-raw // every)) * every)


TRAIN_RANK_PLANNER = int(os.environ.get("TRAIN_RANK_PLANNER", "64"))
TRAIN_RANK_DECODER = int(os.environ.get("TRAIN_RANK_DECODER", "32"))
TRAIN_RANK = TRAIN_RANK_PLANNER
# The Planner trains on each song whole, as one sequence: style, lyrics, the song's audio
# codes and an end token.  A song whose sequence is longer than TRAIN_MAX_TOKENS is left
# out of Planner training altogether, so songs are cut at TRAIN_MAX_MINUTES to fit.  A
# larger context lets longer songs in whole, at the cost of memory and time.
# Both are worked out from the graphics card (see trainsize.py) unless set to numbers.
_MINUTES = os.environ.get("TRAIN_MAX_MINUTES", "auto").strip().lower()
_TOKENS = os.environ.get("TRAIN_MAX_TOKENS", "auto").strip().lower()
TRAIN_MINUTES_AUTO = _MINUTES in ("", "auto")
TRAIN_TOKENS_AUTO = _TOKENS in ("", "auto")
TRAIN_MAX_MINUTES = 6.0 if TRAIN_MINUTES_AUTO else float(_MINUTES)
TRAIN_MAX_TOKENS = 8192 if TRAIN_TOKENS_AUTO else int(_TOKENS)
# The length cap a new take starts with, in seconds, until Settings says otherwise.  A cap is a firm
# limit, not a target: a render usually ends by itself, and a planned take's cap rises to fit its plan
# when nobody set it by hand, so this is mostly how long a render that will not stop is let run.
def _default_cap() -> int:
    try:
        return max(10, min(900, int(float(os.environ.get("DEFAULT_CAP", "360")))))
    except ValueError:
        return 360


DEFAULT_CAP = _default_cap()
# A render can overshoot full scale, and saving it as 16-bit then flattens the peaks.  When the
# engine has the peak guard (an engine built since it was added), it turns the audio down around
# those peaks, in floating point, before the save.  PEAK_GUARD=0 leaves it out.
PEAK_GUARD = os.environ.get("PEAK_GUARD", "1").strip().lower() not in ("0", "false", "no", "off")
PEAK_CEILING_DB = float(os.environ.get("PEAK_CEILING_DB", "-0.5"))
TRAIN_END_TOKEN_WEIGHT = float(os.environ.get("TRAIN_END_TOKEN_WEIGHT", "1.0"))
TRAIN_CLIP_SECONDS = float(os.environ.get("TRAIN_CLIP_SECONDS", "30.0"))
REGULARIZER_PACK = os.environ.get("REGULARIZER_PACK", "minted_regularizer_pack_v2.pt")
# Give up on a job when the engine has been unreachable this long.
ENGINE_LOST_AFTER = 5 * 60

