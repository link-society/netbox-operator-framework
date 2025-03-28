import pytest

from anyio import create_task_group, TASK_STATUS_IGNORED
from anyio.abc import TaskStatus

from nopf.core.channel import create_channel, ChannelSender, ChannelReceiver
from nopf.core.tasks import Tasks


pytestmark = pytest.mark.anyio


async def test_group_start():
    count = 0

    async def producer(
        tx: ChannelSender,
        task_status: TaskStatus[None] = TASK_STATUS_IGNORED,
    ):
        task_status.started()

        await tx.send("hello")
        await tx.aclose()

    async def consumer(rx: ChannelReceiver):
        nonlocal count

        async for resp_tx, event in rx.stream:
            assert event == "hello"
            await resp_tx.send(None)
            count += 1

    tasks = Tasks()

    tasks.add(producer)
    tasks.add(producer)

    sender, receiver = create_channel()

    async with create_task_group() as tg:
        tg.start_soon(consumer, receiver)
        await tasks.start(tg, sender)
        await sender.aclose()

    assert count == 2
