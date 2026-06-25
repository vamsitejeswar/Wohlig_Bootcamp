# BI Co-Pilot — 10 Test Queries

## BigQuery-only (3 queries)
These require only `structured_data_agent`. The answer lives entirely in the nyc_taxi table.

| ID  | Query | Why structured only |
|-----|-------|---------------------|
| Q01 | How many trips happened in each month of last year? | Pure GROUP BY aggregation |
| Q02 | Which vendor had the highest average fare in Q3? | AVG + date filter + ranking |
| Q03 | Show the top 5 pickup hours by trip count. | EXTRACT(HOUR) + ORDER BY LIMIT |

## RAG-only (3 queries)
These require only `unstructured_data_agent`. The answer lives in documents/PDFs.

| ID  | Query | Why unstructured only |
|-----|-------|-----------------------|
| Q04 | What is the data retention policy for trip records? | Policy question — PDF only |
| Q05 | Explain the process for disputing a fare charge. | Procedural question — doc only |
| Q06 | What are the SLA targets for data pipeline uptime? | SLA definition — contract/doc |

## Both agents needed (4 queries)
These mix a data question with a policy/standard context. `structured_data_agent`
runs first to get the number, then `unstructured_data_agent` gets the standard to compare against.

| ID  | Query | Why both |
|-----|-------|----------|
| Q07 | Did last month's average trip duration exceed the service standard? | BQ for avg duration + doc for the service standard |
| Q08 | How many refund requests were filed, and what is the refund policy? | BQ for count + doc for the policy text |
| Q09 | Compare peak-hour trip counts against the capacity guidelines. | BQ for trip counts + doc for capacity rule |
| Q10 | Which payment type has grown most, and are there compliance requirements for it? | BQ for growth trend + doc for compliance docs |

## Routing signals used in the orchestrator prompt

**→ structured:** "how many", "total", "average", "count", "top N", "trend", "grew", "revenue", "fare", "by month", "per hour"

**→ unstructured:** "policy", "SLA", "procedure", "rule", "guideline", "compliance", "requirement", "definition", "process for"

**→ both:** "exceed", "violate", "comply", "vs", "against", "below target", "meets the standard"
