SELECT
    trip_date,
    AVG(daily_trip_count) OVER (ORDER BY trip_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_avg_3_day_trips
  FROM (
    SELECT
        CAST(pickup_datetime AS DATE) AS trip_date,
        COUNT(*) AS daily_trip_count
      FROM
        `wohlig.big_query_dataset.nyc_taxi`
      GROUP BY
        CAST(pickup_datetime AS DATE)
  )
  ORDER BY
    trip_date
  LIMIT 1000