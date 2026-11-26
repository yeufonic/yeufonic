#!/bin/bash
# Build the self-extracting native Linux installer:
#   linux/dist/yeufonic-<version>-linux-x86_64.run
#
#   bash linux/build.sh                  # uses VERSION
#   VERSION=0.0.99 bash linux/build.sh   # custom version
#
# Carries only Yeufonic's own files (studio/, engine node, start.py, voice service,
# install.sh, setup.sh, launcher.py, uninstall.sh, CLI wrapper, icon, notices) — under 2 MB.
# Python, PyTorch, ComfyUI/yue2.cpp, static tools and models are fetched by setup.sh at install time.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${VERSION:-$(cat "$ROOT/VERSION")}"
OUT="${OUT:-$ROOT/linux/dist}"
STAGE="$OUT/stage"
BUNDLE="yeufonic-$VERSION"
PKG="$STAGE/$BUNDLE"
STUDIO="$PKG/studio"

rm -rf "$STAGE"
mkdir -p "$STUDIO/engine-nodes" "$STUDIO/engine" "$STUDIO/voice" "$OUT"

tar -C "$ROOT" --exclude='__pycache__' --exclude='static/__*' -cf - app | tar -C "$STUDIO" -xf -
cp "$ROOT/requirements.txt" "$STUDIO/"
echo "$VERSION" > "$STUDIO/VERSION"
BUILD_ID="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
[ -z "$(git -C "$ROOT" status --porcelain --untracked-files=no 2>/dev/null)" ] || BUILD_ID="$BUILD_ID+"
echo "$BUILD_ID, $(date -u +'%d %b %Y %H:%M UTC')" > "$STUDIO/BUILD"
tar -C "$ROOT/engine/custom_nodes" --exclude='__pycache__' -cf - yue2_harmony | tar -C "$STUDIO/engine-nodes" -xf -
cp "$ROOT/engine/start.py" "$STUDIO/engine/start.py"
cp "$ROOT/voice/server.py" "$ROOT/voice/requirements.txt" "$STUDIO/voice/"

cp "$ROOT/linux/install.sh" "$ROOT/linux/setup.sh" "$ROOT/linux/launcher.py" \
   "$ROOT/linux/uninstall.sh" "$ROOT/linux/yeufonic" "$ROOT/linux/yeufonic.desktop.in" "$PKG/"
cp "$ROOT/app/static/icon.svg" "$ROOT/app/static/icon-192.png" "$PKG/"
cp "$ROOT/LICENSE.md" "$ROOT/THIRD_PARTY_NOTICES.md" "$PKG/"
chmod +x "$PKG/install.sh" "$PKG/setup.sh" "$PKG/uninstall.sh" "$PKG/yeufonic"

TAR="$STAGE/$BUNDLE.tar.gz"
tar -C "$STAGE" -czf "$TAR" "$BUNDLE"
PAYLOAD_SHA="$(sha256sum "$TAR" | awk '{print $1}')"

RUN="$OUT/yeufonic-$VERSION-linux-x86_64.run"
cat > "$RUN" <<HEADER
#!/bin/bash
# Yeufonic $VERSION self-extracting command-line installer for Linux (x86_64, no Docker, no GUI).
#
#   ./yeufonic-$VERSION-linux-x86_64.run [options]
#
# Installer options:
#   --help, -h                 show this help and exit
#   --version                  print the bundled Yeufonic version and exit
#   --install-dir <path>       where to install Yeufonic (default: ~/.local/share/yeufonic)
#   --extract-only [dir]       unpack the installer files into [dir] (default: ./$BUNDLE) and exit
#   --no-desktop               skip ~/.local/bin symlink and .desktop menu entry
#
# Setup options (passed through to setup.sh):
#   --engine comfyui|yue2cpp   choose the music engine (default: comfyui)
#   --int8 | --bf16            ComfyUI YuE2 model size (default: bf16)
#   --cpp-model q8|bf16        yue2.cpp YuE2 model size (default: q8)
#   --lyrics | --no-lyrics     include or skip local Gemma 4 for lyric drafts (default: include)
#   --pictures | --no-pictures  local take pictures (default: FLUX.2 klein 4B)
#   --picture-model 4b|fibo2    choose local take-picture model (implies --pictures)
#   --loras | --no-loras        39 style LoRAs (CC BY-NC 4.0)
#   --voices | --no-voices      recorded voices (RVC + BS-Roformer)
#   --demos | --no-demos        Starter Pack demo takes (~1.7 GB; default yes on fresh install, no on existing)
#   --force-downloads          re-download models, LoRAs, SoundFonts and voice files even if present
#   --reconfigure              re-ask engine, model size and component choices (pre-filling current settings)
#   --check-only               run the system check without installing or downloading
#   --skip-models              install everything except the multi-GB models
set -euo pipefail

VERSION="$VERSION"
BUNDLE="$BUNDLE"
PAYLOAD_SHA="$PAYLOAD_SHA"

EXTRACT_ONLY=0
EXTRACT_DIR=""
PASS_ARGS=()

show_help() {
  sed -n '2,/^set -euo/p' "\$0" | sed '\$d' | sed 's/^# \{0,1\}//'
}

while [ \$# -gt 0 ]; do
  case "\$1" in
    -h|--help)
      show_help
      exit 0 ;;
    --version)
      echo "Yeufonic \$VERSION (linux-x86_64)"
      exit 0 ;;
    --extract-only)
      EXTRACT_ONLY=1
      if [ \$# -ge 2 ] && [ "\${2#-}" = "\$2" ]; then
        EXTRACT_DIR="\$2"; shift 2
      else
        EXTRACT_DIR="./\$BUNDLE"; shift
      fi ;;
    --extract-only=*)
      EXTRACT_ONLY=1
      EXTRACT_DIR="\${1#*=}"; shift ;;
    --install-dir)
      [ \$# -ge 2 ] || { echo "--install-dir requires a path" >&2; exit 2; }
      PASS_ARGS+=("\$1" "\$2"); shift 2 ;;
    --install-dir=*)
      PASS_ARGS+=("\$1"); shift ;;
    *)
      PASS_ARGS+=("\$1"); shift ;;
  esac
done

MARKER_LINE="\$(LC_ALL=C awk '/^__YEUFONIC_ARCHIVE_BELOW__\$/ { print NR + 1; exit 0 }' "\$0")"
if [ -z "\$MARKER_LINE" ]; then
  echo "Installer archive marker is missing: this file may be truncated." >&2
  exit 1
fi

verify_payload() {
  local got
  got="\$(tail -n +"\$MARKER_LINE" "\$0" | sha256sum | awk '{print \$1}')"
  if [ "\$got" != "\$PAYLOAD_SHA" ]; then
    echo "Installer payload checksum mismatch (expected \$PAYLOAD_SHA, got \$got). Re-download the installer." >&2
    exit 1
  fi
}

verify_payload

if [ "\$EXTRACT_ONLY" -eq 1 ]; then
  mkdir -p "\$EXTRACT_DIR"
  tail -n +"\$MARKER_LINE" "\$0" | tar -xzf - -C "\$EXTRACT_DIR" --strip-components=1
  echo "Extracted Yeufonic \$VERSION to \$EXTRACT_DIR"
  echo "Inspect the scripts or install manually with: bash \$(printf '%q' "\$EXTRACT_DIR/install.sh")"
  exit 0
fi

TMP="\$(mktemp -d "\${TMPDIR:-/tmp}/yeufonic-install.XXXXXX")"
trap 'rm -rf "\$TMP"' EXIT
tail -n +"\$MARKER_LINE" "\$0" | tar -xzf - -C "\$TMP"
bash "\$TMP/\$BUNDLE/install.sh" "\${PASS_ARGS[@]}"
exit 0
__YEUFONIC_ARCHIVE_BELOW__
HEADER

cat "$TAR" >> "$RUN"
chmod +x "$RUN"
rm -rf "$STAGE"

SHA="$(sha256sum "$RUN" | awk '{print $1}')"
printf '%s  %s\n' "$SHA" "$(basename "$RUN")" > "$RUN.sha256"
echo "Built $RUN ($(du -h "$RUN" | cut -f1))"
echo "SHA-256: $SHA"
