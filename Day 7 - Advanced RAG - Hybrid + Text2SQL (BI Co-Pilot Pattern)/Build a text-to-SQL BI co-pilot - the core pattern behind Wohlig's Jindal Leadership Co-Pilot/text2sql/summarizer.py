"""
summarizer.py
-------------
Takes a pandas DataFrame (query result) and a natural-language question,
then returns a 2-3 sentence plain-English summary using Gemini.

Exports:
  - Summarizer  class  (.summarize(question, df) → str)
"""

import os
import pandas as pd
from google import genai
from dotenv import load_dotenv

load_dotenv()

_MAX_DISPLAY_ROWS = 20  # cap rows sent to Gemini to stay within token limits


class Summarizer:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=os.getenv("PROJECT_ID", "wohlig"),
            location=os.getenv("LOCATION", "us-central1"),
        )

    def summarize(self, question: str, df: pd.DataFrame) -> str:
        """
        Generate a 2-3 sentence natural-language summary of a query result.

        Args:
            question: The original NL question the user asked.
            df:       The result DataFrame returned by BigQuery.

        Returns:
            A plain-English summary string. Never mentions SQL or technical details.
        """
        if df.empty:
            return "The query returned no results."

        row_count = len(df)
        col_names = list(df.columns)
        sample    = df.head(_MAX_DISPLAY_ROWS).to_string(index=False)

        prompt = f"""You are a data analyst presenting findings to a business stakeholder.
                    A user asked: "{question}"
                    The query returned {row_count} row(s) with columns: {col_names}
                    Results (first {min(_MAX_DISPLAY_ROWS, row_count)} rows):
                    {sample}
                    Write a 2-3 sentence plain English summary of what the data shows.
                    - Be specific: mention actual numbers, top values, or clear trends.
                    - Do NOT mention SQL, databases, queries, or technical terms.
                    - Write as if explaining to a manager who just wants the key insight."""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return (response.text or "").strip()


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    summarizer = Summarizer()

    sample_df = pd.DataFrame({
        "month":       ["2022-01", "2022-02", "2022-03"],
        "trip_count":  [120000, 98000, 145000],
    })
    question = "How many trips happened each month in 2022?"
    print(summarizer.summarize(question, sample_df))
