from pathlib import Path
from pypdf import PdfReader
from google import genai
import json
from pathlib import Path

from strategies import (
    fixed_size_chunker,
    sentence_aware_chunker,
    semantic_chunker
)

BASE_DIR = Path(__file__).parent

CORPUS_DIR = (
    BASE_DIR.parent
    / ".."
    / "Build a production-style vector search index - the foundation for all RAG work"
    / "vvs"
    / "corpus"
).resolve()
print("Corpus Path:", CORPUS_DIR)
print("Exists:", CORPUS_DIR.exists())


OUTPUT_DIR = (BASE_DIR/ "indexes")

OUTPUT_DIR.mkdir(exist_ok=True)

client = genai.Client(
    vertexai=True,
    project="wohlig",
    location="us-central1"
)


def extract_text(pdf_path):

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


strategies = {
    "fixed":fixed_size_chunker,
    "sentence":sentence_aware_chunker,
    "semantic":semantic_chunker
}


for strategy_name, chunker in strategies.items():

    print(f"\nBuilding {strategy_name}")

    vectors = []

    chunk_id = 1

    for pdf_file in CORPUS_DIR.glob("*.pdf"):

        text = extract_text(pdf_file)

        chunks = chunker(text)

        for chunk in chunks:

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

            vectors.append(
                {
                    "chunk_id":f"{strategy_name}_{chunk_id}",
                    "doc_id":pdf_file.stem,
                    "text":chunk,
                    "embedding":embedding
                }
            )

            chunk_id += 1

    with open(OUTPUT_DIR/ f"{strategy_name}.json","w") as f:
        json.dump(vectors,f)

    print(f"Saved {strategy_name}")