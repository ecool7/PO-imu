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

REM Build with PyInstaller
pyinstaller --noconfirm --clean ^
  --name IMU_Monitor ^
  --windowed ^
  --add-data "venv/Lib/site-packages/PyQt5/Qt5/bin/;PyQt5/Qt5/bin/" ^
  --add-data "venv/Lib/site-packages/PyQt5/Qt5/plugins/platforms/;PyQt5/Qt5/plugins/platforms/" ^
  --add-data "venv/Lib/site-packages/PyQt5/Qt5/plugins/styles/;PyQt5/Qt5/plugins/styles/" ^
  main.py

echo.
echo Build finished. Executable located in dist\IMU_Monitor\IMU_Monitor.exe
pause

endlocal

