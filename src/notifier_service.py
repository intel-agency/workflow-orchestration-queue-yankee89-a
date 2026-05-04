"""
OS-APOW Work Event Notifier.

A FastAPI-based webhook receiver that maps provider events (GitHub, etc.)
to a unified Work Item queue.
"""

import hashlib
import hmac
import os
import sys
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from src.models.work_item import TaskType, WorkItem, WorkItemStatus
from src.queue.github_queue import GitHubQueue, ITaskQueue

# --- Environment validation ---

_WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# When run as a module (not imported by tests), validate config.
# Tests should set env vars or mock as needed.
_VALIDATE_ENV = os.environ.get("NOTIFIER_SKIP_ENV_CHECK", "") != "1"

if _VALIDATE_ENV:
    if not _WEBHOOK_SECRET:
        print(
            "WARNING: WEBHOOK_SECRET is not set. Signature verification will fail.",
            file=sys.stderr,
        )
    if not _GITHUB_TOKEN:
        print(
            "WARNING: GITHUB_TOKEN is not set. Queue operations will fail.",
            file=sys.stderr,
        )

WEBHOOK_SECRET = _WEBHOOK_SECRET.encode() if _WEBHOOK_SECRET else b""

# --- FastAPI Application ---

app = FastAPI(title="OS-APOW Event Notifier")


def get_queue() -> ITaskQueue:
    """Dependency injection for the queue implementation."""
    return GitHubQueue(token=_GITHUB_TOKEN)


async def verify_signature(
    request: Request,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> None:
    """Verify the GitHub webhook signature."""
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="X-Hub-Signature-256 missing")

    body = await request.body()
    signature = "sha256=" + hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")


# --- Endpoints ---


@app.post("/webhooks/github", dependencies=[Depends(verify_signature)])
async def handle_github_webhook(
    request: Request, queue: Annotated[ITaskQueue, Depends(get_queue)]
) -> dict[str, str]:
    """Handle incoming GitHub webhook events."""
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "issues" and payload.get("action") == "opened":
        issue = payload["issue"]
        labels = [label["name"] for label in issue.get("labels", [])]

        if "[Application Plan]" in issue["title"] or "agent:plan" in labels:
            work_item = WorkItem(
                id=str(issue["id"]),
                issue_number=issue["number"],
                source_url=issue["html_url"],
                target_repo_slug=payload["repository"]["full_name"],
                task_type=TaskType.PLAN,
                context_body=issue.get("body") or "",
                status=WorkItemStatus.QUEUED,
                node_id=issue.get("node_id", ""),
            )
            await queue.add_to_queue(work_item)
            return {"status": "accepted", "item_id": work_item.id}

    return {"status": "ignored", "reason": "No actionable OS-APOW event mapping found"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "online", "system": "OS-APOW Notifier"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
