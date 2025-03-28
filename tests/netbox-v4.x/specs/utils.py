from unittest.mock import MagicMock

from contextlib import asynccontextmanager

from anyio.abc import TaskStatus
from anyio import create_task_group, fail_after, to_thread, sleep, TASK_STATUS_IGNORED

from httpx import AsyncClient as HttpClient

from nopf.operator import Operator


@asynccontextmanager
async def run_operator(
    op: Operator,
    expected_exit_code: int = 0,
    healthcheck: bool = True,
):
    exit_notifier = MagicMock()

    async with create_task_group() as tg:
        await tg.start(operator_task, op, exit_notifier, healthcheck)

        yield

        op.shutdown_handler.trigger()

    exit_notifier.assert_called_once_with(expected_exit_code)


async def operator_task(
    op: Operator,
    exit_notifier: MagicMock,
    healthcheck: bool,
    task_status: TaskStatus[None] = TASK_STATUS_IGNORED,
):
    async with create_task_group() as tg:
        tg.start_soon(
            to_thread.run_sync,
            lambda: op.run(catch_ctrlc=False, exit=exit_notifier),
        )

        if healthcheck:
            await tg.start(wait_for_operator_healthcheck)

        task_status.started()


async def wait_for_operator_healthcheck(
    task_status: TaskStatus[None] = TASK_STATUS_IGNORED,
):
    async with HttpClient(base_url="http://localhost:5000") as operator_client:
        with fail_after(30):
            while True:
                try:
                    resp = await operator_client.get("/health")
                    resp.raise_for_status()
                    break

                except Exception:
                    await sleep(1.0)

    task_status.started()
