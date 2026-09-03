param(
    [Parameter(Mandatory=$true)][string]$LevelUpDiagRoot,
    [string]$KonnaxionRoot = "C:\\mycode\\Konnaxion\\Konnaxion",
    [string]$CapsuleManagerRoot = "C:\\mycode\\Konnaxion\\Konnaxion_Capsule_Manager",
    [string]$CapsuleFile = ""
)
& (Join-Path $PSScriptRoot "CONFIGURE_KONNAXION_LEVELUPDIAG.ps1") -LevelUpDiagRoot $LevelUpDiagRoot -KonnaxionRoot $KonnaxionRoot -CapsuleManagerRoot $CapsuleManagerRoot -CapsuleFile $CapsuleFile
exit $LASTEXITCODE
