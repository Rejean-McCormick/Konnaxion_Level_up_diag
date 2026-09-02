@echo off
python "%~dp0..\scripts\run_konnaxion.py" auth-debug
exit /b %ERRORLEVEL%
