SELECT
    EXTRACT(HOUR FROM t.pickup_datetime) AS pickup_hour,
    AVG(TIMESTAMP_DIFF(t.dropoff_datetime, t.pickup_datetime, MINUTE)) AS average_trip_duration_minutes
  FROM
    `wohlig.big_query_dataset.nyc_taxi` AS t
  GROUP BY
    pickup_hour
  ORDER BY
    pickup_hour