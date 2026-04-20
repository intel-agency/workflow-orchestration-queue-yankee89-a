"""Pydantic schemas for GitHub webhook payloads."""

from __future__ import annotations

from pydantic import BaseModel


class GitHubLabel(BaseModel):
    """Represents a label on a GitHub issue."""

    id: int
    name: str
    color: str
    default: bool = False


class GitHubUser(BaseModel):
    """Represents a GitHub user."""

    id: int
    login: str
    node_id: str = ""


class GitHubIssue(BaseModel):
    """Represents a GitHub issue from a webhook payload."""

    id: int
    number: int
    title: str
    html_url: str
    body: str | None = None
    node_id: str = ""
    labels: list[GitHubLabel] = []
    assignees: list[GitHubUser] = []


class GitHubRepository(BaseModel):
    """Represents a GitHub repository from a webhook payload."""

    id: int
    name: str
    full_name: str
    html_url: str
    owner: GitHubUser


class GitHubWebhookPayload(BaseModel):
    """Top-level payload for GitHub webhook events."""

    action: str = ""
    issue: GitHubIssue | None = None
    repository: GitHubRepository | None = None
    sender: GitHubUser | None = None
