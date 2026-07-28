import json
from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


BASE_URL = "https://api.anakin.io/v1"


def _parse_json_field(tool_parameters: dict[str, Any], name: str) -> tuple[Any, str | None]:
    """Parse an optional JSON-string parameter. Returns (value, error_message)."""
    raw = tool_parameters.get(name)
    if not raw:
        return None, None
    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        return None, f"Error: Invalid JSON in {name}"


class MonitorCreateTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        api_key = self.runtime.credentials.get("api_key")

        url = tool_parameters.get("url")
        if not url:
            yield self.create_text_message("Error: URL is required")
            return

        interval_minutes = tool_parameters.get("interval_minutes")
        if interval_minutes is None:
            yield self.create_text_message("Error: Interval (minutes) is required")
            return

        # Parse the JSON-string fields
        output_schema, err = _parse_json_field(tool_parameters, "output_schema")
        if err:
            yield self.create_text_message(err)
            return
        include_patterns, err = _parse_json_field(tool_parameters, "include_patterns")
        if err:
            yield self.create_text_message(err)
            return
        exclude_patterns, err = _parse_json_field(tool_parameters, "exclude_patterns")
        if err:
            yield self.create_text_message(err)
            return
        wire_params, err = _parse_json_field(tool_parameters, "wire_params")
        if err:
            yield self.create_text_message(err)
            return
        wire_watch_paths, err = _parse_json_field(tool_parameters, "wire_watch_paths")
        if err:
            yield self.create_text_message(err)
            return

        payload: dict[str, Any] = {
            "url": url,
            "intervalMinutes": int(interval_minutes),
            "scope": tool_parameters.get("scope", "page"),
            "watchMode": tool_parameters.get("watch_mode", "full_page"),
            "watchFormat": tool_parameters.get("watch_format", "markdown"),
            "aiMode": tool_parameters.get("ai_mode", False),
            "useBrowser": tool_parameters.get("use_browser", False),
            "country": tool_parameters.get("country", "us"),
            "isActive": tool_parameters.get("is_active", True)
        }

        if output_schema is not None:
            payload["outputSchema"] = output_schema
        if tool_parameters.get("ai_goal"):
            payload["aiGoal"] = tool_parameters["ai_goal"]
        if tool_parameters.get("session_id"):
            payload["sessionId"] = tool_parameters["session_id"]
        if tool_parameters.get("expires_at"):
            payload["expiresAt"] = tool_parameters["expires_at"]
        if tool_parameters.get("alert_webhook_url"):
            payload["alertWebhookUrl"] = tool_parameters["alert_webhook_url"]
        if tool_parameters.get("alert_emails"):
            payload["alertEmails"] = tool_parameters["alert_emails"]
        if tool_parameters.get("max_pages") is not None:
            payload["maxPages"] = int(tool_parameters["max_pages"])
        if tool_parameters.get("max_depth") is not None:
            payload["maxDepth"] = int(tool_parameters["max_depth"])
        if include_patterns is not None:
            payload["includePatterns"] = include_patterns
        if exclude_patterns is not None:
            payload["excludePatterns"] = exclude_patterns
        if tool_parameters.get("wire_action_id"):
            payload["wireActionId"] = tool_parameters["wire_action_id"]
        if tool_parameters.get("wire_catalog_slug"):
            payload["wireCatalogSlug"] = tool_parameters["wire_catalog_slug"]
        if tool_parameters.get("wire_credential_id"):
            payload["wireCredentialId"] = tool_parameters["wire_credential_id"]
        if wire_params is not None:
            payload["wireParams"] = wire_params
        if wire_watch_paths is not None:
            payload["wireWatchPaths"] = wire_watch_paths

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{BASE_URL}/monitors",
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
                elif response.status_code not in [200, 201, 202]:
                    yield self.create_text_message(f"Error: {response.text}")
                    return

                result = response.json()
                yield self.create_json_message(result)

        except httpx.TimeoutException:
            yield self.create_text_message("Error: Request timeout")
        except httpx.RequestError as e:
            yield self.create_text_message(f"Error: {str(e)}")
