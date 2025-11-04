# dotfiles

This project contains the files I use to set up my personal environment.

Supports:

- Linux (tested withFedora and Ubuntu/WSL)
- macOS (arm64 and x86_64)

Usage:

First, ensure [Homebrew](https://brew.sh/) is installed and PATH is configured.

Set up the dotfiles with:

```sh
brew install starship chezmoi
chezmoi init sargunv --apply
```

If Homebrew can't be used, install [chezmoi](https://www.chezmoi.io/) and
[starship](https://starship.rs/) some other way, and check
[packages.yml](./.chezmoidata/packages.yml) for a list of other optional packages to install.

## Customization

The configuration is highly opinionated, but most configs can be overridden with additional files loaded after the default config.

- Profile: `~/.profile.d/*` will be sourced after the default profile
- Zsh: `~/.zshrc.d/*` will be sourced after the default zshrc
- Bash: `~/.bashrc.d/*` will be sourced after the default bashrc
- Tmux: `~/.config/tmux/tmux.conf.d/*` will be sourced after the default tmux.conf
- Ghostty: `~/.config/ghostty/local-config` will be sourced after the default ghostty config

For further customization, you can modify the source directly in `~/.local/share/chezmoi/...`. Modifications made this way
will need to be kept up to date manually in case of merge conflicts.
