# Workflow Execution Plan: project-setup

## 1. Overview

| Field | Value |
|-------|-------|
| **Workflow Name** | project-setup |
| **Workflow File** | `ai_instruction_modules/ai-workflow-assignments/dynamic-workflows/project-setup.md` |
| **Project Name** | workflow-orchestration-queue (OS-APOW) |
| **Repository** | intel-agency/workflow-orchestration-queue-yankee89-a |
| **Total Assignments** | 6 main + 1 pre-script + 2 post-assignment events + 1 post-script event |

**Summary:** This workflow initiates a new repository by setting up project infrastructure, creating the application plan, establishing project structure, documenting for AI agents, debriefing, and finalizing with a PR merge. The system is designed to be **self-bootstrapping** — the initial deployment seeds the foundational components and the system uses its own orchestration capabilities to refine itself.

---

## 2. Project Context Summary

### Key Facts

| Category | Details |
|----------|---------|
| **Project Type** | Headless agentic orchestration platform (AI worker orchestration) |
| **Primary Language** | Python 3.12+ |
| **Package Manager** | uv (Rust-based, fast dependency management) |
| **Frameworks** | FastAPI, Uvicorn, Pydantic, HTTPX |
| **Architecture** | 4-Pillar System: Ear (Notifier), State (Work Queue), Brain (Sentinel), Hands (Opencode Worker) |
| **Containerization** | Docker / DevContainers |
| **State Management** | GitHub Issues as "Markdown-as-Database" with labels (agent:queued, agent:in-progress, etc.) |
| **Security** | HMAC webhook verification, credential scrubbing, network isolation |

### Repository Details

- **Template Source:** workflow-orchestration-queue-yankee89-a (GitHub template repo)
- **Target Repository:** workflow-orchestration-queue
- **Branch Strategy:** main (production), develop (integration)

### Key Components (Reference Implementations in plan_docs/)

1. **orchestrator_sentinel.py** - Background polling service (Brain) — *reference only*
2. **notifier_service.py** - FastAPI webhook receiver (Ear) — *reference only*
3. **src/models/work_item.py** - Unified data model with credential scrubber — *reference only*
4. **src/queue/github_queue.py** - GitHub Issues queue implementation — *reference only*

### Known Risks & Challenges

| Risk | Mitigation |
|------|------------|
| GitHub API Rate Limiting | Use GitHub App Installation tokens (5,000 req/hr); jittered exponential backoff |
| LLM "Looping" / Hallucination | Max steps timeout; cost guardrails; retries counter |
| Concurrency Collisions | Assign-then-verify pattern using GitHub Assignees as distributed lock |
| Container Drift | Stop worker container between tasks |

### Special Requirements

- **Action SHA Pinning:** All GitHub Actions workflows MUST pin actions to specific commit SHA of their latest release
- **Self-Bootstrapping:** System is designed to build itself after initial seed
- **Provider-Agnostic Interface:** ITaskQueue ABC supports future provider swapping (Linear, Jira, etc.)

---

## 3. Assignment Execution Plan

### Event: pre-script-begin

---

| Field | Content |
|-------|---------|
| **Assignment** | `create-workflow-plan`: Create Workflow Plan |
| **Goal** | Create a comprehensive workflow execution plan covering how each workflow assignment will be executed |
| **Key Acceptance Criteria** | • Dynamic workflow file read and understood • All workflow assignments traced and read • All plan_docs/ files read • Plan presented to stakeholder for approval • Approved plan committed to plan_docs/workflow-plan.md |
| **Project-Specific Notes** | This is the current assignment. Project has extensive planning docs in plan_docs/ including Architecture Guide, Development Plan, Implementation Spec, Plan Review, and Simplification Report. Reference implementations exist for sentinel and notifier. |
| **Prerequisites** | None (first assignment) |
| **Dependencies** | None |
| **Risks / Challenges** | None significant — planning assignment only |
| **Events** | None |

---

### Assignment 1: init-existing-repository

---

| Field | Content |
|-------|---------|
| **Assignment** | `init-existing-repository`: Initiate Existing Repository |
| **Goal** | Set up an existing repository for a project: configure settings, create issue-tracking project, import labels, create milestones |
| **Key Acceptance Criteria** | • New branch created (dynamic-workflow-project-setup) • Branch protection ruleset imported • GitHub Project created with columns (Not Started, In Progress, In Review, Done) • Labels imported from .github/.labels.json • Workspace/devcontainer files renamed • PR created |
| **Project-Specific Notes** | Repository is a template clone. Must verify `administration: write` scope for branch protection ruleset import. Use GH_ORCHESTRATION_AGENT_TOKEN (not GITHUB_TOKEN) for admin operations. |
| **Prerequisites** | GitHub authentication with scopes: repo, project, read:project, read:user, user:email, administration:write |
| **Dependencies** | None |
| **Risks / Challenges** | • Ruleset import may fail if PAT lacks admin scope • PR creation requires at least one commit pushed first |
| **Events** | post-assignment-complete → validate-assignment-completion, report-progress |

---

### Assignment 2: create-app-plan

---

| Field | Content |
|-------|---------|
| **Assignment** | `create-app-plan`: Create Application Plan |
| **Goal** | Create a comprehensive application plan based on the filled-out application template and supporting documents |
| **Key Acceptance Criteria** | • Application template analyzed • Project structure documented • Plan created using template from Appendix A • All phases documented with steps • Milestones created and linked • Issue created in GitHub Project • Labels applied (planning, documentation) |
| **Project-Specific Notes** | Planning documents are in plan_docs/: OS-APOW Architecture Guide v3.2, Development Plan v4.2, Implementation Specification v1.2, Plan Review, Simplification Report. Tech stack is Python/FastAPI/Pydantic. This is PLANNING ONLY — no code implementation. |
| **Prerequisites** | Application template exists in plan_docs/ |
| **Dependencies** | #1 (init-existing-repository) must complete for GitHub Project and labels to exist |
| **Risks / Challenges** | • Ambiguous requirements may need clarification • Plan must balance 4-phase roadmap with MVP scope |
| **Events** | pre-assignment-begin → gather-context; on-assignment-failure → recover-from-error; post-assignment-complete → report-progress |

---

### Assignment 3: create-project-structure

---

| Field | Content |
|-------|---------|
| **Assignment** | `create-project-structure`: Create Project Structure |
| **Goal** | Create the actual project structure and scaffolding based on the application plan |
| **Key Acceptance Criteria** | • Solution/project structure created • Initial configuration files created • Basic CI/CD pipeline structure established • Documentation structure created • Repository summary document created • All GitHub Actions pinned to SHA • Initial commit made |
| **Project-Specific Notes** | Tech stack is Python 3.12+ with uv package manager. Structure should include: pyproject.toml, src/ directory with models/ and queue/ subdirectories, Dockerfile, docker-compose.yml, tests/. Reference implementations in plan_docs/ are architectural guidance only. |
| **Prerequisites** | Application plan exists (Assignment #2 output) |
| **Dependencies** | #2 (create-app-plan) must complete for plan guidance |
| **Risks / Challenges** | • Docker healthcheck must use Python stdlib (not curl) • COPY src/ before uv pip install -e . for editable installs • All actions must be SHA-pinned |
| **Events** | post-assignment-complete → validate-assignment-completion, report-progress |

---

### Assignment 4: create-agents-md-file

---

| Field | Content |
|-------|---------|
| **Assignment** | `create-agents-md-file`: Create AGENTS.md File |
| **Goal** | Create a comprehensive AGENTS.md file at the repository root that provides AI coding agents with context and instructions |
| **Key Acceptance Criteria** | • AGENTS.md exists at repository root • Contains project overview, setup/build/test commands • Contains code style conventions, project structure • Commands validated by running them • File committed and pushed |
| **Project-Specific Notes** | Project uses Python 3.12+, uv, FastAPI, Docker. Key commands: uv sync, uv run pytest, uv run python -m src.main. File should complement README.md and .ai-repository-summary.md. |
| **Prerequisites** | Repository initialized, application plan exists, project structure created |
| **Dependencies** | #1 (init-existing-repository), #3 (create-project-structure) |
| **Risks / Challenges** | Commands must be validated — any incorrect command will cause agent failures |
| **Events** | post-assignment-complete → validate-assignment-completion, report-progress |

---

### Assignment 5: debrief-and-document

---

| Field | Content |
|-------|---------|
| **Assignment** | `debrief-and-document`: Debrief and Document Learnings |
| **Goal** | Perform comprehensive debriefing capturing key learnings, insights, and areas for improvement |
| **Key Acceptance Criteria** | • Detailed report created using structured template • Report documented in .md format • All deviations from assignment documented • Report reviewed and approved • Committed to repo • Execution trace saved |
| **Project-Specific Notes** | Report should include: deviations, plan-impacting discoveries, action items. Must flag findings that affect subsequent phases (Phase 2: Webhook Automation, Phase 3: Deep Orchestration). |
| **Prerequisites** | All main assignments completed |
| **Dependencies** | #1-4 must complete |
| **Risks / Challenges** | None significant — documentation assignment |
| **Events** | post-assignment-complete → validate-assignment-completion, report-progress |

---

### Assignment 6: pr-approval-and-merge

---

| Field | Content |
|-------|---------|
| **Assignment** | `pr-approval-and-merge`: Pull Request Approval and Merge |
| **Goal** | Complete the full PR approval and merge process including resolving PR comments, obtaining approval, merging, and closing associated issues |
| **Key Acceptance Criteria** | • CI verification passed (remediation loop up to 3 attempts) • Code review delegated to code-reviewer subagent • PR review comments resolved via ai-pr-comment-protocol.md • Stakeholder approval obtained • Merge performed • Source branch deleted • Related issues closed |
| **Project-Specific Notes** | This is an automated setup PR — self-approval by orchestrator is acceptable. No human stakeholder approval required. CI remediation loop must still be executed. Pass $pr_num from #1 output. |
| **Prerequisites** | PR exists from Assignment #1 |
| **Dependencies** | #1-5 must complete; PR number from #1 |
| **Risks / Challenges** | • CI failures require up to 3 fix cycles before escalation • Must commit all local changes before merge • GraphQL verification required for thread resolution |
| **Events** | post-assignment-complete → validate-assignment-completion, report-progress |
| **Special Handling** | Pass `$pr_num` from `#initiate-new-repository.init-existing-repository`. Self-approval acceptable. Delete setup branch and close setup issues on success. |

---

### Post-Assignment Events (after each assignment)

---

| Field | Content |
|-------|---------|
| **Assignment** | `validate-assignment-completion`: Validate Assignment Completion |
| **Goal** | Validate that a completed assignment has successfully met all acceptance criteria |
| **Key Acceptance Criteria** | • All required files exist • All verification commands pass • Validation report created • Pass/fail determined • If failed, remediation steps provided |
| **Project-Specific Notes** | Must be delegated to independent qa-test-engineer agent. For GitHub operations, delegate github-expert to query live repository state. |
| **Prerequisites** | Assignment just completed |
| **Dependencies** | Previous assignment output |
| **Risks / Challenges** | Self-validation bias — must use independent agent |
| **Events** | None |

---

| Field | Content |
|-------|---------|
| **Assignment** | `report-progress`: Report Progress After Workflow Step Completion |
| **Goal** | Provide progress reporting, output capture, and validation checkpoints after each workflow step |
| **Key Acceptance Criteria** | • Structured progress report generated • Step outputs captured and stored • Validation checks passed • Workflow state checkpointed • Action items filed as GitHub issues |
| **Project-Specific Notes** | Progress report must include deviations & findings, plan-impacting discoveries. ALL action items MUST be filed as GitHub issues. |
| **Prerequisites** | Workflow step completed successfully |
| **Dependencies** | Previous assignment output |
| **Risks / Challenges** | None significant — reporting assignment |
| **Events** | None |

---

### Event: post-script-complete

---

| Field | Content |
|-------|---------|
| **Event** | Apply `orchestration:plan-approved` label |
| **Goal** | Signal that the application plan is ready for epic creation |
| **Actions** | • Locate the application plan issue created during create-app-plan • Apply label `orchestration:plan-approved` to that plan issue • Record output as `#events.post-script-complete.plan-approved` |
| **Project-Specific Notes** | This label triggers the next phase of the orchestration pipeline (orchestration:plan-approved clause in orchestrator prompt) |
| **Prerequisites** | All main assignments completed successfully |
| **Dependencies** | All assignments and post-assignment events complete |

---

## 4. Sequencing Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROJECT-SETUP WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [PRE-SCRIPT-BEGIN]                                                          │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────┐                                                 │
│  │ create-workflow-plan    │ ◄── FIRST ASSIGNMENT                           │
│  └─────────────────────────┘                                                 │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────┐    ┌────────────────────────┐                   │
│  │ init-existing-repo      │───▶│ validate-completion    │                   │
│  └─────────────────────────┘    │ report-progress        │                   │
│       │                         └────────────────────────┘                   │
│       ▼                                                                      │
│  ┌─────────────────────────┐    ┌────────────────────────┐                   │
│  │ create-app-plan         │───▶│ report-progress        │                   │
│  └─────────────────────────┘    └────────────────────────┘                   │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────┐    ┌────────────────────────┐                   │
│  │ create-project-structure│───▶│ validate-completion    │                   │
│  └─────────────────────────┘    │ report-progress        │                   │
│       │                         └────────────────────────┘                   │
│       ▼                                                                      │
│  ┌─────────────────────────┐    ┌────────────────────────┐                   │
│  │ create-agents-md-file   │───▶│ validate-completion    │                   │
│  └─────────────────────────┘    │ report-progress        │                   │
│       │                         └────────────────────────┘                   │
│       ▼                                                                      │
│  ┌─────────────────────────┐    ┌────────────────────────┐                   │
│  │ debrief-and-document    │───▶│ validate-completion    │                   │
│  └─────────────────────────┘    │ report-progress        │                   │
│       │                         └────────────────────────┘                   │
│       ▼                                                                      │
│  ┌─────────────────────────┐    ┌────────────────────────┐                   │
│  │ pr-approval-and-merge   │───▶│ validate-completion    │                   │
│  │ ($pr_num from #1)       │    │ report-progress        │                   │
│  └─────────────────────────┘    └────────────────────────┘                   │
│       │                                                                      │
│       ▼                                                                      │
│  [POST-SCRIPT-COMPLETE]                                                      │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────┐                                │
│  │ Apply orchestration:plan-approved label │                                │
│  │ to application plan issue               │                                │
│  └─────────────────────────────────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Open Questions (RESOLVED)

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | Should Phase 2 (Webhook Automation) and Phase 3 (Deep Orchestration) features be documented as separate issues now, or deferred? | **Defer** - Create separate issues after project-setup completes | Keeps MVP scope focused |
| 2 | Is the reference implementation in plan_docs/ (sentinel, notifier, queue) considered "seed code" to be moved to src/, or reference only? | **Reference only** - Architectural guidance | Agents will implement fresh based on specs |
| 3 | Should cost guardrails (Story 6) be implemented in MVP or explicitly deferred? | **Deferred** - Phase 3 concern, document as future enhancement | Core polling-claim-execute loop prioritized |

---

## 6. Files Referenced

| Category | File Path | Purpose |
|----------|-----------|---------|
| **Dynamic Workflow** | `ai_instruction_modules/ai-workflow-assignments/dynamic-workflows/project-setup.md` | Workflow definition |
| **Planning Docs** | `plan_docs/OS-APOW Architecture Guide v3.2.md` | System architecture |
| **Planning Docs** | `plan_docs/OS-APOW Development Plan v4.2.md` | Phased roadmap |
| **Planning Docs** | `plan_docs/OS-APOW Implementation Specification v1.2.md` | Requirements & specs |
| **Planning Docs** | `plan_docs/OS-APOW Plan Review.md` | Issues & recommendations |
| **Planning Docs** | `plan_docs/OS-APOW Simplification Report v1.md` | Simplification decisions |
| **Reference Code** | `plan_docs/orchestrator_sentinel.py` | Sentinel implementation (reference only) |
| **Reference Code** | `plan_docs/notifier_service.py` | Notifier implementation (reference only) |
| **Reference Code** | `plan_docs/src/models/work_item.py` | Unified data model (reference only) |
| **Reference Code** | `plan_docs/src/queue/github_queue.py` | Queue implementation (reference only) |

---

## 7. Approval Record

| Field | Value |
|-------|-------|
| **Plan Prepared By** | Planner Agent |
| **Date** | 2026-04-06 |
| **Approved By** | Orchestrator |
| **Approval Date** | 2026-04-06 |
| **Status** | ✅ APPROVED |
| **Commit SHA** | `32791a5b92b0102e20b01aeee3064972775f5316` |
