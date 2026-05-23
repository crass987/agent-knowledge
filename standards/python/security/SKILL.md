---
name: python-security
description: Python security best practices
---

# Python Security Standards

## Input validation

- Validate and sanitize all external input (HTTP params, file uploads, env vars).
- Use `pydantic` or similar for schema validation at API boundaries.
- Never interpolate user input into SQL — use parameterized queries.
- Never interpolate user input into shell commands — use `subprocess` with args list.

## Dependencies

- Run `pip-audit` or `safety check` in CI to catch known vulnerabilities.
- Pin all dependencies. Review changelogs before upgrading.

## Secrets

- Never hardcode secrets. Use environment variables or a secrets manager.
- Add `.env` to `.gitignore`. Provide `.env.example` with placeholder values.
- Use `python-dotenv` for local development only.

## Authentication

- Use established libraries (e.g., `authlib`, `python-jose`) for JWT/OAuth.
- Store password hashes with `bcrypt` or `argon2` — never plain text or MD5.
- Set secure cookie flags: `HttpOnly`, `Secure`, `SameSite`.

## Common pitfalls

- Deserialization: avoid `pickle` with untrusted data. Use `json` or `msgspec`.
- Path traversal: validate file paths with `Path.resolve()` and check they stay within expected directories.
- YAML: use `yaml.safe_load()`, not `yaml.load()`.
