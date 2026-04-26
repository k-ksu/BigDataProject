-- q3: average audio features for positive vs negative interactions.
-- Stage-3 implication: features whose mean differs meaningfully between
-- the two classes (e.g. danceability, energy, loudness) are first-class
-- candidates for the model's feature set; features that look identical
-- on both sides can be dropped or down-weighted.
USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS q3_results;
CREATE EXTERNAL TABLE q3_results(
    interaction_flag INT,
    n                BIGINT,
    avg_danceability DOUBLE,
    avg_energy       DOUBLE,
    avg_valence      DOUBLE,
    avg_acousticness DOUBLE,
    avg_loudness     DOUBLE,
    avg_tempo        DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 'project/hive/warehouse/q3_results';

INSERT OVERWRITE TABLE q3_results
SELECT
    i.interaction_flag,
    COUNT(*)                      AS n,
    ROUND(AVG(t.danceability), 4) AS avg_danceability,
    ROUND(AVG(t.energy),       4) AS avg_energy,
    ROUND(AVG(t.valence),      4) AS avg_valence,
    ROUND(AVG(t.acousticness), 4) AS avg_acousticness,
    ROUND(AVG(t.loudness),     4) AS avg_loudness,
    ROUND(AVG(t.tempo),        4) AS avg_tempo
FROM interactions_part i
JOIN tracks_part       t ON i.item_id = t.id
GROUP BY i.interaction_flag
ORDER BY i.interaction_flag;

INSERT OVERWRITE DIRECTORY 'project/output/q3'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
SELECT * FROM q3_results;

SELECT * FROM q3_results;
