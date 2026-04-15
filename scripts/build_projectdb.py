"""
Stage 1: Build PostgreSQL database for music interaction dataset.

This script:
  1. Connects to team11_projectdb on the Hadoop cluster
  2. Creates tables (tracks, interactions) with constraints
  3. Loads data from CSV files using COPY
  4. Runs test queries to verify the data

Usage:
    python scripts/build_projectdb.py

Requirements:
    - psycopg2-binary
    - secrets/.psql.pass must contain the database password
    - data/ must contain interaction.csv and tracks_features.csv
    - sql/ must contain create_tables.sql, import_data.sql, test_database.sql
"""

import logging
import os
import sys
from pprint import pformat

import psycopg2 as psql

DB_HOST = "hadoop-04.uni.innopolis.ru"
DB_PORT = 5432
DB_USER = "team11"
DB_NAME = "team11_projectdb"

SECRETS_FILE = os.path.join("secrets", ".psql.pass")

SQL_DIR = "sql"
DATA_DIR = "data"


IMPORT_FILES = [
    os.path.join(DATA_DIR, "tracks_features.csv"),
    os.path.join(DATA_DIR, "interaction.csv"),
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def read_password(path: str) -> str:
    """Read the database password from a secrets file."""
    if not os.path.isfile(path):
        log.error("Password file not found: %s", path)
        log.error(
            "Create it with:  mkdir -p secrets && echo 'YOUR_PASSWORD' > %s", path
        )
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as fh:
        password = fh.read().strip()
    if not password:
        log.error("Password file is empty: %s", path)
        sys.exit(1)
    return password


def get_connection(password: str):
    """Return a psycopg2 connection to the project database."""
    conn_string = (
        f"host={DB_HOST} port={DB_PORT} "
        f"user={DB_USER} dbname={DB_NAME} "
        f"password={password}"
    )
    log.info("Connecting to %s@%s:%s/%s ...", DB_USER, DB_HOST, DB_PORT, DB_NAME)
    conn = psql.connect(conn_string)
    log.info("Connected successfully.")
    return conn


def run_create_tables(conn):
    """Execute sql/create_tables.sql — drops and recreates all tables."""
    sql_path = os.path.join(SQL_DIR, "create_tables.sql")
    log.info("Running %s ...", sql_path)
    with open(sql_path, "r", encoding="utf-8") as fh:
        sql_content = fh.read()
    with conn.cursor() as cur:
        cur.execute(sql_content)
    conn.commit()
    log.info("Tables created and constraints applied.")


def run_import_data(conn):
    """
    Execute sql/import_data.sql — bulk-load CSV files via COPY ... FROM STDIN.

    Each line in import_data.sql is a separate COPY command.
    The i-th command is paired with the i-th file in IMPORT_FILES.
    """
    sql_path = os.path.join(SQL_DIR, "import_data.sql")
    log.info("Running %s ...", sql_path)

    with open(sql_path, "r", encoding="utf-8") as fh:
        commands = [
            line.strip()
            for line in fh
            if line.strip() and not line.strip().startswith("--")
        ]

    if len(commands) != len(IMPORT_FILES):
        log.error(
            "Mismatch: %d COPY commands but %d data files configured.",
            len(commands),
            len(IMPORT_FILES),
        )
        sys.exit(1)

    for copy_cmd, csv_path in zip(commands, IMPORT_FILES):
        if not os.path.isfile(csv_path):
            log.error("Data file not found: %s", csv_path)
            sys.exit(1)

        file_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
        log.info("Loading %s (%.1f MB) ...", csv_path, file_size_mb)

        with conn.cursor() as cur:
            with open(csv_path, "r", encoding="utf-8") as data_fh:
                cur.copy_expert(copy_cmd, data_fh)

        conn.commit()
        log.info("  -> Done loading %s", csv_path)

    log.info("All data loaded successfully.")


def run_test_queries(conn):
    """Execute sql/test_database.sql — verify data by running SELECT queries."""
    sql_path = os.path.join(SQL_DIR, "test_database.sql")
    log.info("Running %s ...", sql_path)

    with open(sql_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Split on semicolons to get individual statements
    statements = [s.strip() for s in content.split(";") if s.strip()]

    with conn.cursor() as cur:
        for stmt in statements:
            # Skip pure comment blocks
            lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
            clean = "\n".join(lines).strip()
            if not clean:
                continue

            log.info(
                "  Query: %s",
                clean[:120].replace("\n", " ") + ("..." if len(clean) > 120 else ""),
            )
            cur.execute(stmt + ";")

            if cur.description:  # SELECT — has result set
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                log.info("  Columns: %s", columns)
                for row in rows[:10]:  # print at most 10 rows
                    log.info("  %s", pformat(row))
                if len(rows) > 10:
                    log.info("  ... (%d rows total)", len(rows))

    log.info("All test queries passed.")


def main():
    """Main entry point."""
    log.info("=" * 60)
    log.info("Stage 1: Building PostgreSQL database")
    log.info("=" * 60)

    password = read_password(SECRETS_FILE)

    with get_connection(password) as conn:
        # Step 1 — Create tables (idempotent: drops first)
        run_create_tables(conn)

        # Step 2 — Load CSV data
        run_import_data(conn)

        # Step 3 — Verify
        run_test_queries(conn)

    log.info("=" * 60)
    log.info("Database build complete!")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
