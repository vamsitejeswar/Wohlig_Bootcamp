"""
deploy/agent_engine/deploy.py
------------------------------
Deploys the Day-9 BI Co-Pilot to Vertex AI Agent Engine.

Run once to create the engine:
    cd "Deploy your Day-9..."
    python deploy/agent_engine/deploy.py

The script prints the resource name — save it in .env as AGENT_ENGINE_ID.

Requirements:
    pip install google-cloud-aiplatform[agent_engines,adk] google-adk
"""

import os
import sys
from pathlib import Path

# Make bi_copilot importable
_DAY9 = Path(__file__).parents[4] / (
    "Day 9 - ADK Multi-Agent (BI Co-Pilot , Doc Governance Pattern"
    "/Build a multi-agent BI co-pilot - the same pattern as the Jindal Leadership Co-Pilot"
)
sys.path.insert(0, str(_DAY9))

from dotenv import load_dotenv
load_dotenv(_DAY9 / ".env")

import vertexai
from vertexai.preview import reasoning_engines

PROJECT  = os.getenv("GOOGLE_CLOUD_PROJECT", "wohlig")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

vertexai.init(project=PROJECT, location=LOCATION)

# Import root_agent after Vertex AI is initialised
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
from bi_copilot.orchestrator import root_agent

REQUIREMENTS = [
    "google-adk>=2.2.0",
    "google-cloud-bigquery",
    "google-cloud-aiplatform[agent_engines,adk]",
    "google-cloud-aiplatform[reasoningengine]",
    "pandas",
    "db-dtypes",
    "python-dotenv",
]

def deploy():
    print(f"Deploying BI Co-Pilot to Vertex AI Agent Engine...")
    print(f"  Project : {PROJECT}")
    print(f"  Location: {LOCATION}")

    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    engine = reasoning_engines.ReasoningEngine.create(
        app,
        requirements=REQUIREMENTS,
        display_name="bi-copilot-agent-engine",
        description=(
            "Multi-agent BI Co-Pilot: routes questions to structured_data_agent "
            "(BigQuery/text-to-SQL) or unstructured_data_agent (RAG/policy docs)."
        ),
    )

    resource_name = engine.resource_name
    print(f"\nDeployment complete.")
    print(f"Resource name: {resource_name}")
    print(f"\nAdd to your .env:")
    print(f"  AGENT_ENGINE_ID={resource_name}")
    return resource_name


if __name__ == "__main__":
    deploy()
