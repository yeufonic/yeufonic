#!/bin/bash
# Build the macOS distribution: Yeufonic.app and Yeufonic-Setup-<version>.dmg
#
# Runs natively on macOS (including GitHub Actions macos-14 Apple Silicon runners).
# On Linux, stages the .app bundle and archives it as a tarball.
#
# Usage:
#   bash macos/build.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${VERSION:-$(cat "${ROOT}/VERSION")}"
OUT="${ROOT}/macos/dist"
STAGE="${OUT}/stage"
APP_NAME="Yeufonic"
APP_DIR="${STAGE}/${APP_NAME}.app"
CONTENTS="${APP_DIR}/Contents"
MACOS="${CONTENTS}/MacOS"
RESOURCES="${CONTENTS}/Resources"

rm -rf "${STAGE}"
mkdir -p "${MACOS}" "${RESOURCES}/studio/engine-nodes"

echo "=== Staging macOS Bundle for ${APP_NAME} ${VERSION} ==="

# 1. Stage Application Files
tar -C "${ROOT}" --exclude='__pycache__' --exclude='static/__*' --exclude='.branch' --exclude='BRANCH' -cf - app | tar -C "${RESOURCES}/studio" -xf -
cp "${ROOT}/requirements.txt" "${RESOURCES}/studio/"
echo "${VERSION}" > "${RESOURCES}/studio/VERSION"

BUILD_ID=$(git -C "${ROOT}" rev-parse --short HEAD 2>/dev/null || echo unknown)
[ -z "$(git -C "${ROOT}" status --porcelain --untracked-files=no 2>/dev/null)" ] || BUILD_ID="${BUILD_ID}+"
echo "${BUILD_ID}, $(date -u +'%d %b %Y %H:%M UTC')" > "${RESOURCES}/studio/BUILD"

tar -C "${ROOT}/engine/custom_nodes" --exclude='__pycache__' -cf - yue2_harmony | tar -C "${RESOURCES}/studio/engine-nodes" -xf -

# 2. Stage macOS Scripts & Metadata
cp "${ROOT}/macos/Info.plist" "${CONTENTS}/"
sed -i.bak "s/0.0.47/${VERSION}/g" "${CONTENTS}/Info.plist" && rm -f "${CONTENTS}/Info.plist.bak"

cp "${ROOT}/macos/launcher.py" "${RESOURCES}/"
cp "${ROOT}/macos/setup.sh" "${RESOURCES}/"
chmod +x "${RESOURCES}/setup.sh"

cp "${ROOT}/LICENSE.md" "${RESOURCES}/"
cp "${ROOT}/THIRD_PARTY_NOTICES.md" "${RESOURCES}/"

# 3. Create the Executable Launcher
cat > "${MACOS}/${APP_NAME}" << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
APP_SUPPORT="$HOME/Library/Application Support/Yeufonic"

# First launch check: run setup if runtime is not ready
if [ ! -f "${APP_SUPPORT}/state/python-runtime.done" ]; then
  osascript -e 'tell application "Terminal" to do script "bash \"'"$DIR/setup.sh"'\""'
  exit 0
fi

PYTHON_BIN="${APP_SUPPORT}/venv/bin/python"
if [ ! -x "${PYTHON_BIN}" ]; then
  PYTHON_BIN="python3"
fi

exec "${PYTHON_BIN}" "${DIR}/launcher.py" "$@"
EOF
chmod +x "${MACOS}/${APP_NAME}"

# 4. Icon handling
if [ -f "${ROOT}/macos/yeufonic.icns" ]; then
  cp "${ROOT}/macos/yeufonic.icns" "${RESOURCES}/"
elif [ -f "${ROOT}/app/static/icon-192.png" ]; then
  # Stage PNG fallback
  cp "${ROOT}/app/static/icon-192.png" "${RESOURCES}/yeufonic.png"
fi

DMG_NAME="Yeufonic-Setup-${VERSION}.dmg"

# 5. Disk Image Assembly
mkdir -p "${OUT}"

if command -v hdiutil >/dev/null 2>&1; then
  echo "Assembling macOS Disk Image (DMG) via hdiutil..."
  # Create link to /Applications for standard drag-and-drop installer UX
  ln -sf /Applications "${STAGE}/Applications"

  DMG_OUT="${OUT}/${DMG_NAME}"
  rm -f "${DMG_OUT}"

  hdiutil create \
    -volname "${APP_NAME}" \
    -srcfolder "${STAGE}" \
    -ov \
    -format UDZO \
    "${DMG_OUT}"

  echo "Built ${DMG_OUT} ($(du -h "${DMG_OUT}" | cut -f1))"
else
  echo "hdiutil not available on this platform (Linux/WSL)."
  echo "Packaging tarball archive for distribution..."
  TAR_OUT="${OUT}/Yeufonic-${VERSION}-macos.tar.gz"
  tar -C "${STAGE}" -czf "${TAR_OUT}" "${APP_NAME}.app"
  echo "Built ${TAR_OUT} ($(du -h "${TAR_OUT}" | cut -f1))"
fi
