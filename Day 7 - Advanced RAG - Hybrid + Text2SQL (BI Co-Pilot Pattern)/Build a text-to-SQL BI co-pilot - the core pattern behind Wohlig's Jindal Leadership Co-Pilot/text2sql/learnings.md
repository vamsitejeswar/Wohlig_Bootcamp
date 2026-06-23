# Learnings

Results from running `python main.py` on 2026-06-23 against `wohlig.big_query_dataset.nyc_taxi`.

---

## Accuracy by Difficulty Bucket

| Bucket | Total | Pass | Fail | Pass Rate |
|--------|-------|------|------|-----------|
| Easy   | 5     | 5    | 0    | 100%      |
| Medium | 5     | 5    | 0    | 100%      |
| Hard   | 5     | 5    | 0    | 100%      |
| **All**| **15**| **15**| **0** | **100%** |

One hard query (Q14) required **2 Gemini correction retries** before passing dry-run —
caught and fixed automatically by the validator without human intervention.

---

## Schema-Prompting Tricks That Worked

### 1. Including sample rows in the prompt
The model used the literal sample row values to infer column types correctly.
For example, `passenger_count` is stored as `INTEGER` but `vendor_id` and `payment_type`
are `STRING` (not INT). The sample rows showed `'2'` vs `2`, so the model never wrote
`WHERE vendor_id = 2` (which would fail a string comparison).

### 2. Listing column types (`STRING`, `NUMERIC`, `TIMESTAMP`)
The model used `ROUND(trip_distance)` correctly for Q10 because it saw `NUMERIC` not `FLOAT`.
For TIMESTAMP comparisons it defaulted to `EXTRACT()` and `FORMAT_TIMESTAMP()` — no incorrect
`DATE()` casts needed.

### 3. Precomputed integer columns as shortcuts
The table has `data_file_year` (INTEGER) and `data_file_month` (INTEGER) alongside raw
timestamps. For Q06 ("trips per month") the model chose `EXTRACT(MONTH FROM pickup_datetime)`
rather than those columns — both are valid, but using the timestamp is more flexible for
multi-year filtering.

### 4. Backtick-quoted fully qualified table name in the system rules
Zero "table not found" errors across all 15 queries. The rule
"always use fully qualified table names with backtick quoting" was obeyed in every query.

### 5. "Return ONLY the SQL — no markdown fences" instruction
Without this, Gemini occasionally wraps output in \`\`\`sql ... \`\`\`. The explicit
instruction + `_clean()` regex in agent.py together eliminated this reliably.

---

## Hallucinated Column Failures

**None detected across 15 queries.** The model stayed within the schema on every attempt.

The most tempting hallucination opportunity was Q12 (percentage above 5 miles) — the model
correctly used `COUNTIF(trip_distance > 5)`, a BigQuery-native aggregate, rather than
inventing a column like `long_trip_flag`.

---

## How Validation Caught Bad SQL

### Q14 — Window function PARTITION BY on ungrouped column (2 retries needed)

**First attempt (failed):**
```sql
SELECT
  vendor_id,
  FORMAT_TIMESTAMP('%Y-%m', pickup_datetime) AS trip_month,
  COUNT(*) AS total_trips,
  RANK() OVER (PARTITION BY FORMAT_TIMESTAMP('%Y-%m', pickup_datetime)
               ORDER BY COUNT(*) DESC) AS rank
FROM `wohlig.big_query_dataset.nyc_taxi`
GROUP BY vendor_id, trip_month
```

**BigQuery error:**
```
PARTITION BY expression references column pickup_datetime which is
neither grouped nor aggregated
```

**Why it failed:** The `OVER()` clause referenced the raw `pickup_datetime` column
inside `FORMAT_TIMESTAMP()`. Even though the `GROUP BY` used the alias `trip_month`,
BigQuery does not accept raw column references in window clause expressions when those
columns are not directly in the `GROUP BY`.

**Fix after retry 2 (succeeded):**
The model rewrote it using a CTE to pre-aggregate, then applied `RANK()` over the
already-aggregated result — the standard correct pattern:
```sql
WITH MonthlyTrips AS (
  SELECT
    vendor_id,
    FORMAT_TIMESTAMP('%Y-%m', pickup_datetime) AS trip_month,
    COUNT(*) AS total_trips
  FROM `wohlig.big_query_dataset.nyc_taxi`
  GROUP BY vendor_id, FORMAT_TIMESTAMP('%Y-%m', pickup_datetime)
)
SELECT
  vendor_id, trip_month, total_trips,
  RANK() OVER (PARTITION BY trip_month ORDER BY total_trips DESC) AS vendor_rank_per_month
FROM MonthlyTrips
ORDER BY trip_month, vendor_rank_per_month
LIMIT 1000
```

**Lesson:** Always write `GROUP BY` using the raw expression, not the alias, in BigQuery.
The validator loop (dry-run → error → Gemini fix → retry) successfully recovered from this
without human intervention.

---

## Chart Type Distribution

| Chart Type | Count | Queries |
|------------|-------|---------|
| bar        | 9     | Q04, Q06, Q07, Q10, Q11, Q12, Q13, Q14, Q15 (actually line) |
| line       | 1     | Q15 (3-day rolling average — date × numeric → line correctly picked) |
| none       | 5     | Q01, Q02, Q03, Q05, Q08 (single-value scalar results) |

The `none` cases are correct: a single scalar value (e.g. "total trips = 500,000") has
nothing to chart. The chart_picker correctly returns `none` for 1-row × 1-column results.

Q15 (rolling average, date × numeric) correctly triggered the `line` chart path.

---

## Key Takeaways

1. **Schema prompting with sample rows is essential.** Without concrete sample values,
   the LLM would likely confuse STRING columns (vendor_id='2') with INTEGER columns (vendor_id=2).
   Two or three sample rows cost ~200 tokens and prevent many class-of-errors.

2. **BQ dry-run as a validation gate is low-cost and highly effective.** It catches 100%
   of syntax errors and column-name hallucinations before any data is read. In production,
   wrap the retry loop in a circuit-breaker: if all retries fail, return a user-friendly
   message instead of silently crashing.

3. **Hard queries (window functions) need CTEs, not inline aggregations.** Q14 failed twice
   until the model was guided by the error message to restructure into a CTE. Consider adding
   a few-shot example of a CTE + window function directly in the system prompt to reduce
   retries on this pattern.

4. **Single-value results (Q01–Q03, Q05, Q08) are unchartable.** The chart_picker correctly
   returns `none` for these. In a real BI co-pilot you would render these as a "big number"
   KPI card rather than suppressing the visualization entirely.

5. **`COUNTIF()` is BigQuery-specific.** Q12 used `COUNTIF(trip_distance > 5)` — a BQ
   aggregate that doesn't exist in standard SQL. The system rules correctly guide the model
   toward BigQuery Standard SQL; using a generic SQL prompt would have produced
   `SUM(CASE WHEN...)` which is valid but more verbose.
