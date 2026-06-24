import json
import os
from google.cloud import bigquery
from dotenv import load_dotenv
from safety.sql_guard import is_read_only
from safety.cost_guard import check_cost

load_dotenv()


def query_bigquery(sql: str) -> str:
    """Run a read-only BigQuery SQL query. Rejects non-SELECT and queries scanning > 100MB."""
    if not is_read_only(sql):
        return json.dumps({"error": True, "code": "NOT_READ_ONLY", "message": "Only SELECT queries are allowed."})

    client = bigquery.Client(project=os.getenv("PROJECT_ID", "wohlig"))

    try:
        ok, bytes_scanned = check_cost(sql, client)
        if not ok:
            mb = bytes_scanned / (1024 * 1024)
            return json.dumps({"error": True, "code": "COST_LIMIT", "message": f"Query would scan {mb:.1f}MB — limit is 100MB."})
    except Exception as e:
        return json.dumps({"error": True, "code": "DRY_RUN_FAILED", "message": str(e)})

    try:
        rows = list(client.query(sql).result())
        data = [dict(row) for row in rows]
        return json.dumps({"error": False, "count": len(data), "rows": data}, default=str)
    except Exception as e:
        return json.dumps({"error": True, "code": "QUERY_FAILED", "message": str(e)})
