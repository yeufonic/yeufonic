#!/bin/bash
# Install or update Yeufonic on Linux from an extracted release folder (or a checkout).
#
#   bash install.sh [--install-dir <path>] [--no-desktop] [setup.sh options...]
#
# Copies Yeufonic's own files into $INSTALL_DIR, wires ~/.local/bin/yeufonic and the
# desktop application entry (unless --no-desktop or --check-only), then runs setup.sh.
# Existing data/, models/, settings.ini and state/ are always kept on an update.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${YEUFONIC_HOME:-$HOME/.local/share/yeufonic}"
NO_DESKTOP=0
CHECK_ONLY=0
SETUP_ARGS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --install-dir)
      [ $# -ge 2 ] || { echo "--install-dir requires a path" >&2; exit 2; }
      INSTALL_DIR="$2"; shift 2 ;;
    --install-dir=*)
      INSTALL_DIR="${1#*=}"; shift ;;
    --no-desktop)
      NO_DESKTOP=1; shift ;;
    --check-only)
      CHECK_ONLY=1; SETUP_ARGS+=("$1"); shift ;;
    -h|--help)
      sed -n '2,/^set -euo/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'
      echo ""
      echo "setup.sh options (passed through):"
      bash "$HERE/setup.sh" --help | sed 's/^/  /'
      exit 0 ;;
    *)
      SETUP_ARGS+=("$1"); shift ;;
  esac
done

# Expand leading ~ if passed unexpanded.
case "$INSTALL_DIR" in
  "~") INSTALL_DIR="$HOME" ;;
  "~/"*) INSTALL_DIR="$HOME/${INSTALL_DIR#~/}" ;;
esac

# Check-only needs no file copies or desktop integration.
if [ "$CHECK_ONLY" -eq 1 ]; then
  exec bash "$HERE/setup.sh" --install-dir "$INSTALL_DIR" "${SETUP_ARGS[@]}"
fi

mkdir -p "$INSTALL_DIR/bin"

# Where our source payload lives: inside a built release bundle studio/ sits beside install.sh;
# from a git checkout, the repo root is one folder up.
if [ -d "$HERE/studio" ]; then
  echo "Installing Yeufonic files into $INSTALL_DIR..."
  rm -rf "$INSTALL_DIR/studio.new"
  cp -a "$HERE/studio" "$INSTALL_DIR/studio.new"
  rm -rf "$INSTALL_DIR/studio"
  mv "$INSTALL_DIR/studio.new" "$INSTALL_DIR/studio"
  for f in LICENSE.md THIRD_PARTY_NOTICES.md; do
    [ -f "$HERE/$f" ] && cp -f "$HERE/$f" "$INSTALL_DIR/$f"
  done
  [ -f "$HERE/icon.svg" ] && cp -f "$HERE/icon.svg" "$INSTALL_DIR/icon.svg"
  [ -f "$HERE/icon-192.png" ] && cp -f "$HERE/icon-192.png" "$INSTALL_DIR/icon-192.png"
else
  ROOT="$(cd "$HERE/.." && pwd)"
  echo "Installing Yeufonic from checkout ($ROOT) into $INSTALL_DIR..."
  rm -rf "$INSTALL_DIR/studio.new"
  mkdir -p "$INSTALL_DIR/studio.new/engine-nodes" "$INSTALL_DIR/studio.new/voice" "$INSTALL_DIR/studio.new/engine"
  tar -C "$ROOT" --exclude='__pycache__' --exclude='static/__*' -cf - app | tar -C "$INSTALL_DIR/studio.new" -xf -
  cp -f "$ROOT/requirements.txt" "$ROOT/VERSION" "$INSTALL_DIR/studio.new/"
  BUILD_ID="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  echo "$BUILD_ID, $(date -u +'%d %b %Y %H:%M UTC')" > "$INSTALL_DIR/studio.new/BUILD"
  tar -C "$ROOT/engine/custom_nodes" --exclude='__pycache__' -cf - yue2_harmony | tar -C "$INSTALL_DIR/studio.new/engine-nodes" -xf -
  cp -f "$ROOT/engine/start.py" "$INSTALL_DIR/studio.new/engine/start.py"
  cp -f "$ROOT/voice/server.py" "$ROOT/voice/requirements.txt" "$INSTALL_DIR/studio.new/voice/"
  rm -rf "$INSTALL_DIR/studio"
  mv "$INSTALL_DIR/studio.new" "$INSTALL_DIR/studio"
  for f in LICENSE.md THIRD_PARTY_NOTICES.md; do
    [ -f "$ROOT/$f" ] && cp -f "$ROOT/$f" "$INSTALL_DIR/$f"
  done
  [ -f "$ROOT/app/static/icon.svg" ] && cp -f "$ROOT/app/static/icon.svg" "$INSTALL_DIR/icon.svg"
  [ -f "$ROOT/app/static/icon-192.png" ] && cp -f "$ROOT/app/static/icon-192.png" "$INSTALL_DIR/icon-192.png"
fi

cp -f "$HERE/setup.sh" "$INSTALL_DIR/setup.sh"
cp -f "$HERE/launcher.py" "$INSTALL_DIR/launcher.py"
cp -f "$HERE/uninstall.sh" "$INSTALL_DIR/uninstall.sh"
cp -f "$HERE/yeufonic" "$INSTALL_DIR/bin/yeufonic"
[ -f "$HERE/yeufonic.desktop.in" ] && cp -f "$HERE/yeufonic.desktop.in" "$INSTALL_DIR/yeufonic.desktop.in"
chmod +x "$INSTALL_DIR/setup.sh" "$INSTALL_DIR/uninstall.sh" "$INSTALL_DIR/bin/yeufonic"

if [ "$NO_DESKTOP" -eq 0 ]; then
  mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications" \
           "$HOME/.local/share/icons/hicolor/scalable/apps" \
           "$HOME/.local/share/icons/hicolor/192x192/apps"
  ln -sf "$INSTALL_DIR/bin/yeufonic" "$HOME/.local/bin/yeufonic"
  [ -f "$INSTALL_DIR/icon.svg" ] && cp -f "$INSTALL_DIR/icon.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/yeufonic.svg"
  [ -f "$INSTALL_DIR/icon-192.png" ] && cp -f "$INSTALL_DIR/icon-192.png" "$HOME/.local/share/icons/hicolor/192x192/apps/yeufonic.png"
  if [ -f "$INSTALL_DIR/yeufonic.desktop.in" ]; then
    # Escape & and | in INSTALL_DIR for sed.
    ESC_DIR="$(printf '%s' "$INSTALL_DIR" | sed 's/[&|]/\\&/g')"
    sed "s|@INSTALL_DIR@|$ESC_DIR|g" "$INSTALL_DIR/yeufonic.desktop.in" > "$HOME/.local/share/applications/yeufonic.desktop"
  fi
  command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
  command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

bash "$INSTALL_DIR/setup.sh" --install-dir "$INSTALL_DIR" "${SETUP_ARGS[@]}"

if [ "$NO_DESKTOP" -eq 0 ]; then
  case ":${PATH:-}:" in
    *":$HOME/.local/bin:"*) ;;
    *)
      echo ""
      echo "Note: $HOME/.local/bin is not on your PATH."
      echo "To run 'yeufonic' from any terminal, add this to your ~/.bashrc or ~/.zshrc:"
      echo '  export PATH="$HOME/.local/bin:$PATH"'
      ;;
  esac
fi
