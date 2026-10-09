import httpx

from conftest import run
from tools import wire_build_status
from tools.wire_build_status import WireBuildStatusTool

BASE = "https://api.anakin.io/v1/wire/build-requests"


def test_detail_mode_drops_events_by_default(make_tool, mock_api):
    reqs = mock_api(
        wire_build_status,
        lambda r: httpx.Response(200, json={"id": "br_1", "status": "success", "events": [1, 2]}),
    )
    out = run(make_tool(WireBuildStatusTool), {"id": " br_1 "})
    assert out == [("json", {"id": "br_1", "status": "success"})]
    assert str(reqs[0].url) == f"{BASE}/br_1"
    assert reqs[0].headers["X-API-Key"] == "ask_test"
    assert reqs[0].headers["X-Source"] == "dify"


def test_detail_mode_keeps_events_when_asked(make_tool, mock_api):
    mock_api(wire_build_status, lambda r: httpx.Response(200, json={"id": "br_1", "events": [1]}))
    out = run(make_tool(WireBuildStatusTool), {"id": "br_1", "include_events": True})
    assert out == [("json", {"id": "br_1", "events": [1]})]


def test_detail_mode_encodes_id_as_one_path_segment(make_tool, mock_api):
    reqs = mock_api(wire_build_status, lambda r: httpx.Response(200, json={}))
    run(make_tool(WireBuildStatusTool), {"id": "../x/y"})
    assert reqs[0].url.raw_path == b"/v1/wire/build-requests/..%2Fx%2Fy"


def test_detail_mode_404(make_tool, mock_api):
    mock_api(wire_build_status, lambda r: httpx.Response(404, json={"error": "not found"}))
    out = run(make_tool(WireBuildStatusTool), {"id": "nope"})
    assert out == [("text", "Error: No build request found with id nope")]


def test_blank_id_lists_with_default_limit(make_tool, mock_api):
    reqs = mock_api(wire_build_status, lambda r: httpx.Response(200, json={"items": []}))
    out = run(make_tool(WireBuildStatusTool), {"id": "  "})
    assert out == [("json", {"items": []})]
    assert reqs[0].url.path == "/v1/wire/build-requests"
    assert dict(reqs[0].url.params) == {"limit": "10", "page": "1"}


def test_list_mode_forwards_filters_and_clamps_limit(make_tool, mock_api):
    reqs = mock_api(wire_build_status, lambda r: httpx.Response(200, json={"items": []}))
    run(make_tool(WireBuildStatusTool), {"status": "failed", "limit": 500.0, "page": 3.0})
    assert dict(reqs[0].url.params) == {"limit": "100", "page": "3", "status": "failed"}


def test_list_mode_ignores_invalid_numbers(make_tool, mock_api):
    reqs = mock_api(wire_build_status, lambda r: httpx.Response(200, json={}))
    run(make_tool(WireBuildStatusTool), {"limit": 0, "page": "abc"})
    assert dict(reqs[0].url.params) == {"limit": "10", "page": "1"}


def test_auth_and_plan_errors(make_tool, mock_api):
    mock_api(wire_build_status, lambda r: httpx.Response(401))
    assert run(make_tool(WireBuildStatusTool), {}) == [("text", "Error: Invalid API Key")]


def test_timeout(make_tool, mock_api):
    def boom(r):
        raise httpx.ReadTimeout("slow", request=r)

    mock_api(wire_build_status, boom)
    assert run(make_tool(WireBuildStatusTool), {}) == [("text", "Error: Request timeout")]
