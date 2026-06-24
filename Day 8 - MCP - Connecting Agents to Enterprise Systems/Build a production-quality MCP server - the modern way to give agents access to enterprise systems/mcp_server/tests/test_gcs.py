import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from unittest.mock import MagicMock, patch
from tools.gcs_list_tool import list_gcs_objects
from tools.gcs_read_tool import read_gcs_object


# ── list_gcs_objects ──────────────────────────────────────────────────────────

@patch("tools.gcs_list_tool.storage.Client")
def test_list_objects_happy_path(mock_client_cls):
    blob = MagicMock()
    blob.name = "folder/file.txt"
    blob.size = 1024
    blob.updated = "2024-01-01"

    mock_client = MagicMock()
    mock_client.list_blobs.return_value = [blob]
    mock_client_cls.return_value = mock_client

    result = json.loads(list_gcs_objects("my-bucket", "folder/"))
    assert result["error"] is False
    assert result["count"] == 1
    assert result["objects"][0]["name"] == "folder/file.txt"


def test_list_objects_empty_bucket_name():
    result = json.loads(list_gcs_objects(""))
    assert result["error"] is True
    assert result["code"] == "INVALID_INPUT"


# ── read_gcs_object ───────────────────────────────────────────────────────────

@patch("tools.gcs_read_tool.storage.Client")
def test_read_object_happy_path(mock_client_cls):
    blob = MagicMock()
    blob.exists.return_value = True
    blob.size = 500
    blob.download_as_text.return_value = "hello world"

    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = blob
    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket
    mock_client_cls.return_value = mock_client

    result = json.loads(read_gcs_object("my-bucket", "file.txt"))
    assert result["error"] is False
    assert result["content"] == "hello world"


@patch("tools.gcs_read_tool.storage.Client")
def test_read_object_not_found(mock_client_cls):
    blob = MagicMock()
    blob.exists.return_value = False

    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = blob
    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket
    mock_client_cls.return_value = mock_client

    result = json.loads(read_gcs_object("my-bucket", "missing.txt"))
    assert result["error"] is True
    assert result["code"] == "NOT_FOUND"


@patch("tools.gcs_read_tool.storage.Client")
def test_read_object_size_limit(mock_client_cls):
    blob = MagicMock()
    blob.exists.return_value = True
    blob.size = 5 * 1024 * 1024  # 5MB

    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = blob
    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket
    mock_client_cls.return_value = mock_client

    result = json.loads(read_gcs_object("my-bucket", "bigfile.csv"))
    assert result["error"] is True
    assert result["code"] == "SIZE_LIMIT"


def test_read_object_missing_inputs():
    result = json.loads(read_gcs_object("", "file.txt"))
    assert result["error"] is True
    assert result["code"] == "INVALID_INPUT"
