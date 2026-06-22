import json
import numpy as np
from pathlib import Path

from google import genai

BASE_DIR = Path(__file__).parent

client = genai.Client(
    vertexai=True,
    project="wohlig",
    location="us-central1"
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


with open(BASE_DIR/ "test_set.jsonl") as f:

    questions = [json.loads(line)for line in f]


strategies = [
    "fixed",
    "sentence",
    "semantic"
]

results = []

for question in questions:

    row = {"question_id":question["question_id"]}

    query = (question["question"])

    gt_doc = (question["ground_truth_doc"])

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

    for strategy in strategies:

        with open(BASE_DIR/ "indexes"/ f"{strategy}.json") as f:
            vectors = json.load(f)

        scores = []

        for item in vectors:

            score = (
                cosine_similarity(
                    query_vector,
                    item["embedding"]
                )
            )

            scores.append((score,item))

        scores.sort(
            reverse=True,
            key=lambda x: x[0]
        )

        top5 = scores[:5]

        top10 = scores[:10]

        recall5 = int(
            any(x[1]["doc_id"]== gt_doc for x in top5)
        )

        recall10 = int(
            any(
                x[1]["doc_id"]
                == gt_doc
                for x in top10
            )
        )

        row[
            f"{strategy}_recall_5"
        ] = recall5

        row[
            f"{strategy}_recall_10"
        ] = recall10

    results.append(
        row
    )


import pandas as pd

pd.DataFrame(results).to_csv(BASE_DIR/ "results.csv",index=False)

print("Done")