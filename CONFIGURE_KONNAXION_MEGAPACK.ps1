param(
    [Parameter(Mandatory=$true)][string]$LevelUpDiagRoot,
    [string]$KonnaxionRoot = "C:\mycode\Konnaxion\Konnaxion",
    [string]$CapsuleManagerRoot = "C:\mycode\Konnaxion\Konnaxion_Capsule_Manager",
    [string]$CapsuleFile = ""
)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path $LevelUpDiagRoot).Path
$Example = Join-Path $Root "levelupdiag.config.example.json"
if (-not (Test-Path $Example)) { throw "Missing $Example" }
$Cfg = Get-Content $Example -Raw | ConvertFrom-Json
$Cfg.target_repo_root = $KonnaxionRoot
$Cfg.konnaxion.capsule_manager_repo = $CapsuleManagerRoot
$Cfg.konnaxion.capsule_file = $CapsuleFile
$Out = Join-Path $Root "levelupdiag.config.local.json"
$Cfg | ConvertTo-Json -Depth 20 | Set-Content -Encoding utf8 $Out
Write-Host "Wrote: $Out"
Write-Host "Konnaxion: $KonnaxionRoot"
Write-Host "Capsule Manager: $CapsuleManagerRoot"
if ($CapsuleFile) { Write-Host "Capsule: $CapsuleFile" }
