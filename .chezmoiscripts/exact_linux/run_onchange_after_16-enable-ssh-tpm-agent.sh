#!/bin/sh
set -eu

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl is required to enable ssh-tpm-agent.socket." >&2
  exit 1
fi

if [ ! -x "$HOME/.local/share/mise/shims/ssh-tpm-agent" ]; then
  echo "ssh-tpm-agent is missing from mise shims; the earlier mise tool install step did not complete." >&2
  exit 1
fi

systemctl --user daemon-reload
systemctl --user enable --now ssh-tpm-agent.socket
