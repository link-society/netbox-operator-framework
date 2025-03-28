"""
`Anycorn <https://github.com/davidbrochart/anycorn>`_ HTTP server, serving the
`FastAPI <https://fastapi.tiangolo.com/>`_ ASGI application, which is used to
handle the Netbox Webhook requests.
"""

from typing import cast, Callable, Awaitable
from anycorn.typing import ASGIFramework

from anyio.abc import TaskStatus
from anyio import TASK_STATUS_IGNORED

from fastapi import FastAPI
import anycorn

from nopf.settings import Settings
from nopf.logging import WebLogger
from nopf.core.channel import ChannelSender

from .router import router


async def server_task(
    settings: Settings,
    tx: ChannelSender,
    shutdown_trigger: Callable[[], Awaitable[None]],
    task_status: TaskStatus[list[str]] = TASK_STATUS_IGNORED,
) -> None:
    """
    Create the FastAPI application, and starts the HTTP server.

    :param settings: The operator settings.
    :param tx: Internal operator channel, used to send the webhook events to.
    :param shutdown_trigger: Used to gracefully shutdown the HTTP server.
    :param task_status: Used to notify when the HTTP server is ready to accept requests.
    """

    asgi_app = FastAPI(openapi_url=None)
    asgi_app.state.settings = settings
    asgi_app.state.channel = tx
    asgi_app.include_router(router)

    config = anycorn.Config()
    config.logger_class = WebLogger
    config.bind = [f"{settings.server_bind_host}:{settings.server_bind_port}"]

    await anycorn.serve(
        cast(ASGIFramework, asgi_app),
        config,
        shutdown_trigger=shutdown_trigger,
        task_status=task_status,
    )
