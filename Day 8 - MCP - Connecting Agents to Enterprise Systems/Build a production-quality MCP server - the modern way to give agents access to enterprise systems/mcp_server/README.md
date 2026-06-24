# Wohlig Enterprise MCP Server

An MCP server exposing 4 tools that any AI agent (Claude, Gemini, Cursor) can call.

## Run

```bash
pip install -r requirements.txt
python server.py          # stdio mode
mcp dev server.py         # with browser inspector UI
```

## Tools

### 1. `query_bigquery(sql)`
Run a read-only BigQuery SQL query.

| Input | Type | Required |
|-------|------|----------|
| sql | string | Yes |

**Safety:** Blocks non-SELECT. Rejects if dry-run estimates > 100MB scan.

**Example:**
```
query_bigquery("SELECT vendor_id, COUNT(*) FROM `wohlig.big_query_dataset.nyc_taxi` GROUP BY 1")
```

---

### 2. `list_gcs_objects(bucket, prefix)`
List files in a GCS bucket.

| Input | Type | Required |
|-------|------|----------|
| bucket | string | Yes |
| prefix | string | No (default: "") |

**Example:**
```
list_gcs_objects("wohlig-rag-bucket", "pdfs/")
```

---

### 3. `read_gcs_object(bucket, path)`
Read a file from GCS as text.

| Input | Type | Required |
|-------|------|----------|
| bucket | string | Yes |
| path | string | Yes |

**Safety:** Rejects files > 1MB.

**Example:**
```
read_gcs_object("wohlig-rag-bucket", "pdfs/policy.txt")
```

---

### 4. `send_slack_message(channel, message)`
Send a Slack message. **Stubbed** — prints to console only.

| Input | Type | Required |
|-------|------|----------|
| channel | string | Yes |
| message | string | Yes |

**Example:**
```
send_slack_message("alerts", "Query complete — 500 rows returned.")
```

## Run Tests

```bash
cd mcp_server
pytest tests/ -v
```
