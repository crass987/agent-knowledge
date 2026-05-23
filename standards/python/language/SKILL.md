---
name: python-language
description: Python language conventions and idioms
---

# Python Language Standards

## Style

- Follow PEP 8. Use `ruff` for linting and formatting.
- Python 3.10+ baseline. Use modern syntax: `match/case`, `X | Y` union types, `TypeAlias`.
- Type hints on all public functions. Use `from __future__ import annotations` for forward refs.
- Max line length: 120.

## Project structure

- `src/` layout for libraries (`src/package_name/`).
- Single `pyproject.toml` for build config, deps, and tool settings.
- Tests in `tests/` mirroring source structure.

## Dependencies

- Pin dependencies in production: `requirements.txt` with hashes or `poetry.lock`.
- Separate dev dependencies (`pytest`, `ruff`, `mypy`) from runtime.

## Patterns

- Use `pathlib.Path` instead of `os.path`.
- Use f-strings, not `.format()` or `%`.
- Prefer `dataclasses` or `pydantic` models over raw dicts for structured data.
- Use `logging` module, never `print()` for runtime output.
- Context managers (`with`) for resources (files, connections, locks).

## Error handling

- Use specific exception types, never bare `except:`.
- Let unexpected exceptions propagate — don't swallow them.
- Use `raise ... from err` to preserve traceback chains.
