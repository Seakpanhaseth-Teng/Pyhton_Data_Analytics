# Syncs the Obsidian notes staged in docs/obsidian/ into the real vault.
#
# Why this exists: the agent sandbox can read C:\Users\Admin\Documents but
# cannot write to it, so notes are drafted in the repo and copied from there.
# Run this after any session that changes project state.
#
# Usage:
#   powershell -File tools/sync_obsidian.ps1
#   powershell -File tools/sync_obsidian.ps1 -VaultPath "D:\MyVault"

param(
    [string]$VaultPath = (Join-Path $env:USERPROFILE "Documents\Obsidian Vault")
)

$ErrorActionPreference = "Stop"
$source = Join-Path $PSScriptRoot "..\docs\obsidian"

if (-not (Test-Path $VaultPath)) {
    throw "Vault not found: $VaultPath"
}
if (-not (Test-Path $source)) {
    throw "Source not found: $source"
}

$copied = 0
Get-ChildItem -Path $source -Recurse -Filter *.md | ForEach-Object {
    $relative = $_.FullName.Substring((Resolve-Path $source).Path.Length).TrimStart('\')
    $target = Join-Path $VaultPath $relative
    $targetDir = Split-Path $target -Parent

    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }

    # Skip identical files so the sync is quiet on repeat runs.
    if ((Test-Path $target) -and
        ((Get-FileHash $_.FullName).Hash -eq (Get-FileHash $target).Hash)) {
        return
    }

    Copy-Item -Path $_.FullName -Destination $target -Force
    Write-Host "  -> $relative"
    $script:copied++
}

Write-Host "Synced $copied note(s) into $VaultPath"
