#!/usr/bin/env python3
"""Offline sanity check (needs no database server).

Builds a small graph, runs the SAME SQL text used for PostgreSQL on SQLite, and checks it
against an independent Python BFS. This validates the query logic (not performance).
Run:  python selftest.py
"""
import os
import sqlite3
import tempfile
from collections import deque

from generate_graph import generate_edges
from queries import cte_sql, levels_sql


def bfs_count(adj, s, k):
    seen, frontier = {s}, deque([(s, 0)])
    while frontier:
        u, d = frontier.popleft()
        if d == k:
            continue
        for v in adj[u]:
            if v not in seen:
                seen.add(v); frontier.append((v, d + 1))
    return len(seen) - 1


def main():
    n, m = 600, 3
    edges = generate_edges(n, m, seed=7)
    assert len(edges) == (m + 1) * m // 2 + (n - (m + 1)) * m, "unexpected edge count"
    assert len(set(edges)) == len(edges), "duplicate edges"
    adj = {i: [] for i in range(n)}
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE friendship(src INT, dst INT, PRIMARY KEY(src,dst))")
    for u, v in edges:
        adj[u].append(v); adj[v].append(u)
        con.executemany("INSERT INTO friendship VALUES (?,?)", [(u, v), (v, u)])
    checked = 0
    for k in (1, 2, 3, 4):
        for s in range(0, n, 37):
            want = bfs_count(adj, s, k)
            for build in (cte_sql, levels_sql):
                got = con.execute(build(k, ":id"), {"id": s}).fetchone()[0]
                assert got == want, (build.__name__, k, s, got, want)
                checked += 1
    print(f"selftest OK: {checked} query results match the BFS oracle "
          f"(n={n}, edges={len(edges)})")


if __name__ == "__main__":
    main()
