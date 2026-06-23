"""
rrf.py
Reciprocal Rank Fusion — merges two ranked lists.
score(chunk) = 1/(60 + rank_dense) + 1/(60 + rank_bm25)
"""


def rrf_merge(dense_ids, bm25_ids, top_k=5, k=60):
    scores = {}
    for rank, cid in enumerate(dense_ids, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    for rank, cid in enumerate(bm25_ids, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda x: scores[x], reverse=True)[:top_k]


if __name__ == "__main__":
    dense = ["A", "B", "C"]
    bm25  = ["C", "D", "A"]
    print("Merged:", rrf_merge(dense, bm25))
