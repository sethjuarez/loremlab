"""Project configuration schema for document generation."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Structure(BaseModel):
    """Document structure configuration."""

    has_tables: bool = Field(default=False, description="Whether to include tables")
    section_count: int = Field(default=1, ge=1, description="Number of sections")
    target_length: str = Field(
        default="medium",
        description="Target length: 'short' (~200 words), 'medium' (~500 words), 'long' (~1000 words)",
    )

    def to_prompt_context(self) -> str:
        """Convert structure to prompt-friendly text."""
        length_map = {
            "short": "approximately 200 words",
            "medium": "approximately 500 words",
            "long": "approximately 1000 words",
        }
        parts = [
            f"- Target length: {length_map.get(self.target_length, self.target_length)}",
            f"- Number of sections: {self.section_count}",
            f"- Include tables: {'yes' if self.has_tables else 'no'}",
        ]
        return "\n".join(parts)


class DocumentKind(BaseModel):
    """Configuration for a specific document kind/type."""

    name: str = Field(description="Kind name (e.g., 'memo', 'policy', 'faq')")
    prompt: str | None = Field(
        default=None,
        description="Path to AgentSchema prompt YAML file. If not specified, uses built-in prompt.",
    )
    structure: Structure = Field(
        default_factory=Structure, description="Default structure for this kind"
    )
    count: int = Field(
        default=1, ge=1, description="Number of documents of this kind to generate"
    )

    def get_prompt_path(self) -> str:
        """Get the prompt path, using built-in prompt if not specified."""
        if self.prompt:
            return self.prompt

        # Get the prompts directory from the package
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        builtin_prompt = prompts_dir / f"{self.name}.yaml"
        if builtin_prompt.exists():
            return str(builtin_prompt)
        raise ValueError(
            f"No prompt specified and no built-in prompt found for kind '{self.name}'. "
            f"Available kinds: memo, policy, report, faq, email"
        )

    @classmethod
    def with_defaults(cls, name: str, prompt: str) -> "DocumentKind":
        """Create a DocumentKind with sensible defaults based on name."""
        defaults: dict[str, dict[str, Any]] = {
            "memo": {
                "structure": Structure(
                    has_tables=False, section_count=1, target_length="short"
                )
            },
            "policy": {
                "structure": Structure(
                    has_tables=True, section_count=4, target_length="long"
                )
            },
            "report": {
                "structure": Structure(
                    has_tables=True, section_count=5, target_length="long"
                )
            },
            "faq": {
                "structure": Structure(
                    has_tables=False, section_count=1, target_length="medium"
                )
            },
            "email": {
                "structure": Structure(
                    has_tables=False, section_count=1, target_length="short"
                )
            },
        }
        kind_defaults = defaults.get(name, {})
        return cls(name=name, prompt=prompt, **kind_defaults)


class ProjectConfig(BaseModel):
    """Main project configuration for document generation."""

    name: str = Field(description="Project name")
    description: str = Field(default="", description="Project description")
    seed_data_dir: str = Field(description="Directory containing seed markdown files")
    output_dir: str = Field(
        default="output", description="Output directory for generated documents"
    )
    goals: list[str] = Field(
        default_factory=list,
        description="Goals these documents should satisfy (e.g., 'answer questions about PTO')",
    )
    kinds: list[DocumentKind] = Field(
        default_factory=list, description="Document kinds to generate"
    )

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "ProjectConfig":
        """Load project configuration from a YAML file."""
        import yaml

        yaml_path = Path(yaml_path)
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Resolve relative paths based on yaml file location
        base_dir = yaml_path.parent

        if "seed_data_dir" in data:
            seed_path = Path(data["seed_data_dir"])
            if not seed_path.is_absolute():
                data["seed_data_dir"] = str(base_dir / seed_path)

        if "output_dir" in data:
            output_path = Path(data["output_dir"])
            if not output_path.is_absolute():
                data["output_dir"] = str(base_dir / output_path)

        # Resolve prompt paths in kinds (only if explicitly specified)
        if "kinds" in data:
            for kind in data["kinds"]:
                if "prompt" in kind and kind["prompt"]:
                    prompt_path = Path(kind["prompt"])
                    if not prompt_path.is_absolute():
                        kind["prompt"] = str(base_dir / prompt_path)

        return cls(**data)

    def load_seed_data(self) -> str:
        """Load all markdown files from seed_data_dir and concatenate."""
        seed_path = Path(self.seed_data_dir)
        if not seed_path.exists():
            raise FileNotFoundError(f"Seed data directory not found: {seed_path}")

        seed_files = sorted(seed_path.glob("*.md"))
        if not seed_files:
            raise ValueError(f"No markdown files found in {seed_path}")

        contents = []
        for file in seed_files:
            content = file.read_text(encoding="utf-8")
            contents.append(f"## Source: {file.name}\n\n{content}")

        return "\n\n---\n\n".join(contents)

    def get_total_document_count(self) -> int:
        """Get total number of documents to generate."""
        return sum(kind.count for kind in self.kinds)
