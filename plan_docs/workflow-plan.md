# Workflow Execution Plan: project-setup

**Dynamic Workflow:** `project-setup`  
**Repository:** `intel-agency/workflow-orchestration-queue-yankee89-a`  
**Generated:** 2026-03-30

---

## 1. Overview

This document defines the execution plan for the `project-setup` dynamic workflow, which initiates a new repository by running a sequence of assignments to set up the `workflow-orchestration-queue` system.

**Workflow File Reference:**  
`ai_instruction_modules/ai-workflow-assignments/dynamic-workflows/project-setup.md`

**Total Assignments:** 6 main assignments + event handlers

**High-Level Summary:**  
The workflow will initialize the repository, create an application plan, set up project scaffolding, create configuration files, document learnings, and merge the setup PR. This transforms the template repository into a fully configured development environment for the `workflow-orchestration-queue` headless agentic orchestration platform.

---

## 2. Project Context Summary

**Project Name:** `workflow-orchestration-queue`

**Description:** A groundbreaking headless agentic orchestration platform that transforms GitHub Issues into automated execution orders. The system shifts AI from a passive co-pilot to an autonomous background production service capable of multi-step, specification-driven task fulfillment without human intervention.

**Technology Stack:**
- **Language:** Python 3.12+
- **Framework:** FastAPI (webhook receiver), Uvicorn (ASGI server)
- **Package Manager:** uv (Rust-based, fast dependency management)
- **Validation:** Pydantic (data schemas)
- **HTTP Client:** HTTPX (async)
- **Containerization:** Docker, Docker Compose, DevContainers
- **CLI Tools:** GitHub CLI (gh), opencode CLI
- **MCP Servers:** @modelcontextprotocol/server-sequential-thinking, @modelcontextprotocol/server-memory

**Key Constraints:**
- All GitHub Actions MUST pin to SHA (not `@v3` or `@main`)
- CI remediation loop: up to 3 fix attempts on failure
- Delete setup branch and close setup issues after merge
- Branch protection ruleset must be imported from `.github/protected branches - main - ruleset.json`

**Repository Details:**
- Owner: `intel-agency`
- Repo: `workflow-orchestration-queue-yankee89-a`
- Template Source: `intel-agency/workflow-orchestration-queue-yankee89-a`

**Known Risks:**
1. Ruleset file has spaces in name - may need special handling during import
2. Requires `administration: write` scope for ruleset import
3. CI validation may require multiple attempts

---

## 3. Assignment Execution Plan

### Phase 0: Pre-script-begin Event

| Field | Content |
|---|---|
| **Assignment** | `create-workflow-plan`: Create Workflow Plan |
| **Goal** | Create a comprehensive workflow execution plan before any assignments begin |
| **Key Acceptance Criteria** | - Dynamic workflow file read and understood<br>- All assignments traced and read<br>- All plan_docs/ files read<br>- Workflow execution plan produced<br>- Plan approved by stakeholder<br>- Plan committed to `plan_docs/workflow-plan.md` |
| **Project-Specific Notes** | Plan docs contain comprehensive architecture guide, development plan, and implementation spec for the orchestration platform |
| **Prerequisites** | None (first step) |
| **Dependencies** | None |
| **Risks / Challenges** | None significant |
| **Events** | None |

---

### Phase 1: init-existing-repository

| Field | Content |
|---|---|
| **Assignment** | `init-existing-repository`: Initiate Existing Repository |
| **Goal** | Initialize the repository with proper configuration, create setup PR |
| **Key Acceptance Criteria** | - New branch created (`dynamic-workflow-project-setup`)<br>- Branch protection ruleset imported<br>- GitHub Project created for issue tracking<br>- Labels imported from `.github/.labels.json`<br>- Workspace/devcontainer files renamed<br>- PR created to main |
| **Project-Specific Notes** | - Workspace file already matches repo name<br>- Ruleset file has spaces in name (`protected branches - main - ruleset.json`)<br>- `.labels.json` already exists in `.github/` |
| **Prerequisites** | GitHub auth with `repo`, `project`, `administration: write` scopes |
| **Dependencies** | Phase 0 (workflow plan) |
| **Risks / Challenges** | - Ruleset import may fail due to file naming<br>- Need `GH_ORCHESTRATION_AGENT_TOKEN` with proper scopes |
| **Events** | `post-assignment-complete`: `validate-assignment-completion`, `report-progress` |
| **Outputs** | PR number for Phase 6 |

---

### Phase 2: create-app-plan

| Field | Content |
|---|---|
| **Assignment** | `create-app-plan`: Create Application Plan |
| **Goal** | Create a comprehensive application plan issue based on the planning documents |
| **Key Acceptance Criteria** | - Application template analyzed<br>- Plan documented in GitHub issue using template<br>- Milestones created and linked<br>- Issue added to GitHub Project<br>- Appropriate labels applied |
| **Project-Specific Notes** | - Plan docs are comprehensive (Development Plan v4.2, Architecture Guide v3.2, Implementation Spec v1.2)<br>- Issue template at `.github/ISSUE_TEMPLATE/application-plan.md` |
| **Prerequisites** | Phase 1 (repository initialized) |
| **Dependencies** | Phase 1 outputs (GitHub Project created) |
| **Risks / Challenges** | Plan docs are extensive - need to synthesize key points |
| **Events** | `pre-assignment-begin`: `gather-context`<br>`on-assignment-failure`: `recover-from-error`<br>`post-assignment-complete`: `validate-assignment-completion`, `report-progress` |
| **Outputs** | Plan issue number for `orchestration:plan-approved` label |

---

### Phase 3: create-project-structure

| Field | Content |
|---|---|
| **Assignment** | `create-project-structure`: Create Project Structure |
| **Goal** | Create the actual project structure and scaffolding based on the application plan |
| **Key Acceptance Criteria** | - Solution/project structure created<br>- All project files and directories established<br>- Docker configurations created<br>- CI/CD pipeline structure established<br>- Documentation structure created<br>- All GitHub Actions pinned to SHA |
| **Project-Specific Notes** | - Python project: `pyproject.toml`, `uv.lock`, `src/`, `tests/`<br>- FastAPI app structure needed<br>- DevContainer already configured |
| **Prerequisites** | Phase 2 (application plan created) |
| **Dependencies** | Phase 2 outputs (plan issue with structure guidance) |
| **Risks / Challenges** | Must ensure all workflow actions are SHA-pinned |
| **Events** | `post-assignment-complete`: `validate-assignment-completion`, `report-progress` |
| **Outputs** | Complete project scaffolding |

---

### Phase 4: create-agents-md-file

| Field | Content |
|---|---|
| **Assignment** | `create-agents-md-file`: Create AGENTS.md Configuration |
| **Goal** | Create the AGENTS.md configuration file for AI agent context |
| **Key Acceptance Criteria** | - AGENTS.md created at repository root<br>- Contains project-specific AI agent instructions<br>- Aligned with project tech stack and conventions |
| **Project-Specific Notes** | - AGENTS.md already exists in template - may need updating<br>- Should reflect Python/FastAPI/uv stack |
| **Prerequisites** | Phase 3 (project structure created) |
| **Dependencies** | Phase 3 outputs (project structure) |
| **Risks / Challenges** | Ensure AGENTS.md reflects actual project context |
| **Events** | `post-assignment-complete`: `validate-assignment-completion`, `report-progress` |
| **Outputs** | Updated AGENTS.md |

---

### Phase 5: debrief-and-document

| Field | Content |
|---|---|
| **Assignment** | `debrief-and-document`: Debrief and Document Learnings |
| **Goal** | Create comprehensive debriefing report capturing key learnings and insights |
| **Key Acceptance Criteria** | - Detailed report created following template<br>- All deviations documented<br>- Report reviewed and approved<br>- Execution trace saved |
| **Project-Specific Notes** | - Document all deviations from assignments<br>- Capture any plan-impacting discoveries<br>- File action items as GitHub issues |
| **Prerequisites** | Phases 1-4 complete |
| **Dependencies** | All prior phase outputs |
| **Risks / Challenges** | None significant |
| **Events** | `post-assignment-complete`: `validate-assignment-completion`, `report-progress` |
| **Outputs** | Debrief report, execution trace |

---

### Phase 6: pr-approval-and-merge

| Field | Content |
|---|---|
| **Assignment** | `pr-approval-and-merge`: PR Approval and Merge |
| **Goal** | Complete the full PR approval and merge process for the setup PR |
| **Key Acceptance Criteria** | - CI verification (up to 3 remediation attempts)<br>- Code review delegated to `code-reviewer`<br>- All review comments resolved<br>- Stakeholder approval obtained<br>- PR merged<br>- Source branch deleted<br>- Related issues closed |
| **Project-Specific Notes** | - Self-approval acceptable for automated setup PR<br>- Must follow `ai-pr-comment-protocol.md` |
| **Prerequisites** | Phase 1 (PR created), Phases 2-5 (implementation complete) |
| **Dependencies** | PR number from Phase 1 |
| **Risks / Challenges** | - CI may require multiple fix attempts<br>- Must ensure all changes committed before merge |
| **Events** | `post-assignment-complete`: `validate-assignment-completion`, `report-progress` |
| **Outputs** | Merged PR, cleaned up branches and issues |

---

## 4. Sequencing Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    project-setup Dynamic Workflow                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [pre-script-begin]                                                         │
│       │                                                                      │
│       ▼                                                                      │
│  ┌──────────────────────┐                                                   │
│  │ create-workflow-plan │ ─────────────────────────────────────────────┐    │
│  └──────────────────────┘                                               │    │
│       │                                                                  │    │
│       ▼                                                                  │    │
│  ┌───────────────────────────┐     ┌───────────────────────────────┐   │    │
│  │ init-existing-repository  │────▶│ validate-assignment-completion│   │    │
│  └───────────────────────────┘     └───────────────────────────────┘   │    │
│       │                                      │                          │    │
│       │                                      ▼                          │    │
│       │                              ┌───────────────┐                  │    │
│       │                              │report-progress│                  │    │
│       │                              └───────────────┘                  │    │
│       ▼                                                                  │    │
│  ┌───────────────────┐      ┌───────────────────────────────┐          │    │
│  │  create-app-plan  │─────▶│ validate-assignment-completion│          │    │
│  └───────────────────┘      └───────────────────────────────┘          │    │
│       │                               │                                 │    │
│       │                               ▼                                 │    │
│       │                        ┌───────────────┐                        │    │
│       │                        │report-progress│                        │    │
│       │                        └───────────────┘                        │    │
│       ▼                                                                 │    │
│  ┌──────────────────────────┐  ┌───────────────────────────────┐       │    │
│  │create-project-structure  │─▶│ validate-assignment-completion│       │    │
│  └──────────────────────────┘  └───────────────────────────────┘       │    │
│       │                               │                                 │    │
│       │                               ▼                                 │    │
│       │                        ┌───────────────┐                        │    │
│       │                        │report-progress│                        │    │
│       │                        └───────────────┘                        │    │
│       ▼                                                                 │    │
│  ┌────────────────────────┐    ┌───────────────────────────────┐       │    │
│  │create-agents-md-file   │───▶│ validate-assignment-completion│       │    │
│  └────────────────────────┘    └───────────────────────────────┘       │    │
│       │                               │                                 │    │
│       │                               ▼                                 │    │
│       │                        ┌───────────────┐                        │    │
│       │                        │report-progress│                        │    │
│       │                        └───────────────┘                        │    │
│       ▼                                                                 │    │
│  ┌──────────────────────┐     ┌───────────────────────────────┐       │    │
│  │ debrief-and-document │────▶│ validate-assignment-completion│       │    │
│  └──────────────────────┘     └───────────────────────────────┘       │    │
│       │                               │                                 │    │
│       │                               ▼                                 │    │
│       │                        ┌───────────────┐                        │    │
│       │                        │report-progress│                        │    │
│       │                        └───────────────┘                        │    │
│       ▼                                                                 │    │
│  ┌────────────────────────┐   ┌───────────────────────────────┐       │    │
│  │ pr-approval-and-merge  │──▶│ validate-assignment-completion│       │    │
│  └────────────────────────┘   └───────────────────────────────┘       │    │
│       │                               │                                 │    │
│       │                               ▼                                 │    │
│       │                        ┌───────────────┐                        │    │
│       │                        │report-progress│                        │    │
│       │                        └───────────────┘                        │    │
│       ▼                                                                 │    │
│  [post-script-complete]                                                  │    │
│       │                                                                  │    │
│       ▼                                                                  │    │
│  ┌────────────────────────────────────────────────────────────────┐    │    │
│  │ Apply `orchestration:plan-approved` label to plan issue        │◀───┘    │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Open Questions

1. **Authentication Scopes:** Does the current `GITHUB_TOKEN` have the required `administration: write` scope for ruleset import? If not, the `GH_ORCHESTRATION_AGENT_TOKEN` environment variable must be set with a PAT that has this scope.

2. **Ruleset File Naming:** The ruleset file has spaces in its name (`protected branches - main - ruleset.json`). Should this be renamed to match the expected naming convention (`protected-branches_ruleset.json`) before import, or should the import command handle the spaces?

3. **AGENTS.md Content:** The AGENTS.md file already exists with template content. Should it be updated to reflect the Python/FastAPI stack, or is the existing content sufficient?

---

## 6. Guardrails Summary

| Guardrail | Enforcement |
|-----------|-------------|
| GitHub Actions SHA Pinning | All workflow actions MUST be pinned to full commit SHA |
| CI Remediation Loop | Up to 3 fix attempts before escalation |
| Branch Cleanup | Delete setup branch after successful merge |
| Issue Cleanup | Close setup-related issues after merge |
| Self-Approval | Permitted for automated setup PR |

---

## 7. Approval

**Stakeholder Approval Status:** ⏳ Pending

**Approved By:** _To be filled after stakeholder review_

**Approval Date:** _To be filled after stakeholder review_

**Notes:** _Any stakeholder feedback or conditions_

---

*This workflow execution plan was generated by the `create-workflow-plan` assignment as part of the `project-setup` dynamic workflow.*
