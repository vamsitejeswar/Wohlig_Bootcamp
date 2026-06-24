"""
gemini_client.py
----------------
Connects to the deployed MCP server using Google ADK Agent + mcp-remote,
then runs 3 test queries through Gemini.

Run:
    python gemini_client.py
"""

import asyncio
import os
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters
from google.genai import types

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

QUERIES = [
    # (a) single-tool
    "List the files in the GCS bucket called wohlig-rag-pipeline-bucket",
    # (b) multi-tool
    "List the files in the GCS bucket wohlig-rag-pipeline-bucket, then read the first file you find",
    # (c) error case
    "Run this SQL query: DELETE FROM `wohlig.big_query_dataset.nyc_taxi` WHERE 1=1",
]

root_agent = Agent(
    model="gemini-2.5-flash",
    name="wohlig-enterprise",
    instruction=(
        "You are a helpful data assistant with access to Google Cloud Storage "
        "and BigQuery via MCP tools. Use the available tools to answer questions "
        "about data. Always be concise and structured in your responses."
    ),
    tools=[
        MCPToolset(
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


async def run():
    session_service = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name="mcp_test", session_service=session_service)
    session = await session_service.create_session(app_name="mcp_test", user_id="test_user")

    for i, query in enumerate(QUERIES, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}: {query}")
        print("="*60)

        content = types.Content(role="user", parts=[types.Part(text=query)])
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=content,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if part.text:
                        print(f"Gemini: {part.text}")


if __name__ == "__main__":
    asyncio.run(run())
