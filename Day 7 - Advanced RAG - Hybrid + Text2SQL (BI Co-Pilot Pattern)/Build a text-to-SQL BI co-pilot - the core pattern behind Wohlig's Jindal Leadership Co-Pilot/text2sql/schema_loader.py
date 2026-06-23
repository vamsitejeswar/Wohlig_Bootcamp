"""
schema_loader.py
----------------
Fetches the BigQuery table schema (column names, types, modes) and sample rows,
then formats them into a prompt-ready string for the SQL generation agent.

Exports:
  - SchemaLoader  class  (.get_schema() → dict, .format_for_prompt() → str)
"""

import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID  = os.getenv("PROJECT_ID", "wohlig")
DATASET_ID  = os.getenv("DATASET_ID", "big_query_dataset")
TABLE_ID    = os.getenv("TABLE_ID", "nyc_taxi")
SAMPLE_ROWS = 3


class SchemaLoader:
    def __init__(self):
        self.client     = bigquery.Client(project=PROJECT_ID)
        self.project_id = PROJECT_ID
        self.dataset_id = DATASET_ID
        self.table_id   = TABLE_ID
        self.full_table = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    def get_schema(self) -> dict:
        """Returns schema dict with columns list and sample rows."""
        table_ref = self.client.get_table(self.full_table)

        columns = [
            {
                "name": field.name,
                "type": field.field_type,
                "mode": field.mode,
            }
            for field in table_ref.schema
        ]

        # Fetch a few rows to give the LLM real value examples
        query     = f"SELECT * FROM `{self.full_table}` LIMIT {SAMPLE_ROWS}"
        sample_rows = [dict(row) for row in self.client.query(query).result()]

        return {
            "table":       self.full_table,
            "columns":     columns,
            "sample_rows": sample_rows,
        }

    def format_for_prompt(self) -> str:
        """
        Returns a formatted schema string ready to inject into an LLM prompt.

        Example output:
            Table: `wohlig.big_query_dataset.nyc_taxi`

            Columns:
              - vendor_id (INTEGER, NULLABLE)
              - pickup_datetime (TIMESTAMP, NULLABLE)
              ...

            Sample rows (first 3):
              Row 1: {'vendor_id': 2, 'pickup_datetime': ..., ...}
        """
        schema = self.get_schema()

        lines = [f"Table: `{schema['table']}`", "", "Columns:"]
        for col in schema["columns"]:
            lines.append(f"  - {col['name']} ({col['type']}, {col['mode']})")

        lines.append("")
        lines.append(f"Sample rows (first {SAMPLE_ROWS}):")
        for i, row in enumerate(schema["sample_rows"], 1):
            # Truncate long values so the prompt stays compact
            compact = {k: (str(v)[:50] if v is not None else "null") for k, v in row.items()}
            lines.append(f"  Row {i}: {compact}")

        return "\n".join(lines)


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    loader = SchemaLoader()
    print(loader.format_for_prompt())
