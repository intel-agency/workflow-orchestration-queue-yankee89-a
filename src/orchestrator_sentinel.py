"""
OS-APOW Sentinel Orchestrator.

This script acts as the 'Brain' of the OS-APOW system. It:
1. Polls a GitHub repo for issues labeled 'agent:queued'.
2. Claims the task using assign-then-verify distributed locking.
3. Manages the worker lifecycle.
4. Posts heartbeat comments during long-running tasks.
5. Reports progress and results back to GitHub.
"""

import asyncio
import contextlib
import logging
import os
import random
import signal
import subprocess
import sys
import uuid

import httpx

from src.models.work_item import TaskType, WorkItem, WorkItemStatus
from src.queue.github_queue import GitHubQueue

# --- Configuration ---

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))
MAX_BACKOFF = int(os.getenv("MAX_BACKOFF", "960"))
SENTINEL_ID = f"sentinel-{uuid.uuid4().hex[:8]}"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_ORG = os.getenv("GITHUB_ORG", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "300"))
SUBPROCESS_TIMEOUT = int(os.getenv("SUBPROCESS_TIMEOUT", "5700"))
SENTINEL_BOT_LOGIN = os.getenv("SENTINEL_BOT_LOGIN", "")
SHELL_BRIDGE_PATH = "./scripts/devcontainer-opencode.sh"

# Setup Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s [%(levelname)s] {SENTINEL_ID} - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("OS-APOW-Sentinel")

# Graceful shutdown flag
_shutdown_requested = False


def _handle_signal(signum: int, _frame: object) -> None:
    """Set shutdown flag on SIGTERM/SIGINT so the current task can finish."""
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.info("Received %s — will shut down after current task finishes", sig_name)
    _shutdown_requested = True


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


# --- Shell Bridge Interface ---


async def run_shell_command(
    args: list[str], timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    """Invokes the local shell bridge (devcontainer-opencode.sh)."""
    try:
        logger.info("Executing Bridge: %s", " ".join(args))
        process = await asyncio.create_subprocess_exec(
            *args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except TimeoutError:
            logger.warning("Shell command timed out after %ds — killing", timeout)
            process.kill()
            stdout, stderr = await process.communicate()
            return subprocess.CompletedProcess(
                args=args,
                returncode=-1,
                stdout=stdout.decode().strip() if stdout else "",
                stderr=f"TIMEOUT after {timeout}s\n" + (stderr.decode().strip() if stderr else ""),
            )

        return subprocess.CompletedProcess(
            args=args,
            returncode=process.returncode or 0,
            stdout=stdout.decode().strip() if stdout else "",
            stderr=stderr.decode().strip() if stderr else "",
        )
    except Exception as e:
        logger.error("Critical shell execution error: %s", str(e))
        raise


# --- Orchestration Logic ---


class Sentinel:
    """Sentinel orchestrator that polls for tasks and dispatches workers."""

    def __init__(self, queue: GitHubQueue) -> None:
        self.queue = queue
        self._current_backoff = POLL_INTERVAL

    async def _heartbeat_loop(self, item: WorkItem, start_time: float) -> None:
        """Post periodic heartbeat comments while a task is running."""
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            elapsed = int(asyncio.get_event_loop().time() - start_time)
            await self.queue.post_heartbeat(item, SENTINEL_ID, elapsed)

    async def process_task(self, item: WorkItem) -> None:
        """Process a single work item through the worker pipeline."""
        logger.info("Processing Task #%d...", item.issue_number)
        start_time = asyncio.get_event_loop().time()

        heartbeat_task = asyncio.create_task(self._heartbeat_loop(item, start_time))

        try:
            # Step 1: Initialize Infrastructure
            res_up = await run_shell_command([SHELL_BRIDGE_PATH, "up"], timeout=300)
            if res_up.returncode != 0:
                err = f"**Infrastructure Failure** during `up` stage:\n```\n{res_up.stderr}\n```"
                await self.queue.update_status(item, WorkItemStatus.INFRA_FAILURE, err)
                return

            # Step 2: Start Opencode Server
            res_start = await run_shell_command([SHELL_BRIDGE_PATH, "start"], timeout=120)
            if res_start.returncode != 0:
                err = (
                    "**Infrastructure Failure** starting `opencode-server`:\n"
                    f"```\n{res_start.stderr}\n```"
                )
                await self.queue.update_status(item, WorkItemStatus.INFRA_FAILURE, err)
                return

            # Step 3: Trigger Agent Workflow
            workflow_map: dict[TaskType, str] = {
                TaskType.PLAN: "create-app-plan.md",
                TaskType.IMPLEMENT: "perform-task.md",
                TaskType.BUGFIX: "recover-from-error.md",
            }
            workflow = workflow_map.get(item.task_type, "perform-task.md")
            instruction = f"Execute workflow {workflow} for context: {item.source_url}"

            res_prompt = await run_shell_command(
                [SHELL_BRIDGE_PATH, "prompt", instruction],
                timeout=SUBPROCESS_TIMEOUT,
            )

            # Step 4: Handle Completion
            if res_prompt.returncode == 0:
                success_msg = (
                    f"**Workflow Complete**\n"
                    f"Sentinel successfully executed `{workflow}`. "
                    f"Please review Pull Requests."
                )
                await self.queue.update_status(item, WorkItemStatus.SUCCESS, success_msg)
            else:
                log_tail = (
                    res_prompt.stderr[-1500:] if res_prompt.stderr else "No error output captured."
                )
                fail_msg = f"**Execution Error** during `{workflow}`:\n```\n...{log_tail}\n```"
                await self.queue.update_status(item, WorkItemStatus.ERROR, fail_msg)

        except Exception as e:
            logger.exception("Internal Sentinel Error on Task #%d", item.issue_number)
            await self.queue.update_status(
                item,
                WorkItemStatus.INFRA_FAILURE,
                f"Sentinel encountered an unhandled exception: {str(e)}",
            )
        finally:
            heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat_task

            logger.info("Resetting environment (stop)")
            await run_shell_command([SHELL_BRIDGE_PATH, "stop"], timeout=60)

    async def run_forever(self) -> None:
        """Main polling loop that continuously looks for queued tasks."""
        logger.info("Sentinel %s entering polling loop (interval: %ds)", SENTINEL_ID, POLL_INTERVAL)

        while not _shutdown_requested:
            try:
                tasks = await self.queue.fetch_queued_tasks()
                if tasks:
                    logger.info("Found %d queued task(s).", len(tasks))
                    for task in tasks:
                        if _shutdown_requested:
                            break
                        if await self.queue.claim_task(task, SENTINEL_ID, SENTINEL_BOT_LOGIN):
                            await self.process_task(task)
                            break

                self._current_backoff = POLL_INTERVAL

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in (403, 429):
                    jitter = random.uniform(0, self._current_backoff * 0.1)
                    wait = min(self._current_backoff + jitter, MAX_BACKOFF)
                    logger.warning("Rate limited (%d) — backing off %.0fs", status, wait)
                    self._current_backoff = min(self._current_backoff * 2, MAX_BACKOFF)
                    await asyncio.sleep(wait)
                    continue
                else:
                    logger.error("GitHub API error: %s", exc)
            except Exception as e:
                logger.error("Polling cycle error: %s", str(e))

            await asyncio.sleep(self._current_backoff)

        logger.info("Shutdown flag set — exiting polling loop")


# --- Entry Point ---


async def _main() -> None:
    required = ["GITHUB_TOKEN", "GITHUB_ORG", "GITHUB_REPO"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        logger.error("Critical Error: Missing environment variables: %s", ", ".join(missing))
        sys.exit(1)

    if not SENTINEL_BOT_LOGIN:
        logger.warning(
            "SENTINEL_BOT_LOGIN is not set — assign-then-verify locking is disabled. "
            "Set it to the GitHub login of the bot account for concurrency safety."
        )

    gh_queue = GitHubQueue(GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO)
    sentinel = Sentinel(gh_queue)

    try:
        await sentinel.run_forever()
    finally:
        await gh_queue.close()
        logger.info("Sentinel shut down.")


def _cli_main() -> None:
    """Console script entry point for ``uv run sentinel``."""
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logger.info("Sentinel shutting down gracefully.")


if __name__ == "__main__":
    _cli_main()
