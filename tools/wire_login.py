import json
from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"


class WireLoginTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key")

        catalog_slug = tool_parameters.get("catalog_slug")
        if not catalog_slug:
            yield self.create_text_message("Error: Catalog slug is required")
            return

        # Parse optional login params
        params_str = tool_parameters.get("params")
        params = None
        if params_str:
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError:
                yield self.create_text_message("Error: Invalid JSON in params")
                return

        # Parse optional 1Password item locator
        source_ref_str = tool_parameters.get("source_ref")
        source_ref = None
        if source_ref_str:
            try:
                source_ref = json.loads(source_ref_str)
            except json.JSONDecodeError:
                yield self.create_text_message("Error: Invalid JSON in source_ref")
                return

        identity_name = tool_parameters.get("identity_name")
        source_id = tool_parameters.get("source_id")

        payload = {"catalog_slug": catalog_slug}
        if params is not None:
            payload["params"] = params
        if identity_name:
            payload["identity_name"] = identity_name
        if source_id:
            payload["source_id"] = source_id
        if source_ref is not None:
            payload["source_ref"] = source_ref

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{BASE_URL}/wire/login",
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
