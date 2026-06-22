# =========================================================
# ingest.py
# BigQuery Vector Search — Ingestion
# =========================================================

import os
import uuid
import json
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from tqdm import tqdm
from pypdf import PdfReader

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

CHUNK_SIZE = 512

# =========================================================
# CORPUS PATH
# Reuses the same 10 PDFs from Day 5 Task 1
# =========================================================

BASE_DIR = Path(__file__).parent

CORPUS_DIR = Path(
    os.getenv(
        "CORPUS_PATH",
        str(
            BASE_DIR.parent.parent
            / "Build a production-style vector search index"
              " - the foundation for all RAG work"
            / "vvs"
            / "corpus"
        )
    )
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
# PDF EXTRACTION
# =========================================================

def extract_text_from_pdf(pdf_path):

    reader = PdfReader(pdf_path)

    pages = []

    for page_num, page in enumerate(
        reader.pages
    ):

        text = page.extract_text()

        pages.append({
            "page_number": page_num + 1,
            "text": text if text else ""
        })

    return pages

# =========================================================
# CHUNKING
# =========================================================

def chunk_text(text,chunk_size=CHUNK_SIZE):

    words = text.split()

    chunks = []

    for i in range(0,len(words),chunk_size):

        chunk = " ".join(words[i:i + chunk_size])

        chunks.append(chunk)

    return chunks

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
# DATASET CREATION
# =========================================================

def create_dataset():

    dataset_ref = bigquery.Dataset(
        f"{PROJECT_ID}.{DATASET_ID}"
    )

    dataset_ref.location = "US"

    bq_client.create_dataset(
        dataset_ref,
        exists_ok=True
    )

    print(
        f"\nDataset ready: "
        f"{PROJECT_ID}.{DATASET_ID}"
    )

# =========================================================
# TABLE CREATION
# =========================================================

def create_table():

    schema = [

        bigquery.SchemaField(
            "chunk_id",
            "STRING"
        ),

        bigquery.SchemaField(
            "doc_id",
            "STRING"
        ),

        bigquery.SchemaField(
            "page_number",
            "INTEGER"
        ),

        bigquery.SchemaField(
            "text",
            "STRING"
        ),

        bigquery.SchemaField(
            "embedding",
            "FLOAT64",
            mode="REPEATED"
        )
    ]

    table = bigquery.Table(
        TABLE_ID,
        schema=schema
    )

    table = bq_client.create_table(
        table,
        exists_ok=True
    )

    print(
        f"\nTable ready: {TABLE_ID}"
    )

# =========================================================
# INSERT CHUNK
# =========================================================

chunk_store = []

def insert_chunk(
    chunk,
    embedding,
    metadata
):

    chunk_id = str(uuid.uuid4())

    row = {

        "chunk_id": chunk_id,

        "doc_id": metadata["doc_id"],

        "page_number": metadata[
            "page_number"
        ],

        "text": chunk,

        "embedding": embedding
    }

    # =====================================================
    # INSERT INTO BIGQUERY
    # =====================================================

    errors = bq_client.insert_rows_json(
        TABLE_ID,
        [row]
    )

    if errors:

        print(
            f"\nInsert Errors:\n{errors}"
        )

    else:

        # =====================================================
        # SAVE LOCALLY
        # =====================================================

        chunk_store.append({

            "chunk_id": chunk_id,

            "doc_id": metadata["doc_id"],

            "page_number": metadata[
                "page_number"
            ],

            "text": chunk
        })

        # =====================================================
        # CREATE DIR
        # =====================================================

        embeddings_dir = BASE_DIR / "embeddings"

        embeddings_dir.mkdir(exist_ok=True)

        # =====================================================
        # SAVE JSON
        # =====================================================

        with open(
            embeddings_dir / "chunk_store.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                chunk_store,
                f,
                indent=2,
                ensure_ascii=False
            )

# =========================================================
# BUILD VECTOR INDEX
# =========================================================

def build_vector_index():

    # =====================================================
    # Check row count first.
    # BigQuery IVF index requires >= 5000 rows.
    # For smaller corpora, VECTOR_SEARCH runs exact search
    # directly on the table — no index needed.
    # =====================================================

    count_sql = f"""
    SELECT COUNT(*) AS total
    FROM `{TABLE_ID}`
    """

    result = list(
        bq_client.query(count_sql).result()
    )

    total_rows = result[0].total

    print(
        f"\nTotal rows in table: {total_rows}"
    )

    MIN_ROWS_FOR_INDEX = 5000

    if total_rows < MIN_ROWS_FOR_INDEX:

        print(
            f"\nSkipping vector index: "
            f"{total_rows} rows < {MIN_ROWS_FOR_INDEX} minimum."
        )

        print(
            "\nVECTOR_SEARCH will run exact search directly."
        )

        return

    sql = f"""
    CREATE VECTOR INDEX IF NOT EXISTS
        chunks_embedding_idx
    ON `{TABLE_ID}`(embedding)
    OPTIONS (
        distance_type = 'COSINE',
        index_type = 'IVF',
        ivf_options = '{{"num_lists": 10}}'
    )
    """

    print(
        "\nBuilding vector index..."
    )

    bq_client.query(sql).result()

    print(
        "\nVector index ready."
    )

# =========================================================
# INGEST CORPUS
# =========================================================

def ingest_corpus():

    pdf_files = list(
        CORPUS_DIR.glob("*.pdf")
    )

    print(f"\nCorpus: {CORPUS_DIR}")

    print(f"\nFound {len(pdf_files)} PDFs")

    for pdf_file in tqdm(pdf_files):

        print(f"\nProcessing: {pdf_file.name}")

        doc_id = pdf_file.stem

        pages = extract_text_from_pdf(pdf_file)

        for page in pages:

            page_number = page[
                "page_number"
            ]

            page_text = page["text"]

            chunks = chunk_text(
                page_text,
                chunk_size=CHUNK_SIZE
            )

            for chunk in chunks:

                if not chunk.strip():
                    continue

                # =====================================================
                # EMBEDDING
                # =====================================================

                embedding = generate_embedding(
                    chunk
                )

                # =====================================================
                # METADATA
                # =====================================================

                metadata = {
                    "doc_id": doc_id,
                    "page_number": page_number
                }

                # =====================================================
                # INSERT
                # =====================================================

                insert_chunk(
                    chunk,
                    embedding,
                    metadata
                )

    print("\n===================================")

    print("BigQuery ingestion completed!")

    print(f"\nTotal chunks: {len(chunk_store)}")

    print("\n===================================")

# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    create_dataset()

    create_table()

    ingest_corpus()

    build_vector_index()
