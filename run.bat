@echo off
REM Kartly -- security training target. Localhost only.
cd /d "%~dp0"
python -m pip install -r requirements.txt >nul 2>&1
python app.py
