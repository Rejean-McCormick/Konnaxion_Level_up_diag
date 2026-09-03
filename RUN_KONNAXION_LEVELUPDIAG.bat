@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD="
where py >nul 2>nul && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>nul && set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo [LevelUpDiag] Python 3 introuvable dans PATH.
  echo Installe/configure Python puis relance ce fichier.
  echo.
  pause
  exit /b 30
)

echo [LevelUpDiag] Konnaxion - lancement automatique de connection-debug...
%PYTHON_CMD% levelupdiag.py run connection-debug
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [LevelUpDiag] Termine. Resultat disponible dans le repo cible sous .levelupdiag\current\summary.txt
) else (
  echo [LevelUpDiag] Termine avec code %RC%.
  echo Consulte .levelupdiag\current\summary.txt et les resultats de niveaux.
)
echo.
pause
exit /b %RC%
