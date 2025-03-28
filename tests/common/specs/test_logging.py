from anycorn.typing import WWWScope, ResponseSummary

from unittest.mock import MagicMock
import pytest

from datetime import datetime
import sys

from anycorn import Config
import logbook

from nopf.logging import LogHandler, WebLogger
from nopf.settings import Settings


pytestmark = pytest.mark.anyio


async def test_weblogger_message():
    config = Config()
    weblogger = WebLogger(config)
    weblogger.logger = MagicMock()

    await weblogger.critical("test")
    await weblogger.error("test")
    await weblogger.warning("test")
    await weblogger.info("test")
    await weblogger.debug("test")
    await weblogger.exception("test")

    weblogger.logger.critical.assert_called_once()
    weblogger.logger.error.assert_called_once()
    weblogger.logger.warning.assert_called_once()
    weblogger.logger.info.assert_called_once()
    weblogger.logger.debug.assert_called_once()
    weblogger.logger.exception.assert_called_once()


async def test_weblogger_access_no_response():
    config = Config()
    weblogger = WebLogger(config)
    weblogger.logger = MagicMock()

    request: WWWScope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "query_string": b"",
        "headers": [],
    }

    response: ResponseSummary = None

    await weblogger.access(request, response, 0.0)
    weblogger.logger.info.assert_not_called()


async def test_weblogger_access_no_client():
    config = Config()
    weblogger = WebLogger(config)
    weblogger.logger = MagicMock()

    request: WWWScope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "query_string": b"",
        "headers": [],
    }

    response: ResponseSummary = {
        "status": 200,
    }

    await weblogger.access(request, response, 0.0)
    weblogger.logger.info.assert_called_once_with(
        "HTTP Request",
        extra={
            "scope": "api",
            "remote_addr": None,
            "protocol": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "query_string": "",
            "status_code": "200",
            "status_phrase": "OK",
            "content_length": "-",
            "referer": "-",
            "user_agent": "-",
        },
    )


async def test_weblogger_access_with_client_host_port():
    config = Config()
    weblogger = WebLogger(config)
    weblogger.logger = MagicMock()

    request: WWWScope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "client": ("1.2.3.4", 5678),
    }

    response: ResponseSummary = {
        "status": 200,
    }

    await weblogger.access(request, response, 0.0)
    weblogger.logger.info.assert_called_once_with(
        "HTTP Request",
        extra={
            "scope": "api",
            "remote_addr": "1.2.3.4:5678",
            "protocol": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "query_string": "",
            "status_code": "200",
            "status_phrase": "OK",
            "content_length": "-",
            "referer": "-",
            "user_agent": "-",
        },
    )


async def test_weblogger_access_with_client_addr():
    config = Config()
    weblogger = WebLogger(config)
    weblogger.logger = MagicMock()

    request: WWWScope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "client": ("1.2.3.4",),
    }

    response: ResponseSummary = {
        "status": 200,
    }

    await weblogger.access(request, response, 0.0)
    weblogger.logger.info.assert_called_once_with(
        "HTTP Request",
        extra={
            "scope": "api",
            "remote_addr": "1.2.3.4",
            "protocol": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "query_string": "",
            "status_code": "200",
            "status_phrase": "OK",
            "content_length": "-",
            "referer": "-",
            "user_agent": "-",
        },
    )


async def test_weblogger_access_with_client_unknown():
    config = Config()
    weblogger = WebLogger(config)
    weblogger.logger = MagicMock()

    request: WWWScope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "client": "foo",
    }

    response: ResponseSummary = {
        "status": 200,
    }

    await weblogger.access(request, response, 0.0)
    weblogger.logger.info.assert_called_once_with(
        "HTTP Request",
        extra={
            "scope": "api",
            "remote_addr": "<???foo???>",
            "protocol": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "query_string": "",
            "status_code": "200",
            "status_phrase": "OK",
            "content_length": "-",
            "referer": "-",
            "user_agent": "-",
        },
    )


async def test_weblogger_access_with_non_http():
    config = Config()
    weblogger = WebLogger(config)
    weblogger.logger = MagicMock()

    request: WWWScope = {
        "type": "foo",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "query_string": b"",
        "headers": [],
    }

    response: ResponseSummary = {
        "status": 200,
    }

    await weblogger.access(request, response, 0.0)
    weblogger.logger.info.assert_called_once_with(
        "HTTP Request",
        extra={
            "scope": "api",
            "remote_addr": None,
            "protocol": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "query_string": "",
            "status_code": "200",
            "status_phrase": "OK",
            "content_length": "-",
            "referer": "-",
            "user_agent": "-",
        },
    )


async def test_weblogger_access_with_method():
    config = Config()
    weblogger = WebLogger(config)
    weblogger.logger = MagicMock()

    request: WWWScope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/",
        "query_string": b"",
        "headers": [],
    }

    response: ResponseSummary = {
        "status": 200,
    }

    await weblogger.access(request, response, 0.0)
    weblogger.logger.info.assert_called_once_with(
        "HTTP Request",
        extra={
            "scope": "api",
            "remote_addr": None,
            "protocol": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/",
            "query_string": "",
            "status_code": "200",
            "status_phrase": "OK",
            "content_length": "-",
            "referer": "-",
            "user_agent": "-",
        },
    )


async def test_weblogger_access_with_unknown_status():
    config = Config()
    weblogger = WebLogger(config)
    weblogger.logger = MagicMock()

    request: WWWScope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "query_string": b"",
        "headers": [],
    }

    response: ResponseSummary = {
        "status": 0,
    }

    await weblogger.access(request, response, 0.0)
    weblogger.logger.info.assert_called_once_with(
        "HTTP Request",
        extra={
            "scope": "api",
            "remote_addr": None,
            "protocol": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "query_string": "",
            "status_code": "0",
            "status_phrase": "<???0???>",
            "content_length": "-",
            "referer": "-",
            "user_agent": "-",
        },
    )


async def test_weblogger_formatting():
    config = Config()
    weblogger = WebLogger(config)
    weblogger.logger = MagicMock()

    await weblogger.info("test %s %(x)s", "foo", x="bar")
    weblogger.logger.info.assert_called_once_with("test {0} {x}", "foo", x="bar")


def test_formatter():
    settings = Settings(
        secret_key="s3cr3!",
        netbox_api="http://netbox.local/",
        netbox_token="t0k3n",
        server_bind_host="127.0.0.1",
        server_bind_port=0,
        server_callback_name="test",
        log_appname="test",
    )

    handler = LogHandler(settings)

    now = datetime.now()
    record = logbook.LogRecord(
        channel="pytest",
        level=logbook.INFO,
        msg="test",
        extra={"foo": "bar"},
    )
    record.time = now

    result = handler.formatter(record, handler)
    assert (
        result
        == f'app="test" channel="pytest" time="{now}" level="INFO" message="test" foo="bar"'
    )

    try:
        raise RuntimeError("test")

    except RuntimeError:
        exc_info = sys.exc_info()
        record = logbook.LogRecord(
            channel="pytest",
            level=logbook.ERROR,
            msg="test",
            extra={"foo": "bar"},
            exc_info=exc_info,
        )
        record.time = now

        result = handler.formatter(record, handler)
        assert (
            result
            == f'app="test" channel="pytest" time="{now}" level="ERROR" message="test" foo="bar" exc.type="RuntimeError" exc.message="test"'
        )
