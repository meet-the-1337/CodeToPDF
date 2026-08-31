#!/usr/bin/env bash
set -e

echo "==============================================="
echo " Building CodeToPDF Android Package (.apk)"
echo "==============================================="

if ! command -v buildozer &> /dev/null; then
    echo "Installing buildozer and dependencies..."
    pip install buildozer cython
fi

echo "Patching python-for-android ReportLab recipe URL to avoid Cloudflare 403 blocks..."
python3 -c "
import os, glob
target_url = 'https://files.pythonhosted.org/packages/4a/51/dbe28534ae12c852f61be91f039f343305fd1f34f1c66b8de75afae7a525/reportlab-5.0.1.tar.gz'
search_paths = glob.glob('/opt/hostedtoolcache/Python/*/x64/lib/python*/site-packages/pythonforandroid/recipes/reportlab/__init__.py') + \
               glob.glob('/home/runner/.local/lib/python*/site-packages/pythonforandroid/recipes/reportlab/__init__.py') + \
               glob.glob('/usr/local/lib/python*/dist-packages/pythonforandroid/recipes/reportlab/__init__.py')

for p in search_paths:
    if os.path.exists(p):
        content = open(p).read()
        if 'hg.reportlab.com' in content:
            new_content = content.replace('https://hg.reportlab.com/hg-public/reportlab/archive/{version}.tar.gz', target_url)
            new_content = new_content.replace('https://hg.reportlab.com/hg-public/reportlab/archive', target_url)
            open(p, 'w').write(new_content)
            print(f'Successfully patched p4a reportlab recipe at: {p}')
"

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
