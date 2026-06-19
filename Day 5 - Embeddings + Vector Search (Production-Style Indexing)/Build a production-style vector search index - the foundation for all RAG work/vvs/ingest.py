from pathlib import Path
from pypdf import PdfReader
from google import genai
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.getenv("PROJECT_ID"),
    location=os.getenv("LOCATION", "us-central1")
)

BASE_DIR = Path(__file__).parent

PDF_DIR = BASE_DIR / "corpus"
VECTOR_DIR = BASE_DIR / "vector_store"

pdfs = list(PDF_DIR.glob("*.pdf"))

print("PDF Count:", len(pdfs))


VECTOR_DIR.mkdir(exist_ok=True)

manifest_rows = []
all_chunks = []


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
                    contents=chunk
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

    json.dump(
        all_chunks,
        f
    )

pd.DataFrame(manifest_rows).to_csv("corpus_manifest.csv",index=False)

print("Done")