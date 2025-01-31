#!/bin/bash

[ -f "/etc/profile.d/bash-preexec.sh" ] && . "/etc/profile.d/bash-preexec.sh"
[ -f "/usr/share/bash-prexec" ] && . "/usr/share/bash-prexec"
[ -n "$HOMEBREW_PREFIX" ] && [ -f "${HOMEBREW_PREFIX}/etc/profile.d/bash-preexec.sh" ] && . "${HOMEBREW_PREFIX}/etc/profile.d/bash-preexec.sh"
[ "$(command -v starship)" ] && eval "$(starship init bash)"
[ "$(command -v atuin)" ] && eval "$(atuin init bash ${ATUIN_INIT_FLAGS})"
[ "$(command -v zoxide)" ] && eval "$(zoxide init bash)"
[ "$(command -v chezmoi)" ] && source <(chezmoi completion bash)
