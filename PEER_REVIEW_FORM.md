# Peer review - DBMS Assignment 1

**Group reviewed:** Group G8 (*Benchmarking Relational and Non-Relational Paradigms: Key-Value Stores vs. Relational Databases for Real-Time Social Feed Ingestion and Traversal*)

**Reviewer group:** G9  
**Reviewers:** Harleen Kaur, Gurveer Singh Brar, Hardik Jassar, Harmanparteek Singh (NIT Jalandhar)  
**Mentor:** Dr. Vijay Kumar  
**Date:** November 20, 2026  

---

## Comments

1. **Section / page:** Section IV-B (*Experimental Setup & Benchmarking Harness*), Page 4, Lines 184–212

   **Observation:** The benchmarking harness computes the arithmetic mean across five iterations per configuration directly after starting the containers without implementing an untimed warm-up phase or controlling buffer pool cache state. In PostgreSQL, the initial iteration incurs physical disk I/O and cold page faults to populate `shared_buffers` ($\approx 420\text{ ms}$), while subsequent runs execute in-memory ($\approx 28\text{ ms}$), causing the reported arithmetic mean ($106.4\text{ ms}$) to overstate steady-state latency by nearly $3.8\times$. Conversely, Redis operates in-memory from startup, unfairly benefiting from zero cold-cache penalties. Furthermore, reporting arithmetic means rather than medians and tail percentiles ($P_{95}/P_{99}$) conceals high latency variance caused by background checkpointing.

   **Suggested change:** Restructure the benchmarking harness to enforce a strict two-phase protocol: (i) an untimed warm-up phase (at least 2–3 runs to prime `shared_buffers` or table pre-warming via `pg_prewarm`), followed by (ii) a timed measurement phase with $N \ge 10$ repetitions. If evaluating cold-cache conditions, flush the OS page cache (`drop_caches`) and restart containers between runs, reporting warm-cache and cold-cache regimes separately. Replace arithmetic mean with the median ($P_{50}$) and report $P_{95}$ tail percentiles with error bars.

2. **Section / page:** Section II-C (*Storage Models & Traversal Foundations*) and Section V-A (*Query Formulation*), Page 2, Line 95 & Page 5, Lines 240–268

   **Observation:** Section II-C attributes the entire traversal performance difference to index-free adjacency (IFA) being $O(1)$ versus B-tree lookups being $O(\log N)$, asserting relational databases suffer an unavoidable algorithmic flaw on multi-hop graph queries. This ignores modern memory hierarchies: pointer chasing in graph stores causes random memory dereferencing, CPU L1/L2/L3 cache misses, and TLB invalidations, whereas clustered B-trees in relational memory benefit from spatial locality and sequential memory prefetching. Crucially, Section V-A provides no `EXPLAIN (ANALYZE, BUFFERS)` execution plans, and inspecting the team's repository shows the PostgreSQL edge table lacked a composite index on `(src_id, dst_id)`, causing the recursive CTE to degrade to sequential table scans and unindexed hash joins.

   **Suggested change:** Reframe Section II-C using peer-reviewed literature (e.g., Pacaci et al. 2017, Robinson et al. 2015) to balance asymptotic complexity against hardware memory-hierarchy realities. Profile all queries using `EXPLAIN (ANALYZE, BUFFERS)` in Section V to report buffer hits, join types (Nested Loop vs. Hash Join), and memory consumption. Add the missing composite index (`CREATE INDEX idx_edges_src_dst ON relationships(src_id, dst_id);`) to ensure fair index-backed relational execution.

3. **Section / page:** Section VI-B (*Traversal Latency Results*) and Figure 4, Page 6, Lines 312–345

   **Observation:** The benchmark compares fundamentally non-equivalent query workloads. The Redis script traverses lists returning all reachable paths including duplicates ($O(d^k)$ elements), whereas the PostgreSQL recursive query enforces set deduplication via `SELECT DISTINCT` and `COUNT(DISTINCT)`, incurring substantial hashing and sorting overhead not present in the Redis test. In addition, Figure 4 truncates the vertical latency axis at $y = 35\text{ ms}$ instead of $y = 0\text{ ms}$, visually exaggerating a modest $1.35\times$ latency difference at hop 2 into an apparent $5\times$ gap, without providing error bars or variance metrics.

   **Suggested change:** Enforce identical semantic query contracts across both systems: ensure both either return raw path enumerations or distinct reachable vertex counts (e.g., use Redis Sets via `SADD`/`SCARD` to mirror PostgreSQL's `DISTINCT` set semantics), and validate cardinalities against a BFS ground-truth oracle. Correct Figure 4 by starting the y-axis at zero (or adopt a $\log_{10}$ scale for wide ranges) and plot error bars indicating the 95% confidence interval or standard deviation alongside a comprehensive data summary table.

---

*Note: For the exhaustive evaluation rubric, extended critique, and blank form template for alternate group evaluations, see [PEER_REVIEW.md](PEER_REVIEW.md).*
