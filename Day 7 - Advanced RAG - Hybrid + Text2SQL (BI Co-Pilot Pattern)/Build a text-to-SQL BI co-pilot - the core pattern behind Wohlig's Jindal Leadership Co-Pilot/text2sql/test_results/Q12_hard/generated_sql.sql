SELECT
    EXTRACT(HOUR FROM `pickup_datetime`) AS `trip_hour`,
    COUNTIF(`trip_distance` > 5) * 100.0 / COUNT(*) AS `percentage_trips_above_5_miles`
  FROM
    `wohlig.big_query_dataset.nyc_taxi`
  GROUP BY
    1
  ORDER BY
    1