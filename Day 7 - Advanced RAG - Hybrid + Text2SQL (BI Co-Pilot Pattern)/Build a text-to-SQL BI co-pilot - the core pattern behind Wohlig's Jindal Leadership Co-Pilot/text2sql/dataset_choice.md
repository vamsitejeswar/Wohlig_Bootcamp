# Dataset Choice

## Chosen Dataset

**Table:** `wohlig.big_query_dataset.nyc_taxi`  
**Source:** NYC Yellow Taxi Trip Records (2022), loaded into the Wohlig GCP project.

## Why This Dataset

| Reason | Detail |
|--------|--------|
| **Already available** | The table exists in `wohlig.big_query_dataset` — no data loading needed |
| **Rich for BI queries** | Timestamps, distances, fares, tips, passenger counts → supports aggregations, time-series, percentages |
| **Real-world relevance** | NYC taxi analytics mirrors the kind of operational BI questions Wohlig clients (e.g. Jindal) ask about their own transactional data |
| **Good difficulty range** | Simple counts → hourly patterns → window-function rankings, covering easy/medium/hard SQL |
| **Known schema** | NYC taxi is a well-documented public dataset, so the LLM already has implicit knowledge of what columns mean |

## Key Table: `nyc_taxi`

| Column | Type | Meaning |
|--------|------|---------|
| `vendor_id` | INTEGER | Taxi vendor (1 = Creative Mobile, 2 = VeriFone) |
| `pickup_datetime` | TIMESTAMP | Trip start time |
| `dropoff_datetime` | TIMESTAMP | Trip end time |
| `passenger_count` | INTEGER | Number of passengers |
| `trip_distance` | FLOAT | Trip distance in miles |
| `rate_code` | FLOAT | Rate code (1=standard, 2=JFK, etc.) |
| `fare_amount` | FLOAT | Meter fare |
| `tip_amount` | FLOAT | Tip paid |
| `total_amount` | FLOAT | Total charged |
| `payment_type` | INTEGER | 1=credit card, 2=cash, 3=no charge, 4=dispute |

> Note: schema_loader.py dynamically fetches the exact columns from BigQuery at runtime —
> the table above shows the expected standard NYC taxi schema.

## Why Not the Public Dataset

`bigquery-public-data.new_york_taxi_trips` is a multi-table dataset (yellow, green, FHV)
across many years. Using our own `nyc_taxi` table is simpler (single table, single schema)
and avoids cross-region billing complexity.
