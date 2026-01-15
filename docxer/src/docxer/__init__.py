"""Docxer - Convert GitHub-flavored Markdown to Microsoft Word documents."""

import argparse
import shutil
import sys
from pathlib import Path

from docxer.converter import convert_file, convert_markdown_to_docx
from docxer.generator import (
    ModelClient,
    PromptContext,
    StubModelClient,
    generate_content,
    load_prompt,
    render_instructions,
)
from docxer.orchestrator import generate_documents, run_project
from docxer.project import DocumentKind, ProjectConfig, Structure


__version__ = "0.1.0"
__all__ = [
    # Converter
    "convert_file",
    "convert_markdown_to_docx",
    # Generator
    "generate_content",
    "load_prompt",
    "render_instructions",
    "ModelClient",
    "PromptContext",
    "StubModelClient",
    # Orchestrator
    "generate_documents",
    "run_project",
    # Project
    "DocumentKind",
    "ProjectConfig",
    "Structure",
    # CLI
    "main",
]


def cmd_convert(args: argparse.Namespace) -> None:
    """Handle the convert subcommand."""
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


def cmd_generate(args: argparse.Namespace) -> None:
    """Handle the generate subcommand."""
    from docxer.orchestrator import run_project

    project_path = Path(args.project)

    if not project_path.exists():
        print(f"Error: Project file '{project_path}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        results = run_project(project_path, verbose=not args.quiet)
        if args.quiet:
            for path in results:
                print(path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_init(args: argparse.Namespace) -> None:
    """Handle the init subcommand."""
    project_dir = Path(args.name)

    if project_dir.exists():
        print(f"Error: Directory '{project_dir}' already exists.", file=sys.stderr)
        sys.exit(1)

    try:
        # Create project structure
        project_dir.mkdir(parents=True)
        (project_dir / "seed").mkdir()
        (project_dir / "output").mkdir()
        (project_dir / "prompts").mkdir()

        # Find the package prompts directory
        package_dir = Path(__file__).parent.parent.parent  # docxer/src/docxer -> docxer
        prompts_src = package_dir.parent / "prompts"  # docxer/../prompts

        # Copy default prompts if available
        if prompts_src.exists():
            for prompt_file in prompts_src.glob("*.yaml"):
                shutil.copy(prompt_file, project_dir / "prompts" / prompt_file.name)
            prompts_path = "prompts"
        else:
            # Use relative path to package prompts as fallback
            prompts_path = str(prompts_src)

        # Create sample seed file
        seed_file = project_dir / "seed" / "sample-data.md"
        seed_file.write_text(
            """# Sample Seed Data

This file contains seed data that will be used to generate realistic documents.

## Company Information

- **Company Name**: Acme Corporation
- **Founded**: 1985
- **Headquarters**: Springfield, IL
- **Employees**: 5,000+

## Key Facts

Add your domain-specific facts, policies, procedures, and other information here.
The document generator will use this content to create realistic documents that
can answer questions about these topics.

## Tips

- Be specific with names, dates, and numbers
- Include realistic scenarios and examples
- Cover the topics that your goals reference
""",
            encoding="utf-8",
        )

        # Create project.yaml
        project_file = project_dir / "project.yaml"
        project_file.write_text(
            f"""# Docxer Project Configuration
name: {args.name}
description: Auto-generated project for document generation

# Directory containing seed markdown files
seed_data_dir: seed

# Output directory for generated documents
output_dir: output

# Goals: What questions should these documents help answer?
goals:
  - Answer general questions about company policies
  - Provide information for employee onboarding

# Document kinds to generate
kinds:
  - name: memo
    prompt: {prompts_path}/memo.yaml
    count: 2
    structure:
      has_tables: false
      section_count: 1
      target_length: short

  - name: policy
    prompt: {prompts_path}/policy.yaml
    count: 1
    structure:
      has_tables: true
      section_count: 4
      target_length: long

  - name: faq
    prompt: {prompts_path}/faq.yaml
    count: 1
    structure:
      has_tables: false
      section_count: 1
      target_length: medium
""",
            encoding="utf-8",
        )

        print(f"Created project '{args.name}' with structure:")
        print(f"  {project_dir}/")
        print(f"  ├── project.yaml")
        print(f"  ├── seed/")
        print(f"  │   └── sample-data.md")
        print(f"  ├── prompts/")
        if prompts_src.exists():
            for prompt_file in sorted((project_dir / "prompts").glob("*.yaml")):
                print(f"  │   └── {prompt_file.name}")
        print(f"  └── output/")
        print()
        print("Next steps:")
        print(f"  1. Edit seed/*.md files with your domain data")
        print(f"  2. Customize project.yaml goals and kinds")
        print(f"  3. Run: docxer generate {project_dir}/project.yaml")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Entry point for the docxer CLI."""
    parser = argparse.ArgumentParser(
        prog="docxer",
        description="Convert GitHub-flavored Markdown to Microsoft Word documents.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Convert command (default behavior)
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert a single markdown file to Word",
    )
    convert_parser.add_argument(
        "input",
        type=str,
        help="Input markdown file path",
    )
    convert_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output .docx file path (default: input filename with .docx extension)",
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate documents from a project configuration",
    )
    generate_parser.add_argument(
        "project",
        type=str,
        help="Path to project YAML configuration file",
    )
    generate_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only output generated file paths",
    )

    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new document generation project",
    )
    init_parser.add_argument(
        "name",
        type=str,
        help="Name of the project directory to create",
    )

    args = parser.parse_args()

    # Handle commands
    if args.command == "convert":
        cmd_convert(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "init":
        cmd_init(args)
    elif args.command is None:
        # Backward compatibility: if no subcommand, treat first positional as input file
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            # Re-parse with convert as implicit command
            sys.argv.insert(1, "convert")
            main()
        else:
            parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
