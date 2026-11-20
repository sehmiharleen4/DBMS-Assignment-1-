#!/usr/bin/env python3
"""Load the generated graph into Neo4j (each friendship stored ONCE, traversed undirected)."""
import argparse
import csv
import time

from neo4j import GraphDatabase


def batches(rows, size=10000):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--uri", default="bolt://localhost:7687")
    ap.add_argument("--user", default="neo4j")
    ap.add_argument("--password", default="g9password123")
    a = ap.parse_args()
    persons = [{"id": int(r[0]), "name": r[1], "age": int(r[2])}
               for r in csv.reader(open(f"{a.data}/persons.csv"))]
    edges = [{"a": int(r[0]), "b": int(r[1])} for r in csv.reader(open(f"{a.data}/friendships.csv"))]

    driver = GraphDatabase.driver(a.uri, auth=(a.user, a.password))
    t0 = time.perf_counter()
    with driver.session() as s:
        s.run("MATCH (n) CALL { WITH n DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS").consume()
        s.run("CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE").consume()
        for b in batches(persons):
            s.run("UNWIND $rows AS r CREATE (:Person {id: r.id, name: r.name, age: r.age})", rows=b).consume()
        s.run("CALL db.awaitIndexes()").consume()
        for b in batches(edges):
            s.run("UNWIND $rows AS r MATCH (x:Person {id: r.a}), (y:Person {id: r.b}) "
                  "CREATE (x)-[:FRIEND]->(y)", rows=b).consume()
    print(f"neo4j: load_seconds={time.perf_counter()-t0:.1f} nodes={len(persons)} relationships={len(edges)}")
    print("Tip: after loading, let the DB settle ~30 s, then measure store size with "
          "`docker exec g9_neo4j du -sb /data/databases/neo4j`.")
    driver.close()


if __name__ == "__main__":
    main()
