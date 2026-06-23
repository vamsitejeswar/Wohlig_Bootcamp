SELECT
    `payment_type`,
    AVG(`tip_amount`)
  FROM
    `wohlig.big_query_dataset.nyc_taxi`
  GROUP BY
    `payment_type`