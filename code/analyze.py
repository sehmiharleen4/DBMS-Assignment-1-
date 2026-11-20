#!/usr/bin/env python3
"""Turn results/raw.csv into figures, a LaTeX table and LaTeX macros for the paper.

Outputs (default ../paper): figs/fig_latency.pdf, figs/fig_scaling.pdf,
results_table.tex, results_numbers.tex.  Also prints a correctness report:
all systems must return identical counts for every (n, depth, start).
"""
import argparse
import os

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
    return f"{x:.2f}" if x < 10 else (f"{x:.1f}" if x < 1000 else f"{x:,.0f}".replace(",", "\\,"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="../results/raw.csv")
    ap.add_argument("--paper", default="../paper")
    a = ap.parse_args()
    os.makedirs(f"{a.paper}/figs", exist_ok=True)
    df = pd.read_csv(a.raw)
    ok = df[df.status == "ok"].copy()
    ok["ms"] = ok.ms.astype(float)

    # ---------- correctness: every system must agree ----------
    first = ok[ok.rep == 1].pivot_table(index=["n", "depth", "start_id"], columns="system",
                                        values="count", aggfunc="first").dropna()
    all_match = bool((first.nunique(axis=1) == 1).all()) if len(first) else False
    print(f"correctness: {len(first)} comparable queries, all systems agree = {all_match}")
    if not all_match:
        print(first[first.nunique(axis=1) > 1].head(20))

    # ---------- summaries ----------
    per_start = ok.groupby(["system", "n", "depth", "start_id", "kind"]).ms.median().reset_index()
    summ = per_start.groupby(["system", "n", "depth"]).ms.agg(
        median="median", p95=lambda s: s.quantile(.95)).reset_index()
    to = df[df.status == "timeout"].groupby(["system", "n", "depth"]).size().rename("timeouts")
    summ = summ.merge(to.reset_index(), how="outer", on=["system", "n", "depth"]).fillna({"timeouts": 0})
    summ.to_csv(f"{a.paper}/../results/summary.csv", index=False)
    print(summ.to_string(index=False))
    sizes = sorted(summ.n.unique()); depths = sorted(summ.depth.unique())
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
        ax.set_yscale("log"); ax.set_xticks(depths); ax.set_xlabel("hops $k$")
        ax.set_title(f"$n$ = {n:,}", fontsize=8); ax.grid(alpha=.3, which="both", lw=.3)
    axes[0].set_ylabel("latency (ms, log)")
    axes[0].legend(fontsize=5.5)
    fig.tight_layout(); fig.savefig(f"{a.paper}/figs/fig_latency.pdf"); plt.close(fig)

    # ---------- figure 2: scaling with graph size at fixed depth ----------
    kfix = 3 if 3 in depths else depths[-1]
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    for s in LABEL:
        d = summ[(summ.system == s) & (summ.depth == kfix)].sort_values("n")
        if d.empty:
            continue
        c, mk = STYLE[s]
        ax.plot(d.n, d["median"], marker=mk, color=c, label=LABEL[s])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("persons $n$"); ax.set_ylabel(f"median latency (ms), $k$={kfix}")
    ax.grid(alpha=.3, which="both", lw=.3); ax.legend(fontsize=6)
    fig.tight_layout(); fig.savefig(f"{a.paper}/figs/fig_scaling.pdf"); plt.close(fig)

    # ---------- LaTeX table for the largest graph ----------
    rows = []
    for k in depths:
        cells, med = [], {}
        for s in LABEL:
            r = summ[(summ.system == s) & (summ.n == big) & (summ.depth == k)]
            if r.empty:
                cells.append("--"); continue
            r = r.iloc[0]; med[s] = r["median"]
            t = f" ({int(r.timeouts)} t/o)" if r.timeouts else ""
            cells.append(f"{fmt(r['median'])} [{fmt(r.p95)}]{t}")
        sp = f"{med['pg_cte']/med['neo4j']:.1f}$\\times$" if {"pg_cte", "neo4j"} <= med.keys() else "--"
        rows.append(f"{k} & " + " & ".join(cells) + f" & {sp} \\\\")
    with open(f"{a.paper}/results_table.tex", "w") as f:
        f.write("\\begin{tabular}{@{}rccc r@{}}\n\\toprule\n"
                "$k$ & Rec.\\ CTE & Level-wise & Neo4j & CTE/Neo4j \\\\\n\\midrule\n"
                + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

    # ---------- macros ----------
    out = ["% AUTO-GENERATED by analyze.py -- do not edit by hand",
           f"\\renewcommand{{\\resNLarge}}{{{big:,}}}".replace(",", "\\,"),
           f"\\renewcommand{{\\resAllMatch}}{{{'yes' if all_match else 'NO'}}}"]
    for s, name in MACRO.items():
        for k in depths:
            r = summ[(summ.system == s) & (summ.n == big) & (summ.depth == k)]
            if not r.empty and k in WORD:
                out.append(f"\\renewcommand{{\\res{name}{WORD[k]}}}{{{fmt(r.iloc[0]['median'])}}}")
    for k in (3, 4):
        g = lambda s: summ[(summ.system == s) & (summ.n == big) & (summ.depth == k)]
        if not g("pg_cte").empty and not g("neo4j").empty:
            out.append(f"\\renewcommand{{\\resSpeedCte{WORD[k]}}}"
                       f"{{{g('pg_cte').iloc[0]['median']/g('neo4j').iloc[0]['median']:.1f}}}")
        if not g("pg_levels").empty and not g("neo4j").empty:
            out.append(f"\\renewcommand{{\\resSpeedLevels{WORD[k]}}}"
                       f"{{{g('pg_levels').iloc[0]['median']/g('neo4j').iloc[0]['median']:.1f}}}")
    with open(f"{a.paper}/results_numbers.tex", "w") as f:
        f.write("\n".join(out) + "\n")
    print("wrote figures, results_table.tex, results_numbers.tex")


if __name__ == "__main__":
    main()
