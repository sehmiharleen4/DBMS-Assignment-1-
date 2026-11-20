# G9 talk script - 10 minutes

This script presents the literature review and proposed benchmark. It does not report results from a G9 database run. The assignment may require a separate slide deck; this script is not a slide file.

## Slide 1 - Graph traversal versus relational recursion (S1, 45 seconds)

This paper reviews published graph and relational database benchmarks and proposes a separate Neo4j/PostgreSQL comparison. The proposed task counts people within one to four friendship hops. We do not claim that our group ran this experiment.

## Slide 2 - Research questions (S1, 60 seconds)

RQ1 compares property-graph and RDF models and their query languages. RQ2 asks how native graph stores and relational engines handle relationships. RQ3 asks what published timings show and whether they answer our specific Neo4j/PostgreSQL question. The paper describes a recursive CTE and level-wise SQL comparison as proposed work.

## Slide 3 - Models and languages (S2, 75 seconds)

A property graph has labelled nodes and typed relationships, with properties on both. Neo4j uses Cypher, where a relationship pattern is written directly. RDF represents data as subject-predicate-object triples and uses SPARQL. GQL became an ISO standard in 2024, while SQL/PGQ adds graph pattern matching inside SQL. For this project, the property-graph model matches the friendship traversal directly.

## Slide 4 - Related work and gap (S2, 75 seconds)

The review covers graph models and languages, graph database design, relational support for graph workloads, and benchmark studies. The sources use different systems and workloads. The proposed G9 benchmark would compare three query formulations on the same generated graphs, but it has not been run.

## Slide 5 - Method (S3, 90 seconds)

The supplied generator is designed to create deterministic Barabasi-Albert graphs at 1,000, 10,000, and 100,000 people. PostgreSQL and Neo4j loaders and a timing harness are included. These are proposed experiment details; no performance run has been completed.

## Slide 6 - Correctness and setup (S3, 60 seconds)

The benchmark is intended to count distinct people reachable within the depth bound. A local code self-test checked the two SQL formulations against an independent breadth-first search; this tests query correctness, not database performance. The database counts and timing results remain unavailable because the benchmark has not run.

## Slide 7 - Results (S4, 120 seconds)

Present the published studies summarized in Section VI. Neo4j was about three times faster on two tasks in the 2022 invoice study; MariaDB was faster on its aggregation and recursive-chain tasks. The 2019 PostgreSQL study shows how indexing changed a five-hop query time. These figures come from different workloads and do not answer the proposed G9 comparison. Do not present them as G9 measurements.

## Slide 8 - Limits and conclusion (S4, 75 seconds)

The reviewed evidence does not establish a universal speed ranking or answer the specific friends-within-k-hops question. The proposed G9 test could address that gap after it is run. Its planned limits include synthetic graphs, one machine, warm caches, and a reachability-count query rather than a path-returning workload.

## Likely questions

- Why does the recursive CTE use `UNION`? It removes duplicate `(id, depth)` rows and prevents repeated expansion from cycles at the same depth.
- Why does PostgreSQL store each friendship twice? It makes traversal from either endpoint an indexed lookup on `src`.
- Why count distinct endpoints instead of paths? It measures reachability and avoids reporting many duplicate paths to the same person.
- Does a PostgreSQL index make it index-free adjacency? No. It accelerates row lookup, but it does not turn rows into stored relationship pointers.
- What does a Barabasi-Albert graph miss? It has degree skew but does not reproduce all real social-network features, such as communities, temporal behaviour, and attribute correlations.

