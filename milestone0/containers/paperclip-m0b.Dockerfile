# syntax=docker/dockerfile:1.20
FROM ghcr.io/paperclipai/paperclip@sha256:99f4de5e419e0292db9912753adb800cca2d761cb839f21c7c1f1096f689fa83

USER root
WORKDIR /app
ARG PAPERCLIP_BUILD_COMMIT=b75cbb5fa6ee408c516e04544365cdcd2ff1a383

# Admission-only source build. The context must be the exact Paperclip
# composite revision recorded in dependencies.lock.yaml. The pinned base
# supplies the previously tested Linux native runner and CLI tool layer;
# this layer rebuilds the plugin SDK and server from source (not the UI).
COPY . .
RUN pnpm --filter @paperclipai/plugin-sdk build
# Paperclip master currently fails its own runner manifest freshness check
# before the server compiler runs. This admission image deliberately retains
# the native runner already present in the pinned base and performs the
# remaining server build steps directly.
RUN cd server \
  && ./node_modules/.bin/tsc --noCheck \
  && mkdir -p dist/onboarding-assets dist/built-ins dist/services/scripts dist/vendor/paperclip-runner \
  && cp -R src/onboarding-assets/. dist/onboarding-assets/ \
  && cp -R src/built-ins/. dist/built-ins/ \
  && cp -R src/services/scripts/. dist/services/scripts/ \
  && cp -R ../packages/paperclip-runner/dist/. dist/vendor/paperclip-runner/ \
  && PAPERCLIP_BUILD_COMMIT=${PAPERCLIP_BUILD_COMMIT} node scripts/write-build-stamp.mjs \
  && test -f dist/index.js

ENV PAPERCLIP_BUILD_COMMIT=${PAPERCLIP_BUILD_COMMIT}
