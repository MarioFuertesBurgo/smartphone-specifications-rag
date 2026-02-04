import os
from llama_index.core import Document
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.neo4j_utils import get_driver
from app.rag_utils import build_index

PERSIST_DIR = "index_store"

QUERY = """
MATCH (p:Phone)
WHERE p.text IS NOT NULL
RETURN p.model_raw AS model, p.text AS text
"""

def main():
    os.makedirs(PERSIST_DIR, exist_ok=True)
    driver = get_driver()
    try:
        with driver.session() as s:
            rows = list(s.run(QUERY))
        docs = [Document(text=r["text"], metadata={"model": r["model"]}) for r in rows]
        build_index(docs, persist_dir=PERSIST_DIR)
        print(f"OK. Índice creado con {len(docs)} documentos en {PERSIST_DIR}/")
    finally:
        driver.close()

if __name__ == "__main__":
    main()
