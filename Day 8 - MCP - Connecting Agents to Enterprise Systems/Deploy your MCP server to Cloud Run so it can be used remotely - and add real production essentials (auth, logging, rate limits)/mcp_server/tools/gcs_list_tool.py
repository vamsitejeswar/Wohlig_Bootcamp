import json
import os
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()


def list_gcs_objects(bucket: str, prefix: str = "") -> str:
    """List files in a GCS bucket. Optionally filter by prefix (folder path)."""
    if not bucket:
        return json.dumps({"error": True, "code": "INVALID_INPUT", "message": "bucket name is required."})

    try:
        client = storage.Client(project=os.getenv("PROJECT_ID", "wohlig"))
        blobs = client.list_blobs(bucket, prefix=prefix)
        objects = [{"name": b.name, "size_bytes": b.size, "updated": str(b.updated)} for b in blobs]
        return json.dumps({"error": False, "bucket": bucket, "prefix": prefix, "count": len(objects), "objects": objects})
    except Exception as e:
        return json.dumps({"error": True, "code": "GCS_ERROR", "message": str(e)})
