import json

import httpx
import pytest

from conftest import body, run
from tools import wire_build
from tools.wire_build import WireBuildTool

OK = {"status": "ok", "build_request": {"id": "br_1", "status": "pending"}}
BASE_PARAMS = {"website_url": "https://example.com", "goal": "list products"}


@pytest.fixture
def api(mock_api):
    return mock_api(wire_build, lambda r: httpx.Response(202, json=OK))


def test_minimal_payload_unchanged(make_tool, api):
    out = run(make_tool(WireBuildTool), dict(BASE_PARAMS))
    assert out == [("json", OK)]
    assert body(api[0]) == {**BASE_PARAMS, "visibility": "private", "force": False}


@pytest.mark.parametrize(
    "raw, expected",
    [
        ('["search products", "get product details"]', ["search products", "get product details"]),
        ("search products\n  get product details \n\n", ["search products", "get product details"]),
        ("search products", ["search products"]),
        ('"search products"', ["search products"]),
    ],
)
def test_actions_forms(make_tool, api, raw, expected):
    run(make_tool(WireBuildTool), {**BASE_PARAMS, "actions": raw})
    assert body(api[0])["actions"] == expected


def test_actions_rejects_non_string_items(make_tool, api):
    out = run(make_tool(WireBuildTool), {**BASE_PARAMS, "actions": "[1, 2]"})
    assert out[0][0] == "text" and out[0][1].startswith("Error: Actions must be")
    assert api == []


def test_whitespace_only_actions_are_omitted(make_tool, api):
    run(make_tool(WireBuildTool), {**BASE_PARAMS, "actions": " \n "})
    assert "actions" not in body(api[0])


def test_country_passed_through(make_tool, api):
    run(make_tool(WireBuildTool), {**BASE_PARAMS, "country": " US "})
    assert body(api[0])["country"] == "US"


def test_plain_credential(make_tool, api):
    cred = {"type": "plain", "username": "u", "password": "p", "login_url": "https://example.com/login"}
    run(make_tool(WireBuildTool), {**BASE_PARAMS, "credential": json.dumps(cred)})
    assert body(api[0])["credential"] == cred


def test_vault_credential_drops_unknown_keys(make_tool, api):
    cred = {"type": "vault", "source_id": "s1", "source_ref": {"item_id": "i"}, "junk": 1}
    run(make_tool(WireBuildTool), {**BASE_PARAMS, "credential": json.dumps(cred)})
    assert body(api[0])["credential"] == {"type": "vault", "source_id": "s1", "source_ref": {"item_id": "i"}}


@pytest.mark.parametrize(
    "raw, fragment",
    [
        ("not json secret123", "must be valid JSON"),
        ('["a"]', "must be a JSON object"),
        ('{"type": "plain", "username": "u"}', '"plain" credential needs'),
        ('{"type": "vault", "source_id": "s"}', '"vault" credential needs'),
        ('{"type": "oauth"}', '"type" must be'),
    ],
)
def test_bad_credential_is_rejected_without_echoing_it(make_tool, api, raw, fragment):
    out = run(make_tool(WireBuildTool), {**BASE_PARAMS, "credential": raw})
    assert len(out) == 1 and out[0][0] == "text"
    assert fragment in out[0][1]
    assert "secret123" not in out[0][1]
    assert api == []
