---
applyTo: "**/*.md"
description: Instructions for converting Markdown documents to Word using docxer
---

# Markdown to Word Conversion (docxer)

This workspace includes `docxer`, a CLI tool for converting GitHub-flavored Markdown files to Microsoft Word (.docx) documents.

## Basic Usage

```bash
# Convert a markdown file (output defaults to same name with .docx extension)
uv run docxer input.md

# Specify a custom output path
uv run docxer input.md -o output.docx

# Show help
uv run docxer --help

# Show version
uv run docxer --version
```

## Supported Markdown Features

- **Headings** (h1-h6) → Word heading styles
- **Bold** (`**text**`) → Bold text
- **Italic** (`*text*`) → Italic text
- **Strikethrough** (`~~text~~`) → Strikethrough text
- **Inline code** (`` `code` ``) → Courier New font
- **Code blocks** (triple backticks) → Monospace formatting
- **Links** (`[text](https://url)`) → Text with URL in parentheses
- **Bullet lists** (`- item`) → Word bullet lists
- **Blockquotes** (`> quote`) → Indented paragraphs
- **Horizontal rules** (`---`) → Centered line

## Examples

```bash
# Convert README to Word
uv run docxer README.md

# Convert with custom output location
uv run docxer docs/guide.md -o exports/guide.docx

# Convert multiple files (run separately)
uv run docxer chapter1.md -o book/chapter1.docx
uv run docxer chapter2.md -o book/chapter2.docx
```

## Programmatic Usage

The converter can also be used as a Python library:

```python
from docxer import convert_file, convert_markdown_to_docx

# Convert file to file
convert_file("input.md", "output.docx")

# Convert string to Document object
doc = convert_markdown_to_docx("# Hello\n\nThis is **bold** text.")
doc.save("output.docx")
```

## Tips

- Output file is created in the same directory as input if `-o` is not specified
- The tool preserves document structure suitable for further editing in Word
- For best results, use well-structured markdown with clear heading hierarchy

