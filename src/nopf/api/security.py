"""
Netbox will use the secret key to sign the Webhook request body with
the HMAC-SHA512 algorithm, and include the signature in the ``X-Hook-Signature``
HTTP header.
"""

from typing import Annotated

from fastapi import HTTPException, Request, Depends

import hashlib
import hmac

from nopf.settings import Settings

from .deps import get_settings


async def verify_netbox_request_signature(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """
    Verify the Netbox Webhook request signature.

    :param request: The FastAPI request object.
    :param settings: The operator settings.
    :raises HTTPException: If the signature is invalid, or missing, a ``403 Forbidden`` HTTP response is returned.
    """

    content = await request.body()
    digest = hmac.new(
        key=settings.secret_key.encode(),
        msg=content,
        digestmod=hashlib.sha512,
    ).hexdigest()

    signature = request.headers.get("X-Hook-Signature")
    if signature != digest:
        raise HTTPException(status_code=403, detail="Invalid signature")
