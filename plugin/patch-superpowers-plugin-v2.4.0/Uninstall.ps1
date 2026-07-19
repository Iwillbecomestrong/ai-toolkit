param([string]$ClaudeHome = "$HOME\.claude")
$ErrorActionPreference = 'Stop'
$Target = Join-Path (Join-Path $ClaudeHome 'skills') 'patch-superpowers'
if (Test-Path $Target) { Remove-Item $Target -Recurse -Force }
Write-Output 'UNINSTALL_OK'
Write-Output 'Original Superpowers was not modified.'
