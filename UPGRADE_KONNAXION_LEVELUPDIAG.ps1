param([Parameter(Mandatory=$true)][string]$LevelUpDiagRoot)
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = (Resolve-Path $LevelUpDiagRoot).Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $Target ".levelupdiag-upgrade-backups\konnaxion-v3-$Stamp"
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
$Preserve = Join-Path $Target "levelupdiag.config.local.json"
if (Test-Path $Preserve) { Copy-Item -Force $Preserve (Join-Path $Backup "levelupdiag.config.local.json") }
$Dirs = @("levelupdiag_core","konnaxion_diag","levels","scripts","launchers","docs","schemas","tests")
foreach ($Dir in $Dirs) {
    $Dest = Join-Path $Target $Dir
    if (Test-Path $Dest) { Move-Item -Force $Dest (Join-Path $Backup $Dir) }
    Copy-Item -Recurse -Force (Join-Path $PackRoot $Dir) $Dest
}
foreach ($File in @("levelupdiag.py","levelupdiag_manifest.json","levelupdiag.config.json","levelupdiag.config.example.json","README.md","RUN_KONNAXION_LEVELUPDIAG.bat","RUN_KONNAXION_LEVELUPDIAG.sh",".gitignore",".smartignore")) {
    $Src=Join-Path $PackRoot $File; $Dst=Join-Path $Target $File
    if (Test-Path $Dst) { Copy-Item -Force $Dst (Join-Path $Backup $File) }
    Copy-Item -Force $Src $Dst
}
if (Test-Path (Join-Path $Backup "levelupdiag.config.local.json")) { Copy-Item -Force (Join-Path $Backup "levelupdiag.config.local.json") $Preserve }
Get-ChildItem -Path $Target -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Upgraded Konnaxion LevelUpDiag v3: $Target"
Write-Host "Backup: $Backup"
Write-Host "Existing local config preserved. Old runtime logs are not migrated; next campaign uses current-only evidence."
Write-Host "Run: python levelupdiag.py doctor"
Write-Host "Then: python levelupdiag.py run connection-debug"
