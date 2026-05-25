---
name: am-grill-docs
description: Use when auditing documentation in Astra Monitoring — "проверь доки X", "прожарь документацию", "найди неточности", "audit docs", "doc review". Triggers on documentation accuracy and quality questions.
---

# Audit Documentation

## Overview

Cross-reference documentation against actual source code to find inaccuracies, outdated information, and missing content. The code is the source of truth — docs must match it.

## When to Use

- User asks to check or audit documentation
- User suspects docs are outdated or inaccurate
- User wants to verify docs match current implementation

## When NOT to Use

- Researching how a feature works → use `am-research`
- Evaluating a feature idea → use `am-grill-feature`
- Writing new requirements → use `am-write-specs`

## Process

### 1. Identify target scope

Determine what documentation to audit:
- **Service profiles**: `meta/repos/<service>.md`
- **Architecture docs**: `analytics-hub/master_docs/Архитектура/`, `analytics-hub/docs/architecture/`
- **Requirements**: `analytics-hub/docs/requirements/`
- **Specifications**: `analytics-hub/docs/specifications/`
- **Per-repo AGENTS.md**: in each service directory
- **User docs**: `docs/` (Sphinx source)

The user may specify a single service, a feature area, or a specific doc file.

### 2. Ensure code is current

Run `sync-repos.sh --force` (or inform the user to run it) so that code reflects latest state.

### 3. Read the documentation

Read the target documentation thoroughly. Extract all claims:
- File paths mentioned
- API endpoints described
- Dependencies listed
- Architecture statements
- Configuration options
- Build/test commands

### 4. Read the actual code

For each claim in the docs, verify against source:
- **Paths**: Do the mentioned directories/files exist?
- **Dependencies**: Check go.mod, package.json, pyproject.toml — are deps current?
- **API**: Grep for actual route definitions, handler registrations
- **Structure**: Compare doc's directory listing with actual `ls`
- **Commands**: Check Makefile/package.json scripts — do they exist?
- **Architecture**: Compare described flow with actual import/call chains

### 5. Categorize findings

```
## Audit Report: [target]

### Critical (misleading/will break things)
- [ ] [doc path]: [what's wrong] → should be [correct info]

### High (outdated but not breaking)
- [ ] ...

### Medium (minor inaccuracies)
- [ ] ...

### Low (style, missing context)
- [ ] ...

### Missing (not documented but should be)
- [ ] ...
```

### 6. Propose fixes

For each finding, provide:
- File path and approximate location
- Current (wrong) text
- Proposed correction
- How to verify the correction

## What to look for

| Category | Examples |
|---|---|
| **Stale paths** | Directory renamed, file moved, package restructured |
| **Missing deps** | New dependencies added but not documented |
| **Removed deps** | Dependencies removed but still listed |
| **Wrong commands** | Makefile targets renamed, new scripts added |
| **API drift** | Endpoints changed, request/response format updated |
| **Architecture drift** | Service boundaries changed, new services added |
| **Version references** | "v2.38.0" but now on v2.40.x |
| **Missing features** | Features implemented but not documented |

## Rules

- **Code is truth.** If docs and code disagree, code wins.
- Don't flag stylistic issues as critical. Focus on factual inaccuracies.
- If you can't verify something (code too complex, would take too long), mark as [UNVERIFIED] rather than guessing.
- Prioritize findings — a PM doesn't need 50 minor issues, they need the 5 that matter.
- When proposing fixes, be specific enough that someone could apply them without re-investigating.
