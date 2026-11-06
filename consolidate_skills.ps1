$ErrorActionPreference = 'Stop'
$legacySkillsRoot = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE '.codex/skills'))
$canonicalSkillsRoot = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE '.agents/skills'))
$taskBackupRoot = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE '.codex/skill-install-backups/social-studio'))
New-Item -ItemType Directory -Path $taskBackupRoot -Force | Out-Null
$skillNames = @('hyperframes','hyperframes-cli','hyperframes-registry','media-use','remotion-best-practices')
$records = @()
foreach ($skillName in $skillNames) {
    $source = [IO.Path]::GetFullPath((Join-Path $legacySkillsRoot $skillName))
    $canonical = [IO.Path]::GetFullPath((Join-Path $canonicalSkillsRoot $skillName))
    $backup = [IO.Path]::GetFullPath((Join-Path $taskBackupRoot $skillName))
    if ([IO.Path]::GetDirectoryName($source) -ne $legacySkillsRoot -or
        [IO.Path]::GetDirectoryName($canonical) -ne $canonicalSkillsRoot -or
        [IO.Path]::GetDirectoryName($backup) -ne $taskBackupRoot) { throw 'Skill path escaped the intended roots.' }
    if (Test-Path -LiteralPath $source) {
        if (-not (Test-Path -LiteralPath (Join-Path $canonical 'SKILL.md'))) {
            if (Test-Path -LiteralPath $canonical) { throw "Unexpected incomplete destination: $canonical" }
            Copy-Item -LiteralPath $source -Destination $canonical -Recurse
        }
        if (Test-Path -LiteralPath $backup) { throw "Backup already exists: $backup" }
        Move-Item -LiteralPath $source -Destination $backup
    }
    if (-not (Test-Path -LiteralPath (Join-Path $canonical 'SKILL.md'))) { throw "Canonical skill missing: $canonical" }
    $records += [pscustomobject]@{name=$skillName;canonical=$canonical;backup=$backup}
}
$records | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'skill-consolidation.json') -Encoding utf8
Write-Output 'Official skills consolidated under .agents/skills; legacy copies preserved outside discovery roots.'
