"""
retriever.py
------------
Step 1 of RAG: Take a question, search the Vertex AI Vector Index,
return the top-k matching chunks.

Exports:
  - RetrievedChunk   dataclass  (used by app.py and generator.py)
  - Retriever        class      (.retrieve(question) → list[RetrievedChunk])
"""

import json
import os
from dataclasses import dataclass, field

from google import genai
from google.cloud import aiplatform, storage
from dotenv import load_dotenv

load_dotenv()


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class RetrievedChunk:
    doc_id:       str
    page:         int
    chunk_number: int
    text:         str
    score:        float
    source:       str = ""   # filename, e.g. "doc3.pdf"


# ── Retriever class ───────────────────────────────────────────────────────────

class Retriever:
    """
    Wraps Vertex AI Vector Search + GCS metadata into one simple .retrieve() call.
    Metadata is loaded once and cached for the lifetime of this object.
    """

    def __init__(self):
        self.project_id        = os.getenv("PROJECT_ID")
        self.location          = os.getenv("LOCATION", "us-central1")
        self.index_endpoint_id = os.getenv("INDEX_ENDPOINT_ID")
        self.deployed_index_id = os.getenv("DEPLOYED_INDEX_ID")
        self.gcs_bucket        = "wohlig-rag-pipeline-bucket"
        self.gcs_metadata_blob = "vectors/chunks_metadata.json"

        # Initialize GCP clients
        self.genai_client = genai.Client(
            vertexai=True, project=self.project_id, location=self.location
        )
        aiplatform.init(project=self.project_id, location=self.location)
        self.gcs_client = storage.Client(project=self.project_id)

        # Metadata cache — loaded on first .retrieve() call
        self._metadata: dict | None = None

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _load_metadata(self) -> dict:
        """
        Load chunk metadata into a lookup dict.
        Checks for a local file first (written by file-upload flow),
        then falls back to GCS (Day-5 index).
        """
        if self._metadata is not None:
            return self._metadata

        local_path = os.environ.get("CHUNK_METADATA_PATH", "chunk_metadata.json")

        if os.path.exists(local_path):
            # Local file format written by app.py's upload handler:
            # { "doc_id::page": { "text": ..., "source": ..., "page": ... } }
            print(f"Loading metadata from local file: {local_path}")
            with open(local_path, encoding="utf-8") as f:
                self._metadata = json.load(f)
        else:
            # GCS format from Day-5 ingest:
            # [ { "doc_id": ..., "page_number": ..., "chunk_number": ..., "text": ... } ]
            print("Loading metadata from GCS...")
            blob = self.gcs_client.bucket(self.gcs_bucket).blob(self.gcs_metadata_blob)
            all_chunks = json.loads(blob.download_as_text())
            # Build lookup: "{doc_id}_{chunk_number}" → chunk dict
            self._metadata = {
                f"{c['doc_id']}_{c['chunk_number']}": c
                for c in all_chunks
            }
            print(f"Cached {len(self._metadata)} chunks from GCS.")

        return self._metadata

    # ── Public API ────────────────────────────────────────────────────────────

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievedChunk]:
        """
        Embed the question, search the Vertex AI index, return top-k chunks.
        """

        # Step 1: Embed the question (same model + dimensions as ingest time)
        embed_response = self.genai_client.models.embed_content(
            model="gemini-embedding-001",
            contents=question,
            config={"output_dimensionality": 768}
        )
        question_vector = embed_response.embeddings[0].values

        # Step 2: Search the Vertex AI Vector index
        index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=self.index_endpoint_id
        )
        results = index_endpoint.find_neighbors(
            deployed_index_id=self.deployed_index_id,
            queries=[question_vector],
            num_neighbors=top_k
        )

        if not results:
            return []

        # Step 3: Map each result ID back to its text + metadata
        metadata = self._load_metadata()
        chunks = []

        for neighbor in results[0]:
            info = metadata.get(neighbor.id)
            if info:
                chunks.append(RetrievedChunk(
                    doc_id=       info.get("doc_id", neighbor.id),
                    page=         info.get("page_number", info.get("page", 0)),
                    chunk_number= info.get("chunk_number", 0),
                    text=         info.get("text", ""),
                    score=        round(neighbor.distance, 4),
                    source=       info.get("source", info.get("doc_id", ""))
                ))

        return chunks


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    retriever = Retriever()
    question = input("Enter a test question: ")
    results = retriever.retrieve(question)

    print(f"\nTop {len(results)} chunks:\n")
    for i, c in enumerate(results, 1):
        print(f"[{i}] {c.doc_id} | Page {c.page} | Score {c.score}")
        print(f"    {c.text[:200]}...")
        print()
