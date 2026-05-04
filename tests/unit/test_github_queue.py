"""Unit tests for GitHubQueue and ITaskQueue."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.work_item import TaskType, WorkItem, WorkItemStatus
from src.queue.github_queue import GitHubQueue, ITaskQueue

pytestmark = pytest.mark.unit

# --- ITaskQueue interface tests ---


class TestITaskQueue:
    """Tests that ITaskQueue defines the expected abstract interface."""

    def test_cannot_instantiate_abstract(self) -> None:
        """ITaskQueue should not be instantiable directly."""
        with pytest.raises(TypeError):
            ITaskQueue()  # type: ignore[abstract]

    def test_subclass_must_implement_methods(self) -> None:
        """A subclass that doesn't implement all methods should not be instantiable."""

        class PartialImpl(ITaskQueue):
            async def add_to_queue(self, _item: WorkItem) -> bool:
                return True

        with pytest.raises(TypeError):
            PartialImpl()  # type: ignore[abstract]

    def test_complete_implementation_works(self) -> None:
        """A complete implementation should be instantiable."""

        class FullImpl(ITaskQueue):
            async def add_to_queue(self, _item: WorkItem) -> bool:
                return True

            async def fetch_queued_tasks(self) -> list[WorkItem]:
                return []

            async def update_status(
                self, _item: WorkItem, _status: WorkItemStatus, _comment: str | None = None
            ) -> None:
                pass

        impl = FullImpl()
        assert isinstance(impl, ITaskQueue)


# --- GitHubQueue tests ---


class TestGitHubQueue:
    """Tests for the GitHubQueue concrete implementation."""

    @pytest.fixture
    def queue(self) -> GitHubQueue:
        """Create a GitHubQueue instance with a mock token."""
        return GitHubQueue(token="fake-token", org="test-org", repo="test-repo")

    def test_init(self, queue: GitHubQueue) -> None:
        assert queue.token == "fake-token"
        assert queue.org == "test-org"
        assert queue.repo == "test-repo"
        assert "Authorization" in queue.headers
        assert queue.headers["Authorization"] == "token fake-token"

    def test_repo_api_url(self, queue: GitHubQueue) -> None:
        url = queue._repo_api_url("owner/repo")
        assert url == "https://api.github.com/repos/owner/repo"

    async def test_close(self, queue: GitHubQueue) -> None:
        """close() should not raise."""
        await queue.close()

    async def test_add_to_queue_success(self, queue: GitHubQueue) -> None:
        item = WorkItem(
            id="123",
            issue_number=1,
            source_url="https://github.com/test-org/test-repo/issues/1",
            context_body="Test",
            target_repo_slug="test-org/test-repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            node_id="node_1",
        )

        mock_response = MagicMock()
        mock_response.status_code = 201

        with patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await queue.add_to_queue(item)

        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "labels" in call_args[1]["json"]

    async def test_add_to_queue_failure(self, queue: GitHubQueue) -> None:
        item = WorkItem(
            id="123",
            issue_number=1,
            source_url="https://github.com/test-org/test-repo/issues/1",
            context_body="Test",
            target_repo_slug="test-org/test-repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            node_id="node_1",
        )

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await queue.add_to_queue(item)

        assert result is False

    async def test_fetch_queued_tasks_empty(self, queue: GitHubQueue) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await queue.fetch_queued_tasks()

        assert result == []

    async def test_fetch_queued_tasks_with_issues(self, queue: GitHubQueue) -> None:
        issues: list[dict[str, Any]] = [
            {
                "id": 111,
                "number": 10,
                "html_url": "https://github.com/test-org/test-repo/issues/10",
                "body": "Implement feature X",
                "labels": [{"name": "agent:queued"}],
                "node_id": "node_10",
            },
            {
                "id": 222,
                "number": 11,
                "html_url": "https://github.com/test-org/test-repo/issues/11",
                "body": "[Plan] Design system",
                "labels": [{"name": "agent:queued"}, {"name": "agent:plan"}],
                "node_id": "node_11",
            },
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = issues

        with patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await queue.fetch_queued_tasks()

        assert len(result) == 2
        assert result[0].issue_number == 10
        assert result[0].task_type == TaskType.IMPLEMENT
        assert result[1].issue_number == 11
        assert result[1].task_type == TaskType.PLAN

    async def test_fetch_queued_tasks_bugfix(self, queue: GitHubQueue) -> None:
        issues: list[dict[str, Any]] = [
            {
                "id": 333,
                "number": 12,
                "html_url": "https://github.com/test-org/test-repo/issues/12",
                "body": "Fix the bug",
                "labels": [{"name": "agent:queued"}, {"name": "bug"}],
                "node_id": "node_12",
            },
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = issues

        with patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await queue.fetch_queued_tasks()

        assert len(result) == 1
        assert result[0].task_type == TaskType.BUGFIX

    async def test_fetch_queued_tasks_no_org_repo(self) -> None:
        q = GitHubQueue(token="fake-token")
        result = await q.fetch_queued_tasks()
        assert result == []
        await q.close()

    async def test_fetch_queued_tasks_rate_limit(self, queue: GitHubQueue) -> None:
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limited", request=MagicMock(), response=mock_response
        )

        with (
            patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get,
            pytest.raises(httpx.HTTPStatusError),
        ):
            mock_get.return_value = mock_response
            await queue.fetch_queued_tasks()

    async def test_fetch_queued_tasks_api_error(self, queue: GitHubQueue) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await queue.fetch_queued_tasks()

        assert result == []

    async def test_update_status_success(self, queue: GitHubQueue) -> None:
        item = WorkItem(
            id="123",
            issue_number=1,
            source_url="https://github.com/test-org/test-repo/issues/1",
            context_body="Test",
            target_repo_slug="test-org/test-repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.IN_PROGRESS,
            node_id="node_1",
        )

        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 200
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200

        with (
            patch.object(queue._client, "delete", new_callable=AsyncMock) as mock_delete,
            patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post,
        ):
            mock_delete.return_value = mock_delete_response
            mock_post.return_value = mock_post_response
            await queue.update_status(item, WorkItemStatus.SUCCESS, "All done!")

        # Should have 2 posts: one for labels, one for comment
        assert mock_post.call_count == 2

    async def test_claim_task_with_bot_login(self, queue: GitHubQueue) -> None:
        item = WorkItem(
            id="123",
            issue_number=1,
            source_url="https://github.com/test-org/test-repo/issues/1",
            context_body="Test",
            target_repo_slug="test-org/test-repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            node_id="node_1",
        )

        mock_assign_response = MagicMock()
        mock_assign_response.status_code = 201

        mock_verify_response = MagicMock()
        mock_verify_response.status_code = 200
        mock_verify_response.json.return_value = {"assignees": [{"login": "test-bot"}]}

        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 200

        mock_post_response = MagicMock()
        mock_post_response.status_code = 201

        with (
            patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get,
            patch.object(queue._client, "delete", new_callable=AsyncMock) as mock_delete,
        ):
            mock_post.return_value = mock_post_response
            mock_get.return_value = mock_verify_response
            mock_delete.return_value = mock_delete_response
            result = await queue.claim_task(item, "sentinel-1", "test-bot")

        assert result is True

    async def test_claim_task_lost_race(self, queue: GitHubQueue) -> None:
        item = WorkItem(
            id="123",
            issue_number=1,
            source_url="https://github.com/test-org/test-repo/issues/1",
            context_body="Test",
            target_repo_slug="test-org/test-repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            node_id="node_1",
        )

        mock_assign_response = MagicMock()
        mock_assign_response.status_code = 201

        mock_verify_response = MagicMock()
        mock_verify_response.status_code = 200
        mock_verify_response.json.return_value = {"assignees": [{"login": "other-bot"}]}

        with (
            patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get,
        ):
            mock_post.return_value = mock_assign_response
            mock_get.return_value = mock_verify_response
            result = await queue.claim_task(item, "sentinel-1", "test-bot")

        assert result is False

    async def test_post_heartbeat(self, queue: GitHubQueue) -> None:
        item = WorkItem(
            id="123",
            issue_number=1,
            source_url="https://github.com/test-org/test-repo/issues/1",
            context_body="Test",
            target_repo_slug="test-org/test-repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.IN_PROGRESS,
            node_id="node_1",
        )

        mock_response = MagicMock()
        mock_response.status_code = 201

        with patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            await queue.post_heartbeat(item, "sentinel-1", 300)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        body = call_args[1]["json"]["body"]
        assert "sentinel-1" in body
        assert "5m" in body  # 300s // 60 = 5m
