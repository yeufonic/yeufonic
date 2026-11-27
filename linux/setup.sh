#!/bin/bash
# Yeufonic for Linux (command-line installer): checks this machine, then fetches and sets up
# everything the installer does not carry. Every part comes from its own publisher, pinned to
# a version and checked by sha256 where the publisher gives one. Safe to run again: models,
# LoRAs and tools already on disk are skipped unless --force-downloads is passed, and an
# interrupted download carries on from where it stopped.
#
#   bash setup.sh [--install-dir <folder>] [--engine comfyui|yue2cpp] [--int8 | --bf16]
#                 [--cpp-model q8|bf16] [--no-lyrics] [--pictures | --no-pictures]
#                 [--picture-model 4b|flux3|fibo2] [--loras | --no-loras] [--voices | --no-voices]
#                 [--demos | --no-demos] [--force-downloads] [--reconfigure] [--check-only] [--skip-models]
#
#   --install-dir      where it goes (default: ~/.local/share/yeufonic)
#   --engine           comfyui (everything, LoRA training included: the default) or yue2cpp
#                      (smaller native engine; no training). Kept for later runs.
#   --int8             low-memory YuE2 model (4.0 GB) instead of full quality BF16 (ComfyUI)
#   --bf16             full-quality YuE2 model (7.8 GB, the default for ComfyUI)
#   --cpp-model        yue2.cpp's YuE2: q8 (default, 3.8 GB) or bf16 (7.2 GB)
#   --no-lyrics        leave out Gemma 4 (8.1 GB), for an external LLM in Settings instead
#   --pictures         enable local take pictures (default: FLUX.2 klein 4B, ~8.3 GB);
#                      --no-pictures fetches none. Asked once on first interactive run.
#   --picture-model    local take-picture model: 4b (FLUX.2 klein 4B, default, Apache 2.0),
#                      flux3 (FLUX 3 klein GGUF, yue2.cpp only, FLUX Kommunity License, ~9.0 GB) or
#                      fibo2 (FIBO 2.0, ComfyUI only, CC BY-NC 4.0 non-commercial). Implies --pictures.
#   --loras            39 style LoRAs by their authors (CC BY-NC 4.0, about 3.8 GB); --no-loras none.
#   --voices           recorded voices (RVC + BS-Roformer in Python 3.12, ~1.1 GB models + ~3 GB packages);
#                      --no-voices none.
#   --demos            Starter Pack (curated demo takes in a "Starter Pack" space with artwork, mastering
#                      settings, cover recording, voice and style LoRAs, ~1.7 GB); --no-demos none.
#                      Defaults to yes on a fresh install and no on an existing install.
#   --force-downloads  re-download models, LoRAs, SoundFonts and voice files even if already present
#   --reconfigure      re-ask engine, model size and component choices (pre-filling current settings)
#   --check-only       only run the system check (downloads nothing)
#   --skip-models      set up tools, Python, engine and app without downloading the multi-GB models
set -euo pipefail

ORIG_ARGS="$*"
INSTALL_DIR="${YEUFONIC_HOME:-}"
EXPLICIT_INSTALL_DIR=0
LYRICS_CHOICE=""
NO_LYRICS=0
CHECK_ONLY=0
SKIP_MODELS=0
FORCE_DOWNLOADS=0
RECONFIGURE=0
INT8_CHOICE=""
PICTURES=""
PICTURE_MODEL=""
LORAS=""
VOICES=""
DEMOS=""
ENGINE_CHOICE=""
CPP_MODEL=""

while [ $# -gt 0 ]; do
  case "$1" in
    --install-dir) INSTALL_DIR="$2"; EXPLICIT_INSTALL_DIR=1; shift 2 ;;
    --install-dir=*) INSTALL_DIR="${1#*=}"; EXPLICIT_INSTALL_DIR=1; shift ;;
    --engine) ENGINE_CHOICE="$2"; shift 2 ;;
    --engine=*) ENGINE_CHOICE="${1#*=}"; shift ;;
    --int8) INT8_CHOICE=int8; shift ;;
    --bf16) INT8_CHOICE=bf16; shift ;;
    --cpp-model) CPP_MODEL="$2"; shift 2 ;;
    --cpp-model=*) CPP_MODEL="${1#*=}"; shift ;;
    --lyrics) LYRICS_CHOICE=yes; shift ;;
    --no-lyrics) LYRICS_CHOICE=no; shift ;;
    --pictures) PICTURES=yes; shift ;;
    --no-pictures) PICTURES=no; shift ;;
    --picture-model) PICTURE_MODEL="$2"; PICTURES=yes; shift 2 ;;
    --picture-model=*) PICTURE_MODEL="${1#*=}"; PICTURES=yes; shift ;;
    --loras) LORAS=yes; shift ;;
    --no-loras) LORAS=no; shift ;;
    --voices) VOICES=yes; shift ;;
    --no-voices) VOICES=no; shift ;;
    --demos) DEMOS=yes; shift ;;
    --no-demos) DEMOS=no; shift ;;
    --force-downloads|--redownload) FORCE_DOWNLOADS=1; shift ;;
    --reconfigure) RECONFIGURE=1; shift ;;
    --check-only) CHECK_ONLY=1; shift ;;
    --skip-models) SKIP_MODELS=1; shift ;;
    -h|--help) sed -n '2,/^set -euo/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 1 ;;
  esac
done

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# When no --install-dir or YEUFONIC_HOME was given: if running setup.sh directly inside an
# existing install directory, target that directory; else follow ~/.local/bin/yeufonic if present.
if [ "$EXPLICIT_INSTALL_DIR" -eq 0 ] && [ -z "$INSTALL_DIR" ]; then
  if [ -x "$HERE/bin/yeufonic" ] && [ -d "$HERE/studio" ]; then
    INSTALL_DIR="$HERE"
  elif [ -L "$HOME/.local/bin/yeufonic" ]; then
    _existing_bin="$(readlink -f "$HOME/.local/bin/yeufonic" 2>/dev/null || true)"
    if [ -n "$_existing_bin" ] && [ "$(basename "$_existing_bin")" = "yeufonic" ] && [ "$(basename "$(dirname "$_existing_bin")")" = "bin" ]; then
      INSTALL_DIR="$(cd "$(dirname "$_existing_bin")/.." && pwd)"
    fi
  fi
  INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/share/yeufonic}"
fi

case "$INSTALL_DIR" in
  "~") INSTALL_DIR="$HOME" ;;
  "~/"*) INSTALL_DIR="$HOME/${INSTALL_DIR#~/}" ;;
esac
while [ "$INSTALL_DIR" != "/" ] && [ "${INSTALL_DIR%/}" != "$INSTALL_DIR" ]; do
  INSTALL_DIR="${INSTALL_DIR%/}"
done
if [ -d "$HERE/studio" ]; then
  STUDIO="$HERE/studio"
  NODE_SRC="$STUDIO/engine-nodes/yue2_harmony"
  START_SRC="$STUDIO/engine/start.py"
else
  STUDIO="$(cd "$HERE/.." && pwd)"
  NODE_SRC="$STUDIO/engine/custom_nodes/yue2_harmony"
  START_SRC="$STUDIO/engine/start.py"
fi

DOWNLOADS="$INSTALL_DIR/downloads"
TOOLS="$INSTALL_DIR/tools"
ENGINE="$INSTALL_DIR/engine"
COMFY="$ENGINE/ComfyUI"
MODELS="$COMFY/models"
CUDA12_DIR="$ENGINE/cuda12"
STATE="$INSTALL_DIR/state"
LOGS="${YEUFONIC_LOGS:-$INSTALL_DIR/logs}"
APP_VENV="$INSTALL_DIR/venv"
ENGINE_VENV="$ENGINE/venv"

# Keep stdout/stderr attached directly to the terminal (no async `exec > >(tee ...)` pipe)
# so prompts never race ahead of printed lines, progress bars render cleanly in place, and
# tools like uv / faster_whisper / demucs / ollama see a real TTY. say(), step(), prompts,
# and download summaries synchronously append to $LOGS/setup.log.
IS_TTY=0
if [ -t 1 ] && [ -t 2 ]; then
  IS_TTY=1
fi
exec 3>&1 4>&2

if [ "$CHECK_ONLY" -eq 0 ]; then
  mkdir -p "$INSTALL_DIR" "$DOWNLOADS" "$TOOLS/bin" "$STATE" "$LOGS"
  printf '\n---- %s setup.sh %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$ORIG_ARGS" >> "$LOGS/setup.log"
fi

# ------------------------------------------------------------------------ pins
# Same commits as engine/Dockerfile, windows/setup.ps1 and macos/setup.sh.
COMFY_COMMIT=bb878b9ee35274e67931634ba9e8c338f8c06035
TRAINER_COMMIT=32b1d423e9252434ca8345cefcf0b698693b672c
RVC_COMMIT=81eed5e8f68b6bed1789f682fe78cdd324495afc
PYTHON=3.13
VOICE_PYTHON=3.12

# Engine PyTorch: cu130 (driver >= 580) uses ComfyUI's fast quantised kernels (matching Windows/macOS);
# cu128 (driver 525-579) uses engine/Dockerfile's tested 2.9.1+cu128 triple.
ENGINE_TORCH_CU130="torch==2.13.0 torchvision==0.28.0 torchaudio==2.11.0"
ENGINE_TORCH_CU128="torch==2.9.1 torchvision==0.24.1 torchaudio==2.9.1"
# Isolated CUDA 12 libraries for GPU Whisper (CTranslate2) when engine torch is cu130.
CUDA12_WHISPER_PKGS="nvidia-cublas-cu12==12.8.4.1 nvidia-cudnn-cu12==9.10.2.21"
# App CPU PyTorch for stems (matching Dockerfile and Windows/macOS).
APP_TORCH="torch==2.9.1 torchaudio==2.9.1"
# Voice service PyTorch (RVC, matching voice/Dockerfile and Windows/macOS).
VOICE_TORCH="torch==2.7.1 torchaudio==2.7.1"

# Static musl uv: zero glibc dependency across all x86_64 Linux distros.
UV_URL=https://github.com/astral-sh/uv/releases/download/0.12.18/uv-x86_64-unknown-linux-musl.tar.gz
UV_SHA=e38d97460b98ebfd31b197de0fe9fa578add4bc8ba0179b203dd3f87b99f98e6
UV_SIZE=22714365

# Static Linux amd64 ffmpeg & ffprobe 9.0.2 from Martin Riedl's build server (same publisher as macos/setup.sh).
FFMPEG_BASE=https://ffmpeg.martin-riedl.de/download/linux/amd64/1789931100_9.0.2
FFMPEG_SHA=fa8ecf4abbd290d98f7d188b8649cc6b391ae209a98452be955a15aab1909d7f
FFMPEG_SIZE=33326445
FFPROBE_SHA=3f428c49070be3d24ec338602b76d412e401ffcb8a5641ef0e729181a232fc32
FFPROBE_SIZE=33223234

# Prebuilt static offline FluidSynth and portable glibc-2.28 yue2.cpp + sd-server (Phase 1 pre-releases).
# Override via YEUFONIC_FLUIDSYNTH_URL / YEUFONIC_CPP_URL for testing local builds.
FLUIDSYNTH_URL="${YEUFONIC_FLUIDSYNTH_URL:-https://github.com/yeufonic/yeufonic/releases/download/fluidsynth-linux-2.6.2-sndfile-1.2.2-p1/fluidsynth-linux-2.6.2-sndfile-1.2.2-p1.tar.gz}"
FLUIDSYNTH_SHA="${YEUFONIC_FLUIDSYNTH_SHA:-e96a2954961671f0d51e174d8019d71a2148928b10616ea46cd6308314930552}"
FLUIDSYNTH_SIZE="${YEUFONIC_FLUIDSYNTH_SIZE:-1048817}"
CPP_URL="${YEUFONIC_CPP_URL:-https://github.com/yeufonic/yeufonic/releases/download/yue2cpp-linux-8af0174-38a072a2-p1/yue2cpp-linux-8af0174-38a072a2-p1.tar.gz}"
CPP_SHA="${YEUFONIC_CPP_SHA:-9d8759c31674abf653676162fe98998b27d5af884b5b17de69ff22ad1daa5772}"
CPP_SIZE="${YEUFONIC_CPP_SIZE:-856514666}"

# Ollama for Linux (used with --engine yue2cpp). Official Linux releases are .tar.zst.
OLLAMA_URL=https://github.com/ollama/ollama/releases/download/v0.40.13/ollama-linux-amd64.tar.zst
OLLAMA_SHA=c9490e0f520be21271d969e6703f012268b1d39f8b70dd58854e5bfef7a75bb6
OLLAMA_SIZE=1525346571
GEMMA_MODEL=gemma4:e4b-it-qat

HF=https://huggingface.co
COPIES=$HF/pshields/yue2-mothersuperior-copies/resolve/main
GGUF=$HF/Serveurperso/YuE2-GGUF/resolve/e630f2b8f6aedf8254c3186438633c1b5eeaf80a
GGUF_COPIES=$HF/pshields/yue2-gguf-copies/resolve/main

# dir|file|bytes|sha256|url|lyrics|copy — identical checksums to windows/setup.ps1.
model_list() {
  cat <<LIST
checkpoints|yue2_3b_bf16.safetensors|7799983228|33765adbf9813c9a50318218760b2fd819a319862460a04884607581961c6fee|$HF/Comfy-Org/YuE2/resolve/main/checkpoints/yue2_3b_bf16.safetensors|
audio_encoders|sheetsage2_bf16.safetensors|1386868122|5fd960ce3df281e3f3a889d174584d88f96247711480cf96377b12d7e8b6adc5|$HF/Comfy-Org/YuE2/resolve/main/audio_encoders/sheetsage2_bf16.safetensors|
text_encoders|gemma4_e4b_it_int8_convrot.safetensors|8090965702|974d0c838ef4ac1a989b06ccb4e57691c21b6270dd8e345ffa7531f9388f117c|$HF/Comfy-Org/gemma-4/resolve/main/text_encoders/gemma4_e4b_it_int8_convrot.safetensors|lyrics
loras|ar_lora_inst_v3abc_comfyui.safetensors|212891736|de6a11d5701df103a191c87dc73115266e2420f3834739319dec5c24d2119f31|$HF/Mothersuperior/YuE2-instrumental-cot-full-loras/resolve/main/ar_lora_inst_v3abc_comfyui.safetensors||$COPIES/ar_lora_inst_v3abc_comfyui.safetensors
loras|nar_lora_joint_v9_comfyui.safetensors|107518800|cd2bf0d3ce4bf68697daa016671da7d70e34e2f5545617ab9094c96b14a581db|$HF/Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/resolve/main/nar_lora_joint_v9_comfyui.safetensors||$COPIES/nar_lora_joint_v9_comfyui.safetensors
audio_encoders|tokenizer_head_joint_v9.safetensors|171278808|06440f25605c6c12c4e517ef033d7b70b8d9e961b3b06aa3848b1f8028fd7eb8|$HF/Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/resolve/main/tokenizer_head_joint_v9.safetensors||$COPIES/tokenizer_head_joint_v9.safetensors
fs_audio|minted_regularizer_pack_v2.pt|296098847|587631eec5946f9f87d4b422abcda7e35dee43299efb7b7d2fcba4cd8752c475|$HF/Mothersuperior/YuE2-hum-to-song/resolve/main/minted_regularizer_pack_v2.pt||$COPIES/minted_regularizer_pack_v2.pt
LIST
}
int8_model() {
  echo "checkpoints|yue2_3b_int8_convrot.safetensors|3960938800|96fe199377309001ed8cd26a944baeee8cc31a20ba7c36d1d3c0a7e1f4149db6|$HF/Comfy-Org/YuE2/resolve/main/checkpoints/yue2_3b_int8_convrot.safetensors|"
}
# NVIDIA FLUX.2 klein 4B (FP8 + FP4 encoder + VAE), identical to windows/setup.ps1.
picture_list() {
  cat <<LIST
diffusion_models|flux-2-klein-4b-fp8.safetensors|4070624520|97ed34fe0567e436200f2faee3939b88f2b5d99f8af2a4dc16532c4245c0ccb6|$HF/black-forest-labs/FLUX.2-klein-4b-fp8/resolve/main/flux-2-klein-4b-fp8.safetensors
text_encoders|qwen_3_4b_fp4_flux2.safetensors|3848213998|3eab03a77adb0ee5304a4e677d5c10ac22f9049c1d7c894adca4f8bb39206ca8|$HF/Comfy-Org/Flux-2-Klein-4B/resolve/main/split_files/text_encoders/qwen_3_4b_fp4_flux2.safetensors
vae|flux2-vae.safetensors|336211292|868fe7b343cc8f3a19dbcfcafbc3d5f888802be3f89bd81b65b3621a066ce8f3|$HF/Comfy-Org/Flux-2-Klein-4B/resolve/main/split_files/vae/flux2-vae.safetensors
LIST
}
cpp_model_list() {
  cat <<LIST
yue2cpp|YuE2-3B-Q8_0.gguf|3810232064|41121ce97786d7795a325bcf123ca196956c03bb252c9e75384cfc1f2fc19e6b|$GGUF/YuE2-3B-Q8_0.gguf||$GGUF_COPIES/YuE2-3B-Q8_0.gguf
yue2cpp|YuE2-Vae-F32.gguf|530497344|93e49dfb1970e89ad64cacb17cf13b5d05f6bb30ef7ed3adae3050bcb728638a|$GGUF/YuE2-Vae-F32.gguf||$GGUF_COPIES/YuE2-Vae-F32.gguf
yue2cpp|SheetSage2-Q8_0.gguf|105629856|95d8fa8761753b4833782a52b68d5c0afa3bd3cfbc03d3dcbbf8ded0c13f611e|$GGUF/SheetSage2-Q8_0.gguf||$GGUF_COPIES/SheetSage2-Q8_0.gguf
yue2cpp|MERT-v2-FullSong-Q8_0.gguf|902283712|35a6032ec7e8123c02becdefc7bfe10a3adb33faa8a1951dc0af864b4494b8ef|$GGUF/MERT-v2-FullSong-Q8_0.gguf||$GGUF_COPIES/MERT-v2-FullSong-Q8_0.gguf
LIST
}
cpp_full_model() {
  echo "yue2cpp|YuE2-3B-BF16.gguf|7166072352|668ca9ffa4622449916aae5068b5737363e7ec186a824cd3d7a1a8a95269f166|$GGUF/YuE2-3B-BF16.gguf||$GGUF_COPIES/YuE2-3B-BF16.gguf"
}
cpp_picture_encoder() {
  echo "text_encoders|Qwen3-4B-Q4_K_M.gguf|2497281312|f6f851777709861056efcdad3af01da38b31223a3ba26e61a4f8bf3a2195813a|$HF/unsloth/Qwen3-4B-GGUF/resolve/22c9fc8a8c7700b76a1789366280a6a5a1ad1120/Qwen3-4B-Q4_K_M.gguf"
}

engine_models() {
  if [ "$CPP" -eq 1 ]; then
    if [ "$CPP_MODEL" = bf16 ]; then
      cpp_model_list | grep -v '|YuE2-3B-Q8_0.gguf|'
      cpp_full_model
    else
      cpp_model_list
    fi
    model_list | grep '^loras|'
  elif [ "$MODEL_SIZE" = int8 ]; then
    model_list | grep -v '|yue2_3b_bf16.safetensors|'
    int8_model
  else
    model_list
  fi
}

picture_models() {
  if [ "$CPP" -eq 1 ]; then
    picture_list | grep -v '^text_encoders|'
    cpp_picture_encoder
  else
    picture_list
  fi
}

picture_vae_entry() {
  picture_list | grep '^vae|'
}

# FLUX 3 klein GGUF (yue2.cpp only, ungated; weights under FLUX Kommunity License).
picture_flux3_cpp_models() {
  echo "diffusion_models|flux3-image-klein-Q8_0.gguf|6151716032|8b71ffd749bcacbd50cc0acca4f2d31a044c94412743e1e780db99bf13f89752|$HF/leejet/flux-3-image-klein-GGUF/resolve/main/flux3-image-klein-Q8_0.gguf"
  echo "text_encoders|Qwen3VL-4B-Instruct-Q4_K_M.gguf|2497281664|66358cb18bb6b3b1b6675aa412c7a88ef01d228f481184d13668e5201c730a0a|$HF/Qwen/Qwen3-VL-4B-Instruct-GGUF/resolve/main/Qwen3VL-4B-Instruct-Q4_K_M.gguf"
  picture_vae_entry
}

# FIBO 2.0 (ComfyUI only, ungated on Comfy-Org/Fibo-2.0, CC BY-NC 4.0 non-commercial use only).
picture_fibo2_models() {
  echo "diffusion_models|fibo2_dev_int8_convrot.safetensors|8408562474|063dd397395809fd22234c6bd32932cfcb22619f4d2282bdbf1dc58c406fe325|$HF/Comfy-Org/Fibo-2.0/resolve/main/diffusion_models/fibo2_dev_int8_convrot.safetensors"
  echo "loras|fibo_2.0_turbo_lora_avg_rank_270_bf16.safetensors|1989177460|ce149058ba122b15b4323513ba1935cd0d5de4e1b897b2ddcc4d85b196d72ac0|$HF/Comfy-Org/Fibo-2.0/resolve/main/loras/fibo_2.0_turbo_lora_avg_rank_270_bf16.safetensors"
  echo "text_encoders|qwen3vl_4b_int8_convrot.safetensors|4858559240|32de113cbf8282b02cbff0794b637b9d6676da09314a1db5a30bcea9bf4ee01c|$HF/Comfy-Org/Fibo-2.0/resolve/main/text_encoders/qwen3vl_4b_int8_convrot.safetensors"
  picture_vae_entry
}

selected_picture_models() {
  case "${PICTURE_MODEL:-4b}" in
    flux3) picture_flux3_cpp_models ;;
    fibo2) picture_fibo2_models ;;
    *)     picture_models ;;
  esac
}

style_lora_list() {
  cat <<LIST
blgr_kargyraa.safetensors|177279864|5f5e0274fa0233c7f97fc1408d67184d0dafa621508767d02c2c65f74b7e0642
blgr_kargyraa.txt|218|ef6c73a5739e9100330f004b8563ee523df483a9f912f6f52e5e0666800587e0
blgr_rhodope.safetensors|177279960|e6c216c5ee55683e1d75bd4f9fa6b92c67dc5960dc52706fa98f3eeab192656d
blgr_rhodope.txt|252|96bb6d99644b8a5fe30bf9380d054642ca0bfbadfa5c273e1fb0a7a061d13b55
blgr_steppe.safetensors|177279864|adfd9dabaeb5f9cfd61f98e6dfe1a4f908e79e276fd40587c355d8634497f77d
blgr_steppe.txt|243|738d050a0a0abbefaa59c5ecbf93e253563a393111a0bf6f79b03399df813b7c
chnsn_cabaret.safetensors|117500808|0230ff0ba9f75fcf1586b36a8dcfe67f526703c193d9a63cf1c3f5de9c7f896e
chnsn_cabaret.txt|315|2da7dbc56629c46814228a26719dcf42155ca32ef9f4350c74272cb46f2d2ace
chnsn_grand_boulevard.safetensors|177279864|42527d1f61d26693905316f4392e93a2a404906309a37b884c124e38190ae101
chnsn_grand_boulevard.txt|264|874064b90d57d0f1c97f5cacc3e294fa4aa1081a5b848c0e978623cb27d9902d
chnsn_montmartre.safetensors|117500808|bcbf1b5aebe2947b1677f87265f0d422adf868745bec12462e39ed9897c9dc65
chnsn_montmartre.txt|310|c808d526e4423bfd984d284ffd66d2ada3894cfaadd1250c92dd4225e2ddf470
chnsn_rive_gauche.safetensors|177279864|8421a25b6650febf8e6b7418b1830dc27d79fab57605962f2c6890be98c42ef6
chnsn_rive_gauche.txt|308|f6a6e6a20dda3bd7daee7e53cbd6dd37b438e40b85095dd7e001d13bcb92ec06
cnzn_coro.safetensors|117500808|c0708785f63a7f6d582d172120aa64e8085a3f578ac5b722cb36a2c2b1e347ed
cnzn_coro.txt|232|f8180110ba36e12488e521f5695f08edd05eceb1392150905f576e0901074849
cnzn_notte.safetensors|117500808|93b87d31bbce1dfb4e83be9d1f55e155b71f3572e640eda5351e7a34f0f32527
cnzn_notte.txt|279|46ef979461e8505fcf80f3f99fbef1659c29468e50554ff5439e2a435a270ad1
cnzn_sanremo.safetensors|177279960|8a0322971cfe484414d01f0765092f2454384a18cfa4167824832346451cade0
cnzn_sanremo.txt|299|fc4c4bb3d82617a2dd3b66ff0f809360a5311144d4ed5caba020aa54c9e1fe25
cnzn_sussurro.safetensors|117500808|2ec3fc4eab4413623c600015ba3f5b7ce59f5604668344912cd2eb495b0bbd63
cnzn_sussurro.txt|342|3f9c829d54356dfcef44fcbb15b8f2ca89cf95c3faa215001d6e13f9f37060d9
cnzn_teatro.safetensors|117500808|6faef04d10c20a28b311815421e12676b3abfa5c650bfbd1fff1a0c01d48f31d
cnzn_teatro.txt|285|15a125c3e2a268e7fcbcd09e95e9cd58fa5747b0bd6be559770557b450b53944
dreampop_sv_dreampop.safetensors|234969024|617852d379c66b0407879421a353233d29cda8188cca82973a94c61b512ca03d
dreampop_sv_dreampop.txt|387|588c63e08b70640b78eb141cb4d6a3f99e42f54f50e49e6465cef4a4ef65a7fe
drksf_midnight.safetensors|177279760|924076bc78c0ef29d6705341e82c4d292bf557dcc9743045b4fca9bb77e7f580
drksf_midnight.txt|334|d38ea4d03e69eb3c79d4415fee82b603118d4be86e6b0b24e15a891344c24f59
mltnt_chanter.safetensors|117500816|4aaaa42f7c61b4a3226880dd1e6f1a36bd585171d26a45358c3dba3c9d56b20c
mltnt_chanter.txt|359|b7e1f6ede32b6578d5e2cd33fad975aeb85141d0a83e260c698224e6cd3ef1f5
mltnt_frontline.safetensors|177279880|9c8960158db6340156cc1b44fbec1ff58d0bfabfc96e933ee5a1d14b0bc26574
mltnt_frontline.txt|357|cb33570cfc0005371ef1888546cc6dc020bde8be6a7960b0f9203d9c7c390903
mltnt_fusion.safetensors|177279784|e9525b892ce625ac7491a13c21b39b7623ef132884996a87eb341370f459aa7b
mltnt_fusion.txt|272|4a4886eb5d4e554f5ac9e7f4e73843b8920bcefaead50f95ba46a6e7502df29c
mltnt_roots.safetensors|177279888|e829f3af1534614bc28f85e821115d48888edf35aead317e9b5cdf179a79f5f3
mltnt_roots.txt|209|3304dd0f8c160eee5465be5c169780916bd7487824cd6b19c1defd0d0abe69d0
mltnt_soundclash.safetensors|117500816|fa43a4ddb7af26fb0e7821c1ad3386fc90db84897efd00571e0c7f27cf790537
mltnt_soundclash.txt|330|d5a988ebbe5ee8dceee6f758a178eeb04430cbf11984ff84ede647769d3c04d7
mltnt_steppers.safetensors|177279888|63094f0bbf8dd1e1fb2654a94aaba77e7360b0bef08d2254ef4a972ea8dce10e
mltnt_steppers.txt|232|dade8fa79bf12ea685b02b9a3fb5b4a9243a34ba42bd9f622f01d789b77f57b9
qwwl_mehfil.safetensors|177279760|28132e4b545b3c57a831179553e509408fa11d6eed96811c50f0d2629ddceb2e
qwwl_mehfil.txt|359|5d09c0ec81338395b17b8788bd8c6cf597f0307f9b26d3ff8aa7ca0a7c831582
slider-acoustic-folk.safetensors|10113448|b51c0f8a80d1001e19a2650e3184ed188c3aac97c1e2cd9cb3ec5ed03a6efef0
slider-acoustic-folk.txt|341|0b9a3f253d774133f0f021e07d1e484354b06993e7211376ae7ecc43fcc9ecec
slider-afrobeats.safetensors|10113448|7b0be8a08aa9bb63579d3daf6f23f08f36084282c1e143be7aa2184088a86982
slider-afrobeats.txt|339|921d7cea8aba2282a771fdfb20e0b5ed3e2284b2c4dc595201794fcd11951878
slider-country.safetensors|10113448|c41c13e09e0daf764808be8cdbe6970b3bce359c11460584ccb09b4d502aee2a
slider-country.txt|330|cbbe724e264dc8548dec51d1123dc91da7d82a37010518279bb2eeae56e8ef3e
slider-disco-funk.safetensors|10113448|89149145bc3f69518a7b9de63672083f994786c9af66822ef11d7b521f82cb27
slider-disco-funk.txt|343|d3e3759eeb72ac67e8a30545bfe5bfde618352d16b240b78202d6a8a41d50ed7
slider-female.safetensors|10113448|a760f6535b9be6412aec12e8ebd30c45c7886ecb01007dc900c944d57cce4a53
slider-female.txt|329|6b9c69609cc65d1ffdb14f0761283741f98124ae90daaad4ae5954c701032ab5
slider-hiphop.safetensors|10113448|544481919541a7f97fa581911a71fdeace03a55ddd15172a58a60ec60b963cad
slider-hiphop.txt|325|cb5aba62431e1f480d6502ddea6678ae68e3b11f2878f820d8e89cc787c95144
slider-house.safetensors|10113448|6149fcde75b7f959c323ebd90f760dc7994183aef1a9345482fddf530c06737a
slider-house.txt|333|5bf43f69b59d8b8f7eb3da675bec0b2e5a0c6fc8456871e9e9037c42390b7306
slider-indie-rock.safetensors|10113448|bf97b12ae89317343b1498f0bb066dbf01aa547381d60b6cf9b163db05f1b5d9
slider-indie-rock.txt|333|25fe649e8b414b09760b2fac5e6e7970f9f733ba838997af8cef3dba688a0a7a
slider-kpop.safetensors|10113448|eca99b3b12bf94e1a605122a99c42bb3123c0d32bdb93758ee9967d20fc7458c
slider-kpop.txt|331|9e1a9e8057178c689ea4d869c883eddc62b041c28b96c346eaf380b42c23f9be
slider-lofi.safetensors|10113448|14474d0273924c7abe3b3b2caae794ae9052cff9a392985ff9540f0829067db4
slider-lofi.txt|331|4d37f0cc153b6f2486a36c44a093eca0729feaedcdd452baddab9d4f7b22349b
slider-male.safetensors|10113448|125a5e3adad5e1c541ad47bd377f1e7ff4edffc02f7552895dd6eb86dda7b5c1
slider-male.txt|325|0b65c5e885a29267fd1141b486edc07a47d9c039bdde813d33308c0cc7a10ae5
slider-metal.safetensors|10113448|8ae844629dcaf4fd55f13ed123f24ace69fa28951382e7652e169a6c9b7a4d5b
slider-metal.txt|335|93a52f3f387f20906d1a9dfc9352ad0c09a620aab60251247cd25f46688a7522
slider-pop-punk.safetensors|10113448|bb8d8e4146f872c74ade1e6982946f84be1538a618a922ff9eb9674539ec34c3
slider-pop-punk.txt|330|dafbe727ea18498a1334fa836a81ffebe47d79ec9c032ae2fe78e937cc1ed7f2
slider-pop.safetensors|10113448|bc6642b68882fbc0f73df4a0e89a51c1ebe144bc1ded5b877b5dd157ffa48cd2
slider-pop.txt|323|66699ef7c06098f77d4514d72aed2e12ceae22735d91829ea1984c20442b7604
slider-reggaeton.safetensors|10113448|297623d8a2546749bfa7190acc5de7bfdb02135358156558cd7a8506f1a905ff
slider-reggaeton.txt|339|730d823a662eb143088ada83e838f49851cd4ea0a5282c7467045a784ad574f6
slider-rnb.safetensors|10113448|faa89944f0d3c9a7e17f62374e29ee76d1d82f5283674060d11a811eaf9f632d
slider-rnb.txt|324|220d04247170392e2dfe9c2daaa13d5e648034da547ef49e72d36b47951f7b9c
sv_oldschoolhiphop.safetensors|234969032|ca176909d55998d4f78426439885ff79cc96ba4daaaaea22a9936590d6e72694
sv_oldschoolhiphop.txt|431|93c332bb5c5cfb6b387cb32335a4e398381804597af888d47e7b620e7ea7086a
yue2_jpop_t4.safetensors|106474864|8cdbe15cf1968ff586d734a8ce4f8e7c823f8a8005fe1466c5aa9f442d257d57
yue2_jpop_t4.txt|231|f799ce448332f646850d3dab41c182d5819c39c2840a8f3617464574fab2f173
LIST
}

RVC_HF=$HF/lj1995/VoiceConversionWebUI/resolve/main
PYMSS_HF=$HF/baicai1145/pymss/resolve/main/vocal/vocal_extraction
VOICE_COPIES=https://github.com/yeufonic/yeufonic/releases/download/voice-models-1
voice_list() {
  cat <<LIST
assets/hubert_base|config.json|1492|0346950779dfb7f9316fa74ed846e2b8a22a08eedfdc5387b73f327cb1a4a7cf|$RVC_HF/hubert_base/config.json|$VOICE_COPIES/hubert_base.config.json
assets/hubert_base|preprocessor_config.json|225|7c1976a680fb7acc757cd36fb08eef878fa36c70b4c9d2d595df9c608bbbbf0e|$RVC_HF/hubert_base/preprocessor_config.json|$VOICE_COPIES/hubert_base.preprocessor_config.json
assets/hubert_base|pytorch_model.bin|189206711|cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5|$RVC_HF/hubert_base/pytorch_model.bin|$VOICE_COPIES/hubert_base.pytorch_model.bin
assets/rmvpe|rmvpe.pt|181184272|6d62215f4306e3ca278246188607209f09af3dc77ed4232efdd069798c4ec193|$RVC_HF/rmvpe.pt|$VOICE_COPIES/rmvpe.pt
assets/pretrained_v2|f0G48k.pth|75465569|b5d51f589cc3632d4eae36a315b4179397695042edc01d15312e1bddc2b764a4|$RVC_HF/pretrained_v2/f0G48k.pth|$VOICE_COPIES/f0G48k.pth
assets/pretrained_v2|f0D48k.pth|142875703|2269b73c7a4cf34da09aea99274dabf99b2ddb8a42cbfb065fb3c0aa9a2fc748|$RVC_HF/pretrained_v2/f0D48k.pth|$VOICE_COPIES/f0D48k.pth
assets/pymss/vocal/vocal_extraction|model_bs_roformer_ep_317_sdr_12.9755.ckpt|639331213|5b84f37e8d444c8cb30c79d77f613a41c05868ff9c9ac6c7049c00aefae115aa|$PYMSS_HF/model_bs_roformer_ep_317_sdr_12.9755.ckpt|$VOICE_COPIES/model_bs_roformer_ep_317_sdr_12.9755.ckpt
assets/pymss/vocal/vocal_extraction|model_bs_roformer_ep_317_sdr_12.9755.yaml|2279|3dae086b481bc6adecccb6bdfd2386ffd78708e11c221876a146972cab5b2afe|$PYMSS_HF/model_bs_roformer_ep_317_sdr_12.9755.yaml|$VOICE_COPIES/model_bs_roformer_ep_317_sdr_12.9755.yaml
.|mute.zip|312273|ee948e85213e4ed2f2ba2f8dfcee810bfd0b63131d91450e920bbe1cbd0321d0|$RVC_HF/mute.zip|$VOICE_COPIES/mute.zip
LIST
}

whisper_engine_list() {
  local base="$HF/dropbox-dash/faster-whisper-large-v3-turbo/resolve/main"
  cat <<LIST
config.json|2263||$base/config.json
preprocessor_config.json|340||$base/preprocessor_config.json
tokenizer.json|2710337||$base/tokenizer.json
vocabulary.json|1068114||$base/vocabulary.json
model.bin|1617884929|e76620f83d5f5b69efd3d87e3dc180c1bd21df9fbebacfd4335e5e1efcc018da|$base/model.bin
LIST
}

soundfont_list() {
  cat <<LIST
github_Jnsgm2.sf2|33187490|dc48cb5c322cab23fce1b18442066be30ccc49a184603c7a3bf7615003ee137d|https://raw.githubusercontent.com/wrightflyer/SF2_SoundFonts/master/Jnsgm2.sf2
Arachno_SoundFont_Version_1.0.sf2|155405818|9a57fb3b6714e69dda12390e351b087e81fc3b1eca15c6b4bbe172799f4cf3cd|https://archive.org/download/free-soundfonts-sf2-2019-04/Arachno_SoundFont_Version_1.0.sf2
LIST
}

# ------------------------------------------------------------------- helpers
log_line() {
  if [ "$CHECK_ONLY" -eq 0 ] && [ -d "$LOGS" ]; then
    printf '%s\n' "$*" >> "$LOGS/setup.log" 2>/dev/null || true
  fi
}
say() {
  printf '%s\n' "$*"
  log_line "$*"
}
step() {
  say ""
  say "== $*"
}
mark_done() { date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE/$1.done"; }
is_done() { [ -f "$STATE/$1.done" ]; }

ACTIVE_DL_PID=""
PY313=""

# Choose UTF-8 block characters on UTF-8 terminals, plain ASCII otherwise.
case "${LC_ALL:-${LC_CTYPE:-${LANG:-}}}" in
  *[Uu][Tt][Ff]-8*|*[Uu][Tt][Ff]8*)
    BAR_FULL="████████████████████████████"
    BAR_EMPTY="░░░░░░░░░░░░░░░░░░░░░░░░░░░░"
    ;;
  *)
    BAR_FULL="############################"
    BAR_EMPTY="............................"
    ;;
esac
BAR_WIDTH=28

cleanup_dl() {
  if [ -n "$ACTIVE_DL_PID" ] && kill -0 "$ACTIVE_DL_PID" 2>/dev/null; then
    kill "$ACTIVE_DL_PID" 2>/dev/null || true
    wait "$ACTIVE_DL_PID" 2>/dev/null || true
  fi
  ACTIVE_DL_PID=""
  if [ "$IS_TTY" -eq 1 ]; then
    printf '\r\033[K\n' >&3 2>/dev/null || true
  fi
  echo "Interrupted. Partial downloads are kept and will resume on the next run."
  exit 130
}
trap cleanup_dl INT TERM

stop_setup() {
  trap - ERR
  if [ -n "$ACTIVE_DL_PID" ] && kill -0 "$ACTIVE_DL_PID" 2>/dev/null; then
    kill "$ACTIVE_DL_PID" 2>/dev/null || true
    wait "$ACTIVE_DL_PID" 2>/dev/null || true
  fi
  ACTIVE_DL_PID=""
  say ""
  say "Setup stopped: $1"
  if [ "$CHECK_ONLY" -eq 0 ]; then
    say "The details are in $LOGS/setup.log."
    say "Run setup again to carry on from where it stopped."
  fi
  exit 1
}
trap 'stop_setup "an unexpected error at line $LINENO"' ERR

sha_of() { sha256sum "$1" | awk '{print $1}'; }
size_of() { stat -c %s "$1"; }

fmt_bytes() {
  local b="${1:-0}"
  if [ "$b" -ge 1000000000 ]; then
    local g=$((b / 1000000000))
    local rem=$(((b % 1000000000) / 10000000))
    printf '%d.%02d GB' "$g" "$rem"
  elif [ "$b" -ge 1000000 ]; then
    local m=$((b / 1000000))
    local rem=$(((b % 1000000) / 100000))
    printf '%d.%d MB' "$m" "$rem"
  elif [ "$b" -ge 1000 ]; then
    printf '%d KB' $((b / 1000))
  else
    printf '%d B' "$b"
  fi
}

fmt_time() {
  local s="${1:-0}"
  if [ "$s" -ge 3600 ]; then
    printf '%dh %02dm' $((s / 3600)) $(((s % 3600) / 60))
  elif [ "$s" -ge 60 ]; then
    printf '%dm %02ds' $((s / 60)) $((s % 60))
  else
    printf '%ds' "$s"
  fi
}

# Run a command directly on the terminal so native progress bars (uv, faster_whisper, demucs,
# ollama pull) render live, while logging the command invocation and exit status to setup.log.
run_live() {
  log_line "  running: $*"
  if [ "$IS_TTY" -eq 1 ]; then
    "$@"
  else
    local rc=0
    if [ "$CHECK_ONLY" -eq 0 ] && [ -d "$LOGS" ]; then
      "$@" 2>&1 | tee -a "$LOGS/setup.log" || rc=${PIPESTATUS[0]}
      return "$rc"
    fi
    "$@"
  fi
}

http_head() {
  if command -v curl >/dev/null 2>&1; then
    curl -s -o /dev/null -I --connect-timeout 8 --max-time 12 "$1"
  elif command -v wget >/dev/null 2>&1; then
    wget -q --spider --timeout=12 "$1"
  else
    return 1
  fi
}

# Download one file with a clean single-line CLI progress bar on TTY (bar, %, size, speed, ETA)
# and milestone lines when non-TTY. Returns curl/wget's exit code without triggering ERR trap.
download_with_progress() {
  local url="$1" dest_part="$2" total="${3:-0}" resume="${4:-1}"
  local err_file="$dest_part.err"
  local start_bytes=0
  [ "$resume" -eq 1 ] && [ -f "$dest_part" ] && start_bytes="$(stat -c %s "$dest_part" 2>/dev/null || echo 0)"
  [ "$resume" -eq 0 ] && rm -f "$dest_part"
  rm -f "$err_file"

  if command -v curl >/dev/null 2>&1; then
    if [ "$resume" -eq 1 ]; then
      curl -sS -L --fail --retry 5 -C - -o "$dest_part" "$url" 2>"$err_file" &
    else
      curl -sS -L --fail --retry 5 -o "$dest_part" "$url" 2>"$err_file" &
    fi
  else
    if [ "$resume" -eq 1 ]; then
      wget -q --tries=5 -c -O "$dest_part" "$url" 2>"$err_file" &
    else
      wget -q --tries=5 -O "$dest_part" "$url" 2>"$err_file" &
    fi
  fi
  ACTIVE_DL_PID=$!

  local t_start="$SECONDS"
  local last_milestone=0
  local spin_i=0
  local spin_chars='|/-\'
  local cur=0 pct=0 filled=0 empty=0 elapsed=0 delta=0 speed=0 eta_str=""

  while kill -0 "$ACTIVE_DL_PID" 2>/dev/null; do
    cur="$(stat -c %s "$dest_part" 2>/dev/null || echo 0)"
    elapsed=$((SECONDS - t_start))
    delta=$((cur - start_bytes))
    [ "$delta" -lt 0 ] && delta=0
    if [ "$elapsed" -gt 0 ] && [ "$delta" -gt 0 ]; then
      speed=$((delta / elapsed))
    else
      speed=0
    fi

    if [ -n "$total" ] && [ "$total" -gt 0 ]; then
      pct=$((cur * 100 / total))
      [ "$pct" -gt 100 ] && pct=100
      if [ "$IS_TTY" -eq 1 ]; then
        filled=$((pct * BAR_WIDTH / 100))
        empty=$((BAR_WIDTH - filled))
        if [ "$speed" -gt 0 ] && [ "$cur" -lt "$total" ]; then
          eta_str="ETA $(fmt_time $(((total - cur) / speed)))"
        else
          eta_str=""
        fi
        printf '\r  [%s%s] %3d%%  %s / %s  %s/s  %s\033[K' \
          "${BAR_FULL:0:filled}" "${BAR_EMPTY:0:empty}" "$pct" \
          "$(fmt_bytes "$cur")" "$(fmt_bytes "$total")" "$(fmt_bytes "$speed")" "$eta_str" >&3
      else
        if [ "$pct" -ge $((last_milestone + 25)) ] && [ "$pct" -lt 100 ]; then
          last_milestone=$(((pct / 25) * 25))
          say "  ${last_milestone}% ($(fmt_bytes "$cur") / $(fmt_bytes "$total"), $(fmt_bytes "$speed")/s)"
        fi
      fi
    elif [ "$IS_TTY" -eq 1 ]; then
      local ch="${spin_chars:spin_i%4:1}"
      spin_i=$((spin_i + 1))
      printf '\r  [%s] %s  %s/s\033[K' "$ch" "$(fmt_bytes "$cur")" "$(fmt_bytes "$speed")" >&3
    fi
    sleep 0.25
  done

  local code=0
  wait "$ACTIVE_DL_PID" || code=$?
  ACTIVE_DL_PID=""

  cur="$(stat -c %s "$dest_part" 2>/dev/null || echo 0)"
  elapsed=$((SECONDS - t_start))
  delta=$((cur - start_bytes))
  [ "$delta" -lt 0 ] && delta=0
  if [ "$elapsed" -gt 0 ] && [ "$delta" -gt 0 ]; then
    speed=$((delta / elapsed))
  else
    speed="$delta"
  fi

  if [ "$code" -eq 0 ]; then
    if [ "$IS_TTY" -eq 1 ]; then
      if [ -n "$total" ] && [ "$total" -gt 0 ]; then
        printf '\r  [%s] 100%%  %s  (%s, %s/s)\033[K\n' \
          "$BAR_FULL" "$(fmt_bytes "$cur")" "$(fmt_time "$elapsed")" "$(fmt_bytes "$speed")" >&3
      else
        printf '\r  done  %s  (%s, %s/s)\033[K\n' \
          "$(fmt_bytes "$cur")" "$(fmt_time "$elapsed")" "$(fmt_bytes "$speed")" >&3
      fi
    fi
    # Record one clean summary line in setup.log (without duplicating to TTY).
    if [ "$CHECK_ONLY" -eq 0 ] && [ -f "$LOGS/setup.log" ]; then
      echo "  downloaded $(basename "$dest_part" .part): $(fmt_bytes "$cur") in $(fmt_time "$elapsed") ($(fmt_bytes "$speed")/s)" >> "$LOGS/setup.log"
    fi
  else
    [ "$IS_TTY" -eq 1 ] && printf '\r\033[K' >&3
    if [ -s "$err_file" ]; then
      say "  download error: $(head -n 2 "$err_file" | tr '\n' ' ')"
    fi
  fi
  rm -f "$err_file"
  return "$code"
}

# Verify SHA-256 with a live progress bar for large files (>= 50 MB) when Python is available.
verify_sha() {
  local file="$1" expected="$2"
  local actual=""
  local fsize
  fsize="$(size_of "$file")"
  if [ "$IS_TTY" -eq 1 ] && [ "$fsize" -ge 50000000 ] && [ -n "$PY313" ] && [ -x "$PY313" ]; then
    actual="$("$PY313" - "$file" "$fsize" "$BAR_FULL" "$BAR_EMPTY" "$BAR_WIDTH" 3>&3 <<'PY'
import hashlib, os, sys
path, total, full, empty, width = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], int(sys.argv[5])
h = hashlib.sha256()
done = 0
last = -1
tty = os.fdopen(3, "w", buffering=1)
with open(path, "rb") as fh:
    while chunk := fh.read(4 * 1024 * 1024):
        h.update(chunk)
        done += len(chunk)
        pct = min(100, done * 100 // total) if total else 100
        if pct != last:
            last = pct
            n = pct * width // 100
            tty.write(f"\r  [{full[:n]}{empty[:width - n]}] {pct:3d}%  verifying checksum...\033[K")
tty.write("\r\033[K")
print(h.hexdigest())
PY
)"
  else
    say "  verifying checksum..."
    actual="$(sha_of "$file")"
  fi
  [ "$actual" = "$expected" ]
}

# get_verified URL DEST SIZE SHA [COPY] [LABEL] [KEEP_IF_PRESENT]
# Skips files already verified on disk (or any existing copy when KEEP_IF_PRESENT=1),
# unless --force-downloads was passed.
get_verified() {
  local url="$1" dest="$2" size="$3" sha="$4" copy="${5:-}" label="${6:-}" keep="${7:-0}"
  LAST_USED_FALLBACK=0
  local name prefix
  name="$(basename "$dest")"
  prefix="${label:+$label }"

  if [ "$FORCE_DOWNLOADS" -eq 1 ]; then
    rm -f "$dest" "$dest.sha256ok" "$dest.part"
  else
    if [ "$keep" = "1" ] && [ -f "$dest" ]; then
      say "${prefix}${name} — already present, skipping"
      return 0
    fi
    if [ -f "$dest" ] && [ -f "$dest.sha256ok" ]; then
      say "${prefix}${name} — already present, skipping"
      return 0
    fi
    if [ -f "$dest" ]; then
      # File exists without .sha256ok (e.g. copied from another install): keep it if size + checksum match.
      if [ -n "$size" ] && [ "$(size_of "$dest")" != "$size" ]; then
        say "${prefix}${name} — incomplete copy found ($(fmt_bytes "$(size_of "$dest")") of $(fmt_bytes "$size")), re-downloading"
        rm -f "$dest"
      else
        say "${prefix}${name} — already present, verifying checksum"
      fi
    fi
  fi

  if [ ! -f "$dest" ]; then
    if [ -n "$size" ] && [ "$size" -gt 0 ]; then
      say "${prefix}Downloading ${name} ($(fmt_bytes "$size"))"
    else
      say "${prefix}Downloading ${name}"
    fi
    local try source tries=6 got=0 code
    [ -n "$copy" ] && tries=3
    for source in $copy $url; do
      for try in $(seq 1 "$tries"); do
        code=0
        download_with_progress "$source" "$dest.part" "$size" 1 || code=$?
        if [ "$code" -eq 0 ]; then
          got=1
          [ -n "$copy" ] && [ "$source" = "$url" ] && LAST_USED_FALLBACK=1
          break
        fi
        if [ "$code" -eq 22 ] || [ "$try" -eq "$tries" ]; then break; fi
        say "  the download broke off; trying again ($try of $((tries - 1)))"
        sleep $((5 * try))
      done
      [ "$got" -eq 1 ] && break
      rm -f "$dest.part"
      [ "$source" != "$url" ] && say "  could not download it from $source; trying $url"
    done
    [ "$got" -eq 1 ] || stop_setup "could not download $url"
    mv -f "$dest.part" "$dest"
  fi
  if [ -n "$size" ] && [ "$(size_of "$dest")" != "$size" ]; then
    rm -f "$dest"
    stop_setup "$name came down the wrong size; it has been removed, so the next run fetches it again"
  fi
  if [ -n "$sha" ]; then
    if ! verify_sha "$dest" "$sha"; then
      rm -f "$dest"
      stop_setup "$name did not match its published checksum; it has been removed, so the next run fetches it again"
    fi
  fi
  date -u +%Y-%m-%dT%H:%M:%SZ > "$dest.sha256ok"
}

get_commit() {
  local repo="$1" commit="$2" dest="$3" also="${4:-}"
  local archive source got=0 code
  archive="$DOWNLOADS/$(echo "$repo" | tr / _)-${commit:0:8}.tar.gz"
  if [ ! -f "$archive" ]; then
    for source in $repo $also; do
      say "Downloading $source at ${commit:0:8}"
      code=0
      download_with_progress "https://codeload.github.com/$source/tar.gz/$commit" "$archive.part" 0 0 || code=$?
      if [ "$code" -eq 0 ]; then
        got=1; break
      fi
      rm -f "$archive.part"
    done
    [ "$got" -eq 1 ] || stop_setup "could not download $repo"
    mv -f "$archive.part" "$archive"
  fi
  local tmp="$DOWNLOADS/unpack"
  rm -rf "$tmp"; mkdir -p "$tmp"
  tar -xzf "$archive" -C "$tmp"
  rm -rf "$dest"
  mv "$tmp"/* "$dest"
  rm -rf "$tmp"
}

# Instant kernel port check via /proc/net/tcp{,6} (state 0A = LISTEN).
# Never opens a TCP socket (which can hang on firewalls / WSL2 mirrored networking) and never
# touches shell file descriptors like FD 3. Portable across mawk, gawk, and busybox awk.
port_taken() {
  local hex
  hex="$(printf '%04X' "$1")"
  awk -v p=":$hex" 'NR>1 && $4=="0A" && substr($2, length($2)-4)==p { found=1; exit } END { exit !found }' \
    /proc/net/tcp /proc/net/tcp6 2>/dev/null
}

# Extract a .zip using Python's stdlib zipfile (avoids requiring the host 'unzip' package).
extract_zip() {
  local zip="$1" dest="$2"
  mkdir -p "$dest"
  "$PY313" -m zipfile -e "$zip" "$dest"
}

# Extract a .tar.zst using system zstd if present, else uv + zstandard wheel (zero sudo).
extract_zst() {
  local archive="$1" dest="$2"
  mkdir -p "$dest"
  if command -v zstd >/dev/null 2>&1; then
    tar -I zstd -xf "$archive" -C "$dest"
  else
    "$UV" run --no-project --python "$PY313" --with zstandard python -c \
      "import io, sys, tarfile, zstandard; d = zstandard.ZstdDecompressor();
with open(sys.argv[1], 'rb') as fh, d.stream_reader(fh) as r, tarfile.open(fileobj=r, mode='r|') as tf: tf.extractall(sys.argv[2])" \
      "$archive" "$dest"
  fi
}

# -------------------------------------------------------------- system check
step "Checking this Linux machine"
problems=""
warnings=""
problem() { problems="$problems$1"$'\n'; }
warning() { warnings="$warnings$1"$'\n'; }

OS_NAME="$(uname -s)"
ARCH="$(uname -m)"
DISTRO="Linux"
DISTRO_ID=""
DISTRO_LIKE=""
if [ -f /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  DISTRO="${PRETTY_NAME:-Linux}"
  DISTRO_ID="${ID:-}"
  DISTRO_LIKE="${ID_LIKE:-}"
fi
IS_WSL=0
if grep -qi microsoft /proc/version 2>/dev/null; then
  IS_WSL=1
  say "$DISTRO, $ARCH (WSL2)"
else
  say "$DISTRO, $ARCH"
fi

[ "$OS_NAME" = Linux ] || problem "This installer is for Linux (found $OS_NAME)."
[ "$ARCH" = x86_64 ] || problem "Yeufonic for Linux needs an x86_64 (amd64) processor; this machine is $ARCH."

if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
  problem "Neither curl nor wget is installed. Install curl and run setup again."
fi
for base_cmd in tar gzip sha256sum; do
  command -v "$base_cmd" >/dev/null 2>&1 || problem "Required command '$base_cmd' is missing."
done

# glibc version check (PyTorch wheels and Yeufonic C++ binaries target glibc >= 2.28).
GLIBC_VER="$(ldd --version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+$' || true)"
if [ -n "$GLIBC_VER" ]; then
  say "glibc: $GLIBC_VER"
  g_maj="${GLIBC_VER%%.*}"
  g_min="${GLIBC_VER#*.}"
  if [ "$g_maj" -lt 2 ] || { [ "$g_maj" -eq 2 ] && [ "$g_min" -lt 28 ]; }; then
    problem "glibc $GLIBC_VER is too old; glibc 2.28 or newer is required (Ubuntu 20.04+, Debian 10+, RHEL/Rocky 8+)."
  fi
fi

# NVIDIA GPU and driver check (run before component prompts so the user sees their GPU/VRAM first).
SMI="$(command -v nvidia-smi 2>/dev/null || true)"
if [ -z "$SMI" ] && [ -x /usr/lib/wsl/lib/nvidia-smi ]; then
  SMI=/usr/lib/wsl/lib/nvidia-smi
fi
VARIANT=""
DRIVER_MAJOR=0
GPU_NAME=""
VRAM_GB=""
COMPUTE_CAP=""
if [ -z "$SMI" ]; then
  problem "No NVIDIA graphics card was found (nvidia-smi is missing). Yeufonic needs an NVIDIA GPU with the proprietary NVIDIA driver installed."
else
  GPU_LINE="$("$SMI" --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader,nounits 2>/dev/null | head -1 || true)"
  if [ -z "$GPU_LINE" ]; then
    problem "The NVIDIA driver did not answer nvidia-smi. Check your NVIDIA driver installation and reboot if it was just updated."
  else
    IFS=',' read -r GPU_NAME VRAM_MB DRIVER_VER COMPUTE_CAP <<< "$GPU_LINE"
    GPU_NAME="$(echo "$GPU_NAME" | xargs)"
    VRAM_MB="$(echo "$VRAM_MB" | xargs)"
    DRIVER_VER="$(echo "$DRIVER_VER" | xargs)"
    COMPUTE_CAP="$(echo "$COMPUTE_CAP" | xargs)"
    VRAM_GB="$(awk -v m="$VRAM_MB" 'BEGIN { printf "%.1f", m / 1024 }')"
    say "Graphics card: $GPU_NAME, $VRAM_GB GB, driver $DRIVER_VER, compute $COMPUTE_CAP"
    DRIVER_MAJOR="${DRIVER_VER%%.*}"
    case "$DRIVER_MAJOR" in
      ''|*[!0-9]*) DRIVER_MAJOR=0; problem "Could not parse NVIDIA driver version ($DRIVER_VER)." ;;
      *)
        if [ "$DRIVER_MAJOR" -ge 580 ]; then
          VARIANT=cu130
        elif [ "$DRIVER_MAJOR" -ge 525 ]; then
          VARIANT=cu128
          warning "NVIDIA driver $DRIVER_VER uses CUDA 12 (PyTorch cu128). Driver 580 or later (CUDA 13) gives much faster INT8 and local Gemma performance."
        else
          problem "NVIDIA driver $DRIVER_VER is too old (525 or later required; 580+ recommended)."
        fi
        ;;
    esac
  fi
fi

# Read the dynamic linker cache once (check /sbin and /usr/sbin for non-root Debian/RHEL shells).
# Always match via here-string (<<<) rather than piping into grep -q, which triggers SIGPIPE under pipefail.
LDCONFIG="$(command -v ldconfig 2>/dev/null || true)"
if [ -z "$LDCONFIG" ]; then
  for p in /sbin/ldconfig /usr/sbin/ldconfig; do
    [ -x "$p" ] && { LDCONFIG="$p"; break; }
  done
fi
LDCACHE=""
[ -n "$LDCONFIG" ] && LDCACHE="$("$LDCONFIG" -p 2>/dev/null || true)"

# Verify libcuda.so.1 is present so PyTorch can actually talk to the driver.
if [ -n "$SMI" ]; then
  if ! grep -q 'libcuda\.so\.1' <<< "$LDCACHE" && [ ! -e /usr/lib/wsl/lib/libcuda.so.1 ]; then
    problem "libcuda.so.1 was not found in the system library cache. Reinstall the NVIDIA driver userspace libraries."
  fi
fi

# System RAM check.
RAM_KB="$(awk '/^MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)"
RAM_GB="$(awk -v k="$RAM_KB" 'BEGIN { printf "%.1f", k / 1048576 }')"
say "Memory: $RAM_GB GB"
if awk -v r="$RAM_GB" 'BEGIN { exit !(r + 0 < 15.0) }'; then
  warning "This machine has $RAM_GB GB of RAM; 16 GB is recommended."
fi

# WSL2 filesystem advice.
if [ "$IS_WSL" -eq 1 ]; then
  case "$INSTALL_DIR" in
    /mnt/[a-z]/*)
      warning "Install path ($INSTALL_DIR) is on the Windows filesystem (/mnt/...), which is very slow under WSL2. Install inside your Linux home directory instead." ;;
  esac
fi

# Interactive component choices (mirroring the Windows installer's components page).
# Asked once on an interactive terminal and remembered in state/, so updates do not ask again.
ask_yes_no() {
  local var="$1" prompt="$2" default="${3:-no}" ans="" hint="[y/N]"
  [ "$default" = yes ] && hint="[Y/n]"
  printf '%s %s ' "$prompt" "$hint"
  read -r ans || ans=""
  log_line "$prompt $hint $ans"
  case "$ans" in
    [yY]*) printf -v "$var" '%s' yes ;;
    [nN]*) printf -v "$var" '%s' no ;;
    *)     printf -v "$var" '%s' "$default" ;;
  esac
}

ask_choice() {
  local var="$1" prompt="$2" opt1="$3" opt2="$4" default="${5:-1}" ans=""
  printf '%s [%s]: ' "$prompt" "$default"
  read -r ans || ans=""
  log_line "$prompt [$default]: $ans"
  case "${ans:-$default}" in
    2|"$opt2") printf -v "$var" '%s' "$opt2" ;;
    *)         printf -v "$var" '%s' "$opt1" ;;
  esac
}

INTERACTIVE=0
if [ -z "$problems" ] && [ "$CHECK_ONLY" -eq 0 ] && [ -t 0 ] && { [ "$SKIP_MODELS" -eq 0 ] || [ "$RECONFIGURE" -eq 1 ]; }; then
  INTERACTIVE=1
fi

# 1. Engine (ComfyUI vs yue2.cpp)
# Choices are kept in memory during setup and only committed to $STATE/ once setup completes,
# so cancelling with Ctrl-C mid-prompt or mid-download never locks in an aborted choice.
SAVED_ENGINE=""
[ -f "$STATE/engine" ] && SAVED_ENGINE="$(cat "$STATE/engine")"
if [ -n "$ENGINE_CHOICE" ]; then
  case "$ENGINE_CHOICE" in
    comfyui|yue2cpp) ;;
    *) problem "--engine is comfyui or yue2cpp, not $ENGINE_CHOICE." ;;
  esac
elif [ -n "$SAVED_ENGINE" ] && [ "$RECONFIGURE" -eq 0 ]; then
  ENGINE_CHOICE="$SAVED_ENGINE"
elif [ "$INTERACTIVE" -eq 1 ]; then
  def_e=1
  [ "$SAVED_ENGINE" = yue2cpp ] && def_e=2
  say ""
  say "Music engine"
  say "  1) ComfyUI — full features including LoRA training (recommended for 12 GB+ VRAM)"
  if [ -n "$CPP_URL" ]; then
    say "  2) yue2.cpp — smaller native engine for less VRAM (no LoRA training)"
  else
    say "  2) yue2.cpp — smaller native engine (Linux pre-release not published yet; requires YEUFONIC_CPP_URL)"
  fi
  ask_choice ENGINE_CHOICE 'Choose engine (1 or 2)' comfyui yue2cpp "$def_e"
elif [ -n "$SAVED_ENGINE" ]; then
  ENGINE_CHOICE="$SAVED_ENGINE"
fi
CPP=0
if [ "$ENGINE_CHOICE" = yue2cpp ]; then CPP=1; else ENGINE_CHOICE=comfyui; fi
say "Engine: $ENGINE_CHOICE"

# 2. YuE2 model size (depends on chosen engine, as on Windows)
if [ "$CPP" -eq 0 ]; then
  SAVED_MODEL=""
  [ -f "$STATE/model" ] && SAVED_MODEL="$(cat "$STATE/model")"
  if [ -n "$INT8_CHOICE" ]; then
    :
  elif [ -n "$SAVED_MODEL" ] && [ "$RECONFIGURE" -eq 0 ]; then
    INT8_CHOICE="$SAVED_MODEL"
  elif [ "$INTERACTIVE" -eq 1 ]; then
    def_m=1
    if [ "$SAVED_MODEL" = int8 ]; then
      def_m=2
    elif [ -z "$SAVED_MODEL" ] && [ -n "$VRAM_GB" ] && awk -v g="$VRAM_GB" 'BEGIN { exit !(g + 0 < 11.5) }'; then
      def_m=2
    fi
    say ""
    say "YuE2 model size (ComfyUI)"
    say "  1) Full quality (BF16, 7.8 GB — recommended for 12 GB+ VRAM)"
    say "  2) Low memory (INT8, 4.0 GB — for 8-12 GB cards)"
    ask_choice INT8_CHOICE 'Choose YuE2 model (1 or 2)' bf16 int8 "$def_m"
  elif [ -n "$SAVED_MODEL" ]; then
    INT8_CHOICE="$SAVED_MODEL"
  fi
  MODEL_SIZE="${INT8_CHOICE:-bf16}"
  say "YuE2 model: $MODEL_SIZE"
else
  MODEL_SIZE=bf16
  SAVED_CPP_MODEL=""
  [ -f "$STATE/cpp-model" ] && SAVED_CPP_MODEL="$(cat "$STATE/cpp-model")"
  if [ -n "$CPP_MODEL" ]; then
    case "$CPP_MODEL" in
      q8|bf16) ;;
      *) problem "--cpp-model is q8 or bf16, not $CPP_MODEL." ;;
    esac
    CPP_MODEL_ASKED=1
  else
    CPP_MODEL_ASKED=0
    if [ -n "$SAVED_CPP_MODEL" ] && [ "$RECONFIGURE" -eq 0 ]; then
      CPP_MODEL="$SAVED_CPP_MODEL"
    elif [ "$INTERACTIVE" -eq 1 ]; then
      def_cm=1
      [ "$SAVED_CPP_MODEL" = bf16 ] && def_cm=2
      say ""
      say "YuE2 model size (yue2.cpp)"
      say "  1) Low memory (Q8, 3.8 GB — near lossless, default)"
      say "  2) Full quality (BF16, 7.2 GB — about twice the VRAM)"
      ask_choice CPP_MODEL 'Choose yue2.cpp model (1 or 2)' q8 bf16 "$def_cm"
      CPP_MODEL_ASKED=1
    elif [ -n "$SAVED_CPP_MODEL" ]; then
      CPP_MODEL="$SAVED_CPP_MODEL"
    fi
  fi
  [ "$CPP_MODEL" = bf16 ] || CPP_MODEL=q8
  say "yue2.cpp model: $CPP_MODEL"
  if [ -z "$CPP_URL" ]; then
    problem "The Linux yue2.cpp pre-release is not published yet (Phase 1). Use --engine comfyui for now, or set YEUFONIC_CPP_URL."
  fi
fi

# 3. Local lyric drafts (Gemma 4 — default Yes, matching Windows)
SAVED_LYRICS=""
[ -f "$STATE/lyrics" ] && SAVED_LYRICS="$(cat "$STATE/lyrics")"
if [ -n "$LYRICS_CHOICE" ]; then
  :
elif [ -n "$SAVED_LYRICS" ] && [ "$RECONFIGURE" -eq 0 ]; then
  LYRICS_CHOICE="$SAVED_LYRICS"
elif [ "$INTERACTIVE" -eq 1 ]; then
  gemma_sz="8.1 GB"
  [ "$CPP" -eq 1 ] && gemma_sz="6.1 GB via Ollama"
  def_ly="${SAVED_LYRICS:-yes}"
  say ""
  say "Local lyric drafts and song analysis (Gemma 4)"
  say "  Draft lyrics and analyse songs locally ($gemma_sz). Leave out if you use an external LLM API."
  ask_yes_no LYRICS_CHOICE 'Include local Gemma 4?' "$def_ly"
elif [ -n "$SAVED_LYRICS" ]; then
  LYRICS_CHOICE="$SAVED_LYRICS"
fi
if [ "$LYRICS_CHOICE" = no ]; then NO_LYRICS=1; LYRICS_CHOICE=no; else NO_LYRICS=0; LYRICS_CHOICE=yes; fi
say "Local lyric drafts (Gemma): $LYRICS_CHOICE"

# 4. Local take pictures (FLUX.2 klein 4B, or optional FIBO 2.0 on ComfyUI)
SAVED_PICTURES=""
[ -f "$STATE/pictures" ] && SAVED_PICTURES="$(cat "$STATE/pictures")"
if [ -n "$PICTURES" ]; then
  :
elif [ -n "$SAVED_PICTURES" ] && [ "$RECONFIGURE" -eq 0 ]; then
  PICTURES="$SAVED_PICTURES"
elif [ "$INTERACTIVE" -eq 1 ]; then
  def_pic="${SAVED_PICTURES:-yes}"
  say ""
  say "Take pictures drawn on this PC (optional)"
  say "  Draws a cover picture for each take locally (FLUX.2 klein 4B, FLUX 3 klein on yue2.cpp, or FIBO 2.0 on ComfyUI)."
  ask_yes_no PICTURES 'Set up local take pictures?' "$def_pic"
elif [ -n "$SAVED_PICTURES" ]; then
  PICTURES="$SAVED_PICTURES"
fi
[ "$PICTURES" = yes ] || PICTURES=no
say "Take pictures: $PICTURES"

# 4b. Local take-picture model: FLUX.2 klein 4B (default, Apache 2.0), FLUX 3 klein GGUF (yue2.cpp, FLUX Kommunity License) or FIBO 2.0 (ComfyUI, CC BY-NC 4.0)
SAVED_PIC_MODEL=""
[ -f "$STATE/picture-model" ] && SAVED_PIC_MODEL="$(cat "$STATE/picture-model")"
if [ "$PICTURES" = yes ]; then
  if [ -n "$PICTURE_MODEL" ]; then
    PICTURE_MODEL="$(echo "$PICTURE_MODEL" | tr '[:upper:]' '[:lower:]')"
    case "$PICTURE_MODEL" in
      4b|flux3|fibo2)
        if [ "$CPP" -eq 1 ] && [ "$PICTURE_MODEL" = fibo2 ]; then
          problem "FIBO 2.0 only runs on the ComfyUI engine (use --engine comfyui, or --picture-model 4b|flux3 for yue2.cpp)."
        fi
        if [ "$CPP" -eq 0 ] && [ "$PICTURE_MODEL" = flux3 ]; then
          problem "Automatic FLUX 3 klein GGUF download is for yue2.cpp (--engine yue2cpp --picture-model flux3); ComfyUI's FLUX 3 weights are gated on Hugging Face and added by hand (see the guide)."
        fi
        ;;
      *) problem "--picture-model is 4b, flux3 or fibo2, not $PICTURE_MODEL." ;;
    esac
  elif [ "$CPP" -eq 1 ]; then
    if [ "$SAVED_PIC_MODEL" = fibo2 ]; then
      say "  note: saved picture model 'fibo2' is ComfyUI-only; defaulting to FLUX.2 klein 4B on yue2.cpp."
      SAVED_PIC_MODEL=""
    fi
    if [ -n "$SAVED_PIC_MODEL" ] && [ "$RECONFIGURE" -eq 0 ]; then
      PICTURE_MODEL="$SAVED_PIC_MODEL"
    elif [ "$INTERACTIVE" -eq 1 ]; then
      def_pm=1
      [ "$SAVED_PIC_MODEL" = flux3 ] && def_pm=2
      say ""
      say "Local take-picture model (yue2.cpp)"
      say "  1) FLUX.2 klein 4B — 6.9 GB, Apache 2.0, fast, 8 GB+ VRAM (default)"
      say "  2) FLUX 3 klein    — ~9.0 GB (ungated GGUF + Qwen3-VL + VAE), better lettering, 12 GB+ VRAM (FLUX Kommunity License)"
      ask_choice PICTURE_MODEL 'Choose picture model (1 or 2)' 4b flux3 "$def_pm"
    elif [ -n "$SAVED_PIC_MODEL" ]; then
      PICTURE_MODEL="$SAVED_PIC_MODEL"
    else
      PICTURE_MODEL=4b
    fi
  else
    if [ "$SAVED_PIC_MODEL" = flux3 ]; then
      say "  note: saved picture model 'flux3' GGUF is yue2.cpp-only; defaulting to FLUX.2 klein 4B on ComfyUI."
      SAVED_PIC_MODEL=""
    fi
    if [ -n "$SAVED_PIC_MODEL" ] && [ "$RECONFIGURE" -eq 0 ]; then
      PICTURE_MODEL="$SAVED_PIC_MODEL"
    elif [ "$INTERACTIVE" -eq 1 ]; then
      def_pm=1
      [ "$SAVED_PIC_MODEL" = fibo2 ] && def_pm=2
      say ""
      say "Local take-picture model (ComfyUI)"
      say "  1) FLUX.2 klein 4B — 8.3 GB, Apache 2.0, fast, 8 GB+ VRAM (default)"
      say "  2) FIBO 2.0        — ~15 GB with turbo LoRA, photographic, 16 GB+ VRAM (CC BY-NC 4.0, non-commercial only)"
      ask_choice PICTURE_MODEL 'Choose picture model (1 or 2)' 4b fibo2 "$def_pm"
    elif [ -n "$SAVED_PIC_MODEL" ]; then
      PICTURE_MODEL="$SAVED_PIC_MODEL"
    else
      PICTURE_MODEL=4b
    fi
  fi
  say "Take-picture model: $PICTURE_MODEL"
else
  PICTURE_MODEL="${SAVED_PIC_MODEL:-4b}"
fi

# 5. Style LoRAs
SAVED_LORAS=""
[ -f "$STATE/loras" ] && SAVED_LORAS="$(cat "$STATE/loras")"
if [ -n "$LORAS" ]; then
  :
elif [ -n "$SAVED_LORAS" ] && [ "$RECONFIGURE" -eq 0 ]; then
  LORAS="$SAVED_LORAS"
elif [ "$INTERACTIVE" -eq 1 ]; then
  def_loras="${SAVED_LORAS:-yes}"
  say ""
  say "Style LoRAs (optional)"
  say "  39 style LoRAs by their authors (CC BY-NC 4.0, about 3.8 GB), each with a description."
  ask_yes_no LORAS 'Fetch the style LoRAs?' "$def_loras"
elif [ -n "$SAVED_LORAS" ]; then
  LORAS="$SAVED_LORAS"
fi
[ "$LORAS" = yes ] || LORAS=no
say "Style LoRAs: $LORAS"

# 6. Recorded voices
SAVED_VOICES=""
[ -f "$STATE/voices" ] && SAVED_VOICES="$(cat "$STATE/voices")"
if [ -n "$VOICES" ]; then
  :
elif [ -n "$SAVED_VOICES" ] && [ "$RECONFIGURE" -eq 0 ]; then
  VOICES="$SAVED_VOICES"
elif [ "$INTERACTIVE" -eq 1 ]; then
  def_voices="${SAVED_VOICES:-yes}"
  say ""
  say "Recorded voices (optional)"
  say "  Train an RVC voice from recordings of a singer (~1.1 GB models + ~3 GB Python packages)."
  ask_yes_no VOICES 'Set up recorded voices?' "$def_voices"
elif [ -n "$SAVED_VOICES" ]; then
  VOICES="$SAVED_VOICES"
fi
[ "$VOICES" = yes ] || VOICES=no
say "Recorded voices: $VOICES"

# 7. Starter Pack (demo songs): defaults to yes on a fresh install, no on an existing install.
EXISTING_INSTALL=0
if [ -f "$INSTALL_DIR/data/yue2.sqlite" ] || [ -f "$STATE/set-up-for" ]; then
  EXISTING_INSTALL=1
fi
SAVED_DEMOS=""
[ -f "$STATE/demos" ] && SAVED_DEMOS="$(cat "$STATE/demos")"
if [ -n "$DEMOS" ]; then
  :
elif [ "$EXISTING_INSTALL" -eq 1 ] && [ "$RECONFIGURE" -eq 0 ]; then
  DEMOS="no"
elif [ "$INTERACTIVE" -eq 1 ]; then
  def_demos="yes"
  [ "$EXISTING_INSTALL" -eq 1 ] && def_demos="no"
  say ""
  say "Starter Pack (optional demo songs)"
  say "  Curated takes in a 'Starter Pack' space with artwork, mastering settings, a cover recording, a voice and their style LoRAs (about 1.7 GB; skips any LoRA or voice already installed)."
  ask_yes_no DEMOS 'Include the Starter Pack demo songs?' "$def_demos"
else
  if [ "$EXISTING_INSTALL" -eq 1 ]; then DEMOS="no"; else DEMOS="yes"; fi
fi
[ "$DEMOS" = yes ] || DEMOS=no
say "Starter Pack: $DEMOS"

# Engine-dependent GPU compatibility checks (now that engine choice is known).
if [ -n "$COMPUTE_CAP" ]; then
  min_cap="8.0"
  [ "$CPP" -eq 1 ] && min_cap="7.5"
  if awk -v c="$COMPUTE_CAP" -v m="$min_cap" 'BEGIN { exit !(c + 0 < m + 0) }'; then
    if [ "$CPP" -eq 1 ]; then
      problem "$GPU_NAME (compute $COMPUTE_CAP) is too old for yue2.cpp (RTX 20-series / compute 7.5 or newer required)."
    else
      problem "$GPU_NAME (compute $COMPUTE_CAP) is too old for ComfyUI YuE2 (RTX 30-series / compute 8.0 or newer required)."
    fi
  fi
fi
if [ "$CPP" -eq 0 ] && [ -n "$VRAM_GB" ]; then
  if awk -v g="$VRAM_GB" 'BEGIN { exit !(g + 0 < 7.5) }'; then
    problem "$GPU_NAME has $VRAM_GB GB of VRAM; ComfyUI YuE2 needs 8 GB (12 GB+ recommended)."
  elif awk -v g="$VRAM_GB" 'BEGIN { exit !(g + 0 < 11.5) }'; then
    warning "$VRAM_GB GB of VRAM works (consider --int8), though local Gemma lyric drafts will be tight. 12 GB+ is recommended."
  fi
fi

# Base shared libraries that Python packages / ggml may load dynamically.
pkg_hint() {
  case "$DISTRO_ID $DISTRO_LIKE" in
    *ubuntu*|*debian*) echo "sudo apt install $1" ;;
    *rhel*|*fedora*|*rocky*|*almalinux*|*centos*) echo "sudo dnf install $2" ;;
    *arch*|*manjaro*) echo "sudo pacman -S $3" ;;
    *suse*) echo "sudo zypper install $4" ;;
    *) echo "install the equivalent package ($1 / $2)" ;;
  esac
}
if [ -n "$LDCACHE" ]; then
  if ! grep -q 'libgomp\.so\.1' <<< "$LDCACHE"; then
    warning "libgomp.so.1 is not installed ($(pkg_hint 'libgomp1' 'libgomp' 'gcc-libs' 'libgomp1'))."
  fi
  if [ "$CPP" -eq 0 ]; then
    if ! grep -q 'libGL\.so\.1' <<< "$LDCACHE" || ! grep -q 'libglib-2\.0\.so\.0' <<< "$LDCACHE"; then
      warning "libGL.so.1 or libglib-2.0.so.0 is missing; some ComfyUI image nodes may need it ($(pkg_hint 'libgl1 libglib2.0-0' 'mesa-libGL glib2' 'mesa glib2' 'Mesa-libGL1 libglib-2_0-0'))."
    fi
  fi
fi

if [ "$VOICES" = yes ] && [ -d /dev/shm ]; then
  SHM_MB="$(df -Pm /dev/shm 2>/dev/null | awk 'NR==2 {print $2}' || echo 0)"
  if [ "${SHM_MB:-0}" -gt 0 ] && [ "$SHM_MB" -lt 2048 ]; then
    warning "/dev/shm is only ${SHM_MB} MB; RVC voice training recommends at least 2048 MB of shared memory."
  fi
fi

# Disk space check (probe the nearest existing parent when --check-only hasn't created INSTALL_DIR yet).
PROBE_DIR="$INSTALL_DIR"
while [ ! -d "$PROBE_DIR" ] && [ "$PROBE_DIR" != "/" ]; do
  PROBE_DIR="$(dirname "$PROBE_DIR")"
done
NEED=12000000000   # engine venv, app venv, tools and unpacking room
if [ "$SKIP_MODELS" -eq 0 ]; then
  while IFS='|' read -r dir file size sha url lyrics copy; do
    [ -z "$file" ] && continue
    if [ "$lyrics" = lyrics ] && [ "$NO_LYRICS" -eq 1 ]; then continue; fi
    [ -f "$MODELS/$dir/$file" ] || NEED=$((NEED + size))
  done <<EOF
$(engine_models)
EOF
  if [ "$PICTURES" = yes ]; then
    while IFS='|' read -r dir file size sha url; do
      [ -z "$file" ] && continue
      [ -f "$MODELS/$dir/$file" ] || NEED=$((NEED + size))
    done <<EOF
$(selected_picture_models)
EOF
  fi
  if [ "$LORAS" = yes ]; then
    while IFS='|' read -r file size sha; do
      [ -z "$file" ] && continue
      [ -f "$MODELS/loras/$file" ] || NEED=$((NEED + size))
    done <<EOF
$(style_lora_list)
EOF
  fi
  if [ "$VOICES" = yes ]; then
    while IFS='|' read -r dir file size sha url copy; do
      [ -z "$file" ] && continue
      [ -f "$INSTALL_DIR/voice/models/$dir/$file" ] || NEED=$((NEED + size))
    done <<EOF
$(voice_list)
EOF
  fi
  NEED=$((NEED + 3300000000))   # app Whisper + engine Whisper + demucs
  if [ "$DEMOS" = yes ] && [ ! -f "$STATE/starter-pack.done" ]; then
    NEED=$((NEED + 1800000000))
  fi
  if [ "$CPP" -eq 1 ] && [ "$NO_LYRICS" -eq 0 ] && [ ! -d "$MODELS/ollama/manifests" ]; then
    NEED=$((NEED + 6200000000))
  fi
fi
if [ "$VOICES" = yes ] && [ ! -x "$INSTALL_DIR/voice/venv/bin/python" ]; then
  NEED=$((NEED + 3500000000))
fi
FREE_KB="$(df -Pk "$PROBE_DIR" | awk 'NR==2 {print $4}')"
FREE=$((FREE_KB * 1024))
NEED_GB=$(((NEED + 999999999) / 1000000000))
say "Free space at $PROBE_DIR: $((FREE / 1000000000)) GB (needed: about $NEED_GB GB)"
if [ "$FREE" -lt "$NEED" ]; then
  problem "Not enough free space: about $NEED_GB GB is needed."
fi

# Port check (respecting settings.ini if already present).
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
    warning "Port $port is already in use (Docker, or another copy of Yeufonic or ComfyUI?). Stop it or set app_port/engine_port in $INI before starting."
  fi
done

say "Checking network..."
for site in https://huggingface.co https://github.com https://pypi.org https://download.pytorch.org; do
  http_head "$site" || problem "Cannot reach $site. Check your internet connection, firewall, or proxy."
done

if [ -n "$warnings" ]; then while IFS= read -r w; do [ -n "$w" ] && say "  note: $w"; done <<< "$warnings"; fi
if [ -n "$problems" ]; then
  while IFS= read -r p; do [ -n "$p" ] && say "  problem: $p"; done <<< "$problems"
  stop_setup "this machine does not meet the requirements above"
fi
say "This machine is suitable."
if [ "$CHECK_ONLY" -eq 1 ]; then exit 0; fi

# ------------------------------------------------------------------- tools
step "Tools"
UV="$TOOLS/bin/uv"
if [ ! -x "$UV" ]; then
  get_verified "$UV_URL" "$DOWNLOADS/uv.tar.gz" "$UV_SIZE" "$UV_SHA"
  tar -xzf "$DOWNLOADS/uv.tar.gz" -C "$TOOLS/bin" --strip-components=1
fi
# uv keeps its Pythons and cache inside INSTALL_DIR, leaving ~/.local and system Python untouched.
# Large CUDA wheels (200-500 MB) from pypi.nvidia.com / download.pytorch.org can exceed uv's 30s default timeout.
export UV_PYTHON_INSTALL_DIR="$INSTALL_DIR/python"
export UV_CACHE_DIR="$DOWNLOADS/uv-cache"
export UV_HTTP_TIMEOUT="${UV_HTTP_TIMEOUT:-300}"
export UV_HTTP_RETRIES="${UV_HTTP_RETRIES:-5}"
export UV_CONCURRENT_DOWNLOADS="${UV_CONCURRENT_DOWNLOADS:-4}"
if ! is_done "python-$PYTHON"; then
  run_live "$UV" python install --no-bin "$PYTHON" || stop_setup "Python $PYTHON could not be installed"
  mark_done "python-$PYTHON"
fi
PY313="$("$UV" python find "$PYTHON")"

for tool in ffmpeg ffprobe; do
  if [ ! -x "$TOOLS/bin/$tool" ]; then
    if [ "$tool" = ffmpeg ]; then sha="$FFMPEG_SHA"; size="$FFMPEG_SIZE"; else sha="$FFPROBE_SHA"; size="$FFPROBE_SIZE"; fi
    get_verified "$FFMPEG_BASE/$tool.zip" "$DOWNLOADS/$tool.zip" "$size" "$sha"
    extract_zip "$DOWNLOADS/$tool.zip" "$TOOLS/bin"
    chmod +x "$TOOLS/bin/$tool"
    rm -f "$DOWNLOADS/$tool.zip" "$DOWNLOADS/$tool.zip.sha256ok"
  fi
done

# FluidSynth (for offline MIDI rendering): fetch our portable Linux build once published,
# otherwise fall back cleanly to any system fluidsynth on PATH.
if [ -n "$FLUIDSYNTH_URL" ]; then
  FS_NAME="$(basename "$FLUIDSYNTH_URL" .tar.gz)"
  if ! is_done "$FS_NAME" || [ ! -x "$TOOLS/bin/fluidsynth" ]; then
    get_verified "$FLUIDSYNTH_URL" "$DOWNLOADS/$FS_NAME.tar.gz" "$FLUIDSYNTH_SIZE" "$FLUIDSYNTH_SHA"
    rm -rf "$DOWNLOADS/unpack"
    mkdir -p "$DOWNLOADS/unpack" "$TOOLS/licenses"
    tar -xzf "$DOWNLOADS/$FS_NAME.tar.gz" -C "$DOWNLOADS/unpack"
    mv -f "$DOWNLOADS/unpack/$FS_NAME/fluidsynth" "$TOOLS/bin/fluidsynth"
    chmod +x "$TOOLS/bin/fluidsynth"
    rm -rf "$TOOLS/licenses/fluidsynth"
    mv "$DOWNLOADS/unpack/$FS_NAME" "$TOOLS/licenses/fluidsynth"
    rm -rf "$DOWNLOADS/unpack"
    mark_done "$FS_NAME"
  fi
elif ! command -v fluidsynth >/dev/null 2>&1; then
  say "note: fluidsynth is not installed yet (MIDI import playback needs it; static build arrives in Phase 1, or $(pkg_hint 'fluidsynth' 'fluidsynth' 'fluidsynth' 'fluidsynth'))."
fi

# ------------------------------------------------------------------- engine
CPP_DIR="$INSTALL_DIR/engine-cpp"
if [ "$CPP" -eq 1 ]; then
  step "The engine (yue2.cpp, on CUDA)"
  CPP_NAME="$(basename "$CPP_URL" .tar.gz)"
  if ! is_done "yue2cpp-$CPP_NAME" || [ ! -x "$CPP_DIR/yue2cpp/yue-server" ]; then
    get_verified "$CPP_URL" "$DOWNLOADS/$CPP_NAME.tar.gz" "$CPP_SIZE" "$CPP_SHA"
    rm -rf "$DOWNLOADS/unpack" "${CPP_DIR:?}/yue2cpp"
    mkdir -p "$DOWNLOADS/unpack" "$CPP_DIR"
    tar -xzf "$DOWNLOADS/$CPP_NAME.tar.gz" -C "$DOWNLOADS/unpack"
    mv "$DOWNLOADS/unpack/$CPP_NAME" "$CPP_DIR/yue2cpp"
    rm -rf "$DOWNLOADS/unpack"
    mark_done "yue2cpp-$CPP_NAME"
  fi
  if [ "$NO_LYRICS" -eq 0 ]; then
    OLLAMA_MARK="ollama-$(basename "$(dirname "$OLLAMA_URL")")"
    if ! is_done "$OLLAMA_MARK" || { [ ! -x "$CPP_DIR/ollama/bin/ollama" ] && [ ! -x "$CPP_DIR/ollama/ollama" ]; }; then
      say "Ollama, which runs Gemma beside the engine"
      get_verified "$OLLAMA_URL" "$DOWNLOADS/ollama-linux-amd64.tar.zst" "$OLLAMA_SIZE" "$OLLAMA_SHA"
      rm -rf "${CPP_DIR:?}/ollama"
      extract_zst "$DOWNLOADS/ollama-linux-amd64.tar.zst" "$CPP_DIR/ollama"
      rm -f "$DOWNLOADS/ollama-linux-amd64.tar.zst" "$DOWNLOADS/ollama-linux-amd64.tar.zst.sha256ok"
      mark_done "$OLLAMA_MARK"
    fi
  fi
  for sub in yue2cpp loras text_encoders diffusion_models vae ollama; do mkdir -p "$MODELS/$sub"; done
else
  step "The engine (ComfyUI, on CUDA $VARIANT)"
  ENGINE_MARK="engine-$VARIANT-${COMFY_COMMIT:0:8}"
  if ! is_done "$ENGINE_MARK" || [ ! -f "$COMFY/main.py" ] || [ ! -x "$ENGINE_VENV/bin/python" ]; then
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
    say "Installing PyTorch ($VARIANT) and ComfyUI's packages"
    ENGINE_TORCH="$ENGINE_TORCH_CU130"
    [ "$VARIANT" = cu128 ] && ENGINE_TORCH="$ENGINE_TORCH_CU128"
    # shellcheck disable=SC2086
    run_live "$UV" pip install --python "$ENGINE_VENV/bin/python" $ENGINE_TORCH \
      --index-url "https://download.pytorch.org/whl/$VARIANT" || stop_setup "the engine's PyTorch ($VARIANT) failed"
    run_live "$UV" pip install --python "$ENGINE_VENV/bin/python" -r "$COMFY/requirements.txt" || stop_setup "the engine's packages failed"
    mark_done "$ENGINE_MARK"
  fi
  EPY="$ENGINE_VENV/bin/python"

  NODES="$COMFY/custom_nodes"
  mkdir -p "$NODES"
  if ! is_done "yue2_trainer-${TRAINER_COMMIT:0:8}" || [ ! -d "$NODES/ComfyUI-YuE2-Trainer" ]; then
    get_commit yeufonic/ComfyUI-YuE2-Trainer "$TRAINER_COMMIT" "$NODES/ComfyUI-YuE2-Trainer"
    run_live "$UV" pip install --python "$EPY" "soundfile>=0.12" "librosa>=0.10" scipy mutagen einops || stop_setup "the trainer's packages failed"
    mark_done "yue2_trainer-${TRAINER_COMMIT:0:8}"
  fi
  if ! is_done engine-demucs || ! "$EPY" -c "import demucs" >/dev/null 2>&1; then
    run_live "$UV" pip install --python "$EPY" demucs==4.1.0 || stop_setup "demucs for the engine failed"
    mark_done engine-demucs
  fi
  # GPU Whisper (faster-whisper + CTranslate2). On cu130, CTranslate2's CUDA 12 cuBLAS/cuDNN
  # go into $CUDA12_DIR so they never collide with PyTorch's CUDA 13 cuDNN; launcher.py passes CUDA12_LIBS.
  if ! is_done "engine-whisper-$VARIANT" || ! "$EPY" -c "import faster_whisper, ctranslate2" >/dev/null 2>&1; then
    run_live "$UV" pip install --python "$EPY" --no-deps faster-whisper==1.2.1 || stop_setup "faster-whisper for the engine failed"
    run_live "$UV" pip install --python "$EPY" "ctranslate2>=4.5,<5" tokenizers || stop_setup "ctranslate2 for the engine failed"
    if [ "$VARIANT" = cu130 ]; then
      rm -rf "$CUDA12_DIR"
      mkdir -p "$CUDA12_DIR"
      # shellcheck disable=SC2086
      run_live "$UV" pip install --python "$EPY" --target "$CUDA12_DIR" $CUDA12_WHISPER_PKGS || stop_setup "CUDA 12 libraries for GPU Whisper failed"
    fi
    mark_done "engine-whisper-$VARIANT"
  fi
  # Our own node and startup driver guard, copied from studio/.
  rm -rf "$NODES/yue2_harmony"
  cp -R "$NODE_SRC" "$NODES/yue2_harmony"
  rm -rf "$NODES/yue2_harmony/__pycache__"
  [ -f "$START_SRC" ] && cp -f "$START_SRC" "$ENGINE/start.py"
  for sub in checkpoints audio_encoders text_encoders loras fs_audio whisper demucs; do
    mkdir -p "$MODELS/$sub"
  done
fi

# Restore any models kept by an earlier uninstall.
KEPT="$INSTALL_DIR/models-kept"
if [ -d "$KEPT" ]; then
  say "Putting back models kept by an earlier uninstall"
  cp -an "$KEPT/." "$MODELS/" 2>/dev/null || cp -rn "$KEPT/." "$MODELS/" 2>/dev/null || true
  rm -rf "$KEPT"
fi

# ---------------------------------------------------------------------- app
step "The app"
REQS="$STUDIO/requirements.txt"
APP_MARK="app-$(sha_of "$REQS" | cut -c1-12)"
if ! is_done "$APP_MARK" || [ ! -x "$APP_VENV/bin/python" ]; then
  if [ ! -x "$APP_VENV/bin/python" ]; then
    "$UV" venv --python "$PYTHON" "$APP_VENV" || stop_setup "the app's Python could not be set up"
  fi
  run_live "$UV" pip install --python "$APP_VENV/bin/python" -r "$REQS" || stop_setup "the app's packages failed"
  # CPU build of torch for stems (identical to Dockerfile): the GPU belongs to YuE2.
  # shellcheck disable=SC2086
  run_live "$UV" pip install --python "$APP_VENV/bin/python" $APP_TORCH \
    --index-url https://download.pytorch.org/whl/cpu || stop_setup "CPU torch for stems failed"
  run_live "$UV" pip install --python "$APP_VENV/bin/python" demucs==4.1.0 || stop_setup "demucs for the app failed"
  mark_done "$APP_MARK"
fi

DATA="$INSTALL_DIR/data"
v="$(ini_value data_dir)"; if [ -n "$v" ]; then DATA="${v/#\~/$HOME}"; fi
mkdir -p "$DATA"

# ------------------------------------------------------------------- models
if [ "$SKIP_MODELS" -eq 0 ]; then
  step "The models (the long part)"
  # Count total and remaining bytes up front so the user sees overall progress and what is skipped.
  m_total=0; m_have=0; m_bytes=0
  while IFS='|' read -r dir file size sha url lyrics copy; do
    [ -z "$file" ] && continue
    if [ "$lyrics" = lyrics ] && [ "$NO_LYRICS" -eq 1 ]; then continue; fi
    m_total=$((m_total + 1))
    if [ "$FORCE_DOWNLOADS" -eq 0 ] && [ -f "$MODELS/$dir/$file" ]; then
      m_have=$((m_have + 1))
    else
      m_bytes=$((m_bytes + size))
    fi
  done <<EOF
$(engine_models)
EOF
  if [ "$FORCE_DOWNLOADS" -eq 1 ]; then
    say "Core models: forcing re-download of all $m_total files ($(fmt_bytes "$m_bytes"))"
  elif [ "$m_have" -eq "$m_total" ]; then
    say "Core models: all $m_total files already present (checking any unverified)"
  else
    say "Core models: $m_have already present, $((m_total - m_have)) to download ($(fmt_bytes "$m_bytes"))"
  fi
  m_idx=0
  while IFS='|' read -r dir file size sha url lyrics copy; do
    [ -z "$file" ] && continue
    if [ "$lyrics" = lyrics ] && [ "$NO_LYRICS" -eq 1 ]; then continue; fi
    m_idx=$((m_idx + 1))
    mkdir -p "$MODELS/$dir"
    get_verified "$url" "$MODELS/$dir/$file" "$size" "$sha" "$copy" "[$m_idx/$m_total]"
  done <<EOF
$(engine_models)
EOF

  if [ "$PICTURES" = yes ]; then
    p_total=0; p_idx=0
    while IFS='|' read -r dir file size sha url; do
      [ -z "$file" ] && continue
      p_total=$((p_total + 1))
    done <<EOF
$(selected_picture_models)
EOF
    say ""
    say "Take pictures — $PICTURE_MODEL ($p_total files):"
    while IFS='|' read -r dir file size sha url; do
      [ -z "$file" ] && continue
      p_idx=$((p_idx + 1))
      mkdir -p "$MODELS/$dir"
      get_verified "$url" "$MODELS/$dir/$file" "$size" "$sha" "" "[$p_idx/$p_total]"
    done <<EOF
$(selected_picture_models)
EOF
  fi

  if [ "$LORAS" = yes ]; then
    l_total=0; l_have=0; l_bytes=0
    while IFS='|' read -r file size sha; do
      [ -z "$file" ] && continue
      l_total=$((l_total + 1))
      if [ "$FORCE_DOWNLOADS" -eq 0 ] && [ -f "$MODELS/loras/$file" ]; then
        l_have=$((l_have + 1))
      else
        l_bytes=$((l_bytes + size))
      fi
    done <<EOF
$(style_lora_list)
EOF
    say ""
    if [ "$FORCE_DOWNLOADS" -eq 0 ] && [ "$l_have" -eq "$l_total" ]; then
      say "Style LoRAs: all $l_total files already present, skipping"
    else
      say "Style LoRAs: $l_have already present, $((l_total - l_have)) to download ($(fmt_bytes "$l_bytes"))"
      l_idx=0
      mkdir -p "$MODELS/loras"
      while IFS='|' read -r file size sha; do
        [ -z "$file" ] && continue
        l_idx=$((l_idx + 1))
        if [ "$FORCE_DOWNLOADS" -eq 0 ] && [ -f "$MODELS/loras/$file" ]; then
          continue
        fi
        get_verified "https://huggingface.co/pshields/yue2-style-loras/resolve/main/$file" "$MODELS/loras/$file" "$size" "$sha" "" "[$l_idx/$l_total]" 1
      done <<EOF
$(style_lora_list)
EOF
    fi
  fi
  if [ "$CPP" -eq 0 ] && [ ! -f "$MODELS/fs_audio/tokenizer_head_joint_v9.safetensors" ]; then
    cp "$MODELS/audio_encoders/tokenizer_head_joint_v9.safetensors" "$MODELS/fs_audio/"
  fi
fi

# ------------------------------------------------------ the app's own models
if [ "$SKIP_MODELS" -eq 0 ] && { [ "$FORCE_DOWNLOADS" -eq 1 ] || ! is_done app-models; }; then
  step "The app's own models (lyric timing and stems)"
  export TORCH_HOME="$DATA/models/torch"
  export HF_HOME="$DATA/models/whisper"
  say "Whisper large-v3-turbo (about 1.6 GB)"
  run_live "$APP_VENV/bin/python" -c "import sys; from faster_whisper import download_model; download_model('large-v3-turbo', cache_dir=sys.argv[1])" \
    "$DATA/models/whisper" || stop_setup "Whisper could not be fetched"
  say "demucs htdemucs (about 80 MB)"
  run_live "$APP_VENV/bin/python" -c "from demucs.pretrained import get_model; get_model('htdemucs')" || stop_setup "demucs model could not be fetched"
  mark_done app-models
fi
if [ "$CPP" -eq 0 ] && [ "$SKIP_MODELS" -eq 0 ] && { [ "$FORCE_DOWNLOADS" -eq 1 ] || ! is_done engine-demucs-model; }; then
  say "demucs htdemucs for the engine (about 80 MB)"
  if run_live "$EPY" -s -c "import sys, torch; torch.hub.set_dir(sys.argv[1]); from huggingface_hub import constants; constants.HF_HUB_CACHE = sys.argv[1] + '/hub'; from demucs.pretrained import get_model; get_model('htdemucs')" \
      "$MODELS/demucs"; then
    mark_done engine-demucs-model
  else
    say "Could not fetch it now; the engine will when it first separates a vocal."
  fi
fi
if [ "$CPP" -eq 0 ] && [ "$SKIP_MODELS" -eq 0 ] && { [ "$FORCE_DOWNLOADS" -eq 1 ] || ! is_done engine-whisper-model; }; then
  step "Whisper for the engine (about 1.6 GB)"
  mkdir -p "$MODELS/whisper/large-v3-turbo"
  w_idx=0
  while IFS='|' read -r file size sha url; do
    [ -z "$file" ] && continue
    w_idx=$((w_idx + 1))
    get_verified "$url" "$MODELS/whisper/large-v3-turbo/$file" "$size" "$sha" "" "[$w_idx/5]"
  done <<EOF
$(whisper_engine_list)
EOF
  mark_done engine-whisper-model
fi

# Gemma for yue2.cpp via Ollama.
GEMMA_MARK="gemma-$(echo "$GEMMA_MODEL" | tr ':' '-')"
if [ "$CPP" -eq 1 ] && [ "$NO_LYRICS" -eq 0 ] && [ "$SKIP_MODELS" -eq 0 ] && { [ "$FORCE_DOWNLOADS" -eq 1 ] || ! is_done "$GEMMA_MARK"; }; then
  step "Gemma for lyric drafts (about 6.1 GB, through Ollama)"
  OLLAMA_BIN="$CPP_DIR/ollama/bin/ollama"
  [ -x "$OLLAMA_BIN" ] || OLLAMA_BIN="$CPP_DIR/ollama/ollama"
  OLLAMA_MODELS="$MODELS/ollama" OLLAMA_HOST=127.0.0.1:11439 "$OLLAMA_BIN" serve > "$LOGS/setup-ollama.log" 2>&1 &
  OLLAMA_PID=$!
  up=0
  for _ in $(seq 1 30); do
    if http_head http://127.0.0.1:11439/api/tags; then up=1; break; fi
    sleep 1
  done
  pulled=0
  if [ "$up" -eq 1 ] && OLLAMA_HOST=127.0.0.1:11439 run_live "$OLLAMA_BIN" pull "$GEMMA_MODEL"; then pulled=1; fi
  kill "$OLLAMA_PID" 2>/dev/null || true
  wait "$OLLAMA_PID" 2>/dev/null || true
  [ "$up" -eq 1 ] || stop_setup "Ollama did not start, so Gemma could not be fetched"
  [ "$pulled" -eq 1 ] || stop_setup "Gemma could not be fetched"
  mark_done "$GEMMA_MARK"
fi

# ---------------------------------------------------------------- soundfonts
if [ "$SKIP_MODELS" -eq 0 ]; then
  step "SoundFonts for MIDI playback"
  mkdir -p "$DATA/models/soundfonts/sf2"
  sf_idx=0
  while IFS='|' read -r file size sha url; do
    [ -z "$file" ] && continue
    sf_idx=$((sf_idx + 1))
    get_verified "$url" "$DATA/models/soundfonts/sf2/$file" "$size" "$sha" "" "[$sf_idx/2]"
  done <<EOF
$(soundfont_list)
EOF
fi

# ----------------------------------------------------------- recorded voices
if [ "$VOICES" = yes ]; then
  step "Recorded voices (the voice service)"
  VOICE_DIR="$INSTALL_DIR/voice"
  RVC_DIR="$VOICE_DIR/rvc"
  VOICE_MODELS="$VOICE_DIR/models"
  VOICE_VENV="$VOICE_DIR/venv"
  mkdir -p "$VOICE_MODELS/assets" "$VOICE_MODELS/logs"
  RVC_MARK="rvc-${RVC_COMMIT:0:12}"
  if ! is_done "$RVC_MARK" || [ ! -d "$RVC_DIR/infer" ]; then
    for link in assets logs; do
      [ -L "$RVC_DIR/$link" ] && unlink "$RVC_DIR/$link"
    done
    get_commit yeufonic/Retrieval-based-Voice-Conversion-WebUI "$RVC_COMMIT" "$RVC_DIR" RVC-Project/Retrieval-based-Voice-Conversion-WebUI
    mark_done "$RVC_MARK"
  fi
  for link in assets logs; do
    if [ ! -L "$RVC_DIR/$link" ]; then
      rm -rf "${RVC_DIR:?}/${link:?}"
      ln -s "$VOICE_MODELS/$link" "$RVC_DIR/$link"
    fi
  done
  VOICE_CUDA=cu126
  [ "$DRIVER_MAJOR" -ge 570 ] && VOICE_CUDA=cu128
  VOICE_MARK="voice-env-$VOICE_CUDA-$(sha_of "$STUDIO/voice/requirements.txt" | cut -c1-12)"
  if ! is_done "$VOICE_MARK" || [ ! -x "$VOICE_VENV/bin/python" ]; then
    if ! is_done "python-$VOICE_PYTHON"; then
      run_live "$UV" python install --no-bin "$VOICE_PYTHON" || stop_setup "Python $VOICE_PYTHON could not be installed"
      mark_done "python-$VOICE_PYTHON"
    fi
    if [ ! -x "$VOICE_VENV/bin/python" ]; then
      "$UV" venv --python "$VOICE_PYTHON" "$VOICE_VENV" || stop_setup "the voice service's Python could not be set up"
    fi
    # shellcheck disable=SC2086
    run_live "$UV" pip install --python "$VOICE_VENV/bin/python" $VOICE_TORCH \
      --index-url "https://download.pytorch.org/whl/$VOICE_CUDA" || stop_setup "PyTorch for the voice service failed"
    run_live "$UV" pip install --python "$VOICE_VENV/bin/python" -r "$STUDIO/voice/requirements.txt" || stop_setup "the voice service's packages failed"
    mark_done "$VOICE_MARK"
  fi
  if [ "$SKIP_MODELS" -eq 0 ]; then
    v_idx=0
    while IFS='|' read -r dir file size sha url copy; do
      [ -z "$file" ] && continue
      v_idx=$((v_idx + 1))
      mkdir -p "$VOICE_MODELS/$dir"
      get_verified "$url" "$VOICE_MODELS/$dir/$file" "$size" "$sha" "$copy" "[$v_idx/9]"
    done <<EOF
$(voice_list)
EOF
    mkdir -p "$VOICE_MODELS/assets/weights" "$VOICE_MODELS/assets/indices"
    if [ ! -d "$VOICE_MODELS/logs/mute/0_gt_wavs" ] || [ "$FORCE_DOWNLOADS" -eq 1 ]; then
      extract_zip "$VOICE_MODELS/mute.zip" "$VOICE_MODELS/logs"
    fi
  fi
fi

# -------------------------------------------------------------- starter pack
if [ "$DEMOS" = yes ] && [ "$SKIP_MODELS" -eq 0 ]; then
  step "Starter Pack (curated demo takes)"
  STARTER_URL="${STARTER_PACK_URL:-https://media.yeufonic.com/starter-pack}"
  STARTER_URL="${STARTER_URL%/}"
  if [ -n "${STARTER_PACK_URL:-}" ]; then
    STARTER_FALLBACK=""
  else
    STARTER_FALLBACK="$HF/pshields/yeufonic-starter-pack/resolve/main"
  fi
  SP_MANIFEST="$DOWNLOADS/starter-pack-manifest.json"
  if ! curl -fsSL --retry 3 --connect-timeout 15 -o "$SP_MANIFEST" "$STARTER_URL/manifest.json"; then
    if [ -n "$STARTER_FALLBACK" ] && curl -fsSL --retry 3 --connect-timeout 15 -o "$SP_MANIFEST" "$STARTER_FALLBACK/manifest.json"; then
      say "  could not reach $STARTER_URL; using fallback mirror on Hugging Face"
      STARTER_URL="$STARTER_FALLBACK"
      STARTER_FALLBACK=""
    else
      stop_setup "could not download Starter Pack manifest from $STARTER_URL/manifest.json"
    fi
  fi
  sp_fetch() {
    local rel="${1#/}" dest="$2" size="$3" sha="$4" keep="${5:-0}"
    if [ -n "$STARTER_FALLBACK" ]; then
      get_verified "$STARTER_FALLBACK/$rel" "$dest" "$size" "$sha" "$STARTER_URL/$rel" "" "$keep"
      if [ "${LAST_USED_FALLBACK:-0}" -eq 1 ]; then
        STARTER_URL="$STARTER_FALLBACK"
        STARTER_FALLBACK=""
      fi
    else
      get_verified "$STARTER_URL/$rel" "$dest" "$size" "$sha" "" "" "$keep"
    fi
  }
  mkdir -p "$MODELS/loras"
  while IFS='|' read -r sp_file sp_path sp_size sp_sha; do
    [ -z "$sp_file" ] && continue
    sp_fetch "$sp_path" "$MODELS/loras/$sp_file" "$sp_size" "$sp_sha" 1
  done <<EOF
$("$APP_VENV/bin/python" - "$SP_MANIFEST" <<'PY'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
if m.get("format") != "yeufonic-starter-pack-manifest":
    raise SystemExit(1)
for item in m.get("loras") or []:
    print(f"{item['file']}|{item['path']}|{item['bytes']}|{item['sha256']}")
PY
)
EOF

  SP_PLAN="$("$APP_VENV/bin/python" - "$SP_MANIFEST" "$DATA" <<'PY'
import json, sqlite3, sys
from pathlib import Path
m = json.load(open(sys.argv[1], encoding="utf-8"))
data_dir = Path(sys.argv[2])
pack_id = str(m.get("pack_id") or "")
space_name = str(m.get("space_name") or "Starter Pack")
db_path = data_dir / "yue2.sqlite"
have_ids, have_names = set(), set()
vdir = data_dir / "voices"
if vdir.is_dir():
    for d in vdir.iterdir():
        if d.is_dir() and (d / "model.pth").is_file():
            have_ids.add(d.name)
installed = False
if db_path.is_file():
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "voices" in tables:
            for vid, name in con.execute("SELECT id, name FROM voices"):
                if vid: have_ids.add(str(vid))
                if name: have_names.add(str(name).strip().lower())
        if {"settings", "spaces", "takes"}.issubset(tables) and pack_id:
            row = con.execute("SELECT value FROM settings WHERE key = 'starter_pack.installed'").fetchone()
            if row and row[0] and json.loads(row[0]).get("pack_id") == pack_id:
                sp = con.execute("SELECT id FROM spaces WHERE LOWER(name) = LOWER(?)", (space_name,)).fetchone()
                if sp and con.execute("SELECT COUNT(*) FROM takes WHERE space_id = ?", (sp[0],)).fetchone()[0] > 0:
                    installed = True
    finally:
        con.close()
if installed:
    print(f"SKIP|{pack_id}")
else:
    for v in m.get("voices") or []:
        vid, vname = str(v.get("id") or ""), str(v.get("name") or "")
        if vid in have_ids or (vname and vname.lower() in have_names):
            continue
        for f in v.get("files") or []:
            print(f"VOICE|{vid}|{f['dest']}|{f['path']}|{f['bytes']}|{f['sha256']}")
    for b in m.get("bundles") or ([m["bundle"]] if m.get("bundle") else []):
        print(f"BUNDLE|{b['path']}|{b['bytes']}|{b['sha256']}")
PY
)"
  SP_STAGE="$DATA/starter-pack"
  SP_SKIPPED=0
  while IFS='|' read -r kind a b c d e; do
    case "$kind" in
      SKIP)
        say "Starter Pack ($a) is already installed."
        SP_SKIPPED=1 ;;
      VOICE)
        mkdir -p "$SP_STAGE/voices/$a"
        sp_fetch "$c" "$SP_STAGE/voices/$a/$b" "$d" "$e" ;;
      BUNDLE)
        mkdir -p "$SP_STAGE"
        bname="$(basename "$a")"
        sp_fetch "$a" "$SP_STAGE/$bname" "$b" "$c"
        "$APP_VENV/bin/python" - "$SP_STAGE/$bname" "$SP_STAGE" <<'PY'
import shutil, sys, zipfile
from pathlib import Path
zp, dest = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
with zipfile.ZipFile(zp, "r") as zf:
    for m in zf.infolist():
        if m.is_dir(): continue
        target = (dest / m.filename).resolve()
        target.relative_to(dest)
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(m, "r") as src, target.open("wb") as out:
            shutil.copyfileobj(src, out)
PY
        rm -f "$SP_STAGE/$bname" "$SP_STAGE/$bname.sha256ok" ;;
    esac
  done <<EOF
$SP_PLAN
EOF
  if [ "$SP_SKIPPED" -eq 0 ]; then
    say "Starter Pack staged — it will appear in the 'Starter Pack' space when Yeufonic starts."
  fi
  mark_done "starter-pack"
fi

# -------------------------------------------------------------------- done
ini_set() {
  local key="$1" value="$2"
  if [ ! -f "$INI" ]; then
    printf '[yue2]\n%s = %s\n' "$key" "$value" > "$INI"
    return 0
  fi
  awk -v k="$key" -v v="$value" '
    BEGIN { done = 0; inside = 0; seen = 0 }
    /^[[:space:]]*\[/ {
      if (inside && !done) { print k " = " v; done = 1 }
      inside = ($0 ~ /^[[:space:]]*\[yue2\]/); if (inside) seen = 1
      print; next
    }
    inside && $0 ~ ("^[[:space:]]*" k "[[:space:]]*=") { if (!done) { print k " = " v; done = 1 }; next }
    { print }
    END { if (!done) { if (!seen) print "[yue2]"; print k " = " v } }' "$INI" > "$INI.tmp" && mv "$INI.tmp" "$INI"
}

ini_set engine "$ENGINE_CHOICE"
if [ "$CPP" -eq 1 ]; then
  ini_set gemma_model "$GEMMA_MODEL"
  named="$(ini_value yue2cpp_model)"
  case "$named" in
    ''|YuE2-3B-Q8_0.gguf|YuE2-3B-BF16.gguf) own=0 ;;
    *) own=1 ;;
  esac
  if [ "$own" -eq 0 ] || [ "$CPP_MODEL_ASKED" -eq 1 ]; then
    if [ "$CPP_MODEL" = bf16 ]; then ini_set yue2cpp_model YuE2-3B-BF16.gguf; else ini_set yue2cpp_model YuE2-3B-Q8_0.gguf; fi
  fi
else
  ini_set model "$MODEL_SIZE"
fi

# Commit chosen component settings only after setup has finished cleanly so cancelling with
# Ctrl-C mid-prompt or mid-download never locks in an aborted choice.
echo "$ENGINE_CHOICE" > "$STATE/engine"
if [ "$CPP" -eq 1 ]; then
  echo "$CPP_MODEL" > "$STATE/cpp-model"
else
  echo "$MODEL_SIZE" > "$STATE/model"
fi
echo "$LYRICS_CHOICE" > "$STATE/lyrics"
echo "$PICTURES" > "$STATE/pictures"
echo "$PICTURE_MODEL" > "$STATE/picture-model"
echo "$LORAS" > "$STATE/loras"
echo "$VOICES" > "$STATE/voices"
echo "$DEMOS" > "$STATE/demos"

# Activate the chosen local picture model in the app's Settings database when it already exists
# (on a brand-new install, the app picks the installed picture model automatically on first start).
if [ "$PICTURES" = yes ] && [ "$SKIP_MODELS" -eq 0 ] && [ -f "$DATA/yue2.sqlite" ] && [ -x "$APP_VENV/bin/python" ]; then
  "$APP_VENV/bin/python" - "$DATA/yue2.sqlite" "$PICTURE_MODEL" <<'PY' 2>/dev/null || true
import sqlite3, sys
db_path, val = sys.argv[1], sys.argv[2]
con = sqlite3.connect(db_path, timeout=5)
try:
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
    if cur.fetchone():
        con.execute(
            "INSERT INTO settings(key, value) VALUES('art.klein', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (val,),
        )
        con.commit()
finally:
    con.close()
PY
fi

cat "$STUDIO/VERSION" "$STUDIO/BUILD" 2>/dev/null > "$STATE/set-up-for" || true
rm -rf "$UV_CACHE_DIR"
step "Finished"
if [ "$PICTURES" = yes ]; then
  say "Yeufonic is set up in $INSTALL_DIR (engine: $ENGINE_CHOICE, picture model: $PICTURE_MODEL)."
else
  say "Yeufonic is set up in $INSTALL_DIR (engine: $ENGINE_CHOICE)."
fi
if port_taken "$APP_PORT"; then
  say "Note: something is currently running on port $APP_PORT. Restart Yeufonic ($INSTALL_DIR/bin/yeufonic stop && $INSTALL_DIR/bin/yeufonic) for any engine or model changes to take effect."
else
  say "Start it with: $INSTALL_DIR/bin/yeufonic"
fi
exit 0
