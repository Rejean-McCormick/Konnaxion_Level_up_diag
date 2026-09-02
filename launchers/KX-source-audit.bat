@echo off
python "%~dp0..\scripts\run_konnaxion.py" source-audit
exit /b %ERRORLEVEL%
