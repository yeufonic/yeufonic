#!/bin/bash
# Yeufonic for macOS: checks this Mac, then fetches and sets up everything the app does
# not carry.  Every part comes from its own publisher, pinned to a version and checked by
# sha256 where the publisher gives one.  Safe to run again: whatever is already in place is
# kept, and an interrupted download carries on.  The macOS counterpart of windows/setup.ps1,
# and it keeps that script's order, so the two can be read side by side.
#
#   bash setup.sh [--install-dir <folder>] [--no-lyrics] [--check-only] [--skip-models] [--then-open <app>]
#   ... --install-dir   where it goes (default: ~/Library/Application Support/Yeufonic)
#   ... --no-lyrics     leave out Gemma 4 (8.1 GB), for an external LLM in Settings instead
#   ... --check-only    only the system check
#   ... --skip-models   everything but the 18 GB of models (for testing)
#   ... --then-open     open this app when setup has finished (the launcher passes itself)
#
# Written for the bash that comes with macOS (3.2): no associative arrays, no mapfile.
set -euo pipefail

INSTALL_DIR="$HOME/Library/Application Support/Yeufonic"
NO_LYRICS=0
CHECK_ONLY=0
SKIP_MODELS=0
THEN_OPEN=""
while [ $# -gt 0 ]; do
  case "$1" in
    --install-dir) INSTALL_DIR="$2"; shift 2 ;;
    --no-lyrics) NO_LYRICS=1; shift ;;
    --check-only) CHECK_ONLY=1; shift ;;
    --skip-models) SKIP_MODELS=1; shift ;;
    --then-open) THEN_OPEN="$2"; shift 2 ;;
    -h|--help) sed -n '2,/^set -euo/p' "$0" | sed '$d'; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 1 ;;
  esac
done

# What this script was given: inside the app it sits beside studio/ (the app, its
# requirements, VERSION, BUILD and our engine node); run from a checkout, the checkout is it.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$HERE/studio" ]; then
  STUDIO="$HERE/studio"
  NODE_SRC="$STUDIO/engine-nodes/yue2_harmony"
else
  STUDIO="$(cd "$HERE/.." && pwd)"
  NODE_SRC="$STUDIO/engine/custom_nodes/yue2_harmony"
fi

DOWNLOADS="$INSTALL_DIR/downloads"
TOOLS="$INSTALL_DIR/tools"
ENGINE="$INSTALL_DIR/engine"
COMFY="$ENGINE/ComfyUI"
MODELS="$COMFY/models"
STATE="$INSTALL_DIR/state"
LOGS="${YEUFONIC_LOGS:-$HOME/Library/Logs/Yeufonic}"
APP_VENV="$INSTALL_DIR/venv"
ENGINE_VENV="$ENGINE/venv"
mkdir -p "$INSTALL_DIR" "$DOWNLOADS" "$TOOLS/bin" "$STATE" "$LOGS"
# Everything said here is also kept, for when it goes wrong.
exec > >(tee -a "$LOGS/setup.log") 2>&1
echo ""
echo "---- $(date -u +%Y-%m-%dT%H:%M:%SZ) setup.sh $*"

# ------------------------------------------------------------------------ pins
# What was tested together.  Change one deliberately, and test again.  The ComfyUI and
# trainer commits are engine/Dockerfile's and windows/setup.ps1's.
COMFY_COMMIT=36da3ff763687eab86a35e1019995dd1fb369b0d
TRAINER_COMMIT=6a9355efff60589d93b41b569676f09d5db85d09
PYTHON=3.13
# The engine's torch: the version the Windows engine runs.  The macOS wheels carry Metal
# (MPS) and want macOS 14, which is also where bf16 on the GPU starts.
ENGINE_TORCH="torch==2.13.0 torchvision==0.28.0 torchaudio==2.11.0"
# The app's own torch, for stems on the CPU: the version the app container and the Windows
# app run.
APP_TORCH="torch==2.9.1 torchaudio==2.9.1"
UV_URL=https://github.com/astral-sh/uv/releases/download/0.12.18/uv-aarch64-apple-darwin.tar.gz
UV_SHA=cf40e0c6a202190ccd9e0406dcfdd5b2d6668a9a5c779b17948963df32aafe5b
UV_SIZE=16963768
# ffmpeg and ffprobe 9.0.2 (the Windows install's version), static arm64 builds, from
# Martin Riedl's build server, which publishes a sha256 beside each.
FFMPEG_BASE=https://ffmpeg.martin-riedl.de/download/macos/arm64/1789931890_9.0.2
FFMPEG_SHA=c8ed4c4e6978a03c485edbfe4e0a5dc2380f8a30bba5150531b31b094492d924
FFMPEG_SIZE=28395699
FFPROBE_SHA=fcbe839537485eaee7a7a8bc5cbc0f90d53617e80943e8a5b2e31cb851197ea6
FFPROBE_SIZE=28317701

HF=https://huggingface.co
# dir|file|bytes|sha256|url|lyrics: the models windows/setup.ps1 fetches, with the same
# checksums (tests/test_macos.py holds the two lists together).  Left out on a Mac: the
# low-memory YuE2 and FLUX.2 [klein], whose int8 and fp8 kernels are CUDA's.
model_list() {
  cat <<LIST
checkpoints|yue2_3b_bf16.safetensors|7799983228|33765adbf9813c9a50318218760b2fd819a319862460a04884607581961c6fee|$HF/Comfy-Org/YuE2/resolve/main/checkpoints/yue2_3b_bf16.safetensors|
audio_encoders|sheetsage2_bf16.safetensors|1386868122|5fd960ce3df281e3f3a889d174584d88f96247711480cf96377b12d7e8b6adc5|$HF/Comfy-Org/YuE2/resolve/main/audio_encoders/sheetsage2_bf16.safetensors|
text_encoders|gemma4_e4b_it_int8_convrot.safetensors|8090965702|974d0c838ef4ac1a989b06ccb4e57691c21b6270dd8e345ffa7531f9388f117c|$HF/Comfy-Org/gemma-4/resolve/main/text_encoders/gemma4_e4b_it_int8_convrot.safetensors|lyrics
loras|ar_lora_inst_v3abc_comfyui.safetensors|212891736|de6a11d5701df103a191c87dc73115266e2420f3834739319dec5c24d2119f31|$HF/Mothersuperior/YuE2-instrumental-cot-full-loras/resolve/main/ar_lora_inst_v3abc_comfyui.safetensors|
loras|nar_lora_joint_v9_comfyui.safetensors|107518800|cd2bf0d3ce4bf68697daa016671da7d70e34e2f5545617ab9094c96b14a581db|$HF/Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/resolve/main/nar_lora_joint_v9_comfyui.safetensors|
audio_encoders|tokenizer_head_joint_v9.safetensors|171278808|06440f25605c6c12c4e517ef033d7b70b8d9e961b3b06aa3848b1f8028fd7eb8|$HF/Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/resolve/main/tokenizer_head_joint_v9.safetensors|
fs_audio|minted_regularizer_pack_v2.pt|296098847|587631eec5946f9f87d4b422abcda7e35dee43299efb7b7d2fcba4cd8752c475|$HF/Mothersuperior/YuE2-hum-to-song/resolve/main/minted_regularizer_pack_v2.pt|
LIST
}
soundfont_list() {
  cat <<LIST
github_Jnsgm2.sf2|33187490|dc48cb5c322cab23fce1b18442066be30ccc49a184603c7a3bf7615003ee137d|https://raw.githubusercontent.com/wrightflyer/SF2_SoundFonts/master/Jnsgm2.sf2
Arachno_SoundFont_Version_1.0.sf2|155405818|9a57fb3b6714e69dda12390e351b087e81fc3b1eca15c6b4bbe172799f4cf3cd|https://archive.org/download/free-soundfonts-sf2-2019-04/Arachno_SoundFont_Version_1.0.sf2
LIST
}

# ------------------------------------------------------------------- helpers
say() { echo "$*"; }
step() { echo ""; echo "== $*"; }
mark_done() { date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE/$1.done"; }
is_done() { [ -f "$STATE/$1.done" ]; }

stop_setup() {
  trap - ERR
  echo ""
  echo "Setup stopped: $1"
  echo "The details are in $LOGS/setup.log."
  echo "Open Yeufonic again to carry on from here."
  exit 1
}
trap 'stop_setup "an unexpected error at line $LINENO"' ERR

sha_of() { shasum -a 256 "$1" | awk '{print $1}'; }
size_of() { stat -f %z "$1" 2>/dev/null || stat -c %s "$1"; }

# A file from its publisher.  curl resumes a broken download; the sha256 is checked once and
# remembered, so a second run does not read 8 GB again.
get_verified() {
  local url="$1" dest="$2" size="$3" sha="$4"
  if [ -f "$dest" ] && [ -f "$dest.sha256ok" ]; then return 0; fi
  if [ ! -f "$dest" ]; then
    say "Downloading $(basename "$dest") ($((size / 1000000)) MB)"
    local try
    for try in 1 2 3 4 5 6; do
      if curl -L --fail --retry 5 -C - -# -o "$dest.part" "$url"; then break; fi
      if [ "$try" -eq 6 ]; then stop_setup "could not download $url"; fi
      say "  the download broke off; trying again ($try of 5)"
      sleep $((5 * try))
    done
    mv -f "$dest.part" "$dest"
  fi
  if [ -n "$size" ] && [ "$(size_of "$dest")" != "$size" ]; then
    rm -f "$dest"
    stop_setup "$(basename "$dest") came down the wrong size; it has been removed, so the next run fetches it again"
  fi
  if [ -n "$sha" ]; then
    say "  checking $(basename "$dest")"
    if [ "$(sha_of "$dest")" != "$sha" ]; then
      rm -f "$dest"
      stop_setup "$(basename "$dest") did not match its published checksum; it has been removed, so the next run fetches it again"
    fi
  fi
  date -u +%Y-%m-%dT%H:%M:%SZ > "$dest.sha256ok"
}

# An archive of one commit from GitHub.  GitHub builds these on request, so they have no
# fixed checksum; the commit id pins the contents.
get_commit() {
  local repo="$1" commit="$2" dest="$3"
  local archive
  archive="$DOWNLOADS/$(echo "$repo" | tr / _)-${commit:0:8}.tar.gz"
  if [ ! -f "$archive" ]; then
    say "Downloading $repo at ${commit:0:8}"
    curl -L --fail --retry 5 -# -o "$archive.part" "https://codeload.github.com/$repo/tar.gz/$commit" \
      || stop_setup "could not download $repo"
    mv -f "$archive.part" "$archive"
  fi
  local tmp="$DOWNLOADS/unpack"
  rm -rf "$tmp"; mkdir -p "$tmp"
  tar -xzf "$archive" -C "$tmp"
  rm -rf "$dest"
  mv "$tmp"/* "$dest"
  rm -rf "$tmp"
}

port_taken() { nc -z 127.0.0.1 "$1" >/dev/null 2>&1; }

# -------------------------------------------------------------- system check
step "Checking this Mac"
problems=""
warnings=""
problem() { problems="$problems$1"$'\n'; }
warning() { warnings="$warnings$1"$'\n'; }

OS_VERSION="$(sw_vers -productVersion 2>/dev/null || echo 0)"
OS_MAJOR="${OS_VERSION%%.*}"
ARCH="$(uname -m)"
say "macOS $OS_VERSION, $ARCH"
if [ "$ARCH" != arm64 ]; then
  problem "Yeufonic needs a Mac with Apple silicon (M1 or later); this one is $ARCH."
fi
case "$OS_MAJOR" in
  ''|*[!0-9]*) problem "This does not look like macOS (no version from sw_vers)." ;;
  *) if [ "$OS_MAJOR" -lt 14 ]; then problem "macOS 14 (Sonoma) or later is needed (this is $OS_VERSION)."; fi ;;
esac

MEM_BYTES="$(sysctl -n hw.memsize 2>/dev/null || echo 0)"
MEM_GB=$((MEM_BYTES / 1073741824))
say "Memory: $MEM_GB GB, shared by the system and the GPU"
if [ "$MEM_GB" -lt 16 ]; then
  if [ "$CHECK_ONLY" -eq 1 ] || [ "$SKIP_MODELS" -eq 1 ]; then
    # A test of the set-up itself (a build machine has little memory): it can go on.
    warning "This Mac has $MEM_GB GB of memory, too little to make songs; YuE2 alone takes about 8 GB."
  else
    problem "This Mac has $MEM_GB GB of memory; YuE2 alone takes about 8 GB of it, and 16 GB is the least that can work."
  fi
elif [ "$MEM_GB" -lt 32 ]; then
  warning "$MEM_GB GB of memory may be enough for songs, but not for lyric drafts on this Mac as well: choose an external LLM in Settings. 32 GB is recommended."
fi

# Room for what is still to come: the missing models, plus about 8 GB for the engine, the
# app and the downloads while they unpack.  Counted in thousands, as download sites count.
NEED=8000000000
if [ "$SKIP_MODELS" -eq 0 ]; then
  while IFS='|' read -r dir file size sha url lyrics; do
    [ -z "$file" ] && continue
    if [ "$lyrics" = lyrics ] && [ "$NO_LYRICS" -eq 1 ]; then continue; fi
    [ -f "$MODELS/$dir/$file" ] || NEED=$((NEED + size))
  done <<EOF
$(model_list)
EOF
  NEED=$((NEED + 1700000000))   # Whisper and demucs, for the app
fi
FREE_KB="$(df -k "$INSTALL_DIR" | awk 'NR==2 {print $4}')"
FREE=$((FREE_KB * 1024))
NEED_GB=$(((NEED + 999999999) / 1000000000))
say "Free space: $((FREE / 1000000000)) GB (needed: about $NEED_GB GB)"
if [ "$FREE" -lt "$NEED" ]; then
  problem "Not enough free space: about $NEED_GB GB is needed."
fi

# The ports this install uses: the defaults, or what its settings.ini says.
APP_PORT=8090
ENGINE_PORT=8188
INI="$INSTALL_DIR/settings.ini"
ini_value() {
  [ -f "$INI" ] || return 0
  sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*\\(.*[^[:space:]]\\)[[:space:]]*\$/\\1/p" "$INI" | head -1
}
v="$(ini_value app_port)"; case "$v" in ''|*[!0-9]*) ;; *) APP_PORT="$v" ;; esac
v="$(ini_value engine_port)"; case "$v" in ''|*[!0-9]*) ;; *) ENGINE_PORT="$v" ;; esac
for port in "$APP_PORT" "$ENGINE_PORT"; do
  if port_taken "$port"; then
    warning "Something is already using port $port (another copy of Yeufonic or ComfyUI?). Stop it before starting Yeufonic."
  fi
done

for site in https://huggingface.co https://github.com https://pypi.org; do
  curl -s -o /dev/null -I --max-time 15 "$site" || problem "Cannot reach $site. Check the internet connection, or a firewall or proxy."
done

if [ -n "$warnings" ]; then printf '%s' "$warnings" | sed 's/^/  note: /'; fi
if [ -n "$problems" ]; then
  printf '%s' "$problems" | sed 's/^/  problem: /'
  stop_setup "this Mac does not meet the requirements above"
fi
say "This Mac is suitable."
if [ "$CHECK_ONLY" -eq 1 ]; then exit 0; fi

# ------------------------------------------------------------------- tools
step "Tools"
UV="$TOOLS/bin/uv"
if [ ! -x "$UV" ]; then
  get_verified "$UV_URL" "$DOWNLOADS/uv.tar.gz" "$UV_SIZE" "$UV_SHA"
  tar -xzf "$DOWNLOADS/uv.tar.gz" -C "$TOOLS/bin" --strip-components=1
fi
for tool in ffmpeg ffprobe; do
  if [ ! -x "$TOOLS/bin/$tool" ]; then
    if [ "$tool" = ffmpeg ]; then sha="$FFMPEG_SHA"; size="$FFMPEG_SIZE"; else sha="$FFPROBE_SHA"; size="$FFPROBE_SIZE"; fi
    get_verified "$FFMPEG_BASE/$tool.zip" "$DOWNLOADS/$tool.zip" "$size" "$sha"
    unzip -o -q "$DOWNLOADS/$tool.zip" -d "$TOOLS/bin"
    chmod +x "$TOOLS/bin/$tool"
  fi
done
# FluidSynth, for hearing an imported MIDI file, has no macOS build of its own; the launcher
# gives the app Homebrew's if it is there (brew install fluid-synth).
if [ -x /opt/homebrew/bin/fluidsynth ]; then
  say "FluidSynth: Homebrew's, at /opt/homebrew/bin/fluidsynth"
else
  say "FluidSynth: not found. MIDI files can be imported but not heard; 'brew install fluid-synth' adds it."
fi
# uv keeps its Pythons and its cache in this folder, not in the user's own.
export UV_PYTHON_INSTALL_DIR="$INSTALL_DIR/python"
export UV_CACHE_DIR="$DOWNLOADS/uv-cache"
# --no-bin: uv would also put a python3.13 in the user's own ~/.local/bin, outside this folder.
if ! is_done "python-$PYTHON"; then
  "$UV" python install --no-bin "$PYTHON" || stop_setup "Python $PYTHON could not be installed"
  mark_done "python-$PYTHON"
fi

# ------------------------------------------------------------------- engine
step "The engine (ComfyUI, on the GPU through Metal)"
ENGINE_MARK="engine-${COMFY_COMMIT:0:8}"
if ! is_done "$ENGINE_MARK" || [ ! -f "$COMFY/main.py" ]; then
  # Keep the models and anything made with the engine when it is replaced.
  KEEP="$INSTALL_DIR/engine-keep"
  if [ -d "$COMFY" ]; then
    mkdir -p "$KEEP"
    for sub in models input output user; do
      if [ -e "$COMFY/$sub" ]; then mv "$COMFY/$sub" "$KEEP/$sub"; fi
    done
  fi
  mkdir -p "$ENGINE"
  get_commit Comfy-Org/ComfyUI "$COMFY_COMMIT" "$COMFY"
  if [ -d "$KEEP" ]; then
    for sub in models input output user; do
      if [ -e "$KEEP/$sub" ]; then rm -rf "${COMFY:?}/$sub"; mv "$KEEP/$sub" "$COMFY/$sub"; fi
    done
    rm -rf "$KEEP"
  fi
  if [ ! -x "$ENGINE_VENV/bin/python" ]; then
    "$UV" venv --python "$PYTHON" "$ENGINE_VENV" || stop_setup "the engine's Python could not be set up"
  fi
  say "Installing the engine's packages"
  # torch first, pinned, so ComfyUI's unpinned "torch" is already met.
  # shellcheck disable=SC2086
  "$UV" pip install --python "$ENGINE_VENV/bin/python" $ENGINE_TORCH || stop_setup "the engine's torch failed"
  "$UV" pip install --python "$ENGINE_VENV/bin/python" -r "$COMFY/requirements.txt" || stop_setup "the engine's packages failed"
  mark_done "$ENGINE_MARK"
fi
EPY="$ENGINE_VENV/bin/python"

NODES="$COMFY/custom_nodes"
mkdir -p "$NODES"
if ! is_done "yue2_trainer-${TRAINER_COMMIT:0:8}" || [ ! -d "$NODES/ComfyUI-YuE2-Trainer" ]; then
  get_commit yeufonic/ComfyUI-YuE2-Trainer "$TRAINER_COMMIT" "$NODES/ComfyUI-YuE2-Trainer"
  "$UV" pip install --python "$EPY" "soundfile>=0.12" "librosa>=0.10" scipy mutagen einops || stop_setup "the trainer's packages failed"
  mark_done "yue2_trainer-${TRAINER_COMMIT:0:8}"
fi
# Stem separation in the engine's queue, on the GPU through Metal.  Whisper stays with the
# app, on the CPU: CTranslate2 has no Metal backend, so the engine's Whisper node is not
# there on a Mac and the app hears words itself, as it does wherever that node is missing.
if ! is_done engine-demucs; then
  "$UV" pip install --python "$EPY" demucs==4.1.0 || stop_setup "demucs for the engine failed"
  mark_done engine-demucs
fi
# Our own node, carried by the app.
rm -rf "$NODES/yue2_harmony"
cp -R "$NODE_SRC" "$NODES/yue2_harmony"
rm -rf "$NODES/yue2_harmony/__pycache__"
for sub in checkpoints audio_encoders text_encoders loras fs_audio; do mkdir -p "$MODELS/$sub"; done

# ---------------------------------------------------------------------- app
step "The app"
REQS="$STUDIO/requirements.txt"
APP_MARK="app-$(sha_of "$REQS" | cut -c1-12)"
if ! is_done "$APP_MARK" || [ ! -x "$APP_VENV/bin/python" ]; then
  if [ ! -x "$APP_VENV/bin/python" ]; then
    "$UV" venv --python "$PYTHON" "$APP_VENV" || stop_setup "the app's Python could not be set up"
  fi
  "$UV" pip install --python "$APP_VENV/bin/python" -r "$REQS" || stop_setup "the app's packages failed"
  # Stems run on the CPU, as in the app container: the GPU belongs to YuE2.
  # shellcheck disable=SC2086
  "$UV" pip install --python "$APP_VENV/bin/python" $APP_TORCH || stop_setup "torch for stems failed"
  "$UV" pip install --python "$APP_VENV/bin/python" demucs==4.1.0 || stop_setup "demucs failed"
  # The icon the launcher puts in the menu bar.
  "$UV" pip install --python "$APP_VENV/bin/python" pyobjc-framework-Cocoa==12.2.2 || stop_setup "the menu-bar icon's package failed"
  mark_done "$APP_MARK"
fi

# The data folder, which settings.ini may move.
DATA="$INSTALL_DIR/data"
v="$(ini_value data_dir)"; if [ -n "$v" ]; then DATA="$v"; fi
mkdir -p "$DATA"

# ------------------------------------------------------------------- models
if [ "$SKIP_MODELS" -eq 0 ]; then
  step "The models (the long part)"
  while IFS='|' read -r dir file size sha url lyrics; do
    [ -z "$file" ] && continue
    if [ "$lyrics" = lyrics ] && [ "$NO_LYRICS" -eq 1 ]; then continue; fi
    say ""
    say "$file"
    mkdir -p "$MODELS/$dir"
    get_verified "$url" "$MODELS/$dir/$file" "$size" "$sha"
  done <<EOF
$(model_list)
EOF
  # The trainer lists its tokenizer head from fs_audio as well.
  if [ ! -f "$MODELS/fs_audio/tokenizer_head_joint_v9.safetensors" ]; then
    cp "$MODELS/audio_encoders/tokenizer_head_joint_v9.safetensors" "$MODELS/fs_audio/"
  fi
fi

# ------------------------------------------------------ the app's own models
# Whisper (times the lyric lines of a cover) and demucs (separates the vocal) would otherwise
# download the first time a cover or stems are made.  Fetched with the app's own Python, by
# the same calls the app makes, into the folders the launcher gives it.
if [ "$SKIP_MODELS" -eq 0 ] && ! is_done app-models; then
  step "The app's own models (lyric timing and stems)"
  export TORCH_HOME="$DATA/models/torch"
  export HF_HOME="$DATA/models/whisper"
  say "Whisper large-v3-turbo (about 1.6 GB)"
  "$APP_VENV/bin/python" -c "import sys; from faster_whisper import download_model; download_model('large-v3-turbo', cache_dir=sys.argv[1])" \
    "$DATA/models/whisper" || stop_setup "Whisper could not be fetched"
  say "demucs htdemucs (about 80 MB)"
  "$APP_VENV/bin/python" -c "from demucs.pretrained import get_model; get_model('htdemucs')" || stop_setup "demucs' model could not be fetched"
  mark_done app-models
fi
if [ "$SKIP_MODELS" -eq 0 ] && ! is_done engine-demucs-model; then
  say "demucs htdemucs for the engine (about 80 MB)"
  if "$EPY" -s -c "import sys, torch; torch.hub.set_dir(sys.argv[1]); from huggingface_hub import constants; constants.HF_HUB_CACHE = sys.argv[1] + '/hub'; from demucs.pretrained import get_model; get_model('htdemucs')" \
      "$MODELS/demucs"; then
    mark_done engine-demucs-model
  else
    say "Could not fetch it now; the engine will when it first separates a vocal."
  fi
fi

# ---------------------------------------------------------------- soundfonts
if [ "$SKIP_MODELS" -eq 0 ]; then
  step "SoundFonts for MIDI playback"
  mkdir -p "$DATA/models/soundfonts/sf2"
  while IFS='|' read -r file size sha url; do
    [ -z "$file" ] && continue
    get_verified "$url" "$DATA/models/soundfonts/sf2/$file" "$size" "$sha"
  done <<EOF
$(soundfont_list)
EOF
fi

# -------------------------------------------------------------------- done
# The launcher runs this again whenever the app it comes with is not the one set up here, so
# a new copy dragged into Applications brings its packages and its engine node with it.
cat "$STUDIO/VERSION" "$STUDIO/BUILD" 2>/dev/null > "$STATE/set-up-for" || true
rm -rf "$UV_CACHE_DIR"
step "Finished"
say "Yeufonic is set up."
if [ -n "$THEN_OPEN" ]; then
  say "Opening it now. This window can be closed."
  open "$THEN_OPEN"
fi
exit 0
