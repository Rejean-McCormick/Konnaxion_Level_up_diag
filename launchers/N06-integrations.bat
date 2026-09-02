@echo off
setlocal
py "%~dp0..\scripts\run_level.py" N06 --windowed
exit /b %ERRORLEVEL%
