#!/bin/bash
# Yeufonic for macOS: checks this Mac, then fetches and sets up everything the app does
# not carry.  Every part comes from its own publisher, pinned to a version and checked by
# sha256 where the publisher gives one.  Safe to run again: whatever is already in place is
# kept, and an interrupted download carries on.  The macOS counterpart of windows/setup.ps1,
# and it keeps that script's order, so the two can be read side by side.
#
#   bash setup.sh [--install-dir <folder>] [--engine comfyui|yue2cpp] [--no-lyrics] [--pictures | --no-pictures]
#                 [--loras | --no-loras] [--voices | --no-voices] [--check-only] [--skip-models] [--then-open <app>]
#   ... --install-dir   where it goes (default: ~/Library/Application Support/Yeufonic)
#   ... --engine        comfyui (everything, the default) or yue2cpp (yue2.cpp's server: faster lyric drafts and
#                       pictures on a Mac, with Gemma in Ollama and pictures in stable-diffusion.cpp beside it,
#                       and no training).  Kept for every later run; the other engine's files are left in place.
#   ... --no-lyrics     leave out Gemma 4 (8.1 GB), for an external LLM in Settings instead
#   ... --pictures      FLUX.2 [klein], which draws each take's picture on this Mac (about 16 GB);
#                       --no-pictures fetches none.  Without either, the first run asks and the
#                       answer is kept for every later run.
#   ... --loras         39 style LoRAs by their authors (CC BY-NC 4.0, about 3.8 GB); --no-loras none.
#                       Asked and kept as --pictures is.
#   ... --voices        recorded voices: the voice service (RVC and a BS-Roformer separator) in a Python of its
#                       own, about 1.1 GB of models and 1.5 GB of packages; --no-voices none.  Asked and kept
#                       as --pictures is.
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
PICTURES=""
LORAS=""
VOICES=""
ENGINE_CHOICE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --install-dir) INSTALL_DIR="$2"; shift 2 ;;
    --engine) ENGINE_CHOICE="$2"; shift 2 ;;
    --no-lyrics) NO_LYRICS=1; shift ;;
    --pictures) PICTURES=yes; shift ;;
    --no-pictures) PICTURES=no; shift ;;
    --loras) LORAS=yes; shift ;;
    --no-loras) LORAS=no; shift ;;
    --voices) VOICES=yes; shift ;;
    --no-voices) VOICES=no; shift ;;
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
COMFY_COMMIT=bb878b9ee35274e67931634ba9e8c338f8c06035
TRAINER_COMMIT=6a9355efff60589d93b41b569676f09d5db85d09
PYTHON=3.13
# The engine's torch: the version the Windows engine runs.  The macOS wheels carry Metal
# (MPS) and want macOS 14, which is also where bf16 on the GPU starts.
ENGINE_TORCH="torch==2.13.0 torchvision==0.28.0 torchaudio==2.11.0"
# The app's own torch, for stems on the CPU: the version the app container and the Windows
# app run.
APP_TORCH="torch==2.9.1 torchaudio==2.9.1"
# Recorded voices: RVC, MIT, driven by its scripts' argument positions, so pinned as voice/Dockerfile and
# windows/setup.ps1 pin it, in a Python of its own (it pins an older transformers, numpy and librosa than the
# engine's) with the torch the Windows voice service runs.  The macOS wheels carry Metal.
RVC_COMMIT=81eed5e8f68b6bed1789f682fe78cdd324495afc
VOICE_PYTHON=3.12
VOICE_TORCH="torch==2.7.1 torchaudio==2.7.1"
# The yue2.cpp engine (--engine yue2cpp): yue2.cpp's server and stable-diffusion.cpp's, built for macOS 14 by
# macos/build-cpp.sh and published as a pre-release by .github/workflows/engine-cpp-macos.yml; Ollama, which runs Gemma
# beside it, from its own release, the version windows/setup.ps1 pins.
CPP_URL=https://github.com/yeufonic/yeufonic/releases/download/yue2cpp-macos-8af0174-86a8de0e-p1/yue2cpp-macos-8af0174-86a8de0e-p1.tar.gz
CPP_SHA=4478032b265982475897eb2023fa9553fc45ce63302ad582e0684377a2478333
CPP_SIZE=19762625
# A build not yet published can be tried by naming it, a file:// address among them (a test of this script).
CPP_URL="${YEUFONIC_CPP_URL:-$CPP_URL}"
CPP_SHA="${YEUFONIC_CPP_SHA:-$CPP_SHA}"
CPP_SIZE="${YEUFONIC_CPP_SIZE:-$CPP_SIZE}"
OLLAMA_URL=https://github.com/ollama/ollama/releases/download/v0.40.13/ollama-darwin.tgz
OLLAMA_SHA=bae29252232b9e1358cf5801a7d65a07442af18fb5467cb68c7fc3711f59c511
OLLAMA_SIZE=186689993
GEMMA_MODEL=gemma4:e4b-it-qat   # Gemma 4 E4B for Ollama, about 6.1 GB
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
# FluidSynth, which plays an imported MIDI file: no macOS build of its own, so ours, made by macos/build-fluidsynth.sh
# and published by .github/workflows/fluidsynth-macos.yml (one program that needs nothing but macOS).
FLUIDSYNTH_URL=https://github.com/yeufonic/yeufonic/releases/download/fluidsynth-macos-2.6.2-sndfile-1.2.2-p1/fluidsynth-macos-2.6.2-sndfile-1.2.2-p1.tar.gz
FLUIDSYNTH_SHA=bb862c35de5d24e6c073e13aa7e4db53c7f7d4f39159f0f56b6905eefbfef466
FLUIDSYNTH_SIZE=443876

HF=https://huggingface.co
COPIES=$HF/pshields/yue2-mothersuperior-copies/resolve/main
# dir|file|bytes|sha256|url|lyrics|copy: the models windows/setup.ps1 fetches, with the same
# checksums and, for Mothersuperior's files (one author's account), our unchanged copy, tried first
# (tests/test_macos.py holds the two lists together).  Left out on a Mac: the
# low-memory YuE2, whose int8 kernels are CUDA's, and FLUX.2 [klein]'s FP8 and FP4 files (below).
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
# dir|file|bytes|sha256|url: FLUX.2 [klein] 4B, its text encoder and its VAE (Apache 2.0), only when
# chosen.  Windows and Docker fetch the model in FP8 and the encoder in FP4, which a Mac's GPU does
# not have, so a Mac takes the full-precision pair, about twice the size; the VAE is the same file.
# The app draws with whichever pair the engine lists.  Left out, a take's picture is drawn by the
# external LLM's image model, if it has one, or not at all.
picture_list() {
  cat <<LIST
diffusion_models|flux-2-klein-4b.safetensors|7751105712|ec3d4e733a771f61c052fb4856c48b336c55eaf2c65487c2a1faeb9bbda7a343|$HF/Comfy-Org/Flux-2-Klein-4B/resolve/main/split_files/diffusion_models/flux-2-klein-4b.safetensors
text_encoders|qwen_3_4b.safetensors|8044982048|6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a|$HF/Comfy-Org/Flux-2-Klein-4B/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors
vae|flux2-vae.safetensors|336211292|868fe7b343cc8f3a19dbcfcafbc3d5f888802be3f89bd81b65b3621a066ce8f3|$HF/Comfy-Org/Flux-2-Klein-4B/resolve/main/split_files/vae/flux2-vae.safetensors
LIST
}
# dir|file|bytes|sha256|url||copy: yue2.cpp's own files, as windows/setup.ps1 fetches them (tests/test_macos.py holds
# the lists together), our unchanged copies first.  With it the engine takes none of ComfyUI's files but the LoRAs.
GGUF=$HF/Serveurperso/YuE2-GGUF/resolve/e630f2b8f6aedf8254c3186438633c1b5eeaf80a
GGUF_COPIES=$HF/pshields/yue2-gguf-copies/resolve/main
cpp_model_list() {
  cat <<LIST
yue2cpp|YuE2-3B-Q8_0.gguf|3810232064|41121ce97786d7795a325bcf123ca196956c03bb252c9e75384cfc1f2fc19e6b|$GGUF/YuE2-3B-Q8_0.gguf||$GGUF_COPIES/YuE2-3B-Q8_0.gguf
yue2cpp|YuE2-Vae-F32.gguf|530497344|93e49dfb1970e89ad64cacb17cf13b5d05f6bb30ef7ed3adae3050bcb728638a|$GGUF/YuE2-Vae-F32.gguf||$GGUF_COPIES/YuE2-Vae-F32.gguf
yue2cpp|SheetSage2-Q8_0.gguf|105629856|95d8fa8761753b4833782a52b68d5c0afa3bd3cfbc03d3dcbbf8ded0c13f611e|$GGUF/SheetSage2-Q8_0.gguf||$GGUF_COPIES/SheetSage2-Q8_0.gguf
yue2cpp|MERT-v2-FullSong-Q8_0.gguf|902283712|35a6032ec7e8123c02becdefc7bfe10a3adb33faa8a1951dc0af864b4494b8ef|$GGUF/MERT-v2-FullSong-Q8_0.gguf||$GGUF_COPIES/MERT-v2-FullSong-Q8_0.gguf
LIST
}
# Its picture server reads klein's model and VAE as ComfyUI does, but not ComfyUI's text encoder: Qwen 3 4B as GGUF,
# which is also a third of the size.
cpp_picture_encoder() {
  echo "text_encoders|Qwen3-4B-Q4_K_M.gguf|2497281312|f6f851777709861056efcdad3af01da38b31223a3ba26e61a4f8bf3a2195813a|$HF/unsloth/Qwen3-4B-GGUF/resolve/22c9fc8a8c7700b76a1789366280a6a5a1ad1120/Qwen3-4B-Q4_K_M.gguf"
}
# The model files the chosen engine reads, in model_list's and picture_list's forms.
engine_models() {
  if [ "$CPP" -eq 1 ]; then
    cpp_model_list
    model_list | grep '^loras|'
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
# file|bytes|sha256: style LoRAs by their authors (CC BY-NC 4.0), gathered unchanged in pshields/yue2-style-loras,
# with a description each: only when chosen.  The same list as scripts/fetch-models.sh --loras and the Windows
# installer's Style LoRAs option (tests/test_macos.py holds them together).  A file already here is left alone.
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
# dir|file|bytes|sha256|url|copy: what the voice service reads, as windows/setup.ps1 and scripts/fetch-models.sh --voice
# fetch it (tests/test_macos.py holds the lists together), with an unchanged copy of each, tried first: a pre-release
# of Yeufonic's own (the originals are single accounts).  Only when chosen.
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

# A file from its publisher, or first from our copy of it where there is one.  curl resumes a
# broken download; a refusal (404 and the like, curl's 22) moves on at once, and a part left by
# one source is not resumed from another.  The sha256 is checked once and remembered, so a
# second run does not read 8 GB again.
get_verified() {
  local url="$1" dest="$2" size="$3" sha="$4" copy="${5:-}"
  if [ -f "$dest" ] && [ -f "$dest.sha256ok" ]; then return 0; fi
  if [ ! -f "$dest" ]; then
    say "Downloading $(basename "$dest") ($((size / 1000000)) MB)"
    local try source tries=6 got=0 code
    [ -n "$copy" ] && tries=3
    for source in $copy $url; do
      for try in $(seq 1 "$tries"); do
        code=0
        curl -L --fail --retry 5 -C - -# -o "$dest.part" "$source" || code=$?
        if [ "$code" -eq 0 ]; then got=1; break; fi
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
  local repo="$1" commit="$2" dest="$3" also="${4:-}"
  local archive source got=0
  archive="$DOWNLOADS/$(echo "$repo" | tr / _)-${commit:0:8}.tar.gz"
  if [ ! -f "$archive" ]; then
    # A second repository, where given, holds the same commit: tried when the first cannot be had.
    for source in $repo $also; do
      say "Downloading $source at ${commit:0:8}"
      if curl -L --fail --retry 5 -# -o "$archive.part" "https://codeload.github.com/$source/tar.gz/$commit"; then
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

# Take pictures drawn on this Mac: an option, asked once (in the Terminal window setup runs in)
# and kept in state/, so an update does not ask again.  --pictures or --no-pictures changes it.
# Answering no fetches nothing and leaves any files already here, as the Windows installer does.
ask_pictures() {
  say ""
  say "Take pictures drawn on this Mac (optional)"
  say "  FLUX.2 [klein] can draw a picture for each take on this Mac, with no external service."
  say "  - About 16 GB more to download. A Mac needs the model's full-size files: the smaller"
  say "    ones that Windows uses need an NVIDIA graphics card."
  say "  - Slow on a Mac: a picture can take minutes, where an NVIDIA card takes seconds."
  say "    It waits until no song is being made."
  say "  - It needs a lot of memory while it draws: 24 GB at the least, 32 GB or more recommended."
  if [ "$MEM_GB" -lt 24 ]; then
    say "    This Mac has $MEM_GB GB: not recommended, as the whole Mac would slow down while it draws."
  fi
  say "  - Experimental on a Mac."
  say "  Without it, a take's picture comes from the external LLM's image model, if it has one."
  say "  To change this later, quit Yeufonic and run in Terminal:"
  say "    bash $(printf '%q' "$HERE/setup.sh") --pictures    (or --no-pictures)"
  printf 'Draw take pictures on this Mac? [y/N] '
  local answer=""
  read -r answer || answer=""
  case "$answer" in [yY]*) PICTURES=yes ;; *) PICTURES=no ;; esac
}
if [ -n "$PICTURES" ]; then
  [ "$CHECK_ONLY" -eq 1 ] || echo "$PICTURES" > "$STATE/pictures"
elif [ -f "$STATE/pictures" ]; then
  PICTURES="$(cat "$STATE/pictures")"
elif [ -z "$problems" ] && [ "$CHECK_ONLY" -eq 0 ] && [ "$SKIP_MODELS" -eq 0 ] && [ -t 0 ]; then
  ask_pictures
  echo "$PICTURES" > "$STATE/pictures"
fi
# Not asked (no terminal, or only a check): none, and nothing kept, so the next run in a window asks.
[ "$PICTURES" = yes ] || PICTURES=no
say "Take pictures on this Mac: $PICTURES"

ask_loras() {
  say ""
  say "Style LoRAs (optional)"
  say "  39 style LoRAs by their authors, each with a description giving its trigger word, about 3.8 GB."
  say "  Free for non-commercial use (CC BY-NC 4.0). More can be added later from Hugging Face."
  say "  To change this later, quit Yeufonic and run in Terminal:"
  say "    bash $(printf '%q' "$HERE/setup.sh") --loras"
  printf 'Fetch the style LoRAs? [y/N] '
  local answer=""
  read -r answer || answer=""
  case "$answer" in [yY]*) LORAS=yes ;; *) LORAS=no ;; esac
}
if [ -n "$LORAS" ]; then
  [ "$CHECK_ONLY" -eq 1 ] || echo "$LORAS" > "$STATE/loras"
elif [ -f "$STATE/loras" ]; then
  LORAS="$(cat "$STATE/loras")"
elif [ -z "$problems" ] && [ "$CHECK_ONLY" -eq 0 ] && [ "$SKIP_MODELS" -eq 0 ] && [ -t 0 ]; then
  ask_loras
  echo "$LORAS" > "$STATE/loras"
fi
[ "$LORAS" = yes ] || LORAS=no
say "Style LoRAs: $LORAS"

ask_voices() {
  say ""
  say "Recorded voices (optional)"
  say "  Train a voice from recordings of a singer, and have a take sung again in it."
  say "  About 1.1 GB of models and 1.5 GB of packages. A voice trains in some minutes on this Mac."
  say "  To change this later, quit Yeufonic and run in Terminal:"
  say "    bash $(printf '%q' "$HERE/setup.sh") --voices"
  printf 'Set up recorded voices? [y/N] '
  local answer=""
  read -r answer || answer=""
  case "$answer" in [yY]*) VOICES=yes ;; *) VOICES=no ;; esac
}
if [ -n "$VOICES" ]; then
  [ "$CHECK_ONLY" -eq 1 ] || echo "$VOICES" > "$STATE/voices"
elif [ -f "$STATE/voices" ]; then
  VOICES="$(cat "$STATE/voices")"
elif [ -z "$problems" ] && [ "$CHECK_ONLY" -eq 0 ] && [ "$SKIP_MODELS" -eq 0 ] && [ -t 0 ]; then
  ask_voices
  echo "$VOICES" > "$STATE/voices"
fi
[ "$VOICES" = yes ] || VOICES=no
say "Recorded voices: $VOICES"

# The engine: ComfyUI unless yue2.cpp was chosen, now or before.
if [ -n "$ENGINE_CHOICE" ]; then
  case "$ENGINE_CHOICE" in
    comfyui|yue2cpp) [ "$CHECK_ONLY" -eq 1 ] || echo "$ENGINE_CHOICE" > "$STATE/engine" ;;
    *) problem "--engine is comfyui or yue2cpp, not $ENGINE_CHOICE." ;;
  esac
elif [ -f "$STATE/engine" ]; then
  ENGINE_CHOICE="$(cat "$STATE/engine")"
fi
CPP=0
if [ "$ENGINE_CHOICE" = yue2cpp ]; then CPP=1; else ENGINE_CHOICE=comfyui; fi
say "Engine: $ENGINE_CHOICE"
if [ "$CPP" -eq 1 ] && [ -z "$CPP_URL" ]; then
  problem "The yue2.cpp engine for macOS is not published yet: run setup.sh --engine comfyui."
fi

# Room for what is still to come: the missing models, plus about 8 GB for the engine, the
# app and the downloads while they unpack.  Counted in thousands, as download sites count.
NEED=8000000000
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
$(picture_models)
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
  NEED=$((NEED + 1700000000))   # Whisper and demucs, for the app
  # Gemma, which Ollama fetches for yue2.cpp.
  if [ "$CPP" -eq 1 ] && [ "$NO_LYRICS" -eq 0 ] && [ ! -d "$MODELS/ollama/manifests" ]; then NEED=$((NEED + 6200000000)); fi
fi
# The voice service's own Python and packages.
if [ "$VOICES" = yes ] && [ ! -x "$INSTALL_DIR/voice/venv/bin/python" ]; then NEED=$((NEED + 1500000000)); fi
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
# FluidSynth, for hearing an imported MIDI file, into the tools folder, which the launcher puts on the app's PATH ahead
# of Homebrew's.
FLUIDSYNTH_NAME="$(basename "$FLUIDSYNTH_URL" .tar.gz)"
if ! is_done "$FLUIDSYNTH_NAME" || [ ! -x "$TOOLS/bin/fluidsynth" ]; then
  get_verified "$FLUIDSYNTH_URL" "$DOWNLOADS/$FLUIDSYNTH_NAME.tar.gz" "$FLUIDSYNTH_SIZE" "$FLUIDSYNTH_SHA"
  rm -rf "$DOWNLOADS/unpack"
  mkdir -p "$DOWNLOADS/unpack" "$TOOLS/licenses"
  tar -xzf "$DOWNLOADS/$FLUIDSYNTH_NAME.tar.gz" -C "$DOWNLOADS/unpack"
  mv -f "$DOWNLOADS/unpack/$FLUIDSYNTH_NAME/fluidsynth" "$TOOLS/bin/fluidsynth"
  rm -rf "$TOOLS/licenses/fluidsynth"
  mv "$DOWNLOADS/unpack/$FLUIDSYNTH_NAME" "$TOOLS/licenses/fluidsynth"
  rm -rf "$DOWNLOADS/unpack"
  mark_done "$FLUIDSYNTH_NAME"
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
CPP_DIR="$INSTALL_DIR/engine-cpp"
if [ "$CPP" -eq 1 ]; then
  step "The engine (yue2.cpp, on the GPU through Metal)"
  # yue2.cpp's server and the picture server, then Ollama, each replaced when its pin changes and the models left alone.
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
  OLLAMA_MARK="ollama-$(basename "$(dirname "$OLLAMA_URL")")"
  if ! is_done "$OLLAMA_MARK" || [ ! -x "$CPP_DIR/ollama/ollama" ]; then
    say "Ollama, which runs Gemma beside the engine"
    get_verified "$OLLAMA_URL" "$DOWNLOADS/ollama-darwin.tgz" "$OLLAMA_SIZE" "$OLLAMA_SHA"
    rm -rf "${CPP_DIR:?}/ollama"
    mkdir -p "$CPP_DIR/ollama"
    tar -xzf "$DOWNLOADS/ollama-darwin.tgz" -C "$CPP_DIR/ollama"
    mark_done "$OLLAMA_MARK"
  fi
  for sub in yue2cpp loras text_encoders diffusion_models vae ollama; do mkdir -p "$MODELS/$sub"; done
else
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
fi

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
  mark_done "$APP_MARK"
fi

# The data folder, which settings.ini may move.
DATA="$INSTALL_DIR/data"
v="$(ini_value data_dir)"; if [ -n "$v" ]; then DATA="$v"; fi
mkdir -p "$DATA"

# ------------------------------------------------------------------- models
if [ "$SKIP_MODELS" -eq 0 ]; then
  step "The models (the long part)"
  while IFS='|' read -r dir file size sha url lyrics copy; do
    [ -z "$file" ] && continue
    if [ "$lyrics" = lyrics ] && [ "$NO_LYRICS" -eq 1 ]; then continue; fi
    say ""
    say "$file"
    mkdir -p "$MODELS/$dir"
    get_verified "$url" "$MODELS/$dir/$file" "$size" "$sha" "$copy"
  done <<EOF
$(engine_models)
EOF
  if [ "$PICTURES" = yes ]; then
    while IFS='|' read -r dir file size sha url; do
      [ -z "$file" ] && continue
      say ""
      say "$file (take pictures)"
      mkdir -p "$MODELS/$dir"
      get_verified "$url" "$MODELS/$dir/$file" "$size" "$sha"
    done <<EOF
$(picture_models)
EOF
  fi
  if [ "$LORAS" = yes ]; then
    while IFS='|' read -r file size sha; do
      [ -z "$file" ] && continue
      # One already here is kept as it is: it may be your own copy, or a description you have written over.
      [ -f "$MODELS/loras/$file" ] && continue
      say ""
      say "$file (style LoRAs)"
      mkdir -p "$MODELS/loras"
      get_verified "https://huggingface.co/pshields/yue2-style-loras/resolve/main/$file" "$MODELS/loras/$file" "$size" "$sha"
    done <<EOF
$(style_lora_list)
EOF
  fi
  # The trainer lists its tokenizer head from fs_audio as well.
  if [ "$CPP" -eq 0 ] && [ ! -f "$MODELS/fs_audio/tokenizer_head_joint_v9.safetensors" ]; then
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
if [ "$CPP" -eq 0 ] && [ "$SKIP_MODELS" -eq 0 ] && ! is_done engine-demucs-model; then
  say "demucs htdemucs for the engine (about 80 MB)"
  if "$EPY" -s -c "import sys, torch; torch.hub.set_dir(sys.argv[1]); from huggingface_hub import constants; constants.HF_HUB_CACHE = sys.argv[1] + '/hub'; from demucs.pretrained import get_model; get_model('htdemucs')" \
      "$MODELS/demucs"; then
    mark_done engine-demucs-model
  else
    say "Could not fetch it now; the engine will when it first separates a vocal."
  fi
fi

# Gemma for the yue2.cpp engine, fetched by Ollama itself into the models folder (Ollama checks what it fetches), on a
# port of its own so a running copy of Yeufonic is not disturbed.
GEMMA_MARK="gemma-$(echo "$GEMMA_MODEL" | tr ':' '-')"
if [ "$CPP" -eq 1 ] && [ "$NO_LYRICS" -eq 0 ] && [ "$SKIP_MODELS" -eq 0 ] && ! is_done "$GEMMA_MARK"; then
  step "Gemma for lyric drafts (about 6.1 GB, through Ollama)"
  OLLAMA_BIN="$CPP_DIR/ollama/ollama"
  OLLAMA_MODELS="$MODELS/ollama" OLLAMA_HOST=127.0.0.1:11439 "$OLLAMA_BIN" serve > "$LOGS/setup-ollama.log" 2>&1 &
  OLLAMA_PID=$!
  up=0
  for _ in $(seq 1 30); do
    if curl -s -o /dev/null --max-time 2 http://127.0.0.1:11439/api/tags; then up=1; break; fi
    sleep 1
  done
  pulled=0
  if [ "$up" -eq 1 ] && OLLAMA_HOST=127.0.0.1:11439 "$OLLAMA_BIN" pull "$GEMMA_MODEL"; then pulled=1; fi
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
  while IFS='|' read -r file size sha url; do
    [ -z "$file" ] && continue
    get_verified "$url" "$DATA/models/soundfonts/sf2/$file" "$size" "$sha"
  done <<EOF
$(soundfont_list)
EOF
fi

# ----------------------------------------------------------- recorded voices
# The voice service runs in a Python of its own, with RVC beside it, RVC's assets and logs folders linked into
# voice/models (so a new RVC commit leaves them in place), and voice/rvc-mps.patch applied, which lets RVC train and
# sing on Apple's GPU when the service asks it to.  The service itself comes with the app; the launcher starts it.
if [ "$VOICES" = yes ]; then
  step "Recorded voices (the voice service)"
  VOICE_DIR="$INSTALL_DIR/voice"
  RVC_DIR="$VOICE_DIR/rvc"
  VOICE_MODELS="$VOICE_DIR/models"
  VOICE_VENV="$VOICE_DIR/venv"
  mkdir -p "$VOICE_MODELS/assets" "$VOICE_MODELS/logs"
  RVC_MARK="rvc-${RVC_COMMIT:0:12}-$(sha_of "$STUDIO/voice/rvc-mps.patch" | cut -c1-12)"
  if ! is_done "$RVC_MARK" || [ ! -d "$RVC_DIR/infer" ]; then
    # The links go first, on their own: replacing the folder must not follow one into the models.
    for link in assets logs; do
      if [ -L "$RVC_DIR/$link" ]; then unlink "$RVC_DIR/$link"; fi
    done
    get_commit yeufonic/Retrieval-based-Voice-Conversion-WebUI "$RVC_COMMIT" "$RVC_DIR" RVC-Project/Retrieval-based-Voice-Conversion-WebUI
    patch -p1 -s -d "$RVC_DIR" < "$STUDIO/voice/rvc-mps.patch" || stop_setup "RVC could not be patched for this Mac's GPU"
    mark_done "$RVC_MARK"
  fi
  for link in assets logs; do
    if [ ! -L "$RVC_DIR/$link" ]; then
      rm -rf "${RVC_DIR:?}/${link:?}"
      ln -s "$VOICE_MODELS/$link" "$RVC_DIR/$link"
    fi
  done
  VOICE_MARK="voice-env-$(sha_of "$STUDIO/voice/requirements.txt" | cut -c1-12)"
  if ! is_done "$VOICE_MARK" || [ ! -x "$VOICE_VENV/bin/python" ]; then
    if ! is_done "python-$VOICE_PYTHON"; then
      "$UV" python install --no-bin "$VOICE_PYTHON" || stop_setup "Python $VOICE_PYTHON could not be installed"
      mark_done "python-$VOICE_PYTHON"
    fi
    if [ ! -x "$VOICE_VENV/bin/python" ]; then
      "$UV" venv --python "$VOICE_PYTHON" "$VOICE_VENV" || stop_setup "the voice service's Python could not be set up"
    fi
    # shellcheck disable=SC2086
    "$UV" pip install --python "$VOICE_VENV/bin/python" $VOICE_TORCH || stop_setup "torch for the voice service failed"
    "$UV" pip install --python "$VOICE_VENV/bin/python" -r "$STUDIO/voice/requirements.txt" || stop_setup "the voice service's packages failed"
    mark_done "$VOICE_MARK"
  fi
  if [ "$SKIP_MODELS" -eq 0 ]; then
    while IFS='|' read -r dir file size sha url copy; do
      [ -z "$file" ] && continue
      mkdir -p "$VOICE_MODELS/$dir"
      get_verified "$url" "$VOICE_MODELS/$dir/$file" "$size" "$sha" "$copy"
    done <<EOF
$(voice_list)
EOF
    mkdir -p "$VOICE_MODELS/assets/weights" "$VOICE_MODELS/assets/indices"
    if [ ! -d "$VOICE_MODELS/logs/mute/0_gt_wavs" ]; then
      unzip -o -q "$VOICE_MODELS/mute.zip" -d "$VOICE_MODELS/logs"
    fi
  fi
fi

# -------------------------------------------------------------------- done
# Which engine the launcher starts, and Gemma's name for Ollama, in settings.ini beside the user's own settings.
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
if [ "$CPP" -eq 1 ]; then ini_set gemma_model "$GEMMA_MODEL"; fi
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
