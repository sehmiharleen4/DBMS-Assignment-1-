#!/usr/bin/env python3
"""Generate a synthetic social network (Barabasi-Albert preferential attachment).

Writes  persons.csv (id,name,age)  friendships.csv (a,b with a<b, one row per
undirected edge)  starts.csv (id,kind)  into --out. Fully deterministic given --seed.
No real personal data is used (assignment ethics rule).
"""
import argparse
import csv
import os
import random
from collections import Counter


def generate_edges(n: int, m: int, seed: int):
    rng = random.Random(seed)
    m0 = m + 1
    edges, pool = [], []
    for i in range(m0):                      # seed clique
        for j in range(i + 1, m0):
            edges.append((i, j)); pool += [i, j]
    for v in range(m0, n):
        chosen = set()
        while len(chosen) < m:
            chosen.add(rng.choice(pool))     # probability proportional to degree
        for u in sorted(chosen):
            edges.append((u, v)); pool += [u, v]
    return edges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True, help="number of persons")
    ap.add_argument("--m", type=int, default=5, help="edges added per new person")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--random-starts", type=int, default=30)
    ap.add_argument("--hub-starts", type=int, default=5)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rng = random.Random(a.seed + 1)

    edges = generate_edges(a.n, a.m, a.seed)
    with open(f"{a.out}/persons.csv", "w", newline="") as f:
        w = csv.writer(f)
        for i in range(a.n):
            w.writerow([i, f"user{i}", rng.randint(18, 80)])
    with open(f"{a.out}/friendships.csv", "w", newline="") as f:
        csv.writer(f).writerows(edges)

    deg = Counter()
    for u, v in edges:
        deg[u] += 1; deg[v] += 1
    hubs = [i for i, _ in deg.most_common(a.hub_starts)]
    rand = rng.sample([i for i in range(a.n) if i not in set(hubs)], a.random_starts)
    with open(f"{a.out}/starts.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "kind"])
        for i in rand: w.writerow([i, "random"])
        for i in hubs: w.writerow([i, "hub"])
    print(f"n={a.n} edges={len(edges)} max_degree={max(deg.values())} "
          f"avg_degree={2*len(edges)/a.n:.2f}")


if __name__ == "__main__":
    main()
