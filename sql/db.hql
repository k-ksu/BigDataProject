-- Stage 2: Hive data warehouse for team11.
-- Builds  team11_projectdb  on top of the Sqoop AVRO output, materialises
-- partitioned + bucketed copies, and drops the un-optimised originals.

DROP DATABASE IF EXISTS team11_projectdb CASCADE;
CREATE DATABASE team11_projectdb LOCATION "project/hive/warehouse";
USE team11_projectdb;

DROP TABLE IF EXISTS tracks;
CREATE EXTERNAL TABLE tracks
STORED AS AVRO
LOCATION 'project/warehouse/tracks'
TBLPROPERTIES ('avro.schema.url'='project/warehouse/avsc/tracks.avsc');

DROP TABLE IF EXISTS interactions;
CREATE EXTERNAL TABLE interactions
STORED AS AVRO
LOCATION 'project/warehouse/interactions'
TBLPROPERTIES ('avro.schema.url'='project/warehouse/avsc/interactions.avsc');

SHOW TABLES;
SELECT 'tracks_count'       AS metric, COUNT(*) AS value FROM tracks;
SELECT 'interactions_count' AS metric, COUNT(*) AS value FROM interactions;

SET hive.exec.dynamic.partition              = true;
SET hive.exec.dynamic.partition.mode         = nonstrict;
SET hive.enforce.bucketing                   = true;
SET hive.exec.max.dynamic.partitions         = 5000;
SET hive.exec.max.dynamic.partitions.pernode = 2000;
SET hive.execution.engine                    = tez;

-- year is omitted from the column list because it becomes the partition key;
-- `key` and `mode` are HiveQL reserved words and must be back-ticked.
DROP TABLE IF EXISTS tracks_part;
CREATE EXTERNAL TABLE tracks_part(
    id               STRING,
    name             STRING,
    album            STRING,
    album_id         STRING,
    artists          STRING,
    artist_ids       STRING,
    track_number     INT,
    disc_number      INT,
    explicit         BOOLEAN,
    danceability     DOUBLE,
    energy           DOUBLE,
    `key`            INT,
    loudness         DOUBLE,
    `mode`           INT,
    speechiness      DOUBLE,
    acousticness     DOUBLE,
    instrumentalness DOUBLE,
    liveness         DOUBLE,
    valence          DOUBLE,
    tempo            DOUBLE,
    duration_ms      INT,
    time_signature   DOUBLE,
    release_date     STRING
)
PARTITIONED BY (year INT)
CLUSTERED BY  (id) INTO 11 BUCKETS
STORED AS AVRO
LOCATION 'project/hive/warehouse/tracks_part'
TBLPROPERTIES ('AVRO.COMPRESS'='SNAPPY');

INSERT OVERWRITE TABLE tracks_part PARTITION (year)
SELECT
    id, name, album, album_id, artists, artist_ids,
    track_number, disc_number, explicit,
    danceability, energy, `key`, loudness, `mode`,
    speechiness, acousticness, instrumentalness,
    liveness, valence, tempo,
    duration_ms, time_signature, release_date,
    year
FROM tracks;

-- interaction_flag is the binary target for stage 3 ML, so partitioning
-- by it gives free class-based pruning at training time.
DROP TABLE IF EXISTS interactions_part;
CREATE EXTERNAL TABLE interactions_part(
    id      INT,
    user_id STRING,
    item_id STRING,
    ts      BIGINT
)
PARTITIONED BY (interaction_flag INT)
CLUSTERED BY  (user_id) INTO 11 BUCKETS
STORED AS AVRO
LOCATION 'project/hive/warehouse/interactions_part'
TBLPROPERTIES ('AVRO.COMPRESS'='SNAPPY');

INSERT OVERWRITE TABLE interactions_part PARTITION (interaction_flag)
SELECT id, user_id, item_id, ts, interaction_flag
FROM interactions;

-- Drop the un-optimised tables (checklist requirement). Because they are
-- EXTERNAL the underlying AVRO files in project/warehouse/ are kept on HDFS.
DROP TABLE IF EXISTS tracks;
DROP TABLE IF EXISTS interactions;

SHOW TABLES;
SHOW PARTITIONS tracks_part;
SHOW PARTITIONS interactions_part;
DESCRIBE FORMATTED tracks_part;
DESCRIBE FORMATTED interactions_part;
SELECT 'tracks_part'       AS metric, COUNT(*) AS value FROM tracks_part;
SELECT 'interactions_part' AS metric, COUNT(*) AS value FROM interactions_part;
