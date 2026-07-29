import json
import time
from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"
# Browser AI tasks are hard-capped server-side at ~330s, so the poll window
# must outlast the longest legitimate run.
MAX_POLL_ATTEMPTS = 120
POLL_INTERVAL = 3


class BrowserTaskTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key")

        prompt = tool_parameters.get("prompt")
        if not prompt:
            yield self.create_text_message("Error: Prompt is required")
            return

        url = tool_parameters.get("url")
        session_id = tool_parameters.get("session_id")
        max_steps = tool_parameters.get("max_steps")
        timeout_ms = tool_parameters.get("timeout_ms")

        # Parse optional output schema
        output_schema_str = tool_parameters.get("output_schema")
        output_schema = None
        if output_schema_str:
            try:
                output_schema = json.loads(output_schema_str)
            except json.JSONDecodeError:
                yield self.create_text_message("Error: Invalid JSON in output_schema")
                return

        payload = {"prompt": prompt, "async": True}
        if url:
            payload["url"] = url
        if session_id:
            payload["session_id"] = session_id
        if max_steps is not None:
            payload["max_steps"] = int(max_steps)
        if timeout_ms is not None:
            payload["timeout_ms"] = int(timeout_ms)
        if output_schema is not None:
            payload["output_schema"] = output_schema

        try:
            with httpx.Client(timeout=30) as client:
                # Submit the browser task
                response = client.post(
                    f"{BASE_URL}/ai/evaluate",
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
                workflow_id = job_data.get("workflow_id")

                if not workflow_id:
                    # Service answered synchronously (shouldn't happen with async: true).
                    yield self.create_json_message(job_data)
                    return

                # Poll for results (browser tasks can run up to ~5.5 minutes)
                for _ in range(MAX_POLL_ATTEMPTS):
                    time.sleep(POLL_INTERVAL)

                    result_response = client.get(
                        f"{BASE_URL}/ai/jobs/{workflow_id}",
                        headers={"X-API-Key": api_key, "X-Source": "dify"}
                    )

                    if result_response.status_code != 200:
                        continue

                    job = result_response.json()
                    status = job.get("status")

                    if status == "completed":
                        result = job.get("result", job)
                        yield self.create_json_message(result)
                        return
                    elif status in ("failed", "timed_out"):
                        error = job.get("error", "Unknown error")
                        yield self.create_text_message(f"Browser task {status}: {error}")
                        return

                yield self.create_text_message("Error: Browser task timed out after 6 minutes of polling.")

        except httpx.TimeoutException:
            yield self.create_text_message("Error: Request timeout")
        except httpx.RequestError as e:
            yield self.create_text_message(f"Error: {str(e)}")
