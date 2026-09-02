@echo off
setlocal
py "%~dp0..\scripts\run_level.py" N02 --windowed
exit /b %ERRORLEVEL%
