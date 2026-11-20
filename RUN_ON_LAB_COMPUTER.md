# Run the G9 benchmark on another computer

Use this guide on a group member's computer or a lab computer. The benchmark needs Docker Desktop because it starts PostgreSQL 16 and Neo4j 5.26 in matched containers.

## Before starting

- Install and open Docker Desktop. Wait until it says the engine is running.
- Allow Docker at least 8 CPU cores if available and 12 GB of memory. The project containers use up to 6 GB each, so 16 GB of system RAM is the practical minimum.
- Install Python 3.10 or later and Git.
- Copy the whole `G9_submission_kit` folder to a local drive. Do not run it from cloud-sync storage if that storage blocks Docker volume access.

## First run

Open a terminal in `G9_submission_kit/code` and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python selftest.py
SIZES="1000 10000" ./run_all.sh
```

This small run checks that Docker, both database drivers, and the analysis stage work. It may take several minutes while Neo4j starts and data load.

## Full run

After the small run completes and says all systems agree, run:

```bash
rm -f ../results/raw.csv ../results/summary.csv
rm -f ../paper/results_table.tex ../paper/results_numbers.tex
rm -f ../paper/figs/*.pdf
./run_all.sh
```

Keep the computer plugged in. The 100,000-person graph may take more than an hour, depending on hardware. Do not browse Neo4j Browser during the timed part.

## Validate results

Open `results/summary.csv`. Check that each system has values for each graph size and depth. Read the final console line from `analyze.py`; it must report `all systems agree = True`.

If a query has a timeout, retain it. It is a real result. Do not delete a timeout just to make a graph look better.

## Copy results into the paper

The script writes the following files automatically:

- `paper/figs/fig_latency.pdf`
- `paper/figs/fig_scaling.pdf`
- `paper/results_table.tex`
- `paper/results_numbers.tex`

Upload the complete `paper/` folder to an Overleaf project that uses the IEEE conference template. The paper reads the generated values automatically. It still needs the team identity, hardware description, GitHub URL, EXPLAIN-plan summary, and result interpretation before submission.

## Stop the databases when finished

```bash
docker compose down
```

Use `docker compose down -v` only if you are sure you no longer need the local database volumes. It deletes the loaded data.
