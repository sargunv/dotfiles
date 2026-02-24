#!/bin/zsh
[ -n "$NO_FANCY_SHELL" ] && return

[ "$(command -v starship-multi-config)" ] && eval "$(starship-multi-config init zsh)"
[ "$(command -v atuin)" ] && eval "$(atuin init zsh ${ATUIN_INIT_FLAGS})"
[ "$(command -v zoxide)" ] && eval "$(zoxide init zsh)"
[ "$(command -v mise)" ] && eval "$(mise activate zsh)"
