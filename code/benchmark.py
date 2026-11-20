#!/usr/bin/env python3
"""Run the multi-hop benchmark for ONE system on the graph currently loaded.

Appends rows to results/raw.csv:
system,n,depth,start_id,kind,rep,ms,count,status
Per (depth,start): 1 un-timed warm-up run, then --reps timed runs.
"""
import argparse
import csv
import os
import platform
import time

from queries import cte_sql, cypher, levels_sql

FIELDS = ["system", "n", "depth", "start_id", "kind", "rep", "ms", "count", "status"]


def make_runner(system, a):
    if system in ("pg_cte", "pg_levels"):
        import psycopg2
        conn = psycopg2.connect(a.pg_dsn); conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"SET statement_timeout = {int(a.timeout * 1000)}")
        build = cte_sql if system == "pg_cte" else levels_sql

        def run(k, sid):
            cur.execute(build(k, "%(id)s"), {"id": sid})
            return cur.fetchone()[0]
        return run
    if system == "neo4j":
        from neo4j import GraphDatabase, Query
        driver = GraphDatabase.driver(a.neo_uri, auth=(a.neo_user, a.neo_password))
        session = driver.session()

        def run(k, sid):
            rec = session.run(Query(cypher(k), timeout=a.timeout), id=sid).single()
            return rec["c"]
        return run
    raise SystemExit(f"unknown system {system}")


def record_env(path):
    mem = ""
    try:
        mem = next(l for l in open("/proc/meminfo") if l.startswith("MemTotal")).strip()
    except Exception:
        pass
    with open(path, "w") as f:
        f.write(f"platform: {platform.platform()}\nprocessor: {platform.processor()}\n"
                f"cpu_count: {os.cpu_count()}\n{mem}\npython: {platform.python_version()}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True, choices=["pg_cte", "pg_levels", "neo4j"])
    ap.add_argument("--n", type=int, required=True, help="graph size label (number of persons)")
    ap.add_argument("--data", required=True, help="dir with starts.csv")
    ap.add_argument("--depths", type=int, nargs="+", default=[1, 2, 3, 4])
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--timeout", type=float, default=60.0, help="seconds")
    ap.add_argument("--out", default="../results/raw.csv")
    ap.add_argument("--pg-dsn", dest="pg_dsn",
                    default="host=localhost port=5432 dbname=g9 user=g9 password=g9pass")
    ap.add_argument("--neo-uri", dest="neo_uri", default="bolt://localhost:7687")
    ap.add_argument("--neo-user", dest="neo_user", default="neo4j")
    ap.add_argument("--neo-password", dest="neo_password", default="g9password123")
    a = ap.parse_args()

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    record_env(os.path.join(os.path.dirname(a.out) or ".", "env.txt"))
    starts = [(int(r["id"]), r["kind"]) for r in csv.DictReader(open(f"{a.data}/starts.csv"))]
    run = make_runner(a.system, a)
    new = not os.path.exists(a.out)
    with open(a.out, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for k in a.depths:
            for sid, kind in starts:
                status, count = "ok", None
                try:
                    run(k, sid)                                  # warm-up (not recorded)
                except Exception as e:                           # timeout or error
                    status = "timeout" if ("timeout" in str(e).lower() or "timed out" in str(e).lower()
                                           or "canceling statement" in str(e).lower()) else "error"
                    w.writerow(dict(system=a.system, n=a.n, depth=k, start_id=sid, kind=kind,
                                    rep=0, ms="", count="", status=status))
                    print(f"{a.system} n={a.n} k={k} start={sid}: {status}"); fh.flush()
                    continue
                for rep in range(1, a.reps + 1):
                    t0 = time.perf_counter()
                    count = run(k, sid)
                    ms = (time.perf_counter() - t0) * 1000
                    w.writerow(dict(system=a.system, n=a.n, depth=k, start_id=sid, kind=kind,
                                    rep=rep, ms=f"{ms:.3f}", count=count, status="ok"))
                fh.flush()
            print(f"{a.system} n={a.n} depth={k} done")


if __name__ == "__main__":
    main()
