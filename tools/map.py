import time
from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"
MAX_POLL_ATTEMPTS = 60
POLL_INTERVAL = 3


class MapTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key")

        url = tool_parameters.get("url")
        if not url:
            yield self.create_text_message("Error: URL is required")
            return

        limit = tool_parameters.get("limit", 100)
        depth = tool_parameters.get("depth", 2)
        limit_per_level = tool_parameters.get("limit_per_level", 100)
        include_subdomains = tool_parameters.get("include_subdomains", False)
        include_external_links = tool_parameters.get("include_external_links", False)
        use_browser = tool_parameters.get("use_browser", False)
        search = tool_parameters.get("search")

        payload = {
            "url": url,
            "limit": int(limit),
            "depth": int(depth),
            "limitPerLevel": int(limit_per_level),
            "includeSubdomains": include_subdomains,
            "includeExternalLinks": include_external_links,
            "useBrowser": use_browser
        }
        if search:
            payload["search"] = search

        try:
            with httpx.Client(timeout=30) as client:
                # Submit the mapping job
                response = client.post(
                    f"{BASE_URL}/map",
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

                job_data = response.json()
                job_id = job_data.get("jobId")

                if not job_id:
                    yield self.create_json_message(job_data)
                    return

                # Poll for results
                for _ in range(MAX_POLL_ATTEMPTS):
                    time.sleep(POLL_INTERVAL)

                    result_response = client.get(
                        f"{BASE_URL}/map/{job_id}",
                        headers={"X-API-Key": api_key, "X-Source": "dify"}
                    )

                    if result_response.status_code != 200:
                        continue

                    result = result_response.json()
                    status = result.get("status")

                    if status == "completed":
                        yield self.create_json_message(result)
                        return
                    elif status == "failed":
                        error = result.get("error", "Unknown error")
                        yield self.create_text_message(f"Mapping failed: {error}")
                        return

                yield self.create_text_message("Error: Job timed out. Please try again.")

        except httpx.TimeoutException:
            yield self.create_text_message("Error: Request timeout")
        except httpx.RequestError as e:
            yield self.create_text_message(f"Error: {str(e)}")
