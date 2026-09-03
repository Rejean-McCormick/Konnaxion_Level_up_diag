@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run source-audit
exit /b %ERRORLEVEL%
