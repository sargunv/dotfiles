#!/bin/zsh
[ -n "$NO_FANCY_SHELL" ] && return

autoload -Uz compinit
compinit -u

command -v starship > /dev/null && source <(starship completions zsh)
command -v chezmoi > /dev/null && source <(chezmoi completion zsh)
command -v mise > /dev/null && source <(mise completion zsh)
