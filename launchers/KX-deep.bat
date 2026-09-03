@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run deep
exit /b %ERRORLEVEL%
