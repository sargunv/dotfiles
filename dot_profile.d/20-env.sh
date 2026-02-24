#!/bin/sh

# misc env vars
export ATUIN_INIT_FLAGS='--disable-up-arrow'
export PAGER='less -RF --mouse'
export DELTA_PAGER="$PAGER"
export EDITOR='hx'
export STARSHIP_PRESET='pure-preset'
export STARSHIP_CONFIG="$HOME/.config/starship.toml.d/*.toml"
export TEALDEER_CONFIG_DIR="$HOME/.config/tealdeer"
export FNOX_AGE_KEY_FILE=~/.ssh/id_ed25519
