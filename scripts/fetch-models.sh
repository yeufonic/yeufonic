#!/bin/sh
# Fetch the models into ./models, about 19 GB:
#
#   checkpoints/yue2_3b_bf16.safetensors                 YuE2, plans and renders       7.8 GB
#   audio_encoders/sheetsage2_bf16.safetensors           SheetSage2, transcription      1.4 GB
#   text_encoders/gemma4_e4b_it_int8_convrot.safetensors Gemma 4 E4B, lyric drafts      8.1 GB
#   loras/ar_lora_inst_v3abc_comfyui.safetensors         instrumental LoRA              0.2 GB
#   loras/nar_lora_joint_v9_comfyui.safetensors          Realaudio decoder LoRA         0.1 GB
#   audio_encoders/tokenizer_head_joint_v9.safetensors   Realaudio tokenizer head       0.2 GB
#   whisper/large-v3-turbo/                              Whisper, the engine hears lyrics 1.6 GB
#   data/models/soundfonts/sf2/github_Jnsgm2.sf2         Jnsgm2 SoundFont                33 MB
#   data/models/soundfonts/sf2/Arachno_SoundFont...sf2   Arachno SoundFont 1.0          149 MB
#
#   sh scripts/fetch-models.sh           the full-quality YuE2 model (recommended)
#   sh scripts/fetch-models.sh --int8    the low-memory YuE2 model instead, 4.0 GB, for GPUs
#                                        with little memory (checkpoints/yue2_3b_int8_convrot.safetensors)
#
# One size or the other: with both in models/checkpoints the app uses the full-quality one.
# A file that is already there is kept, and an interrupted download resumes.
# It also creates data/ and engine-state/output/, which the app needs to own, and
# records your user and group ids in .env for compose.yml to run the app as.
set -eu

MODEL=bf16
for arg in "$@"; do
  case "$arg" in
    --int8) MODEL=int8 ;;
    -h|--help) sed -n '2,/^set -eu/p' "$0" | sed '$d'; exit 0 ;;
    *) echo "unknown option: $arg (see --help)" >&2; exit 1 ;;
  esac
done

ROOT=$(cd "$(dirname "$0")/.." && pwd)
YUE2=https://huggingface.co/Comfy-Org/YuE2/resolve/main
GEMMA=https://huggingface.co/Comfy-Org/gemma-4/resolve/main
INSTRUMENTAL=https://huggingface.co/Mothersuperior/YuE2-instrumental-cot-full-loras/resolve/main
REAL_AUDIO=https://huggingface.co/Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/resolve/main
REGULARIZER=https://huggingface.co/Mothersuperior/YuE2-hum-to-song/resolve/main
WHISPER=https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo/resolve/main

mkdir -p "$ROOT/models/checkpoints" "$ROOT/models/audio_encoders" "$ROOT/models/text_encoders" "$ROOT/models/loras" "$ROOT/models/fs_audio"
# The engine writes under these when it fetches a model for itself, and as root: a folder it makes first is root's, and
# this script, run as you, cannot write in it.  Made here first, as you, they are yours; where they are already root's
# the failure is ignored, and the Whisper step below says what to do.
mkdir -p "$ROOT/models/whisper" "$ROOT/models/demucs" 2>/dev/null || true
# The folders compose.yml mounts into the app.  Created here, as you, because a
# folder Docker creates for a mount belongs to root, and the app cannot write to it.
mkdir -p "$ROOT/data" "$ROOT/data/models/soundfonts/sf2" "$ROOT/engine-state/output"
# The app runs as APP_UID:APP_GID, 1000:1000 unless set, and what it writes belongs
# to those ids. Compose reads .env beside compose.yml, so record whoever is setting
# this up, once. Linux only: Docker Desktop maps ownership itself, and root is
# not someone the app should run as.
if [ "$(uname -s)" = Linux ] && [ "$(id -u)" != 0 ] && ! grep -qs '^APP_UID=' "$ROOT/.env"; then
  if [ -s "$ROOT/.env" ] && [ -n "$(tail -c 1 "$ROOT/.env")" ]; then echo >> "$ROOT/.env"; fi
  printf 'APP_UID=%s\nAPP_GID=%s\n' "$(id -u)" "$(id -g)" >> "$ROOT/.env"
  echo "wrote APP_UID=$(id -u) and APP_GID=$(id -g) to .env"
fi

fetch() {
  url="$1"; dest="$2"
  if [ -s "$dest" ]; then
    echo "have  $(basename "$dest")"
    return 0
  fi
  echo "fetch $(basename "$dest")"
  curl -L --fail --retry 5 --retry-all-errors -C - -o "$dest.part" "$url"
  mv "$dest.part" "$dest"
}

if [ "$MODEL" = int8 ]; then
  fetch "$YUE2/checkpoints/yue2_3b_int8_convrot.safetensors" \
        "$ROOT/models/checkpoints/yue2_3b_int8_convrot.safetensors"
  if [ -s "$ROOT/models/checkpoints/yue2_3b_bf16.safetensors" ]; then
    echo "note: yue2_3b_bf16.safetensors is also here, and the app uses it. To use the low-memory model,"
    echo "      remove that file (or set YUE2_CHECKPOINT=int8 for the app)."
  fi
else
  fetch "$YUE2/checkpoints/yue2_3b_bf16.safetensors" \
        "$ROOT/models/checkpoints/yue2_3b_bf16.safetensors"
fi

fetch "$YUE2/audio_encoders/sheetsage2_bf16.safetensors" \
      "$ROOT/models/audio_encoders/sheetsage2_bf16.safetensors"

fetch "$GEMMA/text_encoders/gemma4_e4b_it_int8_convrot.safetensors" \
      "$ROOT/models/text_encoders/gemma4_e4b_it_int8_convrot.safetensors"

fetch "$INSTRUMENTAL/ar_lora_inst_v3abc_comfyui.safetensors" \
      "$ROOT/models/loras/ar_lora_inst_v3abc_comfyui.safetensors"

fetch "$REAL_AUDIO/nar_lora_joint_v9_comfyui.safetensors" \
      "$ROOT/models/loras/nar_lora_joint_v9_comfyui.safetensors"

fetch "$REAL_AUDIO/tokenizer_head_joint_v9.safetensors" \
      "$ROOT/models/audio_encoders/tokenizer_head_joint_v9.safetensors"

fetch "$REGULARIZER/minted_regularizer_pack_v2.pt" \
      "$ROOT/models/fs_audio/minted_regularizer_pack_v2.pt"

# Whisper for the engine, which hears the words of a separated vocal on the GPU.  The engine would fetch it the first
# time it is needed, and a lyric hearing would wait on 1.6 GB; here it is a plain folder the engine uses as it stands.
if mkdir -p "$ROOT/models/whisper/large-v3-turbo" 2>/dev/null && [ -w "$ROOT/models/whisper/large-v3-turbo" ]; then
  for f in config.json preprocessor_config.json tokenizer.json vocabulary.json model.bin; do
    fetch "$WHISPER/$f" "$ROOT/models/whisper/large-v3-turbo/$f"
  done
else
  echo "skip  Whisper: models/whisper is not yours to write in. The engine made it, as root, when it fetched the model" >&2
  echo "      itself, so it has Whisper already. To fetch it here instead: sudo chown -R $(id -u):$(id -g) models/whisper" >&2
fi

# The trainer lists the tokenizer head from models/fs_audio; the rest of the app reads it from audio_encoders.
# It has to be in both, or training is refused ("tokenizer_head ... not in ['(run FS_Audio Training Assets first)']").
if [ -s "$ROOT/models/audio_encoders/tokenizer_head_joint_v9.safetensors" ] && \
   [ ! -s "$ROOT/models/fs_audio/tokenizer_head_joint_v9.safetensors" ]; then
  cp "$ROOT/models/audio_encoders/tokenizer_head_joint_v9.safetensors" "$ROOT/models/fs_audio/tokenizer_head_joint_v9.safetensors"
  echo "copy  tokenizer_head_joint_v9.safetensors for the trainer"
fi

SF2_DIR="$ROOT/data/models/soundfonts/sf2"
fetch "https://raw.githubusercontent.com/wrightflyer/SF2_SoundFonts/master/Jnsgm2.sf2" \
      "$SF2_DIR/github_Jnsgm2.sf2"

fetch "https://archive.org/download/free-soundfonts-sf2-2019-04/Arachno_SoundFont_Version_1.0.sf2" \
      "$SF2_DIR/Arachno_SoundFont_Version_1.0.sf2"

echo "done.  models/ now holds:"
ls -la "$ROOT/models/checkpoints" "$ROOT/models/audio_encoders" "$ROOT/models/text_encoders" "$ROOT/models/loras" "$ROOT/models/fs_audio" | grep -v '^total' | grep -v '^d'
echo ""
echo "soundfonts/sf2/ now holds:"
ls -la "$SF2_DIR" | grep -v '^total' | grep -v '^d'
