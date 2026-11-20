# Plan and checklist (deadline: 20 November 2026)

## Who does what (matches the assignment roles)
| Member | Role | Do this |
|---|---|---|
| S1 | Team lead / editor | Abstract, Introduction, Conclusion (finish numbers); weekly log; final formatting; submission |
| S2 | Literature lead | Verify all 24 references and matrix rows; add 3+ recent papers you really read; Zotero; citation check |
| S3 | Implementation lead | Push `code/` to GitHub; run `run_all.sh`; EXPLAIN plans; README fixes; Methodology/Setup accuracy |
| S4 | Analysis lead | Section VI interpretation (replace red TODOs); check figures; plagiarism check; slides |

Everyone: read the whole paper. The viva asks about all sections.

## Submission checklist (from the assignment)
- [ ] Article PDF in IEEE template, 6–8 pages (compile on Overleaf; check page count with references)
- [ ] Abstract 150–250 words with a numeric result (count words after the numbers fill in)
- [ ] RQ1–RQ3 answered explicitly in Results (Sections VI-A, VI-B, VI-C)
- [ ] 15+ references, ≥ 3 top venues, IEEE style, ≥ 60 % from the last 5 years (currently 15 of 24 are 2021 or later; recheck after your edits)
- [ ] `literature_matrix.xlsx` verified
- [ ] GitHub link with README and run instructions (repo must contain `code/`; add a `.gitignore` for `data/` and `.venv/`)
- [ ] Plagiarism report < 10 % (excluding references) from the institute's tool; attach it
- [ ] Contribution statement and AI usage note, truthful
- [ ] Peer review form for the assigned group (specific and constructive – cite section and line)
- [ ] Presentation slides (10 minutes)

## Before you submit: remove placeholders
Search `main.tex` for `TBD`, `TODO`, `S1 Name`, `\tbd`. None may remain.

## Likely viva questions (everyone should answer all)
1. What is index-free adjacency, and does PostgreSQL's index on `src` give the same thing?
2. Why does your recursive CTE use `UNION` and not `UNION ALL`? What would happen with `UNION ALL`?
3. Why do you count distinct end nodes instead of returning paths? How does that change the comparison?
4. Which hypotheses (H1–H4) did the data support, and why?
5. Why store friendships twice in PostgreSQL but once in Neo4j?
6. What does the Barabási–Albert model give you that a random graph would not? What does it fail to capture?
7. How do you know the systems return the same answer?
8. What are the threats to validity? Which one worries you most?
9. Property graph vs RDF: when would you choose RDF?
10. What do GQL and SQL/PGQ add, and how would your query look in SQL/PGQ?
11. What is a warm-up run and why did you use one?
12. How would results change with cold caches or the Enterprise edition?

## 10-minute talk outline (about 8 slides, ~75 s each; each member presents their part)
1. Title + the "people you may know" example (S1)
2. Problem and RQ1–RQ3 (S1)
3. Background: property graph vs RDF, Cypher/GQL/SQL-PGQ, index-free adjacency (S2)
4. Related work in one table and the gap (S2)
5. Method: pipeline figure, three query formulations (S3)
6. Setup and correctness check (S3)
7. Results: latency vs depth figure, scaling, table; H1–H4 verdicts (S4)
8. Conclusion, limitations, future work, thanks/questions (S4)
Practise with a timer; do not read from slides.

## Plagiarism tips (to stay under 10 %)
- Run the tool on the PDF *without* references; ask for the report excluding bibliography.
- Do not copy abstracts or definitions from papers or documentation; if a sentence is flagged, rewrite it from your own understanding.
- Keep any quote under one short phrase, in quotation marks, with a citation.
- Code listings and the vendor names (Neo4j, PostgreSQL, Cypher) can raise the score slightly; that is normal.
