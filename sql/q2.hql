-- q2: artist loyalty -- distribution of positive interactions per (user, artist) pair.
-- Stage-3 implication: if the distribution has a long right tail (many pairs
-- with 3+ positives) then "user has previously liked this artist" is a
-- strong feature and an artist embedding will pay off.  If most pairs sit
-- at 1 the signal is weak and we should not over-rely on artist features.
USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS q2_results;
CREATE EXTERNAL TABLE q2_results(
    positives_per_user_artist INT,
    pair_count                BIGINT,
    pct                       DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 'project/hive/warehouse/q2_results';

WITH ua_pairs AS (
    SELECT
        i.user_id,
        t.artists  AS artist,
        COUNT(*)   AS pos_count
    FROM interactions_part i
    JOIN tracks_part       t ON i.item_id = t.id
    WHERE i.interaction_flag = 1
    GROUP BY i.user_id, t.artists
),
binned AS (
    SELECT CASE WHEN pos_count >= 10 THEN 10 ELSE pos_count END AS bucket
    FROM ua_pairs
)
INSERT OVERWRITE TABLE q2_results
SELECT
    bucket                                              AS positives_per_user_artist,
    COUNT(*)                                            AS pair_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4)  AS pct
FROM binned
GROUP BY bucket
ORDER BY bucket;

INSERT OVERWRITE DIRECTORY 'project/output/q2'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
SELECT * FROM q2_results;

SELECT * FROM q2_results;
