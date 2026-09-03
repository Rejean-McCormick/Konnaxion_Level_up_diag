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
$Cfg | ConvertTo-Json -Depth 30 | Set-Content -Encoding utf8 $Out
Write-Host "Wrote: $Out"
Write-Host "Konnaxion: $KonnaxionRoot"
Write-Host "Capsule Manager: $CapsuleManagerRoot"
Write-Host "Primary sequence: N00 -> N01 -> N02 -> N03 -> N04 -> N05 -> N06 -> N11"
