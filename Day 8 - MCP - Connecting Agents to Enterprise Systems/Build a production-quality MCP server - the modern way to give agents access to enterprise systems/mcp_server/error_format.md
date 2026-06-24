# Structured Error Response Format

Every tool returns a dict with an `error` flag. This makes it easy for the agent to check if a call succeeded.

## Success
```json
{ "error": false, ...result fields... }
```

## Failure
```json
{ "error": true, "code": "ERROR_CODE", "message": "Human-readable explanation." }
```

## Error Codes

| Code | Tool | Meaning |
|------|------|---------|
| `NOT_READ_ONLY` | query_bigquery | SQL is not a SELECT statement |
| `COST_LIMIT` | query_bigquery | Query would scan > 100MB |
| `DRY_RUN_FAILED` | query_bigquery | BQ dry-run itself failed |
| `QUERY_FAILED` | query_bigquery | Query execution error |
| `NOT_FOUND` | read_gcs_object | File does not exist in bucket |
| `SIZE_LIMIT` | read_gcs_object | File is > 1MB |
| `GCS_ERROR` | list/read GCS | Generic GCS API error |
| `INVALID_INPUT` | all tools | Required field is empty |
