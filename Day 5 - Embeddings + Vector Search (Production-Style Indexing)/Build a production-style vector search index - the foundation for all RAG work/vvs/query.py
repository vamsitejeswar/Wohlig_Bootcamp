import json
import os

from google import genai
from google.cloud import aiplatform, storage
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
GCS_BUCKET = os.getenv("GCS_BUCKET", "")
INDEX_ENDPOINT_ID = os.getenv("INDEX_ENDPOINT_ID")
DEPLOYED_INDEX_ID = os.getenv("DEPLOYED_INDEX_ID")

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

aiplatform.init(project=PROJECT_ID, location=LOCATION)

gcs_client = storage.Client(project=PROJECT_ID)


def query():

    print("Loading metadata from gs://wohlig-rag-pipeline-bucket/vectors/chunks_metadata.json")

    blob = gcs_client.bucket("wohlig-rag-pipeline-bucket").blob("vectors/chunks_metadata.json")
    metadata = json.loads(blob.download_as_text())

    lookup = {
        f"{item['doc_id']}_{item['chunk_number']}": item
        for item in metadata
    }

    question = input("Enter Question: ")

    query_embedding = client.models.embed_content(
        model="gemini-embedding-001",
        contents=question,
        config={"output_dimensionality": 768}
    )

    query_vector = (
        query_embedding
        .embeddings[0]
        .values
    )

    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=INDEX_ENDPOINT_ID
    )

    response = index_endpoint.find_neighbors(
        deployed_index_id=DEPLOYED_INDEX_ID,
        queries=[query_vector],
        num_neighbors=5
    )

    if not response or not response[0]:
        print("No results returned. Ensure the Vertex AI index is populated and deployed.")
        return

    print("\nTOP 5 RESULTS\n")

    for neighbor in response[0]:

        item = lookup.get(neighbor.id)

        if not item:
            continue

        print("=" * 50)
        print(f"Score: {neighbor.distance:.4f}")
        print(f"Doc: {item['doc_id']}")
        print(f"Page: {item['page_number']}")
        print(item["text"][:300])


if __name__ == "__main__":
    query()
