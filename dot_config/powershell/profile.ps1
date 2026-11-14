$env:ADB_MDNS = '0'
$env:STARSHIP_CONFIG = "$HOME/.config/starship/config.toml"

if (Get-Command mise -ErrorAction SilentlyContinue) {
  (& mise activate pwsh) | Out-String | Invoke-Expression
}
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
  (& zoxide init powershell) | Out-String | Invoke-Expression
}
if ($env:TERM -ne 'dumb' -and (Get-Command starship -ErrorAction SilentlyContinue)) {
  (& starship init powershell) | Out-String | Invoke-Expression
}

# Git Bash supports agent shell tools; avoid the Windows WSL bash launcher.
$git = Get-Command git.exe -ErrorAction SilentlyContinue
if ($git) {
  $gitBash = Join-Path (Split-Path (Split-Path $git.Source)) 'bin/bash.exe'
  if (Test-Path -LiteralPath $gitBash) {
    $env:CLAUDE_CODE_GIT_BASH_PATH = $gitBash
  }
}

function codex-direct {
  & codex -c 'model_provider="openai"' @args
}

function claude-direct {
  & claude --settings '{"apiKeyHelper":"","env":{"ANTHROPIC_BASE_URL":"https://api.anthropic.com"}}' @args
}

if (Test-Path -LiteralPath "$HOME/.config/powershell/profile.local.ps1") {
  . "$HOME/.config/powershell/profile.local.ps1"
}
