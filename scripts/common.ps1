Set-StrictMode -Version Latest
$script:YonaSkillName = 'yona-supplier-catalog'
$script:YonaDefaultOrigin = 'https://github.com/Amthurson/yona-skills.git'

function Invoke-YonaGit {
    param([string]$Directory, [string[]]$GitArguments)
    $ErrorActionPreference = 'Continue'
    $taskPrefix = if ($Directory) { @('-C', $Directory) } else { @() }
    if ($Directory -and (Get-Variable -Name YonaTrustedRepository -Scope Script -ErrorAction SilentlyContinue) -and [IO.Path]::GetFullPath($Directory) -eq $script:YonaTrustedRepository) {
        $taskPrefix = @('-c', ('safe.directory=' + $script:YonaTrustedRepository)) + $taskPrefix
    }
    $taskOutput = @(& git @taskPrefix @GitArguments 2>&1 | ForEach-Object { "$_" })
    if ($LASTEXITCODE -ne 0) {
        $taskExitCode = $LASTEXITCODE
        $taskError = $taskOutput -join "`n"
        $taskReason = 'git_failed'
        if ($taskError -match '(?i)permission denied|access is denied|拒绝访问|权限不足|operation not permitted') { $taskReason = 'permission_denied' }
        elseif ($taskError -match '(?i)dubious ownership|safe.directory') { $taskReason = 'worktree_ownership' }
        elseif ($taskError -match '(?i)index.lock|config.lock|another git process') { $taskReason = 'repository_locked' }
        elseif ($taskError -match '(?i)not a git repository|cannot change to|could not find') { $taskReason = 'repository_unavailable' }
        elseif ($taskError -match '(?i)could not resolve|unable to access|timed out|authentication failed') { $taskReason = 'network_or_remote_access' }
        throw ('Git operation failed: ' + $GitArguments[0] + '; exit=' + $taskExitCode + '; reason=' + $taskReason + '. Existing files retained; raw output withheld.')
    }
    return ($taskOutput -join "`n").Trim()
}

function Enable-YonaRepositoryTrust {
    param([string]$Repository)
    Assert-YonaPlainPath $Repository
    $taskGit = Join-Path $Repository '.git'
    if (-not (Test-Path -LiteralPath $taskGit -PathType Container)) { throw 'Trust requires a normal installed Skill repository, not a linked worktree.' }
    Assert-YonaPlainPath $taskGit
    $taskManifest = Get-Content -LiteralPath (Join-Path $Repository 'skill-release.json') -Raw | ConvertFrom-Json
    if ($taskManifest.skill -ne $script:YonaSkillName -or $taskManifest.schema -ne 1) { throw 'Incompatible installed Skill; trust not enabled.' }
    Assert-YonaOrigin $taskManifest.repository
    $taskOrigin = Invoke-YonaGit $null @('config', '--file', (Join-Path $taskGit 'config'), '--get', 'remote.origin.url')
    if ($taskOrigin -ne $taskManifest.repository) { throw 'Installed origin differs from its release manifest; trust not enabled.' }
    # Applies only to this exact repository and this process, never global Git config.
    $script:YonaTrustedRepository = [IO.Path]::GetFullPath($Repository)
}

function Assert-YonaOrigin {
    param([string]$Origin)
    if ($Origin -match '^git@[A-Za-z0-9.-]+:[A-Za-z0-9_./-]+$') { return }
    $taskUri = $null
    if (-not [Uri]::TryCreate($Origin, [UriKind]::Absolute, [ref]$taskUri) -or $taskUri.Scheme -ne 'https' -or $taskUri.UserInfo -or $taskUri.Query -or $taskUri.Fragment -or -not $taskUri.Host) {
        throw 'Use an HTTPS or git@host:path repository URL without embedded credentials.'
    }
}

function Assert-YonaPlainPath {
    param([string]$Path)
    $taskCurrent = [IO.Path]::GetFullPath($Path)
    while ($taskCurrent) {
        if (Test-Path -LiteralPath $taskCurrent) {
            $taskItem = Get-Item -LiteralPath $taskCurrent -Force
            if ($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked installation or state directories require manual review.' }
        }
        $taskParent = [IO.Path]::GetDirectoryName($taskCurrent)
        if ($taskParent -eq $taskCurrent) { break }
        $taskCurrent = $taskParent
    }
}

function Assert-YonaInside {
    param([string]$Path, [string]$Root)
    $taskAbsolute = [IO.Path]::GetFullPath($Path)
    $taskBase = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if (-not $taskAbsolute.StartsWith($taskBase + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'File operation escaped its intended directory.' }
    Assert-YonaPlainPath $taskAbsolute
}

function Read-YonaRelease {
    param([string]$Repository, [string]$Revision = 'HEAD')
    $taskManifest = (Invoke-YonaGit $Repository @('show', ($Revision + ':skill-release.json'))) | ConvertFrom-Json
    if ($taskManifest.schema -ne 1 -or $taskManifest.skill -ne $script:YonaSkillName -or $taskManifest.version -notmatch '^\d+\.\d+\.\d+$' -or $taskManifest.stableBranch -ne 'main') { throw 'Incompatible YONA Skill release manifest.' }
    $taskSkill = Invoke-YonaGit $Repository @('show', ($Revision + ':SKILL.md'))
    if ($taskSkill -notmatch '(?m)^name: yona-supplier-catalog\s*$' -or $taskSkill -notmatch ('(?m)^  version: ' + [regex]::Escape($taskManifest.version) + '\s*$')) { throw 'Skill name or version differs from the release manifest.' }
    $taskTree = Invoke-YonaGit $Repository @('ls-tree', '-r', $Revision)
    if ($taskTree -match '(?m)^120000 ') { throw 'Symlink entries are not accepted in managed Skill releases.' }
    return $taskManifest
}

function Get-YonaStateRoot {
    param([string]$Requested)
    if ($Requested) { return [IO.Path]::GetFullPath($Requested) }
    return Join-Path ([Environment]::GetFolderPath('UserProfile')) 'AppData/Local/YONA/SkillManager'
}

function Assert-YonaPublished {
    param([string]$Repository, [string]$Revision, [object]$Release)
    $taskTag = Invoke-YonaGit $Repository @('rev-parse', ('refs/tags/v' + $Release.version + '^{commit}'))
    $taskTarget = Invoke-YonaGit $Repository @('rev-parse', ($Revision + '^{commit}'))
    if ($taskTag -ne $taskTarget) { throw 'Stable branch is not tagged as the declared release. Current Skill retained until the maintainer publishes it.' }
}

function Write-YonaReceipt {
    param([string]$StateRoot, [object]$Receipt)
    Assert-YonaPlainPath $StateRoot
    New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null
    $taskReceipt = Join-Path $StateRoot ('receipt-' + [Guid]::NewGuid().ToString('N') + '.json')
    Assert-YonaInside $taskReceipt $StateRoot
    $Receipt | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $taskReceipt -Encoding UTF8
    return $taskReceipt
}
