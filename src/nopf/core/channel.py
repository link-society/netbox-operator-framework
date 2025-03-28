from typing import Any

from anyio.abc import ObjectSendStream, ObjectReceiveStream
from anyio import create_memory_object_stream

from pydantic import BaseModel

from nopf.schema import WebhookPayload


class EventCreate(BaseModel):
    payload: WebhookPayload


class EventUpdate(BaseModel):
    payload: WebhookPayload


class EventDelete(BaseModel):
    payload: WebhookPayload


class EventCustom(BaseModel):
    data: Any


type Event = EventCreate | EventUpdate | EventDelete | EventCustom

type ChannelResponse = Exception | None
type ChannelMessage = tuple[ObjectSendStream[ChannelResponse], Event]


class ChannelSender:
    def __init__(self, stream: ObjectSendStream[ChannelMessage]):
        self.stream = stream

    def clone(self):
        return ChannelSender(self.stream.clone())

    async def aclose(self):
        await self.stream.aclose()

    async def send(self, event: Event) -> None:
        resp_tx, resp_rx = create_memory_object_stream[ChannelResponse]()

        await self.stream.send((resp_tx, event))

        response = await resp_rx.receive()
        if isinstance(response, Exception):
            raise response

        await resp_rx.aclose()


class ChannelReceiver:
    def __init__(self, stream: ObjectReceiveStream[ChannelMessage]):
        self.stream = stream

    def clone(self):
        return ChannelReceiver(self.stream.clone())

    async def aclose(self):
        await self.stream.aclose()


def create_channel() -> tuple[ChannelSender, ChannelReceiver]:
    tx, rx = create_memory_object_stream[ChannelMessage]()

    return ChannelSender(tx), ChannelReceiver(rx)
