import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from dify_plugin.entities.tool import ToolInvokeMessage, ToolRuntime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def make_tool():
    def _make(tool_cls):
        runtime = ToolRuntime(credentials={"api_key": "ask_test"}, user_id=None, session_id=None)
        return tool_cls(runtime=runtime, session=MagicMock())

    return _make


@pytest.fixture
def mock_api(monkeypatch):
    """Route every httpx.Client the tool opens through a recording mock transport."""

    def _install(module, handler):
        requests: list[httpx.Request] = []

        def record(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return handler(request)

        real_client = httpx.Client
        monkeypatch.setattr(
            module.httpx,
            "Client",
            lambda **kw: real_client(transport=httpx.MockTransport(record), **kw),
        )
        return requests

    return _install


def run(tool, params):
    """Invoke a tool and return its messages as (kind, payload) tuples."""
    out = []
    for msg in tool._invoke(params):
        if msg.type == ToolInvokeMessage.MessageType.JSON:
            out.append(("json", msg.message.json_object))
        else:
            out.append(("text", msg.message.text))
    return out


def body(request: httpx.Request) -> dict:
    return json.loads(request.content)
