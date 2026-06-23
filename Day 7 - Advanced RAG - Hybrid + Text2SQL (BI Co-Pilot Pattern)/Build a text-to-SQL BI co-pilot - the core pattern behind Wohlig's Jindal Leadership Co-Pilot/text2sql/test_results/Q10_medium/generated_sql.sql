SELECT
    ROUND(`trip_distance`) AS rounded_trip_distance,
    COUNT(*) AS frequency
  FROM
    `wohlig.big_query_dataset.nyc_taxi`
  GROUP BY
    rounded_trip_distance
  ORDER BY
    frequency DESC
  LIMIT 5