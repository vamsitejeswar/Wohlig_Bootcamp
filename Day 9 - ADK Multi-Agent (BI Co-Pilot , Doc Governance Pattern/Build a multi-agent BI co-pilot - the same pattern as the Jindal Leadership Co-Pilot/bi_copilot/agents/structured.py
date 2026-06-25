import importlib.util
import os
import sys

from google.adk.agents import LlmAgent
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def _import_file(module_name, relative_path):
    abs_path = os.path.normpath(os.path.join(os.path.dirname(__file__), relative_path))
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


_d7 = "../../../../Day 7 - Advanced RAG - Hybrid + Text2SQL (BI Co-Pilot Pattern)/Build a text-to-SQL BI co-pilot - the core pattern behind Wohlig's Jindal Leadership Co-Pilot/text2sql"

_schema_mod    = _import_file("schema_loader", f"{_d7}/schema_loader.py")
_agent_mod     = _import_file("agent",         f"{_d7}/agent.py")
_validator_mod = _import_file("sql_validator", f"{_d7}/sql_validator.py")
_summarizer_mod = _import_file("summarizer",   f"{_d7}/summarizer.py")

SQLAgent     = _agent_mod.SQLAgent
SchemaLoader = _schema_mod.SchemaLoader
SQLValidator = _validator_mod.SQLValidator
Summarizer   = _summarizer_mod.Summarizer

# Initialise once
_sql_agent  = SQLAgent()
_schema     = SchemaLoader().format_for_prompt()
_validator  = SQLValidator(_sql_agent)
_summarizer = Summarizer()
_bq_client  = bigquery.Client(project=os.getenv("PROJECT_ID", "wohlig"))


def query_bigquery(question: str) -> str:
    """
    Convert a natural-language question into BigQuery SQL, execute it,
    and return a plain-English summary of the results.

    Use this tool for any question requiring counts, totals, averages,
    trends, rankings, or other numerical data from tables.
    """
    sql        = _sql_agent.generate_sql(question, _schema)
    validation = _validator.validate_with_retry(sql, _schema)

    if not validation["is_valid"]:
        return f"SQL generation failed after {validation['attempts']} attempts. Error: {validation['error']}"

    try:
        df      = _bq_client.query(validation["sql"]).result().to_dataframe()
        summary = _summarizer.summarize(question, df)
        return f"{summary}\n\n[Rows returned: {len(df)} | SQL auto-corrected: {validation['was_corrected']}]"
    except Exception as exc:
        return f"Query execution failed: {exc}"


structured_data_agent = LlmAgent(
    name="structured_data_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Structured Data specialist for a BI Co-Pilot system.\n\n"
        "Your job is to answer questions that require querying tabular data from BigQuery.\n"
        "You have access to NYC taxi trip data and other project tables.\n\n"
        "Use query_bigquery() with the user's exact question as-is.\n"
        "Return the data summary clearly, including the row count.\n"
        "If the query fails, report the error message and explain what went wrong."
    ),
    tools=[query_bigquery],
)
