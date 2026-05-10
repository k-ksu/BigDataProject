-- q6: marginal P(positive) vs cold vs hit tracks (reconciles q1 with q4).
-- Stage-3 implication: global class balance hides huge heterogeneity by track
-- exposure — stratify metrics by popularity and add log(popularity) as a feature.
USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS q6_results;
CREATE EXTERNAL TABLE q6_results(
    sort_key       INT,
    scenario       STRING,
    positive_rate  DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 'project/hive/warehouse/q6_results';

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
        total,
        pos
    FROM track_stats
),
agg AS (
    SELECT
        popularity_bucket,
        ROUND(SUM(pos) * 1.0 / SUM(total), 4) AS positive_rate
    FROM bucketed
    GROUP BY popularity_bucket
)
INSERT OVERWRITE TABLE q6_results
SELECT sort_key, scenario, positive_rate
FROM (
    SELECT
        1 AS sort_key,
        'Marginal: share of positive rows (all data)' AS scenario,
        ROUND(SUM(interaction_flag) * 1.0 / COUNT(*), 4) AS positive_rate
    FROM interactions_part
    UNION ALL
    SELECT
        2 AS sort_key,
        'Cold tracks: 1 interaction per track' AS scenario,
        positive_rate
    FROM agg
    WHERE popularity_bucket = '1'
    UNION ALL
    SELECT
        3 AS sort_key,
        'Hit tracks: 100+ interactions per track' AS scenario,
        positive_rate
    FROM agg
    WHERE popularity_bucket = '100+'
) x
ORDER BY sort_key;

INSERT OVERWRITE DIRECTORY 'project/output/q6'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
SELECT * FROM q6_results;

SELECT * FROM q6_results;
