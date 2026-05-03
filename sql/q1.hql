-- q1: class balance of interaction_flag.
-- Stage-3 implication: the positive/negative ratio dictates whether the
-- classifier needs class weights and which metrics make sense (PR-AUC over
-- ROC-AUC if the imbalance is severe).
USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS q1_results;
CREATE EXTERNAL TABLE q1_results(
    interaction_flag INT,
    cnt              BIGINT,
    pct              DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 'project/hive/warehouse/q1_results';

INSERT OVERWRITE TABLE q1_results
SELECT
    interaction_flag,
    COUNT(*)                                            AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4)  AS pct
FROM interactions_part
GROUP BY interaction_flag
ORDER BY interaction_flag;

INSERT OVERWRITE DIRECTORY 'project/output/q1'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
SELECT * FROM q1_results;

SELECT * FROM q1_results;
