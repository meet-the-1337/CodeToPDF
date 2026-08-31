"""
code_to_pdf_engine: A local-first Python module to convert code and text files into styled PDFs.

Supported inputs: File paths (.c, .cpp, .java, .py, .txt, etc.) OR raw text strings.
Features:
- Dual input mode: Accepts file paths OR raw text strings directly.
- Pygments automatic language detection (guess_lexer_for_filename / guess_lexer) and explicit language selection.
- Syntax highlighting for code, plain text rendering for .txt / text files.
- ReportLab Platypus (SimpleDocTemplate, XPreformatted).
- Safe XML escaping for ReportLab (no HTML rendering errors).
- Custom TTF font registration and loading with global caching.
- Pre-resolved token style map caching & token consolidation for ultra-fast execution.
- Full background color styling across the entire PDF document.
- In-memory PDF generation via io.BytesIO (no temp files on disk).
- Content chunking to handle large files (up to 10,000+ lines) efficiently.
- 100% offline with zero external API calls.
"""

from pathlib import Path
from io import BytesIO
import html
import os
import sys

from pygments import lex
from pygments.lexers import (
    guess_lexer,
    guess_lexer_for_filename,
    get_lexer_by_name,
    get_lexer_for_filename,
    TextLexer,
)
from pygments.styles import get_style_by_name
from pygments.util import ClassNotFound

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, XPreformatted


# Global Performance Caches
_REGISTERED_FONTS: set[str] = set()
_RESOLVED_STYLE_MAPS: dict[str, dict] = {}
_STYLE_OBJ_CACHE: dict[str, object] = {}


def get_luminance(hex_color: str) -> float:
    """Calculates relative luminance of a hex color string (0.0=dark, 1.0=light)."""
    hex_c = hex_color.lstrip("#")
    if len(hex_c) == 3:
        hex_c = "".join([c * 2 for c in hex_c])
    if len(hex_c) != 6:
        return 0.5
    try:
        r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
        return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    except Exception:
        return 0.5


def get_bundle_dir() -> Path:
    """Returns directory path, accounting for PyInstaller sys._MEIPASS bundle directory."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.resolve()


def resolve_font(font_path: str | Path | None = None, font_name: str | None = None) -> str:
    """
    Registers custom TTF font if font_path is provided.
    Caches registered font names globally to prevent redundant font metric parsing.
    Returns the font name to use in ReportLab.
    """
    if font_path:
        font_p = Path(font_path)
        if not font_p.exists():
            raise FileNotFoundError(f"Custom font file not found: {font_p}")
        target_name = font_name or font_p.stem
        if target_name not in _REGISTERED_FONTS:
            pdfmetrics.registerFont(TTFont(target_name, str(font_p)))
            _REGISTERED_FONTS.add(target_name)
        return target_name

    if font_name and font_name != "Courier":
        if font_name in _REGISTERED_FONTS:
            return font_name
        try:
            pdfmetrics.getFont(font_name)
            _REGISTERED_FONTS.add(font_name)
            return font_name
        except KeyError:
            pass

    bundle_dir = get_bundle_dir()
    system_font_candidates = [
        ("JetBrainsMono", str(bundle_dir / "fonts" / "JetBrainsMonoNerdFontMono-Regular.ttf")),
        ("JetBrainsMono", "/usr/share/fonts/TTF/JetBrainsMonoNerdFontMono-Regular.ttf"),
        ("LiberationMono", "/usr/share/fonts/liberation/LiberationMono-Regular.ttf"),
        ("DejaVuSansMono", "/usr/share/fonts/TTF/DejaVuSansMono.ttf"),
        ("DejaVuSansMono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        ("Consolas", os.path.expandvars(r"%WINDIR%\Fonts\consola.ttf")),
        ("CourierNew", os.path.expandvars(r"%WINDIR%\Fonts\cour.ttf")),
        ("CourierNew", "/System/Library/Fonts/Supplemental/Courier New.ttf"),
    ]

    for name, path in system_font_candidates:
        if name in _REGISTERED_FONTS:
            return name
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                _REGISTERED_FONTS.add(name)
                return name
            except Exception:
                continue

    return "Courier"


def safe_get_style(style_name: str):
    """Safely retrieves Pygments style with caching."""
    if style_name in _STYLE_OBJ_CACHE:
        return _STYLE_OBJ_CACHE[style_name]
    try:
        style_obj = get_style_by_name(style_name)
    except ClassNotFound:
        try:
            style_obj = get_style_by_name("monokai")
        except ClassNotFound:
            style_obj = get_style_by_name("default")
    _STYLE_OBJ_CACHE[style_name] = style_obj
    return style_obj


def get_resolved_style_map(style_name: str) -> dict:
    """Returns a cached, pre-resolved mapping from Pygments tokens to ReportLab XML tags."""
    if style_name in _RESOLVED_STYLE_MAPS:
        return _RESOLVED_STYLE_MAPS[style_name]

    style_cls = safe_get_style(style_name)
    raw_map = {}
    for token, style in style_cls:
        color = style.get("color")
        bold = style.get("bold")
        italic = style.get("italic")
        prefix = f'<font color="#{color}">' if color else ""
        suffix = "</font>" if color else ""
        if bold:
            prefix += "<b>"
            suffix = "</b>" + suffix
        if italic:
            prefix += "<i>"
            suffix = "</i>" + suffix
        raw_map[token] = (prefix, suffix)

    _RESOLVED_STYLE_MAPS[style_name] = raw_map
    return raw_map


def format_code_to_xml_lines(content: str, lexer, style_name: str) -> list[str]:
    """Tokenizes code content and splits into line strings with token consolidation."""
    raw_map = get_resolved_style_map(style_name)
    all_lines = []
    curr_line_parts = []
    token_cache = {}

    last_prefix = None
    last_suffix = None
    accum_val = []

    for ttype, val in lex(content, lexer):
        if ttype in token_cache:
            prefix, suffix = token_cache[ttype]
        else:
            prefix, suffix = "", ""
            curr_t = ttype
            while curr_t:
                if curr_t in raw_map:
                    prefix, suffix = raw_map[curr_t]
                    break
                curr_t = curr_t.parent
            token_cache[ttype] = (prefix, suffix)

        parts = val.split("\n")
        for idx, part in enumerate(parts):
            if idx > 0:
                if accum_val:
                    esc = html.escape("".join(accum_val), quote=False)
                    curr_line_parts.append(f"{last_prefix}{esc}{last_suffix}")
                    accum_val = []
                all_lines.append("".join(curr_line_parts))
                curr_line_parts = []
                last_prefix, last_suffix = None, None

            if part:
                if prefix == last_prefix and suffix == last_suffix:
                    accum_val.append(part)
                else:
                    if accum_val:
                        esc = html.escape("".join(accum_val), quote=False)
                        curr_line_parts.append(f"{last_prefix}{esc}{last_suffix}")
                        accum_val = []
                    last_prefix, last_suffix = prefix, suffix
                    accum_val.append(part)

    if accum_val:
        esc = html.escape("".join(accum_val), quote=False)
        curr_line_parts.append(f"{last_prefix}{esc}{last_suffix}")

    if curr_line_parts or not all_lines:
        all_lines.append("".join(curr_line_parts))

    return all_lines


def format_text_to_xml_lines(content: str, text_color: str) -> list[str]:
    """Formats plain text content line-by-line with XML escaping and base text color."""
    raw_lines = content.splitlines()
    if not raw_lines:
        return [""]
    formatted = []
    for line in raw_lines:
        esc = html.escape(line, quote=False)
        if esc:
            formatted.append(f'<font color="{text_color}">{esc}</font>')
        else:
            formatted.append("")
    return formatted


def apply_line_numbers(lines: list[str], line_number_color: str) -> list[str]:
    """Prepends formatted line numbers to each line."""
    total = len(lines)
    max_digits = max(1, len(str(total)))
    numbered = []
    for idx, line in enumerate(lines, start=1):
        num_str = f"{idx:>{max_digits}}  "
        prefix = f'<font color="{line_number_color}">{num_str}</font>'
        numbered.append(prefix + line)
    return numbered


def create_page_decorator(
    title: str,
    lang_name: str,
    bg_color: str,
    header_footer_color: str,
    font_name: str,
):
    """Creates page canvas callback for drawing background color, headers, and footers."""
    bg_hex = colors.HexColor(bg_color)
    hf_hex = colors.HexColor(header_footer_color)

    lum = get_luminance(bg_color)
    line_hex = colors.HexColor("#333333") if lum < 0.5 else colors.HexColor("#cccccc")

    def draw_decorations(canvas, doc):
        canvas.saveState()
        w, h = doc.pagesize

        # 1. Fill background across entire page
        canvas.setFillColor(bg_hex)
        canvas.rect(0, 0, w, h, fill=1, stroke=0)

        # 2. Header
        canvas.setFillColor(hf_hex)
        try:
            canvas.setFont(font_name, 8)
        except Exception:
            canvas.setFont("Courier", 8)

        canvas.drawString(36, h - 25, title)
        canvas.drawRightString(w - 36, h - 25, f"Language: {lang_name}")

        canvas.setStrokeColor(line_hex)
        canvas.setLineWidth(0.5)
        canvas.line(36, h - 28, w - 36, h - 28)

        # 3. Footer
        canvas.line(36, 32, w - 36, 32)
        canvas.drawString(36, 20, "Generated by code_to_pdf_engine")
        canvas.drawRightString(w - 36, 20, f"Page {canvas._pageNumber}")

        canvas.restoreState()

    return draw_decorations


def resolve_lexer(
    content: str,
    file_path: str | Path | None = None,
    language: str | None = None,
) -> tuple[bool, str, object | None]:
    """
    Determines lexer and language name from file_path, language hint, or content auto-detection.
    Returns tuple: (is_code: bool, lang_name: str, lexer: object | None).
    """
    if language:
        lang_clean = language.strip().lower()
        if lang_clean in ("text", "plain text", "txt"):
            return False, "Plain Text", None
        elif lang_clean != "auto":
            try:
                lexer = get_lexer_by_name(lang_clean)
                return True, lexer.name, lexer
            except ClassNotFound:
                pass

    if file_path:
        path = Path(file_path)
        filename = path.name
        ext = path.suffix.lower()
        if ext == ".txt":
            return False, "Plain Text", None
        try:
            lexer = guess_lexer_for_filename(filename, content)
            if isinstance(lexer, TextLexer):
                return False, "Plain Text", None
            return True, lexer.name, lexer
        except ClassNotFound:
            try:
                lexer = get_lexer_for_filename(filename)
                return True, lexer.name, lexer
            except ClassNotFound:
                return False, "Plain Text", None

    # Raw text content auto-detection
    try:
        lexer = guess_lexer(content)
        if isinstance(lexer, TextLexer):
            return False, "Plain Text", None
        return True, lexer.name, lexer
    except ClassNotFound:
        return False, "Plain Text", None


def generate_pdf(
    file_path: str | Path | None = None,
    raw_text: str | None = None,
    language: str | None = None,
    output_path: str | Path | None = None,
    font_path: str | Path | None = None,
    font_name: str | None = None,
    font_size: int = 9,
    bg_color: str = "#1e1e1e",
    text_color: str = "#d4d4d4",
    line_number_color: str = "#5a5a5a",
    pygments_style: str = "monokai",
    show_line_numbers: bool = True,
    chunk_size: int = 200,
    page_size=letter,
    title: str | None = None,
) -> BytesIO:
    """
    Generates a styled PDF from either a file path OR a raw text string.

    Parameters:
    - file_path: Optional path to the input file (.c, .cpp, .java, .py, .txt, etc.).
    - raw_text: Optional raw code/text string (used when file_path is None).
    - language: Optional language hint/alias (e.g. 'python', 'cpp', 'java', 'text', 'auto').
    - output_path: Optional path to save PDF to disk.
    - font_path: Optional path to local TTF font file.
    - font_name: Optional name for registered font.
    - font_size: Font size in points (default: 9).
    - bg_color: Hex background color string (default: '#1e1e1e').
    - text_color: Base text color for unstyled text/plain text (default: '#d4d4d4').
    - line_number_color: Color for line numbers and headers/footers (default: '#5a5a5a').
    - pygments_style: Pygments theme name (default: 'monokai').
    - show_line_numbers: Whether to prefix lines with line numbers (default: True).
    - chunk_size: Number of lines per Platypus flowable for memory chunking (default: 200).
    - page_size: ReportLab page size tuple (default: letter).
    - title: Custom title for header (default: filename or 'Snippet').

    Returns:
    - BytesIO buffer containing the PDF binary data.
    """
    if file_path is None and raw_text is None:
        raise ValueError("Either file_path or raw_text must be provided.")

    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        content = path.read_text(encoding="utf-8", errors="replace").expandtabs(4)
        doc_title = title or path.name
    else:
        content = str(raw_text).expandtabs(4)
        doc_title = title or "Pasted_Snippet"

    is_code, lang_name, lexer = resolve_lexer(
        content=content, file_path=file_path, language=language
    )

    # Luminance & contrast check for text_color and line_number_color
    lum = get_luminance(bg_color)
    if lum >= 0.5:
        if text_color == "#d4d4d4":
            text_color = "#1e293b"
        if line_number_color == "#5a5a5a":
            line_number_color = "#64748b"
    else:
        if text_color == "#1e293b":
            text_color = "#d4d4d4"
        if line_number_color == "#64748b":
            line_number_color = "#5a5a5a"

    # Format lines into ReportLab XML markup strings
    if is_code and lexer is not None:
        xml_lines = format_code_to_xml_lines(content, lexer, pygments_style)
    else:
        xml_lines = format_text_to_xml_lines(content, text_color)

    # Apply line numbers if enabled
    if show_line_numbers:
        xml_lines = apply_line_numbers(xml_lines, line_number_color)

    # Resolve font with global caching
    resolved_font = resolve_font(font_path, font_name)

    # Setup Document & Story
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=page_size,
        topMargin=40,
        bottomMargin=40,
        leftMargin=36,
        rightMargin=36,
    )

    leading = font_size + 3
    code_style = ParagraphStyle(
        "CodeBlockStyle",
        fontName=resolved_font,
        fontSize=font_size,
        leading=leading,
        textColor=colors.HexColor(text_color),
    )

    decorator = create_page_decorator(
        title=doc_title,
        lang_name=lang_name,
        bg_color=bg_color,
        header_footer_color=line_number_color,
        font_name=resolved_font,
    )

    story = []

    if not xml_lines:
        xml_lines = [""]

    # Streaming/Chunking content into flowables to optimize memory & build speed
    for i in range(0, len(xml_lines), chunk_size):
        chunk = xml_lines[i : i + chunk_size]
        chunk_text = "\n".join(chunk)
        story.append(XPreformatted(chunk_text, code_style))

    doc.build(story, onFirstPage=decorator, onLaterPages=decorator)

    buf.seek(0)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_bytes(buf.getvalue())
        buf.seek(0)

    return buf


code_to_pdf = generate_pdf
