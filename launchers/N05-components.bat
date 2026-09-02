@echo off
setlocal
py "%~dp0..\scripts\run_level.py" N05 --windowed
exit /b %ERRORLEVEL%
