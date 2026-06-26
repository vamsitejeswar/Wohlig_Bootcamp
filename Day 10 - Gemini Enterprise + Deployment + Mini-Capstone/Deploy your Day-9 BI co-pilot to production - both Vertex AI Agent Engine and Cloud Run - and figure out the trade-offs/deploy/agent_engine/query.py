"""
deploy/agent_engine/query.py
-----------------------------
Runs a 5-turn conversation against the deployed Vertex AI Agent Engine.

Usage:
    export AGENT_ENGINE_ID=projects/wohlig/locations/us-central1/reasoningEngines/<ID>
    python deploy/agent_engine/query.py

Prints each question, the agent response, and which sub-agents were called.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parents[2] / ".env")

import vertexai
from vertexai.preview import reasoning_engines

PROJECT        = os.getenv("GOOGLE_CLOUD_PROJECT", "wohlig")
LOCATION       = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID", "")

if not AGENT_ENGINE_ID:
    print("ERROR: Set AGENT_ENGINE_ID in your .env file.")
    print("  Run deploy.py first to get the resource name.")
    sys.exit(1)

vertexai.init(project=PROJECT, location=LOCATION)

# 5-turn conversation — covers BQ-only, RAG-only, and both-agent routing
CONVERSATION = [
    ("Q1 — BQ only",   "How many trips happened last month?"),
    ("Q2 — RAG only",  "What is the data retention policy for trip records?"),
    ("Q3 — Both",      "Did last month's average trip duration exceed the service standard?"),
    ("Q4 — BQ only",   "Which vendor had the highest average fare in Q3?"),
    ("Q5 — Both",      "What are the SLA targets for data pipeline uptime and did we meet them last month?"),
]


def run_conversation():
    engine = reasoning_engines.ReasoningEngine(AGENT_ENGINE_ID)

    print("Creating session...")
    session = engine.create_session(user_id="deployment_test")
    session_id = session["id"]
    print(f"Session ID: {session_id}\n")
    print("=" * 65)

    for label, question in CONVERSATION:
        print(f"\n[{label}]")
        print(f"Question: {question}")
        print("-" * 40)

        response_text = ""
        for event in engine.stream_query(
            user_id="deployment_test",
            session_id=session_id,
            message=question,
        ):
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_text = part.text

        print(f"Response: {response_text[:400]}")
        print("=" * 65)

    print(f"\nDone. View traces in Cloud Trace:")
    print(f"  https://console.cloud.google.com/traces/list?project={PROJECT}")


if __name__ == "__main__":
    run_conversation()
