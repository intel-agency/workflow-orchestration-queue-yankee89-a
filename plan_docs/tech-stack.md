# Technology Stack - workflow-orchestration-queue (OS-APOW)

**Last Updated:** 2026-03-20

## Overview

This document defines the technology stack for the workflow-orchestration-queue system, a headless agentic orchestration platform that transforms GitHub Issues into autonomous AI execution orders.

---

## Runtime & Languages

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.12+ | Primary language for Orchestrator, API Webhook receiver, and all system logic |
| **PowerShell Core (pwsh)** | Latest | Shell Bridge Scripts, Auth synchronization, cross-platform CLI |
| **Bash** | Latest | Shell Bridge Scripts, container orchestration |

---

## Web Framework & API

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | Latest | High-performance async web framework for Webhook Notifier ("The Ear") |
| **Uvicorn** | Latest | ASGI web server for serving FastAPI application in production |
| **Pydantic** | Latest | Strict data validation, settings management, and schema definitions |

---

## HTTP & Networking

| Technology | Version | Purpose |
|------------|---------|---------|
| **httpx** | Latest | Async HTTP client for GitHub REST API calls without blocking event loop |

---

## Package Management

| Technology | Version | Purpose |
|------------|---------|---------|
| **uv** | 0.10.9+ | Rust-based Python package installer and dependency resolver (faster than pip/poetry) |
| **pip** | (via uv) | Fallback package installer |

---

## Containerization & Infrastructure

| Technology | Version | Purpose |
|------------|---------|---------|
| **Docker** | Latest | Core worker execution engine, sandboxing, environment consistency |
| **Docker Compose** | Latest | Multi-container orchestration for complex scenarios |
| **DevContainers** | Latest | Reproducible development and worker environments |

---

## AI/Agent Runtime

| Technology | Version | Purpose |
|------------|---------|---------|
| **opencode CLI** | 1.2.24+ | AI agent runtime for executing markdown-based instruction modules |
| **ZhipuAI GLM-5** | Latest | Primary LLM model via ZHIPU_API_KEY |

---

## Testing

| Technology | Version | Purpose |
|------------|---------|---------|
| **pytest** | Latest | Python testing framework |
| **pytest-asyncio** | Latest | Async test support |

---

## Logging & Observability

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python logging** | Built-in | Structured logging via StreamHandler for console output |
| **Docker logs** | Built-in | Container runtime log capture |

---

## Security

| Technology | Purpose |
|------------|---------|
| **HMAC SHA256** | Webhook signature verification |
| **GitHub App Installation Tokens** | Scoped, ephemeral authentication |
| **Regex Credential Scrubbing** | Secret removal from public logs |

---

## Development Tools

| Technology | Version | Purpose |
|------------|---------|---------|
| **git** | Latest | Version control |
| **GitHub CLI (gh)** | Latest | GitHub API interactions |
| **MCP Servers** | Latest | Model Context Protocol for sequential thinking and memory |

---

## Key Dependencies (pyproject.toml)

```toml
[project]
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
]
```

---

## Environment Variables (Required)

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub App Installation Token or PAT | **Yes** |
| `GITHUB_REPO` | Target repository (org/repo format) | **Yes** |
| `SENTINEL_BOT_LOGIN` | GitHub login of bot account for locking | **Yes** |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBHOOK_SECRET` | - | HMAC secret for webhook verification (Phase 2) |

---

## Design Principles

1. **Script-First Integration:** Use existing shell scripts (`devcontainer-opencode.sh`) instead of reimplementing container management
2. **State Visibility:** Store state in GitHub via labels and comments ("Markdown as a Database")
3. **Self-Bootstrapping:** System builds itself after initial manual seeding
4. **Polling-First Resiliency:** Polling as primary discovery; webhooks as optimization
