@echo off
REM build_windows.bat - Build standalone Windows executable (.exe) using PyInstaller

echo Building Code to PDF standalone binary for Windows...

pip install PyQt6 reportlab pygments pyinstaller

pyinstaller --noconfirm --clean --onefile --windowed ^
  --name code-to-pdf-windows ^
  --hidden-import=pygments.lexers ^
  --hidden-import=pygments.styles ^
  --hidden-import=reportlab ^
  --hidden-import=PyQt6.QtNetwork ^
  --add-data "assets/icon.png;assets" ^
  src/gui.py

echo Build complete! Output executable: dist\code-to-pdf-windows.exe
pause
