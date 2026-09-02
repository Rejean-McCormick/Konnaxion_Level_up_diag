@echo off
setlocal
start "" /D "%~dp0" pyw "%~dp0levelupdiag_wrapper.pyw"
exit /b %ERRORLEVEL%
