-- Test queries to verify the data was loaded correctly into PostgreSQL
-- These queries are executed by scripts/build_projectdb.py after data import

-- Check row counts
SELECT 'tracks' AS table_name, COUNT(*) AS row_count FROM tracks;
SELECT 'interactions' AS table_name, COUNT(*) AS row_count FROM interactions;

-- Preview tracks table
SELECT * FROM tracks LIMIT 5;

-- Preview interactions table
SELECT * FROM interactions LIMIT 5;

-- Check for NULL values in key columns
SELECT
    COUNT(*) AS total,
    COUNT(name) AS non_null_name,
    COUNT(album) AS non_null_album,
    COUNT(danceability) AS non_null_danceability
FROM tracks;

-- Verify FK integrity: all item_ids in interactions exist in tracks
SELECT COUNT(*) AS orphan_interactions
FROM interactions i
LEFT JOIN tracks t ON i.item_id = t.id
WHERE t.id IS NULL;

-- Basic statistics on interactions
SELECT
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT item_id) AS unique_tracks,
    MIN(ts) AS min_timestamp,
    MAX(ts) AS max_timestamp
FROM interactions;
