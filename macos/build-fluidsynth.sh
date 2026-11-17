#!/bin/bash
# FluidSynth for the Mac install: one arm64 program that needs nothing but macOS itself, as FluidSynth's own
# Windows "cpp11" builds are made (C++11 threads instead of glib), with libsndfile built in for its WAV output only.
# FluidSynth publishes no macOS build, so .github/workflows/fluidsynth-macos.yml runs this and publishes the result as
# a pre-release, which macos/setup.sh fetches.  Without it, MIDI files can be imported on a Mac but not heard unless
# Homebrew's fluid-synth is there.
#
#   OUT=<folder> bash macos/build-fluidsynth.sh     (default: dist/fluidsynth)
#
# Needs Xcode's command line tools and cmake.  Both sources are pinned and checked.
set -euo pipefail

FLUIDSYNTH_VERSION=2.6.2
FLUIDSYNTH_SHA=ca376b42a3c1b186a4c8c248931789a455ac94a89b777394969d678010c2f91f
SNDFILE_VERSION=1.2.2
SNDFILE_SHA=3799ca9924d3125038880367bf1468e53a1b7e3686a934f098b7e1d286cdb80e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-$ROOT/dist/fluidsynth}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
export MACOSX_DEPLOYMENT_TARGET=14.0
cd "$WORK"

fetch() {  # url file sha
  curl -sfL --retry 5 -o "$2" "$1"
  [ "$(shasum -a 256 "$2" | cut -d' ' -f1)" = "$3" ] || { echo "$2 did not match its checksum" >&2; exit 1; }
}
fetch "https://github.com/libsndfile/libsndfile/releases/download/$SNDFILE_VERSION/libsndfile-$SNDFILE_VERSION.tar.xz" \
  sndfile.tar.xz "$SNDFILE_SHA"
fetch "https://github.com/FluidSynth/fluidsynth/archive/refs/tags/v$FLUIDSYNTH_VERSION.tar.gz" fluidsynth.tar.gz \
  "$FLUIDSYNTH_SHA"
tar -xf sndfile.tar.xz
tar -xzf fluidsynth.tar.gz

# libsndfile with no codecs of its own (WAV, which is all FluidSynth writes here), as a static library.
cmake -S "libsndfile-$SNDFILE_VERSION" -B b-sndfile -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$WORK/prefix" \
  -DBUILD_SHARED_LIBS=OFF -DENABLE_EXTERNAL_LIBS=OFF -DENABLE_MPEG=OFF -DBUILD_PROGRAMS=OFF -DBUILD_EXAMPLES=OFF \
  -DBUILD_TESTING=OFF -DENABLE_CPACK=OFF -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build b-sndfile -j "$(sysctl -n hw.ncpu)"
cmake --install b-sndfile

# FluidSynth: no glib, no other audio systems, the program statically linked.
cmake -S "fluidsynth-$FLUIDSYNTH_VERSION" -B b-fs -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$WORK/prefix" \
  -DBUILD_SHARED_LIBS=OFF -Dosal=cpp11 -Denable-libsndfile=ON -Denable-coreaudio=ON -Denable-coremidi=ON \
  -Denable-dbus=OFF -Denable-jack=OFF -Denable-pulseaudio=OFF -Denable-pipewire=OFF -Denable-portaudio=OFF \
  -Denable-sdl3=OFF -Denable-readline=OFF -Denable-libinstpatch=OFF -Denable-openmp=OFF -Denable-systemd=OFF \
  -Denable-ladspa=OFF -Denable-framework=OFF -DCMAKE_OSX_ARCHITECTURES=arm64
cmake --build b-fs -j "$(sysctl -n hw.ncpu)"

rm -rf "$OUT"
mkdir -p "$OUT/licenses/fluidsynth" "$OUT/licenses/libsndfile"
cp b-fs/src/fluidsynth "$OUT/fluidsynth"
strip "$OUT/fluidsynth"
cp "fluidsynth-$FLUIDSYNTH_VERSION/LICENSE" "$OUT/licenses/fluidsynth/"
cp "libsndfile-$SNDFILE_VERSION/COPYING" "$OUT/licenses/libsndfile/"
cat > "$OUT/README.txt" <<EOF
FluidSynth $FLUIDSYNTH_VERSION (LGPL-2.1) with libsndfile $SNDFILE_VERSION (LGPL-2.1) built in, for macOS on Apple
silicon, built unchanged from their published sources by macos/build-fluidsynth.sh in
https://github.com/yeufonic/yeufonic, which also says how to build it again (with a libsndfile of your own, say):
  https://github.com/FluidSynth/fluidsynth/archive/refs/tags/v$FLUIDSYNTH_VERSION.tar.gz
  https://github.com/libsndfile/libsndfile/releases/download/$SNDFILE_VERSION/libsndfile-$SNDFILE_VERSION.tar.xz
EOF

# Nothing but macOS's own libraries and frameworks.
if otool -L "$OUT/fluidsynth" | tail -n +2 | grep -v -E '^\s*(/System/Library/|/usr/lib/)'; then
  echo "fluidsynth links a library macOS does not have" >&2
  exit 1
fi
"$OUT/fluidsynth" --version | head -1
ls -la "$OUT"
