"""
deploy/cloud_run/main.py
-------------------------
FastAPI server that wraps the Day-9 BI Co-Pilot for Cloud Run deployment.

Endpoints:
    POST /query          — single-turn query (stateless)
    POST /session/create — create a named session
    POST /session/query  — multi-turn query within a session
    GET  /health         — health check for Cloud Run
"""

import asyncio
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ── Environment ───────────────────────────────────────────────────────────────
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "wohlig")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

# ── ADK imports ───────────────────────────────────────────────────────────────
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# bi_copilot is copied into the container at /app/bi_copilot (see Dockerfile)
from bi_copilot.orchestrator import root_agent

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="BI Co-Pilot", version="1.0")

_session_service = InMemorySessionService()
_runner = Runner(
    agent=root_agent,
    app_name="bi_copilot",
    session_service=_session_service,
)

APP_NAME = "bi_copilot"
USER_ID  = "cloud_run_user"


# ── Request / Response models ─────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    session_id: str = "default"


class QueryResponse(BaseModel):
    answer: str
    session_id: str


class SessionResponse(BaseModel):
    session_id: str


# ── Helper ────────────────────────────────────────────────────────────────────
async def _run_query(session_id: str, question: str) -> str:
    message = types.Content(
        role="user",
        parts=[types.Part(text=question)],
    )
    final_answer = ""
    async for event in _runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_answer = event.content.parts[0].text or ""
    return final_answer


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "agent": root_agent.name}


@app.post("/session/create", response_model=SessionResponse)
async def create_session():
    session = await _session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
    )
    return {"session_id": session.id}


@app.post("/query", response_model=QueryResponse)
async def query(body: QueryRequest):
    # Auto-create session if it doesn't exist
    try:
        session = await _session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=body.session_id,
        )
    except Exception:
        session = await _session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
        )

    answer = await _run_query(session.id, body.question)
    if not answer:
        raise HTTPException(status_code=500, detail="Agent returned no response.")

    return {"answer": answer, "session_id": session.id}


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)), reload=False)
