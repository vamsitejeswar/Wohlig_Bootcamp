"""
agent.py
--------
Multi-agent setup (required by Vertex AI):
  - Vertex AI cannot mix google_search (grounding) with other tools in one agent.
  - Solution: split into two sub-agents, root orchestrator delegates to both.

  web_search_agent    → only google_search
  enterprise_agent    → only MCP tools (BigQuery, GCS, Slack via Cloud Run)
  root_agent          → orchestrator, calls the two sub-agents as tools

Run:
    cd "Day 9 - ADK Multi-Agent ..."
    adk web
"""

import os
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
from .callbacks import before_tool_callback

CLOUD_RUN_URL = "https://bootcamp-mcp-server-465203017930.us-central1.run.app/mcp"
API_KEY = os.getenv("MCP_API_KEY", "wohlig-mcp-key-2024")

# Sub-agent 1: web search only
web_search_agent = LlmAgent(
    name="web_search_agent",
    model="gemini-2.5-flash",
    instruction="You are a web search specialist. Use google_search to find information on the web. Return clear, concise results.",
    tools=[google_search],
    before_tool_callback=before_tool_callback,
)

# Sub-agent 2: enterprise data only (BigQuery, GCS, Slack via MCP)
enterprise_agent = LlmAgent(
    name="enterprise_agent",
    model="gemini-2.5-flash",
    instruction="You are an enterprise data specialist. Use your tools to query BigQuery, list/read GCS objects, or send Slack messages. Return clear results.",
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=CLOUD_RUN_URL,
                headers={"x-api-key": API_KEY},
            )
        )
    ],
    before_tool_callback=before_tool_callback,
)

# Root orchestrator: delegates to the two sub-agents
root_agent = LlmAgent(
    name="wohlig_enterprise",
    model="gemini-2.5-flash",
    instruction=(
        "You are an enterprise research orchestrator.\n\n"
        "You have EXACTLY TWO tools available to you:\n"
        "- web_search_agent: call this to search the web\n"
        "- enterprise_agent: call this to query BigQuery, GCS, or Slack\n\n"
        "IMPORTANT RULES:\n"
        "- NEVER call bigquery_query, list_gcs_objects, google_search, or any other tool directly.\n"
        "- ALWAYS delegate: web questions → web_search_agent, internal data → enterprise_agent.\n"
        "- For questions needing both, call web_search_agent first, then enterprise_agent.\n"
        "- Pass the full user question as-is to the sub-agent.\n"
        "- Synthesize both answers into one final response."
    ),
    tools=[
        AgentTool(agent=web_search_agent),
        AgentTool(agent=enterprise_agent),
    ],
)
