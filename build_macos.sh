#!/usr/bin/env bash
# build_macos.sh - Build standalone macOS app / binary using PyInstaller
set -e

echo "Building Code to PDF standalone app for macOS..."

pip install -q PyQt6 reportlab pygments pyinstaller

pyinstaller --noconfirm --clean --onefile --windowed \
  --name code-to-pdf-macos \
  --hidden-import=pygments.lexers \
  --hidden-import=pygments.styles \
  --hidden-import=reportlab \
  --hidden-import=PyQt6.QtNetwork \
  --add-data "assets/icon.png:assets" \
  src/gui.py

echo "✓ Build complete! Output app: dist/code-to-pdf-macos"
