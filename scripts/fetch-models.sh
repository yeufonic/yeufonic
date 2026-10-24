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
#   sh scripts/fetch-models.sh --pictures   also FLUX.2 klein 4B, 8.3 GB, which draws each take's
#                                        picture on this PC (diffusion_models/, text_encoders/, vae/).
#                                        Without it a picture is drawn by the external LLM's image
#                                        model, if one is set up in Settings, or not at all.
#   sh scripts/fetch-models.sh --loras      also 39 style LoRAs by their authors (CC BY-NC 4.0), 3.8 GB, with a
#                                        description each, into models/loras/. One already there is kept as
#                                        it is. The README of pshields/yue2-style-loras credits them.
#
# One size or the other: with both in models/checkpoints the app uses the full-quality one.
# A file that is already there is kept, and an interrupted download resumes.
# It also creates data/ and engine-state/output/, which the app needs to own, and
# records your user and group ids in .env for compose.yml to run the app as.
set -eu

MODEL=bf16
PICTURES=no
LORAS=no
for arg in "$@"; do
  case "$arg" in
    --int8) MODEL=int8 ;;
    --pictures) PICTURES=yes ;;
    --loras) LORAS=yes ;;
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
WHISPER=https://huggingface.co/dropbox-dash/faster-whisper-large-v3-turbo/resolve/main
# Unchanged copies of the files by Mothersuperior, a single author's account: tried first, the author's own after.
COPIES=https://huggingface.co/pshields/yue2-mothersuperior-copies/resolve/main

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

# fetch URL DEST [FALLBACK_URL]: a FALLBACK is tried when URL cannot be had, starting the file afresh.
fetch() {
  url="$1"; dest="$2"; fallback="${3:-}"
  if [ -s "$dest" ]; then
    echo "have  $(basename "$dest")"
    return 0
  fi
  echo "fetch $(basename "$dest")"
  if [ -n "$fallback" ]; then
    if curl -L --fail --retry 3 -C - -o "$dest.part" "$url"; then
      mv "$dest.part" "$dest"
      return 0
    fi
    rm -f "$dest.part"
    echo "      not from $url; trying $fallback"
    url="$fallback"
  fi
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

fetch "$COPIES/ar_lora_inst_v3abc_comfyui.safetensors" \
      "$ROOT/models/loras/ar_lora_inst_v3abc_comfyui.safetensors" \
      "$INSTRUMENTAL/ar_lora_inst_v3abc_comfyui.safetensors"

fetch "$COPIES/nar_lora_joint_v9_comfyui.safetensors" \
      "$ROOT/models/loras/nar_lora_joint_v9_comfyui.safetensors" \
      "$REAL_AUDIO/nar_lora_joint_v9_comfyui.safetensors"

fetch "$COPIES/tokenizer_head_joint_v9.safetensors" \
      "$ROOT/models/audio_encoders/tokenizer_head_joint_v9.safetensors" \
      "$REAL_AUDIO/tokenizer_head_joint_v9.safetensors"

fetch "$COPIES/minted_regularizer_pack_v2.pt" \
      "$ROOT/models/fs_audio/minted_regularizer_pack_v2.pt" \
      "$REGULARIZER/minted_regularizer_pack_v2.pt"

# FLUX.2 klein 4B for take pictures drawn here, with its text encoder and VAE (all Apache 2.0): only when asked for.
if [ "$PICTURES" = yes ]; then
  mkdir -p "$ROOT/models/diffusion_models" "$ROOT/models/vae"
  KLEIN=https://huggingface.co/Comfy-Org/Flux-2-Klein-4B/resolve/main/split_files
  fetch "https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8/resolve/main/flux-2-klein-4b-fp8.safetensors" \
        "$ROOT/models/diffusion_models/flux-2-klein-4b-fp8.safetensors"
  fetch "$KLEIN/text_encoders/qwen_3_4b_fp4_flux2.safetensors" \
        "$ROOT/models/text_encoders/qwen_3_4b_fp4_flux2.safetensors"
  fetch "$KLEIN/vae/flux2-vae.safetensors" "$ROOT/models/vae/flux2-vae.safetensors"
fi

# Style LoRAs by their authors, gathered unchanged in one Hugging Face repository: only when asked for.  A file already
# here is left alone (it may be your own copy, or a description you have written over); a new one is checked against
# its SHA-256 and removed if it does not match.
if [ "$LORAS" = yes ]; then
  mkdir -p "$ROOT/models/loras"
  STYLE_LORAS=https://huggingface.co/pshields/yue2-style-loras/resolve/main
  while read -r file sha; do
    [ -n "$file" ] || continue
    dest="$ROOT/models/loras/$file"
    if [ -s "$dest" ]; then echo "have  $file"; continue; fi
    fetch "$STYLE_LORAS/$file" "$dest"
    if [ "$(sha256sum "$dest" | cut -d' ' -f1)" != "$sha" ]; then
      rm -f "$dest"
      echo "error: $file did not match its published checksum; removed, so the next run fetches it again" >&2
      exit 1
    fi
  done <<'LIST'
blgr_kargyraa.safetensors 5f5e0274fa0233c7f97fc1408d67184d0dafa621508767d02c2c65f74b7e0642
blgr_kargyraa.txt ef6c73a5739e9100330f004b8563ee523df483a9f912f6f52e5e0666800587e0
blgr_rhodope.safetensors e6c216c5ee55683e1d75bd4f9fa6b92c67dc5960dc52706fa98f3eeab192656d
blgr_rhodope.txt 96bb6d99644b8a5fe30bf9380d054642ca0bfbadfa5c273e1fb0a7a061d13b55
blgr_steppe.safetensors adfd9dabaeb5f9cfd61f98e6dfe1a4f908e79e276fd40587c355d8634497f77d
blgr_steppe.txt 738d050a0a0abbefaa59c5ecbf93e253563a393111a0bf6f79b03399df813b7c
chnsn_cabaret.safetensors 0230ff0ba9f75fcf1586b36a8dcfe67f526703c193d9a63cf1c3f5de9c7f896e
chnsn_cabaret.txt 2da7dbc56629c46814228a26719dcf42155ca32ef9f4350c74272cb46f2d2ace
chnsn_grand_boulevard.safetensors 42527d1f61d26693905316f4392e93a2a404906309a37b884c124e38190ae101
chnsn_grand_boulevard.txt 874064b90d57d0f1c97f5cacc3e294fa4aa1081a5b848c0e978623cb27d9902d
chnsn_montmartre.safetensors bcbf1b5aebe2947b1677f87265f0d422adf868745bec12462e39ed9897c9dc65
chnsn_montmartre.txt c808d526e4423bfd984d284ffd66d2ada3894cfaadd1250c92dd4225e2ddf470
chnsn_rive_gauche.safetensors 8421a25b6650febf8e6b7418b1830dc27d79fab57605962f2c6890be98c42ef6
chnsn_rive_gauche.txt f6a6e6a20dda3bd7daee7e53cbd6dd37b438e40b85095dd7e001d13bcb92ec06
cnzn_coro.safetensors c0708785f63a7f6d582d172120aa64e8085a3f578ac5b722cb36a2c2b1e347ed
cnzn_coro.txt f8180110ba36e12488e521f5695f08edd05eceb1392150905f576e0901074849
cnzn_notte.safetensors 93b87d31bbce1dfb4e83be9d1f55e155b71f3572e640eda5351e7a34f0f32527
cnzn_notte.txt 46ef979461e8505fcf80f3f99fbef1659c29468e50554ff5439e2a435a270ad1
cnzn_sanremo.safetensors 8a0322971cfe484414d01f0765092f2454384a18cfa4167824832346451cade0
cnzn_sanremo.txt fc4c4bb3d82617a2dd3b66ff0f809360a5311144d4ed5caba020aa54c9e1fe25
cnzn_sussurro.safetensors 2ec3fc4eab4413623c600015ba3f5b7ce59f5604668344912cd2eb495b0bbd63
cnzn_sussurro.txt 3f9c829d54356dfcef44fcbb15b8f2ca89cf95c3faa215001d6e13f9f37060d9
cnzn_teatro.safetensors 6faef04d10c20a28b311815421e12676b3abfa5c650bfbd1fff1a0c01d48f31d
cnzn_teatro.txt 15a125c3e2a268e7fcbcd09e95e9cd58fa5747b0bd6be559770557b450b53944
dreampop_sv_dreampop.safetensors 617852d379c66b0407879421a353233d29cda8188cca82973a94c61b512ca03d
dreampop_sv_dreampop.txt 588c63e08b70640b78eb141cb4d6a3f99e42f54f50e49e6465cef4a4ef65a7fe
drksf_midnight.safetensors 924076bc78c0ef29d6705341e82c4d292bf557dcc9743045b4fca9bb77e7f580
drksf_midnight.txt d38ea4d03e69eb3c79d4415fee82b603118d4be86e6b0b24e15a891344c24f59
mltnt_chanter.safetensors 4aaaa42f7c61b4a3226880dd1e6f1a36bd585171d26a45358c3dba3c9d56b20c
mltnt_chanter.txt b7e1f6ede32b6578d5e2cd33fad975aeb85141d0a83e260c698224e6cd3ef1f5
mltnt_frontline.safetensors 9c8960158db6340156cc1b44fbec1ff58d0bfabfc96e933ee5a1d14b0bc26574
mltnt_frontline.txt cb33570cfc0005371ef1888546cc6dc020bde8be6a7960b0f9203d9c7c390903
mltnt_fusion.safetensors e9525b892ce625ac7491a13c21b39b7623ef132884996a87eb341370f459aa7b
mltnt_fusion.txt 4a4886eb5d4e554f5ac9e7f4e73843b8920bcefaead50f95ba46a6e7502df29c
mltnt_roots.safetensors e829f3af1534614bc28f85e821115d48888edf35aead317e9b5cdf179a79f5f3
mltnt_roots.txt 3304dd0f8c160eee5465be5c169780916bd7487824cd6b19c1defd0d0abe69d0
mltnt_soundclash.safetensors fa43a4ddb7af26fb0e7821c1ad3386fc90db84897efd00571e0c7f27cf790537
mltnt_soundclash.txt d5a988ebbe5ee8dceee6f758a178eeb04430cbf11984ff84ede647769d3c04d7
mltnt_steppers.safetensors 63094f0bbf8dd1e1fb2654a94aaba77e7360b0bef08d2254ef4a972ea8dce10e
mltnt_steppers.txt dade8fa79bf12ea685b02b9a3fb5b4a9243a34ba42bd9f622f01d789b77f57b9
qwwl_mehfil.safetensors 28132e4b545b3c57a831179553e509408fa11d6eed96811c50f0d2629ddceb2e
qwwl_mehfil.txt 5d09c0ec81338395b17b8788bd8c6cf597f0307f9b26d3ff8aa7ca0a7c831582
slider-acoustic-folk.safetensors b51c0f8a80d1001e19a2650e3184ed188c3aac97c1e2cd9cb3ec5ed03a6efef0
slider-acoustic-folk.txt 0b9a3f253d774133f0f021e07d1e484354b06993e7211376ae7ecc43fcc9ecec
slider-afrobeats.safetensors 7b0be8a08aa9bb63579d3daf6f23f08f36084282c1e143be7aa2184088a86982
slider-afrobeats.txt 921d7cea8aba2282a771fdfb20e0b5ed3e2284b2c4dc595201794fcd11951878
slider-country.safetensors c41c13e09e0daf764808be8cdbe6970b3bce359c11460584ccb09b4d502aee2a
slider-country.txt cbbe724e264dc8548dec51d1123dc91da7d82a37010518279bb2eeae56e8ef3e
slider-disco-funk.safetensors 89149145bc3f69518a7b9de63672083f994786c9af66822ef11d7b521f82cb27
slider-disco-funk.txt d3e3759eeb72ac67e8a30545bfe5bfde618352d16b240b78202d6a8a41d50ed7
slider-female.safetensors a760f6535b9be6412aec12e8ebd30c45c7886ecb01007dc900c944d57cce4a53
slider-female.txt 6b9c69609cc65d1ffdb14f0761283741f98124ae90daaad4ae5954c701032ab5
slider-hiphop.safetensors 544481919541a7f97fa581911a71fdeace03a55ddd15172a58a60ec60b963cad
slider-hiphop.txt cb5aba62431e1f480d6502ddea6678ae68e3b11f2878f820d8e89cc787c95144
slider-house.safetensors 6149fcde75b7f959c323ebd90f760dc7994183aef1a9345482fddf530c06737a
slider-house.txt 5bf43f69b59d8b8f7eb3da675bec0b2e5a0c6fc8456871e9e9037c42390b7306
slider-indie-rock.safetensors bf97b12ae89317343b1498f0bb066dbf01aa547381d60b6cf9b163db05f1b5d9
slider-indie-rock.txt 25fe649e8b414b09760b2fac5e6e7970f9f733ba838997af8cef3dba688a0a7a
slider-kpop.safetensors eca99b3b12bf94e1a605122a99c42bb3123c0d32bdb93758ee9967d20fc7458c
slider-kpop.txt 9e1a9e8057178c689ea4d869c883eddc62b041c28b96c346eaf380b42c23f9be
slider-lofi.safetensors 14474d0273924c7abe3b3b2caae794ae9052cff9a392985ff9540f0829067db4
slider-lofi.txt 4d37f0cc153b6f2486a36c44a093eca0729feaedcdd452baddab9d4f7b22349b
slider-male.safetensors 125a5e3adad5e1c541ad47bd377f1e7ff4edffc02f7552895dd6eb86dda7b5c1
slider-male.txt 0b65c5e885a29267fd1141b486edc07a47d9c039bdde813d33308c0cc7a10ae5
slider-metal.safetensors 8ae844629dcaf4fd55f13ed123f24ace69fa28951382e7652e169a6c9b7a4d5b
slider-metal.txt 93a52f3f387f20906d1a9dfc9352ad0c09a620aab60251247cd25f46688a7522
slider-pop-punk.safetensors bb8d8e4146f872c74ade1e6982946f84be1538a618a922ff9eb9674539ec34c3
slider-pop-punk.txt dafbe727ea18498a1334fa836a81ffebe47d79ec9c032ae2fe78e937cc1ed7f2
slider-pop.safetensors bc6642b68882fbc0f73df4a0e89a51c1ebe144bc1ded5b877b5dd157ffa48cd2
slider-pop.txt 66699ef7c06098f77d4514d72aed2e12ceae22735d91829ea1984c20442b7604
slider-reggaeton.safetensors 297623d8a2546749bfa7190acc5de7bfdb02135358156558cd7a8506f1a905ff
slider-reggaeton.txt 730d823a662eb143088ada83e838f49851cd4ea0a5282c7467045a784ad574f6
slider-rnb.safetensors faa89944f0d3c9a7e17f62374e29ee76d1d82f5283674060d11a811eaf9f632d
slider-rnb.txt 220d04247170392e2dfe9c2daaa13d5e648034da547ef49e72d36b47951f7b9c
sv_oldschoolhiphop.safetensors ca176909d55998d4f78426439885ff79cc96ba4daaaaea22a9936590d6e72694
sv_oldschoolhiphop.txt 93c332bb5c5cfb6b387cb32335a4e398381804597af888d47e7b620e7ea7086a
yue2_jpop_t4.safetensors 8cdbe15cf1968ff586d734a8ce4f8e7c823f8a8005fe1466c5aa9f442d257d57
yue2_jpop_t4.txt f799ce448332f646850d3dab41c182d5819c39c2840a8f3617464574fab2f173
LIST
fi

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

SF2_DIR="$ROOT/data/models/soundfonts/sf2"
fetch "https://raw.githubusercontent.com/wrightflyer/SF2_SoundFonts/master/Jnsgm2.sf2" \
      "$SF2_DIR/github_Jnsgm2.sf2"

fetch "https://archive.org/download/free-soundfonts-sf2-2019-04/Arachno_SoundFont_Version_1.0.sf2" \
      "$SF2_DIR/Arachno_SoundFont_Version_1.0.sf2"

echo "done.  models/ now holds:"
ls -la "$ROOT/models/checkpoints" "$ROOT/models/audio_encoders" "$ROOT/models/text_encoders" "$ROOT/models/loras" | grep -v '^total' | grep -v '^d'
echo ""
echo "soundfonts/sf2/ now holds:"
ls -la "$SF2_DIR" | grep -v '^total' | grep -v '^d'
