#!/bin/zsh
[ -n "$NO_FANCY_SHELL" ] && return

if [ "$(command -v starship-multi-config)" ] && [ "$(command -v starship)" ]; then
  NERD_ARGS=""
  [ -n "$HAS_NERD_FONT" ] && NERD_ARGS="$HOME/.config/starship/config-nerd.toml"
  export STARSHIP_CONFIG="$(starship-multi-config --preset pure-preset ~/.config/starship/config.toml $NERD_ARGS ~/.config/starship/config.d/*.toml(N))"
  eval "$(starship init zsh)"
fi
[ "$(command -v atuin)" ] && eval "$(atuin init zsh ${ATUIN_INIT_FLAGS})"
[ "$(command -v zoxide)" ] && eval "$(zoxide init zsh)"
[ "$(command -v mise)" ] && eval "$(mise activate zsh)"
