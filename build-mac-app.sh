#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python3 -m venv venv || true
source venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements-macos.txt

rm -rf build dist main.spec || true

pyinstaller \
  --noconfirm --clean \
  --name IMU_Monitor \
  --windowed \
  --osx-bundle-identifier com.example.imu.monitor \
  main.py

echo "App built: dist/IMU_Monitor.app"
echo "To zip for sending:"
echo "  ditto -c -k --sequesterRsrc --keepParent dist/IMU_Monitor.app IMU_Monitor-mac.zip"

