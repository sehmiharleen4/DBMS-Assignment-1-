#!/usr/bin/env python3
"""Turn results/raw.csv into figures, a LaTeX table and LaTeX macros for the paper.

Outputs (default ../paper): figs/fig_latency.pdf, figs/fig_scaling.pdf,
results_table.tex, results_numbers.tex.

Enforces strict correctness:
- Mismatched query counts across systems will fail the analysis.
- Calculates both true repetition p95 and per-start medians.
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

LABEL = {"pg_cte": "PostgreSQL recursive CTE", "pg_levels": "PostgreSQL level-wise joins",
         "neo4j": "Neo4j (Cypher)"}
MACRO = {"pg_cte": "Cte", "pg_levels": "Levels", "neo4j": "Neo"}
WORD = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five"}
STYLE = {"pg_cte": ("tab:blue", "o"), "pg_levels": ("tab:green", "s"), "neo4j": ("tab:red", "^")}


def fmt(x):
    if pd.isna(x):
        return "--"
    return f"{x:.2f}" if x < 10 else (f"{x:.1f}" if x < 1000 else f"{x:,.0f}".replace(",", "\\,"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="../results/raw.csv")
    ap.add_argument("--paper", default="../paper")
    ap.add_argument("--strict", action="store_true", default=True,
                    help="Fail with non-zero exit code if results mismatch")
    a = ap.parse_args()
    os.makedirs(f"{a.paper}/figs", exist_ok=True)

    if not os.path.exists(a.raw):
        print(f"Notice: Raw benchmark results file '{a.raw}' does not exist.")
        sys.exit(0)

    df = pd.read_csv(a.raw)
    if df.empty or len(df.dropna(how="all")) == 0:
        print(f"Notice: '{a.raw}' is empty or contains only headers.")
        sys.exit(0)

    ok = df[df.status == "ok"].copy()
    if ok.empty:
        print("Warning: No successful ('ok') runs found in raw benchmark data.")
        sys.exit(0)

    ok["ms"] = ok.ms.astype(float)

    # ---------- correctness: every system must agree on returned counts ----------
    # Group by (n, depth, start_id) and check count consistency across systems
    pivot_counts = ok[ok.rep == 1].pivot_table(
        index=["n", "depth", "start_id"],
        columns="system",
        values="count",
        aggfunc="first"
    )

    # Identify any mismatches where multiple systems ran and produced different counts
    mismatches = pivot_counts[pivot_counts.nunique(axis=1) > 1]
    all_match = len(mismatches) == 0

    print(f"Correctness audit: {len(pivot_counts)} evaluated query points.")
    if not all_match:
        print(f"ERROR: Detected {len(mismatches)} query results with divergent counts between systems!")
        print(mismatches.head(25))
        if a.strict:
            sys.exit("FATAL: Benchmark failed correctness audit. Aborting analysis to prevent invalid reporting.")
    else:
        print("PASS: All systems returned mathematically identical friend counts across all comparable queries.")

    # Check for missing systems (e.g. one system ran but another was omitted without timeout)
    present_systems = set(ok.system.unique())
    expected_systems = set(LABEL.keys())
    missing_systems = expected_systems - present_systems
    if missing_systems:
        print(f"Note: Systems not present in dataset: {missing_systems}")

    # ---------- summaries ----------
    # 1. True p95 across all individual timed repetitions
    true_stats = ok.groupby(["system", "n", "depth"]).ms.agg(
        median="median",
        p95=lambda s: s.quantile(0.95),
        mean="mean",
        std="std"
    ).reset_index()

    # 2. Per-start statistics (to evaluate start-node degree sensitivity)
    per_start = ok.groupby(["system", "n", "depth", "start_id", "kind"]).ms.median().reset_index()
    start_stats = per_start.groupby(["system", "n", "depth"]).ms.agg(
        start_median="median",
        start_p95=lambda s: s.quantile(0.95)
    ).reset_index()

    summ = true_stats.merge(start_stats, on=["system", "n", "depth"])

    # 3. Timeouts count
    to = df[df.status == "timeout"].groupby(["system", "n", "depth"]).size().rename("timeouts")
    summ = summ.merge(to.reset_index(), how="outer", on=["system", "n", "depth"]).fillna({"timeouts": 0})

    results_dir = os.path.abspath(os.path.join(a.paper, "..", "results"))
    os.makedirs(results_dir, exist_ok=True)
    summ.to_csv(f"{results_dir}/summary.csv", index=False)
    print("\nBenchmark Summary Table:")
    print(summ[["system", "n", "depth", "median", "p95", "timeouts"]].to_string(index=False))

    sizes = sorted(summ.n.dropna().unique())
    depths = sorted(summ.depth.dropna().unique())
    if not sizes or not depths:
        print("No valid benchmark grid points found.")
        sys.exit(0)

    big = sizes[-1]

    # ---------- figure 1: latency vs depth, one panel per graph size ----------
    fig, axes = plt.subplots(1, len(sizes), figsize=(3.4 * len(sizes) / 1.6 + 1, 2.6), sharey=True)
    axes = [axes] if len(sizes) == 1 else list(axes)
    for ax, n in zip(axes, sizes):
        for s in LABEL:
            d = summ[(summ.system == s) & (summ.n == n)].sort_values("depth")
            if d.empty:
                continue
            c, mk = STYLE[s]
            ax.plot(d.depth, d["median"], marker=mk, color=c, label=LABEL[s])
            ax.fill_between(d.depth, d["median"], d.p95, color=c, alpha=.12)
        ax.set_yscale("log")
        ax.set_xticks(depths)
        ax.set_xlabel("hops $k$")
        ax.set_title(f"$n$ = {int(n):,}", fontsize=8)
        ax.grid(alpha=.3, which="both", lw=.3)
    axes[0].set_ylabel("latency (ms, log)")
    axes[0].legend(fontsize=5.5)
    fig.tight_layout()
    fig.savefig(f"{a.paper}/figs/fig_latency.pdf")
    plt.close(fig)

    # ---------- figure 2: scaling with graph size at fixed depth ----------
    kfix = 3 if 3 in depths else depths[-1]
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    for s in LABEL:
        d = summ[(summ.system == s) & (summ.depth == kfix)].sort_values("n")
        if d.empty:
            continue
        c, mk = STYLE[s]
        ax.plot(d.n, d["median"], marker=mk, color=c, label=LABEL[s])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("persons $n$")
    ax.set_ylabel(f"median latency (ms), $k$={int(kfix)}")
    ax.grid(alpha=.3, which="both", lw=.3)
    ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(f"{a.paper}/figs/fig_scaling.pdf")
    plt.close(fig)

    # ---------- LaTeX table for the largest graph ----------
    rows = []
    for k in depths:
        cells, med = [], {}
        for s in LABEL:
            r = summ[(summ.system == s) & (summ.n == big) & (summ.depth == k)]
            if r.empty:
                cells.append("--")
                continue
            r = r.iloc[0]
            med[s] = r["median"]
            t = f" ({int(r.timeouts)} t/o)" if r.timeouts else ""
            cells.append(f"{fmt(r['median'])} [{fmt(r.p95)}]{t}")
        sp = f"{med['pg_cte']/med['neo4j']:.1f}$\\times$" if {"pg_cte", "neo4j"} <= med.keys() and med["neo4j"] > 0 else "--"
        rows.append(f"{int(k)} & " + " & ".join(cells) + f" & {sp} \\\\")

    with open(f"{a.paper}/results_table.tex", "w") as f:
        f.write("\\begin{tabular}{@{}rccc r@{}}\n\\toprule\n"
                "$k$ & Rec.\\ CTE & Level-wise & Neo4j & CTE/Neo4j \\\\\n"
                " & Med [p95] (ms) & Med [p95] (ms) & Med [p95] (ms) & Ratio \\\\\n\\midrule\n"
                + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

    # ---------- macros ----------
    out = ["% AUTO-GENERATED by analyze.py -- do not edit by hand",
           f"\\renewcommand{{\\resNLarge}}{{{int(big):,}}}".replace(",", "\\,"),
           f"\\renewcommand{{\\resAllMatch}}{{{'yes' if all_match else 'NO'}}}"]
    for s, name in MACRO.items():
        for k in depths:
            r = summ[(summ.system == s) & (summ.n == big) & (summ.depth == k)]
            if not r.empty and int(k) in WORD:
                out.append(f"\\renewcommand{{\\res{name}{WORD[int(k)]}}}{{{fmt(r.iloc[0]['median'])}}}")
    for k in (3, 4):
        g = lambda s: summ[(summ.system == s) & (summ.n == big) & (summ.depth == k)]
        if not g("pg_cte").empty and not g("neo4j").empty and g("neo4j").iloc[0]["median"] > 0:
            out.append(f"\\renewcommand{{\\resSpeedCte{WORD[k]}}}"
                       f"{{{g('pg_cte').iloc[0]['median']/g('neo4j').iloc[0]['median']:.1f}}}")
        if not g("pg_levels").empty and not g("neo4j").empty and g("neo4j").iloc[0]["median"] > 0:
            out.append(f"\\renewcommand{{\\resSpeedLevels{WORD[k]}}}"
                       f"{{{g('pg_levels').iloc[0]['median']/g('neo4j').iloc[0]['median']:.1f}}}")
    with open(f"{a.paper}/results_numbers.tex", "w") as f:
        f.write("\n".join(out) + "\n")
    print("Successfully wrote figures, results_table.tex, results_numbers.tex")


if __name__ == "__main__":
    main()
