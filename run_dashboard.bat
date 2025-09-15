@echo off
cd /d "%~dp0"
call pm2aqi_env\Scripts\activate.bat
python dashboard.py
pause