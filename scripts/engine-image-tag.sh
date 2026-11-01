#!/bin/sh
# The tag of a ready-made engine image: the first 12 hex digits of a SHA-256 over every file in its folder, names and
# contents, so the tag changes exactly when what the image is built from changes.  compose.cpp.yml names the image by
# it, and .github/workflows/engine-images.yml builds and publishes it under it.
#
#   sh scripts/engine-image-tag.sh engine-cpp        (or engine-pictures)
set -eu
dir=${1:?usage: engine-image-tag.sh <folder>}
cd "$(dirname "$0")/.."
find "$dir" -type f | LC_ALL=C sort | while read -r f; do
  printf '%s\n' "${f#"$dir"/}"
  cat "$f"
done | sha256sum | cut -c1-12
