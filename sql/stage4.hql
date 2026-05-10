-- Stage 4: Superset dashboard input tables and views.
-- The dashboard itself is created manually in Apache Superset.

USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

DROP TABLE IF EXISTS stage3_evaluation;
CREATE EXTERNAL TABLE stage3_evaluation(
    model              STRING,
    areaUnderPR        DOUBLE,
    areaUnderROC       DOUBLE,
    testUsers          BIGINT,
    testRows           BIGINT,
    trueInteractions   DOUBLE,
    threshold          DOUBLE,
    accuracy           DOUBLE,
    precision          DOUBLE,
    recall             DOUBLE,
    f1                 DOUBLE,
    rankingUsers       BIGINT,
    rankingRows        BIGINT,
    sampledCandidates  BIGINT,
    precisionAt10      DOUBLE,
    recallAt10         DOUBLE,
    ndcgAt10           DOUBLE,
    mrrAt10            DOUBLE,
    best_params        STRING
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'project/output/evaluation'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS stage3_model1_predictions;
CREATE EXTERNAL TABLE stage3_model1_predictions(
    label      DOUBLE,
    prediction DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'project/output/model1_predictions'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS stage3_model2_predictions;
CREATE EXTERNAL TABLE stage3_model2_predictions(
    label      DOUBLE,
    prediction DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'project/output/model2_predictions'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS stage3_model1_scores;
CREATE EXTERNAL TABLE stage3_model1_scores(
    user_id    STRING,
    item_id    STRING,
    label      DOUBLE,
    prediction DOUBLE,
    rel_score  DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'project/output/model1_scores'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS stage3_model2_scores;
CREATE EXTERNAL TABLE stage3_model2_scores(
    user_id    STRING,
    item_id    STRING,
    label      DOUBLE,
    prediction DOUBLE,
    rel_score  DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'project/output/model2_scores'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP VIEW IF EXISTS stage4_dataset_summary;
CREATE VIEW stage4_dataset_summary AS
SELECT 'tracks_part' AS table_name, COUNT(*) AS row_count
FROM tracks_part
UNION ALL
SELECT 'interactions_part' AS table_name, COUNT(*) AS row_count
FROM interactions_part
UNION ALL
SELECT 'stage3_evaluation' AS table_name, COUNT(*) AS row_count
FROM stage3_evaluation
UNION ALL
SELECT 'stage3_model1_predictions' AS table_name, COUNT(*) AS row_count
FROM stage3_model1_predictions
UNION ALL
SELECT 'stage3_model2_predictions' AS table_name, COUNT(*) AS row_count
FROM stage3_model2_predictions;

DROP VIEW IF EXISTS stage4_table_columns;
CREATE VIEW stage4_table_columns AS
SELECT stack(
    18,
    'tracks_part', 'id', 'string', 'track identifier',
    'tracks_part', 'artists', 'string', 'artist names used for text features',
    'tracks_part', 'danceability', 'double', 'audio feature',
    'tracks_part', 'energy', 'double', 'audio feature',
    'tracks_part', 'valence', 'double', 'audio feature',
    'tracks_part', 'tempo', 'double', 'audio feature',
    'tracks_part', 'year', 'int', 'release year partition',
    'interactions_part', 'id', 'int', 'interaction identifier',
    'interactions_part', 'user_id', 'string', 'user identifier',
    'interactions_part', 'item_id', 'string', 'track identifier',
    'interactions_part', 'ts', 'bigint', 'event timestamp',
    'interactions_part', 'interaction_flag', 'int', 'binary target partition',
    'stage3_evaluation', 'areaUnderPR', 'double', 'main optimization metric',
    'stage3_evaluation', 'precisionAt10', 'double', 'ranking metric',
    'stage3_evaluation', 'recallAt10', 'double', 'ranking metric',
    'stage3_evaluation', 'ndcgAt10', 'double', 'ranking metric',
    'stage3_evaluation', 'mrrAt10', 'double', 'ranking metric',
    'stage3_evaluation', 'best_params', 'string', 'selected hyperparameters'
) AS (table_name, column_name, data_type, dashboard_note);

DROP VIEW IF EXISTS stage4_track_sample;
CREATE VIEW stage4_track_sample AS
SELECT
    id,
    name,
    artists,
    danceability,
    energy,
    valence,
    tempo,
    year
FROM tracks_part
LIMIT 100;

DROP VIEW IF EXISTS stage4_interaction_sample;
CREATE VIEW stage4_interaction_sample AS
SELECT
    id,
    user_id,
    item_id,
    ts,
    interaction_flag
FROM interactions_part
LIMIT 100;

DROP VIEW IF EXISTS stage4_feature_extraction_summary;
CREATE VIEW stage4_feature_extraction_summary AS
SELECT stack(
    6,
    'track audio', 'danceability, energy, loudness, speechiness, acousticness, instrumentalness, liveness, valence, tempo, duration_ms', 'content features for track preference',
    'track metadata', 'explicit, key, mode, time_signature, year', 'categorical and release metadata',
    'artist text', 'artists tokenized with RegexTokenizer and HashingTF', 'high-cardinality artist signal without huge one-hot vectors',
    'timestamp', 'event_year plus cyclic month/day/hour features', 'uses derived time features instead of raw unix timestamp',
    'user history', 'last-50 context interaction aggregates', 'captures user activity and positive-share history',
    'user-artist history', 'last-50 context artist aggregates', 'captures repeated interest in the same artist'
) AS (feature_group, feature_columns, modeling_purpose);

DROP VIEW IF EXISTS stage4_model_comparison;
CREATE VIEW stage4_model_comparison AS
SELECT
    model,
    areaUnderPR,
    areaUnderROC,
    threshold,
    accuracy,
    precision,
    recall,
    f1,
    precisionAt10,
    recallAt10,
    ndcgAt10,
    mrrAt10,
    testRows,
    trueInteractions,
    sampledCandidates,
    ROUND(trueInteractions / testRows, 6) AS positive_rate,
    ROUND(sampledCandidates * 1.0 / rankingRows, 6) AS sampled_candidate_share,
    best_params
FROM stage3_evaluation;

DROP VIEW IF EXISTS stage4_model_metrics_long;
CREATE VIEW stage4_model_metrics_long AS
SELECT model, 'areaUnderPR' AS metric, areaUnderPR AS value FROM stage3_evaluation
UNION ALL SELECT model, 'areaUnderROC' AS metric, areaUnderROC AS value FROM stage3_evaluation
UNION ALL SELECT model, 'accuracy' AS metric, accuracy AS value FROM stage3_evaluation
UNION ALL SELECT model, 'precision' AS metric, precision AS value FROM stage3_evaluation
UNION ALL SELECT model, 'recall' AS metric, recall AS value FROM stage3_evaluation
UNION ALL SELECT model, 'f1' AS metric, f1 AS value FROM stage3_evaluation
UNION ALL SELECT model, 'precisionAt10' AS metric, precisionAt10 AS value FROM stage3_evaluation
UNION ALL SELECT model, 'recallAt10' AS metric, recallAt10 AS value FROM stage3_evaluation
UNION ALL SELECT model, 'ndcgAt10' AS metric, ndcgAt10 AS value FROM stage3_evaluation
UNION ALL SELECT model, 'mrrAt10' AS metric, mrrAt10 AS value FROM stage3_evaluation;

DROP VIEW IF EXISTS stage4_prediction_confusion;
CREATE VIEW stage4_prediction_confusion AS
SELECT model, label, prediction, COUNT(*) AS row_count
FROM (
    SELECT 'model1' AS model, label, prediction FROM stage3_model1_predictions
    UNION ALL
    SELECT 'model2' AS model, label, prediction FROM stage3_model2_predictions
) predictions
GROUP BY model, label, prediction;

DROP VIEW IF EXISTS stage4_prediction_rates;
CREATE VIEW stage4_prediction_rates AS
SELECT
    model,
    COUNT(*) AS row_count,
    ROUND(SUM(label) / COUNT(*), 6) AS true_positive_rate,
    ROUND(SUM(prediction) / COUNT(*), 6) AS predicted_positive_rate
FROM (
    SELECT 'model1' AS model, label, prediction FROM stage3_model1_predictions
    UNION ALL
    SELECT 'model2' AS model, label, prediction FROM stage3_model2_predictions
) predictions
GROUP BY model;

DROP VIEW IF EXISTS stage4_score_summary;
CREATE VIEW stage4_score_summary AS
SELECT
    model,
    label,
    COUNT(*) AS row_count,
    ROUND(MIN(rel_score), 6) AS min_rel_score,
    ROUND(AVG(rel_score), 6) AS avg_rel_score,
    ROUND(MAX(rel_score), 6) AS max_rel_score
FROM (
    SELECT 'model1' AS model, label, rel_score FROM stage3_model1_scores
    UNION ALL
    SELECT 'model2' AS model, label, rel_score FROM stage3_model2_scores
) scores
GROUP BY model, label;

SHOW TABLES LIKE 'stage3*';
SHOW TABLES LIKE 'stage4*';
SELECT * FROM stage4_dataset_summary;
SELECT * FROM stage4_model_comparison;
SELECT * FROM stage4_prediction_rates;
SELECT * FROM stage4_score_summary;
