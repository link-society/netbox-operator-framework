import pytest

from threading import Event
from anyio import to_thread

from httpx import Client as HttpClient

from nopf.operator import Operator
from nopf.settings import Settings
from nopf.schema import WebhookPayload

from .utils import run_operator

pytestmark = pytest.mark.anyio


async def test_callbacks(settings: Settings, netbox_client: HttpClient):
    op = Operator(settings)

    create_site_event = Event()
    update_site_event = Event()
    delete_site_event = Event()

    create_region_event = Event()
    update_region_event = Event()
    delete_region_event = Event()

    @op.on_create("dcim.site")
    async def on_create_site(payload: WebhookPayload):
        create_site_event.set()

    @op.on_update("dcim.site")
    async def on_update_site(payload: WebhookPayload):
        update_site_event.set()

    @op.on_delete("dcim.site")
    async def on_delete_site(payload: WebhookPayload):
        delete_site_event.set()

    @op.on_create("dcim.region")
    async def on_create_region(payload: WebhookPayload):
        create_region_event.set()

    @op.on_update("dcim.region")
    async def on_update_region(payload: WebhookPayload):
        update_region_event.set()

    @op.on_delete("dcim.region")
    async def on_delete_region(payload: WebhookPayload):
        delete_region_event.set()

    async with run_operator(op):
        # Site
        resp = await netbox_client.post(
            "/api/dcim/sites/",
            json={"name": "Test Site", "slug": "test-site", "status": "planned"},
        )
        resp.raise_for_status()
        obj_id = resp.json()["id"]
        assert await to_thread.run_sync(create_site_event.wait, 5.0), (
            "Create site event not received"
        )

        resp = await netbox_client.patch(
            f"/api/dcim/sites/{obj_id}/",
            json={"status": "active"},
        )
        resp.raise_for_status()
        assert await to_thread.run_sync(update_site_event.wait, 5.0), (
            "Update site event not received"
        )

        resp = await netbox_client.delete(f"/api/dcim/sites/{obj_id}/")
        resp.raise_for_status()
        assert await to_thread.run_sync(delete_site_event.wait, 5.0), (
            "Delete site event not received"
        )

        # Region
        resp = await netbox_client.post(
            "/api/dcim/regions/",
            json={"name": "Test Region", "slug": "test-region"},
        )
        resp.raise_for_status()
        obj_id = resp.json()["id"]
        assert await to_thread.run_sync(create_region_event.wait, 5.0), (
            "Create region event not received"
        )

        resp = await netbox_client.patch(
            f"/api/dcim/regions/{obj_id}/",
            json={"description": "foobar"},
        )
        resp.raise_for_status()
        assert await to_thread.run_sync(update_region_event.wait, 5.0), (
            "Update region event not received"
        )

        resp = await netbox_client.delete(f"/api/dcim/regions/{obj_id}/")
        resp.raise_for_status()
        assert await to_thread.run_sync(delete_region_event.wait, 5.0), (
            "Delete region event not received"
        )
