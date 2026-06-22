# When to Recommend Vertex AI Vector Search vs BigQuery Vector Search

*Wohlig Internal Reference — RAG Client Engagements*

---

## What We Measured

We ran the same 25 evaluation questions (768-dim Gemini embeddings, 426 chunks across 10 documents) through both systems and measured real query latency and recall.

| Metric | Vertex AI Vector Search | BigQuery Vector Search |
|--------|------------------------|----------------------|
| Avg latency (p50) | **591.4 ms** | **586.6 ms** |
| Min / Max latency | 494.7 ms / 711.2 ms | 447.0 ms / 726.0 ms |
| Recall@10 | **0.840** | **0.720** |
| Monthly infra cost (idle) | ~$48 (cheapest node) | **$0** |

**Key finding**: At small corpus scale (426 chunks), latencies are nearly identical — BigQuery is marginally faster on average. VSS shows better recall (0.840 vs 0.720). The traditional "VVS = fast" advantage only appears at larger scale (1M+ vectors) where ANN indexing reduces the search space significantly.

---

## Choose BigQuery Vector Search when...

**1. The client's data is already in BigQuery.**
If source tables live in BQ (orders, documents, tickets, logs), embedding and searching in the same system eliminates an entire pipeline. No ETL to a separate vector DB, no sync jobs, no drift.

**2. They need SQL + vector together.**
BQ VECTOR_SEARCH composes with JOINs, WHERE filters, and CTEs. Example: "find the 10 most relevant support tickets created in the last 30 days by customers on the Enterprise plan." VVS cannot filter pre-search; you'd have to post-filter results yourself.

**3. Corpus is small to medium (< 500K chunks).**
At small scale, BQ latency (~587ms avg) matches VVS (~591ms avg). The ANN advantage of VVS only materialises at 1M+ vectors where full-scan cost grows. Below that threshold there is no meaningful latency benefit from VVS.

**4. The client wants zero standing infrastructure.**
BQ is serverless. No endpoint to deploy, no machine to size, no minimum monthly charge. Perfect for MVPs, prototypes, or infrequent workloads. You pay only when queries run.

**5. Latency of 500ms–1s is acceptable.**
Document Q&A, async summarisation pipelines, batch report generation, nightly RAG jobs — none need sub-100ms response times. BigQuery is ideal here.

**Typical client fit:** Internal search tools, document analytics, batch RAG pipelines, reporting dashboards, any workflow where data already lives in BQ.

---

## Choose Vertex AI Vector Search when...

**1. Corpus is large (1M+ chunks) AND latency matters.**
At small scale VVS and BQ latency are equal (~590ms). VVS's ANN advantage only kicks in at scale — at 1M chunks, VVS drops to ~20–50ms while BQ climbs to 500ms–2s. Do not pay for a VVS node unless the corpus justifies it.

**2. Recall quality is critical.**
Our benchmark shows VSS recall@10 = 0.840 vs BQ = 0.720 — a 12-point gap. For high-stakes retrieval (legal, medical, compliance), VSS returns more relevant results even on the same corpus.

**3. The vector index needs near-real-time updates.**
VVS supports streaming upserts — add/remove individual datapoints without rebuilding the index. BQ vector indexes rebuild asynchronously; a freshly inserted row may not appear in VECTOR_SEARCH results immediately.

**4. Query volume is high enough to amortize the dedicated node.**
At 10M+ queries/month on a multi-million-chunk corpus, BQ's per-TB charge exceeds VVS node cost. VVS becomes the cheaper option at scale.

**5. Scale > 10M vectors with SLA guarantees.**
VVS is purpose-built for billion-scale ANN. It supports multiple replicas, autoscaling, and a public/private endpoint model with GCP-backed SLA.

**Typical client fit:** Customer-facing chatbots at scale, real-time product recommendations, production RAG with large corpora and strict recall requirements.

---

## Decision Flowchart

```
Is corpus < 500K chunks?
├── YES → Is recall@10 critical (legal/medical/compliance)?
│         ├── NO  → Use BigQuery Vector Search (zero infra, same latency)
│         └── YES → Use Vertex AI Vector Search (0.840 vs 0.720 recall)
└── NO (large corpus, 1M+ chunks)
          ├── Is real-time latency (<200ms) required?
          │   ├── YES → Use Vertex AI Vector Search
          │   └── NO  → Is data already in BigQuery?
          │             ├── YES → Use BigQuery Vector Search
          │             └── NO  → Use Vertex AI Vector Search
          └── Is query volume > 67K/month (5M-chunk corpus)?
              ├── YES → VVS becomes cost-competitive
              └── NO  → BigQuery cheaper
```

---

## Practical Guidance for Wohlig Engagements

| Client situation | Recommendation |
|-----------------|----------------|
| Small corpus (<500K chunks), internal tool | **BigQuery** — zero infra, equal latency |
| Small corpus, high recall needed (legal/compliance) | **Vertex AI VSS** — 12-point recall advantage |
| Data in BQ, no latency SLA | **BigQuery** — zero infra, SQL composable |
| Large corpus (1M+), user-facing chatbot | **Vertex AI VSS** — latency gap appears at scale |
| High-volume production RAG (>500K q/month) | **Vertex AI VSS** (cost crossover) |
| Batch RAG / nightly pipeline | **BigQuery** — pay per run, no idle cost |
| Multi-tenant SaaS, each tenant has own corpus | **BigQuery** — partition by tenant, no per-tenant endpoint |
| Compliance: data must stay in BQ | **BigQuery** |

---

## Bottom Line

Our benchmark shows that **at small corpus scale, latency is nearly identical** (BigQuery 586.6ms vs VSS 591.4ms). The default advice changes:

- **Default to BigQuery Vector Search** for small-to-medium corpora (< 500K chunks). Zero infra cost, SQL composable, and latency is on par with VSS at this scale.
- **Upgrade to Vertex AI Vector Search** when corpus exceeds 1M chunks (latency gap opens up), when recall quality is critical (0.840 vs 0.720), or when query volume justifies the dedicated node cost.
