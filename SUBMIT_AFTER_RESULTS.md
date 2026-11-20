# G9 submission gate

This folder contains the article source, reproducible benchmark code, a literature matrix, a talk script, and a peer-review form. It is not safe to submit until the items below are complete.

## What has been checked

- `code/selftest.py` completed successfully: 136 SQL query results matched an independent breadth-first-search oracle on a generated graph with 600 nodes and 1,794 undirected edges.
- The paper structure matches the brief: title, abstract, background, related work, methodology, setup, results, conclusion, contribution statement, code link, AI-use note, and references.
- The data generator is deterministic. It creates only synthetic people and friendships.

## Run the real benchmark

Use a computer with Docker Desktop, at least 16 GB of RAM, and a stable power supply. Close memory-heavy applications first.

```bash
cd code
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python selftest.py
SIZES="1000 10000" ./run_all.sh
```

Check the final line from `analyze.py`. It must say that all systems agree. Then run the full set:

```bash
./run_all.sh
```

The scripts create `results/raw.csv`, `results/summary.csv`, `results/env.txt`, two figures, `paper/results_table.tex`, and `paper/results_numbers.tex`.

## Complete the article

1. Copy the computer specification from `results/env.txt` into `paper/main.tex`. Also record the Docker CPU and memory limits from `code/docker-compose.yml`.
2. Add the four student names, affiliation, email addresses, mentor name, and the GitHub repository URL.
3. Run `EXPLAIN (ANALYZE, BUFFERS)` for both PostgreSQL queries and `EXPLAIN` for the Neo4j query. Replace the plan-summary note in Section VI-B with what the plans show.
4. Replace the two interpretation notes in Section VI with conclusions that match the generated table and figures. Do not report a hypothesis as supported unless the results support it.
5. Replace the contribution statement and AI-use note with truthful information about this group.
6. Search the source for `TODO`, `TBD`, `S1 Name`, and `\\tbd`. Resolve every match before compiling.
7. Compile the paper in Overleaf using the IEEE conference template. Confirm that it is 6-8 pages including references and that the abstract is 150-250 words after results are inserted.

## References and matrix

The supplied matrix is a working matrix, not proof that every bibliographic field is correct. Before submission, the literature lead must open the original source for every cited item and check authors, title, venue, year, pages/article number, and DOI or stable URL. Keep at least 15 references, with at least 60% published in 2021-2026. Cite at least three papers from strong DB or systems venues.

## Similarity report

Run the institute's similarity checker on the final PDF, asking it to exclude references where that option exists. The required result is below 10%. If it is above the limit, revise only the flagged prose in your own words, preserve citations, recompile, and run the checker again. Do not alter or misrepresent the report.

## Final upload list

- Article PDF
- Similarity report
- Literature matrix spreadsheet
- Public or instructor-accessible GitHub repository with this `code/` folder and README
- Peer-review form for the assigned group
- Presentation slides or the material in `TALK_SCRIPT.md` converted into your course's slide format

