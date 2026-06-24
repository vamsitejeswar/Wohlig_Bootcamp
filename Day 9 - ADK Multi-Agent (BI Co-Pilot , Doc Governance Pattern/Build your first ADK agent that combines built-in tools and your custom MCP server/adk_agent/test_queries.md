# Test Queries — Enterprise Search Agent

These 5 queries are designed to use **both** tool sources in a single conversation.
Each forces the agent to combine web search (`google_search`) with internal data (`BigQuery`/`GCS`).

---

## Query 1 — Cloud Providers Cross-Reference
```
Find the top 5 cloud providers on Google, then check our BigQuery to see which ones we have data for.
```
**Expected tools used:** `google_search` → `query_bigquery`

---

## Query 2 — GCS File Discovery
```
Search Google for the latest Apache Parquet file format spec, then list what files we have stored in our GCS bucket.
```
**Expected tools used:** `google_search` → `list_gcs_objects`

---

## Query 3 — Market Data Validation
```
Search Google for the current top 3 programming languages by popularity, then query our BigQuery to see if we have usage data for any of them.
```
**Expected tools used:** `google_search` → `query_bigquery`

---

## Query 4 — Internal Data Summary with Web Context
```
What datasets do we have in BigQuery? Also search Google to find what industry uses that kind of data most.
```
**Expected tools used:** `query_bigquery` → `google_search`

---

## Query 5 — GCS Content + Web Research
```
Read the contents of one of our GCS objects and then search Google for more information about that topic.
```
**Expected tools used:** `list_gcs_objects` → `read_gcs_object` → `google_search`
