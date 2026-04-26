"""
Stage 2 - alternative entry point: run sql/db.hql + sql/q*.hql via hivejdbc.

Equivalent to the  beeline -f  calls inside  scripts/stage2.sh , but driven
from a single Python process so the pipeline can be invoked from notebooks
or schedulers (Airflow, etc).

Usage:
    python scripts/build_hive.py

Requires hivejdbc and a JDK on PATH; on the IU cluster the standalone Hive
JDBC jar is at  /shared/hive-jdbc-3.1.3-standalone.jar .
"""

import logging
import os
import sys

HIVE_HOST = "hadoop-03.uni.innopolis.ru"
HIVE_PORT = 10001
HIVE_USER = "team11"
HIVE_DB = "default"
HIVE_JAR = "/shared/hive-jdbc-3.1.3-standalone.jar"

SQL_DIR = "sql"
DDL_FILE = os.path.join(SQL_DIR, "db.hql")
EDA_FILES = [os.path.join(SQL_DIR, f"q{i}.hql") for i in range(1, 6)]

SECRETS = ["secrets/.hive.pass", "secrets/.psql.pass"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def read_password() -> str:
    """Return the cluster password from the first existing secrets file."""
    for path in SECRETS:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                pwd = fh.read().strip()
            if pwd:
                log.info("Using password from %s", path)
                return pwd
    log.error("No password file found. Tried: %s", SECRETS)
    sys.exit(1)


def split_statements(sql_text: str):
    """
    Split a HiveQL script into individual statements.

    The Hive JDBC driver only accepts one statement per execute() call, so
    we have to break the file ourselves. Single quotes are tracked so that
    semicolons inside string literals do not terminate a statement.
    """
    stmts, buf, in_str = [], [], False
    for raw_line in sql_text.splitlines():
        line = raw_line.split("--", 1)[0]
        if not line.strip():
            continue
        for ch in line:
            if ch == "'":
                in_str = not in_str
            if ch == ";" and not in_str:
                stmt = "".join(buf).strip()
                if stmt:
                    stmts.append(stmt)
                buf = []
            else:
                buf.append(ch)
        buf.append(" ")
    tail = "".join(buf).strip()
    if tail:
        stmts.append(tail)
    return stmts


def run_script(cur, path: str) -> None:
    """Execute every statement in the given .hql file, in order."""
    log.info("Running %s ...", path)
    with open(path, "r", encoding="utf-8") as fh:
        statements = split_statements(fh.read())
    for i, stmt in enumerate(statements, 1):
        preview = stmt[:120].replace("\n", " ") + ("..." if len(stmt) > 120 else "")
        log.info("  [%d/%d] %s", i, len(statements), preview)
        try:
            cur.execute(stmt)
            try:
                rows = cur.fetchall()
                if rows:
                    log.info("       -> %d row(s) returned", len(rows))
            except Exception:                           # noqa: BLE001
                pass
        except Exception as exc:                        # noqa: BLE001
            log.error("       FAILED: %s", exc)
            raise


def main() -> None:
    """Main entry point."""
    try:
        from hivejdbc import connect
    except ImportError:
        log.error("hivejdbc is not installed. Run:  pip install hivejdbc")
        sys.exit(1)

    password = read_password()
    log.info("Connecting to %s:%s as %s ...", HIVE_HOST, HIVE_PORT, HIVE_USER)
    conn = connect(
        host=HIVE_HOST,
        port=HIVE_PORT,
        driver=HIVE_JAR,
        database=HIVE_DB,
        user=HIVE_USER,
        password=password,
    )
    cur = conn.cursor()

    run_script(cur, DDL_FILE)
    for q in EDA_FILES:
        if os.path.isfile(q):
            run_script(cur, q)

    log.info("All Hive scripts finished.")


if __name__ == "__main__":
    main()
