"""Batch document generation orchestrator."""

import re
from pathlib import Path
from typing import AsyncIterator

from docxer.converter import convert_markdown_to_docx
from docxer.generator import (
    ModelClient,
    PromptContext,
    StubModelClient,
    generate_content,
    generate_short_title,
)
from docxer.project import ProjectConfig


def _extract_title(markdown: str) -> str | None:
    """Extract the first heading from markdown content.

    Args:
        markdown: The markdown content.

    Returns:
        The title text, or None if no heading found.
    """
    # Look for first # heading
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def _sanitize_filename(title: str) -> str:
    """Convert a title to a safe filename.

    Args:
        title: The document title.

    Returns:
        A sanitized filename (without extension).
    """
    # Remove or replace invalid filename characters
    filename = re.sub(r'[<>:"/\\|?*]', "", title)
    # Replace spaces and multiple dashes with single dash
    filename = re.sub(r"[\s_]+", "-", filename)
    filename = re.sub(r"-+", "-", filename)
    # Remove leading/trailing dashes
    filename = filename.strip("-")
    # Limit length
    if len(filename) > 100:
        filename = filename[:100].rsplit("-", 1)[0]
    return filename.lower()


async def generate_documents(
    config: ProjectConfig,
    client: ModelClient | None = None,
    verbose: bool = False,
) -> AsyncIterator[tuple[str, Path]]:
    """Generate all documents defined in a project configuration.

    Args:
        config: Project configuration.
        client: Model client for content generation. Defaults to StubModelClient.
        verbose: Print progress information.

    Yields:
        Tuples of (kind_name, output_path) for each generated document.
    """
    if client is None:
        client = StubModelClient()

    # Ensure output directory exists
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load seed data once
    seed_content = config.load_seed_data()
    goals_text = (
        "\n".join(f"- {goal}" for goal in config.goals)
        if config.goals
        else "No specific goals defined."
    )

    if verbose:
        print(f"Project: {config.name}")
        print(f"Seed data loaded from: {config.seed_data_dir}")
        print(f"Output directory: {output_dir}")
        print(f"Total documents to generate: {config.get_total_document_count()}")
        print()

    document_number = 0
    generated_titles: list[str] = []  # Track titles to avoid duplicates

    for kind in config.kinds:
        if verbose:
            print(f"Generating {kind.count} '{kind.name}' document(s)...")

        for i in range(kind.count):
            document_number += 1

            # Build context for this document
            context = PromptContext(
                seed_content=seed_content,
                goal=goals_text,
                structure=kind.structure.to_prompt_context(),
                kind_name=kind.name,
                document_number=document_number,
                previous_titles=generated_titles.copy() if generated_titles else None,
            )

            # Generate markdown content (use get_prompt_path to resolve built-in prompts)
            markdown_content = await generate_content(
                kind.get_prompt_path(), context, client
            )

            # Convert to Word document
            doc = convert_markdown_to_docx(markdown_content)

            # Generate a short title using LLM, fall back to extracted title or numbered
            title = _extract_title(markdown_content)
            if title:
                generated_titles.append(title)  # Track full title for context

            # Use LLM to generate a short filename
            base_name: str | None = None
            try:
                short_title = await generate_short_title(markdown_content, client)
                if short_title:
                    base_name = _sanitize_filename(short_title)
                elif title:
                    base_name = _sanitize_filename(title)
            except Exception:
                # Fall back to extracted title if LLM fails
                if title:
                    base_name = _sanitize_filename(title)

            if base_name:
                filename = f"{base_name}.docx"
                # Handle duplicates by adding number suffix
                output_path = output_dir / filename
                counter = 1
                while output_path.exists():
                    counter += 1
                    filename = f"{base_name}-{counter}.docx"
                    output_path = output_dir / filename
            else:
                filename = f"{kind.name}_{document_number:03d}.docx"
                output_path = output_dir / filename

            doc.save(str(output_path))

            if verbose:
                print(f"  Created: {output_path}")

            yield kind.name, output_path

    if verbose:
        print()
        print(f"Done! Generated {document_number} document(s).")


async def run_project(
    project_path: str | Path,
    client: ModelClient | None = None,
    verbose: bool = True,
) -> list[Path]:
    """Run document generation for a project.

    Args:
        project_path: Path to the project YAML configuration file.
        client: Model client for content generation.
        verbose: Print progress information.

    Returns:
        List of paths to generated documents.
    """
    config = ProjectConfig.from_yaml(project_path)
    results = [item async for item in generate_documents(config, client, verbose)]
    return [path for _, path in results]
