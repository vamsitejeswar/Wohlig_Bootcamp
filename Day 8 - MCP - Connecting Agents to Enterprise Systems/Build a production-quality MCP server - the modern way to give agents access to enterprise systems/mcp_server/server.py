"""
server.py
---------
Wohlig Enterprise MCP Server.
Exposes 4 tools that any MCP-compatible AI agent can call.

Run:  python server.py
      mcp dev server.py    (with inspector UI)
"""

from mcp.server.fastmcp import FastMCP
from tools.bigquery_tool import query_bigquery
from tools.gcs_list_tool  import list_gcs_objects
from tools.gcs_read_tool  import read_gcs_object
from tools.slack_tool      import send_slack_message

mcp = FastMCP(
    name="wohlig-enterprise",
    instructions=(
        "Gateway to BigQuery, GCS, and Slack. "
        "Always prefer read-only operations. "
        "Never run destructive SQL."
    ),
)

mcp.tool()(query_bigquery)
mcp.tool()(list_gcs_objects)
mcp.tool()(read_gcs_object)
mcp.tool()(send_slack_message)

if __name__ == "__main__":
    mcp.run()
