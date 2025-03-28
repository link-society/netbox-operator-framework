"""
`Pydantic <https://docs.pydantic.dev/>`_ models to validate webhook payloads
sent by Netbox.
"""

from typing import Any

from pydantic import BaseModel


type NetboxRecord = dict[str, Any]


class WebhookPayloadSnapshots(BaseModel):
    prechange: NetboxRecord | None
    postchange: NetboxRecord | None


class WebhookPayload(BaseModel):
    """
    See `Netbox Webhooks <https://netboxlabs.com/docs/netbox/en/stable/integrations/webhooks/#default-request-body>`_
    for more information.
    """

    event: str
    timestamp: str
    model: str
    username: str
    request_id: str
    data: NetboxRecord
    snapshots: WebhookPayloadSnapshots
