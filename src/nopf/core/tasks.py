from typing import Protocol, Awaitable

from anyio.abc import TaskStatus, TaskGroup
from anyio import TASK_STATUS_IGNORED

from nopf.core.channel import ChannelSender


class TaskHandler(Protocol):
    def __call__(
        self,
        tx: ChannelSender,
        task_status: TaskStatus[None] = TASK_STATUS_IGNORED,
    ) -> Awaitable[None]: ...


class Tasks:
    def __init__(self) -> None:
        self.handlers: list[TaskHandler] = []

    def add(self, handler: TaskHandler) -> None:
        self.handlers.append(handler)

    async def start(self, tg: TaskGroup, tx: ChannelSender) -> None:
        for handler in self.handlers:
            await tg.start(handler, tx.clone())
