#!/bin/bash
[ -n "$NO_FANCY_SHELL" ] && return

LG_NERD_CONFIG=""
if command -v has-nerd-font > /dev/null && has-nerd-font; then
  HAS_NERD_FONT=1
  LG_NERD_CONFIG=",$HOME/.config/lazygit/config-nerd.yml"
fi
export LG_CONFIG_FILE="$HOME/.config/lazygit/config.yml$LG_NERD_CONFIG${LG_CONFIG_FILE:+,$LG_CONFIG_FILE}"
