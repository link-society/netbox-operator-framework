"""
The Netbox HTTP Client is generated dynamically from the OpenAPI schema.

.. note::

   It supports fetching the schema directly from the Netbox, which can be slow,
   but also from a JSON file, or a YAML file.

   Using a JSON file is recommended as it is the fastest option.
"""

from contextvars import ContextVar
from urllib.parse import urlparse
from pathlib import Path

import yaml
import json
import re

from logbook import Logger  # type: ignore

from httpx import Client, AsyncClient, Request, Response
from openapi_spec_validator import validate, OpenAPIV30SpecValidator

from nopf.settings import Settings

from .operation import Operation


_client: ContextVar["NetboxClient | None"] = ContextVar(
    "nof_netbox_client",
    default=None,
)


class NetboxClient:
    """
    Dynamically generated Netbox HTTP client.
    """

    @staticmethod
    def main() -> "NetboxClient":
        """
        Get the operator's Netbox HTTP client.

        :return: The operator's Netbox HTTP client.
        :raises RuntimeError: If this function is called outside the context of an operator (and therefore, the client is not set).
        """

        value = _client.get()
        if value is None:
            raise RuntimeError("NetboxClient not set")

        return value

    def __init__(self, settings: Settings) -> None:
        """
        :param settings: The operator settings.
        """

        self._logger = Logger("nopf.client")

        client = AsyncClient(
            base_url=settings.netbox_api,
            verify=settings.netbox_ssl_verify,
            follow_redirects=True,
            headers={
                "Authorization": f"Token {settings.netbox_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            event_hooks={
                "request": [self._log_request],
                "response": [Response.aread, self._log_response],
            },
        )

        netbox_schema_url = urlparse(settings.netbox_schema)

        match netbox_schema_url.scheme:
            case "http" | "https":
                with Client(follow_redirects=True, timeout=10) as sync_client:
                    resp = sync_client.get(
                        settings.netbox_schema,
                        headers={"Accept": "application/json"},
                    )
                    resp.raise_for_status()
                    self._schema = resp.json()

            case "" | "file":
                netbox_schema_path = Path(netbox_schema_url.path)
                ext = netbox_schema_path.suffix.lower()

                match ext:
                    case ".json":
                        with open(netbox_schema_path) as file:
                            self._schema = json.load(file)

                    case ".yml" | ".yaml":
                        with open(netbox_schema_path) as file:
                            self._schema = yaml.safe_load(file)

                    case _:
                        raise ValueError(f"Unsupported schema file format: {ext}")

            case _:
                raise ValueError(
                    f"Unsupported schema URL scheme: {netbox_schema_url.scheme}"
                )

        validate(self._schema, cls=OpenAPIV30SpecValidator)

        operations: dict[str, Operation] = {}

        for path, path_spec in self._schema["paths"].items():
            for method, operation_spec in path_spec.items():
                operation_id = operation_spec["operationId"]
                operations[operation_id] = Operation(
                    client,
                    method,
                    path,
                    operation_spec,
                    self._schema,
                )

        self._operations = Operations(operations)
        self._version = Version(self._schema["info"]["version"])

    @property
    def title(self) -> str:
        """
        Title of the OpenAPI schema. This is equivalent to the ``#/info/title``
        field.
        """

        return self._schema["info"]["title"]

    @property
    def version(self) -> "Version":
        """
        Version of the OpenAPI schema. This is equivalent to the
        ``#/info/version``. This correspond to the Netbox version.
        """

        return self._version

    @property
    def license(self) -> str:
        """
        License of the OpenAPI schema. This is equivalent to the
        ``#/info/license/name`` field.
        """

        return self._schema["info"]["license"]["name"]

    @property
    def operations(self) -> "Operations":
        """
        Operations available in the OpenAPI schema.
        """

        return self._operations

    async def _log_request(self, request: Request) -> None:
        self._logger.info(
            "netbox request",
            extra={
                "request.method": request.method,
                "request.url": request.url,
            },
        )

    async def _log_response(self, response: Response) -> None:
        extra = {
            "request.method": response.request.method,
            "request.url": response.request.url,
            "response.status_code": response.status_code,
            "response.reason_phrase": response.reason_phrase,
        }

        if response.is_error:
            log = self._logger.error
            extra["response.body"] = response.text

        else:
            log = self._logger.info

        log("netbox response", extra=extra)


class Version:
    """
    Netbox API version parser.

    .. note::

       Netbox API Version is in the format ``Major.Minor.Patch (Major.Minor)``
       or ``Major.Minor.Patch-Meta (Major.Minor)``.
    """

    _pattern = re.compile(r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<meta>.+?))? \((\d+)\.(\d+)\)")

    def __init__(self, version: str):
        """
        :param version: Version string as it appears in the ``#/info/version`` field.
        """

        self._version = version

        match = self._pattern.match(version)
        if match is None:
            raise ValueError(f"Invalid version: {version}")

        self._major = int(match.group("major"))
        self._minor = int(match.group("minor"))
        self._patch = int(match.group("patch"))
        self._meta = match.group("meta") or ""

    @property
    def major(self) -> int:
        """
        Major version number.
        """

        return self._major

    @property
    def minor(self) -> int:
        """
        Minor version number.
        """

        return self._minor

    @property
    def patch(self) -> int:
        """
        Patch version number.
        """

        return self._patch

    @property
    def meta(self) -> str:
        """
        Version metadata.
        """

        return self._meta

    def __str__(self) -> str:
        return self._version


class Operations:
    """
    Operations container implementing dynamic lookup via ``__getattr__``.
    """

    def __init__(self, operations: dict[str, Operation]):
        self._operations = operations

    def __getattr__(self, operation_id: str) -> Operation:
        """
        Lookup an operation by its ID.

        :param operation_id: Operation ID.
        :return: The operation callable.
        """

        return self._operations[operation_id]
