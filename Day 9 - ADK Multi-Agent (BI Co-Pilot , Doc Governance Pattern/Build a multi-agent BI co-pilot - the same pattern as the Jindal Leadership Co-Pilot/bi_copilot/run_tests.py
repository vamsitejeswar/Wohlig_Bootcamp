"""
run_tests.py
------------
Runs all 10 test queries through the BI Co-Pilot orchestrator and saves
structured results to test_results/<query_id>/result.md.

For each query records:
  - Which sub-agents were called (and in what order)
  - Intermediate tool call arguments
  - The final answer
  - Whether routing was correct (fill in manually after reviewing)

Run:
    cd "Build a multi-agent BI co-pilot..."
    python bi_copilot/run_tests.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Make sure the parent of bi_copilot/ is on sys.path so
# "from bi_copilot.orchestrator import root_agent" resolves correctly
# regardless of which directory the script is run from.
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(_PROJECT_ROOT / ".env")

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from bi_copilot.orchestrator import root_agent

# ── Test queries ──────────────────────────────────────────────────────────────
TEST_QUERIES = [
    # BQ-only (structured data)
    ("Q01_bq",   "sql",  "How many trips happened in each month of last year?"),
    ("Q02_bq",   "sql",  "Which vendor had the highest average fare in Q3?"),
    ("Q03_bq",   "sql",  "Show the top 5 pickup hours by trip count."),

    # RAG-only (unstructured / policy)
    ("Q04_rag",  "rag",  "What is the data retention policy for trip records?"),
    ("Q05_rag",  "rag",  "Explain the process for disputing a fare charge."),
    ("Q06_rag",  "rag",  "What are the SLA targets for data pipeline uptime?"),

    # Both agents needed
    ("Q07_both", "both", "Did last month's average trip duration exceed the service standard?"),
    ("Q08_both", "both", "How many refund requests were filed, and what is the refund policy?"),
    ("Q09_both", "both", "Compare peak-hour trip counts against the capacity guidelines."),
    ("Q10_both", "both", "Which payment type has grown most, and are there compliance requirements for it?"),
]

RESULTS_DIR = Path(__file__).parent / "test_results"
APP_NAME    = "bi_copilot"
USER_ID     = "test_runner"


async def run_query(runner: Runner, session_id: str, question: str) -> dict:
    """Run one query and capture agents called + final answer."""
    agents_called = []
    intermediate  = []
    final_answer  = ""

    message = types.Content(
        role="user",
        parts=[types.Part(text=question)],
    )

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        # Capture sub-agent tool calls from the orchestrator's content
        if event.content and event.content.parts:
            for part in event.content.parts:
                # Function call = orchestrator invoking a sub-agent
                if hasattr(part, "function_call") and part.function_call:
                    name = part.function_call.name
                    args = dict(part.function_call.args) if part.function_call.args else {}
                    if name not in agents_called:
                        agents_called.append(name)
                    intermediate.append({"agent": name, "input": args})

                # Function response = sub-agent result
                if hasattr(part, "function_response") and part.function_response:
                    resp = part.function_response
                    intermediate.append({
                        "agent":  resp.name,
                        "output": str(resp.response)[:500],
                    })

        if event.is_final_response() and event.content and event.content.parts:
            final_answer = event.content.parts[0].text or ""

    return {
        "agents_called":  agents_called,
        "intermediate":   intermediate,
        "final_answer":   final_answer,
    }


def save_result(query_id: str, question: str, expected: str, result: dict) -> None:
    out_dir = RESULTS_DIR / query_id
    out_dir.mkdir(parents=True, exist_ok=True)

    agents_str = " → ".join(result["agents_called"]) if result["agents_called"] else "none captured"

    md = f"""# {query_id}

## Question
{question}

## Expected routing
{expected}

## Agents called
{agents_str}

## Routing correct?
<!-- Fill in after review: YES / NO + reason -->
PENDING

## Intermediate outputs
```json
{json.dumps(result["intermediate"], indent=2, default=str)}
```

## Final answer
{result["final_answer"]}
"""
    (out_dir / "result.md").write_text(md)
    print(f"  Saved → {out_dir / 'result.md'}")


async def main() -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    print("=" * 65)
    print("BI Co-Pilot — Test Runner")
    print("=" * 65)

    for query_id, expected, question in TEST_QUERIES:
        print(f"\n[{query_id}] {question[:60]}")
        print(f"  Expected: {expected}")

        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
        )

        try:
            result = await run_query(runner, session.id, question)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            result = {"agents_called": [], "intermediate": [], "final_answer": f"ERROR: {exc}"}

        called_str = " → ".join(result["agents_called"]) or "none"
        print(f"  Agents called: {called_str}")
        print(f"  Answer preview: {result['final_answer'][:120].replace(chr(10), ' ')}...")

        save_result(query_id, question, expected, result)

    print("\n" + "=" * 65)
    print(f"Done. Results in: {RESULTS_DIR}")
    print("=" * 65)
    print("\nNext step: open each result.md and fill in 'Routing correct? YES/NO'")
    print("Then add any failures to routing_failures.md")


if __name__ == "__main__":
    asyncio.run(main())
