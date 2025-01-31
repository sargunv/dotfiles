#!/bin/sh

command -v batcat > /dev/null && ! command -v bat > /dev/null && alias bat='batcat'
command -v chezmoi > /dev/null && alias reload='chezmoi apply && exec $SHELL'
