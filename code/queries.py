"""Query builders shared by the benchmark and the self-test.

Semantics (identical for every system): given a start person s and a depth k,
return the number of DISTINCT persons, other than s, reachable from s by
following 1..k FRIEND edges (friendship is undirected).
"""


def cte_sql(k: int, p: str) -> str:
    """Variant A: textbook recursive CTE (UNION removes duplicate (id, depth) rows)."""
    return f"""
WITH RECURSIVE r(id, depth) AS (
    SELECT dst, 1 FROM friendship WHERE src = {p}
    UNION
    SELECT f.dst, r.depth + 1
    FROM r JOIN friendship f ON f.src = r.id
    WHERE r.depth < {k}
)
SELECT count(DISTINCT id) FROM r WHERE id <> {p}
""".strip()


def levels_sql(k: int, p: str) -> str:
    """Variant B: hand-written level-by-level expansion with DISTINCT at every level
    (a BFS expressed as k chained joins). A stronger relational baseline than A."""
    parts = [f"l1(id) AS (SELECT DISTINCT dst FROM friendship WHERE src = {p})"]
    for i in range(2, k + 1):
        parts.append(
            f"l{i}(id) AS (SELECT DISTINCT f.dst FROM l{i-1} "
            f"JOIN friendship f ON f.src = l{i-1}.id)"
        )
    union = " UNION ".join(f"SELECT id FROM l{i}" for i in range(1, k + 1))
    return "WITH " + ",\n".join(parts) + f"\nSELECT count(*) FROM ({union}) u WHERE id <> {p}"


def cypher(k: int) -> str:
    """Variant C: Neo4j variable-length pattern. The bound cannot be a parameter in
    Cypher, so k is inlined (it is an int that we control)."""
    return (
        f"MATCH (p:Person {{id: $id}})-[:FRIEND*1..{int(k)}]-(f:Person) "
        "WHERE f <> p RETURN count(DISTINCT f) AS c"
    )
