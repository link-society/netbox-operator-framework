"""
Dependency providers for FastAPI routes.
"""

from typing import cast

from fastapi import Request

from nopf.settings import Settings
from nopf.core.channel import ChannelSender


def get_settings(request: Request) -> Settings:
    """
    Access the operator settings from the FastAPI request object.

    :param request: The FastAPI request object.
    :return: The operator settings.
    """

    return cast(Settings, request.app.state.settings)


def get_channel(request: Request) -> ChannelSender:
    """
    Access the operator internal channel from the FastAPI request object.

    :param request: The FastAPI request object.
    :return: The operator internal channel
    """

    return cast(ChannelSender, request.app.state.channel)
