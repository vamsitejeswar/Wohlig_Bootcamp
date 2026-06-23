"""
contextualizer.py
-----------------
Implements Anthropic's "Contextual Retrieval" technique.

  PREP (one-time, run as __main__):
    1. Load every chunk from GCS metadata (same source as retriever.py).
    2. For each chunk, ask Gemini Flash to write ONE situating sentence
       (e.g. "This chunk is from the introduction of doc2 and defines the
       Föllmer drift in the context of stochastic optimal control.").
    3. Prepend that sentence to the chunk text.
    4. Re-embed the augmented text with gemini-embedding-001.
    5. Persist:
         chunks_metadata_contextual.json  — list of chunk dicts (text updated)
         contextual_embeddings.npy        — float32 array, shape [N, 768]

  RETRIEVAL (used by run_eval.py):
    ContextualRetriever.retrieve(question, top_k)
      → embeds question locally, cosine-sim over saved embeddings, top-k.

Why this helps:
  Plain chunks are often pronoun-heavy or lack surrounding context, so the
  embedding misses the right semantic cluster.  Adding a precise anchor
  sentence makes the chunk's embedding far more discriminative.

Cost:
  Prep is one-time: N Gemini Flash calls (cheap) + N embedding calls.
  Retrieval is zero extra API calls — it's pure local numpy math.
"""

import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.cloud import storage

# ── Paths ─────────────────────────────────────────────────────────────────────
RAG_BOT_DIR = (
    Path(__file__).resolve().parents[2]
    / "Build a RAG chatbot that cites every claim - exactly the pattern behind Meesho Memory and Apollo content search"
    / "rag_bot"
)
PROD_DIR = Path(__file__).resolve().parent

load_dotenv(RAG_BOT_DIR / ".env")


def _load_module(name: str, filepath: Path):
    # Reuse cached module if already loaded — avoids duplicate class objects.
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# Output files (written by prep, read by ContextualRetriever)
CONTEXTUAL_META_PATH = PROD_DIR / "chunks_metadata_contextual.json"
CONTEXTUAL_EMB_PATH  = PROD_DIR / "contextual_embeddings.npy"

# GCS source (same as retriever.py)
GCS_BUCKET        = "wohlig-rag-pipeline-bucket"
GCS_METADATA_BLOB = "vectors/chunks_metadata.json"

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION   = os.getenv("LOCATION", "us-central1")


# ── Context generation ────────────────────────────────────────────────────────

_CONTEXT_PROMPT = """\
You are preparing a document chunk for semantic search indexing.

Document ID : {doc_id}
Page        : {page}
Chunk #     : {chunk_number}

Chunk text:
\"\"\"{text}\"\"\"

Write EXACTLY ONE sentence (≤ 30 words) that situates this chunk within its
document — name what document/section it comes from and what topic it covers.
Do NOT quote or paraphrase the chunk; just situate it.
Output only the sentence, no labels or quotes."""


def _generate_context(client: genai.Client, chunk: dict) -> str:
    """Call Gemini Flash to produce a 1-line situating sentence."""
    prompt = _CONTEXT_PROMPT.format(
        doc_id=chunk.get("doc_id", "unknown"),
        page=chunk.get("page_number", chunk.get("page", "?")),
        chunk_number=chunk.get("chunk_number", "?"),
        text=chunk.get("text", "")[:1000],  # guard against huge chunks
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return (response.text or "").strip()


# ── Embedding helper ──────────────────────────────────────────────────────────

def _embed_batch(client: genai.Client, texts: list[str]) -> list[list[float]]:
    """Embed a list of texts; returns list of 768-dim float vectors."""
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config={"output_dimensionality": 768},
    )
    return [e.values for e in response.embeddings]


# ── Corpus prep (run once) ────────────────────────────────────────────────────

def run_contextualizer(embed_batch_size: int = 10, max_chunks: int = 100):
    """
    One-time script that contextualises chunks and saves outputs.
    Safe to re-run — skips if output files already exist.

    Args:
        max_chunks: how many chunks to process (default 100 out of 426).
    """
    if CONTEXTUAL_META_PATH.exists() and CONTEXTUAL_EMB_PATH.exists():
        print("Contextual files already exist — skipping prep.")
        print(f"  {CONTEXTUAL_META_PATH}")
        print(f"  {CONTEXTUAL_EMB_PATH}")
        return

    # 1. Load raw chunks from GCS, then cap at max_chunks
    print("Loading chunks from GCS…")
    gcs = storage.Client(project=PROJECT_ID)
    all_chunks: list[dict] = json.loads(
        gcs.bucket(GCS_BUCKET).blob(GCS_METADATA_BLOB).download_as_text()
    )
    raw_chunks = all_chunks[:max_chunks]
    print(f"  Loaded {len(all_chunks)} chunks total — using first {len(raw_chunks)}.")

    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    # 2. Generate a 1-line context for each chunk
    print("\nGenerating context sentences (1 Gemini call per chunk)…")
    contextual_chunks = []
    for i, chunk in enumerate(raw_chunks, 1):
        ctx = _generate_context(client, chunk)
        augmented_text = f"{ctx}\n\n{chunk['text']}"

        updated = dict(chunk)  # shallow copy; don't mutate original
        updated["context_sentence"] = ctx
        updated["text"] = augmented_text
        contextual_chunks.append(updated)

        if i % 10 == 0 or i == len(raw_chunks):
            print(f"  [{i}/{len(raw_chunks)}] done")
        # Respect Gemini rate limits (60 RPM on Flash)
        time.sleep(1.1)

    # 3. Save contextual metadata
    CONTEXTUAL_META_PATH.write_text(
        json.dumps(contextual_chunks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nSaved {CONTEXTUAL_META_PATH.name}")

    # 4. Embed all contextualised texts (batched to respect API limits)
    print("\nEmbedding contextualised chunks…")
    texts = [c["text"] for c in contextual_chunks]
    all_embeddings: list[list[float]] = []

    for start in range(0, len(texts), embed_batch_size):
        batch = texts[start : start + embed_batch_size]
        vecs  = _embed_batch(client, batch)
        all_embeddings.extend(vecs)
        print(f"  Embedded {min(start + embed_batch_size, len(texts))}/{len(texts)}")
        time.sleep(0.5)

    # 5. Persist embeddings as numpy array (float32 saves ~half the disk space)
    emb_array = np.array(all_embeddings, dtype=np.float32)
    np.save(str(CONTEXTUAL_EMB_PATH), emb_array)
    print(f"Saved {CONTEXTUAL_EMB_PATH.name}  shape={emb_array.shape}")


# ── ContextualRetriever ───────────────────────────────────────────────────────

class ContextualRetriever:
    """
    Drop-in for Retriever.  Uses the locally saved contextual embeddings
    instead of the Vertex AI Vector Search index.

    retrieve(question, top_k) → list[RetrievedChunk]

    No extra API calls at retrieval time — pure numpy cosine similarity.
    Cost is one embedding call per question (same as naive retriever).
    """

    def __init__(self):
        if not CONTEXTUAL_META_PATH.exists() or not CONTEXTUAL_EMB_PATH.exists():
            raise FileNotFoundError(
                "Contextual files not found. Run:\n"
                "  python contextualizer.py\n"
                "to generate them first."
            )

        # Resolve RetrievedChunk here — reuses whichever module instance is
        # already live in sys.modules (loaded by run_eval.py or reranker.py),
        # so all three files share the same class object.
        self._RetrievedChunk = _load_module(
            "retriever", RAG_BOT_DIR / "retriever.py"
        ).RetrievedChunk

        self._chunks: list[dict] = json.loads(
            CONTEXTUAL_META_PATH.read_text(encoding="utf-8")
        )
        # shape [N, 768], already L2-normalised for cosine sim
        raw = np.load(str(CONTEXTUAL_EMB_PATH))
        norms = np.linalg.norm(raw, axis=1, keepdims=True)
        self._embeddings = raw / np.clip(norms, 1e-9, None)  # unit vectors

        self._client = genai.Client(
            vertexai=True, project=PROJECT_ID, location=LOCATION
        )

    def retrieve(self, question: str, top_k: int = 5) -> list:
        # Embed the question
        resp = self._client.models.embed_content(
            model="gemini-embedding-001",
            contents=question,
            config={"output_dimensionality": 768},
        )
        q_vec = np.array(resp.embeddings[0].values, dtype=np.float32)
        q_vec /= max(np.linalg.norm(q_vec), 1e-9)

        # Cosine similarity = dot product of unit vectors
        scores = self._embeddings @ q_vec  # shape [N]
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            c = self._chunks[idx]
            results.append(
                self._RetrievedChunk(
                    doc_id=       c.get("doc_id", ""),
                    page=         c.get("page_number", c.get("page", 0)),
                    chunk_number= c.get("chunk_number", 0),
                    text=         c["text"],
                    score=        round(float(scores[idx]), 4),
                    source=       c.get("source", c.get("doc_id", "")),
                )
            )
        return results


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_contextualizer()
    print("\nDone. You can now run run_eval.py.")
