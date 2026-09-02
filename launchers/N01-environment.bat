@echo off
setlocal
py "%~dp0..\scripts\run_level.py" N01 --windowed
exit /b %ERRORLEVEL%
