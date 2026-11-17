#!/bin/bash
# The yue2.cpp engine for the Mac install: yue2.cpp's server, at the commit engine-cpp/Dockerfile pins with our patches
# (engine-cpp/patches), and stable-diffusion.cpp's server, at the release windows/setup.ps1 pins, both built for Metal
# as single programs that need nothing but macOS 14 or later.  stable-diffusion.cpp publishes a macOS build, but for
# macOS 26 and later; yue2.cpp publishes none.  .github/workflows/engine-cpp-macos.yml runs this and publishes the
# result as a pre-release, which macos/setup.sh fetches for setup.sh --engine yue2cpp.
#
#   OUT=<folder> bash macos/build-cpp.sh     (default: dist/yue2cpp-macos)
#
# Needs Xcode's command line tools, git and cmake.
set -euo pipefail

SDCPP_TAG=master-1030-0a06712
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-$ROOT/dist/yue2cpp-macos}"
YUE2CPP_REF="$(sed -n 's/^ARG YUE2CPP_REF=//p' "$ROOT/engine-cpp/Dockerfile")"
[ -n "$YUE2CPP_REF" ] || { echo "no YUE2CPP_REF in engine-cpp/Dockerfile" >&2; exit 1; }
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
JOBS="$(sysctl -n hw.ncpu)"
# Metal's shaders inside each program, no library beside it, and no instructions newer than an M1's.
COMMON=(-DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=14.0
        -DBUILD_SHARED_LIBS=OFF -DGGML_NATIVE=OFF -DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON)

# yue2.cpp, from our unchanged copy first and the author's after (a repository a build needs can vanish).
get_yue2cpp() {
  rm -rf "$WORK/yue2.cpp"
  git "$@" clone --quiet https://github.com/ServeurpersoCom/yue2.cpp.git "$WORK/yue2.cpp" &&
    git -C "$WORK/yue2.cpp" checkout --quiet "$YUE2CPP_REF" &&
    git -C "$WORK/yue2.cpp" "$@" submodule update --quiet --init --recursive
}
get_yue2cpp -c "url.https://github.com/yeufonic/.insteadOf=https://github.com/ServeurpersoCom/" ||
  { echo "Our copy of yue2.cpp could not be used; trying the author's"; get_yue2cpp -c core.quotepath=on; }
git -C "$WORK/yue2.cpp" -c user.name=build -c user.email=build@localhost am --quiet "$ROOT"/engine-cpp/patches/*.patch
cmake -S "$WORK/yue2.cpp" -B "$WORK/b-yue2cpp" "${COMMON[@]}"
cmake --build "$WORK/b-yue2cpp" -j "$JOBS" --target yue-server

git clone --quiet https://github.com/leejet/stable-diffusion.cpp.git "$WORK/sdcpp"
git -C "$WORK/sdcpp" checkout --quiet "$SDCPP_TAG"
git -C "$WORK/sdcpp" submodule update --quiet --init --recursive
cmake -S "$WORK/sdcpp" -B "$WORK/b-sdcpp" "${COMMON[@]}" -DSD_METAL=ON
cmake --build "$WORK/b-sdcpp" -j "$JOBS" --target sd-server

rm -rf "$OUT"
mkdir -p "$OUT/licenses"
cp "$(find "$WORK/b-yue2cpp" -name yue-server -type f -perm -u+x | head -1)" "$OUT/yue-server"
cp "$(find "$WORK/b-sdcpp" -name sd-server -type f -perm -u+x | head -1)" "$OUT/sd-server"
strip "$OUT/yue-server" "$OUT/sd-server"
for project in yue2.cpp sdcpp; do
  (cd "$WORK/$project" && find . \( -name .git -o -name build \) -prune -o -type f \
    \( -name 'LICENSE*' -o -name 'COPYING*' -o -name 'NOTICE*' \) -print) | while read -r rel; do
    mkdir -p "$OUT/licenses/$project/$(dirname "$rel")"
    cp "$WORK/$project/$rel" "$OUT/licenses/$project/$rel"
  done
done
[ -f "$OUT/licenses/yue2.cpp/LICENSE" ] || { echo "no LICENSE for yue2.cpp" >&2; exit 1; }
cat > "$OUT/README.txt" <<EOF
yue2.cpp's server (https://github.com/ServeurpersoCom/yue2.cpp) at $YUE2CPP_REF with the patches in
engine-cpp/patches, and stable-diffusion.cpp's server (https://github.com/leejet/stable-diffusion.cpp) at $SDCPP_TAG,
built for macOS 14 or later on Apple silicon with Metal by macos/build-cpp.sh in https://github.com/yeufonic/yeufonic.
Their licences are in licenses/.
EOF

# Nothing but macOS's own libraries and frameworks, and nothing newer than macOS 14 asks for.
for program in yue-server sd-server; do
  if otool -L "$OUT/$program" | tail -n +2 | grep -v -E '^\s*(/System/Library/|/usr/lib/)'; then
    echo "$program links a library macOS does not have" >&2
    exit 1
  fi
  otool -l "$OUT/$program" | grep -A3 LC_BUILD_VERSION | grep -q 'minos 14.0' ||
    { echo "$program is not built for macOS 14" >&2; exit 1; }
done
"$OUT/yue-server" --help 2>&1 | head -3 || true
ls -la "$OUT"
