"""
gui.py: PyQt6 Desktop GUI for Code to PDF Converter.
Supports both Upload File and Paste Code/Text input modes.
Includes persistent config, drag-and-drop support, auto-naming, and status error handling.
"""

from pathlib import Path
import json
import os
import sys
import time

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

SERVER_NAME = "code_to_pdf_single_instance_socket"

if sys.platform == "win32":
    CONFIG_DIR = Path(os.getenv("APPDATA", Path.home())) / "code-to-pdf"
else:
    CONFIG_DIR = Path.home() / ".config" / "code-to-pdf"

CONFIG_FILE = CONFIG_DIR / "config.json"


def load_app_config() -> dict:
    """Loads saved app preferences from ~/.config/code-to-pdf/config.json cleanly."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_app_config(cfg: dict):
    """Saves app preferences to ~/.config/code-to-pdf/config.json cleanly."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        pass


class PDFWorkerThread(QThread):
    """Background worker thread to run code_to_pdf_engine without freezing the UI."""

    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(
        self,
        file_path: str | None,
        raw_text: str | None,
        language: str | None,
        output_path: str,
        bg_color: str,
        text_color: str,
        line_number_color: str,
        pygments_style: str,
        font_path: str | None,
        font_name: str | None,
        show_line_numbers: bool,
    ):
        super().__init__()
        self.file_path = file_path
        self.raw_text = raw_text
        self.language = language
        self.output_path = output_path
        self.bg_color = bg_color
        self.text_color = text_color
        self.line_number_color = line_number_color
        self.pygments_style = pygments_style
        self.font_path = font_path
        self.font_name = font_name
        self.show_line_numbers = show_line_numbers

    def run(self):
        try:
            from code_to_pdf_engine import generate_pdf

            generate_pdf(
                file_path=self.file_path,
                raw_text=self.raw_text,
                language=self.language,
                output_path=self.output_path,
                bg_color=self.bg_color,
                text_color=self.text_color,
                line_number_color=self.line_number_color,
                pygments_style=self.pygments_style,
                font_path=self.font_path,
                font_name=self.font_name,
                show_line_numbers=self.show_line_numbers,
            )
            self.finished_signal.emit(str(self.output_path))
        except Exception as e:
            self.error_signal.emit(str(e))


def get_bundle_dir() -> Path:
    """Returns directory path, accounting for PyInstaller sys._MEIPASS bundle directory."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.resolve()


class CodeToPDFWindow(QMainWindow):
    """Main Application Window for Code to PDF Converter."""

    THEMES = {
        "Dark (Monokai)": {
            "style": "monokai",
            "bg": "#1e1e1e",
            "text_color": "#d4d4d4",
            "line_num": "#64748b",
        },
        "Light (GitHub)": {
            "style": "default",
            "bg": "#ffffff",
            "text_color": "#1e293b",
            "line_num": "#94a3b8",
        },
        "Monochrome (B&W)": {
            "style": "bw",
            "bg": "#f8fafc",
            "text_color": "#0f172a",
            "line_num": "#64748b",
        },
        "Dracula": {
            "style": "dracula",
            "bg": "#282a36",
            "text_color": "#f8f8f2",
            "line_num": "#6272a4",
        },
        "Solarized Dark": {
            "style": "solarized-dark",
            "bg": "#002b36",
            "text_color": "#839496",
            "line_num": "#586e75",
        },
    }

    FONTS = [
        ("JetBrains Mono (System)", "/usr/share/fonts/TTF/JetBrainsMonoNerdFontMono-Regular.ttf", "JetBrainsMono"),
        ("Liberation Mono (System)", "/usr/share/fonts/liberation/LiberationMono-Regular.ttf", "LiberationMono"),
        ("Standard Monospace (Courier)", None, "Courier"),
        ("Custom TTF File...", "CUSTOM", "Custom"),
    ]

    LANGUAGES = [
        ("Auto-Detect", "auto"),
        ("Python", "python"),
        ("C / C++", "cpp"),
        ("Java", "java"),
        ("JavaScript", "js"),
        ("HTML / CSS", "html"),
        ("JSON", "json"),
        ("SQL", "sql"),
        ("Plain Text", "text"),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code to PDF Converter")
        self.setAcceptDrops(True)

        self.config_data = load_app_config()
        win_w = self.config_data.get("window_width", 650)
        win_h = self.config_data.get("window_height", 540)
        self.resize(win_w, win_h)
        self.setMinimumSize(540, 480)

        icon_path = get_bundle_dir() / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.current_bg_color = self.config_data.get("bg_color", "#1e1e1e")
        self.custom_font_path = None
        self.worker = None
        self.is_test_mode = False

        self.init_ui()
        self.restore_saved_settings()

    def restore_saved_settings(self):
        """Restores last used settings instantly from loaded config."""
        saved_theme = self.config_data.get("theme")
        if saved_theme in self.THEMES:
            self.theme_combo.setCurrentText(saved_theme)

        font_idx = self.config_data.get("font_index", 0)
        if 0 <= font_idx < len(self.FONTS):
            self.font_combo.setCurrentIndex(font_idx)

        last_tab = self.config_data.get("last_tab_index", 0)
        if 0 <= last_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(last_tab)

        show_lines = self.config_data.get("show_line_numbers", True)
        self.line_num_checkbox.setChecked(show_lines)

    def save_current_config(self):
        """Saves current window state and preferences to config.json."""
        self.config_data.update({
            "theme": self.theme_combo.currentText(),
            "font_index": self.font_combo.currentIndex(),
            "bg_color": self.current_bg_color,
            "show_line_numbers": self.line_num_checkbox.isChecked(),
            "last_tab_index": self.tab_widget.currentIndex(),
            "window_width": self.width(),
            "window_height": self.height(),
        })
        save_app_config(self.config_data)

    def closeEvent(self, event):
        """Saves active settings to config.json upon window close."""
        self.save_current_config()
        super().closeEvent(event)

    def dragEnterEvent(self, event):
        """Accepts file drag operations into main window."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Loads dropped source file into application."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path and Path(file_path).is_file():
                self.tab_widget.setCurrentIndex(0)
                self.file_path_edit.setText(file_path)
                self.status_label.setText(f"Status: Selected {Path(file_path).name}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header Banner
        header_layout = QVBoxLayout()
        title_label = QLabel("Code to PDF Converter")
        title_label.setObjectName("TitleLabel")
        title_label.setFont(QFont("Sans-Serif", 16, QFont.Weight.Bold))

        subtitle_label = QLabel("Convert source code files or pasted text into beautifully styled PDFs")
        subtitle_label.setObjectName("SubtitleLabel")
        subtitle_label.setFont(QFont("Sans-Serif", 10))

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        main_layout.addLayout(header_layout)

        # Tab Switch: Upload File vs Paste Code/Text
        self.tab_widget = QTabWidget()

        # Tab 1: Upload File
        file_tab = QWidget()
        file_tab_layout = QVBoxLayout(file_tab)
        file_tab_layout.setSpacing(8)

        file_label = QLabel("Select or Drag & Drop Input Source Code / Text File:")
        file_label.setFont(QFont("Sans-Serif", 9, QFont.Weight.Bold))

        file_input_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select or drag & drop a file (.py, .c, .cpp, .java, .txt)...")

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_file)

        file_input_layout.addWidget(self.file_path_edit)
        file_input_layout.addWidget(self.browse_btn)

        file_tab_layout.addWidget(file_label)
        file_tab_layout.addLayout(file_input_layout)
        file_tab_layout.addStretch()

        # Tab 2: Paste Code/Text
        paste_tab = QWidget()
        paste_tab_layout = QVBoxLayout(paste_tab)
        paste_tab_layout.setSpacing(8)

        paste_header_layout = QHBoxLayout()
        paste_label = QLabel("Paste Code or Plain Text:")
        paste_label.setFont(QFont("Sans-Serif", 9, QFont.Weight.Bold))

        lang_label = QLabel("Language:")
        self.lang_combo = QComboBox()
        for lang_name, _ in self.LANGUAGES:
            self.lang_combo.addItem(lang_name)

        paste_header_layout.addWidget(paste_label)
        paste_header_layout.addStretch()
        paste_header_layout.addWidget(lang_label)
        paste_header_layout.addWidget(self.lang_combo)

        self.text_editor = QPlainTextEdit()
        self.text_editor.setPlaceholderText("Paste your source code or text snippet here...")
        self.text_editor.setFont(QFont("Courier", 9))

        paste_tab_layout.addLayout(paste_header_layout)
        paste_tab_layout.addWidget(self.text_editor)

        self.tab_widget.addTab(file_tab, "📁 Upload File")
        self.tab_widget.addTab(paste_tab, "📝 Paste Code / Text")
        main_layout.addWidget(self.tab_widget)

        # Options Card
        options_card = QFrame()
        options_card.setObjectName("CardFrame")
        options_layout = QVBoxLayout(options_card)
        options_layout.setSpacing(10)

        options_title = QLabel("PDF Styling Options")
        options_title.setFont(QFont("Sans-Serif", 10, QFont.Weight.Bold))
        options_layout.addWidget(options_title)

        # Row 1: Theme & Font
        row1_layout = QHBoxLayout()

        theme_layout = QVBoxLayout()
        theme_lbl = QLabel("Color Theme:")
        self.theme_combo = QComboBox()
        for t_name in self.THEMES.keys():
            self.theme_combo.addItem(t_name)
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(theme_lbl)
        theme_layout.addWidget(self.theme_combo)

        font_layout = QVBoxLayout()
        font_lbl = QLabel("Font:")
        self.font_combo = QComboBox()
        for f_name, f_path, _ in self.FONTS:
            self.font_combo.addItem(f_name)
        self.font_combo.currentIndexChanged.connect(self.on_font_changed)
        font_layout.addWidget(font_lbl)
        font_layout.addWidget(self.font_combo)

        row1_layout.addLayout(theme_layout)
        row1_layout.addLayout(font_layout)
        options_layout.addLayout(row1_layout)

        # Row 2: Color Picker & Line Numbers
        row2_layout = QHBoxLayout()

        color_layout = QHBoxLayout()
        color_lbl = QLabel("Background Color:")
        self.color_swatch = QFrame()
        self.color_swatch.setFixedSize(24, 24)
        self.color_swatch.setObjectName("ColorSwatch")
        self.update_swatch_color(self.current_bg_color)

        self.pick_color_btn = QPushButton("Pick Color...")
        self.pick_color_btn.clicked.connect(self.pick_color)

        color_layout.addWidget(color_lbl)
        color_layout.addWidget(self.color_swatch)
        color_layout.addWidget(self.pick_color_btn)
        color_layout.addStretch()

        self.line_num_checkbox = QCheckBox("Show Line Numbers")
        self.line_num_checkbox.setChecked(True)

        row2_layout.addLayout(color_layout)
        row2_layout.addWidget(self.line_num_checkbox)
        options_layout.addLayout(row2_layout)

        main_layout.addWidget(options_card)

        # Action Area
        action_layout = QVBoxLayout()
        self.generate_btn = QPushButton("Generate PDF")
        self.generate_btn.setObjectName("GenerateButton")
        self.generate_btn.setFont(QFont("Sans-Serif", 11, QFont.Weight.Bold))
        self.generate_btn.clicked.connect(self.start_pdf_generation)
        action_layout.addWidget(self.generate_btn)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_layout.addWidget(self.status_label)

        main_layout.addLayout(action_layout)

        self.apply_stylesheet()

    def apply_stylesheet(self):
        """Applies modern dark-mode stylesheet to the PyQt6 window."""
        qss = """
        QMainWindow {
            background-color: #121218;
        }
        QLabel {
            color: #e2e8f0;
        }
        QLabel#SubtitleLabel {
            color: #94a3b8;
        }
        QLabel#StatusLabel {
            color: #cbd5e1;
            font-size: 11px;
        }
        QTabWidget::pane {
            border: 1px solid #2e2e42;
            background-color: #1e1e2a;
            border-radius: 8px;
            padding: 10px;
        }
        QTabBar::tab {
            background-color: #161622;
            color: #94a3b8;
            border: 1px solid #2e2e42;
            padding: 8px 16px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-weight: bold;
        }
        QTabBar::tab:selected {
            background-color: #1e1e2a;
            color: #3b82f6;
            border-bottom: 2px solid #3b82f6;
        }
        QFrame#CardFrame {
            background-color: #1e1e2a;
            border: 1px solid #2e2e42;
            border-radius: 8px;
            padding: 10px;
        }
        QLineEdit {
            background-color: #0f0f17;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
        }
        QLineEdit:focus {
            border: 1px solid #3b82f6;
        }
        QPlainTextEdit {
            background-color: #0f0f17;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 8px;
            font-size: 12px;
        }
        QPlainTextEdit:focus {
            border: 1px solid #3b82f6;
        }
        QComboBox {
            background-color: #0f0f17;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 6px 12px;
        }
        QComboBox QAbstractItemView {
            background-color: #1e1e2a;
            color: #f1f5f9;
            selection-background-color: #3b82f6;
        }
        QPushButton {
            background-color: #2563eb;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #3b82f6;
        }
        QPushButton#GenerateButton {
            background-color: #10b981;
            padding: 12px 24px;
            font-size: 14px;
            border-radius: 8px;
        }
        QPushButton#GenerateButton:hover {
            background-color: #059669;
        }
        QPushButton#GenerateButton:disabled {
            background-color: #334155;
            color: #94a3b8;
        }
        QCheckBox {
            color: #f1f5f9;
        }
        QFrame#ColorSwatch {
            border: 1px solid #ffffff;
            border-radius: 4px;
        }
        QMessageBox {
            background-color: #1e1e2a;
        }
        QMessageBox QLabel {
            color: #f1f5f9;
            font-size: 13px;
        }
        QMessageBox QPushButton {
            background-color: #2563eb;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 6px 20px;
            min-width: 65px;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover {
            background-color: #3b82f6;
        }
        """
        self.setStyleSheet(qss)

    def update_swatch_color(self, hex_color: str):
        self.current_bg_color = hex_color
        self.color_swatch.setStyleSheet(
            f"background-color: {hex_color}; border: 1px solid #94a3b8; border-radius: 4px;"
        )

    def on_theme_changed(self, theme_name: str):
        theme_info = self.THEMES.get(theme_name)
        if theme_info:
            self.update_swatch_color(theme_info["bg"])

    def on_font_changed(self, index: int):
        if index < len(self.FONTS):
            f_name, f_path, _ = self.FONTS[index]
            if f_path == "CUSTOM":
                path, _ = QFileDialog.getOpenFileName(
                    self, "Select TTF Font File", "", "TrueType Fonts (*.ttf)"
                )
                if path:
                    self.custom_font_path = path
                else:
                    self.font_combo.setCurrentIndex(0)

    def pick_color(self):
        initial_color = QColor(self.current_bg_color)
        chosen_color = QColorDialog.getColor(initial_color, self, "Select Background Color")
        if chosen_color.isValid():
            self.update_swatch_color(chosen_color.name())

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Input Source Code / Text File",
            "",
            "Supported Files (*.c *.cpp *.java *.py *.txt *.js *.html *.json *.sql);;All Files (*)",
        )
        if file_path:
            self.file_path_edit.setText(file_path)
            self.status_label.setText(f"Status: Selected {Path(file_path).name}")

    def start_pdf_generation(self):
        active_tab_idx = self.tab_widget.currentIndex()

        file_path_param = None
        raw_text_param = None
        language_param = None
        output_pdf_path = None

        if active_tab_idx == 0:
            # Mode 1: Upload File
            file_str = self.file_path_edit.text().strip()
            if not file_str or not Path(file_str).exists():
                self.status_label.setText("Status: Error - Selected file does not exist or is invalid.")
                if not getattr(self, "is_test_mode", False) and "--test" not in sys.argv:
                    QMessageBox.warning(
                        self,
                        "File Missing",
                        "Please select a valid input file (.c, .cpp, .java, .py, .txt) first.",
                    )
                return

            input_path = Path(file_str)
            if not input_path.is_file():
                self.status_label.setText("Status: Error - Target path is not a file.")
                return

            file_path_param = str(input_path)
            suggested_name = f"{input_path.stem}_code_to_pdf.pdf"
            last_save_dir = self.config_data.get("last_save_directory")
            if last_save_dir and Path(last_save_dir).is_dir():
                default_suggested_path = Path(last_save_dir) / suggested_name
            else:
                default_suggested_path = input_path.parent / suggested_name
        else:
            # Mode 2: Paste Code/Text
            pasted_code = self.text_editor.toPlainText().strip()
            if not pasted_code:
                self.status_label.setText("Status: Error - Text area is empty.")
                if not getattr(self, "is_test_mode", False) and "--test" not in sys.argv:
                    QMessageBox.warning(
                        self,
                        "Input Empty",
                        "Please paste code or plain text into the text area before generating PDF.",
                    )
                return
            raw_text_param = pasted_code
            lang_idx = self.lang_combo.currentIndex()
            language_param = self.LANGUAGES[lang_idx][1]

            suggested_name = "pasted_code_to_pdf.pdf"
            last_save_dir = self.config_data.get("last_save_directory")
            if last_save_dir and Path(last_save_dir).is_dir():
                default_suggested_path = Path(last_save_dir) / suggested_name
            else:
                default_suggested_path = Path.cwd() / suggested_name

        # Ask user where to save PDF file (unless running automated test mode)
        if not getattr(self, "is_test_mode", False) and "--test" not in sys.argv:
            save_path_str, _ = QFileDialog.getSaveFileName(
                self,
                "Save Generated PDF",
                str(default_suggested_path),
                "PDF Files (*.pdf);;All Files (*)",
            )
            if not save_path_str:
                self.status_label.setText("Status: PDF save cancelled by user.")
                return
            output_pdf_path = Path(save_path_str)
            # Remember selected save directory for future generations
            self.config_data["last_save_directory"] = str(output_pdf_path.parent)
            self.save_current_config()
        else:
            output_pdf_path = default_suggested_path

        # Permission check for target output directory
        try:
            output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            if not os.access(output_pdf_path.parent, os.W_OK):
                self.status_label.setText("Status: Error - Permission denied for output directory.")
                return
        except Exception as e:
            self.status_label.setText(f"Status: Error - {str(e)}")
            return

        theme_name = self.theme_combo.currentText()
        theme_info = self.THEMES.get(theme_name, self.THEMES["Dark (Monokai)"])
        pygments_style = theme_info["style"]
        text_color = theme_info.get("text_color", "#d4d4d4")
        line_num_color = theme_info.get("line_num", "#64748b")

        font_idx = self.font_combo.currentIndex()
        font_info = self.FONTS[font_idx] if font_idx < len(self.FONTS) else self.FONTS[0]
        font_path = font_info[1]
        font_name = font_info[2]

        if font_path == "CUSTOM" and self.custom_font_path:
            font_path = self.custom_font_path
            font_name = "CustomTTF"
        elif font_path and not Path(font_path).exists():
            font_path = None

        show_lines = self.line_num_checkbox.isChecked()
        bg_color = self.current_bg_color

        # UI state during generation
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("Generating PDF...")
        self.status_label.setText("Status: Generating PDF in background thread...")

        # Start worker thread
        self.worker = PDFWorkerThread(
            file_path=file_path_param,
            raw_text=raw_text_param,
            language=language_param,
            output_path=str(output_pdf_path),
            bg_color=bg_color,
            text_color=text_color,
            line_number_color=line_num_color,
            pygments_style=pygments_style,
            font_path=font_path,
            font_name=font_name,
            show_line_numbers=show_lines,
        )
        self.worker.finished_signal.connect(self.on_generation_finished)
        self.worker.error_signal.connect(self.on_generation_error)
        self.worker.start()

    def on_generation_finished(self, output_path: str):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("Generate PDF")
        self.status_label.setText(f"Status: PDF saved to {Path(output_path).name}")

        if not getattr(self, "is_test_mode", False) and "--test" not in sys.argv:
            QMessageBox.information(
                self,
                "Success",
                f"PDF generated successfully!\nSaved to: {output_path}",
            )

    def on_generation_error(self, err_msg: str):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("Generate PDF")
        self.status_label.setText("Status: Generation Failed")

        if not getattr(self, "is_test_mode", False) and "--test" not in sys.argv:
            QMessageBox.critical(
                self,
                "Error Generating PDF",
                f"Failed to generate PDF:\n{err_msg}",
            )


def main():
    t0 = time.time()

    # Suppress GPU/compositor log spam in app environment
    os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"

    app = QApplication(sys.argv)

    # Check if test mode flag is present (skip single instance check for test scripts)
    if "--test" not in sys.argv:
        socket = QLocalSocket()
        socket.connectToServer(SERVER_NAME)
        if socket.waitForConnected(500):
            # Instance already running! Signal existing window to focus and exit cleanly.
            socket.write(b"ACTIVATE")
            socket.flush()
            socket.disconnectFromServer()
            sys.exit(0)

        # Primary instance: setup local server
        server = QLocalServer()
        QLocalServer.removeServer(SERVER_NAME)
        server.listen(SERVER_NAME)
    else:
        server = None

    window = CodeToPDFWindow()

    if server:
        def handle_new_connection():
            client_socket = server.nextPendingConnection()
            if client_socket:
                client_socket.waitForReadyRead(300)
                window.show()
                window.setWindowState(
                    window.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive
                )
                window.raise_()
                window.activateWindow()
                client_socket.disconnectFromServer()

        server.newConnection.connect(handle_new_connection)

    window.show()
    startup_ms = (time.time() - t0) * 1000
    print(f"CodeToPDF PyQt6 GUI started in {startup_ms:.2f} ms")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
