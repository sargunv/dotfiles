# dotfiles

This project contains the files I use to set up my personal environment.

Supports:

- Linux (tested with [Bluefin](https://projectbluefin.io/))
- macOS

Usage:

- Ensure [Homebrew](https://brew.sh/) is installed and PATH is configured
- If not on macOS, ensure the terminal uses some [Nerd Font](https://www.nerdfonts.com/)

```
brew install starship chezmoi
chezmoi init sargunv --apply
```

If Homebrew can't be used, install chezmoi and starship some other way, and check
.chezmoidata/packages.yml for a list of other optional packages to install. 
