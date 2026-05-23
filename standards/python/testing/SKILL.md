---
name: python-testing
description: Python testing conventions
---

# Python Testing Standards

## Framework

- Use `pytest` as the test framework.
- Structure: `tests/` directory mirroring `src/` layout.
- File naming: `test_<module>.py`. Function naming: `test_<behavior>`.

## Test design

- One assertion per concept. Multiple assertions are fine if they test the same behavior.
- Use `pytest.parametrize` for data-driven tests instead of loops.
- Use fixtures for setup, not module-level globals.
- Mark slow tests with `@pytest.mark.slow` and integration tests with `@pytest.mark.integration`.

## Mocking

- Prefer real implementations over mocks. Use test databases, in-memory services.
- When mocking is necessary: mock at the boundary (external API, filesystem), not internal modules.
- Use `pytest-mock` for cleaner mock lifecycle.

## Coverage

- Target 80%+ coverage for business logic.
- Don't chase 100% — exclude trivial code (dataclasses, constants).
- Run with `pytest --cov --cov-fail-under=80` in CI.

## Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
markers = ["slow: slow tests", "integration: requires external services"]
```
