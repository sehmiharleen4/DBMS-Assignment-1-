# Peer Review Report — DBMS Assignment 1

**Reviewing Group:** G9  
**Reviewer Team Members:**  
- Harleen Kaur (`kaurh.it.23@nitj.ac.in`)  
- Gurveer Singh Brar (`brargs.it.23@nitj.ac.in`)  
- Hardik Jassar (`jassarh.it.23@nitj.ac.in`)  
- Harmanparteek Singh (`singhhp.it.23@nitj.ac.in`)  
**Department:** Information Technology, Dr. B. R. Ambedkar National Institute of Technology Jalandhar  
**Faculty Mentor:** Dr. Vijay Kumar  
**Date of Review:** November 20, 2026  

---

## Part I: Formal Review for Assigned Group (Exemplary Submission)

### 1. Metadata
* **Group Reviewed:** Group G8  
* **Paper Title:** *Benchmarking Relational and Non-Relational Paradigms: Key-Value Stores vs. Relational Databases for Real-Time Social Feed Ingestion and Traversal*  
* **Assigned Reviewer:** Group G9  
* **Overall Recommendation:** **Major Revision** (Sound conceptual motivation and good Docker scaffolding, but critical methodological confounds in cache controls, theoretical misconceptions regarding index-free adjacency vs. B-Trees, and unverified query equivalence require correction prior to final archival acceptance).

---

### 2. Summary of the Paper
Group G8 investigates the trade-offs between a relational database (PostgreSQL 16) and a key-value/in-memory store (Redis 7.2) for a social media activity feed workload. The authors evaluate two primary operations: (i) high-throughput post ingestion with fan-out-on-write, and (ii) $k$-degree friend activity retrieval (traversal up to $k=3$ hops). The authors claim that Redis outperforms PostgreSQL by up to $14\times$ on traversal latency and conclude that relational engines are fundamentally unsuited for multi-hop graph reachability due to the logarithmic overhead of B-tree lookups.

While the engineering implementation and Docker automation are well-executed, several methodological flaws compromise the internal and construct validity of the conclusions:
1. Warm-up runs and buffer cache residency were neither controlled nor reported, conflating cold disk I/O latency with algorithmic efficiency.
2. The theoretical analysis mischaracterizes "index-free adjacency" and ignores modern memory hierarchy phenomena (CPU cache lines, TLB misses, and random pointer chasing).
3. The benchmarked queries evaluate non-equivalent workloads: the Redis script traverses and returns duplicate paths, whereas the PostgreSQL query executes duplicate elimination (`COUNT(DISTINCT)`), artificially inflating relational computational overhead.

---

### 3. Detailed Section-by-Section Comments

#### Comment 1: Methodological Rigor & Experimental Controls
* **Section / Page / Line:** Section IV-B (*Experimental Setup & Benchmarking Harness*), Page 4, Lines 184–212
* **Observation:**  
  The benchmark harness executes five consecutive iterations per query configuration and reports the arithmetic mean without isolating or discarding the initial iteration (cold start). In Section IV-B (Lines 195–198), the authors state: *"Each query was executed 5 times immediately following container initialization, and the average latency was computed."*  
  This constitutes a severe confounding factor:
  - In PostgreSQL, the first execution incurs physical disk read I/O to populate `shared_buffers` and the OS page cache, generating latencies of $\approx 420\text{ ms}$, whereas subsequent executions hit memory pages in $\approx 28\text{ ms}$.
  - Conversely, Redis operates entirely in-memory from startup, meaning all iterations benefited from zero disk page fault overhead.
  - Averaging an un-warmed initial run ($420\text{ ms}$) with four warm runs ($28\text{ ms}$) yields a skewed mean of $106.4\text{ ms}$ ($3.8\times$ higher than steady-state performance). Furthermore, reporting arithmetic means rather than medians ($P_{50}$) and tail percentiles ($P_{95}$, $P_{99}$) masks significant latency variance and outlier behavior caused by background checkpointing.
* **Suggested Actionable Change:**  
  1. Restructure the benchmarking harness to implement a strict **two-phase protocol**: an explicit untimed warm-up phase (minimum 2–3 runs to prime `shared_buffers` or pre-warm tables via `pg_prewarm`), followed by a timed measurement phase ($N \ge 10$ iterations).
  2. If evaluating cold-cache behavior, explicitly drop OS buffer caches and database caches between runs (`sync; echo 3 > /proc/sys/vm/drop_caches` and container restart), reporting "Cold Cache" and "Warm Cache" as distinct independent test dimensions.
  3. Replace arithmetic mean with **median ($P_{50}$)** as the primary measure of central tendency, and plot error bars or interquartile ranges (IQR) with $P_{95}/P_{99}$ to accurately capture tail latency.

---

#### Comment 2: Theoretical Foundations & Execution Plan Verification
* **Section / Page / Line:** Section II-C (*Storage Models & Traversal Foundations*) and Section V-A (*Query Formulation*), Page 2, Lines 91–114 & Page 5, Lines 240–268
* **Observation:**  
  The authors justify the observed performance delta by claiming: *"PostgreSQL must perform an $O(\log N)$ index lookup per hop, whereas graph and key-value pointer referencing is $O(1)$, proving that relational systems suffer an unavoidable algorithmic disadvantage on connected data"* (Section II-C, Lines 102–105).  
  This assertion contains two major defects:
  1. **Memory Hierarchy & Locality Reality:** As established in modern database literature (e.g., Pacaci et al., GRADES 2017; Robinson et al., *Graph Databases*, 2015), pointer chasing in graph stores/in-memory pointer graphs exhibits poor spatial locality, generating random memory dereferences, frequent CPU L1/L2/L3 cache misses, and TLB invalidations. In contrast, B+ Tree indexes in relational systems maintain packed key-pointer arrays with high cache line density; once index pages reside in `shared_buffers`, traversal along a clustered index can match or exceed pointer chasing due to prefetching and sequential memory bandwidth.
  2. **Lack of Query Plan Verification (`EXPLAIN ANALYZE`):** In Section V-A, the authors do not provide `EXPLAIN (ANALYZE, BUFFERS)` output for their PostgreSQL recursive query. Inspection of their GitHub repository reveals that the edge table `relationships(src_id, dst_id)` lacked a composite index on `(src_id, dst_id)` with covering attributes, causing PostgreSQL's recursive CTE step to fall back to a Sequential Scan or an unindexed Hash Join on larger graph sizes ($N = 100{,}000$).
* **Suggested Actionable Change:**  
  1. Revise Section II-C to present a balanced theoretical framework citing published literature: clarify that while index-free adjacency avoids index traversal, its asymptotic advantage is bounded by memory layout and hardware cache behavior.
  2. Instrument all database queries with full query plan profiling:
     - For PostgreSQL: Include `EXPLAIN (ANALYZE, BUFFERS, TIMING, COSTS)` outputs in Section V or an appendix, reporting the selected join strategy (Nested Loop vs. Hash Join), buffer hit ratios (`shared hit / read`), and memory allocated for CTE worktables.
     - Ensure appropriate indexing: Add `CREATE INDEX idx_rel_src_dst ON relationships(src_id, dst_id);` and verify that an Index Only Scan or Bitmap Index Scan is selected.

---

#### Comment 3: Workload Equivalence, Result Presentation & Visualization
* **Section / Page / Line:** Section VI-B (*Traversal Latency Results*) and Figure 4, Page 6, Lines 312–348
* **Observation:**  
  1. **Semantic Inequivalence:** In Listing 2, the Redis traversal script performs recursive list fetching that retrieves all reachable IDs including duplicates across multi-paths ($O(d^k)$ elements), whereas the PostgreSQL recursive query in Listing 1 specifies `SELECT DISTINCT dst_id` and aggregates via `COUNT(DISTINCT)`. The relational query is therefore performing heavy set deduplication, sorting, and hash aggregate operations that the Redis script omits. This is an unfair "apples-to-oranges" comparison: the workloads perform fundamentally different computational tasks.
  2. **Misleading Visual Presentation:** In Figure 4 ("Mean Latency Across Hops $k=1, 2, 3$"), the vertical axis is truncated, beginning at $y = 35\text{ ms}$ rather than $y = 0\text{ ms}$. This truncation visually distorts the visual magnitude: a $1.35\times$ performance difference at $k=2$ appears visually as an apparent $5\times$ gap. In addition, no error bars, standard deviations, or confidence intervals are displayed.
* **Suggested Actionable Change:**  
  1. Standardize query semantics: Ensure both systems return identical end results. If the goal is counting unique reachable vertices (friends within $k$ hops), the Redis script must insert keys into a temporary Redis `Set` (`SADD`) and execute `SCARD`, or both systems must return raw path streams. Confirm correctness by verifying identical output cardinality against an independent Python BFS oracle on small test graphs.
  2. Fix Figure 4:
     - Start the y-axis at zero ($y = 0$), or utilize a logarithmic scale ($\log_{10}$) if span across hops varies across orders of magnitude ($1\text{ ms}$ to $10{,}000\text{ ms}$).
     - Add error bars representing the 95% confidence interval or standard deviation across benchmark repetitions.
     - Include a corresponding summary table reporting exact values: Sample size ($N$), Median ($P_{50}$), $P_{95}$, Minimum, Maximum, and standard deviation.

---

### 4. Quantitative Evaluation Matrix (Rubric)

| Evaluation Dimension | Score (1–5) | Justification & Specific Feedback |
|:---|:---:|:---|
| **1. Problem Formulation & Research Questions** | 4 / 5 | Well-defined problem relevant to modern real-time feed architecture. RQs are clear, though RQ2 needs reformulation to reflect workload equivalence rather than pure vendor speedup. |
| **2. Theoretical Foundation & Literature** | 3 / 5 | Good foundational citations on NoSQL, but relies on oversimplified vendor marketing claims regarding index-free adjacency. Lacks critical systems papers on worst-case optimal joins (Ngo et al.) and modern relational graph capabilities. |
| **3. Methodological Rigor & Controls** | 2 / 5 | Critical deficiency in experimental controls: lack of warm-up runs, unisolated cold cache I/O, failure to report buffer pool sizes, and lack of run timeouts. |
| **4. Implementation & Query Correctness** | 3 / 5 | Docker environment is cleanly orchestrated and reproducible. However, query semantics between Redis and PostgreSQL diverge significantly (distinct set reachability vs. multi-path traversal). Missing composite index in relational schema. |
| **5. Analysis, Results & Visualizations** | 2.5 / 5 | Figure 4 suffers from truncated y-axis distortion. Over-reliance on arithmetic means masks tail latency. Lack of `EXPLAIN` query plan analysis leaves performance causes uncorroborated. |
| **6. Readability, Formatting & IEEE Standards** | 4 / 5 | Adheres well to IEEE 2-column format. Clear prose and good typographical structure. Minor citation formatting inconsistencies in bibliography. |
| **Overall Weighted Score** | **3.1 / 5.0** | **Verdict: Major Revision** |

---

### 5. Commendations & Strengths
1. **Reproducibility Framework:** The Docker Compose environment, seed-controlled synthetic data generation, and clean repository layout allow for rapid deployment and testing.
2. **Relevance of Benchmark Scenario:** Evaluating feed ingestion alongside traversal addresses a genuine database engineering tension (write penalty vs. read penalty) in real-world platforms.
3. **Writing Clarity:** The introduction and system descriptions are written in fluent, grammatically sound academic English with an intuitive running motivating example.

---

## Part II: Blank, Ready-to-Edit Peer Review Form (Template)

```markdown
# Peer review - DBMS Assignment 1

Group reviewed: [Insert Group ID, e.g., Group G_]
Paper Title: [Insert Title of Assigned Group's Submission]

Reviewer group: G9
Reviewer Team Members:
- Harleen Kaur (kaurh.it.23@nitj.ac.in)
- Gurveer Singh Brar (brargs.it.23@nitj.ac.in)
- Hardik Jassar (jassarh.it.23@nitj.ac.in)
- Harmanparteek Singh (singhhp.it.23@nitj.ac.in)

## General Assessment & Summary
[Provide 2-3 concise paragraphs summarizing the paper's core hypothesis, the systems compared, the experimental design, and the overall technical verdict: Accept / Minor Revision / Major Revision / Reject.]

## Comments

1. Section / page: [e.g., Section III-B, Page 3, Lines 120-145]

   Observation: [State specifically what was observed in the text, code, or results. Focus on technical rigor, experimental controls, theoretical grounding, or validity. Avoid vague feedback like "good work" or "needs improvement".]

   Suggested change: [Provide an explicit, concrete, actionable engineering or writing recommendation. Include specific SQL/Cypher clauses, experimental controls (e.g. warm-up runs, buffer cache clearing), statistical metrics (median/p95 instead of mean), or citations.]

2. Section / page: [e.g., Section V-A, Page 5, Lines 210-235]

   Observation: [Specific technical critique regarding query formulation, plan inspection (EXPLAIN ANALYZE), schema indexing, or benchmark execution.]

   Suggested change: [Actionable remediation: index creation, plan verification, parameter tuning, or mathematical formulation.]

3. Section / page: [e.g., Section VI-C, Page 6, Lines 310-340]

   Observation: [Specific critique regarding figures, data interpretation, threats to validity, truncated axes, or unsupported claims.]

   Suggested change: [Actionable remediation: untruncated axes, logarithmic scaling, error bars, ablation study, or qualification of claims.]

## Evaluation Rubric

| Criteria | Score (1-5) | Specific Remarks |
|---|:---:|---|
| Research Questions & Problem Clarity | _ / 5 | |
| Theoretical Grounding & Literature | _ / 5 | |
| Experimental Rigor & Controls | _ / 5 | |
| Query Formulation & Correctness | _ / 5 | |
| Result Interpretation & Plots | _ / 5 | |
| Academic Writing & Formatting | _ / 5 | |
```
