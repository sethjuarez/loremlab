"""Docxer - Convert GitHub-flavored Markdown to Microsoft Word documents."""

import argparse
import sys
from pathlib import Path

from docxer.converter import convert_file, convert_markdown_to_docx


__version__ = "0.1.0"
__all__ = ["convert_file", "convert_markdown_to_docx", "main"]


def main() -> None:
    """Entry point for the docxer CLI."""
    parser = argparse.ArgumentParser(
        prog="docxer",
        description="Convert GitHub-flavored Markdown to Microsoft Word documents.",
    )
    parser.add_argument(
        "input",
        type=str,
        help="Input markdown file path",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output .docx file path (default: input filename with .docx extension)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix(".docx")

    try:
        convert_file(str(input_path), str(output_path))
        print(f"Successfully converted '{input_path}' to '{output_path}'")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
