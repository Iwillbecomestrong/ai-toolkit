param(
  [string]$ClaudeHome = "$HOME\.claude",
  [switch]$CleanLegacyOverlay
)
$ErrorActionPreference = 'Stop'
$Version = '2.4.0'
$DefaultTargetHint = "$HOME\.claude\skills\patch-superpowers"
$Source = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsRoot = Join-Path $ClaudeHome 'skills'
$Target = Join-Path $SkillsRoot 'patch-superpowers'
$BackupRoot = Join-Path $ClaudeHome ('.patch-superpowers-backups\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $SkillsRoot | Out-Null
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
if (Test-Path $Target) { Copy-Item $Target (Join-Path $BackupRoot 'patch-superpowers') -Recurse -Force; Remove-Item $Target -Recurse -Force }
Copy-Item $Source $Target -Recurse -Force

# 原版 Superpowers 必须保留。这里只记录路径，不删除。
$original = @(
  (Join-Path $SkillsRoot 'brainstorming'),
  (Join-Path $SkillsRoot 'writing-plans'),
  (Join-Path $SkillsRoot 'using-superpowers')
)

if ($CleanLegacyOverlay) {
  $legacySkills = @('parallel-dag-development','dag-worktree-development','challenging-plans','sol-final-audit','_dag-runtime')
  foreach ($name in $legacySkills) {
    $p = Join-Path $SkillsRoot $name
    if (Test-Path $p) { Copy-Item $p (Join-Path $BackupRoot ('legacy-skill-' + $name)) -Recurse -Force; Remove-Item $p -Recurse -Force }
  }
  $agentsRoot = Join-Path $ClaudeHome 'agents'
  $legacyAgents = @('superpowers-investigator.md','superpowers-plan-challenger.md','superpowers-tdd-implementer.md','superpowers-integration-operator.md','superpowers-task-reviewer.md','superpowers-integration-reviewer.md')
  foreach ($name in $legacyAgents) {
    $p = Join-Path $agentsRoot $name
    if (Test-Path $p) { Copy-Item $p (Join-Path $BackupRoot ('legacy-agent-' + $name)) -Force; Remove-Item $p -Force }
  }
}
python (Join-Path $Target 'Verify-Package.py') --source $Target
Write-Output 'VERIFY_OK'
Write-Output 'INSTALL_OK'
Write-Output ('PACKAGE_VERSION=' + $Version)
Write-Output ('PLUGIN_PATH=' + $Target)
Write-Output ('BACKUP_PATH=' + $BackupRoot)
