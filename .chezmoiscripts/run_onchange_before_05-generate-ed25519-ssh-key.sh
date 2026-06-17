#!/bin/sh
set -eu

key_path="$HOME/.ssh/id_ed25519"

if [ -e "$key_path" ] || [ -e "$key_path.pub" ]; then
  exit 0
fi

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
ssh-keygen -t ed25519 -f "$key_path" -N "" -C "$(id -un)@$(hostname -s)"
chmod 600 "$key_path"
chmod 644 "$key_path.pub"
