-- A track is "popular" iff its interaction_count is in the top decile of tracks that received any interaction; this informs feature engineering in the stage 3 ML pipeline.
USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS q5_results;
CREATE EXTERNAL TABLE q5_results(
    bucket           STRING,
    n_tracks         BIGINT,
    avg_danceability DOUBLE,
    avg_energy       DOUBLE,
    avg_valence      DOUBLE,
    avg_loudness     DOUBLE,
    avg_tempo        DOUBLE,
    avg_acousticness DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 'project/hive/warehouse/q5_results';

WITH track_pop AS (
    SELECT
        t.id           AS track_id,
        t.danceability,
        t.energy,
        t.valence,
        t.loudness,
        t.tempo,
        t.acousticness,
        COUNT(i.user_id) AS interaction_count
    FROM tracks_part t
    LEFT JOIN interactions_part i
           ON i.item_id = t.id AND i.interaction_flag = 1
    GROUP BY t.id, t.danceability, t.energy, t.valence,
             t.loudness, t.tempo, t.acousticness
),
quantiles AS (
    SELECT percentile_approx(interaction_count, 0.90) AS p90
    FROM track_pop
    WHERE interaction_count > 0
),
labelled AS (
    SELECT
        CASE
            WHEN tp.interaction_count >= q.p90 THEN 'popular'
            WHEN tp.interaction_count > 0      THEN 'mid'
            ELSE 'cold'
        END AS bucket,
        tp.danceability, tp.energy, tp.valence,
        tp.loudness, tp.tempo, tp.acousticness
    FROM track_pop tp CROSS JOIN quantiles q
)
INSERT OVERWRITE TABLE q5_results
SELECT
    bucket,
    COUNT(*)                    AS n_tracks,
    ROUND(AVG(danceability), 4) AS avg_danceability,
    ROUND(AVG(energy),       4) AS avg_energy,
    ROUND(AVG(valence),      4) AS avg_valence,
    ROUND(AVG(loudness),     4) AS avg_loudness,
    ROUND(AVG(tempo),        4) AS avg_tempo,
    ROUND(AVG(acousticness), 4) AS avg_acousticness
FROM labelled
GROUP BY bucket
ORDER BY bucket;

INSERT OVERWRITE DIRECTORY 'project/output/q5'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
SELECT * FROM q5_results;

SELECT * FROM q5_results;
