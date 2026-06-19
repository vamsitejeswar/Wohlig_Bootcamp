# VVS — Vector Vector Search

Production-style vector search index for RAG workloads.

## Index Configuration

| Parameter | Value |
|-----------|-------|
| Embedding model | `gemini-embedding-001` (Vertex AI) |
| Embedding dimensions | **3072** |
| Distance metric | **Cosine similarity** |
| Chunk strategy | Word‑based sliding window |
| Chunk size | 512 words |
| Total documents | 10 (academic PDFs) |
| Total chunks | 426 |
| Storage | Local JSON (`vector_store/embeddings.json`) |
| Filter support | Client‑side post-filter (add before similarity search) |

## Dependencies

```
google-genai
pypdf
numpy
pandas
python-dotenv
```

## Environment

Set these in `.env` at project root:

```
PROJECT_ID=your-gcp-project
LOCATION=us-central1
```

## Pipeline

```
corpus/*.pdf  ──►  ingest.py  ──►  vector_store/embeddings.json  ──►  query.py
```

## Commands

### Ingest

```bash
python ingest.py
```

Iterates all PDFs in `corpus/`, extracts text per page, chunks into 512‑word segments, embeds each chunk via Vertex AI `gemini-embedding-001`, and saves to `vector_store/embeddings.json`.

### Query (interactive)

```bash
python query.py
```

Prompts for a question, embeds it, computes cosine similarity against all stored chunks, and prints the top‑5 results.

### Deploy to Vertex AI Vector Search

```bash
# 1. Convert embeddings to Vertex AI format (TSV)
python3 -c "
import json
with open('vvs/vector_store/embeddings.json') as f:
    data = json.load(f)
with open('/tmp/embeddings.tsv', 'w') as out:
    for item in data:
        vec = '\t'.join(str(v) for v in item['embedding'])
        out.write(f\"{item['doc_id']}_{item['chunk_number']}\t{vec}\n\")
"

# 2. Upload to GCS
gsutil cp /tmp/embeddings.tsv gs://<YOUR_BUCKET>/embeddings.tsv

# 3. Create index
gcloud ai indexes create \
  --project=$PROJECT_ID \
  --region=$LOCATION \
  --display-name=vvs-index \
  --metadata-file=index_metadata.json \
  --index-update-method=BATCH_UPDATE

# 4. Create index endpoint
gcloud ai index-endpoints create \
  --project=$PROJECT_ID \
  --region=$LOCATION \
  --display-name=vvs-endpoint

# 5. Deploy
gcloud ai index-endpoints deploy-index \
  --project=$PROJECT_ID \
  --region=$LOCATION \
  --index-endpoint-name=vvs-endpoint \
  --index=<INDEX_ID> \
  --deployed-index-id=vvs-deployed
```

### `index_metadata.json`

```json
{
  "contentsDeltaUri": "gs://<YOUR_BUCKET>/",
  "config": {
    "dimensions": 3072,
    "approximateNeighborsCount": 100,
    "distanceMeasureType": "DOT_PRODUCT_DISTANCE",
    "shardSize": "SHARD_SIZE_SMALL",
    "algorithmConfig": {
      "treeAhConfig": {
        "leafNodeEmbeddingCount": 1000,
        "leafNodesToSearchPercent": 10
      }
    }
  }
}
```

> Note: Cosine similarity = `1 - DOT_PRODUCT_DISTANCE` when embeddings are L2‑normalized. Normalize queries server‑side or use `COSINE_DISTANCE` if your Vertex AI version supports it.
