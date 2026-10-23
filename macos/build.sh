#!/bin/bash
# Build Yeufonic.app and the disk image it is shipped in, macos/dist/Yeufonic-<version>.dmg.
#
#   bash macos/build.sh                  the version in VERSION
#   VERSION=0.0.99 bash macos/build.sh   another
#
# The disk image needs a Mac (hdiutil).  Anywhere else the app is still put together, in
# macos/dist/Yeufonic.app, and packed as a .tar.gz to look inside: it is not something to ship.
#
# The app carries what windows/build.sh puts in the installer: the app, its requirements,
# VERSION, BUILD and our engine node, with setup.sh and launcher.py.  Python, the engine and
# the models are fetched by setup.sh the first time it is opened.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${VERSION:-$(cat "$ROOT/VERSION")}"
OUT="${OUT:-$ROOT/macos/dist}"
APP_DIR="$OUT/Yeufonic.app"
CONTENTS="$APP_DIR/Contents"
RES="$CONTENTS/Resources"
STUDIO="$RES/studio"

rm -rf "$APP_DIR" "$OUT/stage"
mkdir -p "$CONTENTS/MacOS" "$STUDIO/engine-nodes"

tar -C "$ROOT" --exclude='__pycache__' --exclude='static/__*' -cf - app | tar -C "$STUDIO" -xf -
cp "$ROOT/requirements.txt" "$STUDIO/"
echo "$VERSION" > "$STUDIO/VERSION"
# The commit it was built from, marked + when the working tree had changes, as windows/build.sh does.
BUILD_ID="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
[ -z "$(git -C "$ROOT" status --porcelain --untracked-files=no 2>/dev/null)" ] || BUILD_ID="$BUILD_ID+"
echo "$BUILD_ID, $(date -u +'%d %b %Y %H:%M UTC')" > "$STUDIO/BUILD"
tar -C "$ROOT/engine/custom_nodes" --exclude='__pycache__' -cf - yue2_harmony | tar -C "$STUDIO/engine-nodes" -xf -

sed "s/@VERSION@/$VERSION/g" "$ROOT/macos/Info.plist" > "$CONTENTS/Info.plist"
cp "$ROOT/macos/launcher.py" "$ROOT/macos/setup.sh" "$RES/"
cp "$ROOT/macos/yeufonic.icns" "$RES/"
cp "$ROOT/LICENSE.md" "$ROOT/THIRD_PARTY_NOTICES.md" "$RES/"

# The app's own program.  On first use, and whenever the app is not the one set up (a new copy
# dragged into Applications), setup.sh runs in a Terminal window and opens the app again when it
# has finished; otherwise the launcher runs with the app's Python.  A .command file opened with
# Terminal needs no permission to control Terminal, which "tell application" would.
cat > "$CONTENTS/MacOS/Yeufonic" <<'STUB'
#!/bin/bash
RES="$(cd "$(dirname "$0")/../Resources" && pwd)"
APP="$(cd "$(dirname "$0")/../.." && pwd)"
SUPPORT="${YEUFONIC_HOME:-$HOME/Library/Application Support/Yeufonic}"
case "$APP" in
  /Volumes/*|*/AppTranslocation/*)
    # Opened from the disk image, or from Downloads before being moved: macOS runs it from a
    # read-only copy of its own, which would be gone by the time setup opens it again.
    osascript -e 'display alert "Yeufonic" message "Drag Yeufonic into the Applications folder first, then open it from there."'
    exit 0 ;;
esac
WANT="$(cat "$RES/studio/VERSION" "$RES/studio/BUILD" 2>/dev/null)"
if [ ! -x "$SUPPORT/venv/bin/python" ] || [ "$(cat "$SUPPORT/state/set-up-for" 2>/dev/null)" != "$WANT" ]; then
  mkdir -p "$SUPPORT"
  CMD="$SUPPORT/Set up Yeufonic.command"
  {
    echo '#!/bin/bash'
    echo 'clear'
    printf '/bin/bash %q --then-open %q\n' "$RES/setup.sh" "$APP"
  } > "$CMD"
  chmod +x "$CMD"
  open -a Terminal "$CMD"
  exit 0
fi
exec "$SUPPORT/venv/bin/python" "$RES/launcher.py" "$@"
STUB
chmod +x "$CONTENTS/MacOS/Yeufonic" "$RES/setup.sh"

mkdir -p "$OUT"
if command -v hdiutil >/dev/null 2>&1; then
  # Not signed with a Developer ID, so Gatekeeper asks the first time (see macos/README.md).
  # An ad-hoc signature at least seals the bundle, so a damaged download says so.
  codesign --force --deep --sign - "$APP_DIR"
  STAGE="$OUT/stage"
  mkdir -p "$STAGE"
  cp -R "$APP_DIR" "$STAGE/"
  ln -s /Applications "$STAGE/Applications"
  DMG="$OUT/Yeufonic-$VERSION.dmg"
  rm -f "$DMG"
  hdiutil create -volname "Yeufonic $VERSION" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
  rm -rf "$STAGE"
  echo "built $DMG ($(du -h "$DMG" | cut -f1))"
  shasum -a 256 "$DMG"
else
  TAR="$OUT/Yeufonic-$VERSION-macos-app.tar.gz"
  tar -C "$OUT" -czf "$TAR" Yeufonic.app
  echo "No hdiutil here, so no disk image: the app is in $APP_DIR, and packed in $TAR to look inside."
fi
