#!/bin/zsh

export HISTSIZE=100000
export SAVEHIST=100000
export HISTFILE="$HOME/.zsh_history"
setopt HIST_REDUCE_BLANKS # remove leading blanks from history
setopt APPEND_HISTORY     # append to history file, don't overwrite it
setopt HIST_IGNORE_SPACE # don't enter into history if command starts with space
setopt HIST_IGNORE_DUPS  # don't enter into history if duplicate of previous command
setopt SHARE_HISTORY     # write to history file after every command, and import into other zsh instances
setopt COMPLETE_IN_WORD  # complete from the cursor position
