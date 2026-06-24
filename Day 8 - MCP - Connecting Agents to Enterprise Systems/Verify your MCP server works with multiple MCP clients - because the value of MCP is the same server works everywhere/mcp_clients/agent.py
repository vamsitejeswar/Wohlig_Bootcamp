import os
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

os.environ["GOOGLE_CLOUD_PROJECT"] = "wohlig"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

MCP_SERVER_URL = os.environ.get(
    "MCP_SERVER_URL",
    "https://bootcamp-mcp-server-qsnv3hviuq-uc.a.run.app/mcp"
)
MCP_API_KEY = os.environ.get(
    "MCP_API_KEY",
    "wohlig-mcp-key-2024"
)

root_agent = Agent(
    model="gemini-2.5-flash",
    name="wohlig_enterprise",
    instruction=(
        "You are a helpful data assistant with access to Google Cloud Storage "
        "and BigQuery via MCP tools. Use the available tools to answer questions "
        "about data. Always be concise and structured in your responses."
    ),
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=[
                        "-y",
                        "mcp-remote",
                        MCP_SERVER_URL,
                        "--header",
                        f"x-api-key:{MCP_API_KEY}",
                    ],
                )
            )
        )
    ],
)
