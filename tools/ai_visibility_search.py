import json
import time
from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"
MAX_POLL_ATTEMPTS = 60
POLL_INTERVAL = 3


class AiVisibilitySearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key")

        query = tool_parameters.get("query")
        if not query:
            yield self.create_text_message("Error: Query is required")
            return

        # Parse optional sources array
        sources_str = tool_parameters.get("sources")
        sources = None
        if sources_str:
            try:
                sources = json.loads(sources_str)
            except json.JSONDecodeError:
                yield self.create_text_message("Error: Invalid JSON in sources")
                return

        country = tool_parameters.get("country")
        include_full_content = tool_parameters.get("include_full_content", False)

        payload = {"query": query}
        if sources is not None:
            payload["sources"] = sources
        if country:
            payload["country"] = country

        try:
            with httpx.Client(timeout=30) as client:
                # Submit the AI visibility search
                response = client.post(
                    f"{BASE_URL}/ai-visibility/search",
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

                submitted = response.json()
                search_id = submitted.get("search_id")

                if not search_id:
                    yield self.create_json_message(submitted)
                    return

                # Poll until the search leaves the "running" state. A "failed" status
                # is still returned with data (per-source results/errors), not raised.
                search = None
                for _ in range(MAX_POLL_ATTEMPTS):
                    time.sleep(POLL_INTERVAL)

                    result_response = client.get(
                        f"{BASE_URL}/ai-visibility/search/{search_id}",
                        headers={"X-API-Key": api_key, "X-Source": "dify"}
                    )

                    if result_response.status_code != 200:
                        continue

                    search = result_response.json()
                    if search.get("status") != "running":
                        break
                else:
                    yield self.create_text_message(
                        f"AI visibility search {search_id} timed out after 3 minutes; "
                        "poll it later via the dashboard or retry."
                    )
                    return

                if search is None:
                    yield self.create_text_message("Error: Job timed out. Please try again.")
                    return

                results = search.get("results") or []
                if not include_full_content:
                    results = [
                        {k: v for k, v in r.items() if k != "full_content"}
                        for r in results
                    ]

                yield self.create_json_message({
                    "search_id": search.get("search_id"),
                    "status": search.get("status"),
                    "country": search.get("country"),
                    "synthesis": search.get("synthesis"),
                    "results": results
                })

        except httpx.TimeoutException:
            yield self.create_text_message("Error: Request timeout")
        except httpx.RequestError as e:
            yield self.create_text_message(f"Error: {str(e)}")
