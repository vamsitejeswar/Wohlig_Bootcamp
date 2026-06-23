# Production RAG: Lift Report

> Judge: Gemini Flash scoring faithfulness / relevancy / precision / recall

## 1. Aggregate Scores

| Metric | Naive | +Reranker | +Contextual | +Both |
|--------|-------|-----------|-------------|-------|
| Faithfulness | 0.4667 | 0.4500 | 0.2000 | 0.3333 |
| Answer Relevance | 0.1767 | 0.0833 | 0.0833 | 0.0500 |
| Context Precision | 0.2333 | 0.1133 | 0.0967 | 0.0767 |
| Context Recall | 0.1350 | 0.0683 | 0.1017 | 0.1400 |
| Overall Average | 0.2529 | 0.1787 | 0.1204 | 0.1500 |

## 2. Lift vs Naive

| Metric | +Reranker | +Contextual | +Both |
|--------|-----------|-------------|-------|
| Faithfulness | -3.6% | -57.1% | -28.6% |
| Answer Relevance | -52.8% | -52.8% | -71.7% |
| Context Precision | -51.4% | -58.6% | -67.1% |
| Context Recall | -49.4% | -24.7% | +3.7% |
| Overall Average | -29.3% | -52.4% | -40.7% |

## 3. Recommendation

**Ship `reranked`** — -29.3% overall lift.

- Reranker   : -29.3% — no prep, tiny per-query cost
- Contextual : -52.4% — one-time prep, zero per-query cost
- Both       : -40.7% — compounds both gains