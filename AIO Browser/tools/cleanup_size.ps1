param(
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

function Remove-PathIfExists([string]$path) {
  $full = Join-Path $repoRoot $path
  if (Test-Path -LiteralPath $full) {
    Write-Host "Removing $path"
    Remove-Item -LiteralPath $full -Recurse -Force -WhatIf:$WhatIf
  }
}

# Big optional tool downloads
Remove-PathIfExists "tools/ffmpeg"
Remove-PathIfExists "tools/goldberg_emu"
Remove-PathIfExists "tools/ffmpeg.zip"

# Local downloads / scratch
Remove-PathIfExists "test_downloads"

# Python caches
Get-ChildItem -LiteralPath $repoRoot -Recurse -Directory -Force -Filter "__pycache__" -ErrorAction SilentlyContinue |
  ForEach-Object {
    Write-Host "Removing $($_.FullName)"
    Remove-Item -LiteralPath $_.FullName -Recurse -Force -WhatIf:$WhatIf
  }

Get-ChildItem -LiteralPath $repoRoot -Recurse -File -Force -Filter "*.pyc" -ErrorAction SilentlyContinue |
  ForEach-Object {
    Write-Host "Removing $($_.FullName)"
    Remove-Item -LiteralPath $_.FullName -Force -WhatIf:$WhatIf
  }

Get-ChildItem -LiteralPath $repoRoot -Recurse -File -Force -Filter "*.pyo" -ErrorAction SilentlyContinue |
  ForEach-Object {
    Write-Host "Removing $($_.FullName)"
    Remove-Item -LiteralPath $_.FullName -Force -WhatIf:$WhatIf
  }

