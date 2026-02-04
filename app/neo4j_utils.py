# app/neo4j_utils.py
from neo4j import GraphDatabase
from app.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_cypher(driver, query: str, params: dict | None = None):
    with driver.session() as session:
        return session.run(query, params or {}).consume()

def run_cypher_many(driver, multi_query: str):
    """
    Ejecuta varias sentencias separadas por ';' (ignorando vacías).
    """
    statements = [q.strip() for q in multi_query.split(";") if q.strip()]
    for q in statements:
        run_cypher(driver, q)