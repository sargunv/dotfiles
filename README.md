# dotfiles

Personal dotfiles managed with chezmoi.

## Development

Repo tooling is pinned with mise. Python linting and type checking use locked uv
dependencies; formatting runs through dprint.

```sh
mise install
mise run check
mise run test
```

Use `mise run fix` to apply formatting and lint fixes.

## Bootstrap

On macOS, install Homebrew first:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Install chezmoi, then apply:

```sh
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- -b "$HOME/.local/bin"
"$HOME/.local/bin/chezmoi" init sargunv --apply
```
