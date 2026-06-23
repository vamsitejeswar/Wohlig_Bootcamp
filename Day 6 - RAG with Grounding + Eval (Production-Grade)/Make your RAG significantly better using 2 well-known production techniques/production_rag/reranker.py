"""
reranker.py
-----------
Wraps the existing Retriever with a two-stage pipeline:
  Stage 1 (ANN):     fetch top-20 candidates by embedding cosine similarity
  Stage 2 (Ranking): call Vertex AI Ranking API to re-score and keep top-5

Why two stages?
  Embedding search is O(1) nearest-neighbor lookup — very fast, but it only
  measures "topic closeness" in vector space, not true answer relevance.
  The Ranking API is a cross-encoder: it reads the question AND each chunk
  together and outputs a relevance score. Much more accurate, but can't scan
  millions of vectors, so we use ANN to narrow the field first.

Vertex AI Ranking API:
  - Package : google-cloud-discoveryengine
  - Model   : semantic-ranker-512@latest  (free tier available)
  - Quota   : ~100 QPS default, 512 tokens per record
  - Cost    : charged per 1 000 records ranked (very cheap)
"""

import importlib.util
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import discoveryengine_v1 as discoveryengine

# ── Resolve paths ─────────────────────────────────────────────────────────────
RAG_BOT_DIR = (
    Path(__file__).resolve().parents[2]
    / "Build a RAG chatbot that cites every claim - exactly the pattern behind Meesho Memory and Apollo content search"
    / "rag_bot"
)
load_dotenv(RAG_BOT_DIR / ".env")


def _load_module(name: str, filepath: Path):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_retriever_mod = _load_module("retriever", RAG_BOT_DIR / "retriever.py")
Retriever      = _retriever_mod.Retriever
RetrievedChunk = _retriever_mod.RetrievedChunk


# ── ReRankingRetriever ────────────────────────────────────────────────────────

class ReRankingRetriever:
    """
    Drop-in replacement for Retriever.

    retrieve(question) fetches `fetch_k` candidates via ANN, then
    calls the Vertex AI Ranking API to reorder and return the top `final_k`.

    Accepts any base retriever that exposes .retrieve(question, top_k=N)
    so it can wrap ContextualRetriever too (the "both" config).
    """

    # Vertex AI Ranking API constants
    _RANKING_CFG = (
        "projects/{project}/locations/global/rankingConfigs/default_ranking_config"
    )
    _MODEL = "semantic-ranker-512@latest"

    def __init__(self, base_retriever=None, fetch_k: int = 20, final_k: int = 5):
        """
        Args:
            base_retriever: any retriever with .retrieve(q, top_k). Defaults
                            to the standard Vertex AI vector Retriever.
            fetch_k: how many candidates to pull from ANN (stage 1).
            final_k: how many to keep after re-ranking (stage 2).
        """
        self.fetch_k = fetch_k
        self.final_k = final_k
        self.project = os.getenv("PROJECT_ID")

        self._base   = base_retriever or Retriever()
        self._ranker = discoveryengine.RankServiceClient()

    # ── Public API ────────────────────────────────────────────────────────────

    def retrieve(self, question: str, top_k: int = None) -> list[RetrievedChunk]:
        """
        Two-stage retrieval:
          1. ANN fetch (fast, high-recall)
          2. Cross-encoder re-rank (slower, high-precision)

        `top_k` overrides final_k when provided — lets the eval harness
        request a different number without changing the object.
        """
        effective_final = top_k if top_k is not None else self.final_k

        # ── Stage 1: ANN ─────────────────────────────────────────────────────
        candidates = self._base.retrieve(question, top_k=self.fetch_k)
        if not candidates:
            return []

        # ── Stage 2: cross-encoder re-rank ───────────────────────────────────
        # Each RankingRecord gets an ID (string index) and up to 512 tokens.
        # The API returns records sorted by relevance score (highest first).
        records = [
            discoveryengine.RankingRecord(
                id=str(i),
                title="",
                content=c.text[:512],  # hard token limit per record
            )
            for i, c in enumerate(candidates)
        ]

        response = self._ranker.rank(
            request=discoveryengine.RankRequest(
                ranking_config=self._RANKING_CFG.format(project=self.project),
                model=self._MODEL,
                top_n=effective_final,
                query=question,
                records=records,
            )
        )

        # Map re-ranked IDs back to original RetrievedChunk objects.
        # Replace the ANN cosine score with the ranker's relevance score.
        id_to_chunk = {str(i): c for i, c in enumerate(candidates)}
        reranked: list[RetrievedChunk] = []
        for rec in response.records:
            chunk = id_to_chunk[rec.id]
            chunk.score = round(rec.score, 4)
            reranked.append(chunk)

        return reranked


# ── Quick smoke-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    rr = ReRankingRetriever(fetch_k=20, final_k=5)
    q  = input("Test question: ")
    results = rr.retrieve(q)

    print(f"\nTop {len(results)} re-ranked chunks:\n")
    for i, c in enumerate(results, 1):
        print(f"[{i}] {c.doc_id} | Page {c.page} | Score {c.score}")
        print(f"    {c.text[:200]}…")
        print()
