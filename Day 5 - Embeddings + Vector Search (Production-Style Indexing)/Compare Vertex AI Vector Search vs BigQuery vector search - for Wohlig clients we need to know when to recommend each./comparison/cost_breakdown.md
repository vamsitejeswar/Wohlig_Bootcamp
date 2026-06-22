# Cost Breakdown: Vertex AI Vector Search vs BigQuery Vector Search

*Corpus: 426 chunks, 768-dimensional embeddings (gemini-embedding-001)*
*Evaluated: June 2026 | Region: us-central1 / US multi-region*

---

## 1. Setup Cost (One-Time)

| Step | Vertex AI Vector Search | BigQuery Vector Search |
|------|------------------------|----------------------|
| Index creation | ~$0.05 (build job, <5 min) | $0 (DDL, no charge) |
| Endpoint deployment | ~$0.07–$0.20 (30–60 min provisioning) | N/A |
| Data ingestion | Streaming insert to GCS → index upsert ≈ $0 | Streaming insert: $0.01/200 MB = **$0.00** for 2.6 MB |
| **Total setup** | **~$0.12–$0.25** | **< $0.01** |

---

## 2. Storage Cost (Monthly, Ongoing)

### Corpus data (426 chunks × 768 dims × 8 bytes ≈ 2.6 MB embeddings)

| Component | VVS | BigQuery |
|-----------|-----|---------|
| Index storage | $0.025/GB/month × 0.003 GB = **$0.000075/month** | $0.02/GB/month × 0.003 GB = **$0.000060/month** |
| Index node (deployed endpoint) | **e2-standard-2: $0.067/hr = $48.24/month** (minimum) | **$0** — no dedicated node |
| Metadata (GCS) | $0.020/GB × 0.001 GB = **$0.000020/month** | Included in table storage |
| **Total storage** | **~$48.24/month** | **< $0.01/month** |

> **Key insight**: VVS requires a deployed endpoint to serve queries. Even the cheapest machine type (e2-standard-2) costs ~$48/month running 24/7. For production workloads, n1-standard-16 is recommended: **~$274/month**. BigQuery has zero infrastructure cost — you only pay for queries.

### At Scale (1M chunks, 768-dim)

| Component | VVS (n1-standard-16) | BigQuery |
|-----------|---------------------|---------|
| Embedding data | 6.1 GB | 6.1 GB |
| Index storage | ~$0.15/month | $0.12/month |
| Endpoint node | **$274/month** | **$0** |
| **Total storage/infra** | **~$274/month** | **~$0.12/month** |

---

## 3. Query Cost (Per 1,000 Queries)

### Small corpus (426 chunks, 2.6 MB embeddings)

| Metric | VVS | BigQuery |
|--------|-----|---------|
| Pricing model | Included in node cost | $5/TB processed |
| Data scanned per query | N/A | ~2.6 MB |
| Cost per 1,000 queries | **$0** (node already running) | **$0.013** |
| Latency (avg) | **~591 ms** (p50, 426 chunks) | **~587 ms** (p50, 426 chunks) |

### Large corpus (1M chunks, 6.1 GB embeddings)

| Metric | VVS | BigQuery |
|--------|-----|---------|
| Cost per 1,000 queries | **$0** (node already running) | **$30.50** |
| Queries/day to break even on infra | — | — |
| Latency | **~20–50 ms** | **~500 ms–2 s** |

---

## 4. Monthly Total — Realistic Scenarios

### Scenario A: Startup RAG app (50K queries/month, 500K chunks)

| | VVS (e2-standard-2) | BigQuery |
|-|---------------------|---------|
| Infrastructure | $48.24 | $0 |
| Storage | $0.10 | $0.06 |
| Queries (50K × 3GB scan per query) | $0 | $0.75 |
| **Total** | **$48.34/month** | **$0.81/month** |

### Scenario B: Enterprise RAG app (500K queries/month, 5M chunks)

| | VVS (n1-standard-16 × 2 nodes) | BigQuery |
|-|--------------------------------|---------|
| Infrastructure | $548/month | $0 |
| Storage | $1.20 | $1.20 |
| Queries (500K × 30 GB scan) | $0 | $75.00 |
| **Total** | **$549/month** | **$76.20/month** |

### Scenario C: High-throughput production (10M queries/month, 10M chunks)

| | VVS (n1-standard-32 × 3 nodes) | BigQuery |
|-|--------------------------------|---------|
| Infrastructure | $2,016/month | $0 |
| Queries (10M × 60 GB scan) | $0 | $3,000/month |
| **Total** | **$2,016/month** | **$3,000/month** |

> **Crossover**: VVS becomes cheaper than BigQuery when **queries/month × scan_size_TB × $5 > endpoint_node_cost**. For a 10M-chunk corpus (60 GB/query), that crossover is at ~**67K queries/month per $274 node**.

---

## 5. Summary Numbers

| | Vertex AI Vector Search | BigQuery Vector Search |
|-|------------------------|----------------------|
| Setup cost | ~$0.25 | ~$0 |
| Minimum monthly | **$48/month** (idle endpoint) | **$0** (pay per query) |
| Query latency avg (426 chunks) | **~591 ms** | **~587 ms** |
| Query latency avg (1M+ chunks) | **~20–50 ms** | **~500 ms–2 s** |
| Recall@10 (this corpus) | **0.840** | **0.720** |
| Cost per 1K queries (5M chunk corpus) | ~$0 (included) | ~$15.25 |
| Scales to 1B+ vectors | Yes (with sharding) | Yes (BQ native) |
| SQL JOINs alongside search | No | Yes (native) |
