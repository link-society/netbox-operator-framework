import pytest

import re

from nopf.client import NetboxClient
from nopf.settings import Settings


pytestmark = pytest.mark.anyio


async def test_from_api(netbox_token: str):
    settings = Settings(
        netbox_api="http://localhost:8080",
        netbox_token=netbox_token,
        server_bind_host="0.0.0.0",
        server_bind_port=5000,
        server_callback_name="pytest",
        server_callback_url="http://host.docker.internal:5000",
    )

    client = NetboxClient(settings)

    assert client.title == "NetBox REST API"
    assert client.version.major == 4
    assert client.version.minor == 2
    assert client.version.patch == 6
    assert client.version.meta == "Docker-3.2.0"
    assert str(client.version) == "4.2.6-Docker-3.2.0 (4.2)"
    assert client.license == "Apache v2 License"


async def test_from_json_file(netbox_token: str):
    settings = Settings(
        netbox_api="http://localhost:8080",
        netbox_token=netbox_token,
        netbox_schema="./tests/netbox-v4.x/openapi.json",
        server_bind_host="0.0.0.0",
        server_bind_port=5000,
        server_callback_name="pytest",
        server_callback_url="http://host.docker.internal:5000",
    )

    client = NetboxClient(settings)

    assert client.title == "NetBox REST API"
    assert client.version.major == 4
    assert client.version.minor == 2
    assert client.version.patch == 6
    assert client.version.meta == "Docker-3.2.0"
    assert str(client.version) == "4.2.6-Docker-3.2.0 (4.2)"
    assert client.license == "Apache v2 License"


async def test_from_yaml_file(netbox_token: str):
    settings = Settings(
        netbox_api="http://localhost:8080",
        netbox_token=netbox_token,
        netbox_schema="./tests/netbox-v4.x/openapi.yml",
        server_bind_host="0.0.0.0",
        server_bind_port=5000,
        server_callback_name="pytest",
        server_callback_url="http://host.docker.internal:5000",
    )

    client = NetboxClient(settings)

    assert client.title == "NetBox REST API"
    assert client.version.major == 4
    assert client.version.minor == 2
    assert client.version.patch == 6
    assert client.version.meta == "Docker-3.2.0"
    assert str(client.version) == "4.2.6-Docker-3.2.0 (4.2)"
    assert client.license == "Apache v2 License"


async def test_unsupported_schema_file_format(netbox_token: str):
    settings = Settings(
        netbox_api="http://localhost:8080",
        netbox_token=netbox_token,
        netbox_schema="./tests/netbox-v4.x/openapi.txt",
        server_bind_host="0.0.0.0",
        server_bind_port=5000,
        server_callback_name="pytest",
        server_callback_url="http://host.docker.internal:5000",
    )

    with pytest.raises(
        ValueError,
        match=re.escape("Unsupported schema file format: .txt"),
    ):
        NetboxClient(settings)


async def test_unsupported_schema_url_scheme(netbox_token: str):
    settings = Settings(
        netbox_api="http://localhost:8080",
        netbox_token=netbox_token,
        netbox_schema="ftp://localhost:8080/openapi.json",
        server_bind_host="0.0.0.0",
        server_bind_port=5000,
        server_callback_name="pytest",
        server_callback_url="http://host.docker.internal:5000",
    )

    with pytest.raises(
        ValueError,
        match=re.escape("Unsupported schema URL scheme: ftp"),
    ):
        NetboxClient(settings)


def test_no_main_client():
    with pytest.raises(
        RuntimeError,
        match=re.escape("NetboxClient not set"),
    ):
        NetboxClient.main()


async def test_missing_parameters(settings: Settings):
    client = NetboxClient(settings)

    with pytest.raises(
        ValueError,
        match=re.escape("Operation(dcim_sites_retrieve): Missing parameter: id"),
    ):
        await client.operations.dcim_sites_retrieve()


async def test_invalid_parameters(settings: Settings):
    client = NetboxClient(settings)

    with pytest.raises(
        ValueError,
        match=re.escape("Operation(dcim_sites_retrieve): Invalid parameter: id"),
    ):
        await client.operations.dcim_sites_retrieve(
            params={
                "id": "str",
            }
        )


async def test_bad_request(settings: Settings):
    client = NetboxClient(settings)

    resp = await client.operations.dcim_sites_create(
        body={
            "name": "str",
            "slug": "str",
        }
    )
    resp.raise_for_status()
    obj_id = resp.json()["id"]

    try:
        resp = await client.operations.dcim_sites_create(
            body={
                "name": "str",
                "slug": "str",
            }
        )
        assert resp.is_error

    finally:
        await client.operations.dcim_sites_destroy(
            params={
                "id": obj_id,
            }
        )


async def test_query_params(settings: Settings):
    client = NetboxClient(settings)

    resp = await client.operations.dcim_sites_create(
        body={
            "name": "str",
            "slug": "str",
        }
    )
    resp.raise_for_status()
    obj_id = resp.json()["id"]

    try:
        resp = await client.operations.dcim_sites_list(
            params={
                "q": "str",
            }
        )
        resp.raise_for_status()
        result1 = resp.json()

        resp = await client.operations.dcim_sites_list(
            params={
                "name": ["str"],
            }
        )
        resp.raise_for_status()
        result2 = resp.json()

        assert result1 == result2

    finally:
        await client.operations.dcim_sites_destroy(
            params={
                "id": obj_id,
            }
        )
