@echo off
setlocal
cd /d "%~dp0.."
py "%CD%\scriptsun_level.py" N14
if errorlevel 1 pause
