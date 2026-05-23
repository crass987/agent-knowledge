---
name: go-language
description: Go language conventions and idioms
---

# Go Language Standards

## Style

- Run `gofmt` (or `goimports`) on all files. No configuration debates.
- Follow [Effective Go](https://go.dev/doc/effective_go) and [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments).
- Use `golangci-lint` with default linters enabled.

## Project structure

- Follow the standard Go project layout for larger projects.
- `cmd/` for entrypoints, `internal/` for private packages, `pkg/` for public packages.
- One package per directory. Package name matches directory name.

## Error handling

- Always check errors. Never use `_` for error returns unless explicitly safe.
- Wrap errors with context: `fmt.Errorf("reading config: %w", err)`.
- Use `errors.Is()` and `errors.As()` for error matching.
- Define sentinel errors for API boundaries: `var ErrNotFound = errors.New("not found")`.

## Concurrency

- Prefer channels over shared memory. Prefer `sync` primitives over channels for simple coordination.
- Always have a way to stop goroutines (context cancellation, done channel).
- Use `sync.WaitGroup` to wait for goroutine completion in tests.
- Use `sync.Once` for one-time initialization.

## Testing

- Use the standard `testing` package. Table-driven tests with `t.Run`.
- Test file naming: `xxx_test.go` in the same package (white-box) or same directory with `_test` package (black-box).
- Use `testify` only for assertions if the team prefers it — not required.

## Common patterns

- Use `context.Context` as the first parameter in all public functions that do I/O.
- Return structs, not interfaces. Accept interfaces, not structs.
- Keep interfaces small. Single-method interfaces are idiomatic.
- Use `io.Reader` / `io.Writer` for streaming data.
