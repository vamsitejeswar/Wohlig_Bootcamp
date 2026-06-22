# =========================================================
# query.py
# BigQuery VECTOR_SEARCH — Benchmarking
# =========================================================

import os
import csv
import json
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

from google import genai
from google.cloud import bigquery

# =========================================================
# LOAD ENV
# =========================================================

load_dotenv(find_dotenv())

PROJECT_ID = os.getenv("PROJECT_ID")

LOCATION = os.getenv(
    "LOCATION",
    "us-central1"
)

DATASET_ID = os.getenv(
    "BQ_DATASET",
    "rag_comparison"
)

TABLE_ID = (
    f"{PROJECT_ID}."
    f"{DATASET_ID}."
    f"document_chunks"
)

EMBED_MODEL = "text-embedding-005"

BASE_DIR = Path(__file__).parent

RESULTS_CSV = (
    BASE_DIR.parent
    / "comparison"
    / "results_bq.csv"
)

# =========================================================
# CLIENTS
# =========================================================

genai_client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

bq_client = bigquery.Client(
    project=PROJECT_ID
)

# =========================================================
# LOAD GROUND TRUTH
# Keys   : question_id strings (e.g. "q1")
# Values : list of expected doc_ids (e.g. ["doc1"])
# Recall is doc-level — we check whether the correct
# source document appears in the top-10 results.
# =========================================================

with open(
    BASE_DIR / "ground_truth.json",
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
# CREATE CSV IF NOT EXISTS
# =========================================================

RESULTS_CSV.parent.mkdir(
    parents=True,
    exist_ok=True
)

if not RESULTS_CSV.exists():

    with open(
        RESULTS_CSV,
        "w",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "question_id",
            "bq_latency_ms",
            "bq_recall_10",
            "bytes_processed",
            "cost_usd"
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
    top_k=10
):

    print(f"\n==============================")

    print(f"\n{question_id}| {question}")

    # =====================================================
    # EMBED QUERY
    # =====================================================

    embedding = generate_embedding(question)

    # =====================================================
    # EMBEDDING TO SQL ARRAY STRING
    # =====================================================

    embedding_str = ",".join(
        map(str, embedding)
    )

    # =====================================================
    # SQL
    # =====================================================

    sql = f"""

    SELECT
        base.doc_id,
        base.page_number,
        base.text,
        distance

    FROM VECTOR_SEARCH(

        TABLE `{TABLE_ID}`,

        'embedding',

        (
            SELECT
                [{embedding_str}]
                AS embedding
        ),

        top_k => {top_k}
    )

    ORDER BY distance ASC

    """

    # =====================================================
    # EXECUTE QUERY
    # =====================================================

    query_job = bq_client.query(sql)

    results = list(query_job.result())

    # =====================================================
    # BIGQUERY EXECUTION LATENCY (from job metadata)
    # =====================================================

    bq_execution_latency_ms = (
        query_job.ended -
        query_job.started
    ).total_seconds() * 1000

    # =====================================================
    # BYTES PROCESSED & COST
    # =====================================================

    bytes_processed = (
        query_job.total_bytes_processed
    )

    # BigQuery pricing: $5 per TB scanned
    cost_usd = (
        bytes_processed / (1024 ** 4)
    ) * 5

    # =====================================================
    # PRINT METRICS
    # =====================================================

    print(
        f"\nBQ Execution Latency: "
        f"{bq_execution_latency_ms:.2f} ms"
    )

    print(
        f"\nBytes Processed: "
        f"{bytes_processed:,}"
    )

    print(
        f"\nEstimated Cost: "
        f"${cost_usd:.8f}"
    )

    # =====================================================
    # RECALL@10 — doc_id level
    # retrieved_docs: doc_id from each BQ result row
    # ground_truth:   expected doc_ids for this question
    # =====================================================

    retrieved_docs = [
        str(row.doc_id).strip().lower()
        for row in results
    ]

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
            round(bq_execution_latency_ms, 2),
            round(recall_10, 4),
            bytes_processed,
            round(cost_usd, 8)
        ])

    print(
        f"\nSaved to {RESULTS_CSV}"
    )

    # =====================================================
    # PRINT TOP RESULTS
    # =====================================================

    print("\n===================================")

    for idx, row in enumerate(results):

        print(f"\nResult {idx + 1}")
        print(f"\nDistance: {row.distance}")
        print(f"\nDocument: {row.doc_id}")
        print(f"\nPage: {row.page_number}")
        print(f"\nText:\n{row.text[:500]}")
        print(
            "\n-----------------------------------"
        )

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    questions_file = BASE_DIR / "questions.txt"

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
            top_k=10
        )

    print("\n===================================")
    print("\nAll queries complete.")
    print(f"\nResults: {RESULTS_CSV}")
    print("\n===================================")
