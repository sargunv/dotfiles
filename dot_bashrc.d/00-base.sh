#!/bin/bash

[ -z "$PS1" ] && return

if [ -f /etc/bashrc ]; then
  . /etc/bashrc
fi
