#!/bin/bash
# FluidSynth for the native Linux install: one x86_64 binary for offline MIDI-to-WAV rendering
# (`fluidsynth -ni -o audio.file.format=float -g <gain> -F <wav> <sf2> <midi>`), with libsndfile
# built in and all live audio/MIDI/DBus/GLib backends disabled.
#
# Built inside Alpine Linux (musl) by .github/workflows/fluidsynth-linux.yml, it links 100%
# statically (`-static`) so the single binary runs on every x86_64 Linux distro regardless of
# glibc version. Built on a glibc host, it links libgcc/libstdc++ statically.
#
#   OUT=<folder> bash linux/build-fluidsynth.sh     (default: dist/fluidsynth-linux)
#
# Needs a C/C++ compiler, cmake, make/ninja, curl and tar. Both sources are pinned and checked.
set -euo pipefail

FLUIDSYNTH_VERSION=2.6.2
FLUIDSYNTH_SHA=ca376b42a3c1b186a4c8c248931789a455ac94a89b777394969d678010c2f91f
SNDFILE_VERSION=1.2.2
SNDFILE_SHA=3799ca9924d3125038880367bf1468e53a1b7e3686a934f098b7e1d286cdb80e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-$ROOT/dist/fluidsynth-linux}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
JOBS="$(nproc 2>/dev/null || echo 4)"
cd "$WORK"

IS_MUSL=0
if [ -f /etc/alpine-release ] || ls /lib/ld-musl-*.so.1 >/dev/null 2>&1; then
  IS_MUSL=1
fi

fetch() {  # url file sha
  curl -sfL --retry 5 -o "$2" "$1"
  [ "$(sha256sum "$2" | awk '{print $1}')" = "$3" ] || { echo "$2 did not match its checksum" >&2; exit 1; }
}

fetch "https://github.com/libsndfile/libsndfile/releases/download/$SNDFILE_VERSION/libsndfile-$SNDFILE_VERSION.tar.xz" \
  sndfile.tar.xz "$SNDFILE_SHA"
fetch "https://github.com/FluidSynth/fluidsynth/archive/refs/tags/v$FLUIDSYNTH_VERSION.tar.gz" \
  fluidsynth.tar.gz "$FLUIDSYNTH_SHA"
tar -xf sndfile.tar.xz
tar -xzf fluidsynth.tar.gz

# libsndfile with no external codecs (WAV float output is all Yeufonic uses), as a static library.
cmake -S "libsndfile-$SNDFILE_VERSION" -B b-sndfile -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$WORK/prefix" \
  -DBUILD_SHARED_LIBS=OFF -DENABLE_EXTERNAL_LIBS=OFF -DENABLE_MPEG=OFF \
  -DBUILD_PROGRAMS=OFF -DBUILD_EXAMPLES=OFF -DBUILD_TESTING=OFF -DENABLE_CPACK=OFF \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build b-sndfile -j "$JOBS"
cmake --install b-sndfile

# FluidSynth: C++11 OSAL (no glib), offline WAV only (no ALSA/Pulse/PipeWire/JACK/DBus/systemd).
LINK_FLAGS="-static-libgcc -static-libstdc++"
if [ "$IS_MUSL" -eq 1 ]; then
  LINK_FLAGS="-static"
fi

cmake -S "fluidsynth-$FLUIDSYNTH_VERSION" -B b-fs -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="$WORK/prefix" \
  -DCMAKE_EXE_LINKER_FLAGS="$LINK_FLAGS" \
  -DBUILD_SHARED_LIBS=OFF -Dosal=cpp11 -Denable-libsndfile=ON \
  -Denable-alsa=OFF -Denable-oss=OFF -Denable-dbus=OFF -Denable-jack=OFF \
  -Denable-pulseaudio=OFF -Denable-pipewire=OFF -Denable-portaudio=OFF \
  -Denable-sdl3=OFF -Denable-readline=OFF -Denable-libinstpatch=OFF \
  -Denable-openmp=OFF -Denable-systemd=OFF -Denable-ladspa=OFF \
  -Denable-lash=OFF -Denable-network=OFF -Denable-ipv6=OFF
cmake --build b-fs -j "$JOBS"

rm -rf "$OUT"
mkdir -p "$OUT/licenses/fluidsynth" "$OUT/licenses/libsndfile"
cp b-fs/src/fluidsynth "$OUT/fluidsynth"
strip "$OUT/fluidsynth"
chmod +x "$OUT/fluidsynth"
cp "fluidsynth-$FLUIDSYNTH_VERSION/LICENSE" "$OUT/licenses/fluidsynth/"
cp "libsndfile-$SNDFILE_VERSION/COPYING" "$OUT/licenses/libsndfile/"
cat > "$OUT/README.txt" <<EOF
FluidSynth $FLUIDSYNTH_VERSION (LGPL-2.1) with libsndfile $SNDFILE_VERSION (LGPL-2.1) built in,
for Linux x86_64 (offline WAV rendering only), built unchanged from their published sources by
linux/build-fluidsynth.sh in https://github.com/yeufonic/yeufonic:
  https://github.com/FluidSynth/fluidsynth/archive/refs/tags/v$FLUIDSYNTH_VERSION.tar.gz
  https://github.com/libsndfile/libsndfile/releases/download/$SNDFILE_VERSION/libsndfile-$SNDFILE_VERSION.tar.xz
EOF

# Portability verification gate.
if [ "$IS_MUSL" -eq 1 ]; then
  if ldd "$OUT/fluidsynth" 2>&1 | grep -q '=>'; then
    echo "fluidsynth is not statically linked!" >&2
    ldd "$OUT/fluidsynth" >&2
    exit 1
  fi
else
  # Allow only universal base Linux system libraries when built on glibc.
  if ldd "$OUT/fluidsynth" | grep -vE 'linux-vdso|ld-linux|libc\.so\.6|libm\.so\.6|libpthread\.so\.0|libdl\.so\.2|librt\.so\.1'; then
    echo "fluidsynth links an unexpected shared library" >&2
    exit 1
  fi
fi

"$OUT/fluidsynth" --version | head -2
ls -lh "$OUT/fluidsynth"
