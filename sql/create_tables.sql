-- Stage 1: Create tables for music interaction dataset
-- This script is idempotent — safe to run multiple times

START TRANSACTION;

-- Drop existing tables (order matters due to FK dependencies)
DROP TABLE IF EXISTS interactions CASCADE;
DROP TABLE IF EXISTS tracks CASCADE;

-- =============================================================
-- Table: tracks (from tracks_features.csv)
-- 1,204,025 rows, 24 columns
-- =============================================================
CREATE TABLE IF NOT EXISTS tracks (
    id                  VARCHAR(50)      NOT NULL PRIMARY KEY,
    name                TEXT,
    album               TEXT,
    album_id            VARCHAR(50),
    artists             TEXT             NOT NULL,
    artist_ids          TEXT             NOT NULL,
    track_number        INTEGER,
    disc_number         INTEGER,
    explicit            BOOLEAN,
    danceability        DOUBLE PRECISION,
    energy              DOUBLE PRECISION,
    key                 INTEGER,
    loudness            DOUBLE PRECISION,
    mode                INTEGER,
    speechiness         DOUBLE PRECISION,
    acousticness        DOUBLE PRECISION,
    instrumentalness    DOUBLE PRECISION,
    liveness            DOUBLE PRECISION,
    valence             DOUBLE PRECISION,
    tempo               DOUBLE PRECISION,
    duration_ms         INTEGER,
    time_signature      DOUBLE PRECISION,
    year                INTEGER,
    release_date        VARCHAR(20)
);

-- =============================================================
-- Table: interactions (from interaction.csv)
-- 11,808,554 rows, 4 columns
-- SERIAL PK because there are ~111K duplicate (user_id, item_id) pairs
-- Column renames: exists -> interaction_flag (reserved word)
--                 timestamp -> ts (reserved word)
-- =============================================================
CREATE TABLE IF NOT EXISTS interactions (
    id                  SERIAL           PRIMARY KEY,
    user_id             VARCHAR(50)      NOT NULL,
    item_id             VARCHAR(50)      NOT NULL,
    interaction_flag    INTEGER          NOT NULL DEFAULT 1,
    ts                  BIGINT           NOT NULL
);

-- =============================================================
-- Constraints
-- =============================================================

-- FK: every interaction references an existing track
ALTER TABLE interactions
    ADD CONSTRAINT fk_interactions_item
    FOREIGN KEY (item_id) REFERENCES tracks(id);

-- Indexes for faster lookups and joins
CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_item_id ON interactions(item_id);
CREATE INDEX IF NOT EXISTS idx_interactions_ts      ON interactions(ts);

COMMIT;
