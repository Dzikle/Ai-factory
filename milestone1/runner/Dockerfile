FROM aif-paperclip-fork:62760ac@sha256:2c574c948ce21a22cf6e8bbcf136b99b8e55bd2d460042ec69fa62bbbc224455

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-server python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/aif-venv \
    && /opt/aif-venv/bin/pip install --no-cache-dir 'jsonschema[format]==4.25.1' 'PyYAML==6.0.2'

ENV PATH="/opt/aif-venv/bin:${PATH}"

COPY --chmod=755 python3-wrapper.sh /usr/local/bin/python3
COPY --chmod=755 start-sshd.sh /usr/local/bin/aif-runner-sshd
USER node
WORKDIR /runner
EXPOSE 2222
ENTRYPOINT ["/usr/local/bin/aif-runner-sshd"]
