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
  --onefile \
  main.py

echo "Onefile built: dist/IMU_Monitor"
echo "Note: Gatekeeper may block unsigned binaries. See README-macOS.md."

