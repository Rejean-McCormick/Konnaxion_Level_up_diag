@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run capsule-local
exit /b %ERRORLEVEL%
