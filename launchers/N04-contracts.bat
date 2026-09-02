@echo off
setlocal
py "%~dp0..\scripts\run_level.py" N04 --windowed
exit /b %ERRORLEVEL%
