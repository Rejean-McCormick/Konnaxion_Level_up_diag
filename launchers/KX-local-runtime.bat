@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run local-runtime
exit /b %ERRORLEVEL%
