# 15 Test Queries

Grouped by SQL difficulty. Each query is phrased in natural language exactly as a business
user would ask it. The agent resolves column names from the schema at runtime.

---

## Easy — Single-Table Aggregations (Q01–Q05)

These require only `SELECT COUNT / AVG / MAX / SUM ... FROM table` — no filtering, no date
logic, no subqueries. A correct LLM should nail these on the first try.

| ID | Question |
|----|----------|
| Q01 | How many total trips are in the dataset? |
| Q02 | What is the average trip distance across all trips? |
| Q03 | What is the maximum fare amount recorded in the dataset? |
| Q04 | How many trips were completed by each vendor? |
| Q05 | What is the total number of passengers carried across all trips? |

**Expected SQL pattern:**
```sql
SELECT COUNT(*) AS total_trips FROM `wohlig.big_query_dataset.nyc_taxi`
```

---

## Medium — Filtering, Date Functions, Grouping (Q06–Q10)

These require `WHERE`, `GROUP BY`, `EXTRACT()` / `DATE_TRUNC()`, or simple subqueries.
Risk: hallucinated column names (e.g. `pickup_hour` instead of `EXTRACT(HOUR FROM pickup_datetime)`).

| ID | Question |
|----|----------|
| Q06 | How many trips happened each month? Order by month. |
| Q07 | What is the average tip amount grouped by payment type? |
| Q08 | Which hour of the day has the highest number of trip pickups? |
| Q09 | What is the average trip distance for trips with more than 2 passengers? |
| Q10 | What are the top 5 trip distances (rounded to nearest mile) by frequency? |

**Expected SQL pattern (Q06):**
```sql
SELECT
  DATE_TRUNC(pickup_datetime, MONTH) AS month,
  COUNT(*) AS trip_count
FROM `wohlig.big_query_dataset.nyc_taxi`
GROUP BY 1
ORDER BY 1
```

---

## Hard — Window Functions, CTEs, Rolling Aggregations (Q11–Q15)

These require `OVER (PARTITION BY ... ORDER BY ...)`, CTEs, or multi-step aggregations.
Risk: incorrect window frame clauses, wrong PARTITION BY columns, or hallucinated functions.

| ID | Question |
|----|----------|
| Q11 | Show the running total (cumulative count) of trips by month. |
| Q12 | For each hour of the day, what percentage of trips had a trip distance above 5 miles? |
| Q13 | What is the average trip duration in minutes grouped by hour of pickup? |
| Q14 | Using a window function, rank each vendor by their total trip count per month. |
| Q15 | What is the 3-day rolling average of daily trip counts? Show date and rolling average. |

**Expected SQL pattern (Q11 — running total):**
```sql
WITH monthly AS (
  SELECT
    DATE_TRUNC(pickup_datetime, MONTH) AS month,
    COUNT(*) AS trip_count
  FROM `wohlig.big_query_dataset.nyc_taxi`
  GROUP BY 1
)
SELECT
  month,
  trip_count,
  SUM(trip_count) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM monthly
ORDER BY month
```

**Expected SQL pattern (Q14 — vendor ranking):**
```sql
WITH monthly_vendor AS (
  SELECT
    DATE_TRUNC(pickup_datetime, MONTH) AS month,
    vendor_id,
    COUNT(*) AS trip_count
  FROM `wohlig.big_query_dataset.nyc_taxi`
  GROUP BY 1, 2
)
SELECT
  month,
  vendor_id,
  trip_count,
  RANK() OVER (PARTITION BY month ORDER BY trip_count DESC) AS vendor_rank
FROM monthly_vendor
ORDER BY month, vendor_rank
```
