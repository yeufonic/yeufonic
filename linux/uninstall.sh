#!/bin/bash
# Uninstall a native Linux Yeufonic install.
#
#   bash uninstall.sh [--install-dir <path>] [--keep-data | --purge] [--yes]
#
# Stops any running Yeufonic, removes the CLI symlink and desktop entry (if they point to
# this install), and removes the app, Python environments, engine code and tools. By default
# asks whether to keep your library (data/) and downloaded models (models/).
set -euo pipefail

SELF="$(readlink -f "${BASH_SOURCE[0]}")"
INSTALL_DIR="${YEUFONIC_HOME:-$(cd "$(dirname "$SELF")" && pwd)}"
MODE=""
YES=0

while [ $# -gt 0 ]; do
  case "$1" in
    --install-dir) INSTALL_DIR="$2"; shift 2 ;;
    --install-dir=*) INSTALL_DIR="${1#*=}"; shift ;;
    --keep-data) MODE=keep; shift ;;
    --purge) MODE=purge; shift ;;
    --yes|-y) YES=1; shift ;;
    -h|--help) sed -n '2,/^set -euo/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
  esac
done

case "$INSTALL_DIR" in
  "~") INSTALL_DIR="$HOME" ;;
  "~/"*) INSTALL_DIR="$HOME/${INSTALL_DIR#~/}" ;;
esac

if [ ! -d "$INSTALL_DIR" ]; then
  echo "Nothing to uninstall at $INSTALL_DIR."
  exit 0
fi

# Stop any running processes belonging to this install.
if [ -x "$INSTALL_DIR/venv/bin/python" ] && [ -f "$INSTALL_DIR/launcher.py" ]; then
  YEUFONIC_HOME="$INSTALL_DIR" "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/launcher.py" --stop >/dev/null 2>&1 || true
fi

if [ -z "$MODE" ]; then
  if [ "$YES" -eq 1 ] || [ ! -t 0 ]; then
    MODE=keep
  else
    echo "Uninstalling Yeufonic from $INSTALL_DIR"
    printf 'Keep your library (data/) and downloaded models? [Y/n] '
    read -r ans || ans=""
    case "$ans" in [nN]*) MODE=purge ;; *) MODE=keep ;; esac
  fi
fi

# Only remove ~/.local/bin/yeufonic and the desktop entry if they point to this install.
BIN_LINK="$HOME/.local/bin/yeufonic"
if [ -L "$BIN_LINK" ] && [ "$(readlink -f "$BIN_LINK" 2>/dev/null || true)" = "$(readlink -f "$INSTALL_DIR/bin/yeufonic" 2>/dev/null || true)" ]; then
  rm -f "$BIN_LINK"
fi
DESKTOP="$HOME/.local/share/applications/yeufonic.desktop"
if [ -f "$DESKTOP" ] && grep -Fq "$INSTALL_DIR/bin/yeufonic" "$DESKTOP"; then
  rm -f "$DESKTOP"
  rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/yeufonic.svg" \
        "$HOME/.local/share/icons/hicolor/192x192/apps/yeufonic.png"
  command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

if [ "$MODE" = purge ]; then
  rm -rf "$INSTALL_DIR"
  echo "Removed Yeufonic completely from $INSTALL_DIR."
else
  # Preserve data/, settings.ini, and downloaded models (in models-kept/ so a reinstall picks them back up).
  MODELS_SRC="$INSTALL_DIR/engine/ComfyUI/models"
  if [ -d "$MODELS_SRC" ] && [ -n "$(ls -A "$MODELS_SRC" 2>/dev/null || true)" ]; then
    mkdir -p "$INSTALL_DIR/models-kept"
    cp -al "$MODELS_SRC/." "$INSTALL_DIR/models-kept/" 2>/dev/null || mv "$MODELS_SRC"/* "$INSTALL_DIR/models-kept/" 2>/dev/null || true
  fi
  for item in studio bin python venv tools engine engine-cpp downloads state cache logs browsers \
              setup.sh launcher.py uninstall.sh yeufonic.desktop.in icon.svg icon-192.png \
              LICENSE.md THIRD_PARTY_NOTICES.md; do
    rm -rf "${INSTALL_DIR:?}/${item:?}"
  done
  if [ -d "$INSTALL_DIR/voice" ]; then
    rm -rf "$INSTALL_DIR/voice/venv" "$INSTALL_DIR/voice/rvc"
  fi
  echo "Removed Yeufonic program files from $INSTALL_DIR."
  echo "Kept your library (data/), settings.ini, and models (models-kept/)."
fi
