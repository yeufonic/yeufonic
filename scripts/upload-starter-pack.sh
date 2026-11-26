#!/bin/sh
# Upload a built Starter Pack directory (from tools/build_starter_pack.py) to
# Cloudflare R2 (yeufonic-media/starter-pack/, served at https://media.yeufonic.com/starter-pack/).
#
#   sh scripts/upload-starter-pack.sh /tmp/starter-pack
#   FORCE=1 sh scripts/upload-starter-pack.sh /tmp/starter-pack
#
# By default, skips files already on R2 with the exact same byte size (except
# manifest.json, which is always uploaded last so clients never see a half-uploaded
# pack). Set FORCE=1 to re-upload every object.
set -eu

if [ -d "$HOME/.nvm/versions/node/v24.11.1/bin" ]; then
  export PATH="$HOME/.nvm/versions/node/v24.11.1/bin:$PATH"
elif [ -s "$HOME/.nvm/nvm.sh" ]; then
  export NVM_DIR="$HOME/.nvm"
  # shellcheck disable=SC1090
  . "$NVM_DIR/nvm.sh"
fi

SRC="${1:-/tmp/starter-pack}"
BUCKET="${R2_BUCKET:-yeufonic-media}"
PREFIX="${R2_PREFIX:-starter-pack}"
PUBLIC_BASE="${R2_PUBLIC_BASE:-https://media.yeufonic.com}"
FORCE="${FORCE:-0}"

if [ ! -f "$SRC/manifest.json" ]; then
  echo "error: $SRC/manifest.json not found — run: python3 tools/build_starter_pack.py --out $SRC" >&2
  exit 1
fi

content_type_for() {
  case "$1" in
    *.json) echo "application/json" ;;
    *.zip)  echo "application/zip" ;;
    *.txt)  echo "text/plain; charset=utf-8" ;;
    *)      echo "application/octet-stream" ;;
  esac
}

upload_one() {
  rel="$1"
  cache="$2"
  always="${3:-0}"
  file="$SRC/$rel"
  [ -f "$file" ] || { echo "error: missing file $file" >&2; exit 1; }
  local_bytes=$(wc -c < "$file" | tr -d ' ')
  url="$PUBLIC_BASE/$PREFIX/$rel"

  if [ "$FORCE" != "1" ] && [ "$always" != "1" ]; then
    # Use a cache-busting query string on the existence probe so Cloudflare does not cache a 404 on the real URL.
    head_info=$(curl -sI -L --max-time 15 "$url?probe=$(date +%s)" | tr -d '\r' || true)
    code=$(printf '%s\n' "$head_info" | awk 'toupper($1) ~ /^HTTP\// { c=$2 } END { print c }')
    remote_bytes=$(printf '%s\n' "$head_info" | awk 'tolower($1) == "content-length:" { len=$2 } END { print len }')
    if [ "$code" = "200" ] && [ "$remote_bytes" = "$local_bytes" ]; then
      echo "have  $rel ($local_bytes bytes)"
      return 0
    fi
  fi

  ctype=$(content_type_for "$rel")
  attempt=1
  while [ "$attempt" -le 3 ]; do
    echo "put   $rel ($local_bytes bytes) -> $BUCKET/$PREFIX/$rel (attempt $attempt/3)"
    if npx --yes wrangler r2 object put "$BUCKET/$PREFIX/$rel" \
      --file "$file" \
      --content-type "$ctype" \
      --cache-control "$cache" \
      --remote; then
      return 0
    fi
    attempt=$((attempt + 1))
    if [ "$attempt" -le 3 ]; then
      echo "retry $rel in 5s..." >&2
      sleep 5
    fi
  done
  echo "error: failed to upload $rel after 3 attempts" >&2
  exit 1
}

# Upload all payloads first (LoRAs, voices, core zip bundle(s)), then manifest.json last.
python3 - "$SRC/manifest.json" <<'PY' | while IFS= read -r rel; do
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
for item in m.get("loras") or []:
    print(item["path"])
for v in m.get("voices") or []:
    for f in v.get("files") or []:
        print(f["path"])
bundles = m.get("bundles") or ([m["bundle"]] if m.get("bundle") else [])
for b in bundles:
    print(b["path"])
PY
  [ -n "$rel" ] || continue
  upload_one "$rel" "public, max-age=86400" 0
done

upload_one "manifest.json" "public, max-age=300" 1

echo ""
echo "verifying $PUBLIC_BASE/$PREFIX/manifest.json ..."
curl -fsS --max-time 15 "$PUBLIC_BASE/$PREFIX/manifest.json" | head -n 16
echo ""
first_bundle=$(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); bs=m.get("bundles") or [m["bundle"]]; print(bs[0]["path"])' "$SRC/manifest.json")
echo "verifying byte-range support on $first_bundle ..."
status=$(curl -s -o /dev/null -w "%{http_code}" -r 0-99 --max-time 15 "$PUBLIC_BASE/$PREFIX/$first_bundle" || true)
echo "HTTP $status (expected 206)"
