from typing import Callable

import sys

from logbook import Logger  # type: ignore

from anyio.abc import TaskStatus
from anyio import create_task_group, TASK_STATUS_IGNORED, run as run_event_loop

from nopf.settings import Settings
from nopf.logging import LogHandler
from nopf.api import server_task
from nopf.client import NetboxClient, _client

from nopf.core.errors import flatten_error_tree
from nopf.core.tasks import Tasks, TaskHandler
from nopf.core.channel import ChannelSender
from nopf.core.handlers import (
    Handlers,
    ModelHandler,
    CustomHandler,
)

from .shutdown import ShutdownHandler
from .controller import task as controller_task
from .setup import create_webhooks


type Decorator[T] = Callable[[T], T]


class Operator:
    def __init__(self, settings: Settings):
        self.settings = settings

        self.logger = Logger("nopf.operator")
        self.shutdown_handler = ShutdownHandler(self.logger)

        self.tasks = Tasks()
        self.handlers = Handlers()

        self.exit_code = 0

    def run(
        self,
        catch_ctrlc: bool = True,
        exit: Callable[[int], None] = sys.exit,
    ) -> None:
        if catch_ctrlc:  # pragma: no cover
            self.shutdown_handler.connect()

        with LogHandler(self.settings).applicationbound():
            try:
                run_event_loop(self._run)

            except Exception as err:
                self._on_error(err)

        exit(self.exit_code)

    async def _run(self) -> None:
        self.logger.info("Initialize netbox client")
        _client.set(NetboxClient(self.settings))

        self.logger.info("Create webhooks")
        await create_webhooks(self.settings, self.handlers)

        async with create_task_group() as tg:
            self.logger.info("Start controller")
            tx = await tg.start(controller_task, self.handlers)

            self.logger.info("Start tasks")
            await tg.start(self._run_tasks, tx)

            self.logger.info("Start HTTP server")
            await self._run_server(tx)

            self.logger.info("Shutting down")
            tg.cancel_scope.cancel()

    async def _run_tasks(
        self,
        tx: ChannelSender,
        task_status: TaskStatus[None] = TASK_STATUS_IGNORED,
    ) -> None:
        try:
            async with create_task_group() as tg:
                await self.tasks.start(tg, tx)
                task_status.started()

        except Exception as err:
            self._on_error(err)
            self.shutdown_handler.trigger()

    async def _run_server(self, tx: ChannelSender) -> None:
        async with create_task_group() as tg:
            await tg.start(
                server_task,
                self.settings,
                tx.clone(),
                self.shutdown_handler.wait,
            )

    def _on_error(self, err: ExceptionGroup | Exception) -> None:
        if isinstance(err, ExceptionGroup):
            excgroup = err
            self.logger.error(
                "Unhandled exception tree",
                extra={
                    "exc.group": f"{excgroup}",
                },
            )

            for exc in flatten_error_tree(excgroup):
                self.logger.error(
                    "Sub exception",
                    extra={
                        "exc.type": type(exc).__name__,
                        "exc.message": str(exc),
                    },
                )

        else:
            self.logger.error(
                f"Unhandled exception",
                extra={
                    "exc.type": type(err).__name__,
                    "exc.message": str(err),
                },
            )

        self.exit_code = 1

    def task(self, func: TaskHandler) -> TaskHandler:
        self.tasks.add(func)
        return func

    def on_create(self, model_name: str) -> Decorator[ModelHandler]:
        def decorator(func: ModelHandler) -> ModelHandler:
            self.handlers.add_create_handler(model_name, func)
            return func

        return decorator

    def on_update(self, model_name: str) -> Decorator[ModelHandler]:
        def decorator(func: ModelHandler) -> ModelHandler:
            self.handlers.add_update_handler(model_name, func)
            return func

        return decorator

    def on_delete(self, model_name: str) -> Decorator[ModelHandler]:
        def decorator(func: ModelHandler) -> ModelHandler:
            self.handlers.add_delete_handler(model_name, func)
            return func

        return decorator

    def on_custom(self, func: CustomHandler) -> CustomHandler:
        self.handlers.add_custom_handler(func)
        return func
