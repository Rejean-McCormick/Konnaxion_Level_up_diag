@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run full
exit /b %ERRORLEVEL%
