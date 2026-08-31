#!/usr/bin/env bash
# build_linux.sh - Build standalone Linux binary using PyInstaller
set -e

echo "Building Code to PDF standalone binary for Linux..."

pyinstaller --noconfirm --clean --onefile --windowed \
  --name code-to-pdf \
  --hidden-import=pygments.lexers \
  --hidden-import=pygments.styles \
  --hidden-import=reportlab \
  --hidden-import=PyQt6.QtNetwork \
  --add-data "assets/icon.png:assets" \
  src/gui.py

echo "✓ Build complete! Output executable: dist/code-to-pdf"
