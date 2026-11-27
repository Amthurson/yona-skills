Set-StrictMode -Version Latest
$script:YonaSkillName = 'yona-supplier-catalog'
$script:YonaDefaultOrigin = 'https://github.com/Amthurson/yona-skills.git'

function Invoke-YonaGit {
    param([string]$Directory, [string[]]$GitArguments)
    $ErrorActionPreference = 'Continue'
    $taskPrefix = if ($Directory) { @('-C', $Directory) } else { @() }
    $taskOutput = @(& git @taskPrefix @GitArguments 2>&1 | ForEach-Object { "$_" })
    if ($LASTEXITCODE -ne 0) { throw ('Git operation failed: ' + $GitArguments[0] + '. Existing files are retained; check Git access or local history.') }
    return ($taskOutput -join "`n").Trim()
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
