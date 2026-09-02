@echo off
setlocal
py "%~dp0..\scripts\run_level.py" %*
exit /b %ERRORLEVEL%
