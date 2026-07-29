import json
import time
from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"
MAX_POLL_ATTEMPTS = 60
POLL_INTERVAL = 10


class AgenticSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key")

        prompt = tool_parameters.get("prompt")
        if not prompt:
            yield self.create_text_message("Error: Research question is required")
            return

        use_browser = tool_parameters.get("use_browser", True)

        # Parse optional data schema
        schema_str = tool_parameters.get("schema")
        schema = None
        if schema_str:
            try:
                schema = json.loads(schema_str)
            except json.JSONDecodeError:
                yield self.create_text_message("Error: Invalid JSON in schema")
                return

        payload = {
            "prompt": prompt,
            "useBrowser": use_browser
        }
        if schema is not None:
            payload["schema"] = schema

        try:
            with httpx.Client(timeout=30) as client:
                # Submit research job
                response = client.post(
                    f"{BASE_URL}/agentic-search",
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
                job_id = job_data.get("job_id")

                if not job_id:
                    yield self.create_json_message(job_data)
                    return

                # Poll for results (agentic search takes longer)
                for _ in range(MAX_POLL_ATTEMPTS):
                    time.sleep(POLL_INTERVAL)

                    result_response = client.get(
                        f"{BASE_URL}/agentic-search/{job_id}",
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
                        yield self.create_text_message(f"Research failed: {error}")
                        return

                yield self.create_text_message("Error: Research job timed out. This typically takes 1-5 minutes. Please try again.")

        except httpx.TimeoutException:
            yield self.create_text_message("Error: Request timeout")
        except httpx.RequestError as e:
            yield self.create_text_message(f"Error: {str(e)}")
