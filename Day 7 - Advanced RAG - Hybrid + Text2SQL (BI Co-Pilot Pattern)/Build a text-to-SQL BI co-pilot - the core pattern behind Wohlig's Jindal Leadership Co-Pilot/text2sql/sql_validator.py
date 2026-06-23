"""
sql_validator.py
----------------
Validates BigQuery SQL using the BQ dry-run API (syntax check, no data scanned).
If the SQL has errors, feeds the error back to the SQLAgent for correction.
Retries up to MAX_RETRIES times before giving up.

Exports:
  - SQLValidator  class  (.validate_with_retry(sql, schema) → dict)
"""

import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()


class SQLValidator:
    MAX_RETRIES = 2  # number of Gemini fix attempts after the first failure

    def __init__(self, agent):
        # agent is an SQLAgent instance — injected so this module stays decoupled
        self.bq_client = bigquery.Client(project=os.getenv("PROJECT_ID", "wohlig"))
        self.agent     = agent

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _dry_run(self, sql: str) -> tuple[bool, str]:
        """
        Submit a dry-run job to BigQuery.
        Returns (is_valid: bool, error_message: str).
        BigQuery checks syntax and schema without reading any data.
        """
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        try:
            self.bq_client.query(sql, job_config=job_config)
            return True, ""
        except Exception as exc:
            return False, str(exc)

    # ── Public API ────────────────────────────────────────────────────────────

    def validate_with_retry(self, sql: str, schema: str) -> dict:
        """
        Validate SQL with up to MAX_RETRIES correction attempts.

        Returns a dict:
          sql           str   – the final SQL (may differ from input if corrected)
          is_valid      bool  – True if the final SQL passed dry-run
          attempts      int   – total dry-run attempts made (1 + retries used)
          error         str   – last BigQuery error (empty string if valid)
          was_corrected bool  – True if the original SQL was modified by Gemini
        """
        current_sql   = sql
        last_error    = ""
        was_corrected = False

        # Up to MAX_RETRIES + 1 total attempts (initial + up to 2 corrections)
        for attempt in range(1, self.MAX_RETRIES + 2):
            is_valid, error = self._dry_run(current_sql)

            if is_valid:
                return {
                    "sql":           current_sql,
                    "is_valid":      True,
                    "attempts":      attempt,
                    "error":         "",
                    "was_corrected": was_corrected,
                }

            last_error = error
            print(f"    [validator] Attempt {attempt} — dry-run failed.")
            print(f"    [validator] Error: {error[:300]}")

            if attempt <= self.MAX_RETRIES:
                print(f"    [validator] Asking Gemini to fix (retry {attempt}/{self.MAX_RETRIES})...")
                current_sql   = self.agent.fix_sql(current_sql, error, schema)
                was_corrected = True
            else:
                print(f"    [validator] Max retries reached. Giving up.")

        return {
            "sql":           current_sql,
            "is_valid":      False,
            "attempts":      self.MAX_RETRIES + 1,
            "error":         last_error,
            "was_corrected": was_corrected,
        }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from schema_loader import SchemaLoader
    from agent import SQLAgent

    loader    = SchemaLoader()
    schema    = loader.format_for_prompt()
    agent     = SQLAgent()
    validator = SQLValidator(agent)

    bad_sql  = "SELECT nonexistent_column FROM `wohlig.big_query_dataset.nyc_taxi` LIMIT 5"
    result   = validator.validate_with_retry(bad_sql, schema)

    print(f"\nValid: {result['is_valid']}")
    print(f"Attempts: {result['attempts']}")
    print(f"Was corrected: {result['was_corrected']}")
    print(f"Final SQL:\n{result['sql']}")
