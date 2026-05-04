"""
OS-APOW GitHub Queue.

Consolidated GitHub-backed work queue used by both the Sentinel
Orchestrator and the Work Event Notifier. Implements the ITaskQueue
ABC so the provider can be swapped to Linear, Jira, etc. in the future.
"""

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

import httpx

from src.models.work_item import (
    TaskType,
    WorkItem,
    WorkItemStatus,
    scrub_secrets,
)

logger = logging.getLogger("OS-APOW")


# --- Abstract Interface ---


class ITaskQueue(ABC):
    """Interface for the Work Queue (e.g., GH Issues, Linear, Jira, etc.)."""

    @abstractmethod
    async def add_to_queue(self, item: WorkItem) -> bool:
        """Add a work item to the queue."""

    @abstractmethod
    async def fetch_queued_tasks(self) -> list[WorkItem]:
        """Fetch all queued work items."""

    @abstractmethod
    async def update_status(
        self, item: WorkItem, status: WorkItemStatus, comment: str | None = None
    ) -> None:
        """Update the status of a work item."""


# --- Concrete Implementation: GitHub Issues ---


class GitHubQueue(ITaskQueue):
    """GitHub-backed work queue with connection pooling.

    Used by both the Sentinel Orchestrator and the Work Event Notifier.
    The sentinel passes org/repo for polling; the notifier only needs a
    token since it derives the repo from the webhook payload.
    """

    def __init__(self, token: str, org: str = "", repo: str = "") -> None:
        self.token = token
        self.org = org
        self.repo = repo
        self.headers: dict[str, str] = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self._client: httpx.AsyncClient = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
        )

    async def close(self) -> None:
        """Release the connection pool. Call during graceful shutdown."""
        await self._client.aclose()

    def _repo_api_url(self, repo_slug: str) -> str:
        """Build the GitHub API URL for a repository."""
        return f"https://api.github.com/repos/{repo_slug}"

    # --- ITaskQueue implementation ---

    async def add_to_queue(self, item: WorkItem) -> bool:
        """Add the agent:queued label to a GitHub issue."""
        url = f"{self._repo_api_url(item.target_repo_slug)}/issues/{item.issue_number}/labels"
        resp = await self._client.post(url, json={"labels": [WorkItemStatus.QUEUED.value]})
        if resp.status_code in (200, 201):
            logger.info("Queued issue #%d (%s)", item.issue_number, item.task_type.value)
            return True
        logger.error("Failed to queue #%d: %d", item.issue_number, resp.status_code)
        return False

    async def fetch_queued_tasks(self) -> list[WorkItem]:
        """Query GitHub for issues labeled 'agent:queued' in the configured repo.

        Note: Cross-repo org-wide polling via the Search API is planned
        for a future phase. Currently requires org and repo to be set.
        """
        if not self.org or not self.repo:
            logger.warning("fetch_queued_tasks requires org and repo to be set")
            return []

        url = f"{self._repo_api_url(f'{self.org}/{self.repo}')}/issues"
        params: dict[str, str] = {"labels": WorkItemStatus.QUEUED.value, "state": "open"}

        response = await self._client.get(url, params=params)

        if response.status_code in (403, 429):
            # Propagate rate-limit errors so the sentinel's backoff logic fires
            response.raise_for_status()

        if response.status_code != 200:
            logger.error(
                "GitHub API error: %d %s",
                response.status_code,
                response.text[:200],
            )
            return []

        issues: list[dict[str, Any]] = response.json()

        work_items: list[WorkItem] = []
        for issue in issues:
            labels = [label["name"] for label in issue.get("labels", [])]
            task_type = TaskType.IMPLEMENT
            if "agent:plan" in labels or "[Plan]" in str(issue.get("title", "")):
                task_type = TaskType.PLAN
            elif "bug" in labels:
                task_type = TaskType.BUGFIX

            html_url = str(issue["html_url"])
            parts = html_url.split("/")
            repo_slug = "/".join(parts[3:5])

            work_items.append(
                WorkItem(
                    id=str(issue["id"]),
                    issue_number=int(issue["number"]),
                    source_url=html_url,
                    context_body=str(issue.get("body") or ""),
                    target_repo_slug=repo_slug,
                    task_type=task_type,
                    status=WorkItemStatus.QUEUED,
                    node_id=str(issue.get("node_id", "")),
                )
            )
        return work_items

    async def update_status(
        self, item: WorkItem, status: WorkItemStatus, comment: str | None = None
    ) -> None:
        """Finalize the task state on GitHub with terminal labels and logs."""
        base = self._repo_api_url(item.target_repo_slug)
        url_labels = f"{base}/issues/{item.issue_number}/labels"

        resp = await self._client.delete(f"{url_labels}/{WorkItemStatus.IN_PROGRESS.value}")
        if resp.status_code not in (200, 204, 404, 410):
            logger.error("Label cleanup failed: %d", resp.status_code)

        await self._client.post(url_labels, json={"labels": [status.value]})

        if comment:
            safe_comment = scrub_secrets(comment)
            comment_url = f"{base}/issues/{item.issue_number}/comments"
            await self._client.post(comment_url, json={"body": safe_comment})

    # --- Sentinel-specific methods ---

    async def claim_task(self, item: WorkItem, sentinel_id: str, bot_login: str = "") -> bool:
        """Claim a task using assign-then-verify distributed locking.

        Steps:
          1. Attempt to assign bot_login to the issue.
          2. Re-fetch the issue to verify we are the assignee.
          3. Only then update labels and post the claim comment.
        """
        base = self._repo_api_url(item.target_repo_slug)
        url_issue = f"{base}/issues/{item.issue_number}"

        # Step 1: Attempt assignment
        if bot_login:
            resp = await self._client.post(
                f"{url_issue}/assignees",
                json={"assignees": [bot_login]},
            )
            if resp.status_code not in (200, 201):
                logger.warning("Failed to assign #%d: %d", item.issue_number, resp.status_code)
                return False

            # Step 2: Re-fetch and verify assignee
            verify_resp = await self._client.get(url_issue)
            if verify_resp.status_code == 200:
                assignees = [a["login"] for a in verify_resp.json().get("assignees", [])]
                if bot_login not in assignees:
                    logger.warning(
                        "Lost race on #%d — assignees are %s, expected %s",
                        item.issue_number,
                        assignees,
                        bot_login,
                    )
                    return False
            else:
                logger.warning(
                    "Could not verify assignment for #%d: %d",
                    item.issue_number,
                    verify_resp.status_code,
                )
                return False

        # Step 3: Update labels
        url_labels = f"{url_issue}/labels"
        resp = await self._client.delete(f"{url_labels}/{WorkItemStatus.QUEUED.value}")
        if resp.status_code not in (200, 204, 404, 410):
            logger.error("Label removal failed: %d", resp.status_code)
            return False

        await self._client.post(
            url_labels,
            json={"labels": [WorkItemStatus.IN_PROGRESS.value]},
        )

        # Step 4: Post claim comment
        comment_url = f"{url_issue}/comments"
        msg = (
            f"**Sentinel {sentinel_id}** has claimed this task.\n"
            f"- **Start Time:** {datetime.now(UTC).isoformat()}\n"
            f"- **Environment:** `devcontainer-opencode.sh` initializing..."
        )
        await self._client.post(comment_url, json={"body": msg})

        logger.info("Successfully claimed Task #%d", item.issue_number)
        return True

    async def post_heartbeat(self, item: WorkItem, sentinel_id: str, elapsed_secs: int) -> None:
        """Post a heartbeat comment to keep observers informed."""
        base = self._repo_api_url(item.target_repo_slug)
        comment_url = f"{base}/issues/{item.issue_number}/comments"
        minutes = elapsed_secs // 60
        msg = (
            f"**Heartbeat** — Sentinel {sentinel_id} still working.\n"
            f"- **Elapsed:** {minutes}m\n"
            f"- **Timestamp:** {datetime.now(UTC).isoformat()}"
        )
        try:
            await self._client.post(comment_url, json={"body": msg})
        except Exception as exc:
            logger.warning("Heartbeat post failed: %s", exc)
