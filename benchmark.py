#!/usr/bin/env python3
"""Run the G9 graph-database benchmark from the repository root.

Examples:
  python benchmark.py --quick
  python benchmark.py --full

Docker Desktop must be running. The command delegates to the tested scripts in
code/ and writes real measurements to benchmark_results.csv and results/.
"""
import argparse
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CODE = ROOT / "code"


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--quick", action="store_true", help="run 1,000 and 10,000 person graphs")
    group.add_argument("--full", action="store_true", help="run 1,000, 10,000, and 100,000 person graphs")
    args = parser.parse_args()

    if not shutil.which("docker"):
        raise SystemExit("Docker Desktop is required. See RUN_ON_LAB_COMPUTER.md.")

    env = os.environ.copy()
    if args.quick:
        env["SIZES"] = "1000 10000"
    subprocess.run(["bash", "run_all.sh"], cwd=CODE, env=env, check=True)

    raw = ROOT / "results" / "raw.csv"
    if not raw.exists():
        raise SystemExit("The benchmark did not create results/raw.csv.")
    shutil.copyfile(raw, ROOT / "benchmark_results.csv")
    print("Wrote benchmark_results.csv and generated paper figures.")


if __name__ == "__main__":
    main()

