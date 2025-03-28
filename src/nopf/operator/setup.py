from urllib.parse import urljoin

from nopf.settings import Settings
from nopf.client import NetboxClient

from nopf.core.handlers import Handlers


async def create_webhooks(settings: Settings, handlers: Handlers) -> None:
    client = NetboxClient.main()

    if (client.version.major, client.version.minor) <= (3, 6):
        await create_webhooks_legacy(client, settings, handlers)

    else:
        await create_webhooks_with_eventrules(client, settings, handlers)


async def create_webhooks_legacy(
    client: NetboxClient,
    settings: Settings,
    handlers: Handlers,
) -> None:
    model_hooks = handlers.get_hooks()

    for model_hook in model_hooks:
        webhook_name = f"nopf_webhook_{settings.server_callback_name}:{model_hook.name}"
        webhook_url = urljoin(
            f"{settings.server_callback_url}/",
            f"./callback/{model_hook.name}",
        )

        resp = await client.operations.extras_webhooks_list(
            params={
                "name": [webhook_name],
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if data["count"] > 0:
            resp = await client.operations.extras_webhooks_bulk_destroy(
                body=data["results"],
            )
            resp.raise_for_status()

        resp = await client.operations.extras_webhooks_create(
            body={
                "name": webhook_name,
                "content_types": [model_hook.name],
                "enabled": True,
                "type_create": model_hook.create,
                "type_update": model_hook.update,
                "type_delete": model_hook.delete,
                "payload_url": webhook_url,
                "http_method": "POST",
                "http_content_type": "application/json",
                "secret": settings.secret_key,
                "ssl_verification": settings.server_callback_ssl_verify,
            },
        )
        resp.raise_for_status()


async def create_webhooks_with_eventrules(
    client: NetboxClient,
    settings: Settings,
    handlers: Handlers,
) -> None:
    model_hooks = handlers.get_hooks()

    for model_hook in model_hooks:
        webhook_name = f"nopf_webhook_{settings.server_callback_name}:{model_hook.name}"
        webhook_url = urljoin(
            f"{settings.server_callback_url}/",
            f"./callback/{model_hook.name}",
        )

        event_types = []

        if model_hook.create:
            event_types.append("object_created")

        if model_hook.update:
            event_types.append("object_updated")

        if model_hook.delete:
            event_types.append("object_deleted")

        resp = await client.operations.extras_event_rules_list(
            params={
                "name": [webhook_name],
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if data["count"] > 0:
            resp = await client.operations.extras_event_rules_bulk_destroy(
                body=data["results"],
            )
            resp.raise_for_status()

        resp = await client.operations.extras_webhooks_list(
            params={
                "name": [webhook_name],
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if data["count"] > 0:
            resp = await client.operations.extras_webhooks_bulk_destroy(
                body=data["results"]
            )
            resp.raise_for_status()

        resp = await client.operations.extras_webhooks_create(
            body={
                "name": webhook_name,
                "payload_url": webhook_url,
                "http_method": "POST",
                "http_content_type": "application/json",
                "secret": settings.secret_key,
                "ssl_verification": settings.server_callback_ssl_verify,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        resp = await client.operations.extras_event_rules_create(
            body={
                "name": webhook_name,
                "event_types": event_types,
                "action_object_id": data["id"],
                "action_object_type": "extras.webhook",
            },
        )
        resp.raise_for_status()
