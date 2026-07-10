<#
.SYNOPSIS
  3 个子子仓的 SemVer commit + tag + push 助手。

.DESCRIPTION
  用法: bump-skill.ps1 -Skill <name> [-Type major|minor|patch] [-Message <msg>]
  例子: bump-skill.ps1 -Skill autocontents-skill -Type minor -Message "added XX"

  流程:
  1. cd 进 skills/<name>/
  2. add + commit(若工作树有改动)
  3. 计算下一个 SemVer tag(从最新 tag 解析,按 -Type 增量)
  4. git tag <new>
  5. git push origin main --follow-tags
  6. 回到 skills/ 子仓更新引用 + commit
  7. 回到主仓更新 skills/ 引用 + commit
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('autocontents-skill', 'mdtolatex', 'md-to-docx', 'fix-critical-bug')]
    [string]$Skill,

    [ValidateSet('major', 'minor', 'patch')]
    [string]$Type = 'patch',

    [string]$Message = ''
)

$ErrorActionPreference = 'Stop'

$skillPath = Join-Path $PSScriptRoot "skills/$Skill"
if (-not (Test-Path $skillPath)) { throw "skill submodule not found: $skillPath" }

# 1. cd into sub-submodule
Push-Location $skillPath
try {
    Write-Host "==> 1/4 sub-submodule commit..." -ForegroundColor Cyan
    git add -A
    $commitMsg = if ($Message) { $Message } else { "chore($Skill): bump" }
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  no staged changes, skip commit" -ForegroundColor Yellow
    } else {
        git commit -m "$commitMsg`n`nCo-Authored-By: Claude <noreply@anthropic.com>"
    }

    # 2. Compute SemVer
    Write-Host "==> 2/4 compute SemVer..." -ForegroundColor Cyan
    $latestTag = (git tag --sort=-v:refname | Select-Object -First 1)
    if (-not $latestTag) { $latestTag = 'v0.0.0' }
    if ($latestTag -notmatch '^v(\d+)\.(\d+)\.(\d+)$') {
        throw "latest tag format wrong: $latestTag (need vX.Y.Z)"
    }
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    $patch = [int]$Matches[3]
    switch ($Type) {
        'major' { $major++; $minor = 0; $patch = 0 }
        'minor' { $minor++; $patch = 0 }
        'patch' { $patch++ }
    }
    $newTag = "v$major.$minor.$patch"
    Write-Host "  $latestTag -> $newTag" -ForegroundColor Green

    # 3. Tag + push
    Write-Host "==> 3/4 tag + push..." -ForegroundColor Cyan
    git tag $newTag
    # Use the branch name from .gitmodules config (mdtolatex uses custom branch)
    $branch = (git rev-parse --abbrev-ref HEAD)
    git push origin $branch --follow-tags
} finally {
    Pop-Location
}

# 4. Update parent submodule reference
Write-Host "==> 4/4 update parent submodule ref..." -ForegroundColor Cyan
Push-Location (Join-Path $PSScriptRoot 'skills')
try {
    git add $Skill
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "chore(skills): bump $Skill to $newTag`n`nCo-Authored-By: Claude <noreply@anthropic.com>"
        git push origin main
    } else {
        Write-Host "  skills/ ref unchanged" -ForegroundColor Yellow
    }
} finally {
    Pop-Location
}

Push-Location $PSScriptRoot
try {
    git add skills
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "chore: bump skills submodule ($Skill $newTag)`n`nCo-Authored-By: Claude <noreply@anthropic.com>"
    } else {
        Write-Host "  main repo ref unchanged" -ForegroundColor Yellow
    }
} finally {
    Pop-Location
}

Write-Host "`nOK $Skill bumped to $newTag" -ForegroundColor Green
