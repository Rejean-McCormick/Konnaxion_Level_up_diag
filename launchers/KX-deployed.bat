@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run deployed
exit /b %ERRORLEVEL%
