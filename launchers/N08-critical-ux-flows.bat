@echo off
setlocal
cd /d "%~dp0.."
py "%CD%\scriptsun_level.py" N08
if errorlevel 1 pause
