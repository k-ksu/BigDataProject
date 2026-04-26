USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS q4_results;
CREATE EXTERNAL TABLE q4_results(
    user_id           STRING,
    interaction_count BIGINT,
    distinct_tracks   BIGINT
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 'project/hive/warehouse/q4_results';

INSERT OVERWRITE TABLE q4_results
SELECT
    user_id,
    COUNT(*)                AS interaction_count,
    COUNT(DISTINCT item_id) AS distinct_tracks
FROM interactions_part
WHERE interaction_flag = 1
GROUP BY user_id
ORDER BY interaction_count DESC
LIMIT 20;

INSERT OVERWRITE DIRECTORY 'project/output/q4'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
SELECT * FROM q4_results;

SELECT * FROM q4_results;
