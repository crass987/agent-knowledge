---
name: typescript-react
description: React + TypeScript conventions
---

# React + TypeScript Standards

## Component design

- Functional components only. No class components.
- One component per file. File name matches component name: `UserCard.tsx`.
- Props: define an interface named `ComponentNameProps`.
- Destructure props in function signature: `function UserCard({ name, email }: UserCardProps)`.

## Hooks

- Custom hooks prefix: `use` (e.g., `useAuth`, `useDebounce`).
- Keep hooks focused on one concern.
- Return tuples for simple hooks, objects for complex ones.
- Use `useCallback` only when passing callbacks to optimized children. Don't wrap everything.

## State management

- Start with `useState` and `useReducer`.
- Lift state to the nearest common parent.
- Use context for truly global state (auth, theme). Avoid context for frequently changing data.
- Reach for external state libraries (Zustand, Jotai) only when prop drilling becomes a real problem.

## Rendering

- Prefer conditional rendering with `&&` and ternaries over `switch` for simple cases.
- Use `key` prop with stable IDs, never array indices for dynamic lists.
- Memoize expensive computations with `useMemo`. Don't memoize simple values.

## File structure

```
ComponentName/
├── ComponentName.tsx
├── ComponentName.test.tsx
├── ComponentName.module.css  (or .styles.ts)
└── index.ts                  (re-export)
```
