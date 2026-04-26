-- q4: positive rate by track popularity bucket.
-- Stage-3 implication: if the positive_rate climbs sharply with popularity,
-- the model has a popularity bias and we either need a popularity feature
-- or a debiasing strategy (e.g. inverse-propensity weighting).  The cold
-- bucket also tells us how many tracks the model will see only at inference
-- time -- the cold-start problem.
USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS q4_results;
CREATE EXTERNAL TABLE q4_results(
    popularity_bucket STRING,
    n_tracks          BIGINT,
    n_interactions    BIGINT,
    n_positive        BIGINT,
    positive_rate     DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 'project/hive/warehouse/q4_results';

WITH track_stats AS (
    SELECT
        item_id,
        COUNT(*)              AS total,
        SUM(interaction_flag) AS pos
    FROM interactions_part
    GROUP BY item_id
),
bucketed AS (
    SELECT
        CASE
            WHEN total <= 1   THEN '1'
            WHEN total <= 3   THEN '2-3'
            WHEN total <= 10  THEN '4-10'
            WHEN total <= 30  THEN '11-30'
            WHEN total <= 100 THEN '31-100'
            ELSE                   '100+'
        END AS popularity_bucket,
        total, pos
    FROM track_stats
)
INSERT OVERWRITE TABLE q4_results
SELECT
    popularity_bucket,
    COUNT(*)                              AS n_tracks,
    SUM(total)                            AS n_interactions,
    SUM(pos)                              AS n_positive,
    ROUND(SUM(pos) * 1.0 / SUM(total), 4) AS positive_rate
FROM bucketed
GROUP BY popularity_bucket
ORDER BY n_interactions;

INSERT OVERWRITE DIRECTORY 'project/output/q4'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
SELECT * FROM q4_results;

SELECT * FROM q4_results;
