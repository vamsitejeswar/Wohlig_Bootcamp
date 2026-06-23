"""
main.py
-------
Orchestrates the full text-to-SQL pipeline for 15 test queries:

  1. Load BigQuery table schema → format for prompt
  2. Generate SQL (Gemini via agent.py)
  3. Validate SQL (BQ dry-run + retry via sql_validator.py)
  4. Execute query → pandas DataFrame
  5. Summarize result (Gemini via summarizer.py)
  6. Pick + render chart (chart_picker.py)
  7. Save all artifacts to test_results/<query_id>/

Run: python main.py
"""

import json
import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

from agent         import SQLAgent
from chart_picker  import generate_chart, pick_chart_type
from schema_loader import SchemaLoader
from sql_validator import SQLValidator
from summarizer    import Summarizer

load_dotenv()

PROJECT_ID  = os.getenv("PROJECT_ID", "wohlig")
RESULTS_DIR = Path(__file__).parent / "test_results"

# ── 15 test queries ──────────────────────────────────────────────────────────
# Grouped by difficulty (easy → medium → hard).
# Phrased in natural language — the agent resolves column names from schema.
TEST_QUERIES = [
    # EASY — single-table aggregations (no filtering, no date logic)
    ("Q01_easy",   "How many total trips are in the dataset?"),
    ("Q02_easy",   "What is the average trip distance across all trips?"),
    ("Q03_easy",   "What is the maximum fare amount recorded in the dataset?"),
    ("Q04_easy",   "How many trips were completed by each vendor?"),
    ("Q05_easy",   "What is the total number of passengers carried across all trips?"),

    # MEDIUM — filtering, date functions, grouping, subqueries
    ("Q06_medium", "How many trips happened each month? Order by month."),
    ("Q07_medium", "What is the average tip amount grouped by payment type?"),
    ("Q08_medium", "Which hour of the day has the highest number of trip pickups?"),
    ("Q09_medium", "What is the average trip distance for trips with more than 2 passengers?"),
    ("Q10_medium", "What are the top 5 trip distances (rounded to nearest mile) by frequency?"),

    # HARD — window functions, CTEs, rolling aggregations
    ("Q11_hard",   "Show the running total (cumulative count) of trips by month."),
    ("Q12_hard",   "For each hour of the day, what percentage of trips had a trip distance above 5 miles?"),
    ("Q13_hard",   "What is the average trip duration in minutes grouped by hour of pickup?"),
    ("Q14_hard",   "Using a window function, rank each vendor by their total trip count per month."),
    ("Q15_hard",   "What is the 3-day rolling average of daily trip counts? Show date and rolling average."),
]


# ── Pipeline helpers ─────────────────────────────────────────────────────────

def execute_query(bq_client: bigquery.Client, sql: str) -> pd.DataFrame:
    return bq_client.query(sql).result().to_dataframe()


def run_pipeline(
    question:   str,
    query_id:   str,
    schema:     str,
    agent:      SQLAgent,
    validator:  SQLValidator,
    summarizer: Summarizer,
    bq_client:  bigquery.Client,
) -> dict:
    """Run the full 5-step pipeline for one NL question."""

    result_dir = RESULTS_DIR / query_id
    result_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*65}")
    print(f"[{query_id}] {question}")
    print("=" * 65)

    # Save the question text
    (result_dir / "nl_question.txt").write_text(question)

    # ── Step 1: Generate SQL ──────────────────────────────────────────────────
    print("  [1/5] Generating SQL...")
    sql = agent.generate_sql(question, schema)
    print(f"  → {sql[:200].replace(chr(10), ' ')}")

    # ── Step 2: Validate SQL (dry-run + retry) ────────────────────────────────
    print("  [2/5] Validating SQL (dry-run)...")
    validation  = validator.validate_with_retry(sql, schema)
    final_sql   = validation["sql"]
    is_valid    = validation["is_valid"]

    status_tag  = "VALID" if is_valid else "INVALID"
    corrected   = " [CORRECTED]" if validation["was_corrected"] else ""
    print(f"  → {status_tag} | attempts={validation['attempts']}{corrected}")

    (result_dir / "generated_sql.sql").write_text(final_sql)
    (result_dir / "validation_status.json").write_text(
        json.dumps(
            {
                "is_valid":      is_valid,
                "attempts":      validation["attempts"],
                "was_corrected": validation["was_corrected"],
                "error":         validation["error"],
            },
            indent=2,
        )
    )

    if not is_valid:
        print(f"  ✗ FAILED — SQL invalid after {validation['attempts']} attempts.")
        (result_dir / "success.txt").write_text("FAILURE")
        return {
            "query_id": query_id,
            "question": question,
            "success":  False,
            "error":    validation["error"],
        }

    # ── Step 3: Execute query ─────────────────────────────────────────────────
    print("  [3/5] Executing query...")
    try:
        df = execute_query(bq_client, final_sql)
        df.to_csv(result_dir / "result_table.csv", index=False)
        print(f"  → {len(df)} rows × {len(df.columns)} columns")
    except Exception as exc:
        print(f"  ✗ FAILED — Execution error: {exc}")
        (result_dir / "success.txt").write_text("FAILURE")
        return {"query_id": query_id, "question": question, "success": False, "error": str(exc)}

    # ── Step 4: Summarize ─────────────────────────────────────────────────────
    print("  [4/5] Summarizing...")
    summary = summarizer.summarize(question, df)
    (result_dir / "nl_summary.txt").write_text(summary)
    print(f"  → {summary[:160].replace(chr(10), ' ')}...")

    # ── Step 5: Chart ─────────────────────────────────────────────────────────
    print("  [5/5] Picking chart...")
    chart_type  = pick_chart_type(df)
    chart_path  = str(result_dir / "chart.png")
    chart_saved = generate_chart(df, chart_type, question[:60], chart_path)
    print(f"  → type={chart_type} | saved={chart_saved}")

    (result_dir / "chart_type.txt").write_text(chart_type)
    (result_dir / "success.txt").write_text("SUCCESS")

    return {
        "query_id":      query_id,
        "question":      question,
        "success":       True,
        "rows":          len(df),
        "chart_type":    chart_type,
        "was_corrected": validation["was_corrected"],
        "summary":       summary,
    }


# ── Main entry point ─────────────────────────────────────────────────────────

def main():
    print("Initializing components...")
    loader     = SchemaLoader()
    agent      = SQLAgent()
    validator  = SQLValidator(agent)
    summarizer = Summarizer()
    bq_client  = bigquery.Client(project=PROJECT_ID)

    print("\nLoading schema from BigQuery...")
    schema = loader.format_for_prompt()
    print(schema)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_results = []

    for query_id, question in TEST_QUERIES:
        result = run_pipeline(
            question, query_id, schema,
            agent, validator, summarizer, bq_client,
        )
        all_results.append(result)
        time.sleep(0.5)  # small pause to stay within Gemini rate limits

    # ── Final report ──────────────────────────────────────────────────────────
    successes = [r for r in all_results if r["success"]]
    failures  = [r for r in all_results if not r["success"]]
    corrected = [r for r in successes if r.get("was_corrected")]

    print(f"\n{'='*65}")
    print("FINAL REPORT")
    print("=" * 65)
    print(f"Total : {len(all_results)}")
    print(f"Pass  : {len(successes)}  |  Fail : {len(failures)}  |  Auto-corrected : {len(corrected)}")
    print()

    for r in all_results:
        icon = "✓" if r["success"] else "✗"
        fix  = " [FIXED]" if r.get("was_corrected") else ""
        chart = f"  chart={r.get('chart_type','')}" if r["success"] else ""
        print(f"  {icon} {r['query_id']}: {r['question'][:55]}{fix}{chart}")

    # Save JSON summary
    report_path = RESULTS_DIR / "summary_report.json"
    report_path.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"\nFull report → {report_path}")


if __name__ == "__main__":
    main()
