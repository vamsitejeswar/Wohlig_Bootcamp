"""
retriever_hybrid.py
Runs dense search (Vertex AI) + BM25, merges via RRF, returns top-5 chunks.
"""

import importlib.util
import sys
from pathlib import Path
from dotenv import load_dotenv

from bm25_index import BM25Index
from rrf import rrf_merge

_HERE = Path(__file__).resolve().parent
RAG_BOT_DIR = (
    _HERE.parents[2]
    / "Day 6 - RAG with Grounding + Eval (Production-Grade)"
    / "Build a RAG chatbot that cites every claim - exactly the pattern behind Meesho Memory and Apollo content search"
    / "rag_bot"
)
load_dotenv(RAG_BOT_DIR / ".env")


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


DenseRetriever = _load("retriever", RAG_BOT_DIR / "retriever.py").Retriever
RetrievedChunk = _load("retriever", RAG_BOT_DIR / "retriever.py").RetrievedChunk


class HybridRetriever:
    def __init__(self):
        self.dense = DenseRetriever()
        self.bm25  = BM25Index()

    def retrieve(self, question, top_k=5):
        # Step 1: Dense search → top 20 from Vertex AI
        dense_results = self.dense.retrieve(question, top_k=20)
        dense_ids     = [f"{c.doc_id}_{c.chunk_number}" for c in dense_results]
        dense_map     = {f"{c.doc_id}_{c.chunk_number}": c for c in dense_results}

        # Step 2: BM25 keyword search → top 20
        bm25_ids = self.bm25.search(question, top_k=20)

        # Step 3: RRF merge → top 5
        merged = rrf_merge(dense_ids, bm25_ids, top_k=top_k)

        # Step 4: Return RetrievedChunk objects
        final = []
        for cid in merged:
            if cid in dense_map:
                final.append(dense_map[cid])
            else:
                text = self.bm25.get_text(cid)
                if text:
                    doc_id, chunk_no = cid.rsplit("_", 1)
                    final.append(RetrievedChunk(
                        doc_id=doc_id, page=0,
                        chunk_number=int(chunk_no),
                        text=text, score=0.0
                    ))
        return final


if __name__ == "__main__":
    r = HybridRetriever()
    q = input("Question: ")
    for i, c in enumerate(r.retrieve(q), 1):
        print(f"[{i}] {c.doc_id} chunk {c.chunk_number}: {c.text[:150]}...")
