@echo off
cd /d "%~dp0"
python app.py --browser
if errorlevel 1 pause
