@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run backend
exit /b %ERRORLEVEL%
