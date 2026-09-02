@echo off
setlocal
py "%~dp0..\scripts\run_level.py" N10 --windowed
exit /b %ERRORLEVEL%
