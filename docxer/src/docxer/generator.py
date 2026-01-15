"""AgentSchema prompt loader and content generator."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from docxer.foundry import get_openai_client
import yaml
from agentschema.core import AgentDefinition, PromptAgent
from dotenv import load_dotenv
from openai.types.responses import EasyInputMessageParam, ResponseInputItemParam


load_dotenv()


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


def parse_instructions(rendered: str) -> tuple[str, str]:
    """Parse rendered instructions into system and user messages.

    Instructions may contain 'system:' and 'user:' sections.
    If not found, the entire content is treated as a user message.

    Args:
        rendered: The rendered instructions string.

    Returns:
        Tuple of (system_message, user_message).
    """
    system_msg = ""
    user_msg = rendered

    # Look for system: and user: markers
    if "system:" in rendered.lower():
        # Find the start of system section
        lower = rendered.lower()
        system_start = lower.find("system:")

        # Find where user section starts (if present)
        user_start = lower.find("user:", system_start)

        if user_start != -1:
            # Extract system content (after "system:" marker)
            system_content_start = system_start + len("system:")
            system_msg = rendered[system_content_start:user_start].strip()

            # Extract user content (after "user:" marker)
            user_content_start = user_start + len("user:")
            user_msg = rendered[user_content_start:].strip()
        else:
            # Only system section, no user section
            system_content_start = system_start + len("system:")
            system_msg = rendered[system_content_start:].strip()
            user_msg = ""
    elif "user:" in rendered.lower():
        # Only user section
        lower = rendered.lower()
        user_start = lower.find("user:")
        user_content_start = user_start + len("user:")
        user_msg = rendered[user_content_start:].strip()

    return system_msg, user_msg


class ModelClient(Protocol):
    """Protocol for model clients that can generate content."""

    async def generate(self, prompt: str, model: str | None = None) -> str:
        """Generate content from a prompt.

        Args:
            prompt: The prompt to send to the model.
            model: Optional model identifier to use. Implementation decides default.
        """
        ...


class StubModelClient:
    """Stub model client that returns the rendered prompt for inspection."""

    def __init__(self, return_stub_content: bool = True) -> None:
        self.return_stub_content = return_stub_content
        self.last_prompt: str | None = None
        self.last_model: str | None = None

    async def generate(self, prompt: str, model: str | None = None) -> str:
        """Return stub content with the rendered prompt embedded."""
        self.last_prompt = prompt
        self.last_model = model

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


class FoundryModelClient:
    """Model client using Azure AI Foundry's Responses API."""

    DEFAULT_MODEL = "gpt-4o"

    def __init__(self) -> None:
        """Initialize the Foundry model client."""
        self.last_prompt: str | None = None
        self.last_model: str | None = None

    async def generate(self, prompt: str, model: str | None = None) -> str:
        """Generate content using the Responses API.

        Args:
            prompt: The prompt to send to the model (may contain system:/user: sections).
            model: Model identifier from prompt file. Falls back to DEFAULT_MODEL.

        Returns:
            The generated text content.
        """
        self.last_prompt = prompt
        self.last_model = model or self.DEFAULT_MODEL

        # Parse into system and user messages
        system_msg, user_msg = parse_instructions(prompt)

        # Build messages array with proper types
        messages: list[EasyInputMessageParam] = []
        if system_msg:
            messages.append(
                {"role": "system", "content": system_msg, "type": "message"}
            )
        if user_msg:
            messages.append({"role": "user", "content": user_msg, "type": "message"})

        # Fallback if no messages parsed
        if not messages:
            messages.append({"role": "user", "content": prompt, "type": "message"})

        client = await get_openai_client()

        # Cast to list[ResponseInputItemParam] for API compatibility
        input_messages = cast(list[ResponseInputItemParam], messages)

        try:
            response = await client.responses.create(
                model=self.last_model,
                input=input_messages,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to generate content with model '{self.last_model}': {e}"
            ) from e

        return response.output_text or ""


async def generate_content(
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

    # Extract model from prompt file if available
    model_id: str | None = None
    if agent.model and agent.model.id:
        model_id = agent.model.id

    # Render the instructions with context
    rendered_prompt = render_instructions(agent, context)

    # Generate content with the model from the prompt
    return await client.generate(rendered_prompt, model=model_id)
