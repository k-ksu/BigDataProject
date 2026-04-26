USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS q2_results;
CREATE EXTERNAL TABLE q2_results(
    interaction_flag INT,
    cnt              BIGINT,
    pct              DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 'project/hive/warehouse/q2_results';

INSERT OVERWRITE TABLE q2_results
SELECT
    interaction_flag,
    COUNT(*)                                            AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4)  AS pct
FROM interactions_part
GROUP BY interaction_flag
ORDER BY interaction_flag;

INSERT OVERWRITE DIRECTORY 'project/output/q2'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
SELECT * FROM q2_results;

SELECT * FROM q2_results;
