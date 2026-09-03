param([Parameter(Mandatory=$true)][string]$LevelUpDiagRoot)
& (Join-Path $PSScriptRoot "UPGRADE_KONNAXION_LEVELUPDIAG.ps1") -LevelUpDiagRoot $LevelUpDiagRoot
exit $LASTEXITCODE
