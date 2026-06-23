SELECT
    EXTRACT(HOUR FROM `t`.`pickup_datetime`) AS pickup_hour
  FROM
    `wohlig.big_query_dataset.nyc_taxi` AS `t`
  GROUP BY
    1
ORDER BY
  COUNT(*) DESC
LIMIT 1