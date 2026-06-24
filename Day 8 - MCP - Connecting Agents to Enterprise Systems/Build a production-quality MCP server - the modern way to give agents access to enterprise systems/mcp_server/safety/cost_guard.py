# Rejects queries that would scan more than 100MB using BQ dry-run

from google.cloud import bigquery

MAX_BYTES = 100 * 1024 * 1024  # 100 MB


def check_cost(sql: str, client: bigquery.Client) -> tuple[bool, int]:
    """
    Returns (is_within_limit, bytes_scanned).
    Uses BQ dry-run — no data is actually read.
    """
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    job = client.query(sql, job_config=job_config)
    bytes_scanned = job.total_bytes_processed or 0
    return bytes_scanned <= MAX_BYTES, bytes_scanned
