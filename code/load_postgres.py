#!/usr/bin/env python3
"""Load the generated graph into PostgreSQL (friendship stored in BOTH directions)."""
import argparse
import time

import psycopg2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--dsn", default="host=localhost port=5432 dbname=g9 user=g9 password=g9pass")
    a = ap.parse_args()
    conn = psycopg2.connect(a.dsn); conn.autocommit = True
    cur = conn.cursor()
    t0 = time.perf_counter()
    cur.execute("""
        DROP TABLE IF EXISTS friendship; DROP TABLE IF EXISTS person; DROP TABLE IF EXISTS stage;
        CREATE TABLE person(id int PRIMARY KEY, name text, age int);
        CREATE TABLE stage(a int, b int);
        CREATE TABLE friendship(src int NOT NULL, dst int NOT NULL);
    """)
    with open(f"{a.data}/persons.csv") as f:
        cur.copy_expert("COPY person FROM STDIN WITH CSV", f)
    with open(f"{a.data}/friendships.csv") as f:
        cur.copy_expert("COPY stage FROM STDIN WITH CSV", f)
    cur.execute("""
        INSERT INTO friendship SELECT a, b FROM stage UNION ALL SELECT b, a FROM stage;
        DROP TABLE stage;
        ALTER TABLE friendship ADD PRIMARY KEY (src, dst);   -- the adjacency index
        VACUUM ANALYZE person; VACUUM ANALYZE friendship;
    """)
    load_s = time.perf_counter() - t0
    cur.execute("SELECT pg_total_relation_size('friendship') + pg_total_relation_size('person')")
    size = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM friendship")
    rows = cur.fetchone()[0]
    print(f"postgres: load_seconds={load_s:.1f} total_bytes={size} directed_rows={rows}")


if __name__ == "__main__":
    main()
