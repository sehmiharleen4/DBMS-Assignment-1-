#!/usr/bin/env bash
# One-shot reproduction. Usage:  ./run_all.sh            (sizes 1k, 10k, 100k)
#                                SIZES="1000 10000" ./run_all.sh
set -euo pipefail
cd "$(dirname "$0")"
SIZES=${SIZES:-"1000 10000 100000"}
python selftest.py
docker compose up -d
echo "Waiting for databases..."; sleep 40
rm -f ../results/raw.csv
for N in $SIZES; do
  python generate_graph.py --n "$N" --m 5 --seed 42 --out "../data/n$N"
  python load_postgres.py --data "../data/n$N"
  python load_neo4j.py   --data "../data/n$N"
  for SYS in pg_cte pg_levels neo4j; do
    python benchmark.py --system "$SYS" --n "$N" --data "../data/n$N" --depths 1 2 3 4 --reps 5
  done
done
python analyze.py
echo "Done. Now rebuild the paper (Overleaf: upload paper/ incl. figs and results_*.tex)."
