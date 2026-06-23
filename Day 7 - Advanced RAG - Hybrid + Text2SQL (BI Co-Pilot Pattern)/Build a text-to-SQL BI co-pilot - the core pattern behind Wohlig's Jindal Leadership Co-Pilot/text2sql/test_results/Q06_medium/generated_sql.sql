SELECT
    EXTRACT(MONTH FROM `t`.`pickup_datetime`) AS `trip_month`,
    COUNT(*) AS `total_trips`
  FROM
    `wohlig.big_query_dataset.nyc_taxi` AS `t`
  GROUP BY
    `trip_month`
  ORDER BY
    `trip_month`