# AGENTS.md

<!--
  Formatting: Follows https://agents.md/ specification
  - Standard Markdown format
  - Agent-focused, actionable instructions
  - Commands have been validated
-->

## Project Overview

**workflow-orchestration-queue (OS-APOW)** is a headless agentic orchestration platform that transforms GitHub Issues into autonomous AI execution orders. The system shifts AI from a passive co-pilot to an autonomous background production service.

**Tech Stack:**
- **Language:** Python 3.12+
- **Framework:** FastAPI
- **Package Manager:** uv (Astral's fast Python package manager)
- **Testing:** pytest with pytest-asyncio
- **Linting:** ruff
- **Type Checking:** mypy (strict mode)
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions

**Architecture:** 4-Pillar Design
- **The Ear (Notifier):** FastAPI webhook receiver for GitHub events
- **The State (Queue):** GitHub Issues as database with label-based state machine
- **The Brain (Sentinel):** Async Python background service for polling and dispatch
- **The Hands (Worker):** DevContainer with opencode CLI for code execution

## Setup Commands

**Prerequisites:**
- Python 3.12+ in PATH
- uv installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker (for worker execution)
- PowerShell (for validation scripts)

**Bootstrap (First-time Setup):**
```bash
# 1. Install all dependencies (main + dev)
uv sync --extra dev

# 2. Copy environment template and configure
cp .env.example .env
# Edit .env with: GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO

# 3. Install dev tools for validation (optional but recommended)
pwsh -NoProfile -File ./scripts/install-dev-tools.ps1
```

**Run Services:**
```bash
# Run Sentinel service (requires .env configured)
uv run python -m src.orchestrator_sentinel

# Or use the installed entry point
uv run sentinel

# Run with Docker Compose
docker compose up sentinel

# Run Notifier (Phase 2)
docker compose --profile phase2 up notifier
```

## Project Structure

```
workflow-orchestration-queue-yankee89-a/
├── src/                        # MAIN APPLICATION SOURCE
│   ├── __init__.py
│   ├── orchestrator_sentinel.py # Sentinel: polling, claiming, dispatch
│   ├── notifier_service.py     # Notifier: FastAPI webhook receiver
│   ├── models/
│   │   ├── __init__.py
│   │   ├── work_item.py        # WorkItem, TaskType, WorkItemStatus
│   │   └── github_events.py    # Webhook payload schemas
│   └── queue/
│       ├── __init__.py
│       └── github_queue.py     # ITaskQueue + GitHubQueue implementation
├── tests/                      # PYTHON PYTEST TESTS
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures (sample_work_item, etc.)
│   ├── unit/
│   │   ├── test_github_queue.py
│   │   └── test_work_item.py
│   └── integration/
├── test/                       # INFRASTRUCTURE VALIDATION TESTS
│   ├── fixtures/               # Test fixtures for Pester/shell tests
│   ├── run-pester-tests.ps1    # Pester test runner
│   └── test-*.sh               # Shell-based validation scripts
├── scripts/
│   ├── validate.ps1            # Main validation script (CI and local)
│   ├── install-dev-tools.ps1   # Idempotent tool installer
│   └── gh-auth.ps1             # GitHub authentication helper
├── plan_docs/                  # Planning documents and reference implementations
├── docs/adr/                   # Architecture Decision Records
├── pyproject.toml              # Python project config (dependencies, tool settings)
├── uv.lock                    # Locked dependency versions
├── docker-compose.yml          # Local development: sentinel + notifier services
├── Dockerfile.sentinel         # Sentinel service container
├── Dockerfile.notifier         # Notifier service container
└── .env.example                # Environment variable template
```

**Key Files:**
| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies, pytest config, ruff config, mypy config |
| `src/orchestrator_sentinel.py` | Main entry point for Sentinel service |
| `src/queue/github_queue.py` | GitHub Issues as task queue |
| `src/models/work_item.py` | Core data models |
| `scripts/validate.ps1` | CI validation script |
| `.github/workflows/validate.yml` | CI pipeline definition |

## Testing Instructions

**Run Tests:**
```bash
# All tests (recommended)
uv run pytest

# With coverage report
uv run pytest --cov=src --cov-report=html

# Specific test markers
uv run pytest -m unit
uv run pytest -m integration

# Verbose output
uv run pytest -v --tb=short

# Collect only (verify test discovery)
uv run pytest --collect-only
```

**Testing Conventions:**
- Unit tests go in `tests/unit/`
- Integration tests go in `tests/integration/`
- Shared fixtures in `tests/conftest.py`
- Test file naming: `test_*.py`
- Test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`
- Always add or update tests for changed code

## Code Style

- **Line length:** 100 characters (ruff enforced)
- **Python version:** 3.12+ (target-version in pyproject.toml)
- **Type checking:** mypy strict mode
- **Imports:** isort via ruff (known-first-party: src)
- **Async:** Use `asyncio` for all I/O operations
- **Secrets:** NEVER hardcode; use environment variables

**Ruff rules enabled:** E, W, F, I, B, C4, UP, ARG, SIM
**Ruff rules ignored:** E501, B008, UP042

**Lint and Format:**
```bash
# Check linting issues
uv run ruff check src tests

# Auto-fix linting issues
uv run ruff check --fix src tests

# Format code
uv run ruff format src tests

# Type check
uv run mypy src
```

## Architecture Notes

**Task State Machine (Label-based):**

| Label | State | Description |
|-------|-------|-------------|
| `agent:queued` | Pending | Task validated, awaiting Sentinel |
| `agent:in-progress` | Active | Sentinel claimed, work in progress |
| `agent:reconciling` | Reconciling | Sentinel performing reconciliation checks |
| `agent:success` | Complete | PR created, tests passed |
| `agent:error` | Failed | Technical failure, logs posted |
| `agent:infra-failure` | Infra Error | Container/build failure |
| `agent:stalled-budget` | Stalled | Budget exhausted, task stalled |

**Key Components:**
- **Sentinel** (`src/orchestrator_sentinel.py`): Background polling & dispatch service
- **Notifier** (`src/notifier_service.py`): FastAPI webhook receiver (Phase 2)
- **Queue** (`src/queue/github_queue.py`): GitHub Issues as task queue with label-based state machine
- **Models** (`src/models/`): WorkItem, TaskType, WorkItemStatus, GitHub event schemas

## PR and Commit Guidelines

**Before Committing:**
1. Run linting: `uv run ruff check src tests`
2. Run formatting: `uv run ruff format src tests`
3. Run type check: `uv run mypy src`
4. Run tests: `uv run pytest`
5. Run validation: `pwsh -NoProfile -File ./scripts/validate.ps1 -All`

**Commit Message Format:**
- Use clear, descriptive messages
- Reference issue numbers when applicable

**Branch Naming:**
- Feature branches: `feature/description`
- Fix branches: `fix/description`
- Follow conventional naming patterns

**After Push:**
Monitor CI until green:
```bash
gh run list --limit 5
gh run watch <run-id>
gh run view <run-id> --log-failed
```

## Common Pitfalls

1. **"Missing environment variables" error**
   - Solution: Copy `.env.example` to `.env` and fill in required values

2. **uv sync fails to install dev tools**
   - Solution: Use `uv sync --extra dev` to install dev dependencies

3. **Validation tools not found**
   - Solution: Run `pwsh -NoProfile -File ./scripts/install-dev-tools.ps1`

4. **mypy import errors for src.* modules**
   - Solution: Ensure you're running from repo root with `uv run mypy src`

5. **Docker compose fails to start**
   - Solution: Ensure `.env` file exists with required variables

6. **pytest cannot find tests**
   - Solution: Run from repo root; tests are in `tests/` directory

7. **ruff version command fails**
   - Solution: Use `uv run ruff --version` (not `ruff check --version`)

## Validation Commands

**CRITICAL: Run validation before committing any non-trivial change.**

```bash
# Run ALL validations (local default)
pwsh -NoProfile -File ./scripts/validate.ps1 -All

# Individual checks (parallel in CI)
pwsh -NoProfile -File ./scripts/validate.ps1 -Lint   # actionlint, hadolint, shellcheck, PSScriptAnalyzer
pwsh -NoProfile -File ./scripts/validate.ps1 -Scan   # gitleaks secrets scan
pwsh -NoProfile -File ./scripts/validate.ps1 -Test   # Pester + pytest tests
```

**Validation includes:**
- `actionlint`: GitHub Actions workflow linting
- `hadolint`: Dockerfile linting
- `shellcheck`: Shell script linting
- `PSScriptAnalyzer`: PowerShell linting
- `gitleaks`: Secret detection
- `Pester`: PowerShell tests
- `pytest`: Python tests

## Environment Variables

**Required:**
| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub PAT or App Installation Token |
| `GITHUB_ORG` | Target organization name |
| `GITHUB_REPO` | Target repository name |

**Optional:**
| Variable | Default | Description |
|----------|---------|-------------|
| `SENTINEL_BOT_LOGIN` | - | Bot account login for distributed locking |
| `WEBHOOK_SECRET` | - | HMAC secret for webhook verification |
| `POLL_INTERVAL` | 60 | Polling interval in seconds |
| `MAX_BACKOFF` | 960 | Max backoff on rate limits (seconds) |
| `HEARTBEAT_INTERVAL` | 300 | Heartbeat comment interval (seconds) |
| `SUBPROCESS_TIMEOUT` | 5700 | Subprocess hard timeout (seconds) |

## Related Documentation

- [Architecture Documentation](plan_docs/architecture.md)
- [Technology Stack](plan_docs/tech-stack.md)
- [Architecture Decision Records](docs/adr/)
- [.ai-repository-summary.md](.ai-repository-summary.md) - Comprehensive repository overview

---

*Last Updated: 2026-04-13*
