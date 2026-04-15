COPY tracks FROM STDIN WITH CSV HEADER DELIMITER ',' NULL AS '';
COPY interactions(user_id, item_id, interaction_flag, ts) FROM STDIN WITH CSV HEADER DELIMITER ',' NULL AS '';
