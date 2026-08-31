#!/usr/bin/env bash
# build_appimage.sh - Build portable Linux AppImage for Code to PDF
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/AppDir"
APPIMAGE_OUTPUT="${SCRIPT_DIR}/CodeToPDF-x86_64.AppImage"

echo "Building AppImage package..."

# Ensure standalone Linux binary exists
if [ ! -f "${SCRIPT_DIR}/dist/code-to-pdf" ]; then
    echo "Executable dist/code-to-pdf not found! Building first..."
    "${SCRIPT_DIR}/build_linux.sh"
fi

# Clean previous AppDir
rm -rf "${APP_DIR}"
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/256x256/apps"

# Copy binary
cp "${SCRIPT_DIR}/dist/code-to-pdf" "${APP_DIR}/usr/bin/code-to-pdf"
chmod +x "${APP_DIR}/usr/bin/code-to-pdf"

# Copy Icon & Desktop file into AppDir root
if [ -f "${SCRIPT_DIR}/assets/icon.png" ]; then
    cp "${SCRIPT_DIR}/assets/icon.png" "${APP_DIR}/code-to-pdf.png"
    cp "${SCRIPT_DIR}/assets/icon.png" "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/code-to-pdf.png"
fi

cat << 'EOF' > "${APP_DIR}/code-to-pdf.desktop"
[Desktop Entry]
Name=Code to PDF
Comment=Convert source code and text into styled PDFs
Exec=code-to-pdf
Icon=code-to-pdf
Type=Application
Terminal=false
Categories=Utility;Development;
EOF
chmod 644 "${APP_DIR}/code-to-pdf.desktop"

# Create AppRun entrypoint
cat << 'EOF' > "${APP_DIR}/AppRun"
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export QT_LOGGING_RULES="*.debug=false;qt.qpa.*=false"
exec "${HERE}/usr/bin/code-to-pdf" "$@"
EOF
chmod +x "${APP_DIR}/AppRun"

# Check appimagetool availability
if command -v appimagetool >/dev/null 2>&1; then
    ARCH=x86_64 appimagetool --appimage-extract-and-run "${APP_DIR}" "${APPIMAGE_OUTPUT}"
    echo "✓ AppImage generated successfully: ${APPIMAGE_OUTPUT}"
else
    echo "⚠️ appimagetool not found on host. AppDir structure prepared in AppDir/."
    echo "Downloading appimagetool in CI runner will package ${APPIMAGE_OUTPUT} automatically."
fi
