# BI Co-Pilot — Architecture

## Agent Topology

```
User Question
      │
      ▼
┌─────────────────────────────────────────────┐
│          bi_copilot_orchestrator            │
│          LlmAgent · gemini-2.5-flash        │
│                                             │
│  Reads question → decides routing →         │
│  delegates to one or both sub-agents →      │
│  synthesises final answer                   │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐     ┌──────────────────────┐
│  structured_  │     │  unstructured_data_  │
│  data_agent   │     │  agent               │
│               │     │                      │
│  LlmAgent +   │     │  LlmAgent +          │
│  query_       │     │  search_documents()  │
│  bigquery()   │     │                      │
└──────┬────────┘     └──────────┬───────────┘
       │                         │
       ▼                         ▼
  BigQuery                Vertex AI
  (nyc_taxi table)        Vector Search
  text2SQL pipeline       + Gemini RAG
  (Day 7)                 (Day 6)
```

## Delegation Logic

| Question type            | Agent(s) called                              |
|--------------------------|----------------------------------------------|
| Numbers / trends / data  | `structured_data_agent` only                 |
| Policy / procedure / SLA | `unstructured_data_agent` only               |
| Data vs standard         | `structured_data_agent` → then `unstructured_data_agent` |

The orchestrator uses keyword signals in the user's question to decide:
- "how many", "average", "top N", "trend" → structured
- "policy", "SLA", "procedure", "rule", "compliance" → unstructured
- "exceed", "violate", "comply", "vs", "against" → both (in that order)

## Sub-Agent Details

### structured_data_agent
- **Tool**: `query_bigquery(question: str) → str`
- **Pipeline**: NL question → SQLAgent (Gemini) → dry-run validation → BigQuery execute → Summarizer (Gemini)
- **Source**: Day 7 `text2sql/` (SQLAgent, SQLValidator, SchemaLoader, Summarizer)
- **Dataset**: `wohlig.big_query_dataset.nyc_taxi`

### unstructured_data_agent
- **Tool**: `search_documents(question: str) → str`
- **Pipeline**: question → embedding (gemini-embedding-001) → Vertex AI Vector Search → Gemini generation with citations
- **Source**: Day 6 `rag_bot/` (Retriever, Generator)
- **Index**: `INDEX_ENDPOINT_ID=4372390506781474816`

## How AgentTool Works

`AgentTool(agent=sub_agent)` makes the orchestrator treat each sub-agent like
a regular function call. The orchestrator passes the question as a string, the
sub-agent runs its full pipeline, and returns a string result. The orchestrator
then synthesises both results into the final answer.

This is the same pattern used in the Jindal Leadership Co-Pilot: one orchestrator,
multiple domain specialists, clean separation of concerns.
