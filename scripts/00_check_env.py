import os
import urllib.request
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

def check_ollama(base_url: str):
    url = base_url.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            if r.status != 200:
                raise RuntimeError(f"Ollama respondió con status {r.status}")
        print(f"OK Ollama: {base_url}")
    except Exception as e:
        raise RuntimeError(
            f"No puedo conectar con Ollama en {base_url}. "
            f"Asegúrate de que Ollama está instalado y ejecutándose. Detalle: {e}"
        )

def check_neo4j(uri: str, user: str, pwd: str):
    try:
        driver = GraphDatabase.driver(uri, auth=(user, pwd))
        with driver.session() as s:
            s.run("RETURN 1 AS ok").single()
        driver.close()
        print(f"OK Neo4j: {uri}")
    except Exception as e:
        raise RuntimeError(
            f"No puedo conectar con Neo4j en {uri} con el usuario {user}. Detalle: {e}"
        )

def main():
    load_dotenv()
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pwd = os.getenv("NEO4J_PASSWORD", "")
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    if not neo4j_pwd:
        raise RuntimeError("Falta NEO4J_PASSWORD en tu .env")

    check_ollama(ollama_url)
    check_neo4j(neo4j_uri, neo4j_user, neo4j_pwd)

    print("Entorno OK.")

if __name__ == "__main__":
    main()
