SELECT 'tracks' AS table_name, COUNT(*) AS row_count FROM tracks;
SELECT 'interactions' AS table_name, COUNT(*) AS row_count FROM interactions;

SELECT * FROM tracks LIMIT 5;

SELECT * FROM interactions LIMIT 5;

SELECT
    COUNT(*) AS total,
    COUNT(name) AS non_null_name,
    COUNT(album) AS non_null_album,
    COUNT(danceability) AS non_null_danceability
FROM tracks;

SELECT COUNT(*) AS orphan_interactions
FROM interactions i
LEFT JOIN tracks t ON i.item_id = t.id
WHERE t.id IS NULL;

SELECT
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT item_id) AS unique_tracks,
    MIN(ts) AS min_timestamp,
    MAX(ts) AS max_timestamp
FROM interactions;
