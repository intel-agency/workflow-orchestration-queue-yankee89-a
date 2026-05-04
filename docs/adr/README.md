# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records for the
**workflow-orchestration-queue (OS-APOW)** project.

## What is an ADR?

An Architecture Decision Record (ADR) captures a single, significant
architectural decision along with its context and consequences. ADRs
provide a permanent record of *why* a particular approach was chosen,
making it easier for future contributors to understand the reasoning.

## ADR Format

Each ADR follows this naming convention:

```
NNNN-short-title.md
```

Where `NNNN` is a zero-padded sequence number (e.g., `0001`).

### Template

```markdown
# NNNN. [Short Title]

## Status

[Proposed | Accepted | Deprecated | Superseded by ADR-NNNN]

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?
```

## Index of ADRs

| ADR | Title | Status |
|-----|-------|--------|
| — | *(No ADRs yet — add them as significant decisions are made)* | — |

## Guidelines

- Create an ADR when making a significant architectural or technology decision.
- ADRs are immutable once accepted — create a new ADR to supersede an old one.
- Keep ADRs concise and focused on a single decision.
- Reference related ADRs when applicable.
