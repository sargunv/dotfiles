#!/bin/zsh
[ -n "$NO_FANCY_SHELL" ] && return

if [ "$(command -v starship-multi-config)" ] && [ "$(command -v starship)" ]; then
  export STARSHIP_CONFIG="$(starship-multi-config --preset pure-preset ~/.config/starship.toml.d/*.toml)"
  eval "$(starship init zsh)"
fi
[ "$(command -v atuin)" ] && eval "$(atuin init zsh ${ATUIN_INIT_FLAGS})"
[ "$(command -v zoxide)" ] && eval "$(zoxide init zsh)"
[ "$(command -v mise)" ] && eval "$(mise activate zsh)"
