#!/bin/zsh

autoload -Uz compinit
compinit -u

command -v starship > /dev/null && source <(starship completions zsh)
command -v chezmoi > /dev/null && source <(chezmoi completion zsh)
command -v gt > /dev/null && source <(gt completion)
