import os
import uvicorn
from mcp.server.fastmcp import FastMCP

from tools.bigquery_tool import query_bigquery
from tools.gcs_list_tool  import list_gcs_objects
from tools.gcs_read_tool  import read_gcs_object
from tools.slack_tool      import send_slack_message

from middleware.auth       import AuthMiddleware
from middleware.rate_limit import RateLimitMiddleware
from middleware.logging    import LoggingMiddleware

mcp = FastMCP(
    name="wohlig-enterprise",
    host="0.0.0.0",
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

app = mcp.streamable_http_app()
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, proxy_headers=True, forwarded_allow_ips="*")
