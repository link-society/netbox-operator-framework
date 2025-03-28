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


async def test_channel_error(settings: Settings):
    op = Operator(settings)

    trigger_error = Event()
    err_notifier = MagicMock()

    @op.task
    async def notify(tx: ChannelSender, task_status: TaskStatus[None]):
        task_status.started()

        await to_thread.run_sync(trigger_error.wait)

        try:
            await tx.send(EventCustom(data="test"))

        except RuntimeError as err:
            err_notifier(f"{err}")

    @op.on_custom
    async def on_custom_event(data: str):
        raise RuntimeError("test")

    async with run_operator(op):
        trigger_error.set()
        await sleep(0.5)

    err_notifier.assert_called_once_with("test")


async def test_invalid_payload(settings: Settings):
    op = Operator(settings)

    err_notifier = MagicMock()
    trigger_error = Event()

    @op.task
    async def notify(tx: ChannelSender, task_status: TaskStatus[None]):
        task_status.started()

        await to_thread.run_sync(trigger_error.wait)

        try:
            await tx.send("invalid payload")

        except ValueError as err:
            err_notifier(f"{err}")

    async with run_operator(op):
        trigger_error.set()
        await sleep(0.5)

    err_notifier.assert_called_once_with("Invalid event type: str")


async def test_invalid_netbox_api(netbox):
    settings = Settings(
        netbox_api="http://invalid:8080",
        netbox_token="s3cr3!",
        server_bind_host="0.0.0.0",
        server_bind_port=5000,
        server_callback_name="pytest",
        server_callback_url="http://host.docker.internal:5000",
    )
    op = Operator(settings)

    async with run_operator(op, expected_exit_code=1, healthcheck=False):
        await sleep(0.5)
