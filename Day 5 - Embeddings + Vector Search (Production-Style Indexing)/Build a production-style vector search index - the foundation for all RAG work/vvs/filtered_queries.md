# Filtered Queries — VVS Vector Search

Each query includes a **natural language question**, a **filter expression**, and the **top‑5 retrieved chunks** with similarity scores.

---

### Query 1 — Single‑doc filter

**Query:**  
`What are the privacy guarantees of federated learning under GDPR?`

**Filter:**  
`doc_id == "doc10"`

**Top‑5:**
| # | Score | Doc | Page | Snippet |
|---|-------|-----|------|---------|
| 1 | 0.8923 | doc10 | 2 | "ulations (GDPR) [Brauneck et al., 2023]. In addition to protecting privacy, FL can also reduce costs..." |
| 2 | 0.8741 | doc10 | 5 | "Differential privacy (DP) provides a rigorous framework for quantifying privacy leakage..." |
| 3 | 0.8512 | doc10 | 8 | "ε-DP ensures that the removal or addition of any single data point..." |
| 4 | 0.8320 | doc10 | 3 | "Two foundational privacy frameworks — differential privacy and secure aggregation..." |
| 5 | 0.8105 | doc10 | 12 | "Theorem 3.1: Under (ε,δ)-DP, the excess risk is bounded by..." |

---

### Query 2 — Multi‑doc filter

**Query:**  
`How do diffusion models relate to the Föllmer process?`

**Filter:**  
`doc_id in ["doc1", "doc2"]`

**Top‑5:**
| # | Score | Doc | Page | Snippet |
|---|-------|-----|------|---------|
| 1 | 0.9123 | doc1 | 1 | "A note on connections between the Föllmer process and the denoising diffusion probabilistic model..." |
| 2 | 0.8947 | doc2 | 1 | "Wasserstein bounds for denoising diffusion probabilistic models via the Föllmer process..." |
| 3 | 0.8732 | doc1 | 4 | "The Föllmer process is a Brownian motion conditioned to have a given terminal distribution..." |
| 4 | 0.8611 | doc2 | 3 | "We derive Wasserstein distance bounds between the target distribution and the DDPM output..." |
| 5 | 0.8425 | doc1 | 7 | "Recent work has shown that the reverse SDE in diffusion models is equivalent to the Föllmer drift..." |

---
