from unittest.mock import AsyncMock

import pytest

from nopf.core.handlers import Handlers
from nopf.schema import WebhookPayload


pytestmark = pytest.mark.anyio


async def test_invocation():
    handlers = Handlers()

    create_mock = AsyncMock()
    update_mock = AsyncMock()
    delete_mock = AsyncMock()
    custom_mock = AsyncMock()

    model_name = "test"

    handlers.add_create_handler(model_name, create_mock)
    handlers.add_update_handler(model_name, update_mock)
    handlers.add_delete_handler(model_name, delete_mock)
    handlers.add_custom_handler(custom_mock)

    webhook_payload = WebhookPayload(
        event="string",
        timestamp="string",
        model=model_name,
        username="string",
        request_id="string",
        data={},
        snapshots={"prechange": None, "postchange": None},
    )
    custom_payload = {"hello": "world"}

    await handlers.invoke_create_handlers(webhook_payload)
    await handlers.invoke_update_handlers(webhook_payload)
    await handlers.invoke_delete_handlers(webhook_payload)
    await handlers.invoke_custom_handlers(custom_payload)

    create_mock.assert_awaited_once_with(webhook_payload)
    update_mock.assert_awaited_once_with(webhook_payload)
    delete_mock.assert_awaited_once_with(webhook_payload)
    custom_mock.assert_awaited_once_with(custom_payload)


async def test_hook_generation():
    handlers = Handlers()

    create_mock = AsyncMock()
    update_mock = AsyncMock()
    delete_mock = AsyncMock()

    handlers.add_create_handler("foo", create_mock)
    handlers.add_update_handler("bar", update_mock)
    handlers.add_delete_handler("baz", delete_mock)

    handlers.add_create_handler("qux", create_mock)
    handlers.add_update_handler("qux", update_mock)
    handlers.add_delete_handler("qux", delete_mock)

    hooks = handlers.get_hooks()

    assert len([hook for hook in hooks if hook.name == "foo"]) == 1, (
        "Expected to find a hook for model 'foo'"
    )
    assert len([hook for hook in hooks if hook.name == "bar"]) == 1, (
        "Expected to find a hook for model 'bar'"
    )
    assert len([hook for hook in hooks if hook.name == "baz"]) == 1, (
        "Expected to find a hook for model 'baz'"
    )
    assert len([hook for hook in hooks if hook.name == "qux"]) == 1, (
        "Expected to find a hook for model 'qux'"
    )

    hook_foo = next(hook for hook in hooks if hook.name == "foo")
    hook_bar = next(hook for hook in hooks if hook.name == "bar")
    hook_baz = next(hook for hook in hooks if hook.name == "baz")
    hook_qux = next(hook for hook in hooks if hook.name == "qux")

    assert hook_foo.create, "Expected a create hook for model 'foo'"
    assert not hook_foo.update, "Expected no update hook for model 'foo'"
    assert not hook_foo.delete, "Expected no delete hook for model 'foo'"

    assert not hook_bar.create, "Expected no create hook for model 'bar'"
    assert hook_bar.update, "Expected an update hook for model 'bar'"
    assert not hook_bar.delete, "Expected no delete hook for model 'bar'"

    assert not hook_baz.create, "Expected no create hook for model 'baz'"
    assert not hook_baz.update, "Expected no update hook for model 'baz'"
    assert hook_baz.delete, "Expected a delete hook for model 'baz'"

    assert hook_qux.create, "Expected a create hook for model 'qux'"
    assert hook_qux.update, "Expected an update hook for model 'qux'"
    assert hook_qux.delete, "Expected a delete hook for model 'qux'"
