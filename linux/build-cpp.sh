#!/bin/bash
# The yue2.cpp engine for the native Linux install: yue2.cpp's server (at the commit
# engine-cpp/Dockerfile pins with our patches in engine-cpp/patches/) and stable-diffusion.cpp's
# server (at the commit engine-pictures/Dockerfile pins), built with CUDA 12.8 and bundled
# redistributable CUDA 12 runtime libraries (RPATH=$ORIGIN) so users need only an NVIDIA driver.
#
# Built inside nvidia/cuda:12.8.0-devel-rockylinux8 (glibc 2.28, matching PyTorch's manylinux_2_28
# floor) by .github/workflows/engine-cpp-linux.yml, with static libgcc/libstdc++ so one archive runs
# on Ubuntu 20.04+, Debian 10+, RHEL/Rocky/AlmaLinux 8/9/10, Fedora, Arch, openSUSE, and WSL2.
#
#   OUT=<folder> bash linux/build-cpp.sh
#   CUDA_ARCHITECTURES="89-real" OUT=<folder> bash linux/build-cpp.sh   # fast single-GPU local build
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-$ROOT/dist/yue2cpp-linux}"
YUE2CPP_REF="$(sed -n 's/^ARG YUE2CPP_REF=//p' "$ROOT/engine-cpp/Dockerfile")"
SDCPP_REF="$(sed -n 's/^ARG SDCPP_REF=//p' "$ROOT/engine-pictures/Dockerfile")"
[ -n "$YUE2CPP_REF" ] || { echo "no YUE2CPP_REF in engine-cpp/Dockerfile" >&2; exit 1; }
[ -n "$SDCPP_REF" ] || { echo "no SDCPP_REF in engine-pictures/Dockerfile" >&2; exit 1; }

CUDA_ARCHITECTURES="${CUDA_ARCHITECTURES:-75-real;80-real;86-real;89-real;120-real;120-virtual}"
MAX_GLIBC="${MAX_GLIBC:-2.28}"
JOBS="$(nproc 2>/dev/null || echo 4)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Locate the CUDA toolkit installation for bundling redistributable runtime libraries.
CUDA_HOME="${CUDA_HOME:-${CUDA_PATH:-/usr/local/cuda}}"
CUDA_LIB_DIR=""
for cand in "$CUDA_HOME/targets/x86_64-linux/lib" "$CUDA_HOME/lib64"; do
  if [ -d "$cand" ] && [ -e "$cand/libcudart.so.12" ]; then
    CUDA_LIB_DIR="$cand"
    break
  fi
done
[ -n "$CUDA_LIB_DIR" ] || { echo "Could not find CUDA 12 runtime libraries (libcudart.so.12) under $CUDA_HOME" >&2; exit 1; }

# --allow-shlib-undefined defers libcuda.so.1 driver symbols to runtime;
# static libgcc/libstdc++ prevents GLIBCXX version mismatches across distros;
# CMAKE_BUILD_WITH_INSTALL_RPATH + CMAKE_INSTALL_RPATH='$ORIGIN' embeds literal $ORIGIN
# cleanly across Make and Ninja without Make expanding $O.
LINKER_FLAGS="-Wl,--allow-shlib-undefined -static-libgcc -static-libstdc++"

# ------------------------------------------------------------------ yue2.cpp
get_yue2cpp() {
  rm -rf "$WORK/yue2.cpp"
  git "$@" clone --quiet https://github.com/ServeurpersoCom/yue2.cpp.git "$WORK/yue2.cpp" &&
    git -C "$WORK/yue2.cpp" checkout --quiet "$YUE2CPP_REF" &&
    git -C "$WORK/yue2.cpp" "$@" submodule update --quiet --init --recursive
}
get_yue2cpp -c "url.https://github.com/yeufonic/.insteadOf=https://github.com/ServeurpersoCom/" ||
  { echo "Our copy of yue2.cpp could not be used; trying the author's"; get_yue2cpp -c core.quotepath=on; }
git -C "$WORK/yue2.cpp" -c user.name=build -c user.email=build@localhost am --quiet "$ROOT"/engine-cpp/patches/*.patch

cmake -S "$WORK/yue2.cpp" -B "$WORK/b-yue2cpp" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DGGML_CUDA=ON \
  -DGGML_NATIVE=OFF \
  -DCMAKE_CUDA_ARCHITECTURES="$CUDA_ARCHITECTURES" \
  -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
  '-DCMAKE_INSTALL_RPATH=$ORIGIN' \
  -DCMAKE_EXE_LINKER_FLAGS="$LINKER_FLAGS"
cmake --build "$WORK/b-yue2cpp" -j "$JOBS" --target yue-server

# ------------------------------------------------------- stable-diffusion.cpp
get_sdcpp() {
  rm -rf "$WORK/sdcpp"
  git "$@" clone --quiet https://github.com/leejet/stable-diffusion.cpp.git "$WORK/sdcpp" &&
    git -C "$WORK/sdcpp" checkout --quiet "$SDCPP_REF" &&
    git -C "$WORK/sdcpp" "$@" submodule update --quiet --init --recursive
}
get_sdcpp -c "url.https://github.com/yeufonic/.insteadOf=https://github.com/leejet/" ||
  { echo "Our copy of stable-diffusion.cpp could not be used; trying the author's"; get_sdcpp -c core.quotepath=on; }

cmake -S "$WORK/sdcpp" -B "$WORK/b-sdcpp" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DSD_CUDA=ON \
  -DGGML_NATIVE=OFF \
  -DCMAKE_CUDA_ARCHITECTURES="$CUDA_ARCHITECTURES" \
  -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
  '-DCMAKE_INSTALL_RPATH=$ORIGIN' \
  -DCMAKE_EXE_LINKER_FLAGS="$LINKER_FLAGS"
cmake --build "$WORK/b-sdcpp" -j "$JOBS" --target sd-server

# ------------------------------------------------------------------- package
rm -rf "$OUT"
mkdir -p "$OUT/licenses/cuda"

YUE_BIN="$(find "$WORK/b-yue2cpp" -name yue-server -type f -perm -u+x | head -1)"
SD_BIN="$(find "$WORK/b-sdcpp" -name sd-server -type f -perm -u+x | head -1)"
[ -n "$YUE_BIN" ] || { echo "yue-server binary not found" >&2; exit 1; }
[ -n "$SD_BIN" ] || { echo "sd-server binary not found" >&2; exit 1; }

cp "$YUE_BIN" "$OUT/yue-server"
cp "$SD_BIN" "$OUT/sd-server"
strip "$OUT/yue-server" "$OUT/sd-server"
chmod +x "$OUT/yue-server" "$OUT/sd-server"

# Copy any ggml shared libraries if cmake produced any despite BUILD_SHARED_LIBS=OFF.
find "$WORK/b-yue2cpp" "$WORK/b-sdcpp" -name 'libggml*.so*' -exec cp -a {} "$OUT/" \;

# Redistributable CUDA 12.8 runtime libraries (under NVIDIA CUDA Toolkit EULA), dereferenced to
# their SONAMEs so RPATH=$ORIGIN resolves them directly on any Linux distro with only a driver.
for lib in libcudart.so.12 libcublas.so.12 libcublasLt.so.12; do
  [ -e "$CUDA_LIB_DIR/$lib" ] || { echo "Missing $CUDA_LIB_DIR/$lib" >&2; exit 1; }
  cp -L "$CUDA_LIB_DIR/$lib" "$OUT/$lib"
done

# Collect licences for yue2.cpp, stable-diffusion.cpp, vendored headers, and NVIDIA CUDA runtime.
for project in yue2.cpp sdcpp; do
  (cd "$WORK/$project" && find . \( -name .git -o -name build \) -prune -o -type f \
    \( -iname 'LICENSE*' -o -iname 'COPYING*' -o -iname 'NOTICE*' -o -iname 'PATENTS*' \) -print) | while read -r rel; do
    mkdir -p "$OUT/licenses/$project/$(dirname "$rel")"
    cp "$WORK/$project/$rel" "$OUT/licenses/$project/$rel"
  done
done
for rel in vendor/yyjson/yyjson.h vendor/minimp3/minimp3.h; do
  if [ -f "$WORK/yue2.cpp/$rel" ]; then
    mkdir -p "$OUT/licenses/yue2.cpp/$(dirname "$rel")"
    cp "$WORK/yue2.cpp/$rel" "$OUT/licenses/yue2.cpp/$rel"
  fi
done
for f in "$WORK/sdcpp"/thirdparty/*.h "$WORK/sdcpp"/thirdparty/*.hpp; do
  if [ -f "$f" ]; then
    mkdir -p "$OUT/licenses/sdcpp/thirdparty"
    cp "$f" "$OUT/licenses/sdcpp/thirdparty/"
  fi
done
for eula in "$CUDA_HOME"/EULA* "$CUDA_HOME"/doc/EULA*; do
  if [ -f "$eula" ]; then
    cp "$eula" "$OUT/licenses/cuda/$(basename "$eula")"
    break
  fi
done
cat > "$OUT/licenses/cuda/README.txt" <<'EOF'
libcudart.so.12, libcublas.so.12 and libcublasLt.so.12 are NVIDIA CUDA 12.8 runtime libraries,
redistributed unchanged under the NVIDIA CUDA Toolkit End User License Agreement:
  https://docs.nvidia.com/cuda/eula/
EOF
[ -f "$OUT/licenses/yue2.cpp/LICENSE" ] || { echo "no LICENSE for yue2.cpp" >&2; exit 1; }
[ -f "$OUT/licenses/sdcpp/LICENSE" ] || { echo "no LICENSE for stable-diffusion.cpp" >&2; exit 1; }

cat > "$OUT/README.txt" <<EOF
yue2.cpp's server (https://github.com/ServeurpersoCom/yue2.cpp) at $YUE2CPP_REF with the patches
in engine-cpp/patches, and stable-diffusion.cpp's server (https://github.com/leejet/stable-diffusion.cpp)
at $SDCPP_REF, built for Linux x86_64 with CUDA 12.8 (architectures: $CUDA_ARCHITECTURES) by
linux/build-cpp.sh in https://github.com/yeufonic/yeufonic. Their licences are in licenses/.
EOF

# ---------------------------------------------------------- portability checks
check_glibc_floor() {
  local bin="$1" max_ver="$2"
  local max_maj="${max_ver%%.*}" max_min="${max_ver#*.}"
  local syms bad
  syms="$(readelf --version-info "$bin" 2>/dev/null | grep -oE 'GLIBC_[0-9]+\.[0-9]+' | sort -u || true)"
  bad="$(while read -r sym; do
    [ -z "$sym" ] && continue
    v="${sym#GLIBC_}"
    maj="${v%%.*}"; min="${v#*.}"
    if [ "$maj" -gt "$max_maj" ] || { [ "$maj" -eq "$max_maj" ] && [ "$min" -gt "$max_min" ]; }; then
      echo "$sym"
    fi
  done <<< "$syms")"
  if [ -n "$bad" ]; then
    echo "$bin requires glibc newer than $max_ver: $bad" >&2
    exit 1
  fi
}

for program in yue-server sd-server; do
  echo "== Checking dynamic dependencies and RPATH of $program"
  readelf -d "$OUT/$program" | grep -E 'RPATH|RUNPATH' | grep -Fq '$ORIGIN' || {
    echo "$program is missing RPATH/RUNPATH=\$ORIGIN!" >&2
    readelf -d "$OUT/$program" >&2
    exit 1
  }
  if readelf -d "$OUT/$program" | grep -q 'libstdc++\.so'; then
    echo "$program dynamically links libstdc++.so (expected static libstdc++)!" >&2
    exit 1
  fi
  ldd "$OUT/$program"
  # Every library must either live in $OUT (resolved via RPATH=$ORIGIN) or be a universal base/driver library.
  if ldd "$OUT/$program" | grep -vE "linux-vdso|ld-linux|libc\.so\.6|libm\.so\.6|libpthread\.so\.0|libdl\.so\.2|librt\.so\.1|libgomp\.so\.1|libgcc_s\.so\.1|libcuda\.so\.1|$OUT/"; then
    echo "$program links an unexpected external library!" >&2
    exit 1
  fi
  if [ "${SKIP_GLIBC_CHECK:-0}" -eq 0 ]; then
    check_glibc_floor "$OUT/$program" "$MAX_GLIBC"
  fi
  # Smoke test: both servers must print usage without a GPU attached.
  "$OUT/$program" --help 2>&1 | head -3 || true
done

ls -lh "$OUT"
