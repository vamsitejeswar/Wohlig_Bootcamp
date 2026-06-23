SELECT
    `vendor_id`,
    COUNT(*) AS `total_trips`
  FROM
    `wohlig.big_query_dataset.nyc_taxi`
  GROUP BY
    `vendor_id`