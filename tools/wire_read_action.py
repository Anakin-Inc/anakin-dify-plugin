import json
import time
from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"
MAX_POLL_ATTEMPTS = 60
DEFAULT_POLL_INTERVAL = 3
MIN_POLL_INTERVAL = 0.5
MAX_POLL_INTERVAL = 10


class WireReadActionTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key")

        action_id = tool_parameters.get("action_id")
        if not action_id:
            yield self.create_text_message("Error: Action ID is required")
            return

        # Parse optional params
        params_str = tool_parameters.get("params")
        params = {}
        if params_str:
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError:
                yield self.create_text_message("Error: Invalid JSON in params")
                return

        credential_id = tool_parameters.get("credential_id")
        identity_id = tool_parameters.get("identity_id")

        payload = {"action_id": action_id}
        if params:
            payload["params"] = params
        if credential_id:
            payload["credential_id"] = credential_id
        if identity_id:
            payload["identity_id"] = identity_id

        try:
            with httpx.Client(timeout=30) as client:
                # Submit the Wire task
                response = client.post(
                    f"{BASE_URL}/wire/task",
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
                    # Synchronous action: the result came back inline, no job to poll.
                    yield self.create_json_message(job_data)
                    return

                # Poll for results, honoring the server's retry_after_ms pacing hint
                poll_interval = DEFAULT_POLL_INTERVAL
                for _ in range(MAX_POLL_ATTEMPTS):
                    time.sleep(poll_interval)

                    result_response = client.get(
                        f"{BASE_URL}/wire/jobs/{job_id}",
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
                        error = result.get("error") or {}
                        message = error.get("message") if isinstance(error, dict) else str(error)
                        yield self.create_text_message(f"Wire action failed: {message or 'Unknown error'}")
                        return

                    retry_after_ms = result.get("retry_after_ms")
                    if isinstance(retry_after_ms, (int, float)):
                        poll_interval = max(MIN_POLL_INTERVAL, min(retry_after_ms / 1000, MAX_POLL_INTERVAL))

                yield self.create_text_message("Error: Wire job timed out. Please try again.")

        except httpx.TimeoutException:
            yield self.create_text_message("Error: Request timeout")
        except httpx.RequestError as e:
            yield self.create_text_message(f"Error: {str(e)}")
