WITH MonthlyTrips AS (
  SELECT
    vendor_id,
    FORMAT_TIMESTAMP('%Y-%m', pickup_datetime) AS trip_month,
    COUNT(*) AS total_trips
  FROM
    `wohlig.big_query_dataset.nyc_taxi`
  GROUP BY
    vendor_id,
    FORMAT_TIMESTAMP('%Y-%m', pickup_datetime)
)
SELECT
  vendor_id,
  trip_month,
  total_trips,
  RANK() OVER (PARTITION BY trip_month ORDER BY total_trips DESC) AS vendor_rank_per_month
FROM
  MonthlyTrips
ORDER BY
  trip_month,
  vendor_rank_per_month
LIMIT 1000