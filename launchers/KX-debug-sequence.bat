@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run-sequence recommended-debug
exit /b %ERRORLEVEL%
