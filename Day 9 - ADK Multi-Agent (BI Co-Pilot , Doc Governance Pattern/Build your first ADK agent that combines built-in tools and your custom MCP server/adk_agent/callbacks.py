"""
callbacks.py
------------
before_tool_callback that logs every tool call as structured JSON.

On GCP: Cloud Logging agent picks up these JSON logs from stdout automatically.
Locally: logs print to console — use `adk web` and watch the terminal.

To use the native google-cloud-logging client (when available):
    pip install google-cloud-logging
"""

import json
import uuid
import logging
import datetime

# Standard Python logger — outputs structured JSON to stderr
logging.basicConfig(level=logging.INFO, format="%(message)s")
_logger = logging.getLogger("adk-agent")


def before_tool_callback(tool, args: dict, tool_context):
    """Fires before every tool call. Logs a structured entry and returns None to proceed."""
    entry = {
        "severity": "INFO",
        "agent_name": "enterprise_search_agent",
        "tool_called": tool.name,
        "args": args,
        "trace_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
    _logger.info(json.dumps(entry))
    return None  # None = let the tool run normally
