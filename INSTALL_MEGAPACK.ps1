param(
    [Parameter(Mandatory=$true)][string]$LevelUpDiagRoot
)
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = (Resolve-Path $LevelUpDiagRoot).Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $Target ".levelupdiag-pack-backups\konnaxion-megapack-$Stamp"
New-Item -ItemType Directory -Force -Path $Backup | Out-Null

$Replace = @("levelupdiag_manifest.json", "levelupdiag.config.example.json", "tests\test_manifest.py")
foreach ($Rel in $Replace) {
    $Dest = Join-Path $Target $Rel
    if (Test-Path $Dest) {
        $B = Join-Path $Backup $Rel
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $B) | Out-Null
        Copy-Item -Force $Dest $B
    }
    Copy-Item -Force (Join-Path $PackRoot $Rel) $Dest
}

foreach ($Dir in @("konnaxion_diag", "levels", "scripts", "launchers", "docs", "tests")) {
    $Source = Join-Path $PackRoot $Dir
    $Dest = Join-Path $Target $Dir
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    Copy-Item -Recurse -Force (Join-Path $Source "*") $Dest
}

Write-Host "Installed Konnaxion Mega Diagnostic Pack into: $Target"
Write-Host "Backup of replaced files: $Backup"
Write-Host "Next: copy levelupdiag.config.example.json to levelupdiag.config.local.json and set local paths."
Write-Host "Then run: python scripts\run_konnaxion.py connection-debug"
