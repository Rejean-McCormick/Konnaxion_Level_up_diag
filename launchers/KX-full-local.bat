@echo off
python "%~dp0..\scripts\run_konnaxion.py" full-local
exit /b %ERRORLEVEL%
