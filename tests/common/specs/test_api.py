from unittest.mock import MagicMock

import pytest

from dataclasses import dataclass
import hashlib
import hmac

import anyio.abc
import anyio

from httpx import AsyncClient

from nopf.core.channel import (
    create_channel,
    ChannelReceiver,
    EventCreate,
    EventUpdate,
    EventDelete,
)

from nopf.settings import Settings
from nopf.schema import WebhookPayload
from nopf.api import server_task


pytestmark = pytest.mark.anyio


@dataclass
class HttpServer:
    taskgroup: anyio.abc.TaskGroup
    mbox: ChannelReceiver
    binds: list[str]


def sign_request(content: str) -> str:
    hashobj = hmac.new(key=b"s3cr3!", msg=content, digestmod=hashlib.sha512)
    return hashobj.hexdigest()


@pytest.fixture(scope="function")
async def http_server():
    settings = Settings(
        secret_key="s3cr3!",
        netbox_api="http://netbox.local/",
        netbox_token="t0k3n",
        server_bind_host="127.0.0.1",
        server_bind_port=0,
        server_callback_name="test",
    )

    shutdown = anyio.Event()
    sender, receiver = create_channel()

    async with anyio.create_task_group() as tg:
        binds = await tg.start(server_task, settings, sender, shutdown.wait)

        yield HttpServer(taskgroup=tg, mbox=receiver, binds=binds)

        shutdown.set()
        await sender.aclose()


@pytest.fixture
async def http_client(http_server: HttpServer):
    async with AsyncClient(base_url=http_server.binds[0]) as client:
        yield client


async def test_healthcheck(http_client: AsyncClient):
    resp = await http_client.get("/health")
    resp.raise_for_status()

    assert resp.status_code == 200
    assert resp.text == "OK"


async def test_invalid_signature(http_client: AsyncClient):
    payload = WebhookPayload(
        event="created",
        timestamp="2021-01-01T00:00:00Z",
        model="foo",
        username="unit",
        request_id="123",
        data={},
        snapshots={
            "prechange": None,
            "postchange": None,
        },
    )

    resp = await http_client.post(
        "/callback/test.foo",
        content=payload.model_dump_json(),
    )
    assert resp.status_code == 403

    resp = await http_client.post(
        "/callback/test.foo",
        content=payload.model_dump_json(),
        headers={"X-Hook-Signature": "invalid"},
    )
    assert resp.status_code == 403


async def test_non_matching_payload(http_client: AsyncClient):
    payload = WebhookPayload(
        event="created",
        timestamp="2021-01-01T00:00:00Z",
        model="foobar",
        username="unit",
        request_id="123",
        data={},
        snapshots={
            "prechange": None,
            "postchange": None,
        },
    )
    content = payload.model_dump_json()
    signature = sign_request(content.encode())

    resp = await http_client.post(
        "/callback/test.foo",
        content=content,
        headers={"X-Hook-Signature": signature},
    )

    assert resp.status_code == 400


async def test_created_event(
    http_server: HttpServer,
    http_client: AsyncClient,
):
    on_event = MagicMock()

    async def consumer(rx: ChannelReceiver):
        async for resp_tx, event in rx.stream:
            on_event(event)
            await resp_tx.send(None)

    http_server.taskgroup.start_soon(consumer, http_server.mbox)

    payload = WebhookPayload(
        event="created",
        timestamp="2021-01-01T00:00:00Z",
        model="foo",
        username="unit",
        request_id="123",
        data={},
        snapshots={
            "prechange": None,
            "postchange": None,
        },
    )
    content = payload.model_dump_json()
    signature = sign_request(content.encode())

    resp = await http_client.post(
        "/callback/test.foo",
        content=content,
        headers={"X-Hook-Signature": signature},
    )

    assert resp.status_code == 200

    payload.model = "test.foo"
    on_event.assert_called_once_with(EventCreate(payload=payload))


async def test_updated_event(
    http_server: HttpServer,
    http_client: AsyncClient,
):
    on_event = MagicMock()

    async def consumer(rx: ChannelReceiver):
        async for resp_tx, event in rx.stream:
            on_event(event)
            await resp_tx.send(None)

    http_server.taskgroup.start_soon(consumer, http_server.mbox)

    payload = WebhookPayload(
        event="updated",
        timestamp="2021-01-01T00:00:00Z",
        model="foo",
        username="unit",
        request_id="123",
        data={},
        snapshots={
            "prechange": None,
            "postchange": None,
        },
    )
    content = payload.model_dump_json()
    signature = sign_request(content.encode())

    resp = await http_client.post(
        "/callback/test.foo",
        content=content,
        headers={"X-Hook-Signature": signature},
    )

    assert resp.status_code == 200

    payload.model = "test.foo"
    on_event.assert_called_once_with(EventUpdate(payload=payload))


async def test_deleted_event(
    http_server: HttpServer,
    http_client: AsyncClient,
):
    on_event = MagicMock()

    async def consumer(rx: ChannelReceiver):
        async for resp_tx, event in rx.stream:
            on_event(event)
            await resp_tx.send(None)

    http_server.taskgroup.start_soon(consumer, http_server.mbox)

    payload = WebhookPayload(
        event="deleted",
        timestamp="2021-01-01T00:00:00Z",
        model="foo",
        username="unit",
        request_id="123",
        data={},
        snapshots={
            "prechange": None,
            "postchange": None,
        },
    )
    content = payload.model_dump_json()
    signature = sign_request(content.encode())

    resp = await http_client.post(
        "/callback/test.foo",
        content=content,
        headers={"X-Hook-Signature": signature},
    )

    assert resp.status_code == 200

    payload.model = "test.foo"
    on_event.assert_called_once_with(EventDelete(payload=payload))
