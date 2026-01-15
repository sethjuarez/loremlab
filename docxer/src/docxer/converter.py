"""Markdown to DOCX converter using mistune and python-docx."""

from docx import Document
from docx.document import Document as DocumentClass
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import mistune
from typing import Any


class DocxRenderer(mistune.HTMLRenderer):
    """Custom renderer that builds a Word document instead of HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.doc = Document()
        self._current_paragraph: Any = None
        self._in_list = False
        self._list_level = 0

    def _ensure_paragraph(self) -> Any:
        """Ensure we have a current paragraph to add runs to."""
        if self._current_paragraph is None:
            self._current_paragraph = self.doc.add_paragraph()
        return self._current_paragraph

    def _finish_paragraph(self) -> None:
        """Mark current paragraph as finished."""
        self._current_paragraph = None

    def text(self, text: str) -> str:
        """Handle plain text."""
        if text.strip():
            p = self._ensure_paragraph()
            p.add_run(text)
        return ""

    def paragraph(self, text: str) -> str:
        """Handle paragraph elements."""
        self._finish_paragraph()
        if text.strip():
            self.doc.add_paragraph(text)
        self._finish_paragraph()
        return ""

    def heading(self, text: str, level: int, **attrs: Any) -> str:
        """Handle headings (h1-h6)."""
        self._finish_paragraph()
        self.doc.add_heading(text, level=level)
        self._finish_paragraph()
        return ""

    def strong(self, text: str) -> str:
        """Handle bold text."""
        p = self._ensure_paragraph()
        run = p.add_run(text)
        run.bold = True
        return ""

    def emphasis(self, text: str) -> str:
        """Handle italic text."""
        p = self._ensure_paragraph()
        run = p.add_run(text)
        run.italic = True
        return ""

    def codespan(self, text: str) -> str:
        """Handle inline code."""
        p = self._ensure_paragraph()
        run = p.add_run(text)
        run.font.name = "Courier New"
        run.font.size = Pt(10)
        return ""

    def block_code(self, code: str, info: str | None = None) -> str:
        """Handle code blocks."""
        self._finish_paragraph()
        p = self.doc.add_paragraph(style="No Spacing")
        run = p.add_run(code)
        run.font.name = "Courier New"
        run.font.size = Pt(10)
        self._finish_paragraph()
        return ""

    def link(self, text: str, url: str, title: str | None = None) -> str:
        """Handle links (rendered as text with URL in parentheses)."""
        p = self._ensure_paragraph()
        p.add_run(f"{text} ({url})")
        return ""

    def list(self, text: str, ordered: bool, **attrs: Any) -> str:
        """Handle lists."""
        self._finish_paragraph()
        return ""

    def list_item(self, text: str, **attrs: Any) -> str:
        """Handle list items."""
        self._finish_paragraph()
        self.doc.add_paragraph(text, style="List Bullet")
        self._finish_paragraph()
        return ""

    def block_quote(self, text: str) -> str:
        """Handle blockquotes."""
        self._finish_paragraph()
        p = self.doc.add_paragraph(text)
        p.paragraph_format.left_indent = Inches(0.5)
        self._finish_paragraph()
        return ""

    def thematic_break(self) -> str:
        """Handle horizontal rules."""
        self._finish_paragraph()
        p = self.doc.add_paragraph("─" * 50)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._finish_paragraph()
        return ""

    def linebreak(self) -> str:
        """Handle line breaks."""
        p = self._ensure_paragraph()
        p.add_run("\n")
        return ""

    def strikethrough(self, text: str) -> str:
        """Handle strikethrough text (GFM extension)."""
        p = self._ensure_paragraph()
        run = p.add_run(text)
        run.font.strike = True
        return ""


def convert_markdown_to_docx(markdown_text: str) -> DocumentClass:
    """Convert markdown text to a Word document.

    Args:
        markdown_text: The GitHub-flavored markdown text to convert.

    Returns:
        A python-docx Document object.
    """
    renderer = DocxRenderer()
    md = mistune.create_markdown(renderer=renderer)
    md(markdown_text)
    return renderer.doc


def convert_file(input_path: str, output_path: str) -> None:
    """Convert a markdown file to a Word document.

    Args:
        input_path: Path to the input markdown file.
        output_path: Path for the output .docx file.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    doc = convert_markdown_to_docx(markdown_text)
    doc.save(output_path)
