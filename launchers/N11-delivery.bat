@echo off
setlocal
py "%~dp0..\scripts\run_level.py" N11 --windowed
exit /b %ERRORLEVEL%
