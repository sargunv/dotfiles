#!/bin/sh
set -eu

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl not found; skipping update-agents.timer enable." >&2
  exit 0
fi

# Ensure the timer unit exists in the target (chezmoi has applied it)
if [ ! -f "$HOME/.config/systemd/user/update-agents.timer" ]; then
  echo "update-agents.timer not found in target; skipping." >&2
  exit 0
fi

systemctl --user daemon-reload
systemctl --user enable --now update-agents.timer
systemctl --user list-timers update-agents.timer --no-pager || true
