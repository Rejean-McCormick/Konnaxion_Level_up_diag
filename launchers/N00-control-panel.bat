@echo off
setlocal
py "%~dp0..\scripts\run_level.py" N00 --windowed
exit /b %ERRORLEVEL%
