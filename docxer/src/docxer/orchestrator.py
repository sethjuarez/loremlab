"""Batch document generation orchestrator."""

from pathlib import Path
from typing import AsyncIterator

from docxer.converter import convert_markdown_to_docx
from docxer.generator import (
    ModelClient,
    PromptContext,
    StubModelClient,
    generate_content,
)
from docxer.project import ProjectConfig


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
            )

            # Generate markdown content
            markdown_content = await generate_content(kind.prompt, context, client)

            # Convert to Word document
            doc = convert_markdown_to_docx(markdown_content)

            # Save document
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
