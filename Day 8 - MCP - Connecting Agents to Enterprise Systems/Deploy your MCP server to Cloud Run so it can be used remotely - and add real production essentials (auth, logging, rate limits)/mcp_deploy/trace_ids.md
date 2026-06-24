# Test Calls + Trace IDs

## Service
URL: `https://bootcamp-mcp-server-qsnv3hviuq-uc.a.run.app`
Revision: `bootcamp-mcp-server-00003-lzg`

## Test Results

| # | Tool / Method | Input | Status | Notes |
|---|---------------|-------|--------|-------|
| 1 | `initialize` | protocolVersion 2024-11-05 | 200 ✓ | Server returned name=wohlig-enterprise, all 4 tools listed |
| 2 | Auth check | No x-api-key header | 401 ✓ | "Missing or invalid x-api-key header." |
| 3 | Auth check | x-api-key: wrong-key | 401 ✓ | Auth middleware blocking correctly |
| 4 | `tools/list` | (no session) | 400 | Expected — MCP requires initialize handshake first |
| 5 | GET /mcp | Accept: text/event-stream, no session | 400 | Expected — session ID required |

## Initialize Response (Test 1)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "experimental": {},
      "prompts": {"listChanged": false},
      "resources": {"subscribe": false, "listChanged": false},
      "tools": {"listChanged": false}
    },
    "serverInfo": {"name": "wohlig-enterprise", "version": "1.28.0"},
    "instructions": "Gateway to BigQuery, GCS, and Slack. Always prefer read-only operations. Never run destructive SQL."
  }
}
```

## Cloud Logging
View logs at:
https://console.cloud.google.com/logs?project=wohlig

Filter: `resource.type="cloud_run_revision" resource.labels.service_name="bootcamp-mcp-server"`

## Root Cause Fixed (421 Invalid Host header)
FastMCP defaults to `host="127.0.0.1"` which auto-enables DNS rebinding protection,
blocking any non-localhost Host header. Fix: pass `host="0.0.0.0"` to FastMCP()
so it skips the auto-protection. Cloud Run's HTTPS layer handles this at the infra level.


##To delete deployed mcp server in cloud run

gcloud run services delete bootcamp-mcp-server --region us-central1
gcloud container images delete gcr.io/wohlig/bootcamp-mcp-server --force-delete-tags