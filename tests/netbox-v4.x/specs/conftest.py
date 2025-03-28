import pytest

from httpx import AsyncClient as HttpClient

from nopf.settings import Settings


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def netbox_token(netbox):
    async with HttpClient(base_url="http://localhost:8080") as client:
        resp = await client.post(
            "/api/users/tokens/provision/",
            json={"username": "admin", "password": "admin"},
        )
        resp.raise_for_status()
        token = resp.json()["key"]

        yield token


@pytest.fixture(scope="function")
async def netbox_client(netbox_token: str):
    async with HttpClient(
        base_url="http://localhost:8080",
        headers={"Authorization": f"Token {netbox_token}"},
    ) as client:
        yield client


@pytest.fixture(scope="function")
async def settings(netbox_token: str):
    yield Settings(
        netbox_api="http://localhost:8080",
        netbox_token=netbox_token,
        netbox_schema="./tests/netbox-v4.x/openapi.json",
        server_bind_host="0.0.0.0",
        server_bind_port=5000,
        server_callback_name="pytest",
        server_callback_url="http://host.docker.internal:5000",
    )
