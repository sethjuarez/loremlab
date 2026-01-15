"""AgentSchema prompt loader and content generator."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import yaml
from agentschema.core import AgentDefinition, PromptAgent


@dataclass
class PromptContext:
    """Context variables for prompt rendering."""

    seed_content: str
    goal: str
    structure: str
    kind_name: str
    document_number: int
    additional_context: dict[str, Any] | None = None


def load_prompt(yaml_path: str | Path) -> PromptAgent:
    """Load an AgentSchema PromptAgent from a YAML file.

    Args:
        yaml_path: Path to the AgentSchema YAML prompt file.

    Returns:
        A PromptAgent instance.

    Raises:
        ValueError: If the loaded agent is not a PromptAgent.
    """
    yaml_path = Path(yaml_path)
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    agent = AgentDefinition.load(data)

    if not isinstance(agent, PromptAgent):
        raise ValueError(
            f"Expected a PromptAgent, got {type(agent).__name__}. "
            f"Ensure the YAML file has 'kind: prompt'."
        )

    return agent


def render_instructions(agent: PromptAgent, context: PromptContext) -> str:
    """Render agent instructions with mustache-style variable substitution.

    Args:
        agent: The PromptAgent containing instructions.
        context: Context variables for rendering.

    Returns:
        Rendered instructions string.
    """
    instructions = agent.instructions or ""

    # Build substitution map
    variables = {
        "seed_content": context.seed_content,
        "goal": context.goal,
        "structure": context.structure,
        "kind_name": context.kind_name,
        "document_number": str(context.document_number),
    }

    if context.additional_context:
        variables.update({k: str(v) for k, v in context.additional_context.items()})

    # Simple mustache-style replacement: {{variable}}
    rendered = instructions
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)

    return rendered


class ModelClient(Protocol):
    """Protocol for model clients that can generate content."""

    def generate(self, prompt: str) -> str:
        """Generate content from a prompt."""
        ...


class StubModelClient:
    """Stub model client that returns the rendered prompt for inspection."""

    def __init__(self, return_stub_content: bool = True) -> None:
        self.return_stub_content = return_stub_content
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        """Return stub content with the rendered prompt embedded."""
        self.last_prompt = prompt

        if self.return_stub_content:
            # Return a placeholder markdown document
            return f"""# Generated Document

> **Note**: This is stub content. Replace StubModelClient with a real model client to generate actual content.

## Rendered Prompt

The following prompt would be sent to the model:

---

{prompt}

---

## Placeholder Content

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor 
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud 
exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

### Section 1

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu 
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in 
culpa qui officia deserunt mollit anim id est laborum.

### Section 2

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium 
doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore 
veritatis et quasi architecto beatae vitae dicta sunt explicabo.
"""
        else:
            # Return just a marker for testing
            return "<!-- STUB: Model call would happen here -->"


def generate_content(
    prompt_path: str | Path,
    context: PromptContext,
    client: ModelClient | None = None,
) -> str:
    """Generate document content using an AgentSchema prompt.

    Args:
        prompt_path: Path to the AgentSchema YAML prompt file.
        context: Context variables for prompt rendering.
        client: Model client for content generation. Defaults to StubModelClient.

    Returns:
        Generated markdown content.
    """
    if client is None:
        client = StubModelClient()

    # Load the prompt using the agentschema package
    agent = load_prompt(prompt_path)

    # Render the instructions with context
    rendered_prompt = render_instructions(agent, context)

    # Generate content
    return client.generate(rendered_prompt)
