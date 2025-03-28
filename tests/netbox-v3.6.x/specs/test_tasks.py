from unittest.mock import MagicMock
import pytest

from threading import Event

from anyio.abc import TaskStatus
from anyio import to_thread, sleep

from nopf.core.channel import ChannelSender, EventCustom

from nopf.operator import Operator
from nopf.settings import Settings

from .utils import run_operator

pytestmark = pytest.mark.anyio


async def test_task_failure(settings: Settings):
    op = Operator(settings)

    trigger_error = Event()

    @op.task
    async def failing_task(tx: ChannelSender, task_status: TaskStatus[None]):
        task_status.started()

        await to_thread.run_sync(trigger_error.wait)
        raise RuntimeError("test")

    async with run_operator(op, expected_exit_code=1):
        trigger_error.set()
        await sleep(0.5)


async def test_send_custom_event(settings: Settings):
    op = Operator(settings)

    custom_notifier = MagicMock()

    @op.task
    async def notify(tx: ChannelSender, task_status: TaskStatus[None]):
        task_status.started()

        await tx.send(EventCustom(data="test"))

    @op.on_custom
    async def on_custom_event(data: str):
        custom_notifier(data)

    async with run_operator(op):
        await sleep(0.5)

    custom_notifier.assert_called_once_with("test")
