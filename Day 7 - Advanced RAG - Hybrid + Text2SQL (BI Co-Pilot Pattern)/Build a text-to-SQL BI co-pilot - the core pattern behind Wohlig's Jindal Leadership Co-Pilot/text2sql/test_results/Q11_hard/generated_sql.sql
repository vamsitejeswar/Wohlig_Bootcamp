SELECT
    FORMAT_TIMESTAMP('%Y-%m', month_start) AS trip_month,
    monthly_trip_count,
    SUM(monthly_trip_count) OVER (ORDER BY month_start) AS running_total_trips
  FROM
    (
      SELECT
          DATE_TRUNC(t1.pickup_datetime, MONTH) AS month_start,
          COUNT(t1.pickup_datetime) AS monthly_trip_count
        FROM
          `wohlig.big_query_dataset.nyc_taxi` AS t1
        GROUP BY
          1
    )
ORDER BY
  trip_month