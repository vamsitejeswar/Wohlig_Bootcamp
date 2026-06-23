"""
agent.py
--------
Converts a natural-language question into a BigQuery SQL query using Gemini.
Also exposes fix_sql() — called by sql_validator.py when a dry-run fails.

Exports:
  - SQLAgent  class  (.generate_sql(question, schema) → str,
                      .fix_sql(sql, error, schema) → str)
"""

import os
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

_SYSTEM_RULES = """You are a BigQuery SQL expert.
Your job is to convert natural language questions into valid BigQuery Standard SQL queries.

Rules:
1. Use ONLY the table and columns shown in the schema — never invent column names.
2. Always use the fully qualified table name: `project.dataset.table` with backtick quoting.
3. Return ONLY the SQL query — no markdown fences, no explanation, no comments.
4. Use BigQuery Standard SQL syntax (not legacy SQL).
5. For date/time: use EXTRACT(), DATE_TRUNC(), TIMESTAMP_DIFF(), FORMAT_TIMESTAMP().
6. For window functions: use OVER (PARTITION BY ... ORDER BY ...).
7. Add LIMIT 1000 to non-aggregation queries to control result size.
8. When the question asks for a ranking, use ROW_NUMBER() or RANK() window functions.
"""


class SQLAgent:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=os.getenv("PROJECT_ID", "wohlig"),
            location=os.getenv("LOCATION", "us-central1"),
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _clean(text: str) -> str:
        """Strip markdown code fences that Gemini sometimes adds."""
        text = text.strip()
        text = re.sub(r"^```(?:sql)?\s*\n?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\n?```\s*$", "", text)
        return text.strip()

    def _call_gemini(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return (response.text or "").strip()

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_sql(self, question: str, schema: str) -> str:
        """Generate a BigQuery SQL query for a natural-language question."""
        prompt = f"""{_SYSTEM_RULES}

--- SCHEMA ---
{schema}
--- END SCHEMA ---

Question: {question}

SQL Query:"""
        return self._clean(self._call_gemini(prompt))

    def fix_sql(self, original_sql: str, error_message: str, schema: str) -> str:
        """
        Ask Gemini to repair a SQL query given a BigQuery error message.
        Called by SQLValidator when a dry-run fails.
        """
        prompt = f"""{_SYSTEM_RULES}

--- SCHEMA ---
{schema}
--- END SCHEMA ---

The following BigQuery SQL query failed with an error. Fix it.

Original SQL:
{original_sql}

BigQuery Error:
{error_message}

Return ONLY the corrected SQL — no explanation, no markdown fences.

Fixed SQL:"""
        return self._clean(self._call_gemini(prompt))


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from schema_loader import SchemaLoader

    loader = SchemaLoader()
    schema = loader.format_for_prompt()
    agent  = SQLAgent()

    question = "How many trips were taken each month in 2022?"
    sql = agent.generate_sql(question, schema)
    print(f"Question: {question}")
    print(f"SQL:\n{sql}")
