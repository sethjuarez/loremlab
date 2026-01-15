---
applyTo: "**/*.py"
description: Instructions for Python projects using uv package manager
---

# Python Project Instructions (uv)

This project uses [uv](https://docs.astral.sh/uv/) for Python package and project management.

## Project Setup

- Use `uv init` to initialize new Python projects
- Project configuration is defined in `pyproject.toml`
- Python version is specified in `.python-version`
- Dependencies are locked in `uv.lock` (commit this file to version control)

## Running Code

- **Always use `uv run` to execute Python scripts**: `uv run main.py`
- `uv run` ensures the environment is synchronized with the lockfile before execution
- For commands with arguments: `uv run -- command --flag value`
- Alternative: manually sync and activate the environment:
  ```
  uv sync
  .venv\Scripts\activate  # Windows
  source .venv/bin/activate  # macOS/Linux
  ```

## Managing Dependencies

- **Add dependencies**: `uv add <package>` (e.g., `uv add requests`)
- **Add with version constraint**: `uv add 'requests==2.31.0'`
- **Add from git**: `uv add git+https://github.com/owner/repo`
- **Add dev dependencies**: `uv add --dev pytest`
- **Remove dependencies**: `uv remove <package>`
- **Upgrade a package**: `uv lock --upgrade-package <package>`
- **Sync environment**: `uv sync`

## Project Structure

```
project/
├── .venv/              # Virtual environment (auto-created, do not commit)
├── .python-version     # Python version for the project
├── pyproject.toml      # Project metadata and dependencies
├── uv.lock             # Lockfile (commit this)
├── main.py             # Entry point
└── README.md
```

## Building & Publishing

- **Build distributions**: `uv build` (creates `dist/` with wheel and sdist)
- **Check version**: `uv version`

## Best Practices

- Always commit `uv.lock` to version control for reproducible builds
- Use `uv run` instead of activating the virtual environment manually
- Specify version constraints in `pyproject.toml` for production dependencies
- Use `uv add --dev` for development-only dependencies (testing, linting, etc.)
- Never edit `uv.lock` manually - it's managed by uv

