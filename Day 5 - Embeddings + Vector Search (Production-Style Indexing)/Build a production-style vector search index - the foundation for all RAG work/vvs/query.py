import json
import numpy as np
import os
from pathlib import Path

from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.getenv("PROJECT_ID"),
    location=os.getenv("LOCATION", "us-central1")
)


def cosine_similarity(a, b):

    a = np.array(a)
    b = np.array(b)

    return (
        np.dot(a, b)
        /
        (
            np.linalg.norm(a)
            *
            np.linalg.norm(b)
        )
    )


BASE_DIR = Path(__file__).parent

VECTOR_FILE = (
    BASE_DIR
    / "vector_store"
    / "embeddings.json"
)

print("Loading:", VECTOR_FILE)

with open(VECTOR_FILE, "r") as f:
    vectors = json.load(f)


query = input(
    "Enter Question: "
)

query_embedding = (
    client.models.embed_content(
        model="gemini-embedding-001",
        contents=query
    )
)

query_vector = (
    query_embedding
    .embeddings[0]
    .values
)

results = []

for item in vectors:

    score = cosine_similarity(
        query_vector,
        item["embedding"]
    )

    results.append(
        (
            score,
            item
        )
    )

results.sort(
    reverse=True,
    key=lambda x: x[0]
)

print("\nTOP 5 RESULTS\n")

for score, item in results[:5]:

    print("=" * 50)

    print(f"Score: {score:.4f}")

    print(f"Doc: {item['doc_id']}")

    print(f"Page: {item['page_number']}")

    print(item["text"][:300])