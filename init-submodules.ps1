<#
.SYNOPSIS
  初始化主仓 + 子仓的嵌套 submodule。

.DESCRIPTION
  跑两层 git submodule update --init --recursive:
  - 1 层: skills/ + agent-memory/(主仓 .gitmodules)
  - 2 层: autocontents-skill/ + mdtolatex/ + md-to-docx/(skills/.gitmodules)

  PC#2 首次配置 + 日常 submodule 指针更新都用这个脚本。

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\init-submodules.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# 1. 主仓层
Write-Host "==> 1/2 main submodule update..." -ForegroundColor Cyan
git submodule update --init --recursive
if ($LASTEXITCODE -ne 0) { throw "main submodule update failed" }

# 2. 子仓层(嵌套)
Write-Host "==> 2/2 skills nested submodule update..." -ForegroundColor Cyan
Push-Location skills
try {
    git submodule update --init --recursive
    if ($LASTEXITCODE -ne 0) { throw "skills submodule update failed" }
} finally {
    Pop-Location
}

Write-Host "`nOK two-layer submodules ready" -ForegroundColor Green
git submodule status
Push-Location skills
try { git submodule status } finally { Pop-Location }
