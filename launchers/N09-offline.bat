@echo off
setlocal
py "%~dp0..\scripts\run_level.py" N09 --windowed
exit /b %ERRORLEVEL%
