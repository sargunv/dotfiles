# dotfiles

Personal dotfiles managed with chezmoi.

## AI gateway

Coding agents use the LiteLLM gateway. Save its key on each machine; chezmoi
does not manage it:

```sh
install -d -m 700 ~/.config/litellm
install -m 600 /dev/null ~/.config/litellm/api-key
$EDITOR ~/.config/litellm/api-key
```

On Windows, create the same file from PowerShell:

```powershell
New-Item -ItemType Directory -Path "$HOME/.config/litellm" -Force
notepad "$HOME/.config/litellm/api-key"
```

To bypass the gateway for one invocation, use these shell functions (zsh or
PowerShell):

```sh
codex-direct
claude-direct --continue
```

They use the provider's normal authentication, such as your existing ChatGPT or
Claude login. Arguments pass through to the CLI. Regular `codex` and `claude`
launches keep using the gateway.

## Git signing

On macOS, commits and tags use `~/.ssh/commit_signing_key.pub`, backed by a
non-exportable Secure Enclave key without biometric protection. Its private
counterpart is a local hardware reference, not an exported private key. Register
the public key with GitHub as a signing key only.

SSH authentication continues to use its separate key. Linux signing continues to
use the TPM setup. Hardware keys and their local references are provisioned on
each machine; they are not stored in this repository.

Windows uses the local `~/.ssh/id_ed25519` software key for SSH and signing. The
first apply creates it only if neither the private nor public key exists. Add
`id_ed25519.pub` to GitHub for authentication and signing, and add its public
key to `.chezmoidata/ssh_keys.yml` for local signature verification. To use a
different signing key, override `user.signingKey` in
`~/.config/git/config.local`.

## Development

```sh
mise install
mise run check
node --test
```

Use `mise run fix` to apply formatting and lint fixes.

The tests require chezmoi on PATH (or set `CHEZMOI` to its executable). They
check platform selection and rendered agent configs without applying the
dotfiles. Windows also runs credential helpers, checks PowerShell syntax, and
exercises SSH key creation and package-install failure handling in temporary
directories.

## Bootstrap

### Windows

Use native Windows PowerShell/PowerShell 7, not WSL. Enable **Developer Mode**
in Windows Settings so chezmoi can create the shared agent instruction and skill
symlinks without running elevated. Install the prerequisites:

```powershell
winget install --id Microsoft.PowerShell --exact --source winget
winget install --id Git.Git --exact --source winget
winget install --id twpayne.chezmoi --exact --source winget
```

Open a new PowerShell 7 terminal (`pwsh`), then:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
chezmoi init sargunv
chezmoi diff
chezmoi apply
```

The apply installs the development CLI utilities through WinGet, the global mise
toolchain, and Claude, Codex, OpenCode v2, Pi, oh-my-pi, and Grok through their
official installers. OpenCode's installer uses Git Bash to install its native
Windows binary. Installers select the Windows ARM64 or x64 builds where
available; WinGet can use x64 emulation for packages without ARM64 builds.

The PowerShell setup adds one source line to your existing PowerShell 7 profile,
including when Documents is redirected to OneDrive. It enables mise, Starship,
and zoxide; put machine-specific overrides in
`~/.config/powershell/profile.local.ps1`. Reopen terminals and dev/agent apps
after the first apply so they inherit the updated PATH.

Agent updates run daily at 09:00 through the current user's
`chezmoi-update-agents` scheduled task. It requires a signed-in session, catches
up on missed runs, and writes logs under
`%LOCALAPPDATA%/chezmoi/logs/update-agents.log`. Run `update-agents.ps1` to
update manually. WinGet owns updates to mise and the other WinGet packages.

Neovim, LazyGit, sccache, and tealdeer receive copies of the shared configs in
their Windows AppData locations. Neovim's optional native Telescope sorter is
disabled on Windows; Treesitter parsers still need a C compiler. The custom
`starship-multi-config` binary currently has no Windows release, so PowerShell
uses the shared Starship config directly. zsh, tmux, Atuin shell integration,
Ghostty, and the hardware-backed macOS/Linux SSH setup remain platform-specific.

### macOS and Linux

On macOS, install Homebrew first:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

On Debian and Ubuntu, the first apply installs the apt packages with `sudo`.
Make zsh the login shell afterwards with `chsh -s "$(command -v zsh)"`. SSH
hosts that belong to one machine go in `~/.ssh/config.local`.

Install chezmoi, then apply:

```sh
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- -b "$HOME/.local/bin"
"$HOME/.local/bin/chezmoi" init sargunv --apply
```
