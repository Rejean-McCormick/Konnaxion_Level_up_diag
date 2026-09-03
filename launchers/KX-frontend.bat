@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run frontend
exit /b %ERRORLEVEL%
