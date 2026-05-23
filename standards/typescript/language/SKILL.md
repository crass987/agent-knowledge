---
name: typescript-language
description: TypeScript language conventions and best practices
---

# TypeScript Language Standards

## Style

- Use `eslint` with `@typescript-eslint` plugin. Use `prettier` for formatting.
- Strict mode: `"strict": true` in `tsconfig.json`.
- Prefer `interface` for object shapes, `type` for unions and utilities.
- Use `enum` only for open-ended sets; prefer union types for fixed sets: `'active' | 'inactive'`.

## Types

- No `any`. Use `unknown` when type is truly unknown, then narrow with type guards.
- Use const assertions for literal types: `as const`.
- Use generics for reusable functions — avoid function overloads unless the return type varies by input.
- Prefer branded types for domain IDs: `type UserId = string & { __brand: 'UserId' }`.

## Patterns

- Use `async/await` over raw promises.
- Use `Record<string, T>` over `{ [key: string]: T }`.
- Use `Readonly<T>` or `as const` for immutable data.
- Use optional chaining (`?.`) and nullish coalescing (`??`).

## Module system

- Use ES modules (`"type": "module"` in `package.json` or `.mts` extension).
- Use barrel files (`index.ts`) sparingly — prefer direct imports.
- Keep imports organized: node builtins → external packages → internal modules.

## Project structure

- `src/` for source, `tests/` or `__tests__/` for tests.
- One component/hook/module per file.
- Co-locate tests: `Component.tsx` + `Component.test.tsx`.
