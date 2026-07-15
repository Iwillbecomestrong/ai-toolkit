#Requires -Version 5.1
<#
.SYNOPSIS
    Copies skills/plugins from G:\ai-toolkit\ into all installed AI framework directories.

.DESCRIPTION
    3-tier skill source (hardcoded; manifest.json's skills_src is informational only):
      - skills/             self-designed, always installed
      - vendor/active/      marketplace, frequently used, always installed
      - vendor/archived/    marketplace, rarely used, opt-in via -IncludeArchived

    Idempotent. Safe to re-run. Per-framework try/catch — one framework's failure
    does not abort the others. Logs to G:\ai-toolkit\install.log.

.PARAMETER RepoRoot
    Path to the central skills repo. Defaults to the directory containing this script.

.PARAMETER IncludeArchived
    Also scan vendor/archived/ in addition to skills/ + vendor/active/.
    Default OFF — keep archived/ untouched so it doesn't bloat framework installs.

.PARAMETER OnlyArchived <name>
    Install ONLY one archived skill (by name) and skip everything else.
    Useful to try a single archived skill before promoting it to active/.
    Implies -IncludeArchived for that one skill.

.PARAMETER Framework <name>
    Restrict installation to a single framework (must match manifest.json key).
    Default: all non-skipped frameworks.

.PARAMETER DryRun
    Print what would be installed, do not modify dst. Safe to combine with others.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\install-all.ps1
    powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\install-all.ps1 -IncludeArchived
    powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\install-all.ps1 -OnlyArchived pptx
    powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\install-all.ps1 -DryRun
    powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\install-all.ps1 -Framework claude -DryRun
#>

[CmdletBinding()]
param(
    [string]$RepoRoot,
    [switch]$IncludeArchived,
    [string]$OnlyArchived,
    [string]$Framework,
    [switch]$DryRun
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

# -OnlyArchived implies -IncludeArchived (we need to read from that tier)
if ($OnlyArchived) { $IncludeArchived = $true }

# --- helpers -----------------------------------------------------------------

function Write-Log {
    param([string]$Message, [string]$Level = 'info')
    $stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $prefix = if ($DryRun) { '[DRY] ' } else { '' }
    $line   = "$stamp  $prefix$Message"
    Write-Host $line
    if (-not $DryRun) {
        Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
    }
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
    $expanded = $expanded -replace '%APPDATA%', $env:APPDATA
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
        Write-Log "  WARN: could not remove $Path -- $($_.Exception.Message)" 'warn'
    }
}

function Copy-SkillTree {
    param([string]$SourceDir, [string]$DestinationDir)
    if ($DryRun) { return }
    New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
    Copy-Item -Path (Join-Path $SourceDir '*') -Destination $DestinationDir -Recurse -Force -Exclude '.git','.gitmodules','install.log'
}

# Collect all skills from the requested tiers, deduped by name (skills/ wins).
function Get-SkillSources {
    $tiers = @(
        @{ Path = (Join-Path $Repo 'skills');           Label = 'skills' }
        @{ Path = (Join-Path (Join-Path $Repo 'vendor') 'active');   Label = 'vendor/active' }
    )
    if ($IncludeArchived) {
        $tiers += @{ Path = (Join-Path (Join-Path $Repo 'vendor') 'archived'); Label = 'vendor/archived' }
    }

    $map = [ordered]@{}
    foreach ($tier in $tiers) {
        if (-not (Test-Path -LiteralPath $tier.Path)) { continue }
        Get-ChildItem -LiteralPath $tier.Path -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            # Skip shared directories (prefixed with _) — these are skill dependencies
            if ($_.Name.StartsWith('_')) { return }
            # Skip dot-prefixed dirs (hidden / runtime / git worktrees — not skills, would pollute dst)
            if ($_.Name.StartsWith('.')) { return }
            # Skip brace-prefixed dirs (template placeholders like {PROJECT_DIR})
            if ($_.Name.StartsWith('{')) { return }
            # Skip package directories containing Install.ps1 (e.g. evolving-used-skills-package, superpowers-*-overlay-v*)
            if (Test-Path -LiteralPath (Join-Path $_.FullName 'Install.ps1')) { return }
            # Skip bundle/package dirs (contain BUNDLE-* or README.md but no SKILL.md at root)
            if (-not (Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md'))) { return }
            # -OnlyArchived: keep only the named skill, and only from archived tier
            if ($OnlyArchived) {
                if ($_.Name -ne $OnlyArchived) { return }
                if ($tier.Label -ne 'vendor/archived') { return }
            }
            if (-not $map.Contains($_.Name)) {
                $map[$_.Name] = @{ Path = $_.FullName; Tier = $tier.Label }
            }
        }
    }
    return $map
}

# --- bootstrap ---------------------------------------------------------------

$null = New-Item -ItemType File -Path $LogFile -Force
Write-Log "===== install-all.ps1 START (user=$env:USERNAME, repo=$Repo) ====="
Write-Log "Flags: IncludeArchived=$IncludeArchived OnlyArchived=$OnlyArchived Framework=$Framework DryRun=$DryRun"

if (-not (Test-Path -LiteralPath $Manifest)) {
    Write-Log "FATAL: manifest.json not found at $Manifest" 'fatal'
    exit 1
}

try {
    $cfg = Get-Content -Raw -LiteralPath $Manifest | ConvertFrom-Json
} catch {
    Write-Log "FATAL: manifest.json is not valid JSON -- $($_.Exception.Message)" 'fatal'
    exit 1
}

# --- main loop over frameworks ----------------------------------------------

$skillMap = Get-SkillSources
Write-Log "Discovered $($skillMap.Count) skill(s) to install"

foreach ($fw in $cfg.frameworks.PSObject.Properties) {
    $name = $fw.Name
    $def  = $fw.Value

    if ($Framework -and $Framework -ne $name) { continue }
    if ($def.PSObject.Properties.Name -contains 'skip' -and $def.skip) {
        Write-Log "[$name] SKIPPED -- $($def.reason)"
        continue
    }

    try {
        $dst = Expand-PathVar $def.skills_dst
        # $src is no longer used for skill scan (we use $skillMap) but keep for logging
        $src = Join-Path $Repo $def.skills_src

        if ($skillMap.Count -eq 0) {
            Write-Log "[$name] no skills to install, skipping dst prep"
            continue
        }

        New-Item -ItemType Directory -Path $dst -Force | Out-Null

        # Install _shared/ dependency directory (shared core for auto-dev, multi-agent-core, etc.)
        $sharedSrc = Join-Path (Join-Path $Repo 'skills') '_shared'
        $sharedDst = Join-Path $dst '_shared'
        if (Test-Path -LiteralPath $sharedSrc) {
            if ($DryRun) {
                Write-Log "[$name] would install shared: _shared/"
            } else {
                Remove-DirRobust $sharedDst
                Copy-SkillTree $sharedSrc $sharedDst
                Write-Log "[$name] installed shared: _shared/"
            }
        }

        # Additive model for ALL frameworks:
        #   - For each skill in src, overwrite dst/<skill>/ (so updates propagate)
        #   - NEVER delete unknown entries in dst/ (framework built-ins and runtime-installed
        #     skills must survive). If you want to drop a skill, delete it manually from dst
        #     or promote a stub SKILL.md with `name: __disabled__`.
        foreach ($skillName in $skillMap.Keys) {
            $entry   = $skillMap[$skillName]
            $target  = Join-Path $dst $skillName
            $srcPath = $entry.Path
            $tier    = $entry.Tier
            if ($DryRun) {
                Write-Log "[$name] would install: $skillName (from $tier)"
            } else {
                Remove-DirRobust $target
                Copy-SkillTree $srcPath $target
                Write-Log "[$name] installed: $skillName (from $tier)"
            }
        }

        # For shared_target frameworks, ensure ~/.claude/skills/ has junctions
        # because Claude Code scans ~/.claude/skills/ for slash commands,
        # not ~/.agents/skills/ (even though they're conceptually shared).
        if ($def.shared_target -and (-not $DryRun)) {
            $claudeSkillsDir = Expand-PathVar "~/.claude/skills"
            foreach ($skillName in $skillMap.Keys) {
                $junctionPath = Join-Path $claudeSkillsDir $skillName
                if (-not (Test-Path -LiteralPath $junctionPath)) {
                    try {
                        New-Item -ItemType Junction -Path $junctionPath -Target (Join-Path $dst $skillName) -Force | Out-Null
                        Write-Log "[$name] junction: $skillName -> ~/.claude/skills/"
                    } catch {
                        Write-Log "[$name] WARN: junction failed for $skillName -- $($_.Exception.Message)" 'warn'
                    }
                }
            }
        }

        Write-Log "[$name] OK"
    } catch {
        Write-Log "[$name] FAILED: $($_.Exception.Message)" 'err'
    }
}

# --- plugins (unchanged) -----------------------------------------------------

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
                if ($DryRun) {
                    Write-Log "[plugin:$name] would stage: $($_.Name)"
                } else {
                    Remove-DirRobust $target
                    Copy-Item -Path $_.FullName -Destination $target -Recurse -Force
                    Write-Log "[plugin:$name] staged: $($_.Name)"
                }
                $count++
            }

        if ($count -eq 0) { Write-Log "[plugin:$name] OK (no marketplaces staged)" }
        elseif ($DryRun)  { Write-Log "[plugin:$name] DRY: would stage $count marketplace(s)" }
        else              { Write-Log "[plugin:$name] OK ($count marketplace(s))" }
    } catch {
        Write-Log "[plugin:$name] FAILED: $($_.Exception.Message)" 'err'
    }
}

Write-Log "===== install-all.ps1 END ====="
