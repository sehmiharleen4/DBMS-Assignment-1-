#!/usr/bin/env python3
"""Run graph queries over Neo4j and PostgreSQL, measuring latency and checking results.

Records git commit, hardware and software versions in results/env.txt.
Flushes measurements to CSV after each start node.
Catches timeouts and exceptions in both warm-up and timed runs to prevent aborts.
"""
import argparse
import csv
import os
import platform
import subprocess
import time

FIELDS = ["system", "n", "depth", "start_id", "kind", "rep", "ms", "count", "status"]


def get_git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def record_env(path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(f"commit: {get_git_commit()}\n")
        f.write(f"platform: {platform.platform()}\n")
        f.write(f"processor: {platform.processor()}\n")
        f.write(f"python: {platform.python_version()}\n")
        f.write(f"time_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")


def make_runner(system, a):
    if system == "neo4j":
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(f"bolt://{a.host}:{a.neo4j_port}",
                                      auth=(a.neo4j_user, a.neo4j_password))
        def run(k, sid):
            with driver.session() as s:
                res = s.run("MATCH (a:Person {id: $id})-[*1.." + str(k) + "]-(b:Person) "
                            "WHERE a <> b RETURN count(DISTINCT b) AS c", id=sid)
                return res.single()["c"]
        return run

    import psycopg2
    conn = psycopg2.connect(host=a.host, port=a.pg_port, dbname=a.pg_db,
                            user=a.pg_user, password=a.pg_password)
    conn.autocommit = True
    from queries import build_query
    def run(k, sid):
        sql = build_query(system, k, sid)
        with conn.cursor() as cur:
            cur.execute(f"SET statement_timeout = '{a.timeout_ms}';")
            cur.execute(sql)
            return cur.fetchone()[0]
    return run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True, choices=["neo4j", "pg_cte", "pg_levels"])
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--depths", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="results/raw.csv")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--timeout-ms", type=int, default=60000)
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--pg-port", type=int, default=5432)
    ap.add_argument("--pg-db", default="graphbench")
    ap.add_argument("--pg-user", default="postgres")
    ap.add_argument("--pg-password", default="postgres")
    ap.add_argument("--neo4j-port", type=int, default=7687)
    ap.add_argument("--neo4j-user", default="neo4j")
    ap.add_argument("--neo4j-password", default="graphbench123")
    a = ap.parse_args()

    record_env(os.path.join(os.path.dirname(a.out) or ".", "env.txt"))
    starts_file = f"{a.data}/starts.csv"
    if not os.path.exists(starts_file):
        raise FileNotFoundError(f"Missing start nodes file: {starts_file}")

    starts = [(int(r["id"]), r["kind"]) for r in csv.DictReader(open(starts_file))]
    run = make_runner(a.system, a)
    new = not os.path.exists(a.out)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for k in a.depths:
            for sid, kind in starts:
                # 1. Warm-up run with failure handling
                try:
                    run(k, sid)
                except Exception as e:
                    err_msg = str(e).lower()
                    status = "timeout" if ("timeout" in err_msg or "timed out" in err_msg
                                           or "canceling statement" in err_msg) else "error"
                    w.writerow(dict(system=a.system, n=a.n, depth=k, start_id=sid, kind=kind,
                                    rep=0, ms="", count="", status=status))
                    print(f"[WARMUP FAIL] {a.system} n={a.n} k={k} start={sid}: {status} ({e})")
                    fh.flush()
                    continue

                # 2. Timed repetitions with individual failure handling
                for rep in range(1, a.reps + 1):
                    try:
                        t0 = time.perf_counter()
                        count = run(k, sid)
                        ms = (time.perf_counter() - t0) * 1000
                        w.writerow(dict(system=a.system, n=a.n, depth=k, start_id=sid, kind=kind,
                                        rep=rep, ms=f"{ms:.3f}", count=count, status="ok"))
                    except Exception as e:
                        err_msg = str(e).lower()
                        status = "timeout" if ("timeout" in err_msg or "timed out" in err_msg
                                               or "canceling statement" in err_msg) else "error"
                        w.writerow(dict(system=a.system, n=a.n, depth=k, start_id=sid, kind=kind,
                                        rep=rep, ms="", count="", status=status))
                        print(f"[TIMED FAIL] {a.system} n={a.n} k={k} start={sid} rep={rep}: {status} ({e})")
                        break  # Do not hammer system further for this timed-out node
                fh.flush()
            print(f"{a.system} n={a.n} depth={k} done")


if __name__ == "__main__":
    main()
