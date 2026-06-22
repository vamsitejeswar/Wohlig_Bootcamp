from pathlib import Path
from pypdf import PdfReader
from google import genai
from google.cloud import aiplatform, storage
from google.cloud.aiplatform.matching_engine.matching_engine_index import MatchingEngineIndex
from google.cloud.aiplatform_v1.types import IndexDatapoint
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
GCS_BUCKET = os.getenv("GCS_BUCKET", "")
INDEX_ID = os.getenv("INDEX_ID")

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

aiplatform.init(project=PROJECT_ID, location=LOCATION)
gcs_client = storage.Client(project=PROJECT_ID)

BASE_DIR = Path(__file__).parent

PDF_DIR = BASE_DIR / "corpus"
VECTOR_DIR = BASE_DIR / "vector_store"

pdfs = list(PDF_DIR.glob("*.pdf"))

print("PDF Count:", len(pdfs))


VECTOR_DIR.mkdir(exist_ok=True)


def extract_text(pdf_path):
    reader = PdfReader(pdf_path)

    pages = []

    for page_no, page in enumerate(reader.pages, start=1):

        text = page.extract_text()

        if text:
            pages.append(
                {
                    "page_number": page_no,
                    "text": text
                }
            )

    return pages


def chunk_text(text, chunk_size=512):

    words = text.split()

    chunks = []

    for i in range(
        0,
        len(words),
        chunk_size
    ):
        chunk = " ".join(
            words[i:i+chunk_size]
        )

        chunks.append(chunk)

    return chunks


def ingest():

    manifest_rows = []
    all_chunks = []

    for pdf_file in PDF_DIR.glob("*.pdf"):

        print(f"Processing {pdf_file.name}")

        pages = extract_text(pdf_file)

        total_chunks = 0

        for page in pages:

            chunks = chunk_text(page["text"])

            total_chunks += len(chunks)

            for chunk_no, chunk in enumerate(chunks):

                embedding_response = (
                    client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=chunk,
                        config={"output_dimensionality": 768}
                    )
                )

                embedding = (
                    embedding_response
                    .embeddings[0]
                    .values
                )

                all_chunks.append(
                    {
                        "doc_id": pdf_file.stem,
                        "page_number": page["page_number"],
                        "chunk_number": chunk_no,
                        "text": chunk,
                        "embedding": embedding
                    }
                )

        manifest_rows.append(
            {
                "doc_id": pdf_file.stem,
                "title": pdf_file.name,
                "num_pages": len(pages),
                "num_chunks": total_chunks
            }
        )

    with open(
        VECTOR_DIR / "embeddings.json",
        "w"
    ) as f:
        json.dump(all_chunks, f)

    bucket = gcs_client.bucket("wohlig-rag-pipeline-bucket")

    # Upload chunk metadata (without embeddings) to GCS for query lookup
    metadata = [
        {k: v for k, v in chunk.items() if k != "embedding"}
        for chunk in all_chunks
    ]

    blob = bucket.blob("vectors/chunks_metadata.json")
    blob.upload_from_string(
        json.dumps(metadata),
        content_type="application/json"
    )
    print(f"Uploaded {len(metadata)} chunks metadata to gs://wohlig-rag-pipeline-bucket/vectors/chunks_metadata.json")

    # Upsert embeddings directly to Vertex AI index (no GCS needed)
    print("Upserting embeddings to Vertex AI index...")
    index = MatchingEngineIndex(index_name=INDEX_ID)

    datapoints = [
        IndexDatapoint(
            datapoint_id=f"{chunk['doc_id']}_{chunk['chunk_number']}",
            feature_vector=chunk["embedding"]
        )
        for chunk in all_chunks
    ]

    index.upsert_datapoints(datapoints=datapoints)
    print(f"Upserted {len(datapoints)} datapoints to Vertex AI index.")

    pd.DataFrame(manifest_rows).to_csv("corpus_manifest.csv", index=False)

    print("Done")


if __name__ == "__main__":
    ingest()