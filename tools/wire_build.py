from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"


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
