# Pinned official server, built as an isolated runtime rather than a host process.
ARG PYTHON_IMAGE=python:3.10-slim@sha256:31dd4d9529d02d7436659061cb7564cd4733fc90e5e152709a942d53382ec8d0
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.11.7@sha256:240fb85ab0f263ef12f492d8476aa3a2e4e1e333f7d67fbdd923d00a506a516a

FROM ${UV_IMAGE} AS uvbin
FROM ${PYTHON_IMAGE} AS builder
ARG SOURCE_REV=fcb23ec17186ba905590fb06b2eeecb063bc54a7
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=uvbin /uv /usr/local/bin/uv
RUN git clone --filter=blob:none https://github.com/opensearch-project/opensearch-mcp-server-py.git /source \
    && git -C /source checkout --detach ${SOURCE_REV} \
    && test "$(git -C /source rev-parse HEAD)" = "${SOURCE_REV}"
WORKDIR /source
ENV UV_PROJECT_ENVIRONMENT=/opt/mcp-venv UV_LINK_MODE=copy
RUN uv sync --frozen --no-dev --no-editable --no-cache --python /usr/local/bin/python3

FROM ${PYTHON_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends tini && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/mcp-venv /opt/mcp-venv
ENV PATH=/opt/mcp-venv/bin:${PATH} PYTHONUNBUFFERED=1
USER 65532:65532
EXPOSE 9900
ENTRYPOINT ["/usr/bin/tini", "--", "/opt/mcp-venv/bin/python", "-m", "mcp_server_opensearch"]
CMD ["--transport", "stream", "--host", "0.0.0.0", "--port", "9900", "--config", "/etc/ai-factory/opensearch-mcp.yaml"]
