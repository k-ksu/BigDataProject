-- q5: user-activity power law -- distribution of users by # of interactions.
-- Stage-3 implication: a heavy long tail of low-activity users means most
-- of the user-side signal comes from a small core; train/test must be
-- split per-user (not random row split) so cold users land in test, and
-- evaluation should be reported separately for each activity bucket.
USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS q5_results;
CREATE EXTERNAL TABLE q5_results(
    activity_bucket  STRING,
    user_count       BIGINT,
    pct_users        DOUBLE,
    n_interactions   BIGINT,
    pct_interactions DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 'project/hive/warehouse/q5_results';

WITH user_stats AS (
    SELECT user_id, COUNT(*) AS n
    FROM interactions_part
    GROUP BY user_id
),
bucketed AS (
    SELECT
        CASE
            WHEN n <= 1    THEN '1'
            WHEN n <= 5    THEN '2-5'
            WHEN n <= 20   THEN '6-20'
            WHEN n <= 100  THEN '21-100'
            WHEN n <= 500  THEN '101-500'
            ELSE                '500+'
        END AS activity_bucket,
        n
    FROM user_stats
)
INSERT OVERWRITE TABLE q5_results
SELECT
    activity_bucket,
    COUNT(*)                                            AS user_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4)  AS pct_users,
    SUM(n)                                              AS n_interactions,
    ROUND(100.0 * SUM(n) / SUM(SUM(n)) OVER (), 4)      AS pct_interactions
FROM bucketed
GROUP BY activity_bucket
ORDER BY n_interactions;

INSERT OVERWRITE DIRECTORY 'project/output/q5'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
SELECT * FROM q5_results;

SELECT * FROM q5_results;
