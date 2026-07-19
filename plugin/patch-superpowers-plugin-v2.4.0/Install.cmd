@echo off
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install.ps1" %*
if errorlevel 1 powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install.ps1" %*
