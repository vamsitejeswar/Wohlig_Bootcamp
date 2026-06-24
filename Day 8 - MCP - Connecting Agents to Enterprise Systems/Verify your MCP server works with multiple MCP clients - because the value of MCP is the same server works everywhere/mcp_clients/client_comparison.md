# MCP Client Comparison — Gemini (ADK) vs Claude Code

## MCP Server
- **URL:** `https://bootcamp-mcp-server-qsnv3hviuq-uc.a.run.app/mcp`
- **Auth:** `x-api-key: wohlig-mcp-key-2024`
- **Tools:** `query_bigquery`, `list_gcs_objects`, `read_gcs_object`, `send_slack_message`

---

## 1. Setup

### Client A — Gemini via ADK (`gemini_client.py`)

```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams

toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://bootcamp-mcp-server-qsnv3hviuq-uc.a.run.app/mcp",
        headers={"x-api-key": "wohlig-mcp-key-2024"},
    )
)

agent = LlmAgent(
    model="gemini-2.5-flash",
    name="mcp_test_agent",
    tools=[toolset],
)
```

Environment variables needed:
```bash
GOOGLE_CLOUD_PROJECT=wohlig
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
```

Run: `python3 gemini_client.py`

---

### Client B — Claude Code (`~/.claude.json`)

```json
{
  "mcpServers": {
    "wohlig-enterprise": {
      "type": "http",
      "url": "https://bootcamp-mcp-server-qsnv3hviuq-uc.a.run.app/mcp",
      "headers": {
        "x-api-key": "wohlig-mcp-key-2024"
      }
    }
  }
}
```

After editing, restart Claude Code. The 4 MCP tools appear automatically in the session.

---

## 2. The 3 Test Queries

| # | Type | Query |
|---|------|-------|
| a | Single-tool | "List the files in the GCS bucket called wohlig-rag-pipeline-bucket" |
| b | Multi-tool | "List the files in wohlig-rag-pipeline-bucket, then read the first file you find" |
| c | Error case | "Run this SQL: DELETE FROM `wohlig.big_query_dataset.nyc_taxi` WHERE 1=1" |

---

## 3. Side-by-Side Results

| # | Query | Gemini (ADK) Behavior | Claude Code Behavior | Differences |
|---|-------|-----------------------|----------------------|-------------|
| a | List GCS files | Called `list_gcs_objects`, returned 1 file: `vectors/chunks_metadata.json` (1MB, last updated 2026-06-22) | Called `list_gcs_objects`, returned same file with same metadata | No difference — identical tool call, identical result |
| b | List then read first file | Called `list_gcs_objects` first, then attempted `read_gcs_object`, correctly reported file exceeds 1MB limit and cannot be read | Called both tools in sequence, same 1MB limit error surfaced | No difference in tool behavior; both clients handled multi-step correctly |
| c | DELETE SQL (blocked) | Refused to call the tool at all — said "I can only run SELECT statements" | Attempted to call `query_bigquery`, server returned error: `Blocked: destructive SQL not allowed`, then reported the error to user | **Difference:** Gemini refused before calling the tool (model-level knowledge). Claude called the tool and let the server's safety guard block it. Both produced the correct outcome but via different paths. |

---

## 4. Auth / Format / Error Differences

### Auth
- **Both clients** pass the `x-api-key` header in every request automatically once configured.
- No difference in auth handling — the middleware works identically for both.

### Tool-call format
- Both clients speak the same MCP JSON-RPC protocol (`tools/call` over `POST /mcp`).
- ADK translates the tool schema into Gemini function-calling format internally.
- Claude Code uses the tool schema natively.
- The server sees identical wire-format requests from both.

### Error display
- **Gemini (ADK):** Surfaces errors as natural language in the final response. The raw MCP error JSON is hidden from the user.
- **Claude Code:** Shows the tool call, the raw error from the server, then explains it in natural language. More transparent — user can see exactly what the server returned.

### Multi-turn / session
- **Gemini (ADK):** Each `run_async` call is one session. Multi-tool queries (Query b) are handled in a single agent loop turn.
- **Claude Code:** Each conversation turn is one session. Tool calls within a turn share the same MCP session ID.

---

## 5. Recommendation — Server-Side Changes for Better Compatibility

| Issue | Current Behavior | Recommended Change |
|-------|------------------|--------------------|
| Error messages | Raw Python exception strings | Return structured JSON errors: `{"error": "BLOCKED_SQL", "message": "...", "code": "safety_guard"}` — easier for both clients to parse and display |
| 1MB GCS limit | Hard error with no metadata | Return `{"truncated": true, "size_bytes": 1063242, "preview": "...first 500 chars"}` so clients can still show partial content |
| Tool descriptions | Brief one-liners | Add example inputs to each tool's docstring — Gemini uses these to decide when to call the tool |
| Rate limit response | `429` with JSON body | Add `Retry-After` header — ADK can automatically retry instead of failing |

### Summary
The same MCP server worked with zero changes across both clients. The MCP protocol is the reason — both Gemini and Claude speak the same JSON-RPC wire format. The only real difference was error handling: Claude Code shows server errors transparently, Gemini abstracts them. For production, structured error codes would help both clients handle failures gracefully.
