@echo off
setlocal
cd /d "%~dp0"
python levelupdiag.py run connection-debug
exit /b %ERRORLEVEL%
