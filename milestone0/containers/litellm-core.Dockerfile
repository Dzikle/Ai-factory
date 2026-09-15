# Milestone 0 image for LiteLLM's MIT core/Router at the exact source revision.
# The `proxy` extra is deliberately absent: at 1.102.0 it has a direct
# dependency on the separately licensed `litellm-enterprise` package.
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.11.7@sha256:240fb85ab0f263ef12f492d8476aa3a2e4e1e333f7d67fbdd923d00a506a516a
ARG BUILD_IMAGE=cgr.dev/chainguard/wolfi-base@sha256:e624c5d5e42382ce7165ddafcbbf8e6769a24cbd02ea6114b880b05ae5ba2a8d

FROM ${UV_IMAGE} AS uvbin
FROM ${BUILD_IMAGE}

USER root
WORKDIR /app

COPY --from=uvbin /uv /usr/local/bin/uv
COPY --from=uvbin /uvx /usr/local/bin/uvx

RUN apk add --no-cache \
    bash \
    gcc \
    python-3.13 \
    python-3.13-dev \
    rust \
    openssl \
    openssl-dev \
    libsndfile

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PATH=/app/.venv/bin:${PATH}

COPY pyproject.toml uv.lock ./
COPY enterprise/pyproject.toml enterprise/
COPY litellm-proxy-extras/pyproject.toml litellm-proxy-extras/

RUN uv sync --frozen --package litellm --no-install-project \
    --no-default-groups --no-editable --python python3.13

COPY . .

RUN uv sync --frozen --package litellm --no-default-groups \
    --no-editable --python python3.13

ENTRYPOINT ["/app/.venv/bin/python"]
