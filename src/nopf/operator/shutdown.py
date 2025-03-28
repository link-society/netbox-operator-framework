from typing import Any

import signal

from threading import Event
from anyio import to_thread

from logbook import Logger  # type: ignore


class ShutdownHandler:
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.event = Event()

    def trigger(self, *_: Any) -> None:
        self.event.set()

    async def wait(self) -> None:
        await to_thread.run_sync(self.event.wait)
        self.logger.info("Shutdown requested")

    def connect(self):  # pragma: no cover
        for signame in ("SIGINT", "SIGTERM", "SIGBREAK"):
            if hasattr(signal, signame):
                signal.signal(getattr(signal, signame), self.trigger)
