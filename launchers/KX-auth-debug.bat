@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run auth-debug
exit /b %ERRORLEVEL%
