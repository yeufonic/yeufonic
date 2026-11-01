#!/bin/sh
# The browser tests, in the app's image with Playwright's Chromium added (browser-tests/Dockerfile), against this
# checkout: the app and a stand-in engine run inside the container, on ports of their own, with a library of their
# own, so a Yeufonic running on the same PC is left alone.
#
#   sh browser-tests/run.sh                 every test
#   sh browser-tests/run.sh -k cover        the ones matching, and any other pytest option
#
# BASE=<image> picks the app image to start from (yeufonic-app:latest unless set).  Screenshots of failures and the
# app's log are left in browser-tests/artifacts/.
set -eu
cd "$(dirname "$0")/.."
BASE="${BASE:-yeufonic-app:latest}"
docker build -q --build-arg BASE="$BASE" -t yeufonic-browser-tests:local browser-tests >/dev/null
exec docker run --rm --network host --label com.docker.compose.project=scratch \
  --label com.docker.compose.service=browser-tests -v "$PWD":/src -w /src \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -e BROWSER_TESTS_APP_PORT -e BROWSER_TESTS_ENGINE_PORT \
  --entrypoint python yeufonic-browser-tests:local -m pytest -p no:cacheprovider -q browser-tests "$@"
