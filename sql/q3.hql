USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS q3_results;
CREATE EXTERNAL TABLE q3_results(
    year             INT,
    track_count      BIGINT,
    avg_duration_min DOUBLE,
    avg_energy       DOUBLE,
    avg_danceability DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 'project/hive/warehouse/q3_results';

INSERT OVERWRITE TABLE q3_results
SELECT
    year,
    COUNT(*)                          AS track_count,
    ROUND(AVG(duration_ms)/60000, 3)  AS avg_duration_min,
    ROUND(AVG(energy),       4)       AS avg_energy,
    ROUND(AVG(danceability), 4)       AS avg_danceability
FROM tracks_part
WHERE year IS NOT NULL AND year >= 1950
GROUP BY year
ORDER BY year;

INSERT OVERWRITE DIRECTORY 'project/output/q3'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
SELECT * FROM q3_results;

SELECT * FROM q3_results;
