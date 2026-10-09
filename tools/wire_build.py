import json
from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"


def _parse_actions(raw: Any) -> list[str] | None:
    """Accept a JSON array of strings, or plain text with one capability per line."""
    if isinstance(raw, list):
        items = raw
    else:
        text = str(raw).strip()
        try:
            items = json.loads(text)
        except json.JSONDecodeError:
            items = text.splitlines()
        if isinstance(items, str):
            items = [items]
    if not isinstance(items, list) or not all(isinstance(a, str) for a in items):
        return None
    return [a.strip() for a in items if a.strip()]


def _parse_credential(raw: Any) -> tuple[dict | None, str | None]:
    """Parse and shape-check a plain or vault login credential.

    Returns (credential, error). Error messages never include the credential's
    contents, since it carries a password.
    """
    if isinstance(raw, dict):
        cred = raw
    else:
        try:
            cred = json.loads(str(raw))
        except json.JSONDecodeError:
            return None, "Error: Login credential must be valid JSON"
    if not isinstance(cred, dict):
        return None, "Error: Login credential must be a JSON object"

    cred_type = cred.get("type")
    if cred_type == "plain":
        if not isinstance(cred.get("username"), str) or not isinstance(cred.get("password"), str):
            return None, 'Error: A "plain" credential needs both "username" and "password" (strings)'
    elif cred_type == "vault":
        if not isinstance(cred.get("source_id"), str) or not isinstance(cred.get("source_ref"), dict):
            return None, 'Error: A "vault" credential needs "source_id" (string) and "source_ref" (object)'
    else:
        return None, 'Error: Login credential "type" must be "plain" or "vault"'

    allowed = {"type", "username", "password", "source_id", "source_ref", "login_url"}
    return {k: v for k, v in cred.items() if k in allowed}, None


class WireBuildTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key")

        website_url = tool_parameters.get("website_url")
        if not website_url:
            yield self.create_text_message("Error: Website URL is required")
            return

        goal = tool_parameters.get("goal")
        if not goal:
            yield self.create_text_message("Error: Goal is required")
            return

        catalog_id = tool_parameters.get("catalog_id")
        visibility = tool_parameters.get("visibility", "private")
        force = tool_parameters.get("force", False)

        payload = {
            "website_url": website_url,
            "goal": goal,
            "visibility": visibility,
            "force": force
        }
        if catalog_id:
            payload["catalog_id"] = catalog_id

        raw_actions = tool_parameters.get("actions")
        if raw_actions:
            actions = _parse_actions(raw_actions)
            if actions is None:
                yield self.create_text_message(
                    'Error: Actions must be a JSON array of strings (e.g. ["search products", "get product details"]) or one capability per line'
                )
                return
            if actions:
                payload["actions"] = actions

        country = (tool_parameters.get("country") or "").strip()
        if country:
            payload["country"] = country

        raw_credential = tool_parameters.get("credential")
        if raw_credential:
            credential, error = _parse_credential(raw_credential)
            if error:
                yield self.create_text_message(error)
                return
            payload["credential"] = credential

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{BASE_URL}/wire/build-request",
                    headers={
                        "X-API-Key": api_key,
                        "Content-Type": "application/json",
                        "X-Source": "dify"
                    },
                    json=payload
                )

                if response.status_code == 401:
                    yield self.create_text_message("Error: Invalid API Key")
                    return
                elif response.status_code == 402:
                    yield self.create_text_message("Error: Plan upgrade required")
                    return
                elif response.status_code not in [200, 202]:
                    yield self.create_text_message(f"Error: {response.text}")
                    return

                result = response.json()
                yield self.create_json_message(result)

        except httpx.TimeoutException:
            yield self.create_text_message("Error: Request timeout")
        except httpx.RequestError as e:
            yield self.create_text_message(f"Error: {str(e)}")
