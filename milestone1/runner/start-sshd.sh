#!/bin/sh
set -eu

test -n "${AIF_RUNNER_PUBLIC_KEY:-}"
mkdir -p /runner/workspace /runner/ssh /runner/home
printf '%s\n' "$AIF_RUNNER_PUBLIC_KEY" > /runner/ssh/authorized_keys
chmod 600 /runner/ssh/authorized_keys

if [ ! -f /runner/ssh/host_ed25519_key ]; then
  ssh-keygen -q -t ed25519 -N '' -f /runner/ssh/host_ed25519_key
fi

printf '%s\n' \
  'Port 2222' \
  'ListenAddress 0.0.0.0' \
  'HostKey /runner/ssh/host_ed25519_key' \
  'AuthorizedKeysFile /runner/ssh/authorized_keys' \
  'PasswordAuthentication no' \
  'KbdInteractiveAuthentication no' \
  'PubkeyAuthentication yes' \
  'PermitRootLogin no' \
  'UsePAM no' \
  'StrictModes no' \
  'AllowUsers node' \
  'PrintMotd no' \
  'UseDNS no' \
  'Subsystem sftp internal-sftp' \
  > /runner/ssh/sshd_config

exec /usr/sbin/sshd -D -e -f /runner/ssh/sshd_config
