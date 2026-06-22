# =========================================================
# vss_eval.py
# Vertex AI Vector Search — Benchmarking
# =========================================================

import os
import csv
import time
import json
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

from google import genai
from google.cloud import aiplatform, storage

# =========================================================
# LOAD ENV
# =========================================================

load_dotenv(find_dotenv())

PROJECT_ID        = os.getenv("PROJECT_ID")
LOCATION          = os.getenv("LOCATION", "us-central1")
INDEX_ENDPOINT_ID = os.getenv("INDEX_ENDPOINT_ID")
DEPLOYED_INDEX_ID = os.getenv("DEPLOYED_INDEX_ID")

EMBED_MODEL = "text-embedding-005"

BASE_DIR = Path(__file__).parent

RESULTS_CSV = BASE_DIR / "results_vss.csv"

# =========================================================
# CLIENTS
# =========================================================

genai_client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

aiplatform.init(
    project=PROJECT_ID,
    location=LOCATION
)

gcs_client = storage.Client(
    project=PROJECT_ID
)

# =========================================================
# LOAD GROUND TRUTH
# Keys   : question_id strings (e.g. "q1")
# Values : list of expected doc_ids (e.g. ["doc1"])
# Shared with bq_vector/ground_truth.json
# =========================================================

with open(
    BASE_DIR.parent / "bq_vector" / "ground_truth.json",
    "r",
    encoding="utf-8"
) as f:
    _raw_ground_truth = json.load(f)

GROUND_TRUTH = {
    k.strip().lower(): [
        str(v).strip().lower()
        for v in vs
    ]
    for k, vs in _raw_ground_truth.items()
}

# =========================================================
# HELPERS
# =========================================================

def parse_question_line(line):
    """
    Strips the leading label from a question line.

    Supports format:
      "q1| What is the Föllmer process?"

    Returns (question_id, question_text).
    """
    if "|" in line:
        label, _, text = line.partition("|")
        return label.strip(), text.strip()
    return None, line.strip()

# =========================================================
# LOAD CHUNK METADATA FROM GCS
# Used to resolve VVS neighbor IDs to doc_ids.
# VVS neighbor IDs have format: "{doc_id}_{chunk_number}"
# =========================================================

def load_metadata():

    print(
        "\nLoading chunk metadata from GCS..."
    )

    blob = (
        gcs_client
        .bucket("wohlig-rag-pipeline-bucket")
        .blob("vectors/chunks_metadata.json")
    )

    metadata = json.loads(
        blob.download_as_text()
    )

    lookup = {
        f"{item['doc_id']}_{item['chunk_number']}": item
        for item in metadata
    }

    print(
        f"\nMetadata loaded: {len(lookup)} chunks"
    )

    return lookup

# =========================================================
# CREATE CSV IF NOT EXISTS
# =========================================================

if not RESULTS_CSV.exists():

    with open(
        RESULTS_CSV,
        "w",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "question_id",
            "vss_latency_ms",
            "vss_recall_10"
        ])

# =========================================================
# EMBEDDING
# =========================================================

def generate_embedding(text):

    response = genai_client.models.embed_content(
        model=EMBED_MODEL,
        contents=text
    )

    return response.embeddings[0].values

# =========================================================
# RECALL@10
# Checks how many ground-truth doc_ids appear
# in the top-k retrieved doc_ids.
# =========================================================

def recall_at_k(
    retrieved,
    ground_truth,
    k=10
):

    seen = set()
    retrieved_k = []

    for item in retrieved[:k]:
        if item not in seen:
            seen.add(item)
            retrieved_k.append(item)

    hits = len(
        set(retrieved_k) &
        set(ground_truth)
    )

    if len(ground_truth) == 0:
        return 0.0

    return hits / len(ground_truth)

# =========================================================
# VECTOR SEARCH
# =========================================================

def vector_search(
    question_id,
    question,
    lookup,
    top_k=10
):

    print(
        f"\n=============================="
    )

    print(f"\n{question_id}| {question}")

    # =====================================================
    # EMBED QUERY
    # =====================================================

    embed_start = time.time()

    embedding = generate_embedding(
        question
    )

    embedding_latency_ms = (
        time.time() - embed_start
    ) * 1000

    print(
        f"\nEmbedding Latency: "
        f"{embedding_latency_ms:.2f} ms"
    )

    # =====================================================
    # QUERY VERTEX AI VECTOR SEARCH
    # Wall-clock latency (VVS has no server-side job metadata)
    # =====================================================

    endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=INDEX_ENDPOINT_ID
    )

    search_start = time.time()

    response = endpoint.find_neighbors(
        deployed_index_id=DEPLOYED_INDEX_ID,
        queries=[embedding],
        num_neighbors=top_k
    )

    vss_latency_ms = (
        time.time() - search_start
    ) * 1000

    print(
        f"\nVSS Latency: "
        f"{vss_latency_ms:.2f} ms"
    )

    # =====================================================
    # EXTRACT doc_ids FROM NEIGHBOR IDs
    # Neighbor ID format: "{doc_id}_{chunk_number}"
    # e.g. "doc1_0" → doc_id = "doc1"
    # =====================================================

    neighbors = response[0] if response else []

    retrieved_docs = []

    for neighbor in neighbors:

        # Extract doc_id from "{doc_id}_{chunk_number}"
        doc_id = neighbor.id.rsplit("_", 1)[0].lower()

        retrieved_docs.append(doc_id)

    # =====================================================
    # RECALL@10 — doc_id level
    # =====================================================

    ground_truth = GROUND_TRUTH.get(
        question_id.lower(),
        []
    )

    print("\nGround Truth Docs:")
    print(ground_truth)

    print("\nRetrieved Docs (top-10):")
    print(retrieved_docs[:10])

    print("\nHits:")
    print(
        set(retrieved_docs[:10]) &
        set(ground_truth)
    )

    recall_10 = recall_at_k(
        retrieved_docs,
        ground_truth,
        k=10
    )

    print(
        f"\nRecall@10: "
        f"{recall_10:.4f}"
    )

    # =====================================================
    # SAVE TO CSV
    # =====================================================

    with open(
        RESULTS_CSV,
        "a",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            question_id,
            round(vss_latency_ms, 2),
            round(recall_10, 4)
        ])

    print(
        f"\nSaved to {RESULTS_CSV}"
    )

    # =====================================================
    # PRINT TOP RESULTS
    # =====================================================

    print(
        "\n==================================="
    )

    for idx, neighbor in enumerate(neighbors):

        item = lookup.get(neighbor.id, {})

        print(f"\nResult {idx + 1}")

        print(
            f"\nDistance: {neighbor.distance}"
        )

        print(
            f"\nID: {neighbor.id}"
        )

        print(
            f"\nDocument: {item.get('doc_id', 'unknown')}"
        )

        print(
            f"\nPage: {item.get('page_number', '?')}"
        )

        print(
            f"\nText:\n{item.get('text', '')[:500]}"
        )

        print(
            "\n-----------------------------------"
        )

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    lookup = load_metadata()

    questions_file = (
        BASE_DIR.parent / "bq_vector" / "questions.txt"
    )

    with open(
        questions_file,
        "r",
        encoding="utf-8"
    ) as f:

        lines = [
            line.strip()
            for line in f
            if line.strip()
        ]

    print(
        f"\nLoaded {len(lines)} questions"
    )

    for line in lines:

        question_id, question = (
            parse_question_line(line)
        )

        vector_search(
            question_id=question_id,
            question=question,
            lookup=lookup,
            top_k=10
        )

    print(
        "\n==================================="
    )

    print(
        "\nAll queries complete."
    )

    print(
        f"\nResults: {RESULTS_CSV}"
    )

    print(
        "\n==================================="
    )
