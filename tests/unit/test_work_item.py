"""Unit tests for WorkItem, TaskType, WorkItemStatus, and scrub_secrets."""

import pytest
from pydantic import ValidationError

from src.models.work_item import TaskType, WorkItem, WorkItemStatus, scrub_secrets

pytestmark = pytest.mark.unit

# --- TaskType enum tests ---


class TestTaskType:
    """Tests for the TaskType enum."""

    def test_plan_value(self) -> None:
        assert TaskType.PLAN.value == "PLAN"

    def test_implement_value(self) -> None:
        assert TaskType.IMPLEMENT.value == "IMPLEMENT"

    def test_bugfix_value(self) -> None:
        assert TaskType.BUGFIX.value == "BUGFIX"

    def test_all_members(self) -> None:
        members = set(TaskType)
        assert members == {TaskType.PLAN, TaskType.IMPLEMENT, TaskType.BUGFIX}

    def test_from_string(self) -> None:
        assert TaskType("PLAN") is TaskType.PLAN
        assert TaskType("IMPLEMENT") is TaskType.IMPLEMENT
        assert TaskType("BUGFIX") is TaskType.BUGFIX


# --- WorkItemStatus enum tests ---


class TestWorkItemStatus:
    """Tests for the WorkItemStatus enum."""

    def test_queued_label(self) -> None:
        assert WorkItemStatus.QUEUED.value == "agent:queued"

    def test_in_progress_label(self) -> None:
        assert WorkItemStatus.IN_PROGRESS.value == "agent:in-progress"

    def test_reconciling_label(self) -> None:
        assert WorkItemStatus.RECONCILING.value == "agent:reconciling"

    def test_success_label(self) -> None:
        assert WorkItemStatus.SUCCESS.value == "agent:success"

    def test_error_label(self) -> None:
        assert WorkItemStatus.ERROR.value == "agent:error"

    def test_infra_failure_label(self) -> None:
        assert WorkItemStatus.INFRA_FAILURE.value == "agent:infra-failure"

    def test_stalled_budget_label(self) -> None:
        assert WorkItemStatus.STALLED_BUDGET.value == "agent:stalled-budget"

    def test_all_members(self) -> None:
        expected = {
            WorkItemStatus.QUEUED,
            WorkItemStatus.IN_PROGRESS,
            WorkItemStatus.RECONCILING,
            WorkItemStatus.SUCCESS,
            WorkItemStatus.ERROR,
            WorkItemStatus.INFRA_FAILURE,
            WorkItemStatus.STALLED_BUDGET,
        }
        assert set(WorkItemStatus) == expected


# --- WorkItem model tests ---


class TestWorkItem:
    """Tests for the WorkItem Pydantic model."""

    def test_create_work_item(self, sample_work_item: WorkItem) -> None:
        assert sample_work_item.id == "12345"
        assert sample_work_item.issue_number == 42
        assert sample_work_item.source_url == "https://github.com/test-org/test-repo/issues/42"
        assert sample_work_item.context_body == "Implement the new feature"
        assert sample_work_item.target_repo_slug == "test-org/test-repo"
        assert sample_work_item.task_type == TaskType.IMPLEMENT
        assert sample_work_item.status == WorkItemStatus.QUEUED
        assert sample_work_item.node_id == "NI_node123"

    def test_work_item_serialization(self, sample_work_item: WorkItem) -> None:
        data = sample_work_item.model_dump()
        assert data["id"] == "12345"
        assert data["issue_number"] == 42
        assert data["task_type"] == TaskType.IMPLEMENT
        assert data["status"] == WorkItemStatus.QUEUED

    def test_work_item_from_dict(self) -> None:
        data = {
            "id": "99999",
            "issue_number": 100,
            "source_url": "https://github.com/org/repo/issues/100",
            "context_body": "Some task",
            "target_repo_slug": "org/repo",
            "task_type": "PLAN",
            "status": "agent:in-progress",
            "node_id": "node_xyz",
        }
        item = WorkItem.model_validate(data)
        assert item.task_type == TaskType.PLAN
        assert item.status == WorkItemStatus.IN_PROGRESS

    def test_work_item_missing_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkItem(
                id="12345",
                issue_number=1,
                # missing required fields
            )

    def test_work_item_invalid_task_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkItem(
                id="12345",
                issue_number=1,
                source_url="https://github.com/org/repo/issues/1",
                context_body="test",
                target_repo_slug="org/repo",
                task_type="INVALID",
                status=WorkItemStatus.QUEUED,
                node_id="node_1",
            )


# --- scrub_secrets tests ---


class TestScrubSecrets:
    """Tests for the scrub_secrets function."""

    def test_scrub_github_pat_classic(self) -> None:
        text = "token is ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn"
        result = scrub_secrets(text)
        assert "ghp_" not in result
        assert "***REDACTED***" in result

    def test_scrub_github_app_token(self) -> None:
        text = "token is ghs_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn"
        result = scrub_secrets(text)
        assert "ghs_" not in result
        assert "***REDACTED***" in result

    def test_scrub_github_oauth_token(self) -> None:
        text = "token is gho_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn"
        result = scrub_secrets(text)
        assert "gho_" not in result
        assert "***REDACTED***" in result

    def test_scrub_github_fine_grained_pat(self) -> None:
        text = "token is github_pat_ABCDEFGHIJKLMNOPQRSTUVWXYZab"
        result = scrub_secrets(text)
        assert "github_pat_" not in result
        assert "***REDACTED***" in result

    def test_scrub_bearer_token(self) -> None:
        text = "Authorization: Bearer abcdefghijklmnopqrstuvwxyz0123456789ABCDEF=="
        result = scrub_secrets(text)
        assert "Bearer " not in result
        assert "***REDACTED***" in result

    def test_scrub_openai_key(self) -> None:
        text = "API key: sk-ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        result = scrub_secrets(text)
        assert "sk-" not in result
        assert "***REDACTED***" in result

    def test_scrub_zhipuai_key(self) -> None:
        text = "key: abcdefghijklmnopqrstuvwxyz0123456.zhipuXYZ"
        result = scrub_secrets(text)
        assert ".zhipu" not in result
        assert "***REDACTED***" in result

    def test_no_secrets_unchanged(self) -> None:
        text = "This is a normal string with no secrets."
        result = scrub_secrets(text)
        assert result == text

    def test_custom_replacement(self) -> None:
        text = "token is ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn"
        result = scrub_secrets(text, replacement="[HIDDEN]")
        assert "[HIDDEN]" in result

    def test_multiple_secrets_in_one_string(self) -> None:
        text = (
            "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn and "
            "sk-ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        )
        result = scrub_secrets(text)
        assert "ghp_" not in result
        assert "sk-" not in result
        assert result.count("***REDACTED***") == 2
