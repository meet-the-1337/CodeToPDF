"""
src/mobile_gui.py: Kivy Touch-Optimized Mobile Interface for Code to PDF.
Designed specifically for phone screens (portrait orientation, touch inputs, file choosing, and PDF generation).
"""

from pathlib import Path
import os
import sys

try:
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.spinner import Spinner
    from kivy.uix.switch import Switch
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.popup import Popup
    from kivy.uix.filechooser import FileChooserListView
    from kivy.utils import platform
except ImportError:
    App = object
    platform = "desktop"

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).parent.resolve()))
from code_to_pdf_engine import generate_pdf


class CodeToPDFMobileApp(App):
    title = "Code to PDF Mobile"

    THEMES = {
        "Dark (Monokai)": {"style": "monokai", "bg": "#1e1e1e", "text": "#d4d4d4", "line": "#64748b"},
        "Light (GitHub)": {"style": "default", "bg": "#ffffff", "text": "#1e293b", "line": "#94a3b8"},
        "Monochrome": {"style": "bw", "bg": "#f8fafc", "text": "#0f172a", "line": "#64748b"},
        "Dracula": {"style": "dracula", "bg": "#282a36", "text": "#f8f8f2", "line": "#6272a4"},
        "Solarized Dark": {"style": "solarized-dark", "bg": "#002b36", "text": "#839496", "line": "#586e75"},
    }

    LANGUAGES = [
        "Auto-Detect",
        "Python",
        "C / C++",
        "Java",
        "JavaScript",
        "HTML / CSS",
        "JSON",
        "SQL",
        "Plain Text",
    ]

    LANG_MAP = {
        "Auto-Detect": "auto",
        "Python": "python",
        "C / C++": "cpp",
        "Java": "java",
        "JavaScript": "js",
        "HTML / CSS": "html",
        "JSON": "json",
        "SQL": "sql",
        "Plain Text": "text",
    }

    def build(self):
        self.selected_file_path = None

        main_layout = BoxLayout(orientation="vertical", padding=15, spacing=10)

        # Header
        header = Label(
            text="[b]Code to PDF 🚀[/b]\n[size=14sp]Mobile Phone Edition[/size]",
            markup=True,
            size_hint_y=None,
            height=60,
            halign="center",
        )
        main_layout.add_widget(header)

        # Scrollable Form Content
        scroll = ScrollView(size_hint=(1, 1))
        form_layout = BoxLayout(orientation="vertical", spacing=12, size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter("height"))

        # Mode Selection: Upload File vs Paste Code
        form_layout.add_widget(Label(text="[b]Input Source:[/b]", markup=True, size_hint_y=None, height=25))

        mode_box = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        self.btn_file_mode = Button(text="📁 Select File", background_color=(0.2, 0.5, 0.9, 1))
        self.btn_paste_mode = Button(text="📝 Paste Text", background_color=(0.3, 0.3, 0.3, 1))
        self.btn_file_mode.bind(on_release=self.set_file_mode)
        self.btn_paste_mode.bind(on_release=self.set_paste_mode)
        mode_box.add_widget(self.btn_file_mode)
        mode_box.add_widget(self.btn_paste_mode)
        form_layout.add_widget(mode_box)

        # Active Mode Content Box
        self.mode_content_box = BoxLayout(orientation="vertical", spacing=8, size_hint_y=None, height=80)

        # File Mode UI
        self.file_label = Label(text="No file selected", size_hint_y=None, height=30, halign="left")
        self.btn_browse = Button(text="Browse File...", size_hint_y=None, height=40)
        self.btn_browse.bind(on_release=self.open_file_chooser)
        self.file_box = BoxLayout(orientation="vertical", spacing=5)
        self.file_box.add_widget(self.btn_browse)
        self.file_box.add_widget(self.file_label)

        # Paste Mode UI
        self.text_input = TextInput(
            hint_text="Paste your source code or text snippet here...",
            multiline=True,
            size_hint_y=None,
            height=120,
        )
        self.lang_spinner = Spinner(
            text="Auto-Detect",
            values=self.LANGUAGES,
            size_hint_y=None,
            height=40,
        )
        self.paste_box = BoxLayout(orientation="vertical", spacing=5)
        self.paste_box.add_widget(self.lang_spinner)
        self.paste_box.add_widget(self.text_input)

        # Default mode: File Mode
        self.current_mode = "file"
        self.mode_content_box.add_widget(self.file_box)
        form_layout.add_widget(self.mode_content_box)

        # Styling Options Section
        form_layout.add_widget(Label(text="[b]PDF Styling Options:[/b]", markup=True, size_hint_y=None, height=25))

        # Theme Selector
        theme_box = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        theme_box.add_widget(Label(text="Color Theme:", size_hint_x=0.4))
        self.theme_spinner = Spinner(
            text="Dark (Monokai)",
            values=list(self.THEMES.keys()),
            size_hint_x=0.6,
        )
        theme_box.add_widget(self.theme_spinner)
        form_layout.add_widget(theme_box)

        # Line Numbers Switch
        line_box = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        line_box.add_widget(Label(text="Show Line Numbers:", size_hint_x=0.7))
        self.line_switch = Switch(active=True, size_hint_x=0.3)
        line_box.add_widget(self.line_switch)
        form_layout.add_widget(line_box)

        scroll.add_widget(form_layout)
        main_layout.add_widget(scroll)

        # Action Buttons
        action_box = BoxLayout(orientation="vertical", spacing=8, size_hint_y=None, height=90)

        self.btn_generate = Button(
            text="Generate PDF 📄",
            font_size="16sp",
            bold=True,
            background_color=(0.06, 0.72, 0.5, 1),
            size_hint_y=None,
            height=50,
        )
        self.btn_generate.bind(on_release=self.generate_pdf_action)

        self.status_label = Label(text="Status: Ready", size_hint_y=None, height=30)

        action_box.add_widget(self.btn_generate)
        action_box.add_widget(self.status_label)
        main_layout.add_widget(action_box)

        return main_layout

    def set_file_mode(self, instance):
        self.current_mode = "file"
        self.btn_file_mode.background_color = (0.2, 0.5, 0.9, 1)
        self.btn_paste_mode.background_color = (0.3, 0.3, 0.3, 1)
        self.mode_content_box.clear_widgets()
        self.mode_content_box.height = 80
        self.mode_content_box.add_widget(self.file_box)

    def set_paste_mode(self, instance):
        self.current_mode = "paste"
        self.btn_paste_mode.background_color = (0.2, 0.5, 0.9, 1)
        self.btn_file_mode.background_color = (0.3, 0.3, 0.3, 1)
        self.mode_content_box.clear_widgets()
        self.mode_content_box.height = 170
        self.mode_content_box.add_widget(self.paste_box)

    def open_file_chooser(self, instance):
        content = BoxLayout(orientation="vertical")

        start_dir = "/sdcard/Download" if platform == "android" else str(Path.home())
        if not os.path.exists(start_dir):
            start_dir = str(Path.cwd())

        file_chooser = FileChooserListView(path=start_dir)
        content.add_widget(file_chooser)

        btn_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40, spacing=10)
        btn_cancel = Button(text="Cancel")
        btn_select = Button(text="Select File", background_color=(0.2, 0.5, 0.9, 1))
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_select)
        content.add_widget(btn_box)

        popup = Popup(title="Select Source Code File", content=content, size_hint=(0.9, 0.9))

        def select_file(btn):
            if file_chooser.selection:
                selected = file_chooser.selection[0]
                if os.path.isfile(selected):
                    self.selected_file_path = selected
                    self.file_label.text = f"Selected: {Path(selected).name}"
                    popup.dismiss()

        btn_cancel.bind(on_release=popup.dismiss)
        btn_select.bind(on_release=select_file)
        popup.open()

    def show_popup(self, title, message):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(Label(text=message, halign="center"))
        btn_ok = Button(text="OK", size_hint_y=None, height=40)
        content.add_widget(btn_ok)

        popup = Popup(title=title, content=content, size_hint=(0.85, 0.4))
        btn_ok.bind(on_release=popup.dismiss)
        popup.open()

    def generate_pdf_action(self, instance):
        theme_info = self.THEMES.get(self.theme_spinner.text, self.THEMES["Dark (Monokai)"])
        pygments_style = theme_info["style"]
        bg_color = theme_info["bg"]
        text_color = theme_info["text"]
        line_num_color = theme_info["line"]
        show_lines = self.line_switch.active

        if platform == "android":
            out_dir = Path("/sdcard/Download")
            if not out_dir.exists():
                out_dir = Path.home()
        else:
            out_dir = Path.home() / "Downloads"
            if not out_dir.exists():
                out_dir = Path.cwd()

        if self.current_mode == "file":
            if not self.selected_file_path or not os.path.isfile(self.selected_file_path):
                self.show_popup("Error", "Please select a valid input file first.")
                return
            input_p = Path(self.selected_file_path)
            out_path = out_dir / f"{input_p.stem}_code_to_pdf.pdf"
            file_param = str(input_p)
            text_param = None
            lang_param = None
        else:
            pasted_text = self.text_input.text.strip()
            if not pasted_text:
                self.show_popup("Error", "Text input is empty. Please paste code or text.")
                return
            out_path = out_dir / "pasted_code_to_pdf.pdf"
            file_param = None
            text_param = pasted_text
            lang_param = self.LANG_MAP.get(self.lang_spinner.text, "auto")

        self.status_label.text = "Status: Generating PDF..."

        try:
            generate_pdf(
                file_path=file_param,
                raw_text=text_param,
                language=lang_param,
                output_path=out_path,
                bg_color=bg_color,
                text_color=text_color,
                line_number_color=line_num_color,
                pygments_style=pygments_style,
                show_line_numbers=show_lines,
            )
            self.status_label.text = f"Status: Saved to {out_path.name}"
            self.show_popup("Success 🎉", f"PDF generated successfully!\nSaved to: {out_path}")
        except Exception as e:
            self.status_label.text = "Status: Generation Failed"
            self.show_popup("Error", f"Failed to generate PDF:\n{str(e)}")
