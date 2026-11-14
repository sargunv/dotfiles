# Pick up tools installed by earlier scripts without reopening the terminal.
$env:PATH = @(
  [Environment]::GetEnvironmentVariable('Path', 'Machine')
  [Environment]::GetEnvironmentVariable('Path', 'User')
  "$env:LOCALAPPDATA\mise\shims"
  "$HOME\.local\bin"
  "$HOME\.opencode\bin"
) -join ';'
