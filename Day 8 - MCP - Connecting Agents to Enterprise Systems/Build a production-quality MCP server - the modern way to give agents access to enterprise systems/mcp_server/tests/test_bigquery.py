import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from unittest.mock import MagicMock, patch
from tools.bigquery_tool import query_bigquery


# ── Happy path ────────────────────────────────────────────────────────────────

@patch("tools.bigquery_tool.bigquery.Client")
@patch("tools.bigquery_tool.check_cost", return_value=(True, 500))
def test_valid_select_query(mock_cost, mock_client_cls):
    mock_client = MagicMock()
    mock_client.query.return_value.result.return_value = []
    mock_client_cls.return_value = mock_client

    result = json.loads(query_bigquery("SELECT * FROM `wohlig.big_query_dataset.nyc_taxi` LIMIT 5"))
    assert result["error"] is False
    assert result["count"] == 0


# ── Safety: non-SELECT blocked ────────────────────────────────────────────────

def test_delete_query_blocked():
    result = json.loads(query_bigquery("DELETE FROM `wohlig.big_query_dataset.nyc_taxi` WHERE 1=1"))
    assert result["error"] is True
    assert result["code"] == "NOT_READ_ONLY"


def test_drop_query_blocked():
    result = json.loads(query_bigquery("DROP TABLE `wohlig.big_query_dataset.nyc_taxi`"))
    assert result["error"] is True
    assert result["code"] == "NOT_READ_ONLY"


# ── Safety: cost limit hit ────────────────────────────────────────────────────

@patch("tools.bigquery_tool.bigquery.Client")
@patch("tools.bigquery_tool.check_cost", return_value=(False, 200 * 1024 * 1024))
def test_cost_limit_exceeded(mock_cost, mock_client_cls):
    result = json.loads(query_bigquery("SELECT * FROM `wohlig.big_query_dataset.nyc_taxi`"))
    assert result["error"] is True
    assert result["code"] == "COST_LIMIT"
    assert "200.0MB" in result["message"]
