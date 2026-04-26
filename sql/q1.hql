USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS q1_results;
CREATE EXTERNAL TABLE q1_results(
    track_id          STRING,
    track_name        STRING,
    artists           STRING,
    interaction_count BIGINT
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 'project/hive/warehouse/q1_results';

INSERT OVERWRITE TABLE q1_results
SELECT
    t.id      AS track_id,
    t.name    AS track_name,
    t.artists AS artists,
    COUNT(*)  AS interaction_count
FROM interactions_part i
JOIN tracks_part       t ON i.item_id = t.id
WHERE i.interaction_flag = 1
GROUP BY t.id, t.name, t.artists
ORDER BY interaction_count DESC
LIMIT 10;

INSERT OVERWRITE DIRECTORY 'project/output/q1'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
SELECT * FROM q1_results;

SELECT * FROM q1_results;
