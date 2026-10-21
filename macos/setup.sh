#!/bin/bash
# Yeufonic for macOS: checks this Mac, then sets up Python, ComfyUI (with Metal/MPS),
# and the models.
#
# Usage:
#   bash setup.sh [--install-dir <path>] [--skip-models] [--no-lyrics] [--int8] [--check-only]
#
# Options:
#   --install-dir <path>  Target directory (default: ~/Library/Application Support/Yeufonic)
#   --skip-models         Set up environment only, skipping model downloads (for testing / CI)
#   --no-lyrics           Skip Gemma 4 download (saves 8 GB; recommended for 16 GB Macs with External LLM)
#   --int8                Download low-memory int8 model instead of bf16
#   --check-only          Run pre-flight hardware and OS checks only
set -euo pipefail

DEFAULT_DIR="$HOME/Library/Application Support/Yeufonic"
INSTALL_DIR="${DEFAULT_DIR}"
SKIP_MODELS=0
NO_LYRICS=0
INT8=0
CHECK_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    --skip-models)
      SKIP_MODELS=1
      shift
      ;;
    --no-lyrics)
      NO_LYRICS=1
      shift
      ;;
    --int8)
      INT8=1
      shift
      ;;
    --check-only)
      CHECK_ONLY=1
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Yeufonic Setup for macOS (Apple Silicon) ==="
echo "Target: ${INSTALL_DIR}"

# 1. Pre-flight Hardware & Architecture Checks
echo ""
echo "== Checking System Hardware"

ARCH=$(uname -m)
if [ "${ARCH}" != "arm64" ]; then
  echo "Error: Yeufonic on macOS requires an Apple Silicon Mac (M1, M2, M3, M4 or later)." >&2
  echo "Current architecture: ${ARCH}. Intel Macs lack Metal Performance Shaders (MPS) support." >&2
  exit 1
fi
echo "  Architecture: Apple Silicon (arm64) [OK]"

if command -v sysctl >/dev/null 2>&1; then
  TOTAL_MEM_BYTES=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
  TOTAL_MEM_GB=$((TOTAL_MEM_BYTES / 1024 / 1024 / 1024))
  echo "  Unified Memory: ${TOTAL_MEM_GB} GB"

  if [ "${TOTAL_MEM_GB}" -lt 12 ]; then
    echo "  Warning: 8 GB Macs have insufficient unified memory to run YuE2 locally without severe paging." >&2
    echo "  A Mac with at least 16 GB of unified memory is strongly recommended." >&2
  elif [ "${TOTAL_MEM_GB}" -lt 20 ]; then
    echo "  Notice: On 16 GB Macs, enable 'External LLM' in Settings to avoid loading local Gemma concurrently."
  fi
fi

if [ "${CHECK_ONLY}" -eq 1 ]; then
  echo ""
  echo "Hardware checks passed successfully."
  exit 0
fi

# Directory structure
DOWNLOADS_DIR="${INSTALL_DIR}/downloads"
TOOLS_DIR="${INSTALL_DIR}/tools"
ENGINE_DIR="${INSTALL_DIR}/engine"
COMFY_DIR="${ENGINE_DIR}/ComfyUI"
MODELS_DIR="${COMFY_DIR}/models"
STATE_DIR="${INSTALL_DIR}/state"
LOGS_DIR="${INSTALL_DIR}/logs"
VENV_DIR="${INSTALL_DIR}/venv"

mkdir -p "${INSTALL_DIR}" "${DOWNLOADS_DIR}" "${TOOLS_DIR}" "${ENGINE_DIR}" "${MODELS_DIR}" "${STATE_DIR}" "${LOGS_DIR}"

is_done() {
  [ -f "${STATE_DIR}/$1.done" ]
}

mark_done() {
  date -u +"%Y-%m-%dT%H:%M:%SZ" > "${STATE_DIR}/$1.done"
}

get_verified() {
  local name="$1"
  local url="$2"
  local dest="$3"
  local expected_sha="$4"

  if [ -f "${dest}" ] && [ -f "${dest}.sha256ok" ]; then
    return 0
  fi

  echo "Downloading ${name}..."
  local part="${dest}.part"
  curl -L --fail --retry 5 -C - -# -o "${part}" "${url}"
  mv -f "${part}" "${dest}"

  if [ -n "${expected_sha}" ]; then
    echo "  Verifying checksum for ${name}..."
    local actual_sha
    actual_sha=$(shasum -a 256 "${dest}" | awk '{print $1}')
    if [ "${actual_sha}" != "${expected_sha}" ]; then
      rm -f "${dest}"
      echo "Error: Checksum mismatch for ${name}. Download removed." >&2
      exit 1
    fi
  fi
  touch "${dest}.sha256ok"
}

# 2. Tools & Python Runtime Provisioning
echo ""
echo "== Setting up Python Runtime"

UV_BIN="${TOOLS_DIR}/uv"
if [ ! -x "${UV_BIN}" ]; then
  echo "Fetching uv package manager for macOS arm64..."
  UV_URL="https://github.com/astral-sh/uv/releases/download/0.12.18/uv-aarch64-apple-darwin.tar.gz"
  curl -sSL "${UV_URL}" | tar -xz -C "${TOOLS_DIR}" --strip-components=1
  chmod +x "${TOOLS_DIR}/uv"
fi

if ! is_done "python-runtime" || [ ! -x "${VENV_DIR}/bin/python" ]; then
  echo "Provisioning standalone Python 3.12..."
  "${UV_BIN}" python install --no-bin 3.12
  "${UV_BIN}" venv --python 3.12 "${VENV_DIR}"

  echo "Installing PyTorch with Apple Silicon Metal (MPS) support..."
  "${UV_BIN}" pip install --python "${VENV_DIR}/bin/python" \
    torch torchvision torchaudio

  echo "Installing application requirements..."
  "${UV_BIN}" pip install --python "${VENV_DIR}/bin/python" \
    -r "${ROOT_DIR}/requirements.txt"

  echo "Installing demucs and faster-whisper..."
  "${UV_BIN}" pip install --python "${VENV_DIR}/bin/python" \
    demucs==4.1.0 faster-whisper==1.2.1

  mark_done "python-runtime"
fi

# 3. ComfyUI Engine Setup
echo ""
echo "== Setting up Engine (ComfyUI with Metal/MPS)"

COMFY_COMMIT="36da3ff763687eab86a35e1019995dd1fb369b0d"
YUE2_TRAINER_COMMIT="6a9355efff60589d93b41b569676f09d5db85d09"

if ! is_done "engine-${COMFY_COMMIT:0:8}" || [ ! -d "${COMFY_DIR}" ]; then
  echo "Fetching ComfyUI at commit ${COMFY_COMMIT:0:8}..."
  mkdir -p "${COMFY_DIR}"
  curl -sSL "https://codeload.github.com/comfyanonymous/ComfyUI/zip/${COMFY_COMMIT}" | tar -xz -C "${ENGINE_DIR}"
  rm -rf "${COMFY_DIR}"
  mv "${ENGINE_DIR}/ComfyUI-${COMFY_COMMIT}" "${COMFY_DIR}"

  echo "Installing ComfyUI dependencies..."
  "${UV_BIN}" pip install --python "${VENV_DIR}/bin/python" \
    -r "${COMFY_DIR}/requirements.txt"

  mark_done "engine-${COMFY_COMMIT:0:8}"
fi

# Custom Nodes: yue2_harmony
NODES_DIR="${COMFY_DIR}/custom_nodes"
mkdir -p "${NODES_DIR}"
rm -rf "${NODES_DIR}/yue2_harmony"
cp -r "${ROOT_DIR}/engine/custom_nodes/yue2_harmony" "${NODES_DIR}/yue2_harmony"

# Custom Nodes: ComfyUI-YuE2-Trainer
if ! is_done "yue2-trainer-${YUE2_TRAINER_COMMIT:0:8}" || [ ! -d "${NODES_DIR}/ComfyUI-YuE2-Trainer" ]; then
  echo "Fetching YuE2 Trainer custom node..."
  mkdir -p "${NODES_DIR}/ComfyUI-YuE2-Trainer"
  curl -sSL "https://codeload.github.com/speedyrulz/ComfyUI-YuE2-Trainer/zip/${YUE2_TRAINER_COMMIT}" | tar -xz -C "${NODES_DIR}"
  rm -rf "${NODES_DIR}/ComfyUI-YuE2-Trainer"
  mv "${NODES_DIR}/ComfyUI-YuE2-Trainer-${YUE2_TRAINER_COMMIT}" "${NODES_DIR}/ComfyUI-YuE2-Trainer"

  "${UV_BIN}" pip install --python "${VENV_DIR}/bin/python" \
    soundfile librosa scipy mutagen einops

  mark_done "yue2-trainer-${YUE2_TRAINER_COMMIT:0:8}"
fi

# 4. Models Download
if [ "${SKIP_MODELS}" -eq 1 ]; then
  echo ""
  echo "Skipping model downloads (--skip-models specified)."
  echo "Setup completed successfully."
  exit 0
fi

echo ""
echo "== Downloading Core Models"

HF="https://huggingface.co"
mkdir -p "${MODELS_DIR}/checkpoints" "${MODELS_DIR}/audio_encoders" "${MODELS_DIR}/text_encoders" "${MODELS_DIR}/loras" "${MODELS_DIR}/fs_audio"

# YuE2 Checkpoint
if [ "${INT8}" -eq 1 ]; then
  echo "Using INT8 low-memory model..."
  get_verified "YuE2 (int8)" \
    "${HF}/Comfy-Org/YuE2/resolve/main/checkpoints/yue2_3b_int8_convrot.safetensors" \
    "${MODELS_DIR}/checkpoints/yue2_3b_int8_convrot.safetensors" \
    ""
else
  get_verified "YuE2 (bf16)" \
    "${HF}/Comfy-Org/YuE2/resolve/main/checkpoints/yue2_3b_bf16.safetensors" \
    "${MODELS_DIR}/checkpoints/yue2_3b_bf16.safetensors" \
    "33765adbf9813c9a50318218760b2fd819a319862460a04884607581961c6fee"
fi

# SheetSage2 Audio Encoder
get_verified "SheetSage2" \
  "${HF}/Comfy-Org/YuE2/resolve/main/audio_encoders/sheetsage2_bf16.safetensors" \
  "${MODELS_DIR}/audio_encoders/sheetsage2_bf16.safetensors" \
  "5fd960ce3df281e3f3a889d174584d88f96247711480cf96377b12d7e8b6adc5"

# LoRAs
get_verified "Instrumental LoRA" \
  "${HF}/Mothersuperior/YuE2-instrumental-cot-full-loras/resolve/main/ar_lora_inst_v3abc_comfyui.safetensors" \
  "${MODELS_DIR}/loras/ar_lora_inst_v3abc_comfyui.safetensors" \
  "de6a11d5701df103a191c87dc73115266e2420f3834739319dec5c24d2119f31"

get_verified "Production Polish LoRA" \
  "${HF}/Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/resolve/main/nar_lora_joint_v9_comfyui.safetensors" \
  "${MODELS_DIR}/loras/nar_lora_joint_v9_comfyui.safetensors" \
  "cd2bf0d3ce4bf68697daa016671da7d70e34e2f5545617ab9094c96b14a581db"

get_verified "Realaudio Tokenizer Head" \
  "${HF}/Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/resolve/main/tokenizer_head_joint_v9.safetensors" \
  "${MODELS_DIR}/audio_encoders/tokenizer_head_joint_v9.safetensors" \
  "06440f25605c6c12c4e517ef033d7b70b8d9e961b3b06aa3848b1f8028fd7eb8"

# Gemma 4 (optional lyric model)
if [ "${NO_LYRICS}" -eq 0 ]; then
  get_verified "Gemma 4" \
    "${HF}/Comfy-Org/gemma-4/resolve/main/text_encoders/gemma4_e4b_it_int8_convrot.safetensors" \
    "${MODELS_DIR}/text_encoders/gemma4_e4b_it_int8_convrot.safetensors" \
    "974d0c838ef4ac1a989b06ccb4e57691c21b6270dd8e345ffa7531f9388f117c"
fi

# SoundFonts
SOUNDFONTS_DIR="${INSTALL_DIR}/data/soundfonts"
mkdir -p "${SOUNDFONTS_DIR}"

get_verified "Jnsgm2 SoundFont" \
  "https://raw.githubusercontent.com/wrightflyer/SF2_SoundFonts/master/Jnsgm2.sf2" \
  "${SOUNDFONTS_DIR}/Jnsgm2.sf2" \
  "dc48cb5c322cab23fce1b18442066be30ccc49a184603c7a3bf7615003ee137d"

echo ""
echo "=== Yeufonic macOS Setup Complete ==="
echo "You can now start Yeufonic with: python3 macos/launcher.py"
