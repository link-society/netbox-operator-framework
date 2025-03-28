"""
Settings can be injected via environment variables, or directly via code as
constructor parameters.
"""

from typing import Any

from secrets import token_hex
from urllib.parse import urljoin

from socket import gethostname

from decouple import config  # type: ignore
from pydantic import BaseModel, Field


def _get_default_callback_url(data: dict[str, Any]) -> str:
    hostname = gethostname()
    port = data["server_bind_port"]
    return f"http://{hostname}:{port}"


class Settings(BaseModel):
    """
    Operator settings.
    """

    secret_key: str = Field(
        default_factory=lambda: config(
            "NOPF_SECRET_KEY",
            default=token_hex(32),
        ),
    )
    """
    Secret key given to Netbox to sign webhook requests.

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NOPF_SECRET_KEY``
    * Randomly generated token
    """

    netbox_api: str = Field(
        default_factory=lambda: config(
            "NETBOX_API",
        ),
    )
    """
    URL to the Netbox instance.

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NETBOX_API``
    """

    netbox_token: str = Field(
        default_factory=lambda: config(
            "NETBOX_TOKEN",
        ),
    )
    """
    Token to authenticate against the Netbox API.

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NETBOX_TOKEN``
    """

    netbox_schema: str = Field(
        default_factory=lambda data: config(
            "NETBOX_SCHEMA",
            default=(
                urljoin(f"{data['netbox_api']}/", "./api/schema")
                if data.get("netbox_api")
                else ""
            ),
        ),
    )
    """
    URL to the Netbox API schema. Can be a local file path or a remote URL.
    When pointing to a local file, either JSON or YAML are supported. The format
    is determined by the file extension.

    .. note::

       Using JSON is recommended, as it is faster to parse.

    **Examples:**

    * ``http://localhost:8080/api/schema``
    * ``file:///path/to/schema.json``
    * ``./path/to/schema.json``
    * ``/path/to/schema.yml``

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NETBOX_SCHEMA``
    * Default: ``{netbox_api}/api/schema``
    """

    netbox_ssl_verify: bool = Field(
        default_factory=lambda: config(
            "NETBOX_SSL_VERIFY",
            cast=bool,
            default=True,
        ),
    )
    """
    Verify SSL certificates when connecting to the Netbox API.

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NETBOX_SSL_VERIFY``
    * Default: ``True``
    """

    server_bind_host: str = Field(
        default_factory=lambda: config(
            "NOPF_SERVER_BIND_HOST",
            default="0.0.0.0",
        ),
    )
    """
    Hostname or IP address to bind the HTTP server to.

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NOPF_SERVER_BIND_HOST``
    * Default: ``0.0.0.0``
    """

    server_bind_port: int = Field(
        default_factory=lambda: config(
            "NOPF_SERVER_BIND_PORT",
            cast=int,
            default=5000,
        ),
    )
    """
    Port to bind the HTTP server to.

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NOPF_SERVER_BIND_PORT``
    * Default: ``5000``
    """

    server_callback_name: str = Field(
        default_factory=lambda: config(
            "NOPF_SERVER_CALLBACK_NAME",
        )
    )
    """
    Name of the callback in Netbox. The Netbox Operator Framework will use this
    value to name the webhooks in Netbox.

    .. warning::

       Make sure the name does not clash with another operator. If any callback
       with the same name exist, they will be overwritten.

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NOPF_SERVER_CALLBACK_NAME``
    """

    server_callback_url: str = Field(
        default_factory=lambda data: config(
            "NOPF_SERVER_CALLBACK_URL",
            default=_get_default_callback_url(data),
        ),
    )
    """
    URL where Netbox will send the webhook requests. If not set, the Netbox
    Operator Framework will use the hostname of the machine and port of the
    server.

    This is the URL as seen by Netbox, so make sure it is reachable by it. If
    there are any Reverse Proxy in between, this must be the URL exposed by said
    Reverse Proxy.

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NOPF_SERVER_CALLBACK_URL``
    * Default: ``http://{gethostname()}:{server_bind_port}``
    """

    server_callback_ssl_verify: bool = Field(
        default_factory=lambda: config(
            "NOPF_SERVER_CALLBACK_SSL_VERIFY",
            cast=bool,
            default=True,
        ),
    )
    """
    Tell Netbox to verify SSL certificates when connecting to the callback URL.

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NOPF_SERVER_CALLBACK_SSL_VERIFY``
    * Default: ``True``
    """

    log_level: str = Field(
        default_factory=lambda: config(
            "NOPF_LOG_LEVEL",
            default="INFO",
        ),
    )
    """
    Logging level for the Netbox Operator Framework.

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NOPF_LOG_LEVEL``
    * Default: ``INFO``
    """

    log_appname: str = Field(
        default_factory=lambda: config(
            "NOPF_LOG_APPNAME",
            default="nopf",
        ),
    )
    """
    Application name to use in the logs.

    **Resolution order:**

    * Constructor parameter
    * Environment variable ``NOPF_LOG_APPNAME``
    * Default: ``nopf``
    """
