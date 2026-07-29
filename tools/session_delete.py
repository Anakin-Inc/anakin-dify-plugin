from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"


class SessionDeleteTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key")

        session_id = tool_parameters.get("id")
        if not session_id:
            yield self.create_text_message("Error: Session ID is required")
            return

        try:
            with httpx.Client(timeout=30) as client:
                response = client.delete(
                    f"{BASE_URL}/sessions/{session_id}",
                    headers={"X-API-Key": api_key, "X-Source": "dify"}
                )

                if response.status_code == 401:
                    yield self.create_text_message("Error: Invalid API Key")
                    return
                elif response.status_code == 402:
                    yield self.create_text_message("Error: Plan upgrade required")
                    return
                elif response.status_code not in [200, 202, 204]:
                    yield self.create_text_message(f"Error: {response.text}")
                    return

                if response.status_code == 204 or not response.text:
                    yield self.create_json_message({"status": "ok", "id": session_id})
                    return

                result = response.json()
                yield self.create_json_message(result)

        except httpx.TimeoutException:
            yield self.create_text_message("Error: Request timeout")
        except httpx.RequestError as e:
            yield self.create_text_message(f"Error: {str(e)}")
