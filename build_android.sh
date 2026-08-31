#!/usr/bin/env bash
set -e

echo "==============================================="
echo " Building CodeToPDF Android Package (.apk)"
echo "==============================================="

if ! command -v buildozer &> /dev/null; then
    echo "Installing buildozer and dependencies..."
    pip install buildozer cython
fi

echo "Running buildozer debug build..."
buildozer -v android debug

mkdir -p dist
if ls bin/*.apk 1> /dev/null 2>&1; then
    cp bin/*.apk dist/code-to-pdf-android.apk
    echo "==============================================="
    echo " Build Success: dist/code-to-pdf-android.apk"
    echo "==============================================="
else
    echo "Error: APK package not found in bin/"
    exit 1
fi
