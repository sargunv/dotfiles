#!/bin/zsh
[ -n "$NO_FANCY_SHELL" ] && return

[ "$(command -v starship)" ] && eval "$(starship init zsh)"
[ "$(command -v atuin)" ] && eval "$(atuin init zsh ${ATUIN_INIT_FLAGS})"
[ "$(command -v zoxide)" ] && eval "$(zoxide init zsh)"
[ "$(command -v mise)" ] && eval "$(mise activate zsh)"
