"""
FastAPI routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, HTTPException

from nopf.schema import WebhookPayload
from nopf.core.channel import (
    ChannelSender,
    EventCreate,
    EventUpdate,
    EventDelete,
)

from .security import verify_netbox_request_signature
from .deps import get_channel


router = APIRouter()


@router.get("/health")
def health() -> Response:
    """
    Healthcheck, always returns a ``200 OK`` response.
    Used for monitoring purposes.
    """

    return Response(content="OK", media_type="text/plain", status_code=200)


@router.post(
    "/callback/{model_name}",
    dependencies=[Depends(verify_netbox_request_signature)],
)
async def handle_netbox_webhook(
    model_name: str,
    payload: WebhookPayload,
    channel: Annotated[ChannelSender, Depends(get_channel)],
) -> Response:
    """
    Actual webhook callback route, dispatching the event to the correct
    event handlers.

    .. note::

       Netbox does not include the fully qualified model name in the payload.
       So we expect the model name to be passed as a path parameter.

       If the model name in the payload does not match the last segment of the
       fully qualified model name, we return a ``400 Bad Request`` response.
    """

    if model_name.rsplit(".", 1)[-1] != payload.model:
        raise HTTPException(
            status_code=400,
            detail="Payload does not match expected model name",
        )

    # To facilitate dispatching the event to the correct handlers, we replace
    # the model name in the payload with the fully qualified model name.
    payload.model = model_name

    match payload.event:
        case "created":
            await channel.send(EventCreate(payload=payload))

        case "updated":
            await channel.send(EventUpdate(payload=payload))

        case "deleted":
            await channel.send(EventDelete(payload=payload))

    return Response(content="OK", media_type="text/plain", status_code=200)
