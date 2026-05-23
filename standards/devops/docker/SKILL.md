---
name: devops-docker
description: Docker and container conventions
---

# Docker Standards

## Dockerfile

- Use multi-stage builds to keep final images small.
- Pin base image versions: `FROM node:20.11-alpine`, not `FROM node:latest`.
- Order layers from least to most frequently changed (base → system deps → app deps → app code).
- Use `.dockerignore` to exclude `.git`, `node_modules`, `.env`, `__pycache__`.
- Run as non-root user:
  ```dockerfile
  RUN adduser -D appuser
  USER appuser
  ```

## docker-compose

- Use `docker-compose.yml` for local development, not production orchestration.
- Define `healthcheck` for services that depend on each other.
- Use `depends_on` with `condition: service_healthy` for startup order.
- Keep environment-specific values in `.env` files, not in the compose file.

## Image management

- Tag images with semantic versions, not `latest`.
- Use `docker scan` or `trivy` for vulnerability scanning in CI.
- Clean up dangling images regularly: `docker image prune`.

## Common pitfalls

- Don't store secrets in Dockerfiles or compose files — use Docker secrets or env vars at runtime.
- Don't install unnecessary packages in production images (no `curl`, `vim`, `git`).
- Set appropriate `HEALTHCHECK` instructions for long-running services.
