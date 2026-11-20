param([switch]$Pause)

$ErrorActionPreference = 'Stop'

$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  throw 'Run this script from an Administrator PowerShell (or double-click Add-Dev-Exclusions.cmd).'
}

$paths = @(
  (Join-Path $env:USERPROFILE '.t3\worktrees')
  (Join-Path $env:USERPROFILE 'Projects')
  (Join-Path $env:USERPROFILE '.cargo')
  (Join-Path $env:USERPROFILE '.rustup')
  (Join-Path $env:USERPROFILE '.gradle')
  (Join-Path $env:USERPROFILE '.konan')
  (Join-Path $env:USERPROFILE '.m2')
  (Join-Path $env:USERPROFILE '.jdks')
  (Join-Path $env:USERPROFILE '.nuget')
  (Join-Path $env:USERPROFILE '.cache')
  (Join-Path $env:USERPROFILE 'go')
  (Join-Path $env:LOCALAPPDATA 'Android')
  (Join-Path $env:LOCALAPPDATA 'go-build')
  (Join-Path $env:LOCALAPPDATA 'kotlin')
  (Join-Path $env:LOCALAPPDATA 'mise')
  (Join-Path $env:LOCALAPPDATA 'Mozilla\sccache')
  (Join-Path $env:LOCALAPPDATA 'npm-cache')
  (Join-Path $env:LOCALAPPDATA 'NuGet')
  (Join-Path $env:LOCALAPPDATA 'pip')
  (Join-Path $env:LOCALAPPDATA 'pnpm')
  (Join-Path $env:LOCALAPPDATA 'pnpm-cache')
  (Join-Path $env:LOCALAPPDATA 'uv')
  (Join-Path $env:LOCALAPPDATA 'vcpkg')
  (Join-Path $env:LOCALAPPDATA 'zig')
)

foreach ($path in $paths) {
  Add-MpPreference -ExclusionPath $path
  Write-Host "Excluded: $path"
}

Write-Host ''
Write-Host '=== Active Defender Exclusions ===' -ForegroundColor Green
(Get-MpPreference).ExclusionPath | Sort-Object | ForEach-Object { Write-Host "  $_" }

if ($Pause) {
  Write-Host ''
  Read-Host 'Done! Press Enter to close'
}
