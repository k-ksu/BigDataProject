-- Stage 4: register Stage 3 result files in Hive for Superset.

USE team11_projectdb;

SET hive.resultset.use.unique.column.names = false;

CREATE EXTERNAL TABLE IF NOT EXISTS stage3_evaluation(
    model              STRING,
    areaUnderPR        DOUBLE,
    areaUnderROC       DOUBLE,
    testUsers          BIGINT,
    testRows           BIGINT,
    trueInteractions   DOUBLE,
    threshold          DOUBLE,
    accuracy           DOUBLE,
    `precision`        DOUBLE,
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

CREATE EXTERNAL TABLE IF NOT EXISTS stage3_model1_predictions(
    label      DOUBLE,
    prediction DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'project/output/model1_predictions'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE IF NOT EXISTS stage3_model2_predictions(
    label      DOUBLE,
    prediction DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'project/output/model2_predictions'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE IF NOT EXISTS stage3_model1_scores(
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

CREATE EXTERNAL TABLE IF NOT EXISTS stage3_model2_scores(
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

CREATE VIEW IF NOT EXISTS team11_stage3_feature_extraction_characteristics AS
SELECT stack(
    6,
    'track audio',
    'danceability, energy, loudness, speechiness, acousticness, instrumentalness, liveness, valence, tempo, duration_ms',
    'content preference signal',
    'track metadata',
    'explicit, key, mode, time_signature, year',
    'track context signal',
    'artist text',
    'tokenized artists with HashingTF',
    'artist preference signal',
    'timestamp',
    'calendar and cyclic time features from ts',
    'listening time pattern',
    'user history',
    'recent user aggregates and positive-rate history',
    'previous behavior signal',
    'user-artist history',
    'recent aggregates for the same artist',
    'repeated artist interest signal'
) AS (feature_group, examples, purpose);

SHOW TABLES LIKE 'stage3*';
SELECT * FROM team11_stage3_feature_extraction_characteristics;
SELECT * FROM stage3_evaluation;
SELECT * FROM stage3_model1_predictions LIMIT 10;
SELECT * FROM stage3_model2_predictions LIMIT 10;
SELECT * FROM stage3_model1_scores LIMIT 10;
SELECT * FROM stage3_model2_scores LIMIT 10;
