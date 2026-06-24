import json
import os
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

SIZE_LIMIT = 1 * 1024 * 1024  # 1 MB


def read_gcs_object(bucket: str, path: str) -> str:
    """Read a file from GCS. Rejects files larger than 1MB."""
    if not bucket or not path:
        return json.dumps({"error": True, "code": "INVALID_INPUT", "message": "bucket and path are required."})

    try:
        client = storage.Client(project=os.getenv("PROJECT_ID", "wohlig"))
        blob = client.bucket(bucket).blob(path)

        if not blob.exists():
            return json.dumps({"error": True, "code": "NOT_FOUND", "message": f"'{path}' not found in bucket '{bucket}'."})

        blob.reload()
        if blob.size > SIZE_LIMIT:
            mb = blob.size / (1024 * 1024)
            return json.dumps({"error": True, "code": "SIZE_LIMIT", "message": f"File is {mb:.1f}MB — limit is 1MB."})

        content = blob.download_as_text()
        return json.dumps({"error": False, "bucket": bucket, "path": path, "size_bytes": blob.size, "content": content})
    except Exception as e:
        return json.dumps({"error": True, "code": "GCS_ERROR", "message": str(e)})
