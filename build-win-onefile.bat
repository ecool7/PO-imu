@echo off
setlocal enableextensions enabledelayedexpansion

REM Create and activate venv if missing
if not exist venv (
    py -3 -m venv venv
)
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
pip install -r requirements-win.txt

REM Clean previous builds
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist
if exist main.spec del /Q main.spec

REM Build as onefile
pyinstaller --noconfirm --clean ^
  --name IMU_Monitor ^
  --windowed ^
  --onefile ^
  main.py

echo.
echo Onefile build finished. Executable located in dist\IMU_Monitor.exe
pause

endlocal

