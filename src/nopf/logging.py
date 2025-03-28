"""
The Netbox Operator Framework builds upon the logging library
`Logbook <https://logbook.readthedocs.io/>`_ with a
`logfmt <https://betterstack.com/community/guides/logging/logfmt/>`_ formatter.
"""

from typing import cast, Any, Callable
from anycorn.typing import WWWScope, HTTPScope, ResponseSummary

from http import HTTPStatus
import traceback
import sys
import re

from logbook import Logger, LogRecord, Handler, StreamHandler  # type: ignore
import logfmt  # type: ignore

from anycorn.logging import Logger as BaseWebLogger
from anycorn import Config

from nopf.settings import Settings


type FormatterCallback = Callable[[LogRecord, Handler], str]


def make_formatter(settings: Settings) -> FormatterCallback:
    """
    Create a logfmt formatter for Logbook.

    :param settings: The operator settings (for loglevel and appname).
    :return: A formatter callback.
    """

    def _formatter(record: LogRecord, _handler: Handler) -> str:
        logentry = {
            "app": settings.log_appname,
            "channel": record.channel,
            "time": record.time,
            "level": record.level_name,
            "message": record.message,
        }
        logentry.update(record.extra)

        if record.exc_info:
            exc_type, exc, tb = record.exc_info
            logentry["exc.type"] = exc_type.__name__
            logentry["exc.message"] = str(exc)
            traceback.print_exception(exc_type, exc, tb, file=sys.stderr)

        return logfmt.format_line(logentry)

    return _formatter


class LogHandler(StreamHandler):
    """
    Logging handler that streams log messages to ``stdout``, using the logfmt
    formatter.
    """

    def __init__(self, settings: Settings):
        """
        :param settings: The operator settings (for loglevel and appname).
        """

        super().__init__(sys.stdout, level=settings.log_level)
        self.formatter = make_formatter(settings)


class WebLogger(BaseWebLogger):
    """
    Custom logger for the Anycorn web server.
    """

    def __init__(self, config: Config):
        super().__init__(config)
        self.logger = Logger("nopf.api")

    async def access(
        self,
        request: WWWScope,
        response: ResponseSummary,
        _request_time: float,
    ) -> None:
        """
        Log an HTTP request.
        """

        if response is None:
            return

        protocol = request.get("http_version", "ws")
        client = request.get("client")

        match client:
            case None:
                remote_addr = None

            case (host, port):
                remote_addr = f"{host}:{port}"

            case (addr,):
                remote_addr = addr

            case _:
                remote_addr = f"<???{client}???>"

        match request["type"]:
            case "http":
                method = cast(HTTPScope, request)["method"]

            case _:
                method = "GET"

        qs = request["query_string"].decode()

        status_code = "-"
        status_phrase = "-"

        request_headers = {
            name.decode("latin1").lower(): value.decode("latin1")
            for name, value in request.get("headers", [])
        }
        status_code = str(response["status"])
        try:
            status_phrase = HTTPStatus(response["status"]).phrase

        except ValueError:
            status_phrase = f"<???{status_code}???>"

        response_headers = {
            name.decode("latin1").lower(): value.decode("latin1")
            for name, value in response.get("headers", [])
        }

        extra = {
            "scope": "api",
            "remote_addr": remote_addr,
            "protocol": protocol,
            "method": method,
            "scheme": request["scheme"],
            "path": request["path"],
            "query_string": qs if qs else "",
            "status_code": status_code,
            "status_phrase": status_phrase,
            "content_length": response_headers.get("content-length", "-"),
            "referer": request_headers.get("referer", "-"),
            "user_agent": request_headers.get("user-agent", "-"),
        }

        self.logger.info("HTTP Request", extra=extra)

    async def critical(
        self,
        message: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Log a critical message.
        """

        fmt = _convert_string_template(message)
        self.logger.critical(fmt, *args, **kwargs)

    async def error(
        self,
        message: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Log an error message.
        """

        fmt = _convert_string_template(message)
        self.logger.error(fmt, *args, **kwargs)

    async def warning(
        self,
        message: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Log a warning message.
        """

        fmt = _convert_string_template(message)
        self.logger.warning(fmt, *args, **kwargs)

    async def info(
        self,
        message: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Log an informational message.
        """

        fmt = _convert_string_template(message)
        self.logger.info(fmt, *args, **kwargs)

    async def debug(
        self,
        message: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Log a debug message.
        """

        fmt = _convert_string_template(message)
        self.logger.debug(fmt, *args, **kwargs)

    async def exception(
        self,
        message: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Log an exception.
        """

        exc_info = kwargs.pop("exc_info", None)
        fmt = _convert_string_template(message)
        self.logger.exception(fmt, *args, **kwargs, exc_info=exc_info)


def _convert_string_template(string):
    index = -1

    def repl(matched):
        nonlocal index
        keyword = matched.group(1)

        if keyword:
            return "{%s}" % keyword.strip("()")

        else:
            index += 1
            return "{%d}" % index

    return re.sub(r"(?:%(\(\w+\))?[diouxXeEfFgGcrs])", repl, string)
