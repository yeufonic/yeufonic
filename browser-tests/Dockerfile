# The app's image with a browser in it, for the browser tests: Playwright and its Chromium, where any user can run it
# (run.sh runs the tests as you, so what they leave in the checkout is yours).
ARG BASE=yeufonic-app:latest
FROM ${BASE}
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN pip install --no-cache-dir pytest==8.4.2 playwright==1.64.1 anyio \
    && playwright install --with-deps chromium-headless-shell \
    && chmod -R a+rX /ms-playwright
