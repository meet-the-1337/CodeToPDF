#!/usr/bin/env bash
# build_deb.sh - Build Debian (.deb) package for Code to PDF
set -e

VERSION="1.0.0"
PACKAGE_NAME="code-to-pdf"
ARCH="amd64"
DEB_FILE="${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/debpkg"

echo "Building Debian package: ${DEB_FILE}..."

# Ensure standalone Linux binary exists
if [ ! -f "${SCRIPT_DIR}/dist/code-to-pdf" ]; then
    echo "Executable dist/code-to-pdf not found! Building first..."
    "${SCRIPT_DIR}/build_linux.sh"
fi

# Clean previous build directory
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/local/bin"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/256x256/apps"

# Copy binary
cp "${SCRIPT_DIR}/dist/code-to-pdf" "${BUILD_DIR}/usr/local/bin/code-to-pdf"
chmod +x "${BUILD_DIR}/usr/local/bin/code-to-pdf"

# Copy Icon
if [ -f "${SCRIPT_DIR}/assets/icon.png" ]; then
    cp "${SCRIPT_DIR}/assets/icon.png" "${BUILD_DIR}/usr/share/icons/hicolor/256x256/apps/code-to-pdf.png"
fi

# Copy Desktop Launcher
cat << 'EOF' > "${BUILD_DIR}/usr/share/applications/code-to-pdf.desktop"
[Desktop Entry]
Name=Code to PDF
Comment=Convert source code and text into styled PDFs
Exec=/usr/local/bin/code-to-pdf
Icon=code-to-pdf
Type=Application
Terminal=false
Categories=Utility;Development;
EOF
chmod 644 "${BUILD_DIR}/usr/share/applications/code-to-pdf.desktop"

# Write DEBIAN/control
cat << EOF > "${BUILD_DIR}/DEBIAN/control"
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: meet-the-1337 <msinghal1_be24@thapar.edu>
Description: High-performance local-first Code to PDF Converter
 Convert source code files (.py, .c, .cpp, .java, .js, .txt) or pasted text into styled, syntax-highlighted PDFs.
EOF

# Write DEBIAN/postinst
cat << 'EOF' > "${BUILD_DIR}/DEBIAN/postinst"
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"

if command -v dpkg-deb >/dev/null 2>&1; then
    dpkg-deb --build "${BUILD_DIR}" "${SCRIPT_DIR}/${DEB_FILE}"
    rm -rf "${BUILD_DIR}"
    echo "========================================================"
    echo "✓ Debian package build complete: ${DEB_FILE}"
    echo "Install with: sudo apt install ./${DEB_FILE}"
    echo "========================================================"
else
    echo "⚠️ dpkg-deb not found on host (normal for Arch/macOS/Windows). Package structure prepared in debpkg/."
fi
