"""Shared test fixtures for OS-APOW tests."""

import pytest

from src.models.work_item import TaskType, WorkItem, WorkItemStatus


@pytest.fixture
def sample_work_item() -> WorkItem:
    """Create a sample WorkItem for testing."""
    return WorkItem(
        id="12345",
        issue_number=42,
        source_url="https://github.com/test-org/test-repo/issues/42",
        context_body="Implement the new feature",
        target_repo_slug="test-org/test-repo",
        task_type=TaskType.IMPLEMENT,
        status=WorkItemStatus.QUEUED,
        node_id="NI_node123",
    )


@pytest.fixture
def plan_work_item() -> WorkItem:
    """Create a WorkItem with PLAN task type."""
    return WorkItem(
        id="67890",
        issue_number=99,
        source_url="https://github.com/test-org/test-repo/issues/99",
        context_body="[Application Plan] Design the system",
        target_repo_slug="test-org/test-repo",
        task_type=TaskType.PLAN,
        status=WorkItemStatus.QUEUED,
        node_id="NI_node456",
    )


@pytest.fixture
def bugfix_work_item() -> WorkItem:
    """Create a WorkItem with BUGFIX task type."""
    return WorkItem(
        id="11111",
        issue_number=7,
        source_url="https://github.com/test-org/test-repo/issues/7",
        context_body="Fix the authentication bug",
        target_repo_slug="test-org/test-repo",
        task_type=TaskType.BUGFIX,
        status=WorkItemStatus.QUEUED,
        node_id="NI_node789",
    )
