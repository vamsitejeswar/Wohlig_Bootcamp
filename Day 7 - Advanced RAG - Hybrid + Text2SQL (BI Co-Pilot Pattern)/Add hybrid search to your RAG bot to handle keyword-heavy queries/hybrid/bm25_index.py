"""
bm25_index.py
Loads chunk text from GCS, builds a BM25 keyword index.
"""

import json
import os
import re
from dotenv import load_dotenv
from pathlib import Path
from google.cloud import storage
from rank_bm25 import BM25Okapi

load_dotenv(Path(__file__).parents[3] /
    "Day 6 - RAG with Grounding + Eval (Production-Grade)" /
    "Build a RAG chatbot that cites every claim - exactly the pattern behind Meesho Memory and Apollo content search" /
    "rag_bot" / ".env")

GCS_BUCKET = "wohlig-rag-pipeline-bucket"
GCS_BLOB   = "vectors/chunks_metadata.json"


def tokenize(text):
    return re.sub(r"[^\w\s]", " ", text.lower()).split()


class BM25Index:
    def __init__(self):
        # Load chunk texts from GCS
        project = os.getenv("PROJECT_ID", "wohlig")
        client  = storage.Client(project=project)
        blob    = client.bucket(GCS_BUCKET).blob(GCS_BLOB)
        chunks  = json.loads(blob.download_as_text())
        print(f"[BM25] Loaded {len(chunks)} chunks from GCS")

        # Deduplicate — chunk_number restarts per page in Day-5 ingest,
        # so same ID can appear multiple times. Keep last (matches dense retriever).
        seen = {}
        for c in chunks:
            cid = f"{c['doc_id']}_{c['chunk_number']}"
            seen[cid] = c
        chunks = list(seen.values())
        print(f"[BM25] {len(chunks)} unique chunks after dedup")

        self.ids    = [f"{c['doc_id']}_{c['chunk_number']}" for c in chunks]
        self.chunks = chunks
        self.bm25   = BM25Okapi([tokenize(c["text"]) for c in chunks])

    def search(self, query, top_k=20):
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self.ids, scores), key=lambda x: x[1], reverse=True)
        return [cid for cid, _ in ranked[:top_k]]

    def get_text(self, chunk_id):
        if chunk_id in self.ids:
            return self.chunks[self.ids.index(chunk_id)]["text"]
        return None


if __name__ == "__main__":
    idx = BM25Index()
    q   = input("Query: ")
    for cid in idx.search(q, top_k=5):
        print(f"  {cid}: {idx.get_text(cid)[:120]}...")
