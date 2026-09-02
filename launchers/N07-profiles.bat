@echo off
setlocal
py "%~dp0..\scripts\run_level.py" N07 --windowed
exit /b %ERRORLEVEL%
