#Requires -Version 5.1
<#
.SYNOPSIS
    Copies skills/plugins from G:\skill\ into all installed AI framework directories.

.DESCRIPTION
    Idempotent. Safe to re-run. Per-framework try/catch — one framework's failure
    does not abort the others. Logs to G:\skill\install.log.

.PARAMETER RepoRoot
    Path to the central skills repo. Defaults to the directory containing this script.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File G:\skill\install.ps1
    powershell -ExecutionPolicy Bypass -File G:\skill\install.ps1 -RepoRoot 'D:\skill'
#>

[CmdletBinding()]
param(
    [string]$RepoRoot
)

# When invoked via -File, $PSScriptRoot can be empty; fall back to script path
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    if ($PSScriptRoot) {
        $RepoRoot = $PSScriptRoot
    } elseif ($MyInvocation.MyCommand.Path) {
        $RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    } else {
        $RepoRoot = (Get-Location).Path
    }
}

$ErrorActionPreference = 'Continue'
$Repo     = (Resolve-Path -LiteralPath $RepoRoot).Path
$LogFile  = Join-Path $Repo 'install.log'
$Manifest = Join-Path $Repo 'manifest.json'

# --- helpers -----------------------------------------------------------------

function Write-Log {
    param([string]$Message)
    $stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $line  = "$stamp  $Message"
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
}

function Expand-PathVar {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $Path }
    $expanded = $Path
    if ($expanded.StartsWith('~/')) {
        $expanded = Join-Path $HOME $expanded.Substring(2)
    } elseif ($expanded -eq '~') {
        $expanded = $HOME
    }
    $expanded = $expanded -replace '%LOCALAPPDATA%', $env:LOCALAPPDATA
    return $expanded
}

function Remove-DirRobust {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    try {
        $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
        $item.Attributes = 'Normal'
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
    } catch {
        Write-Log "  WARN: could not remove $Path -- $($_.Exception.Message)"
    }
}

function Copy-SkillTree {
    param([string]$SourceDir, [string]$DestinationDir)
    New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
    Copy-Item -Path (Join-Path $SourceDir '*') -Destination $DestinationDir -Recurse -Force
}

# --- bootstrap ---------------------------------------------------------------

$null = New-Item -ItemType File -Path $LogFile -Force
Write-Log "===== install.ps1 START (user=$env:USERNAME, repo=$Repo) ====="

if (-not (Test-Path -LiteralPath $Manifest)) {
    Write-Log "FATAL: manifest.json not found at $Manifest"
    exit 1
}

try {
    $cfg = Get-Content -Raw -LiteralPath $Manifest | ConvertFrom-Json
} catch {
    Write-Log "FATAL: manifest.json is not valid JSON -- $($_.Exception.Message)"
    exit 1
}

# --- main loop over frameworks ----------------------------------------------

foreach ($fw in $cfg.frameworks.PSObject.Properties) {
    $name = $fw.Name
    $def  = $fw.Value

    if ($def.PSObject.Properties.Name -contains 'skip' -and $def.skip) {
        Write-Log "[$name] SKIPPED -- $($def.reason)"
        continue
    }

    try {
        $dst = Expand-PathVar $def.skills_dst
        $src = Join-Path $Repo $def.skills_src

        if (-not (Test-Path -LiteralPath $src)) {
            Write-Log "[$name] no source dir ($src), skipping"
            continue
        }

        $skills = @{}
        Get-ChildItem -LiteralPath $src -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { $skills[$_.Name] = $_.FullName }

        New-Item -ItemType Directory -Path $dst -Force | Out-Null

        # Additive model for ALL frameworks:
        #   - For each skill in src, overwrite dst/<skill>/ (so updates propagate)
        #   - NEVER delete unknown entries in dst/ (framework built-ins and runtime-installed
        #     skills must survive). If you want to drop a skill, delete it manually from dst
        #     or add a stub SKILL.md with `name: __disabled__` later.
        # `shared_target: true` in manifest is informational only (kept for documentation);
        # behavior is identical either way.
        foreach ($skillName in $skills.Keys) {
            $target = Join-Path $dst $skillName
            Remove-DirRobust $target
            Copy-SkillTree $skills[$skillName] $target
            Write-Log "[$name] installed: $skillName"
        }

        Write-Log "[$name] OK"
    } catch {
        Write-Log "[$name] FAILED: $($_.Exception.Message)"
    }
}

# --- plugins -----------------------------------------------------------------

foreach ($pp in $cfg.plugins.PSObject.Properties) {
    $name = $pp.Name
    $def  = $pp.Value

    try {
        $src = Join-Path $Repo $def.src
        $dst = Expand-PathVar $def.dst

        if (-not (Test-Path -LiteralPath $src)) {
            Write-Log "[plugin:$name] no source dir ($src), skipping"
            continue
        }

        New-Item -ItemType Directory -Path $dst -Force | Out-Null

        $count = 0
        Get-ChildItem -LiteralPath $src -Directory |
            ForEach-Object {
                $target = Join-Path $dst $_.Name
                Remove-DirRobust $target
                Copy-Item -Path $_.FullName -Destination $target -Recurse -Force
                Write-Log "[plugin:$name] staged: $($_.Name)"
                $count++
            }

        if ($count -eq 0) { Write-Log "[plugin:$name] OK (no marketplaces staged)" }
        else { Write-Log "[plugin:$name] OK ($count marketplace(s))" }
    } catch {
        Write-Log "[plugin:$name] FAILED: $($_.Exception.Message)"
    }
}

Write-Log "===== install.ps1 END ====="
