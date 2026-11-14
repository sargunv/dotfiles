$ErrorActionPreference = 'Stop'
$directory = Join-Path $HOME '.local/share/workflow-cli'
$lockfile = Join-Path $directory 'pnpm-lock.yaml'
$installedLockfile = Join-Path $directory 'node_modules/.pnpm/lock.yaml'

if (-not (Test-Path -LiteralPath $installedLockfile) -or
  (Get-FileHash -LiteralPath $lockfile).Hash -ne (Get-FileHash -LiteralPath $installedLockfile).Hash) {
  Push-Location $directory
  try {
    mise install --yes
    if ($LASTEXITCODE -ne 0) { throw 'Could not install workflow-cli tools.' }
    mise exec -- pnpm install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw 'Could not install workflow-cli dependencies.' }
  } finally {
    Pop-Location
  }
}

# Resolve Node explicitly so a project's pin and hooks cannot change this CLI.
$nodeDirectory = mise where node@24
if ($LASTEXITCODE -ne 0) { throw 'Node 24 is required for workflow-cli.' }
& (Join-Path $nodeDirectory 'node.exe') "$directory/src/cli.ts" @args
exit $LASTEXITCODE
