from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"


class WireIdentitiesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key")

        catalog_id = tool_parameters.get("catalog_id")
        params = {}
        if catalog_id:
            params["catalog_id"] = catalog_id

        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    f"{BASE_URL}/wire/identities",
                    headers={"X-API-Key": api_key, "X-Source": "dify"},
                    params=params
                )

                if response.status_code == 401:
                    yield self.create_text_message("Error: Invalid API Key")
                    return
                elif response.status_code == 402:
                    yield self.create_text_message("Error: Plan upgrade required")
                    return
                elif response.status_code != 200:
                    yield self.create_text_message(f"Error: {response.text}")
                    return

                result = response.json()
                yield self.create_json_message(result)

        except httpx.TimeoutException:
            yield self.create_text_message("Error: Request timeout")
        except httpx.RequestError as e:
            yield self.create_text_message(f"Error: {str(e)}")
