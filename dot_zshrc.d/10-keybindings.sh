#!/bin/zsh

autoload -U select-word-style
select-word-style bash
autoload -U up-line-or-beginning-search
autoload -U down-line-or-beginning-search
zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search
bindkey "^[[A" up-line-or-beginning-search # up
bindkey "^[[B" down-line-or-beginning-search # down
bindkey '^[[1;5C' emacs-forward-word # ctrl-right
bindkey '^[[1;5D' emacs-backward-word # ctrl-left
bindkey '^[f' emacs-forward-word # opt-right
bindkey '^[b' emacs-backward-word # opt-left
