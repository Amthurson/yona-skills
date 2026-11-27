param([string]$Destination, [string]$Origin = 'https://github.com/Amthurson/yona-skills.git', [string]$StateRoot)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
Assert-YonaOrigin $Origin
if (-not $Destination) { $Destination = Join-Path ([Environment]::GetFolderPath('UserProfile')) '.agents/skills/yona-supplier-catalog' }
$taskDestination = [IO.Path]::GetFullPath($Destination)
if ([IO.Path]::GetFileName($taskDestination) -ne $script:YonaSkillName) { throw 'Destination must be the yona-supplier-catalog directory.' }
Assert-YonaPlainPath $taskDestination
$taskState = Get-YonaStateRoot $StateRoot
Assert-YonaPlainPath $taskState
if ($taskState.StartsWith($taskDestination, [StringComparison]::OrdinalIgnoreCase)) { throw 'Backups must stay outside the installed Skill.' }
if ($taskState -match '(?i)[\\/]\.(agents|codex)[\\/]skills([\\/]|$)') { throw 'Backups must stay outside every Skill discovery directory.' }
if (Test-Path -LiteralPath (Join-Path $taskDestination '.git')) { throw 'This Skill is already Git-managed. Use its update.ps1.' }
if (Test-Path -LiteralPath $taskDestination) {
    $taskOldSkill = Join-Path $taskDestination 'SKILL.md'
    if (-not (Test-Path -LiteralPath $taskOldSkill) -or (Get-Content -LiteralPath $taskOldSkill -Raw) -notmatch '(?m)^name: yona-supplier-catalog\s*$') { throw 'Existing destination is not the expected YONA Skill; preserved.' }
}
$taskRun = Join-Path $taskState ('install-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskRun -Force | Out-Null
$taskClone = Join-Path $taskRun 'verified-clone'
$null = Invoke-YonaGit '' @('clone', '--single-branch', '--branch', 'main', $Origin, $taskClone)
$taskRelease = Read-YonaRelease $taskClone
Assert-YonaPublished $taskClone 'HEAD' $taskRelease
$taskCommit = Invoke-YonaGit $taskClone @('rev-parse', 'HEAD')
$taskBackup = Join-Path $taskRun 'previous-skill'
$taskParent = [IO.Path]::GetDirectoryName($taskDestination)
New-Item -ItemType Directory -Path $taskParent -Force | Out-Null
Assert-YonaInside $taskClone $taskRun
Assert-YonaInside $taskBackup $taskRun
Assert-YonaInside $taskDestination $taskParent
$taskHadPrevious = Test-Path -LiteralPath $taskDestination
try {
    if ($taskHadPrevious) { Move-Item -LiteralPath $taskDestination -Destination $taskBackup }
    Move-Item -LiteralPath $taskClone -Destination $taskDestination
} catch {
    if ((Test-Path -LiteralPath $taskBackup) -and -not (Test-Path -LiteralPath $taskDestination)) { Move-Item -LiteralPath $taskBackup -Destination $taskDestination }
    throw
}
$taskResult = [ordered]@{ installed = $true; skill = $script:YonaSkillName; version = $taskRelease.version; commit = $taskCommit; origin = $Origin; destination = $taskDestination; previousSkillRetained = [bool]$taskHadPrevious; backup = $(if ($taskHadPrevious) { $taskBackup } else { $null }); serverChanged = $false }
$taskResult.receipt = Write-YonaReceipt $taskState $taskResult
$taskResult | ConvertTo-Json -Depth 10
