"""
main.py: Unified entry point for Code to PDF Application.
On Desktop: Runs PyQt6 Desktop GUI.
On Mobile (Android / Kivy environment / --mobile flag): Runs Kivy Touch Mobile GUI.
"""

from pathlib import Path
import os
import sys

# Ensure src/ is on python search path
sys.path.insert(0, str(Path(__file__).parent / "src"))

IS_ANDROID = "ANDROID_ARGUMENT" in os.environ or "PYTHON_SERVICE_ARGUMENT" in os.environ or "KIVY_BUILD" in os.environ


def run_mobile_app():
    """Launches Kivy Touch Mobile GUI."""
    try:
        from mobile_gui import CodeToPDFMobileApp
        CodeToPDFMobileApp().run()
    except Exception as e:
        print(f"Error starting Mobile GUI: {e}")
        sys.exit(1)


def run_desktop_app():
    """Launches PyQt6 Desktop GUI."""
    from gui import main as gui_main
    gui_main()


if __name__ == "__main__":
    if IS_ANDROID or "--mobile" in sys.argv:
        run_mobile_app()
    else:
        try:
            run_desktop_app()
        except ImportError:
            # Fallback to mobile GUI if PyQt6 is not installed
            run_mobile_app()
