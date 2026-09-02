@echo off
setlocal
py "%~dp0..\scripts\run_level.py" N08 --windowed
exit /b %ERRORLEVEL%
