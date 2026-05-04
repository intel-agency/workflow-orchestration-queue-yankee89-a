# Architecture - workflow-orchestration-queue (OS-APOW)

**Last Updated:** 2026-03-20

## Executive Summary

workflow-orchestration-queue represents a paradigm shift from **Interactive AI Coding** to **Headless Agentic Orchestration**. It transforms standard project management artifacts (GitHub Issues) into "Execution Orders" that are autonomously fulfilled by specialized AI agents—moving the agent from a passive co-pilot to a background production service.

---

## 4-Pillar Architecture

The system is distributed across four conceptual pillars, each handling a distinct domain:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        workflow-orchestration-queue                      │
├─────────────────┬─────────────────┬─────────────────┬───────────────────┤
│   THE EAR       │   THE STATE     │   THE BRAIN     │   THE HANDS       │
│   (Notifier)    │   (Queue)       │   (Sentinel)    │   (Worker)        │
├─────────────────┼─────────────────┼─────────────────┼───────────────────┤
│ FastAPI         │ GitHub Issues   │ Python Async    │ DevContainer      │
│ Webhook         │ Labels          │ Polling         │ opencode CLI      │
│ Receiver        │ Assignees       │ Dispatcher      │ LLM Agent         │
└─────────────────┴─────────────────┴─────────────────┴───────────────────┘
```

---

## Pillar 1: The Ear (Work Event Notifier)

**Technology:** Python 3.12, FastAPI, Pydantic

**Role:** System's primary gateway for external stimuli and asynchronous triggers

**Responsibilities:**
- **Secure Webhook Ingestion:** Hardened endpoint for GitHub webhook events
- **Cryptographic Verification:** HMAC SHA256 signature validation against `WEBHOOK_SECRET`
- **Intelligent Event Triage:** Parse issue bodies and labels, map to unified `WorkItem` objects
- **Queue Initialization:** Apply `agent:queued` label to signal Sentinel

**Phase:** Phase 2 (not in MVP)

---

## Pillar 2: The State (Work Queue)

**Implementation:** GitHub Issues, Labels, Milestones

**Philosophy:** "Markdown as a Database" - public-facing issue labels manage task states

**State Machine (Label Logic):**

| Label | State | Description |
|-------|-------|-------------|
| `agent:queued` | Pending | Task validated, awaiting Sentinel |
| `agent:in-progress` | Active | Sentinel claimed, work in progress |
| `agent:reconciling` | Recovery | Stale task being recovered |
| `agent:success` | Complete | PR created, tests passed |
| `agent:error` | Failed | Technical failure, logs posted |
| `agent:infra-failure` | Infra Error | Container/build failure |
| `agent:stalled-budget` | Budget Exceeded | Cost threshold breached |

**Concurrency Control:** GitHub Assignees as distributed lock via **assign-then-verify** pattern:
1. Attempt to assign `SENTINEL_BOT_LOGIN` to issue
2. Re-fetch the issue
3. Verify assignee matches before proceeding
4. If verification fails, skip gracefully

---

## Pillar 3: The Brain (Sentinel Orchestrator)

**Technology:** Python (Async), PowerShell, Docker CLI

**Role:** Persistent supervisor managing Worker lifecycle and task dispatch

**Lifecycle:**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   POLL      │────▶│   CLAIM     │────▶│   DISPATCH  │────▶│   FINALIZE  │
│   (60s)     │     │ (lock)      │     │ (worker)    │     │ (state)     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      ▲                                                           │
      └───────────────────────────────────────────────────────────┘
```

**Key Operations:**

1. **Polling Discovery:** Query GitHub Issues API for `agent:queued` labels
2. **Auth Synchronization:** Run `scripts/gh-auth.ps1` for token management
3. **Shell-Bridge Protocol:** Interact via `devcontainer-opencode.sh`:
   - `up`: Provision Docker network and volumes
   - `start`: Launch opencode-server in DevContainer
   - `prompt "{workflow}"`: Execute workflow instruction
4. **Heartbeat:** Post status comments every 5 minutes during long tasks
5. **Environment Reset:** Stop worker container between tasks (prevent state bleed)
6. **Graceful Shutdown:** Handle `SIGTERM`/`SIGINT`, finish current task, exit cleanly

---

## Pillar 4: The Hands (Opencode Worker)

**Technology:** opencode CLI, LLM (GLM-5), DevContainer

**Role:** Execution layer where actual coding happens

**Worker Capabilities:**
- **Contextual Awareness:** Access project structure via vector indices
- **Instructional Logic:** Execute markdown workflows from `/local_ai_instruction_modules/`
- **Verification:** Run local test suites before PR submission

**Environment:**
- Isolated DevContainer (2 CPUs, 4GB RAM limits)
- Ephemeral credentials (in-memory env vars only)
- Network isolation from host

---

## Key Architectural Decisions (ADRs)

### ADR 07: Standardized Shell-Bridge Execution

**Decision:** Orchestrator interacts with agentic environment *exclusively* via `./scripts/devcontainer-opencode.sh`

**Rationale:** Existing shell infrastructure handles Docker logic, volume mounting, SSH-agent forwarding. Reusing scripts ensures perfect environment parity with local developers.

### ADR 08: Polling-First Resiliency Model

**Decision:** Sentinel uses polling as primary discovery; webhooks are optimization

**Rationale:** Webhooks are "fire and forget." Polling ensures state reconciliation on restart, making the system self-healing against downtime.

### ADR 09: Provider-Agnostic Interface Layer

**Decision:** Queue interactions abstracted behind `ITaskQueue` interface (Strategy Pattern)

**Rationale:** Enables future provider swapping (Linear, Notion, SQL) without Orchestrator rewrite.

---

## Data Flow (Happy Path)

```
User Opens Issue → Notifier Webhook → Triage & Queue Label
                                              ↓
                         Sentinel Polls & Claims (assign-then-verify)
                                              ↓
                         Sentinel Syncs Repo & Runs devcontainer-opencode.sh up
                                              ↓
                         Sentinel Dispatches Workflow Prompt
                                              ↓
                         Worker Executes Instructions, Creates PR
                                              ↓
                         Sentinel Detects Success, Labels agent:success
```

---

## Security Model

| Layer | Protection |
|-------|------------|
| **Network Isolation** | Worker containers in segregated Docker network |
| **Credential Scoping** | Ephemeral tokens via environment variables |
| **Credential Scrubbing** | Regex removal of secrets from public logs |
| **Resource Constraints** | 2 CPU / 4GB RAM limits per worker |
| **HMAC Verification** | Webhook signature validation |

---

## Project Structure

```
workflow-orchestration-queue/
├── pyproject.toml              # uv dependencies and metadata
├── uv.lock                     # Deterministic lockfile
├── src/
│   ├── notifier_service.py     # FastAPI Webhook (Phase 2)
│   ├── orchestrator_sentinel.py # Background polling & dispatch
│   ├── models/
│   │   ├── work_item.py        # Unified WorkItem, TaskType, WorkItemStatus
│   │   └── github_events.py    # Webhook payload schemas
│   └── queue/
│       └── github_queue.py     # ITaskQueue + GitHubQueue
├── scripts/
│   ├── devcontainer-opencode.sh # Shell bridge to worker
│   ├── gh-auth.ps1             # GitHub App auth sync
│   └── update-remote-indices.ps1 # Vector index maintenance
├── local_ai_instruction_modules/ # Markdown workflow prompts
└── docs/                       # Architecture and user docs
```

---

## Self-Bootstrapping Lifecycle

1. **Bootstrap:** Developer manually clones template repository
2. **Seed:** Add plan docs, run project-setup workflow
3. **Init:** Run `devcontainer-opencode.sh up` first time
4. **Orchestrate:** Use `orchestrate-dynamic-workflow` for environment configuration
5. **Autonomous Phase:** Start Sentinel service; AI manages all further development
