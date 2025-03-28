from anyio.abc import TaskStatus
from anyio import TASK_STATUS_IGNORED

from nopf.core.channel import (
    ChannelSender,
    create_channel,
    EventCreate,
    EventUpdate,
    EventDelete,
    EventCustom,
)
from nopf.core.handlers import Handlers


async def task(
    handlers: Handlers,
    task_status: TaskStatus[ChannelSender] = TASK_STATUS_IGNORED,
) -> None:
    tx, rx = create_channel()
    task_status.started(tx)

    async for resp_tx, evt in rx.stream:
        try:
            match evt:
                case EventCreate():
                    await handlers.invoke_create_handlers(evt.payload)

                case EventUpdate():
                    await handlers.invoke_update_handlers(evt.payload)

                case EventDelete():
                    await handlers.invoke_delete_handlers(evt.payload)

                case EventCustom():
                    await handlers.invoke_custom_handlers(evt.data)

                case _:
                    typename = type(evt).__name__
                    raise ValueError(f"Invalid event type: {typename}")

        except Exception as err:
            await resp_tx.send(err)

        else:
            await resp_tx.send(None)
