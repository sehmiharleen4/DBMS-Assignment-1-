# Graph traversal versus relational recursion

This repository contains the paper source, literature matrix, and benchmark code for DBMS Assignment 1, Group G9. The proposed experiment compares Neo4j 5 with PostgreSQL 16 on a friends-within-k-hops query over synthetic social graphs.

## Project overview

The benchmark is designed to measure how query time changes with graph size, traversal depth, and the degree of the starting node. It compares three formulations of the same reachability-count query:

- Neo4j Cypher variable-length traversal
- PostgreSQL recursive CTE
- PostgreSQL level-wise joins with duplicate removal at each level

The repository uses deterministic Barabasi-Albert graph generation. No real personal data are used.

## Team

- Harleen Kaur
- Gurveer Singh Brar
- Hardik Jassar
- Harmanparteek Singh
- Faculty mentor: Dr. Vijay Kumar

The paper includes a draft contribution statement. The group must check and correct it to reflect the work each person actually completed.

## Repository structure

```text
.
├── G9_DBMS_Research_Paper.tex    IEEE article source
├── benchmark.py                  Root benchmark runner
├── benchmark_results.csv         Empty results file until the benchmark is run
├── docker-compose.yml            PostgreSQL and Neo4j containers
├── literature_matrix.csv         GitHub-friendly literature-review matrix
├── literature_matrix.xlsx        Spreadsheet version for submission
├── PEER_REVIEW.md                Deliverable 6: Exemplary peer review & blank template
├── PEER_REVIEW_FORM.md           Deliverable 6: Official submitted peer review form
├── PLAGIARISM_REPORT_AND_GUIDE.md Deliverable 4: Turnitin compliance audit & protocol
├── plots/                        Figure instructions; no measured plots yet
├── presentation_and_viva.md      Eight-slide talk plan and viva answers
├── requirements.txt              Python packages
├── code/                         Generator, loaders, query builders, harness, analysis
└── paper/                        Article assets and auto-generated LaTeX result files
```

## Quick start

Requirements: Python 3.10 or later, Docker Desktop, and at least 16 GB RAM.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python code/selftest.py
python benchmark.py --quick
```

The quick run uses 1,000 and 10,000 person graphs. After it completes and reports identical counts across all systems, run the full benchmark:

```bash
python benchmark.py --full
```

The benchmark writes raw measurements to `results/raw.csv`, summaries and figures under `results/` and `paper/figs/`, and LaTeX result files after a real database run.

## Article, results, and submission

Upload the complete repository to Overleaf and compile `paper/main.tex`. `G9_DBMS_Research_Paper.tex` is a root-level entry point kept for the same repository layout as the reference project. The paper currently reviews published benchmark results and describes an unrun G9 experiment. Add the authors' email addresses if required, and check the contribution statement and AI-use note against the group's actual work.

`SUBMIT_AFTER_RESULTS.md` gives the full final checklist. `RUN_ON_LAB_COMPUTER.md` gives a step-by-step guide for a computer that can run Docker.

## Integrity

The repository contains no fabricated benchmark data. `benchmark_results.csv` has only its header until a genuine benchmark run produces measurements. Verify every reference in the literature matrix against its original source. Run the institute's checker on the final PDF and attach the required similarity report.
