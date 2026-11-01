#!/bin/sh
# A new Docker install, made as a user makes one, then checked: in a checkout with no data, models or .env, run
# scripts/fetch-models.sh, start the app, and write in every folder mounted read-write into it, as the user it runs as.
# A folder that is not there when Docker starts the app is made by Docker, as root, and the app cannot write in it;
# an install that has had the folder for months never shows it, so this starts from nothing.
#
#   sh scripts/check-fresh-install.sh [--comfyui | --cpp]
#
# Run it in a fresh clone: GitHub's workflow (.github/workflows/tests.yml) does.  Nothing is downloaded: curl is stood
# in for, so the models are placeholders, and only the app is started (no engine, no graphics card needed).  On a PC
# that runs Yeufonic, CHECK_PROJECT=<name> gives the app a container, image and port of its own, so the one running is
# left alone.
set -eu
ENGINE="${1:---comfyui}"
cd "$(dirname "$0")/.."
for d in data models engine-state .env; do
  if [ -e "$d" ]; then echo "$d is here already: run this in a fresh checkout" >&2; exit 2; fi
done

stub=$(mktemp -d)
trap 'rm -rf "$stub"' EXIT
printf '#!/bin/sh\nwhile [ $# -gt 0 ]; do [ "$1" = -o ] && echo placeholder > "$2"; shift; done\n' > "$stub/curl"
chmod +x "$stub/curl"
PATH="$stub:$PATH" sh scripts/fetch-models.sh "$ENGINE" > "$stub/fetch.log" 2>&1 || { cat "$stub/fetch.log"; exit 1; }
grep -E '^(note|skip)' "$stub/fetch.log" || true

files=$(sed -n 's/^COMPOSE_FILE=//p' .env)
files="${files:-compose.yml}"
if [ -n "${CHECK_PROJECT:-}" ]; then
  cat > "$stub/own.yml" <<EOF
services:
  app:
    container_name: $CHECK_PROJECT-app
    image: yeufonic-app:$CHECK_PROJECT
    ports: !reset []
EOF
  files="$files:$stub/own.yml"
  set -- -p "$CHECK_PROJECT"
else
  set --
fi
export COMPOSE_FILE="$files"

status=0
docker compose "$@" up -d --build --no-deps app
app=$(docker compose "$@" ps -q app)
i=0
until [ "$(docker inspect "$app" --format '{{.State.Health.Status}}')" = healthy ]; do
  i=$((i + 1))
  if [ $i -gt 60 ]; then echo "the app did not come up" >&2; status=1; break; fi
  sleep 2
done

if [ $status = 0 ]; then
  rw=$(docker inspect "$app" --format '{{range .Mounts}}{{if .RW}}{{.Destination}} {{end}}{{end}}')
  echo "read-write in the app: $rw"
  # shellcheck disable=SC2086
  docker compose "$@" exec -T app sh -c '
    bad=0
    for d; do
      [ -d "$d" ] || continue
      if touch "$d/.write-check" 2>/dev/null; then rm -f "$d/.write-check"; else echo "cannot write in $d" >&2; bad=1; fi
    done
    for d in /data/models/whisper /data/models/torch; do
      mkdir -p "$d/.write-check" 2>/dev/null && rmdir "$d/.write-check" || { echo "cannot make a folder in $d" >&2; bad=1; }
    done
    exit $bad' sh $rw || status=1
  if docker compose "$@" logs app 2>&1 | grep -E 'Permission denied|Traceback|Read-only file system'; then
    echo "the app's log has errors" >&2
    status=1
  fi
fi

[ $status = 0 ] || docker compose "$@" logs app 2>&1 | tail -40
docker compose "$@" down
[ $status = 0 ] && echo "a new install with $ENGINE: every folder the app writes in is its own"
exit $status
