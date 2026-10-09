from collections.abc import Generator
from typing import Any
from urllib.parse import quote

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"
DEFAULT_LIMIT = 10
MAX_LIMIT = 100


def _positive_int(value: Any, default: int, maximum: int | None = None) -> int:
    """Coerce a Dify number parameter (may arrive as float or str) to a bounded int."""
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        return default
    if n < 1:
        return default
    return min(n, maximum) if maximum else n


class WireBuildStatusTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key")
        headers = {"X-API-Key": api_key, "X-Source": "dify"}

        # Dify sends unset text inputs as "" -- treat blank the same as omitted
        # and fall through to list mode.
        build_id = (tool_parameters.get("id") or "").strip()

        if build_id:
            url = f"{BASE_URL}/wire/build-requests/{quote(build_id, safe='')}"
            params = None
        else:
            url = f"{BASE_URL}/wire/build-requests"
            # Always send a limit so the advertised default (10) applies,
            # not the API's own default (20).
            params = {
                "limit": _positive_int(tool_parameters.get("limit"), DEFAULT_LIMIT, MAX_LIMIT),
                "page": _positive_int(tool_parameters.get("page"), 1),
            }
            status = (tool_parameters.get("status") or "").strip()
            if status:
                params["status"] = status

        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(url, headers=headers, params=params)

                if response.status_code == 401:
                    yield self.create_text_message("Error: Invalid API Key")
                    return
                elif response.status_code == 402:
                    yield self.create_text_message("Error: Plan upgrade required")
                    return
                elif response.status_code == 404 and build_id:
                    yield self.create_text_message(f"Error: No build request found with id {build_id}")
                    return
                elif response.status_code != 200:
                    yield self.create_text_message(f"Error: {response.text}")
                    return

                result = response.json()

                # The step-event log is UI-oriented and verbose -- drop it unless
                # asked, so a polling agent stays cheap.
                if build_id and isinstance(result, dict) and not tool_parameters.get("include_events"):
                    result.pop("events", None)

                yield self.create_json_message(result)

        except httpx.TimeoutException:
            yield self.create_text_message("Error: Request timeout")
        except httpx.RequestError as e:
            yield self.create_text_message(f"Error: {str(e)}")
