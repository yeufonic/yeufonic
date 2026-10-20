#!/bin/sh
# Build the Windows installer: windows/dist/Yeufonic-Setup-<version>.exe
#
# It stages what the installer carries (the app, our engine node, the scripts and the
# notices), then runs NSIS.  makensis on the PATH is used when there is one (Linux:
# apt install nsis; CI).  Otherwise, from WSL, the Windows NSIS in $NSIS_DIR, which
# is the zip from nsis.sourceforge.io unpacked; nothing needs installing.
#
#   sh windows/build.sh
#   NSIS_DIR=/mnt/c/tools/nsis-3.12 sh windows/build.sh
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
# VERSION=x.y.z in the environment builds as another version (the installer and the app inside
# it say so), to test an update.
VERSION=${VERSION:-$(cat "$ROOT/VERSION")}
OUT="$ROOT/windows/dist"
STAGE="$OUT/stage"

rm -rf "$STAGE"
mkdir -p "$STAGE/studio/engine-nodes"
# The app, less caches, branch markers and the page-test harnesses.
tar -C "$ROOT" --exclude='__pycache__' --exclude='static/__*' --exclude='.branch' --exclude='BRANCH' -cf - app | tar -C "$STAGE/studio" -xf -
rm -f "$STAGE/studio/app/.branch" "$STAGE/studio/app/BRANCH"
cp "$ROOT/requirements.txt" "$STAGE/studio/"
echo "$VERSION" > "$STAGE/studio/VERSION"
# Which build of this version it is, for the About window: the commit, whether the tree had
# uncommitted changes, and when it was built.
BUILD_ID=$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)
[ -z "$(git -C "$ROOT" status --porcelain --untracked-files=no 2>/dev/null)" ] || BUILD_ID="$BUILD_ID+"
echo "$BUILD_ID, $(date -u +'%-d %b %Y %H:%M UTC')${TEST_BUILD:+, test build}" > "$STAGE/studio/BUILD"
tar -C "$ROOT/engine/custom_nodes" --exclude='__pycache__' -cf - yue2_harmony | tar -C "$STAGE/studio/engine-nodes" -xf -
cp "$ROOT/windows/setup.ps1" "$ROOT/windows/launcher.py" "$ROOT/windows/yeufonic.ico" "$ROOT/windows/installer-panel.bmp" \
   "$ROOT/windows/terms.txt" "$ROOT/LICENSE.md" "$ROOT/THIRD_PARTY_NOTICES.md" "$STAGE/"

EXE="Yeufonic-Setup-$VERSION${TEST_SMALL:+-int8}${TEST_BUILD:+-test}.exe"
# Yeufonic.exe, what the shortcuts start, is built first and carried by the installer.
cp "$ROOT/windows/yeufonic-exe.nsi" "$STAGE/"
# TEST_BUILD=1 makes an installer whose setup skips the 18 GB of models.
EXTRA=${TEST_BUILD:+-DSETUP_ARGS=${TEST_ARGS:--SkipModels}}
# TEST_MANIFEST=<url> (with TEST_BUILD) makes the install look for updates at that address only,
# to try an update before it is released.  Never set for a release.
# TEST_FULL=1 (with TEST_BUILD) is a test install that downloads everything, under the test name, so it
# can sit beside a real install; TEST_SMALL=1 starts it with the low-memory model chosen.
[ -z "${TEST_FULL:-}" ] || EXTRA="-DTEST_INSTALL=1"
EXTRA="$EXTRA${TEST_SMALL:+ -DTEST_SMALL=1}"
EXTRA="$EXTRA${TEST_MANIFEST:+ -DTEST_MANIFEST=$TEST_MANIFEST}"
if command -v makensis >/dev/null 2>&1; then
  (cd "$STAGE" && makensis -V2 -DVERSION="$VERSION" -DICON=yeufonic.ico -DOUTFILE=Yeufonic.exe yeufonic-exe.nsi)
  makensis -V2 $EXTRA -DVERSION="$VERSION" -DSTAGE="$STAGE" -DOUTFILE="$OUT/$EXE" "$ROOT/windows/installer.nsi"
else
  NSIS_DIR=${NSIS_DIR:-/mnt/c/Users/Public/yue2-build/nsis-3.12}
  if [ ! -x "$NSIS_DIR/makensis.exe" ]; then
    echo "No makensis found. Install NSIS (apt install nsis), or unpack the NSIS zip and set NSIS_DIR." >&2
    exit 1
  fi
  # Windows NSIS reads Windows paths, and cannot read the WSL filesystem reliably, so
  # the staged files and the script are copied next to it first.
  WORK="$NSIS_DIR/../yue2-installer-work"
  rm -rf "$WORK"
  mkdir -p "$WORK"
  cp -r "$STAGE" "$WORK/stage"
  cp "$ROOT/windows/installer.nsi" "$WORK/"
  (cd "$WORK/stage" && "$NSIS_DIR/makensis.exe" -V2 -DVERSION="$VERSION" -DICON=yeufonic.ico -DOUTFILE=Yeufonic.exe yeufonic-exe.nsi)
  (cd "$WORK" && "$NSIS_DIR/makensis.exe" -V2 $EXTRA -DVERSION="$VERSION" -DSTAGE="$(wslpath -w "$WORK/stage")" \
      -DOUTFILE="$(wslpath -w "$WORK/$EXE")" "$(wslpath -w "$WORK/installer.nsi")")
  cp "$WORK/$EXE" "$OUT/$EXE"
  rm -rf "$WORK"
fi
echo "Built $OUT/$EXE ($(du -h "$OUT/$EXE" | cut -f1))"
