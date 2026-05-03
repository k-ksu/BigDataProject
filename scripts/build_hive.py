"""run stage 2 hive scripts through hivejdbc."""

import logging
import os
import sys

from hivejdbc import connect

HIVE_HOST = "hadoop-03.uni.innopolis.ru"
HIVE_PORT = 10001
HIVE_USER = "team11"
HIVE_DB = "default"
HIVE_JAR = "/shared/hive-jdbc-3.1.3-standalone.jar"

SQL_DIR = "sql"
DDL_FILE = os.path.join(SQL_DIR, "db.hql")
EDA_FILES = [os.path.join(SQL_DIR, f"q{i}.hql") for i in range(1, 6)]

SECRETS = ["secrets/.hive.pass", "secrets/.psql.pass"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def read_password():
    """read the hive password from local secrets."""
    for path in SECRETS:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                pwd = fh.read().strip()
            if pwd:
                return pwd
    log.error("No password file found. Tried: %s", SECRETS)
    sys.exit(1)


def split_statements(sql_text):
    """split hql text into executable statements."""
    stmts, buf, in_str = [], [], False
    for raw in sql_text.splitlines():
        line = raw.split("--", 1)[0]
        if not line.strip():
            continue
        for ch in line:
            if ch == "'":
                in_str = not in_str
            if ch == ";" and not in_str:
                s = "".join(buf).strip()
                if s:
                    stmts.append(s)
                buf = []
            else:
                buf.append(ch)
        buf.append(" ")
    tail = "".join(buf).strip()
    if tail:
        stmts.append(tail)
    return stmts


def run_script(cur, path):
    """run one hql script through the open cursor."""
    log.info("Running %s", path)
    with open(path, "r", encoding="utf-8") as fh:
        statements = split_statements(fh.read())
    for i, stmt in enumerate(statements, 1):
        preview = stmt[:120].replace("\n", " ") + ("..." if len(stmt) > 120 else "")
        log.info("  [%d/%d] %s", i, len(statements), preview)
        cur.execute(stmt)
        if cur.description:
            rows = cur.fetchall()
            if rows:
                log.info("       -> %d row(s)", len(rows))


def main():
    """run the stage 2 hive build and eda scripts."""
    password = read_password()
    log.info("Connecting to %s:%s as %s", HIVE_HOST, HIVE_PORT, HIVE_USER)
    conn = connect(
        host=HIVE_HOST, port=HIVE_PORT, driver=HIVE_JAR,
        database=HIVE_DB, user=HIVE_USER, password=password,
    )
    cur = conn.cursor()
    run_script(cur, DDL_FILE)
    for q in EDA_FILES:
        if os.path.isfile(q):
            run_script(cur, q)


if __name__ == "__main__":
    main()
