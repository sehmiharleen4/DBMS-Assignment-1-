#!/usr/bin/env python3
"""Regenerate article figures from genuine benchmark_results.csv."""
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "benchmark_results.csv"
PAPER = ROOT / "paper"


if not RAW.exists() or RAW.stat().st_size <= len("system,n,depth,start_id,kind,rep,ms,count,status\n"):
    raise SystemExit("benchmark_results.csv has no measurements. Run python benchmark.py --quick or --full first.")

subprocess.run(
    [sys.executable, "analyze.py", "--raw", str(RAW), "--paper", str(PAPER)],
    cwd=ROOT / "code",
    check=True,
)
(ROOT / "plots").mkdir(exist_ok=True)
for plot in (PAPER / "figs").glob("*.pdf"):
    shutil.copy2(plot, ROOT / "plots" / plot.name)
print("Wrote article figures to paper/figs and plots/.")
