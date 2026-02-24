#!/bin/bash
[ -n "$NO_FANCY_SHELL" ] && return

[ -f "/etc/profile.d/bash-preexec.sh" ] && . "/etc/profile.d/bash-preexec.sh"
[ -f "/usr/share/bash-prexec" ] && . "/usr/share/bash-prexec"
[ -n "$HOMEBREW_PREFIX" ] && [ -f "${HOMEBREW_PREFIX}/etc/profile.d/bash-preexec.sh" ] && . "${HOMEBREW_PREFIX}/etc/profile.d/bash-preexec.sh"
[ "$(command -v starship-multi-config)" ] && eval "$(starship-multi-config init bash)"
[ "$(command -v atuin)" ] && eval "$(atuin init bash ${ATUIN_INIT_FLAGS})"
[ "$(command -v zoxide)" ] && eval "$(zoxide init bash)"
[ "$(command -v mise)" ] && eval "$(mise activate bash)"
