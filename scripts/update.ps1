param([string]$Version, [string]$Origin, [string]$StateRoot, [switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$taskRepository = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
Assert-YonaPlainPath $taskRepository
if (-not (Test-Path -LiteralPath (Join-Path $taskRepository '.git'))) { throw 'Copied Skill: use install.ps1 to create a managed installation first.' }
if (Invoke-YonaGit $taskRepository @('status', '--porcelain', '--untracked-files=all')) { throw 'Local Skill changes found. They are preserved; update from a clean working copy.' }
$taskOld = Read-YonaRelease $taskRepository
$taskOldCommit = Invoke-YonaGit $taskRepository @('rev-parse', 'HEAD')
$taskOldOrigin = Invoke-YonaGit $taskRepository @('config', '--get', 'remote.origin.url')
Assert-YonaOrigin $taskOldOrigin
if ($Version -and $Version -notmatch '^\d+\.\d+\.\d+$') { throw 'Use a released version such as 0.2.0.' }
$taskCandidateRef = $null
if ($Origin) {
    Assert-YonaOrigin $Origin
    $taskCandidateRef = 'refs/yona-skill-source/' + [Guid]::NewGuid().ToString('N')
    $taskSourceRef = if ($Version) { 'refs/tags/v' + $Version } else { 'refs/heads/main' }
    $null = Invoke-YonaGit $taskRepository @('fetch', '--no-tags', $Origin, ($taskSourceRef + ':' + $taskCandidateRef))
    $taskCandidate = Read-YonaRelease $taskRepository $taskCandidateRef
    if ($CheckOnly) { throw 'Source switching and CheckOnly are separate operations.' }
    $null = Invoke-YonaGit $taskRepository @('remote', 'set-url', 'origin', $Origin)
}
$taskChanged = $false
try {
    $null = Invoke-YonaGit $taskRepository @('fetch', '--tags', 'origin', 'main')
    $taskTarget = if ($Version) { 'refs/tags/v' + $Version } else { 'refs/remotes/origin/main' }
    $taskNew = Read-YonaRelease $taskRepository $taskTarget
    Assert-YonaPublished $taskRepository $taskTarget $taskNew
    if ($Version -and $taskNew.version -ne $Version) { throw 'The version tag does not match its release manifest.' }
    if (-not $CheckOnly) {
        $taskBranch = Invoke-YonaGit $taskRepository @('rev-parse', '--abbrev-ref', 'HEAD')
        if ($taskBranch -notin @('main', 'HEAD')) { throw 'A maintainer branch is checked out; no automatic branch change.' }
        if ($Version) { $null = Invoke-YonaGit $taskRepository @('switch', '--detach', $taskTarget) }
        else {
            if ($taskBranch -eq 'HEAD') { $null = Invoke-YonaGit $taskRepository @('switch', 'main') }
            $null = Invoke-YonaGit $taskRepository @('merge', '--ff-only', $taskTarget)
        }
        $taskCurrent = Read-YonaRelease $taskRepository
        if ($taskCurrent.version -ne $taskNew.version) { throw 'Post-update version check failed.' }
        $taskChanged = $taskOldCommit -ne (Invoke-YonaGit $taskRepository @('rev-parse', 'HEAD'))
    }
} catch {
    if (-not (Invoke-YonaGit $taskRepository @('status', '--porcelain'))) { $null = Invoke-YonaGit $taskRepository @('switch', '--detach', $taskOldCommit) }
    if ($Origin) { $null = Invoke-YonaGit $taskRepository @('remote', 'set-url', 'origin', $taskOldOrigin) }
    throw
} finally {
    if ($taskCandidateRef) { $null = Invoke-YonaGit $taskRepository @('update-ref', '-d', $taskCandidateRef) }
}
$taskResult = [ordered]@{ skill = $script:YonaSkillName; oldVersion = $taskOld.version; version = $(if ($CheckOnly) { $taskOld.version } else { $taskNew.version }); availableVersion = $taskNew.version; commit = (Invoke-YonaGit $taskRepository @('rev-parse', 'HEAD')); origin = (Invoke-YonaGit $taskRepository @('config', '--get', 'remote.origin.url')); changed = $taskChanged; checkOnly = [bool]$CheckOnly; serverChanged = $false }
$taskResult.receipt = Write-YonaReceipt (Get-YonaStateRoot $StateRoot) $taskResult
$taskResult | ConvertTo-Json -Depth 10
