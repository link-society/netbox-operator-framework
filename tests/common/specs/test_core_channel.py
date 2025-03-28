import pytest
import anyio

from nopf.core.channel import (
    create_channel,
    ChannelSender,
    ChannelReceiver,
    EventCustom,
)


pytestmark = pytest.mark.anyio


async def test_single_producer_single_consumer():
    sender, receiver = create_channel()

    async def producer(sender: ChannelSender):
        msg = EventCustom(data="hello")
        await sender.send(msg)
        await sender.aclose()

    async def consumer(receiver: ChannelReceiver):
        async for resp_tx, event in receiver.stream:
            assert isinstance(event, EventCustom)
            assert event.data == "hello"
            await resp_tx.send(None)

    async with anyio.create_task_group() as tg:
        tg.start_soon(producer, sender)
        tg.start_soon(consumer, receiver)


async def test_single_producer_multiple_consumer():
    sender, receiver = create_channel()
    world = {
        "c0": 0,
        "c1": 0,
    }

    async def producer(sender: ChannelSender):
        msg = EventCustom(data="hello")
        await sender.send(msg)
        await sender.send(msg)
        await sender.aclose()

    async def consumer(name: str, receiver: ChannelReceiver):
        async for resp_tx, event in receiver.stream:
            assert isinstance(event, EventCustom)
            assert event.data == "hello"
            await resp_tx.send(None)
            world[name] += 1

    async with anyio.create_task_group() as tg:
        tg.start_soon(producer, sender)
        tg.start_soon(consumer, "c0", receiver.clone())
        tg.start_soon(consumer, "c1", receiver)

    assert world["c0"] == 1
    assert world["c1"] == 1


async def test_multiple_producer_single_consumer():
    sender, receiver = create_channel()
    count = 0

    async def producer(sender: ChannelSender):
        msg = EventCustom(data="hello")
        await sender.send(msg)
        await sender.aclose()

    async def consumer(receiver: ChannelReceiver):
        nonlocal count

        async for resp_tx, event in receiver.stream:
            assert isinstance(event, EventCustom)
            assert event.data == "hello"
            await resp_tx.send(None)
            count += 1

    async with anyio.create_task_group() as tg:
        tg.start_soon(producer, sender.clone())
        tg.start_soon(producer, sender)
        tg.start_soon(consumer, receiver)

    assert count == 2


async def test_reply_exception():
    sender, receiver = create_channel()

    async def producer(sender: ChannelSender):
        msg = EventCustom(data="hello")

        with pytest.raises(ValueError, match="error"):
            await sender.send(msg)

        await sender.aclose()

    async def consumer(receiver: ChannelReceiver):
        async for resp_tx, event in receiver.stream:
            assert isinstance(event, EventCustom)
            assert event.data == "hello"
            await resp_tx.send(ValueError("error"))

    async with anyio.create_task_group() as tg:
        tg.start_soon(producer, sender)
        tg.start_soon(consumer, receiver)


async def test_sender_closed():
    sender, _ = create_channel()
    await sender.aclose()

    with pytest.raises(anyio.ClosedResourceError):
        await sender.send(EventCustom(data="hello"))


async def test_receiver_closed():
    sender, receiver = create_channel()
    await receiver.aclose()

    with pytest.raises(anyio.BrokenResourceError):
        await sender.send(EventCustom(data="hello"))
